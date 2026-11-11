from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.core.errors import AppError, ProviderUnavailableError
from app.schemas.analysis import DocumentAnalysis, DocumentType, Indicator

logger = logging.getLogger("ai_decision_lab.providers")


class AnalysisProvider(ABC):
    name: str
    model: str
    simulated: bool

    @abstractmethod
    async def analyze(self, text: str) -> DocumentAnalysis: ...


class DemoAnalysisProvider(AnalysisProvider):
    name = "local-demo"
    model = "deterministic-rules-v1"
    simulated = True

    async def analyze(self, text: str) -> DocumentAnalysis:
        lowered = text.lower()
        doc_type = self._document_type(lowered)
        has_date = bool(re.search(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b", text))
        has_amount = bool(re.search(r"(?:[$€£]|USD|BRL|EUR)\s?\d", text, re.I))
        has_parties = any(word in lowered for word in ("party", "client", "supplier", "requester"))
        has_signature = "signature" in lowered or "signed" in lowered
        flags = [
            ("Explicit date", has_date, "A recognizable date pattern was found." if has_date else "No recognizable date pattern was found."),
            ("Financial amount", has_amount, "A currency amount was detected." if has_amount else "No currency amount was detected."),
            ("Named roles", has_parties, "At least one business role was detected." if has_parties else "No standard party role was detected."),
            ("Signature marker", has_signature, "A signature marker was detected." if has_signature else "No signature marker was detected."),
        ]
        missing = [name for name, observed, _ in flags if not observed]
        score = round(sum(1 for _, observed, _ in flags if observed) / len(flags) * 100)
        first_sentence = re.split(r"(?<=[.!?])\s+", text.strip())[0][:360]
        return DocumentAnalysis(
            summary=f"Synthetic {doc_type.value.lower()} analyzed locally. {first_sentence}",
            document_type=doc_type,
            attention_items=[f"Verify {item.lower()}." for item in missing] or ["No rule-based gaps detected; human verification remains required."],
            indicators=[Indicator(name=name, value="detected" if observed else "not detected", observed=observed, evidence=evidence) for name, observed, evidence in flags],
            completeness_score=score,
        )

    @staticmethod
    def _document_type(text: str) -> DocumentType:
        keywords = {
            DocumentType.INVOICE: ("invoice", "total due", "payment"),
            DocumentType.AGREEMENT: ("agreement", "parties", "terms"),
            DocumentType.POLICY: ("policy", "procedure", "scope"),
            DocumentType.REPORT: ("report", "findings", "executive summary"),
            DocumentType.REQUEST: ("request", "requested", "applicant"),
        }
        scores = {kind: sum(token in text for token in tokens) for kind, tokens in keywords.items()}
        winner = max(scores, key=scores.get)
        return winner if scores[winner] else DocumentType.OTHER


class GeminiAnalysisProvider(AnalysisProvider):
    name = "google-gemini"
    simulated = False

    def __init__(
        self,
        config: Settings,
        client_factory: Callable[..., Any] | None = None,
        max_attempts: int | None = None,
    ) -> None:
        self.config = config
        self.model = config.gemini_model
        self._client_factory = client_factory
        self._max_attempts = max_attempts
        self.last_model_version: str | None = None
        self.last_usage: dict[str, Any] | None = None

    async def analyze(self, text: str) -> DocumentAnalysis:
        if not self.config.gemini_enabled or not self.config.gemini_api_key:
            raise ProviderUnavailableError("Gemini")
        started = time.perf_counter()
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._analyze_sync, text),
                timeout=self.config.request_timeout_seconds,
            )
        except TimeoutError as exc:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.warning(
                "provider_failed provider=gemini stage=timeout error_type=%s duration_ms=%.2f",
                type(exc).__name__,
                duration_ms,
            )
            raise AppError(
                "Gemini analysis timed out. Retry later or use DEMO mode.",
                status_code=504,
                error_code="gemini_timeout",
                provider="gemini",
                stage="analysis",
            ) from exc

    def _analyze_sync(self, text: str) -> DocumentAnalysis:
        request_started = time.perf_counter()
        try:
            if self._client_factory is None:
                from google import genai
                from google.genai import types

                factory = genai.Client
                retry_options = (
                    types.HttpRetryOptions(attempts=self._max_attempts)
                    if self._max_attempts is not None
                    else None
                )
                client_kwargs = {
                    "api_key": self.config.gemini_api_key,
                    "http_options": types.HttpOptions(
                        timeout=int(self.config.request_timeout_seconds * 1000),
                        retry_options=retry_options,
                    ),
                }
                config = types.GenerateContentConfig(
                    system_instruction=(
                        "Analyze only the supplied synthetic document. Report observable facts, "
                        "mark uncertainty, and never provide legal or regulatory approval."
                    ),
                    response_mime_type="application/json",
                    response_schema=DocumentAnalysis,
                    temperature=0,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                )
            else:
                factory = self._client_factory
                client_kwargs = {"api_key": self.config.gemini_api_key}
                config = {
                    "response_mime_type": "application/json",
                    "response_schema": DocumentAnalysis,
                    "temperature": 0,
                }
            with factory(**client_kwargs) as client:
                response = client.models.generate_content(
                    model=self.model,
                    contents=f"Document text:\n{text}",
                    config=config,
                )
        except Exception as exc:
            duration_ms = (time.perf_counter() - request_started) * 1000
            logger.warning(
                "provider_failed provider=gemini stage=request error_type=%s duration_ms=%.2f",
                type(exc).__name__,
                duration_ms,
            )
            raise AppError(
                "Gemini request failed. Retry later or use DEMO mode.",
                status_code=502,
                error_code="gemini_request_failed",
                provider="gemini",
                stage="request",
            ) from exc

        request_duration_ms = (time.perf_counter() - request_started) * 1000
        logger.info(
            "provider_completed provider=gemini stage=request duration_ms=%.2f model=%s",
            request_duration_ms,
            self.model,
        )
        validation_started = time.perf_counter()
        try:
            self.last_model_version = getattr(response, "model_version", None)
            usage = getattr(response, "usage_metadata", None)
            self.last_usage = usage.model_dump(exclude_none=True) if usage else None
            analysis, normalized_fields = _parse_gemini_analysis(response)
            logger.info(
                "provider_completed provider=gemini stage=response_validation "
                "duration_ms=%.2f normalized_fields=%s",
                (time.perf_counter() - validation_started) * 1000,
                ",".join(normalized_fields) if normalized_fields else "none",
            )
            return analysis
        except (ValidationError, ValueError, TypeError, json.JSONDecodeError) as exc:
            duration_ms = (time.perf_counter() - validation_started) * 1000
            logger.warning(
                "provider_failed provider=gemini stage=response_validation "
                "error_type=%s duration_ms=%.2f",
                type(exc).__name__,
                duration_ms,
            )
            raise AppError(
                "Gemini returned a structured response that failed validation.",
                status_code=502,
                error_code="gemini_response_invalid",
                provider="gemini",
                stage="response_validation",
            ) from exc


