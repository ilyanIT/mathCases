"""VentureMind - Streamlit frontend.

The page only displays what the pipeline returns (see frontend/data.py).
No finance maths and no AI prompts live here.
"""
import sys
from dataclasses import replace
from pathlib import Path

import streamlit as st

# Make project root importable (for parsing/ and schemas/).
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import charts  # noqa: E402
from config import load_secrets  # noqa: E402
from data import USE_EXAMPLES, extract_assumptions, run_pipeline  # noqa: E402
from report import break_even_text, build_markdown, disagreements, fmt, runway_text  # noqa: E402
from parsing.pdf_extract import MIN_TEXT_CHARS, PdfExtractError, extract_text  # noqa: E402
from schemas import AgentResult, Assumption, PipelineResult, Scenario  # noqa: E402

PREVIEW_CHARS = 600
STEPS = {"upload": "1. Upload your plan", "checkpoint": "2. Check the numbers",
         "dashboard": "3. See your results"}


class InputError(Exception):
    """A problem with what the founder typed; message is shown as-is."""


# ---------- state ----------

def init_state() -> None:
    """Set default session values once."""
    defaults = {"stage": "upload", "plan_text": "", "assumptions": None, "result": None}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def go_to(stage: str) -> None:
    st.session_state.stage = stage


