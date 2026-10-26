"""Streamlit dispatch desk with independent previews and an explicit saved local plan."""

import hashlib
import html
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

import altair as alt
import streamlit as st

from dss5105.allocator import ObjectiveWeights
from dss5105.chat_ui import remember_tool_reply, render_chat, reset_preview
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, read_inbox, ship_date_is_due_date
from dss5105.evaluate import DEFAULT_PRESET, PRESETS
from dss5105.intake import preview_conversation
from dss5105.records import AllocationError, AllocationStore
from dss5105.replies import STATUS_LABELS
from dss5105.workshop_ui import render_workshops

STYLE = Path(__file__).with_name("assets") / "desk.css"
LABELS = {
    "hybrid": "Recommended: on time first, then quality",
    "lateness": "Prioritise on-time delivery",
    "defects": "Prioritise quality",
    "fairness": "Spread the work fairly",
    "robustness": "Absorb a workshop stoppage",
    "custom": "Set relative priorities",
}
# Custom sliders: term, label, help. Defaults start from the recommended preset.
SLIDERS = (
    ("lateness", "On time (lateness)", "Late batches and late days. Our primary objective."),
    ("defects", "Quality (defects)", "Expected defective pieces. Our secondary objective."),
    ("fairness", "Fair share (fairness)", "Spread booked pieces; uses this plan's saved bookings."),
    ("robustness", "Resilience (robustness)", "Slack to absorb a two-week workshop stoppage."),
    ("cost", "Cost", "Cheaper workshops. A measured tradeoff, not a course objective."),
)
INK = "#1d1b18"
MUTED = "#6b665d"
GRID = "#ece6db"
CARD = "#ffffff"
# Delivery segments in timeline order: estimate field (None = expected rework), display key, label, color.
# The four colors pass the dataviz palette checks on the paper surface and avoid the status green and red.
SEGMENTS = (
    ("queue_days", "queue", "Queue wait", "#a8742f"),
    ("process_days", "processing", "Processing", "#2f6db5"),
    ("transport_days", "transport", "Transport", "#14a08c"),
    (None, "expected_rework", "Expected rework", "#8b55b0"),
)
FLAGS = {
    "PAST_DEADLINE": "The requested deadline is already in the past.",
    "NO_ON_TIME_OPTION": "No permitted whole-batch option meets the date.",
    "SPLIT_REVIEW": "A split was requested. Its estimate is shown; split plans cannot be saved yet.",
    "SELECTED_OPTION_LATE": "The selected option misses the date.",
    "SUGGESTION_REFUSED": "The proposed workshop is not permitted.",
}


