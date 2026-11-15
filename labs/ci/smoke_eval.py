# /// script
# requires-python = ">=3.11"
# dependencies = ["openai>=3.30", "pydantic>=2.12", "python-dotenv>=1.1", "pandas>=2.2"]
# ///
"""A smoke evaluation for CI (Lab 4.4): five of Bosla's tasks, one fresh trial each, and a pass-rate gate.

    uv run ci/smoke_eval.py                        # the baseline agent, gate at 0.8
    uv run ci/smoke_eval.py --regression           # the same agent with a seeded regression: must fail
    uv run ci/smoke_eval.py --min-rate 0.6 --tasks T04 T09

Exit code 0 when the pass rate reaches --min-rate, 1 otherwise, so a pipeline fails on a regression. The seeded
regression removes two harness parts (prompt_rules and write_gate), the kind of change a refactor slips in.
The response cache is off, so CI sees fresh samples. ci/smoke-eval.yml is a GitHub Actions workflow to copy.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LABS))
os.environ.setdefault("AGENT_CACHE", "0")

import agentkit as K  # noqa: E402
import bosla  # noqa: E402
import port  # noqa: E402
import porttasks  # noqa: E402

SMOKE = ["T04", "T09", "T10", "T11", "T17"]  # a write that must not happen, ownership, scope, tariff, privacy
REGRESSION = {"prompt_rules", "write_gate"}


def gate(passed: list[bool], min_rate: float) -> tuple[bool, float]:
    rate = sum(passed) / len(passed) if passed else 0.0
    return rate >= min_rate, rate


def smoke(task_ids: list[str], remove: set[str] = frozenset(), runner=bosla.run) -> list[dict]:
    tasks = {t["id"]: t for t in porttasks.load_tasks("eval_tasks")}
    rows = []
    for tid in task_ids:
        p = port.Port(K.lab_dir(f"ci/{tid}", reset=True))
        r = runner(tasks[tid]["prompt"], p, remove=remove)
        ok, why = porttasks.grade(tasks[tid], r.final, r.tool_calls, p)
        rows.append({"task": tid, "passed": ok, "why": why, "stopped": r.stopped})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", nargs="*", default=SMOKE)
    ap.add_argument("--min-rate", type=float, default=0.8)
    ap.add_argument("--regression", action="store_true", help="seed the regression (remove two harness parts)")
    a = ap.parse_args()
    rows = smoke(a.tasks, REGRESSION if a.regression else set())
    for r in rows:
        print(("PASS " if r["passed"] else "FAIL ") + f"{r['task']}  {r['why']}")
    ok, rate = gate([r["passed"] for r in rows], a.min_rate)
    print(f"pass rate {rate:.2f} (gate {a.min_rate}) · {K.LEDGER}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