def start_over() -> None:
    """Forget everything and return to the upload screen."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_state()


# ---------- upload screen ----------

def read_plan_text(uploaded, pasted: str) -> str:
    """Get plan text from the PDF (preferred) or the pasted box.

    Raises PdfExtractError with a friendly message.
    """
    if uploaded is not None:
        return extract_text(uploaded.getvalue())
    text = pasted.strip()
    if len(text) < MIN_TEXT_CHARS:
        raise InputError("That text is very short. Please paste your full business plan.")
    return text


def analyze(uploaded, pasted: str) -> None:
    """Read the plan and extract its key numbers, with progress shown."""
    st.session_state.plan_text = ""  # clear any previous result
    with st.status("Analyzing your plan...", expanded=True) as status:
        try:
            st.write("Reading the text...")
            text = read_plan_text(uploaded, pasted)
            st.write("Finding the key numbers...")
            assumptions = extract_assumptions(text)
        except PdfExtractError as err:
            status.update(label="We couldn't read that PDF", state="error")
            st.error(f"{err} Please copy the text and use **Or paste the plan text** instead.")
            return
        except InputError as err:
            status.update(label="We need a bit more text", state="error")
            st.error(str(err))
            return
        except Exception:
            status.update(label="Something went wrong", state="error")
            st.error("We couldn't analyze this plan. Please try again, or paste the text instead.")
            return
        status.update(label="Done! Your plan has been read.", state="complete", expanded=False)

    st.session_state.plan_text = text
    st.session_state.assumptions = assumptions


def show_preview() -> None:
    """Show the start of the extracted text so the founder can see it worked."""
    text = st.session_state.plan_text
    st.success(f"We read {len(text):,} characters from your plan.", icon=":material/check_circle:")
    with st.expander("Preview of the text we read", expanded=True):
        snippet = text[:PREVIEW_CHARS] + ("..." if len(text) > PREVIEW_CHARS else "")
        st.text(snippet)
    st.button("Next: check the numbers →", type="primary", on_click=go_to, args=("checkpoint",))


def upload_screen() -> None:
    st.title("VentureMind")
    st.markdown(
        "Upload your business plan and we'll stress-test it: **three financial "
        "scenarios** and **four expert reviews**, each backed by evidence from your plan."
    )

    uploaded = st.file_uploader("Upload your business plan (PDF)", type=["pdf"])
    pasted = st.text_area("Or paste the plan text", height=200,
                          placeholder="Paste your business plan here...")

    has_input = uploaded is not None or bool(pasted.strip())
    if not has_input:
        st.info("Start by uploading a PDF or pasting your plan text, then click **Analyze**.",
                icon=":material/upload_file:")
    elif uploaded is not None and pasted.strip():
        st.caption("You gave both a PDF and pasted text. We'll use the PDF.")

    if st.button("Analyze", type="primary", disabled=not has_input):
        analyze(uploaded, pasted)

    if st.session_state.plan_text:
        show_preview()


# ---------- checkpoint screen ----------

SOURCES = ["from the plan", "assumption"]


def to_rows(assumptions: list[Assumption]) -> list[dict]:
    """Assumption objects -> editable table rows."""
    return [
        {"key": a.key, "Number": a.label, "Value": a.value, "Unit": a.unit,
         "Source": a.source, "Note": a.note}
        for a in assumptions
    ]


def from_rows(rows: list[dict], original: list[Assumption]) -> list[Assumption]:
    """Edited table rows -> Assumption objects (keeps non-edited fields)."""
    by_key = {a.key: a for a in original}
    return [
        replace(by_key[r["key"]], value=float(r["Value"]), source=r["Source"])
        for r in rows
    ]


def find_problems(rows: list[dict]) -> list[str]:
    """Return friendly messages for empty cells."""
    problems = []
    for r in rows:
        if r["Value"] is None:
            problems.append(f"**{r['Number']}** needs a value.")
        if r["Source"] not in SOURCES:
            problems.append(f"**{r['Number']}** needs a source.")
    return problems


def confirm_and_run(rows: list[dict]) -> None:
    """Save the confirmed numbers and run the pipeline."""
    assumptions = from_rows(rows, st.session_state.assumptions)
    try:
        with st.spinner("Building your scenarios and expert reviews..."):
            result = run_pipeline(st.session_state.plan_text, assumptions)
    except Exception:
        st.error("We couldn't run the analysis. Please click **Confirm and run** again.")
        return
    st.session_state.assumptions = assumptions
    st.session_state.result = result
    go_to("dashboard")
    st.rerun()


def checkpoint_screen() -> None:
    st.title("Check the numbers")
    assumptions = st.session_state.assumptions
    if not assumptions:
        st.warning("We didn't find any numbers in your plan. Try pasting a plan "
                   "that includes prices, costs or funding.")
        st.button("← Back to upload", on_click=start_over)
        return

    guessed = sum(a.source == "assumption" for a in assumptions)
    st.write("These are the key numbers we found. Check them and fix anything "
             "that's wrong. Nothing is calculated until you confirm.")
    if guessed:
        st.info(f"**{guessed}** number(s) were not in your plan, so we assumed them. "
                "Please check the rows marked **assumption**.", icon=":material/edit_note:")

    rows = st.data_editor(
        to_rows(assumptions),
        key="checkpoint_editor",  # keeps edits across reruns
        column_order=["Number", "Value", "Unit", "Source", "Note"],
        column_config={
            "Number": st.column_config.TextColumn(disabled=True),
            "Value": st.column_config.NumberColumn(required=True, min_value=0),
            "Unit": st.column_config.TextColumn(disabled=True),
            "Source": st.column_config.SelectboxColumn(options=SOURCES, required=True),
            "Note": st.column_config.TextColumn("Where it came from", disabled=True),
        },
        hide_index=True,
        num_rows="fixed",
        width="stretch",
    )

    problems = find_problems(rows)
    for p in problems:
        st.error(p)

    left, right = st.columns([1, 4])
    left.button("← Start over", on_click=start_over)
    if right.button("Confirm and run", type="primary", disabled=bool(problems)):
        confirm_and_run(rows)


# ---------- dashboard ----------

# Material icons keep one consistent icon style; every color also has a text label.
SCENARIO_TABS = [("base", ":material/analytics: Base"),
                 ("upside", ":material/trending_up: Upside"),
                 ("downside", ":material/trending_down: Downside")]
VERDICT_ICON = {"positive": ":material/check_circle:", "neutral": ":material/info:",
                "concerned": ":material/warning:"}
VERDICT_COLOR = {"positive": "green", "neutral": "gray", "concerned": "orange"}
SEVERITY_LABEL = {"low": "Low", "medium": "Medium", "high": "High"}
SEVERITY_COLOR = {"low": "gray", "medium": "orange", "high": "red"}


def headline_metrics(s: Scenario) -> None:
    """Runway and break-even cards."""
    left, right = st.columns(2)
    left.metric("Runway", runway_text(s), border=True,
                help="How long the cash lasts. 24+ means it never runs out in the projection.")
    right.metric("Break-even", break_even_text(s), border=True,
                 help="First month where revenue covers all costs.")


def kpi_cards(s: Scenario) -> None:
    """The scenario's other KPIs as metric cards."""
    if not s.kpis:
        return
    cols = st.columns(len(s.kpis))
    for col, k in zip(cols, s.kpis):
        col.metric(k.label, fmt(k.value, k.unit), help=k.help or None, border=True)


