from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from wallet_vitals.domain.risk import RAY
from wallet_vitals.graph.aave import AaveV3Subgraph
from wallet_vitals.graph.errors import GraphIndexingError, GraphStaleDataError


class FakeGraphClient:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.variables: dict[str, Any] | None = None

    async def query(self, document: str, variables: dict[str, Any]) -> dict[str, Any]:
        assert "WalletVitalsAaveUser" in document
        self.variables = variables
        return self.payload


def graph_payload(timestamp: int) -> dict[str, Any]:
    return {
        "_meta": {
            "deployment": "QmDeployment",
            "hasIndexingErrors": False,
            "block": {"number": 12345, "timestamp": timestamp, "hash": "0xabc"},
        },
        "user": {
            "id": "0x1111111111111111111111111111111111111111",
            "eModeCategoryId": None,
            "reserves": [
                {
                    "id": "position-1",
                    "usageAsCollateralEnabledOnUser": True,
                    "scaledATokenBalance": 10**18,
                    "scaledVariableDebt": 500 * 10**6,
                    "principalStableDebt": 0,
                    "stableBorrowRate": 0,
                    "stableBorrowLastUpdateTimestamp": timestamp,
                    "reserve": {
                        "id": "reserve-1",
                        "underlyingAsset": "0x2222222222222222222222222222222222222222",
                        "symbol": "TEST",
                        "decimals": 18,
                        "reserveLiquidationThreshold": 8000,
                        "liquidityRate": 0,
                        "variableBorrowRate": 0,
                        "liquidityIndex": RAY,
                        "variableBorrowIndex": RAY,
                        "lastUpdateTimestamp": timestamp,
                        "eMode": None,
                        "price": {
                            "priceInEth": 2000 * 10**8,
                            "lastUpdateTimestamp": timestamp,
                            "oracle": {
                                "baseCurrency": "USD",
                                "baseCurrencyUnit": 10**8,
                            },
                        },
                    },
                }
            ],
        },
    }


@pytest.mark.asyncio
async def test_subgraph_normalizes_snapshot_and_address() -> None:
    timestamp = int(datetime.now(UTC).timestamp())
    client = FakeGraphClient(graph_payload(timestamp))
    adapter = AaveV3Subgraph(client, "subgraph-id", max_block_age_seconds=900)  # type: ignore[arg-type]

    snapshot = await adapter.fetch_snapshot("0xAbCd111111111111111111111111111111111111")

    assert client.variables == {"address": "0xabcd111111111111111111111111111111111111"}
    assert snapshot.source.block_number == 12345
    assert snapshot.source.deployment == "QmDeployment"
    assert snapshot.assets[0].supply == 1
    assert snapshot.assets[0].price_usd == 2000


@pytest.mark.asyncio
async def test_subgraph_rejects_stale_or_broken_index() -> None:
    stale_timestamp = int(datetime.now(UTC).timestamp()) - 901
    client = FakeGraphClient(graph_payload(stale_timestamp))
    adapter = AaveV3Subgraph(client, "subgraph-id", max_block_age_seconds=900)  # type: ignore[arg-type]
    with pytest.raises(GraphStaleDataError):
        await adapter.fetch_snapshot("0x1111111111111111111111111111111111111111")

    payload = graph_payload(int(datetime.now(UTC).timestamp()))
    payload["_meta"]["hasIndexingErrors"] = True
    adapter = AaveV3Subgraph(FakeGraphClient(payload), "subgraph-id")  # type: ignore[arg-type]
    with pytest.raises(GraphIndexingError):
        await adapter.fetch_snapshot("0x1111111111111111111111111111111111111111")
