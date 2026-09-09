from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any

from wallet_vitals.domain.models import (
    EvidenceSnapshot,
    PositionAsset,
    PriceEvidence,
    SourceMetadata,
)
from wallet_vitals.domain.risk import (
    RULES_VERSION,
    accrue_scaled_balance,
    accrue_stable_debt,
    normalized_income,
    normalized_variable_debt,
)
from wallet_vitals.graph.client import GraphClient
from wallet_vitals.graph.errors import (
    GraphIndexingError,
    GraphResponseError,
    GraphStaleDataError,
)
from wallet_vitals.graph.oracle import AaveOracleClient, verify_account

AAVE_USER_QUERY = """
query WalletVitalsAaveUser($address: ID!) {
  user(id: $address) {
    id
    eModeCategoryId {
      id
      liquidationThreshold
    }
    reserves(first: 100) {
      id
      usageAsCollateralEnabledOnUser
      scaledATokenBalance
      scaledVariableDebt
      principalStableDebt
      stableBorrowRate
      stableBorrowLastUpdateTimestamp
      reserve {
        id
        underlyingAsset
        symbol
        decimals
        reserveLiquidationThreshold
        liquidityRate
        variableBorrowRate
        liquidityIndex
        variableBorrowIndex
        lastUpdateTimestamp
        eMode {
          id
        }
        price {
          priceInEth
          lastUpdateTimestamp
          oracle {
            baseCurrency
            baseCurrencyUnit
          }
        }
      }
    }
  }
  _meta {
    deployment
    hasIndexingErrors
    block {
      number
      hash
      timestamp
    }
  }
}
"""


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GraphResponseError(f"Missing or invalid {label} in Aave data.")
    return value


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise GraphResponseError(f"Invalid integer for {label} in Aave data.")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise GraphResponseError(f"Invalid integer for {label} in Aave data.") from exc
    if result < 0:
        raise GraphResponseError(f"Negative value for {label} in Aave data.")
    return result


