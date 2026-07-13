import { useState, useMemo, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, ReferenceLine, ResponsiveContainer, Cell, Tooltip } from "recharts";

/* ============================================================
   Prospect Assist AI — Underwriting Support Dashboard (Layer 8)
   Material Design 3 · tokens seeded on IDBI green / orange
   Data: Phase-1 mock sandbox, 700 synthetic personas (seed=42)
   ============================================================ */

import SNAPSHOT from "./snapshot_data.json";

/* ---------- MD3 design tokens ---------- */
const T = {
  primary: "#006B5B", onPrimary: "#FFFFFF",
  primaryContainer: "#74F8DE", onPrimaryContainer: "#00201A",
  secondaryContainer: "#CCE8E0", onSecondaryContainer: "#06201B",
  tertiary: "#B54708", tertiaryContainer: "#FFDCC7", onTertiaryContainer: "#331200",
  surface: "#F5FAF7", surfaceContainer: "#E9EFEB", surfaceContainerHigh: "#DDE4E0",
  surfaceContainerLow: "#EFF5F1", onSurface: "#171D1B", onSurfaceVariant: "#3F4945",
  outline: "#6F7975", outlineVariant: "#BEC9C4",
  error: "#BA1A1A", errorContainer: "#FFDAD6", onErrorContainer: "#410002",
  amber: "#B26A00", amberContainer: "#FFDEA8",
};

const TIER_META = {
  serious:            { label: "Serious",        bg: T.primary,          fg: "#fff",                 action: "Priority RM call today" },
  interested:         { label: "Interested",     bg: T.secondaryContainer, fg: T.onSecondaryContainer, action: "Personalized offer campaign" },
  quality_watch:      { label: "Quality watch",  bg: T.amberContainer,   fg: "#4A2800",              action: "Nurture · monitor risk drivers" },
  needs_manual_review:{ label: "Manual review",  bg: T.tertiaryContainer, fg: T.onTertiaryContainer, action: "Route to underwriter" },
  not_ready:          { label: "Not ready",      bg: T.surfaceContainerHigh, fg: T.onSurfaceVariant, action: "Drip marketing only" },
};

const PRODUCT_LABEL = { home_loan: "Home Loan", personal_loan: "Personal Loan", auto_loan: "Auto Loan", mortgage_lap: "Mortgage / LAP" };
const SEGMENT_LABEL = { salaried: "Salaried", gig_self_employed: "Gig / Self-employed", new_to_credit: "New-to-credit" };
const inr = (n) => "₹" + Math.round(n).toLocaleString("en-IN");
const pct = (n) => Math.round(n * 100) + "%";

const type = {
  display: { fontSize: 30, fontWeight: 400, letterSpacing: 0 },
  headline: { fontSize: 22, fontWeight: 400 },
  titleL: { fontSize: 18, fontWeight: 500 },
  title: { fontSize: 15, fontWeight: 500 },
  body: { fontSize: 13.5, fontWeight: 400, lineHeight: 1.45 },
  label: { fontSize: 11.5, fontWeight: 500, letterSpacing: 0.4, textTransform: "uppercase" },
};

function Chip({ active, onClick, children, count }) {
  return (
    <button onClick={onClick}
      style={{
        display: "inline-flex", alignItems: "center", gap: 6, cursor: "pointer",
        height: 32, padding: "0 14px", borderRadius: 8,
        border: `1px solid ${active ? "transparent" : T.outlineVariant}`,
        background: active ? T.secondaryContainer : "transparent",
        color: active ? T.onSecondaryContainer : T.onSurfaceVariant,
        fontSize: 13, fontWeight: 500, fontFamily: "inherit",
      }}>
      {active && <span aria-hidden>✓</span>}{children}
      {count != null && <span style={{ opacity: 0.7 }}>{count}</span>}
    </button>
  );
}

function TierBadge({ tier, small }) {
  const m = TIER_META[tier];
  return (
    <span style={{
      background: m.bg, color: m.fg, borderRadius: 8,
      padding: small ? "3px 9px" : "5px 12px",
      fontSize: small ? 11 : 12.5, fontWeight: 600, whiteSpace: "nowrap",
    }}>{m.label}</span>
  );
}

