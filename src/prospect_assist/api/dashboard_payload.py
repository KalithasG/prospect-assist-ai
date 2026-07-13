"""Transforms scored leads into the dashboard's data contract.

The RM console consumes GET /api/v1/dashboard, whose shape this module owns.
The same transform generates the offline snapshot bundled with the dashboard
(scripts/export_dashboard_data.py), so live and fallback data stay identical
in structure.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

CAVEAT = ("Synthetic 700-persona cohort (seed 42) — upper-bound results; "
          "Phase 2 re-runs this harness on IDBI sandbox data.")

_EVAL_REPORT = Path(__file__).resolve().parents[3] / "eval" / "eval_report.json"


def lead_view(lead: dict) -> dict:
    """Full scored lead (evidence bundle) → compact dashboard lead."""
    eb = lead["evidence_bundle"]
    cap, intent = eb["capability"], eb["intent"]
    reflection = {k: v for k, v in eb["reflection"].items()
                  if v and k != "retries"}
    return {
        "lead_id": lead["lead_id"][:8],
        "customer_id": lead["customer_id"],
        "product": lead["product"],
        "segment": lead["segment"],
        "tier": lead["tier"],
        "composite": lead["composite_score"],
        "confidence": lead["confidence_level"],
        "income": round(lead["estimated_income"]),
        "surplus": round(lead["disposable_surplus"]),
        "intent": lead["intent_score"],
        "risk": lead["delinquency_risk_score"],
        "conv": lead["conversion_propensity"],
        "queue": lead["rm_priority_queue"],
        "afford": cap["affordability_breakdown"],
        "foir": cap["foir"],
        "stability": round(cap["income_stability"], 2),
        "strategy": cap["strategy"],
        "income_conf": cap["income_confidence"],
        "safe_emi": cap["safe_emi_capacity"],
        "max_loan": cap["max_loan_eligibility"],
        "cap_signals": cap["signals"],
        "intent_signals": ([s["signal"] for s in intent["batch_signals"]]
                           + [s["signal"] for s in intent["realtime_amplification"]]),
        "risk_drivers": eb["delinquency"]["risk_drivers"],
        "contrib": eb["contributions"],
        "elig": eb["eligibility"]["eligibility_score"],
        "narrative": eb["narrative"],
        "reflection": reflection,
    }


def _load_eval_report() -> dict | None:
    try:
        return json.loads(_EVAL_REPORT.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def build(all_leads: list[dict], lead_limit: int | None = None) -> dict:
    """Dashboard payload: KPI block over the full cohort + lead views."""
    views = [lead_view(l) for l in all_leads]
    serious = [v for v in views if v["tier"] == "serious"]
    kpi = {
        "total_scored": len(views),
        "tier_distribution": dict(Counter(v["tier"] for v in views)),
        "rm_queue": sum(1 for v in views if v["queue"]),
        "avg_conversion_priority": (
            round(sum(v["conv"] for v in serious) / len(serious), 3)
            if serious else 0.0),
        "avg_estimated_income": (
            round(sum(v["income"] for v in views) / len(views))
            if views else 0),
        "eval": _load_eval_report(),
        "caveat": CAVEAT,
    }
    # Queue-first ordering so a trimmed payload keeps the RM queue intact.
    views.sort(key=lambda v: (not v["queue"], -v["conv"]))
    if lead_limit:
        views = views[:lead_limit]
    return {"kpi": kpi, "leads": views}