def _decimal(value: Any, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise GraphResponseError(f"Invalid decimal for {label} in Aave data.") from exc
    if not result.is_finite():
        raise GraphResponseError(f"Non-finite value for {label} in Aave data.")
    return result


class AaveV3Subgraph:
    def __init__(
        self,
        client: GraphClient,
        subgraph_id: str,
        max_block_age_seconds: int = 900,
        max_price_age_seconds: int = 86400,
        oracle_client: AaveOracleClient | None = None,
    ) -> None:
        self._client = client
        self._subgraph_id = subgraph_id
        self._max_block_age_seconds = max_block_age_seconds
        self._max_price_age_seconds = max_price_age_seconds
        self._oracle_client = oracle_client

    async def fetch_snapshot(self, address: str) -> EvidenceSnapshot:
        queried_at = datetime.now(UTC)
        data = await self._client.query(AAVE_USER_QUERY, {"address": address.lower()})
        meta = _mapping(data.get("_meta"), "_meta")
        block = _mapping(meta.get("block"), "_meta.block")
        block_number = _integer(block.get("number"), "block number")
        block_timestamp_raw = _integer(block.get("timestamp"), "block timestamp")
        block_timestamp = datetime.fromtimestamp(block_timestamp_raw, tz=UTC)
        deployment = str(meta.get("deployment") or "").strip()
        if not deployment:
            raise GraphResponseError("The Aave subgraph deployment identifier is missing.")
        if meta.get("hasIndexingErrors") is not False:
            raise GraphIndexingError(
                "The Aave subgraph reports indexing errors; analysis was stopped."
            )
        graph_block_hash = block.get("hash")
        if graph_block_hash is not None and (
            not isinstance(graph_block_hash, str)
            or not re.fullmatch(r"0x[0-9a-fA-F]{64}", graph_block_hash)
        ):
            raise GraphResponseError("Invalid Graph evidence block hash.")
        age_seconds = (queried_at - block_timestamp).total_seconds()
        if age_seconds > self._max_block_age_seconds:
            raise GraphStaleDataError(
                f"Aave data is stale by {int(age_seconds)} seconds; analysis was stopped."
            )
        if age_seconds < -60:
            raise GraphResponseError("The Aave block timestamp is unexpectedly in the future.")

        user = data.get("user")
        assets: list[PositionAsset] = []
        warnings: list[str] = []
        oracle_snapshot = None
        reserves: list[Any] = []
        if user is not None:
            user_data = _mapping(user, "user")
            if user_data.get("eModeCategoryId") is not None:
                raise GraphResponseError("Indexed eMode positions are not supported yet.")
            reserves = user_data.get("reserves")
            if not isinstance(reserves, list):
                raise GraphResponseError("Missing reserve positions in Aave data.")
            if len(reserves) >= 100:
                raise GraphResponseError(
                    "Reserve query reached its limit; evidence may be incomplete."
                )
        if self._oracle_client is not None:
            active_addresses: list[str] = []
            for item in reserves:
                position = _mapping(item, "user reserve")
                if any(
                    _integer(position.get(field), field)
                    for field in (
                        "scaledATokenBalance",
                        "scaledVariableDebt",
                        "principalStableDebt",
                    )
                ):
                    reserve = _mapping(position.get("reserve"), "reserve")
                    active_addresses.append(str(reserve.get("underlyingAsset") or "").lower())
            if len(set(active_addresses)) != len(active_addresses):
                raise GraphResponseError("Duplicate reserve assets in indexed positions.")
            oracle_snapshot = await self._oracle_client.fetch(
                address, active_addresses, block_number, block_timestamp_raw, graph_block_hash
            )
            warnings.append(
                "Prices are Aave oracle contract values at the receipt block, not market quotes. "
                "Reading the oracle does not establish each underlying feed's update time."
            )
        if user is not None:
            for item in reserves:
                position = _mapping(item, "user reserve")
                raw_balances = [
                    _integer(position.get(field), field)
                    for field in (
                        "scaledATokenBalance",
                        "scaledVariableDebt",
                        "principalStableDebt",
                    )
                ]
                if not any(raw_balances):
                    continue
                reserve = _mapping(position.get("reserve"), "reserve")
                asset_address = str(reserve.get("underlyingAsset") or "").lower()
                price_evidence = None
                if oracle_snapshot is not None:
                    price_usd = oracle_snapshot.prices[asset_address]
                    proof = oracle_snapshot.evidence
                    price_evidence = PriceEvidence(
                        oracle_address=proof.oracle_address,
                        block_number=proof.block_number,
                        block_hash=proof.block_hash,
                    )
                else:
                    # Strict indexed-only mode is useful for adapter tests. The live app always
                    # supplies the oracle client and fails closed if RPC evidence is unavailable.
                    price = reserve.get("price")
                    if price is None:
                        raise GraphResponseError(
                            "Missing oracle price; position analysis is incomplete."
                        )
                    price_data = _mapping(price, "reserve price")
                    price_updated = _integer(
                        price_data.get("lastUpdateTimestamp"), "price timestamp"
                    )
                    if block_timestamp_raw - price_updated > self._max_price_age_seconds:
                        raise GraphStaleDataError(
                            "An active asset's indexed oracle price is too old; "
                            "risk analysis was stopped."
                        )
                    if price_updated > block_timestamp_raw:
                        raise GraphResponseError(
                            "Oracle timestamp is later than the evidence block."
                        )
                    oracle = _mapping(price_data.get("oracle"), "price oracle")
                    base_unit = _integer(oracle.get("baseCurrencyUnit"), "oracle base unit")
                    if base_unit != 10**8 or str(oracle.get("baseCurrency")).lower() not in {
                        "usd",
                        "0x0000000000000000000000000000000000000000",
                    }:
                        raise GraphResponseError("Unsupported Aave oracle currency or unit.")
                    price_usd = _decimal(price_data.get("priceInEth"), "oracle price") / Decimal(
                        base_unit
                    )

                last_update = _integer(reserve.get("lastUpdateTimestamp"), "reserve last update")
                elapsed = max(0, block_timestamp_raw - last_update)
                liquidity_index = _integer(reserve.get("liquidityIndex"), "liquidity index")
                variable_index = _integer(
                    reserve.get("variableBorrowIndex"), "variable borrow index"
                )
                current_supply_raw = accrue_scaled_balance(
                    _integer(position.get("scaledATokenBalance"), "scaled aToken balance"),
                    normalized_income(
                        liquidity_index,
                        _integer(reserve.get("liquidityRate"), "liquidity rate"),
                        elapsed,
                    ),
                )
                current_variable_debt_raw = accrue_scaled_balance(
                    _integer(position.get("scaledVariableDebt"), "scaled variable debt"),
                    normalized_variable_debt(
                        variable_index,
                        _integer(reserve.get("variableBorrowRate"), "variable borrow rate"),
                        elapsed,
                    ),
                )
                stable_last_update = _integer(
                    position.get("stableBorrowLastUpdateTimestamp"),
                    "stable debt last update",
                )
                stable_elapsed = max(0, block_timestamp_raw - stable_last_update)
                current_stable_debt_raw = accrue_stable_debt(
                    _integer(position.get("principalStableDebt"), "principal stable debt"),
                    _integer(position.get("stableBorrowRate"), "stable borrow rate"),
                    stable_elapsed,
                )
                decimals = _integer(reserve.get("decimals"), "token decimals")
                if decimals > 36:
                    raise GraphResponseError("Aave returned unsupported token decimals.")

                with localcontext() as context:
                    context.prec = 70
                    scale = Decimal(10) ** decimals
                    supply = Decimal(current_supply_raw) / scale
                    debt = Decimal(current_variable_debt_raw + current_stable_debt_raw) / scale
                    if price_usd <= 0:
                        if supply == 0 and debt == 0:
                            continue
                        raise GraphResponseError("Aave returned a non-positive oracle price.")
                    supply_usd = supply * price_usd
                    debt_usd = debt * price_usd

                threshold = _integer(
                    reserve.get("reserveLiquidationThreshold"), "reserve liquidation threshold"
                )
                collateral_enabled = position.get("usageAsCollateralEnabledOnUser")
                if not isinstance(collateral_enabled, bool) or threshold > 10_000:
                    raise GraphResponseError("Invalid indexed collateral configuration.")
                if (
                    current_supply_raw == 0
                    and current_variable_debt_raw == 0
                    and current_stable_debt_raw == 0
                ):
                    continue
                assets.append(
                    PositionAsset(
                        address=asset_address,
                        symbol=str(reserve.get("symbol") or "UNKNOWN")[:24],
                        decimals=decimals,
                        supply=supply,
                        debt=debt,
                        price_usd=price_usd,
                        supply_usd=supply_usd,
                        debt_usd=debt_usd,
                        liquidation_threshold_bps=threshold,
                        collateral_enabled=collateral_enabled and threshold > 0,
                        evidence_ref=f"aave-v3:user-reserve:{position.get('id')}",
                        price_evidence=price_evidence,
                    )
                )

        snapshot = EvidenceSnapshot(
            address=address.lower(),
            source=SourceMetadata(
                subgraph_id=self._subgraph_id,
                deployment=deployment,
                block_number=block_number,
                block_timestamp=block_timestamp,
                queried_at=queried_at,
                has_indexing_errors=False,
                rules_version=RULES_VERSION if oracle_snapshot else "aave-v1",
            ),
            assets=assets,
            warnings=warnings,
            onchain_evidence=oracle_snapshot.evidence if oracle_snapshot else None,
        )
        if oracle_snapshot is not None:
            verify_account(snapshot)
        return snapshot
