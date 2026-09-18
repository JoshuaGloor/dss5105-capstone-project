import csv
import io
import json
import sys

import pytest

from dss5105 import prototype


def test_bundle_keeps_effective_preferences_and_same_comparison_snapshot():
    bundle = prototype.build_bundle()
    assert set(bundle["previews"]) == {row["request_id"] for row in bundle["inbox"]}
    for variants in bundle["previews"].values():
        assert len({result["snapshot"]["id"] for result in variants.values()}) == 1
    explicit = bundle["previews"]["R21"]
    assert explicit["defects"]["effective_weights"] == explicit["lateness"]["effective_weights"]
    for variants in bundle["previews"].values():
        for result in variants.values():
            for candidate in result["candidates"]:
                assert candidate["display"]["cost"] == f"{candidate['estimate']['cost']:,.2f}"


def test_annotation_sheet_has_no_predicted_answers():
    inbox = [{"request_id": "R01", "requester": "A", "time": "09:00", "text": 'A request, with "quotes".'}]
    rows = list(csv.DictReader(io.StringIO(prototype.annotation_sheet(inbox))))
    assert len(rows) == 1
    assert {key: rows[0][key] for key in inbox[0]} == inbox[0]
    assert all(value == "" for key, value in rows[0].items() if key not in inbox[0])


def test_generator_embeds_safe_reproducible_data_and_preserves_annotations(tmp_path, monkeypatch):
    output = tmp_path / "index.html"
    evidence = tmp_path / "evidence.json"
    annotations = tmp_path / "labels.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        ["prototype", "--output", str(output), "--evidence", str(evidence), "--annotations", str(annotations)],
    )
    prototype.main()
    html = output.read_text()
    bundle = json.loads(evidence.read_text())
    embedded = html.split('<script id="dispatch-data" type="application/json">')[1].split("</script>")[0]
    assert json.loads(embedded) == bundle
    assert "__DISPATCH_DATA__" not in html
    assert prototype.build_bundle() == bundle
    annotations.write_text("existing human annotations")
    with pytest.raises(SystemExit):
        prototype.main()
    assert annotations.read_text() == "existing human annotations"
