---
course: "Agentic Systems Engineering: Loops, Context and Harnesses"
code: "AE-302"
version: "2027.2.0"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-302/index.html"
---

# Agentic Systems Engineering: Loops, Context and Harnesses

AI Engineering Track · 4 teaching days + capstone day · 26 hours · Level 300

Build an agent as a model in a loop calling typed tools, with most of the engineering in the harness

Participants build an agent as a model in a loop calling typed tools inside a sandbox, with most of the engineering in the harness. For a fictional ports authority they write the loop from scratch, budget the context, add a context file, a skill and a Model Context Protocol (MCP) server, compare an agent SDK with their own harness, gate bookings in a checkpointed state graph, and ship a traced, evaluated and contained agent behind an API.

**Who it is for:** Practitioners: developers and engineers who already build applications on language models and now need agents that are measured, contained and shipped.

**Format:** Intensive: 4 teaching days of four sessions and a capstone day, with guided pre-work and a tracked follow-up task

## The case study

**Marsa Ports Authority.** Marsa Ports Authority is a fictional Red Sea port authority with three services: a berth schedule, bilingual tariff circulars and a booking service with write actions. Participants build Bosla, its booking assistant, as a model in a loop calling typed tools: the loop from scratch, a context budget, a context file, a tariff skill and an MCP server over the circulars, an SDK comparison, a check of every booking against the schedule, evaluation over repeated trials, a booking graph that pauses for the duty harbour master at a risk threshold, an injection attack and its containment, and an API service gated in CI. All data is synthetic and generated with a fixed seed.

## The course

### Day 1: From Model to Agent

Slides: https://sdaiaacademy.github.io/ae-302/slides/day1.md

