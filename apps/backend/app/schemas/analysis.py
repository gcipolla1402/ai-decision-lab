from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    AGREEMENT = "AGREEMENT"
    INVOICE = "INVOICE"
    POLICY = "POLICY"
    REPORT = "REPORT"
    REQUEST = "REQUEST"
    OTHER = "OTHER"


class Route(StrEnum):
    APPROVE_FOR_REVIEW = "APPROVE_FOR_REVIEW"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class Indicator(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    value: str = Field(min_length=1, max_length=160)
    observed: bool
    evidence: str = Field(min_length=1, max_length=240)


class DocumentAnalysis(BaseModel):
    summary: str = Field(min_length=1, max_length=700)
    document_type: DocumentType
    attention_items: list[str] = Field(max_length=8)
    indicators: list[Indicator] = Field(min_length=1, max_length=10)
    completeness_score: int = Field(ge=0, le=100)


class StageTiming(BaseModel):
    stage: str
    duration_ms: float = Field(ge=0)


class DecisionResult(BaseModel):
    route: Route
    confidence: float = Field(ge=0, le=1)
    rationale: str
    provider: str
    simulated: bool
    model: str | None = None


class RunConditions(BaseModel):
    execution_mode: str
    analysis_provider: str
    analysis_model: str
    analysis_simulated: bool
    decision_provider: str
    decision_simulated: bool
    input_fingerprint: str
    shared_extraction: bool = False
    shared_analysis: bool = False
    cache_used: bool = False
    paid_calls_made: bool = False
    notes: list[str] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    run_id: str
    filename: str
    analysis: DocumentAnalysis
    decision: DecisionResult
    timings: list[StageTiming]
    total_duration_ms: float
    conditions: RunConditions
    disclaimer: str = (
        "Demonstration recommendation only; not legal, regulatory, or automatic approval."
    )


class ComparisonArm(BaseModel):
    label: str
    decision: DecisionResult
    timings: list[StageTiming]
    total_duration_ms: float
    conditions: RunConditions


class ComparisonResponse(BaseModel):
    run_id: str
    filename: str
    analysis: DocumentAnalysis
    arms: list[ComparisonArm]
    comparable: bool
    comparability_notes: list[str]
    disclaimer: str = (
        "Exploratory measurement only. No latency improvement is claimed from a single run."
    )

