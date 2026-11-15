# %% [markdown]
# # Lab 4.2 · Two agents or one?
#
# Day 4 · Session 2 · 25 min. Splitting work between agents can help (each sees less, does one job) or hurt (more
# calls, lost context at the handover). In this lab a **researcher** with read tools gathers facts and a
# **drafter** with no tools writes the reply to the shipping agent. You compare the pair with one Bosla on quality
# and cost, on the same tasks.
#
# **Reference state.** `bosla.py`, `port.py`, the twenty evaluation tasks. Nothing from Lab 4.1.
#
# **Tasks**
# - [ ] 1 · The researcher: read tools, notes out (6')
# - [ ] 2 · The drafter: notes in, reply out, no tools (5')
# - [ ] 3 · Pair against single: quality and tokens on six tasks (9')
# - [ ] 4 · When does a second agent pay? (5')
# - [ ] ✱ Stretch · Delegation as a task with a status

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
import pandas as pd

import bosla
import port
import porttasks

TASKS = {t["id"]: t for t in porttasks.load_tasks("eval_tasks")}
SIX = ["T02", "T03", "T11", "T13", "T15", "T18"]  # read-only tasks: the pair has no write tools

RESEARCHER = ("You research for Marsa Ports Authority's booking desk. Use the tools to collect the facts the "
              "question needs. Reply with short notes only: each fact with its source (tool or circular ID). "
              "Do not write a reply to the customer.")
DRAFTER = ("You write the reply to a shipping agent for Marsa Ports Authority. Use only the notes given; if they do "
           "not answer the question, say what is missing. Cite circular IDs from the notes. Reply in the language "
           "of the question.")

# %% [markdown]
# ## 1 · The researcher (6')
#
# ✏️ **Exercise** · Write `research(question, p)`: `K.run_agent` with the read tools and `RESEARCHER`, at most 6
# steps; return the notes and the run.

# %%
def research(question: str, p: port.Port) -> tuple[str, K.Run]:
    # BEGIN SOLUTION
    r = K.run_agent(question, p.tools(port.Port.READ_TOOLS), system=RESEARCHER, max_steps=6, verbose=False)
    return r.final, r
    # END SOLUTION


notes, _ = research(TASKS["T11"]["prompt"], port.Port(K.lab_dir("D4_2/try", reset=True)))
print(notes)

# %% [markdown]
# ## 2 · The drafter (5')
#
# ✏️ **Exercise** · Write `draft(question, notes)`: one `K.chat` call with `DRAFTER` as system and the question and
# the notes in the user message. No tools: the drafter cannot look anything up, so the handover is everything.

# %%
def draft(question: str, notes: str) -> str:
    # BEGIN SOLUTION
    msg = f"Question from the shipping agent:\n{question}\n\nResearch notes:\n{notes}"
    return K.text_of(K.chat([{"role": "system", "content": DRAFTER}, {"role": "user", "content": msg}]))
    # END SOLUTION


print(draft(TASKS["T11"]["prompt"], notes))

# %% [markdown]
# ## 3 · Pair against single (9')
#
# ✏️ **Exercise** · For each of the six tasks, on fresh ports: the pair (research, then draft) and the single
# Bosla (`bosla.run`). Grade both with `porttasks.grade` (the pair's tool calls are the researcher's), and record
# input tokens from `K.LEDGER` (reset before each).

# %%
rows = []
for tid in SIX:
    t = TASKS[tid]
    # BEGIN SOLUTION
    K.LEDGER.reset()
    p = port.Port(K.lab_dir(f"D4_2/pair/{tid}", reset=True))
    notes, rr = research(t["prompt"], p)
    reply = draft(t["prompt"], notes)
    pair_ok, _ = porttasks.grade(t, reply, rr.tool_calls, p)
    pair_tokens = K.LEDGER.input_tokens
    K.LEDGER.reset()
    q = port.Port(K.lab_dir(f"D4_2/single/{tid}", reset=True))
    r = bosla.run(t["prompt"], q)
    single_ok, _ = porttasks.grade(t, r.final, r.tool_calls, q)
    rows.append({"task": tid, "pair_ok": pair_ok, "single_ok": single_ok, "pair_tokens": pair_tokens,
                 "single_tokens": K.LEDGER.input_tokens})
    # END SOLUTION
cmp = pd.DataFrame(rows)
print(cmp.to_string(index=False))
print("passed: pair", cmp.pair_ok.sum(), "| single", cmp.single_ok.sum(),
      "| tokens: pair", cmp.pair_tokens.sum(), "| single", cmp.single_tokens.sum())

# %% [markdown]
# 🔍 Find a task where the pair failed and the single agent passed. Read the notes: was the fact missing, or lost
# in the drafting? A handover drops whatever the first agent did not think to write down.

# %% [markdown]
# ## 4 · When does a second agent pay? (5')
#
# ✏️ **Exercise** · Write three conditions in `pays_when` under which you would split Bosla into two agents, and
# one in `not_when`. Use your table.

# %%
# BEGIN SOLUTION
pays_when = ["the research reads far more than the reply needs, so the drafter's context stays small",
             "the two jobs need different permissions (the drafter must never see the booking list)",
             "research can run in parallel over several sources"]
not_when = ["the task is short and the handover would carry most of the context anyway"]
# END SOLUTION
print(pays_when, not_when)

# %% [markdown]
# ## ✱ Stretch · Delegation as a task
#
# Agent-to-agent protocols hand over a **task** with a status (submitted, working, completed, failed) rather than a
# function call. Wrap `research` so it returns `{"status", "notes", "steps"}` and let `draft` refuse to write when
# the status is not `completed`.

# %% [markdown]
# ## Checkpoint
#
# 1. What did the drafter not know that the single agent knew?
# 2. Which cost more tokens, and why?
# 3. Name a Marsa task where splitting would protect personal data.
