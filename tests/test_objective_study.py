import json
from dataclasses import asdict

from dss5105 import objective_study as study
from dss5105.dispatch import ROOT
from dss5105.evaluate import PRESETS


def rows(**policies):
    """Development summaries: name -> (normal % late, late days, expected defects, max share, delta % late)."""
    out = {}
    for name, (late, days, defects, share, delta) in policies.items():
        row = {"% late": late, "late days": days, "expected % def pcs": defects, "max share": share}
        out[name] = {"normal": row, "shock": dict(row), "delta": {"% late": delta, "late days": delta / 10}}
    return {"policies": out}


def test_presets_are_the_frozen_study_choices():
    evidence = json.loads((ROOT / "docs" / "evidence" / "objective-study.json").read_text())
    frozen = evidence["frozen_weights"]
    assert {name: asdict(weights) for name, weights in PRESETS.items()} == {name: frozen[name] for name in PRESETS}
    assert set(evidence["report"]["seeds"]) == set(range(study.REPORT_SEED, study.REPORT_SEED + study.REPORT_SEEDS))
    assert evidence["selected"]["lateness"] == "lateness"


def test_grids_keep_the_reservation_and_vary_only_their_own_terms():
    grids = study.objective_grids(1.0)
    assert len(grids["hybrid"]) == len(study.HYBRID_DEFECTS) * len(study.HYBRID_BUFFERS)
    for objective, grid in grids.items():
        for weights in grid.values():
            assert weights.capacity_reservation == 1.0
            assert weights.cost == 0
            if objective in ("hybrid", "fairness", "robustness"):
                assert weights.lateness == 1.0
    assert all(w.fairness == w.robustness == 0 for w in grids["hybrid"].values())


def test_lateness_selection_breaks_ties_toward_the_unit_rate():
    grid = study.lateness_grid()
    tied = rows(**{name: (2.0, 0.1, 7.0, 28.0, 0.1) for name in grid})
    assert grid[study.select_lateness(tied, grid)].capacity_reservation == 1.0


def test_hybrid_needs_primary_lateness_before_secondary_defects():
    dev = rows(
        lateness=(1.7, 0.10, 7.0, 28.0, 0.2),
        good=(1.8, 0.08, 6.0, 40.0, 0.4),
        too_late=(2.5, 0.08, 4.0, 40.0, 0.4),
        slower=(1.7, 0.20, 5.0, 40.0, 0.4),
    )
    grid = {"good": None, "too_late": None, "slower": None}
    assert study.select_hybrid(dev, grid, "lateness") == "good"
    assert study.select_hybrid(dev, {"too_late": None}, "lateness") == "lateness"


def test_defects_respects_the_random_guardrail_with_margin():
    dev = rows(random=(30.0, 6.0, 6.0, 22.0, 3.0), safe=(20.0, 2.0, 5.0, 40.0, 1.0), edge=(29.0, 2.0, 4.0, 40.0, 1.0))
    assert study.select_defects(dev, {"safe": None, "edge": None}) == "safe"
    assert study.select_defects(dev, {"edge": None}) is None


def test_fairness_and_robustness_rules():
    dev = rows(
        lateness=(1.7, 0.1, 7.0, 28.0, 0.25),
        spread=(2.0, 0.1, 7.0, 21.0, 0.6),
        late_spread=(4.0, 0.2, 7.0, 18.0, 0.6),
    )
    assert study.select_fairness(dev, {"spread": None, "late_spread": None}, "lateness") == "spread"
    grid = study.objective_grids(1.0)["robustness"]
    calm = next(iter(grid))
    deltas = rows(**{name: (1.7, 0.1, 7.0, 28.0, 0.5) for name in grid})
    deltas["policies"][calm]["delta"]["% late"] = 0.1
    assert study.select_robustness(deltas, grid) == calm
