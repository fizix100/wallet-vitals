"""Native Python Worker; the deterministic core is shared with the local app."""

from __future__ import annotations

import asyncio
import hashlib
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from jinja2 import Environment, select_autoescape
from workers import Response as WorkerResponse
from workers import fetch

from wallet_vitals.ai.narrator import RiskNarrator
from wallet_vitals.application.service import (
    AnalysisService,
    InvalidAddressError,
    ReportNotFoundError,
)
from wallet_vitals.domain.models import AnalyzeRequest, ExplainRequest, ExplainResponse, RiskReport
from wallet_vitals.graph.aave import AaveV3Subgraph
from wallet_vitals.graph.client import GraphClient
from wallet_vitals.graph.errors import GraphError
from wallet_vitals.graph.oracle import AaveOracleClient
from wallet_vitals.storage.d1 import D1Store

BASE_PATH = "/wallet-vitals"
app = FastAPI(title="Wallet Vitals", root_path=BASE_PATH, docs_url=None, redoc_url=None)
templates = Environment(autoescape=select_autoescape(default_for_string=True))


class WorkerTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        # Worker fetch replaces socket I/O; httpx still supplies the same request/response API.
        timeout = request.extensions.get("timeout", {}).get("read") or 20
        try:
            async with asyncio.timeout(timeout):
                response = await fetch(
                    str(request.url),
                    method=request.method,
                    headers=dict(request.headers),
                    body=(await request.aread()).decode() or None,
                    redirect="manual",
                )
                content = await response.bytes()
            if response.status >= 400:
                print("Upstream HTTP error:", request.url.host, response.status)
            # Fetch already decodes compressed bodies. Do not ask httpx to decode them again.
            headers = {
                key: value
                for key, value in response.headers.items()
                if key.lower() not in {"content-encoding", "content-length"}
            }
            return httpx.Response(response.status, headers=headers, content=content)
        except TimeoutError as exc:
            raise httpx.ReadTimeout("Worker upstream timeout", request=request) from exc
        except Exception as exc:
            print("Upstream transport error:", request.url.host, type(exc).__name__)
            raise httpx.ConnectError("Worker upstream unavailable", request=request) from exc


def setting(env, name: str, default: str = "") -> str:
    value = getattr(env, name, None)
    return str(value) if value is not None else default


@asynccontextmanager
async def service(request: Request, needs_graph: bool = False):
    env = request.scope["env"]
    key = setting(env, "GRAPH_API_KEY")
    if needs_graph and not key:
        raise HTTPException(503, "The live data provider is not configured.")
    store = D1Store(env.DB)
    graph = (
        GraphClient(
            "https://gateway.thegraph.com/api/subgraphs/id/" + setting(env, "GRAPH_SUBGRAPH_ID"),
            key,
            timeout_seconds=18,
            transport=WorkerTransport(),
        )
        if key
        else None
    )
    oracle = AaveOracleClient(setting(env, "ETHEREUM_RPC_URL"), transport=WorkerTransport())
    narrator = RiskNarrator(
        setting(env, "OPENAI_API_KEY") or None,
        setting(env, "OPENAI_MODEL"),
        transport=WorkerTransport(),
    )
    adapter = (
        AaveV3Subgraph(graph, setting(env, "GRAPH_SUBGRAPH_ID"), oracle_client=oracle)
        if graph
        else None
    )
    try:
        yield AnalysisService(adapter, store, narrator, address_cooldown_seconds=0), store
    finally:
        if graph:
            await graph.close()
        await oracle.close()


