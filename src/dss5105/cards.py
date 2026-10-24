"""Answer-card pieces: delivery tiles and the collapsible working section.

Every value shown comes from a dispatch tool result; nothing here computes a number.
"""

import html
import json

import altair as alt
import streamlit as st

MEETS_COLOR = "#26a37c"
MISSES_COLOR = "#94631a"
MEETS_LABEL = "Meets the deadline"
MISSES_LABEL = "Misses the deadline"
TONES = {
    "RECOMMEND": "ok",
    "ALREADY_ALLOCATED": "ok",
    "CLARIFY": "ask",
    "RECORDED_STATUS": "ask",
    "DECLINE": "limit",
    "NO_FEASIBLE_OPTION": "bad",
}


def tone(status: str) -> str:
    return TONES.get(status, "warn")


def chosen_candidate(result: dict) -> dict | None:
    chosen_id = result["recommendation"] or result["alternative"]
    return next((row for row in result["candidates"] if row["estimate"]["workshop_id"] == chosen_id), None)


def candidate_chart(result: dict):
    """Plot only tool-produced estimates; tooltips reuse the tool's formatted strings."""
    rows = [
        {
            "name": candidate["name"],
            "days": candidate["estimate"]["expected_turnaround_days"],
            "status": MEETS_LABEL if candidate["meets_deadline"] else MISSES_LABEL,
            "turnaround": candidate["display"]["turnaround"],
            "cost": candidate["display"]["cost"],
            "defects": candidate["display"]["defects"],
            "eta": candidate["display"]["eta"],
        }
        for candidate in result["candidates"]
    ]
    order = [row["name"] for row in rows]
    axis = alt.Axis(grid=True, gridColor="#e6e9e4", gridWidth=1, domain=False, tickSize=0, labelColor="#60726c")
    bars = (
        alt.Chart(alt.Data(values=rows))
        .mark_bar(cornerRadiusEnd=4, size=18)
        .encode(
            y=alt.Y("name:N", sort=order, title=None, axis=alt.Axis(domain=False, tickSize=0, labelColor="#203731")),
            x=alt.X("days:Q", title="Expected days to delivery", axis=axis),
            color=alt.Color(
                "status:N",
                scale=alt.Scale(domain=[MEETS_LABEL, MISSES_LABEL], range=[MEETS_COLOR, MISSES_COLOR]),
                legend=alt.Legend(title=None, orient="top", labelColor="#203731"),
            ),
            tooltip=[
                alt.Tooltip("name:N", title="Workshop"),
                alt.Tooltip("turnaround:N", title="Expected"),
                alt.Tooltip("eta:N", title="ETA"),
                alt.Tooltip("cost:N", title="Cost units"),
                alt.Tooltip("defects:N", title="Defect risk"),
                alt.Tooltip("status:N", title="Deadline"),
            ],
        )
    )
    layers = [bars]
    available = result["candidates"][0]["estimate"]["available_days"]
    if available >= 0:
        marker = alt.Data(values=[{"available": available, "label": "Deadline"}])
        layers.append(alt.Chart(marker).mark_rule(size=2, color="#203731").encode(x="available:Q"))
        layers.append(
            alt.Chart(marker)
            .mark_text(align="left", dx=6, dy=-2, baseline="top", color="#203731", fontSize=11, fontWeight=600)
            .encode(x="available:Q", text="label:N")
        )
    chart = alt.layer(*layers).properties(height=alt.Step(30)).configure_view(stroke=None)
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


def deadline_text(result: dict, chosen: dict) -> str:
    batch = result.get("batch") or {}
    due = batch.get("due_date") or (result.get("order") or {}).get("due_date") or ""
    state = "meets estimate" if chosen["meets_deadline"] else "late " + chosen["display"]["lateness"]
    return f"{due}, {state}" if due else state


def option_tiles(result: dict, chosen: dict, lead: str | None):
    values = chosen["display"]
    tiles = [
        ("Estimated delivery", values["eta"], ""),
        ("Turnaround", values["turnaround"], ""),
        ("Deadline", deadline_text(result, chosen), "qr-good" if chosen["meets_deadline"] else "qr-late"),
        ("Cost", values["cost"] + " source units", ""),
        ("Batch defect risk", values["defects"], ""),
    ]
    cells = "".join(
        f'<div class="qr-tile {cls}"><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>'
        for label, value, cls in tiles
    )
    head = (
        f'<div class="qr-option-head"><span class="qr-eyebrow">{html.escape(lead)}</span>'
        f"<strong>{html.escape(chosen['name'])} <small>{html.escape(chosen['estimate']['workshop_id'])}</small>"
        "</strong></div>"
        if lead
        else ""
    )
    st.html(f'<div class="qr-option">{head}<div class="qr-tiles">{cells}</div></div>')


def render_working(result: dict, steps: list[list[str]], uid: str):
    """The working behind one answer: comparison, exclusions, estimate build-up, reference policies and trace."""
    st.caption(result["assumption"])
    if result["candidates"]:
        st.markdown("#### Options compared")
        candidate_chart(result)
        candidate_table(result)
    else:
        st.info("No permitted candidate evidence is available for this request.")
    if result["split_option"]:
        st.markdown("#### Two-workshop split estimate")
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
    if result.get("resolution", {}).get("status") == "AMBIGUOUS" and result["resolution"]["matches"]:
        st.markdown("#### Matching recorded orders")
        st.dataframe(
            [
                {key: row[key] for key in ("order_id", "customer", "product", "pieces", "due_date")}
                for row in result["resolution"]["matches"]
            ],
            hide_index=True,
        )
    if result["excluded"]:
        st.markdown("#### Why other workshops are not used")
        for row in result["excluded"]:
            st.markdown("**" + row["name"] + "**")
            for reason in row["reasons"]:
                st.write(reason)
    if result["candidates"]:
        st.markdown("#### How delivery estimates are built")
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
    if result["baselines"]:
        st.markdown("#### Compared with the reference policies")
        st.caption(
            "Same order, same queue snapshot. Reference policies see eligibility only, "
            "so they can pick a workshop this desk has been told to avoid."
        )
        baseline_table(result)
    st.markdown("#### Objective weights and scales")
    st.json({"weights": result["effective_weights"], "scales": result["scales"]}, expanded=True)
    st.caption("Weights are relative preferences, not probabilities. Scales are the existing reference units.")
    st.markdown("#### How this answer was produced")
    st.html(
        '<ol class="qr-steps">'
        + "".join(f"<li><strong>{html.escape(title)}</strong> {html.escape(detail)}</li>" for title, detail in steps)
        + "</ol>"
    )
    st.caption("Every value comes from the Python dispatch tools. The model only extracted the request fields.")
    st.markdown("#### Raw evidence")
    st.json(result, expanded=False)
    st.download_button(
        "Export evidence JSON",
        data=json.dumps(result, ensure_ascii=True, indent=2),
        file_name=f"{result['request']['request_id']}-preview.json",
        mime="application/json",
        key="evidence_" + uid,
    )
