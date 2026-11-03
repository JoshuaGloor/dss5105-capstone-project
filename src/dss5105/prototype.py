"""Build a portable HTML prototype from real offline dispatch tool outputs."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, read_inbox
from dss5105.evaluate import SPRINT1_PRESETS as PRESETS
from dss5105.replies import build_reply


def build_bundle() -> dict:
    """Previews for the three Sprint 1 configurations the HTML design reference was built around."""
    inbox = read_inbox()
    fixture_path = ROOT / "examples" / "dispatch_inputs.json"
    fixtures = json.loads(fixture_path.read_text())
    if set(fixtures) != {item["request_id"] for item in inbox}:
        raise ValueError("Draft fixtures must cover exactly the supplied inbox")
    desk = DispatchDesk()
    previews = {
        item["request_id"]: {
            name: desk.preview(item, DispatchInput(**fixtures[item["request_id"]]), weights)
            for name, weights in PRESETS.items()
        }
        for item in inbox
    }
    return {
        "as_of": desk.as_of.isoformat(),
        "inbox_count": str(len(inbox)),
        "inbox": inbox,
        "previews": previews,
        "replies": {
            rid: {name: build_reply(result) for name, result in by_preset.items()}
            for rid, by_preset in previews.items()
        },
        "preset_labels": {"lateness": "Lateness", "defects": "Defects", "hybrid": "Hybrid"},
        "fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        "interpretation_source": "Hand-authored development inputs; not model extraction or gold labels.",
    }


def annotation_sheet(inbox: list[dict]) -> str:
    """Blank independent annotation worksheet: deliberately no predicted labels."""
    buffer = io.StringIO(newline="")
    fields = [
        "request_id",
        "time",
        "requester",
        "text",
        "annotator",
        "expected_behaviors",
        "order_reference",
        "constraints_and_provenance",
        "date_interpretation",
        "acceptable_outcome",
        "supporting_evidence",
        "disagreement_notes",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(inbox)
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "prototype" / "index.html")
    parser.add_argument("--template", type=Path, default=ROOT / "docs" / "prototype" / "template.html")
    parser.add_argument("--evidence", type=Path, default=ROOT / "results" / "dispatch-previews.json")
    parser.add_argument("--annotations", type=Path, help="Create a NEW blank annotation CSV; never overwrite labels")
    args = parser.parse_args()
    if args.annotations and args.annotations.exists():
        parser.error("Annotation destination already exists; choose a new file to preserve labels")
    bundle = build_bundle()
    template = args.template.read_text()
    encoded = json.dumps(bundle, ensure_ascii=True, separators=(",", ":")).replace("<", "\\u003c")
    if template.count("__DISPATCH_DATA__") != 1:
        raise ValueError("Expected exactly one prototype data placeholder")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(template.replace("__DISPATCH_DATA__", encoded))
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(bundle, ensure_ascii=True, indent=2) + "\n")
    if args.annotations:
        args.annotations.parent.mkdir(parents=True, exist_ok=True)
        with args.annotations.open("x", encoding="utf-8", newline="") as file:
            file.write(annotation_sheet(bundle["inbox"]))
    print(f"Prototype: {args.output}")
    print(f"Tool evidence: {args.evidence}")
    print("Structured fixture replay only; no model invoked and no allocation committed.")


if __name__ == "__main__":
    main()
