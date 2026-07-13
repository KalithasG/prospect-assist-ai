"""Regenerates the dashboard's offline snapshot (dashboard/snapshot_data.json).

Scores the full 700-persona cohort through the real pipeline, builds the
same payload the live GET /api/v1/dashboard endpoint serves (KPIs over the
full cohort), and embeds a tier-balanced subset of leads so the fallback
bundle stays small. Run after any scoring or generator change:

    python scripts/export_dashboard_data.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from prospect_assist.store import InMemoryStore
from prospect_assist.connectors.mock import MockSandboxConnector
from prospect_assist.consent import ConsentService
from prospect_assist.orchestrator import ProspectAssistOrchestrator
from prospect_assist.data.generator import ARCH_PRODUCT, generate
from prospect_assist.api import dashboard_payload

PER_TIER = {"serious": 12, "interested": 12, "quality_watch": 10,
            "needs_manual_review": 8, "not_ready": 8}


def main() -> None:
    store = InMemoryStore()
    labels = generate(store, seed=42)
    consent = ConsentService()
    orch = ProspectAssistOrchestrator(MockSandboxConnector(store), consent)
    for row in labels:
        token = consent.grant(row["customer_id"],
                              ["transactions", "upi", "bureau", "alt_data",
                               "gst"])["consent_token"]
        lead = orch.score(row["customer_id"], ARCH_PRODUCT[row["archetype"]],
                          token)
        store.save_lead(row["customer_id"], lead)

    payload = dashboard_payload.build(store.all_leads())
    taken: dict[str, int] = defaultdict(int)
    subset = []
    for lead in payload["leads"]:
        if taken[lead["tier"]] < PER_TIER.get(lead["tier"], 0):
            taken[lead["tier"]] += 1
            subset.append(lead)
    payload["leads"] = subset

    out = ROOT / "dashboard" / "snapshot_data.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    print(f"wrote {out} — kpi over {payload['kpi']['total_scored']} leads, "
          f"{len(subset)} lead views embedded")


if __name__ == "__main__":
    main()