async def budget(request: Request, store: D1Store, address: str | None = None):
    now = int(time.time())
    ip = request.headers.get("cf-connecting-ip", "unknown")
    digest = hashlib.sha256((ip + str(now // 86400)).encode()).hexdigest()[:24]
    if not await store.reserve_budget("ip:" + digest, now // 60 * 60, 6):
        raise HTTPException(429, "Please wait a minute before making another check.")
    if address and not await store.reserve_budget("address:" + address, now // 10 * 10, 1):
        raise HTTPException(429, "Please wait ten seconds before checking this address again.")
    limit = int(setting(request.scope["env"], "DAILY_REQUEST_LIMIT", "100"))
    if not await store.reserve_budget("global", now // 86400 * 86400, limit):
        raise HTTPException(
            429, "The public demo's daily query budget is used. Please try tomorrow."
        )


class SecurityMiddleware:
    """Pure ASGI avoids a needless streaming response across the Python/JS boundary."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request = Request(scope)
        if request.method == "POST":
            origin = request.headers.get("origin")
            if origin and origin != f"{request.url.scheme}://{request.url.netloc}":
                return await JSONResponse(
                    {"detail": "Cross-origin requests are not allowed."}, status_code=403
                )(scope, receive, send)
            messages, size = [], 0
            while True:
                message = await receive()
                messages.append(message)
                size += len(message.get("body", b""))
                if size > 2048:
                    return await JSONResponse({"detail": "Request too large."}, status_code=413)(
                        scope, receive, send
                    )
                if not message.get("more_body", False):
                    break
            original_receive = receive

            async def replay():
                return messages.pop(0) if messages else await original_receive()

            receive = replay

        started = False

        async def secure_send(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                message["headers"] = [
                    *message.get("headers", []),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"x-frame-options", b"DENY"),
                    (b"cache-control", b"no-store"),
                    (
                        b"content-security-policy",
                        (
                            b"default-src 'self'; script-src 'self'; style-src 'self'; "
                            b"img-src 'self' data:; connect-src 'self'; object-src 'none'; "
                            b"base-uri 'self'; frame-ancestors 'none'"
                        ),
                    ),
                ]
            await send(message)

        try:
            await self.app(scope, receive, secure_send)
        except Exception as exc:
            print("Wallet Vitals request failed:", type(exc).__name__)
            if started:
                raise
            await JSONResponse(
                {"detail": "Service temporarily unavailable. Please retry."}, status_code=503
            )(scope, receive, secure_send)


app.add_middleware(SecurityMiddleware)


async def homepage(request: Request, report_id: str = ""):
    env = request.scope["env"]
    raw_asset = await env.ASSETS.fetch("https://assets.local/index.html")
    asset = raw_asset if isinstance(raw_asset, WorkerResponse) else WorkerResponse(raw_asset)
    template = templates.from_string(await asset.text())
    return HTMLResponse(
        template.render(
            configured=bool(setting(env, "GRAPH_API_KEY")),
            initial_report_id=report_id[:64],
            base_path=BASE_PATH,
            url_for=lambda name, path: BASE_PATH + "/static/" + path.lstrip("/"),
        )
    )


@app.get("/")
async def home(request: Request):
    return await homepage(request)


@app.get("/reports/{report_id}")
async def report_page(report_id: str, request: Request):
    return await homepage(request, report_id)


@app.get("/static/{path:path}")
async def static(path: str, request: Request):
    if path not in {"app.js", "app.css", "favicon.svg"}:
        raise HTTPException(404)
    raw_asset = await request.scope["env"].ASSETS.fetch("https://assets.local/static/" + path)
    asset = raw_asset if isinstance(raw_asset, WorkerResponse) else WorkerResponse(raw_asset)
    return Response(
        await asset.bytes(),
        status_code=asset.status,
        media_type=asset.headers.get("content-type", "application/octet-stream"),
    )


@app.get("/health")
async def health(request: Request):
    env = request.scope["env"]
    return {
        "status": "ok",
        "runtime": "python-workers",
        "storage": "d1",
        "graph_configured": bool(setting(env, "GRAPH_API_KEY")),
    }


@app.get("/demo", response_class=HTMLResponse)
async def demo_video():
    return HTMLResponse("""<!doctype html><html lang="en"><head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Wallet Vitals — Demo video</title>
    <link rel="stylesheet" href="/wallet-vitals/static/app.css"></head><body>
    <main class="shell demo-layout">
    <p class="eyebrow">ETHONLINE 2026 · PRODUCT WALKTHROUGH</p>
    <h1>Wallet Vitals, in action.</h1>
    <p>Real public-deployment captures, edited with English synthetic narration and subtitles.</p>
    <video class="demo-player" controls playsinline preload="metadata">
    <source src="/wallet-vitals/demo.mp4" type="video/mp4">
    <track default kind="subtitles" srclang="en" label="English"
    src="/wallet-vitals/demo.vtt"></video>
    <p><a href="/wallet-vitals/">Open the app</a> ·
    <a href="/wallet-vitals/demo.mp4" download>Download MP4</a> ·
    <a href="https://github.com/fizix100/wallet-vitals">Source code</a></p>
    <p>Recorded September 9, 2026. Historical snapshots, not current risk or financial advice.</p>
    </main></body></html>""")


@app.post("/api/analyze", response_model=RiskReport)
async def analyze(payload: AnalyzeRequest, request: Request):
    try:
        address = AnalysisService.normalize_address(payload.address)
        async with service(request, needs_graph=True) as (engine, store):
            await budget(request, store, address)
            await store.prune()
            return await engine.analyze(address)
    except InvalidAddressError as exc:
        raise HTTPException(422, str(exc)) from exc
    except GraphError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.get("/api/reports/{report_id}", response_model=RiskReport)
async def report(report_id: str, request: Request):
    try:
        async with service(request) as (engine, _store):
            return await engine.get_report(report_id)
    except ReportNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/api/reports/{report_id}/explain", response_model=ExplainResponse)
async def explain(report_id: str, payload: ExplainRequest, request: Request):
    try:
        async with service(request) as (engine, store):
            report = await engine.get_report(report_id)
            cached = await store.get_explanation(report_id, payload.intent)
            if cached:
                return ExplainResponse.model_validate_json(cached)
            await budget(request, store)
            result = await engine.explain(report_id, payload.intent)
            await store.save_explanation(report, payload.intent, result.model_dump_json())
            return result
    except ReportNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
