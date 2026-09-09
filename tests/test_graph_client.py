from __future__ import annotations

import httpx
import pytest

from wallet_vitals.graph.client import GraphClient


@pytest.mark.asyncio
async def test_graph_client_keeps_key_out_of_url_and_parses_data() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": {"ok": True}})

    client = GraphClient(
        "https://example.test/subgraphs/id/abc",
        "secret-key",
        transport=httpx.MockTransport(handler),
    )

    data = await client.query("query { ok }", {})
    await client.close()

    assert data == {"ok": True}
    assert str(requests[0].url) == "https://example.test/subgraphs/id/abc"
    assert "secret-key" not in str(requests[0].url)
    assert requests[0].headers["Authorization"] == "Bearer secret-key"
