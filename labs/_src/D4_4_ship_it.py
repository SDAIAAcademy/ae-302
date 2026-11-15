# %% [markdown]
# # Lab 4.4 · Bosla behind an API, traced, gated in CI
#
# Day 4 · Session 4 · 25 min. A production agent is a service: an endpoint with a key and a budget, a trace of
# every request in a collector, and a smoke evaluation that stops a release when the agent gets worse. In this lab
# you build each piece in-process (FastAPI's `TestClient`, an in-memory span exporter), then show the CI gate
# passing on the baseline and failing on a seeded regression.
#
# **Reference state.** `bosla.py`, `port.py`, the twenty evaluation tasks, `ci/smoke_eval.py` and the workflow
# template `ci/smoke-eval.yml`. Nothing from earlier labs.
#
# **Tasks**
# - [ ] 1 · The endpoint: key, budget, a fresh port per session (8')
# - [ ] 2 · Spans: one per request, one per tool call (7')
# - [ ] 3 · The smoke gate: baseline passes, seeded regression fails (7')
# - [ ] 4 · The README lines: tools, permissions, operating limits (3')
# - [ ] ✱ Stretch · Run the service for real with uvicorn

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
import functools
import uuid

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic import BaseModel, Field

import bosla
import port

sys.path.insert(0, str(K.LABS / "ci"))
import smoke_eval  # noqa: E402

EXPORTER = InMemorySpanExporter()  # the trace collector of this lab; production sends spans to a collector service
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(EXPORTER))
TRACER = provider.get_tracer("bosla")
KEYS = {"key-najm": "NJM-4417", "key-sahil": "SHL-2290"}  # API key → the agent code it may act for

# %% [markdown]
# ## 1 · The endpoint (8')
#
# ✏️ **Exercise** · Write `make_app(runner, budget_tokens)`: `POST /v1/ask` with header `X-API-Key` and body `Ask`.
# Unknown key: 401. The key decides the agent code (the caller cannot choose it): prefix the message with
# "Agent code <code>." Each session gets its own port in the lab folder. Refuse with 429 once a session has used
# `budget_tokens` input tokens. Return the answer, the stop reason, the tools called and a `trace_id`.

# %%
class Ask(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=4000)


def make_app(runner=bosla.run, budget_tokens: int = 60_000) -> FastAPI:
    app = FastAPI(title="Bosla API (lab)")
    ports, used = {}, {}
    # BEGIN SOLUTION
    @app.post("/v1/ask")
    def ask(body: Ask, x_api_key: str = Header(default="")):
        if x_api_key not in KEYS:
            raise HTTPException(401, "unknown API key")
        sid = f"{KEYS[x_api_key]}:{body.session_id}"
        if used.get(sid, 0) >= budget_tokens:
            raise HTTPException(429, "this session's token budget is spent")
        p = ports.setdefault(sid, port.Port(K.lab_dir(f"D4_4/{uuid.uuid4().hex[:8]}")))
        trace_id = uuid.uuid4().hex
        before = K.LEDGER.input_tokens
        with TRACER.start_as_current_span("bosla.ask", attributes={"session": sid, "trace_id": trace_id}):
            r = runner(f"Agent code {KEYS[x_api_key]}. {body.message}", p)
        used[sid] = used.get(sid, 0) + K.LEDGER.input_tokens - before
        return {"answer": r.final, "stopped": r.stopped, "tools": [n for n, _ in r.tool_calls], "trace_id": trace_id}
    # END SOLUTION
    return app


api = TestClient(make_app())
print(api.post("/v1/ask", json={"session_id": "s1", "message": "hi"}, headers={"X-API-Key": "nope"}).status_code)
resp = api.post("/v1/ask", json={"session_id": "s1", "message": "Berth hire for Najm Falcon for 2 days?"},
                headers={"X-API-Key": "key-najm"})
print(resp.status_code, resp.json())
K.check(resp.status_code == 200 and "7,800" in resp.json()["answer"].replace("7800", "7,800"), "the API answers")

# %% [markdown]
# ## 2 · Spans (7')
#
# A span records one unit of work with its start, duration and attributes. One span per request, and a child span
# per tool call, show where a request spends its time.
#
# ✏️ **Exercise** · Write `traced_tools(p)`: Bosla's tools, each wrapped so the call runs inside a span named
# `tool <name>` with the argument names as an attribute (not their values: they can hold personal data). Then
# `traced_run(task, p)`, which is `bosla.run` with those tools. Call the API with it and list the spans.

