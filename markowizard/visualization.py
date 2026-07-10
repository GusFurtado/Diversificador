"""
Plotly-based visualization functions for portfolio analysis.

Returns standalone Plotly Figure objects (not tied to Dash).
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objects import Figure

from markowizard.core import COL_RETURN, COL_RISK, COL_SHARPE

# Shared default layout margin
_DEFAULT_MARGIN = {"b": 10, "t": 10}


def _build_hover_text(
    risco: pd.Series,
    retorno: pd.Series,
    sharpe: pd.Series | None = None,
) -> list[str]:
    """Build hover text from risk, return, and optional Sharpe columns."""
    if sharpe is None:
        sharpe = pd.Series([0.0] * len(risco), index=risco.index)
    return [
        f"<b>Retorno Esperado:</b> {y:.1%}<br>"
        f"<b>Risco:</b> ±{x:.1%}<br>"
        f"<b>Sharpe Ratio:</b> {z:.2f}"
        for x, y, z in zip(risco, retorno, sharpe, strict=True)
    ]


def _marker_styles(
    n: int,
    highlight_idx: int,
    base_color: str = "cyan",
    highlight_color: str = "yellow",
) -> tuple[list[str], list[int]]:
    """Build marker color and size lists, highlighting one index."""
    colors = [base_color if i != highlight_idx else highlight_color for i in range(n)]
    sizes = [8 if i != highlight_idx else 12 for i in range(n)]
    return colors, sizes


def efficiency_frontier_plot(
    portfolios: pd.DataFrame,
    highlight_portfolio: int = 0,
) -> Figure:
    """
    Plot the efficient frontier as a scatter plot of expected return vs risk.

    Parameters
    ----------
    portfolios : pd.DataFrame
        DataFrame with 'Retorno Esperado', 'Risco', and 'Sharpe' columns
        (as produced by MarkowitzOptimizer).
    highlight_portfolio : int, optional
        Index of the portfolio to highlight (default 0).

    Returns
    -------
    plotly.graph_objects.Figure
    """
    df = portfolios

    sharpe_col = df.get(COL_SHARPE) if COL_SHARPE in df.columns else None
    text = _build_hover_text(df[COL_RISK], df[COL_RETURN], sharpe_col)

    marker_color, marker_size = _marker_styles(len(df), highlight_portfolio)

    fig = go.Figure(
        data=go.Scatter(
            x=df[COL_RISK],
            y=df[COL_RETURN],
            name="Fronteira da Eficiência",
            mode="markers",
            marker={
                "size": marker_size,
                "color": marker_color,
                "opacity": 1,
                "line": {"color": "blue", "width": 2},
            },
            hovertext=text,
            hoverinfo="text",
        ),
        layout={
            "margin": _DEFAULT_MARGIN,
            "xaxis": {
                "tickformat": ",.1%",
                "title": {"text": "Risco (desvio padrão)"},
            },
            "yaxis": {
                "tickformat": ",.1%",
                "title": {"text": "Retorno Esperado (% a.m.)"},
            },
        },
    )

    # Annotate max Sharpe portfolio
    if COL_SHARPE in df.columns:
        max_sharpe = df[COL_SHARPE].idxmax()
        fig.add_annotation(
            x=df.loc[max_sharpe, COL_RISK],
            y=df.loc[max_sharpe, COL_RETURN],
            text="Maior Sharpe Ratio",
            showarrow=True,
            arrowhead=1,
            arrowwidth=2,
            axref="pixel",
            ax=100,
            ayref="pixel",
            ay=20,
        )

    return fig


def allocation_pie(portfolio: pd.Series) -> Figure:
    """
    Pie chart showing asset allocation for a single portfolio.

    Parameters
    ----------
    portfolio : pd.Series
        A single portfolio row from the efficient frontier DataFrame.
        Non-zero asset weights are displayed; meta columns like
        'Retorno Esperado', 'Risco', 'Sharpe' are excluded.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    # Filter out metadata columns and near-zero weights
    keys_to_exclude = {COL_RETURN, COL_RISK, COL_SHARPE}
    ds = portfolio[~portfolio.index.isin(keys_to_exclude)]
    ds = ds[ds > 0.0001]

    if ds.empty:
        ds = pd.Series({"(no allocation)": 1.0})

    fig = go.Figure(
        data=go.Pie(
            labels=ds.index.tolist(),
            values=ds.values,
            hole=0.4,
            textinfo="label+percent",
            hoverinfo="skip",
        ),
        layout=go.Layout(margin={"b": 0, "t": 0}),
    )
    return fig


