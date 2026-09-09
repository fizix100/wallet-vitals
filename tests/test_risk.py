from __future__ import annotations

from decimal import Decimal

from wallet_vitals.domain.models import EvidenceSnapshot
from wallet_vitals.domain.risk import (
    RAY,
    build_stress_ladder,
    calculate_compounded_interest,
    calculate_linear_interest,
    calculate_snapshot_risk,
    compare_snapshots,
    liquidation_buffer_pct,
    ray_mul,
)


def test_ray_math_identity() -> None:
    assert ray_mul(3 * RAY, 2 * RAY) == 6 * RAY
    assert calculate_linear_interest(0, 999) == RAY
    assert calculate_compounded_interest(0, 999) == RAY


def test_risk_uses_liquidation_weighted_collateral(
    evidence_snapshot: EvidenceSnapshot,
) -> None:
    result = calculate_snapshot_risk(evidence_snapshot)

    assert result.total_collateral_usd == Decimal("2000.00")
    assert result.total_debt_usd == Decimal("1000.00")
    assert result.liquidation_weighted_collateral_usd == Decimal("1600.00")
    assert result.health_factor == Decimal("1.6000")
    assert result.severity == "healthy"
    assert liquidation_buffer_pct(result) == Decimal("37.50")


def test_stress_ladder_is_monotonic(evidence_snapshot: EvidenceSnapshot) -> None:
    ladder = build_stress_ladder(evidence_snapshot)

    assert [item.collateral_shock_pct for item in ladder] == [-5, -10, -20]
    assert [item.health_factor for item in ladder] == [
        Decimal("1.5200"),
        Decimal("1.4400"),
        Decimal("1.2800"),
    ]


def test_delta_requires_later_comparable_block(evidence_snapshot: EvidenceSnapshot) -> None:
    first = compare_snapshots(evidence_snapshot, None)
    same_block = compare_snapshots(evidence_snapshot, evidence_snapshot)
    current = evidence_snapshot.model_copy(deep=True)
    current.source.block_number = 101
    current.assets[1].debt_usd = Decimal("1100")
    delta = compare_snapshots(current, evidence_snapshot)

    assert first.status == "no_baseline"
    assert same_block.status == "incomparable"
    assert delta.status == "comparable"
    assert delta.debt_usd_change == Decimal("100.00")
    assert delta.health_factor_change == Decimal("-0.1455")
