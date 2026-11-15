# %% [markdown]
# # Lab 3.2 · An agent SDK against your own loop
#
# Day 3 · Session 2 · 25 min. Agent SDKs package the loop, tools, sessions, guardrails and tracing. In this lab you
# rebuild Bosla on one SDK (the OpenAI Agents SDK, pointed at a free OpenRouter model), run the same ten tasks, and
# compare it with the reference loop on three things: code size, what the trace shows, and what you control.
#
# **Reference state.** `bosla.py` (the own-loop agent), `port.py`, the ten Day 1 tasks. Nothing from Lab 3.1.
#
# **Tasks**
# - [ ] 1 · Bosla on the SDK: model, tools, agent (7')
# - [ ] 2 · The same ten tasks, graded the same way (6')
# - [ ] 3 · Traces and control, side by side (7')
# - [ ] 4 · The comparison table (5')
# - [ ] ✱ Stretch · The write gate in the SDK

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
import asyncio
import inspect
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled
from openai import AsyncOpenAI

import bosla
import port
import porttasks

set_tracing_disabled(True)  # the SDK exports traces to OpenAI's dashboard by default; we keep them local
TASKS = porttasks.load_tasks("day1_tasks")


def run_sync(coro):
    """Run a coroutine from a notebook (which already has an event loop) or from a script."""
    with ThreadPoolExecutor(1) as pool:
        return pool.submit(asyncio.run, coro).result()


# %% [markdown]
# ## 1 · Bosla on the SDK (7')
#
# The SDK speaks the Responses API to OpenAI by default. For any other provider, wrap an `AsyncOpenAI` client in
# `OpenAIChatCompletionsModel`. `function_tool` reads the same type hints and docstrings as `K.tool_schema`.
#
# ✏️ **Exercise** · Write `make_sdk_agent(p)`: the model for OpenRouter, every port tool through `function_tool`,
# and an `Agent` named "Bosla" with the reference prompt plus the context file as instructions.

# %%
def make_sdk_agent(p: port.Port) -> Agent:
    # BEGIN SOLUTION
    client = AsyncOpenAI(base_url=K.PROVIDERS[K.PROVIDER]["base_url"], api_key=K.api_key(), default_headers=K.headers())
    model = OpenAIChatCompletionsModel(model=K.MODEL, openai_client=client)
    tools = [function_tool(t) for t in p.tools()]
    return Agent(name="Bosla", instructions=port.SYSTEM_PROMPT + "\n\n" + bosla.CONTEXT_FILE, model=model, tools=tools)
    # END SOLUTION


p = port.Port(K.lab_dir("D3_2/warmup", reset=True))
result = run_sync(Runner.run(make_sdk_agent(p), "Berth hire for Najm Falcon for 2 days?", max_turns=8))
print(result.final_output)
for item in result.new_items:
    print(f"  {type(item).__name__:22s}", getattr(item.raw_item, "name", "") or "")

# %% [markdown]
# ## 2 · The same ten tasks (6')
#
# The SDK reports tool calls as run items. To grade with `porttasks.grade` you need `(name, args)` pairs.
#
# ✏️ **Exercise** · For each task: a fresh port, the SDK agent, `Runner.run(..., max_turns=8)`, the tool calls from
# `result.new_items` (items whose type is `ToolCallItem`: name and JSON arguments on `raw_item`), the grade. An
# exception from the SDK (for example `MaxTurnsExceeded`) is a failed task with the exception's name as `why`.

# %%
import json

rows = []
for t in TASKS:
    # BEGIN SOLUTION
    p = port.Port(K.lab_dir(f"D3_2/{t['id']}", reset=True))
    try:
        res = run_sync(Runner.run(make_sdk_agent(p), t["prompt"], max_turns=8))
        calls = [(i.raw_item.name, json.loads(i.raw_item.arguments or "{}")) for i in res.new_items
                 if type(i).__name__ == "ToolCallItem"]
        ok, why = porttasks.grade(t, res.final_output, calls, p)
    except Exception as e:  # noqa: BLE001 - the SDK stops a run by raising
        ok, why, calls = False, type(e).__name__, []
    rows.append({"task": t["id"], "passed": ok, "why": why, "tools": " ".join(n for n, _ in calls)})
    # END SOLUTION
sdk = pd.DataFrame(rows)
print(sdk.to_string(index=False))
K.check(len(sdk) == 10, "ten tasks on the SDK")

# %% [markdown]
# 🔍 T04 says "do not book yet" and T09 uses the wrong agent code. The SDK agent has no write gate: which of the two
# does the tool's own check still protect, and which depends on the model alone?

# %% [markdown]
# ## 3 · Traces and control (7')
#
# ✏️ **Exercise** · Fill `control`: for each harness part of `bosla.PARTS` (except `verify`), how you would get it
# on the SDK, in a few words, or "not built in". Then count the lines of the two agents' code: `bosla.run` plus
# `agentkit.run_agent` against `make_sdk_agent` plus the run call.

# %%
# BEGIN SOLUTION
control = {
    "prompt_rules": "instructions=",
    "context_file": "append to instructions",
    "useful_errors": "the tool's own messages; the SDK passes exceptions to the model as text by default",
    "step_budget": "max_turns= (raises MaxTurnsExceeded instead of returning a stop reason)",
    "write_gate": "not built in as a plain hook here: a tool guardrail or an approval setting per tool (stretch)",
}
own_lines = len(inspect.getsource(bosla.run).splitlines()) + len(inspect.getsource(K.run_agent).splitlines())
sdk_lines = len(inspect.getsource(make_sdk_agent).splitlines()) + 1
# END SOLUTION
print(pd.DataFrame(control.items(), columns=["part", "on the SDK"]).to_string(index=False))
print("lines: own loop", own_lines, "| SDK agent", sdk_lines)

# %% [markdown]
# ## 4 · The comparison table (5')
#
# ✏️ **Exercise** · Write `table`: rows `code size`, `trace`, `control`, `passed tasks`; columns `own loop` and
# `SDK`. Use your numbers, and one line of judgement per row. This is the table the capstone README asks for when
# you choose between an SDK and your own harness.

# %%
# BEGIN SOLUTION
table = pd.DataFrame([
    {"": "code size", "own loop": f"{own_lines} lines, all yours", "SDK": f"{sdk_lines} lines plus the SDK"},
    {"": "trace", "own loop": "events you defined, stop reason returned", "SDK": "run items; exceptions for stops"},
    {"": "control", "own loop": "every hook is a line you can read", "SDK": "settings and guardrails; less to write"},
    {"": "passed tasks", "own loop": "from Lab 3.1's baseline", "SDK": f"{sdk.passed.sum()} of 10"},
])
# END SOLUTION
print(table.to_string(index=False))

# %% [markdown]
# ## ✱ Stretch · The write gate in the SDK
#
# Read the SDK's documentation for tool approvals or tool guardrails, and add a gate that refuses
# `create_booking`, `amend_booking` and `cancel_booking` unless the input says "I confirm". Run T04 again.

# %% [markdown]
# ## Checkpoint
#
# 1. Name one thing you lost and one thing you gained by moving to the SDK.
# 2. The SDK raises when `max_turns` is reached. What does your evaluation code have to do about that?
# 3. Where, in the SDK's run, would you look for the equivalent of your trace's `guard` events?
