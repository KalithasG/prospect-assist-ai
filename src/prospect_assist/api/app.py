"""Public API (spec §17) — stable across all three phases.

Error mapping per contract: 403 consent, 422 insufficient signal,
503 connector outage.
"""
from __future__ import annotations

import uuid

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..connectors.base import ConnectorUnavailable
from ..consent import ConsentService
from ..orchestrator import ConsentError, ProspectAssistOrchestrator
from ..agents.capability import InsufficientSignal
from ..store import InMemoryStore


class ScoreRequest(BaseModel):
    product: str
    consent_token: str | None = None


class ConsentGrantRequest(BaseModel):
    customer_id: str
    scope: list[str]


class BatchScoreRequest(BaseModel):
    customer_ids: list[str]
    product: str


class FeedbackRequest(BaseModel):
    lead_id: str
    outcome: str
    underwriting_decision: str | None = None


def create_app(orchestrator: ProspectAssistOrchestrator,
               consent_service: ConsentService,
               store: InMemoryStore) -> FastAPI:
    app = FastAPI(title="Prospect Assist AI", version="1.0.0")

    @app.post("/mock/v1/consent/grant")
    def grant_consent(req: ConsentGrantRequest):
        return consent_service.grant(req.customer_id, req.scope)

    @app.post("/api/v1/prospects/{customer_id}/score")
    def score(customer_id: str, req: ScoreRequest):
        try:
            lead = orchestrator.score(customer_id, req.product,
                                      req.consent_token)
        except ConsentError:
            return JSONResponse(status_code=403,
                                content={"error": "Consent not granted or expired"})
        except InsufficientSignal:
            return JSONResponse(status_code=422, content={
                "error": "Insufficient signal to score — thin-file, "
                         "no proxy data available"})
        except ConnectorUnavailable:
            return JSONResponse(status_code=503, content={
                "error": "Upstream data connector unavailable"})
        store.save_lead(customer_id, lead)
        return lead

    @app.get("/api/v1/prospects/{customer_id}/leads")
    def leads(customer_id: str):
        return {"leads": store.get_leads(customer_id)}

    @app.post("/api/v1/prospects/batch-score", status_code=202)
    def batch_score(req: BatchScoreRequest):
        job_id = str(uuid.uuid4())
        store.batch_jobs[job_id] = {"status": "queued", "results_uri": None}
        # Phase 1: synchronous in-process execution (spec §24.3)
        store.batch_jobs[job_id]["status"] = "running"
        results = []
        for cid in req.customer_ids:
            token = consent_service.grant(
                cid, ["transactions", "upi", "bureau", "alt_data"])
            try:
                lead = orchestrator.score(cid, req.product,
                                          token["consent_token"])
                store.save_lead(cid, lead)
                results.append(lead["lead_id"])
            except Exception as exc:  # noqa: BLE001 — batch isolates failures
                results.append({"customer_id": cid, "error": str(exc)})
        store.batch_jobs[job_id] = {"status": "complete",
                                    "results_uri": f"/api/v1/batch-jobs/{job_id}",
                                    "lead_ids": results}
        return {"batch_job_id": job_id, "status": "accepted"}

    @app.get("/api/v1/batch-jobs/{batch_job_id}")
    def batch_status(batch_job_id: str):
        job = store.batch_jobs.get(batch_job_id)
        if not job:
            return JSONResponse(status_code=404, content={"error": "Unknown job"})
        return job

    @app.post("/api/v1/prospects/{customer_id}/feedback")
    def feedback(customer_id: str, req: FeedbackRequest):
        store.record_feedback({"customer_id": customer_id,
                               **req.model_dump()})
        return {"acknowledged": True}

    return app
