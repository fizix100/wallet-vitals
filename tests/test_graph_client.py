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

    client = GraphClient("https://example.test/subgraphs/id/abc", "secret-key")
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url="https://example.test/subgraphs/id/abc",
        headers={"Authorization": "Bearer secret-key"},
        transport=httpx.MockTransport(handler),
    )

    data = await client.query("query { ok }", {})
    await client.close()

    assert data == {"ok": True}
    assert "secret-key" not in str(requests[0].url)
    assert requests[0].headers["Authorization"] == "Bearer secret-key"
