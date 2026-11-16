"""Cohen's kappa between the two independent request-kind labellings of inbox R01-R30.

By default this reads examples/human_rater_labels_v1.json, a committed export of both
raters' labels, so anyone can reproduce the figures offline with no extra packages:

    uv run python scripts/rater_agreement.py

The original rater sheets are committed unchanged in examples/rater_sheets/. Their
SHA-256 hashes are recorded under "sources" in examples/human_request_kinds_v1.json and in
the export. To regenerate the export from the sheets and check it against them (the sheet
readers are not project dependencies):

    uv run --no-project --with openpyxl --with numbers-parser --with "protobuf>=7.36.2" \
        python scripts/rater_agreement.py --sheets examples/rater_sheets/rater_blank2.xlsx \
        examples/rater_sheets/human_labelled_cases.numbers

`shasum -a 256` of those two sheets must also match the recorded hashes.

Labels are lower-cased, spaces become underscores, and the one typo ("complete_meltable")
is mapped to complete_meetable before comparison; the export keeps the raw labels too.
Agreement here describes these two raters on request kinds only, not the reliability of
labelling in general. No provider calls.
"""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADJUDICATED = ROOT / "examples" / "human_request_kinds_v1.json"
RUBRIC = ROOT / "examples" / "chat_rubric.json"
EXPORT = ROOT / "examples" / "human_rater_labels_v1.json"
TYPOS = {"complete_meltable": "complete_meetable"}


def normalise(value) -> str:
    text = re.sub(r"\s+", "_", str(value or "").strip().lower())
    return TYPOS.get(text, text)


def kinds_by_id(rows) -> dict[str, str]:
    rows = [list(row) for row in rows]
    header = [str(cell or "").strip().lower() for cell in rows[0]]
    id_col, kind_col = header.index("request_id"), header.index("kind")
    return {str(r[id_col]).strip(): str(r[kind_col]) for r in rows[1:] if str(r[id_col] or "").strip().startswith("R")}


def read_rater_a(path: Path) -> dict[str, str]:
    import openpyxl

    return kinds_by_id(
        openpyxl.load_workbook(path, data_only=True)["rater-niyanthri-kind-only"].iter_rows(values_only=True)
    )


def read_rater_b(path: Path) -> dict[str, str]:
    import numbers_parser

    document = numbers_parser.Document(path)
    table = next(t for s in document.sheets for t in s.tables if t.name == "blank_sheet")
    return kinds_by_id(table.rows(values_only=True))


def export_from_sheets(rater_a: Path, rater_b: Path, sources: dict[str, str]) -> dict:
    for path in (rater_a, rater_b):
        if sources.get(path.name) != hashlib.sha256(path.read_bytes()).hexdigest():
            raise SystemExit(f"{path.name} does not match the hash recorded in {ADJUDICATED.name}")
    raw = {"rater_a": read_rater_a(rater_a), "rater_b": read_rater_b(rater_b)}
    return {
        "version": "data-v3-human-rater-labels-v1",
        "scope": "request_kind_only",
        "description": "Independent request-kind labels from two team members, before adjudication. "
        "Exported from the rater sheets by scripts/rater_agreement.py --sheets.",
        "sources": {
            "rater_a": {rater_a.name: sources[rater_a.name]},
            "rater_b": {rater_b.name: sources[rater_b.name]},
        },
        "normalisation": "lower-case, whitespace to underscore, typo complete_meltable -> complete_meetable",
        "raw": {rater: dict(sorted(labels.items())) for rater, labels in raw.items()},
        "labels": {rater: {i: normalise(v) for i, v in sorted(labels.items())} for rater, labels in raw.items()},
    }


def cohen(x: dict[str, str], y: dict[str, str], ids: list[str]) -> dict:
    n = len(ids)
    agree = sum(x[i] == y[i] for i in ids)
    cx, cy = Counter(x[i] for i in ids), Counter(y[i] for i in ids)
    expected = sum(cx[k] * cy[k] for k in set(cx) | set(cy)) / n / n
    observed = agree / n
    return {
        "agree": agree,
        "n": n,
        "observed": round(observed, 4),
        "expected": round(expected, 4),
        "kappa": round((observed - expected) / (1 - expected), 4),
        "disagreements": [i for i in ids if x[i] != y[i]],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sheets", nargs=2, type=Path, metavar=("RATER_A_XLSX", "RATER_B_NUMBERS"))
    args = parser.parse_args()
    adjudicated = json.loads(ADJUDICATED.read_text())
    if args.sheets:
        export = export_from_sheets(*args.sheets, adjudicated["sources"])
        text = json.dumps(export, indent=2) + "\n"
        if EXPORT.exists() and EXPORT.read_text() != text:
            print(f"note: {EXPORT.name} differs from the sheets; rewriting it")
        EXPORT.write_text(text)
    export = json.loads(EXPORT.read_text())
    for rater, source in export["sources"].items():
        for name, digest in source.items():
            if adjudicated["sources"].get(name) != digest:
                raise SystemExit(f"{EXPORT.name}: {rater} source hash differs from {ADJUDICATED.name}")

    a, b = export["labels"]["rater_a"], export["labels"]["rater_b"]
    final = {k: v["kind"] for k, v in adjudicated["cases"].items()}
    rubric = {k: v["course_kind"] for k, v in json.loads(RUBRIC.read_text())["cases"].items()}
    ids = sorted(final)
    pairs = {
        "rater_a_vs_rater_b": (a, b),
        "rater_a_vs_adjudicated": (a, final),
        "rater_b_vs_adjudicated": (b, final),
        "rater_a_vs_rubric": (a, rubric),
        "rater_b_vs_rubric": (b, rubric),
        "adjudicated_vs_rubric": (final, rubric),
    }
    kinds = sorted({a[i] for i in ids} | {b[i] for i in ids} | set(final.values()))
    output = {
        "agreement": {name: cohen(x, y, ids) for name, (x, y) in pairs.items()},
        "counts": {
            name: dict(sorted(Counter(labels[i] for i in ids).items()))
            for name, labels in (("rater_a", a), ("rater_b", b), ("adjudicated", final))
        },
        "confusion_rows_a_cols_b": {
            "kinds": kinds,
            "rows": [[sum(a[i] == r and b[i] == c for i in ids) for c in kinds] for r in kinds],
        },
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
