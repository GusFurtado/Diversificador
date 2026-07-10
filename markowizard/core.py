"""
Core portfolio optimization using Markowitz Modern Portfolio Theory.

Uses scipy.optimize to compute the efficient frontier.
"""

import logging
from collections.abc import Callable

import numpy as np
import pandas as pd
from scipy.optimize import minimize

logger = logging.getLogger(__name__)

# English column names for display (region-agnostic)
COL_RETURN = "Expected Return"
COL_RISK = "Risk"
COL_SHARPE = "Sharpe"
COL_RISK_FREE = "Risk-Free"


def _make_objective(
    mu: float,
    cov_matrix: np.ndarray,
    mean_returns: np.ndarray,
) -> Callable[[np.ndarray], float]:
    """Build the quadratic objective function for a given risk-aversion parameter."""

    def objective(w: np.ndarray) -> float:
        return float(0.5 * mu * w @ cov_matrix @ w - mean_returns @ w)

    return objective


class MarkowitzOptimizer:
    """
    Performs Markowitz mean-variance optimization to find the efficient frontier.

    Parameters
    ----------
    returns : pandas.DataFrame
        DataFrame of historical asset returns, where each column is an asset
        and each row is a time period (e.g., monthly returns). Returns should
        be in decimal form (e.g., 0.01 = 1%), not percentage form.

    Attributes
    ----------
    tickers : pandas.Index
        Asset tickers/column names.
    returns : pandas.DataFrame
        The input returns data.
    portfolios : pandas.DataFrame | None
        DataFrame of optimized portfolios along the efficient frontier,
        containing weights for each asset plus 'Expected Return',
        'Risk' (std), and 'Sharpe' (Sharpe ratio).
    n_assets : int
        Number of assets in the portfolio.
    """

    def __init__(self, returns: pd.DataFrame) -> None:
        if returns.empty:
            raise ValueError("returns DataFrame must not be empty.")
        if returns.shape[1] < 1:
            raise ValueError("returns DataFrame must have at least one asset column.")

        self.returns = returns
        self.tickers = returns.columns
        self.portfolios: pd.DataFrame | None = None
        self.n_assets = returns.shape[1]

    def optimize(self) -> pd.DataFrame:
        """
        Compute the efficient frontier by solving quadratic programming
        problems for a range of risk-aversion parameters (mu).

        Uses warm-starting: the optimal weights from one mu value serve as
        the initial guess for the next, reducing total iterations.

        Returns
        -------
        pandas.DataFrame
            Efficient frontier portfolios with columns for each asset weight,
            'Expected Return', 'Risk', and 'Sharpe'.
        """
        returns_array = self.returns.values.T  # shape: (n_assets, n_periods)
        n = self.n_assets

        # Mean returns vector and covariance matrix
        mean_returns = np.mean(returns_array, axis=1)
        cov_matrix = np.cov(returns_array)

        # Constraints: sum(weights) = 1
        constraints: dict = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}

        # Bounds: no short selling (weights >= 0)
        bounds: list[tuple[float, float | None]] = [(0.0, None) for _ in range(n)]

        # Generate a range of risk-aversion parameters (mu)
        # Higher mu = more risk-averse -> lower risk portfolios
        mus = [10 ** (t / 20 - 1) for t in range(100)]

        portfolios_list: list[np.ndarray] = []
        n_failed = 0

        # Warm-start: start with equal weights, then use previous solution
        w0 = np.ones(n) / n

        for mu in mus:
            objective = _make_objective(mu, cov_matrix, mean_returns)

            result = minimize(
                objective,
                w0,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
            )

            if result.success:
                portfolios_list.append(result.x)
                w0 = result.x  # warm-start next iteration
            else:
                n_failed += 1
                # Fall back to equal weights as a last resort
                w_fallback = w0.copy()
                portfolios_list.append(w_fallback)
                logger.warning(
                    "Optimization failed for mu=%f (iteration %d). "
                    "Using previous weights as fallback.",
                    mu,
                    len(portfolios_list) - 1,
                )

        if n_failed > 0:
            logger.warning("%d out of %d optimizations failed.", n_failed, len(mus))

        # Build DataFrame
        concat = np.array(portfolios_list)
        df = pd.DataFrame(concat, columns=self.tickers)

        # Compute expected return and risk for each portfolio
        df[COL_RETURN] = concat @ mean_returns
        df[COL_RISK] = np.sqrt(np.diag(concat @ cov_matrix @ concat.T))

        # Sort by risk (ascending) so the frontier is ordered
        df = df.sort_values(COL_RISK).reset_index(drop=True)

        self.portfolios = df
        return self.portfolios

    def compute_sharpe(self, risk_free_rate: float) -> pd.DataFrame:
        """
        Compute the Sharpe ratio for each portfolio on the efficient frontier.

        Parameters
        ----------
        risk_free_rate : float
        Risk-free rate (e.g., monthly rate). Should be in decimal
            form (e.g., 0.005 for 0.5% a.m.).

        Returns
        -------
        pandas.DataFrame
            The portfolios DataFrame with an added 'Sharpe' column.
        """
        if self.portfolios is None:
            raise ValueError("Call optimize() before computing Sharpe ratios.")

        self.portfolios[COL_SHARPE] = (
            self.portfolios[COL_RETURN] - risk_free_rate
        ) / self.portfolios[COL_RISK]
        return self.portfolios

    def max_sharpe_portfolio(self) -> pd.Series:
        """
        Return the portfolio with the highest Sharpe ratio.

        Returns
        -------
        pandas.Series
            The tangency (maximum Sharpe) portfolio.
        """
        if self.portfolios is None or COL_SHARPE not in self.portfolios.columns:
            raise ValueError("Call optimize() and compute_sharpe() first.")

        idx = self.portfolios[COL_SHARPE].idxmax()
        return self.portfolios.loc[idx]
