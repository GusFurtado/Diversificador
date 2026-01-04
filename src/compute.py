import cvxopt as opt
from cvxopt import blas, solvers
import numpy as np
import pandas as pd


def compute_pct_change(
    df_tickers: pd.DataFrame, df_dolar: pd.DataFrame
) -> pd.DataFrame:
    df = pd.concat([df_tickers, df_dolar], axis=1)

    # Aplicar câmbio para colunas que não são em reais
    for col in df.columns:
        if not col.endswith(".SA") and col != "USD":
            df[col] = df[col] * df["USD"]

    df.drop(columns=["USD"], inplace=True)
    return df.pct_change(fill_method=None).dropna()


def compute_markowitz(
    df_pct_change: pd.DataFrame,
    risk_free_rate: float,
) -> pd.DataFrame:
    """Gera um DataFrame de portfólios otimizados.

    Returns
    -------
    pandas.DataFrame
        DataFrame de portfólios.

    """

    tickers = df_pct_change.columns.tolist()

    # Returns setup
    returns = np.asmatrix(df_pct_change.T)
    n = len(returns)

    # Optimizer setup
    S = opt.matrix(np.cov(returns))
    pbar = opt.matrix(np.mean(returns, axis=1))
    G = -opt.matrix(np.eye(n))
    h = opt.matrix(0.0, (n, 1))
    A = opt.matrix(1.0, (1, n))
    b = opt.matrix(1.0)

    # Solve
    mus = [10 ** (t / 20 - 1) for t in range(100)]
    portfolios = [solvers.qp(mu * S, -pbar, G, h, A, b)["x"] for mu in mus]

    # Concatenate porfolios
    concat = np.concatenate([np.asarray(portfolio) for portfolio in portfolios])
    df = pd.DataFrame(concat.reshape(-1, n))
    df.columns = tickers

    # Results
    df["Retorno Esperado"] = [blas.dot(pbar, x) for x in portfolios]
    df["Risco"] = [np.sqrt(blas.dot(x, S * x)) for x in portfolios]

    df.index = df.index[::-1]
    df = df.sort_index()

    df["Sharpe"] = (df["Retorno Esperado"] - risk_free_rate) / df["Risco"]
    return df
