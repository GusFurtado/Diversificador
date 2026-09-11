/**
 * MarkoWizard — analytical workstation.
 *
 * Owns the control-rail state (universe, history window, risk-free rate),
 * the KPI band, the efficient-frontier chart, and the allocation donut/cash
 * blend/weights table. The rest of the report (correlation, per-asset
 * statistics, saved runs) lands in later PRs and will read from the same
 * `state` object this file sets up.
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

// Chart series order, assigned by position in the selection — shared by the
// frontier's per-asset dots and (in later PRs) the allocation donut/table.
const CHART_PALETTE = [
  "#2fc7cc", "#001d63", "#008ea0", "#42d4d7", "#64748b",
  "#2c4d9c", "#00424c", "#94a3b8", "#5f7cbd", "#cbd5e1",
];

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
  iF: null, // frontier selection; null = tangency (max Sharpe)
  cash: 0, // cash blend; wired up in a later PR
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
function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}
/** "Nice" tick step for an axis running 0..max: the largest of 1/2/2.5/5 x
 * 10^n that still gives at least 4 ticks. Same rule the design handoff's
 * prototype uses, so frontier tick counts match the reference screenshots. */
function niceTickValues(max) {
  const raw = max / 4;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) || mag * 10;
  const out = [];
  for (let v = 0; v <= max + 1e-9; v += step) out.push(v);
  return out;
}

function isStale() {
  return (
    state.sel.join() !== state.appliedSel.join() ||
    state.period !== state.appliedPeriod ||
    state.rfIdx !== state.appliedRfIdx
  );
}

/** Resolves `state.iF` against the current result: the effective frontier
 * index, the tangency (max-Sharpe) index, and the descriptive label the
 * design handoff uses for both the frontier stats panel and the KPI
 * headline. `efficient_frontier[best]` and `max_sharpe_portfolio` are the
 * same row from the backend's optimizer output, just serialized twice —
 * reading through the frontier array here keeps a single source of truth
 * for "which point is selected". */
function resolveSelection(result) {
  const pts = result.efficient_frontier;
  const best = pts.reduce(
    (b, p, i) => ((p.sharpe ?? -Infinity) > (pts[b].sharpe ?? -Infinity) ? i : b),
    0,
  );
  const iF = state.iF == null ? best : Math.max(0, Math.min(pts.length - 1, state.iF));
  let label;
  if (iF === best) label = "Tangency portfolio — maximum Sharpe";
  else if (iF === 0) label = "Minimum-variance portfolio";
  else if (iF < best) label = "Below tangency — risk-averse";
  else if (iF > pts.length - 5) label = "Frontier edge — single-asset concentration";
  else label = "Above tangency — return-seeking";
  return { iF, best, label, isBest: iF === best };
}

/** The portfolio the KPI band (and, later, the rest of the report) reads
 * from. */
function selectedPortfolio() {
  if (!state.result) return null;
  const { iF } = resolveSelection(state.result);
  return state.result.efficient_frontier[iF];
}

/** Blends the selected portfolio with cash: a plain weighted average, valid
 * for whatever point is currently selected — not the theoretical capital
 * allocation line specifically, which (by construction) only dominates the
 * frontier when it's anchored at the tangency portfolio. The backend's
 * `capital_allocation_line` is fixed to the tangency portfolio for exactly
 * that reason, so it can't be reused here once the frontier selection (PR 4)
 * has moved off tangency; this local formula is what the design handoff's
 * own prototype uses too, for any selected point, not just the tangency
 * case the README's "prefer the API's CAL" note assumed. Sharpe is
 * unaffected by a cash blend, so callers that need it just read `p.sharpe`
 * directly. */