function Card({ children, style, filled }) {
  return (
    <div style={{
      background: filled ? T.surfaceContainerLow : "#fff",
      border: `1px solid ${T.outlineVariant}`,
      borderRadius: 16, padding: 18, ...style,
    }}>{children}</div>
  );
}

function PanelTitle({ children, sub }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ ...type.title, color: T.onSurface }}>{children}</div>
      {sub && <div style={{ ...type.body, color: T.onSurfaceVariant, fontSize: 12.5 }}>{sub}</div>}
    </div>
  );
}

function Row({ k, v, strong, alert }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, padding: "6px 0", borderBottom: `1px solid ${T.surfaceContainer}` }}>
      <span style={{ ...type.body, color: T.onSurfaceVariant }}>{k}</span>
      <span style={{ ...type.body, fontWeight: strong ? 600 : 500, color: alert ? T.tertiary : T.onSurface, textAlign: "right" }}>{v}</span>
    </div>
  );
}

function ScoreDial({ value, label, color }) {
  const deg = Math.min(1, Math.max(0, value)) * 360;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
      <div style={{
        width: 74, height: 74, borderRadius: "50%",
        background: `conic-gradient(${color} ${deg}deg, ${T.surfaceContainerHigh} 0deg)`,
        display: "grid", placeItems: "center",
      }}>
        <div style={{ width: 56, height: 56, borderRadius: "50%", background: "#fff", display: "grid", placeItems: "center", fontWeight: 600, fontSize: 15, color: T.onSurface }}>
          {pct(value)}
        </div>
      </div>
      <div style={{ ...type.label, color: T.onSurfaceVariant }}>{label}</div>
    </div>
  );
}

/* Affordability waterfall: income bar decomposed into obligations + surplus */
function AffordabilityBar({ afford }) {
  const parts = [
    ["EMIs", afford.existing_emi, "#8C1D18"],
    ["Rent", afford.rent, "#B3261E"],
    ["Insurance", afford.insurance, "#7D5260"],
    ["Utilities", afford.utilities, "#625B71"],
    ["Living", afford.minimum_living, "#79747E"],
    ["Savings", afford.mandatory_savings, "#4A635D"],
    ["Surplus", afford.monthly_surplus, T.primary],
  ].filter(([, v]) => v > 0);
  const total = afford.estimated_monthly_income || parts.reduce((a, [, v]) => a + v, 0);
  return (
    <div>
      <div style={{ display: "flex", height: 26, borderRadius: 8, overflow: "hidden", border: `1px solid ${T.outlineVariant}` }}>
        {parts.map(([k, v, c]) => (
          <div key={k} title={`${k}: ${inr(v)}`} style={{ width: `${(v / total) * 100}%`, background: c, minWidth: 2 }} />
        ))}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px 14px", marginTop: 8 }}>
        {parts.map(([k, v, c]) => (
          <span key={k} style={{ ...type.body, fontSize: 12, color: T.onSurfaceVariant, display: "inline-flex", alignItems: "center", gap: 5 }}>
            <span style={{ width: 9, height: 9, borderRadius: 2, background: c, display: "inline-block" }} />
            {k} {inr(v)}
          </span>
        ))}
      </div>
    </div>
  );
}

