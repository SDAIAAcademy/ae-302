---
course: "Agentic Systems Engineering: Loops, Context and Harnesses"
code: "AE-302"
version: "2027.2.0"
deck: "day5"
day: 5
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-302/slides/day5.html"
---

# Agentic Systems Engineering: Loops, Context and Harnesses

## Capstone: Capstone: a research agent and its defence

#### [day5#title] Capstone: a research agent and its defence

*SDAIA Academy · Agentic Systems Engineering: Loops, Context and Harnesses*

Capstone

AI Engineering Track · 4 teaching days + capstone day · 8 min talk and demo · AE-302

#### [day5#agenda] Finish, publish, defend

*Day 5*

- **Morning · finish**: Re-run both configurations over five trials, re-run the injection, test a clean clone, finish the README
- **Deadline · publish**: The public repository, with results, logs and transcripts committed
- **Afternoon · defend**: Eight minutes each: the numbers, a live run on an unseen task, one failure from its trace

#### [day5#the-brief] A research agent over the port's documents

*What you build*

**Tariff office:** Sahil Tide carries fuel and wants a berth for 3 days. What does it pay, and which circulars apply?

**Your agent:** SAR 12,960: berth hire under TC-07 with the 20% dangerous-goods surcharge of TC-04. TC-02 is superseded.

- Questions that need several sources, each claim cited.
- The course starter or your own harness.
- At least three tools, one over MCP.
- One write action (a brief), behind a person's approval.

#### [day5#report-over-trials] Success over repeated trials, and what a completed task costs

*The numbers the README reports*

| Config | pass^5 | pass@5 | per trial | cost per completed task |
| --- | --- | --- | --- | --- |
| A · baseline | … | … | … | … |
| B · one change | … | … | … | … |

- At least 15 tasks, five trials each, graded by code, response cache off.
- An error analysis: the causes counted, and what flipped between A and B.

#### [day5#containment-design] Show your three legs, the one you removed, and the failed attack

*Containment*

- **Private data.** What personal data can any part read? Why is that the minimum (PDPL)?
- **Untrusted content.** TC-09 or your own planted document, read by the agent.
- **Exit path.** What could send data out, and what code stops it?

> **Evidence:** a logged injection run in which exfiltration fails, with tool results logged by size, not content.

#### [day5#rubric] Five criteria, 100 points

*How the repository is scored*

| Item | Value |
| --- | --- |
| Working agent | 25% |
| Context and harness design | 20% |
| Evaluation over trials | 20% |
| Containment | 20% |
| Reproducibility | 15% |

> **Pass:** 70% overall, and at least 60% on this rubric. The repository is 60% of the result, the defence 20%, the supervised checks 20%.

#### [day5#defence-format] Eight minutes: the numbers, a live run, one failure

*The defence*

- **2 min · the design.** The problem, the harness, the table of trials.
- **3 min · a live run.** The assessor gives a task you have not seen; run it.
- **3 min · one failure.** From a trace: what the agent saw, did, and what would prevent it.

> **AI-full.** Coding agents were allowed; the defence is where you show the decisions are yours.

#### [day5#running-order] Who defends when

*Running order*

| # | Participant | Repository |
| --- | --- | --- |
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |
| 4 |  |  |
| 5 |  |  |
| 6 |  |  |

#### [day5#final-prep] Ten minutes: clone it clean, run one task

*Final preparation*

Clone your public repository into a new folder and run one task from its README. If that fails, the assessor's will too.

#### [day5#now-presenting] Defence

*Now defending*

#### [day5#review] What the room learned

*After the defences*

- **The most common failure.** Which cause appeared in most error analyses?
- **The best containment.** Which removed leg held without the model's help?
- **The cheapest completion.** Whose cost per completed task was lowest, and why?

#### [day5#what-next] The follow-up task, and the AE Associate badge

*What next*

- **Follow-up task.** Within four weeks, apply one harness change to an agent at work and report its trial numbers before and after.
- **Keep the repository.** It is the evidence the AE Associate badge looks at.
