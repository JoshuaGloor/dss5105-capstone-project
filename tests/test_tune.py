from copy import deepcopy

import pytest

from dss5105.evaluate import SPRINT1_PRESETS as PRESETS
from dss5105.harness import Simulator
from dss5105.tune import run_tuning, select_candidates, summarize


def test_summary_distinguishes_batch_exposure_from_piece_weighting():
    workshops = Simulator().workshops
    outcomes = [
        {"workshop": "W1", "pieces": 100, "turnaround": 2.0, "late": False, "defective": False, "cost": 150},
        {"workshop": "W2", "pieces": 900, "turnaround": 4.0, "late": True, "defective": True, "cost": 1170},
    ]
    summary = summarize(outcomes, workshops)
    assert summary["late_count"] == 1
    assert summary["late_pct"] == 50
    assert summary["defect_pct"] == 50
    assert summary["mean_days"] == 3
    assert summary["p90_days"] == 4
    assert summary["expected_batch_defect_pct"] == pytest.approx(7.5)
    assert summary["cost"] == 1320
    assert summary["max_share_pct"] == 90
    with pytest.raises(ValueError, match="empty replay"):
        summarize([], workshops)


def test_selection_respects_lateness_guard_and_keeps_distinct_preferences():
    development = {
        "fast": {"metrics": {"late_count": 1, "cost": 120, "expected_batch_defect_pct": 8}},
        "cheap": {"metrics": {"late_count": 2, "cost": 90, "expected_batch_defect_pct": 7}},
        "quality": {"metrics": {"late_count": 2, "cost": 110, "expected_batch_defect_pct": 3}},
        "too_late": {"metrics": {"late_count": 3, "cost": 50, "expected_batch_defect_pct": 1}},
    }
    assert select_candidates(development, reference_late_count=2) == {
        "lateness_first": "fast",
        "cost_at_reference_lateness": "cheap",
        "quality_at_reference_lateness": "quality",
    }
    with pytest.raises(ValueError, match="reference late count"):
        select_candidates(development, reference_late_count=0)


def test_check_seeds_do_not_change_development_selection_or_presets():
    original_presets = deepcopy(PRESETS)
    first = run_tuning(check_seeds=(5106,), secondary_weights=(0.0, 0.1))
    second = run_tuning(check_seeds=(5110,), secondary_weights=(0.0, 0.1))
    assert first["development"] == second["development"]
    assert first["selected"] == second["selected"]
    assert first["shared_shock"] == second["shared_shock"]
    assert PRESETS == original_presets
    for name, runs in first["checks"].items():
        assert {row["seed"] for row in runs} == {5106}
        assert {row["shock"] for row in runs} == {False, True}
        for row in runs:
            assert row["metrics"]["batch_count"] == len(row["outcomes"])
            assert len({outcome["order_id"] for outcome in row["outcomes"]}) == len(row["outcomes"])


@pytest.mark.parametrize("check_seeds", [(), (5105,), (5106, 5106)])
def test_check_seed_validation(check_seeds):
    with pytest.raises(ValueError, match="Check seeds"):
        run_tuning(check_seeds=check_seeds)
