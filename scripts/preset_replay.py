"""Replay saved live chat inputs through the dispatch tool under two weight configurations.

The Sprint 3 live run scored every request with the bare ObjectiveWeights() (lateness 1,
nothing else; recorded under "weights" in docs/evidence/sprint3-live-01f2524.json), while
the desk ships with the "hybrid" preset. This script feeds each case's validated,
model-extracted input back into DispatchDesk.preview under both, checks the bare replay
reproduces the saved live preview, and lists every case where the hybrid picks a different
workshop. The model's extraction is held fixed: this is a tool replay, not a new live run.

The raw run directory (results/sprint3-live-01f2524) is kept outside version control. Before
replaying, the script checks each split's manifest.json, summary.json and
source_snapshot.json against the hashes in the committed evidence file, and it records the
SHA-256 of every case file it reads. The committed result is
docs/evidence/preset-replay-01f2524.json; regenerate it with

    uv run python scripts/preset_replay.py results/sprint3-live-01f2524 \
        --out docs/evidence/preset-replay-01f2524.json

Deterministic and offline: no provider calls.
"""

import argparse
import dataclasses
import hashlib
import json
from pathlib import Path

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import DispatchDesk, DispatchInput
from dss5105.evaluate import DEFAULT_PRESET, PRESETS

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "evidence" / "sprint3-live-01f2524.json"
SPLITS = ("supplied", "test", "test_extra")
ARTIFACTS = ("manifest.json", "summary.json", "source_snapshot.json")
KEY = ("status", "recommendation", "alternative", "flags")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chosen(result: dict) -> tuple[str | None, dict | None]:
    workshop = result.get("recommendation") or result.get("alternative")
    candidate = next((c for c in result.get("candidates", []) if c["estimate"]["workshop_id"] == workshop), None)
    return workshop, candidate


def display(workshop: str | None, candidate: dict) -> dict:
    return {"workshop": workshop, **{k: candidate["display"][k] for k in ("lateness", "defects", "cost", "eta")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run", type=Path, help="Sprint 3 live run directory")
    parser.add_argument("--out", type=Path, help="write the JSON result here instead of stdout")
    args = parser.parse_args()
    evidence = json.loads(EVIDENCE.read_text())
    for split in SPLITS:
        expected = evidence["splits"][split]["artifact_sha256"]
        for name in ARTIFACTS:
            if sha256(args.run / split / name) != expected[name]:
                parser.error(f"{split}/{name} does not match {EVIDENCE.name}; wrong run directory?")

    desk = DispatchDesk()
    fields = {f.name for f in dataclasses.fields(DispatchInput)}
    case_hashes, reproduced, changed = {}, 0, []
    for split in SPLITS:
        for path in sorted((args.run / split).glob("*.json")):
            if path.name in ARTIFACTS:
                continue
            case_hashes[f"{split}/{path.name}"] = sha256(path)
            record = json.loads(path.read_text())
            saved = record["preview"]
            request = DispatchInput(**{k: v for k, v in saved["input"].items() if k in fields})
            bare = desk.preview(saved["request"], request, ObjectiveWeights())
            hybrid = desk.preview(saved["request"], request, PRESETS[DEFAULT_PRESET])
            reproduced += all(bare.get(k) == saved.get(k) for k in KEY)
            (wa, ca), (wb, cb) = chosen(bare), chosen(hybrid)
            if wa == wb or ca is None or cb is None:
                continue
            changed.append(
                {
                    "id": record["request"]["request_id"],
                    "status": bare["status"],
                    "same_state_and_flags": bare["status"] == hybrid["status"] and bare["flags"] == hybrid["flags"],
                    "bare": display(wa, ca),
                    "hybrid": display(wb, cb),
                    "hybrid_reasons": (hybrid.get("decision_basis") or {}).get("reasons", []),
                }
            )
    summary = {
        "description": "Offline replay of the Sprint 3 live run's extracted inputs under bare and shipped weights.",
        "bare_weights": dataclasses.asdict(ObjectiveWeights()),
        "shipped_preset": DEFAULT_PRESET,
        "shipped_weights": dataclasses.asdict(PRESETS[DEFAULT_PRESET]),
        "cases": len(case_hashes),
        "bare_replay_reproduces_saved_preview": reproduced,
        "hybrid_changes_workshop": len(changed),
        "hybrid_changes_state_or_flags": sum(not c["same_state_and_flags"] for c in changed),
        "hybrid_choice_later_than_bare": [
            c["id"] for c in changed if c["hybrid"]["lateness"] != c["bare"]["lateness"]
        ],
        "changed": changed,
        "case_sha256": case_hashes,
    }
    text = json.dumps(summary, indent=2, sort_keys=False) + "\n"
    if args.out:
        args.out.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
