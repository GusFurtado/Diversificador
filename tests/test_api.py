"""Tests for the FastAPI web service (`backend/`).

The market-data fetch is mocked, so these run offline; everything downstream
of the fetch (returns, optimization, CAL, serialization) exercises the real code.
"""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app

TICKERS = ["AAA", "BBB", "CCC"]


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def fake_prices() -> pd.DataFrame:
    """~3 years of synthetic daily close prices for three tickers."""
    rng = np.random.default_rng(0)
    dates = pd.date_range("2021-01-01", periods=780, freq="B")
    steps = rng.normal(loc=0.0004, scale=0.012, size=(len(dates), len(TICKERS)))
    prices = 100 * np.exp(np.cumsum(steps, axis=0))
    return pd.DataFrame(prices, index=dates, columns=TICKERS)


def test_health(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_root_serves_frontend(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_analyze_happy_path(client: TestClient, fake_prices: pd.DataFrame) -> None:
    with patch("backend.router.fetch_prices", return_value=fake_prices) as fetch:
        resp = client.post(
            "/api/analyze",
            json={"tickers": TICKERS, "period": "3y", "risk_free_rate": 0.004},
        )

    fetch.assert_called_once()
    assert resp.status_code == 200
    body = resp.json()

    assert body["tickers"] == TICKERS
    assert len(body["efficient_frontier"]) == 100
    assert set(body["max_sharpe_portfolio"]["weights"]) == set(TICKERS)
    assert body["max_sharpe_portfolio"]["sharpe"] is not None
    assert len(body["capital_allocation_line"]) == 21
    assert np.allclose(np.array(body["correlation_matrix"]).shape, (3, 3))


def test_analyze_reports_missing_tickers(client: TestClient, fake_prices: pd.DataFrame) -> None:
    partial = fake_prices.drop(columns=["CCC"])
    with patch("backend.router.fetch_prices", return_value=partial):
        resp = client.post("/api/analyze", json={"tickers": TICKERS})

    assert resp.status_code == 400
    assert "CCC" in resp.json()["detail"]


def test_analyze_rejects_empty_tickers(client: TestClient) -> None:
    resp = client.post("/api/analyze", json={"tickers": []})
    assert resp.status_code == 422


def test_analyze_wraps_fetch_errors(client: TestClient) -> None:
    with patch("backend.router.fetch_prices", side_effect=RuntimeError("yfinance down")):
        resp = client.post("/api/analyze", json={"tickers": TICKERS})

    assert resp.status_code == 500
    assert "yfinance down" in resp.json()["detail"]
