from __future__ import annotations

from datetime import timedelta

import pytest

from wallet_vitals.domain.models import EvidenceSnapshot
from wallet_vitals.storage.sqlite import SQLiteStore


@pytest.mark.asyncio
async def test_snapshot_round_trip(tmp_path, evidence_snapshot: EvidenceSnapshot) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    await store.initialize()
    await store.save_snapshot(evidence_snapshot)

    current = evidence_snapshot.model_copy(deep=True)
    current.source.block_number += 1
    previous = await store.latest_snapshot_before(current)

    assert previous == evidence_snapshot


@pytest.mark.asyncio
async def test_same_block_is_idempotent(tmp_path, evidence_snapshot: EvidenceSnapshot) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    await store.initialize()
    await store.save_snapshot(evidence_snapshot)
    changed = evidence_snapshot.model_copy(deep=True)
    changed.source.queried_at += timedelta(seconds=1)
    await store.save_snapshot(changed)

    later = changed.model_copy(deep=True)
    later.source.block_number += 1
    assert await store.latest_snapshot_before(later) == changed
