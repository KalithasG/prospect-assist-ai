"""IntentAgent (Layer 5, spec §11): "Do they need a loan now?"

Product-specific weighted signal taxonomy (§11.2) + real-time amplification
from digital engagement with the §11.3 decay rule (50% after 7d, 25% after
14d, 0 after 30d).
"""
from __future__ import annotations

from datetime import datetime

from ..config import ANCHOR_DATE


def _decay(days_ago: float) -> float:
    if days_ago <= 7:
        return 1.0
    if days_ago <= 14:
        return 0.5
    if days_ago <= 30:
        return 0.25
    return 0.0


class IntentAgent:
    def detect(self, product: str, features: dict, engagement: list[dict],
               bureau: dict | None) -> dict:
        signals: list[dict] = []
        cats = {t["category"] for t in features["intent_transactions"]}

        def hit(name: str, weight: float) -> None:
            signals.append({"signal": name, "weight": weight})

        if product == "home_loan":
            if "property" in cats:
                hit("Builder payment / stamp duty / registration detected", 25)
            if features["avg_rent"] >= 15000:
                hit(f"Sustained rent of ₹{features['avg_rent']:,.0f}/month "
                    "signals housing need", 15)
            if features["sip_consistency"] >= 0.8 and features["avg_investment"] > 5000:
                hit("Savings accumulation pattern (down-payment capacity)", 15)
        elif product == "auto_loan":
            if "vehicle" in cats:
                hit("Vehicle dealer / RTO / insurance payment detected", 25)
            if features["avg_fuel"] > 6000:
                hit("Elevated fuel spend (vehicle usage pattern)", 10)
        elif product == "personal_loan":
            if "medical" in cats:
                hit("Medical emergency payments detected", 20)
            if "education" in cats:
                hit("Education fee payments detected", 20)
            if "wedding" in cats:
                hit("Wedding-related spend cluster detected", 15)
            if bureau and (bureau.get("card_utilization_pct") or 0) > 80:
                hit(f"Credit card utilization {bureau['card_utilization_pct']:.0f}% "
                    "(consolidation need)", 15)
            if bureau and (bureau.get("inquiry_count_90d") or 0) >= 1:
                hit("Recent bureau inquiry for credit", 10)
        elif product == "mortgage_lap":
            if features["monthly_gig_income_avg"] > 0 or "property" in cats:
                hit("Business cash-flow / property ownership signals", 20)

        batch = sum(s["weight"] for s in signals)

        # Real-time amplification (Tier-3-equivalent signals) with decay
        amp = 0.0
        amp_signals: list[dict] = []
        calc_recent, session_long, elig_repeat = 0.0, 0.0, 0
        for s in engagement:
            days = (ANCHOR_DATE - datetime.fromisoformat(
                s["session_timestamp"])).days
            d = _decay(max(days, 0))
            if d == 0:
                continue
            if any("calculator" in p for p in s.get("pages_viewed", [])):
                calc_recent += d
            if s.get("session_duration_seconds", 0) >= 300:
                session_long = max(session_long, d)
            elig_repeat += s.get("eligibility_check_count", 0) * d
        if calc_recent >= 3:
            amp += 15; amp_signals.append(
                {"signal": "Loan calculator used 3+ times in last 7 days",
                 "weight": 15})
        elif calc_recent >= 1:
            amp += 8; amp_signals.append(
                {"signal": "Recent loan calculator usage", "weight": 8})
        if session_long:
            amp += 8 * session_long; amp_signals.append(
                {"signal": "App session in loan section > 5 minutes",
                 "weight": round(8 * session_long, 1)})
        if elig_repeat >= 2:
            amp += 5; amp_signals.append(
                {"signal": "Repeated eligibility checks", "weight": 5})

        score = min(100.0, batch + amp) / 100.0
        return {"intent_score": round(score, 3), "product": product,
                "batch_signals": signals, "realtime_amplification": amp_signals,
                "amplification_points": round(amp, 1)}
