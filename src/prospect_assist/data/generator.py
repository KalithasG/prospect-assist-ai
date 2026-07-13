"""Synthetic dataset generator (spec §18.2).

Rule-based persona generator with randomized noise per trait, seeded for
reproducibility (seed=42). 700 customers across 6 archetypes. Each persona
carries an expected_tier label used ONLY by the eval harness — never fed to
agents at inference time (prevents label leakage).
"""
from __future__ import annotations

import random
from datetime import timedelta

from ..config import ANCHOR_DATE
from ..store import InMemoryStore

ARCHETYPES = [
    ("salaried_high_intent", 150, {"serious"}),
    ("salaried_window_shopper", 200, {"not_ready"}),
    ("gig_worker_high_capacity", 100, {"interested"}),
    ("self_employed_thin_margin", 80, {"quality_watch"}),
    ("ntc_thin_file", 100, {"needs_manual_review", "interested"}),
    ("rising_delinquency_risk", 70, {"quality_watch"}),
]


def _month_ts(months_ago: int, day: int) -> str:
    y, m = ANCHOR_DATE.year, ANCHOR_DATE.month - months_ago
    while m <= 0:
        m += 12
        y -= 1
    return ANCHOR_DATE.replace(year=y, month=m, day=min(day, 28)).isoformat()


def _txn(store, cid, amount, direction, category, narration, months_ago,
         day, channel="netbanking"):
    store.add_transaction({
        "customer_id": cid, "amount": round(amount, 2), "direction": direction,
        "merchant_category": category, "narration": narration,
        "txn_timestamp": _month_ts(months_ago, day), "channel": channel,
        "account_type": "savings", "geo_tag": None})


def generate(store: InMemoryStore, seed: int = 42) -> list[dict]:
    """Seeds the store; returns [{customer_id, archetype, expected_tiers,
    ground_truth_income}] for the eval harness only."""
    rng = random.Random(seed)
    labels: list[dict] = []
    for name, count, expected in ARCHETYPES:
        for i in range(count):
            cid = f"{name}-{i:03d}"
            income = _build(rng, store, name, cid)
            labels.append({"customer_id": cid, "archetype": name,
                           "expected_tiers": expected,
                           "ground_truth_income": income})
    return labels


