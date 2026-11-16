"""Agreement between the two independent reply raters (examples/human_reply_labels_v1.json).

The default run needs no extra packages:

    uv run python scripts/reply_label_agreement.py

--sheets also checks each rater sheet against its recorded SHA-256 and re-reads the labels.
It needs openpyxl, which is not a project dependency, so run it outside the project env:

    uv run --no-project --with openpyxl python scripts/reply_label_agreement.py --sheets
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "examples" / "human_reply_labels_v1.json"
COLUMNS = {"decision": 11, "explanation": 13}


def cohen_kappa(x, y):
    n = len(x)
    observed = sum(a == b for a, b in zip(x, y)) / n
    cx, cy = Counter(x), Counter(y)
    expected = sum(cx[k] * cy[k] for k in set(cx) | set(cy)) / (n * n)
    kappa = None if expected == 1 else (observed - expected) / (1 - expected)
    return observed, expected, kappa


def check_sheets(data):
    try:
        from openpyxl import load_workbook
    except ModuleNotFoundError:
        raise SystemExit(
            "--sheets needs openpyxl: uv run --no-project --with openpyxl "
            "python scripts/reply_label_agreement.py --sheets"
        ) from None

    for key, rater in data["raters"].items():
        path = ROOT / rater["sheet"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != rater["sheet_sha256"]:
            raise SystemExit(f"Rater {key}: sheet hash does not match {rater['sheet']}")
        rows = load_workbook(path, data_only=True)["Labels"].iter_rows(min_row=2, values_only=True)
        for row in rows:
            if row[0]:
                for question, col in COLUMNS.items():
                    if row[col] != rater["labels"][row[0]][question]:
                        raise SystemExit(f"Rater {key}, {row[0]}: {question} differs from the sheet")
    print("Sheets match their recorded hashes and labels.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheets", action="store_true")
    args = parser.parse_args()
    data = json.loads(LABELS.read_text(encoding="utf-8"))
    if args.sheets:
        check_sheets(data)
    a, b = data["raters"]["A"]["labels"], data["raters"]["B"]["labels"]
    ids = sorted(a)
    print(f"Cases: {len(ids)}")
    for question in COLUMNS:
        x = [a[i][question] for i in ids]
        y = [b[i][question] for i in ids]
        _observed, expected, kappa = cohen_kappa(x, y)
        k = "undefined" if kappa is None else f"{kappa:.2f}"
        disagree = [i for i in ids if a[i][question] != b[i][question]]
        print(
            f"\n{question}: agree {sum(p == q for p, q in zip(x, y))}/{len(ids)}, "
            f"chance agreement {expected:.3f}, Cohen's kappa {k}"
        )
        print(f"  rater A: {dict(Counter(x))}")
        print(f"  rater B: {dict(Counter(y))}")
        print(f"  disagreements: {', '.join(disagree) or 'none'}")
        flagged = [i for i in ids if a[i][question] != "Yes" or b[i][question] != "Yes"]
        print(f"  not 'Yes' by at least one rater: {', '.join(flagged) or 'none'}")


if __name__ == "__main__":
    main()
