"""Plotly charts for the dashboard. Display only: plots values it is given."""
from __future__ import annotations

import plotly.graph_objects as go

from schemas import Scenario

# Reference palette, categorical slots 1-2 (fixed order).
BLUE = "#2a78d6"
ORANGE = "#eb6834"
MUTED = "#898781"


def _layout(fig: go.Figure, title: str, currency: str) -> go.Figure:
    """Shared, quiet chart styling."""
    fig.update_layout(
        title=dict(text=title, x=0, font=dict(size=16)),
        hovermode="x unified",
        margin=dict(l=70, r=20, t=60, b=50),
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
        xaxis=dict(title="Month", dtick=3, showgrid=False, automargin=True),
        yaxis=dict(title=currency, tickformat=",.0f", zeroline=False, automargin=True),
    )
    return fig


def _line(x, y, name, color, dash=None) -> go.Scatter:
    return go.Scatter(
        x=x, y=y, name=name, mode="lines",
        line=dict(color=color, width=2, dash=dash),
        hovertemplate="%{y:,.0f}",
    )


def cash_chart(s: Scenario) -> go.Figure:
    """Cash balance over 24 months, with the zero line and cash-out marked."""
    x = [m.month for m in s.months]
    fig = go.Figure(_line(x, [m.cash for m in s.months], "Cash", BLUE))
    fig.update_layout(showlegend=False)
    fig.add_hline(y=0, line=dict(color=MUTED, width=1, dash="dot"))
    if s.runway_months is not None:
        fig.add_vline(x=s.runway_months, line=dict(color=MUTED, width=1, dash="dash"),
                      annotation_text=f"Cash runs out after month {s.runway_months:g}",
                      annotation_position="top left")
    return _layout(fig, "Cash balance", s.currency)


def revenue_costs_chart(s: Scenario) -> go.Figure:
    """Monthly revenue vs costs, with break-even marked."""
    x = [m.month for m in s.months]
    fig = go.Figure([
        _line(x, [m.revenue for m in s.months], "Revenue", BLUE),
        _line(x, [m.costs for m in s.months], "Costs", ORANGE, dash="dash"),
    ])
    if s.break_even_month is not None:
        fig.add_vline(x=s.break_even_month, line=dict(color=MUTED, width=1, dash="dash"),
                      annotation_text=f"Break-even: month {s.break_even_month}",
                      annotation_position="top left")
    return _layout(fig, "Revenue vs costs per month", s.currency)