- **Session 1: Three API shapes**
  - Explain what a language model predicts and why its output varies
  - Call one open-weight model through three API shapes
  - Read stop reasons and token usage in each shape
  - [Lab 1.1: One model, three API shapes (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D1_1_three_shapes.ipynb)
- **Session 2: Structured outputs**
  - Define a schema whose constraints catch wrong values
  - Request output under a JSON Schema response format
  - Recover from malformed replies with validation and repair
  - [Lab 1.2: A berth request as a validated object (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D1_2_structured_outputs.ipynb)
- **Session 3: Tools**
  - Describe a tool call as a request the application executes
  - Write typed argument schemas for schedule and booking tools
  - Return errors a model can act on
  - [Lab 1.3: Typed tools with useful errors (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D1_3_typed_tools.ipynb)
- **Session 4: The agent loop from scratch**
  - Write an agent loop without a framework or AI assistance
  - Bound it with a step budget and explicit stop rules
  - Grade it on ten tasks from their traces
  - [Lab 1.4: The agent loop from scratch (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D1_4_agent_loop.ipynb)

### Day 2: Context Engineering

Slides: https://sdaiaacademy.github.io/ae-302/slides/day2.md

- **Session 1: Context as a budget**
  - Measure tokens per turn on a long agent task
  - Offload large tool results to files the agent can page through
  - Compact old turns into notes without losing what the answer needs
  - [Lab 2.1: Context as a budget (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D2_1_context_budget.ipynb)
- **Session 2: Retrieval for agents**
  - Score retrieval on the top hit, not only the top three
  - Build keyword search with Arabic normalisation and a vector search
  - Read from a trace which search tool the agent chose
  - [Lab 2.2: Keyword and vector search over circulars (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D2_2_retrieval.ipynb)
- **Session 3: Memory, skills and context files**
  - Write a short context file for an agent
  - Package a procedure as a skill with an index line
  - Show staged loading of a skill in a trace
  - [Lab 2.3: A context file and a tariff skill (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D2_3_context_skills.ipynb)
- **Session 4: Model Context Protocol**
  - Build an MCP server with tools and resources
  - Pass a provided test client in-process and over stdio
  - Connect an agent through capability discovery, with a trace
  - [Lab 2.4: An MCP server over the circular store (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D2_4_mcp.ipynb)

### Day 3: Harness and Loop

Slides: https://sdaiaacademy.github.io/ae-302/slides/day3.md

- **Session 1: Anatomy of a harness**
  - Name the parts of an agent harness and what each protects
  - Remove one part from a working agent and measure the effect
  - Read from paired traces where two runs part ways
  - [Lab 3.1: Remove one harness part (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D3_1_harness_teardown.ipynb)
- **Session 2: Agent SDKs and hosted agents**
  - Rebuild an agent on an agent SDK with a free model
  - Grade the SDK agent on the same tasks as the own loop
  - Compare code size, traces and control
  - [Lab 3.2: An agent SDK against your own loop (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D3_2_agents_sdk.ipynb)
- **Session 3: Loop engineering**
  - Write a check of agent actions against the rules
  - Keep the loop running while the check fails, within a budget
  - Compare outcomes with and without verification
  - [Lab 3.3: Verification inside the loop (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D3_3_loop_engineering.ipynb)
- **Session 4: Evaluating agents**
  - Grade agent runs with code and model graders
  - Compute success in any and in every trial
  - Compute cost per completed task
  - [Lab 3.4: Grading over five trials (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D3_4_evals.ipynb)

### Day 4: Graph and Production

Slides: https://sdaiaacademy.github.io/ae-302/slides/day4.md

- **Session 1: State graphs with checkpoints**
  - Model a booking flow as a state graph with checkpoints
  - Pause at an approval interrupt and resume after approval or rejection
  - Survive a restart without repeating work
  - [Lab 4.1: A booking graph with an approval gate (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D4_1_booking_graph.ipynb)
- **Session 2: Several agents and agent-to-agent delegation**
  - Split a task between a researcher and a drafter
  - Compare quality and cost of two agents against one
  - Decide when delegation pays
  - [Lab 4.2: Two agents or one? (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D4_2_multi_agent.ipynb)
- **Session 3: Securing agents**
  - Map the three legs of an injection risk for every tool
  - Reproduce a seeded prompt injection that leaks Restricted data
  - Contain it by removing one leg, and log the failed attempt
  - [Lab 4.3: A planted instruction, one leg removed (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D4_3_security.ipynb)
- **Session 4: Production**
  - Serve an agent behind an API with keys and budgets
  - Trace requests and tool calls with spans
  - Gate a release with a smoke evaluation that fails on a seeded regression
  - [Lab 4.4: Behind an API, traced, gated in CI (25 min)](https://sdaiaacademy.github.io/ae-302/labs/D4_4_ship_it.ipynb)

### Capstone: Capstone: a research agent and its defence

Slides: https://sdaiaacademy.github.io/ae-302/slides/day5.md

## Capstone

An individual research agent over the synthetic documents of Marsa Ports Authority, built on the course starter (labs/capstone/) or an own harness: at least three tools with one over MCP, a context rule, step and cost budgets, and a human approval on every write. It is evaluated on at least 15 tasks over five trials on two configurations, and contained by removing one leg of private data, untrusted content and exit path, with a logged injection run in which exfiltration fails.

**What you submit:** A public repository whose README reports success over repeated trials (pass^5 and pass@5), cost per completed task and the containment design, with the per-run results, the injection log and timestamped agent transcripts committed. Then an eight-minute live defence: the participant runs the agent on a task the assessor supplies and explains one failure from its trace.

**Rubric:**

- Working agent: 25%
- Context and harness design: 20%
- Evaluation over trials: 20%
- Containment: 20%
- Reproducibility: 15%

## Outcomes

- **LO1** Implement a tool-calling agent loop without a framework, with typed tool schemas, a step budget and explicit completion criteria, given three synthetic port services and ten tasks (Applied) Evidence: a loop that completes at least seven tasks, with a trace per run
- **LO2** Apply compaction, offloading of tool results and staged loading of skills, and measure the effect on tokens and success, given long tasks that overflow a fixed context budget (Applied) Evidence: a before-and-after table of tokens, cost and success
- **LO3** Implement a protocol server over a document store and connect the agent to it through capability discovery, given the port's circulars and a provided test client (Applied) Evidence: a server that passes the provided tests, with a trace of discovery and calls
- **LO4** Design a checkpointed state-graph agent with a human approval gate at a defined risk threshold, given booking changes, some of which affect safety or fees (Performance) Evidence: a graph that pauses, resumes after approval and survives a restart, with a test per path
- **LO5** Evaluate the agent over repeated trials, including runs against a seeded prompt injection, given 20 tasks with five trials each and a circular carrying planted instructions (Performance) Evidence: success in every and in any trial, cost per completed task, and a logged injection run in which exfiltration fails
- **LO6** Deliver the agent as a traced API service gated by a smoke evaluation in continuous integration, given a repository with a pipeline and a trace collector (Performance) Evidence: a run that passes on the baseline and fails on a seeded regression, and a README stating tools, permissions and operating limits

## Tools

- **Language model access:** a locally served open-weight model, a free hosted open-weight model, any commercial API
- **Agent framework with state graphs and checkpoints:** LangGraph, Pydantic AI with its graph library
- **Agent SDK for the comparison:** smolagents, OpenAI Agents SDK, Google Agent Development Kit
- **Protocol server SDK:** official Model Context Protocol Python SDK, FastMCP
- **Tracing and evaluation:** OpenTelemetry with Langfuse, Arize Phoenix, Inspect
- **Execution sandbox:** Docker or Podman containers with no network by default, OpenSandbox
- **API service and continuous integration:** FastAPI, GitLab CI, GitHub Actions

## Prerequisites

- AE-203 Building Applications on Language Models
- Writes typed Python and calls a web API that returns JSON
- Runs a container and reads its logs
- Setup: a laptop CPU with uv, or Google Colab, and a key for a free hosted model (OpenRouter by default). Nothing downloads a model. Run 00_setup_check before Day 1; see labs/README.md.

## Sources

### Agents, tools and context

- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Anthropic: Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [AGENTS.md, the context-file convention](https://agents.md/)
- [Liu et al.: Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172)

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

---

SDAIA Academy · AI Engineering Track · Agentic Systems Engineering: Loops, Context and Harnesses

Course version 2027.2.0 · engine 1.0.0 · built 2026-11-24 · commit 3d7c7b6
