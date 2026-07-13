# Track 2: Prospect Assist AI
### IDBI Innovate 2026 — Structured Problem Statement

---

## 1. Track Overview

| Field | Detail |
|---|---|
| **Track Name** | Prospect Assist AI |
| **Domain** | Retail Lending, Behavioral Analytics, Lead Generation |
| **Host** | IDBI Bank |
| **Products in Scope** | Personal Loan, Home Loan, Mortgage Loan (LAP), Auto Loan |

---

## 2. Background

IDBI Bank's retail lending funnel currently relies on **traditional, declaration-based metrics** — self-reported income, credit bureau scores, and static FOIR (Fixed Obligation to Income Ratio) calculations. This approach has two structural weaknesses:

- **Low conversion:** Current lead-to-loan conversion is estimated at **~1% or lower**, driven largely by "window shoppers" who check eligibility on digital channels without genuine borrowing intent.
- **Shallow income visibility:** Declared income and bureau scores don't capture a customer's *actual* cash-flow behavior, disposable income, or repayment discipline — leading to either missed genuine prospects or imprudent underwriting.

---

## 3. Problem Statement

> Bank's retail lending relies on traditional metrics, resulting in low conversions and limited insight into customer intent. A data-driven approach is needed to identify eligible, quantifiable-repayment-capacity, genuinely interested prospects using transaction and behavioral insights.

Restated: **Build an AI-driven system that separates genuinely interested, repayment-capable prospects from casual eligibility-checkers, by mining transaction and digital-behavior data — rather than relying on declared income and simple FOIR.**

This requires solving two coupled sub-problems:
1. **Capability** — Can the customer actually afford and repay the loan? (real income, disposable surplus, spending discipline)
2. **Intent** — Does the customer genuinely want/need a loan right now, and is that need being converted into a lead? (behavioral and digital signals, not just eligibility checks)

---

## 4. Core Objectives

1. **Assess true repayment capacity** — Move beyond salary-slip income and simple FOIR to a behavior-derived affordability estimate.
2. **Improve lead quality, not just volume** — Classify leads into tiers (e.g., *serious / interested / quality*) so relationship managers can prioritize effort.
3. **Handle non-standard income segments** — Gig workers, self-employed, and new-to-credit customers who lack conventional salary or bureau data.
4. **Predict forward-looking risk** — Provide a suggestive/early-warning signal for potential delinquency based on current spending patterns, not just historical bureau data.

---

## 5. Data & Behavioral Signals to Leverage

| Category | Signals |
|---|---|
| **Spending vs. Saving Discipline** | Whether income is retained/saved vs. spent immediately on credit; savings/FD/SIP regularity |
| **Digital Footprint** | UPI transaction patterns (merchant type, location, lifestyle spend); geo-location trends |
| **Multi-Account Behavior** | Secondary/other-bank statements to reconstruct total income and expense picture |
| **Digital Engagement** | Time spent on bank website/app, page depth — to separate genuine research from casual browsing |
| **Life-Event Signals** | Rent payments, builder/property payments, vehicle dealer payments, medical/education bills, wedding-related spend |
| **Credit-Seeking Behavior** | Bureau inquiry frequency, rising card utilization, loan closures |

---

## 6. Special Customer Segments

- **Gig Workers / Self-Employed (variable income):**
  Estimate *disposable income* using business turnover, industry-specific margins, and "retained money" (savings/investment outflows) vs. essential/luxury expense split — instead of a fixed salary assumption.

- **New-to-Credit (NTC) Applicants (thin file):**
  Where GST/UPI data is sparse, use alternate data proxies — electricity consumption, fuel spend, or other digital footprint signals — to infer business turnover and creditworthiness.

---

## 7. Expected Outcomes / Success Criteria

| Metric | Target |
|---|---|
| **Lead-to-loan conversion rate** | **> 30%** (up from ~1% baseline) |
| **Income estimation accuracy** | Accurate assessment of actual (not just declared) income to support underwriting |
| **Lead prioritization** | Leads categorized by seriousness/quality for RM triage |
| **Underwriting support** | Delinquency-risk signal derived from current behavior, feeding prudent loan structuring |
| **Coverage** | Solution must work across Personal, Home, Mortgage/LAP, and Auto loan products |

---

## 8. Constraints & Provided Resources

- **Sandbox Banking APIs** and **synthetic datasets** (transactions, MSME financials, UPI patterns) provided by IDBI Bank for prototyping — no access to live customer PII.
- **Cloud infra:** AWS / ACC tooling expected for build and deployment; reference architectures and starter kits provided.
- Solutions should respect **consent-based data usage** for any alternate/external data sources (Account Aggregator framework, GST, property/vehicle records).

---

## 9. What a Winning Solution Looks Like

A system that, for each customer, answers three questions from transaction and behavioral data alone:

1. **Can they repay?** → income + surplus cash flow + savings behavior
2. **Do they need a loan now?** → spending patterns, life events, purchase-intent signals
3. **Will they convert?** → product affinity, engagement, and historical response behavior

...and outputs a **prioritized, high-quality lead** (with supporting income/affordability evidence) to the underwriting/RM workflow — rather than a raw eligibility check.

---

## 10. Key Differentiator to Emphasize

The core innovation is **moving lending decisions from declared, static inputs to inferred, behavior-driven, and consented alternate-data insights** — closing the gap between "who says they want a loan" and "who actually needs, deserves, and will repay one."
