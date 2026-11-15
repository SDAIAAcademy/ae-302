# %% [markdown]
# # Lab 2.1 · Context as a budget
#
# Day 2 · Session 1 · 25 min. Every model call resends the whole history. On a long task the tool results pile
# up until a request no longer fits the budget you set. In this lab you measure tokens per turn on a long task,
# then cut them two ways: **offloading** big tool results to files, and **compacting** old turns into notes.
#
# **Reference state.** `data/reference/long_task_history.json`: the history of one long Bosla task (fourteen tool
# calls with real results from `port.py`, in a fixed order). A fresh port database for the live run. Nothing from
# Day 1 is needed.
#
# **Tasks**
# - [ ] 1 · Tokens per turn on the long task (5')
# - [ ] 2 · Offload big tool results to files (7')
# - [ ] 3 · Compact old turns into notes (7')
# - [ ] 4 · Before and after: tokens, cost and success, live (6')
# - [ ] ✱ Stretch · A cache-aware layout: stable first, volatile last

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

import pandas as pd

import port

REF = json.loads((K.DATA / "reference" / "long_task_history.json").read_text(encoding="utf-8"))
TASK, HISTORY = REF["task"], REF["messages"]
TOOLS = port.Port().tools()
TOOL_TOKENS = K.count_tokens([K.tool_schema(t) for t in TOOLS])
BUDGET = 4000  # tokens per request: the fixed budget of this lab
print(TASK)
print(len(HISTORY), "messages | tool definitions:", TOOL_TOKENS, "tokens")

# %% [markdown]
# ## 1 · Tokens per turn (5')
#
# The request before each assistant turn holds the tool definitions plus every message so far.
#
# ✏️ **Exercise** · Write `per_turn(messages)`: for each assistant message at index `i`, the tokens of the request
# that produced it, `TOOL_TOKENS + K.count_tokens(messages[:i])`. Return the list. At which turn does the request
# first exceed `BUDGET`?

# %%
def per_turn(messages: list[dict]) -> list[int]:
    # BEGIN SOLUTION
    return [TOOL_TOKENS + K.count_tokens(messages[:i]) for i, m in enumerate(messages) if m["role"] == "assistant"]
    # END SOLUTION


sizes = per_turn(HISTORY)
over = next((i + 1 for i, s in enumerate(sizes) if s > BUDGET), None)
print("request tokens per turn:", sizes)
print("first turn over budget:", over, "| history alone:", K.count_tokens(HISTORY), "tokens")
K.check(over is not None, "the long task overflows the budget")

# %% [markdown]
# 🔍 Which messages grow fastest? Count tokens by role: the tool results are most of it.

# %% [markdown]
# ## 2 · Offload big tool results (7')
#
# A tool result the model does not need in full can live in a file. The model sees a short stub with the path and
# a preview, and gets a `read_result` tool to page through it when it must.
#
# ✏️ **Exercise** · Write `offload(name, args, result)`, an `after_tool` hook: when `result` is longer than
# `LIMIT` characters, write it to `RESULTS/<name>_<n>.json` and return a JSON stub with `offloaded` (the file
# name), `chars`, and `preview` (the first 120 characters). Otherwise return `None` (keep the result). Then apply
# it to every tool message of the reference history and measure again.

# %%
RESULTS = K.lab_dir("D2_1", reset=True) / "results"
RESULTS.mkdir(exist_ok=True)
LIMIT = 500


def offload(name: str, args: dict, result: str) -> str | None:
    # BEGIN SOLUTION
    if len(result) <= LIMIT:
        return None
    path = RESULTS / f"{name}_{len(list(RESULTS.iterdir())) + 1}.json"
    path.write_text(result, encoding="utf-8")
    return json.dumps({"offloaded": path.name, "chars": len(result), "preview": result[:120],
                       "note": "Full result saved. Call read_result with this file name to read it."})
    # END SOLUTION


def read_result(file: str, start: int = 0, length: int = 1500) -> str:
    """Read part of a tool result that was saved to a file.

    Args:
        file: the file name given in the "offloaded" field.
        start: first character to read.
        length: how many characters to read (at most 3000).
    """
    text = (RESULTS / Path(file).name).read_text(encoding="utf-8")
    return text[start: start + min(int(length), 3000)]


offloaded = [dict(m, content=offload("tool", {}, m["content"]) or m["content"]) if m["role"] == "tool" else m
             for m in HISTORY]
print("history:", K.count_tokens(HISTORY), "→", K.count_tokens(offloaded), "tokens;", len(list(RESULTS.iterdir())), "files")
K.check(K.count_tokens(offloaded) < K.count_tokens(HISTORY), "offloading cut the history")

# %% [markdown]
# ## 3 · Compact old turns into notes (7')
#
# Compaction replaces old turns with a short note and keeps the recent ones verbatim. Two rules keep it safe:
# never split a tool call from its result, and keep the task.
#
# ✏️ **Exercise** · Write `compact(messages, keep_last=6)`: keep the system message and the first user message;
# replace everything up to the last `keep_last` messages with **one** user message that starts with
# `"Notes from earlier steps:"` and has one line per earlier tool call: its name, its arguments, and the first
# 120 characters of its result. Move the cut forward until the kept part does not start with a `tool` message.
# Compaction runs again later on a history that already holds notes: carry those lines forward.

