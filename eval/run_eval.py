"""Evaluation harness — run on the 700-persona synthetic cohort.

Criteria (project contract):
  1. income_estimation_accuracy: within ±15% for >= 80% per segment
  2. lead_tiering_quality: tier match or adjacent-tier match >= 85%
  3. conversion_proxy: > 30% simulated conversion on contacted tiers
  4. ntc_segment_handling: zero NTC 'serious' with confidence < 0.6 (HARD)
  5. trajectory_quality: correct segment strategy chosen; reflection gate
     fires on contradictory personas
  6. safety_and_governance: zero scoring without valid consent
  7. mortgage_lap coverage: gig cohort additionally scored for mortgage_lap

Anti-circularity: ground-truth income and the per-persona will_convert flag
are drawn in the generator *before* observable signals are derived (with
cash-income, underreporting, and proxy noise), so these metrics measure
estimation through a realistic observation model — not the generator's own
formulas. Expect honest numbers below 100%.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prospect_assist.store import InMemoryStore
from prospect_assist.connectors.mock import MockSandboxConnector
from prospect_assist.consent import ConsentService
from prospect_assist.orchestrator import ProspectAssistOrchestrator
from prospect_assist.data.generator import ARCH_PRODUCT, generate

TIER_ORDER = ["not_ready", "quality_watch", "interested", "serious"]
ARCH_STRATEGY = {
    "salaried_high_intent": "salaried",
    "salaried_window_shopper": "salaried",
    "gig_worker_high_capacity": "gig_self_employed",
    "self_employed_thin_margin": "gig_self_employed",
    "ntc_thin_file": "new_to_credit",
    "rising_delinquency_risk": "salaried",
}
FULL_SCOPE = ["transactions", "upi", "bureau", "alt_data", "gst"]
# Secondary product coverage: the gig cohort is a natural mortgage/LAP
# audience (business cash flow + GST registration).
MORTGAGE_LAP_ARCH = "gig_worker_high_capacity"
MORTGAGE_LAP_OK = {"interested", "quality_watch", "serious"}


def adjacent(assigned: str, expected: set[str]) -> bool:
    if assigned in expected:
        return True
    if assigned == "needs_manual_review":
        # manual review is the safe route; count adjacent only when expected
        # set includes it or a middle tier
        return bool(expected & {"needs_manual_review", "quality_watch",
                                "interested"})
    for e in expected:
        if e in TIER_ORDER and assigned in TIER_ORDER:
            if abs(TIER_ORDER.index(e) - TIER_ORDER.index(assigned)) <= 1:
                return True
    return False


def main() -> dict:
    store = InMemoryStore()
    labels = generate(store, seed=42)
    connector = MockSandboxConnector(store)
    consent = ConsentService()
    orch = ProspectAssistOrchestrator(connector, consent)

    income_ok = defaultdict(list)
    tier_ok, tier_exact, tier_total = 0, 0, 0
    strategy_ok = 0
    ntc_violations = 0
    consent_violations = 0
    contacted, converted = 0, 0
    ml_total, ml_ok = 0, 0
    tier_counts = Counter()
    leads = []

    for row in labels:
        cid, arch = row["customer_id"], row["archetype"]
        product = ARCH_PRODUCT[arch]
        # safety check: scoring without consent must fail
        try:
            orch.score(cid, product, consent_token=None)
            consent_violations += 1
        except orch.ConsentError:
            pass
        token = consent.grant(cid, FULL_SCOPE)["consent_token"]
        lead = orch.score(cid, product, token)
        leads.append(lead)
        tier_counts[lead["tier"]] += 1

        gt = row["ground_truth_income"]
        if gt:
            err = abs(lead["estimated_income"] - gt) / gt
            income_ok[ARCH_STRATEGY[arch]].append(err <= 0.15)

        tier_total += 1
        if adjacent(lead["tier"], row["expected_tiers"]):
            tier_ok += 1
        if lead["tier"] in row["expected_tiers"]:
            tier_exact += 1
        if lead["evidence_bundle"]["capability"]["strategy"] == ARCH_STRATEGY[arch]:
            strategy_ok += 1
        if (arch == "ntc_thin_file" and lead["tier"] == "serious"
                and lead["confidence_level"] < 0.6):
            ntc_violations += 1
        if lead["tier"] in ("serious", "interested"):
            contacted += 1
            if row["will_convert"]:
                converted += 1

        # §7 product coverage: score the gig cohort for mortgage_lap too
        if arch == MORTGAGE_LAP_ARCH:
            ml_lead = orch.score(cid, "mortgage_lap", token)
            ml_total += 1
            if ml_lead["tier"] in MORTGAGE_LAP_OK:
                ml_ok += 1

    report = {
        "cohort_size": tier_total,
        "tier_distribution": dict(tier_counts),
        "income_estimation_accuracy_by_segment": {
            seg: round(sum(v) / len(v), 3) for seg, v in income_ok.items()},
        "lead_tiering_quality": round(tier_ok / tier_total, 3),
        "lead_tiering_exact_match": round(tier_exact / tier_total, 3),
        "trajectory_strategy_selection": round(strategy_ok / tier_total, 3),
        "simulated_conversion_proxy": (round(converted / contacted, 3)
                                       if contacted else None),
        "ntc_hard_rule_violations": ntc_violations,
        "consent_gate_violations": consent_violations,
        "mortgage_lap_coverage": {
            "scored": ml_total,
            "tier_in_expected_band": round(ml_ok / ml_total, 3) if ml_total else None,
        },
        "products_covered": sorted(set(ARCH_PRODUCT.values()) | {"mortgage_lap"}),
        "ground_truth_note": (
            "True income and will_convert are drawn before observable signals "
            "are derived (cash income, GST underreporting, proxy noise) — "
            "metrics are estimated through a realistic observation model, "
            "not the generator's own formulas."),
        "pass": {
            "income_accuracy_>=0.80_per_segment": all(
                sum(v) / len(v) >= 0.80 for v in income_ok.values()),
            "tiering_>=0.85": tier_ok / tier_total >= 0.85,
            "conversion_proxy_>0.30": (converted / contacted > 0.30
                                       if contacted else False),
            "ntc_zero_violations": ntc_violations == 0,
            "trajectory_100pct": strategy_ok == tier_total,
            "consent_zero_violations": consent_violations == 0,
            "mortgage_lap_>=0.85": (ml_ok / ml_total >= 0.85
                                    if ml_total else False),
        },
    }
    out = Path(__file__).parent / "eval_report.json"
    out.write_text(json.dumps(report, indent=2))
    leads_out = Path(__file__).parent / "scored_leads.json"
    leads_out.write_text(json.dumps(leads, indent=2, default=str))
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
