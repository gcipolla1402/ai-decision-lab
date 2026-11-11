from __future__ import annotations

import hashlib
import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from app.core.config import Settings
from app.schemas.analysis import (
    AnalysisResponse,
    ComparisonArm,
    ComparisonResponse,
    RunConditions,
    StageTiming,
)
from app.services.analyzers import AnalysisProvider
from app.services.decisions import DecisionProvider
from app.services.extraction import extract_document

logger = logging.getLogger("ai_decision_lab.pipeline")


async def _timed(stage: str, operation: Callable[[], Awaitable]):
    started = time.perf_counter()
    result = await operation()
    duration_ms = (time.perf_counter() - started) * 1000
    logger.info("pipeline_stage_completed stage=%s duration_ms=%.2f", stage, duration_ms)
    return result, StageTiming(stage=stage, duration_ms=duration_ms)


async def run_pipeline(
    *, filename: str, content_type: str | None, data: bytes, config: Settings,
    analyzer: AnalysisProvider, decision_provider: DecisionProvider,
) -> AnalysisResponse:
    total_started = time.perf_counter()
    extraction_started = time.perf_counter()
    document = extract_document(filename=filename, content_type=content_type, data=data, max_bytes=config.max_upload_bytes)
    extraction_timing = StageTiming(stage="extraction", duration_ms=(time.perf_counter() - extraction_started) * 1000)
    logger.info(
        "pipeline_stage_completed stage=extraction duration_ms=%.2f",
        extraction_timing.duration_ms,
    )
    analysis, analysis_timing = await _timed("analysis", lambda: analyzer.analyze(document.text))
    decision, decision_timing = await _timed("routing", lambda: decision_provider.decide(analysis))
    fingerprint = hashlib.sha256(document.text.encode()).hexdigest()[:12]
    return AnalysisResponse(
        run_id=str(uuid.uuid4()),
        filename=document.filename,
        analysis=analysis,
        decision=decision,
        timings=[extraction_timing, analysis_timing, decision_timing],
        total_duration_ms=(time.perf_counter() - total_started) * 1000,
        conditions=RunConditions(
            execution_mode=(
                "DEMO"
                if analyzer.simulated
                else "GEMINI_ONLY"
                if decision_provider.simulated
                else "GEMINI_JEV"
            ),
            analysis_provider=analyzer.name,
            analysis_model=analyzer.model,
            analysis_simulated=analyzer.simulated,
            decision_provider=decision_provider.name,
            decision_simulated=decision_provider.simulated,
            input_fingerprint=fingerprint,
            cache_used=False,
            paid_calls_made=not analyzer.simulated or not decision_provider.simulated,
            notes=["Input is processed in memory and is not persisted by this application."],
        ),
    )


async def run_comparison(
    *, filename: str, content_type: str | None, data: bytes, config: Settings,
    analyzer: AnalysisProvider, baseline: DecisionProvider, candidate: DecisionProvider,
) -> ComparisonResponse:
    extraction_started = time.perf_counter()
    document = extract_document(filename=filename, content_type=content_type, data=data, max_bytes=config.max_upload_bytes)
    extraction_ms = (time.perf_counter() - extraction_started) * 1000
    logger.info("pipeline_stage_completed stage=extraction duration_ms=%.2f", extraction_ms)
    analysis, analysis_timing = await _timed("shared_analysis", lambda: analyzer.analyze(document.text))
    fingerprint = hashlib.sha256(document.text.encode()).hexdigest()[:12]
    arms: list[ComparisonArm] = []
    for label, provider in (("Gemini Only", baseline), ("Gemini + JEV", candidate)):
        decision, routing = await _timed("routing", lambda provider=provider: provider.decide(analysis))
        timings = [StageTiming(stage="shared_extraction", duration_ms=extraction_ms), analysis_timing, routing]
        arms.append(ComparisonArm(
            label=label,
            decision=decision,
            timings=timings,
            total_duration_ms=sum(item.duration_ms for item in timings),
            conditions=RunConditions(
                execution_mode=(
                    "DEMO"
                    if analyzer.simulated
                    else "GEMINI_ONLY"
                    if provider.simulated
                    else "GEMINI_JEV"
                ),
                analysis_provider=analyzer.name,
                analysis_model=analyzer.model,
                analysis_simulated=analyzer.simulated,
                decision_provider=provider.name,
                decision_simulated=provider.simulated,
                input_fingerprint=fingerprint,
                shared_extraction=True,
                shared_analysis=True,
                cache_used=False,
                paid_calls_made=not analyzer.simulated or not provider.simulated,
                notes=["Extraction and analysis outputs were shared; only routing was measured separately."],
            ),
        ))
    return ComparisonResponse(
        run_id=str(uuid.uuid4()),
        filename=document.filename,
        analysis=analysis,
        arms=arms,
        comparable=True,
        comparability_notes=[
            "Both arms used the same extracted text fingerprint and the same analysis result.",
            "This isolates routing duration but is not an end-to-end independent-call benchmark.",
            "DEMO providers are simulations and do not represent Gemini or JEV network latency.",
        ],
    )

