# %% [markdown]
# # Lab 0 · Setup check
#
# Run this notebook **before Day 1** (about 5 minutes). It:
#
# - installs packages on Colab and checks the Marsa Ports Authority data,
# - checks your API key and makes one call to a **free** model on OpenRouter,
# - checks the three API shapes the course uses (Chat Completions, Responses, Anthropic Messages),
# - checks `uv` (it runs the single-file PEP 723 scripts).
#
# Nothing in this course downloads a model: every model runs behind a free API.
#
# **Before you start:** create a free OpenRouter key at <https://openrouter.ai/keys> and put it in `labs/.env`
# (copy `.env.example`), or on Colab in the 🔑 Secrets panel as `OPENROUTER_API_KEY` with notebook access on.
# Every lab uses free models only. Free models allow 50 requests a day; a one-time purchase of 10 credits raises
# that to 1,000 a day. Identical requests are replayed from `labs/cache`, so re-running a cell costs nothing.

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
print("provider:", K.PROVIDER, "| model:", K.MODEL, "| cache:", K.USE_CACHE)

# %% [markdown]
# ## 1 · Packages and course data

# %%
import platform
from importlib.metadata import PackageNotFoundError, version

import pandas as pd

packages = ["openai", "anthropic", "openai-agents", "pydantic", "huggingface-hub", "model2vec", "bm25s", "mcp",
            "langgraph", "a2a-sdk", "fastapi", "opentelemetry-sdk", "uv"]
rows = []
for name in packages:
    try:
        rows.append((name, version(name)))
    except PackageNotFoundError:
        rows.append((name, "MISSING"))
print("Python", platform.python_version(), "|", platform.system())
pd.DataFrame(rows, columns=["package", "version"])

# %%
import port

m = port.Port(K.lab_dir("00_setup", reset=True))
counts = {t: m.sql(f"SELECT count(*) AS n FROM {t}")[0]["n"] for t in ["berths", "vessels", "bookings"]}
print(counts, "| circulars:", len(port.load_circulars()))
K.check(counts["berths"] == 8 and len(port.load_circulars()) == 8, "Marsa data ready")

# %% [markdown]
# ## 2 · Your key and one free model
#
# One Chat Completions call. If it fails with `401`, the key is wrong; with `429`, the free model is busy or you used
# today's free requests (wait a minute, or set `AGENT_MODEL` to another free model from
# <https://openrouter.ai/models?max_price=0&supported_parameters=tools>).

# %%
resp = K.chat([{"role": "user", "content": "Reply with one word: ready"}], max_tokens=200)
print("served by:", resp.model, "|", repr(K.text_of(resp)[:60]))
print(K.LEDGER)
K.check(bool(K.text_of(resp).strip()), "a free model answered")

# %% [markdown]
# ## 3 · The three API shapes
#
# The course uses one loop over three request shapes. OpenRouter serves all three: `/api/v1/chat/completions`,
# `/api/v1/responses` (stateless) and `/api/v1/messages` (the Anthropic shape).

# %%
shapes = {}
for shape in ["chat", "responses", "anthropic"]:
    try:
        run = K.run_agent("What is the berth hire for a 39,000 GT vessel for 2 days? Use the tool.",
                          [m.compute_dues], shape=shape, max_steps=4, verbose=False)
        shapes[shape] = f"{run.stopped} after {run.steps} step(s), tools: {[c[0] for c in run.tool_calls]}"
    except Exception as e:  # noqa: BLE001 - report and keep going
        shapes[shape] = f"FAILED: {type(e).__name__}: {str(e)[:120]}"
for k, v in shapes.items():
    print(f"{k:10s} {v}")
K.check(all(not v.startswith("FAILED") for v in shapes.values()), "all three API shapes work with your key")

# %% [markdown]
# ## 4 · `uv` for PEP 723 scripts
#
# Standalone programs in this course (the MCP server, the CI smoke evaluation) are single files that
# declare their own dependencies in a `# /// script` block (PEP 723). `uv run file.py` builds an isolated environment
# for them on the fly.

# %%
import shutil

uv = shutil.which("uv") or shutil.which("uv", path=str(Path(sys.executable).parent))
out = subprocess.run([uv, "--version"], capture_output=True, text=True).stdout.strip() if uv else ""
K.check(bool(out), f"uv available: {out or 'not found'}")

# %% [markdown]
# ## You're ready
#
# If every line shows ✅, you are set for Day 1. Total usage of this check:

# %%
print(K.LEDGER)
