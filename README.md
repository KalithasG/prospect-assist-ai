# Prospect Assist AI

**AI-driven lead generation and underwriting support for IDBI retail lending**
*IDBI Innovate 2026 · Track 2 · Prototype (Phase 1 — Mock Sandbox)*

Prospect Assist AI separates genuinely interested, repayment-capable loan prospects
from casual eligibility-checkers by mining **consented transaction and behavioral
data** — instead of relying on self-declared income, bureau scores, and static FOIR.
It covers all four in-scope products: **Personal Loan, Home Loan, Mortgage/LAP, and
Auto Loan**.

---

## 1. The problem

IDBI's retail lending funnel runs on declaration-based metrics. That causes two
structural weaknesses:

- **Low conversion (~1%)** — most digital "leads" are window-shoppers checking
  eligibility with no genuine borrowing intent.
- **Shallow income visibility** — declared income and bureau scores don't capture
  actual cash-flow behavior, disposable surplus, or repayment discipline, so
  genuine prospects are missed and underwriting flies partially blind.

The system therefore answers **three questions** for every prospect, from
transaction and behavioral data alone:

1. **Can they repay?** — real income, disposable surplus, savings behavior
2. **Do they need a loan now?** — life-event spend, purchase-intent signals
3. **Will they convert?** — product affinity, engagement, calibrated propensity

## 2. Solution at a glance

```
Consent gate → Data fetch (connector) → Transaction intelligence
     → Capability · Intent · Delinquency agents (parallel)
     → Eligibility ensemble + Conversion propensity
     → Reflection gate (contradictions, confidence floors, bounded retries)
     → Tier + evidence bundle → RM / underwriting dashboard & API
```

Every scored lead lands in one of **five tiers** — `serious`, `interested`,
`quality_watch`, `needs_manual_review`, `not_ready` — and ships with an
**evidence bundle**: SHAP-style feature contributions, capability/intent/risk
sub-scores, an affordability breakdown, and a plain-language analyst narrative.
The system is decision support by design: a human underwriter always makes the
final lending decision.

## 3. Repository layout

```
├── src/prospect_assist/
│   ├── config.py                  # product rules, tier thresholds, margins (deterministic)
│   ├── consent.py                 # scoped consent tokens, 24h TTL, server-side enforcement
│   ├── store.py                   # in-memory store mirroring the Phase-2 relational schema
│   ├── orchestrator.py            # Plan → Execute → Reflect → Evaluate loop + gates
│   ├── connectors/
│   │   ├── base.py                # BankDataConnector interface + factory (the scalability seam)
│   │   └── mock.py                # Phase-1 mock sandbox connector
│   ├── agents/
│   │   ├── transaction_parser.py  # categorization + behavioral feature extraction
│   │   ├── capability.py          # segment-specific income & surplus estimation
│   │   ├── intent.py              # intent taxonomy + real-time amplification with decay
│   │   └── scoring.py             # delinquency risk, eligibility ensemble, conversion, evidence
│   ├── api/app.py                 # public FastAPI contract (stable across all phases)
│   └── data/generator.py          # 700 synthetic personas, 6 archetypes, seed=42
├── tests/                         # 9 BDD scenarios (written first) + API contract tests
├── eval/run_eval.py               # §22.5-style eval harness → eval_report.json
├── dashboard/                     # React + Vite + Recharts RM console (Material Design 3)
├── demo_server.py                 # boots the seeded API on :8000
├── Prospect_Assist_AI_Submission_Deck.pptx   # hackathon submission deck
├── Prospect_Assist_AI_Problem_Statement.md   # track problem statement
└── Prospect_Assist_AI_Comprehensive_Solution_Spec.md  # full solution specification
```

## 4. How it works — layer by layer

### 4.1 Data source abstraction (`connectors/`)

Every agent talks to the `BankDataConnector` interface, never to a concrete data
source. Phase 1 uses `MockSandboxConnector`; Phase 2 swaps in a bank-sandbox
connector and Phase 3 a production connector **by config only** — zero changes to
agents, orchestrator, schema, or the public API. The connector exposes account
transactions, UPI transactions, secondary bank statements, GST summaries, bureau
summaries, digital engagement logs, and alt-data proxies.

### 4.2 Mock sandbox (`data/generator.py`)

