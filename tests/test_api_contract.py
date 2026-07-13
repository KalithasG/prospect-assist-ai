"""Spec §17 API contract tests, exercised through FastAPI TestClient."""
import pytest
from fastapi.testclient import TestClient

from conftest import build_salaried_high_intent, build_ntc_thin_file
from prospect_assist.api.app import create_app
from prospect_assist.store import InMemoryStore
from prospect_assist.connectors.mock import MockSandboxConnector
from prospect_assist.consent import ConsentService
from prospect_assist.orchestrator import ProspectAssistOrchestrator


@pytest.fixture()
def client_env():
    store = InMemoryStore()
    connector = MockSandboxConnector(store)
    consent = ConsentService()
    orch = ProspectAssistOrchestrator(connector=connector, consent_service=consent)
    app = create_app(orchestrator=orch, consent_service=consent, store=store)
    return TestClient(app), store, consent, connector


def _grant(client, cid):
    r = client.post("/mock/v1/consent/grant",
                    json={"customer_id": cid,
                          "scope": ["transactions", "upi", "bureau",
                                    "alt_data", "gst"]})
    assert r.status_code == 200
    return r.json()["consent_token"]


def test_score_endpoint_200(client_env):
    client, store, _, _ = client_env
    cid = build_salaried_high_intent(store)
    token = _grant(client, cid)
    r = client.post(f"/api/v1/prospects/{cid}/score",
                    json={"product": "home_loan", "consent_token": token})
    assert r.status_code == 200
    body = r.json()
    for k in ("lead_id", "tier", "composite_score", "confidence_level",
              "estimated_income", "disposable_surplus", "delinquency_risk_score",
              "evidence_bundle"):
        assert k in body


def test_score_endpoint_403_without_consent(client_env):
    client, store, _, connector = client_env
    cid = build_salaried_high_intent(store, "c-api-403")
    r = client.post(f"/api/v1/prospects/{cid}/score",
                    json={"product": "home_loan", "consent_token": "bogus"})
    assert r.status_code == 403
    assert "Consent" in r.json()["error"]
    assert connector.call_count == 0


def test_score_endpoint_422_thin_file_no_proxy(client_env):
    client, store, _, _ = client_env
    cid = "c-empty"
    store.add_customer({"customer_id": cid, "segment": "new_to_credit",
                        "consent_status": "granted"})
    store.set_bureau(cid, {"inquiry_count_90d": 0, "card_utilization_pct": 0,
                           "card_utilization_trend": 0.0, "active_loans": 0,
                           "loans_closed_12m": 0, "bureau_score": None})
    token = _grant(client, cid)
    r = client.post(f"/api/v1/prospects/{cid}/score",
                    json={"product": "personal_loan", "consent_token": token})
    assert r.status_code == 422
    assert "Insufficient signal" in r.json()["error"]


def test_score_endpoint_503_on_outage(client_env):
    client, store, _, connector = client_env
    cid = build_salaried_high_intent(store, "c-api-503")
    token = _grant(client, cid)
    connector.simulate_outage = True
    r = client.post(f"/api/v1/prospects/{cid}/score",
                    json={"product": "home_loan", "consent_token": token})
    assert r.status_code == 503
    assert "connector unavailable" in r.json()["error"].lower()


def test_leads_history_and_feedback(client_env):
    client, store, _, _ = client_env
    cid = build_salaried_high_intent(store, "c-hist")
    token = _grant(client, cid)
    lead = client.post(f"/api/v1/prospects/{cid}/score",
                       json={"product": "home_loan", "consent_token": token}).json()
    r = client.get(f"/api/v1/prospects/{cid}/leads")
    assert r.status_code == 200
    assert len(r.json()["leads"]) == 1
    r = client.post(f"/api/v1/prospects/{cid}/feedback",
                    json={"lead_id": lead["lead_id"], "outcome": "converted"})
    assert r.status_code == 200 and r.json()["acknowledged"] is True


def test_batch_score_requires_per_customer_consent(client_env):
    client, store, _, _ = client_env
    ids = [build_salaried_high_intent(store, f"c-batch-{i}") for i in range(3)]
    items = [{"customer_id": cid, "consent_token": _grant(client, cid)}
             for cid in ids]
    # one customer with an invalid token — must fail in isolation
    items.append({"customer_id": ids[0], "consent_token": "bogus"})
    r = client.post("/api/v1/prospects/batch-score",
                    json={"items": items, "product": "home_loan"})
    assert r.status_code == 202
    job = r.json()["batch_job_id"]
    r = client.get(f"/api/v1/batch-jobs/{job}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "complete"
    ok = [x for x in body["lead_ids"] if isinstance(x, str)]
    failed = [x for x in body["lead_ids"] if isinstance(x, dict)]
    assert len(ok) == 3 and len(failed) == 1


def test_dashboard_endpoint(client_env):
    client, store, _, _ = client_env
    cid = build_salaried_high_intent(store, "c-dash")
    token = _grant(client, cid)
    client.post(f"/api/v1/prospects/{cid}/score",
                json={"product": "home_loan", "consent_token": token})
    r = client.get("/api/v1/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["kpi"]["total_scored"] == 1
    assert "caveat" in body["kpi"]
    lead = body["leads"][0]
    for k in ("lead_id", "tier", "afford", "contrib", "narrative",
              "intent_signals", "risk_drivers"):
        assert k in lead
