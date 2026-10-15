"""Streamlit dispatch desk: a chat-first answer view, an Objectives panel and an explicit saved local plan."""

import hashlib
import html
import json
import sqlite3
from pathlib import Path
from uuid import uuid4

import streamlit as st

from dss5105.chat_ui import (
    CUSTOM_DEFAULTS,
    LABELS,
    DeskContext,
    clear_review,
    history,
    open_entry,
    process_pending,
    queue,
    read_weights,
    render_answer,
    render_composer,
    render_working_panel,
    reset_all,
    shown_example,
)
from dss5105.dispatch import ROOT, DispatchDesk, read_inbox
from dss5105.records import AllocationStore

STYLE = Path(__file__).with_name("assets") / "desk.css"
OBJECTIVE_NOTES = {
    "lateness": "Lateness (primary objective)",
    "defects": "Defect (secondary objective)",
    "hybrid": "Hybrid (hybrid objective with fixed weights)",
    "custom": "Custom (customizable weights for objectives)",
}
# One supplied example per request kind in the course data dictionary: (request id, header, description, tone).
SCENARIOS = (
    ("R07", "Feasible Request", "Recommends an available workshop with an estimated delivery date.", "ok"),
    (
        "R30",
        "Unfeasible Deadline",
        "Flags that no workshop can meet the deadline and offers the earliest available date.",
        "bad",
    ),
    ("R25", "Specific Constraints", "Applies buyer preferences or restrictions and records who set them.", "ok"),
    ("R01", "Ambiguous Request", "Detects multiple matching orders and prompts for clarification.", "ask"),
    (
        "R05",
        "Incomplete Information",
        "Identifies missing details and asks for the required order number or date.",
        "ask",
    ),
    (
        "R08",
        "Invalid Workshop Request",
        "Explains why the requested workshop cannot take the order and suggests alternatives.",
        "warn",
    ),
    (
        "R02",
        "Missing Historical Data",
        "Clearly states when required information isn't in the database without guessing.",
        "limit",
    ),
)


def objectives_panel() -> str:
    """Objective choice and workspace switch, drawn inside the Objectives popover. Returns the workspace."""
    st.subheader("Objectives")
    st.caption("Primary selection is pending. These presets are exploratory.")
    mode = st.radio(
        "Objective",
        options=list(LABELS),
        format_func=OBJECTIVE_NOTES.get,
        key="objective",
        label_visibility="collapsed",
    )
    if mode == "custom":
        st.caption("Adjust relative weights. They apply to the next request you send.")
        for term, value in CUSTOM_DEFAULTS.items():
            st.slider(term.capitalize() + " weight", 0.0, 1.0, value, 0.01, key="weight_" + term)
        if read_weights()[0] is None:
            st.error("Every weight is zero. Set at least one weight above zero before sending a request.")
    st.caption("Eligibility and exclusions always apply. A hybrid need not lie between the other results.")
    st.divider()
    st.subheader("Where do saved allocations go?")
    return st.radio(
        "Workspace",
        options=["independent", "saved"],
        key="workspace_mode",
        format_func=lambda value: {"independent": "Preview only", "saved": "Saved local plan"}[value],
        horizontal=True,
    )


def saved_plan_panel(store: AllocationStore | None):
    st.subheader("Saved allocations")
    if store is None:
        st.caption("Preview only is on. Choose Saved local plan in Objectives to record allocations.")
        return
    try:
        records = store.records()
    except (sqlite3.Error, OSError):
        st.error("Could not read saved records. Refresh the plan before continuing.")
        return
    if not records:
        st.write("Nothing has been saved yet.")
        return
    st.dataframe(
        [
            {
                key: record[key]
                for key in ("allocation_id", "order_id", "workshop_name", "confirmed_by", "created_at_utc")
            }
            for record in records
        ],
        hide_index=True,
    )
    st.download_button(
        "Export saved allocation records",
        json.dumps(records, indent=2),
        file_name="allocation-records.json",
        mime="application/json",
        key="download_allocations",
    )


def start_screen(ctx: DeskContext):
    st.html(
        '<div class="qr-start"><div class="qr-eyebrow">Start here</div>'
        "<h1>Which order needs a workshop today?</h1></div>"
    )
    with st.container():  # inside a container the box stays inline instead of docking to the window bottom
        render_composer(start=True)
    st.html('<div class="qr-kinds">Try an example scenario</div>')
    cards = [item for item in SCENARIOS if item[0] in ctx.inbox]
    cards.append(("", "View All Examples", "Browse the full list of test scenarios.", "more"))
    for start in range(0, len(cards), 4):
        for column, (request_id, header, description, tone) in zip(
            st.columns(4), cards[start : start + 4], strict=False
        ):
            quote = (
                f'<p class="qr-kind-quote">&ldquo;{html.escape(ctx.inbox[request_id]["text"])}&rdquo;</p>'
                if request_id
                else ""
            )
            with column, st.container(border=True, key=f"card_{tone}_{request_id or 'all'}"):
                st.html(
                    f'<span class="qr-kind qr-{tone}">{html.escape(header)}</span>'
                    f'<p class="qr-kind-desc">{html.escape(description)}</p>{quote}'
                )
                if request_id:
                    st.button(
                        "Run this example",
                        key=f"scenario_{request_id}",
                        on_click=queue,
                        args=({"kind": "example", "request_id": request_id},),
                        width="stretch",
                    )
                else:
                    st.html('<a class="qr-link" href="#examples">Explore all examples &darr;</a>')


