"""API router for MarkoWizard analysis endpoints."""

import logging

import numpy as np
from fastapi import APIRouter, HTTPException

from markowizard import CapitalAllocator, MarkowitzOptimizer
from markowizard.core import COL_RETURN, COL_RISK, COL_SHARPE
from markowizard.data import compute_monthly_returns, fetch_prices

from .schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AssetStatistics,
    CapitalAllocationPoint,
    MaxSharpePortfolio,
    PortfolioMetrics,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Run full Markowitz analysis on the given tickers.

    Fetches price data, computes monthly returns, optimizes the portfolio,
    computes the efficient frontier, finds the max Sharpe portfolio, and
    returns raw data for chart rendering on the frontend.
    """
    tickers = request.tickers
    period = request.period
    risk_free_rate = request.risk_free_rate

    try:
        # 1. Fetch price data
        prices = fetch_prices(tickers, period=period)

        # Check for missing tickers
        found = set(prices.columns)
        missing = set(tickers) - found
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Tickers not found: {', '.join(sorted(missing))}",
            )

        # 2. Compute monthly returns
        returns = compute_monthly_returns(prices)

        if returns.empty or returns.shape[1] < 1:
            raise HTTPException(
                status_code=400,
                detail="Not enough data to compute returns. Try a longer period.",
            )

        # 3. Compute correlation matrix
        corr_matrix = returns.corr()
        correlation_matrix: list[list[float]] = corr_matrix.values.tolist()

        # 3b. Standalone per-asset statistics (independent of any portfolio weighting)
        asset_statistics = [
            AssetStatistics(
                ticker=ticker,
                expected_return=float(returns[ticker].mean()),
                volatility=float(returns[ticker].std()),
            )
            for ticker in returns.columns
        ]

        # 4. Optimize
        optimizer = MarkowitzOptimizer(returns)
        portfolios = optimizer.optimize()
        optimizer.compute_sharpe(risk_free_rate)

        # 5. Max Sharpe portfolio
        max_sharpe_series = optimizer.max_sharpe_portfolio()
        max_sharpe_weights = {
            k: float(v)
            for k, v in max_sharpe_series.items()
            if k not in {COL_RETURN, COL_RISK, COL_SHARPE}
        }
        max_sharpe_portfolio = MaxSharpePortfolio(
            risk=float(max_sharpe_series[COL_RISK]),
            expected_return=float(max_sharpe_series[COL_RETURN]),
            sharpe=float(max_sharpe_series[COL_SHARPE]),
            weights=max_sharpe_weights,
        )

        # 6. Capital Allocation Line
        allocator = CapitalAllocator(max_sharpe_series, risk_free_rate)
        cal_points_raw = allocator.capital_allocation_line(steps=21)
        cal_points = [
            CapitalAllocationPoint(
                p=p["p"],
                expected_return=p["expected_return"],
                risk=p["risk"],
                label=p["label"],
            )
            for p in cal_points_raw
        ]

        # 7. Build efficient frontier list. MarkowitzOptimizer.optimize() sorts by
        # risk ascending, so frontier[0] below is the minimum-variance portfolio.
        frontier: list[PortfolioMetrics] = []
        for _, row in portfolios.iterrows():
            weights = {
                k: float(v) for k, v in row.items() if k not in {COL_RETURN, COL_RISK, COL_SHARPE}
            }
            frontier.append(
                PortfolioMetrics(
                    risk=float(row[COL_RISK]),
                    expected_return=float(row[COL_RETURN]),
                    sharpe=float(row.get(COL_SHARPE, np.nan)) if COL_SHARPE in row else None,
                    weights=weights,
                )
            )

        return AnalyzeResponse(
            tickers=tickers,
            efficient_frontier=frontier,
            max_sharpe_portfolio=max_sharpe_portfolio,
            min_variance_portfolio=frontier[0],
            capital_allocation_line=cal_points,
            correlation_matrix=correlation_matrix,
            asset_statistics=asset_statistics,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Analysis failed")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}",
        ) from exc
