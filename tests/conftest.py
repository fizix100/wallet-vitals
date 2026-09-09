from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from wallet_vitals.domain.models import EvidenceSnapshot, PositionAsset, SourceMetadata
from wallet_vitals.domain.risk import RULES_VERSION


@pytest.fixture
def evidence_snapshot() -> EvidenceSnapshot:
    timestamp = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    return EvidenceSnapshot(
        address="0x1111111111111111111111111111111111111111",
        source=SourceMetadata(
            rules_version=RULES_VERSION,
            subgraph_id="test-subgraph",
            deployment="test-deployment",
            block_number=100,
            block_timestamp=timestamp,
            queried_at=timestamp,
        ),
        assets=[
            PositionAsset(
                address="0x2222222222222222222222222222222222222222",
                symbol="WETH",
                decimals=18,
                supply=Decimal("1"),
                debt=Decimal("0"),
                price_usd=Decimal("2000"),
                supply_usd=Decimal("2000"),
                debt_usd=Decimal("0"),
                liquidation_threshold_bps=8000,
                collateral_enabled=True,
                evidence_ref="aave-v3:user-reserve:collateral",
            ),
            PositionAsset(
                address="0x3333333333333333333333333333333333333333",
                symbol="USDC",
                decimals=6,
                supply=Decimal("0"),
                debt=Decimal("1000"),
                price_usd=Decimal("1"),
                supply_usd=Decimal("0"),
                debt_usd=Decimal("1000"),
                liquidation_threshold_bps=0,
                collateral_enabled=False,
                evidence_ref="aave-v3:user-reserve:debt",
            ),
        ],
    )
