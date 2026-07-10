"""
Convenience functions for fetching market data and computing returns.

This module is optional — the core analytical modules accept pre-computed
returns DataFrames. Use these functions to quickly download data from
public sources.
"""

import re
from typing import Any

import pandas as pd
import yfinance as yf

# Pattern for validating Yahoo Finance ticker symbols
_TICKER_PATTERN = re.compile(r"^[A-Z0-9.-]+$", re.IGNORECASE)


def _validate_tickers(tickers: list[str]) -> None:
    """Validate a list of ticker symbols against a safe pattern.

    Parameters
    ----------
    tickers : list of str
        Ticker symbols to validate.

    Raises
    ------
    ValueError
        If any ticker contains characters other than letters, digits,
        dots, hyphens, or is empty.
    """
    for t in tickers:
        if not t or not isinstance(t, str):
            raise ValueError(f"Invalid ticker: {t!r}. Tickers must be non-empty strings.")
        if not _TICKER_PATTERN.match(t):
            raise ValueError(
                f"Invalid ticker: {t!r}. Tickers may only contain letters, "
                f"digits, dots, and hyphens."
            )


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
        Each ticker must match ``^[A-Z0-9.-]+$``.
    period : str, optional
        Data period (default '5y'). See yfinance for valid periods.
    auto_adjust : bool, optional
        Whether to use auto-adjusted close prices (default True).

    Returns
    -------
    pd.DataFrame
        DataFrame of closing prices with DatetimeIndex and tickers as columns.
    """
    _validate_tickers(tickers)
    t = yf.Tickers(" ".join(tickers))
    df: Any = t.history(period=period, auto_adjust=auto_adjust, progress=False)
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
        from DadosAbertosBrasil import bacen  # type: ignore[import-not-found]

        df = bacen.cambio(inicio=start, index=True)
        monthly = df.resample("ME").last()
        return monthly
    except ImportError:
        raise ImportError(
            "DadosAbertosBrasil is required for fetching USD rates. "
            "Install it with: pip install markowizard[data]"
        ) from None


def get_selic() -> float:
    """
    Fetch the current monthly SELIC rate (Brazilian risk-free rate).

    Returns
    -------
    float
        Monthly SELIC rate as a decimal (e.g., 0.005 for 0.5% a.m.).
    """
    try:
        from DadosAbertosBrasil import selic  # type: ignore[import-not-found]

        ao_ano = selic(ultimos=1).loc[0, "valor"]
        monthly = (float(ao_ano) / 100 + 1) ** (1 / 12) - 1
        return float(monthly)
    except ImportError:
        raise ImportError(
            "DadosAbertosBrasil is required for fetching SELIC rate. "
            "Install it with: pip install markowizard[data]"
        ) from None


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
    monthly_prices = prices.resample("ME").last()

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
    returns: pd.DataFrame = monthly_prices.pct_change().dropna()
    return returns
