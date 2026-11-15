# %% [markdown]
# # Lab 2.3 · A context file, a tariff skill and staged loading
#
# Day 2 · Session 3 · 25 min. Instructions that apply to every session go in a short **context file**. Procedures
# that apply only sometimes go in **skills**: the agent sees a one-line index and loads a skill's body, then its
# reference file, only when the task needs them. In this lab you wire both into Bosla and show the staged loading
# in a trace.
#
# **Reference state.** `data/bosla/AGENTS.md` (the context file) and two skills in `data/bosla/skills/`
# (`tariff-quote`, `booking-change`), a fresh port database. Nothing from earlier labs.
#
# **Tasks**
# - [ ] 1 · The context file in the system prompt (5')
# - [ ] 2 · Parse the skills and build the index (6')
# - [ ] 3 · Staged loading: `load_skill` and `read_skill_file` (6')
# - [ ] 4 · Show it in a trace (8')
# - [ ] ✱ Stretch · A memory file per agent

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
import port

BOSLA = K.DATA / "bosla"
SKILLS = BOSLA / "skills"
p = port.Port(K.lab_dir("D2_3", reset=True))

# %% [markdown]
# ## 1 · The context file (5')
#
# ✏️ **Exercise** · Build `SYSTEM`: `port.SYSTEM_PROMPT`, a blank line, then the text of `BOSLA / "AGENTS.md"`.
# Print the tokens of each part.

# %%
# BEGIN SOLUTION
context_file = (BOSLA / "AGENTS.md").read_text(encoding="utf-8")
SYSTEM = port.SYSTEM_PROMPT + "\n\n" + context_file
# END SOLUTION
print("prompt", K.count_tokens(port.SYSTEM_PROMPT), "+ context file", K.count_tokens(context_file), "=", K.count_tokens(SYSTEM))
K.check("tariff-quote" in SYSTEM, "the context file is in the system prompt")

# %% [markdown]
# ## 2 · The skill index (6')
#
# A skill is a folder with a `SKILL.md`: a front matter block with `name` and `description`, then the body.
#
# ✏️ **Exercise** · Write `parse_skill(path)` returning `{"name", "description", "body", "dir"}`, then
# `INDEX`, one line per skill: `- <name>: <description>`.

# %%
def parse_skill(path: Path) -> dict:
    # BEGIN SOLUTION
    raw = path.read_text(encoding="utf-8")
    _, head, body = raw.split("---", 2)
    meta = dict(line.split(": ", 1) for line in head.strip().splitlines())
    return {"name": meta["name"], "description": meta["description"], "body": body.strip(), "dir": path.parent}
    # END SOLUTION


SKILL_LIST = [parse_skill(f) for f in sorted(SKILLS.glob("*/SKILL.md"))]
INDEX = "Skills you can load with load_skill:\n" + "\n".join(f"- {s['name']}: {s['description']}" for s in SKILL_LIST)
print(INDEX)
K.check(len(SKILL_LIST) == 2, "two skills parsed")

# %% [markdown]
# ## 3 · Staged loading (6')
#
# Stage 1: the index is always in context. Stage 2: `load_skill` returns a body. Stage 3: `read_skill_file`
# returns a file inside the skill folder, and nothing outside it.
#
# ✏️ **Exercise** · Write both tools. `read_skill_file` must refuse a path that leaves the skill's folder
# (`../`, an absolute path) with a `port.ToolError`. Then compare the tokens of "index only" with "every body and
# reference file in the prompt".

# %%
BY_NAME = {s["name"]: s for s in SKILL_LIST}


def load_skill(name: str) -> str:
    """Load the instructions of one skill from the index.

    Args:
        name: the skill's name, e.g. "tariff-quote".
    """
    # BEGIN SOLUTION
    if name not in BY_NAME:
        raise port.ToolError(f"No skill {name!r}. Skills: {', '.join(BY_NAME)}.")
    return BY_NAME[name]["body"]
    # END SOLUTION


def read_skill_file(name: str, file: str) -> str:
    """Read a file that a loaded skill refers to, such as reference.md.

    Args:
        name: the skill's name.
        file: the file name inside the skill's folder.
    """
    # BEGIN SOLUTION
    if name not in BY_NAME:
        raise port.ToolError(f"No skill {name!r}.")
    folder = BY_NAME[name]["dir"].resolve()
    target = (folder / file).resolve()
    if folder not in target.parents or not target.is_file():
        raise port.ToolError(f"{file!r} is not a file of the skill {name!r}.")
    return target.read_text(encoding="utf-8")
    # END SOLUTION


everything = "\n\n".join(s["body"] + "\n" + "\n".join(f.read_text(encoding="utf-8") for f in s["dir"].glob("*.md")
                                                    if f.name != "SKILL.md") for s in SKILL_LIST)
print("index only:", K.count_tokens(INDEX), "tokens | everything in the prompt:", K.count_tokens(everything), "tokens")
print(K.call_tool({"read_skill_file": read_skill_file}, "read_skill_file", {"name": "tariff-quote", "file": "../../AGENTS.md"}))
K.check("error" in K.call_tool({"read_skill_file": read_skill_file}, "read_skill_file",
                               {"name": "tariff-quote", "file": "../../AGENTS.md"}), "path escape refused")

# %% [markdown]
# ## 4 · Show it in a trace (8')
#
# ✏️ **Exercise** · Run the question below with `SYSTEM + INDEX`, the two skill tools and the port tools. From the
# trace, check the **order**: `load_skill("tariff-quote")` comes before `compute_dues`. Record whether
# `reference.md` was read, and the answer's amount.

# %%
Q = "Agent code SHL-2290. What is the berth hire for Sahil Tide for 3 days? It carries fuel, dangerous goods."
# BEGIN SOLUTION
r = K.run_agent(Q, [load_skill, read_skill_file] + p.tools(port.Port.READ_TOOLS), system=SYSTEM + "\n\n" + INDEX,
                max_steps=8)
order = [n for n, _ in r.tool_calls]
# END SOLUTION
print(order)
K.check("load_skill" in order and "compute_dues" in order and order.index("load_skill") < order.index("compute_dues"),
        "the skill was loaded before the tariff was computed")
K.check("12,960" in r.final.replace("12960", "12,960"), "SAR 12,960 quoted")

# %% [markdown]
# ## ✱ Stretch · A memory file per agent
#
# Faisal asked last week for answers in Arabic. Write `remember(agent_code, note)` that appends one line to
# `memory/<agent_code>.md` in the lab folder (at most 20 lines, no contact data), and load that file into the
# system prompt at the start of the next session.

# %%
# BEGIN SOLUTION
MEMORY = K.lab_dir("D2_3") / "memory"
MEMORY.mkdir(exist_ok=True)


def remember(agent_code: str, note: str) -> str:
    """Save one short preference of the shipping agent for later sessions. No names, phones or emails.

    Args:
        agent_code: e.g. "NJM-4417".
        note: one line, e.g. "prefers answers in Arabic".
    """
    path = MEMORY / f"{agent_code}.md"
    lines = (path.read_text(encoding="utf-8").splitlines() if path.exists() else [])[-19:] + [note.strip()[:200]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f"saved ({len(lines)} lines)"


print(remember("NJM-4417", "prefers answers in Arabic"))
print((MEMORY / "NJM-4417.md").read_text(encoding="utf-8"))
# END SOLUTION

# %% [markdown]
# ## Checkpoint
#
# 1. What belongs in the context file, and what in a skill?
# 2. Which stage of loading did the trace show, and which did not happen?
# 3. Why must `read_skill_file` refuse `../`?
