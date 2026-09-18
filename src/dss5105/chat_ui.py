"""Natural-language controls. Provider calls happen only on explicit send/retry."""

import streamlit as st

from dss5105 import intake
from dss5105.dispatch import DispatchDesk


def reset_preview():
    for key in ("preview", "preview_id", "reviewing_preview", "confirmed_preview"):
        st.session_state.pop(key, None)


def reset_conversation():
    reset_preview()
    for key in ("conversation", "pending_turn", "intake_error", "chat_feedback"):
        st.session_state.pop(key, None)


def render_chat(desk: DispatchDesk, inbox: dict) -> intake.Conversation:
    """Return only a validated conversation; unresolved model failures stop the page."""
    conversation = st.session_state.get("conversation", intake.Conversation())
    with st.sidebar:
        if st.button("New request", key="new_chat"):
            reset_conversation()
            st.rerun()
        st.caption("Start a new request for a different order or a change to existing exclusions.")
    st.caption("Sending a message uses the model configured in the project's .env and may incur provider charges.")
    st.caption(
        "Planning snapshot: " + desk.as_of.isoformat() + ". Relative dates use this snapshot, not the real clock."
    )
    st.caption("Draft inputs and numerical previews stay separate. This workspace never commits an allocation.")
    submitted = None
    speaker = "Dispatcher"
    if not conversation.turns and "pending_turn" not in st.session_state:
        with st.expander("Try an original course inbox message"):
            key = st.selectbox(
                "Inbox message",
                options=list(inbox),
                key="chat_seed",
                format_func=lambda value: f"{value} / {inbox[value]['requester']}",
            )
            st.write(inbox[key]["text"])
            if st.button("Interpret inbox message", key="interpret_inbox"):
                submitted, speaker = inbox[key]["text"], inbox[key]["requester"]
    for turn in conversation.turns:
        with st.chat_message("user"):
            st.write(turn["text"])
        if turn.get("reply"):
            with st.chat_message("assistant"):
                st.write(turn["reply"])
    if "pending_turn" in st.session_state:
        with st.chat_message("user"):
            st.write(st.session_state["pending_turn"]["text"])
        st.error(st.session_state.get("intake_error", "The request has not been interpreted yet."))
        if st.button("Retry interpretation", key="retry_intake"):
            pending = st.session_state["pending_turn"]
            submitted, speaker = pending["text"], pending["speaker"]
    message = st.chat_input(
        "Describe an order or answer the clarification question",
        key="dispatch_chat",
        disabled="pending_turn" in st.session_state,
    )
    if message:
        submitted = message
    if submitted is not None:
        reset_preview()
        st.session_state["pending_turn"] = {"text": submitted, "speaker": speaker}
        try:
            with st.spinner("Interpreting the request; Python tools will check the details..."):
                updated = intake.interpret_turn(conversation, submitted, desk, speaker=speaker)
            st.session_state["conversation"] = updated
            st.session_state.pop("pending_turn", None)
            st.session_state.pop("intake_error", None)
        except intake.IntakeError as error:
            st.session_state["intake_error"] = str(error)
        st.rerun()
    if "pending_turn" in st.session_state:
        reset_preview()
        st.stop()
    if not conversation.turns:
        reset_preview()
        st.info("Send an order request to begin. Missing information will prompt a clarification.")
        st.stop()
    return conversation


def remember_tool_reply(conversation: intake.Conversation, result: dict):
    """Keep a historical tool response without asking the model to write prose."""
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
