# %% [markdown]
# # Lab 3.1 · Anatomy of a harness: remove one part
#
# Day 3 · Session 1 · 25 min. Most of an agent's engineering is in the harness around the model: the prompt, the
# context file, the error messages, the budgets, the gates. In this lab you run a working Bosla on the ten Day 1
# tasks, remove **one** harness part, run again, and record from the traces what broke.
#
# **Reference state.** `bosla.py` (the reference agent and its named parts), the ten tasks of
# `data/tasks/day1_tasks.jsonl`, a fresh port database per task. Nothing from Days 1 and 2.
#
# **Tasks**
# - [ ] 1 · Map the parts, and predict (4')
# - [ ] 2 · Baseline: the full harness on ten tasks (6')
# - [ ] 3 · Remove one part and run again (10')
# - [ ] 4 · What broke, and where in the trace (5')
# - [ ] ✱ Stretch · Remove a second part: do the effects add up?

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
print("provider:", K.PROVIDER, "| model:", K.MODEL)

# %%
import pandas as pd

import bosla
import port
import porttasks

TASKS = porttasks.load_tasks("day1_tasks")
for name, what in bosla.PARTS.items():
    print(f"{name:14s} {what}")

# %% [markdown]
# ## 1 · Map the parts, and predict (4')
#
# ✏️ **Exercise** · Your table removes the part the trainer gives you (default below). Before running anything,
# write in `prediction` which tasks you expect to break, and why.

# %%
REMOVE = "useful_errors"  # the trainer assigns one of: prompt_rules, context_file, useful_errors, step_budget, write_gate
# BEGIN SOLUTION
prediction = {"tasks": ["T09"], "why": "with 'failed' as the only error, the model cannot tell a wrong agent code "
                                       "from a bad argument, and may retry or claim success"}
# END SOLUTION
print(prediction)

# %% [markdown]
# ## 2 · Baseline (6')
#
# ✏️ **Exercise** · Write `run_all(remove)`: for each task, a fresh `port.Port`, `bosla.run(task, p, remove=...)`,
# then `porttasks.grade`. Return one row per task with `task`, `passed`, `why`, `stopped`, `steps`, `errors`
# (tool errors in the trace) and `tools`. Run it with nothing removed.

# %%
def run_all(remove: set[str]) -> pd.DataFrame:
    rows = []
    for t in TASKS:
        # BEGIN SOLUTION
        p = port.Port(K.lab_dir(f"D3_1/{'-'.join(sorted(remove)) or 'full'}/{t['id']}", reset=True))
        r = bosla.run(t["prompt"], p, remove=remove)
        ok, why = porttasks.grade(t, r.final, r.tool_calls, p)
        rows.append({"task": t["id"], "passed": ok, "why": why, "stopped": r.stopped, "steps": r.steps,
                     "errors": sum(e.kind == "error" for e in r.trace), "tools": " ".join(n for n, _ in r.tool_calls)})
        # END SOLUTION
    return pd.DataFrame(rows)


full = run_all(set())
print(full.to_string(index=False))
K.check(len(full) == 10, "baseline over ten tasks")

# %% [markdown]
# ## 3 · Remove one part (10')
#
# ✏️ **Exercise** · Run `run_all({REMOVE})` and join it with the baseline on `task`: one row per task with
# `passed_full`, `passed_removed`, and the tools of each run.

# %%
# BEGIN SOLUTION
removed = run_all({REMOVE})
diff = full[["task", "passed", "tools"]].merge(removed[["task", "passed", "tools", "stopped"]], on="task",
                                               suffixes=("_full", "_removed"))
# END SOLUTION
print(diff.to_string(index=False))
print("full:", full.passed.sum(), "of 10 | without", REMOVE + ":", removed.passed.sum(), "of 10")

# %% [markdown]
# ## 4 · What broke (5')
#
# ✏️ **Exercise** · For each task that flipped, open both traces (`bosla.run(..., verbose=True)` on a fresh port)
# and write one line in `findings`: the task, the step where the runs part, and the part's role there. If nothing
# flipped, say which task would need to exist to show the part's value. Compare with your prediction.

# %%
# BEGIN SOLUTION
flipped = diff[diff.passed_full != diff.passed_removed].task.tolist()
findings = [f"{t}: runs differ from the first tool error on; without useful errors the model gets 'failed' and "
            "cannot tell what to fix" for t in flipped] or [
    f"No task flipped on this run. A task where a tool error must be read (a wrong date format) would show {REMOVE}."]
# END SOLUTION
print("\n".join(findings))

# %% [markdown]
# 🔍 Share your row with the room: one table per part. Which part, removed, cost the most tasks? Which cost none on
# these ten tasks, and what does that say about the tasks rather than the part?

# %% [markdown]
# ## ✱ Stretch · Two parts at once
#
# Remove `REMOVE` and one more part together. Is the loss the sum of the two single losses?

# %%
# BEGIN SOLUTION
both = run_all({REMOVE, "write_gate"})
print("without both:", both.passed.sum(), "of 10")
# END SOLUTION

# %% [markdown]
# ## Checkpoint
#
# 1. Which harness part protects T04 ("do not book yet") when the model is careless?
# 2. A part whose removal breaks nothing on ten tasks: useless, or untested?
# 3. Which of the five parts would you never remove in production, whatever the eval says?