def capital_allocation_line_plot(
    cal_points: list[dict],
    highlight_point: int = 0,
) -> Figure:
    """
    Plot the Capital Allocation Line (CAL) showing risk-return trade-offs
    for different mixes of risky portfolio and risk-free asset.

    Parameters
    ----------
    cal_points : list of dict
        Output from CapitalAllocator.capital_allocation_line().
    highlight_point : int, optional
        Index of the point to highlight (default 0).

    Returns
    -------
    plotly.graph_objects.Figure
    """
    proportions = [p["p"] for p in cal_points]
    retornos = [p["expected_return"] for p in cal_points]

    text = [
        f"<b>Proporção de Renda Fixa:</b> {p['p']:.0%}<br>"
        f"<b>Retorno Esperado:</b> {p['expected_return']:.1%} ± {p['risk']:.1%} a.m."
        for p in cal_points
    ]

    marker_color, marker_size = _marker_styles(len(cal_points), highlight_point)

    fig = go.Figure(
        data=go.Scatter(
            x=proportions,
            y=retornos,
            mode="lines+markers",
            hovertext=text,
            hoverinfo="text",
            marker={
                "size": marker_size,
                "color": marker_color,
                "opacity": 1,
                "line": {"color": "blue", "width": 2},
            },
            line={"color": "blue", "width": 3},
        ),
        layout={
            "margin": _DEFAULT_MARGIN,
            "xaxis": {
                "tickformat": ",.0%",
                "autorange": "reversed",
                "title": {"text": "Proporção de Renda Fixa"},
            },
            "yaxis": {
                "tickformat": ",.1%",
                "title": {"text": "Retorno Esperado (% a.m.)"},
            },
        },
    )

    return fig


def correlation_timeline(
    prices: pd.DataFrame,
    ticker_a: str,
    ticker_b: str | None = None,
) -> Figure:
    """
    Plot the price history of one or two assets, normalizing when comparing
    two different assets.

    Parameters
    ----------
    prices : pd.DataFrame
        DataFrame of historical prices with DatetimeIndex and tickers as columns.
    ticker_a : str
        Primary ticker.
    ticker_b : str or None, optional
        Secondary ticker. If None or equal to ticker_a, plots a single line.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    if ticker_b is None or ticker_a == ticker_b:
        return _plot_single(prices, ticker_a)

    return _plot_multi(prices, ticker_a, ticker_b)


def _plot_single(prices: pd.DataFrame, ticker: str) -> Figure:
    """Plot a single ticker's price history."""
    ds = prices[ticker].dropna()

    fig = go.Figure(
        data=go.Scatter(
            x=ds.index,
            y=ds,
            name=ticker,
            hoverinfo="skip",
        ),
        layout={
            "margin": _DEFAULT_MARGIN,
            "showlegend": False,
        },
    )
    return fig


def _plot_multi(prices: pd.DataFrame, ticker_a: str, ticker_b: str) -> Figure:
    """Plot two tickers' price histories, normalized to [0, 1]."""
    df = prices[[ticker_a, ticker_b]].dropna()

    fig = go.Figure(
        layout={
            "yaxis": {"visible": False},
            "margin": _DEFAULT_MARGIN,
            "showlegend": False,
        }
    )

    for ticker in [ticker_a, ticker_b]:
        series = df[ticker]
        min_val, max_val = series.min(), series.max()
        normalized = (series - min_val) / (max_val - min_val) if max_val > min_val else series * 0

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=normalized,
                name=ticker,
                hoverinfo="skip",
            )
        )

    return fig


def correlation_heatmap(corr_matrix: pd.DataFrame) -> Figure:
    """
    Plot a correlation matrix heatmap.

    Parameters
    ----------
    corr_matrix : pd.DataFrame
        Square correlation matrix with ticker names as index and columns.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    fig = go.Figure(
        data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.index.tolist(),
            text=corr_matrix.values.round(2),
            texttemplate="%{text}",
            colorscale="RdBu",
            zmid=0,
            zmin=-1,
            zmax=1,
            hovertemplate="%{x} vs %{y}: %{z:.2f}<extra></extra>",
        ),
        layout={
            "margin": {"b": 80, "t": 30, "l": 80, "r": 20},
            "xaxis": {"side": "bottom"},
            "yaxis": {"autorange": "reversed"},
        },
    )
    return fig