# %%
def compact(messages: list[dict], keep_last: int = 6) -> list[dict]:
    # BEGIN SOLUTION
    head, body = messages[:2], messages[2:]
    cut = max(0, len(body) - keep_last)
    while cut < len(body) and body[cut]["role"] == "tool":
        cut += 1
    old, recent = body[:cut], body[cut:]
    results = {m["tool_call_id"]: m["content"] for m in old if m["role"] == "tool"}
    lines = []
    for m in old:
        if m["role"] == "user" and str(m["content"]).startswith("Notes from earlier steps:"):
            lines += m["content"].splitlines()[1:]  # keep the notes of an earlier compaction
        for c in m.get("tool_calls") or []:
            lines.append(f"- {c['function']['name']}({c['function']['arguments']}) → "
                         f"{' '.join(results.get(c['id'], '').split())[:120]}")
    if not lines:
        return messages
    return head + [{"role": "user", "content": "Notes from earlier steps:\n" + "\n".join(lines)}] + recent
    # END SOLUTION


compacted = compact(HISTORY)
print(compacted[2]["content"][:600])
print("history:", K.count_tokens(HISTORY), "→", K.count_tokens(compacted), "tokens")
K.check(compacted[2]["content"].startswith("Notes from earlier steps:") and compacted[3]["role"] != "tool",
        "one notes message, and no orphan tool result")

# %% [markdown]
# ## 4 · Before and after, live (6')
#
# `budget_loop` is the Day 1 loop with two switches: offload tool results, and compact whenever the next request
# would exceed `BUDGET`. Each configuration runs on a **fresh** port.
#
# ✏️ **Exercise** · Run the long task in three configurations: `none`, `offload`, `offload+compact`. For each,
# record: largest request (tokens), total input tokens, cost, and success (the answer names all five Najm
# bookings). This table is the evidence the outcome asks for.

# %%
NAJM = ["BK-24017", "BK-24019", "BK-24021", "BK-24022", "BK-24025"]


def budget_loop(task: str, p: port.Port, use_offload: bool, use_compact: bool, max_steps: int = 24) -> dict:
    tools = p.tools() + ([read_result] if use_offload else [])
    by_name = {t.__name__: t for t in tools}
    tool_tokens = K.count_tokens([K.tool_schema(t) for t in tools])
    messages = [{"role": "system", "content": port.SYSTEM_PROMPT}, {"role": "user", "content": task}]
    largest, final = 0, None
    for _ in range(max_steps):
        if use_compact and tool_tokens + K.count_tokens(messages) > BUDGET:
            messages = compact(messages)
        largest = max(largest, tool_tokens + K.count_tokens(messages))
        msg = K.chat(messages, tools=tools).choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            final = msg.content
            break
        for c in msg.tool_calls:
            out = K.call_tool(by_name, c.function.name, c.function.arguments)
            if use_offload:
                out = offload(c.function.name, {}, out) or out
            messages.append({"role": "tool", "tool_call_id": c.id, "content": out})
    return {"final": final, "largest_request": largest}


rows = []
for name, off, comp in [("none", False, False), ("offload", True, False), ("offload+compact", True, True)]:
    # BEGIN SOLUTION
    K.LEDGER.reset()
    r = budget_loop(TASK, port.Port(K.lab_dir(f"D2_1/{name}", reset=True)), off, comp)
    rows.append({"config": name, "largest_request": r["largest_request"], "input_tokens": K.LEDGER.input_tokens,
                 "cost_usd": round(K.LEDGER.cost, 4), "success": all(b in (r["final"] or "") for b in NAJM)})
    # END SOLUTION
table = pd.DataFrame(rows)
print(table.to_string(index=False))
K.check(len(table) == 3, "three configurations measured")

# %% [markdown]
# 🔍 Did a cut cost success? A compaction that drops a booking ID the answer needs is a saving that fails the
# task. Read the trace of any failed configuration before you trust the token column.

# %% [markdown]
# ## ✱ Stretch · Cache-aware layout
#
# Providers can reuse the computation of a request's unchanged **prefix**. Put what is stable first (system prompt,
# tool definitions) and what changes last. Build two requests a day apart, once with the date at the top of the
# system prompt and once at the bottom, and count the shared prefix in tokens.

# %%
# BEGIN SOLUTION
def shared_prefix_tokens(a: str, b: str) -> int:
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    return K.count_tokens(a[:n])


for where in ("top", "bottom"):
    reqs = [(f"Today is {d}.\n" + port.SYSTEM_PROMPT) if where == "top" else (port.SYSTEM_PROMPT + f"\nToday is {d}.")
            for d in ("2026-11-01", "2026-11-02")]
    print(where, shared_prefix_tokens(*reqs), "shared of", K.count_tokens(reqs[0]))
# END SOLUTION

# %% [markdown]
# ## Checkpoint
#
# 1. Which of the two cuts loses information, and which only moves it?
# 2. Why must compaction never keep a `tool` message without the assistant message that asked for it?
# 3. Your table shows fewer tokens and one more failure. Which column decides?