function cashBlend(p) {
  const cashP = state.cash / 100;
  const rf = rfOf(state.appliedRfIdx);
  return {
    expectedReturn: cashP * rf + (1 - cashP) * p.expected_return,
    risk: (1 - cashP) * p.risk,
  };
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

  const { label, isBest } = resolveSelection(state.result);
  const headline = isBest ? `The best risk-adjusted mix of your ${n} asset${n === 1 ? "" : "s"}` : label;
  const periodWords = PERIOD_WORDS[state.appliedPeriod] || state.appliedPeriod;
  const lede =
    `Estimated from ${periodWords} monthly history at a ${pct(toReturn(rfOf(state.appliedRfIdx)))} ` +
    `${unitWord} risk-free rate. ` +
    (state.cash > 0
      ? `Figures below include a ${state.cash}% cash position.`
      : "Fully invested in the risky portfolio.");

  const weights = Object.values(p.weights);
  const holdings = weights.filter((w) => w > 0.005).length;
  const diversification = 1 / weights.reduce((a, w) => a + w * w, 0);
  const blend = cashBlend(p);

  const kpis = [
    { label: "Expected return", value: pct(toReturn(blend.expectedReturn)), note: unitWord },
    { label: "Volatility", value: pct(toVol(blend.risk)), note: "standard deviation" },
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

/* ── Efficient frontier ──────────────────────────────────────────────── */

// SVG plot box, per the handoff: viewBox 0 0 880 470, x from 62 to 862
// (zero at 62), y from 404 (zero) up to 26.
const FR_X0 = 62;
const FR_X_SPAN = 800;
const FR_Y0 = 404;
const FR_Y_SPAN = 378;

// Rebuilt only when `state.result` changes (a new run) — holds the scale
// functions and point coordinates the base SVG and the selection overlay
// both read. Recomputing this on every drag frame would be wasteful and,
// worse, would mean tearing down the SVG element mid-drag and losing its
// pointer capture (see renderFrontier below).
let frontierGeo = null;
let frontierBaseResult = null;
let frontierBaseUnits = null;

function computeFrontierGeometry(result) {
  const pts = result.efficient_frontier;
  const assetStats = result.asset_statistics || [];
  const xMax = Math.max(...pts.map((q) => q.risk), ...assetStats.map((a) => a.volatility)) * 1.08;
  const yMax =
    Math.max(...pts.map((q) => q.expected_return), ...assetStats.map((a) => a.expected_return)) * 1.12;
  const X = (v) => FR_X0 + (v / xMax) * FR_X_SPAN;
  const Y = (v) => FR_Y0 - (v / yMax) * FR_Y_SPAN;
  const geo = pts.map((q) => ({ cx: +X(q.risk).toFixed(1), cy: +Y(q.expected_return).toFixed(1) }));
  return { pts, assetStats, xMax, yMax, X, Y, geo };
}

/** Maps a pointer event's x position to the nearest frontier point by risk,
 * accounting for the plot box's left inset — not a naive fraction of the
 * SVG element's width. */
function pickFrontierPoint(evt, svgEl) {
  const rect = svgEl.getBoundingClientRect();
  const t = Math.max(
    0,
    Math.min(1, (evt.clientX - rect.left - (FR_X0 / 880) * rect.width) / ((FR_X_SPAN / 880) * rect.width)),
  );
  const target = t * frontierGeo.xMax;
  let bestIdx = 0;
  let bestDist = Infinity;
  frontierGeo.pts.forEach((q, i) => {
    const d = Math.abs(q.risk - target);
    if (d < bestDist) {
      bestDist = d;
      bestIdx = i;
    }
  });
  state.iF = bestIdx;
  render();
}

function frontierSectionHtml(result) {
  const geo = frontierGeo;
  const rf = rfOf(state.appliedRfIdx);
  const { best } = resolveSelection(result);

  const gridPath = niceTickValues(geo.yMax).map((v) => `M${FR_X0} ${geo.Y(v).toFixed(1)}H862`).join(" ");
  const xTickPath = niceTickValues(geo.xMax).map((v) => `M${geo.X(v).toFixed(1)} ${FR_Y0}v7`).join(" ");
  const dotsPath = geo.geo
    .map((g) => `M${(g.cx - 2.2).toFixed(1)} ${g.cy}a2.2 2.2 0 1 0 4.4 0a2.2 2.2 0 1 0 -4.4 0`)
    .join(" ");
  const line = geo.geo.map((g) => `${g.cx},${g.cy}`).join(" ");
  const mvp = geo.geo[0];
  const tan = geo.geo[best];

  const tanPoint = geo.pts[best];
  const slope = (tanPoint.expected_return - rf) / tanPoint.risk;
  let calX = geo.xMax;
  let calY = rf + slope * calX;
  if (calY > geo.yMax) {
    calY = geo.yMax;
    calX = (geo.yMax - rf) / slope;
  }
  const cal = {
    x1: geo.X(0).toFixed(1), y1: geo.Y(rf).toFixed(1),
    x2: geo.X(calX).toFixed(1), y2: geo.Y(calY).toFixed(1),
    pctX: (((geo.X(calX) - 6) / 880) * 100).toFixed(2),
    pctY: (((geo.Y(calY) + 6) / 470) * 100).toFixed(2),
  };

  const unitWord = isAnnual() ? "annualized" : "monthly";
  const yTicks = niceTickValues(geo.yMax).map((v) => ({
    pctY: ((geo.Y(v) / 470) * 100).toFixed(2),
    label: pct(toReturn(v), isAnnual() ? 0 : 1),
  }));
  const xTicks = niceTickValues(geo.xMax).map((v) => ({
    pctX: ((geo.X(v) / 880) * 100).toFixed(2),
    label: pct(toVol(v), isAnnual() ? 0 : 1),
  }));

  const statsByTicker = Object.fromEntries(geo.assetStats.map((a) => [a.ticker, a]));
  const assetDots = result.tickers
    .map((t, k) => {
      const a = statsByTicker[t];
      if (!a) return null; // shouldn't happen — every requested ticker gets stats back
      return {
        t,
        color: CHART_PALETTE[k % CHART_PALETTE.length],
        pctX: ((geo.X(a.volatility) / 880) * 100).toFixed(2),
        pctY: ((geo.Y(a.expected_return) / 470) * 100).toFixed(2),
      };
    })
    .filter(Boolean);

  return `
    <section id="frontier">
      <h6 style="color:var(--color-accent-300)">01 · Risk–return</h6>
      <h3 style="margin-bottom:var(--space-2)">Efficient frontier</h3>
      <p class="text-muted mw-section-lede">Every point is a portfolio the optimizer can build from your
        ${result.tickers.length} assets. Click or drag along the curve to move the selection — the whole
        report above follows it.</p>

      <div class="mw-frontier-row">
        <div class="card elev-sm mw-frontier-chart-card">
          <div class="mw-frontier-plot">
            <svg id="mw-frontier-svg" class="mw-frontier-svg" viewBox="0 0 880 470">
              <path d="${gridPath}" fill="none" stroke="var(--color-neutral-900)" stroke-width="1"></path>
              <path d="${xTickPath}" fill="none" stroke="var(--color-neutral-600)" stroke-width="1"></path>
              <line x1="${FR_X0}" y1="${FR_Y0}" x2="862" y2="${FR_Y0}" stroke="var(--color-neutral-500)" stroke-width="1"></line>
              <line x1="${cal.x1}" y1="${cal.y1}" x2="${cal.x2}" y2="${cal.y2}" stroke="var(--color-accent-300)" stroke-width="1.4" stroke-dasharray="6 5"></line>
              <polyline points="${line}" fill="none" stroke="var(--color-accent-400)" stroke-width="2.6" stroke-linejoin="round"></polyline>
              <path d="${dotsPath}" fill="var(--color-accent-300)" opacity="0.55"></path>
              <circle cx="${mvp.cx}" cy="${mvp.cy}" r="4.5" fill="var(--color-bg)" stroke="var(--color-neutral-400)" stroke-width="1.8"></circle>
              <circle cx="${tan.cx}" cy="${tan.cy}" r="6" fill="var(--color-bg)" stroke="var(--color-accent-200)" stroke-width="2.2"></circle>
              <line id="mw-fr-cross-h" x1="${FR_X0}" y1="0" x2="0" y2="0" stroke="var(--color-accent)" stroke-width="1" stroke-dasharray="3 4" opacity="0.55"></line>
              <line id="mw-fr-cross-v" x1="0" y1="0" x2="0" y2="${FR_Y0}" stroke="var(--color-accent)" stroke-width="1" stroke-dasharray="3 4" opacity="0.55"></line>
              <circle id="mw-fr-sel-halo" cx="0" cy="0" r="12" fill="var(--color-accent)" opacity="0.18"></circle>
              <circle id="mw-fr-sel-dot" cx="0" cy="0" r="6" fill="var(--color-accent)" stroke="var(--color-bg)" stroke-width="2"></circle>
            </svg>
            <div class="mw-frontier-overlay">
              ${yTicks.map((t) => `<span style="left:0;width:5.9%;text-align:right;top:${t.pctY}%;transform:translateY(-50%)">${t.label}</span>`).join("")}
              ${xTicks.map((t) => `<span style="left:${t.pctX}%;top:88.5%;transform:translateX(-50%)">${t.label}</span>`).join("")}
              ${assetDots.map((a) => `
                <span style="left:${a.pctX}%;top:${a.pctY}%;transform:translate(9px,-50%);font-size:12.5px;color:var(--color-neutral-300)">${escapeHtml(a.t)}</span>
                <span style="left:${a.pctX}%;top:${a.pctY}%;transform:translate(-50%,-50%);width:9px;height:9px;border-radius:50%;border:2px solid ${a.color};background:var(--color-bg)"></span>`).join("")}
              <span style="left:52.5%;top:95.5%;transform:translateX(-50%);font-size:13px;color:var(--color-neutral-300)">Volatility σ →</span>
              <span style="left:7.4%;top:4.5%;font-size:13px;color:var(--color-neutral-300)">↑ Expected return · ${unitWord}</span>
              <span style="left:${cal.pctX}%;top:${cal.pctY}%;transform:translate(-100%,14px);font-size:12.5px;color:var(--color-accent-300)">Capital allocation line</span>
            </div>
          </div>
          <div class="mw-frontier-legend">
            <span class="text-muted mw-legend-item"><span style="width:16px;height:2px;background:var(--color-accent-400);display:block"></span>Frontier</span>
            <span class="text-muted mw-legend-item"><span style="width:10px;height:10px;border-radius:50%;border:2px solid var(--color-accent-200);display:block"></span>Tangency</span>
            <span class="text-muted mw-legend-item"><span style="width:9px;height:9px;border-radius:50%;border:1.6px solid var(--color-neutral-400);display:block"></span>Minimum variance</span>
            <span class="text-muted mw-legend-item"><span style="width:9px;height:9px;border-radius:50%;border:1.8px solid var(--color-neutral-500);display:block"></span>Single asset</span>
          </div>
        </div>

        <div class="card elev-sm mw-frontier-stats">
          <div>
            <span class="card-kicker">Selected portfolio</span>
            <div class="mw-frontier-stats__title" id="mw-fr-title"></div>
          </div>
          <div class="mw-frontier-stats__rows">
            <div class="mw-frontier-stats__row"><span class="text-muted" style="font-size:12px">Expected return</span><span class="mw-frontier-stats__row-value" id="mw-fr-row-return"></span></div>
            <div class="mw-frontier-stats__row"><span class="text-muted" style="font-size:12px">Volatility</span><span class="mw-frontier-stats__row-value" id="mw-fr-row-risk"></span></div>
            <div class="mw-frontier-stats__row"><span class="text-muted" style="font-size:12px">Sharpe ratio</span><span class="mw-frontier-stats__row-value" style="color:var(--color-accent-300)" id="mw-fr-row-sharpe"></span></div>
            <div class="mw-frontier-stats__row"><span class="text-muted" style="font-size:12px">Largest position</span><span class="mw-frontier-stats__row-value" id="mw-fr-row-largest"></span></div>
          </div>
          <p class="card-body" id="mw-fr-tip"></p>
          <div style="display:flex;gap:var(--space-2)">
            <button type="button" class="btn btn-secondary" data-action="frontier-mvp" style="flex:1">Min variance</button>
            <button type="button" class="btn btn-primary" data-action="frontier-tan" style="flex:1">Max Sharpe</button>
          </div>
        </div>
      </div>
    </section>`;
}

function attachFrontierEvents() {
  const svg = document.getElementById("mw-frontier-svg");
  if (!svg) return;
  svg.addEventListener("pointerdown", (e) => {
    try {
      if (e.pointerId != null) svg.setPointerCapture(e.pointerId);
    } catch {
      // Synthetic events (and some test harnesses) may lack a real pointerId.
    }
    svg._mwDragging = true;
    pickFrontierPoint(e, svg);
  });
  svg.addEventListener("pointermove", (e) => {
    if (svg._mwDragging) pickFrontierPoint(e, svg);
  });
  svg.addEventListener("pointerup", () => {
    svg._mwDragging = false;
  });
  svg.addEventListener("pointercancel", () => {
    svg._mwDragging = false;
  });
}

/** Updates only the selection-dependent bits (crosshair, marker, stats
 * panel) without touching the SVG element itself — rebuilding it mid-drag
 * would drop the pointer capture attachFrontierEvents just set up. */
function updateFrontierSelection() {
  if (!state.result || !frontierGeo) return;
  const { iF, best, label, isBest } = resolveSelection(state.result);
  const p = frontierGeo.pts[iF];
  const g = frontierGeo.geo[iF];

  const crossH = document.getElementById("mw-fr-cross-h");
  const crossV = document.getElementById("mw-fr-cross-v");
  const halo = document.getElementById("mw-fr-sel-halo");
  const dot = document.getElementById("mw-fr-sel-dot");
  if (crossH) {
    crossH.setAttribute("x2", g.cx);
    crossH.setAttribute("y1", g.cy);
    crossH.setAttribute("y2", g.cy);
  }
  if (crossV) {
    crossV.setAttribute("x1", g.cx);
    crossV.setAttribute("x2", g.cx);
    crossV.setAttribute("y1", g.cy);
  }
  if (halo) {
    halo.setAttribute("cx", g.cx);
    halo.setAttribute("cy", g.cy);
  }
  if (dot) {
    dot.setAttribute("cx", g.cx);
    dot.setAttribute("cy", g.cy);
  }

  setText("mw-fr-title", label);
  setText("mw-fr-row-return", pct(toReturn(p.expected_return)));
  setText("mw-fr-row-risk", pct(toVol(p.risk)));
  setText("mw-fr-row-sharpe", toSharpe(p.sharpe).toFixed(3));

  const [largestTicker, largestWeight] = Object.entries(p.weights).reduce(
    (a, [t, w]) => (w > a[1] ? [t, w] : a),
    ["—", -Infinity],
  );
  setText("mw-fr-row-largest", `${largestTicker} · ${(largestWeight * 100).toFixed(0)}%`);

  setText(
    "mw-fr-tip",
    isBest
      ? "This is where the capital allocation line touches the frontier: no other long-only mix of these assets pays more return per unit of risk."
      : iF < best
        ? "Safer than the tangency portfolio, but every unit of risk here buys less return. Blending the tangency mix with cash dominates this point."
        : "Past tangency the curve flattens: additional return costs more volatility than it returns. Low-volatility assets have dropped out.",
  );
}

function renderFrontier() {
  const slot = document.getElementById("mw-frontier-slot");
  // A failed re-run leaves the previous `state.result` in place (see
  // runAnalysis) so a transient failure doesn't blow away a working report;
  // but showing a stale chart under the error card would be confusing, so
  // the error card (in the KPI slot) takes over the whole report area.
  if (!state.result || state.error) {
    slot.innerHTML = "";
    frontierGeo = null;
    frontierBaseResult = null;
    frontierBaseUnits = null;
    return;
  }
  // Units (monthly/annual) change the axis titles and tick labels, which are
  // baked into the static HTML below — not just the selection-dependent
  // bits updateFrontierSelection touches — so a units change needs a base
  // rebuild too. That's safe here (unlike mid-drag) because toggling units
  // is a discrete click, never a pointermove while the SVG holds capture.
  if (state.result !== frontierBaseResult || state.units !== frontierBaseUnits) {
    frontierGeo = computeFrontierGeometry(state.result);
    slot.innerHTML = frontierSectionHtml(state.result);
    attachFrontierEvents();
    frontierBaseResult = state.result;
    frontierBaseUnits = state.units;
  }
  updateFrontierSelection();
}

/* ── Optimal allocation ──────────────────────────────────────────────── */

const DONUT_CIRCUMFERENCE = 2 * Math.PI * 52;

function nameFor(ticker) {
  return UNIVERSE.find((u) => u.t === ticker)?.n || ticker;
}

// Only the row identity (tickers/names/colors, from `result.tickers`) is
// "base" — it never changes for a given result, regardless of frontier
// selection, cash or units. Everything else (weights, bar widths, the donut,
// the blended figures) is recomputed on every render into allocationUpdate().
let allocationBaseResult = null;

function allocationRowsHtml(result) {
  const p = selectedPortfolio();
  const cashP = state.cash / 100;

  const rows = result.tickers.map((t, k) => {
    const w = p.weights[t] ?? 0;
    return {
      ticker: t,
      name: nameFor(t),
      color: CHART_PALETTE[k % CHART_PALETTE.length],
      w,
      capPct: w * (1 - cashP) * 100,
    };
  });

  const cols = "104px minmax(0,1fr) 104px minmax(90px,22%) 104px";
  const assetRows = rows.map((r) => `
    <div class="mw-grid-row mw-grid-row--body" style="grid-template-columns:${cols}">
      <span class="mw-swatch"><span class="mw-swatch__dot" style="background:${r.color}"></span>${escapeHtml(r.ticker)}</span>
      <span class="text-muted" style="font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(r.name)}</span>
      <span class="mw-num" style="text-align:right">${pct(r.w, 1)}</span>
      <span class="mw-bar-track"><span class="mw-bar-fill" style="width:${r.capPct.toFixed(2)}%;background:${r.color}"></span></span>
      <span class="mw-num" style="text-align:right">${pct(r.capPct / 100, 1)}</span>
    </div>`).join("");

  const cashRow = `
    <div class="mw-grid-row mw-grid-row--body" style="grid-template-columns:${cols}">
      <span class="mw-swatch" style="color:var(--color-neutral-400)"><span class="mw-swatch__dot" style="background:var(--color-neutral-700)"></span>CASH</span>
      <span class="text-muted" style="font-size:13px">Risk-free</span>
      <span class="text-muted mw-num" style="text-align:right">—</span>
      <span class="mw-bar-track"><span class="mw-bar-fill" style="width:${state.cash}%;background:var(--color-neutral-700)"></span></span>
      <span class="mw-num" style="text-align:right">${state.cash}%</span>
    </div>`;

  return assetRows + cashRow;
}

function allocationArcsHtml(result) {
  const p = selectedPortfolio();
  const cashP = state.cash / 100;
  let acc = 0;
  return result.tickers
    .map((t, k) => ({ w: p.weights[t] ?? 0, color: CHART_PALETTE[k % CHART_PALETTE.length] }))
    .filter((r) => r.w > 0.0005)
    .map((r) => {
      const len = r.w * (1 - cashP) * DONUT_CIRCUMFERENCE;
      const dash = `${len.toFixed(1)} ${(DONUT_CIRCUMFERENCE - len).toFixed(1)}`;
      const offset = (-acc).toFixed(1);
      acc += len;
      return `<circle cx="64" cy="64" r="52" fill="none" stroke="${r.color}" stroke-width="13" stroke-dasharray="${dash}" stroke-dashoffset="${offset}" transform="rotate(-90 64 64)"></circle>`;
    })
    .join("");
}

function allocationBaseHtml(result) {
  return `
    <section id="allocation">
      <h6 style="color:var(--color-accent-300)">02 · Holdings</h6>
      <h3 style="margin-bottom:var(--space-2)">Optimal allocation</h3>
      <p class="text-muted mw-section-lede">Weights for the selected portfolio. Blending with cash walks down the
        capital allocation line: return and risk both scale, the Sharpe ratio does not move.</p>

      <div class="mw-alloc-row">
        <div class="card elev-sm mw-alloc-donut-card">
          <div class="mw-alloc-donut">
            <svg viewBox="0 0 128 128">
              <circle cx="64" cy="64" r="52" fill="none" stroke="var(--color-neutral-800)" stroke-width="13"></circle>
              <g id="mw-alloc-arcs"></g>
            </svg>
            <div class="mw-alloc-donut__overlay" id="mw-alloc-overlay"></div>
          </div>
          <div class="text-muted mw-alloc-donut__note" id="mw-alloc-note"></div>
        </div>

        <div class="mw-alloc-main">
          <div class="card elev-sm mw-cash-card">
            <div class="mw-cash-card__head">
              <span class="card-kicker">Blend with cash</span>
              <span class="mw-cash-card__pct" id="mw-cash-pct"></span>
            </div>
            <input id="mw-cash" type="range" min="0" max="90" step="5" value="${state.cash}" />
            <div class="text-muted" style="font-size:12px" id="mw-cal-note"></div>
          </div>

          <div class="card elev-sm mw-table">
            <div class="mw-table__inner" style="min-width:520px">
              <div class="mw-grid-row mw-grid-row--head" style="grid-template-columns:104px minmax(0,1fr) 104px minmax(90px,22%) 104px">
                <span>Asset</span><span>Name</span><span style="text-align:right">In risky mix</span><span>Share of capital</span><span style="text-align:right">Of capital</span>
              </div>
              <div id="mw-alloc-rows"></div>
            </div>
          </div>
        </div>
      </div>
    </section>`;
}

function attachAllocationEvents() {
  const cash = document.getElementById("mw-cash");
  if (!cash) return;
  cash.addEventListener("input", () => {
    state.cash = +cash.value;
    render();
  });
}

/** Refreshes everything that depends on the selected portfolio, cash or
 * units — the donut arcs, its center overlay, the cash caption, and the
 * weights rows. Deliberately does not touch `#mw-cash` itself: this runs on
 * every `input` event the slider fires, and replacing the slider element
 * mid-drag would interrupt the browser's own drag gesture on it (the same
 * class of bug the frontier chart's pointer capture has to avoid). */
function updateAllocation() {
  const p = selectedPortfolio();
  const unitWord = isAnnual() ? "annualized" : "monthly";
  const blend = cashBlend(p);

  document.getElementById("mw-alloc-arcs").innerHTML = allocationArcsHtml(state.result);
  document.getElementById("mw-alloc-overlay").innerHTML = `
    <span class="mw-alloc-donut__value">${escapeHtml(pct(toReturn(blend.expectedReturn)))}</span>
    <span class="text-muted" style="font-size:10.5px">expected · ${escapeHtml(unitWord)}</span>`;
  setText("mw-alloc-note", state.cash > 0 ? `Risky mix at ${100 - state.cash}% of capital` : "Fully invested");
  setText("mw-cash-pct", `${state.cash}%`);
  setText(
    "mw-cal-note",
    `At ${state.cash}% cash: ${pct(toReturn(blend.expectedReturn))} expected return, ` +
      `${pct(toVol(blend.risk))} volatility, Sharpe ${toSharpe(p.sharpe).toFixed(2)}.`,
  );
  document.getElementById("mw-alloc-rows").innerHTML = allocationRowsHtml(state.result);
}

function renderAllocation() {
  const slot = document.getElementById("mw-allocation-slot");
  if (!state.result || state.error) {
    slot.innerHTML = "";
    allocationBaseResult = null;
    return;
  }
  if (state.result !== allocationBaseResult) {
    slot.innerHTML = allocationBaseHtml(state.result);
    attachAllocationEvents();
    allocationBaseResult = state.result;
  }
  updateAllocation();
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
  renderFrontier();
  renderAllocation();
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

  // Delegated: the rail's Run button, the error card's Retry button, and the
  // frontier stats panel's jump buttons are all rebuilt on every re-render,
  // so none of them can have a listener attached directly.
  document.body.addEventListener("click", (e) => {
    if (e.target.closest('[data-action="run"]')) runAnalysis();
    if (e.target.closest('[data-action="frontier-mvp"]')) {
      state.iF = 0;
      render();
    }
    if (e.target.closest('[data-action="frontier-tan"]')) {
      state.iF = null;
      render();
    }
  });

  render();
  runAnalysis();
}

document.addEventListener("DOMContentLoaded", init);
