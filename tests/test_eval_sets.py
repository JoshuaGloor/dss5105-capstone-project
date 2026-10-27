import json
from collections import Counter

import pytest

from dss5105 import eval_sets, evaluate_chat
from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import DispatchDesk, DispatchInput, read_inbox
from dss5105.intake import QUESTIONS


def load(name):
    inbox_path, rubric_path = evaluate_chat.SETS[name]
    return read_inbox(inbox_path), json.loads(rubric_path.read_text())


def test_committed_sets_match_the_seeded_generator(tmp_path):
    eval_sets.write(eval_sets.generate(), tmp_path)
    for path in tmp_path.iterdir():
        assert path.read_text() == (eval_sets.OUTPUT / path.name).read_text(), path.name


@pytest.mark.parametrize("name", evaluate_chat.SETS)
def test_labels_are_reachable_from_perfect_extraction(name):
    """Checks the rubric against the tools, not the model."""
    desk = DispatchDesk()
    inbox, rubric = load(name)
    assert set(rubric["cases"]) == {item["request_id"] for item in inbox}
    for envelope in inbox:
        rule = rubric["cases"][envelope["request_id"]]
        exclusions = [
            {"workshop_id": key, "imposed_by": imposer, "evidence": envelope["text"]}
            for key, imposer in rule.get("exclusions", {}).items()
        ]
        needs = " ".join(QUESTIONS[code] for code in rule.get("needs", [])) or None
        request = DispatchInput(**rule["fields"], exclusions=exclusions, clarification=needs)
        result = desk.preview(envelope, request, ObjectiveWeights())
        assert result["status"] in rule["statuses"], envelope["request_id"]
        assert set(rule.get("flags", [])) <= set(result["flags"]), envelope["request_id"]


def test_splits_are_balanced_and_test_wording_is_unseen():
    train_inbox, train = load("train")
    test_inbox, test = load("test")
    supplied_inbox, supplied = load("supplied")
    for rubric in (train, test):
        assert Counter(case["course_kind"] for case in rubric["cases"].values()) == rubric["course_kind_counts"]
        assert set(rubric["course_kind_counts"]) == set(supplied["course_kind_counts"])
    assert len(train["cases"]) + len(test["cases"]) == 105
    templates = {
        name: {case["template"] for case in rubric["cases"].values()}
        for name, rubric in (("train", train), ("test", test))
    }
    assert not templates["train"] & templates["test"]
    texts = [item["text"] for item in train_inbox + test_inbox + supplied_inbox]
    assert len(texts) == len(set(texts))
