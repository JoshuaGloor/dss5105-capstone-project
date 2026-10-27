"""Objective lab: move the four objective sliders and replay the course simulator live.

Every number on this page comes from the unmodified course simulator, averaged over the
course seeds 5105-5114, normal and with the two-week closure. Nothing here is saved.
"""

import html
from dataclasses import asdict

import altair as alt
import streamlit as st

from dss5105.allocator import ObjectiveWeights
from dss5105.evaluate import DEFAULT_PRESET, PRESETS
from dss5105.objective_study import REPORT_SEED, REPORT_SEEDS, measure

ACCENT = "#2a78d6"
CONTEXT = "#c9c7c0"
INK = "#111114"
MUTED = "#74737a"
GRID = "#ecebe7"
NAMES = {
    "yours": "Your configuration",
    "recommended": "Recommended preset",
    "earliest_finish": "Earliest finish",
    "random": "Random (baseline)",
    "greedy_biggest": "Biggest capacity (baseline)",
    "cheapest": "Cheapest (baseline)",
}
BASELINES = ("random", "greedy_biggest", "cheapest")
PRESET_LABELS = {
    "hybrid": "Recommended: on time, then quality",
    "lateness": "On time",
    "defects": "Quality",
    "fairness": "Fair share",
    "robustness": "Resilient",
}
SLIDERS = (
    ("lateness", "On time (lateness)"),
    ("defects", "Quality (defects)"),
    ("fairness", "Fair share (fairness)"),
    ("robustness", "Resilience (robustness)"),
    ("cost", "Cost"),
)
STYLE = """
<style>
.lab-tiles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 4px 0 18px; }
.lab-tile { background: #fff; border: 1px solid rgba(17,17,20,.08); border-radius: 18px; padding: 14px 16px; }
.lab-tile .k { font-size: 12.5px; color: #52514e; }
.lab-tile .v { font-size: 30px; font-weight: 650; letter-spacing: -0.6px; margin-top: 4px; color: #111114; }
.lab-tile .d { font-size: 12px; color: #52514e; margin-top: 2px; }
.lab-check { display: inline-flex; align-items: center; gap: 6px; margin-top: 10px; padding: 3px 9px;
  border-radius: 999px; font-size: 11.5px; font-weight: 650; }
.lab-check.pass { background: #e7f6ee; color: #0a7a40; }
.lab-check.fail { background: #fff3df; color: #8a5300; }
@media (max-width: 900px) { .lab-tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
"""
# (metric key, scenario, tile label, chart title, format, course check)
TILES = (
    ("% late", "normal", "Late batches", "Late batches, % (normal)", "{:.2f}%", "lateness"),
    ("late days", "normal", "Mean late days", "Mean late days per batch (normal)", "{:.3f}", "lateness"),
    ("% def pcs", "normal", "Defective pieces", "Defective pieces, % (normal)", "{:.2f}%", "defects"),
    ("max share", "normal", "Largest workshop share", "Largest workshop share, % (normal)", "{:.1f}%", "fairness"),
)


@st.cache_data(show_spinner=False, max_entries=64)
def replay(weights: tuple) -> dict:
    """Course seeds, normal and shock, for this configuration and every reference."""
    configured = ObjectiveWeights(**dict(weights))
    return measure({"yours": configured, "recommended": PRESETS[DEFAULT_PRESET]}, REPORT_SEED, REPORT_SEEDS)


def checks(rows: dict) -> dict:
    """Tracks v4 criteria for the configured policy, computed from the replay."""
    mine = rows["yours"]
    guard = mine["normal"]["% late"] <= rows["random"]["normal"]["% late"]

    def beats(key):
        return all(mine["normal"][key] < rows[base]["normal"][key] for base in BASELINES)

    return {
        "lateness": (
            "Beats all three baselines on late batches and late days",
            beats("% late") and beats("late days"),
        ),
        "defects": (
            "Beats all three baselines on defective pieces, late rate within random's",
            beats("% def pcs") and guard,
        ),
        "fairness": (
            "Spreads work at least as evenly as random, late rate within random's",
            mine["normal"]["max share"] <= rows["random"]["normal"]["max share"] and guard,
        ),
        "robustness": (
            "Changes less under the closure than random, late rate within random's",
            all(mine["delta"][key] <= rows["random"]["delta"][key] for key in mine["delta"]) and guard,
        ),
    }


def controls() -> dict:
    with st.container(border=True):
        st.caption("PRIORITIES")
        preset = st.selectbox(
            "Start from",
            options=[*PRESET_LABELS, "custom"],
            format_func=lambda key: PRESET_LABELS.get(key, "Custom mix"),
            key="lab_preset",
        )
        start = asdict(PRESETS.get(preset, PRESETS[DEFAULT_PRESET]))
        custom = preset == "custom"
        values = {}
        for term, label in SLIDERS:
            values[term] = st.slider(
                label,
                0.0,
                1.0,
                start[term],
                0.01,
                key=f"lab_{term}_{preset}",
                disabled=not custom,
            )
        values["deadline_buffer_days"] = st.slider(
            "Safety buffer (days)",
            0.0,
            10.0,
            start["deadline_buffer_days"],
            0.5,
            key=f"lab_buffer_{preset}",
            disabled=not custom,
        )
        reserve = st.toggle(
            "Protect scarce capacity",
            value=start["capacity_reservation"] > 0,
            key=f"lab_reserve_{preset}",
            disabled=not custom,
        )
        on_time_first = st.toggle(
            "On-time first",
            value=start["deadline_miss_days"] > 0,
            key=f"lab_miss_{preset}",
            disabled=not custom,
        )
        if not custom:
            st.caption("Choose **Custom mix** to move the sliders.")
        return {
            **values,
            "capacity_reservation": 1.0 if reserve else 0.0,
            "deadline_miss_days": 7.0 if on_time_first else 0.0,
        }