700 synthetic personas across 6 archetypes, generated with a fixed seed (42)
so every run is reproducible. Expected-tier labels, true income, and a latent
`will_convert` flag are held out for evaluation only — the scoring pipeline
never sees them.

**Anti-circularity design:** every persona draws its *true* income first; the
observable signals are then derived from it with realistic distortions — cash
income the bank never sees (15% of salaried), platform-fee/cash-tip variance
on gig credits, GST turnover underreporting, electricity/fuel proxy noise,
and 40% of gig workers splitting income across two banks. The agents estimate
through this observation model rather than inverting the generator's own
formulas, so eval accuracy is honest instead of tautological.

### 4.3 Transaction intelligence (`agents/transaction_parser.py`)

A rule engine categorizes each transaction (salary, gig income, rent, EMI,
insurance, utilities, investments, property, vehicle, medical, education,
wedding…) and extracts behavioral features: salary regularity and credit-date
consistency, gig platform diversity, income stability, SIP consistency,
savings-decline flags, and average spend per essential category.

### 4.4 Capability — "Can they repay?" (`agents/capability.py`)

Segment-specific income estimation with **explicit confidence**:

| Segment | Strategy | Confidence |
|---|---|---|
| Salaried | Median salary credit; regular credits on a consistent date → High | 0.90 |
| Gig / self-employed | UPI platform credits × **0.75 conservative discount**, cross-checked against GST turnover × industry margin (take the max) | 0.65 |
| New-to-credit | Alt-data proxies: `income ≈ 90 × electricity units + 2.2 × fuel spend` | 0.45 |

From estimated income it derives the affordability waterfall:

```
surplus  = income − essentials − committed savings
safe EMI = 60% of surplus
max loan = safe EMI × PVAF(8.5%, 20y)
```

plus FOIR, retained-money ratio, and a full obligation breakdown. A thin file
with no proxy data raises `InsufficientSignal` → **HTTP 422**, never a guess.

**Multi-account reconstruction (§5 multi-account behavior):** the orchestrator
merges account transactions, the UPI feed, and secondary-bank statements —
deduplicated by transaction id — so a gig worker whose payouts split across
two banks is assessed on the full income picture, with an explicit
"reconstructed across N accounts" evidence signal.

### 4.5 Intent — "Do they need a loan now?" (`agents/intent.py`)

Product-specific signal taxonomy (weights in points, capped at 100):

- **Home Loan** — builder/stamp-duty/registration payments (25), sustained rent
  ≥ ₹15k (15), savings accumulation for down-payment (15)
- **Auto Loan** — dealer/RTO/insurance payments (25), elevated fuel spend (10),
  loan closed in last 12 months — repayment proven, capacity freed (10)
- **Personal Loan** — medical (20) / education (20) / wedding (15) spend,
  card utilization > 80% (15), recent bureau inquiry (10), recent loan
  closure (10)
- **Mortgage/LAP** — business cash-flow / property signals (20), GST-registered
  business with regular filings (15), consistent savings build-up (10)

Real-time amplification adds engagement signals — loan-calculator usage, long
sessions in the loan section, repeated eligibility checks — **decayed by
recency**: 100% within 7 days, 50% within 14, 25% within 30, 0 after.

### 4.6 Risk, eligibility, conversion (`agents/scoring.py`)

- **DelinquencyRiskAgent** — forward-looking early warning from *current*
  behavior: card utilization level and 90-day trend, inquiry bursts, declining
  savings outflows. Risk > 0.6 forces the lead into `quality_watch`.
- **EligibilityEngine** — weighted ensemble (income stability 25, cash-flow
  surplus 25, bureau strength 20, obligation headroom 15, savings discipline 15)
  with **hard floors** (bureau < 500 or FOIR > 60% → score 0) and segment
  adjustment (salaried ×1.00, gig ×0.85, NTC ×0.90), checked against per-product
  minimums.
- **ConversionPropensityAgent** — sigmoid squashing over eligibility, intent,
  and engagement recency so the output reads as a probability, with an
  uncertainty band. Honest label: hand-set heuristic coefficients
  (`heuristic_sigmoid_v1`), not a statistically calibrated model — learned
  calibration on real outcomes arrives in Phase 2.
- **EvidenceCompilerAgent** — composite score (0.35 eligibility + 0.35 intent +
  0.30 conversion) → tier mapping, SHAP-style contributions, and the analyst
  narrative.

