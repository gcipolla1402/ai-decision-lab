from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from app.core.config import Settings
from app.core.errors import AppError, ProviderUnavailableError
from app.schemas.analysis import DecisionResult, DocumentAnalysis, Route

logger = logging.getLogger("ai_decision_lab.providers")


class DecisionProvider(ABC):
    name: str
    simulated: bool

    @abstractmethod
    async def decide(self, analysis: DocumentAnalysis) -> DecisionResult: ...


class DemoDecisionProvider(DecisionProvider):
    name = "local-decision-rules"
    simulated = True

    async def decide(self, analysis: DocumentAnalysis) -> DecisionResult:
        score = analysis.completeness_score
        if score < 50:
            route, confidence, rationale = (
                Route.INSUFFICIENT_INFORMATION,
                0.91,
                "Fewer than half of the configured completeness indicators were observed.",
            )
        elif analysis.attention_items and score < 85:
            route, confidence, rationale = (
                Route.NEEDS_HUMAN_REVIEW,
                0.82,
                "Material attention items remain and require a person to assess them.",
            )
        else:
            route, confidence, rationale = (
                Route.APPROVE_FOR_REVIEW,
                0.78,
                "The document appears complete enough to enter a human review queue.",
            )
        return DecisionResult(
            route=route,
            confidence=confidence,
            rationale=rationale,
            provider=self.name,
            simulated=True,
            model="deterministic-rules-v1",
        )


class JevDecisionProvider(DecisionProvider):
    """Official TypeSafe SDK integration verified against its public Python quickstart."""

    name = "typesafe-jev"
    simulated = False

    def __init__(
        self,
        config: Settings,
        client_factory: Callable[..., Any] | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.config = config
        self._client_factory = client_factory
        self._max_retries = max_retries
        self.last_model: str | None = None
        self.last_usage: dict[str, Any] | None = None

    async def decide(self, analysis: DocumentAnalysis) -> DecisionResult:
        if not self.config.jev_enabled or not self.config.typesafe_api_key:
            raise ProviderUnavailableError("TypeSafe/JEV")
        started = time.perf_counter()
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._decide_sync, analysis),
                timeout=self.config.request_timeout_seconds,
            )
        except TimeoutError as exc:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.warning(
                "provider_failed provider=jev stage=timeout error_type=%s duration_ms=%.2f",
                type(exc).__name__,
                duration_ms,
            )
            raise AppError(
                "TypeSafe/JEV routing timed out. Retry later.",
                status_code=504,
                error_code="jev_timeout",
                provider="jev",
                stage="routing",
            ) from exc

    def _decide_sync(self, analysis: DocumentAnalysis) -> DecisionResult:
        request_started = time.perf_counter()
        try:
            if self._client_factory is None:
                from typesafe_sdk import Choice, RetryPolicy, TypeSafeClient

                factory = TypeSafeClient
                retry_policy = (
                    RetryPolicy(max_retries=self._max_retries)
                    if self._max_retries is not None
                    else None
                )
                choice = Choice(
                    instructions=(
                        "Choose the safest demonstration routing recommendation. APPROVE_FOR_REVIEW "
                        "only means ready for human review, never legal or regulatory approval."
                    ),
                    criteria={route.value: None for route in Route},
                )
            else:
                factory = self._client_factory
                retry_policy = None
                choice = {
                    "instructions": "Choose a demonstration routing recommendation.",
                    "criteria": {route.value: None for route in Route},
                }
            state = {
                "document_type": analysis.document_type.value,
                "attention_items": analysis.attention_items,
                "completeness_score": analysis.completeness_score,
                "indicators": [item.model_dump() for item in analysis.indicators],
            }
            with factory(api_key=self.config.typesafe_api_key) as client:
                response = client.system_one(
                    state=state,
                    questions={"route": choice},
                    model=self.config.typesafe_model,
                    retry=retry_policy,
                )
        except Exception as exc:
            duration_ms = (time.perf_counter() - request_started) * 1000
            logger.warning(
                "provider_failed provider=jev stage=request error_type=%s duration_ms=%.2f model=%s",
                type(exc).__name__,
                duration_ms,
                self.config.typesafe_model,
            )
            raise AppError(
                "TypeSafe/JEV request failed. Verify credentials, model access, or retry later.",
                status_code=502,
                error_code="jev_request_failed",
                provider="jev",
                stage="request",
            ) from exc

        logger.info(
            "provider_completed provider=jev stage=request duration_ms=%.2f model=%s",
            (time.perf_counter() - request_started) * 1000,
            self.config.typesafe_model,
        )
        validation_started = time.perf_counter()
        try:
            self.last_model = getattr(response, "model", None)
            usage = getattr(response, "usage", None)
            self.last_usage = usage.model_dump(exclude_none=True) if usage else None
            answer = response.choices["route"]
            route = Route(answer.choice)
            confidence = float(getattr(answer, "confidence", 0.0))
            decision = DecisionResult(
                route=route,
                confidence=max(0.0, min(confidence, 1.0)),
                rationale="Typed Choice result returned by TypeSafe/JEV; human review remains mandatory.",
                provider=self.name,
                simulated=False,
                model=self.config.typesafe_model,
            )
            logger.info(
                "provider_completed provider=jev stage=response_validation duration_ms=%.2f model=%s",
                (time.perf_counter() - validation_started) * 1000,
                self.config.typesafe_model,
            )
            return decision
        except Exception as exc:
            duration_ms = (time.perf_counter() - validation_started) * 1000
            logger.warning(
                "provider_failed provider=jev stage=response_validation "
                "error_type=%s duration_ms=%.2f model=%s",
                type(exc).__name__,
                duration_ms,
                self.config.typesafe_model,
            )
            raise AppError(
                "TypeSafe/JEV returned an invalid routing response.",
                status_code=502,
                error_code="jev_response_invalid",
                provider="jev",
                stage="response_validation",
            ) from exc