def scenario_tab(s: Scenario) -> None:
    st.caption(s.description)
    headline_metrics(s)
    kpi_cards(s)
    left, right = st.columns(2)
    left.plotly_chart(charts.cash_chart(s), width="stretch", key=f"cash_{s.name}")
    right.plotly_chart(charts.revenue_costs_chart(s), width="stretch", key=f"rc_{s.name}")


def scenario_tabs(result: PipelineResult) -> None:
    by_name = {s.name: s for s in result.scenarios}
    tabs = st.tabs([label for _, label in SCENARIO_TABS])
    for tab, (name, label) in zip(tabs, SCENARIO_TABS):
        with tab:
            if name in by_name:
                scenario_tab(by_name[name])
            else:
                st.info(f"No {name} scenario was returned for this plan.")


def show_disagreements(agents: list[AgentResult]) -> None:
    lines = disagreements(agents)
    if lines:
        st.warning("**Where the reviewers disagree.** Look at these topics closely:\n\n"
                   + "\n".join(f"- {line}" for line in lines),
                   icon=":material/compare_arrows:")
    else:
        st.success("The reviewers broadly agree on every topic they covered.",
                   icon=":material/check_circle:")


def agent_card(a: AgentResult) -> None:
    title = f"{a.agent} · {a.verdict.capitalize()}"
    with st.expander(title, icon=VERDICT_ICON.get(a.verdict, ":material/help:")):
        st.badge(a.verdict.capitalize(), color=VERDICT_COLOR.get(a.verdict, "gray"))
        st.caption(a.role)
        st.write(a.summary)
        if a.findings:
            st.markdown("**Findings**")
        for f in a.findings:
            color = SEVERITY_COLOR.get(f.severity, "gray")
            st.markdown(f"**{f.title}** · :{color}-badge[{SEVERITY_LABEL.get(f.severity, f.severity)} "
                        f"severity] · :gray-badge[{f.topic}]")
            st.write(f.detail)
            if f.evidence_quote:
                st.markdown(f"> “{f.evidence_quote}”")
            else:
                st.caption("No quote: the plan doesn't mention this.")
        if a.questions:
            st.markdown("**Questions for you**")
            st.markdown("\n".join(f"- {q}" for q in a.questions))


def agent_section(result: PipelineResult) -> None:
    st.header("Expert reviews", icon=":material/groups:", divider="gray")
    if not result.agents:
        st.info("No reviews were returned for this plan.")
        return
    show_disagreements(result.agents)
    for a in result.agents:
        agent_card(a)


def download_section(result: PipelineResult) -> None:
    """Offer the full report as a Markdown file."""
    st.header("Download your report", icon=":material/description:", divider="gray")
    try:
        report = build_markdown(result, st.session_state.assumptions or result.assumptions)
    except Exception:
        st.error("We couldn't build the report. Please click **Recalculate** and try again.")
        return
    st.write("Get everything above in one file: scenarios, reviews with evidence, "
             "the numbers used and the limitations.")
    st.download_button("Download report (Markdown)", data=report,
                       file_name="venturemind_report.md", mime="text/markdown",
                       type="primary")


DEFAULT_WHATIF_KEY = "marketing_budget_monthly"


