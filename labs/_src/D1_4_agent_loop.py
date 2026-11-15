# %% [markdown]
# # Lab 1.4 · The agent loop from scratch
#
# Day 1 · Session 4 · 25 min. An agent is a model calling tools **in a loop** until a stop rule fires. In this lab
# you write that loop yourself, give it Bosla's tools over the three port services (schedule, tariff, booking), and
# run it on ten tasks with a trace per run.
#
# **AI policy: AI off.** Write `my_loop` without an assistant. That is the point of the lab: you will read every
# other harness this week against the twenty lines you write here.
#
# **Reference state.** The lab starts from a fresh copy of the port database and the tools of `port.py`; it uses
# nothing from Labs 1.1 to 1.3.
#
# **Tasks**
# - [ ] 1 · Write `my_loop()` with a step budget and a stop rule (8')
# - [ ] 2 · A trace per run (5')
# - [ ] 3 · Ten tasks, graded by code (8')
# - [ ] 4 · Break it: a tool that never finishes (4')
# - [ ] ✱ Stretch · Run one turn's tool calls in parallel

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/ae-302.git"
    if not Path("/content/agentic-ai").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/agentic-ai"], check=True)
    os.chdir("/content/agentic-ai/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("agentkit.py").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())

import agentkit as K
print("provider:", K.PROVIDER, "| model:", K.MODEL, "| cache:", K.USE_CACHE)

# %%
import json

import pandas as pd

import port
import porttasks

TOOLS_NAMES = port.Port.READ_TOOLS + port.Port.WRITE_TOOLS
print(TOOLS_NAMES)

# %% [markdown]
# ## 1 · Write `my_loop()` (8')
#
# ```text
# messages = [system, user]
# for step in 1..max_steps:                         ← the step budget
#     reply = model(messages, tools)
#     append reply
#     if reply has no tool calls: stop "done"       ← the model's completion signal
#     if this turn repeats the last turn's calls: stop "repeat"   ← no progress
#     run each call, append one tool message per call
# stop "max_steps"                                  ← the loop's own stop rule
# ```
#
# ✏️ **Exercise** · Implement `my_loop`. Use `K.chat(messages, tools=tools)` (it accepts Python functions) and
# `K.call_tool(by_name, name, arguments)`, which returns the result as JSON, or an error as JSON the model can act
# on. Append the assistant message with `msg.model_dump(exclude_none=True)`. Return a dict with `final` (text or
# `None`), `stopped` (`done`, `repeat` or `max_steps`), `steps`, `calls` (a list of `(name, args)`) and `trace`
# (a list of dicts, one per event).

# %%
def my_loop(task: str, tools: list, system: str = port.SYSTEM_PROMPT, max_steps: int = 8) -> dict:
    by_name = {t.__name__: t for t in tools}
    messages = [{"role": "system", "content": system}, {"role": "user", "content": task}]
    trace, calls, last = [{"kind": "user", "text": task}], [], None
    # BEGIN SOLUTION
    for step in range(1, max_steps + 1):
        msg = K.chat(messages, tools=tools).choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            trace.append({"kind": "final", "step": step, "text": msg.content})
            return {"final": msg.content, "stopped": "done", "steps": step, "calls": calls, "trace": trace}
        this = [(c.function.name, c.function.arguments) for c in msg.tool_calls]
        if this == last:
            trace.append({"kind": "stop", "step": step, "text": "same calls as the previous turn"})
            return {"final": None, "stopped": "repeat", "steps": step, "calls": calls, "trace": trace}
        last = this
        for c in msg.tool_calls:
            args = json.loads(c.function.arguments or "{}")
            calls.append((c.function.name, args))
            trace.append({"kind": "call", "step": step, "name": c.function.name, "args": args})
            out = K.call_tool(by_name, c.function.name, c.function.arguments or "{}")
            trace.append({"kind": "error" if out.startswith('{"error"') else "result", "step": step, "text": out[:300]})
            messages.append({"role": "tool", "tool_call_id": c.id, "content": out})
    trace.append({"kind": "stop", "step": max_steps, "text": "step budget spent"})
    return {"final": None, "stopped": "max_steps", "steps": max_steps, "calls": calls, "trace": trace}
    # END SOLUTION


p = port.Port(K.lab_dir("D1_4", reset=True))
r = my_loop("What is the berth hire for a 39,000 GT vessel for 2 days?", p.tools(TOOLS_NAMES))
print(r["stopped"], r["steps"], r["calls"])
print(r["final"])
K.check(r["stopped"] == "done" and "7,800" in (r["final"] or "").replace("7800", "7,800"), "my_loop quoted SAR 7,800 from compute_dues")

# %% [markdown]
# ## 2 · A trace per run (5')
#
# A trace is the evidence of a run: what the model asked for, what each tool answered, why the loop stopped.
# Tomorrow's context work and Thursday's evaluation read traces, not answers.
#
# ✏️ **Exercise** · Write `save_trace(task_id, run)` that writes `run["trace"]` to `traces/<task_id>.jsonl` in the
# lab folder, one event per line, and adds a last line `{"kind": "summary", ...}` with `stopped`, `steps` and the
# number of tool calls and tool errors. Return the path.

# %%
TRACES = K.lab_dir("D1_4") / "traces"


def save_trace(task_id: str, run: dict) -> Path:
    # BEGIN SOLUTION
    TRACES.mkdir(exist_ok=True)
    path = TRACES / f"{task_id}.jsonl"
    summary = {"kind": "summary", "stopped": run["stopped"], "steps": run["steps"], "tool_calls": len(run["calls"]),
               "tool_errors": sum(e["kind"] == "error" for e in run["trace"])}
    with path.open("w", encoding="utf-8") as f:
        for e in run["trace"] + [summary]:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return path
    # END SOLUTION


path = save_trace("warmup", r)
print(path.read_text(encoding="utf-8"))
K.check(path.exists() and '"summary"' in path.read_text(encoding="utf-8"), "the trace ends with a summary line")

# %% [markdown]
# ## 3 · Ten tasks, graded by code (8')
#
# `data/tasks/day1_tasks.jsonl` holds ten tasks for Najm Lines and Sahil Feeders: reads, a quote, a booking, an
# amendment, a cancellation, an Arabic question, a wrong agent code and an out-of-scope request. Each has a check
# that code can grade: strings in the answer, or the state of the database after the run.
#
# ✏️ **Exercise** · For each task: a **fresh** `port.Port` (so one task's booking cannot change the next), run
# `my_loop`, save the trace, grade with `porttasks.grade(task, final, calls, p)`. Collect one row per task. The
# outcome asks for at least seven of ten.

# %%
tasks = porttasks.load_tasks("day1_tasks")
rows = []
for t in tasks:
    # BEGIN SOLUTION
    p = port.Port(K.lab_dir(f"D1_4/{t['id']}", reset=True))
    run = my_loop(t["prompt"], p.tools(TOOLS_NAMES))
    save_trace(t["id"], run)
    ok, why = porttasks.grade(t, run["final"], run["calls"], p)
    rows.append({"task": t["id"], "passed": ok, "why": why, "stopped": run["stopped"], "steps": run["steps"],
                 "tools": " ".join(n for n, _ in run["calls"])})
    # END SOLUTION
results = pd.DataFrame(rows)
print(results.to_string(index=False))
print(K.LEDGER)
K.check(results.passed.sum() >= 7, f"{results.passed.sum()} of 10 tasks passed (the outcome asks for 7)")

# %% [markdown]
# 🔍 Open the trace of one failed task. Was it the model (wrong tool, wrong argument), the tool (an unhelpful
# error), or the loop (stopped too early)? Write the cause next to it: this is the habit Thursday turns into an
# evaluation.

# %% [markdown]
# ## 4 · Break it: a tool that never finishes (4')
#
# `vessel_position` always answers "position not yet received, call again". Without a stop rule this loop would
# spend your quota.
#
# ✏️ **Exercise** · Run `my_loop` with only this tool and `max_steps=5` on "Keep checking until Najm Falcon's
# position arrives, then tell me." Which rule stopped it? Then write in `fix` one sentence you would put into the
# tool's **result** so that the model stops by itself.

# %%
def vessel_position(vessel_id: str = "V-110") -> dict:
    """Latest reported position of a vessel.

    Args:
        vessel_id: e.g. "V-110".
    """
    return {"vessel_id": vessel_id, "status": "pending", "message": "Position not yet received. Call vessel_position again."}


# BEGIN SOLUTION
broken = my_loop("Keep checking until Najm Falcon's position arrives, then tell me.", [vessel_position], max_steps=5)
fix = "Positions arrive about every 6 hours: tell the agent to ask again later instead of calling again now."
# END SOLUTION
print("stopped:", broken["stopped"], "after", broken["steps"], "steps | fix:", fix)
K.check(broken["stopped"] in ("repeat", "max_steps", "done"), "a stop rule bounded the loop")

# %% [markdown]
# ## ✱ Stretch · Run one turn's tool calls in parallel
#
# Calls the model returns in one turn are independent by definition. Copy `my_loop` into `my_parallel_loop` and run
# a turn's calls with `concurrent.futures.ThreadPoolExecutor`, appending the results **in the original order**.
# Try it on "Berth hire for Najm Sky for 4 days and for Sahil Wave for 2 days?".

# %%
from concurrent.futures import ThreadPoolExecutor

# BEGIN SOLUTION
def my_parallel_loop(task: str, tools: list, system: str = port.SYSTEM_PROMPT, max_steps: int = 8) -> str | None:
    by_name = {t.__name__: t for t in tools}
    messages = [{"role": "system", "content": system}, {"role": "user", "content": task}]
    for _ in range(max_steps):
        msg = K.chat(messages, tools=tools).choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            return msg.content
        with ThreadPoolExecutor() as pool:
            outs = list(pool.map(lambda c: K.call_tool(by_name, c.function.name, c.function.arguments), msg.tool_calls))
        messages.extend({"role": "tool", "tool_call_id": c.id, "content": o} for c, o in zip(msg.tool_calls, outs))
    return None


p = port.Port(K.lab_dir("D1_4/stretch", reset=True))
print(my_parallel_loop("Berth hire for Najm Sky for 4 days and for Sahil Wave for 2 days?", p.tools(TOOLS_NAMES)))
# END SOLUTION

# %% [markdown]
# ## Checkpoint
#
# 1. Who decides that the task is done: the model, the loop, or both? Point to the lines in `my_loop`.
# 2. Why does a tool error go back to the model as a **result** instead of raising?
# 3. Task T09 uses Najm's code on Sahil's booking. Which line of `port.py` made it pass, and would it pass if the
#    tool trusted the model to check ownership?
