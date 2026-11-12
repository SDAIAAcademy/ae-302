<!-- academy:title -->
# Agentic Systems Engineering: Loops, Context and Harnesses

AI Engineering Track · SDAIA Academy · AE-302 · Level 300

Build an agent as a model in a loop calling typed tools, with most of the engineering in the harness

Participants build an agent as a model in a loop calling typed tools inside a sandbox, with most of the engineering in the harness. For a fictional ports authority they write the loop from scratch, budget the context, add a context file, a skill and a Model Context Protocol (MCP) server, compare an agent SDK with their own harness, gate bookings in a checkpointed state graph, and ship a traced, evaluated and contained agent behind an API.

**Format:** Intensive: 4 teaching days of four sessions and a capstone day, with guided pre-work and a tracked follow-up task

**Course page:** https://sdaiaacademy.github.io/agentic-ai/
<!-- /academy:title -->

The whole course follows one case study: **Marsa Ports Authority**, a fictional Red Sea port authority, and **Bosla
(بوصلة)**, the booking assistant participants build for it. The port has three services: a berth schedule, bilingual
tariff circulars and a booking service with write actions. The schedule, circulars, bookings and tasks are synthetic and
generated with a fixed seed by `labs/port_data.py`. One circular, TC-09, carries a planted instruction for the
security lab.

