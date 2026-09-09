from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceMetadata(StrictModel):
    provider: Literal["the-graph"] = "the-graph"
    subgraph_id: str
    deployment: str
    network: Literal["ethereum"] = "ethereum"
    block_number: int = Field(ge=0)
    block_timestamp: datetime
    queried_at: datetime
    has_indexing_errors: bool = False
    rules_version: str = "aave-v1"


class PositionAsset(StrictModel):
    address: str
    symbol: str
    decimals: int = Field(ge=0, le=36)
    supply: Decimal = Field(ge=0)
    debt: Decimal = Field(ge=0)
    price_usd: Decimal = Field(gt=0)
    supply_usd: Decimal = Field(ge=0)
    debt_usd: Decimal = Field(ge=0)
    liquidation_threshold_bps: int = Field(ge=0, le=10_000)
    collateral_enabled: bool
    e_mode_applied: bool = False
    evidence_ref: str


class EvidenceSnapshot(StrictModel):
    address: str
    source: SourceMetadata
    assets: list[PositionAsset]
    warnings: list[str] = Field(default_factory=list)


RiskSeverity = Literal["no_debt", "healthy", "warning", "danger", "liquidatable"]


class StressScenario(StrictModel):
    collateral_shock_pct: int
    health_factor: Decimal | None
    severity: RiskSeverity


class RiskDelta(StrictModel):
    status: Literal["no_baseline", "comparable", "incomparable"]
    previous_block_number: int | None = None
    current_block_number: int
    collateral_usd_change: Decimal | None = None
    debt_usd_change: Decimal | None = None
    health_factor_change: Decimal | None = None


class EvidenceReceipt(StrictModel):
    provider: str
    subgraph_id: str
    deployment: str
    network: str
    block_number: int
    block_timestamp: datetime
    queried_at: datetime
    rules_version: str
    scenario_assumptions: list[str]
    evidence_refs: list[str]


class RiskReport(StrictModel):
    report_id: str
    address: str
    created_at: datetime
    expires_at: datetime
    total_collateral_usd: Decimal
    total_debt_usd: Decimal
    liquidation_weighted_collateral_usd: Decimal
    health_factor: Decimal | None
    severity: RiskSeverity
    liquidation_buffer_pct: Decimal | None
    stress_ladder: list[StressScenario]
    risk_delta: RiskDelta
    assets: list[PositionAsset]
    evidence_receipt: EvidenceReceipt
    narrative: str
    narrative_mode: Literal["openai", "deterministic"]
    warnings: list[str] = Field(default_factory=list)


class AnalyzeRequest(StrictModel):
    address: str = Field(min_length=42, max_length=42)


class ExplainRequest(StrictModel):
    intent: Literal["what_changed", "what_breaks_first", "how_to_verify"]


class ExplainResponse(StrictModel):
    report_id: str
    intent: str
    answer: str
    mode: Literal["openai", "deterministic"]
