"""Streamlit dispatch desk: real Python previews, explicit demo-only confirmation."""

import hashlib
import html
import json
from dataclasses import asdict
from pathlib import Path

import streamlit as st

from dss5105.allocator import ObjectiveWeights
from dss5105.chat_ui import remember_tool_reply, render_chat, reset_preview
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, read_inbox
from dss5105.evaluate import PRESETS
from dss5105.intake import preview_conversation

STYLE = Path(__file__).with_name("assets") / "desk.css"
LABELS = {"lateness": "Lateness", "defects": "Defects", "hybrid": "Hybrid", "custom": "Custom weights"}
STATUS_LABELS = {
    "RECOMMEND": "Ready to review",
    "CLARIFY": "Clarification needed",
    "REFUSE_SUGGESTION": "Suggested workshop refused",
    "NEEDS_REVIEW": "Exception needs review",
    "NO_FEASIBLE_OPTION": "No feasible option",
    "DECLINE": "Data unavailable",
    "RECORDED_STATUS": "Recorded status only",
}
FLAGS = {
    "PAST_DEADLINE": "The requested deadline is already in the past.",
    "NO_ON_TIME_OPTION": "No permitted whole-batch option meets the date.",
    "SPLIT_NOT_IMPLEMENTED": "Split planning needs a separate review.",
    "SELECTED_OPTION_LATE": "The selected option misses the date.",
    "SUGGESTION_REFUSED": "The proposed workshop is not permitted.",
}


def clear_confirmation():
    for key in ("reviewing_preview", "confirmed_preview"):
        st.session_state.pop(key, None)


def bind_preview(result: dict) -> str:
    fingerprint = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    if st.session_state.get("preview_id") != fingerprint:
        clear_confirmation()
    st.session_state["preview_id"] = fingerprint
    st.session_state["preview"] = result
    return fingerprint


def request_card(envelope: dict, request: DispatchInput, desk: DispatchDesk):
    resolution = desk.resolve_order(request)
    tags = [envelope["request_id"]]
    if resolution["status"] == "RESOLVED":
        order = resolution["matches"][0]
        tags.extend([order["order_id"], order["customer"], order["product"], order["pieces"] + " pieces"])
        if request.date_uncertain or request.date_kind == "shipping":
            tags.append("Delivery date needs confirmation")
        else:
            tags.append("Delivery due " + (request.due_date or order["due_date"]))
    badges = "".join(f"<span>{html.escape(tag)}</span>" for tag in tags)
    st.html(
        '<section class="qr-message" aria-label="Original request">'
        f'<div class="qr-avatar">{html.escape(envelope["requester"][:1])}</div><div>'
        f'<div class="qr-meta"><strong>{html.escape(envelope["requester"])}</strong>'
        f" <span>{html.escape(envelope['time'])}</span></div>"
        f'<p>{html.escape(envelope["text"])}</p><div class="qr-tags">{badges}</div></div></section>'
    )


def settings(request: DispatchInput) -> ObjectiveWeights:
    with st.container(border=True, key="decision_settings"):
        st.caption("DECISION SETTINGS")
        st.subheader("Compare objectives")
        st.caption("Primary selection is pending. These presets are exploratory.")
        fixed = request.preference != "configured"
        mode = st.radio(
            "Objective",
            options=list(LABELS),
            format_func=LABELS.get,
            key="objective",
            label_visibility="collapsed",
        )
        if fixed:
            st.info(
                "This request takes priority: "
                + request.preference.replace("_", " ")
                + ". Global settings are retained but do not change its effective weights."
            )
        if mode == "custom":
            st.caption("Adjust relative weights. Every change recomputes the Python preview.")
            weights = {
                term: st.slider(
                    term.capitalize() + " weight",
                    min_value=0.0,
                    max_value=1.0,
                    value=value,
                    step=0.01,
                    key="weight_" + term,
                )
                for term, value in (("lateness", 1.0), ("defects", 0.05), ("cost", 0.1))
            }
            configured = ObjectiveWeights(**weights)
        else:
            configured = PRESETS[mode]
        st.caption("Eligibility and exclusions always apply. A hybrid need not lie between the other results.")
        return configured