Every lab runs on free hosted models (OpenRouter by default), on a laptop CPU with [uv](https://docs.astral.sh/uv/) or
on Google Colab. Nothing downloads a model. See [labs/README.md](labs/README.md).

<!-- academy:units -->
## Units

| Unit | Title | Sessions | Slides |
|---|---|---|---|
| Day 1 | From Model to Agent | Three API shapes; Structured outputs; Tools; The agent loop from scratch | [`slides/day1.html`](slides/day1.html) |
| Day 2 | Context Engineering | Context as a budget; Retrieval for agents; Memory, skills and context files; Model Context Protocol | [`slides/day2.html`](slides/day2.html) |
| Day 3 | Harness and Loop | Anatomy of a harness; Agent SDKs and hosted agents; Loop engineering; Evaluating agents | [`slides/day3.html`](slides/day3.html) |
| Day 4 | Graph and Production | State graphs with checkpoints; Several agents and agent-to-agent delegation; Securing agents; Production | [`slides/day4.html`](slides/day4.html) |
| Capstone | Capstone: a research agent and its defence |  | [`slides/day5.html`](slides/day5.html) |
<!-- /academy:units -->

<!-- academy:labs -->
## Labs

Every lab is a notebook in `labs/`. Open it in Google Colab from the course page, or run it locally with `uv`. Exercises raise `NotImplementedError` until they are done; the reference versions are in `labs/solutions/`.

| | Session | Lab | File |
|---|---|---|---|
| 1.1 | Day 1 · Session 1 | One model, three API shapes | [`D1_1_three_shapes.ipynb`](labs/D1_1_three_shapes.ipynb) |
| 1.2 | Day 1 · Session 2 | A berth request as a validated object | [`D1_2_structured_outputs.ipynb`](labs/D1_2_structured_outputs.ipynb) |
| 1.3 | Day 1 · Session 3 | Typed tools with useful errors | [`D1_3_typed_tools.ipynb`](labs/D1_3_typed_tools.ipynb) |
| 1.4 | Day 1 · Session 4 | The agent loop from scratch | [`D1_4_agent_loop.ipynb`](labs/D1_4_agent_loop.ipynb) |
| 2.1 | Day 2 · Session 1 | Context as a budget | [`D2_1_context_budget.ipynb`](labs/D2_1_context_budget.ipynb) |
| 2.2 | Day 2 · Session 2 | Keyword and vector search over circulars | [`D2_2_retrieval.ipynb`](labs/D2_2_retrieval.ipynb) |
| 2.3 | Day 2 · Session 3 | A context file and a tariff skill | [`D2_3_context_skills.ipynb`](labs/D2_3_context_skills.ipynb) |
| 2.4 | Day 2 · Session 4 | An MCP server over the circular store | [`D2_4_mcp.ipynb`](labs/D2_4_mcp.ipynb) |
| 3.1 | Day 3 · Session 1 | Remove one harness part | [`D3_1_harness_teardown.ipynb`](labs/D3_1_harness_teardown.ipynb) |
| 3.2 | Day 3 · Session 2 | An agent SDK against your own loop | [`D3_2_agents_sdk.ipynb`](labs/D3_2_agents_sdk.ipynb) |
| 3.3 | Day 3 · Session 3 | Verification inside the loop | [`D3_3_loop_engineering.ipynb`](labs/D3_3_loop_engineering.ipynb) |
| 3.4 | Day 3 · Session 4 | Grading over five trials | [`D3_4_evals.ipynb`](labs/D3_4_evals.ipynb) |
| 4.1 | Day 4 · Session 1 | A booking graph with an approval gate | [`D4_1_booking_graph.ipynb`](labs/D4_1_booking_graph.ipynb) |
| 4.2 | Day 4 · Session 2 | Two agents or one? | [`D4_2_multi_agent.ipynb`](labs/D4_2_multi_agent.ipynb) |
| 4.3 | Day 4 · Session 3 | A planted instruction, one leg removed | [`D4_3_security.ipynb`](labs/D4_3_security.ipynb) |
| 4.4 | Day 4 · Session 4 | Behind an API, traced, gated in CI | [`D4_4_ship_it.ipynb`](labs/D4_4_ship_it.ipynb) |
<!-- /academy:labs -->

## Capstone

A research agent over the port's synthetic documents, built on the starter in [labs/capstone/](labs/capstone/) or on
your own harness. You publish it in a public repository whose README reports:

- success over repeated trials;
- cost per completed task;
- the containment design.

Then you defend it for eight minutes: you run the agent on a task the assessor supplies and explain one failure from its
trace.

## Repository

```
course.json   the course manifest: outcomes, days, sessions, labs, capstone, tools, sources
slides/       one deck per day; the engine builds them into the course site
labs/         notebooks and their solutions, the port (port.py, data/), the reference agent (bosla.py),
              the helper module (agentkit.py), the MCP server (servers/), the CI smoke evaluation (ci/), the capstone kit
```

Build and check with the Academy engine: `node academy.mjs check`, `node academy.mjs build`.

<!-- academy:tools -->
## Tools

Each line is a capability; the examples are interchangeable.

- **Language model access:** a locally served open-weight model, a free hosted open-weight model, any commercial API
- **Agent framework with state graphs and checkpoints:** LangGraph, Pydantic AI with its graph library
- **Agent SDK for the comparison:** smolagents, OpenAI Agents SDK, Google Agent Development Kit
- **Protocol server SDK:** official Model Context Protocol Python SDK, FastMCP
- **Tracing and evaluation:** OpenTelemetry with Langfuse, Arize Phoenix, Inspect
- **Execution sandbox:** Docker or Podman containers with no network by default, OpenSandbox
- **API service and continuous integration:** FastAPI, GitLab CI, GitHub Actions
<!-- /academy:tools -->

<!-- academy:sources -->
## Sources

### Agents, tools and context

- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Anthropic: Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [AGENTS.md, the context-file convention](https://agents.md/)

### Harnesses, SDKs and evaluation

- [Birgitta Böckeler: Harness engineering](https://martinfowler.com/articles/harness-engineering.html)
- [OpenAI Agents SDK documentation](https://openai.github.io/openai-agents-python/)
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

### Protocols and several agents

- [Model Context Protocol: versioning](https://modelcontextprotocol.io/specification/versioning)
- [MCP Python SDK v2: migration guide](https://py.sdk.modelcontextprotocol.io/v2/migration/)
- [Agent2Agent (A2A) protocol](https://a2a-protocol.org/)
- [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Cognition: Don't build multi-agents](https://cognition.ai/blog/dont-build-multi-agents)

### Security and governance

- [OWASP GenAI Security Project: Top 10 for Agentic Applications for 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [Simon Willison: The lethal trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)
- [Simon Willison: The dual LLM pattern](https://simonwillison.net/2023/Apr/25/dual-llm-pattern/)
- [Debenedetti et al.: Defeating prompt injections by design (CaMeL)](https://arxiv.org/abs/2503.18813)
- [SDAIA: national data and AI regulations, including the PDPL](https://sdaia.gov.sa/)
<!-- /academy:sources -->
