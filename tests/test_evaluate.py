import json
from dataclasses import asdict

import pytest

from dss5105 import evaluate
from dss5105.allocator import ObjectiveWeights

REFERENCES = {"random", "greedy_biggest", "cheapest", "earliest_finish"}


def test_default_cli_keeps_all_presets(tmp_path, capsys):
    output = tmp_path / "default.json"
    evaluate.main(["--output", str(output)])
    result = json.loads(output.read_text())
    assert set(result["policies"]) == REFERENCES | set(evaluate.PRESETS)
    assert result["weights"] == {name: asdict(weights) for name, weights in evaluate.PRESETS.items()}
    assert "Objective weights:" in capsys.readouterr().out


def test_selected_preset_keeps_reference_comparisons(tmp_path):
    output = tmp_path / "preset.json"
    evaluate.main(["--preset", "defects", "--shock", "--seed", "5106", "--output", str(output)])
    result = json.loads(output.read_text())
    assert result["shock"] is True
    assert result["seed"] == 5106
    assert set(result["policies"]) == REFERENCES | {"defects"}
    assert result["weights"] == {"defects": asdict(evaluate.PRESETS["defects"])}


def test_custom_weights_are_applied_and_unspecified_weights_are_zero(tmp_path):
    original_presets = dict(evaluate.PRESETS)
    output = tmp_path / "nested" / "custom.json"
    evaluate.main(["--defects-weight", "1", "--output", str(output)])
    result = json.loads(output.read_text())
    assert result["weights"] == {"custom": asdict(ObjectiveWeights(lateness=0.0, defects=1.0))}
    assert result["weights"]["custom"]["fairness"] == result["weights"]["custom"]["robustness"] == 0.0
    assert set(result["policies"]) == REFERENCES | {"custom"}
    preset = evaluate.run_experiment(configurations={"defects_only": ObjectiveWeights(lateness=0, defects=1)})
    assert result["policies"]["custom"] == preset["policies"]["defects_only"]
    assert evaluate.PRESETS == original_presets


def test_custom_mixture_matches_programmatic_configuration(tmp_path):
    output = tmp_path / "mix.json"
    evaluate.main(
        [
            "--lateness-weight",
            "1",
            "--defects-weight",
            "0.05",
            "--cost-weight",
            "0.1",
            "--shock",
            "--output",
            str(output),
        ]
    )
    result = json.loads(output.read_text())
    expected = evaluate.run_experiment(
        shock=True, configurations={"mixture": ObjectiveWeights(lateness=1, defects=0.05, cost=0.1)}
    )
    assert result["policies"]["custom"] == expected["policies"]["mixture"]
    assert result["weights"]["custom"] == expected["weights"]["mixture"]


@pytest.mark.parametrize(
    "arguments",
    [
        ["--preset", "unknown"],
        ["--preset", "lateness", "--cost-weight", "0.1"],
        ["--lateness-weight", "-1"],
        ["--defects-weight", "nan"],
        ["--cost-weight", "inf"],
        ["--lateness-weight", "0"],
        ["--lateness-weight", "text"],
        ["--seeds", "0"],
        ["--seeds", "-2"],
        ["--deadline-buffer-days", "3"],
        ["--preset", "lateness", "--deadline-buffer-days", "3"],
        ["--lateness-weight", "1", "--deadline-buffer-days", "-1"],
        ["--lateness-weight", "1", "--deadline-buffer-days", "nan"],
    ],
)
def test_invalid_cli_configuration_fails_before_running_or_writing(arguments, tmp_path, monkeypatch, capsys):
    def unexpected_run(**kwargs):
        pytest.fail("Invalid input must not start an experiment")

    monkeypatch.setattr(evaluate, "run_experiment", unexpected_run)
    output = tmp_path / "invalid.json"
    with pytest.raises(SystemExit) as exc:
        evaluate.main([*arguments, "--output", str(output)])
    assert exc.value.code == 2
    assert "error:" in capsys.readouterr().err
    assert not output.exists()


@pytest.mark.parametrize("configurations", [{}, {"random": ObjectiveWeights()}])
def test_programmatic_configuration_cannot_remove_or_replace_reference_policies(configurations):
    with pytest.raises(ValueError, match="reference policy name"):
        evaluate.run_experiment(configurations=configurations)


def test_seed_average_matches_official_helper_and_retains_paired_controls():
    from dss5105.allocator import earliest_finish, make_allocator
    from dss5105.harness import average_over_seeds, cheapest, greedy_biggest, random_choice

    policies = dict(
        random=random_choice,
        greedy_biggest=greedy_biggest,
        cheapest=cheapest,
        earliest_finish=earliest_finish,
        lateness=make_allocator(ObjectiveWeights()),
    )
    result = evaluate.run_seed_series(shock=True, seeds=10, configurations={"lateness": ObjectiveWeights()})
    expected = average_over_seeds(policies, range(5105, 5115), shock=True)
    for name, metrics in expected.items():
        assert result["metrics"][name] == pytest.approx(metrics)
    assert result["seeds"] == list(range(5105, 5115))
    assert len(result["normal_runs"]) == len(result["runs"]) == 10
    for name, metrics in expected.items():
        for key in ("% late", "late days"):
            assert result["paired_deltas"][name][key] == pytest.approx(
                metrics[key] - result["normal_metrics"][name][key]
            )
    assert result["normal_lateness_guardrail"]["lateness"]


def test_seed_series_cli_exports_official_metrics(tmp_path):
    output = tmp_path / "series.json"
    evaluate.main(["--shock", "--seeds", "10", "--preset", "lateness", "--output", str(output)])
    result = json.loads(output.read_text())
    assert "late days" in result["metrics"]["lateness"]
    assert "% def pcs" in result["metrics"]["lateness"]
    assert result["normal_runs"][0]["seed"] == result["runs"][0]["seed"]