def _parse_gemini_analysis(response: Any) -> tuple[DocumentAnalysis, list[str]]:
    """Validate SDK parsed output, with bounded normalization for model overrun.

    Google GenAI can leave ``parsed`` empty after swallowing a Pydantic
    validation error. In that case we recover the JSON text, trim only fields
    that exceeded our documented response bounds, and validate every required
    field and type again with the public response model.
    """

    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, DocumentAnalysis):
        return parsed, []
    if isinstance(parsed, BaseModel):
        payload: Any = parsed.model_dump()
    elif parsed is not None:
        payload = parsed
    else:
        response_text = getattr(response, "text", None)
        if not isinstance(response_text, str) or not response_text.strip():
            raise ValueError("Structured response body is empty")
        payload = json.loads(response_text)
    if not isinstance(payload, dict):
        raise TypeError("Structured response must be an object")

    normalized = dict(payload)
    normalized_fields: list[str] = []

    summary = normalized.get("summary")
    if isinstance(summary, str) and len(summary) > 700:
        normalized["summary"] = summary[:700]
        normalized_fields.append("summary")

    attention_items = normalized.get("attention_items")
    if isinstance(attention_items, list) and len(attention_items) > 8:
        normalized["attention_items"] = attention_items[:8]
        normalized_fields.append("attention_items")

    indicators = normalized.get("indicators")
    if isinstance(indicators, list):
        if len(indicators) > 10:
            normalized_fields.append("indicators")
        bounded_indicators: list[Any] = []
        for indicator in indicators[:10]:
            if isinstance(indicator, BaseModel):
                indicator = indicator.model_dump()
            if not isinstance(indicator, dict):
                bounded_indicators.append(indicator)
                continue
            bounded = dict(indicator)
            for field, limit in (("name", 80), ("value", 160), ("evidence", 240)):
                value = bounded.get(field)
                if isinstance(value, str) and len(value) > limit:
                    bounded[field] = value[:limit]
                    marker = f"indicators.{field}"
                    if marker not in normalized_fields:
                        normalized_fields.append(marker)
            bounded_indicators.append(bounded)
        normalized["indicators"] = bounded_indicators

    return DocumentAnalysis.model_validate(normalized), normalized_fields