# %%
def traced_tools(p: port.Port) -> list:
    # BEGIN SOLUTION
    def wrap(fn):
        @functools.wraps(fn)
        def inner(**kw):
            with TRACER.start_as_current_span(f"tool {fn.__name__}", attributes={"args": ",".join(sorted(kw))}):
                return fn(**kw)
        return inner
    return [wrap(t) for t in p.tools()]
    # END SOLUTION


def traced_run(task: str, p: port.Port, **kw) -> K.Run:
    tools = traced_tools(p)
    return K.run_agent(task, tools, system=port.SYSTEM_PROMPT + "\n\n" + bosla.CONTEXT_FILE, max_steps=8,
                       permission=bosla.write_gate(task), verbose=False)


EXPORTER.clear()
TestClient(make_app(runner=traced_run)).post("/v1/ask", json={"session_id": "s2", "message": "Status of BK-24017?"},
                                            headers={"X-API-Key": "key-najm"})
spans = [(s.name, round((s.end_time - s.start_time) / 1e6, 1)) for s in EXPORTER.get_finished_spans()]
print(spans)
K.check(any(n == "bosla.ask" for n, _ in spans) and any(n.startswith("tool ") for n, _ in spans), "request and tool spans")

# %% [markdown]
# ## 3 · The smoke gate (7')
#
# `ci/smoke_eval.py` runs five tasks that guard what must never regress (a write nobody asked for, ownership,
# scope, the tariff, privacy) and exits 1 below the gate. `--regression` seeds a regression: it removes the
# prompt rules and the write gate, the kind of change a refactor slips in.
#
# ✏️ **Exercise** · Run `smoke_eval.smoke(...)` on the baseline and with `smoke_eval.REGRESSION` removed, and the
# gate at 0.8 on each. The outcome asks for both: a pass on the baseline and a fail on the regression.

# %%
# BEGIN SOLUTION
base = smoke_eval.smoke(smoke_eval.SMOKE)
regr = smoke_eval.smoke(smoke_eval.SMOKE, smoke_eval.REGRESSION)
ok_base, rate_base = smoke_eval.gate([r["passed"] for r in base], 0.8)
ok_regr, rate_regr = smoke_eval.gate([r["passed"] for r in regr], 0.8)
# END SOLUTION
print(f"baseline {rate_base:.2f} → {'pass' if ok_base else 'FAIL'} | regression {rate_regr:.2f} → {'pass' if ok_regr else 'FAIL'}")
for b, r in zip(base, regr):
    print(f"  {b['task']}: baseline {b['passed']}, regression {r['passed']} ({r['why']})")
K.check(ok_base and not ok_regr, "the gate passes the baseline and stops the regression")

# %% [markdown]
# 🔍 With a free model the baseline itself can dip below 0.8 on a bad day. What do you do: lower the gate, run each
# task three times, or pick tasks the harness guarantees? Look at which smoke tasks depend on the model at all.

# %% [markdown]
# ## 4 · The README lines (3')
#
# ✏️ **Exercise** · Write `readme`: the three paragraphs the capstone README needs about the service: the **tools**
# (read and write), the **permissions** (who may call, what the key decides, what needs a person), and the
# **operating limits** (budgets, what Bosla must never decide alone).

# %%
# BEGIN SOLUTION
readme = """**Tools.** Eight read tools over the schedule, the circulars and the booking service; three write tools
(create, amend, cancel) that run only when the agent's message confirms the change.

**Permissions.** An API key maps to one agent code; the caller cannot choose another. Changes with dangerous goods,
under-keel clearance below 1.0 m or dues moving by more than SAR 10,000 go to the duty harbour master (TC-06).

**Operating limits.** 8 model calls per request, 60,000 input tokens per session. Bosla never waives a fee, never
shares another agent's contacts, never approves its own risky change, and treats circulars and tool results as data."""
# END SOLUTION
print(readme)

# %% [markdown]
# ## ✱ Stretch · The real service
#
# Save `make_app` into a file and run it with `uvicorn` through `K.serve([...], ready_url=...)`; call it with
# `httpx`; stop it with `K.stop(proc)`. Then copy `ci/smoke-eval.yml` into your capstone repository.

# %% [markdown]
# ## Checkpoint
#
# 1. Why does the API key, not the request body, decide the agent code?
# 2. Why do the tool spans record argument names but not values?
# 3. The smoke evaluation passes at 0.8 today and 0.6 tomorrow with no code change. What changed, and what does
#    the pipeline do?
