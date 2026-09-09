from __future__ import annotations

from decimal import Decimal

import pytest

from wallet_vitals.ai.narrator import RiskNarrator
from wallet_vitals.application.service import (
    AnalysisService,
    InvalidAddressError,
    ReportNotFoundError,
)
from wallet_vitals.domain.models import EvidenceSnapshot
from wallet_vitals.storage.sqlite import SQLiteStore


class FakeSubgraph:
    def __init__(self, snapshot: EvidenceSnapshot) -> None:
        self.snapshot = snapshot

    async def fetch_snapshot(self, address: str) -> EvidenceSnapshot:
        result = self.snapshot.model_copy(deep=True)
        result.address = address
        return result


@pytest.mark.asyncio
async def test_service_builds_report_and_comparable_delta(
    tmp_path, evidence_snapshot: EvidenceSnapshot
) -> None:
    store = SQLiteStore(tmp_path / "service.db")
    await store.initialize()
    subgraph = FakeSubgraph(evidence_snapshot)
    service = AnalysisService(
        subgraph,  # type: ignore[arg-type]
        store,
        RiskNarrator(None, "unused"),
        address_cooldown_seconds=0,
    )

    first = await service.analyze(evidence_snapshot.address)
    subgraph.snapshot.source.block_number = 101
    subgraph.snapshot.assets[1].debt_usd = Decimal("1100")
    second = await service.analyze(evidence_snapshot.address.upper().replace("0X", "0x"))

    assert first.risk_delta.status == "no_baseline"
    assert first.narrative_mode == "deterministic"
    assert second.risk_delta.status == "comparable"
    assert second.risk_delta.debt_usd_change == Decimal("100.00")
    assert await service.get_report(first.report_id) == first


def test_service_rejects_non_address(evidence_snapshot: EvidenceSnapshot, tmp_path) -> None:
    service = AnalysisService(
        FakeSubgraph(evidence_snapshot),  # type: ignore[arg-type]
        SQLiteStore(tmp_path / "unused.db"),
        RiskNarrator(None, "unused"),
    )

    with pytest.raises(InvalidAddressError):
        service.normalize_address("vitalik.eth")


@pytest.mark.asyncio
async def test_retired_price_rules_cannot_be_served_or_explained(tmp_path, evidence_snapshot):
    store = SQLiteStore(tmp_path / "retired.db")
    await store.initialize()
    service = AnalysisService(FakeSubgraph(evidence_snapshot), store, RiskNarrator(None, "unused"))
    report = await service.analyze(evidence_snapshot.address)
    report.evidence_receipt.rules_version = "aave-v1"
    await store.save_report(report)
    with pytest.raises(ReportNotFoundError, match="retired evidence"):
        await service.get_report(report.report_id)
    with pytest.raises(ReportNotFoundError, match="retired evidence"):
        await service.explain(report.report_id, "what_changed")