def recalculate(changed_key: str, new_value: float) -> None:
    """Re-run the pipeline with one number changed; update every chart and card."""
    updated = [
        replace(a, value=new_value, source="assumption")
        if a.key == changed_key and a.value != new_value else a
        for a in st.session_state.assumptions
    ]
    try:
        with st.spinner("Recalculating your scenarios and reviews..."):
            result = run_pipeline(st.session_state.plan_text, updated)
    except Exception:
        st.error("We couldn't recalculate. Please click **Recalculate** again.")
        return
    st.session_state.assumptions = updated
    st.session_state.result = result
    st.session_state.last_change = changed_key
    st.rerun()


def whatif_panel() -> None:
    """Let the founder change one editable number and recalculate."""
    editable = [a for a in st.session_state.assumptions or [] if a.editable]
    if not editable:
        return
    with st.container(border=True):
        st.subheader("Try a what-if", anchor=False)
        st.caption("Change one number and click **Recalculate** to update every chart and card.")
        keys = [a.key for a in editable]
        by_key = {a.key: a for a in editable}
        start = keys.index(DEFAULT_WHATIF_KEY) if DEFAULT_WHATIF_KEY in keys else 0

        left, mid, right = st.columns([3, 2, 1], vertical_alignment="bottom")
        key = left.selectbox("Number to change", keys, index=start,
                             format_func=lambda k: f"{by_key[k].label} ({by_key[k].unit})")
        current = by_key[key]
        new_value = mid.number_input("New value", min_value=0.0,
                                     value=float(current.value), key=f"whatif_{key}")
        if right.button("Recalculate", type="primary", width="stretch"):
            recalculate(key, new_value)

        changed = st.session_state.get("last_change")
        if changed in by_key:
            a = by_key[changed]
            st.caption(f"Last recalculated with **{a.label} = {fmt(a.value, a.unit)}**.")
        if USE_EXAMPLES:
            st.caption(":material/info: Demo mode: results use example data, so they won't change yet.")


def dashboard_screen() -> None:
    result = st.session_state.get("result")
    if result is None:
        st.title("Your results")
        st.info("No results yet. Please confirm your numbers first.")
        st.button("← Check the numbers", on_click=go_to, args=("checkpoint",))
        return

    st.title("Your results")
    st.info(result.summary, icon=":material/lightbulb:")
    st.caption("Next: explore the three scenarios, read the expert reviews, "
               "then download your report at the bottom.")
    st.button("← Back to the numbers", on_click=go_to, args=("checkpoint",))
    whatif_panel()
    st.header("Scenarios", icon=":material/insights:", divider="gray")
    scenario_tabs(result)
    agent_section(result)
    download_section(result)


# ---------- main ----------

def sidebar() -> None:
    """Show where the founder is, plus a way to start again."""
    with st.sidebar:
        st.markdown("### :material/insights: VentureMind")
        st.caption("Business plan stress-test")
        stages = list(STEPS)
        current = stages.index(st.session_state.stage) if st.session_state.stage in stages else 0
        for i, label in enumerate(STEPS.values()):
            if i == current:  # active item: soft blue background + bold + icon
                st.markdown(f":blue-background[:material/radio_button_checked: **{label}**]")
            elif i < current:
                st.markdown(f":material/check_circle: {label}")
            else:
                st.caption(f":material/radio_button_unchecked: {label}")
        st.divider()
        if st.session_state.stage != "upload":
            st.button("Start over with a new plan", icon=":material/restart_alt:",
                      on_click=start_over, width="stretch")


def main() -> None:
    st.set_page_config(page_title="VentureMind", page_icon=":material/insights:", layout="wide")
    st.set_option("client.showErrorDetails", False)  # never show tracebacks
    load_secrets()
    init_state()
    sidebar()
    screens = {"upload": upload_screen, "checkpoint": checkpoint_screen,
               "dashboard": dashboard_screen}
    try:
        screens.get(st.session_state.stage, upload_screen)()
    except Exception:
        # Safety net: friendly message + one clear next step.
        st.error("Something went wrong on this page. Your plan is still saved. "
                 "Click **Start over with a new plan** in the sidebar, or reload the page.")


main()
