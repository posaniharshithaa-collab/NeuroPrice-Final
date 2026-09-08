import os

# A dummy key so the app's fail-fast startup check succeeds for all normal
# tests -- these tests are about request handling, not about whether a key
# exists. Set BEFORE importing api, since lifespan runs at TestClient entry.
os.environ.setdefault("GEMINI_API_KEY", "dummy-key-for-test-startup")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api import app, get_gemini_client, _real_client_singleton, lifespan
from gemini_adapter import GeminiAdapterConfigError
from test_orchestrator import FakeGeminiClient, VALID_RESPONSE, MALFORMED_JSON_RESPONSE, MISSING_EVIDENCE_RESPONSE

VALID_PAYLOAD = {
    "current_price": 999,
    "variable_cost": 400,
    "conversion_rate": 0.05,
    "estimated_market_size": 10000,
    "price_elasticity": -1.2,
    "customer_segment": "price_sensitive",
    "psychology_weight": 0.4,
    "marketing_copy": "Only 5 seats remaining! Join 50,000+ customers. Offer ends tonight.",
}


@pytest.fixture
def client():
    # Entering as a context manager is what actually triggers lifespan() --
    # a bare TestClient(app) does NOT run startup, which would silently
    # defeat the entire point of this test suite.
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _override_gemini(fake_client):
    app.dependency_overrides[get_gemini_client] = lambda: fake_client


# ---------------------------------------------------------------------------
# Success path — this is the "test with real Gemini" case, structurally.
# The actual live-network call was already proven in smoke_test.py; here we
# prove the API wraps that exact pipeline correctly using the same
# FakeGeminiClient the orchestrator tests trust.
# ---------------------------------------------------------------------------

def test_analyze_success_returns_full_core_result(client):
    _override_gemini(FakeGeminiClient([VALID_RESPONSE]))

    response = client.post("/analyze", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["attempts_used"] == 1
    assert body["psychology"]["scores"]["scarcity"] == 8
    assert len(body["financials"]["scenarios"]) == 3
    assert body["financials"]["modeled_range"]["low"] == 999


def test_analyze_recovers_through_retry(client):
    _override_gemini(FakeGeminiClient([MALFORMED_JSON_RESPONSE, VALID_RESPONSE]))

    response = client.post("/analyze", json=VALID_PAYLOAD)

    assert response.status_code == 200
    assert response.json()["attempts_used"] == 2


# ---------------------------------------------------------------------------
# Gemini failure — a legitimate, well-formed 200 response with ok=false,
# not a 5xx. The API surfaces the pipeline's own controlled failure state.
# ---------------------------------------------------------------------------

def test_analyze_gemini_persistent_failure_returns_200_ok_false(client):
    _override_gemini(FakeGeminiClient([MALFORMED_JSON_RESPONSE, MISSING_EVIDENCE_RESPONSE]))

    response = client.post("/analyze", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["financials"] is None
    assert "No financial calculation was performed" in body["error_message"]


# ---------------------------------------------------------------------------
# Invalid business input — must map to 400 via ProductEconomics' OWN
# validation, not a re-implemented check in the API layer.
# ---------------------------------------------------------------------------

def test_analyze_rejects_variable_cost_above_price_with_400(client):
    _override_gemini(FakeGeminiClient([VALID_RESPONSE]))
    bad_payload = {**VALID_PAYLOAD, "variable_cost": 1200}  # > current_price

    response = client.post("/analyze", json=bad_payload)

    assert response.status_code == 400
    assert "variable_cost" in response.json()["detail"]


def test_analyze_rejects_conversion_rate_out_of_range_with_400(client):
    _override_gemini(FakeGeminiClient([VALID_RESPONSE]))
    bad_payload = {**VALID_PAYLOAD, "conversion_rate": 1.5}

    response = client.post("/analyze", json=bad_payload)

    assert response.status_code == 400


def test_analyze_rejects_positive_elasticity_with_400(client):
    _override_gemini(FakeGeminiClient([VALID_RESPONSE]))
    bad_payload = {**VALID_PAYLOAD, "price_elasticity": 1.2}  # must be negative

    response = client.post("/analyze", json=bad_payload)

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Malformed request shape — Pydantic's job, automatic 422, no custom code.
# These no longer even need a Gemini override: the fail-fast startup check
# means the dependency can never be the reason these fail now.
# ---------------------------------------------------------------------------

def test_analyze_missing_required_field_returns_422(client):
    incomplete_payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "marketing_copy"}

    response = client.post("/analyze", json=incomplete_payload)

    assert response.status_code == 422


def test_analyze_wrong_type_returns_422(client):
    bad_payload = {**VALID_PAYLOAD, "current_price": "not a number"}

    response = client.post("/analyze", json=bad_payload)

    assert response.status_code == 422


def test_analyze_invalid_segment_enum_returns_422(client):
    bad_payload = {**VALID_PAYLOAD, "customer_segment": "extremely_price_sensitive"}  # not a valid enum

    response = client.post("/analyze", json=bad_payload)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Server response sanity
# ---------------------------------------------------------------------------

def test_omitted_elasticity_falls_back_to_segment_default_via_api(client):
    _override_gemini(FakeGeminiClient([VALID_RESPONSE]))
    payload = {**VALID_PAYLOAD}
    del payload["price_elasticity"]  # omitted entirely -> segment default should resolve

    response = client.post("/analyze", json=payload)

    assert response.status_code == 200
    assert response.json()["financials"]["assumptions"]["elasticity_source"] == "segment_default:price_sensitive"


def test_recommended_scenario_field_present_in_api_response(client):
    _override_gemini(FakeGeminiClient([VALID_RESPONSE]))

    response = client.post("/analyze", json=VALID_PAYLOAD)
    financials = response.json()["financials"]

    assert "recommended_scenario" in financials
    flagged = next(s for s in financials["scenarios"] if s["recommended"])
    assert financials["recommended_scenario"] == flagged["name"]


def test_sensitivity_field_present_in_api_response(client):
    _override_gemini(FakeGeminiClient([VALID_RESPONSE]))

    response = client.post("/analyze", json=VALID_PAYLOAD)
    financials = response.json()["financials"]

    assert "sensitivity" in financials
    assert "grid" in financials["sensitivity"]
    assert len(financials["sensitivity"]["grid"]) > 0


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_headers_present_for_configured_origin(client):
    _override_gemini(FakeGeminiClient([VALID_RESPONSE]))
    response = client.post(
        "/analyze", json=VALID_PAYLOAD,
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


# ---------------------------------------------------------------------------
# Fail-fast startup — the whole point of this turn's fix. A missing key
# must prevent the app from ever reaching a serving state, not surface as
# a per-request 500 down the line.
# ---------------------------------------------------------------------------

def test_app_refuses_to_start_without_gemini_api_key():
    had_key = os.environ.pop("GEMINI_API_KEY", None)
    _real_client_singleton.cache_clear()
    try:
        broken_app = FastAPI(lifespan=lifespan)
        broken_app.include_router(app.router)

        with pytest.raises(GeminiAdapterConfigError):
            with TestClient(broken_app):
                pass  # never reached -- lifespan should raise on entry, before any request
    finally:
        if had_key:
            os.environ["GEMINI_API_KEY"] = had_key
        _real_client_singleton.cache_clear()
