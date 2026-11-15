# %% [markdown]
# # Lab 3.4 · Evaluating agents over repeated trials
#
# Day 3 · Session 4 · 25 min. One good run proves little: the model samples, so the same task can pass on Monday
# and fail on Tuesday. In this lab you grade recorded runs of 20 tasks over five trials each, with a code grader and
# a model grader, and compute success in **any** trial (pass@5) and in **every** trial (pass^5), and the cost per
# completed task.
#
# **Reference state.** `data/tasks/eval_tasks.jsonl` (20 tasks; five carry a rubric for the model grader) and
# `data/reference/recorded_runs.jsonl` (100 recorded runs). The recordings shipped with the course are
# **synthetic** (written with a fixed seed, marked `"synthetic": true`); the stretch records your own.
#
# **Tasks**
# - [ ] 1 · A code grader for recorded runs (6')
# - [ ] 2 · A model grader for the rubric tasks (6')
# - [ ] 3 · Success in any and in every trial (7')
# - [ ] 4 · Cost per completed task (6')
# - [ ] ✱ Stretch · Record your own five trials of three tasks

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
print("provider:", K.PROVIDER, "| model:", K.MODEL)

# %%
import json
from typing import Literal

import pandas as pd
from pydantic import BaseModel

import porttasks

TASKS = {t["id"]: t for t in porttasks.load_tasks("eval_tasks")}
RUNS = [json.loads(line) for line in (K.DATA / "reference" / "recorded_runs.jsonl").read_text(encoding="utf-8").splitlines()]
print(len(TASKS), "tasks |", len(RUNS), "recorded runs | synthetic:", all(r.get("synthetic") for r in RUNS))

# %% [markdown]
# ## 1 · A code grader for recorded runs (6')
#
# A recorded run cannot query a database any more, so the recording kept the value of the task's database query
# after the run (`db_value`).
#
# ✏️ **Exercise** · Write `code_grade(task, run)` returning `(passed, why)` with the same rules as
# `porttasks.grade`: strings in the answer (`contains_all`, `contains_any`, `contains_none`), `no_write`,
# `max_tool_calls`, and `db` compared with `run["db_value"]`.

# %%
WRITES = {"create_booking", "amend_booking", "cancel_booking"}


def code_grade(task: dict, run: dict) -> tuple[bool, str]:
    # BEGIN SOLUTION
    c, text = task["check"], run["final"] or ""
    if "contains_all" in c and not all(s in text for s in c["contains_all"]):
        return False, "missing a required string"
    if "contains_any" in c and not any(s in text for s in c["contains_any"]):
        return False, "none of the accepted strings"
    if any(s in text for s in c.get("contains_none", [])):
        return False, "contains a forbidden string"
    if c.get("no_write") and any(n in WRITES for n in run["tool_calls"]):
        return False, "made a write call"
    if "max_tool_calls" in c and len(run["tool_calls"]) > c["max_tool_calls"]:
        return False, "too many tool calls"
    if "db" in c and run["db_value"] != c["db"][1]:
        return False, f"database {run['db_value']} != {c['db'][1]}"
    return True, "ok"
    # END SOLUTION


graded = pd.DataFrame([{**r, "code_ok": code_grade(TASKS[r["task"]], r)[0], "code_why": code_grade(TASKS[r["task"]], r)[1]}
                       for r in RUNS])
print(graded.groupby("task").code_ok.mean().round(1).to_string())
K.check(graded.code_ok.dtype == bool, "every run graded by code")

# %% [markdown]
# ## 2 · A model grader for the rubric tasks (6')
#
# Some properties are hard to check with strings: "replies in Arabic and cites TC-06", "refuses without saying whose
# booking it is". A model grader reads the rubric and the answer and returns a verdict with a reason.
#
# ✏️ **Exercise** · Write `model_grade(task, run)` with `K.structured(...)` and the `Verdict` schema, at
# `temperature=0`. The prompt holds the rubric, the task and the answer, and asks for a strict reading. Grade the
# runs of the five rubric tasks. A run passes when the code grader **and** (if there is a rubric) the model grader
# pass.

# %%
class Verdict(BaseModel):
    reason: str
    verdict: Literal["pass", "fail"]


def model_grade(task: dict, run: dict) -> Verdict:
    # BEGIN SOLUTION
    prompt = (f"Rubric: {task['rubric']}\n\nTask given to the assistant:\n{task['prompt']}\n\n"
              f"The assistant's final answer:\n{run['final']}\n\nGrade strictly against the rubric only.")
    return K.structured(prompt, Verdict, system="You grade one answer of a port booking assistant.")
    # END SOLUTION


