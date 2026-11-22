"""Markdown report + small display helpers shared with the page.

Only formats what the pipeline returned. No finance maths here.
"""
from __future__ import annotations

from datetime import date

from schemas import AgentResult, Assumption, PipelineResult, Scenario

CURRENCY_SYMBOLS = {"EUR": "€", "USD": "$", "GBP": "£"}


def fmt(value, unit: str) -> str:
    """Format a number for display (text only, no calculation)."""
    if value is None:
        return "n/a"
    if unit == "%":
        return f"{value:g}%"
    if unit in CURRENCY_SYMBOLS:
        sign = "-" if value < 0 else ""
        return f"{sign}{CURRENCY_SYMBOLS[unit]}{abs(value):,.0f}"
    return f"{value:,.0f} {unit}"


def runway_text(s: Scenario) -> str:
    return f"{s.runway_months:g} months" if s.runway_months is not None else "24+ months"


def break_even_text(s: Scenario) -> str:
    return f"Month {s.break_even_month}" if s.break_even_month is not None else "Not within 24 months"


def disagreements(agents: list[AgentResult]) -> list[str]:
    """Topics where agents reviewing the same thing gave different verdicts."""
    topics: dict[str, dict[str, str]] = {}
    for a in agents:
        for f in a.findings:
            topics.setdefault(f.topic, {})[a.agent] = a.verdict
    lines = []
    for topic, views in topics.items():
        if len(set(views.values())) > 1:
            who = ", ".join(f"{agent} ({verdict})" for agent, verdict in views.items())
            lines.append(f"**{topic.capitalize()}**: {who}")
    return lines


# ---------- report sections ----------

def _cell(text) -> str:
    """Make text safe inside a Markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ")


def _scenarios_md(scenarios: list[Scenario]) -> list[str]:
    out = ["## Scenarios and KPIs", ""]
    for s in scenarios:
        out += [f"### {s.name.capitalize()}", "", s.description, "",
                "| KPI | Value |", "|---|---|",
                f"| Runway | {runway_text(s)} |",
                f"| Break-even | {break_even_text(s)} |"]
        out += [f"| {_cell(k.label)} | {fmt(k.value, k.unit)} |" for k in s.kpis]
        out.append("")
    return out


def _agents_md(agents: list[AgentResult]) -> list[str]:
    out = ["## Expert reviews", ""]
    conflicts = disagreements(agents)
    if conflicts:
        out += ["**Where the reviewers disagree:**", ""] + [f"- {c}" for c in conflicts] + [""]
    for a in agents:
        out += [f"### {a.agent}: {a.verdict}", "", f"_{a.role}_", "", a.summary, ""]
        for f in a.findings:
            out += [f"- **{f.title}** ({f.severity} severity, {f.topic}): {f.detail}"]
            quote = f"“{f.evidence_quote}”" if f.evidence_quote else "_No quote: the plan doesn't mention this._"
            out += [f"  - Evidence: {quote}"]
        if a.questions:
            out += ["", "**Questions for the founder:**", ""] + [f"- {q}" for q in a.questions]
        out.append("")
    return out


def _numbers_md(assumptions: list[Assumption]) -> list[str]:
    out = ["## Numbers used", "",
           "| Number | Value | Source | Note |", "|---|---|---|---|"]
    out += [f"| {_cell(a.label)} | {fmt(a.value, a.unit)} | {a.source} | {_cell(a.note)} |"
            for a in assumptions]
    return out + [""]


def build_markdown(result: PipelineResult, assumptions: list[Assumption]) -> str:
    """The full downloadable report."""
    lines = ["# VentureMind report", "",
             f"_Generated {date.today().isoformat()}_", "",
             "## Summary", "", result.summary, ""]
    lines += _scenarios_md(result.scenarios)
    lines += _agents_md(result.agents)
    lines += _numbers_md(assumptions)
    lines += ["## Limitations", ""]
    lines += [f"- {item}" for item in result.limitations] or ["- None reported."]
    return "\n".join(lines) + "\n"
