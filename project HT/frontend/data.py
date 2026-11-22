"""Adapter between the page and the pipeline.

Right now there is no real pipeline, so these functions return the example
JSON in schemas/examples/. To switch to the real pipeline, change the
USE_EXAMPLES line below (or replace the two function bodies with imports).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Make the project root importable (streamlit only adds frontend/ to the path).
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from schemas import Assumption, AgentResult, PipelineResult, Scenario  # noqa: E402

EXAMPLES = ROOT / "schemas" / "examples"
USE_EXAMPLES = True  # one-line switch: set False once the real pipeline exists


def _load(name: str):
    """Read one example JSON file."""
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def extract_assumptions(text: str) -> list[Assumption]:
    """Pull the key numbers out of the plan text (stub: example data)."""
    if not USE_EXAMPLES:
        from pipeline import extract_assumptions as real  # type: ignore
        return real(text)
    return [Assumption.from_dict(a) for a in _load("assumptions.json")]


def run_pipeline(text: str, assumptions: list[Assumption] | None = None) -> PipelineResult:
    """Run scenarios + agents on the confirmed numbers (stub: example data).

    Note: the stub ignores edited numbers, so results won't change on
    Recalculate until the real pipeline is plugged in.
    """
    if not USE_EXAMPLES:
        from pipeline import run_pipeline as real  # type: ignore
        return real(text, assumptions)

    meta = _load("meta.json")
    return PipelineResult(
        summary=meta["summary"],
        assumptions=assumptions or [Assumption.from_dict(a) for a in _load("assumptions.json")],
        scenarios=[Scenario.from_dict(_load(f"scenario_{n}.json")) for n in ("base", "upside", "downside")],
        agents=[AgentResult.from_dict(a) for a in _load("agents.json")],
        limitations=meta["limitations"],
    )
