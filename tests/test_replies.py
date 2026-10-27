import json
import re

import pytest

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, read_inbox
from dss5105.evaluate import PRESETS
from dss5105.replies import build_reply

INBOX = {item["request_id"]: item for item in read_inbox()}
FIXTURES = json.loads((ROOT / "examples" / "dispatch_inputs.json").read_text())


@pytest.fixture(scope="module")
def desk():
    return DispatchDesk()


def reply(desk, request_id, preset="lateness"):
    result = desk.preview(INBOX[request_id], DispatchInput(**FIXTURES[request_id]), PRESETS[preset])
    return result, build_reply(result)


@pytest.mark.parametrize("preset", PRESETS)
@pytest.mark.parametrize("request_id", INBOX)
def test_every_numeral_on_a_card_is_copied_from_the_tool_result(desk, request_id, preset):
    result, card = reply(desk, request_id, preset)
    source = json.dumps(result, ensure_ascii=True)
    shown = " ".join([card["headline"], *card["notes"], *(value for _, value in card["facts"])])
    for number in re.findall(r"\d[\d,.:-]*\d|\d", shown):
        assert number in source, f"{request_id}: {number} is not in the tool output"


def test_recommendation_card_uses_the_chosen_candidate_display(desk):
    result, card = reply(desk, "R25")
    chosen = next(row for row in result["candidates"] if row["estimate"]["workshop_id"] == result["recommendation"])
    assert card["headline"] == f"Recommended workshop for ORD-109: {chosen['name']}."
    assert ["Estimated delivery", chosen["display"]["eta"]] in card["facts"]
    assert card["choices"] == []
    assert any("imposed by Mei" in detail for _, detail in card["steps"])


def test_ambiguous_order_offers_each_match_as_a_choice(desk):
    result, card = reply(desk, "R03")
    rows = result["resolution"]["matches"]
    open_ids = [row["order_id"] for row in rows if row["status"] == "IN_PROGRESS"]
    assert len(open_ids) == 6  # The track describes six TrendCart orders.
    assert [choice["value"] for choice in card["choices"]] == open_ids
    assert all(choice["field"] == "order_id" for choice in card["choices"])
    assert f"{len(rows) - 6} matching orders are already complete and are not listed." in card["notes"]


def test_refusal_names_reason_and_offers_the_tool_alternative(desk):
    result, card = reply(desk, "R11")
    assert card["headline"] == "OldMill cannot take ORD-008."
    assert "Status is SUSPENDED." in card["notes"]
    alternative = desk.workshops[result["alternative"]].name
    assert card["choices"] == [
        {
            "field": "suggested_workshop",
            "value": alternative,
            "text": f"Use {alternative} instead.",
            "label": f"Use {alternative} instead",
        }
    ]


@pytest.mark.parametrize("request_id", ["R20", "R23", "R28", "R30"])
def test_review_cards_carry_the_split_and_earliest_options(desk, request_id):
    result, card = reply(desk, request_id)
    assert card["label"] == "Exception needs review"
    assert result["split_option"]["summary"] in card["notes"]
    assert card["choices"] == []


def test_decline_and_status_cards_state_the_limit(desk):
    _, quote = reply(desk, "R13")
    assert quote["headline"].startswith("The supplied data contains neither")
    assert quote["facts"] == []
    _, unknown = reply(desk, "R18")
    assert "No matching order is recorded" in unknown["headline"]
    status = desk.preview(INBOX["R18"], DispatchInput(order_id="ORD-109", intent="status"), ObjectiveWeights())
    assert any(note.startswith("Recorded status: ") for note in build_reply(status)["notes"])
