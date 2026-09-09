from __future__ import annotations

import asyncio
from typing import Any

import httpx

from wallet_vitals.graph.errors import (
    GraphConfigurationError,
    GraphResponseError,
    GraphTransportError,
)


class GraphClient:
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        timeout_seconds: float = 15.0,
        max_attempts: int = 3,
    ) -> None:
        if not api_key.strip():
            raise GraphConfigurationError("GRAPH_API_KEY is required to query the Aave subgraph.")
        self._client = httpx.AsyncClient(
            base_url=endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "User-Agent": "wallet-vitals/0.1",
            },
            timeout=timeout_seconds,
        )
        self._max_attempts = max_attempts

    async def close(self) -> None:
        await self._client.aclose()

    async def query(self, document: str, variables: dict[str, Any]) -> dict[str, Any]:
        response: httpx.Response | None = None
        for attempt in range(self._max_attempts):
            try:
                response = await self._client.post(
                    "",
                    json={"query": document, "variables": variables},
                )
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status not in {429, 502, 503, 504} or attempt + 1 == self._max_attempts:
                    raise GraphTransportError(f"The Graph gateway returned HTTP {status}.") from exc
                retry_after = exc.response.headers.get("Retry-After")
                try:
                    delay = min(float(retry_after), 3.0) if retry_after else 0.25 * (2**attempt)
                except ValueError:
                    delay = 0.25 * (2**attempt)
                await asyncio.sleep(delay)
            except httpx.HTTPError as exc:
                if attempt + 1 == self._max_attempts:
                    raise GraphTransportError("The Graph gateway could not be reached.") from exc
                await asyncio.sleep(0.25 * (2**attempt))

        if response is None:
            raise GraphTransportError("The Graph gateway could not be reached.")

        try:
            payload = response.json()
        except ValueError as exc:
            raise GraphResponseError("The Graph gateway returned invalid JSON.") from exc

        if not isinstance(payload, dict):
            raise GraphResponseError("The Graph gateway returned an unexpected response.")
        errors = payload.get("errors")
        if errors:
            messages = [
                str(item.get("message", "unknown GraphQL error"))
                for item in errors[:3]
                if isinstance(item, dict)
            ]
            raise GraphResponseError("; ".join(messages) or "The Graph query failed.")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise GraphResponseError("The Graph response did not contain data.")
        return data
