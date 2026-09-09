import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from eth_utils import keccak

from wallet_vitals.graph.oracle import SELECTORS
from wallet_vitals.storage.d1 import D1Store


class Statement:
    def __init__(self, db, sql):
        self.db, self.sql, self.args = db, sql, ()

    def bind(self, *args):
        self.args = args
        return self

    async def run(self):
        return self.db.execute(self.sql, self.args)

    async def first(self, column):
        row = self.db.execute(self.sql, self.args).fetchone()
        return row[column] if row is not None else None


class Binding:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript((Path(__file__).parents[1] / "cloudflare/schema.sql").read_text())

    def prepare(self, sql):
        return Statement(self.db, sql)


def test_worker_abi_selectors_match_keccak():
    for signature, selector in SELECTORS.items():
        assert keccak(text=signature)[:4].hex() == selector


@pytest.mark.asyncio
async def test_d1_budget_is_bounded_and_separates_windows():
    store = D1Store(Binding())
    assert await store.reserve_budget("test", 100, 2)
    assert await store.reserve_budget("test", 100, 2)
    assert not await store.reserve_budget("test", 100, 2)
    assert not await store.reserve_budget("test", 100, 2)
    assert await store.reserve_budget("test", 101, 2)


@pytest.mark.asyncio
async def test_d1_snapshot_roundtrip_and_pruning(evidence_snapshot):
    store = D1Store(Binding())
    evidence_snapshot.source.queried_at = datetime.now(UTC)
    await store.save_snapshot(evidence_snapshot)
    current = evidence_snapshot.model_copy(deep=True)
    current.source.block_number += 1
    assert await store.latest_snapshot_before(current) == evidence_snapshot
    assert await store.latest_snapshot_before(evidence_snapshot) is None
    evidence_snapshot.source.queried_at -= timedelta(days=8)
    await store.save_snapshot(evidence_snapshot)
    await store.prune()
    assert await store.latest_snapshot_before(current) is None


@pytest.mark.asyncio
async def test_d1_expired_report_and_explanation_are_not_served():
    binding = Binding()
    store = D1Store(binding)
    yesterday = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    binding.db.execute(
        "INSERT INTO reports VALUES(?,?,?,?,?)", ("old", "a", yesterday, yesterday, "{}")
    )
    binding.db.execute(
        "INSERT INTO explanations VALUES(?,?,?,?)", ("old", "summary", yesterday, "{}")
    )
    assert await store.get_report("old") is None
    assert await store.get_explanation("old", "summary") is None
    await store.prune()
    assert binding.db.execute("SELECT count(*) FROM reports").fetchone()[0] == 0