def candidate_table(result: dict):
    rows = []
    selected_id = result["recommendation"] or result["alternative"]
    for candidate in result["candidates"]:
        estimate = candidate["estimate"]
        values = candidate["display"]
        selected = estimate["workshop_id"] == selected_id
        workshop = html.escape(candidate["name"])
        workshop_id = html.escape(estimate["workshop_id"])
        deadline = "Meets estimate" if candidate["meets_deadline"] else "Late " + values["lateness"]
        cells = "".join(
            f"<td>{html.escape(value)}</td>"
            for value in (
                values["turnaround"],
                values["cost"],
                values["defects"],
                deadline,
            )
        )
        rows.append(
            f'<tr class="{"qr-selected" if selected else ""}"><td><strong>{workshop}</strong>'
            f"<small>{workshop_id}{' / preview' if selected else ''}</small></td>{cells}</tr>"
        )
    st.html(
        '<div class="qr-table-scroll"><table class="qr-table"><caption class="qr-sr-only">'
        "Permitted workshop estimates on the same queue snapshot</caption><thead><tr>"
        '<th scope="col">Workshop</th><th scope="col">Expected days</th><th scope="col">Cost units</th>'
        '<th scope="col">Defect risk</th><th scope="col">Deadline</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def confirmation(result: dict, preview_id: str, chosen: dict | None):
    ready = result["status"] == "RECOMMEND"
    if st.button(
        "Review confirmation" if ready else "Resolve before confirmation",
        type="primary",
        key="review_confirmation",
        disabled=not ready,
    ):
        st.session_state["reviewing_preview"] = preview_id
        st.session_state.pop("confirmed_preview", None)
    if ready and st.session_state.get("reviewing_preview") == preview_id:
        with st.container(border=True, key="confirmation_panel"):
            st.subheader("Review the allocation")
            st.write(
                f"{result['order']['order_id']} to {chosen['name']}. "
                f"Estimated delivery: {chosen['display']['eta']}. "
                f"Cost: {chosen['display']['cost']} source units."
            )
            st.caption("Demo only. No allocation is saved, no queue changes, and no workshop is contacted.")
            approve, cancel = st.columns(2)
            if approve.button("Confirm demo only", key="confirm_demo", type="primary"):
                st.session_state["confirmed_preview"] = preview_id
                st.session_state.pop("reviewing_preview", None)
                st.rerun()
            if cancel.button("Back to comparison", key="cancel_confirmation"):
                st.session_state.pop("reviewing_preview", None)
                st.rerun()
    if ready and st.session_state.get("confirmed_preview") == preview_id:
        st.success("Demo confirmation recorded in this session only. No allocation was saved or capacity reserved.")


def render_decision(result: dict, preview_id: str):
    chosen_id = result["recommendation"] or result["alternative"]
    chosen = next((row for row in result["candidates"] if row["estimate"]["workshop_id"] == chosen_id), None)
    with st.container(border=True, key="decision"):
        st.caption("TOOL-BACKED DECISION")
        if result["status"] == "RECOMMEND":
            st.success(STATUS_LABELS[result["status"]])
        elif result["status"] in ("CLARIFY", "RECORDED_STATUS"):
            st.info(STATUS_LABELS[result["status"]])
        else:
            st.warning(STATUS_LABELS[result["status"]])
        prefix = (
            "Alternative: "
            if result["alternative"]
            else "For discussion: "
            if result["status"] == "NEEDS_REVIEW"
            else ""
        )
        st.subheader(prefix + chosen["name"] if chosen else STATUS_LABELS[result["status"]])
        st.write(result["message"])
        if chosen:
            delivery, cost, defects = st.columns(3)
            delivery.metric("Expected turnaround", chosen["display"]["turnaround"])
            delivery.caption("ETA " + chosen["display"]["eta"])
            cost.metric("Subcontracting cost", chosen["display"]["cost"])
            cost.caption("Source cost units")
            defects.metric("Batch defect risk", chosen["display"]["defects"])
            defects.caption("Workshop profile probability")
        if result["status"] == "RECORDED_STATUS":
            st.write("Recorded status: " + result["order"]["status"])
            st.write("Last recorded activity: " + result["order"]["last_activity_date"])
        if result["flags"]:
            st.warning(" ".join(FLAGS[flag] for flag in result["flags"]))
        confirmation(result, preview_id, chosen)
    with st.container(border=True, key="comparison"):
        st.subheader("Candidate workshops")
        st.caption("Same order. Same queue snapshot. Ranked by effective configuration.")
        if result["candidates"]:
            candidate_table(result)
        else:
            st.info(
                "Resolve the request before comparing workshops."
                if result["status"] == "CLARIFY"
                else "No candidate estimate is available for this request."
            )
        if result["excluded"]:
            with st.expander("Why other workshops are excluded", expanded=True):
                for row in result["excluded"]:
                    st.markdown("**" + row["name"] + "**")
                    for reason in row["reasons"]:
                        st.write(reason)
        if result.get("resolution", {}).get("status") == "AMBIGUOUS" and result["resolution"]["matches"]:
            with st.expander("Matching recorded orders"):
                st.dataframe(
                    [
                        {key: row[key] for key in ("order_id", "customer", "product", "pieces", "due_date")}
                        for row in result["resolution"]["matches"]
                    ],
                    hide_index=True,
                )


def main():
    st.set_page_config(
        page_title="SweaterCo | Quick-Response Dispatch Desk", layout="wide", initial_sidebar_state="expanded"
    )
    st.html("<style>" + STYLE.read_text() + "</style>")
    with st.sidebar:
        st.html('<div class="qr-brand"><span>S</span>SweaterCo</div>')
        st.caption("QUICK-RESPONSE SUBCONTRACTING DESK")
        source = st.radio(
            "Input source",
            options=["examples", "chat"],
            key="input_source",
            format_func=lambda value: {"examples": "Supplied examples (offline)", "chat": "Natural language"}[value],
        )
    if st.session_state.get("active_input_source") != source:
        reset_preview()
        st.session_state["active_input_source"] = source
    try:
        inbox = {row["request_id"]: row for row in read_inbox()}
        if source == "examples":
            fixture_path = ROOT / "examples" / "dispatch_inputs.json"
            fixture_bytes = fixture_path.read_bytes()
            fixtures = json.loads(fixture_bytes)
            if set(fixtures) != set(inbox):
                raise ValueError("Draft interpretations must match the supplied inbox")
        desk = DispatchDesk()
    except (OSError, ValueError, TypeError, KeyError) as error:
        clear_confirmation()
        st.session_state.pop("preview", None)
        st.error("Could not load dispatch data: " + str(error))
        st.stop()
    if source == "examples":
        with st.sidebar:
            st.subheader("Inbox")
            default = list(inbox).index("R25") if "R25" in inbox else 0
            request_id = st.radio(
                "Select a request",
                options=list(inbox),
                index=default,
                key="request_id",
                format_func=lambda key: f"{key} / {inbox[key]['requester']} / {inbox[key]['time']}",
                label_visibility="collapsed",
            )
            st.caption("Each request starts from the same queue snapshot. Previews do not reserve capacity.")
    st.html('<div class="qr-eyebrow">SWEATERCO / DISPATCH DESK</div>')
    st.title("The right workshop. A decision you can explain.")
    st.caption("Understand the request, compare the options, keep the evidence.")
    conversation = None
    if source == "chat":
        conversation = render_chat(desk, inbox)
        request_id = "CHAT"
    else:
        st.info(
            "Demo workspace: real Python estimates, draft request interpretations. "
            "No model calls or actual allocations."
        )
    try:
        request = conversation.request if conversation else DispatchInput(**fixtures[request_id])
        if conversation is None:
            envelope = inbox[request_id]
            request_card(envelope, request, desk)
        left, right = st.columns([3, 1], gap="large")
        with right:
            weights = settings(request)
        if conversation:
            result = preview_conversation(conversation, desk, weights)
            remember_tool_reply(conversation, result)
        else:
            result = desk.preview(envelope, request, weights)
            result["interpretation_source"] = "Hand-authored development fixture; not model extraction or gold labels."
            result["fixture_sha256"] = hashlib.sha256(fixture_bytes).hexdigest()
        preview_id = bind_preview(result)
    except (ValueError, TypeError, KeyError) as error:
        clear_confirmation()
        st.session_state.pop("preview", None)
        st.error("Cannot generate a preview: " + str(error))
        st.caption("Correct the configuration before reviewing a decision.")
        st.stop()
    with right:
        with st.expander("Effective weights and scales", expanded=True):
            st.json({"weights": result["effective_weights"], "scales": result["scales"]}, expanded=True)
            st.caption("Weights are relative preferences, not probabilities. Scales are the existing reference units.")
        st.caption("Snapshot " + result["snapshot"]["as_of"])
    with left:
        render_decision(result, preview_id)
    evidence = json.dumps(result, ensure_ascii=True, indent=2)
    st.download_button(
        "Export tool evidence",
        data=evidence,
        file_name=f"{request_id}-preview.json",
        mime="application/json",
        key="download_evidence",
    )
    with st.expander("Inspect structured input and numerical evidence"):
        st.caption(result["interpretation_source"])
        st.json(result)
    with st.expander("What is connected in this version?"):
        st.write("Inbox selection, objective presets, live custom weights, workshop comparison, and evidence export.")
        st.write("Natural-language extraction and follow-up clarification are connected through the configured model.")
        st.write("Live extraction quality is not yet evaluated. Durable allocation records remain a future increment.")
        st.caption("Current configured weights: " + json.dumps(asdict(weights)))
    st.caption(
        "Delivery estimates include expected rework. They do not guarantee delivery or predict unknown closures."
    )
