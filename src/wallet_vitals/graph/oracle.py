"""Read-only Aave oracle evidence, pinned to the Graph block hash (EIP-1898).

Contract ABI and Ethereum provider address:
https://github.com/aave/aave-v3-origin/tree/main/src/contracts/interfaces
https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Ethereum.sol
No latest-block fallback, transaction signing, or alternative market prices.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import Any

import httpx
from eth_utils import is_address, keccak

from wallet_vitals.domain.models import EvidenceSnapshot, OnchainEvidence
from wallet_vitals.domain.risk import calculate_snapshot_risk, severity_for
from wallet_vitals.graph.errors import GraphResponseError, GraphTransportError

ADDRESSES_PROVIDER = "0x2f39d218133afab8f2b819b1066c7e434ad94e9e"
ZERO_ADDRESS = "0x" + "0" * 40


def _words(value: Any, count: int) -> list[int]:
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-fA-F]+", value):
        raise GraphResponseError("Invalid Aave contract response.")
    if len(value) != 2 + 64 * count:
        raise GraphResponseError("Unexpected Aave contract response length.")
    return [int(value[2 + 64 * i : 2 + 64 * (i + 1)], 16) for i in range(count)]


def _contract_address(value: Any) -> str:
    address = _words(value, 1)[0]
    if not 0 < address < 2**160:
        raise GraphResponseError("Invalid Aave contract address.")
    return "0x" + format(address, "040x")


@dataclass(frozen=True)
class OracleSnapshot:
    prices: dict[str, Decimal]
    evidence: OnchainEvidence


class AaveOracleClient:
    def __init__(
        self,
        endpoint: str,
        timeout_seconds: float = 15,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._client = httpx.AsyncClient(timeout=timeout_seconds, transport=transport)
        self._limit = asyncio.Semaphore(8)
        self._next_id = 0

    async def close(self) -> None:
        await self._client.aclose()

    async def _rpc(self, method: str, params: list[Any]) -> Any:
        self._next_id += 1
        request_id = self._next_id
        async with self._limit:
            try:
                response = await self._client.post(
                    self._endpoint,
                    json={"jsonrpc": "2.0", "id": request_id, "method": method, "params": params},
                )
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                # Never return provider URLs, credentials, or raw error payloads to the browser.
                raise GraphTransportError(
                    "Ethereum RPC could not provide oracle evidence."
                ) from exc
        if (
            not isinstance(payload, dict)
            or payload.get("id") != request_id
            or payload.get("jsonrpc") != "2.0"
            or payload.get("error") is not None
            or "result" not in payload
        ):
            raise GraphResponseError(
                "Ethereum RPC rejected the pinned evidence request; analysis was stopped."
            )
        return payload["result"]

    async def fetch(
        self,
        address: str,
        assets: list[str],
        block_number: int,
        block_timestamp: int,
        graph_block_hash: str | None,
    ) -> OracleSnapshot:
        if not is_address(address) or any(not is_address(asset) for asset in assets):
            raise GraphResponseError("Invalid address in oracle evidence request.")
        chain, block = await asyncio.gather(
            self._rpc("eth_chainId", []),
            self._rpc("eth_getBlockByNumber", [hex(block_number), False]),
        )
        if chain != "0x1":
            raise GraphResponseError("Ethereum RPC is not connected to mainnet.")
        if not isinstance(block, dict):
            raise GraphResponseError("Ethereum RPC cannot resolve the indexed block.")
        try:
            number = int(block["number"], 16)
            timestamp = int(block["timestamp"], 16)
            block_hash = block["hash"]
        except (KeyError, ValueError, TypeError) as exc:
            raise GraphResponseError("Malformed Ethereum evidence block.") from exc
        if (
            number != block_number
            or timestamp != block_timestamp
            or not isinstance(block_hash, str)
            or not re.fullmatch(r"0x[0-9a-fA-F]{64}", block_hash)
            or (graph_block_hash and graph_block_hash.lower() != block_hash.lower())
        ):
            raise GraphResponseError("The Graph and Ethereum RPC evidence blocks do not match.")
        reference = {"blockHash": block_hash, "requireCanonical": True}

        async def call(contract: str, signature: str, argument: str | None = None) -> Any:
            data = "0x" + keccak(text=signature)[:4].hex()
            if argument is not None:
                data += argument[2:].lower().rjust(64, "0")
            return await self._rpc("eth_call", [{"to": contract, "data": data}, reference])

        pool_result, oracle_result = await asyncio.gather(
            call(ADDRESSES_PROVIDER, "getPool()"),
            call(ADDRESSES_PROVIDER, "getPriceOracle()"),
        )
        pool = _contract_address(pool_result)
        oracle = _contract_address(oracle_result)
        currency, unit, account, e_mode, *prices = await asyncio.gather(
            call(oracle, "BASE_CURRENCY()"),
            call(oracle, "BASE_CURRENCY_UNIT()"),
            call(pool, "getUserAccountData(address)", address),
            call(pool, "getUserEMode(address)", address),
            *(call(oracle, "getAssetPrice(address)", asset) for asset in assets),
        )
        if _words(currency, 1)[0] != 0 or _words(unit, 1)[0] != 10**8:
            raise GraphResponseError("Unsupported Aave oracle currency or unit.")
        if _words(e_mode, 1)[0] != 0:
            raise GraphResponseError(
                "This wallet uses eMode. Its current category rules are not supported yet; "
                "analysis was stopped instead of applying legacy indexed thresholds."
            )
        account_values = _words(account, 6)
        price_values = [_words(price, 1)[0] for price in prices]
        if any(price <= 0 for price in price_values):
            raise GraphResponseError("The Aave oracle returned a non-positive asset price.")
        with localcontext() as context:
            context.prec = 80
            evidence = OnchainEvidence(
                block_number=block_number,
                block_hash=block_hash,
                block_timestamp=datetime.fromtimestamp(timestamp, UTC),
                addresses_provider=ADDRESSES_PROVIDER,
                pool_address=pool,
                oracle_address=oracle,
                total_collateral_usd=Decimal(account_values[0]) / Decimal(10**8),
                total_debt_usd=Decimal(account_values[1]) / Decimal(10**8),
                health_factor=(
                    Decimal(account_values[5]) / Decimal(10**18) if account_values[1] else None
                ),
            )
            return OracleSnapshot(
                prices={
                    asset.lower(): Decimal(price) / Decimal(10**8)
                    for asset, price in zip(assets, price_values, strict=True)
                },
                evidence=evidence,
            )


def verify_account(snapshot: EvidenceSnapshot) -> None:
    """Stop on materially incomplete/stale indexed positions, including false empty wallets.

    Totals: 1 ppm relative or $0.000001 absolute rounding allowance.
    HF: 0.0002 absolute or 1 basis point relative (Aave threshold rounding).
    Zero/nonzero debt and severity must agree exactly.
    """
    evidence = snapshot.onchain_evidence
    if evidence is None:
        raise GraphResponseError("Missing onchain account verification.")
    with localcontext() as context:
        context.prec = 80
        collateral = sum(
            (asset.supply_usd for asset in snapshot.assets if asset.collateral_enabled), Decimal(0)
        )
        debt = sum((asset.debt_usd for asset in snapshot.assets), Decimal(0))
        for indexed, contract in (
            (collateral, evidence.total_collateral_usd),
            (debt, evidence.total_debt_usd),
        ):
            tolerance = max(Decimal("0.000001"), abs(contract) * Decimal("0.000001"))
            if (indexed == 0) != (contract == 0) or abs(indexed - contract) > tolerance:
                raise GraphResponseError(
                    "Indexed positions do not reconcile with Aave at the same block; "
                    "risk analysis was stopped because evidence may be incomplete."
                )
        calculation = calculate_snapshot_risk(snapshot)
        indexed_hf = calculation.health_factor
        contract_hf = evidence.health_factor
        if (indexed_hf is None) != (contract_hf is None):
            raise GraphResponseError("Indexed debt does not match the Aave account.")
        if indexed_hf is not None and contract_hf is not None:
            tolerance = max(Decimal("0.0002"), abs(contract_hf) * Decimal("0.0001"))
            if abs(indexed_hf - contract_hf) > tolerance or calculation.severity != severity_for(
                contract_hf, evidence.total_debt_usd
            ):
                raise GraphResponseError(
                    "Indexed risk parameters do not reconcile with the Aave contract; "
                    "analysis was stopped."
                )
    evidence.verification = "matched"
