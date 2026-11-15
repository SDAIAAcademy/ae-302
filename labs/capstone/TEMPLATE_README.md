# <Project name>

> One sentence: who asks this agent what, and what it gives back.

[Agentic Systems Engineering: Loops, Context and Harnesses - SDAIA Academy](https://github.com/sdaiaacademy/agentic-ai/)

**Author:** <name>
**Model(s):** <a free hosted open-weight model, or another>, chosen because <your own evaluation>
**Harness:** <the course starter / your own>

## Problem

What does the agent need to cover? Write 5 to 8 lines:

- the questions it answers;
- who asks them today, and how long they take;
- what a correct answer must contain.

## How to run

```bash
uv run <your_script>.py ask "<an example question>"
uv run <your_script>.py eval tasks.jsonl --config A B --trials 5
```

Put the API key in `.env` as `OPENROUTER_API_KEY` (or another provider's key). No keys are committed.

## Context and harness design

| Part | Your decision | Why |
|---|---|---|
| Spec / context file | | |
| Context rule (retrieval, offloading, compaction, skills) | | |
| Tools and their errors | | |
| Budgets (steps, cost) and stop rule | | |
| Checks before the loop may stop | | |
| Approvals | | |

## Tools, permissions and operating limits

| Tool | Read or write | Over MCP? | Needs approval? | Leg (private data, untrusted content, exit path) |
|---|---|---|---|---|
| | | | | |

**The agent never decides alone:** <list them>

## Evaluation over trials

**Suite:** <N ≥ 15> tasks in `tasks.jsonl`, graded by code: <which checks, and why>.

**Configurations:** A = <baseline>; B = <the one change>.

| Config | pass^5 | pass@5 | per trial | cost per completed task |
|---|---|---|---|---|
| A | | | | |
| B | | | | |

### Error analysis

| Cause | Runs (A) | Runs (B) | Example task and trial | What you changed |
|---|---|---|---|---|
| | | | | |

## Containment

- **Legs:** which of the three your system has, and where they meet.
- **Leg removed:** what you removed, and whether code enforces it or it depends on the model.
- **Injection run:** the planted document, and the log file in which exfiltration fails.
- **PDPL and classification:** what personal data any part of the system can read, and why that is the minimum.
- **Residual risk:** what is still possible.

## Evidence

Link the files that back every number above:

- the per-run CSVs for A and B;
- the injection log;
- the audit log;
- the agent transcripts with timestamps.

## AI assistance

Which coding agents or assistants you used, and for what. You are answerable for every decision and number here.

## Limitations

What does not work yet, and what production would need.
