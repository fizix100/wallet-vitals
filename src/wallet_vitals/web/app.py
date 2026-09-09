from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from wallet_vitals.ai.narrator import RiskNarrator
from wallet_vitals.application.service import (
    AnalysisCooldownError,
    AnalysisService,
    InvalidAddressError,
    ReportNotFoundError,
)
from wallet_vitals.config import Settings
from wallet_vitals.domain.models import AnalyzeRequest, ExplainRequest, ExplainResponse, RiskReport
from wallet_vitals.graph.aave import AaveV3Subgraph
from wallet_vitals.graph.client import GraphClient
from wallet_vitals.graph.errors import GraphConfigurationError, GraphError
from wallet_vitals.storage.sqlite import SQLiteStore

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=PACKAGE_ROOT / "templates")


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    graph_client: GraphClient | None = None

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        nonlocal graph_client
        store = SQLiteStore(config.database_path)
        await store.initialize()
        key = config.graph_api_key.get_secret_value() if config.graph_api_key else ""
        openai_key = config.openai_api_key.get_secret_value() if config.openai_api_key else None
        narrator = RiskNarrator(
            openai_key,
            config.openai_model,
            config.openai_timeout_seconds,
        )
        subgraph: AaveV3Subgraph | None = None
        if key:
            graph_client = GraphClient(
                config.graph_endpoint,
                key,
                config.graph_timeout_seconds,
            )
            subgraph = AaveV3Subgraph(
                graph_client,
                config.graph_subgraph_id,
                config.graph_max_age_seconds,
            )
        app.state.service = AnalysisService(
            subgraph,
            store,
            narrator,
            config.report_ttl_hours,
            config.address_cooldown_seconds,
            config.max_concurrent_analyses,
        )
        app.state.graph_configured = bool(key)
        app.state.store = store
        yield
        if graph_client is not None:
            await graph_client.close()

    app = FastAPI(
        title=config.app_name,
        description="Evidence-grounded Aave V3 position risk analysis.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.mount("/static", StaticFiles(directory=PACKAGE_ROOT / "static"), name="static")

    def service_for(request: Request) -> AnalysisService:
        return request.app.state.service

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"configured": request.app.state.graph_configured, "initial_report_id": ""},
        )

    @app.get("/reports/{report_id}", response_class=HTMLResponse, include_in_schema=False)
    async def report_page(report_id: str, request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "configured": request.app.state.graph_configured,
                "initial_report_id": report_id[:64],
            },
        )

    @app.get("/health")
    async def health(request: Request) -> dict[str, str | bool]:
        return {
            "status": "ok",
            "graph_configured": request.app.state.graph_configured,
            "version": app.version,
        }

    @app.post("/api/analyze", response_model=RiskReport)
    async def analyze(payload: AnalyzeRequest, request: Request) -> RiskReport:
        try:
            return await service_for(request).analyze(payload.address)
        except InvalidAddressError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except GraphConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except AnalysisCooldownError as exc:
            raise HTTPException(
                status_code=429,
                detail=str(exc),
                headers={"Retry-After": str(exc.retry_after_seconds)},
            ) from exc
        except GraphError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get("/api/reports/{report_id}", response_model=RiskReport)
    async def report(report_id: str, request: Request) -> RiskReport:
        try:
            return await service_for(request).get_report(report_id)
        except ReportNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/reports/{report_id}/explain", response_model=ExplainResponse)
    async def explain(report_id: str, payload: ExplainRequest, request: Request) -> ExplainResponse:
        try:
            return await service_for(request).explain(report_id, payload.intent)
        except ReportNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app


app = create_app()
