"""Load the unmodified course simulator from this source checkout."""

import importlib.util
import sys
from pathlib import Path

HARNESS_PATH = Path(__file__).resolve().parents[2] / "track2" / "harness" / "simulate.py"

if not HARNESS_PATH.is_file():
    raise FileNotFoundError("Run from a source checkout containing track2/harness/simulate.py")

_spec = importlib.util.spec_from_file_location("_dss5105_course_simulate", HARNESS_PATH)
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)

Simulator = _module.Simulator
Workshop = _module.Workshop
eligible_workshops = _module.eligible_workshops
random_choice = _module.random_choice
greedy_biggest = _module.greedy_biggest
cheapest = _module.cheapest
