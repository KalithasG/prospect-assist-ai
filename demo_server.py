"""Boots the Phase-1 stack: seeds 700 personas, scores the cohort, and
serves the API.

If the dashboard has been built (dashboard/dist exists), it is served from the
same server at "/" — one URL hosts both the RM console and the scoring API,
and the console reads live leads from GET /api/v1/dashboard.
"""
import os
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from fastapi.staticfiles import StaticFiles
from prospect_assist.store import InMemoryStore
from prospect_assist.connectors.mock import MockSandboxConnector
from prospect_assist.consent import ConsentService
from prospect_assist.orchestrator import ProspectAssistOrchestrator
from prospect_assist.api.app import create_app
from prospect_assist.data.generator import ARCH_PRODUCT, generate

store = InMemoryStore()
labels = generate(store, seed=42)
consent = ConsentService()
orch = ProspectAssistOrchestrator(MockSandboxConnector(store), consent)
app = create_app(orch, consent, store)

# Boot-time cohort scoring so the dashboard serves live leads immediately.
# The mock sandbox is its own consent authority for the synthetic personas
# (each carries consent_status="granted"); real customers grant tokens via
# the consent endpoint per request.
_t0 = time.time()
for _row in labels:
    _token = consent.grant(_row["customer_id"],
                           ["transactions", "upi", "bureau", "alt_data",
                            "gst"])["consent_token"]
    _lead = orch.score(_row["customer_id"], ARCH_PRODUCT[_row["archetype"]],
                       _token)
    store.save_lead(_row["customer_id"], _lead)
print(f"Seeded and scored {len(labels)} personas in {time.time() - _t0:.1f}s")

DIST = Path(__file__).parent / "dashboard" / "dist"
if DIST.is_dir():
    # Mounted last so /api, /mock and /docs keep precedence.
    app.mount("/", StaticFiles(directory=DIST, html=True), name="dashboard")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
