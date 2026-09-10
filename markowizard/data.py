"""
Convenience functions for fetching market data and computing returns.

Use these to quickly download prices from Yahoo Finance. The core
analytical modules also accept a pre-computed returns DataFrame directly,
so these helpers are optional in practice.
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
        Yahoo Finance ticker symbols (e.g., ['AAPL', 'MSFT', 'SPY']).
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


def compute_monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Convert daily close prices to monthly percentage returns.

    Parameters
    ----------
    prices : pd.DataFrame
        Daily closing prices with DatetimeIndex and tickers as columns.

    Returns
    -------
    pd.DataFrame
        DataFrame of monthly percentage returns.
    """
    # Resample prices to end-of-month
    monthly_prices = prices.resample("ME").last()

    # Compute percentage change and drop NaN
    returns: pd.DataFrame = monthly_prices.pct_change().dropna()
    return returns