### 4.7 Orchestration & guardrails (`orchestrator.py`)

`Plan → Execute → Reflect → Evaluate` with:

- **Consent gate first** — no connector call happens without a valid token
  carrying the base scopes {transactions, bureau} (403).
- **Consent minimization** — optional scopes (upi, gst, alt_data) gate their
  data sources individually: a token without `gst` simply skips the GST
  cross-check instead of failing the request.
- **Contradiction gate** — high intent + high eligibility + high delinquency risk
  → `needs_manual_review`, never silently scored.
- **NTC confidence floor** — an NTC lead below 0.6 confidence can never be
  labeled `serious`.
- **Bounded re-segmentation retries** — a claimed salaried/gig profile whose
  capability assessment falls through to the low-confidence proxy strategy is
  re-segmented and re-scored as new-to-credit, capped at depth 3.
- **Thin-file promotion** — a gig lead with strong retained savings (> 25%),
  positive surplus, and clean risk is promoted to `interested` with an
  enhanced-review flag (instead of being dropped).

### 4.8 Public API (`api/app.py`)

Stable across all three phases:

| Endpoint | Purpose |
|---|---|
| `POST /mock/v1/consent/grant` | Issue a scoped consent token (24h TTL) |
| `DELETE /mock/v1/consent/{token}` | Revoke a consent token |
| `POST /api/v1/prospects/{id}/score` | Score one prospect for a product |
| `GET  /api/v1/prospects/{id}/leads` | List a prospect's scored leads |
| `POST /api/v1/prospects/batch-score` | Score a cohort — **one consent token per customer**, the server never self-grants (202 + job id) |
| `GET  /api/v1/batch-jobs/{job_id}` | Batch job status/results |
| `POST /api/v1/prospects/{id}/feedback` | RM/underwriting outcome feedback loop |
| `GET  /api/v1/feedback/summary` | Outcome counts — the Phase-2 training signal |
| `GET  /api/v1/dashboard` | Cohort KPIs + compact lead views for the RM console |

Error contract: **403** consent missing/expired · **422** thin file, no proxy
data · **503** upstream connector outage.

### 4.9 RM dashboard (`dashboard/`)

A React 18 + Vite + Recharts console styled on Material Design 3 (IDBI
green/orange tokens). Six panels per lead: snapshot with conversion/intent/risk
dials, income assessment, affordability waterfall (obligations vs. surplus →
safe EMI → max loan), risk assessment, SHAP-style "why this score" chart, and
the analyst narrative with intent-signal chips. The queue is filterable by tier
and product; every tier carries a recommended RM action.

**Live by default:** the console fetches `GET /api/v1/dashboard` on load and
shows a "● Live API" badge — the same origin in production (Docker/Render) and
the combined local server, or the Vite dev proxy on `:5173`. If no backend is
reachable it falls back to a bundled snapshot (`snapshot_data.json`, regenerated
via `python scripts/export_dashboard_data.py`) and labels itself "Snapshot
data" — the demo never breaks.

## 5. Running everything

Prerequisites: Python 3.12+, Node 18+.

```bash
# 1. Python deps + tests + eval
pip install -r requirements.txt
python -m pytest tests -q          # 25 tests: BDD scenarios + API contract + governance/signals
python eval/run_eval.py            # scores the 700-persona cohort → eval/eval_report.json

# 2. API server (FastAPI on :8000, seeded with the cohort)
python demo_server.py

# 3. Dashboard (Vite dev server on :5173)
cd dashboard
npm install
npm run dev
```

Example scoring call:

```bash
TOKEN=$(curl -s -X POST localhost:8000/mock/v1/consent/grant \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"salaried_high_intent-000","scope":["transactions","upi","bureau","alt_data","gst"]}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['consent_token'])")

curl -s -X POST localhost:8000/api/v1/prospects/salaried_high_intent-000/score \
  -H 'Content-Type: application/json' \
  -d "{\"product\":\"home_loan\",\"consent_token\":\"$TOKEN\"}"
# → tier "serious", 92.3% conversion propensity, full evidence bundle
```

Scoring without a token returns **403**; the consent gate sits in front of every
data fetch.

## 6. Deployment (one URL: dashboard + live API)

`demo_server.py` serves the built dashboard from the same FastAPI process when
`dashboard/dist` exists, so a single free-tier service hosts both the RM console
(at `/`) and the scoring API (`/api/…`, Swagger at `/docs`).

