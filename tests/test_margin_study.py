import pytest

from dss5105 import margin_study
from dss5105.evaluate import SPRINT1_PRESETS as PRESETS
from dss5105.harness import Simulator, eligible_workshops


def series(**late_days):
    rows = {name: {"late days": value, "% late": 1.0, "cost": 10.0} for name, value in late_days.items()}
    return {"normal_metrics": rows, "metrics": rows}


def test_grid_keeps_lateness_as_a_candidate_and_varies_only_the_declared_terms():
    grid = margin_study.grid()
    assert grid["lateness"] == PRESETS["lateness"]
    assert len(grid) == 1 + 2 * len(margin_study.BUFFERS)
    for name, weights in grid.items():
        if name != "lateness":
            assert weights.lateness == 1.0
            assert sorted((weights.defects, weights.cost)) == [0.0, margin_study.SECONDARY_WEIGHT]


def test_selection_is_lateness_first_and_can_choose_no_change():
    assert margin_study.select(series(lateness=0.2, cost_buffer10=0.1), ["lateness", "cost_buffer10"]) == (
        "cost_buffer10"
    )
    assert margin_study.select(series(lateness=0.1, cost_buffer10=0.2), ["lateness", "cost_buffer10"]) == ("lateness")


@pytest.mark.parametrize("seed", [5105, 5109])
def test_closure_oracle_only_chooses_eligible_workshops(seed):
    sim = Simulator(shock=True, seed=seed)
    oracle = margin_study.closure_oracle(seed)
    choices = []

    def record(batch, workshops, queues):
        choice = oracle(batch, workshops, queues)
        assert choice in {w.workshop_id for w in eligible_workshops(batch, workshops)}
        choices.append(choice)
        return choice

    sim.run(record, "oracle")
    assert len(choices) == len(sim.batches)
