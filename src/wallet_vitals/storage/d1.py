"""Persistent report storage through a Cloudflare D1 binding; no local filesystem."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from wallet_vitals.domain.models import EvidenceSnapshot, RiskReport


class D1Store:
    def __init__(self, binding: Any) -> None:
        self._db = binding

    async def save_snapshot(self, snapshot: EvidenceSnapshot) -> None:
        await (
            self._db.prepare(
                "INSERT OR REPLACE INTO snapshots "
                "(address,deployment,block_number,queried_at,payload) VALUES (?,?,?,?,?)"
            )
            .bind(
                snapshot.address,
                snapshot.source.deployment,
                snapshot.source.block_number,
                snapshot.source.queried_at.isoformat(),
                snapshot.model_dump_json(),
            )
            .run()
        )

    async def latest_snapshot_before(self, snapshot: EvidenceSnapshot) -> EvidenceSnapshot | None:
        payload = (
            await self._db.prepare(
                "SELECT payload FROM snapshots WHERE address=? AND deployment=? AND block_number<? "
                "ORDER BY block_number DESC LIMIT 1"
            )
            .bind(snapshot.address, snapshot.source.deployment, snapshot.source.block_number)
            .first("payload")
        )
        return EvidenceSnapshot.model_validate_json(payload) if payload else None

    async def save_report(self, report: RiskReport) -> None:
        await (
            self._db.prepare(
                "INSERT OR REPLACE INTO reports "
                "(report_id,address,created_at,expires_at,payload) VALUES (?,?,?,?,?)"
            )
            .bind(
                report.report_id,
                report.address,
                report.created_at.isoformat(),
                report.expires_at.isoformat(),
                report.model_dump_json(),
            )
            .run()
        )

    async def get_report(self, report_id: str) -> RiskReport | None:
        payload = (
            await self._db.prepare("SELECT payload FROM reports WHERE report_id=? AND expires_at>?")
            .bind(report_id, datetime.now(UTC).isoformat())
            .first("payload")
        )
        return RiskReport.model_validate_json(payload) if payload else None

    async def reserve_budget(self, bucket: str, window: int, limit: int) -> bool:
        result = (
            await self._db.prepare(
                "INSERT INTO quotas(bucket,window,count) VALUES(?,?,1) "
                "ON CONFLICT(bucket,window) DO UPDATE SET count=count+1 "
                "WHERE count<? RETURNING count"
            )
            .bind(bucket, window, limit)
            .first("count")
        )
        return result is not None

    async def get_explanation(self, report_id: str, intent: str) -> str | None:
        return (
            await self._db.prepare(
                "SELECT payload FROM explanations WHERE report_id=? AND intent=? AND expires_at>?"
            )
            .bind(report_id, intent, datetime.now(UTC).isoformat())
            .first("payload")
        )

    async def save_explanation(self, report: RiskReport, intent: str, payload: str) -> None:
        await (
            self._db.prepare(
                "INSERT OR REPLACE INTO explanations(report_id,intent,expires_at,payload) "
                "VALUES(?,?,?,?)"
            )
            .bind(report.report_id, intent, report.expires_at.isoformat(), payload)
            .run()
        )

    async def prune(self) -> None:
        now = datetime.now(UTC)
        await (
            self._db.prepare("DELETE FROM reports WHERE expires_at<=?").bind(now.isoformat()).run()
        )
        await (
            self._db.prepare("DELETE FROM explanations WHERE expires_at<=?")
            .bind(now.isoformat())
            .run()
        )
        await (
            self._db.prepare("DELETE FROM snapshots WHERE queried_at<?")
            .bind((now - timedelta(days=7)).isoformat())
            .run()
        )
        await (
            self._db.prepare("DELETE FROM quotas WHERE window<?")
            .bind(int(now.timestamp()) - 172800)
            .run()
        )
