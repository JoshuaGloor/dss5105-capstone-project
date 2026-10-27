"""Chat replies assembled from dispatch tool output only; no model writes this text."""

from dataclasses import asdict

from dss5105.dispatch import DispatchInput

STATUS_LABELS = {
    "RECOMMEND": "Ready to review",
    "CLARIFY": "Clarification needed",
    "REFUSE_SUGGESTION": "Suggested workshop refused",
    "NEEDS_REVIEW": "Exception needs review",
    "NO_FEASIBLE_OPTION": "No feasible option",
    "DECLINE": "Data unavailable",
    "RECORDED_STATUS": "Recorded status only",
    "ALREADY_ALLOCATED": "Allocation already saved",
    "CAPACITY": "Capacity check",
}
PREFERENCES = {
    "fastest": "fastest turnaround (request preference)",
    "lowest_defects": "lowest defect risk (request preference)",
    "cheapest_on_time": "cheapest option that meets the date (request preference)",
}
MAX_CHOICES = 8
DEFAULTS = asdict(DispatchInput())


def _chosen(result: dict) -> dict | None:
    chosen_id = result.get("recommendation") or result.get("alternative")
    return next((row for row in result["candidates"] if row["estimate"]["workshop_id"] == chosen_id), None)


def _facts(result: dict, chosen: dict) -> list[list[str]]:
    values = chosen["display"]
    due = result["batch"]["due_date"]
    deadline = f"{due}, meets estimate" if chosen["meets_deadline"] else f"{due}, late {values['lateness']}"
    return [
        ["Workshop", f"{chosen['name']} ({chosen['estimate']['workshop_id']})"],
        ["Estimated delivery", values["eta"]],
        ["Expected turnaround", values["turnaround"]],
        ["Deadline", deadline],
        ["Cost", values["cost"] + " source units"],
        ["Batch defect risk", values["defects"]],
    ]


def _ranking(result: dict) -> str:
    preference = result["input"]["preference"]
    if preference in PREFERENCES:
        return "Ranked by " + PREFERENCES[preference] + "."
    effective = result["effective_weights"]
    labels = {
        "lateness": "delivery",
        "defects": "quality risk",
        "fairness": "fair share of work",
        "robustness": "resilience to a stoppage",
        "cost": "subcontracting cost",
    }
    priorities = ", ".join(label for term, label in labels.items() if effective[term] > 0)
    return "Compared permitted workshops using the configured priorities for " + priorities + "."


def _open_matches(result: dict) -> list[dict] | None:
    """In-progress orders behind an ambiguous reference; completed ones are not dispatchable."""
    resolution = result.get("resolution", {})
    if result["status"] != "CLARIFY" or resolution.get("status") != "AMBIGUOUS":
        return None
    return [row for row in resolution["matches"] if row["status"] == "IN_PROGRESS"]


def _choices(result: dict) -> list[dict]:
    matches = _open_matches(result)
    if matches is not None:
        if len(matches) > MAX_CHOICES:
            return []
        return [
            {
                "field": "order_id",
                "value": row["order_id"],
                "text": row["order_id"],
                "label": f"{row['order_id']} / {row['product']} / {row['pieces']} pcs / due {row['due_date']}",
            }
            for row in matches
        ]
    chosen = _chosen(result)
    if result["status"] == "REFUSE_SUGGESTION" and chosen is not None:
        return [
            {
                "field": "suggested_workshop",
                "value": chosen["name"],
                "text": f"Use {chosen['name']} instead.",
                "label": f"Use {chosen['name']} instead",
            }
        ]
    return []


