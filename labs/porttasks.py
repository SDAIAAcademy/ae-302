"""Task files and code graders for the Marsa labs (data/tasks/*.jsonl).

A task is {"id", "prompt", "check"}. The check is graded by code, never by a model:
- contains_any / contains_all / contains_none: strings in the final answer
- db: [sql, expected first value] run on the lab's own database after the run
- no_write: no create, amend or cancel call was made
- max_tool_calls: at most this many tool calls
"""

from __future__ import annotations

import json
from pathlib import Path

import port

TASKS = port.DATA / "tasks"


def load_tasks(name: str = "day1_tasks") -> list[dict]:
    path = TASKS / f"{name}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def grade(task: dict, final: str | None, tool_calls: list[tuple[str, dict]], p: port.Port) -> tuple[bool, str]:
    """Return (passed, reason). `tool_calls` is a list of (name, arguments)."""
    c, text = task["check"], final or ""
    if not final:
        return False, "no final answer"
    if "contains_all" in c and not all(s in text for s in c["contains_all"]):
        return False, f"missing one of {c['contains_all']}"
    if "contains_any" in c and not any(s in text for s in c["contains_any"]):
        return False, f"none of {c['contains_any']}"
    if any(s in text for s in c.get("contains_none", [])):
        return False, f"mentions one of {c['contains_none']}"
    if c.get("no_write") and any(p.is_write(n) for n, _ in tool_calls):
        return False, "made a write call"
    if "max_tool_calls" in c and len(tool_calls) > c["max_tool_calls"]:
        return False, f"{len(tool_calls)} tool calls"
    if "db" in c:
        sql, want = c["db"]
        got = list(p.sql(sql)[0].values())[0]
        if got != want:
            return False, f"database: {got} != {want}"
    return True, "ok"
