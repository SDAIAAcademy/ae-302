# Capstone · A research agent over the port's documents

The capstone is individual. You build a **research agent over Marsa Ports Authority's synthetic documents**, either on the
starter in this folder or on your own harness. You publish it in a **public repository**. Its README reports
success over repeated trials, cost per completed task and the containment design. Then you defend it in an
**eight-minute live defence**: you run the agent on a task the assessor gives you and explain one failure from its trace.

## What the agent does

It answers research questions that need more than one source. For example:

- Which circular applies, and is an older one superseded?
- What does a vessel pay, given its tonnage, the days and its cargo?
- What does a newly received circular say?

It cites the circular or the tool behind each claim. It can write one thing, a brief for the tariff office, and only
after a person approves. You choose the questions it is for and the tools it gets. You may add your own synthetic
documents.

Use the course's synthetic data, or data you generate yourself. No personal data and no internal documents from your entity.

## Minimum requirements

1. **A working agent.** It completes multi-step research tasks with at least three tools, and at least one of them is reached over MCP.
2. **Context and harness design.** It needs:
   - a context file or spec;
   - a deliberate context rule, such as retrieval, offloading, compaction or staged skills;
   - step and cost budgets;
   - a human approval on every write.
3. **Evaluation over trials.** Run at least **15 tasks** with code graders, **five trials each**, on two configurations
   that differ in one thing. Report:
   - success in every trial (pass^5) and in any trial (pass@5);
   - **cost per completed task**;
   - an error analysis.
4. **Containment.** Show the three legs of your system: private data, untrusted content and exit path. Show the leg
   you removed, and **a logged injection run in which exfiltration fails**, using TC-09 or your own planted
   document. Judge the design against the PDPL as well as security.
5. **Reproducibility.** It runs from a clean clone with `uv run` and an API key. Every number in the README is backed by a
   committed file.

## Rubric

| Criterion | Points |
|---|---|
| Working agent | 25 |
| Context and harness design | 20 |
| Evaluation over trials | 20 |
| Containment | 20 |
| Reproducibility | 15 |

The capstone repository counts for 60% of the course result, and you need at least 60% on this rubric. The live
defence of one harness decision counts for 20%. The supervised entry and exit checks count for the other 20%: you
read a trace and predict the next step, without AI assistance. The pass mark is 70% overall.

**AI policy.** AI-full: coding agents are allowed. Keep the transcripts and run logs with timestamps. They are part of
the evidence of authorship, together with the defence.

## Getting started

```bash
cd labs
uv run capstone/starter.py ask "Which circular sets berth hire now, and what does Sahil Tide pay for 3 days with fuel?"
uv run capstone/starter.py eval capstone/tasks.example.jsonl --config A B --trials 5
```

The starter already wires most of the plumbing:

- **Tools.** The circulars come over the course's MCP server (`servers/marsa_mcp.py`). The port's read tools run in
  the same process. There is a reader for newly received circulars, which are untrusted, and a `save_brief` write
  action that asks a person first.
- **Context.** A research spec serves as the system prompt, and tool results are capped in size.
- **Harness.** Step and cost budgets, an audit log that records argument names and sizes but not values, and a
  permission policy.
- **Evaluation.** Repeated trials on fresh ports with code graders (`porttasks.grade`). It reports pass^k, pass@k and
  cost per completed task, and writes a per-run CSV.

Search the starter for `CAPSTONE:` and replace those parts with your own. The five example tasks show the format; you
write at least fifteen.

The labs closest to each part:

| You need | Start from |
|---|---|
| the loop and its stop rule | Lab 1.4, `agentkit.run_agent` |
| retrieval over circulars | Lab 2.2 |
| a context file and staged skills | Lab 2.3, `data/bosla/` |
| an MCP server | Lab 2.4, `servers/marsa_mcp.py` |
| a check before the loop may stop | Lab 3.3, `bosla.py` |
| grading over trials | Lab 3.4 |
| a graph with an approval gate | Lab 4.1 |
| removing one leg, and the injection log | Lab 4.3 |
| an API, spans and a CI gate | Lab 4.4, `ci/` |

**Free quota.** Fifteen tasks × five trials × two configurations is 150 runs, at about four requests each. Free hosted
models limit requests per day. Develop on three tasks and one trial, then run the full suite once. Keep the response
cache off for the scored runs (the starter does this), because cached replies are not new trials.

## Timeline

| When | What |
|---|---|
| Day 4, after Session 4 | Choose the questions your agent is for. Write the pitch, three tasks and the three legs. |
| Day 4, evening | Copy `TEMPLATE_README.md` as your README. Write fifteen tasks. Run configuration A over five trials. Read the failures. Change one thing (B). Plant one injection. |
| Day 5 | Re-run both configurations and the injection. Test a clean clone. Finish the README, publish the repository, then defend it for eight minutes. |

## The defence (eight minutes)

1. **Two minutes.** The problem, the design and the numbers.
2. **Three minutes.** Run the agent on a task the assessor gives you.
3. **Three minutes.** One failure from a trace: what the agent saw, what it did, and what in the harness would
   prevent it.

The assessor may ask about any decision in the README.
