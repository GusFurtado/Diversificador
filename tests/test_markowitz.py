import pytest

from src.compute import compute_pct_change, compute_markowitz
from src.get import get_selic, get_dolar, get_tickers


@pytest.fixture
def selic():
    selic_value = get_selic()

    assert isinstance(selic_value, float)
    assert selic_value > 0

    return selic_value


@pytest.fixture
def dolar():
    dolar_df = get_dolar()

    assert not dolar_df.empty
    assert "USD" in dolar_df.columns

    return dolar_df


@pytest.fixture
def tickers():
    tickers = ["AAPL", "MSFT", "GOOGL"]
    tickers_df = get_tickers(tickers)

    assert not tickers_df.empty
    for ticker in tickers:
        assert ticker in tickers_df.columns

    return tickers_df


@pytest.fixture
def pct_change(tickers, dolar):
    combined_df = compute_pct_change(tickers, dolar)

    assert not combined_df.empty
    assert "AAPL" in combined_df.columns
    assert "MSFT" in combined_df.columns
    assert "USD" in combined_df.columns

    return combined_df


def test_compute_markowitz(pct_change, selic):
    portfolios_df = compute_markowitz(pct_change, selic)

    assert not portfolios_df.empty
    assert "Retorno Esperado" in portfolios_df.columns
    assert "Risco" in portfolios_df.columns
    assert "Sharpe" in portfolios_df.columns
