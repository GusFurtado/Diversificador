"""
Core portfolio optimization using Markowitz Modern Portfolio Theory.

Replaces the original cvxopt-based implementation with scipy.optimize.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize


class MarkowitzOptimizer:
    """
    Performs Markowitz mean-variance optimization to find the efficient frontier.

    Parameters
    ----------
    returns : pandas.DataFrame
        DataFrame of historical asset returns, where each column is an asset
        and each row is a time period (e.g., monthly returns).

    Attributes
    ----------
    tickers : pandas.Index
        Asset tickers/column names.
    returns : pandas.DataFrame
        The input returns data.
    portfolios : pandas.DataFrame
        DataFrame of optimized portfolios along the efficient frontier,
        containing weights for each asset plus 'Retorno Esperado' (expected
        return), 'Risco' (risk/std), and 'Sharpe' (Sharpe ratio).
    """

    def __init__(self, returns: pd.DataFrame):
        self.returns = returns
        self.tickers = returns.columns
        self.portfolios: pd.DataFrame | None = None

    def optimize(self) -> pd.DataFrame:
        """
        Compute the efficient frontier by solving quadratic programming
        problems for a range of risk-aversion parameters (mu).

        Returns
        -------
        pandas.DataFrame
            Efficient frontier portfolios with columns for each asset weight,
            'Retorno Esperado', 'Risco', and 'Sharpe'.
        """
        returns_array = self.returns.values.T  # shape: (n_assets, n_periods)
        n = returns_array.shape[0]

        # Mean returns vector and covariance matrix
        mean_returns = np.mean(returns_array, axis=1)
        cov_matrix = np.cov(returns_array)

        # Constraints: sum(weights) = 1
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}

        # Bounds: no short selling (weights >= 0)
        bounds = [(0.0, None) for _ in range(n)]

        # Initial guess: equal weights
        w0 = np.ones(n) / n

        # Generate a range of risk-aversion parameters (mu)
        # Higher mu = more risk-averse -> lower risk portfolios
        mus = [10 ** (t / 20 - 1) for t in range(100)]

        portfolios_list = []

        for mu in mus:
            # Objective: minimize 0.5 * w^T Σ w * mu - w^T μ
            # (mu scales the risk term; higher mu = more risk penalty)
            def objective(w, mu=mu):
                return 0.5 * mu * w @ cov_matrix @ w - mean_returns @ w

            result = minimize(
                objective,
                w0,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
            )

            if result.success:
                portfolios_list.append(result.x)
            else:
                # If optimization fails, append equal weights as fallback
                portfolios_list.append(w0.copy())

        # Build DataFrame
        concat = np.array(portfolios_list)
        df = pd.DataFrame(concat, columns=self.tickers)

        # Compute expected return and risk for each portfolio
        df["Retorno Esperado"] = concat @ mean_returns
        df["Risco"] = np.sqrt(np.diag(concat @ cov_matrix @ concat.T))

        # Sort by risk (ascending) so the frontier is ordered
        df = df.sort_values("Risco").reset_index(drop=True)

        self.portfolios = df
        return self.portfolios

    def compute_sharpe(self, risk_free_rate: float) -> pd.DataFrame:
        """
        Compute the Sharpe ratio for each portfolio on the efficient frontier.

        Parameters
        ----------
        risk_free_rate : float
            Risk-free rate (e.g., monthly SELIC rate).

        Returns
        -------
        pandas.DataFrame
            The portfolios DataFrame with an added 'Sharpe' column.
        """
        if self.portfolios is None:
            raise ValueError("Call optimize() before computing Sharpe ratios.")

        self.portfolios["Sharpe"] = self.portfolios.apply(
            lambda row: (row["Retorno Esperado"] - risk_free_rate) / row["Risco"],
            axis=1,
        )
        return self.portfolios

    def max_sharpe_portfolio(self) -> pd.Series:
        """
        Return the portfolio with the highest Sharpe ratio.

        Returns
        -------
        pandas.Series
            The tangency (maximum Sharpe) portfolio.
        """
        if self.portfolios is None or "Sharpe" not in self.portfolios.columns:
            raise ValueError("Call optimize() and compute_sharpe() first.")

        idx = self.portfolios["Sharpe"].idxmax()
        return self.portfolios.loc[idx]
