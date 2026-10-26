"""Read-only workshop and workload workspace, available without a language model."""

import json
from datetime import timedelta

import streamlit as st

from dss5105.dispatch import DispatchDesk, LoadScenario, WorkshopQuery
from dss5105.records import AllocationStore


def render_workshops(desk: DispatchDesk, store: AllocationStore | None):
    service = store or desk
    st.subheader("Workshop capacity")
    st.caption("Check who can meet a delivery date, then see how additional work changes the estimate.")
    st.caption(
        "Using saved planning queues. Capacity changes only when an allocation is confirmed."
        if store
        else "Using the independent course snapshot. These checks do not reserve capacity."
    )
    categories = sorted({category for workshop in desk.workshops.values() for category in workshop.makes})
    query = st.session_state.get("workshop_query", WorkshopQuery())
    with st.form("capacity_form"):
        category_col, pieces_col, date_col = st.columns(3)
        category = category_col.selectbox(
            "Product category",
            categories,
            key="capacity_category",
            index=categories.index("TOPS") if "TOPS" in categories else 0,
        )
        pieces = pieces_col.number_input(
            "Batch pieces", min_value=1, max_value=100000, value=1500, step=100, key="capacity_pieces"
        )
        due = date_col.date_input("Delivery deadline", value=desk.as_of + timedelta(days=14), key="capacity_due")
        if st.form_submit_button("Check delivery capacity", key="check_capacity", type="primary"):
            query = WorkshopQuery(category=category, pieces=pieces, due_date=due.isoformat())
            st.session_state["workshop_query"] = query
    result = service.query_register(query)
    st.session_state["register_result"] = result
    if query.pieces is None:
        st.caption("All recorded workshops. Set a batch and deadline above to check delivery estimates.")
    else:
        st.write("Checking " + result["display"]["pieces"] + " of " + query.category + " for " + query.due_date + ".")
    rows = []
    for row in result["matches"]:
        if row["eligible"] is False:
            outcome = " ".join(row["reasons"])
        elif row["meets_deadline"] is not None:
            outcome = "Meets estimate" if row["meets_deadline"] else "Late by " + row["display"]["lateness"]
        else:
            outcome = "Set a batch and date to check"
        rows.append(
            {
                "Workshop": row["name"],
                "Status": row["status"],
                "Products": ", ".join(row["makes"]),
                "Capacity": row["display"]["capacity"],
                "Batch limit": row["display"]["max_batch"],
                "Queue": row["display"]["queue"],
                "Estimated delivery": row["display"].get("eta", "Unavailable"),
                "Delivery check": outcome,
            }
        )
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        st.info("No workshops match this query.")
    st.caption(result["assumption"] + " Planning date: " + result["snapshot"]["as_of"] + ".")
    st.download_button(
        "Export workshop evidence",
        json.dumps(result, indent=2),
        file_name="workshop-capacity.json",
        mime="application/json",
        key="export_register",
    )
    with st.expander("What if we send more work here?", expanded=query.pieces is not None):
        st.caption("Assume an additional batch of the same category waits ahead of your batch. No queues change.")
        if query.pieces is None:
            st.info("Check a batch and delivery date first.")
            return
        with st.form("load_form"):
            workshop_col, extra_col = st.columns(2)
            workshop = workshop_col.selectbox(
                "Workshop to test",
                options=list(desk.workshops),
                key="load_workshop",
                format_func=lambda key: desk.workshops[key].name,
            )
            extra = extra_col.number_input(
                "Additional pieces ahead of this batch",
                min_value=1,
                max_value=100000,
                value=1500,
                step=100,
                key="load_pieces",
            )
            submitted = st.form_submit_button("Compare before and after", key="check_load", type="primary")
        # Keep the submitted scenario, but always regenerate it against current queues.
        if submitted:
            st.session_state["load_scenario"] = LoadScenario(
                workshop, query.category, query.pieces, extra, query.due_date
            )
        scenario = st.session_state.get("load_scenario")
        if scenario is None or (scenario.category, scenario.pieces, scenario.due_date) != (
            query.category,
            query.pieces,
            query.due_date,
        ):
            st.session_state.pop("load_result", None)
            return
        probe = service.probe_load(scenario)
        st.session_state["load_result"] = probe
        if probe["status"] == "UNSUPPORTED":
            st.warning("This workshop cannot accept the proposed workload. " + " ".join(probe["reasons"]))
        else:
            st.write(
                probe["workshop_name"]
                + ": adding "
                + probe["display"]["additional_pieces"]
                + " uses "
                + probe["display"]["additional_processing"]
                + " of processing capacity."
            )
            st.dataframe(
                [
                    {
                        "Scenario": label,
                        "Estimated delivery": probe[key]["display"]["eta"],
                        "Turnaround": probe[key]["display"]["turnaround"],
                        "Deadline": "Meets estimate"
                        if probe[key]["meets_deadline"]
                        else "Late by " + probe[key]["display"]["lateness"],
                    }
                    for key, label in (("before", "Before additional work"), ("after", "After additional work"))
                ],
                hide_index=True,
                width="stretch",
            )
            if alternative := probe["fastest_alternative"]:
                st.info(
                    "Fastest alternative: "
                    + alternative["name"]
                    + ", estimated delivery "
                    + alternative["display"]["eta"]
                    + ". "
                    + (
                        "Meets the date under this estimate."
                        if alternative["meets_deadline"]
                        else "This alternative also misses the date."
                    )
                )
        st.caption(probe["assumption"])
        st.download_button(
            "Export workload scenario",
            json.dumps(probe, indent=2),
            file_name="workload-scenario.json",
            mime="application/json",
            key="export_load",
        )
