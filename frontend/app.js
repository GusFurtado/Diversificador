/* MarkoWizard — Frontend Application Logic */

(function () {
    "use strict";

    const form = document.getElementById("analyze-form");
    const loading = document.getElementById("loading");
    const results = document.getElementById("results");
    const errorDiv = document.getElementById("error-message");
    const metricsDiv = document.getElementById("metrics");
    const btn = document.getElementById("analyze-btn");

    // Keep references to active Chart.js instances for proper cleanup
    const chartInstances = {};

    /** Format a decimal as a percentage string. */
    function fmtPct(value) {
        return (value * 100).toFixed(2) + "%";
    }

    /** Format a number to 4 decimal places. */
    function fmtNum(value) {
        return Number(value).toFixed(4);
    }

    /** Show an error message above the results. */
    function showError(msg) {
        errorDiv.textContent = msg;
        errorDiv.classList.remove("hidden");
    }

    /** Hide the error message. */
    function hideError() {
        errorDiv.classList.add("hidden");
    }

    /** Enable/disable the submit button and toggle loading spinner. */
    function setLoading(isLoading) {
        btn.disabled = isLoading;
        loading.classList.toggle("hidden", !isLoading);
        results.classList.toggle("hidden", isLoading);
    }

    /** Destroy all existing Chart.js instances to free memory. */
    function destroyCharts() {
        for (const key in chartInstances) {
            if (chartInstances[key]) {
                chartInstances[key].destroy();
                delete chartInstances[key];
            }
        }
    }

    // Theme colors pulled from style.css :root
    const THEME = {
        bg: "#0f172a",
        surface: "#1e293b",
        surface2: "#334155",
        text: "#e2e8f0",
        muted: "#94a3b8",
        accent: "#38bdf8",
        accentHover: "#7dd3fc",
        success: "#4ade80",
        error: "#f87171",
        border: "#475569",
    };

    /** Build metric cards from the response data. */
    function renderMetrics(data) {
        const ms = data.max_sharpe_portfolio;
        const cards = [
            { label: "Expected Return (max Sharpe)", value: fmtPct(ms.expected_return), cls: "positive" },
            { label: "Risk (max Sharpe)", value: fmtPct(ms.risk), cls: "negative" },
            { label: "Sharpe Ratio", value: fmtNum(ms.sharpe), cls: "" },
            { label: "Portfolios on Frontier", value: data.efficient_frontier.length, cls: "" },
        ];

        metricsDiv.innerHTML = cards
            .map(
                (c) => `
                    <div class="metric-card">
                        <div class="metric-label">${c.label}</div>
                        <div class="metric-value ${c.cls}">${c.value}</div>
                    </div>
                `
            )
            .join("");
    }

    // ───── Chart Rendering Functions ─────

    /**
     * Render the Efficient Frontier as a scatter chart.
     *
     * Data format: [{ risk, expected_return, sharpe, weights }]
     * We use risk (x) vs expected_return (y), and color by sharpe.
     */
    function renderFrontier(data) {
        const canvas = document.getElementById("chart-frontier");
        if (!canvas) return;

        const scores = data.efficient_frontier;
        const points = scores.map((p) => ({ x: p.risk, y: p.expected_return }));

        // Find max sharpe index
        let maxSharpeIdx = 0;
        let maxSharpe = -Infinity;
        scores.forEach((p, i) => {
            if (p.sharpe !== null && p.sharpe > maxSharpe) {
                maxSharpe = p.sharpe;
                maxSharpeIdx = i;
            }
        });

        chartInstances.frontier = new Chart(canvas, {
            type: "scatter",
            data: {
                datasets: [
                    {
                        label: "Efficient Frontier",
                        data: points,
                        backgroundColor: scores.map((p) => {
                            const sharpe =
                                p.sharpe !== null && p.sharpe !== undefined ? p.sharpe : 0;
                            // Scale sharpe value to a [0, 1] range for color interpolation
                            const minS = Math.min(...scores.map((sp) => sp.sharpe ?? 0));
                            const maxS = Math.max(...scores.map((sp) => sp.sharpe ?? 0));
                            const t = maxS > minS ? (sharpe - minS) / (maxS - minS) : 0.5;
                            // Interpolate between blue-ish (low) and green/yellow (high)
                            const r = Math.round(56 + (74 - 56) * t);
                            const g = Math.round(189 + (222 - 189) * t);
                            const b = Math.round(248 + (128 - 248) * t);
                            return `rgba(${r}, ${g}, ${b}, 0.8)`;
                        }),
                        borderColor: "rgba(56, 189, 248, 0.3)",
                        borderWidth: 0,
                        pointRadius: scores.map((_, i) => (i === maxSharpeIdx ? 8 : 4)),
                        pointHoverRadius: scores.map((_, i) => (i === maxSharpeIdx ? 10 : 6)),
                        pointBorderColor: scores.map((_, i) =>
                            i === maxSharpeIdx ? THEME.success : "transparent"
                        ),
                        pointBorderWidth: scores.map((_, i) => (i === maxSharpeIdx ? 2 : 0)),
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                const idx = ctx.dataIndex;
                                const p = scores[idx];
                                const lines = [
                                    `Risk: ${fmtPct(p.risk)}`,
                                    `Return: ${fmtPct(p.expected_return)}`,
                                ];
                                if (p.sharpe !== null && p.sharpe !== undefined) {
                                    lines.push(`Sharpe: ${fmtNum(p.sharpe)}`);
                                }
                                if (idx === maxSharpeIdx) {
                                    lines.push("★ Max Sharpe Ratio");
                                }
                                return lines;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        title: { display: true, text: "Risk (Std. Deviation)", color: THEME.muted },
                        ticks: {
                            color: THEME.muted,
                            callback: (val) => fmtPct(val),
                        },
                        grid: { color: "rgba(71, 85, 105, 0.3)" },
                    },
                    y: {
                        title: { display: true, text: "Expected Return (% p.m.)", color: THEME.muted },
                        ticks: {
                            color: THEME.muted,
                            callback: (val) => fmtPct(val),
                        },
                        grid: { color: "rgba(71, 85, 105, 0.3)" },
                    },
                },
            },
        });
    }

    /**
     * Render the Optimal Allocation as a doughnut (pie) chart.
     */
    function renderAllocation(data) {
        const canvas = document.getElementById("chart-pie");
        if (!canvas) return;

        const ms = data.max_sharpe_portfolio;
        const weights = ms.weights || {};

        // Filter out near-zero weights
        const entries = Object.entries(weights).filter(([, v]) => v > 0.001);
        if (entries.length === 0) {
            entries.push(["(no allocation)", 1]);
        }

        const labels = entries.map(([k]) => k);
        const values = entries.map(([, v]) => v);

        // Generate distinct colors for the segments
        const palette = [
            "#38bdf8", "#4ade80", "#f87171", "#fbbf24", "#a78bfa",
            "#34d399", "#f472b6", "#22d3ee", "#fb923c", "#e879f9",
        ];

        chartInstances.allocation = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [
                    {
                        data: values,
                        backgroundColor: labels.map((_, i) => palette[i % palette.length]),
                        borderColor: THEME.surface,
                        borderWidth: 2,
                        hoverOffset: 8,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "40%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            color: THEME.text,
                            padding: 12,
                            font: { size: 11 },
                            usePointStyle: true,
                            pointStyle: "circle",
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                const label = ctx.label || "";
                                const val = ctx.parsed || 0;
                                return `${label}: ${fmtPct(val / 100)}`;
                            },
                        },
                    },
                },
            },
        });
    }

    /**
     * Render the Capital Allocation Line as a line chart.
     */
    function renderCAL(data) {
        const canvas = document.getElementById("chart-cal");
        if (!canvas) return;

        const calPoints = data.capital_allocation_line;
        if (!calPoints || calPoints.length === 0) return;

        // Find the highlight point (p ≈ 0.5, i.e. 50% risk-free)
        let highlightIdx = 0;
        if (calPoints.length > 1) {
            const midP = 0.5;
            let minDist = Infinity;
            calPoints.forEach((pt, i) => {
                const dist = Math.abs(pt.p - midP);
                if (dist < minDist) {
                    minDist = dist;
                    highlightIdx = i;
                }
            });
        }

        const proportions = calPoints.map((p) => p.p * 100); // as percentages
        const returns = calPoints.map((p) => p.expected_return);

        chartInstances.cal = new Chart(canvas, {
            type: "line",
            data: {
                labels: proportions.map((v) => v.toFixed(0) + "%"),
                datasets: [
                    {
                        label: "Capital Allocation Line",
                        data: returns,
                        borderColor: THEME.accent,
                        backgroundColor: "rgba(56, 189, 248, 0.08)",
                        fill: true,
                        tension: 0,
                        pointBackgroundColor: calPoints.map((_, i) =>
                            i === highlightIdx ? THEME.success : THEME.accent
                        ),
                        pointBorderColor: calPoints.map((_, i) =>
                            i === highlightIdx ? THEME.success : "transparent"
                        ),
                        pointBorderWidth: calPoints.map((_, i) => (i === highlightIdx ? 2 : 0)),
                        pointRadius: calPoints.map((_, i) => (i === highlightIdx ? 8 : 3)),
                        pointHoverRadius: calPoints.map((_, i) => (i === highlightIdx ? 10 : 5)),
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: function (items) {
                                if (!items.length) return "";
                                const idx = items[0].dataIndex;
                                const pt = calPoints[idx];
                                return `${fmtPct(pt.p)} Risk-Free`;
                            },
                            label: function (ctx) {
                                const idx = ctx.dataIndex;
                                const pt = calPoints[idx];
                                const lines = [
                                    `Return: ${fmtPct(pt.expected_return)}`,
                                    `Risk: ${fmtPct(pt.risk)}`,
                                ];
                                if (idx === highlightIdx) {
                                    lines.push("★ Balanced (50/50)");
                                }
                                return lines;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        title: { display: true, text: "Risk-Free Proportion", color: THEME.muted },
                        ticks: { color: THEME.muted },
                        grid: { color: "rgba(71, 85, 105, 0.3)" },
                        reverse: true,
                    },
                    y: {
                        title: { display: true, text: "Expected Return (% p.m.)", color: THEME.muted },
                        ticks: {
                            color: THEME.muted,
                            callback: (val) => fmtPct(val),
                        },
                        grid: { color: "rgba(71, 85, 105, 0.3)" },
                    },
                },
            },
        });
    }

    /**
     * Render the Correlation Heatmap as a styled HTML table.
     * Uses the same RdBu color scale as the other charts.
     */
    function renderHeatmap(data) {
        const canvas = document.getElementById("chart-corr");
        if (!canvas) return;

        const matrix = data.correlation_matrix;
        const tickers = data.tickers;
        if (!matrix || !tickers || matrix.length === 0) return;

        renderHeatmapFallback(canvas, matrix, tickers);
    }

    /**
     * Map a correlation value to an RdBu-like color string.
     */
    function correlationColor(v, maxAbs) {
        const t = (v + maxAbs) / (2 * maxAbs); // [0, 1] where 0.5 = 0 correlation
        // RdBu: red (1,0,0) -> white (1,1,1) @0 -> blue (0,0,1)
        let r, g, b;
        if (t < 0.5) {
            // Blue to white: (0,0,1) -> (1,1,1)
            const s = t / 0.5; // [0, 1]
            r = Math.round(0 + s * 255);
            g = Math.round(0 + s * 255);
            b = 255;
        } else {
            // White to red: (1,1,1) -> (1,0,0)
            const s = (t - 0.5) / 0.5; // [0, 1]
            r = 255;
            g = Math.round(255 - s * 255);
            b = Math.round(255 - s * 255);
        }
        return `rgb(${r}, ${g}, ${b})`;
    }

    /**
     * Fallback HTML table heatmap when chartjs-chart-matrix plugin is unavailable.
     */
    function renderHeatmapFallback(canvas, matrix, tickers) {
        const n = tickers.length;
        const container = canvas.parentElement;
        // Hide the canvas
        canvas.style.display = "none";

        // Create or reuse a fallback table
        let table = container.querySelector(".heatmap-fallback");
        if (!table) {
            table = document.createElement("div");
            table.className = "heatmap-fallback";
            container.appendChild(table);
        }

        const maxAbs = Math.max(
            ...matrix.flat().map((v) => Math.abs(v)),
            0.5
        );

        let html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
        // Header row
        html += '<tr><td style="padding:4px;"></td>';
        for (let j = 0; j < n; j++) {
            html += `<td style="padding:4px;text-align:center;color:${THEME.muted};">${tickers[j]}</td>`;
        }
        html += "</tr>";
        for (let i = 0; i < n; i++) {
            html += `<tr><td style="padding:4px;text-align:right;color:${THEME.muted};">${tickers[i]}</td>`;
            for (let j = 0; j < n; j++) {
                const v = matrix[i][j];
                const color = correlationColor(v, maxAbs);
                const textColor = Math.abs(v) > 0.6 ? "#fff" : THEME.text;
                html += `<td style="padding:4px;text-align:center;background:${color};color:${textColor};border-radius:4px;">${v.toFixed(2)}</td>`;
            }
            html += "</tr>";
        }
        html += "</table>";
        table.innerHTML = html;
    }

    /** Clean up any fallback heatmap tables. */
    function cleanupHeatmapFallback() {
        document.querySelectorAll(".heatmap-fallback").forEach((el) => el.remove());
        const corrCanvas = document.getElementById("chart-corr");
        if (corrCanvas) {
            corrCanvas.style.display = "";
        }
    }

    /** Render all charts from the response data. */
    function renderCharts(data) {
        destroyCharts();
        cleanupHeatmapFallback();
        renderFrontier(data);
        renderAllocation(data);
        renderCAL(data);
        renderHeatmap(data);
    }

    /** Submit the analysis request. */
    async function handleSubmit(event) {
        event.preventDefault();
        hideError();

        // Gather form data
        const tickersRaw = document.getElementById("tickers").value.trim();
        const tickers = tickersRaw
            .split(",")
            .map((t) => t.trim().toUpperCase())
            .filter((t) => t.length > 0);

        if (tickers.length === 0) {
            showError("Please enter at least one ticker symbol.");
            return;
        }

        const period = document.getElementById("period").value;
        const riskFreeRate = parseFloat(document.getElementById("risk-free-rate").value) || 0.005;

        setLoading(true);

        try {
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tickers: tickers,
                    period: period,
                    risk_free_rate: riskFreeRate,
                }),
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                const detail = errData.detail || `Server error (${response.status})`;
                throw new Error(detail);
            }

            const data = await response.json();

            renderMetrics(data);
            renderCharts(data);

            results.classList.remove("hidden");
            results.scrollIntoView({ behavior: "smooth", block: "start" });
        } catch (err) {
            showError(err.message || "An unexpected error occurred.");
            results.classList.remove("hidden");
        } finally {
            setLoading(false);
        }
    }

    // Warn if opened from file:// protocol (must use http://localhost:8000)
    if (window.location.protocol === "file:") {
        document.body.innerHTML = `
            <div style="font-family:sans-serif;max-width:600px;margin:50px auto;padding:30px;text-align:center;">
                <h1>Cannot open directly</h1>
                <p style="font-size:18px;color:#666;">
                    Please start the MarkoWizard server and open
                    <a href="http://localhost:8000" style="color:#00bcd4;">http://localhost:8000</a>
                    in your browser instead.
                </p>
            </div>
        `;
        return;
    }

    // Attach event listener
    form.addEventListener("submit", handleSubmit);

    // Auto-submit with default values on page load
    document.addEventListener("DOMContentLoaded", () => {
        handleSubmit(new Event("submit", { cancelable: true }));
    });
})();