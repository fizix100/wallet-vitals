from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest
from eth_utils import keccak

from wallet_vitals.domain.models import EvidenceSnapshot, OnchainEvidence
from wallet_vitals.graph.errors import GraphResponseError, GraphTransportError
from wallet_vitals.graph.oracle import ADDRESSES_PROVIDER, AaveOracleClient, verify_account

WALLET = "0x" + "1" * 40
ASSET = "0x" + "2" * 40
POOL = "0x" + "3" * 40
ORACLE = "0x" + "4" * 40
BLOCK_HASH = "0x" + "a" * 64
TIMESTAMP = 1788947000


def encoded(*values: int) -> str:
    return "0x" + "".join(f"{value:064x}" for value in values)


class RpcFixture:
    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.chain = "0x1"
        self.hash = BLOCK_HASH
        self.number = 100
        self.timestamp = TIMESTAMP
        self.e_mode = 0
        self.unit = 10**8
        self.currency = 0
        self.price = 2000 * 10**8
        self.response_override: dict | None = None

    def handle(self, request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        self.requests.append(payload)
        if self.response_override is not None:
            return httpx.Response(200, json={**self.response_override, "id": payload["id"]})
        method = payload["method"]
        if method == "eth_chainId":
            result = self.chain
        elif method == "eth_getBlockByNumber":
            result = {
                "number": hex(self.number),
                "timestamp": hex(self.timestamp),
                "hash": self.hash,
            }
        elif method == "eth_call":
            call, reference = payload["params"]
            assert reference == {"blockHash": BLOCK_HASH, "requireCanonical": True}
            assert call["to"] in {ADDRESSES_PROVIDER, POOL, ORACLE}
            responses = {
                "getPool()": encoded(int(POOL, 16)),
                "getPriceOracle()": encoded(int(ORACLE, 16)),
                "BASE_CURRENCY()": encoded(self.currency),
                "BASE_CURRENCY_UNIT()": encoded(self.unit),
                "getUserAccountData(address)": encoded(
                    2000 * 10**8, 1000 * 10**8, 0, 8000, 7500, 16 * 10**17
                ),
                "getUserEMode(address)": encoded(self.e_mode),
                "getAssetPrice(address)": encoded(self.price),
            }
            by_selector = {"0x" + keccak(text=k)[:4].hex(): v for k, v in responses.items()}
            result = by_selector[call["data"][:10]]
        else:
            raise AssertionError(f"Unexpected RPC method: {method}")
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": payload["id"], "result": result})


async def fetch(fixture: RpcFixture, graph_hash: str | None = BLOCK_HASH):
    client = AaveOracleClient("https://rpc.test", transport=httpx.MockTransport(fixture.handle))
    try:
        return await client.fetch(WALLET, [ASSET], 100, TIMESTAMP, graph_hash)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_oracle_prices_and_account_are_pinned_to_same_block() -> None:
    fixture = RpcFixture()
    result = await fetch(fixture)
    assert result.prices[ASSET] == 2000
    assert result.evidence.pool_address == POOL
    assert result.evidence.oracle_address == ORACLE
    assert result.evidence.health_factor == Decimal("1.6")
    assert result.evidence.verification == "pending"
    assert all(
        request["method"] in {"eth_call", "eth_chainId", "eth_getBlockByNumber"}
        for request in fixture.requests
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("chain", "0xa", "mainnet"),
        ("number", 101, "blocks do not match"),
        ("hash", "0x" + "b" * 64, "blocks do not match"),
        ("timestamp", TIMESTAMP + 1, "blocks do not match"),
        ("e_mode", 1, "eMode"),
        ("unit", 10**18, "currency or unit"),
        ("currency", 123, "currency or unit"),
        ("price", 0, "non-positive"),
    ],
)
async def test_invalid_oracle_evidence_fails_closed(field, value, message) -> None:
    fixture = RpcFixture()
    setattr(fixture, field, value)
    with pytest.raises(GraphResponseError, match=message):
        await fetch(fixture)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"jsonrpc": "2.0", "error": {"message": "secret URL must not leak"}},
        {"jsonrpc": "2.0"},
    ],
)
async def test_rpc_errors_are_sanitized_without_latest_fallback(payload) -> None:
    fixture = RpcFixture()
    fixture.response_override = payload
    with pytest.raises(GraphResponseError, match="pinned evidence request") as caught:
        await fetch(fixture)
    assert "secret" not in str(caught.value)
    assert not any("latest" in str(request["params"]) for request in fixture.requests)


@pytest.mark.asyncio
async def test_rpc_network_failure_is_sanitized() -> None:
    def broken(request):
        raise httpx.ConnectError("secret RPC URL", request=request)

    client = AaveOracleClient("https://rpc.test", transport=httpx.MockTransport(broken))
    try:
        with pytest.raises(GraphTransportError, match="could not provide") as caught:
            await client.fetch(WALLET, [], 100, TIMESTAMP, BLOCK_HASH)
        assert "secret" not in str(caught.value)
    finally:
        await client.close()


def attach_proof(snapshot: EvidenceSnapshot) -> None:
    snapshot.onchain_evidence = OnchainEvidence(
        block_number=100,
        block_hash=BLOCK_HASH,
        block_timestamp=datetime.fromtimestamp(TIMESTAMP, UTC),
        addresses_provider=ADDRESSES_PROVIDER,
        pool_address=POOL,
        oracle_address=ORACLE,
        total_collateral_usd=Decimal("2000"),
        total_debt_usd=Decimal("1000"),
        health_factor=Decimal("1.6"),
    )


def test_account_crosscheck_accepts_matching_positions(evidence_snapshot) -> None:
    attach_proof(evidence_snapshot)
    verify_account(evidence_snapshot)
    assert evidence_snapshot.onchain_evidence.verification == "matched"


@pytest.mark.parametrize("change", ["debt", "collateral", "empty", "threshold", "boundary"])
def test_account_crosscheck_rejects_incomplete_or_wrong_parameters(
    evidence_snapshot, change
) -> None:
    attach_proof(evidence_snapshot)
    if change == "debt":
        evidence_snapshot.assets[1].debt_usd = Decimal("900")
    elif change == "collateral":
        evidence_snapshot.assets[0].supply_usd = Decimal("2100")
    elif change == "empty":
        evidence_snapshot.assets = []
    elif change == "threshold":
        evidence_snapshot.assets[0].liquidation_threshold_bps = 8500
    else:
        evidence_snapshot.assets[0].liquidation_threshold_bps = 5500
        evidence_snapshot.onchain_evidence.health_factor = Decimal("1.10001")
    with pytest.raises(GraphResponseError):
        verify_account(evidence_snapshot)