def delta_text(delta: float, fmt: str) -> str:
    """A change in a percentage metric is in percentage points, not percent."""
    plain = fmt.replace("%", "")
    return ("+" if delta > 0 else "") + plain.format(delta) + (" pts" if fmt.endswith("%") else "")


def tiles(rows: dict, verdicts: dict):
    mine = rows["yours"]
    cards = []
    for key, scenario, label, _, fmt, check in TILES:
        value = mine[scenario][key]
        reference = rows["earliest_finish"][scenario][key]
        delta = value - reference
        text, passed = verdicts[check]
        cards.append(
            f'<div class="lab-tile"><div class="k">{html.escape(label)}</div>'
            f'<div class="v">{fmt.format(value)}</div>'
            f'<div class="d">{delta_text(delta, fmt)} vs earliest finish</div>'
            f'<div class="lab-check {"pass" if passed else "fail"}">'
            f"{'&#10003; Meets' if passed else '&#9888; Misses'} {html.escape(check)} criterion</div></div>"
        )
    st.html('<div class="lab-tiles">' + "".join(cards) + "</div>")
    for check, (text, passed) in verdicts.items():
        st.caption(("\u2713 " if passed else "\u26a0 ") + f"**{check.capitalize()}**: {text}.")


def bar_chart(rows: dict, key: str, scenario: str, title: str, fmt: str):
    order = ["yours", "recommended", "earliest_finish", *BASELINES]
    data = [
        {
            "policy": NAMES[name],
            "value": rows[name][scenario][key] if scenario != "delta" else rows[name]["delta"][key],
            "shown": fmt.format(rows[name][scenario][key] if scenario != "delta" else rows[name]["delta"][key]),
            "emphasis": "Your configuration" if name == "yours" else "Reference",
        }
        for name in order
    ]
    y = alt.Y(
        "policy:N",
        sort=[NAMES[name] for name in order],
        title=None,
        axis=alt.Axis(domain=False, ticks=False, labelColor=INK, labelLimit=190),
    )
    x = alt.X(
        "value:Q", title=None, axis=alt.Axis(grid=True, gridColor=GRID, domain=False, ticks=False, labelColor=MUTED)
    )
    bars = (
        alt.Chart(alt.Data(values=data))
        .mark_bar(size=16, cornerRadiusEnd=4)
        .encode(
            y=y,
            x=x,
            color=alt.Color(
                "emphasis:N",
                scale=alt.Scale(domain=["Your configuration", "Reference"], range=[ACCENT, CONTEXT]),
                legend=None,
            ),
            tooltip=[alt.Tooltip("policy:N", title="Policy"), alt.Tooltip("shown:N", title=title)],
        )
    )
    labels = (
        alt.Chart(alt.Data(values=data))
        .mark_text(align="left", dx=6, color=INK, fontSize=11.5)
        .encode(y=y, x=x, text="shown:N")
    )
    chart = (
        alt.layer(bars, labels)
        .properties(
            title=alt.TitleParams(title, anchor="start", fontSize=13, color=INK, fontWeight=600), height=alt.Step(26)
        )
        .configure_view(stroke=None)
        .properties(padding={"right": 64, "top": 6, "left": 4, "bottom": 4})
    )
    st.altair_chart(chart, width="stretch")


def render():
    st.html(STYLE)
    st.caption("SWEATERCO / OBJECTIVE LAB")
    st.title("What do the priorities buy?")
    st.caption(
        "Move a slider and the course simulator replays all 120 orders under your configuration: ten seeds, "
        "normal and with a two-week workshop closure. One scorer, configured, never a separate policy."
    )
    left, right = st.columns([1, 2.4], gap="large")
    with left:
        values = controls()
        st.caption("Our declared objective: minimise lateness first, then defects.")
    try:
        weights = ObjectiveWeights(**values)
        rows = replay(tuple(sorted(asdict(weights).items())))["policies"]
    except ValueError as error:
        with right:
            st.error(str(error))
        return
    verdicts = checks(rows)
    with right:
        tiles(rows, verdicts)
        first, second = st.columns(2)
        for column, (key, scenario, _, title, fmt, _) in zip((first, second, first, second), TILES, strict=True):
            with column:
                bar_chart(rows, key, scenario, title, fmt.replace("%", ""))
        bar_chart(rows, "late days", "delta", "Change in mean late days under the closure", "{:+.3f}")
        with st.expander("Table view: every metric, normal and shock"):
            table = []
            for name in ("yours", "recommended", "earliest_finish", *BASELINES):
                row = {"Policy": NAMES[name]}
                for scenario in ("normal", "shock"):
                    for key in ("% late", "late days", "% def pcs", "max share", "cost"):
                        row[f"{key} ({scenario})"] = round(rows[name][scenario][key], 3)
                row["Change in % late"] = round(rows[name]["delta"]["% late"], 3)
                row["Change in late days"] = round(rows[name]["delta"]["late days"], 3)
                table.append(row)
            st.dataframe(table, hide_index=True, width="stretch")
        st.caption(
            f"Seeds {REPORT_SEED}-{REPORT_SEED + REPORT_SEEDS - 1}. Metrics are the official simulator metrics, "
            "averaged per run. The presets were chosen on development seeds 6000-6029 before these seeds were "
            "run; see docs/OBJECTIVE_STUDY.md."
        )
