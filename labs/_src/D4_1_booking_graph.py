# %% [markdown]
# # Lab 4.1 · A booking graph with an approval gate
#
# Day 4 · Session 1 · 25 min. Some booking changes need the duty harbour master, Captain Huda Al-Harbi, before they
# take effect (circular TC-06): dangerous goods, under-keel clearance below 1.0 m, or dues that move by more than
# SAR 10,000. In this lab the change flow becomes an explicit **state graph** with checkpoints: it pauses at the
# gate, waits, resumes after approval, and survives a restart. Every node here is code; no model is needed.
#
# **Reference state.** `port.py` and a fresh port database. Nothing from Days 1 to 3.
#
# **Tasks**
# - [ ] 1 · State and the fact-finding node (6')
# - [ ] 2 · The risk node and the router (6')
# - [ ] 3 · The gate: interrupt, approve or reject, and a test per path (7')
# - [ ] 4 · Crash, restart, resume without repeating work (6')
# - [ ] ✱ Stretch · Would an approver notice a bad change?

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/agentic-ai.git"
    if not Path("/content/agentic-ai").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/agentic-ai"], check=True)
    os.chdir("/content/agentic-ai/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("agentkit.py").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())

import agentkit as K

# %%
import sqlite3
from collections import Counter
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

import port

WORK = K.lab_dir("D4_1", reset=True)
p = port.Port(WORK)
CALLS = Counter()  # how many times each node ran: the restart test reads it

# %% [markdown]
# ## 1 · State and the fact-finding node (6')
#
# The state is a typed dict that every node reads and updates. `facts` gathers what the gate needs: the booking,
# the vessel, the berth after the change, the under-keel clearance and the dues before and after.
#
# ✏️ **Exercise** · Write `find_facts(s)`: read the booking with `p.get_booking`, the vessel with `p.get_vessel`, the
# new berth from `p.list_berths()`, and compute `ukc_m` and `dues_before`/`dues_after` with `port.berth_hire`.

# %%
class Change(TypedDict, total=False):
    booking_id: str
    agent_code: str
    change: dict  # any of: arrival, berth_id, days
    facts: dict
    reasons: list[str]
    decision: dict
    result: dict
    log: list[str]


def find_facts(s: Change) -> dict:
    CALLS["find_facts"] += 1
    # BEGIN SOLUTION
    b = p.get_booking(s["booking_id"], s["agent_code"])
    v = p.get_vessel(b["vessel_id"])
    berth_id = s["change"].get("berth_id", b["berth_id"])
    depth = next(x["depth_m"] for x in p.list_berths() if x["berth_id"] == berth_id)
    days = s["change"].get("days", b["days"])
    facts = {"vessel": v["name"], "dangerous_goods": b["dangerous_goods"], "berth_before": b["berth_id"],
             "berth_after": berth_id, "arrival_before": b["arrival"], "arrival_after": s["change"].get("arrival", b["arrival"]),
             "days_before": b["days"], "days_after": days, "ukc_m": round(depth - v["draft_m"], 1),
             "dues_before": port.berth_hire(v["gross_tonnage"], b["days"], b["dangerous_goods"]),
             "dues_after": port.berth_hire(v["gross_tonnage"], days, b["dangerous_goods"])}
    # END SOLUTION
    return {"facts": facts, "log": s.get("log", []) + ["facts"]}


# %% [markdown]
# ## 2 · The risk node and the router (6')
#
# ✏️ **Exercise** · Write `assess_risk(s)` returning `reasons`: one line per TC-06 trigger that applies (dangerous
# goods; `ukc_m` below 1.0; dues moving by more than SAR 10,000). Then `route(s)`: `"approval"` when there is a
# reason, else `"apply"`.

# %%
def assess_risk(s: Change) -> dict:
    CALLS["assess_risk"] += 1
    f = s["facts"]
    # BEGIN SOLUTION
    reasons = []
    if f["dangerous_goods"]:
        reasons.append("carries dangerous goods (TC-06 a)")
    if f["ukc_m"] < port.MIN_UKC_M:
        reasons.append(f"under-keel clearance {f['ukc_m']} m, below 1.0 m (TC-06 b)")
    if abs(f["dues_after"] - f["dues_before"]) > port.APPROVAL_FEE_DELTA:
        reasons.append(f"dues move by SAR {f['dues_after'] - f['dues_before']:,} (TC-06 c)")
    # END SOLUTION
    return {"reasons": reasons, "log": s["log"] + ["risk"]}


def route(s: Change) -> str:
    # BEGIN SOLUTION
    return "approval" if s["reasons"] else "apply"
    # END SOLUTION


# %% [markdown]
# ## 3 · The gate (7')
#
# `interrupt(payload)` pauses the graph inside a node; the checkpointer saves the state; the caller receives the
# payload under `__interrupt__`. `graph.invoke(Command(resume=value), config)` continues the same node, where
# `interrupt(...)` now returns `value`. The `thread_id` names the run.
#
# ✏️ **Exercise** · Write `approval(s)`: interrupt with a payload a busy harbour master can judge in ten seconds
# (the booking, the vessel, **what changes**, before and after, and the reasons), then store the decision. Write
# `after_approval(s)`: `"apply"` if approved, else `"record"`.

# %%
def approval(s: Change) -> dict:
    CALLS["approval"] += 1
    f = s["facts"]
    # BEGIN SOLUTION
    payload = {"booking": s["booking_id"], "vessel": f["vessel"], "why_you": s["reasons"],
               "changes": {k: f"{f[k + '_before']} → {f[k + '_after']}" for k in ("berth", "arrival", "days", "dues")
                           if f[k + "_before"] != f[k + "_after"]}}
    decision = interrupt(payload)
    # END SOLUTION
    return {"decision": decision, "log": s["log"] + [f"approval: {decision.get('outcome')}"]}


def after_approval(s: Change) -> str:
    # BEGIN SOLUTION
    return "apply" if s["decision"].get("outcome") == "approve" else "record"
    # END SOLUTION


def apply(s: Change) -> dict:
    CALLS["apply"] += 1
    out = p.amend_booking(s["booking_id"], s["agent_code"], **s["change"])
    return {"result": out, "log": s["log"] + ["applied"]}


def record(s: Change) -> dict:
    CALLS["record"] += 1
    status = "applied" if s.get("result") else "rejected"
    p._audit("booking_change", {"booking_id": s["booking_id"], "status": status, "reasons": s.get("reasons", [])})
    return {"log": s["log"] + [f"recorded: {status}"]}


def build(checkpointer):
    g = StateGraph(Change)
    for name, fn in [("find_facts", find_facts), ("assess_risk", assess_risk), ("approval", approval),
                     ("apply", apply), ("record", record)]:
        g.add_node(name, fn)
    g.add_edge(START, "find_facts")
    g.add_edge("find_facts", "assess_risk")
    g.add_conditional_edges("assess_risk", route, ["approval", "apply"])
    g.add_conditional_edges("approval", after_approval, ["apply", "record"])
    g.add_edge("apply", "record")
    g.add_edge("record", END)
    return g.compile(checkpointer=checkpointer)


DB = WORK / "checkpoints.sqlite"
graph = build(SqliteSaver(sqlite3.connect(DB, check_same_thread=False)))
cfg = lambda t: {"configurable": {"thread_id": t}}  # noqa: E731

# %% [markdown]
# A test per path. Each case is a change request and, when the graph pauses, the harbour master's decision.
#
# ✏️ **Exercise** · Run the three cases. For each, check: where the graph paused (if at all), the final log, and the
# database after the run.

# %%
CASES = {
    "plain: move BK-24021 one day": ({"booking_id": "BK-24021", "agent_code": "NJM-4417", "change": {"arrival": "2026-11-10"}}, None),
    "dangerous goods, approved": ({"booking_id": "BK-24029", "agent_code": "SHL-2290", "change": {"arrival": "2026-11-12"}},
                                  {"outcome": "approve", "by": "Capt. Huda Al-Harbi"}),
    "dues +36,400, rejected": ({"booking_id": "BK-24017", "agent_code": "NJM-4417", "change": {"days": 10}},
                               {"outcome": "reject", "by": "Capt. Huda Al-Harbi", "note": "B01 is needed from 2026-11-07"}),
}
for name, (req, decision) in CASES.items():
    # BEGIN SOLUTION
    out = graph.invoke({**req, "log": []}, cfg(name))
    paused = out.get("__interrupt__")
    if paused:
        print(f"⏸ {name}: paused with", paused[0].value)
        out = graph.invoke(Command(resume=decision), cfg(name))
    print(f"   {name}: {out['log']}")
    # END SOLUTION
K.check(p.get_booking("BK-24021", "NJM-4417")["arrival"] == "2026-11-10", "plain change applied without the gate")
K.check(p.get_booking("BK-24029", "SHL-2290")["arrival"] == "2026-11-12", "dangerous goods change applied after approval")
K.check(p.get_booking("BK-24017", "NJM-4417")["days"] == 3, "rejected change not applied")

# %% [markdown]
# ## 4 · Crash, restart, resume (6')
#
# ✏️ **Exercise** · Start a gated change on a new thread and stop at the interrupt. Throw the graph away (as if the
# process died), build a new one on a **new** SQLite connection to the same file, read `get_state(...).next`, and
# resume with the approval. Show from `CALLS` that `find_facts` did not run again.

# %%
T = "restart: BK-24029 two more days"
graph.invoke({"booking_id": "BK-24029", "agent_code": "SHL-2290", "change": {"days": 5}, "log": []}, cfg(T))
before = CALLS["find_facts"]
del graph  # the process "dies"
# BEGIN SOLUTION
graph2 = build(SqliteSaver(sqlite3.connect(DB, check_same_thread=False)))
print("waiting at:", graph2.get_state(cfg(T)).next)
out = graph2.invoke(Command(resume={"outcome": "approve", "by": "Capt. Huda Al-Harbi"}), cfg(T))
# END SOLUTION
print(out["log"])
K.check(CALLS["find_facts"] == before and p.get_booking("BK-24029", "SHL-2290")["days"] == 5,
        "resumed after a restart without repeating the fact-finding")

# %% [markdown]
# ## ✱ Stretch · Would an approver notice?
#
# An approval prompt nobody reads is a rubber stamp. Write a second payload design that dumps every field of the
# booking (twenty lines), and give both to a colleague for ten seconds each on the "dues +36,400" case. Which one
# made the change visible? Write down what the payload must always lead with.

# %% [markdown]
# ## Checkpoint
#
# 1. Which decisions in this graph are made by code, which by a person, and which by a model?
# 2. What does the checkpointer save that lets the run survive a restart?
# 3. The gate fires on 40 of 50 changes a day. What happens to the quality of approvals, and what would you change?
