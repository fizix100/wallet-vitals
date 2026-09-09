from __future__ import annotations

import asyncio
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from wallet_vitals.ai.narrator import RiskNarrator
from wallet_vitals.domain.models import ExplainResponse, RiskReport
from wallet_vitals.domain.risk import (
    RULES_VERSION,
    build_evidence_receipt,
    build_stress_ladder,
    calculate_snapshot_risk,
    compare_snapshots,
    liquidation_buffer_pct,
)
from wallet_vitals.graph.aave import AaveV3Subgraph
from wallet_vitals.graph.errors import GraphConfigurationError

if TYPE_CHECKING:
    from wallet_vitals.storage.sqlite import SQLiteStore


class InvalidAddressError(ValueError):
    pass


class AnalysisCooldownError(RuntimeError):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("Please wait before analyzing this address again.")
        self.retry_after_seconds = retry_after_seconds


class ReportNotFoundError(LookupError):
    pass


class AnalysisService:
    def __init__(
        self,
        subgraph: AaveV3Subgraph | None,
        store: SQLiteStore,
        narrator: RiskNarrator,
        report_ttl_hours: int = 24,
        address_cooldown_seconds: int = 10,
        max_concurrent_analyses: int = 4,
    ) -> None:
        self._subgraph = subgraph
        self._store = store
        self._narrator = narrator
        self._report_ttl_hours = report_ttl_hours
        self._cooldown = address_cooldown_seconds
        self._semaphore = asyncio.Semaphore(max_concurrent_analyses)
        self._last_request: dict[str, float] = {}
        self._cooldown_lock = asyncio.Lock()

    @staticmethod
    def normalize_address(address: str) -> str:
        candidate = address.strip()
        if not re.fullmatch(r"0x[0-9a-fA-F]{40}", candidate):
            raise InvalidAddressError("Enter a valid 20-byte Ethereum address.")
        return candidate.lower()

    async def analyze(self, raw_address: str) -> RiskReport:
        address = self.normalize_address(raw_address)
        if self._subgraph is None:
            raise GraphConfigurationError("GRAPH_API_KEY is not configured on this deployment.")
        await self._enforce_cooldown(address)
        async with self._semaphore:
            snapshot = await self._subgraph.fetch_snapshot(address)
            previous = await self._store.latest_snapshot_before(snapshot)
            calculation = calculate_snapshot_risk(snapshot)
            delta = compare_snapshots(snapshot, previous)
            stress_ladder = build_stress_ladder(snapshot)
            await self._store.save_snapshot(snapshot)

            created_at = datetime.now(UTC)
            facts = self._facts(
                snapshot.source.block_number,
                snapshot.source.deployment,
                calculation.health_factor,
                calculation.severity,
                liquidation_buffer_pct(calculation),
                calculation.total_collateral_usd,
                calculation.total_debt_usd,
                stress_ladder,
                delta,
                [asset.evidence_ref for asset in snapshot.assets],
            )
            narrative, narrative_mode = await self._narrator.report_summary(facts)
            report = RiskReport(
                report_id=secrets.token_urlsafe(18),
                address=address,
                created_at=created_at,
                expires_at=created_at + timedelta(hours=self._report_ttl_hours),
                total_collateral_usd=calculation.total_collateral_usd,
                total_debt_usd=calculation.total_debt_usd,
                liquidation_weighted_collateral_usd=(
                    calculation.liquidation_weighted_collateral_usd
                ),
                health_factor=calculation.health_factor,
                severity=calculation.severity,
                liquidation_buffer_pct=liquidation_buffer_pct(calculation),
                stress_ladder=stress_ladder,
                risk_delta=delta,
                assets=snapshot.assets,
                evidence_receipt=build_evidence_receipt(snapshot),
                narrative=narrative,
                narrative_mode=narrative_mode,
                warnings=snapshot.warnings,
            )
            await self._store.save_report(report)
            return report

    async def get_report(self, report_id: str) -> RiskReport:
        if len(report_id) > 64 or not report_id:
            raise ReportNotFoundError("Report not found or expired.")
        report = await self._store.get_report(report_id)
        if report is None:
            raise ReportNotFoundError("Report not found or expired.")
        if report.evidence_receipt.rules_version != RULES_VERSION:
            raise ReportNotFoundError("This report used retired evidence rules. Run a fresh check.")
        return report

    async def explain(self, report_id: str, intent: str) -> ExplainResponse:
        report = await self.get_report(report_id)
        facts = self._facts_from_report(report)
        answer, mode = await self._narrator.explain(facts, intent)
        return ExplainResponse(report_id=report_id, intent=intent, answer=answer, mode=mode)

    async def _enforce_cooldown(self, address: str) -> None:
        if self._cooldown == 0:
            return
        loop = asyncio.get_running_loop()
        now = loop.time()
        async with self._cooldown_lock:
            last = self._last_request.get(address)
            if last is not None and now - last < self._cooldown:
                remaining = max(1, int(self._cooldown - (now - last) + 0.999))
                raise AnalysisCooldownError(remaining)
            self._last_request[address] = now

    @staticmethod
    def _facts(
        block_number: int,
        deployment: str,
        health_factor: Any,
        severity: str,
        buffer: Any,
        collateral: Any,
        debt: Any,
        stress_ladder: Any,
        delta: Any,
        evidence_refs: list[str],
    ) -> dict[str, Any]:
        return {
            "block_number": block_number,
            "deployment": deployment,
            "health_factor": str(health_factor) if health_factor is not None else None,
            "severity": severity,
            "liquidation_buffer_pct": str(buffer) if buffer is not None else None,
            "total_collateral_usd": str(collateral),
            "total_debt_usd": str(debt),
            "stress_ladder": [item.model_dump(mode="json") for item in stress_ladder],
            "risk_delta": delta.model_dump(mode="json"),
            "evidence_refs": evidence_refs,
        }

    @classmethod
    def _facts_from_report(cls, report: RiskReport) -> dict[str, Any]:
        return cls._facts(
            report.evidence_receipt.block_number,
            report.evidence_receipt.deployment,
            report.health_factor,
            report.severity,
            report.liquidation_buffer_pct,
            report.total_collateral_usd,
            report.total_debt_usd,
            report.stress_ladder,
            report.risk_delta,
            report.evidence_receipt.evidence_refs,
        )