def steps(result: dict) -> list[list[str]]:
    """The tool path behind a reply, in order; every value is copied from the result."""
    fields = []
    for key, value in result["input"].items():
        if key == "exclusions":
            fields.extend(f"exclude {item['workshop_id']} (imposed by {item['imposed_by']})" for item in value)
        elif value != DEFAULTS[key]:
            fields.append(f"{key} {value}")
    trace = [["Request", ", ".join(fields) if fields else "No fields established yet."]]
    resolution = result.get("resolution")
    if resolution is None:
        trace.append(["Order lookup", "Not needed; this question is answered from what the data contains."])
    elif resolution["status"] == "RESOLVED":
        order = resolution["matches"][0]
        trace.append(
            [
                "Order lookup",
                f"{order['order_id']} in orders.csv: {order['customer']}, {order['product']}, "
                f"{order['pieces']} pieces, due {order['due_date']}.",
            ]
        )
    elif resolution["status"] == "AMBIGUOUS":
        trace.append(["Order lookup", f"{len(resolution['matches'])} recorded orders match; none was chosen."])
    else:
        trace.append(["Order lookup", "No recorded order matches."])
    if "batch" in result:
        permitted = len(result["candidates"])
        total = permitted + len(result["excluded"])
        excluded = "; ".join(f"{row['name']}: {' '.join(row['reasons'])}" for row in result["excluded"])
        trace.append(["Eligibility", f"{permitted} of {total} workshops permitted. " + (excluded or "None excluded.")])
        on_time = sum(row["meets_deadline"] for row in result["candidates"])
        trace.append(
            [
                "Estimates",
                f"{permitted} delivery estimates on the {result['snapshot']['as_of']} queue snapshot; "
                f"{on_time} meet the deadline.",
            ]
        )
    if result.get("split_option"):
        trace.append(["Split", "Two-workshop split assessed with the same estimate and eligibility rule."])
    trace.append(["Outcome", STATUS_LABELS[result["status"]] + "."])
    return trace


def build_reply(result: dict) -> dict:
    """One chat card per tool result: headline, facts, notes, clickable answers and trace."""
    status = result["status"]
    chosen = _chosen(result)
    order_id = result.get("order", {}).get("order_id")
    notes = []
    facts = []
    if status == "RECOMMEND" and chosen:
        headline = f"Recommended workshop for {order_id}: {chosen['name']}."
        notes.append(_ranking(result))
    elif status == "REFUSE_SUGGESTION":
        suggested = result["input"]["suggested_workshop"]
        refused = next((row for row in result["excluded"] if row["workshop_id"] == suggested), None)
        headline = f"{refused['name'] if refused else suggested} cannot take {order_id}."
        if refused:
            notes.extend(refused["reasons"])
        else:
            notes.append(result["message"])
        if chosen:
            notes.append(f"Alternative: {chosen['name']}. " + _ranking(result))
    elif status == "NEEDS_REVIEW" and chosen:
        headline = f"Needs review before allocating {order_id}. Whole-batch option: {chosen['name']}."
        notes.append(result["message"])
    else:
        headline = result["message"]
    if chosen and status in ("RECOMMEND", "REFUSE_SUGGESTION", "NEEDS_REVIEW"):
        facts = _facts(result, chosen)
        if result.get("decision_basis"):
            notes.extend(result["decision_basis"]["reasons"])
    if result.get("deadline_note"):
        notes.append(result["deadline_note"])
    notes.extend(result["review_options"])
    if status == "RECORDED_STATUS":
        notes.append(f"Recorded status: {result['order']['status']}.")
        notes.append(f"Last recorded activity: {result['order']['last_activity_date']}.")
    matches = _open_matches(result)
    if matches is not None:
        closed = len(result["resolution"]["matches"]) - len(matches)
        if len(matches) > MAX_CHOICES:
            notes.append("Too many in-progress orders match to list here. Please type the order ID.")
        elif not matches:
            notes.append("None of the matching recorded orders is still in progress.")
        if closed:
            notes.append(f"{closed} matching orders are already complete and are not listed.")
    return {
        "status": status,
        "label": STATUS_LABELS[status],
        "headline": headline,
        "facts": facts,
        "notes": notes,
        "choices": _choices(result),
        "steps": steps(result),
    }
