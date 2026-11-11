from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, File, Form, UploadFile

from app.core.config import settings
from app.core.errors import AppError
from app.schemas.analysis import AnalysisResponse, ComparisonResponse
from app.services.analyzers import DemoAnalysisProvider, GeminiAnalysisProvider
from app.services.decisions import DemoDecisionProvider, JevDecisionProvider
from app.services.pipeline import run_comparison, run_pipeline

router = APIRouter(prefix="/api")
logger = logging.getLogger("ai_decision_lab.routes")


@router.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "demo_ready": True,
        "gemini_configured": settings.gemini_enabled and bool(settings.gemini_api_key),
        "jev_configured": settings.jev_enabled and bool(settings.typesafe_api_key),
        "max_upload_mb": settings.max_upload_mb,
    }


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
    analysis_mode: Literal["demo", "gemini"] = Form(...),
    decision_mode: Literal["demo", "jev"] = Form(...),
) -> AnalysisResponse:
    data = await file.read(settings.max_upload_bytes + 1)
    if (analysis_mode, decision_mode) == ("demo", "demo"):
        analyzer = DemoAnalysisProvider()
        decision = DemoDecisionProvider()
    elif (analysis_mode, decision_mode) == ("gemini", "demo"):
        analyzer = GeminiAnalysisProvider(settings)
        decision = DemoDecisionProvider()
    elif (analysis_mode, decision_mode) == ("gemini", "jev"):
        analyzer = GeminiAnalysisProvider(settings)
        decision = JevDecisionProvider(settings)
    else:
        raise AppError("JEV routing requires Gemini analysis in this application.")
    logger.info(
        "pipeline_selected analysis_mode=%s decision_mode=%s analysis_provider=%s decision_provider=%s",
        analysis_mode,
        decision_mode,
        analyzer.name,
        decision.name,
    )
    return await run_pipeline(
        filename=file.filename or "document",
        content_type=file.content_type,
        data=data,
        config=settings,
        analyzer=analyzer,
        decision_provider=decision,
    )


@router.post("/compare", response_model=ComparisonResponse)
async def compare_modes(
    file: UploadFile = File(...),
    live: bool = Form(...),
) -> ComparisonResponse:
    data = await file.read(settings.max_upload_bytes + 1)
    analyzer = GeminiAnalysisProvider(settings) if live else DemoAnalysisProvider()
    candidate = JevDecisionProvider(settings) if live else DemoDecisionProvider()
    return await run_comparison(
        filename=file.filename or "document",
        content_type=file.content_type,
        data=data,
        config=settings,
        analyzer=analyzer,
        baseline=DemoDecisionProvider(),
        candidate=candidate,
    )

