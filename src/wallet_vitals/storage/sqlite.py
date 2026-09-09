from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from wallet_vitals.domain.models import EvidenceSnapshot, RiskReport


class SQLiteStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    async def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._path) as database:
            await database.executescript(
                """
                PRAGMA journal_mode = WAL;
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS snapshots (
                    address TEXT NOT NULL,
                    deployment TEXT NOT NULL,
                    block_number INTEGER NOT NULL,
                    queried_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (address, deployment, block_number)
                );

                CREATE INDEX IF NOT EXISTS snapshots_address_block
                    ON snapshots(address, block_number DESC);

                CREATE TABLE IF NOT EXISTS reports (
                    report_id TEXT PRIMARY KEY,
                    address TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS reports_expiry ON reports(expires_at);
                """
            )
            await database.commit()

    async def save_snapshot(self, snapshot: EvidenceSnapshot) -> None:
        async with aiosqlite.connect(self._path) as database:
            await database.execute(
                """
                INSERT OR REPLACE INTO snapshots
                    (address, deployment, block_number, queried_at, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot.address,
                    snapshot.source.deployment,
                    snapshot.source.block_number,
                    snapshot.source.queried_at.isoformat(),
                    snapshot.model_dump_json(),
                ),
            )
            await database.commit()

    async def latest_snapshot_before(self, snapshot: EvidenceSnapshot) -> EvidenceSnapshot | None:
        async with aiosqlite.connect(self._path) as database:
            cursor = await database.execute(
                """
                SELECT payload
                FROM snapshots
                WHERE address = ? AND deployment = ? AND block_number < ?
                ORDER BY block_number DESC
                LIMIT 1
                """,
                (
                    snapshot.address,
                    snapshot.source.deployment,
                    snapshot.source.block_number,
                ),
            )
            row = await cursor.fetchone()
        return EvidenceSnapshot.model_validate_json(row[0]) if row else None

    async def save_report(self, report: RiskReport) -> None:
        async with aiosqlite.connect(self._path) as database:
            await database.execute(
                """
                INSERT OR REPLACE INTO reports
                    (report_id, address, created_at, expires_at, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    report.report_id,
                    report.address,
                    report.created_at.isoformat(),
                    report.expires_at.isoformat(),
                    report.model_dump_json(),
                ),
            )
            await database.commit()

    async def get_report(self, report_id: str) -> RiskReport | None:
        async with aiosqlite.connect(self._path) as database:
            cursor = await database.execute(
                "SELECT payload FROM reports WHERE report_id = ? AND expires_at > ?",
                (report_id, datetime.now(UTC).isoformat()),
            )
            row = await cursor.fetchone()
        return RiskReport.model_validate_json(row[0]) if row else None

    async def delete_expired_reports(self) -> int:
        async with aiosqlite.connect(self._path) as database:
            cursor = await database.execute(
                "DELETE FROM reports WHERE expires_at <= ?",
                (datetime.now(UTC).isoformat(),),
            )
            await database.commit()
            return cursor.rowcount
