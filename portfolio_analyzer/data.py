"""
Convenience functions for fetching market data and computing returns.

This module is optional — the core analytical modules accept pre-computed
returns DataFrames. Use these functions to quickly download data from
public sources.
"""

import pandas as pd
import yfinance as yf


def fetch_prices(
    tickers: list[str],
    period: str = "5y",
    auto_adjust: bool = True,
) -> pd.DataFrame:
    """
    Download historical adjusted close prices for a list of tickers.

    Parameters
    ----------
    tickers : list of str
        Yahoo Finance ticker symbols (e.g., ['PETR4.SA', 'ITUB4.SA', 'IVVB11.SA']).
    period : str, optional
        Data period (default '5y'). See yfinance for valid periods.
    auto_adjust : bool, optional
        Whether to use auto-adjusted close prices (default True).

    Returns
    -------
    pd.DataFrame
        DataFrame of closing prices with DatetimeIndex and tickers as columns.
    """
    t = yf.Tickers(" ".join(tickers))
    df = t.history(period=period, auto_adjust=auto_adjust, progress=False)
    return df["Close"]


def fetch_usd_rates(start: str = "2015-01-01") -> pd.DataFrame:
    """
    Fetch USD/BRL exchange rates from the Brazilian Central Bank via
    DadosAbertosBrasil.

    Parameters
    ----------
    start : str, optional
        Start date in 'YYYY-MM-DD' format (default '2015-01-01').

    Returns
    -------
    pd.DataFrame
        DataFrame with daily USD/BRL rates, resampled to end-of-month.
    """
    try:
        from DadosAbertosBrasil import bacen

        df = bacen.cambio(inicio=start, index=True)
        monthly = df.groupby(df.index.strftime("%Y-%m")).last()
        monthly.index = pd.to_datetime(monthly.index + "-01") + pd.offsets.MonthEnd(1)
        return monthly
    except ImportError:
        raise ImportError(
            "DadosAbertosBrasil is required for fetching USD rates. "
            "Install it with: pip install DadosAbertosBrasil"
        )


def get_selic() -> float:
    """
    Fetch the current monthly SELIC rate (Brazilian risk-free rate).

    Returns
    -------
    float
        Monthly SELIC rate as a decimal (e.g., 0.005 for 0.5% a.m.).
    """
    try:
        from DadosAbertosBrasil import selic

        ao_ano = selic(ultimos=1).loc[0, "valor"]
        monthly = (float(ao_ano) / 100 + 1) ** (1 / 12) - 1
        return float(monthly)
    except ImportError:
        raise ImportError(
            "DadosAbertosBrasil is required for fetching SELIC rate. "
            "Install it with: pip install DadosAbertosBrasil"
        )


def compute_monthly_returns(
    prices: pd.DataFrame,
    usd_rates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Convert daily close prices to monthly percentage returns, converting
    foreign assets to BRL if USD rates are provided.

    Parameters
    ----------
    prices : pd.DataFrame
        Daily closing prices with DatetimeIndex and tickers as columns.
    usd_rates : pd.DataFrame or None, optional
        Monthly USD/BRL rates with a 'USD' column and DatetimeIndex.
        If provided, tickers not ending in '.SA' will be converted to BRL.

    Returns
    -------
    pd.DataFrame
        DataFrame of monthly percentage returns.
    """
    # Resample prices to end-of-month
    monthly_prices = prices.groupby(prices.index.strftime("%Y-%m")).last()
    monthly_prices.index = pd.to_datetime(
        monthly_prices.index + "-01"
    ) + pd.offsets.MonthEnd(1)

    # Convert foreign assets to BRL
    if usd_rates is not None:
        for col in monthly_prices.columns:
            if not col.endswith(".SA"):
                temp = pd.concat(
                    [monthly_prices[col], usd_rates["USD"]],
                    axis=1,
                    join="inner",
                )
                monthly_prices[col] = temp[col] * temp["USD"]

    # Compute percentage change and drop NaN
    returns = monthly_prices.pct_change().dropna()
    return returns
