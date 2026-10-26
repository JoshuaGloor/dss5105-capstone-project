"""The voice-first assistant page. Turn logic lives in assistant.py; this file is Streamlit glue."""

import hashlib
import sqlite3
from pathlib import Path

import streamlit as st

from dss5105 import assistant
from dss5105.memory import MemoryStore, MemoryUpdateError
from dss5105.records import AllocationError, AllocationStore

ASSETS = Path(__file__).with_name("assets") / "assistant"
PAGE_STYLE = """
<style>
  .stApp { background: #ecebe7; }
  .block-container { padding-top: 4.2rem !important; padding-bottom: 0 !important; max-width: 1180px; }
  [data-testid="stBidiComponentIsolated"], [data-testid="stBidiComponent"] { width: 100%; }
  /* The app shows its own progress; do not fade it while Streamlit reruns. */
  .st-key-assistant, .st-key-assistant[data-stale="true"] { opacity: 1 !important; transition: none !important; }
  @media (max-width: 520px) {
    .block-container { padding-left: 0 !important; padding-right: 0 !important; }
  }
</style>
"""


_REGISTERED = {}


def _component():
    """Register when the assets change, not on every rerun, so edits reload without remounting."""
    sources = {name: (ASSETS / f"app.{name}").read_text(encoding="utf-8") for name in ("html", "css", "js")}
    digest = hashlib.sha256("".join(sources.values()).encode()).hexdigest()
    if _REGISTERED.get("digest") != digest:
        _REGISTERED["component"] = st.components.v2.component("dispatch_assistant", **sources)
        _REGISTERED["digest"] = digest
    return _REGISTERED["component"]


def services() -> assistant.Services:
    memory = MemoryStore()
    weights, _ = assistant.profile_weights(memory.profile())
    return assistant.Services(
        store=AllocationStore(),
        memory=memory,
        weights=weights,
        speaker=memory.profile()["dispatcher"] or "Dispatcher",
    )


def on_event():
    """Component callback: runs before the page script, so the redraw already shows the answer."""
    handle((st.session_state.get("assistant") or {}).get("event"))


def handle(event) -> bool:
    """Apply one component event exactly once; the nonce makes a repeated delivery a no-op."""
    if not isinstance(event, dict) or event.get("nonce") == st.session_state.get("assistant_nonce"):
        return False
    st.session_state["assistant_nonce"] = event.get("nonce")
    session = st.session_state.get("assistant_session", assistant.Session())
    try:
        session, notice = assistant.apply_event(session, event, services())
    except (AllocationError, MemoryUpdateError) as error:
        notice = str(error)
    except (sqlite3.Error, OSError):
        notice = "The local plan could not be read or saved. Try again."
    st.session_state["assistant_session"] = session
    st.session_state["assistant_v"] = st.session_state.get("assistant_v", 0) + 1
    if notice:
        st.session_state["assistant_notice"] = {"id": st.session_state["assistant_v"], "text": notice}
    return True


def render():
    st.html(PAGE_STYLE)
    try:
        current = services()
        session = st.session_state.get("assistant_session", assistant.Session())
        session = assistant.welcome(session, current.memory.profile()["dispatcher"])
        st.session_state["assistant_session"] = session
        view = assistant.build_view(
            session,
            current,
            version=st.session_state.get("assistant_v", 0),
            notice=st.session_state.get("assistant_notice"),
        )
    except (AllocationError, MemoryUpdateError, sqlite3.Error, OSError, ValueError) as error:
        st.error("The assistant could not load the local plan: " + str(error))
        st.stop()
    result = _component()(key="assistant", data=view, on_event_change=on_event)
    # The callback normally handles the event first; this catches one it could not see.
    if handle(result.get("event") if result else None):
        st.rerun()
