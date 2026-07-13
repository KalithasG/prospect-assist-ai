"""Shared fixtures: hand-crafted persona builders for the BDD scenarios (spec §20).

These construct deterministic customers directly in the in-memory store so each
scenario tests exactly the signal pattern the spec describes.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from prospect_assist.store import InMemoryStore
from prospect_assist.connectors.mock import MockSandboxConnector
from prospect_assist.consent import ConsentService
from prospect_assist.orchestrator import ProspectAssistOrchestrator

NOW = datetime(2026, 7, 1)


def month_ts(months_ago: int, day: int = 5) -> str:
    y, m = NOW.year, NOW.month - months_ago
    while m <= 0:
        m += 12
        y -= 1
    return datetime(y, m, min(day, 28)).isoformat()


def add_txn(store, cid, amount, direction, category, narration="", months_ago=0,
            day=5, channel="netbanking"):
    store.add_transaction({
        "customer_id": cid, "amount": float(amount), "direction": direction,
        "merchant_category": category, "narration": narration,
        "txn_timestamp": month_ts(months_ago, day), "channel": channel,
        "account_type": "savings",
    })


def add_secondary_txn(store, cid, amount, direction, category, narration="",
                      months_ago=0, day=5, channel="upi"):
    store.add_secondary_statement({
        "customer_id": cid, "amount": float(amount), "direction": direction,
        "merchant_category": category, "narration": narration,
        "txn_timestamp": month_ts(months_ago, day), "channel": channel,
        "account_type": "savings",
    })


@pytest.fixture()
def store():
    return InMemoryStore()


@pytest.fixture()
def harness(store):
    connector = MockSandboxConnector(store)
    consent = ConsentService()
    orch = ProspectAssistOrchestrator(connector=connector, consent_service=consent)
    return store, connector, consent, orch


FULL_SCOPE = ["transactions", "upi", "bureau", "alt_data", "gst"]


def grant_all(consent, cid):
    return consent.grant(cid, FULL_SCOPE)["consent_token"]


# ---------------- persona builders ----------------

def build_salaried_high_intent(store, cid="c-sal-hi"):
    store.add_customer({"customer_id": cid, "segment": "salaried",
                        "consent_status": "granted"})
    for m in range(6):
        add_txn(store, cid, 85000, "credit", "salary", "NEFT-EMPLOYER_A-SALARY", m, day=5)
        add_txn(store, cid, 18000, "debit", "rent", "UPI-LANDLORD-RENT", m, day=6)
        add_txn(store, cid, 8000, "debit", "emi", "ACH-HDFC-HOMELOAN-EMI", m)
        add_txn(store, cid, 2500, "debit", "insurance", "ACH-LIC-PREMIUM", m)
        add_txn(store, cid, 4500, "debit", "utilities", "BBPS-ELECTRICITY", m)
        add_txn(store, cid, 15000, "debit", "living", "POS-GROCERY", m)
        add_txn(store, cid, 8000, "debit", "investment", "ACH-SIP-MF", m)
    add_txn(store, cid, 25000, "debit", "property", "UPI-ABC_BUILDERS-PAYMENT", 0, channel="upi")
    store.set_bureau(cid, {"inquiry_count_90d": 1, "card_utilization_pct": 45,
                           "card_utilization_trend": 0.0, "active_loans": 1,
                           "loans_closed_12m": 0, "bureau_score": 742})
    for d in range(3):
        store.add_engagement(cid, {"pages_viewed": ["home_loan", "loan_calculator"],
                                   "session_duration_seconds": 420,
                                   "eligibility_check_count": 1,
                                   "session_timestamp": (NOW - timedelta(days=d)).isoformat()})
    return cid


def build_window_shopper(store, cid="c-shopper"):
    store.add_customer({"customer_id": cid, "segment": "salaried",
                        "consent_status": "granted"})
    for m in range(6):
        add_txn(store, cid, 40000, "credit", "salary", "NEFT-EMPLOYER_B-SAL", m)
        add_txn(store, cid, 38500, "debit", "living", "POS-SHOPPING", m)
    store.set_bureau(cid, {"inquiry_count_90d": 0, "card_utilization_pct": 30,
                           "card_utilization_trend": 0.0, "active_loans": 0,
                           "loans_closed_12m": 0, "bureau_score": 690})
    store.add_engagement(cid, {"pages_viewed": ["eligibility_check"],
                               "session_duration_seconds": 45,
                               "eligibility_check_count": 1,
                               "session_timestamp": (NOW - timedelta(days=40)).isoformat()})
    return cid


def build_gig_worker(store, cid="c-gig"):
    store.add_customer({"customer_id": cid, "segment": "gig_self_employed",
                        "consent_status": "granted"})
    for m in range(12):
        add_txn(store, cid, 26000, "credit", "gig_income", "UPI-ZOMATO-PAYOUT", m,
                day=7, channel="upi")
        add_txn(store, cid, 26000, "credit", "gig_income", "UPI-SWIGGY-PAYOUT", m,
                day=21, channel="upi")
        add_txn(store, cid, 12000, "debit", "living", "POS-GROCERY", m)
        add_txn(store, cid, 8000, "debit", "fuel", "UPI-HPCL-FUEL", m, channel="upi")
        add_txn(store, cid, 11000, "debit", "investment", "ACH-RD-DEPOSIT", m)
    store.set_gst(cid, {"gst_turnover_annual": 900000, "filing_regularity": 0.9,
                        "industry_code": "services"})
    store.set_alt_data(cid, {"electricity_avg_monthly_units": 180,
                             "fuel_spend_monthly": 8000, "gst_turnover_annual": 900000})
    store.set_bureau(cid, {"inquiry_count_90d": 1, "card_utilization_pct": 20,
                           "card_utilization_trend": 0.0, "active_loans": 0,
                           "loans_closed_12m": 0, "bureau_score": 705})
    store.add_engagement(cid, {"pages_viewed": ["auto_loan", "loan_calculator"],
                               "session_duration_seconds": 300,
                               "eligibility_check_count": 1,
                               "session_timestamp": (NOW - timedelta(days=2)).isoformat()})
    return cid


def build_ntc_thin_file(store, cid="c-ntc"):
    store.add_customer({"customer_id": cid, "segment": "new_to_credit",
                        "consent_status": "granted"})
    store.set_bureau(cid, {"inquiry_count_90d": 0, "card_utilization_pct": 0,
                           "card_utilization_trend": 0.0, "active_loans": 0,
                           "loans_closed_12m": 0, "bureau_score": None})
    store.set_alt_data(cid, {"electricity_avg_monthly_units": 220,
                             "fuel_spend_monthly": 5500, "gst_turnover_annual": None})
    return cid


def build_rising_risk(store, cid="c-risk"):
    store.add_customer({"customer_id": cid, "segment": "salaried",
                        "consent_status": "granted"})
    for m in range(6):
        add_txn(store, cid, 70000, "credit", "salary", "NEFT-EMPLOYER_C-SALARY", m)
        add_txn(store, cid, 15000, "debit", "rent", "UPI-LANDLORD-RENT", m)
        add_txn(store, cid, 20000, "debit", "living", "POS-SHOPPING", m)
        # declining savings: SIP shrinks over time
        add_txn(store, cid, max(1000, 9000 - (5 - m) * 1500), "debit",
                "investment", "ACH-SIP-MF", m)
    store.set_bureau(cid, {"inquiry_count_90d": 5, "card_utilization_pct": 88,
                           "card_utilization_trend": 0.35, "active_loans": 2,
                           "loans_closed_12m": 0, "bureau_score": 660})
    store.add_engagement(cid, {"pages_viewed": ["personal_loan", "loan_calculator"],
                               "session_duration_seconds": 500,
                               "eligibility_check_count": 3,
                               "session_timestamp": (NOW - timedelta(days=1)).isoformat()})
    return cid
