"""Retain reproducible workshop lookup and workload evidence without provider calls."""

import argparse
import json
from pathlib import Path

from dss5105.dispatch import ROOT, DispatchDesk, LoadScenario, WorkshopQuery


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/evidence/workshop-tools.json")
    args = parser.parse_args()
    desk = DispatchDesk()
    evidence = {
        "register": desk.query_register(WorkshopQuery(category="TOPS", pieces=1500, due_date="2026-04-15")),
        "extra_work": desk.probe_load(LoadScenario("W1", "TOPS", 1500, 1500, "2026-04-15")),
        "capped_workshop": desk.probe_load(LoadScenario("W8", "TOPS", 100, 301, "2026-04-15")),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n")
    print(f"Saved read-only tool evidence: {args.output}")


if __name__ == "__main__":
    main()
