# %% [markdown]
# # Lab 2.4 · An MCP server over the circular store
#
# Day 2 · Session 4 · 25 min. The Model Context Protocol (MCP) lets any host discover a server's tools and
# resources at run time instead of having them written into its code. In this lab you build an MCP server over
# Marsa's circulars, make it pass the provided test client, and connect Bosla to it through discovery, with a trace
# of the discovery and the calls.
#
# **Reference state.** The circulars, `port.py`, the provided test client `mcp_test_client.py`, and a reference
# server in `servers/marsa_mcp.py` (open it only after step 2). Nothing from earlier labs.
#
# **Tasks**
# - [ ] 1 · Read the shape of a server: tools, resources, instructions (3')
# - [ ] 2 · Build the server (8')
# - [ ] 3 · Pass the provided tests, in-process and over stdio (6')
# - [ ] 4 · Bosla discovers the server and uses it, with a trace (8')
# - [ ] ✱ Stretch · Speak the protocol by hand over HTTP

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
import shutil

from mcp import StdioServerParameters
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError

import mcp_test_client
import port

# %% [markdown]
# ## 1 · The shape of a server (3')
#
# An `MCPServer` has a name, **instructions** (sent to the host at connection), **tools** (functions the model may
# call; the input schema comes from type hints, the description from the docstring) and **resources** (documents
# the host may read, addressed by a URI; a template like `circular://{circular_id}` matches many).
#
# ```python
# server = MCPServer("name", instructions="...")
# @server.tool()
# def fn(arg: str) -> dict: ...
# @server.resource("scheme://{id}", mime_type="text/markdown")
# def doc(id: str) -> str: ...
# ```

# %% [markdown]
# ## 2 · Build the server (8')
#
# ✏️ **Exercise** · Write `build_server()` with two tools, `search_circulars(query, k=3)` and
# `get_circular(circular_id)`, backed by `port.Port()`, and two resources, `circulars://index` (one line per
# circular with its status) and `circular://{circular_id}`. Turn `port.ToolError` into MCP's `ToolError` so the
# model reads the message; raise `ResourceNotFoundError` for an unknown circular.

# %%
def build_server() -> MCPServer:
    server = MCPServer("marsa-circulars", log_level="WARNING",
                       instructions="Tariff circulars of Marsa Ports Authority. A superseded circular no longer applies.")
    p = port.Port()
    # BEGIN SOLUTION
    @server.tool()
    def search_circulars(query: str, k: int = 3) -> list[dict]:
        """Search the tariff circulars in English or Arabic. Returns passages with circular ID and status.

        Args:
            query: what you are looking for, e.g. "cancellation fee".
            k: how many passages, 1 to 5.
        """
        return p.search_circulars(query, k)

    @server.tool()
    def get_circular(circular_id: str) -> dict:
        """Read one whole circular by ID (TC-01 to TC-08).

        Args:
            circular_id: e.g. "TC-07".
        """
        try:
            return p.get_circular(circular_id)
        except port.ToolError as e:
            raise ToolError(str(e)) from e

    @server.resource("circulars://index", mime_type="text/markdown")
    def index() -> str:
        """Every circular with its ID, title and status."""
        return "\n".join(f"- {d['id']}: {d['title']} ({d['status']})" for d in port.load_circulars())

    @server.resource("circular://{circular_id}", mime_type="text/markdown")
    def circular(circular_id: str) -> str:
        """One circular, English then Arabic, e.g. circular://TC-07."""
        for d in port.load_circulars():
            if d["id"].lower() == circular_id.lower():
                return d["text"]
        raise ResourceNotFoundError(f"No circular {circular_id!r}. Read circulars://index.")
    # END SOLUTION
    return server


# %% [markdown]
# ## 3 · Pass the provided tests (6')
#
# The test client talks to your server only through the protocol: discovery, calls, resource reads. Run it
# in-process first (fast), then against the reference server launched over **stdio**, the way a desktop host or an
# IDE starts a local server.
#
# ✏️ **Exercise** · Run `mcp_test_client.run(...)` on your server and report. Then run it on
# `StdioServerParameters(command=uv, args=["run", "--quiet", "servers/marsa_mcp.py"])`.

# %%
# BEGIN SOLUTION
passed = mcp_test_client.report(mcp_test_client.run(build_server()))
uv = shutil.which("uv") or "uv"
stdio = StdioServerParameters(command=uv, args=["run", "--quiet", str(K.LABS / "servers" / "marsa_mcp.py")])
passed_stdio = mcp_test_client.report(mcp_test_client.run(stdio))
# END SOLUTION
K.check(passed == 8, "your server passes the provided tests")

# %% [markdown]
# ## 4 · Bosla discovers the server (8')
#
# Bosla's code does not import the circular tools: it asks the server what it has. `mcp.agent_tools()` turns each
# discovered tool into a callable the loop can use.
#
# ✏️ **Exercise** · Open a bridge to your server, write the discovery into `trace` (one event per tool with its
# name and argument names), run the question with the discovered tools plus the port's `compute_dues`, and append
# one event per tool call. Save the trace as JSONL.

# %%
Q = "What does it cost to cancel a booking one day before arrival, and which circular says so?"
trace = []
# BEGIN SOLUTION
with K.MCPBridge(build_server()) as mcp:
    discovered = mcp.list_tools()
    trace += [{"kind": "discover", "tool": t.name, "args": sorted(t.input_schema.get("properties", {}))} for t in discovered]
    r = K.run_agent(Q, mcp.agent_tools() + [port.Port().compute_dues], system=port.SYSTEM_PROMPT, max_steps=6)
    trace += [{"kind": "call", "tool": n, "args": a} for n, a in r.tool_calls]
    trace.append({"kind": "final", "text": r.final})
# END SOLUTION
path = K.lab_dir("D2_4") / "trace.jsonl"
path.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in trace) + "\n", encoding="utf-8")
print(path.read_text(encoding="utf-8"))
K.check(any(e["kind"] == "discover" for e in trace) and any(e["kind"] == "call" for e in trace),
        "the trace shows discovery, then calls")
K.check("TC-06" in trace[-1]["text"], "the answer cites TC-06")

# %% [markdown]
# ## ✱ Stretch · The protocol by hand
#
# Start the reference server over HTTP (`K.serve(["uv", "run", "servers/marsa_mcp.py", "--http", "8765"])`) and
# send JSON-RPC yourself with `httpx`: `initialize`, then `tools/list`, then `tools/call` for `get_circular`. The
# messages are the same ones the bridge sent for you. Stop the server with `K.stop(proc)`.

# %% [markdown]
# ## Checkpoint
#
# 1. Where did Bosla learn the names and arguments of the circular tools?
# 2. Why does the test client never import your server's Python functions?
# 3. A second team adds a write tool to the same server. What changes for every host that connects to it?