The repo ships a multi-stage [`Dockerfile`](Dockerfile) (Node builds the
dashboard, Python serves everything) and a [`render.yaml`](render.yaml) blueprint:

1. Push this repo to a public GitHub repository.
2. On [render.com](https://render.com): **New → Blueprint**, pick the repo —
   `render.yaml` configures a free Docker web service automatically
   (or **New → Web Service** with runtime *Docker*).
3. The deployed URL serves the dashboard at `/` and the API at `/docs`.

The same Dockerfile deploys unchanged to Railway, Fly.io, or Google Cloud Run.
Free-tier note: the service sleeps when idle and cold-starts in ~30 s.

To reproduce the combined server locally:

```bash
cd dashboard && npm install && npm run build && cd ..
python demo_server.py     # http://localhost:8000 → dashboard, /docs → API
```

## 7. Evaluation results (700 personas, seed=42)

All evaluation gates pass — with **honest, non-tautological numbers**: ground
truth is drawn independently of the scoring formulas (see §4.2), so accuracy
below 100% is by design, not failure.

| Gate | Target | Achieved |
|---|---|---|
| Income estimation accuracy (±15%) — salaried | ≥ 80% | **96.4%** |
| Income estimation accuracy (±15%) — gig/self-employed | ≥ 80% | **86.1%** |
| Income estimation accuracy (±15%) — new-to-credit | ≥ 80% | **85.0%** |
| Lead tiering quality (match or adjacent) | ≥ 85% | **100%** (exact match: 84.6%) |
| Simulated conversion proxy on contacted tiers | > 30% | **65.4%** |
| NTC hard-rule violations | 0 | **0** |
| Segment strategy selection | 100% | **100%** |
| Consent-gate violations | 0 | **0** |
| Mortgage/LAP coverage (gig cohort, expected band) | ≥ 85% | **100%** (100 scored) |

Tier distribution: 150 serious · 67 interested · 108 quality-watch ·
100 manual-review · 275 not-ready (RM priority queue: 217). The conversion
proxy uses a per-persona latent `will_convert` flag drawn at generation time
from archetype-level propensities — simulated, but no longer defined by the
tiers it is meant to validate.

**Caveat:** results on a synthetic cohort remain an upper bound, not a market
claim. Phase 2 re-runs the identical harness against IDBI-provided sandbox
data, with RM outcomes flowing back through the feedback endpoint.

## 8. Testing approach

The 9 BDD scenarios in `tests/test_bdd_scenarios.py` were written **before**
implementation (TDD): salaried high-intent home loan, gig-worker income
estimation, NTC alt-data fallback, consent refusal, thin-file 422, connector
outage 503, contradiction gate, NTC confidence floor, and thin-file promotion.
`tests/test_api_contract.py` locks the response shapes and error mapping, and
`tests/test_signal_and_governance.py` covers multi-account reconstruction,
UPI-feed deduplication, the re-segmentation retry, mortgage/LAP coverage,
loan-closure intent, consent TTL expiry, revocation, and consent minimization
— 25 tests in total.

## 9. Phase roadmap

- **Phase 1 (this repo)** — full multi-agent pipeline against the mock sandbox;
  deterministic, explainable scoring; working console; eval harness green.
- **Phase 2 — bank sandbox** — implement `BankSandboxConnector` against IDBI's
  sandbox OpenAPI spec, set `DATA_CONNECTOR=bank_sandbox`, re-run the same eval
  suite. Train XGBoost/CatBoost (eligibility, intent) and FinBERT (ambiguous
  narrations) behind the same agent interfaces; PostgreSQL 16 + Redis behind the
  same store interface.
- **Phase 3 — production** — Account Aggregator / GST / bureau / property &
  vehicle integrations, champion-challenger models, drift monitoring, audit
  trail, portfolio-level early-warning dashboards.

### Phase-1 simplifications (documented deviations)

- Persistence is an in-memory store seeded from generated fixtures; the Phase-2
  Docker stack brings PostgreSQL/Redis behind the same interfaces.
- Scoring uses deterministic rule-weighted ensembles with documented
  coefficients + sigmoid calibration; gradient-boosted models drop in once
  labeled sandbox data exists.
- The rule engine covers the synthetic corpus; FinBERT handles the ambiguous
  narration tail in Phase 2.
