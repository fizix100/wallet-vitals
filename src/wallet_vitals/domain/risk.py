from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, localcontext

from wallet_vitals.domain.models import (
    EvidenceReceipt,
    EvidenceSnapshot,
    RiskDelta,
    RiskSeverity,
    StressScenario,
)

RAY = 10**27
SECONDS_PER_YEAR = 365 * 24 * 60 * 60
RULES_VERSION = "aave-v2-pinned-oracle"
MONEY_QUANTUM = Decimal("0.01")
HF_QUANTUM = Decimal("0.0001")


def ray_mul(a: int, b: int) -> int:
    if a < 0 or b < 0:
        raise ValueError("ray values must be non-negative")
    return (a * b + RAY // 2) // RAY


def calculate_linear_interest(rate: int, elapsed_seconds: int) -> int:
    if rate < 0 or elapsed_seconds < 0:
        raise ValueError("rate and elapsed seconds must be non-negative")
    return RAY + (rate * elapsed_seconds) // SECONDS_PER_YEAR


def calculate_compounded_interest(rate: int, elapsed_seconds: int) -> int:
    """Aave V3's third-order binomial approximation in ray precision."""
    if rate < 0 or elapsed_seconds < 0:
        raise ValueError("rate and elapsed seconds must be non-negative")
    if elapsed_seconds == 0:
        return RAY

    exp = elapsed_seconds
    exp_minus_one = exp - 1
    exp_minus_two = max(exp - 2, 0)
    rate_per_second = rate // SECONDS_PER_YEAR
    base_power_two = ray_mul(rate_per_second, rate_per_second)
    base_power_three = ray_mul(base_power_two, rate_per_second)
    second_term = exp * exp_minus_one * base_power_two // 2
    third_term = exp * exp_minus_one * exp_minus_two * base_power_three // 6
    return RAY + rate_per_second * exp + second_term + third_term


def normalized_income(liquidity_index: int, liquidity_rate: int, elapsed_seconds: int) -> int:
    return ray_mul(calculate_linear_interest(liquidity_rate, elapsed_seconds), liquidity_index)


def normalized_variable_debt(
    variable_borrow_index: int, variable_borrow_rate: int, elapsed_seconds: int
) -> int:
    return ray_mul(
        calculate_compounded_interest(variable_borrow_rate, elapsed_seconds),
        variable_borrow_index,
    )


def accrue_scaled_balance(scaled_balance: int, normalized_index: int) -> int:
    return ray_mul(scaled_balance, normalized_index)


def accrue_stable_debt(principal: int, stable_rate: int, elapsed_seconds: int) -> int:
    return ray_mul(principal, calculate_compounded_interest(stable_rate, elapsed_seconds))


@dataclass(frozen=True)
class RiskCalculation:
    total_collateral_usd: Decimal
    total_debt_usd: Decimal
    liquidation_weighted_collateral_usd: Decimal
    health_factor: Decimal | None
    severity: RiskSeverity


def severity_for(health_factor: Decimal | None, total_debt_usd: Decimal) -> RiskSeverity:
    if total_debt_usd == 0:
        return "no_debt"
    if health_factor is None or health_factor <= Decimal("1"):
        return "liquidatable"
    if health_factor <= Decimal("1.10"):
        return "danger"
    if health_factor <= Decimal("1.25"):
        return "warning"
    return "healthy"


def calculate_snapshot_risk(
    snapshot: EvidenceSnapshot, collateral_multiplier: Decimal = Decimal("1")
) -> RiskCalculation:
    if collateral_multiplier < 0:
        raise ValueError("collateral multiplier must be non-negative")

    collateral = Decimal(0)
    debt = Decimal(0)
    weighted = Decimal(0)
    with localcontext() as context:
        context.prec = 50
        for asset in snapshot.assets:
            debt += asset.debt_usd
            if asset.collateral_enabled:
                shocked = asset.supply_usd * collateral_multiplier
                collateral += shocked
                weighted += shocked * Decimal(asset.liquidation_threshold_bps) / Decimal(10_000)

        health_factor = None if debt == 0 else weighted / debt

    return RiskCalculation(
        total_collateral_usd=collateral.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP),
        total_debt_usd=debt.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP),
        liquidation_weighted_collateral_usd=weighted.quantize(
            MONEY_QUANTUM, rounding=ROUND_HALF_UP
        ),
        health_factor=(
            health_factor.quantize(HF_QUANTUM, rounding=ROUND_HALF_UP)
            if health_factor is not None
            else None
        ),
        severity=severity_for(health_factor, debt),
    )