def clear_confirmation():
    for key in ("reviewing_preview", "confirmed_preview", "confirmation_key"):
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
        if request.date_uncertain or (request.date_kind == "shipping" and not ship_date_is_due_date(request, order)):
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
        st.caption("ALLOCATION PRIORITIES")
        st.subheader("Compare tradeoffs")
        st.caption("Primary objective: minimise lateness. Secondary: minimise defects.")
        fixed = request.preference != "configured"
        mode = st.radio(
            "Objective",
            options=list(LABELS),
            index=list(LABELS).index(DEFAULT_PRESET),
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
            start = asdict(PRESETS[DEFAULT_PRESET])
            weights = {
                term: st.slider(
                    label, min_value=0.0, max_value=1.0, value=start[term], step=0.01, key="weight_" + term, help=hint
                )
                for term, label, hint in SLIDERS
            }
            weights["deadline_buffer_days"] = st.slider(
                "Safety buffer (days)",
                min_value=0.0,
                max_value=10.0,
                value=start["deadline_buffer_days"],
                step=0.5,
                key="weight_buffer",
                help="Prefer workshops that finish this many days before the deadline.",
            )
            reserve = st.toggle(
                "Protect scarce capacity",
                value=start["capacity_reservation"] > 0,
                key="weight_reservation",
                help="Keep workshops that also make accessories free when a tops-only shop meets the date.",
            )
            on_time_first = st.toggle(
                "On-time first",
                value=start["deadline_miss_days"] > 0,
                key="weight_on_time_first",
                help="Missing the date costs a week of lateness, so an on-time workshop beats a late one.",
            )
            configured = ObjectiveWeights(
                **weights,
                capacity_reservation=1.0 if reserve else 0.0,
                deadline_miss_days=7.0 if on_time_first else 0.0,
            )
        else:
            configured = PRESETS[mode]
        st.caption("Workshop restrictions always apply. Priorities change the ranking of permitted options.")
        return configured


def candidate_chart(result: dict):
    """Where each candidate's days go: the tool's own estimate segments, stacked against the deadline.

    Segment lengths are estimate fields; tooltips and end labels reuse the tool's formatted strings.
    """
    rows, ends = [], []
    for candidate in result["candidates"]:
        estimate, display = candidate["estimate"], candidate["display"]
        for index, (field, key, label, _) in enumerate(SEGMENTS):
            days = estimate[field] if field else estimate["expected_turnaround_days"] - estimate["turnaround_days"]
            rows.append(
                {
                    "name": candidate["name"],
                    "segment": label,
                    "order": index,
                    "days": days,
                    "shown": display[key],
                    "turnaround": display["turnaround"],
                    "eta": display["eta"],
                }
            )
        late = "" if candidate["meets_deadline"] else ", late " + display["lateness"]
        ends.append(
            {
                "name": candidate["name"],
                "days": estimate["expected_turnaround_days"],
                "label": display["turnaround"] + late,
            }
        )
    order = [row["name"] for row in ends]
    axis = alt.Axis(
        grid=True, gridColor=GRID, gridWidth=1, domain=False, tickSize=0, labelColor=MUTED, titleColor=MUTED
    )
    y = alt.Y(
        "name:N", sort=order, title=None, axis=alt.Axis(domain=False, tickSize=0, labelColor=INK, labelFontSize=12)
    )
    bars = (
        alt.Chart(alt.Data(values=rows))
        .mark_bar(size=18, stroke=CARD, strokeWidth=2)
        .encode(
            y=y,
            x=alt.X("days:Q", stack="zero", title="Expected days to delivery", axis=axis),
            color=alt.Color(
                "segment:N",
                scale=alt.Scale(domain=[s[2] for s in SEGMENTS], range=[s[3] for s in SEGMENTS]),
                legend=alt.Legend(title=None, orient="top", labelColor=INK, symbolType="square"),
            ),
            order=alt.Order("order:Q"),
            tooltip=[
                alt.Tooltip("name:N", title="Workshop"),
                alt.Tooltip("segment:N", title="Segment"),
                alt.Tooltip("shown:N", title="Days"),
                alt.Tooltip("turnaround:N", title="Expected total"),
                alt.Tooltip("eta:N", title="ETA"),
            ],
        )
    )
    labels = (
        alt.Chart(alt.Data(values=ends))
        .mark_text(align="left", dx=8, color=INK, fontSize=11.5)
        .encode(y=alt.Y("name:N", sort=order), x="days:Q", text="label:N")
    )
    layers = [bars]
    available = result["candidates"][0]["estimate"]["available_days"]
    if available >= 0:
        marker = alt.Data(values=[{"available": available, "label": "Deadline"}])
        layers.append(alt.Chart(marker).mark_rule(size=1.5, color=INK, strokeDash=[4, 3]).encode(x="available:Q"))
        layers.append(
            alt.Chart(marker)
            .mark_text(align="left", dx=6, dy=-2, baseline="bottom", color=INK, fontSize=11, fontWeight=600)
            .encode(x="available:Q", text="label:N", y=alt.value(0))
        )
    layers.append(labels)  # last, so the deadline rule never draws over a value
    chart = (
        alt.layer(*layers)
        .properties(height=alt.Step(34), background=CARD, padding={"top": 14, "right": 90})
        .configure_view(stroke=None)
    )
    st.altair_chart(chart, width="stretch")


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
                values["queue"],
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
        '<th scope="col">Workshop</th><th scope="col">Queue</th>'
        '<th scope="col">Expected days</th><th scope="col">Cost units</th>'
        '<th scope="col">Defect risk</th><th scope="col">Deadline</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def baseline_table(result: dict):
    """One table: this desk's effective configuration against the shared reference policies."""
    chosen_id = result["recommendation"] or result["alternative"]
    chosen = next((row for row in result["candidates"] if row["estimate"]["workshop_id"] == chosen_id), None)
    rows = []
    if chosen is not None:
        rows.append(
            {
                "label": "This desk (effective weights)",
                "name": chosen["name"],
                "display": chosen["display"],
                "meets_deadline": chosen["meets_deadline"],
                "respects_exclusions": True,
                "selected": True,
            }
        )
    rows.extend({**row, "selected": False} for row in result["baselines"])
    body = ""
    for row in rows:
        values = row["display"]
        deadline = "Meets estimate" if row["meets_deadline"] else "Late " + values["lateness"]
        constraint = "Respected" if row["respects_exclusions"] else "Ignores an exclusion"
        cells = "".join(
            f"<td>{html.escape(value)}</td>"
            for value in (values["turnaround"], values["cost"], values["defects"], deadline, constraint)
        )
        body += (
            f'<tr class="{"qr-selected" if row["selected"] else ""}">'
            f"<td><strong>{html.escape(row['label'])}</strong>"
            f"<small>{html.escape(row['name'])}</small></td>{cells}</tr>"
        )
    st.html(
        '<div class="qr-table-scroll"><table class="qr-table"><caption class="qr-sr-only">'
        "This desk compared with the shared reference policies on the same order and queue snapshot"
        '</caption><thead><tr><th scope="col">Policy</th><th scope="col">Expected days</th>'
        '<th scope="col">Cost units</th><th scope="col">Defect risk</th><th scope="col">Deadline</th>'
        '<th scope="col">Exclusions</th></tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def confirmation(result: dict, preview_id: str, chosen: dict | None, store: AllocationStore | None = None):
    ready = result["status"] == "RECOMMEND" and (store is None or result["commit_allowed"])
    if st.button(
        "Review confirmation" if ready else "Resolve before confirmation",
        type="primary",
        key="review_confirmation",
        disabled=not ready,
    ):
        st.session_state["reviewing_preview"] = preview_id
        st.session_state["confirmation_key"] = str(uuid4())
        st.session_state.pop("confirmed_preview", None)
    if ready and st.session_state.get("reviewing_preview") == preview_id:
        with st.container(border=True, key="confirmation_panel"):
            st.subheader("Review the allocation")
            st.write(
                f"{result['order']['order_id']} to {chosen['name']}. "
                f"Estimated delivery: {chosen['display']['eta']}. "
                f"Cost: {chosen['display']['cost']} source units."
            )
            if store is not None:
                st.caption(
                    "Save this allocation and reserve capacity in the local plan. No workshop will be contacted."
                )
                actor = st.text_input("Confirming dispatcher", key="confirmed_by")
            else:
                st.caption("Demo only. No allocation is saved, no queue changes, and no workshop is contacted.")
            approve, cancel = st.columns(2)
            if store is not None and approve.button(
                "Confirm and save allocation", key="confirm_allocation", type="primary", disabled=not actor.strip()
            ):
                try:
                    receipt = store.commit_allocation(
                        result, actor, st.session_state["confirmation_key"], confirmed=True
                    )
                except (AllocationError, sqlite3.Error, OSError) as error:
                    st.error(
                        str(error)
                        if isinstance(error, AllocationError)
                        else "Save failed. Refresh the plan before retrying."
                    )
                else:
                    st.session_state["allocation_receipt"] = receipt
                    clear_confirmation()
                    st.rerun()
            if store is None and approve.button("Confirm demo only", key="confirm_demo", type="primary"):
                st.session_state["confirmed_preview"] = preview_id
                st.session_state.pop("reviewing_preview", None)
                st.session_state.pop("confirmation_key", None)
                st.rerun()
            if cancel.button("Back to comparison", key="cancel_confirmation"):
                clear_confirmation()
                st.rerun()
    if ready and st.session_state.get("confirmed_preview") == preview_id:
        st.success("Demo confirmation recorded in this session only. No allocation was saved or capacity reserved.")


def render_decision(result: dict, preview_id: str, store: AllocationStore | None = None):
    chosen_id = result["recommendation"] or result["alternative"]
    chosen = next((row for row in result["candidates"] if row["estimate"]["workshop_id"] == chosen_id), None)
    with st.container(border=True, key="decision"):
        st.caption("RECOMMENDATION AND APPROVAL")
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
        if chosen and result.get("decision_basis"):
            st.html(
                '<ul class="qr-reasons" aria-label="Why this workshop">'
                + "".join(f"<li>{html.escape(reason)}</li>" for reason in result["decision_basis"]["reasons"])
                + "</ul>"
            )
        st.write(result["message"])
        if result.get("deadline_note"):
            st.caption(result["deadline_note"])
        for option in result["review_options"]:
            st.write(option)
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
        confirmation(result, preview_id, chosen, store)
    with st.container(border=True, key="comparison"):
        st.subheader("Candidate workshops")
        st.caption(result["assumption"])
        if result["candidates"]:
            st.caption(
                "Each bar splits the delivery estimate into queue wait, processing, transport and expected rework. "
                "Compare it with cost and quality risk before approving the allocation."
            )
            candidate_chart(result)
            candidate_table(result)
            with st.expander("How delivery estimates are built"):
                st.caption("Expected turnaround includes queue, processing, transport and expected rework.")
                st.dataframe(
                    [
                        {
                            "Workshop": row["name"],
                            **{
                                key: row["display"][key]
                                for key in ("queue", "processing", "transport", "expected_rework", "eta")
                            },
                        }
                        for row in result["candidates"]
                    ],
                    hide_index=True,
                )
        if result["split_option"]:
            with st.expander("Two-workshop split estimate", expanded=True):
                st.caption(
                    "Each part uses the same estimate and eligibility rule. The course simulator does not model "
                    "splits, so this is chat-layer evidence only."
                )
                st.dataframe(
                    [
                        {
                            "Workshop": part["name"],
                            "Pieces": str(part["pieces"]),
                            **{key: part["display"][key] for key in ("queue", "turnaround", "eta", "cost")},
                        }
                        for part in result["split_option"]["parts"]
                    ],
                    hide_index=True,
                )
        if not result["candidates"]:
            st.info(
                "Resolve the request before comparing workshops."
                if result["status"] == "CLARIFY"
                else "No candidate estimate is available for this request."
            )
        if result["baselines"]:
            st.subheader("Compared with the reference policies")
            st.caption(
                "Same order, same queue snapshot. Reference policies see eligibility only, "
                "so they can pick a workshop this desk has been told to avoid."
            )
            baseline_table(result)
        if result["excluded"]:
            with st.expander("Why other workshops are excluded", expanded=True):
                st.html(
                    '<table class="qr-table qr-excluded"><caption class="qr-sr-only">Excluded workshops</caption>'
                    + "".join(
                        f"<tr><td><strong>{html.escape(row['name'])}</strong></td>"
                        f"<td>{html.escape(' '.join(row['reasons']))}</td></tr>"
                        for row in result["excluded"]
                    )
                    + "</table>"
                )
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
        st.html(
            '<div class="qr-brand"><span class="qr-wordmark">SWEATERCO</span>'
            '<span class="qr-tagline">Quick-response subcontracting desk</span></div><div class="qr-rule"></div>'
        )
        workspace = st.radio(
            "Workspace",
            options=["independent", "saved"],
            key="workspace_mode",
            format_func=lambda value: {"independent": "Independent previews", "saved": "Saved local plan"}[value],
        )
        source = st.radio(
            "Input source",
            options=["chat", "examples", "workshops"],
            key="input_source",
            format_func=lambda value: {
                "chat": "Chat request (live model)",
                "examples": "Inbox examples (offline)",
                "workshops": "Workshop register (offline)",
            }[value],
        )
    if st.session_state.get("active_input_source") != (workspace, source):
        reset_preview()
        st.session_state["active_input_source"] = (workspace, source)
    store = None
    try:
        inbox = {row["request_id"]: row for row in read_inbox()}
        if source == "examples":
            fixture_path = ROOT / "examples" / "dispatch_inputs.json"
            fixture_bytes = fixture_path.read_bytes()
            fixtures = json.loads(fixture_bytes)
            if set(fixtures) != set(inbox):
                raise ValueError("Draft interpretations must match the supplied inbox")
        desk = DispatchDesk()
        if workspace == "saved":
            store = AllocationStore()
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error) as error:
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
            st.caption(
                "Previews use saved planning queues. Only confirmation reserves capacity."
                if store is not None
                else "Each request starts from the same queue snapshot. Previews do not reserve capacity."
            )
    st.html(
        '<div class="qr-eyebrow">SweaterCo / Dispatch desk / Planning snapshot ' + desk.as_of.isoformat() + "</div>"
    )
    st.title("Who should make this batch?")
    st.caption("Compare permitted workshops on delivery, cost and quality, then approve with a decision record.")
    if store is not None:
        st.info("Saved local plan: confirmed allocations persist across sessions and update planning queues.")
        if receipt := st.session_state.get("allocation_receipt"):
            st.success(
                "Most recent saved allocation: "
                + receipt["order_id"]
                + " to "
                + receipt["workshop_name"]
                + ". "
                + receipt["effect"]
            )
        try:
            records = store.records()
        except (sqlite3.Error, OSError):
            st.error("Could not read saved records. Refresh the plan before continuing.")
            st.stop()
        with st.expander("Saved allocation records"):
            if records:
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
            else:
                st.write("No allocations have been saved in this plan.")
    if source == "workshops":
        clear_confirmation()
        try:
            render_workshops(desk, store)
        except (ValueError, TypeError, KeyError, sqlite3.Error, OSError) as error:
            st.error("Could not check workshop capacity: " + str(error))
        return
    conversation = None
    reply_slot = None
    if source == "chat":
        conversation, reply_slot = render_chat(desk, inbox, saved_plan=store is not None)
        request_id = "CHAT"
    else:
        st.info(
            "Inbox examples use draft request interpretations and real Python estimates. No model calls. "
            + ("Confirmation saves to the local plan." if store is not None else "No allocations are saved.")
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
        else:
            result = desk.preview(envelope, request, weights)
            result["interpretation_source"] = "Hand-authored development fixture; not model extraction or gold labels."
            result["fixture_sha256"] = hashlib.sha256(fixture_bytes).hexdigest()
        if store is not None:
            saved_preview = store.preview(result["request"], request, weights)
            for key in ("conversation", "interpretation_source", "fixture_sha256"):
                if key in result:
                    saved_preview[key] = result[key]
            result = saved_preview
        if conversation:
            remember_tool_reply(conversation, result, reply_slot)
        preview_id = bind_preview(result)
    except (ValueError, TypeError, KeyError, sqlite3.Error, OSError) as error:
        clear_confirmation()
        st.session_state.pop("preview", None)
        st.error("Cannot generate a preview: " + str(error))
        st.caption("Correct the configuration before reviewing a decision.")
        st.stop()
    with right:
        with st.expander("Advanced scoring details", expanded=False):
            st.json({"weights": result["effective_weights"], "scales": result["scales"]}, expanded=True)
            st.caption("Weights are relative preferences, not probabilities. Scales are the existing reference units.")
        st.caption("Snapshot " + result["snapshot"]["as_of"])
    with left:
        render_decision(result, preview_id, store)
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
        st.write(
            "Revised live extraction evaluation is pending. "
            "Saved local plans include durable records and queue updates."
        )
        st.caption("Current configured weights: " + json.dumps(asdict(weights)))
    st.caption(
        "Delivery estimates include expected rework. They do not guarantee delivery or predict unknown closures."
    )
