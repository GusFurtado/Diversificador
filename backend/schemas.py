"""Pydantic models for the MarkoWizard API."""

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request body for the /analyze endpoint."""

    tickers: list[str] = Field(
        ..., min_length=1, description="List of Yahoo Finance ticker symbols"
    )
    period: str = Field(default="5y", description="Data period (e.g., '1y', '5y', '10y')")
    risk_free_rate: float = Field(
        default=0.005, ge=0.0, description="Monthly risk-free rate in decimal form"
    )


class PortfolioMetrics(BaseModel):
    """Metrics for a single portfolio on the efficient frontier."""

    risk: float
    expected_return: float
    sharpe: float | None = None
    weights: dict[str, float]


class MaxSharpePortfolio(BaseModel):
    """Details of the maximum Sharpe ratio portfolio."""

    risk: float
    expected_return: float
    sharpe: float
    weights: dict[str, float]


class CapitalAllocationPoint(BaseModel):
    """A single point on the Capital Allocation Line."""

    p: float
    expected_return: float
    risk: float
    label: str


class AnalyzeResponse(BaseModel):
    """Response from the /analyze endpoint."""

    tickers: list[str]
    efficient_frontier: list[PortfolioMetrics]
    max_sharpe_portfolio: MaxSharpePortfolio
    capital_allocation_line: list[CapitalAllocationPoint]
    charts: dict[str, object]
