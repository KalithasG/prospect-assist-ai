"""DelinquencyRiskAgent (§3.2-4), Eligibility ensemble (§10),
ConversionPropensityAgent (§12, Platt-style calibration), and
EvidenceCompilerAgent (§14/§15).

Phase 1 uses deterministic rule-weighted ensembles with documented
coefficients; XGBoost/CatBoost drop in behind these same interfaces in
Phase 2 once labeled sandbox data exists (spec §10.1, §24.1).
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

from ..config import (DELINQUENCY_FLAG_THRESHOLD, PRODUCT_RULES,
                      SEGMENT_ADJUSTMENT, TIER_INTERESTED,
                      TIER_QUALITY_WATCH, TIER_SERIOUS)


class DelinquencyRiskAgent:
    """Forward-looking early-warning signal from *current* behavior."""

    def score(self, bureau: dict | None, features: dict) -> dict:
        b = bureau or {}
        util = (b.get("card_utilization_pct") or 0) / 100.0
        inq = min((b.get("inquiry_count_90d") or 0) / 6.0, 1.0)
        trend = min(max(b.get("card_utilization_trend") or 0.0, 0.0) / 0.5, 1.0)
        decline = features.get("savings_decline_flag", 0.0)
        risk = min(1.0, 0.35 * util + 0.25 * inq + 0.20 * trend + 0.20 * decline)
        drivers = []
        if util > 0.6:
            drivers.append(f"Rising card utilization at {util:.0%}")
        if (b.get("inquiry_count_90d") or 0) >= 3:
            drivers.append(
                f"Bureau inquiry frequency: {b['inquiry_count_90d']} in 90 days")
        if trend > 0.3:
            drivers.append("Card utilization trending upward over 90 days")
        if decline:
            drivers.append("Declining savings/SIP outflows over recent months")
        return {"early_warning_risk_score": round(risk, 3),
                "risk_drivers": drivers or ["No elevated risk drivers detected"]}


class EligibilityEngine:
    """§10 ensemble: weighted components + hard-floor guardrails + segment
    adjustment. Weights become learned (grid-search CV) in Phase 2."""

    def score(self, segment: str, cap: dict, bureau: dict | None,
              product: str) -> dict:
        b = bureau or {}
        bureau_score = b.get("bureau_score")
        hard_rejects: list[str] = []
        if bureau_score is not None and bureau_score < 500:
            hard_rejects.append("Bureau score below 500 hard floor")
        if cap["foir"] > 0.60:
            hard_rejects.append("FOIR exceeds 60% hard cap")

        bureau_comp = ((bureau_score - 500) / 350 if bureau_score
                       else 0.40)  # neutral-low for thin file
        bureau_comp = max(0.0, min(1.0, bureau_comp))
        surplus_comp = min(1.0, cap["disposable_surplus"]
                           / max(0.30 * cap["estimated_income"], 1))
        components = {
            "income_stability": round(25 * cap["income_stability"], 1),
            "cash_flow_surplus": round(25 * surplus_comp, 1),
            "bureau_strength": round(20 * bureau_comp, 1),
            "obligation_headroom": round(15 * (1 - cap["foir"]), 1),
            "savings_discipline": round(15 * cap["savings_discipline_score"], 1),
        }
        raw = sum(components.values())
        adjusted = raw * SEGMENT_ADJUSTMENT.get(segment, 1.0)
        score = 0.0 if hard_rejects else round(min(adjusted, 100.0), 1)
        rules = PRODUCT_RULES[product]
        meets_product = (score >= rules["min_eligibility"]
                         and cap["estimated_income"] >= rules["min_income"]
                         and cap["foir"] <= rules["max_foir"])
        return {"eligibility_score": score, "components": components,
                "segment_adjustment": SEGMENT_ADJUSTMENT.get(segment, 1.0),
                "hard_reject_reasons": hard_rejects,
                "meets_product_rules": meets_product}


class ConversionPropensityAgent:
    """§12: sigmoid (Platt-style) calibration so output reads as probability.
    Coefficients calibrated on the Phase-1 synthetic persona cohort."""

    A_ELIG, A_INTENT, A_ENG, BIAS = 0.03, 2.2, 1.2, -3.2

    def score(self, eligibility: float, intent: float,
              engagement_recency: float) -> dict:
        z = (self.A_ELIG * eligibility + self.A_INTENT * intent
             + self.A_ENG * engagement_recency + self.BIAS)
        p = 1.0 / (1.0 + math.exp(-z))
        return {"conversion_propensity": round(p, 3),
                "calibration": "platt_sigmoid_v1",
                "confidence_interval": [round(max(0, p - 0.08), 3),
                                        round(min(1, p + 0.08), 3)]}


class EvidenceCompilerAgent:
    """§14/§15: composite score, tier mapping, SHAP-style contributions and
    an RM-readable narrative. Runs in Conductor mode."""

    def compile(self, customer_id: str, product: str, segment: str, cap: dict,
                intent: dict, delinq: dict, conv: dict, elig: dict,
                reflection: dict) -> dict:
        composite = (0.35 * elig["eligibility_score"] / 100
                     + 0.35 * intent["intent_score"]
                     + 0.30 * conv["conversion_propensity"])
        composite = round(composite, 3)
        risk = delinq["early_warning_risk_score"]

        if reflection.get("ntc_low_confidence_gate") or \
                reflection.get("contradiction_flag"):
            tier = "needs_manual_review"
        elif reflection.get("thin_file_promotion"):
            tier = "interested"
        elif risk > DELINQUENCY_FLAG_THRESHOLD:
            tier = "quality_watch"
        elif composite >= TIER_SERIOUS and cap["confidence"] >= 0.6:
            tier = "serious"
        elif composite >= TIER_INTERESTED:
            tier = "interested"
        elif composite >= TIER_QUALITY_WATCH:
            tier = "quality_watch"
        else:
            tier = "not_ready"

        contributions = self._contributions(cap, intent, delinq, elig)
        narrative = self._narrative(customer_id, product, tier, composite,
                                    cap, intent, delinq, conv, reflection)
        return {
            "lead_id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "product": product,
            "segment": segment,
            "tier": tier,
            "composite_score": composite,
            "confidence_level": round(cap["confidence"], 2),
            "estimated_income": cap["estimated_income"],
            "disposable_surplus": cap["disposable_surplus"],
            "intent_score": intent["intent_score"],
            "delinquency_risk_score": risk,
            "conversion_propensity": conv["conversion_propensity"],
            "rm_priority_queue": tier in ("serious", "interested"),
            "scored_at": datetime.now(timezone.utc).isoformat(),
            "evidence_bundle": {
                "capability": cap,
                "intent": intent,
                "delinquency": delinq,
                "conversion": conv,
                "eligibility": elig,
                "contributions": contributions,
                "reflection": reflection,
                "narrative": narrative,
            },
        }

    @staticmethod
    def _contributions(cap, intent, delinq, elig) -> list[dict]:
        rows = [{"feature": k.replace("_", " ").title(), "impact": v}
                for k, v in elig["components"].items()]
        rows.append({"feature": "Intent Signals",
                     "impact": round(intent["intent_score"] * 20, 1)})
        rows.append({"feature": "Delinquency Risk",
                     "impact": round(-delinq["early_warning_risk_score"] * 15, 1)})
        return sorted(rows, key=lambda r: -abs(r["impact"]))

    @staticmethod
    def _narrative(cid, product, tier, composite, cap, intent, delinq, conv,
                   reflection) -> str:
        lines = [f"Customer {cid} is a {tier.replace('_', ' ').upper()} lead "
                 f"for {product.replace('_', ' ').title()} with "
                 f"{conv['conversion_propensity']:.0%} conversion probability."]
        lines += [f"• {s}" for s in cap["signals"][:3]]
        lines += [f"• {s['signal']}" for s in intent["batch_signals"][:3]]
        lines.append(f"• Safe EMI capacity ₹{cap['safe_emi_capacity']:,.0f} "
                     f"supports a loan of ~₹{cap['max_loan_eligibility']:,.0f}")
        if delinq["early_warning_risk_score"] > DELINQUENCY_FLAG_THRESHOLD:
            lines.append("⚠ Elevated early-warning risk: "
                         + "; ".join(delinq["risk_drivers"]))
        if reflection.get("contradiction_flag"):
            lines.append("⚠ Contradictory signals detected — routed to manual "
                         "review by the reflection gate.")
        if reflection.get("enhanced_review_flag"):
            lines.append("⚠ Thin file — flagged for enhanced review.")
        return "\n".join(lines)
