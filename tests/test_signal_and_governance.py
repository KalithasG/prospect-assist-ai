"""Tests for multi-source signal consumption and consent governance:
multi-account reconstruction, UPI dedupe, the reachable re-segmentation
retry, mortgage/LAP coverage, loan-closure intent, TTL expiry, revocation,
and consent minimization (optional-scope skipping)."""
import pytest
from fastapi.testclient import TestClient

from conftest import (add_txn, add_secondary_txn, build_gig_worker,
                      build_salaried_high_intent, grant_all)
from prospect_assist.api.app import create_app


# Multi-account behavior (§5): income split across two banks is
# reconstructed from primary account + secondary bank statements.
def test_multi_account_income_reconstruction(harness):
    store, _, consent, orch = harness
    cid = "c-two-banks"
    store.add_customer({"customer_id": cid, "segment": "gig_self_employed",
                        "consent_status": "granted"})
    for m in range(12):
        add_txn(store, cid, 26000, "credit", "gig_income",
                "UPI-ZOMATO-PAYOUT", m, day=7, channel="upi")
        add_secondary_txn(store, cid, 26000, "credit", "gig_income",
                          "UPI-SWIGGY-PAYOUT", m, day=21)
        add_txn(store, cid, 12000, "debit", "living", "POS-GROCERY", m)
        add_txn(store, cid, 11000, "debit", "investment", "ACH-RD-DEPOSIT", m)
    store.set_bureau(cid, {"inquiry_count_90d": 0, "card_utilization_pct": 10,
                           "card_utilization_trend": 0.0, "active_loans": 0,
                           "loans_closed_12m": 0, "bureau_score": 700})
    token = grant_all(consent, cid)
    lead = orch.score(cid, "personal_loan", token)
    # Both banks' credits reconstructed: 52,000 gross × 0.75 ≈ 39,000
    assert 35000 <= lead["estimated_income"] <= 42000
    signals = str(lead["evidence_bundle"]["capability"]["signals"])
    assert "2 accounts" in signals


# The UPI endpoint is consumed but deduplicated — no double counting when
# the same transactions appear in both account and UPI feeds.
def test_upi_feed_deduplicated(harness):
    store, _, consent, orch = harness
    cid = build_gig_worker(store)  # all credits carry channel="upi"
    token = grant_all(consent, cid)
    lead = orch.score(cid, "auto_loan", token)
    assert 35000 <= lead["estimated_income"] <= 42000  # not ~78,000


# Reflection recheck: a claimed salaried profile with no salary credits is
# re-segmented to new-to-credit through the bounded retry loop.
def test_retry_reclassifies_claimed_salaried(harness):
    store, _, consent, orch = harness
    cid = "c-claimed-salaried"
    store.add_customer({"customer_id": cid, "segment": "salaried",
                        "consent_status": "granted"})
    for m in range(6):
        add_txn(store, cid, 9000, "debit", "living", "POS-GROCERY", m)
    store.set_bureau(cid, {"inquiry_count_90d": 0, "card_utilization_pct": 0,
                           "card_utilization_trend": 0.0, "active_loans": 0,
                           "loans_closed_12m": 0, "bureau_score": None})
    store.set_alt_data(cid, {"electricity_avg_monthly_units": 200,
                             "fuel_spend_monthly": 5000,
                             "gst_turnover_annual": None})
    token = grant_all(consent, cid)
    lead = orch.score(cid, "personal_loan", token, segment="salaried")
    assert lead["evidence_bundle"]["capability"]["strategy"] == "new_to_credit"
    assert lead["evidence_bundle"]["reflection"]["retries"] >= 1
    assert lead["segment"] == "new_to_credit"


# Mortgage/LAP: gig/business profile scores with GST-registration intent.
def test_mortgage_lap_gig_business(harness):
    store, _, consent, orch = harness
    cid = build_gig_worker(store)
    token = grant_all(consent, cid)
    lead = orch.score(cid, "mortgage_lap", token)
    signals = str(lead["evidence_bundle"]["intent"]["batch_signals"])
    assert "GST-registered" in signals
    assert lead["tier"] in ("interested", "quality_watch", "serious")


# Credit-seeking behavior (§5): a loan closed in the last 12 months is an
# intent signal (repayment proven, capacity freed).
def test_loan_closure_intent_signal(harness):
    store, _, consent, orch = harness
    cid = build_gig_worker(store, "c-gig-closed")
    store.set_bureau(cid, {"inquiry_count_90d": 1, "card_utilization_pct": 20,
                           "card_utilization_trend": 0.0, "active_loans": 0,
                           "loans_closed_12m": 1, "bureau_score": 705})
    token = grant_all(consent, cid)
    lead = orch.score(cid, "auto_loan", token)
    signals = str(lead["evidence_bundle"]["intent"]["batch_signals"])
    assert "Loan closed in last 12 months" in signals


# Consent TTL: an expired token blocks scoring before any data fetch.
def test_consent_ttl_expiry(harness):
    store, connector, consent, orch = harness
    cid = build_salaried_high_intent(store, "c-expired")
    token = consent.grant(cid, ["transactions", "upi", "bureau"],
                          ttl_hours=0)["consent_token"]
    with pytest.raises(orch.ConsentError):
        orch.score(cid, "home_loan", token)
    assert connector.call_count == 0


# Consent revocation via the API blocks subsequent scoring.
def test_consent_revoke_route(harness):
    store, connector, consent, orch = harness
    client = TestClient(create_app(orch, consent, store))
    cid = build_salaried_high_intent(store, "c-revoked")
    token = client.post("/mock/v1/consent/grant", json={
        "customer_id": cid,
        "scope": ["transactions", "upi", "bureau"]}).json()["consent_token"]
    r = client.delete(f"/mock/v1/consent/{token}")
    assert r.status_code == 200 and r.json()["revoked"] is True
    r = client.post(f"/api/v1/prospects/{cid}/score",
                    json={"product": "home_loan", "consent_token": token})
    assert r.status_code == 403


# Consent minimization: without the optional "gst" scope the GST source is
# skipped (no cross-check signal), but scoring still succeeds.
def test_scope_minimization_skips_gst(harness):
    store, _, consent, orch = harness
    cid = build_gig_worker(store, "c-gig-noscope")
    token = consent.grant(
        cid, ["transactions", "upi", "bureau", "alt_data"])["consent_token"]
    lead = orch.score(cid, "auto_loan", token)
    assert 35000 <= lead["estimated_income"] <= 42000  # UPI estimate stands
    assert "GST turnover" not in str(
        lead["evidence_bundle"]["capability"]["signals"])
    full = grant_all(consent, "c-gig-noscope")
    lead_full = orch.score(cid, "auto_loan", full)
    assert "GST turnover" in str(
        lead_full["evidence_bundle"]["capability"]["signals"])