def examples_section(ctx: DeskContext):
    shown = shown_example()
    with st.container(key="examples_area"):
        st.html('<div id="examples" class="qr-examples-head"><h2>Examples</h2></div>')
        st.caption(
            "Click an example to send it to the desk, as if it arrived in the group chat. "
            "Examples run offline with no model call. Nothing is allocated until you save."
        )
        ids = list(ctx.inbox)
        for start in range(0, len(ids), 4):
            for column, request_id in zip(st.columns(4), ids[start : start + 4], strict=False):
                row = ctx.inbox[request_id]
                column.button(
                    ("✓ " if request_id == shown else "") + f"{request_id} / {row['requester']} / {row['time']}",
                    key=f"example_{request_id}",
                    type="primary" if request_id == shown else "secondary",
                    on_click=queue,
                    args=({"kind": "example", "request_id": request_id},),
                    width="stretch",
                )


def scroll_to_top():
    """After a request is sent, bring the answer into view.

    The nonce re-runs the script on every send, and the function wrapper keeps a repeated run from
    redeclaring a global (a bare `const` would throw the second time).
    """
    if st.session_state.pop("scroll_top", False):
        st.html(
            "<script>/* " + uuid4().hex + " */ (function () {"
            " const main = document.querySelector('[data-testid=\"stMain\"]');"
            " if (main) main.scrollTo({top: 0, behavior: 'smooth'});"
            " window.scrollTo({top: 0, behavior: 'smooth'}); })();</script>",
            unsafe_allow_javascript=True,
        )


def main():
    st.set_page_config(
        page_title="SweaterCo | Quick-Response Dispatch Desk", layout="wide", initial_sidebar_state="collapsed"
    )
    st.html("<style>" + STYLE.read_text() + "</style>")
    top = st.container(key="topbar")
    brand, snapshot, objective_box, plan_box, clear_box = top.columns(
        [3.2, 2.4, 3.2, 1.4, 1.4], vertical_alignment="center"
    )
    brand.html(
        '<div class="qr-brand"><span>S</span><div>SweaterCo'
        "<small>QUICK-RESPONSE SUBCONTRACTING DESK</small></div></div>"
    )
    mode = st.session_state.get("objective", "lateness")
    with objective_box:
        objectives = st.popover(
            "⚙ Objective: " + LABELS[mode], key="objective_pop", help="Choose the objective", width="stretch"
        )
    with objectives:
        workspace = objectives_panel()
    with plan_box:
        plan = st.popover("Saved plan", key="plan_pop", width="stretch")
    clear_box.button("Clear chat", key="clear_chat", on_click=reset_all, width="stretch")
    if st.session_state.get("active_workspace") != workspace:
        clear_review()
        st.session_state["active_workspace"] = workspace
    try:
        inbox = {row["request_id"]: row for row in read_inbox()}
        fixture_bytes = (ROOT / "examples" / "dispatch_inputs.json").read_bytes()
        fixtures = json.loads(fixture_bytes)
        if set(fixtures) != set(inbox):
            raise ValueError("Draft interpretations must match the supplied inbox")
        desk = DispatchDesk()
        store = AllocationStore() if workspace == "saved" else None
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error) as error:
        clear_review()
        st.error("Could not load dispatch data: " + str(error))
        st.stop()
    snapshot.html(
        '<div class="qr-snap">Queue snapshot <b>'
        + html.escape(desk.as_of.isoformat())
        + "</b><br>"
        + ("Saved local plan: confirmed allocations are recorded" if store else "Preview only: no capacity reserved")
        + "</div>"
    )
    with plan:
        saved_plan_panel(store)
    weights, weights_error = read_weights()
    ctx = DeskContext(desk, inbox, fixtures, hashlib.sha256(fixture_bytes).hexdigest(), weights, weights_error, store)
    process_pending(ctx)
    if history() or "pending_turn" in st.session_state or "send_error" in st.session_state:
        opened = open_entry()
        left, right = st.columns([7, 11], gap="medium") if opened else (st.container(), None)
        with left, st.container(key="answer_compact" if opened else "answer_full"):
            render_answer(ctx)
            with st.container():
                render_composer(start=False)
        if opened:
            with right:
                render_working_panel(opened)
    else:
        start_screen(ctx)
    examples_section(ctx)
    st.caption(
        "Planning snapshot: " + desk.as_of.isoformat() + ". Relative dates use this snapshot, not the real clock. "
        "Delivery estimates include expected rework. They do not guarantee delivery or predict unknown closures."
    )
    scroll_to_top()
