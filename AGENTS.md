# AGENTS.md — Prospect Assist AI Project Context

## Stack (Phase 1 — Mock Sandbox)
- Language: Python 3.12
- API Framework: FastAPI 0.115.x
- Data Validation: Pydantic v2.x
- Persistence: in-memory store seeded from JSON fixtures (spec §18.2 allows flat JSON fixtures in Phase 1; PostgreSQL 16 arrives with Docker in Phase 2)
- Scoring: deterministic rule-weighted ensembles + sigmoid (Platt-style) calibration in pure Python. XGBoost/CatBoost slots in at Phase 2 behind the same agent interfaces.
- Testing: pytest 8.x — BDD scenarios from specs/001 §20 implemented 1:1 as tests

## Conventions
- PEP 8, Google docstrings on public APIs
- Tests BEFORE implementation (TDD loop: red → green → refactor)
- Every scoring decision emits reason codes + feature contributions (SHAP-style) in evidence_bundle

## Hard Rules
- NEVER commit secrets or API keys
- NEVER bypass the Orchestrator's reflection/evaluation gate
- NEVER auto-tier an NTC customer as "serious" with confidence < 0.6
- NEVER score without a valid consent token (HTTP 403 otherwise; no connector call is made)
- ALWAYS run the full test suite before packaging
- ALWAYS update specs before code when requirements change

## Workflow
1. Read AGENTS.md, then the relevant section of specs/001 before touching a module
2. Write failing tests for the BDD scenario first
3. Implement the smallest thing that passes
4. Run full suite + eval harness (eval/run_eval.py) before shipping

## Guardrails
- max_recursion_depth_per_lead: 3 (spec §15.4)
- consent_token_ttl: 24h
- Connector selection: DATA_CONNECTOR=mock|bank_sandbox|bank_production via factory (spec §16.1)