def _build(rng: random.Random, store: InMemoryStore, name: str,
           cid: str) -> float:
    n = rng.gauss
    if name == "salaried_high_intent":
        income = max(50000, n(90000, 15000))
        store.add_customer({"customer_id": cid, "segment": "salaried",
                            "consent_status": "granted"})
        day = rng.randint(1, 7)
        for m in range(6):
            _txn(store, cid, income * (1 + n(0, 0.01)), "credit", "salary",
                 "NEFT-EMPLOYER-SALARY", m, day)
            _txn(store, cid, income * 0.20, "debit", "rent",
                 "UPI-LANDLORD-RENT", m, day + 1)
            _txn(store, cid, income * 0.06, "debit", "utilities",
                 "BBPS-ELECTRICITY", m, 10)
            _txn(store, cid, income * 0.16, "debit", "living",
                 "POS-GROCERY", m, 12)
            _txn(store, cid, income * max(0.10, n(0.14, 0.03)), "debit",
                 "investment", "ACH-SIP-MF", m, 15)
        _txn(store, cid, rng.uniform(20000, 60000), "debit", "property",
             "UPI-ABC_BUILDERS-PAYMENT", rng.randint(0, 1), 18, "upi")
        store.set_bureau(cid, {"inquiry_count_90d": rng.randint(0, 1),
                               "card_utilization_pct": rng.uniform(20, 50),
                               "card_utilization_trend": 0.0,
                               "active_loans": rng.randint(0, 1),
                               "loans_closed_12m": 0,
                               "bureau_score": rng.randint(720, 800)})
        for d in range(3):
            store.add_engagement(cid, {
                "pages_viewed": ["home_loan", "loan_calculator"],
                "session_duration_seconds": rng.randint(320, 700),
                "eligibility_check_count": 1,
                "session_timestamp": (ANCHOR_DATE - timedelta(days=d + 1)).isoformat()})
        return income

    if name == "salaried_window_shopper":
        income = max(25000, n(42000, 8000))
        store.add_customer({"customer_id": cid, "segment": "salaried",
                            "consent_status": "granted"})
        for m in range(6):
            _txn(store, cid, income * (1 + n(0, 0.02)), "credit", "salary",
                 "NEFT-EMPLOYER-SAL", m, 3)
            _txn(store, cid, income * rng.uniform(0.90, 0.98), "debit",
                 "living", "POS-SHOPPING", m, 12)
        store.set_bureau(cid, {"inquiry_count_90d": 0,
                               "card_utilization_pct": rng.uniform(20, 45),
                               "card_utilization_trend": 0.0,
                               "active_loans": 0, "loans_closed_12m": 0,
                               "bureau_score": rng.randint(650, 730)})
        store.add_engagement(cid, {
            "pages_viewed": ["eligibility_check"],
            "session_duration_seconds": rng.randint(20, 90),
            "eligibility_check_count": 1,
            "session_timestamp": (ANCHOR_DATE
                                  - timedelta(days=rng.randint(35, 90))).isoformat()})
        return income

    if name == "gig_worker_high_capacity":
        base = max(30000, n(55000, 9000))
        store.add_customer({"customer_id": cid,
                            "segment": "gig_self_employed",
                            "consent_status": "granted"})
        for m in range(12):
            monthly = base * (1 + n(0, 0.12))
            _txn(store, cid, monthly * 0.55, "credit", "gig_income",
                 "UPI-ZOMATO-PAYOUT", m, 7, "upi")
            _txn(store, cid, monthly * 0.45, "credit", "gig_income",
                 "UPI-SWIGGY-PAYOUT", m, 21, "upi")
            _txn(store, cid, base * 0.28, "debit", "living", "POS-GROCERY", m, 12)
            _txn(store, cid, base * 0.12, "debit", "fuel", "UPI-HPCL-FUEL",
                 m, 14, "upi")
            _txn(store, cid, base * max(0.20, n(0.28, 0.05)), "debit",
                 "investment", "ACH-RD-DEPOSIT", m, 16)
        turnover = base * 12 * rng.uniform(1.4, 1.9)
        store.set_gst(cid, {"gst_turnover_annual": turnover,
                            "filing_regularity": rng.uniform(0.8, 1.0),
                            "industry_code": "services"})
        store.set_alt_data(cid, {"electricity_avg_monthly_units": rng.uniform(150, 260),
                                 "fuel_spend_monthly": base * 0.12,
                                 "gst_turnover_annual": turnover})
        store.set_bureau(cid, {"inquiry_count_90d": rng.randint(0, 1),
                               "card_utilization_pct": rng.uniform(10, 35),
                               "card_utilization_trend": 0.0,
                               "active_loans": 0, "loans_closed_12m": 0,
                               "bureau_score": rng.choice(
                                   [None, rng.randint(680, 740)])})
        store.add_engagement(cid, {
            "pages_viewed": ["auto_loan", "loan_calculator"],
            "session_duration_seconds": rng.randint(200, 500),
            "eligibility_check_count": 1,
            "session_timestamp": (ANCHOR_DATE
                                  - timedelta(days=rng.randint(1, 6))).isoformat()})
        return base * 0.75  # ground truth ≈ discounted net gig income

    if name == "self_employed_thin_margin":
        base = max(25000, n(40000, 7000))
        store.add_customer({"customer_id": cid,
                            "segment": "gig_self_employed",
                            "consent_status": "granted"})
        for m in range(12):
            monthly = base * (1 + n(0, 0.20))
            _txn(store, cid, monthly, "credit", "gig_income",
                 "UPI-URBANCLAP-PAYOUT", m, rng.randint(3, 25), "upi")
            _txn(store, cid, base * rng.uniform(0.62, 0.80), "debit", "living",
                 "POS-GROCERY", m, 12)
            _txn(store, cid, base * 0.10, "debit", "fuel", "UPI-IOCL-FUEL",
                 m, 14, "upi")
            _txn(store, cid, base * rng.uniform(0.02, 0.06), "debit",
                 "investment", "ACH-RD-DEPOSIT", m, 16)
        store.set_gst(cid, {"gst_turnover_annual": base * 12 * 1.2,
                            "filing_regularity": rng.uniform(0.5, 0.8),
                            "industry_code": "retail"})
        store.set_bureau(cid, {"inquiry_count_90d": rng.randint(1, 3),
                               "card_utilization_pct": rng.uniform(45, 70),
                               "card_utilization_trend": rng.uniform(0.05, 0.2),
                               "active_loans": rng.randint(0, 2),
                               "loans_closed_12m": 0,
                               "bureau_score": rng.randint(600, 690)})
        return base * 0.75

    if name == "ntc_thin_file":
        elec = rng.uniform(120, 300)
        fuel = rng.uniform(2500, 9000)
        store.add_customer({"customer_id": cid, "segment": "new_to_credit",
                            "consent_status": "granted"})
        store.set_bureau(cid, {"inquiry_count_90d": 0,
                               "card_utilization_pct": 0,
                               "card_utilization_trend": 0.0,
                               "active_loans": 0, "loans_closed_12m": 0,
                               "bureau_score": None})
        store.set_alt_data(cid, {"electricity_avg_monthly_units": elec,
                                 "fuel_spend_monthly": fuel,
                                 "gst_turnover_annual": None})
        return 90.0 * elec + 2.2 * fuel

    # rising_delinquency_risk
    income = max(40000, n(72000, 10000))
    store.add_customer({"customer_id": cid, "segment": "salaried",
                        "consent_status": "granted"})
    for m in range(6):
        _txn(store, cid, income, "credit", "salary", "NEFT-EMPLOYER-SALARY", m, 4)
        _txn(store, cid, income * 0.22, "debit", "rent", "UPI-LANDLORD-RENT", m, 5)
        _txn(store, cid, income * 0.30, "debit", "living", "POS-SHOPPING", m, 12)
        _txn(store, cid, max(500.0, income * 0.13 - (5 - m) * income * 0.022),
             "debit", "investment", "ACH-SIP-MF", m, 16)
    store.set_bureau(cid, {"inquiry_count_90d": rng.randint(4, 7),
                           "card_utilization_pct": rng.uniform(82, 96),
                           "card_utilization_trend": rng.uniform(0.3, 0.5),
                           "active_loans": rng.randint(1, 3),
                           "loans_closed_12m": 0,
                           "bureau_score": rng.randint(620, 680)})
    store.add_engagement(cid, {
        "pages_viewed": ["personal_loan", "loan_calculator"],
        "session_duration_seconds": rng.randint(300, 700),
        "eligibility_check_count": rng.randint(2, 4),
        "session_timestamp": (ANCHOR_DATE - timedelta(days=1)).isoformat()})
    return income
