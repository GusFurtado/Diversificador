/**
 * MarkoWizard — analytical workstation.
 *
 * Owns the control-rail state (universe, history window, risk-free rate) and
 * the KPI band. The rest of the report (frontier, allocation, correlation,
 * per-asset statistics, saved runs) lands in later PRs and will read from
 * the same `state` object this file sets up.
 *
 * No framework, no build step — plain DOM, matching the rest of the repo.
 */

const UNIVERSE = [
  { t: "AAPL", n: "Apple" },
  { t: "MSFT", n: "Microsoft" },
  { t: "GOOGL", n: "Alphabet" },
  { t: "AMZN", n: "Amazon" },
  { t: "NVDA", n: "NVIDIA" },
  { t: "SPY", n: "S&P 500 ETF" },
  { t: "QQQ", n: "Nasdaq 100 ETF" },
  { t: "BND", n: "Total Bond ETF" },
  { t: "GLD", n: "Gold ETF" },
  { t: "VNQ", n: "Real Estate ETF" },
];

const DEFAULT_SEL = [0, 1, 5, 7, 8]; // AAPL, MSFT, SPY, BND, GLD

const PERIOD_WORDS = {
  "1y": "1-year",
  "2y": "2-year",
  "5y": "5-year",
  "10y": "10-year",
  max: "all available",
};

// Pending vs. applied mirrors the design handoff's state shape: `sel` /
// `period` / `rfIdx` are what the rail currently shows; `appliedSel` / etc.
// are what `result` was actually solved from. They start out equal (we
// auto-run once on load), and diverge the moment the user touches a control
// — that's what drives "Run analysis" vs. "Re-run analysis".
const state = {
  sel: [...DEFAULT_SEL],
  period: "5y",
  rfIdx: 8,
  appliedSel: [...DEFAULT_SEL],
  appliedPeriod: "5y",
  appliedRfIdx: 8,
  iF: null, // frontier selection; null = tangency (max Sharpe). Wired up in a later PR.
  cash: 0, // cash blend; wired up in a later PR.
  units: null, // null | 'annual'
  running: false,
  result: null,
  error: null,
  solvedAt: null,
};

function isAnnual() {
  return state.units === "annual";
}
function toReturn(v) {
  return isAnnual() ? Math.pow(1 + v, 12) - 1 : v;
}
function toVol(v) {
  return isAnnual() ? v * Math.sqrt(12) : v;
}
function toSharpe(v) {
  return isAnnual() ? v * Math.sqrt(12) : v;
}
function pct(v, decimals = 2) {
  return (v * 100).toFixed(decimals) + "%";
}
function rfOf(idx) {
  return +(idx * 0.00025).toFixed(5);
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function isStale() {
  return (
    state.sel.join() !== state.appliedSel.join() ||
    state.period !== state.appliedPeriod ||
    state.rfIdx !== state.appliedRfIdx
  );
}

/** The portfolio the KPI band (and, later, the rest of the report) reads
 * from. `iF` isn't selectable yet (that's the frontier chart's job, PR 4),
 * so this always resolves to the tangency portfolio for now. */
function selectedPortfolio() {
  if (!state.result) return null;
  if (state.iF == null) return state.result.max_sharpe_portfolio;
  return state.result.efficient_frontier[state.iF];
}

async function runAnalysis() {
  if (state.running) return;
  state.running = true;
  state.error = null;
  render();

  const tickers = state.sel.map((i) => UNIVERSE[i].t);
  try {
    const resp = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tickers,
        period: state.period,
        risk_free_rate: rfOf(state.rfIdx),
      }),
    });
    const body = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      throw new Error(body.detail || `Request failed (${resp.status})`);
    }

    state.result = body;
    state.appliedSel = [...state.sel];
    state.appliedPeriod = state.period;
    state.appliedRfIdx = state.rfIdx;
    state.iF = null;
    state.cash = 0;
    state.solvedAt = new Date().toTimeString().slice(0, 5);
  } catch (err) {
    state.error = err.message || String(err);
  } finally {
    state.running = false;
    render();
  }
}

/* ── Rendering ───────────────────────────────────────────────────────── */

function renderHeader() {
  const universeTag = document.getElementById("mw-header-universe");
  const periodTag = document.getElementById("mw-header-period");
  const status = document.getElementById("mw-header-status");
  const unitsBtn = document.getElementById("mw-units-btn");

  const shownSel = state.result ? state.appliedSel : state.sel;
  const shownPeriod = state.result ? state.appliedPeriod : state.period;
  universeTag.textContent = shownSel.map((i) => UNIVERSE[i].t).join(" · ");
  periodTag.textContent = (shownPeriod === "max" ? "Max" : shownPeriod.toUpperCase()) + " monthly";
  status.textContent = state.result ? `Solved ${state.solvedAt}` : "Not run yet";
  unitsBtn.textContent = isAnnual() ? "Annualized" : "Monthly";

  const runBtn = document.getElementById("mw-run-btn");
  runBtn.textContent = isStale() ? "Re-run analysis" : "Run analysis";
  runBtn.disabled = state.running;
}