judged = {}
for i, r in graded.iterrows():
    if "rubric" in TASKS[r["task"]]:
        judged[i] = model_grade(TASKS[r["task"]], r.to_dict()).verdict == "pass"
graded["model_ok"] = [judged.get(i, True) for i in graded.index]
graded["passed"] = graded.code_ok & graded.model_ok
print(graded[graded.index.isin(judged)][["task", "trial", "code_ok", "model_ok", "final"]].head(10).to_string(index=False))

# %% [markdown]
# ## 3 · Success in any and in every trial (7')
#
# **pass@5**: the task passed in at least one of five trials (can the agent do it?). **pass^5**: it passed in all
# five (can you rely on it?). The outcome asks for both.
#
# ✏️ **Exercise** · Build `per_task`: one row per task with `trials`, `passes`, `pass_at_5` (any) and
# `pass_hat_5` (every). Then the overall rates over the 20 tasks.

# %%
# BEGIN SOLUTION
per_task = graded.groupby("task").agg(trials=("passed", "size"), passes=("passed", "sum"))
per_task["pass_at_5"] = per_task.passes > 0
per_task["pass_hat_5"] = per_task.passes == per_task.trials
# END SOLUTION
print(per_task.to_string())
print(f"pass@5 {per_task.pass_at_5.mean():.2f} | pass^5 {per_task.pass_hat_5.mean():.2f} | "
      f"per-trial success {graded.passed.mean():.2f}")
K.check(per_task.pass_hat_5.mean() <= per_task.pass_at_5.mean(), "every-trial success is never above any-trial success")

# %% [markdown]
# 🔍 Pick the task with the lowest pass rate and read its failed answers. T02 and T12 fail on arithmetic or on the
# superseded circular: which harness part from Lab 3.1 would you strengthen?

# %% [markdown]
# ## 4 · Cost per completed task (6')
#
# Free models cost nothing, so put a price on the tokens to compare designs as if they ran on a paid model. The
# prices below are **assumptions** to replace with the price list of the model you would deploy.
#
# ✏️ **Exercise** · Compute `cost_per_completed`: the price of **all** 100 runs' tokens divided by the number of
# passed runs. Why divide by passed runs and not by all runs?

# %%
PRICE_IN, PRICE_OUT = 0.20, 0.80  # USD per million tokens: an assumption, not a quote
# BEGIN SOLUTION
total = (graded.input_tokens.sum() * PRICE_IN + graded.output_tokens.sum() * PRICE_OUT) / 1e6
cost_per_completed = total / max(1, graded.passed.sum())
# END SOLUTION
print(f"total ${total:.4f} for {len(graded)} runs | {graded.passed.sum()} passed | ${cost_per_completed:.5f} per completed task")

# %% [markdown]
# ## ✱ Stretch · Record your own trials
#
# Run `bosla.run` on three tasks, five fresh trials each, with the cache off (`use_cache=False`: a cached answer is
# the same sample five times). Write each run in the recording format and grade it with the same code.

# %%
# BEGIN SOLUTION
import bosla
import port

mine = []
for tid in ["T02", "T09", "T12"]:
    for trial in range(1, 6):
        p = port.Port(K.lab_dir(f"D3_4/{tid}_{trial}", reset=True))
        K.LEDGER.reset()
        r = bosla.run(TASKS[tid]["prompt"], p, use_cache=False)
        db = TASKS[tid]["check"].get("db")
        mine.append({"task": tid, "trial": trial, "final": r.final, "tool_calls": [n for n, _ in r.tool_calls],
                     "db_value": list(p.sql(db[0])[0].values())[0] if db else None,
                     "input_tokens": K.LEDGER.input_tokens, "output_tokens": K.LEDGER.output_tokens, "synthetic": False})
print(pd.DataFrame([{**m, "ok": code_grade(TASKS[m["task"]], m)[0]} for m in mine])[["task", "trial", "ok"]])
# END SOLUTION

# %% [markdown]
# ## Checkpoint
#
# 1. A task passes in 4 of 5 trials. Is it in pass@5? In pass^5? Which would you report to the Authority?
# 2. When would you trust a model grader over a code grader, and how do you check the model grader?
# 3. Why must repeated trials run with the response cache off?