def liquidation_buffer_pct(calculation: RiskCalculation) -> Decimal | None:
    if calculation.health_factor is None or calculation.health_factor <= 1:
        return None
    with localcontext() as context:
        context.prec = 50
        value = (Decimal(1) - Decimal(1) / calculation.health_factor) * Decimal(100)
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def build_stress_ladder(snapshot: EvidenceSnapshot) -> list[StressScenario]:
    scenarios: list[StressScenario] = []
    for shock in (5, 10, 20):
        calculation = calculate_snapshot_risk(snapshot, Decimal(100 - shock) / Decimal(100))
        scenarios.append(
            StressScenario(
                collateral_shock_pct=-shock,
                health_factor=calculation.health_factor,
                severity=calculation.severity,
            )
        )
    return scenarios


def compare_snapshots(current: EvidenceSnapshot, previous: EvidenceSnapshot | None) -> RiskDelta:
    if previous is None:
        return RiskDelta(
            status="no_baseline",
            current_block_number=current.source.block_number,
        )

    comparable = (
        previous.address == current.address
        and previous.source.network == current.source.network
        and previous.source.subgraph_id == current.source.subgraph_id
        and previous.source.deployment == current.source.deployment
        and previous.source.rules_version == current.source.rules_version
        and bool(previous.onchain_evidence) == bool(current.onchain_evidence)
        and previous.source.block_number < current.source.block_number
    )
    if not comparable:
        return RiskDelta(
            status="incomparable",
            previous_block_number=previous.source.block_number,
            current_block_number=current.source.block_number,
        )

    before = calculate_snapshot_risk(previous)
    after = calculate_snapshot_risk(current)
    hf_change = None
    if before.health_factor is not None and after.health_factor is not None:
        hf_change = (after.health_factor - before.health_factor).quantize(HF_QUANTUM)

    return RiskDelta(
        status="comparable",
        previous_block_number=previous.source.block_number,
        current_block_number=current.source.block_number,
        collateral_usd_change=(after.total_collateral_usd - before.total_collateral_usd).quantize(
            MONEY_QUANTUM
        ),
        debt_usd_change=(after.total_debt_usd - before.total_debt_usd).quantize(MONEY_QUANTUM),
        health_factor_change=hf_change,
    )


def build_evidence_receipt(snapshot: EvidenceSnapshot) -> EvidenceReceipt:
    return EvidenceReceipt(
        provider=snapshot.source.provider,
        subgraph_id=snapshot.source.subgraph_id,
        deployment=snapshot.source.deployment,
        network=snapshot.source.network,
        block_number=snapshot.source.block_number,
        block_timestamp=snapshot.source.block_timestamp,
        queried_at=snapshot.source.queried_at,
        rules_version=snapshot.source.rules_version,
        onchain_evidence=snapshot.onchain_evidence,
        scenario_assumptions=[
            "All enabled collateral USD prices move by the same percentage.",
            "Debt USD value remains constant.",
            "Liquidation thresholds and protocol parameters remain at the evidence snapshot.",
            "Scenarios are sensitivity tests, not forecasts or safety guarantees.",
        ],
        evidence_refs=[asset.evidence_ref for asset in snapshot.assets],
    )
