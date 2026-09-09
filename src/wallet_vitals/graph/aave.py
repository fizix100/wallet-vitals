from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any

from wallet_vitals.domain.models import EvidenceSnapshot, PositionAsset, SourceMetadata
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
    ) -> None:
        self._client = client
        self._subgraph_id = subgraph_id
        self._max_block_age_seconds = max_block_age_seconds

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
        if bool(meta.get("hasIndexingErrors")):
            raise GraphIndexingError(
                "The Aave subgraph reports indexing errors; analysis was stopped."
            )
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
        if user is not None:
            user_data = _mapping(user, "user")
            user_e_mode = user_data.get("eModeCategoryId")
            user_e_mode_id: str | None = None
            user_e_mode_threshold = 0
            if user_e_mode is not None:
                e_mode = _mapping(user_e_mode, "user eMode category")
                user_e_mode_id = str(e_mode.get("id") or "") or None
                user_e_mode_threshold = _integer(
                    e_mode.get("liquidationThreshold"), "eMode liquidation threshold"
                )

            reserves = user_data.get("reserves")
            if not isinstance(reserves, list):
                raise GraphResponseError("Missing reserve positions in Aave data.")
            for item in reserves:
                position = _mapping(item, "user reserve")
                reserve = _mapping(position.get("reserve"), "reserve")
                price = reserve.get("price")
                if price is None:
                    warnings.append(
                        f"Skipped {str(reserve.get('symbol') or 'unknown')[:24]}: no oracle price."
                    )
                    continue
                price_data = _mapping(price, "reserve price")
                oracle = _mapping(price_data.get("oracle"), "price oracle")
                base_unit = _integer(oracle.get("baseCurrencyUnit"), "oracle base unit")
                if base_unit <= 0:
                    raise GraphResponseError("The Aave oracle base currency unit is invalid.")

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
                    price_usd = _decimal(price_data.get("priceInEth"), "oracle price") / Decimal(
                        base_unit
                    )
                    if price_usd <= 0:
                        if supply == 0 and debt == 0:
                            continue
                        raise GraphResponseError("Aave returned a non-positive oracle price.")
                    supply_usd = supply * price_usd
                    debt_usd = debt * price_usd

                reserve_e_mode = reserve.get("eMode")
                reserve_e_mode_id = (
                    str(_mapping(reserve_e_mode, "reserve eMode").get("id") or "")
                    if reserve_e_mode is not None
                    else None
                )
                e_mode_applied = bool(
                    user_e_mode_id and reserve_e_mode_id and user_e_mode_id == reserve_e_mode_id
                )
                threshold = (
                    user_e_mode_threshold
                    if e_mode_applied
                    else _integer(
                        reserve.get("reserveLiquidationThreshold"),
                        "reserve liquidation threshold",
                    )
                )
                if (
                    current_supply_raw == 0
                    and current_variable_debt_raw == 0
                    and current_stable_debt_raw == 0
                ):
                    continue
                assets.append(
                    PositionAsset(
                        address=str(reserve.get("underlyingAsset") or "").lower(),
                        symbol=str(reserve.get("symbol") or "UNKNOWN")[:24],
                        decimals=decimals,
                        supply=supply,
                        debt=debt,
                        price_usd=price_usd,
                        supply_usd=supply_usd,
                        debt_usd=debt_usd,
                        liquidation_threshold_bps=threshold,
                        collateral_enabled=bool(position.get("usageAsCollateralEnabledOnUser")),
                        e_mode_applied=e_mode_applied,
                        evidence_ref=f"aave-v3:user-reserve:{position.get('id')}",
                    )
                )

        return EvidenceSnapshot(
            address=address.lower(),
            source=SourceMetadata(
                subgraph_id=self._subgraph_id,
                deployment=deployment,
                block_number=block_number,
                block_timestamp=block_timestamp,
                queried_at=queried_at,
                has_indexing_errors=False,
                rules_version=RULES_VERSION,
            ),
            assets=assets,
            warnings=warnings,
        )
