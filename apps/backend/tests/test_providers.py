import asyncio
import json
import logging
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.core.errors import AppError
from app.schemas.analysis import Route
from app.services.analyzers import GeminiAnalysisProvider
from app.services.decisions import DemoDecisionProvider, JevDecisionProvider
from conftest import sample_analysis


class ContextClient:
    def __init__(self, client): self.client = client
    def __enter__(self): return self.client
    def __exit__(self, *args): return None


def test_demo_decision_is_deterministic() -> None:
    decision = asyncio.run(DemoDecisionProvider().decide(sample_analysis(75)))
    assert decision.route == Route.NEEDS_HUMAN_REVIEW
    assert decision.simulated is True


def test_gemini_provider_uses_mock_without_network() -> None:
    expected = sample_analysis()
    models = SimpleNamespace(generate_content=lambda **_: SimpleNamespace(parsed=expected, text=""))
    provider = GeminiAnalysisProvider(
        Settings(gemini_enabled=True, gemini_api_key="test-placeholder"),
        client_factory=lambda **_: ContextClient(SimpleNamespace(models=models)),
    )
    assert asyncio.run(provider.analyze("Synthetic text with enough content.")) == expected


def test_gemini_recovers_json_when_sdk_swallowed_length_validation() -> None:
    payload = sample_analysis().model_dump(mode="json")
    payload["summary"] = "S" * 900
    payload["attention_items"] = [f"Synthetic item {index}" for index in range(12)]
    payload["indicators"] = [
        {
            "name": f"Indicator {index}",
            "value": "V" * 200,
            "observed": True,
            "evidence": "E" * 300,
        }
        for index in range(12)
    ]
    response = SimpleNamespace(
        parsed=None,
        text=json.dumps(payload),
        model_version="mock-model",
        usage_metadata=None,
    )
    models = SimpleNamespace(generate_content=lambda **_: response)
    provider = GeminiAnalysisProvider(
        Settings(gemini_enabled=True, gemini_api_key="test-placeholder"),
        client_factory=lambda **_: ContextClient(SimpleNamespace(models=models)),
    )

    result = asyncio.run(provider.analyze("Synthetic PDF text with enough content."))

    assert len(result.summary) == 700
    assert len(result.attention_items) == 8
    assert len(result.indicators) == 10
    assert len(result.indicators[0].value) == 160
    assert len(result.indicators[0].evidence) == 240


def test_gemini_accepts_sdk_parsed_mapping_without_response_text() -> None:
    expected = sample_analysis()
    response = SimpleNamespace(
        parsed=expected.model_dump(mode="json"),
        text=None,
        model_version="mock-model",
        usage_metadata=None,
    )
    models = SimpleNamespace(generate_content=lambda **_: response)
    provider = GeminiAnalysisProvider(
        Settings(gemini_enabled=True, gemini_api_key="test-placeholder"),
        client_factory=lambda **_: ContextClient(SimpleNamespace(models=models)),
    )

    assert asyncio.run(provider.analyze("Synthetic PDF text with enough content.")) == expected


def test_gemini_invalid_structure_reports_validation_stage(
    caplog: pytest.LogCaptureFixture,
) -> None:
    response = SimpleNamespace(
        parsed=None,
        text=json.dumps({"document_type": "REPORT"}),
        model_version="mock-model",
        usage_metadata=None,
    )
    models = SimpleNamespace(generate_content=lambda **_: response)
    provider = GeminiAnalysisProvider(
        Settings(gemini_enabled=True, gemini_api_key="test-placeholder"),
        client_factory=lambda **_: ContextClient(SimpleNamespace(models=models)),
    )

    with caplog.at_level(logging.WARNING), pytest.raises(AppError) as error:
        asyncio.run(provider.analyze("Synthetic PDF text with enough content."))

    assert error.value.error_code == "gemini_response_invalid"
    assert error.value.stage == "response_validation"
    assert "provider=gemini stage=response_validation" in caplog.text
    assert "Synthetic PDF text" not in caplog.text


def test_jev_provider_uses_verified_mock_shape() -> None:
    answer = SimpleNamespace(choice="NEEDS_HUMAN_REVIEW", confidence=0.88)
    client = SimpleNamespace(system_one=lambda **_: SimpleNamespace(choices={"route": answer}))
    provider = JevDecisionProvider(
        Settings(jev_enabled=True, typesafe_api_key="test-placeholder"),
        client_factory=lambda **_: ContextClient(client),
    )
    decision = asyncio.run(provider.decide(sample_analysis()))
    assert decision.route == Route.NEEDS_HUMAN_REVIEW
    assert decision.confidence == 0.88
    assert decision.simulated is False


def test_jev_invalid_choice_reports_validation_stage(
    caplog: pytest.LogCaptureFixture,
) -> None:
    answer = SimpleNamespace(choice="UNKNOWN_ROUTE", confidence=0.5)
    client = SimpleNamespace(system_one=lambda **_: SimpleNamespace(choices={"route": answer}))
    provider = JevDecisionProvider(
        Settings(jev_enabled=True, typesafe_api_key="test-placeholder"),
        client_factory=lambda **_: ContextClient(client),
    )

    with caplog.at_level(logging.WARNING), pytest.raises(AppError) as error:
        asyncio.run(provider.decide(sample_analysis()))

    assert error.value.error_code == "jev_response_invalid"
    assert error.value.stage == "response_validation"
    assert "provider=jev stage=response_validation" in caplog.text


def test_jev_authentication_error_reports_request_stage() -> None:
    class MockAuthenticationError(Exception):
        pass

    def fail_request(**_):
        raise MockAuthenticationError("sensitive upstream detail")

    client = SimpleNamespace(system_one=fail_request)
    provider = JevDecisionProvider(
        Settings(jev_enabled=True, typesafe_api_key="test-placeholder"),
        client_factory=lambda **_: ContextClient(client),
    )

    with pytest.raises(AppError) as error:
        asyncio.run(provider.decide(sample_analysis()))

    assert error.value.error_code == "jev_request_failed"
    assert error.value.stage == "request"

