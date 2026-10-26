"""Natural-language controls. Provider calls happen only on explicit send/retry."""

import html

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from dss5105 import intake
from dss5105.dispatch import DispatchDesk
from dss5105.replies import build_reply

TONES = {"RECOMMEND": "ok", "CLARIFY": "ask", "RECORDED_STATUS": "ask", "DECLINE": "ask", "CAPACITY": "ask"}


def reset_preview():
    for key in ("preview", "preview_id", "reviewing_preview", "confirmed_preview", "confirmation_key"):
        st.session_state.pop(key, None)


def reset_conversation():
    reset_preview()
    for key in ("conversation", "pending_turn", "intake_error", "chat_feedback", "chat_replies"):
        st.session_state.pop(key, None)


def choose(choice: dict):
    """Button callback: apply a clicked answer before the next run, without a model call."""
    conversation = st.session_state.get("conversation")
    if conversation is None:
        return
    try:
        updated = intake.apply_selection(
            conversation, choice["field"], choice["value"], choice["text"], DispatchDesk()
        )
    except intake.IntakeError as error:
        st.session_state["chat_feedback"] = str(error)
        return
    reset_preview()
    st.session_state["conversation"] = updated
    st.session_state.pop("chat_feedback", None)


def render_reply(card: dict, *, interactive: bool):
    """Draw a tool-authored card; escape every value because it can quote user text."""
    tone = TONES.get(card["status"], "warn")
    facts = "".join(
        f"<div><dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd></div>" for label, value in card["facts"]
    )
    notes = "".join(f"<li>{html.escape(note)}</li>" for note in card["notes"])
    st.html(
        f'<div class="qr-reply qr-{tone}"><span class="qr-badge">{html.escape(card["label"])}</span>'
        f'<p class="qr-headline">{html.escape(card["headline"])}</p>'
        + (f'<dl class="qr-facts">{facts}</dl>' if facts else "")
        + (f'<ul class="qr-notes">{notes}</ul>' if notes else "")
        + "</div>"
    )
    with st.expander("How this answer was produced"):
        st.html(
            '<ol class="qr-steps">'
            + "".join(
                f"<li><strong>{html.escape(title)}</strong> {html.escape(detail)}</li>"
                for title, detail in card["steps"]
            )
            + "</ol>"
        )
        st.caption("Every value comes from the Python dispatch tools. The model only extracted the request fields.")
    if interactive and card["choices"]:
        st.caption("Choose an answer. This applies it directly, with no model call.")
        columns = st.columns(min(len(card["choices"]), 2))
        for index, choice in enumerate(card["choices"]):
            columns[index % len(columns)].button(
                choice["label"], key=f"choice_{index}", on_click=choose, args=(choice,), width="stretch"
            )


def render_chat(
    desk: DispatchDesk, inbox: dict, *, saved_plan=False
) -> tuple[intake.Conversation, DeltaGenerator | None]:
    """Return a validated conversation and the slot for its latest reply; failures stop the page."""
    conversation = st.session_state.get("conversation", intake.Conversation())
    with st.sidebar:
        if st.button("New request", key="new_chat"):
            reset_conversation()
            st.rerun()
        st.caption("Start a new request for a different order or a change to existing exclusions.")
    st.caption(
        "Planning snapshot: " + desk.as_of.isoformat() + ". Relative dates use this snapshot, not the real clock. "
        "Sending a message uses the model configured in .env and may incur provider charges."
    )
    st.caption(
        "Saving a local allocation requires a separate dispatcher review and confirmation."
        if saved_plan
        else "Draft inputs and numerical previews stay separate. This workspace never commits an allocation."
    )
    submitted = None
    speaker = "Dispatcher"
    if not conversation.turns and "pending_turn" not in st.session_state:
        with st.container(border=True, key="chat_start"):
            st.subheader("Paste a group-chat request, or start from the course inbox")
            key = st.selectbox(
                "Inbox message",
                options=list(inbox),
                key="chat_seed",
                format_func=lambda value: f"{value} / {inbox[value]['requester']} / {inbox[value]['time']}",
            )
            st.write(inbox[key]["text"])
            if st.button("Interpret inbox message", key="interpret_inbox", type="primary"):
                submitted, speaker = inbox[key]["text"], inbox[key]["requester"]
    replies = st.session_state.get("chat_replies", {})
    slot = None
    for index, turn in enumerate(conversation.turns):
        with st.chat_message("user"):
            st.caption(turn["speaker"])
            st.write(turn["text"])
        with st.chat_message("assistant"):
            if index == len(conversation.turns) - 1:
                slot = st.container()
            elif index in replies:
                render_reply(replies[index], interactive=False)
            elif turn.get("reply"):
                st.write(turn["reply"])
    if feedback := st.session_state.get("chat_feedback"):
        st.warning(feedback)
    if "pending_turn" in st.session_state:
        with st.chat_message("user"):
            st.write(st.session_state["pending_turn"]["text"])
        st.error(st.session_state.get("intake_error", "The request has not been interpreted yet."))
        if st.button("Retry interpretation", key="retry_intake"):
            pending = st.session_state["pending_turn"]
            submitted, speaker = pending["text"], pending["speaker"]
    message = st.chat_input(
        "Paste a request or answer the question",
        key="dispatch_chat",
        disabled="pending_turn" in st.session_state,
    )
    if message:
        submitted = message
    if submitted is not None:
        reset_preview()
        st.session_state["pending_turn"] = {"text": submitted, "speaker": speaker}
        try:
            with st.spinner("Reading the request; Python tools will check every number..."):
                updated = intake.interpret_turn(conversation, submitted, desk, speaker=speaker)
            st.session_state["conversation"] = updated
            st.session_state.pop("pending_turn", None)
            st.session_state.pop("intake_error", None)
            st.session_state.pop("chat_feedback", None)
        except intake.IntakeError as error:
            st.session_state["intake_error"] = str(error)
        st.rerun()
    if "pending_turn" in st.session_state:
        reset_preview()
        st.stop()
    if not conversation.turns:
        reset_preview()
        st.stop()
    return conversation, slot


def remember_tool_reply(conversation: intake.Conversation, result: dict, slot: DeltaGenerator | None):
    """Show the latest turn's card and keep it, so history stays as the tools answered."""
    card = build_reply(result)
    index = len(conversation.turns) - 1
    st.session_state["chat_replies"] = {**st.session_state.get("chat_replies", {}), index: card}
    if slot is not None:
        with slot:
            render_reply(card, interactive=True)
    if conversation.turns[-1].get("reply"):
        return
    turns = (*conversation.turns[:-1], {**conversation.turns[-1], "reply": result["message"]})
    st.session_state["conversation"] = intake.Conversation(
        conversation.request,
        turns,
        conversation.needs,
        conversation.provenance,
        conversation.traces,
    )