function renderChips() {
  document.getElementById("mw-chips").querySelectorAll(".mw-chip").forEach((btn) => {
    const idx = +btn.dataset.idx;
    btn.classList.toggle("mw-chip--selected", state.sel.includes(idx));
  });
  document.getElementById("mw-chip-count").textContent =
    `${state.sel.length} of ${UNIVERSE.length} selected · minimum 2`;
}

function renderOverlay() {
  const overlay = document.getElementById("mw-overlay");
  overlay.hidden = !state.running;
  document.getElementById("mw-overlay-note").textContent =
    state.sel.map((i) => UNIVERSE[i].t).join(" · ");
}

function kpiSectionHtml() {
  const p = selectedPortfolio();
  const unitWord = isAnnual() ? "annualized" : "monthly";
  const n = state.appliedSel.length;

  const headline = `The best risk-adjusted mix of your ${n} asset${n === 1 ? "" : "s"}`;
  const periodWords = PERIOD_WORDS[state.appliedPeriod] || state.appliedPeriod;
  const lede =
    `Estimated from ${periodWords} monthly history at a ${pct(toReturn(rfOf(state.appliedRfIdx)))} ` +
    `${unitWord} risk-free rate. Fully invested in the risky portfolio.`;

  const weights = Object.values(p.weights);
  const holdings = weights.filter((w) => w > 0.005).length;
  const diversification = 1 / weights.reduce((a, w) => a + w * w, 0);

  const kpis = [
    { label: "Expected return", value: pct(toReturn(p.expected_return)), note: unitWord },
    { label: "Volatility", value: pct(toVol(p.risk)), note: "standard deviation" },
    { label: "Sharpe ratio", value: toSharpe(p.sharpe).toFixed(2), note: "unchanged by the cash blend", accent: true },
    { label: "Holdings", value: String(holdings), note: `of ${n} assets, non-zero weight` },
    { label: "Diversification", value: diversification.toFixed(1), note: "effective assets held" },
  ];

  return `
    <section>
      <h6 style="color:var(--color-accent-300);margin-bottom:var(--space-2)">Portfolio report</h6>
      <h1 class="mw-headline">${escapeHtml(headline)}</h1>
      <p class="text-muted mw-lede">${escapeHtml(lede)}</p>
      <div class="mw-kpi-grid">
        ${kpis.map((k) => `
          <div class="card elev-sm" style="gap:var(--space-1)">
            <span class="card-kicker">${escapeHtml(k.label)}</span>
            <span class="mw-kpi-value${k.accent ? " mw-kpi-value--accent" : ""}">${escapeHtml(k.value)}</span>
            <span class="text-muted" style="font-size:11.5px">${escapeHtml(k.note)}</span>
          </div>`).join("")}
      </div>
    </section>`;
}

function errorCardHtml() {
  return `
    <div class="card elev-sm mw-error">
      <span class="card-kicker">Analysis failed</span>
      <p class="card-body">${escapeHtml(state.error)}</p>
      <button type="button" class="btn btn-secondary" data-action="run" style="align-self:flex-start">Retry</button>
    </div>`;
}

function renderKpiSlot() {
  const slot = document.getElementById("mw-kpi-slot");
  if (state.error) {
    slot.innerHTML = errorCardHtml();
  } else if (state.result) {
    slot.innerHTML = kpiSectionHtml();
  } else {
    slot.innerHTML = "";
  }
}

function render() {
  renderHeader();
  renderChips();
  renderOverlay();
  renderKpiSlot();
}

/* ── Event wiring ────────────────────────────────────────────────────── */

function init() {
  document.getElementById("mw-chips").addEventListener("click", (e) => {
    const btn = e.target.closest(".mw-chip");
    if (!btn) return;
    const idx = +btn.dataset.idx;
    const selected = state.sel.includes(idx);
    if (selected && state.sel.length <= 2) return; // minimum 2, per the handoff
    state.sel = selected ? state.sel.filter((i) => i !== idx) : [...state.sel, idx].sort((a, b) => a - b);
    render();
  });

  document.getElementById("mw-period").querySelectorAll('input[name="mwperiod"]').forEach((input) => {
    input.addEventListener("change", () => {
      state.period = input.value;
      render();
    });
  });

  const rf = document.getElementById("mwrf");
  rf.addEventListener("input", () => {
    state.rfIdx = +rf.value;
    document.getElementById("mwrf-display").textContent = pct(toReturn(rfOf(state.rfIdx)));
    render();
  });

  document.getElementById("mw-units-btn").addEventListener("click", () => {
    state.units = isAnnual() ? null : "annual";
    render();
  });

  // Delegated: both the rail's Run button and the error card's Retry button
  // carry data-action="run" — the latter only exists after a re-render, so
  // it can't have a listener attached directly.
  document.body.addEventListener("click", (e) => {
    if (e.target.closest('[data-action="run"]')) runAnalysis();
  });

  render();
  runAnalysis();
}

document.addEventListener("DOMContentLoaded", init);
