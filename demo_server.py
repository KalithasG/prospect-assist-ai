"""Boots the Phase-1 stack: seeds 700 personas and serves the API.

If the dashboard has been built (dashboard/dist exists), it is served from the
same server at "/" — one URL hosts both the RM console and the scoring API.
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from fastapi.staticfiles import StaticFiles
from prospect_assist.store import InMemoryStore
from prospect_assist.connectors.mock import MockSandboxConnector
from prospect_assist.consent import ConsentService
from prospect_assist.orchestrator import ProspectAssistOrchestrator
from prospect_assist.api.app import create_app
from prospect_assist.data.generator import generate

store = InMemoryStore()
generate(store, seed=42)
consent = ConsentService()
orch = ProspectAssistOrchestrator(MockSandboxConnector(store), consent)
app = create_app(orch, consent, store)

DIST = Path(__file__).parent / "dashboard" / "dist"
if DIST.is_dir():
    # Mounted last so /api, /mock and /docs keep precedence.
    app.mount("/", StaticFiles(directory=DIST, html=True), name="dashboard")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
