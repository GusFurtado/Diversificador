# MarkoWizard

A modern Python library for Markowitz portfolio optimization and analysis.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **Previously known as _Diversificador_.** The original portfolio-analysis web app
> built with [Dash](https://dash.plotly.com/) is no longer maintained, but it is
> preserved on the [`dash-deprecated`](../../tree/dash-deprecated) branch for reference.

## Features

- **Markowitz Mean-Variance Optimization** — Compute the efficient frontier using `scipy.optimize`
- **Capital Allocation Line** — Mix risky portfolios with risk-free assets
- **Visualization** — Plotly-based charts for efficient frontier, allocation pie, CAL, correlation heatmaps, and price timelines
- **Data Fetching** — Optional convenience functions for downloading market data via yfinance
- **Web Application** — FastAPI backend with a dark-themed interactive frontend

## Installation

```bash
pip install markowizard
```

That's everything the library needs: optimization (`scipy`), market-data
fetching (`yfinance`), and visualization (`plotly`). No optional extras.

## Quick Start (Library)

```python
from markowizard import MarkowitzOptimizer, CapitalAllocator
from markowizard.data import fetch_prices, compute_monthly_returns
from markowizard.visualization import efficiency_frontier_plot

# Fetch prices and compute monthly returns (decimal form, e.g. 0.01 = 1%)...
prices = fetch_prices(["AAPL", "MSFT", "GOOGL", "SPY"], period="5y")
returns = compute_monthly_returns(prices)
# ...or bring your own returns DataFrame (assets as columns).

# Optimize
optimizer = MarkowitzOptimizer(returns)
portfolios = optimizer.optimize()

# Compute Sharpe ratios (provide monthly risk-free rate)
risk_free_rate = 0.005  # 0.5% per month
portfolios = optimizer.compute_sharpe(risk_free_rate)

# Plot the efficient frontier
fig = efficiency_frontier_plot(portfolios, highlight_portfolio=50)
fig.show()

# Best portfolio (maximum Sharpe ratio)
best = optimizer.max_sharpe_portfolio()
print(best)

# Capital allocation line
allocator = CapitalAllocator(best, risk_free_rate)
cal_points = allocator.capital_allocation_line(steps=21)
```

## Web Application

An interactive web UI (FastAPI + a dark-themed frontend) lives in `backend/` and
`frontend/`. It is **not part of the PyPI package** — run it from the container
image or a clone.

### Using Docker

```bash
docker run -p 8000:8000 ghcr.io/outliersanalytics/markowizard:latest
```

### From a clone

```bash
git clone https://github.com/OutliersAnalytics/MarkoWizard
cd MarkoWizard
uv run --with-requirements backend/requirements.txt uvicorn backend.main:app --port 8000
```

Open [http://localhost:8000](http://localhost:8000) — the app auto-submits with
default tickers on load.

It exposes a single endpoint, `POST /api/analyze`:

```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL", "SPY"],
  "period": "5y",
  "risk_free_rate": 0.005
}
```

which returns the efficient frontier, max-Sharpe portfolio, capital-allocation-line
points, and correlation matrix as JSON. The frontend renders the charts.

## API Reference

### `markowizard` (top-level)

| Export | Description |
|---|---|
| `MarkowitzOptimizer` | Efficient frontier optimization (from `core`) |
| `CapitalAllocator` | Risk-free asset allocation (from `allocation`) |
| `__version__` | Package version string |

### `markowizard.core`

#### `MarkowitzOptimizer`

```python
class MarkowitzOptimizer:
    def __init__(self, returns: pd.DataFrame) -> None
    def optimize(self) -> pd.DataFrame
    def compute_sharpe(self, risk_free_rate: float) -> pd.DataFrame
    def max_sharpe_portfolio(self) -> pd.Series
```

**Constants**: `COL_RETURN = "Expected Return"`, `COL_RISK = "Risk"`, `COL_SHARPE = "Sharpe"`, `COL_RISK_FREE = "Risk-Free"`

**Parameters**:
- `returns`: DataFrame where each column is an asset and each row is a time period. Values must be in decimal form (e.g., 0.01 = 1%).

**`optimize()`** computes the efficient frontier by solving 100 quadratic programming problems with varying risk-aversion parameters. Uses warm-starting: each iteration's solution seeds the next.

**`compute_sharpe(risk_free_rate)`** adds a `Sharpe` column. `risk_free_rate` must match the period of `returns` (e.g., monthly).

**`max_sharpe_portfolio()`** returns the tangency portfolio row.

#### `MarkowitzOptimizer.portfolios` DataFrame columns

| Column | Description |
|---|---|
| (ticker columns) | Asset weights (sum to 1, all >= 0) |
| `Expected Return` | Expected portfolio return |
| `Risk` | Portfolio standard deviation (risk) |
| `Sharpe` | Sharpe ratio (after `compute_sharpe()`) |

### `markowizard.allocation`

#### `CapitalAllocator`

```python
class CapitalAllocator:
    def __init__(self, portfolio: pd.Series | Mapping, risk_free_rate: float) -> None
    @staticmethod
    def weigh_risk_free(value: float, risk_free_value: float, p: float) -> float
    def capital_allocation_line(self, steps: int = 21) -> list[dict]
    def final_allocation(self, p: float) -> dict[str, float]
    def expected_returns(self, p: float) -> tuple[float, float]
```

**`capital_allocation_line()`** returns points along the CAL, each with keys `p`, `expected_return`, `risk`, and `label`.

**`final_allocation(p)`** returns asset weights including `Risk-Free` (risk-free portion).

### `markowizard.visualization`

| Function | Returns | Description |
|---|---|---|
| `efficiency_frontier_plot(portfolios, highlight_portfolio=0)` | `Figure` | Scatter plot of expected return vs risk |
| `allocation_pie(portfolio)` | `Figure` | Pie chart of asset weights |
| `capital_allocation_line_plot(cal_points, highlight_point=0)` | `Figure` | CAL risk-return trade-off |
| `correlation_timeline(prices, ticker_a, ticker_b=None)` | `Figure` | Price history (single or normalized dual) |
| `correlation_heatmap(corr_matrix)` | `Figure` | Correlation matrix heatmap |

All visualization functions return Plotly `Figure` objects — call `.show()` to display.

### `markowizard.data`

| Function | Returns | Description |
|---|---|---|
| `fetch_prices(tickers, period="5y", auto_adjust=True)` | `pd.DataFrame` | Historical close prices from Yahoo Finance |
| `compute_monthly_returns(prices)` | `pd.DataFrame` | Monthly returns from daily close prices |

## Modules

| Module | Description |
|---|---|
| `core` | `MarkowitzOptimizer` — efficient frontier optimization |
| `allocation` | `CapitalAllocator` — risk-free asset allocation |
| `visualization` | Plotly chart functions (efficient frontier, pie, CAL, correlation) |
| `data` | Market-data fetching and monthly-return helpers (yfinance) |

The web application (`backend/`, `frontend/`) is kept in the repo but is not
part of the installable package — see [Web Application](#web-application).

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and contribution guidelines.

## License

MIT