function ContributionChart({ contrib }) {
  const data = contrib.map((c) => ({ name: c.feature, impact: c.impact }));
  return (
    <div style={{ width: "100%", height: 46 + data.length * 34 }}>
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24, top: 4 }}>
          <XAxis type="number" tick={{ fontSize: 11, fill: T.onSurfaceVariant }} axisLine={false} tickLine={false} />
          <YAxis type="category" dataKey="name" width={160} tick={{ fontSize: 12, fill: T.onSurface }} axisLine={false} tickLine={false} />
          <ReferenceLine x={0} stroke={T.outline} />
          <Tooltip formatter={(v) => [v, "Impact on score"]} cursor={{ fill: T.surfaceContainer }} />
          <Bar dataKey="impact" radius={[4, 4, 4, 4]} barSize={16} isAnimationActive={false}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.impact >= 0 ? T.primary : T.error} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function LeadDetail({ lead }) {
  const m = TIER_META[lead.tier];
  const flags = Object.keys(lead.reflection || {}).filter((k) => k !== "retries");
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {/* Panel 1 — Snapshot */}
      <Card filled style={{ background: T.surfaceContainerLow }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 14, alignItems: "center" }}>
          <div>
            <div style={{ ...type.headline, color: T.onSurface }}>{lead.customer_id}</div>
            <div style={{ ...type.body, color: T.onSurfaceVariant, marginTop: 2 }}>
              {SEGMENT_LABEL[lead.segment]} · {PRODUCT_LABEL[lead.product]} · Lead {lead.lead_id}
            </div>
            <div style={{ marginTop: 10, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <TierBadge tier={lead.tier} />
              <span style={{
                background: lead.queue ? T.primaryContainer : T.surfaceContainerHigh,
                color: lead.queue ? T.onPrimaryContainer : T.onSurfaceVariant,
                borderRadius: 8, padding: "5px 12px", fontSize: 12.5, fontWeight: 600,
              }}>{m.action}</span>
            </div>
          </div>
          <div style={{ display: "flex", gap: 18 }}>
            <ScoreDial value={lead.conv} label="Conversion" color={T.primary} />
            <ScoreDial value={lead.intent} label="Intent" color="#356A5F" />
            <ScoreDial value={lead.risk} label="Delinquency risk" color={lead.risk > 0.6 ? T.error : T.amber} />
          </div>
        </div>
        {flags.length > 0 && (
          <div style={{ marginTop: 12, background: T.tertiaryContainer, color: T.onTertiaryContainer, borderRadius: 12, padding: "10px 14px", ...type.body }}>
            Reflection gate: {flags.map((f) => f.replace(/_/g, " ")).join(" · ")}
          </div>
        )}
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(290px, 1fr))", gap: 14 }}>
        {/* Panel 2 — Income assessment */}
        <Card>
          <PanelTitle sub="Inferred from transactions, not salary slips">Income assessment</PanelTitle>
          <Row k="Estimated monthly income" v={inr(lead.income)} strong />
          <Row k="Estimation strategy" v={SEGMENT_LABEL[lead.strategy] || lead.strategy} />
          <Row k="Income confidence" v={lead.income_conf} alert={lead.income_conf === "Low"} />
          <Row k="Income stability" v={lead.stability} />
          <Row k="Eligibility score" v={`${lead.elig} / 100`} />
          <Row k="Model confidence" v={lead.confidence} alert={lead.confidence < 0.6} />
        </Card>

        {/* Panel 4 — Risk */}
        <Card>
          <PanelTitle sub="Forward-looking early-warning signal">Risk assessment</PanelTitle>
          <Row k="Delinquency risk" v={pct(lead.risk)} strong alert={lead.risk > 0.6} />
          <Row k="FOIR" v={pct(lead.foir)} alert={lead.foir > 0.5} />
          <div style={{ marginTop: 10 }}>
            {lead.risk_drivers.map((d, i) => (
              <div key={i} style={{ ...type.body, color: lead.risk > 0.6 ? T.onErrorContainer : T.onSurfaceVariant, background: lead.risk > 0.6 ? T.errorContainer : T.surfaceContainerLow, borderRadius: 8, padding: "7px 11px", marginBottom: 6 }}>
                {d}
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Panel 3 — Affordability */}
      <Card>
        <PanelTitle sub="Behavior-derived surplus, not fixed FOIR">Affordability</PanelTitle>
        <AffordabilityBar afford={lead.afford} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 12, marginTop: 14 }}>
          {[["Monthly surplus", inr(lead.afford.monthly_surplus)],
            ["Safe EMI capacity", inr(lead.safe_emi)],
            ["Max loan eligibility", inr(lead.max_loan)]].map(([k, v]) => (
            <div key={k} style={{ background: T.surfaceContainerLow, borderRadius: 12, padding: "12px 14px" }}>
              <div style={{ ...type.label, color: T.onSurfaceVariant }}>{k}</div>
              <div style={{ fontSize: 19, fontWeight: 600, color: T.primary, marginTop: 3 }}>{v}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Panel 6 — Explainability contributions */}
      <Card>
        <PanelTitle sub="Feature contributions to the composite score (SHAP-style)">Why this score</PanelTitle>
        <ContributionChart contrib={lead.contrib} />
      </Card>

      {/* Panel 5 — Narrative + evidence */}
      <Card>
        <PanelTitle sub="Evidence bundle — every signal that drove the tier">Analyst narrative</PanelTitle>
        <div style={{ ...type.body, whiteSpace: "pre-line", color: T.onSurface, background: T.surfaceContainerLow, borderRadius: 12, padding: 14 }}>
          {lead.narrative}
        </div>
        {(lead.intent_signals.length > 0) && (
          <div style={{ marginTop: 12 }}>
            <div style={{ ...type.label, color: T.onSurfaceVariant, marginBottom: 6 }}>Intent signals</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {lead.intent_signals.map((s, i) => (
                <span key={i} style={{ ...type.body, fontSize: 12, border: `1px solid ${T.outlineVariant}`, borderRadius: 8, padding: "5px 10px", color: T.onSurfaceVariant }}>{s}</span>
              ))}
            </div>
          </div>
        )}
        <div style={{ ...type.body, fontSize: 11.5, color: T.onSurfaceVariant, marginTop: 12 }}>
          Decision support only — a human underwriter makes the final lending decision.
        </div>
      </Card>
    </div>
  );
}

export default function ProspectAssistDashboard() {
  const [tierFilter, setTierFilter] = useState("all");
  const [productFilter, setProductFilter] = useState("all");
  const [selectedId, setSelectedId] = useState(null);
  // Live-first: same-origin API (demo server / Render) or the Vite dev proxy;
  // falls back to the bundled snapshot when no backend is reachable.
  const [data, setData] = useState(null);
  const [source, setSource] = useState("loading");

  useEffect(() => {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 5000);
    fetch("/api/v1/dashboard", { signal: ctl.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
      .then((d) => { setData(d); setSource("live"); })
      .catch(() => { setData(SNAPSHOT); setSource("snapshot"); })
      .finally(() => clearTimeout(timer));
    return () => { clearTimeout(timer); ctl.abort(); };
  }, []);

  const leads = useMemo(() => (data ? data.leads.filter((l) =>
    (tierFilter === "all" || l.tier === tierFilter) &&
    (productFilter === "all" || l.product === productFilter)
  ) : []), [data, tierFilter, productFilter]);

  if (!data) {
    return (
      <div style={{ fontFamily: "Roboto, 'Segoe UI', system-ui, sans-serif", background: T.surface, minHeight: "100vh", display: "grid", placeItems: "center", color: T.onSurfaceVariant }}>
        Loading scored cohort…
      </div>
    );
  }

  const selected = data.leads.find((l) => l.lead_id === selectedId) || leads[0];
  const k = data.kpi;
  const ev = k.eval || {};

  const kpis = [
    { label: "Prospects scored", value: k.total_scored.toLocaleString("en-IN"), sub: "Phase-1 synthetic cohort" },
    { label: "RM priority queue", value: k.rm_queue, sub: "Serious + interested tiers" },
    { label: "Avg conversion · serious", value: pct(k.avg_conversion_priority), sub: "Heuristic sigmoid probability" },
    { label: "Tiering quality (eval)", value: ev.lead_tiering_quality != null ? pct(ev.lead_tiering_quality) : "—", sub: "match or adjacent · synthetic" },
    { label: "Consent violations", value: ev.consent_gate_violations != null ? ev.consent_gate_violations : "—", sub: "Hard governance gate", ok: ev.consent_gate_violations === 0 },
  ];

  return (
    <div style={{ fontFamily: "Roboto, 'Segoe UI', system-ui, sans-serif", background: T.surface, minHeight: "100vh", color: T.onSurface }}>
      {/* Top app bar */}
      <header style={{ background: T.surface, borderBottom: `1px solid ${T.outlineVariant}`, padding: "14px 22px", display: "flex", alignItems: "center", gap: 14, position: "sticky", top: 0, zIndex: 5 }}>
        <div style={{ width: 40, height: 40, borderRadius: 12, background: T.primary, color: "#fff", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 17 }}>P</div>
        <div>
          <div style={{ ...type.titleL }}>Prospect Assist AI</div>
          <div style={{ ...type.body, fontSize: 12, color: T.onSurfaceVariant }}>Underwriting support · IDBI retail lending · Mock sandbox (Phase 1)</div>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <span title={source === "live"
            ? "Leads scored by the running API at startup"
            : "Bundled snapshot — start the API server for live data"}
            style={{
              background: source === "live" ? T.primaryContainer : T.surfaceContainerHigh,
              color: source === "live" ? T.onPrimaryContainer : T.onSurfaceVariant,
              borderRadius: 8, padding: "6px 12px", fontSize: 12, fontWeight: 600,
            }}>
            {source === "live" ? "● Live API" : "Snapshot data"}
          </span>
        </div>
      </header>

      <main style={{ maxWidth: 1240, margin: "0 auto", padding: "20px 20px 48px" }}>
        {/* KPI row */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
          {kpis.map((c) => (
            <Card key={c.label} filled>
              <div style={{ ...type.label, color: T.onSurfaceVariant }}>{c.label}</div>
              <div style={{ fontSize: 27, fontWeight: 600, marginTop: 4, color: c.ok === false ? T.error : T.onSurface }}>{c.value}</div>
              <div style={{ ...type.body, fontSize: 12, color: T.onSurfaceVariant }}>{c.sub}</div>
            </Card>
          ))}
        </div>
        {k.caveat && (
          <div style={{ ...type.body, fontSize: 11.5, fontStyle: "italic", color: T.onSurfaceVariant, marginTop: 8 }}>
            {k.caveat}
          </div>
        )}

        {/* Filters */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, margin: "18px 0 14px", alignItems: "center" }}>
          <Chip active={tierFilter === "all"} onClick={() => setTierFilter("all")}>All tiers</Chip>
          {Object.keys(TIER_META).map((t) => (
            <Chip key={t} active={tierFilter === t} onClick={() => setTierFilter(t)}
              count={data.leads.filter((l) => l.tier === t).length}>
              {TIER_META[t].label}
            </Chip>
          ))}
          <span style={{ width: 1, height: 24, background: T.outlineVariant, margin: "0 4px" }} />
          {["all", ...Object.keys(PRODUCT_LABEL)].map((p) => (
            <Chip key={p} active={productFilter === p} onClick={() => setProductFilter(p)}>
              {p === "all" ? "All products" : PRODUCT_LABEL[p]}
            </Chip>
          ))}
        </div>

        {/* Queue + detail */}
        <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 360px) 1fr", gap: 16, alignItems: "start" }}>
          <Card style={{ padding: 8, maxHeight: 720, overflowY: "auto" }}>
            {leads.length === 0 && (
              <div style={{ ...type.body, color: T.onSurfaceVariant, padding: 16 }}>
                No leads match these filters. Clear a filter to see the queue.
              </div>
            )}
            {leads.map((l) => {
              const active = selected && l.lead_id === selected.lead_id;
              return (
                <button key={l.lead_id} onClick={() => setSelectedId(l.lead_id)}
                  style={{
                    display: "block", width: "100%", textAlign: "left", cursor: "pointer",
                    background: active ? T.secondaryContainer : "transparent",
                    border: "none", borderRadius: 12, padding: "11px 12px",
                    fontFamily: "inherit", marginBottom: 2,
                  }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                    <span style={{ ...type.body, fontWeight: 600, color: T.onSurface, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {l.customer_id}
                    </span>
                    <TierBadge tier={l.tier} small />
                  </div>
                  <div style={{ ...type.body, fontSize: 12, color: T.onSurfaceVariant, marginTop: 3 }}>
                    {PRODUCT_LABEL[l.product]} · {inr(l.income)}/mo · conv {pct(l.conv)}
                  </div>
                </button>
              );
            })}
          </Card>
          <div>{selected && <LeadDetail lead={selected} />}</div>
        </div>
      </main>
    </div>
  );
}
