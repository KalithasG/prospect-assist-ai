"""TransactionParserAgent (Layer 2, spec §8).

Rule-engine categorization (regex/keyword — the 60%/95% path in §8.1.2) plus
behavioral feature extraction (§8.4). FinBERT handles the ambiguous 30% in
Phase 2; the interface stays identical.
"""
from __future__ import annotations

import re
import statistics
from collections import defaultdict
from datetime import datetime

CATEGORY_RULES: list[tuple[str, str]] = [
    (r"SALARY|PAYROLL|\bSAL\b", "salary"),
    (r"ZOMATO|SWIGGY|UBER|OLA|RAPIDO|URBANCLAP|PORTER|AMAZON.?FLEX", "gig_income"),
    (r"BUILDER|STAMP.?DUTY|REGISTRATION|MAGICBRICKS|99ACRES", "property"),
    (r"MOTORS|DEALER|\bRTO\b|VEHICLE.?INS", "vehicle"),
    (r"HOSPITAL|PHARMACY|DIAGNOSTIC|FORTIS|APOLLO", "medical"),
    (r"JEWELL?ER|TANISHQ|BANQUET|WEDDING", "wedding"),
    (r"SCHOOL|COLLEGE|COACHING|UNIVERSITY|TUITION", "education"),
    (r"\bRENT\b|LANDLORD", "rent"),
    (r"\bEMI\b|HOMELOAN|AUTOLOAN|LOAN.?REPAY", "emi"),
    (r"\bSIP\b|MUTUAL.?FUND|\bFD\b|\bRD\b|DEPOSIT", "investment"),
    (r"INSURANCE|\bLIC\b|PREMIUM", "insurance"),
    (r"ELECTRICITY|BBPS|GAS|WATER|MOBILE|BROADBAND", "utilities"),
    (r"FUEL|PETROL|HPCL|IOCL|BPCL", "fuel"),
    (r"GROCERY|KIRANA|BIGBASKET|DMART", "living"),
]

ESSENTIAL = {"rent", "emi", "insurance", "utilities", "living", "fuel",
             "medical", "education"}
INTENT_CATEGORIES = {"property", "vehicle", "medical", "wedding", "education"}


def categorize(txn: dict) -> str:
    if txn.get("merchant_category"):
        return txn["merchant_category"]
    narr = (txn.get("narration") or "").upper()
    for pattern, cat in CATEGORY_RULES:
        if re.search(pattern, narr):
            return cat
    return "uncategorized"


class TransactionParserAgent:
    """Extracts the §8.4 feature groups from raw transactions."""

    def extract(self, transactions: list[dict]) -> dict:
        monthly_income: dict[tuple, float] = defaultdict(float)
        monthly_by_cat: dict[str, dict[tuple, float]] = defaultdict(
            lambda: defaultdict(float))
        salary_days: list[int] = []
        gig_platforms: set[str] = set()
        intent_txns: list[dict] = []
        months: set[tuple] = set()

        for t in transactions:
            cat = categorize(t)
            ts = datetime.fromisoformat(t["txn_timestamp"])
            key = (ts.year, ts.month)
            months.add(key)
            if t["direction"] == "credit":
                monthly_income[key] += t["amount"]
                if cat == "salary":
                    salary_days.append(ts.day)
                    monthly_by_cat["salary"][key] += t["amount"]
                if cat == "gig_income":
                    monthly_by_cat["gig_income"][key] += t["amount"]
                    m = re.search(r"(ZOMATO|SWIGGY|UBER|OLA|RAPIDO)",
                                  (t.get("narration") or "").upper())
                    if m:
                        gig_platforms.add(m.group(1))
            else:
                monthly_by_cat[cat][key] += t["amount"]
                if cat in INTENT_CATEGORIES:
                    intent_txns.append({"category": cat, "amount": t["amount"],
                                        "narration": t.get("narration"),
                                        "timestamp": t["txn_timestamp"]})

        n_months = max(len(months), 1)

        def avg(cat: str) -> float:
            vals = monthly_by_cat.get(cat, {})
            return sum(vals.values()) / n_months if vals else 0.0

        income_series = [monthly_income[m] for m in sorted(months)] or [0.0]
        mean_inc = statistics.mean(income_series)
        std_inc = statistics.pstdev(income_series) if len(income_series) > 1 else 0.0
        stability = max(0.0, min(1.0, 1 - (std_inc / mean_inc))) if mean_inc else 0.0

        salary_months = monthly_by_cat.get("salary", {})
        salary_regularity = len(salary_months) / n_months if n_months else 0.0
        salary_day_consistent = (len(set(salary_days)) <= 2) if salary_days else False

        inv = monthly_by_cat.get("investment", {})
        sip_consistency = len(inv) / n_months if n_months else 0.0
        inv_series = [inv.get(m, 0.0) for m in sorted(months)]
        savings_decline = 0.0
        if len(inv_series) >= 6:
            early = statistics.mean(inv_series[:3])
            late = statistics.mean(inv_series[-3:])
            if early > 0 and late < early * 0.7:
                savings_decline = 1.0

        return {
            "n_months": n_months,
            "monthly_income_avg": mean_inc,
            "monthly_salary_median": (statistics.median(salary_months.values())
                                      if salary_months else 0.0),
            "salary_regularity": salary_regularity,
            "salary_day_consistent": salary_day_consistent,
            "monthly_gig_income_avg": avg("gig_income"),
            "gig_platform_diversity": len(gig_platforms),
            "income_stability": stability,
            "avg_rent": avg("rent"), "avg_emi": avg("emi"),
            "avg_insurance": avg("insurance"), "avg_utilities": avg("utilities"),
            "avg_living": avg("living"), "avg_fuel": avg("fuel"),
            "avg_investment": avg("investment"),
            "avg_essential": sum(avg(c) for c in ESSENTIAL),
            "sip_consistency": sip_consistency,
            "savings_decline_flag": savings_decline,
            "intent_transactions": intent_txns,
            "has_transactions": bool(transactions),
        }
