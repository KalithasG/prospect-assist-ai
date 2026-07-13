"""Spec §20 BDD scenarios, implemented 1:1 as executable tests (TDD contract)."""
import pytest

from conftest import (build_salaried_high_intent, build_window_shopper,
                      build_gig_worker, build_ntc_thin_file, build_rising_risk,
                      grant_all)


# Scenario: Salaried high-intent customer scores as a serious lead
def test_salaried_high_intent_serious(harness):
    store, _, consent, orch = harness
    cid = build_salaried_high_intent(store)
    token = grant_all(consent, cid)
    lead = orch.score(cid, "home_loan", token)
    assert abs(lead["estimated_income"] - 85000) / 85000 < 0.15
    assert lead["intent_score"] > 0.7
    assert lead["tier"] == "serious"
    signals = str(lead["evidence_bundle"])
    assert "salary" in signals.lower() and "builder" in signals.lower()


# Scenario: Window-shopper is correctly filtered out
def test_window_shopper_not_ready(harness):
    store, _, consent, orch = harness
    cid = build_window_shopper(store)
    token = grant_all(consent, cid)
    lead = orch.score(cid, "personal_loan", token)
    assert lead["conversion_propensity"] < 0.3
    assert lead["tier"] == "not_ready"
    assert lead["rm_priority_queue"] is False


# Scenario: Gig worker surfaced despite no salary slip
def test_gig_worker_not_rejected(harness):
    store, _, consent, orch = harness
    cid = build_gig_worker(store)
    token = grant_all(consent, cid)
    lead = orch.score(cid, "auto_loan", token)
    assert lead["evidence_bundle"]["capability"]["strategy"] == "gig_self_employed"
    assert lead["disposable_surplus"] > 0
    assert lead["tier"] != "not_ready"


# Scenario: NTC thin file uses alt-data proxies, never confident tier
def test_ntc_alt_data_manual_review(harness):
    store, _, consent, orch = harness
    cid = build_ntc_thin_file(store)
    token = grant_all(consent, cid)
    lead = orch.score(cid, "personal_loan", token)
    assert lead["evidence_bundle"]["capability"]["strategy"] == "new_to_credit"
    assert lead["confidence_level"] < 0.6
    assert lead["tier"] == "needs_manual_review"


# Scenario: Consent missing or revoked blocks scoring
def test_missing_consent_blocks(harness):
    store, connector, _, orch = harness
    cid = build_salaried_high_intent(store, "c-noconsent")
    with pytest.raises(orch.ConsentError):
        orch.score(cid, "home_loan", consent_token=None)
    assert connector.call_count == 0  # no data fetched


def test_consent_scope_missing_bureau_blocks(harness):
    store, connector, consent, orch = harness
    cid = build_salaried_high_intent(store, "c-partial")
    token = consent.grant(cid, ["transactions", "upi"])["consent_token"]
    with pytest.raises(orch.ConsentError):
        orch.score(cid, "home_loan", token)
    assert connector.call_count == 0


# Scenario: Rising delinquency risk flags quality_watch even with decent capability
def test_rising_risk_quality_watch(harness):
    store, _, consent, orch = harness
    cid = build_rising_risk(store)
    token = grant_all(consent, cid)
    lead = orch.score(cid, "personal_loan", token)
    assert lead["delinquency_risk_score"] > 0.6
    assert lead["tier"] == "quality_watch"
    drivers = str(lead["evidence_bundle"]["delinquency"]["risk_drivers"]).lower()
    assert "utilization" in drivers and "inquir" in drivers


# Scenario: Connector outage degrades gracefully
def test_connector_outage(harness):
    store, connector, consent, orch = harness
    cid = build_salaried_high_intent(store, "c-outage")
    token = grant_all(consent, cid)
    connector.simulate_outage = True
    with pytest.raises(orch.ConnectorUnavailable):
        orch.score(cid, "home_loan", token)


# Scenario: Contradictory signals trigger the reflection gate
def test_contradiction_reflection_gate(harness):
    store, _, consent, orch = harness
    cid = build_salaried_high_intent(store, "c-contra")
    # overlay high delinquency signals on an otherwise strong profile
    store.set_bureau(cid, {"inquiry_count_90d": 6, "card_utilization_pct": 92,
                           "card_utilization_trend": 0.4, "active_loans": 3,
                           "loans_closed_12m": 0, "bureau_score": 655})
    token = grant_all(consent, cid)
    lead = orch.score(cid, "home_loan", token)
    assert lead["tier"] == "needs_manual_review"
    assert lead["evidence_bundle"]["reflection"]["contradiction_flag"] is True
    eb = lead["evidence_bundle"]
    assert "capability" in eb and "intent" in eb and "delinquency" in eb


# Scenario: Gig worker income estimation with thin GST data (quantified)
def test_gig_thin_gst_income_band(harness):
    store, _, consent, orch = harness
    cid = "c-gig-thin"
    store.add_customer({"customer_id": cid, "segment": "gig_self_employed",
                        "consent_status": "granted"})
    from conftest import add_txn
    for m in range(12):
        add_txn(store, cid, 26000, "credit", "gig_income", "UPI-ZOMATO-PAYOUT", m,
                day=7, channel="upi")
        add_txn(store, cid, 26000, "credit", "gig_income", "UPI-SWIGGY-PAYOUT", m,
                day=21, channel="upi")
        add_txn(store, cid, 8000, "debit", "fuel", "UPI-HPCL-FUEL", m, channel="upi")
        add_txn(store, cid, 15000, "debit", "living", "POS-GROCERY", m)
        add_txn(store, cid, 14000, "debit", "investment", "ACH-RD-DEPOSIT", m)
    store.set_alt_data(cid, {"electricity_avg_monthly_units": 175,
                             "fuel_spend_monthly": 8000, "gst_turnover_annual": None})
    store.set_bureau(cid, {"inquiry_count_90d": 0, "card_utilization_pct": 10,
                           "card_utilization_trend": 0.0, "active_loans": 0,
                           "loans_closed_12m": 0, "bureau_score": None})
    token = grant_all(consent, cid)
    lead = orch.score(cid, "personal_loan", token)
    cap = lead["evidence_bundle"]["capability"]
    assert 35000 <= lead["estimated_income"] <= 42000
    assert cap["income_confidence"] == "Medium"
    assert cap["retained_money_ratio"] is not None
    if cap["retained_money_ratio"] > 0.25:
        assert lead["tier"] == "interested"
        assert lead["evidence_bundle"]["reflection"]["enhanced_review_flag"] is True
