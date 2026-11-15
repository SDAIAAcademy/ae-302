# Agentic Systems Engineering: labs

Hands-on notebooks for the SDAIA Academy course **AE-302 Agentic Systems Engineering: Loops, Context and Harnesses (هندسة الأنظمة الوكيلة: الحلقات والسياق والأُطر)**. Every lab builds a piece of **Bosla (بوصلة)**, the booking assistant of **Marsa Ports Authority**, a fictional Red Sea port with a berth schedule, bilingual tariff circulars and a booking service with write actions. Each lab starts from a supplied reference state, so none depends on an earlier one.

All labs use **free models over an API**. Nothing runs a model on your machine, and a laptop CPU or a Colab CPU runtime is enough.

## Quick start

**1 · Get a free OpenRouter key.** Create one at <https://openrouter.ai/keys>. Free models (IDs ending in `:free`) allow 50 requests a day and 20 a minute. A one-time purchase of 10 credits raises the limit to 1,000 free-model requests a day; the credits are not spent by free models. Identical requests are replayed from `labs/cache/`, so re-running a cell costs nothing.

**2a · Google Colab**
1. Open a notebook from the [course page](https://sdaiaacademy.github.io/ae-302/), or directly: `https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/<notebook>.ipynb`.
2. In the 🔑 **Secrets** panel add `OPENROUTER_API_KEY` and turn on notebook access.
3. Run the first cell. It clones this repository and installs `requirements-colab.txt`.

**2b · Local**
```bash
git clone https://github.com/SDAIAAcademy/ae-302
cd agentic-ai/labs
cp .env.example .env           # then paste your key into .env
uv sync                        # creates .venv from pyproject.toml (uv.lock pins every version)
uv run python port_data.py     # optional: rebuilds data/port.sqlite (committed)
uv run jupyter lab
```
Run `00_setup_check.ipynb` once before Day 1. It checks your key against all three API shapes and checks `uv`.

**Standalone programs** (the MCP server, the CI smoke evaluation) are single-file [PEP 723](https://peps.python.org/pep-0723/) scripts that declare their own dependencies. Run them with `uv run <file>.py`.

## Models and providers

| Setting (`.env`) | Default | Notes |
|---|---|---|
| `AGENT_PROVIDER` | `openrouter` | `openrouter`, `hf` (Hugging Face Inference Providers, needs credits) or `custom` |
| `AGENT_MODEL` | `google/gemma-4-31b-it:free` | any free tool-calling model from <https://openrouter.ai/models?max_price=0&supported_parameters=tools> |
| `AGENT_SMALL_MODEL` | `google/gemma-4-26b-a4b-it:free` | cheaper steps: triage, judges, summaries |
| `AGENT_FALLBACKS` | `google/gemma-4-26b-a4b-it:free,nvidia/nemotron-3-super-120b-a12b:free` | tried in order when a free model is rate-limited |
| `AGENT_CACHE` | `1` | `0` sends every request to the model |
| `AGENT_QUICK` | `0` | `1` shrinks eval runs and samples to save free requests |

Free models change often. If the default disappears or is busy, pick another free model with tool support and check it on [Artificial Analysis](https://artificialanalysis.ai/models), [BFCL](https://gorilla.cs.berkeley.edu/leaderboard.html) or [τ²-bench](https://taubench.com) before relying on it.

**Any other engine** that serves the OpenAI and/or Anthropic API shapes works with `AGENT_PROVIDER=custom`: vLLM, SGLang, llama.cpp, Ollama, LM Studio or LiteLLM. Set `LLM_BASE_URL` (OpenAI shape, ending in `/v1`), `LLM_ANTHROPIC_BASE_URL` (Messages shape), `LLM_API_KEY` and `LLM_MODEL`. A small Qwen or Gemma model is enough for local experiments; the labs are tuned for the free API models.

## Notebooks

| Day | Session | Notebook | API shapes |
|---|---|---|---|
| 0 | Setup | [`00_setup_check.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/00_setup_check.ipynb) | all three |
| 1 | One model, three API shapes | [`D1_1_three_shapes.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D1_1_three_shapes.ipynb) | all three |
| 1 | A berth request as a validated object | [`D1_2_structured_outputs.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D1_2_structured_outputs.ipynb) | Chat Completions |
| 1 | Typed tools with useful errors | [`D1_3_typed_tools.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D1_3_typed_tools.ipynb) | Chat Completions |
| 1 | The agent loop from scratch | [`D1_4_agent_loop.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D1_4_agent_loop.ipynb) | Chat Completions |
| 2 | Context as a budget | [`D2_1_context_budget.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D2_1_context_budget.ipynb) | Chat Completions |
| 2 | Keyword and vector search over circulars | [`D2_2_retrieval.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D2_2_retrieval.ipynb) | Chat Completions |
| 2 | A context file and a tariff skill | [`D2_3_context_skills.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D2_3_context_skills.ipynb) | Chat Completions |
| 2 | An MCP server over the circular store | [`D2_4_mcp.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D2_4_mcp.ipynb) | MCP |
| 3 | Remove one harness part | [`D3_1_harness_teardown.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D3_1_harness_teardown.ipynb) | Chat Completions |
| 3 | An agent SDK against your own loop | [`D3_2_agents_sdk.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D3_2_agents_sdk.ipynb) | Agents SDK |
| 3 | Verification inside the loop | [`D3_3_loop_engineering.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D3_3_loop_engineering.ipynb) | Chat Completions |
| 3 | Grading over five trials | [`D3_4_evals.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D3_4_evals.ipynb) | Chat Completions |
| 4 | A booking graph with an approval gate | [`D4_1_booking_graph.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D4_1_booking_graph.ipynb) | LangGraph + SQLite checkpoints |
| 4 | Two agents or one? | [`D4_2_multi_agent.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D4_2_multi_agent.ipynb) | Chat Completions |
| 4 | A planted instruction and one leg removed | [`D4_3_security.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D4_3_security.ipynb) | Chat Completions + hooks |
| 4 | Behind an API, traced, gated in CI | [`D4_4_ship_it.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-302/blob/main/labs/D4_4_ship_it.ipynb) | FastAPI + OpenTelemetry |

Exercises are marked **✏️ Exercise** and raise `NotImplementedError` until you fill them in. Complete reference versions are in `solutions/`. Cells marked **✱ Stretch** are optional. Self-checks print ✅ or ❌. With free models, an occasional ❌ on an answer-quality check can be the model rather than your code: re-run, or compare with the solution.

Labs don't depend on each other. Each one opens a fresh copy of the port database in `artifacts/<lab>/`, so write tools never change the shared data. Delete `artifacts/` before running the course's `academy check`, which reports ignored files under `labs/`.

## The case study: Marsa Ports Authority

Synthetic and deterministic, dated around **1 November 2026** (the labs' "today"); no real personal data.

| Data | File | Contents |
|---|---|---|
| Port database (SQLite) | `data/port.sqlite`, built by `port_data.py` (fixed seed) | 8 berths, 3 shipping agents, 14 vessels, 14 bookings with contact persons (synthetic personal data, classified Restricted by TC-05), an audit log |
| Tariff circulars | `data/circulars/TC-01 … TC-08` | bilingual Markdown: scope, berth hire (TC-02 superseded by TC-07), berth fit, dangerous goods, contact data, amendments and approval, lead times |
| A planted circular | `data/circulars_untrusted/TC-09` | received by email, carries an instruction for "automated assistants" (Lab 4.3 only) |
| Tasks | `data/tasks/` | ten Day 1 tasks, twenty evaluation tasks (five with a rubric), twelve retrieval questions |
| Reference states | `data/reference/` | a long-task history (Lab 2.1) and 100 recorded runs (Lab 3.4; **synthetic**, written by `_tools/make_reference.py`) |
| Context file and skills | `data/bosla/` | Bosla's AGENTS.md and two skills, `tariff-quote` and `booking-change` (Lab 2.3) |
| Berth requests | `data/berth_requests.jsonl` | six requests in English and Arabic with correct answers (Lab 1.2) |

`port.py` exposes the three services as typed, documented tools: schedule (`list_berths`, `get_vessel`, `berth_schedule`, `find_windows`), tariff (`search_circulars`, `get_circular`, `compute_dues`) and booking (`get_booking`, and the write tools `create_booking`, `amend_booking`, `cancel_booking`). The tools enforce ownership, overlaps and lead times and raise `ToolError` messages the model can act on. They do **not** check under-keel clearance: that is Lab 3.3's planted problem.

`bosla.py` is the reference agent of Days 3 and 4: the loop of `agentkit.run_agent` inside a harness of named parts that a lab can switch off. `porttasks.py` loads tasks and grades runs by code.

Planted problems, for the trainer: TC-02 is superseded by TC-07 (52,000 GT for 3 days is SAR 15,600, not 12,480); Najm Coral (V-108) fits B03 by length but has 0.8 m under the keel; BK-24030 belongs to Sahil Feeders, not Najm Lines; BK-24029 carries dangerous goods; TC-09 carries an injected instruction.

## Standalone programs

| Script | What it is | Run |
|---|---|---|
| `servers/marsa_mcp.py` | The circular store as an MCP server (Lab 2.4 reference); `mcp_test_client.py` holds its tests | `uv run servers/marsa_mcp.py` (stdio) or `--http 8765` |
| `ci/smoke_eval.py` | Five smoke tasks and a pass-rate gate for CI; `--regression` seeds a regression that must fail | `uv run ci/smoke_eval.py --min-rate 0.8` |
| `ci/smoke-eval.yml` | A GitHub Actions workflow to copy into the capstone repository | |
## Helpers: `agentkit.py`

| Helper | What it does |
|---|---|
| `client()`, `anthropic_client()` | OpenAI and Anthropic SDK clients pointed at the configured provider |
| `chat(messages, tools=...)` | one cached, retried Chat Completions call with free-model fallbacks |
| `tool_schema(fn, shape)` | a tool definition from a typed, documented Python function, for `chat`, `responses`, `anthropic` or `mcp` |
| `call_tool(tools, name, args)` | runs a tool call; returns JSON, or a JSON error the model can recover from |
| `run_agent(task, tools, shape=...)` | the course's reference agent loop over all three API shapes, with budgets, permissions and hooks |
| `count_tokens(obj)` | token estimate of a string or a request part, with an open tokenizer from the Hub |
| `MCPBridge(server)` | an MCP client usable from synchronous code; `agent_tools()` turns MCP tools into loop tools |
| `structured(prompt, Schema)` | one call whose answer validates as a Pydantic model (`response_format` + one repair) |
| `serve(cmd, ready_url)` / `stop(proc)` | start a background server (e.g. `uv run servers/...`) and stop it with its child processes |
| `LEDGER` | calls, tokens, cached tokens and cost so far |

`porttasks.grade(task, final, tool_calls, port)` grades a run by code: strings in the answer, write calls, the database after the run.

**Windows and long folder paths.** If an import fails with "The filename or extension is too long", keep the virtual environment in a short folder: set `UV_PROJECT_ENVIRONMENT` to a short path (for example a folder at the root of your drive) before `uv sync`.
