/* MarkoWizard — Frontend Application Logic */

(function () {
    "use strict";

    const form = document.getElementById("analyze-form");
    const loading = document.getElementById("loading");
    const results = document.getElementById("results");
    const errorDiv = document.getElementById("error-message");
    const metricsDiv = document.getElementById("metrics");
    const btn = document.getElementById("analyze-btn");

    const chartIds = {
        efficient_frontier: "chart-frontier",
        allocation_pie: "chart-pie",
        capital_allocation_line: "chart-cal",
        correlation_heatmap: "chart-corr",
    };

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

    /** Render Plotly charts from JSON figure data. */
    function renderCharts(charts) {
        for (const [key, chartJson] of Object.entries(charts)) {
            const containerId = chartIds[key];
            if (!containerId) continue;

            const el = document.getElementById(containerId);
            if (!el) continue;

            try {
                const figure = JSON.parse(chartJson);
                Plotly.react(el, figure.data, figure.layout, { responsive: true });
            } catch (err) {
                console.error("Failed to render chart:", key, err);
            }
        }
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
            renderCharts(data.charts);

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