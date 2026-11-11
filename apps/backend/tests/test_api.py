from fastapi.testclient import TestClient
import pytest

import app.api.routes as routes_module
from app.main import app
from app.schemas.analysis import DecisionResult, Route
from conftest import sample_analysis


client = TestClient(app)


def test_health_reports_demo_ready() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["demo_ready"] is True


def test_demo_analysis_end_to_end() -> None:
    content = (
        "SYNTHETIC INVOICE\nInvoice ID: DEMO-100\nDate: 2026-10-20\n"
        "Client: Example Studio\nTotal due: USD 1250\nSignature: Demo Signer"
    )
    response = client.post(
        "/api/analyze",
        files={"file": ("invoice.txt", content, "text/plain")},
        data={"analysis_mode": "demo", "decision_mode": "demo"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["analysis"]["document_type"] == "INVOICE"
    assert body["decision"]["simulated"] is True
    assert body["conditions"]["paid_calls_made"] is False
    assert body["conditions"]["execution_mode"] == "DEMO"
    assert body["conditions"]["analysis_provider"] == "local-demo"
    assert body["conditions"]["decision_provider"] == "local-decision-rules"


class MockGeminiProvider:
    name = "google-gemini"
    model = "mock-gemini-model"
    simulated = False

    def __init__(self, _settings) -> None:
        pass

    async def analyze(self, _text: str):
        return sample_analysis()


class MockJevProvider:
    name = "typesafe-jev"
    simulated = False

    def __init__(self, _settings) -> None:
        pass

    async def decide(self, _analysis):
        return DecisionResult(
            route=Route.NEEDS_HUMAN_REVIEW,
            confidence=0.8,
            rationale="Mocked typed route.",
            provider=self.name,
            simulated=False,
            model="mock-jev-model",
        )


def _post_mode(analysis_mode: str, decision_mode: str):
    return client.post(
        "/api/analyze",
        files={"file": ("synthetic.txt", "Synthetic report with enough fictional text.", "text/plain")},
        data={"analysis_mode": analysis_mode, "decision_mode": decision_mode},
    )


def test_gemini_only_selects_live_analysis_and_local_routing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routes_module, "GeminiAnalysisProvider", MockGeminiProvider)
    response = _post_mode("gemini", "demo")
    assert response.status_code == 200
    conditions = response.json()["conditions"]
    assert conditions["execution_mode"] == "GEMINI_ONLY"
    assert conditions["analysis_provider"] == "google-gemini"
    assert conditions["analysis_simulated"] is False
    assert conditions["decision_provider"] == "local-decision-rules"
    assert conditions["decision_simulated"] is True


def test_gemini_jev_selects_both_live_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routes_module, "GeminiAnalysisProvider", MockGeminiProvider)
    monkeypatch.setattr(routes_module, "JevDecisionProvider", MockJevProvider)
    response = _post_mode("gemini", "jev")
    assert response.status_code == 200
    conditions = response.json()["conditions"]
    assert conditions["execution_mode"] == "GEMINI_JEV"
    assert conditions["analysis_provider"] == "google-gemini"
    assert conditions["decision_provider"] == "typesafe-jev"
    assert conditions["analysis_simulated"] is False
    assert conditions["decision_simulated"] is False


def test_demo_analysis_cannot_silently_route_through_jev() -> None:
    response = _post_mode("demo", "jev")
    assert response.status_code == 400
    assert response.json()["detail"] == "JEV routing requires Gemini analysis in this application."


def test_missing_mode_fields_do_not_fall_back_to_demo() -> None:
    response = client.post(
        "/api/analyze",
        files={"file": ("synthetic.txt", "Synthetic report with enough fictional text.", "text/plain")},
    )
    assert response.status_code == 422

