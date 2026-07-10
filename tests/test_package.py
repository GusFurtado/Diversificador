"""Tests for markowizard package."""

import numpy as np
import pandas as pd
import pytest

from markowizard.allocation import CapitalAllocator
from markowizard.core import COL_RETURN, COL_RISK, COL_SHARPE, MarkowitzOptimizer
from markowizard.visualization import (
    allocation_pie,
    capital_allocation_line_plot,
    correlation_heatmap,
    correlation_timeline,
    efficiency_frontier_plot,
)


@pytest.fixture
def synthetic_returns() -> pd.DataFrame:
    """Generate synthetic monthly returns for 3 assets (60 periods)."""
    np.random.seed(42)
    n_periods = 60
    tickers = ["PETR4.SA", "ITUB4.SA", "IVVB11.SA"]
    returns = pd.DataFrame(
        np.random.randn(n_periods, 3) * 0.05 + [0.01, 0.008, 0.012],
        columns=tickers,
    )
    return returns


@pytest.fixture
def optimizer(synthetic_returns: pd.DataFrame) -> MarkowitzOptimizer:
    """Return a configured MarkowitzOptimizer."""
    return MarkowitzOptimizer(synthetic_returns)


@pytest.fixture
def portfolios(optimizer: MarkowitzOptimizer) -> pd.DataFrame:
    """Return optimized portfolios DataFrame."""
    return optimizer.optimize()


@pytest.fixture
def portfolio_slice(portfolios: pd.DataFrame) -> pd.Series:
    """Return a single portfolio (row 50) from the frontier."""
    return portfolios.iloc[50]


# --- MarkowitzOptimizer tests ---


class TestMarkowitzOptimizer:
    def test_init_rejects_empty_dataframe(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            MarkowitzOptimizer(pd.DataFrame())

    def test_optimize_shape(self, portfolios: pd.DataFrame) -> None:
        assert portfolios.shape == (100, 5)

    def test_optimize_columns(self, portfolios: pd.DataFrame) -> None:
        expected = ["PETR4.SA", "ITUB4.SA", "IVVB11.SA", COL_RETURN, COL_RISK]
        assert list(portfolios.columns) == expected

    def test_optimize_returns_have_variation(self, portfolios: pd.DataFrame) -> None:
        assert portfolios[COL_RETURN].min() < portfolios[COL_RETURN].max()

    def test_optimize_risk_have_variation(self, portfolios: pd.DataFrame) -> None:
        assert portfolios[COL_RISK].min() < portfolios[COL_RISK].max()

    def test_optimize_weights_sum_to_one(self, portfolios: pd.DataFrame) -> None:
        tickers = ["PETR4.SA", "ITUB4.SA", "IVVB11.SA"]
        weight_sums = portfolios[tickers].sum(axis=1)
        assert np.allclose(weight_sums, 1.0)

    def test_optimize_weights_non_negative(self, portfolios: pd.DataFrame) -> None:
        tickers = ["PETR4.SA", "ITUB4.SA", "IVVB11.SA"]
        assert (portfolios[tickers] >= -1e-10).all().all()

    def test_compute_sharpe_adds_column(self, optimizer: MarkowitzOptimizer) -> None:
        optimizer.optimize()
        result = optimizer.compute_sharpe(0.005)
        assert COL_SHARPE in result.columns

    def test_compute_sharpe_before_optimize_raises(self) -> None:
        opt = MarkowitzOptimizer(pd.DataFrame(np.random.randn(10, 2), columns=["A", "B"]))
        with pytest.raises(ValueError, match="Call optimize"):
            opt.compute_sharpe(0.005)

    def test_max_sharpe_portfolio(self, optimizer: MarkowitzOptimizer) -> None:
        optimizer.optimize()
        optimizer.compute_sharpe(0.005)
        best = optimizer.max_sharpe_portfolio()
        assert isinstance(best, pd.Series)
        assert isinstance(best[COL_SHARPE], float)

    def test_max_sharpe_before_compute_raises(self, optimizer: MarkowitzOptimizer) -> None:
        with pytest.raises(ValueError, match="compute_sharpe"):
            optimizer.max_sharpe_portfolio()


# --- CapitalAllocator tests ---


class TestCapitalAllocator:
    def test_weigh_risk_free(self) -> None:
        result = CapitalAllocator.weigh_risk_free(1.0, 2.0, 0.5)
        assert result == 1.5

    def test_capital_allocation_line_length(self, portfolio_slice: pd.Series) -> None:
        allocator = CapitalAllocator(portfolio_slice, 0.005)
        points = allocator.capital_allocation_line(steps=11)
        assert len(points) == 11

    def test_final_allocation_contains_renda_fixa(self, portfolio_slice: pd.Series) -> None:
        allocator = CapitalAllocator(portfolio_slice, 0.005)
        result = allocator.final_allocation(0.3)
        assert "Renda Fixa" in result
        assert result["Renda Fixa"] == 0.3

    def test_expected_returns(self, portfolio_slice: pd.Series) -> None:
        allocator = CapitalAllocator(portfolio_slice, 0.005)
        ret, risk = allocator.expected_returns(0.3)
        assert isinstance(ret, float)
        assert isinstance(risk, float)
        assert risk >= 0


# --- Visualization tests ---


class TestVisualization:
    def test_efficiency_frontier_plot(self, portfolios: pd.DataFrame) -> None:
        fig = efficiency_frontier_plot(portfolios, highlight_portfolio=50)
        assert fig is not None

    def test_allocation_pie(self, portfolio_slice: pd.Series) -> None:
        fig = allocation_pie(portfolio_slice)
        assert fig is not None

    def test_capital_allocation_line_plot(self, portfolio_slice: pd.Series) -> None:
        allocator = CapitalAllocator(portfolio_slice, 0.005)
        cal_points = allocator.capital_allocation_line(steps=11)
        fig = capital_allocation_line_plot(cal_points, highlight_point=5)
        assert fig is not None

    def test_correlation_heatmap(self, synthetic_returns: pd.DataFrame) -> None:
        corr = synthetic_returns.corr()
        fig = correlation_heatmap(corr)
        assert fig is not None

    def test_correlation_timeline_single(self, synthetic_returns: pd.DataFrame) -> None:
        prices = (1 + synthetic_returns).cumprod() * 100
        fig = correlation_timeline(prices, "PETR4.SA")
        assert fig is not None

    def test_correlation_timeline_multi(self, synthetic_returns: pd.DataFrame) -> None:
        prices = (1 + synthetic_returns).cumprod() * 100
        fig = correlation_timeline(prices, "PETR4.SA", "ITUB4.SA")
        assert fig is not None
