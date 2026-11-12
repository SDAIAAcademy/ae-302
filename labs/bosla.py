"""Bosla, the reference agent of Days 3 and 4: the Day 1 loop (agentkit.run_agent) inside a harness of named parts.

    import bosla, port
    p = port.Port(K.lab_dir("D3_1", reset=True))
    run = bosla.run(task, p)                              # the full harness
    run = bosla.run(task, p, remove={"useful_errors"})    # the same agent without one part

Every Day 3 and Day 4 lab starts from this file, so none depends on an earlier lab's code.
"""

from __future__ import annotations

import json
from datetime import date

import agentkit as K
import port

CONTEXT_FILE = (K.DATA / "bosla" / "AGENTS.md").read_text(encoding="utf-8")
MINIMAL_PROMPT = "You are a booking assistant for a port. Use the tools."

PARTS = {
    "prompt_rules": "the system prompt: scope, citing circulars, never revealing other agents' data, asking before writes",
    "context_file": "the context file data/bosla/AGENTS.md appended to the prompt",
    "useful_errors": "tool errors that say what to send instead (removed: every error reads 'failed')",
    "step_budget": "a budget of 8 model calls (removed: 40)",
    "write_gate": "writes run only when the agent's message says 'I confirm' (removed: every write runs)",
    "verify": "Lab 3.3: every booking is checked against the schedule before the loop may stop (off unless asked)",
}
DEFAULT_OFF = {"verify"}


def write_gate(task: str):
    """A permission hook: write tools need the words 'I confirm' in the agent's own message."""
    confirmed = "confirm" in task.lower() or "أؤكد" in task

    def permission(name: str, args: dict) -> str:
        if name in port.Port.WRITE_TOOLS and not confirmed:
            return "deny"
        return "allow"

    return permission


def violations(p: port.Port, booking_ids: list[str]) -> list[str]:
    """Lab 3.3's check: each booking against the berth rules of TC-03 and the rest of the schedule."""
    problems = []
    for bid in booking_ids:
        rows = p.sql("SELECT b.*, v.name, v.kind AS vkind, v.loa_m, v.draft_m, t.kind AS bkind, t.length_m, t.depth_m "
                     "FROM bookings b JOIN vessels v USING (vessel_id) JOIN berths t USING (berth_id) "
                     "WHERE booking_id = ?", (bid,))
        if not rows or rows[0]["status"] == "cancelled":
            continue
        b = rows[0]
        if b["vkind"] != b["bkind"]:
            problems.append(f"{bid}: {b['name']} is {b['vkind']} but {b['berth_id']} takes {b['bkind']} (TC-03)")
        if b["loa_m"] + 20 > b["length_m"]:
            problems.append(f"{bid}: {b['name']} is too long for {b['berth_id']} (TC-03)")
        ukc = round(b["depth_m"] - b["draft_m"], 1)
        if ukc < port.MIN_UKC_M:
            problems.append(f"{bid}: under-keel clearance at {b['berth_id']} is {ukc} m, below 1.0 m (TC-03). "
                            "Amend to a berth from find_windows, or cancel.")
        start = date.fromisoformat(b["arrival"])
        clash = p._busy(b["berth_id"], start, b["days"], ignore=bid)
        if clash:
            problems.append(f"{bid}: overlaps {', '.join(clash)} on {b['berth_id']}")
    return problems


def run(task: str, p: port.Port, remove: set[str] | frozenset = frozenset(), add: set[str] | frozenset = frozenset(),
        verbose: bool = False, **kw) -> K.Run:
    """Run Bosla on one task with every harness part except those in `remove` (and `verify` only if in `add`)."""
    on = (set(PARTS) - DEFAULT_OFF - set(remove)) | set(add)
    system = port.SYSTEM_PROMPT if "prompt_rules" in on else MINIMAL_PROMPT
    if "context_file" in on:
        system += "\n\n" + CONTEXT_FILE
    hooks = {}
    if "write_gate" in on:
        hooks["permission"] = write_gate(task)
    if "useful_errors" not in on:
        hooks["after_tool"] = lambda name, args, out: '{"error": "failed"}' if out.startswith('{"error"') else None
    max_steps = 8 if "step_budget" in on else 40
    r = K.run_agent(task, p.tools(), system=system, max_steps=max_steps, verbose=verbose, **hooks, **kw)
    if "verify" in on:
        r = _verified(task, p, r, system, max_steps, hooks, verbose, kw)
    return r


def touched(r: K.Run, p: port.Port) -> list[str]:
    """Booking IDs this run created or changed (from its tool calls and the audit log)."""
    ids = [a.get("booking_id") for n, a in r.tool_calls if n in ("amend_booking",) and a.get("booking_id")]
    ids += [json.loads(row["detail"])["booking_id"] for row in p.sql("SELECT detail FROM audit_log WHERE action = 'create_booking'")]
    return sorted(set(ids))


def _verified(task, p, r, system, max_steps, hooks, verbose, kw, rounds: int = 2) -> K.Run:
    for _ in range(rounds):
        problems = violations(p, touched(r, p))
        if not problems or r.stopped != "done":
            return r
        note = "Verification failed. Fix these before you finish:\n" + "\n".join(f"- {x}" for x in problems)
        r.trace.append(K.Event("guard", note))
        history = [m for m in r.state if m.get("role") != "system"]  # the final answer is already in the state
        nxt = K.run_agent(note, p.tools(), system=system, history=history, max_steps=max_steps, verbose=verbose, **hooks, **kw)
        nxt.trace = r.trace + nxt.trace
        nxt.tool_calls = r.tool_calls + nxt.tool_calls
        nxt.steps += r.steps
        r = nxt
    return r
