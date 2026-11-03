"""Memory: what the desk remembers across sessions, where it came from, and how to change it."""

import json
import sqlite3
from dataclasses import asdict

import streamlit as st

from dss5105.assistant import PRESET_VIEW, profile_weights
from dss5105.memory import MemoryStore, MemoryUpdateError
from dss5105.records import AllocationError, AllocationStore

LAYERS = (
    ("Working memory", "This conversation: the request so far, open questions and quoted evidence.", "Session only"),
    (
        "Standing rules",
        "Constraints you confirmed with a booking, applied to later orders for that customer.",
        "Saved",
    ),
    ("Booking ledger", "Every confirmed allocation, its evidence, and the queues it changed.", "Saved"),
    ("Conversation log", "What was said and what the tools answered, for audit.", "Saved"),
    ("Profile", "Your name on bookings, your priorities, and voice settings.", "Saved"),
)


def _layers():
    rows = "".join(
        f'<div style="padding:12px 14px;border:1px solid rgba(17,17,20,.08);border-radius:16px;background:#fff">'
        f'<div style="font-weight:650;font-size:14px">{name}</div>'
        f'<div style="font-size:12.5px;color:#52514e;margin-top:3px;line-height:1.4">{text}</div>'
        f'<div style="font-size:11px;color:#74737a;margin-top:8px;font-weight:600">{scope.upper()}</div></div>'
        for name, text, scope in LAYERS
    )
    st.html(
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));'
        'gap:10px;margin:6px 0 18px">' + rows + "</div>"
    )


def render():
    st.caption("SWEATERCO / MEMORY")
    st.title("What the desk remembers")
    st.caption(
        "Memory never invents a constraint or a number. It learns a rule only from a booking you confirmed, keeps "
        "who said it in their own words, and Python applies it. Everything is stored locally in runtime/."
    )
    try:
        memory = MemoryStore()
        store = AllocationStore()
        rules, records, episodes = memory.rules(), store.records(), memory.episodes(limit=200)
        profile = memory.profile()
        summary = store.summary()
    except (AllocationError, MemoryUpdateError, sqlite3.Error, OSError) as error:
        st.error("Could not read memory: " + str(error))
        st.stop()
    _layers()
    actor = profile["dispatcher"] or "Dispatcher"
    tabs = st.tabs(
        [f"Rules ({len(rules)})", f"Bookings ({len(records)})", f"Log ({len(episodes)})", "Profile", "Plan"]
    )
    with tabs[0]:
        if not rules:
            st.info("No standing rules yet. Confirm a booking that had a constraint, then choose Remember.")
        for rule in rules:
            with st.container(border=True):
                text, action = st.columns([5, 1], vertical_alignment="center")
                text.markdown(f"**{rule['summary']}**" + ("" if rule["active"] else "  \u00b7  _paused_"))
                text.caption(f"{rule['imposed_by']} on {rule['created_on']}: '{rule['evidence']}'")
                text.caption(
                    f"Remembered by {rule['created_by']}"
                    + (f" from booking {rule['source_allocation_id'][:8]}." if rule["source_allocation_id"] else ".")
                )
                if action.button("Pause" if rule["active"] else "Resume", key="rule_" + rule["rule_id"]):
                    try:
                        memory.set_rule_active(rule["rule_id"], not rule["active"], actor)
                    except MemoryUpdateError as error:
                        st.error(str(error))
                    else:
                        st.rerun()
    with tabs[1]:
        if records:
            st.dataframe(
                [
                    {
                        "Order": record["order_id"],
                        "Workshop": record["workshop_name"],
                        "Pieces": record["tool_evidence"]["batch"]["pieces"],
                        "Confirmed by": record["confirmed_by"],
                        "Reserved days": round(record["reserved_processing_days"], 2),
                        "Saved (UTC)": record["created_at_utc"][:19].replace("T", " "),
                    }
                    for record in records
                ],
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("Nothing is booked in this plan yet.")
        st.download_button(
            "Export bookings with evidence",
            json.dumps(records, indent=2),
            file_name="allocation-records.json",
            mime="application/json",
            key="export_records",
        )
    with tabs[2]:
        if episodes:
            st.dataframe(
                [
                    {
                        "When (UTC)": episode["created_at_utc"][:19].replace("T", " "),
                        "Kind": episode.get("kind", ""),
                        "Who": episode.get("speaker", ""),
                        "Said": episode.get("utterance", ""),
                        "Outcome": episode.get("status", "") or episode.get("workshop_id", ""),
                        "Order": episode.get("order_id") or "",
                    }
                    for episode in episodes
                ],
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("Conversations with the assistant are logged here.")
        st.download_button(
            "Export memory",
            json.dumps(memory.export(), indent=2),
            file_name="memory.json",
            mime="application/json",
            key="export_memory",
        )
    with tabs[3]:
        weights, preset = profile_weights(profile)
        st.write(f"Dispatcher name on bookings: **{profile['dispatcher'] or 'not set'}**")
        st.write(f"Priorities: **{PRESET_VIEW.get(preset, ('Custom mix', ''))[0]}**")
        st.json(asdict(weights), expanded=False)
        st.write(f"Read answers aloud: **{'on' if profile['speak_replies'] else 'off'}**")
        st.caption("Change these from the assistant's profile and priorities sheets.")
    with tabs[4]:
        st.write(f"Planning date **{summary['as_of']}**, revision **{summary['revision']}**.")
        st.dataframe(
            [
                {
                    "Workshop": workshop_id,
                    "Queue (days)": round(days, 2),
                    "Booked pieces": summary["ledger"].get(workshop_id, 0),
                }
                for workshop_id, days in summary["queues"].items()
            ],
            hide_index=True,
            width="stretch",
        )
        st.caption("Queues start from the course snapshot and grow only when a booking is confirmed.")
        with st.expander("Start a fresh demo plan"):
            st.write(
                "Moves the current plan to runtime/archive and starts again from the course snapshot. "
                "Nothing is deleted. Standing rules and the log are kept."
            )
            confirm = st.checkbox("I understand the current bookings leave the live plan.", key="confirm_archive")
            if st.button("Archive and start fresh", disabled=not confirm, key="archive_plan"):
                target = store.archive()
                st.session_state.pop("assistant_session", None)
                st.success(f"Archived to {target.relative_to(target.parents[2]) if target else 'nothing'}.")
