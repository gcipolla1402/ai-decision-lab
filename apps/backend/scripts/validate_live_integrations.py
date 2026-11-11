"""Perform exactly one Gemini attempt and one TypeSafe/JEV attempt.

Outputs only sanitized status and usage metadata. Never prints credentials or
the document body. Intended for deliberate manual validation, not CI.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from app.core.config import ROOT_DIR, settings
from app.core.errors import AppError
from app.services.analyzers import DemoAnalysisProvider, GeminiAnalysisProvider
from app.services.decisions import JevDecisionProvider


async def main() -> None:
    document_path = ROOT_DIR / "examples" / "synthetic-request.txt"
    document_text = document_path.read_text(encoding="utf-8")
    output: dict[str, object] = {
        "document": document_path.name,
        "synthetic_only": True,
        "logical_calls": {"gemini": 0, "jev": 0},
    }

    gemini = GeminiAnalysisProvider(settings, max_attempts=1)
    gemini_started = time.perf_counter()
    try:
        output["logical_calls"]["gemini"] = 1  # type: ignore[index]
        analysis = await gemini.analyze(document_text)
        output["gemini"] = {
            "success": True,
            "configured_model": settings.gemini_model,
            "returned_model": gemini.last_model_version,
            "duration_ms": round((time.perf_counter() - gemini_started) * 1000, 2),
            "usage": gemini.last_usage,
            "document_type": analysis.document_type.value,
        }
    except AppError as exc:
        output["gemini"] = {
            "success": False,
            "configured_model": settings.gemini_model,
            "duration_ms": round((time.perf_counter() - gemini_started) * 1000, 2),
            "error": exc.public_message,
        }
        analysis = await DemoAnalysisProvider().analyze(document_text)

    jev = JevDecisionProvider(settings, max_retries=0)
    jev_started = time.perf_counter()
    try:
        output["logical_calls"]["jev"] = 1  # type: ignore[index]
        decision = await jev.decide(analysis)
        output["jev"] = {
            "success": True,
            "configured_model": settings.typesafe_model,
            "returned_model": jev.last_model,
            "duration_ms": round((time.perf_counter() - jev_started) * 1000, 2),
            "usage": jev.last_usage,
            "route": decision.route.value,
            "confidence": decision.confidence,
        }
    except AppError as exc:
        output["jev"] = {
            "success": False,
            "configured_model": settings.typesafe_model,
            "duration_ms": round((time.perf_counter() - jev_started) * 1000, 2),
            "error": exc.public_message,
        }

    gemini_ok = bool(output.get("gemini", {}).get("success"))  # type: ignore[union-attr]
    jev_ok = bool(output.get("jev", {}).get("success"))  # type: ignore[union-attr]
    output["combined"] = {
        "success": gemini_ok and jev_ok,
        "reused_existing_results": True,
        "additional_api_calls": 0,
    }
    print(json.dumps(output, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    asyncio.run(main())
