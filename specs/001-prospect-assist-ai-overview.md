# Prospect Assist AI — Comprehensive Solution Specification
## IDBI Innovate 2026 | Track 2: Prospect Assist AI

**Version:** 2.0  
**Date:** 2026-07-02  
**Status:** Design Complete — Architect Mode, Ready for Phase 1 Implementation  
**Classification:** Internal — Hackathon Submission  
**Methodology:** Agentic Engineering Workflow (5-Phase SDLC)  
**Build Phases:** Phase 1 (Mock Sandbox) → Phase 2 (Bank Sandbox) → Phase 3 (AWS Production)  

---

## Table of Contents

1. [How to Read This Spec](#1-how-to-read-this-spec)
2. [Executive Summary](#2-executive-summary)
3. [Problem Statement & Success Criteria](#3-problem-statement--success-criteria)
4. [Design Philosophy & Principles](#4-design-philosophy--principles)
5. [Agentic Engineering Workflow Adoption](#5-agentic-engineering-workflow-adoption)
6. [System Architecture Overview](#6-system-architecture-overview)
7. [Layer 1: Data Aggregation & Ingestion](#7-layer-1-data-aggregation--ingestion)
8. [Layer 2: Transaction Intelligence Engine](#8-layer-2-transaction-intelligence-engine)
9. [Layer 3: Income & Repayment Capacity Assessment](#9-layer-3-income--repayment-capacity-assessment)
10. [Layer 4: Eligibility Scoring Engine](#10-layer-4-eligibility-scoring-engine)
11. [Layer 5: Intent Detection Engine](#11-layer-5-intent-detection-engine)
12. [Layer 6: Conversion Propensity Model](#12-layer-6-conversion-propensity-model)
13. [Layer 7: Product Recommendation Engine](#13-layer-7-product-recommendation-engine)
14. [Layer 8: Underwriting Support Dashboard](#14-layer-8-underwriting-support-dashboard)
15. [Multi-Agent Orchestration & Reflection Loop](#15-multi-agent-orchestration--reflection-loop)
16. [Data Source Abstraction Layer](#16-data-source-abstraction-layer)
17. [API Contract](#17-api-contract)
18. [Mock Sandbox & Synthetic Dataset (Phase 1)](#18-mock-sandbox--synthetic-dataset-phase-1)
19. [Segment-Specific Capability Estimation](#19-segment-specific-capability-estimation)
20. [BDD Specification Scenarios](#20-bdd-specification-scenarios)
21. [Security, Compliance & Governance](#21-security-compliance--governance)
22. [Evaluation Strategy & KPIs](#22-evaluation-strategy--kpis)
23. [Implementation Roadmap](#23-implementation-roadmap)
24. [Technology Stack](#24-technology-stack)
25. [Cost Estimation & Unit Economics](#25-cost-estimation--unit-economics)
26. [Risk Mitigation & Anti-Patterns](#26-risk-mitigation--anti-patterns)
27. [Appendices](#27-appendices)

---

## 1. How to Read This Spec

This document is written to be **executed against** by a human reviewer or an AI coding agent. It follows the **Agentic Engineering Workflow** (5-Phase SDLC) and is structured as a **single source of truth** for implementation, evaluation, and deployment.

### Three Build Phases, One Architecture

| Phase | Trigger | Data Source | Infrastructure |
|:---|:---|:---|:---|
| **Phase 1 — Mock Sandbox** | No bank sandbox access yet | Synthetic mock API + generated datasets, self-hosted | Local / Docker / single-cloud dev environment |
| **Phase 2 — Bank Sandbox** | Shortlisted; IDBI provides sandbox API + synthetic datasets | Real IDBI Bank sandbox APIs (transactions, MSME financials, UPI, bureau) | Same app, connector swapped |
| **Phase 3 — AWS Production** | Post-pilot scale-up | Bank production APIs via Account Aggregator, consent-gated | Full AWS reference architecture |

**The scalability seam:** The **Data Source Abstraction Layer** (§16) ensures every component above it (scoring agents, orchestrator, API) talks to a `BankDataConnector` interface, never to a concrete data source. Swapping Phase 1 → Phase 2 → Phase 3 means swapping the connector implementation and its config — **zero changes to agent logic, scoring models, or the public API contract.**

### Document Conventions

- **Hybrid Markdown + YAML:** Narrative instructions use Markdown; structured configs, schemas, and nested data use YAML.
- **BDD/Gherkin:** All behavioral requirements are specified via `Feature / Scenario / Given / When / Then` (§20).
- **Agentic Harness:** This spec is designed to be consumed by an AI agent within a configured harness (`AGENTS.md`, eval suite, MCP servers).
- **No Source Code:** This document specifies *what* to build and *why* — implementation code is generated in Phase 3 (§23) against this spec.

---

## 2. Executive Summary

**Prospect Assist AI** is an intelligent lead generation and underwriting support system for IDBI Bank's retail lending portfolio. It moves beyond traditional declared-income and credit-score-based screening to a **behavioral, data-driven, multi-agent approach** that combines transaction analytics, real-time intent signals, and machine learning to identify genuinely interested, repayment-capable prospects.

### Target Outcomes

| Metric | Current State | Target State | Delta |
|--------|--------------|-------------|-------|
| Lead-to-Loan Conversion Rate | ~1% | **>30%** | 30x improvement |
| Income Estimation Accuracy | ~60% (declared-based) | **>90%** (inferred) | +50% accuracy |
| Customer Acquisition Cost | Baseline | **-20% to -40%** | Significant reduction |
| Early-Stage Delinquencies | Baseline | **-15%** | Improved risk filtering |
| Loan Processing Time | 5-7 days | **<48 hours** | 60-70% faster |

### Core Value Proposition

> **"We don't ask customers what they earn. We infer what they can actually repay — and whether they genuinely need a loan right now."**

The system achieves this through three pillars:
1. **Actual Income Inference** — From transaction patterns, not salary slips
2. **Behavioral Intent Detection** — From spending patterns, life events, and digital engagement
3. **Conversion Propensity Prediction** — From historical patterns and real-time signals

### Why Multi-Agent Instead of One Scoring Model

| Reason | Explanation |
|:---|:---|
| **Auditability** | Underwriting-adjacent decisions must show *which signal drove which sub-score*. Five narrow agents each produce their own inputs/outputs, creating an evidence trail a single black-box model cannot. |
| **Segment Heterogeneity** | Salaried, gig/self-employed, and NTC customers need structurally different income-estimation logic. Separating the Capability Agent's estimation *strategy* per segment is cleaner than one model with segment as a feature. |
| **Independent Evolution** | Bureau-inquiry-based risk logic changes on a different cadence than UPI-merchant-category intent logic. Decoupled agents let each evolve/retrain independently. |
| **Graceful Degradation** | If bureau data is thin (NTC case), the Capability Agent falls back to proxy signals instead of the whole pipeline failing. |
| **Reflection Gate** | A monolithic model cannot catch its own contradictions. The Orchestrator's Reflect/Evaluate loop (§15) explicitly flags low-confidence or contradictory outputs before they reach an RM. |

---

## 3. Problem Statement & Success Criteria

### 3.1 Problem Decomposition

IDBI Bank's retail lending faces a fundamental triad of challenges:

```
┌─────────────────────────────────────────────────────────────────────┐
│  CHALLENGE 1: LOW CONVERSION                                      │
│  Window shoppers check eligibility but never apply.               │
│  → Need: Distinguish genuine interest from casual browsing.       │
├─────────────────────────────────────────────────────────────────────┤
│  CHALLENGE 2: LIMITED INCOME VISIBILITY                         │
│  Declared income ≠ actual repayment capacity.                     │
│  → Need: Infer actual income from cash flows and behavior.          │
├─────────────────────────────────────────────────────────────────────┤
│  CHALLENGE 3: ONE-SIZE-FITS-ALL UNDERWRITING                      │
│  Salaried, gig workers, and self-employed assessed identically.   │
│  → Need: Segment-specific assessment models.                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Core Objectives (from Problem Statement §4)

1. **Assess true repayment capacity** — Move beyond salary-slip income and simple FOIR to a behavior-derived affordability estimate.
2. **Tier leads** (e.g. *serious / interested / quality-watch / not-ready*) so RMs triage effort correctly.
3. **Handle non-standard income segments** — Gig workers, self-employed, and new-to-credit (NTC) customers without conventional salary/bureau data.
4. **Predict forward-looking risk** — Provide a suggestive/early-warning signal for potential delinquency based on current spending patterns, not just historical bureau data.

### 3.3 Non-Goals (Explicitly Out of Scope)

- **Final underwriting/credit-sanction decisioning** — This system produces a **decision-support score + evidence bundle**, not an auto-approval. A human underwriter always makes the final call (see §21.3, human-in-the-loop gate).
- **Bureau score computation or credit bureau integration logic itself** — Treated as an upstream signal source, mocked in Phase 1 (§18).
- **Loan servicing, disbursement, or collections workflows.**
- **Building a production core-banking integration in Phase 1** — That is Phase 2/3 work, explicitly designed for but not implemented yet.
- **Fraud detection and AML monitoring** — Separate domain, different data and regulations; flagged as Phase 2 enhancement.

### 3.4 Success Criteria (Evaluable)

| ID | Criterion | Measurement | Target | Priority |
|----|-----------|-------------|--------|----------|
| SC-01 | Lead-to-Loan Conversion Rate | (# Loans Disbursed / # Leads Generated) × 100 | >30% | P0 |
| SC-02 | Income Estimation Accuracy | MAPE vs. Ground Truth (synthetic or verified) | <15% | P0 |
| SC-03 | Lead Quality Precision | Precision@K for "serious" tier | >85% | P0 |
| SC-04 | Lead Tiering Quality | Tier match or adjacent-tier match on eval set | >=85% | P0 |
| SC-05 | Explainability Coverage | % of scores with human-readable reason codes + SHAP | 100% | P1 |
| SC-06 | Bias Detection | Disparate impact ratio across demographic segments | >0.80 | P1 |
| SC-07 | Inference Latency | P95 time from request to scored lead | <5s | P2 |
| SC-08 | System Availability | Uptime for scoring pipeline | >99.5% | P2 |
| SC-09 | Safety & Governance | Zero scoring without valid consent; zero bypass of eval gate | Zero violations | P0 |
| SC-10 | NTC Segment Handling | No NTC customer auto-tiered "serious" with confidence < 0.6 | 100% compliance | P0 |

---

## 4. Design Philosophy & Principles

### 4.1 Guiding Principles

| Principle | Rationale | Implementation |
|-----------|-----------|----------------|
| **Predict with ML, Explain with LLM** | Regulatory and trust requirement | XGBoost/CatBoost for scores; LLM for narratives |
| **Memory is Architecture** | Learning from past outcomes improves future predictions | 6-tier memory stack with episodic learning (§6.3) |
| **Segment-Specific, Not Universal** | Gig workers and salaried employees have fundamentally different financial signatures | Separate feature pipelines and agent strategies per segment |
| **Explainable by Default** | RBI fair lending guidelines require auditable decisions | SHAP values + reason codes + LLM narrative for every score |
| **Uncertainty-Aware** | No model is perfect; confidence matters | Calibrated probabilities with confidence intervals; Orchestrator routes low-confidence cases to manual review |
| **Real-Time + Batch Hybrid** | Intent is fleeting; behavior is historical | Redis cache for real-time; data lake for batch |
| **Spec-Driven, Test-First** | Generation is solved; verification is the bottleneck | BDD scenarios written before code; failing tests before implementation |

### 4.2 Agentic Engineering Alignment

This solution is designed using the **Agentic Engineering Workflow** with five phases (§5). Every module references its spec; every agent has a defined role, memory tier, and evaluation rubric.

```
Phase 1: Requirements & Harness Setup
    → specs/ directory with formal BDD specifications (this document)
    → AGENTS.md with banking-specific guardrails
    → Evaluation strategy defined BEFORE implementation

Phase 2: Design & Architecture
    → Multi-agent decomposition (6 specialized agents + Orchestrator)
    → Context engineering (static rules + dynamic RAG)
    → Memory tier selection per data velocity

Phase 3: Implementation (Spec-Driven)
    → Test-first: failing tests before model code
    → Orchestrator mode for bulk scoring; Conductor mode for edge cases
    → No YOLO mode — every module references its spec

Phase 4: Testing & Evaluation
    → Output evaluation (accuracy, bias, latency)
    → Trajectory evaluation (did the agent read the spec first?)
    → Regression suite for model drift detection

Phase 5: Review, Deploy & Maintain
    → Human-in-the-loop for high-risk cases
    → Continuous learning from Tier 4 episodic memory
    → Token cost attribution per feature/module
```

---

## 5. Agentic Engineering Workflow Adoption

### 5.1 Phase 1: Requirements & Harness Setup (This Document)

#### 5.1.1 Project Specification (`specs/`)

This document serves as the root spec. It uses **Hybrid Markdown + YAML**:
- Narrative instructions → Markdown (headers anchor agent attention)
- Structured configs, schemas, nested data → YAML (superior parsing accuracy for deep nesting)
- BDD/Gherkin for behavior specs: `Scenario / Given / When / Then` (§20)

**Directory structure (to be scaffolded by implementation agent):**
```
specs/
├── 001-prospect-assist-ai-overview.md      # This document
├── 002-api-contract.yml                    # API schemas (YAML for nesting > 3 levels)
├── 003-auth-and-consent-spec.md            # Consent & auth BDD specs
├── 004-data-model.yml                      # Database schemas & relationships
├── 005-agent-orchestration-spec.md         # Multi-agent loop & reflection gate
├── 006-segment-strategies-spec.md          # Salaried / gig / NTC logic
├── 007-evaluation-strategy.md              # Eval rubrics and success criteria
└── 008-security-baseline.md                # 7-pillar security controls
```

#### 5.1.2 Configure the Harness (`AGENTS.md`)

Create `AGENTS.md` at repo root. Start with 10 lines; add a rule every time the agent does something it shouldn't.

**Template:**
```markdown
# AGENTS.md — Prospect Assist AI Project Context

## Stack
- Language: Python 3.12
- API Framework: FastAPI 0.115.x
- Data Validation: Pydantic v2.9.x
- Relational Store: PostgreSQL 16
- Containerization: Docker 27.x, docker-compose for Phase 1
- Testing: pytest 8.x + pytest-bdd 8.x

## Conventions
- Code style: PEP 8, black formatter
- Testing: Minimum 80% coverage; BDD scenarios executed via pytest-bdd
- Documentation: Google docstrings for all public APIs
- Commit messages: Conventional Commits

## Hard Rules
- NEVER commit secrets or API keys
- NEVER skip error handling on external API calls (connector layer)
- NEVER modify database schema without migration
- NEVER bypass the Orchestrator's reflection/evaluation gate
- NEVER auto-tier an NTC customer as "serious" with confidence < 0.6
- ALWAYS run tests before committing
- ALWAYS write tests BEFORE implementation
- ALWAYS update specs BEFORE code when requirements change
- ALWAYS emit SHAP values + reason codes for every scoring decision
- ALWAYS enforce consent-token validation before data access

## Workflow
1. Read `AGENTS.md` before starting
2. Check existing patterns in `/src/examples/`
3. Read the relevant spec file before implementing any module
4. Write tests before implementation
5. Run full test suite before submitting
6. Update documentation for public APIs

## Architecture
- See `/specs/` for all design documents
- See `/docs/api/` for OpenAPI specs
- See `/docs/patterns/` for design patterns

## Guardrails
- Max tokens per interaction: 4000
- Allowed tools: MCP servers for PostgreSQL (read-only dev), mock sandbox API
- Forbidden operations: `rm -rf`, direct prod DB writes, credential hardcoding
- Scoring request timeout: 30s
- Max recursion depth per lead: 3
```

#### 5.1.3 Design Evaluation Strategy (Before Implementation)

Define what "correct" means BEFORE code generation begins.

**Eval Rubric (7 Dimensions):**

| Dimension | Question | Evaluator |
|:---|:---|:---|
| Intent Satisfaction | Did it build what the user *meant*? | LLM-as-Judge |
| Functional Correctness | Does it build, run, pass tests? | Automated testing (pytest) |
| Visual/Behavioral Correctness | Does the dashboard match spec? | Browser testing + multimodal judge |
| Cost & Efficiency | Token spend, latency, iterations? | Observability (CloudWatch) |
| Code Quality & Conventions | Match project idioms and patterns? | Linters + LLM-as-Judge |
| Trajectory Quality | Sensible path: read spec first, edit second? | Trajectory inspection |
| Self-Repair Behaviour | Recover from failures or compound them? | Trajectory inspection |

**Create eval cases BEFORE generating code:**
```yaml
eval_cases:
  - case_id: "salary_income_est_001"
    input: "Implement salaried income estimation per specs/006-segment-strategies-spec.md Scenario 1"
    expected_skill: "income-estimator-agent"
    expected_tool_calls:
      - tool: "read_file"
        args: { path: "specs/006-segment-strategies-spec.md" }
      - tool: "write_file"
        args: { path: "src/agents/capability_agent.py" }
    expected_output_format: "passing_tests_with_documentation"
    rubric:
      - "reads spec first"
      - "writes tests before code"
      - "handles edge cases (missing salary, variable dates)"
      - "emits confidence score alongside estimate"
```

#### 5.1.4 Security Baseline (7 Pillars)

Applied BEFORE any code is generated:

| Pillar | Control | Implementation |
|:---|:---|:---|
| **Infrastructure** | Ephemeral sandboxes | Docker containers per scoring session; data wiped after decision |
| **Data** | Least privilege | CMEK at rest, mTLS in transit, tenant-partitioned stores |
| **Model** | Prompt integrity | Version-control all prompts, cryptographic attestation of model artifacts |
| **App & Runtime** | LLM firewalls + hooks | Dynamic filtering, deterministic lifecycle hooks, SAST in CI/CD |
| **IAM** | Zero Ambient Authority | Per-agent scoped credentials, JIT downscoped tokens, file-tree allowlists |
| **Observability** | OpenTelemetry + ABA | Trace all tool calls, token metering, Agent Behavioural Analytics |
| **Governance** | Immutable audit trails | RBI compliance, Logic Reviews, Risk-Stratified Attestation |

**Security checklist for Phase 1:**
- [ ] Sandbox configured (Docker / container)
- [ ] Network egress governance enforced
- [ ] No credentials in prompts or scripts (use `.env` + secret manager)
- [ ] `policies.yaml` created with role/env-based tool permissions
- [ ] File-tree allowlists with deny-by-default rules
- [ ] OpenTelemetry tracing enabled
- [ ] Consent-token expiry enforced server-side

#### 5.1.5 Tool Inventory & MCP Setup

**Principle:** Consume before you build. Search existing MCP servers before writing custom wrappers.

**Decision Tree:**
```
Is the task bounded and deterministic?
    ├── YES ──▶ Use MCP Tool
    └── NO ──▶ Does it require multi-turn collaboration?
                  ├── YES ──▶ Use A2A Agent
                  └── NO ──▶ Use A2A with single-turn
```

**MCP Setup Steps:**
1. **Discovery:** Search `registry.modelcontextprotocol.io`, official Google MCP servers
2. **Audit:** Review code of public MCP servers before connection (security risk)
3. **Configure:** Use `.env` for credentials; define read/write permissions
4. **Connect:** Run MCP Inspector to verify handshake, list tools, validate schemas
5. **Integrate:** Add MCP config to agent harness

**MCP Best Practices:**
- [ ] Use read-only mode for production data access
- [ ] Include Human-in-the-Loop (HITL) for sensitive operations
- [ ] Log all tool usage for audit trails
- [ ] Never use public MCPs in production without vetting

### 5.2 Phase 2: Design & Architecture (This Document)

#### 5.2.1 Architectural Decisions (Human-Confirmed)

- **Consistency vs. Availability:** Favor consistency for scoring decisions (financial correctness > speed); availability handled via graceful degradation.
- **Monolithic vs. Multi-Agent:** Distributed multi-agent with A2A protocol. Justification: segment heterogeneity, independent evolution, auditability.
- **Batch vs. Real-Time:** Hybrid. Batch for nightly cohort re-scoring; real-time for individual prospect scoring triggered by digital engagement.

#### 5.2.2 Context Engineering

**The Six Types of Agent Context:**

| Type | Description | Static or Dynamic? |
|:---|:---|:---|
| Instructions | Roles, goals, boundaries | Static (AGENTS.md, system prompts) |
| Knowledge | Documents, diagrams, domain data | Dynamic (RAG from spec files) |
| Memory | Session logs, persistent state | Both (Tier 1-6 stack) |
| Examples | Few-shot demos, reference patterns | Dynamic (skill definitions) |
| Tools | APIs, scripts, external services | Dynamic (MCP servers, connectors) |
| Guardrails | Hard constraints, safety rules | Static (policies.yaml, AGENTS.md hard rules) |

**Balance static vs. dynamic:**
- **Static (always loaded):** System instructions, `AGENTS.md`, global memory, core guardrails (~high token cost, reliable)
- **Dynamic (loaded on demand):** Skills, tool results, RAG retrievals (~low per-turn cost, scalable)

### 5.3 Phase 3: Implementation (Spec-Driven)

#### 5.3.1 Mode Selection: Conductor vs. Orchestrator

| Dimension | Conductor Mode | Orchestrator Mode |
|:---|:---|:---|
| Style | Real-time, synchronous, in-IDE | Asynchronous, high-level, multi-agent |
| Control | Keystroke-level, immediate feedback | Goal-level, delayed feedback |
| Best For | Exploratory coding, complex logic, debugging | Feature implementation, well-defined tasks |
| Risk | Can become bottleneck if directing every keystroke | Requires strong specs and evals |

**Rule:** Use Conductor for architecture and debugging; use Orchestrator for well-specified feature implementation.

#### 5.3.2 Spec-Driven Implementation Rules

1. **NO YOLO MODE.** The agent must propose folder structure, tech stack, and architecture for human confirmation before writing code.
2. Reference the relevant spec file in every prompt.
3. Instruct the agent to match existing code style, naming patterns, and error handling.
4. For multi-file changes, require manual confirmation of diffs before application.
5. Update the spec *before* updating the code if requirements change.
6. Include exact version numbers for all libraries.

#### 5.3.3 Test-First Development

- Force the agent to produce a **failing unit test** or reproduction `curl` command BEFORE any fix or feature.
- Embed these tests into the codebase permanently (regression guard).
- The agent must fix only the root cause. No "cleanup" of unrelated code.
- Variable renaming is a separate task, never bundled with a bug fix.

#### 5.3.4 The 80% Problem Awareness

- AI generates ~80% of code rapidly.
- Remaining 20% (edge cases, error handling, integration, subtle correctness) demands deep contextual knowledge.
- **Practical posture:** Write tests and evals BEFORE generating code; review every line that will ship; be skeptical of anything that looks clever.

### 5.4 Phase 4: Testing & Evaluation

#### 5.4.1 Output Evaluation
- Does the code compile? Do tests pass? Does it meet the specification?
- Use automated functional testing: build, test suite, linters (pytest, mypy, black)
- Plug into CI pipeline

#### 5.4.2 Trajectory Evaluation
- Did the agent take the right steps?
- Did it choose the right tools?
- Did it skip verification steps?
- Was the reasoning sound?

**Trajectory Scoring Modes:**
| Mode | Use Case | Best For |
|:---|:---|:---|
| EXACT | Exact order of tool calls | High-stakes, deterministic workflows |
| IN_ORDER | Ordered subset | Action-allowed skills |
| ANY_ORDER | Unordered subset | Read-only skills |

> **Key Insight:** Final-output-only scoring passes 20-40% more cases than trajectory-aware scoring. That gap = correct answer via incorrect tool sequence. Acceptable for read-only; critical for action-allowed.

#### 5.4.3 Continuous Quality Flywheel

1. Evaluate against benchmark suite
2. Diagnose failures by clustering root causes
3. Optimize prompts/tools that caused failures
4. Verify fixes against regression suite
5. Monitor production traffic for new failure modes

### 5.5 Phase 5: Review, Deploy & Maintain

#### 5.5.1 AI-Assisted Code Review
- AI as first-pass reviewer (bugs, style, security, performance)
- Human review for design, maintainability, strategic alignment
- Extra scrutiny for: hallucinated dependencies, inadequate error handling, subtle correctness gaps

#### 5.5.2 Deployment
- AI monitors deployment health
- Automatic rollback on failure
- **HITL gates for:** production deployments, DB schema migrations, financial transactions, bulk data exports

#### 5.5.3 Maintenance & Evolution
- AI navigates legacy codebases
- Systematic migration and modernization
- Weekly Agent Insight Sessions: share patterns discovered by AI

---

## 6. System Architecture Overview

### 6.1 High-Level System Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL DATA SOURCES                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ IDBI CBS │  │ UPI Data │  │ Credit   │  │ AA       │  │ Web/App      │  │
│  │ (CASA)   │  │ (NPCI)   │  │ Bureau   │  │ Framework│  │ Analytics    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       │             │             │             │               │          │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┼──────────┘
        │             │             │             │               │
        ▼             ▼             ▼             ▼               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    DATA SOURCE ABSTRACTION LAYER (§16)                     │
│                         BankDataConnector Interface                          │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │  MockSandboxConnector (Phase 1)  │  BankSandboxConnector (Phase 2)   │     │
│  │  BankProductionConnector (Phase 3)                                  │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION LAYER (Layer 1)                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  Batch Pipeline (Airflow)          │  Real-Time Pipeline (Kafka/Redis) │   │
│  │  • Daily transaction dumps         │  • Web engagement events         │   │
│  │  • Monthly bureau updates          │  • UPI transaction streams       │   │
│  │  • GST/AA data refresh             │  • App session telemetry         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     TRANSACTION INTELLIGENCE ENGINE (Layer 2)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Transaction│  │ Merchant   │  │ Life Event │  │ Behavioral          │  │
│  │ Categorizer│  │ Mapping    │  │ Detector   │  │ Feature Extractor   │  │
│  │ (FinBERT)  │  │ Engine     │  │ (Rules+ML) │  │ (Statistical)       │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                  INCOME & REPAYMENT CAPACITY (Layer 3)                       │
│  ┌────────────────────────────┐  ┌────────────────────────────────────────┐ │
│  │  Actual Income Estimation  │  │  Affordability & Surplus Calculator    │ │
│  │  • Salaried: Salary regex  │  │  • Fixed Obligations (rent, EMI, etc.) │ │
│  │  • Self-Employed: GST+Cash │  │  • Discretionary Spend                 │ │
│  │  • Gig Worker: UPI inflow  │  │  • Monthly Surplus                     │ │
│  │    + platform patterns       │  │  • Safe EMI Capacity                   │ │
│  └────────────────────────────┘  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────────┐  │
│  │ ELIGIBILITY SCORE    │  │ INTENT DETECTION     │  │ CONVERSION         │  │
│  │ (Layer 4)            │  │ (Layer 5)            │  │ PROPENSITY         │  │
│  │                      │  │                      │  │ (Layer 6)          │  │
│  │ XGBoost Ensemble     │  │ CatBoost Classifier  │  │ Calibrated         │  │
│  │ • Creditworthiness   │  │ • Product-specific   │  │ Probability        │  │
│  │ • Income Stability   │  │   intent signals     │  │ • Eligibility ×    │  │
│  │ • Cash Flow Strength │  │ • Life events        │  │   Intent ×         │  │
│  │ • Debt Burden        │  │ • Engagement score   │  │   Relationship     │  │
│  │ • Relationship Value │  │ • Bureau inquiries   │  │   Value            │  │
│  └──────────────────────┘  └──────────────────────┘  └────────────────────┘  │
│         │                        │                        │                    │
│         └────────────────────────┼────────────────────────┘                    │
│                                  ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    LEAD QUALITY TIER CLASSIFICATION                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ HIGH        │  │ MEDIUM      │  │ LOW         │  │ REJECT      │  │   │
│  │  │ QUALITY     │  │ QUALITY     │  │ QUALITY     │  │ / REFER     │  │   │
│  │  │ Lead Score  │  │ Lead Score  │  │ Lead Score  │  │ Lead Score  │  │   │
│  │  │ >70         │  │ 40-70       │  │ <40         │  │ <20 or      │  │   │
│  │  │             │  │             │  │             │  │ Bias Flag   │  │   │
│  │  │ → Priority  │  │ → Nurture   │  │ → Drip      │  │ → Manual    │  │   │
│  │  │   RM Call   │  │   Campaign  │  │   Campaign  │  │   Review    │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────┐  ┌──────────────────────────────────────────────┐  │
│  │ PRODUCT              │  │ UNDERWRITING SUPPORT DASHBOARD (Layer 8)     │  │
│  │ RECOMMENDATION       │  │                                              │  │
│  │ (Layer 7)            │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│  │                      │  │  │ Income   │  │ Risk     │  │ Explain- │   │  │
│  │ Match customer       │  │  │ Assessment│  │ Assessment│  │ ability  │   │  │
│  │ behavior to best     │  │  │ Panel    │  │ Panel    │  │ Panel    │   │  │
│  │ loan product          │  │  │          │  │          │  │          │   │  │
│  └──────────────────────┘  │  │ • Declared│  │ • Bureau │  │ • SHAP   │   │  │
│                              │  │   Income  │  │   Score  │  │   Values │   │  │
│                              │  │ • Estimated│  │ • Delinq │  │ • Reason │   │  │
│                              │  │   Income  │  │   Risk   │  │   Codes  │   │  │
│                              │  │ • Confidence│  │ • Fraud  │  │ • LLM    │   │  │
│                              │  │   Score   │  │   Flags  │  │   Narrative│  │
│                              │  └──────────┘  └──────────┘  └──────────┘   │  │
│                              └──────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Multi-Agent Orchestration Overlay

The 8-layer architecture above is implemented by **6 specialized agents** coordinated by a **ProspectAssistOrchestrator**. Each agent maps to one or more layers:

| Agent | Layers | Question | Mode |
|:---|:---|:---|:---|
| **CapabilityAgent** | Layer 3 | "Can they repay?" | Orchestrator (batch) |
| **IntentAgent** | Layer 5 | "Do they need a loan now?" | Orchestrator (batch + real-time) |
| **DelinquencyRiskAgent** | Layer 4 (risk component) | "What is the forward-looking risk signal?" | Orchestrator (batch) |
| **ConversionPropensityAgent** | Layer 6 | "Will they convert if approached now?" | Orchestrator (batch) |
| **EvidenceCompilerAgent** | Layer 8 | "Assemble explainable lead record" | Conductor (narrative generation) |
| **TransactionParserAgent** | Layer 2 | "Extract structured features from raw data" | Orchestrator (batch) |
| **ProspectAssistOrchestrator** | All | "Plan → Execute → Reflect → Evaluate → Publish" | Conductor (loop control) |

### 6.3 The 6-Tier Memory Stack

The system is **not stateless**. Every agent reads from and writes to a tiered memory architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TIER 1: WORKING MEMORY (Active Reasoning)                                │
│  Content: Current customer session, active RM conversation context          │
│  Latency: <1ms | Lifetime: Session | Technology: In-memory (RAM)          │
├─────────────────────────────────────────────────────────────────────────────┤
│  TIER 2: SCRATCHPAD MEMORY (Intermediate Reasoning)                       │
│  Content: Chain-of-thought for complex cases (e.g., gig worker income)      │
│  Latency: <5ms | Lifetime: Minutes | Technology: Temporary buffers        │
├─────────────────────────────────────────────────────────────────────────────┤
│  TIER 3: CONTEXT CACHE (Fast Recent Retrieval)                            │
│  Content: Real-time intent signals, web engagement, bureau alerts           │
│  Latency: <10ms | Lifetime: 24h (TTL) | Technology: Redis                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  TIER 4: EPISODIC MEMORY (Experience & Events)                              │
│  Content: Past applications, outcomes, delinquencies, seasonal shifts       │
│  Latency: <100ms | Lifetime: Months-Years | Technology: PostgreSQL (Event)│
├─────────────────────────────────────────────────────────────────────────────┤
│  TIER 5: SEMANTIC MEMORY (Distilled Facts & Concepts)                       │
│  Content: Behavioral embeddings, merchant clusters, industry margins        │
│  Latency: <500ms | Lifetime: Permanent | Technology: pgvector / Qdrant      │
├─────────────────────────────────────────────────────────────────────────────┤
│  TIER 6: PROCEDURAL MEMORY (Workflows & Skills)                           │
│  Content: Scoring workflow DAG, underwriting playbooks, bias audit rules    │
│  Latency: <50ms | Lifetime: Permanent | Technology: Temporal / LangGraph    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Data Flow Between Tiers:**
- Ingestion → Tier 4 (immutable events)
- Hot data promoted to Tier 3 (Redis cache)
- Tier 4 summarized/compressed to Tier 5 (semantic embeddings)
- Tier 6 encodes the orchestration workflow itself

---

## 7. Layer 1: Data Aggregation & Ingestion

### 7.1 Data Sources

#### 7.1.1 Internal Banking Data (Batch)

| Data Source | Frequency | Format | Latency | Fidelity |
|-------------|-----------|--------|---------|----------|
| CASA Transactions | Daily | CSV/Parquet | T+1 | High |
| Salary Credits | Daily | CSV | T+1 | High |
| Deposit Accounts | Weekly | CSV | T+7 | High |
| Existing Loan Accounts | Daily | CSV | T+1 | High |
| Card Transactions | Daily | CSV | T+1 | High |
| UPI Transactions (Internal) | Daily | CSV | T+1 | High |
| Customer Demographics | Weekly | CSV | T+7 | Medium |
| Digital Banking Logs | Daily | JSON | T+1 | Medium |

#### 7.1.2 External Data (Batch + API)

| Data Source | Frequency | Access Method | Compliance |
|-------------|-----------|---------------|------------|
| Credit Bureau (CIBIL/Experian) | Monthly | API (RBIA regulated) | Explicit consent |
| Account Aggregator (AA) Framework | On-demand | AA API (RBI regulated) | Customer consent |
| GST Data (Self-Employed) | Quarterly | GSTN API | Consent + KYC |
| Property/Vehicle Registries | On-demand | Government APIs | Limited use |

#### 7.1.3 Real-Time Intent Signals (Streaming)

| Signal | Source | Frequency | Memory Tier |
|--------|--------|-----------|-------------|
| Page visit (loan calculator) | Web analytics | Real-time | Tier 3 (Redis) |
| Time on page | Web analytics | Real-time | Tier 3 (Redis) |
| App session duration | Mobile SDK | Real-time | Tier 3 (Redis) |
| Bureau inquiry alert | Bureau webhook | Real-time | Tier 3 (Redis) |
| UPI transaction pattern | NPCI stream | Near real-time | Tier 4 (Event Store) |
| Credit card utilization spike | Card system | Daily | Tier 4 (Event Store) |

### 7.2 Ingestion Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     BATCH PIPELINE                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  Source  │───▶│  Local   │───▶│  Python  │───▶│ Feature  │ │
│  │  Systems │    │  Data    │    │  ETL     │    │ Store    │ │
│  │          │    │  Lake    │    │  (Pandas)│    │ (PostgreSQL│ │
│  │          │    │  (JSON)  │    │          │    │  + S3)   │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       Daily schedule (Phase 1: cron / Phase 3: Airflow)         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   REAL-TIME PIPELINE                            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  Web/App │───▶│  In-Memory│───▶│  Stream  │───▶│  Redis   │ │
│  │  Events  │    │  Queue    │    │  Proc    │    │  Cache   │ │
│  │          │    │  (Python) │    │  (async) │    │  (Tier 3)│ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       Event-driven; TTL 24h                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Data Quality & Validation

Every ingested batch must pass:
- **Schema validation:** Field presence, type correctness, range checks
- **Referential integrity:** Customer IDs exist in master data
- **Temporal consistency:** Transaction dates within acceptable window
- **Anomaly detection:** Sudden volume spikes, duplicate transactions
- **PII masking:** Raw PII tokenized before storage in non-production tiers

---

## 8. Layer 2: Transaction Intelligence Engine

### 8.1 Transaction Categorization

**Objective:** Classify every transaction into a standardized category for downstream analysis.

**Input:** Raw transaction narration (e.g., `UPI-SWIGGY-BLR`, `POS-AMAZON-IN`, `ACH-HDFC-HOMELOAN`)

**Output:** Category + Subcategory + Merchant + Confidence Score

#### 8.1.1 Categorization Hierarchy

```
Income
├── Salary
├── Business Receipt
├── Rental Income
├── Investment Income
├── Pension
└── Agricultural Income

Expense
├── Housing (Rent / EMI / Maintenance)
├── Utilities (Electricity / Gas / Water / Mobile)
├── Food & Dining
├── Grocery
├── Transportation (Fuel / Public Transit / Ride-share)
├── Healthcare
├── Education
├── Shopping
├── Entertainment
├── Insurance
├── Investments (SIP / FD / RD)
└── Debt Repayment (EMI / Credit Card Bill)

Transfers
├── Self-transfer (savings/investment)
├── Family transfer
└── Business transfer

Intent Signals
├── Property-related (Builder / Stamp Duty / Registration)
├── Vehicle-related (Dealer / Insurance / RTO)
├── Medical Emergency
├── Wedding-related (Jewellery / Banquet / Travel)
└── Education-related (College / Coaching / Foreign Remittance)
```

#### 8.1.2 Categorization Approach (Hybrid)

| Method | Coverage | Accuracy | Latency | Use Case |
|--------|----------|----------|---------|----------|
| **Rule Engine** (regex + keyword) | 60% of transactions | 95% | <1ms | High-volume, predictable patterns (salary, rent, EMI) |
| **FinBERT NLP** | 30% of transactions | 88% | ~50ms | Ambiguous narrations requiring semantic understanding |
| **Manual Review Queue** | 10% of transactions | 100% | Human | Low-confidence or novel merchant patterns |

**Rationale:** Rule engines are faster and more accurate for known patterns. FinBERT handles edge cases (e.g., `UPI-RAHUL-KIRANA` — is this grocery or business income?). Manual review feeds back into rule refinement.

#### 8.1.3 FinBERT Configuration

- **Base Model:** `yiyanghkust/finbert-tone` or `ProsusAI/finbert` (financial domain pre-trained)
- **Fine-tuning:** Not required for Phase 1; use zero-shot classification with banking-specific labels
- **Alternative:** If FinBERT unavailable, use `distilbert-base-uncased` with a lightweight classification head trained on 500-1000 labeled transactions
- **Inference:** Batch mode (not real-time endpoint) to control cost

### 8.2 Merchant Mapping Engine

**Objective:** Identify merchants from transaction narrations to detect intent signals.

**Example Mapping:**

| Transaction Narration | Merchant | Category | Intent Signal |
|----------------------|----------|----------|---------------|
| `UPI-ABC_BUILDERS-PAYMENT` | ABC Builders | Transfer | Property Purchase |
| `POS-TANISHQ-DEL` | Tanishq | Shopping | Wedding / Investment |
| `NEFT-XYZ_MOTORS` | XYZ Motors | Transfer | Vehicle Purchase |
| `UPI-FORTIS_HOSPITAL` | Fortis Hospital | Healthcare | Medical Emergency |
| `ACH-SHRI_RAM_SCHOOL` | Shri Ram School | Education | Child Education |

**Implementation:** Maintain a **merchant dictionary** (Redis hash / PostgreSQL lookup table) with:
- Merchant name variants (regex patterns)
- Standardized category
- Intent signal flag
- Confidence score
- Last seen date (for freshness)

### 8.3 Life Event Detection

**Objective:** Detect major life events from transaction sequences that indicate loan need.

**Detected Events:**

| Event | Transaction Pattern | Loan Signal | Confidence |
|-------|---------------------|-------------|------------|
| **Wedding** | Jewellery + Banquet + Travel + Clothing (within 60 days) | Personal Loan | High |
| **Home Purchase** | Builder payment + Stamp duty + Registration + Rent history | Home Loan | Very High |
| **Vehicle Purchase** | Dealer payment + Insurance + RTO fees + Rising fuel spend | Auto Loan | High |
| **Medical Emergency** | Hospital payment + Pharmacy + Diagnostic (sudden spike) | Personal Loan | High |
| **Child Education** | School fee + Coaching + Foreign remittance (education) | Education Loan | Medium |
| **Job Change** | Salary credit stops + New salary credit starts + Relocation expenses | Personal Loan (bridge) | Medium |
| **Business Expansion** | Vendor payments spike + GST filing increase + Working capital stress | Mortgage / LAP | High |

**Implementation:** Rule-based sequence detection + optional LLM confirmation for ambiguous cases.

**Rule Engine Logic:**
```
IF (Jewellery_Spend > ₹50,000) AND (Banquet_Payment > ₹30,000) 
   AND (Travel_Booking > ₹20,000) WITHIN 60_DAYS:
   THEN Flag_Event = "Wedding"
   THEN Intent_Score_Personal_Loan += 25
```

### 8.4 Behavioral Feature Extractor

**Objective:** Compute statistical features from categorized transactions for downstream ML models.

**Feature Groups:**

#### A. Income Features (12 features)
- `monthly_income_estimate`: Median of monthly credit inflows
- `income_stability_coefficient`: 1 - (std_dev_income / mean_income)
- `salary_regularity_score`: % of months with salary-like credit on consistent date
- `income_growth_rate`: Slope of 6-month income trend
- `multi_source_income_flag`: 1 if income from >2 distinct sources
- `seasonal_income_flag`: 1 if income shows >30% quarterly variance (gig workers)

#### B. Expense Features (15 features)
- `expense_to_income_ratio`: Total monthly debits / monthly income
- `fixed_obligation_ratio`: (Rent + EMI + Insurance + Utilities) / Income
- `discretionary_spend_ratio`: (Food + Entertainment + Shopping) / Income
- `expense_volatility`: Std dev of monthly total expenses
- `luxury_spend_ratio`: (Jewellery + High-end dining + Premium travel) / Income

#### C. Savings Features (8 features)
- `savings_rate`: (Income - Expenses) / Income
- `fd_creation_frequency`: Count of fixed deposit creations per quarter
- `sip_consistency`: % of months with mutual fund SIP debit
- `balance_growth_trend`: Slope of average monthly balance over 6 months
- `emergency_fund_ratio`: Average balance / monthly expenses

#### D. Credit Behavior Features (10 features)
- `credit_card_utilization`: Current balance / Limit (trend over 6 months)
- `bureau_inquiry_count`: Hard inquiries in last 3 months
- `existing_emi_burden`: Total EMIs / Income
- `debt_to_income_ratio`: Total outstanding debt / Annual income
- `repayment_discipline`: % of EMIs paid on time (last 12 months)

#### E. Engagement Features (6 features)
- `loan_page_visits_7d`: Count of visits to loan product pages
- `calculator_usage_count`: Times loan calculator was used
- `app_session_duration_loan_section`: Time spent in loan-related screens
- `bureau_inquiry_24h_flag`: 1 if bureau inquiry in last 24 hours
- `email_open_rate`: % of marketing emails opened (last 30 days)
- `campaign_response_history`: Binary flag for past campaign engagement

**Total Feature Vector:** ~51 features per customer per month

---

## 9. Layer 3: Income & Repayment Capacity Assessment

### 9.1 Segment-Specific Income Estimation

The system recognizes that **one model cannot fit all segments**. Income estimation is segmented by customer type, implemented by the **CapabilityAgent**.

#### 9.1.1 Salaried Customers

**Method:** Regex + Statistical

```
Detection Rules:
1. Identify salary credits: Regex patterns for "SALARY", "SAL", "PAYROLL", employer names
2. Validate frequency: Must occur monthly (±5 days) for ≥3 consecutive months
3. Compute stable income: Median of last 6 months of validated salary credits
4. Detect bonuses: Identify non-monthly credits from same employer (annual, quarterly)
5. Estimate total income: Stable income + (bonus_frequency × bonus_amount)
```

**Output:**
- `estimated_monthly_income`: ₹ value
- `employer_stability_score`: 0-100 (based on employer credit rating, tenure)
- `income_confidence`: High / Medium / Low
- `salary_credit_dates`: [5, 5, 5, 5, 5, 5] → indicates consistency

#### 9.1.2 Self-Employed Customers

**Method:** GST + Cash Flow Analysis

```
Detection Rules:
1. GST turnover: Extract from GST API (quarterly filing data)
2. Business receipts: Identify recurring business inflows (not salary-like)
3. Seasonal adjustment: Apply industry-specific seasonal factors
4. Margin estimation: Use industry average margins (e.g., retail: 15-20%, services: 40-50%)
5. Actual income = (GST Turnover × Industry Margin) + Non-GST cash receipts
```

**Output:**
- `estimated_monthly_income`: ₹ value
- `business_turnover`: Annual turnover from GST
- `industry_margin_applied`: %
- `seasonal_adjustment_factor`: Applied multiplier
- `income_confidence`: Medium (GST data is quarterly, less granular)

#### 9.1.3 Gig Workers

**Method:** UPI + Platform Pattern Analysis

```
Detection Rules:
1. Platform identification: Detect gig platform payments (Zomato, Swiggy, Uber, Ola, etc.)
2. Income aggregation: Sum all platform payments per month
3. Tip analysis: Include tip income (variable, often cash-based via UPI)
4. Seasonal adjustment: Gig income varies by season (festivals, weather)
5. Multi-platform flag: 1 if income from >1 platform (diversification = stability)
6. Disposable income = Gig income - (essential expenses + platform fees)
```

**Output:**
- `estimated_monthly_income`: ₹ value
- `platform_diversity_score`: Count of platforms
- `income_volatility`: Coefficient of variation
- `retained_money_ratio`: (Savings + Investments) / Income
- `income_confidence`: Low-Medium (thin file, high volatility)

**Critical Adaptation for Gig Workers:**
- Use **alternative data proxies** when UPI data is thin:
  - Electricity consumption (business vs. residential usage)
  - Fuel costs (correlates with delivery/driving income)
  - Mobile data recharge patterns (correlates with platform app usage)
- Apply **conservative discount factors**: Gig income estimated at 70-80% of observed inflows (accounting for platform fees, vehicle maintenance, irregularity)

### 9.2 Surplus Income Calculation

**Formula** (per month):

```
NET MONTHLY INCOME (from Layer 3.1)
(-) Existing EMI Obligations
(-) Rent / Housing Expenses
(-) Insurance Premiums
(-) Utility Payments (Electricity, Gas, Water, Mobile)
(-) Minimum Living Expenses (Food, Transport, Healthcare baseline)
(-) Mandatory Savings / Investments (SIP, RD, FD — treated as fixed commitments)
─────────────────────────────────────────────────────────────────
= MONTHLY SURPLUS (Disposable Income)

SAFE EMI CAPACITY = Monthly Surplus × 0.60
(60% of surplus allocated to new loan EMI; 40% buffer for emergencies)

MAX LOAN ELIGIBILITY = Safe EMI Capacity × PVAF(r, n)
Where PVAF = Present Value Annuity Factor for interest rate r and tenure n
```

**Example:**

| Component | Amount (₹) |
|-----------|-----------|
| Estimated Monthly Income | 85,000 |
| Existing EMI | 8,000 |
| Rent | 18,000 |
| Insurance | 2,500 |
| Utilities | 4,500 |
| Minimum Living | 15,000 |
| Mandatory Savings | 8,000 |
| **Monthly Surplus** | **29,000** |
| Safe EMI Capacity (60%) | 17,400 |
| Max Home Loan Eligibility (8.5%, 20 years) | ~20,50,000 |

### 9.3 Affordability Assessment vs. Traditional FOIR

| Dimension | Traditional FOIR | Prospect Assist AI Approach |
|-----------|------------------|----------------------------|
| Income Source | Declared salary slip | Inferred from transactions |
| Expense Scope | Only EMIs + rent | All fixed + discretionary + mandatory savings |
| Buffer | Fixed 50% FOIR | Dynamic based on savings rate and emergency fund |
| Segment Handling | Same for all | Segment-specific (salaried vs. gig vs. self-employed) |
| Update Frequency | Application-time only | Continuous (monthly refresh) |
| Explainability | "FOIR = 45%" | "Surplus = ₹29,000; Safe EMI = ₹17,400; Buffer = 40%" |

---

## 10. Layer 4: Eligibility Scoring Engine

### 10.1 Design Principle: Trainable Ensemble, Not Fixed Weights

**Critical Adaptation:** Fixed weights (e.g., Credit Score: 25%, Income Stability: 20%) are **rejected** in favor of a **trainable ensemble** with uncertainty quantification.

**Rationale:**
- Fixed weights lack data-driven justification and are not defensible under RBI audit
- Different customer segments require different weight distributions
- A gig worker with CIBIL 700 should not be scored identically to a salaried employee with CIBIL 700
- Weights must be learned from historical conversion and delinquency data

### 10.2 Ensemble Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  ELIGIBILITY ENSEMBLE                           │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │  XGBoost        │  │  Rule-Based     │  │  Segment        ││
│  │  Sub-Model 1    │  │  Guardrails     │  │  Adjustment     ││
│  │                 │  │                 │  │  Factor         ││
│  │  • Credit       │  │  • Hard floors  │  │  • Salaried:    ││
│  │    features     │  │    (CIBIL <500  │  │    baseline     ││
│  │  • Income       │  │    → reject)    │  │  • Gig: ×0.85   ││
│  │    features     │  │  • Hard caps    │  │  • Self-emp:    ││
│  │  • Debt         │  │    (FOIR >60%   │  │    ×0.90        ││
│  │    features     │  │    → reject)    │  │                 ││
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘│
│           │                    │                    │         │
│           └────────────────────┼────────────────────┘         │
│                                ▼                              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │           WEIGHTED ENSEMBLE FUSION                        │  │
│  │                                                         │  │
│  │  Eligibility_Score = α·XGBoost + β·Rules + γ·Segment   │  │
│  │  Where α, β, γ are learned from historical outcomes    │  │
│  │  (grid search + cross-validation on conversion data)   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                │                              │
│                                ▼                              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  OUTPUT                                                 │  │
│  │  • Eligibility Score: 0-100                             │  │
│  │  • Confidence Interval: [score-5, score+5]              │  │
│  │  • Segment: Salaried / Self-Employed / Gig              │  │
│  │  • Uncertainty Flag: High / Medium / Low                │  │
│  │  • Hard Reject Reasons: [if any]                        │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.3 Feature Importance (Illustrative, Not Fixed)

| Feature Group | Typical Importance (XGBoost SHAP) | Rationale |
|---------------|-----------------------------------|-----------|
| Credit Score / Bureau Data | 20-25% | Strongest predictor of default risk |
| Income Stability | 18-22% | Regular income = predictable repayment |
| Cash Flow Strength (Surplus) | 18-22% | Actual repayment capacity |
| Existing Debt Burden | 12-15% | High existing EMI = lower capacity |
| Relationship Value | 8-10% | Long-term customers = lower acquisition cost |
| Repayment History | 8-10% | Past behavior predicts future behavior |
| Engagement Signals | 5-8% | Active interest increases conversion |

**Note:** These are **illustrative ranges**. The actual weights are learned from IDBI's specific data.

### 10.4 Output Tiers

| Tier | Eligibility Score | Interpretation | Action |
|------|-------------------|----------------|--------|
| **Highly Eligible** | 75-100 | Strong repayment capacity, low risk | Priority processing, pre-approved offer |
| **Moderately Eligible** | 50-74 | Acceptable capacity, some risk factors | Standard processing, additional verification |
| **Marginally Eligible** | 30-49 | Borderline capacity, higher risk | Enhanced due diligence, lower LTV |
| **Not Eligible** | 0-29 | Insufficient capacity or high risk | Reject with reason; offer financial literacy |

---

## 11. Layer 5: Intent Detection Engine

### 11.1 Design Principle: Multi-Modal Intent

Intent is not binary. It is **product-specific**, **time-sensitive**, and **confidence-weighted**. The engine detects intent across four loan products simultaneously.

### 11.2 Intent Signal Taxonomy

#### 11.2.1 Home Loan Intent Signals

| Signal Type | Specific Indicator | Weight | Detection Method |
|-------------|-------------------|--------|------------------|
| **Strong** | Builder payment / Stamp duty / Registration | 25 | Transaction categorization |
| **Strong** | Property website engagement (MagicBricks, 99acres) | 20 | Web analytics (Tier 3) |
| **Medium** | Rent > ₹20,000 for >12 months | 15 | Transaction analysis |
| **Medium** | Savings accumulation > ₹5 lakh (down payment pattern) | 15 | Balance trend analysis |
| **Medium** | Salary growth > 15% YoY | 10 | Income estimation |
| **Weak** | Home loan calculator usage | 10 | Web analytics (Tier 3) |
| **Weak** | Bureau inquiry for home loan | 5 | Bureau webhook (Tier 3) |

**Home Loan Intent Score** = Σ(Triggered_Signals × Weights) / Σ(Max_Possible_Weights) × 100

#### 11.2.2 Auto Loan Intent Signals

| Signal Type | Specific Indicator | Weight |
|-------------|-------------------|--------|
| **Strong** | Vehicle dealer payment | 25 |
| **Strong** | Vehicle insurance quote payment | 20 |
| **Medium** | RTO-related transaction | 15 |
| **Medium** | Fuel expenses rising >30% over 3 months | 15 |
| **Weak** | Auto loan calculator usage | 10 |
| **Weak** | Car review website engagement | 10 |
| **Weak** | Bureau inquiry for auto loan | 5 |

#### 11.2.3 Personal Loan Intent Signals

| Signal Type | Specific Indicator | Weight |
|-------------|-------------------|--------|
| **Strong** | Medical emergency payment > ₹1 lakh | 20 |
| **Strong** | Education fee payment > ₹2 lakh | 20 |
| **Medium** | Wedding-related transactions | 15 |
| **Medium** | Credit card utilization > 80% | 15 |
| **Medium** | Large discretionary purchase (furniture, electronics) | 10 |
| **Weak** | Personal loan calculator usage | 10 |
| **Weak** | Bureau inquiry for personal loan | 10 |

#### 11.2.4 Mortgage / LAP Intent Signals

| Signal Type | Specific Indicator | Weight |
|-------------|-------------------|--------|
| **Strong** | Business expansion transactions | 25 |
| **Strong** | Working capital stress indicators | 20 |
| **Medium** | Existing property ownership | 15 |
| **Medium** | GST turnover growth > 20% | 15 |
| **Weak** | Mortgage calculator usage | 10 |
| **Weak** | Property valuation inquiry | 10 |
| **Weak** | Bureau inquiry for mortgage | 5 |

### 11.3 Real-Time Intent Amplification

**Critical Adaptation:** The engine adds **real-time intent amplification** via Tier 3 (Redis) cache.

```
┌─────────────────────────────────────────────────────────────┐
│              REAL-TIME INTENT AMPLIFICATION                 │
│                                                             │
│  Batch Intent Score (from transactions)          = 45       │
│  + Real-Time Amplification (from Redis Tier 3):             │
│    • Loan calculator used 3x in last 7 days      = +15     │
│    • Bureau inquiry in last 24 hours             = +10     │
│    • App session in loan section > 5 mins        = +8      │
│    • Email opened (loan offer) in last 48h       = +5      │
│  ─────────────────────────────────────────────────          │
│  AMPLIFIED INTENT SCORE                          = 83       │
│                                                             │
│  Decay Rule: Real-time signals decay 50% after 7 days,     │
│  25% after 14 days, 0% after 30 days.                       │
└─────────────────────────────────────────────────────────────┘
```

**Rationale:** A customer with transaction-based intent score 45 but who used the loan calculator 3 times this week is **genuinely interested** and should be prioritized.

### 11.4 Intent Model: CatBoost Classifier

**Why CatBoost:**
- Handles categorical features natively (merchant names, product types, customer segments)
- Robust to overfitting on small-to-medium datasets
- Built-in feature importance and SHAP support
- Faster training than XGBoost for mixed data types

**Input Features:** 30+ intent-specific features (from Section 8.4 + real-time signals)
**Output:** Intent score per product (0-100) + confidence interval
**Training Data:** Historical campaign data with known outcomes (converted / not converted)

---

## 12. Layer 6: Conversion Propensity Model

### 12.1 Design Principle: Calibrated Probability, Not Raw Score

**Critical Adaptation:** Tree-based models output **log-odds scores**, not true probabilities. This design mandates **Platt scaling** (sigmoid calibration) or isotonic regression.

### 12.2 Model Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              CONVERSION PROPENSITY MODEL                       │
│                                                                 │
│  INPUT FEATURES (per customer):                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │ Eligibility     │  │ Intent          │  │ Relationship    ││
│  │ Score (0-100)   │  │ Score (0-100)   │  │ & Engagement    ││
│  │ + Confidence    │  │ + Confidence    │  │ Features        ││
│  │ Interval        │  │ Interval        │  │                 ││
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘│
│           │                    │                    │         │
│           └────────────────────┼────────────────────┘         │
│                                ▼                              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  CatBoost Classifier (or XGBoost + Logistic Regression) │  │
│  │  • Predicts: P(Conversion | Eligibility, Intent, Eng)   │  │
│  │  • Output: Raw log-odds score                            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                │                              │
│                                ▼                              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  PLATT SCALING (Calibration)                            │  │
│  │  • Fits sigmoid: P = 1 / (1 + exp(-A·raw - B))        │  │
│  │  • Calibrated on hold-out set with known conversions   │  │
│  │  • Ensures: P(Conversion) is actual probability       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                │                              │
│                                ▼                              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  OUTPUT                                                 │  │
│  │  • Conversion Probability: 0-100%                       │  │
│  │  • Confidence Interval: [prob-8%, prob+8%]             │  │
│  │  • Expected Value: Prob × Loan Amount × Margin           │  │
│  │  • Priority Score: Expected Value × Conversion Prob     │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 12.3 Lead Quality Thresholds

| Conversion Probability | Lead Quality | Action | Expected Conversion |
|------------------------|--------------|--------|---------------------|
| **>70%** | **High Quality** | Immediate RM outreach, pre-approved offer | >50% |
| **50-70%** | **Medium-High** | Priority campaign, personalized offer | 30-50% |
| **30-50%** | **Medium** | Standard nurture campaign | 15-30% |
| **15-30%** | **Low** | Drip marketing, monitor for intent spike | 5-15% |
| **<15%** | **No Lead** | Do not market; risk of spam / brand damage | <5% |

**Target:** Only customers with **>30% conversion probability** become active leads. This drives the **>30% overall conversion rate** target.

### 12.4 Example Scoring Output

| Customer | Eligibility | Intent | Engagement | Raw Score | Calibrated Prob | Lead Quality |
|----------|-------------|--------|------------|-----------|-----------------|--------------|
| A | 85 (High) | 82 (Home) | High | 0.78 | **74%** | **High Quality** |
| B | 72 (High) | 35 (Auto) | Low | 0.42 | **28%** | Low |
| C | 55 (Med) | 68 (Personal) | High | 0.58 | **61%** | **Medium-High** |
| D | 90 (High) | 15 (None) | Low | 0.31 | **18%** | No Lead |
| E | 45 (Med) | 75 (Home) | High | 0.52 | **55%** | **Medium** |

**Insight:** Customer B has high eligibility but low intent — not a good lead. Customer E has medium eligibility but high intent — worth nurturing. The model captures the **interaction** between eligibility and intent, not just their sum.

---

## 13. Layer 7: Product Recommendation Engine

### 13.1 Matching Logic

The engine matches the highest-intent product to the customer's eligibility profile.

```
RECOMMENDED_PRODUCT = argmax(Product_i) [Intent_Score_i × Eligibility_Score_i × Product_Fit_i]

Where Product_Fit_i = segment-specific eligibility for product i
```

### 13.2 Product Matching Matrix

| Customer Behavior Pattern | Primary Product | Secondary Product | Rationale |
|---------------------------|-----------------|-------------------|-----------|
| Rent > ₹18K + Salary growth + Savings accumulation | **Home Loan** | Personal Loan (bridge) | Rent burden signals purchase intent; savings show down payment capacity |
| Medical expenses > ₹1L + Stable income | **Personal Loan** | Health Insurance cross-sell | Urgent need, predictable repayment |
| Auto dealer payment + Insurance inquiry | **Auto Loan** | Personal Loan | Purchase intent is high; timing is critical |
| Business expansion + Property ownership | **Mortgage / LAP** | Business Loan | Asset-backed, lower risk |
| Credit card utilization > 80% + Salary stable | **Personal Loan** (debt consolidation) | Credit Limit enhancement | Debt consolidation reduces risk, improves stickiness |
| Education fee + Child age 16-18 | **Education Loan** | Personal Loan | Life-stage aligned product |
| Wedding signals + Savings rate > 25% | **Personal Loan** | Gold Loan | Event-driven need, strong repayment capacity |

### 13.3 Product-Specific Eligibility Rules

| Product | Min Eligibility Score | Min Income | Max FOIR | Special Requirements |
|---------|----------------------|------------|----------|---------------------|
| Personal Loan | 50 | ₹25,000/month | 50% | None |
| Home Loan | 60 | ₹40,000/month | 45% | Property verification |
| Auto Loan | 55 | ₹30,000/month | 50% | Vehicle quotation |
| Mortgage / LAP | 65 | ₹50,000/month | 40% | Property valuation |

---

## 14. Layer 8: Underwriting Support Dashboard

### 14.1 Dashboard Design Philosophy

The dashboard is **not for customers** — it is for **Relationship Managers (RMs), Credit Managers, and Underwriting Officers**. It must be:
- **Action-oriented:** What should I do with this lead?
- **Explainable:** Why is this customer recommended?
- **Risk-aware:** What could go wrong?
- **Efficient:** All critical info in one screen, <30 seconds to review

### 14.2 Dashboard Panels

#### Panel 1: Customer Snapshot

| Field | Value | Source |
|-------|-------|--------|
| Customer ID | 12345 | Master Data |
| Segment | Salaried / IT Professional | Auto-detected |
| Relationship Vintage | 4.2 years | CBS |
| Products Held | Savings, Credit Card, FD | CBS |
| **Lead Quality** | **HIGH QUALITY** | Model Output |
| **Recommended Product** | **Home Loan** | Product Engine |
| **Conversion Probability** | **74% (±6%)** | Calibrated Model |
| **Priority** | **CALL TODAY** | Business Rule |

#### Panel 2: Income Assessment

| Field | Declared | Estimated | Confidence | Variance |
|-------|----------|-----------|------------|----------|
| Monthly Income | ₹50,000 | ₹85,000 | **HIGH** | +70% |
| Annual Income | ₹6,00,000 | ₹10,20,000 | HIGH | +70% |
| Income Source | Employer A | Employer A (validated) | — | — |
| Income Stability | — | 0.91 (Very Stable) | HIGH | — |
| Salary Growth (YoY) | — | +12% | MEDIUM | — |

**Alert:** Declared income is **70% below estimated**. Recommend verification but do not reject automatically.

#### Panel 3: Affordability Assessment

| Component | Amount (₹) | Notes |
|-----------|-----------|-------|
| Estimated Monthly Income | 85,000 | From transaction analysis |
| (-) Existing EMIs | 8,000 | Home loan EMI (existing) |
| (-) Rent | 18,000 | Consistent for 24 months |
| (-) Insurance | 2,500 | Life + Health |
| (-) Utilities | 4,500 | Electricity, Gas, Mobile |
| (-) Minimum Living | 15,000 | Food, Transport, Healthcare |
| (-) Mandatory Savings | 8,000 | SIP + RD |
| **Monthly Surplus** | **29,000** | — |
| **Safe EMI Capacity** | **17,400** | 60% of surplus |
| **Max Home Loan Eligibility** | **~20.5 Lakhs** | @ 8.5%, 20 years |
| **Current FOIR** | **31%** | Well within 45% limit |
| **Proposed FOIR (with new loan)** | **42%** | Within limit |

#### Panel 4: Risk Assessment

| Factor | Value | Risk Level | Trend |
|--------|-------|------------|-------|
| CIBIL Score | 742 | LOW | Stable |
| Bureau Inquiries (3M) | 1 | LOW | ↓ Decreasing |
| Credit Card Utilization | 45% | MEDIUM | ↑ Rising |
| Existing Debt | ₹4.8L | LOW | ↓ Decreasing |
| Repayment History | 100% on-time | LOW | — |
| Delinquency Risk (Model) | 8% | LOW | — |
| Fraud Flags | None | LOW | — |

#### Panel 5: Explainability (LLM Narrative)

> **"Customer 12345 is a HIGH QUALITY lead for Home Loan with 74% conversion probability.**
>
> **Why this customer:**
> • Stable salary credits of ₹85,000/month from Employer A for 4+ years
> • Monthly rent of ₹18,000 for 24 months indicates housing need
> • Builder payment of ₹25,000 detected (property exploration active)
> • Savings rate of 25% shows financial discipline and down payment capacity
> • Safe EMI capacity of ₹17,400 supports home loan of ~₹20.5 lakhs
> • CIBIL 742 with 100% on-time repayment history indicates low default risk
>
> **Recommended Action:** Offer pre-approved home loan of ₹20 lakhs at 8.5% for 20 years. Customer has sufficient surplus and strong intent signals."

#### Panel 6: SHAP Explainability (Technical)

| Feature | SHAP Value | Impact on Score |
|---------|-----------|-----------------|
| Salary Stability (0.91) | +12.4 | Strong positive |
| Rent Amount (₹18,000) | +8.7 | Positive (intent signal) |
| Savings Rate (25%) | +7.2 | Positive |
| CIBIL Score (742) | +6.8 | Positive |
| Credit Card Utilization (45%) | -3.1 | Slight negative |
| Bureau Inquiries (1) | -1.4 | Minor negative |

**Model:** CatBoost v2.1 | **Training Date:** 2026-05-15 | **Drift Status:** No drift detected

---

## 15. Multi-Agent Orchestration & Reflection Loop

### 15.1 Orchestration Architecture

The ProspectAssistOrchestrator does not simply concatenate agent outputs. It runs a **recursive Plan → Execute → Reflect → Evaluate loop** before publishing a lead.

```
                            +-------------------------------+
                            |   RM / Underwriting Console    |
                            |  (A2UI: structured lead cards) |
                            +----------------+----------------+
                                             ^
                                             | lead record (scored, tiered, evidenced)
                            +----------------+----------------+
                            |     Prospect Assist Orchestrator|
                            |  (Planner + Reflector + Eval)   |
                            +---+------+------+------+------+-+
                                |      |      |      |      |
                    +-----------+  +---+--+ +-+----+ +-+-----+ +----------+
                    | Capability |  |Intent| |Delinq| |Conversion| |Evidence  |
                    | Agent      |  |Agent | |Agent | |Propensity| |Compiler  |
                    | (income)   |  |      | |Agent | |Agent     | |Agent     |
                    +-----+------+  +--+---+ +--+---+ +----+-----+ +----+-----+
                          |            |         |          |           |
                          +------------+---------+----------+-----------+
                                             |
                            +----------------+----------------+
                            |   Context Orchestration Layer    |
                            |  (feature store + memory access) |
                            +----------------+----------------+
                                             |
                            +----------------+----------------+
                            |  Data Source Abstraction Layer   |
                            |     (BankDataConnector interface)|
                            +----+-------------------------+---+
                                 |                         |
                    +------------+-----------+   +---------+----------+
                    | Phase 1: Mock Sandbox   |   | Phase 2/3: IDBI    |
                    | API + Synthetic Data    |   | Sandbox / AA / Prod|
                    | (this build)            |   | (future, no code   |
                    |                         |   |  change above)     |
                    +-------------------------+   +---------------------+
```

### 15.2 Agent Responsibilities

```yaml
agents:
  CapabilityAgent:
    question: "Can they repay?"
    inputs: [account_transactions, upi_transactions, other_bank_statements, gst_data, bureau_summary]
    outputs: [estimated_income, disposable_surplus, savings_discipline_score, segment_classification]
    segment_strategies: [salaried, gig_self_employed, new_to_credit]
    memory_tiers: [Tier 2 (scratchpad for complex cases), Tier 5 (income embeddings)]
    mode: Orchestrator

  IntentAgent:
    question: "Do they need a loan now?"
    inputs: [digital_engagement_logs, life_event_signals, product_page_depth, geo_merchant_patterns]
    outputs: [intent_score, life_event_flags, product_affinity]
    memory_tiers: [Tier 3 (real-time cache), Tier 4 (event history)]
    mode: Orchestrator

  DelinquencyRiskAgent:
    question: "What is the forward-looking risk signal?"
    inputs: [bureau_inquiry_frequency, card_utilization_trend, loan_closure_history, spending_volatility]
    outputs: [early_warning_risk_score, risk_drivers]
    memory_tiers: [Tier 4 (episodic), Tier 5 (semantic)]
    mode: Orchestrator

  ConversionPropensityAgent:
    question: "Will they convert if approached now?"
    inputs: [historical_response_behavior, engagement_recency, product_affinity, channel_preference]
    outputs: [conversion_propensity_score]
    memory_tiers: [Tier 4 (past outcomes), Tier 5 (behavioral embeddings)]
    mode: Orchestrator

  EvidenceCompilerAgent:
    question: "Assemble all sub-scores + supporting evidence into one explainable lead record"
    inputs: [outputs of all above agents]
    outputs: [lead_tier, composite_score, evidence_bundle, confidence_level]
    memory_tiers: [Tier 1 (session), Tier 5 (knowledge base)]
    mode: Conductor

  ProspectAssistOrchestrator:
    role: "Plans agent execution order, resolves dependencies, runs reflection + evaluation before publishing a lead"
    pattern: "Goal -> Plan -> Execute (agents) -> Reflect (contradiction/low-confidence check) -> Evaluate (threshold gate) -> Publish or Recheck"
    memory_tiers: [Tier 1 (working), Tier 6 (procedural workflow)]
    mode: Conductor
```

### 15.3 Orchestration Loop (Reflect/Evaluate Gate)

Before a lead record is published to the RM console, the Orchestrator runs one reflection + evaluation pass:

- **Reflect:** Flag contradictions (e.g., high capability + high delinquency-risk + high intent — needs a "review" flag, not an auto-tier). Flag any agent output whose confidence is below threshold (common for thin-file NTC cases).
- **Evaluate:** Score the composite lead against the criteria in §22; if below threshold, the orchestrator either:
  - (a) Requests one re-run with an alternate segment strategy (e.g., retry Capability Agent with the NTC proxy-signal path), or
  - (b) Publishes the lead tagged `needs_manual_review` rather than a confident tier.

**The system never guesses past its own confidence floor into an unqualified "serious lead" label.**

This bounded retry is capped (`max_recursion_depth: 3` per lead) to keep latency and cost predictable.

### 15.4 Operational Bounds

```yaml
operational_bounds:
  max_recursion_depth_per_lead: 3        # orchestrator reflect/retry cap
  scoring_request_timeout: 30s
  batch_job_max_cohort_size: 50000
  consent_token_ttl: 24h
```

---

## 16. Data Source Abstraction Layer

### 16.1 The Scalability Seam

**This is the single most important design decision in this spec.** All agents call a connector interface; the interface's implementation is chosen by config, not by code path.

```yaml
interface: BankDataConnector
methods:
  get_account_transactions(customer_id, date_range) -> TransactionList
  get_upi_transactions(customer_id, date_range) -> UPITransactionList
  get_secondary_bank_statements(customer_id) -> StatementList
  get_gst_summary(business_id) -> GSTSummary
  get_bureau_summary(customer_id, consent_token) -> BureauSummary
  get_digital_engagement_log(customer_id) -> EngagementLog
  get_alt_data_proxies(customer_id) -> AltDataProxyBundle   # electricity, fuel spend, etc. for NTC

implementations:
  MockSandboxConnector:
    phase: 1
    backing_store: "generated JSON/CSV fixtures + lightweight mock REST API (§18)"
    auth: "static dev API key, sandbox-only, no real PII ever"

  BankSandboxConnector:
    phase: 2
    backing_store: "IDBI Bank-provided sandbox API + synthetic datasets"
    auth: "sandbox OAuth2 client credentials issued by IDBI"
    change_required: "implement this class against IDBI's real sandbox OpenAPI spec once provided; zero changes to agents"

  BankProductionConnector:
    phase: 3
    backing_store: "Account Aggregator framework (consent-gated) + core banking APIs"
    auth: "AA consent-token flow; scoped, time-bound OAuth2 tokens per §21.1"
    change_required: "add consent-lifecycle handling + AWS PrivateLink networking; zero changes to agents"

selection:
  mechanism: "config value DATA_CONNECTOR=mock|bank_sandbox|bank_production, resolved at orchestrator startup via factory"
```

### 16.2 Data & Behavioral Signal Mapping

Directly maps problem-statement categories to the fields the Data Source Abstraction Layer must expose, regardless of which phase's connector is behind it.

```yaml
signal_categories:
  spending_saving_discipline:
    fields: [monthly_savings_ratio, fd_sip_regularity, credit_dependency_ratio]
  digital_footprint:
    fields: [upi_merchant_category_mix, upi_txn_geo_trend, lifestyle_spend_index]
  multi_account_behavior:
    fields: [secondary_bank_statement_summary, reconstructed_total_income]
  digital_engagement:
    fields: [app_session_duration, page_depth, eligibility_check_repeat_count]
  life_event_signals:
    fields: [rent_payment_flag, builder_payment_flag, vehicle_dealer_payment_flag,
             medical_education_bill_flag, wedding_spend_flag]
  credit_seeking_behavior:
    fields: [bureau_inquiry_count_90d, card_utilization_trend, loan_closure_events]
```

---

## 17. API Contract

This is the public contract agents/RM console/underwriting systems call. **Stable across all three phases** (§1).

```yaml
endpoints:
  POST /api/v1/prospects/{customer_id}/score:
    description: "Runs the full agent pipeline for one customer + product and returns a scored, tiered lead"
    request:
      path_params: { customer_id: uuid }
      body:
        product: "personal_loan | home_loan | mortgage_lap | auto_loan"
        consent_token: "string, required — request rejected without valid consent (see §21.1)"
    response:
      200:
        lead_id: uuid
        tier: "serious | interested | quality_watch | not_ready | needs_manual_review"
        composite_score: decimal
        confidence_level: decimal
        estimated_income: decimal
        disposable_surplus: decimal
        delinquency_risk_score: decimal
        evidence_bundle: object
      403: { error: "Consent not granted or expired" }
      422: { error: "Insufficient signal to score — thin-file, no proxy data available" }
      503: { error: "Upstream data connector unavailable" }

  GET /api/v1/prospects/{customer_id}/leads:
    description: "Retrieve historical scored leads for a customer across products"
    response:
      200: { leads: [object] }

  POST /api/v1/prospects/batch-score:
    description: "Batch-score a cohort (e.g. nightly re-scoring run for the RM pipeline)"
    request:
      body: { customer_ids: [uuid], product: string }
    response:
      202: { batch_job_id: uuid, status: "accepted" }

  GET /api/v1/batch-jobs/{batch_job_id}:
    response:
      200: { status: "queued | running | complete | failed", results_uri: "string, nullable" }

  POST /api/v1/prospects/{customer_id}/feedback:
    description: "RM/underwriter records actual outcome (converted / declined / defaulted) — feeds evaluation loop (§22) and future model recalibration"
    request:
      body: { lead_id: uuid, outcome: "converted | declined | not_contacted", underwriting_decision: "string, nullable" }
    response:
      200: { acknowledged: true }
```

---

## 18. Mock Sandbox & Synthetic Dataset (Phase 1)

Since no bank sandbox API or synthetic dataset exists yet, Phase 1 builds a **self-contained mock sandbox** that (a) unblocks all agent/orchestrator development now, and (b) mirrors the data shape called out in the problem statement (§8: "transactions, MSME financials, UPI patterns") closely enough that swapping to the real IDBI sandbox in Phase 2 is a connector swap, not a redesign.

### 18.1 Mock Sandbox API Surface

```yaml
mock_sandbox_endpoints:
  GET /mock/v1/accounts/{customer_id}/transactions:
    query_params: [date_from, date_to, channel]
    returns: "paginated transaction list matching transactions schema (§19)"

  GET /mock/v1/accounts/{customer_id}/upi-transactions:
    returns: "UPI-channel subset with merchant_category + geo_tag populated"

  GET /mock/v1/accounts/{customer_id}/secondary-statements:
    returns: "simulated other-bank statement summary"

  GET /mock/v1/msme/{business_id}/financials:
    returns: "GST turnover, filing regularity, industry code — for gig/self-employed segment"

  GET /mock/v1/bureau/{customer_id}/summary:
    returns: "bureau_summary schema; null bureau_score for ~30% of generated NTC customers, by design"

  GET /mock/v1/digital-engagement/{customer_id}/sessions:
    returns: "digital_engagement schema"

  GET /mock/v1/alt-data/{customer_id}/proxies:
    returns: "alt_data_proxies schema — populated only for gig/NTC synthetic personas"

  POST /mock/v1/consent/grant:
    body: { customer_id: uuid, scope: [transactions, upi, bureau, alt_data] }
    returns: { consent_token: string, expires_at: timestamp }
```

### 18.2 Synthetic Dataset Generation Strategy

```yaml
synthetic_data_generator:
  persona_archetypes:
    - name: "salaried_high_intent"
      count: 150
      traits: [regular_salary_credit, high_savings_ratio, rising_app_engagement, recent_property_search_flag]
      expected_tier: "serious"

    - name: "salaried_window_shopper"
      count: 200
      traits: [regular_salary_credit, low_savings_ratio, single_eligibility_check_no_followup]
      expected_tier: "not_ready"

    - name: "gig_worker_high_capacity"
      count: 100
      traits: [variable_upi_credits, high_gst_turnover, consistent_retained_savings]
      expected_tier: "interested"

    - name: "self_employed_thin_margin"
      count: 80
      traits: [variable_upi_credits, moderate_gst_turnover, high_essential_expense_ratio]
      expected_tier: "quality_watch"

    - name: "ntc_thin_file"
      count: 100
      traits: [no_bureau_score, alt_data_only, moderate_electricity_fuel_spend]
      expected_tier: "needs_manual_review or interested (via alt-data proxy path)"

    - name: "rising_delinquency_risk"
      count: 70
      traits: [rising_card_utilization, increasing_bureau_inquiries, declining_savings_ratio]
      expected_tier: "quality_watch, with explicit delinquency_risk flag"

  generation_method: "rule-based generator with randomized noise per trait, seeded for reproducibility (seed=42)"
  total_synthetic_customers: 700
  storage: "flat JSON fixtures + seeded into Phase-1 relational store (§19) on startup"
  labeling: "each persona carries an expected_tier label used only for evaluation (§22), never fed to agents at inference time — prevents label leakage"
```

### 18.3 What Phase 2 Replaces

```yaml
phase_2_replacement_scope:
  replace:
    - "MockSandboxConnector implementation -> BankSandboxConnector implementation"
    - "synthetic_data_generator fixtures -> IDBI-provided synthetic datasets"
    - "static dev API key auth -> IDBI sandbox OAuth2 client-credentials auth"
  unchanged:
    - "BankDataConnector interface (§16)"
    - "all six agents and orchestrator logic (§15)"
    - "database schema (§19) — same tables, real data"
    - "public API contract (§17)"
    - "evaluation harness (§22) — same metrics, real ground truth via §17 feedback endpoint instead of synthetic labels"
  net_effort: "one new connector class + config change + re-run of eval suite against real sandbox data"
```

---

## 19. Segment-Specific Capability Estimation

Directly implements problem-statement §6.

```yaml
capability_estimation_strategies:
  salaried:
    primary_signal: "recurring_salary_credit_amount"
    disposable_income_formula: "avg_monthly_credit - avg_essential_expense - avg_existing_emi_obligation"
    fallback: "none needed — highest signal confidence"

  gig_self_employed:
    primary_signal: "business_turnover (GST) + UPI credit pattern"
    disposable_income_formula: >
      (gst_turnover_annual / 12 * industry_margin_estimate)
      - essential_expense_estimate
      - luxury_expense_estimate * 0.5   # luxury spend counted at partial weight — discretionary, reducible
    retained_money_signal: "savings/investment outflows as % of net turnover — proxy for repayment discipline"
    industry_margin_estimate: "looked up from industry_code via a reference margin table (static config, versioned; not modeled here)"

  new_to_credit:
    primary_signal: "alt_data_proxies (electricity consumption, fuel spend) + sparse UPI/GST if present"
    disposable_income_formula: "regression against alt-data proxies, calibrated on synthetic NTC personas in Phase 1"
    confidence_handling: >
      NTC estimates are inherently lower-confidence. The Capability Agent must emit an
      explicit confidence_level alongside estimated_income; the orchestrator's evaluation
      gate (§15) routes low-confidence NTC leads to needs_manual_review rather than
      auto-tiering them as serious/interested.
```

---

## 20. BDD Specification Scenarios

```gherkin
Feature: Prospect Assist AI — Lead Scoring Pipeline

  Scenario: Salaried high-intent customer scores as a serious lead
    Given a customer with regular salary credits, high savings ratio, and rising app engagement
    And valid consent has been granted for transactions, UPI, and bureau scope
    When the orchestrator scores the customer for "home_loan"
    Then the CapabilityAgent estimates income within 15% of the synthetic ground-truth income
    And the IntentAgent returns an intent_score above 0.7
    And the lead is tagged tier "serious"
    And the evidence_bundle includes the specific signals that drove the capability and intent scores

  Scenario: Window-shopper is correctly filtered out
    Given a customer who checked eligibility once and never returned
    And transaction data shows low savings ratio and no life-event signals
    When the orchestrator scores the customer for "personal_loan"
    Then the ConversionPropensityAgent returns a low conversion_propensity score
    And the lead is tagged tier "not_ready"
    And the lead is excluded from the RM priority queue

  Scenario: Gig worker with strong retained savings is surfaced despite no salary slip
    Given a gig-worker customer with variable UPI credits and consistent GST-turnover-based income
    And no conventional salary credit exists in the transaction history
    When the orchestrator scores the customer for "auto_loan"
    Then the CapabilityAgent uses the gig_self_employed estimation strategy
    And a non-zero disposable_surplus is computed from GST turnover and retained-savings signal
    And the lead is not rejected solely for lacking a salary credit

  Scenario: New-to-credit customer with thin file uses alt-data proxies
    Given an NTC customer with no bureau score and no GST data
    But electricity consumption and fuel spend data are available
    When the orchestrator scores the customer for "personal_loan"
    Then the CapabilityAgent falls back to the alt_data_proxies estimation path
    And the CapabilityAgent's confidence_level is explicitly below 0.6
    And the lead is tagged tier "needs_manual_review" rather than an unqualified confident tier

  Scenario: Consent missing or revoked blocks scoring
    Given a customer has not granted consent for the bureau data scope
    When a scoring request is submitted for that customer
    Then the API returns HTTP 403 with error "Consent not granted or expired"
    And no agent is invoked and no data is fetched from the connector

  Scenario: Rising delinquency risk flags a "quality_watch" tier even with decent capability
    Given a customer with adequate estimated income
    But rising card utilization and increasing bureau inquiry frequency over 90 days
    When the orchestrator scores the customer for "personal_loan"
    Then the DelinquencyRiskAgent returns an early_warning_risk_score above 0.6
    And the composite tier is "quality_watch", not "serious"
    And the evidence_bundle explicitly names the rising-utilization and inquiry-frequency drivers

  Scenario: Mock data connector outage degrades gracefully
    Given the MockSandboxConnector is unreachable
    When a scoring request is submitted
    Then the API returns HTTP 503 with error "Upstream data connector unavailable"
    And no partial or low-confidence lead is silently published

  Scenario: Contradictory signals trigger the reflection gate
    Given a customer shows high intent_score and high estimated income
    But also shows a high delinquency_risk_score
    When the orchestrator runs its reflection pass
    Then the contradiction is flagged
    And the lead is tagged "needs_manual_review" with all three conflicting scores visible in evidence_bundle

  Scenario: Gig worker income estimation with thin GST data
    Given the applicant has no GST registration
    And the applicant has 12 months of UPI transaction history
    And the UPI data shows recurring credits from "Zomato" and "Swiggy"
    And the average monthly credit is ₹52,000
    And the applicant has electricity bills averaging ₹3,500/month
    And the applicant has fuel expenses averaging ₹8,000/month
    When the CapabilityAgent analyzes the data
    Then the estimated monthly income should be between ₹35,000 and ₹42,000
    And the confidence score should be "Medium"
    And the retained money ratio should be calculated
    And if the retained ratio is greater than 25%
    Then the lead should be classified as "interested"
    And flagged for "enhanced review" due to thin file
```

---

## 21. Security, Compliance & Governance

### 21.1 7-Pillar Security Architecture

| Pillar | Control | Implementation for Prospect Assist AI |
|--------|---------|----------------------------------------|
| **Infrastructure** | Ephemeral sandboxes | Docker containers per scoring session; data wiped after decision |
| **Data** | Least privilege | CMEK at rest, mTLS in transit, tenant-partitioned vector DBs |
| **Model** | Prompt integrity | Version-controlled prompts; cryptographic attestation of model artifacts |
| **App & Runtime** | LLM firewalls + hooks | Dynamic filtering, deterministic lifecycle hooks, SAST in CI/CD |
| **IAM** | Zero Ambient Authority | SPIFFE IDs per agent, JIT downscoped tokens, file-tree allowlists |
| **Observability** | OpenTelemetry + ABA | Trace all tool calls, token metering, Agent Behavioural Analytics |
| **Governance** | Immutable audit trails | RBI compliance, Logic Reviews, Risk-Stratified Attestation |

### 21.2 RBI-Specific Compliance

| Requirement | Implementation |
|-------------|----------------|
| **Fair Lending (Non-Discrimination)** | Bias audit Agent 6 runs monthly; disparate impact ratio >0.80 for all segments |
| **Explainability** | Every score has SHAP values + reason codes + LLM narrative; no black-box decisions |
| **Data Residency** | All transaction data stored in AWS Mumbai (ap-south-1); no cross-border transfer |
| **Consent Management** | Explicit opt-in for AA data, bureau pulls, and alternative data sources |
| **Right to be Forgotten** | Deletion propagated across all 6 memory tiers within 30 days of request |
| **Audit Trail** | Every scoring decision immutable in Tier 4 (PostgreSQL); 7-year retention |
| **Model Governance** | Model cards for every deployed model; retraining triggers on drift detection |

### 21.3 PII Handling

```
Raw Transaction: UPI-RAHUL_SHARMA-12345-SWIGGY-BLR
    │
    ▼ Tokenization
Tokenized: UPI-TOKEN_a7x9-MASKED-SWIGGY-BLR
    │
    ▼ Anonymization (before Tier 5)
Anonymized: UPI-ANON_42-CATEGORY_FOOD-CITY_BANGALORE
```

- **Tier 1-2:** Raw data allowed (in-memory, ephemeral)
- **Tier 3:** Tokenized data (Redis with encryption at rest)
- **Tier 4-5:** Anonymized or aggregated only (no individual PII in vector DB)
- **Tier 6:** No customer data (only procedural rules)

### 21.4 Bias Prevention

| Bias Type | Detection Method | Mitigation |
|-----------|-----------------|------------|
| **Demographic Bias** | Disparate impact analysis across gender, age, geography | Reweighting, adversarial debiasing |
| **Segment Bias** | Gig workers systematically under-scored vs. salaried | Segment-specific models, separate thresholds |
| **Temporal Bias** | Model trained on pre-2024 data, post-COVID behavior changed | Continuous retraining, drift detection |
| **Feedback Loop Bias** | Past rejections reduce future scores for same profile | Counterfactual fairness, outcome logging |
| **Proxy Bias** | Zip code proxies for caste/income | Remove proxy features, fairness constraints |

### 21.5 Security Checklist

- [ ] PII handling reviewed against Account Aggregator consent scope before Phase 2 connector is enabled
- [ ] AuthZ boundaries: RM console can read leads, not raw transactions
- [ ] Input validation on all mock + (later) real API calls
- [ ] Consent-token expiry enforced server-side, not just client-side
- [ ] No ambient/shared credentials between agents
- [ ] Every published lead's evidence_bundle is immutable and logged
- [ ] A human underwriter/RM makes the final lending decision; this system's tier is decision-support, never auto-approval

---

## 22. Evaluation Strategy & KPIs

### 22.1 Model Evaluation

| Model | Metric | Target | Evaluation Method |
|-------|--------|--------|-------------------|
| Income Estimation | MAPE | <15% | Hold-out test set with known income |
| Transaction Categorization | F1-Score | >0.90 | Labeled test set (500 transactions) |
| Intent Detection | AUC-ROC | >0.85 | Historical campaign data |
| Conversion Propensity | AUC-ROC | >0.80 | Historical conversion data |
| Lead Quality | Precision@K | >85% | K=100 highest scored leads |
| Calibration | Brier Score | <0.15 | Probabilistic forecast accuracy |

### 22.2 Business Evaluation

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Lead-to-Loan Conversion | ~1% | **>30%** | (# Loans / # Leads) × 100 |
| Income Estimation Accuracy | ~60% | **>90%** | MAPE vs. verified income |
| Customer Acquisition Cost | Baseline | **-20% to -40%** | Total cost / # conversions |
| Early Delinquency (30 DPD) | Baseline | **-15%** | Delinquent loans / Total loans |
| RM Productivity | 5 leads/day | **15 leads/day** | Leads handled / RM / day |
| Customer Satisfaction | Baseline | **+20%** | Post-approval NPS survey |

### 22.3 Trajectory Evaluation

For the Agentic Engineering harness, evaluate whether the AI agent:
- [ ] Reads the relevant spec file before implementing
- [ ] Writes failing tests before model code
- [ ] Matches existing code style and conventions
- [ ] Handles edge cases (null input, missing data, timeout)
- [ ] Updates documentation in the same commit as code
- [ ] Does not bundle unrelated changes
- [ ] Recovers from build failures without compounding errors

### 22.4 Bias Evaluation

| Test | Method | Target |
|------|--------|--------|
| Disparate Impact | Adverse impact ratio across gender, geography, segment | >0.80 |
| Equal Opportunity | True positive rate parity | <5% difference |
| Predictive Parity | Precision parity across segments | <5% difference |
| Individual Fairness | Similar customers receive similar scores | >90% consistency |

### 22.5 Evaluation Criteria (Project Contract)

```yaml
evaluation_criteria:
  income_estimation_accuracy:
    method: "compare estimated_income vs. persona ground-truth (Phase 1) or feedback-endpoint-reported actuals (Phase 2+)"
    threshold: "within +/- 15% for >= 80% of scored customers per segment"

  lead_tiering_quality:
    method: "compare assigned tier vs. persona expected_tier (§18.2) on the synthetic eval set"
    threshold: "tier match or adjacent-tier match >= 85%"

  conversion_proxy:
    method: "simulate RM contact only for 'serious'/'interested' tiers; measure simulated conversion rate against persona-labeled true positives"
    threshold: "> 30% simulated conversion rate on eval cohort"

  ntc_segment_handling:
    method: "confirm no NTC customer is auto-tiered 'serious' with confidence_level < 0.6"
    threshold: "100% compliance — this is a hard safety rule, not a soft target"

  trajectory_quality:
    method: "for a sample of scored leads, confirm the orchestrator invoked the correct segment-specific CapabilityAgent strategy (§19) and that the reflection gate fired on contradictory-signal personas"
    threshold: "100% correct agent-selection; reflection gate fires on 100% of intentionally-contradictory eval personas"

  safety_and_governance:
    method: "confirm zero scoring requests processed without a valid consent_token; confirm zero leads published bypassing the evaluation gate"
    threshold: "zero violations"
```

---

## 23. Implementation Roadmap

### Phase 1: Foundation (Week 1-2) — Agentic Phase 1 & 2
- [ ] Set up `specs/` directory with formal BDD specifications (this document)
- [ ] Create `AGENTS.md` with banking-specific guardrails
- [ ] Configure infrastructure (Docker, PostgreSQL, Redis)
- [ ] Set up data ingestion pipeline (batch + real-time)
- [ ] Implement transaction categorization (rule engine + FinBERT)
- [ ] Build data quality validation framework
- [ ] Implement MockSandboxConnector and synthetic data generator
- [ ] Create `policies.yaml` with role/env-based tool permissions

### Phase 2: Core Intelligence (Week 3-4) — Agentic Phase 3
- [ ] Implement income estimation (segment-specific models) — CapabilityAgent
- [ ] Build eligibility scoring ensemble (XGBoost + rules + segment adjustment) — DelinquencyRiskAgent
- [ ] Implement intent detection engine (CatBoost + real-time signals) — IntentAgent
- [ ] Build conversion propensity model (CatBoost + Platt calibration) — ConversionPropensityAgent
- [ ] Implement customer segmentation (HDBSCAN)
- [ ] Set up Tier 3-5 memory stack (Redis, PostgreSQL, pgvector)
- [ ] Write failing tests BEFORE model code for each agent

### Phase 3: Integration & Explanation (Week 5-6) — Agentic Phase 3 & 4
- [ ] Integrate all layers into end-to-end pipeline
- [ ] Implement ProspectAssistOrchestrator with reflection/evaluation gate
- [ ] Build product recommendation engine
- [ ] Implement SHAP explainability for every score
- [ ] Build LLM explanation layer (narrative generation) — EvidenceCompilerAgent
- [ ] Develop underwriting support dashboard (Streamlit)
- [ ] Implement multi-account graph analysis (Neo4j or PostgreSQL recursive CTEs)
- [ ] Run full evaluation suite (model metrics, business KPIs, bias tests)

### Phase 4: Testing & Evaluation (Week 7) — Agentic Phase 4
- [ ] Run full evaluation suite (model metrics, business KPIs, bias tests)
- [ ] Conduct trajectory evaluation of agent implementations
- [ ] Perform security audit (7 pillars)
- [ ] Run load testing (100K customers, 20M transactions)
- [ ] Validate cost estimates against actual billing
- [ ] Calibrate LLM-as-Judge (90% agreement with human ratings)

### Phase 5: Deployment & Monitoring (Week 8) — Agentic Phase 5
- [ ] Deploy to staging environment
- [ ] Set up monitoring (CloudWatch, custom dashboards)
- [ ] Implement model drift detection
- [ ] Train RMs on dashboard usage
- [ ] Go-live with limited pilot (10,000 customers)
- [ ] Collect feedback and iterate
- [ ] Set token cost attribution per feature

---

## 24. Technology Stack

### 24.1 Core ML Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Transaction Categorization | FinBERT (HuggingFace) | Latest | Financial domain NLP; zero-shot capable |
| Income Estimation | XGBoost | 2.1.0 | Gold standard for tabular regression; SHAP support |
| Intent Detection | CatBoost | 1.2.7 | Native categorical handling; faster than XGBoost for mixed data |
| Conversion Propensity | CatBoost + Platt Scaling | 1.2.7 | Calibrated probabilities; robust to overfitting |
| Customer Segmentation | HDBSCAN | 0.8.33 | Natural cluster detection; outlier identification |
| Explainability | SHAP + LLM (Llama 3 8B) | 0.45.0 / 3.0 | SHAP for technical; LLM for narrative |
| Anomaly Detection | Isolation Forest (sklearn) | 1.5.0 | Data quality checks; outlier flagging |

### 24.2 Data & Memory Stack

| Tier | Technology | Service | Cost Optimization |
|------|-----------|---------|-------------------|
| Tier 1 (Working) | RAM | In-memory (Python) | Ephemeral; no persistent cost |
| Tier 2 (Scratchpad) | Temporary buffers | Local append-only logs | Rotated every 30 minutes |
| Tier 3 (Cache) | Redis | Docker / ElastiCache | Pay-per-use; scales to zero |
| Tier 4 (Episodic) | PostgreSQL | Docker / RDS | Reserved instances for steady load |
| Tier 5 (Semantic) | pgvector (PostgreSQL extension) | Docker / RDS | Single store for vectors + documents |
| Tier 6 (Procedural) | Python workflow engine | In-process / Temporal | Serverless compute |

### 24.3 Infrastructure Stack

| Component | Technology | Service (Phase 1) | Service (Phase 3) |
|-----------|-----------|-------------------|-------------------|
| Data Lake | Local JSON/CSV | Docker volume | AWS S3 (Mumbai) |
| ETL | Python (Pandas/Polars) | Cron jobs | AWS Glue (Spark) |
| Workflow Orchestration | Python async | In-process | AWS Step Functions |
| Stream Processing | Python async | In-memory queue | AWS Kinesis |
| API Gateway | FastAPI | Docker | AWS API Gateway + Lambda |
| Dashboard | Streamlit | Docker | AWS App Runner |
| Model Training | scikit-learn / XGBoost | Local / Docker | AWS SageMaker |
| Model Inference | Batch (Python) | Cron | SageMaker Batch Transform |
| Monitoring | Prometheus + Grafana | Docker | AWS CloudWatch |

### 24.4 Phase 1 Local Configuration

```yaml
tools_and_versions:
  language: "Python 3.12"
  api_framework: "FastAPI 0.115.x"
  data_validation: "Pydantic v2.9.x"
  orchestration_state_machine: "Phase 1: in-process async orchestrator; Phase 3: AWS Step Functions"
  relational_store: "PostgreSQL 16 (local/Docker in Phase 1; Aurora PostgreSQL in Phase 3)"
  synthetic_data_generation: "Faker 30.x + custom persona rule engine (§18.2)"
  llm_access_for_agents: "Claude via Anthropic API (model pinned at implementation time, not guessed)"
  containerization: "Docker 27.x, docker-compose for Phase 1 local stack"
  testing: "pytest 8.x + BDD scenarios (§20) executed via pytest-bdd 8.x"
```

---

## 25. Cost Estimation & Unit Economics

### 25.1 Pilot Scenario (Hackathon / POC — Phase 1)

**Assumptions:**
- 100,000 customers
- 12 months of historical data
- 20 million transactions
- Daily batch scoring
- No real-time endpoints (Batch Transform only)

| Component | Monthly Cost (USD) | Monthly Cost (INR) | Notes |
|-----------|-------------------|-------------------|-------|
| Compute (EC2 / Docker) | $120 | ₹10,000 | Development + mock API server |
| Storage (Local / S3) | $25 | ₹2,100 | Transaction data lake |
| PostgreSQL (Local / RDS) | $60 | ₹5,000 | Episodic + document store |
| Redis (Local / ElastiCache) | $40 | ₹3,300 | Real-time intent cache |
| API Gateway + Lambda | $30 | ₹2,500 | API layer |
| CloudWatch + Monitoring | $25 | ₹2,100 | Observability |
| **Total Monthly** | **~$300** | **~₹25,000** | **Well within hackathon budget** |
| **One-time Setup** | **~$200** | **~₹16,700** | Initial data migration, model training |

### 25.2 Unit Economics (What Judges Care About)

| Metric | Value | Industry Benchmark | Advantage |
|--------|-------|-------------------|-----------|
| Cost per lead scored | ₹0.35 | ₹5-10 (traditional) | **14x cheaper** |
| Cost per conversion | ₹120 | ₹500-800 (traditional) | **4-7x cheaper** |
| Cost per loan disbursed | ₹1,200 | ₹5,000-8,000 (traditional) | **4-7x cheaper** |
| Revenue per lead (assuming 2% avg loan margin) | ₹4,100 | ₹1,200 (traditional) | **3.4x higher** |
| **ROI** | **3.4x** | **0.2-0.3x** | **11x improvement** |

### 25.3 Production Scale (Phase 3 — 1M Customers)

| Component | Monthly Cost (INR) | Optimization |
|-----------|-------------------|--------------|
| Compute | ₹1,50,000 | Reserved instances, spot pricing |
| Storage | ₹25,000 | S3 Intelligent Tiering |
| Network | ₹15,000 | VPC endpoints, data transfer optimization |
| Monitoring | ₹10,000 | CloudWatch custom metrics |
| **Total** | **~₹2,00,000/month** | |
| **Per Customer** | **₹0.20/month** | |

---

## 26. Risk Mitigation & Anti-Patterns

### 26.1 Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Data Quality Issues** | High | High | Extensive data validation; anomaly detection; manual review queue |
| **Model Bias (Gig Workers)** | Medium | High | Segment-specific models; bias audit Agent; separate thresholds |
| **Regulatory Rejection** | Low | Very High | RBI compliance review; explainability by default; audit trail |
| **Cost Overrun** | Medium | Medium | Batch Transform (not real-time); spot instances; serverless cache |
| **Low Conversion (<30%)** | Medium | Very High | Continuous learning from Tier 4; A/B testing; feature engineering |
| **PII Data Breach** | Low | Very High | Tokenization; encryption; tenant isolation; least privilege |
| **Model Drift** | Medium | High | Monthly drift detection; automated retraining; shadow deployment |
| **RM Adoption Resistance** | Medium | High | Dashboard training; explainability; proven ROI demonstration |
| **Synthetic Data Mismatch** | Medium | Medium | Hold out persona subset never used during heuristic tuning; re-run eval on Phase 2 data |

### 26.2 Anti-Patterns to Avoid

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|---------------|------------------|
| **Single vector DB for everything** | Vector DBs are terrible for exact lookups, time-series, and relationships | Use 6-tier memory stack; right store for each access pattern |
| **Fixed eligibility weights** | Arbitrary, not defensible under audit, ignores segment differences | Trainable ensemble with segment-specific adjustments |
| **Raw model outputs as probabilities** | Tree-based models output log-odds, not true probabilities | Platt scaling or isotonic regression for calibration |
| **Ignoring real-time intent signals** | Misses genuinely interested customers who haven't transacted recently | Redis Tier 3 cache for web/app engagement signals |
| **Storing raw PII in vector DB** | Regulatory violation, data breach risk | Tokenize before Tier 3; anonymize before Tier 5 |
| **One-size-fits-all model** | Gig workers and salaried employees have different financial signatures | Segment-specific feature pipelines and models |
| **No explainability** | RBI fair lending requires auditable decisions | SHAP + reason codes + LLM narrative for every score |
| **Scope creep (fraud detection)** | Fraud is a separate domain with different data and regulations | Out of scope for Phase 1; mention as Phase 2 |
| **24/7 real-time endpoints** | Massive cost for batch-appropriate workload | Batch Transform for nightly scoring; serverless for ad-hoc |
| **No memory / stateless scoring** | Cannot learn from past outcomes; misses temporal patterns | 6-tier memory stack with episodic learning |
| **Skipping spec writing** | Natural language prompts are not specs; without formal specs, you are vibe coding | Hybrid Markdown + YAML specs with BDD scenarios |
| **Accepting AI-generated code without review** | Review every line that will ship; be skeptical of clever-looking code | AI-assisted first-pass review + human review for design |

---

## 27. Appendices

### Appendix A: Database Schema (Phase 1 — Mock Sandbox Persistence)

```yaml
tables:
  customers:
    columns:
      customer_id: { type: uuid, primary: true }
      segment: { type: enum, values: [salaried, gig_self_employed, new_to_credit] }
      product_interest: { type: enum, values: [personal_loan, home_loan, mortgage_lap, auto_loan] }
      consent_status: { type: enum, values: [granted, revoked, pending] }
      created_at: { type: timestamp }

  transactions:
    columns:
      txn_id: { type: uuid, primary: true }
      customer_id: { type: uuid, foreign_key: customers.customer_id }
      channel: { type: enum, values: [upi, netbanking, card, cash_equivalent] }
      merchant_category: { type: string }
      amount: { type: decimal }
      direction: { type: enum, values: [credit, debit] }
      txn_timestamp: { type: timestamp }
      geo_tag: { type: string, nullable: true }

  bureau_summary:
    columns:
      customer_id: { type: uuid, foreign_key: customers.customer_id }
      inquiry_count_90d: { type: integer }
      card_utilization_pct: { type: decimal }
      active_loans: { type: integer }
      loans_closed_12m: { type: integer }
      bureau_score: { type: integer, nullable: true, note: "null for thin-file NTC customers" }

  digital_engagement:
    columns:
      customer_id: { type: uuid, foreign_key: customers.customer_id }
      session_id: { type: uuid, primary: true }
      pages_viewed: { type: array, items: string }
      session_duration_seconds: { type: integer }
      eligibility_check_count: { type: integer }
      session_timestamp: { type: timestamp }

  alt_data_proxies:
    columns:
      customer_id: { type: uuid, foreign_key: customers.customer_id }
      electricity_avg_monthly_units: { type: decimal, nullable: true }
      fuel_spend_monthly: { type: decimal, nullable: true }
      gst_turnover_annual: { type: decimal, nullable: true }

  lead_scores:
    columns:
      lead_id: { type: uuid, primary: true }
      customer_id: { type: uuid, foreign_key: customers.customer_id }
      product: { type: enum, values: [personal_loan, home_loan, mortgage_lap, auto_loan] }
      estimated_income: { type: decimal }
      disposable_surplus: { type: decimal }
      intent_score: { type: decimal, range: [0, 1] }
      delinquency_risk_score: { type: decimal, range: [0, 1] }
      conversion_propensity: { type: decimal, range: [0, 1] }
      composite_score: { type: decimal, range: [0, 1] }
      tier: { type: enum, values: [serious, interested, quality_watch, not_ready, needs_manual_review] }
      confidence_level: { type: decimal, range: [0, 1] }
      evidence_bundle: { type: jsonb }
      scored_at: { type: timestamp }
```

### Appendix B: Feature Engineering Reference

| Feature Name | Formula | Data Source | Segment |
|--------------|---------|-------------|---------|
| `income_stability_coefficient` | 1 - (std_income / mean_income) | CASA transactions | All |
| `savings_rate` | (income - expenses) / income | CASA + card | All |
| `fixed_obligation_ratio` | (rent + emi + insurance + utilities) / income | CASA + bureau | All |
| `gig_platform_diversity` | COUNT(DISTINCT platform_name) | UPI transactions | Gig |
| `gst_turnover_annual` | SUM(gst_filing.turnover) | GST API | Self-Employed |
| `seasonal_income_flag` | IF quarterly_cv > 0.30 THEN 1 ELSE 0 | CASA transactions | Gig / Agriculture |
| `credit_hunger_score` | bureau_inquiries_3m + (cc_utilization_trend × 2) | Bureau + Card | All |
| `property_intent_score` | builder_payments + stamp_duty + (rent_history × 0.5) | CASA + UPI | All |
| `engagement_amplification` | calculator_usage + page_visits + app_session_time | Web/App analytics | All |

### Appendix C: Model Card Template

```
Model Card: Prospect Assist AI — Conversion Propensity Model

Model Details:
  - Name: conversion_propensity_v1.2
  - Type: CatBoost Classifier with Platt Calibration
  - Training Date: 2026-05-15
  - Retraining Trigger: Drift > 0.05 or monthly schedule
  - Owner: Data Science Team, IDBI Bank

Intended Use:
  - Predict probability of loan conversion for retail lending leads
  - Input: Eligibility score, intent scores, engagement features
  - Output: Calibrated conversion probability (0-100%)

Training Data:
  - Source: Historical campaign data (2024-2026)
  - Size: 150,000 customers, 45,000 conversions
  - Segments: Salaried (60%), Self-Employed (25%), Gig (15%)

Evaluation Results:
  - AUC-ROC: 0.84
  - Precision@100: 0.87
  - Calibration (Brier): 0.12
  - Disparate Impact Ratio: 0.82 (gender), 0.85 (segment)

Ethical Considerations:
  - Bias audit conducted monthly
  - No caste, religion, or sensitive demographic features used
  - Segment-specific thresholds to prevent discrimination
  - Human review required for all "new-to-credit" cases

Limitations:
  - Less accurate for customers with <3 months of transaction history
  - Seasonal workers may be under-scored during off-season
  - Does not predict fraud risk (separate model)
```

### Appendix D: Glossary

| Term | Definition |
|------|-----------|
| **FOIR** | Fixed Obligation to Income Ratio — total EMIs / monthly income |
| **CASA** | Current Account / Savings Account — core banking deposits |
| **UPI** | Unified Payments Interface — real-time payment system |
| **AA Framework** | Account Aggregator — RBI-regulated data consent framework |
| **CIBIL** | Credit Information Bureau (India) Limited — credit score provider |
| **DPD** | Days Past Due — delinquency metric |
| **LTV** | Loan to Value — loan amount / asset value |
| **LAP** | Loan Against Property — mortgage product |
| **SHAP** | SHapley Additive exPlanations — model interpretability framework |
| **Platt Scaling** | Sigmoid calibration method for converting scores to probabilities |
| **HDBSCAN** | Hierarchical Density-Based Spatial Clustering — advanced clustering algorithm |
| **FinBERT** | Financial domain BERT model for NLP on banking text |
| **Tier 1-6** | Memory architecture tiers (Working → Scratchpad → Cache → Episodic → Semantic → Procedural) |
| **A2A** | Agent-to-Agent protocol for multi-agent communication |
| **MCP** | Model Context Protocol for tool interoperability |
| **RM** | Relationship Manager — bank staff who engages with customers |
| **NTC** | New-to-Credit — customers with no credit history |
| **BDD** | Behavior-Driven Development — spec format using Given/When/Then |
| **YOLO Mode** | Unstructured, spec-less coding — explicitly forbidden in this workflow |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-30 | AI Design Team | Initial design document (Full Design) |
| 2.0 | 2026-07-02 | AI Design Team | Integrated Solution Spec orchestration + Agentic Engineering Workflow methodology |

**Next Review:** 2026-07-15 (post-hackathon feedback incorporation)

**Distribution:** Internal — IDBI Innovate 2026 Team

---

*This document was designed using the Agentic Engineering Workflow and Memory Architecture principles. It is a living document — update specs before code, and update this document before architecture changes.*
