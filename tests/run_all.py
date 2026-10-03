"""Every Reyna test, one command:  python tests/run_all.py

Deliberately not pytest. Phase 1's promise is `dependencies = []`, and a test
suite that needs an install to run is a suite that does not run on a fresh
checkout — which is when it matters most.

DISCOVERED, NOT LISTED. This held a hand-written list of filenames for a day,
which meant `test_pivot.py` was written, passing, and **not being run** — the
quietest possible failure and one that gets worse the longer nobody notices.
A suite you must remember to update is a suite that is wrong by default.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent

if __name__ == "__main__":
    tests = sorted(p for p in HERE.glob("test_*.py"))
    if not tests:
        print("no tests found - that is itself a failure")
        raise SystemExit(1)
    failed = []
    for t in tests:
        print(f"\n{'=' * 60}\n{t.name}\n{'=' * 60}", flush=True)
        if subprocess.call([sys.executable, str(t)]) != 0:
            failed.append(t.name)
    print()
    if failed:
        print("FAILED:", ", ".join(failed))
        raise SystemExit(1)
    print(f"OK - {len(tests)} test file(s) passed")
