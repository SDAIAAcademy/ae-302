---
course: "Agentic Systems Engineering: Loops, Context and Harnesses"
code: "AE-302"
version: "2027.2.0"
deck: "day3"
day: 3
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-302/slides/day3.html"
---

# Agentic Systems Engineering: Loops, Context and Harnesses

## Day 3: Harness and Loop

#### [day3#title] Harness and Loop

*SDAIA Academy · Agentic Systems Engineering: Loops, Context and Harnesses*

Day 3

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-302

#### [day3#agenda] Harness and Loop

*Today*

- **Session 1 · Anatomy of a harness**: Tools, context, state and feedback around the model, and what each part protects
- **Session 2 · Agent SDKs and hosted agents**: What an SDK gives and takes away compared with your own loop
- **Session 3 · Loop engineering**: Verification inside the loop: the agent may not stop while a check fails
- **Session 4 · Evaluating agents**: Code and model graders, repeated trials, success in any and every trial, cost per completed task

### Session 1: Anatomy of a harness

#### [day3#s1] Anatomy of a harness

*Session 1*

- Name the parts of an agent harness and what each protects
- Remove one part from a working agent and measure the effect
- Read from paired traces where two runs part ways

#### [day3#harness-four-parts] The model is one part; the harness is the rest

*Anatomy of a harness*

- **Tools.** Typed contracts, useful errors, checks in code.
- **Context.** Prompt, context file, skills, budgets.
- **State.** History, the database, sessions, traces.
- **Feedback.** Stop rules, gates, verification, evaluation.

The same model behind two harnesses is two different agents. Most of this course's engineering is in these four boxes.

#### [day3#bosla-named-parts] The reference agent has named parts you can switch off

*labs/bosla.py*

| Part | What it does |
| --- | --- |
| `prompt_rules` | scope, citing circulars, never revealing other agents' data |
| `context_file` | data/bosla/AGENTS.md in the prompt |
| `useful_errors` | errors that say what to send instead |
| `step_budget` | 8 model calls, not 40 |
| `write_gate` | writes run only when the agent's message says "I confirm" |

#### [day3#remove-one-part] Remove one part, run the same ten tasks, compare the traces

*Lab 3.1*

1. **1 · Predict** which tasks break
2. **2 · Baseline** full harness
3. **3 · Remove** one part
4. **4 · Explain** from paired traces

> **Each table removes a different part.** The room's results together are the map of what each part protects on these tasks.

#### [day3#which-task-protects] Each part protects a task, if the tasks test it

*What to expect*

| Removed | Task most at risk | Why |
| --- | --- | --- |
| `write_gate` | T04 "do not book yet" | only the model's care stops a write |
| `useful_errors` | T09 wrong agent code | "failed" does not say what to do |
| `prompt_rules` | T02 superseded tariff, T10 scope | no rule to cite TC-07 or decline |
| `step_budget` | none of the ten | until a tool never finishes |

#### [day3#remove-scaffolding] Re-test the scaffolding when the model changes

*A durable habit*

- Some harness parts compensate for a weak model: long prompts, extra checks, forced steps.
- A stronger model may not need them, and they still cost tokens and latency.
- Other parts never go: the write gate and the ownership check protect people, not the model.

- **The method is the lab.** Remove one part, run the evaluation, keep the part only if the numbers say so, or if it protects someone.

#### [day3#checkpoint-1] No task broke

*Checkpoint*

**Question:** Your table removed the step budget and all ten tasks still passed. What do you conclude?

- A. The step budget is useless and can go
- B. The ten tasks do not exercise it; add a task that loops before judging
- C. The model is too good to need budgets
- D. Raise the budget to 40 everywhere

#### [day3#lab-3-1] Remove one harness part

Lab 3.1 · 25 min

Run the reference Bosla on ten tasks, remove one harness part, run again, and record from the traces what broke.

[D3_1_harness_teardown.ipynb](https://sdaiaacademy.github.io/ae-302/labs/D3_1_harness_teardown.ipynb)

- [ ] Map the parts, and predict (4 min)
- [ ] Baseline: the full harness on ten tasks (6 min)
- [ ] Remove one part and run again (10 min)
- [ ] What broke, and where in the trace (5 min)
- [ ] ✱ Stretch: Remove a second part: do the effects add up?

### Session 2: Agent SDKs and hosted agents

#### [day3#s2] Agent SDKs and hosted agents

*Session 2*

- Rebuild an agent on an agent SDK with a free model
- Grade the SDK agent on the same tasks as the own loop
- Compare code size, traces and control

#### [day3#sdk-is-a-harness] An agent SDK is a harness someone else wrote

*Agent SDKs*

- **OpenAI Agents SDK.** Agents, tools, handoffs, guardrails, sessions, tracing. Used in Lab 3.2.
- **smolagents.** Hugging Face's small agent library; agents that can write code as actions.
- **Google ADK.** Agent Development Kit: agents, tools and workflows.

The entry names these three as interchangeable examples. Each has a loop inside: find it, and the rest is configuration.

#### [day3#sdk-on-free-model] The SDK on a free model: wrap a client, list the tools

*Lab 3.2 · step 1*

```python
# file: Lab 3.2
client = AsyncOpenAI(base_url=OPENROUTER, api_key=key)
model = OpenAIChatCompletionsModel(model=K.MODEL, openai_client=client)
tools = [function_tool(t) for t in p.tools()]
bosla_sdk = Agent(name="Bosla", model=model, tools=tools,
                  instructions=port.SYSTEM_PROMPT + CONTEXT_FILE)
result = await Runner.run(bosla_sdk, task, max_turns=8)
```

#### [day3#own-loop-vs-sdk] Code size, trace, control: what you gain and what you give up

*Lab 3.2 · steps 3 and 4*

|  | Own loop | SDK |
| --- | --- | --- |
| Code you write | the loop and every hook | a few lines of configuration |
| Trace | events you defined, a stop reason returned | run items; a stop can be an exception |
| Step budget | a returned `max_steps` | `max_turns`, raises when reached |
| Write gate | a permission hook | a guardrail or approval setting to configure |

#### [day3#hosted-agents] Hosted agents: the provider runs the loop and the tools

*One step further*

- **What you get.** No loop to operate; built-in tools such as search or code execution in the provider's sandbox.
- **What you give up.** Where the data goes, which tools run, what is logged, and whether the same agent runs on another model.

> **For Marsa.** The booking list holds personal data classified Restricted (TC-05). Before any hosted option, ask where it would be processed and stored, against the Personal Data Protection Law.

#### [day3#checkpoint-2] A stop that raises

*Checkpoint*

**Question:** On the SDK, T04 ends with an exception when `max_turns` is reached. How should your evaluation count it?

- A. Let the exception stop the evaluation, so you notice
- B. Skip the task: it did not finish
- C. As a failed task, with the exception's name as the reason
- D. As passed if no write was made

#### [day3#lab-3-2] An agent SDK against your own loop

Lab 3.2 · 25 min

Rebuild Bosla on the OpenAI Agents SDK with a free OpenRouter model, run the same ten tasks, and compare code size, traces and control with the own loop.

[D3_2_agents_sdk.ipynb](https://sdaiaacademy.github.io/ae-302/labs/D3_2_agents_sdk.ipynb)

- [ ] Bosla on the SDK: model, tools, agent (7 min)
- [ ] The same ten tasks, graded the same way (6 min)
- [ ] Traces and control, side by side (7 min)
- [ ] The comparison table (5 min)
- [ ] ✱ Stretch: The write gate in the SDK

### Session 3: Loop engineering

#### [day3#s3] Loop engineering

*Session 3*

- Write a check of agent actions against the rules
- Keep the loop running while the check fails, within a budget
- Compare outcomes with and without verification

#### [day3#stop-is-not-done] "Done" is the model's opinion; a check is evidence

*Loop engineering*

**Faisal:** Book Najm Coral at B03 arriving 2026-11-15 for 2 days. I confirm.

**Bosla (weak example):** Booked BK-24031 at B03.

**0.8 m** under the keel at B03; TC-03 asks for 1.0 m

- **The service said yes.** It checks length and overlaps, not depth. The circular asks the assistant to check.

#### [day3#check-in-code] Check every booking the run touched, in code

*Lab 3.3 · step 2*

- Kind of vessel against kind of berth
- Length plus 20 m against the berth's length
- Depth minus draft against 1.0 m
- No overlap with another booking

- problem: `BK-24031: under-keel clearance at B03 is 0.8 m, below 1.0 m (TC-03). Amend to a berth from find_windows, or cancel.`

#### [day3#loop-may-not-stop] The loop may not stop while the check fails

*Lab 3.3 · step 3*

- call: `create_booking(V-108, B03, 2026-11-15, 2 days)` → BK-24031
- stop?: "Booked BK-24031 at B03."
- guard: Verification failed: under-keel clearance at B03 is 0.8 m ...
- call: `find_windows(V-108, 2 days, from 2026-11-15)`
- call: `amend_booking(BK-24031, berth B01)`
- final: "B03 leaves 0.8 m under the keel (TC-03), so I moved BK-24031 to B01."

#### [day3#pre-existing-problem] BK-24022 breaks the same rule, and Bosla did not make it

*Found by the same check*

- Najm Coral was already booked at B03 from 2026-11-03.
- Bosla's run did not create it, so the loop does not touch it.
- Someone must hear about it: the duty harbour master, not the shipping agent's chat.

> **Scope of a fix.** An agent that repairs everything it notices changes records nobody asked it to change. Report, do not fix.

#### [day3#checkpoint-3] Prompt or check?

*Checkpoint*

**Question:** Bosla booked a vessel with too little water under the keel. What is the most reliable fix?

- A. Add "always check under-keel clearance" to the prompt
- B. Ask the shipping agent to check before confirming
- C. Remove B03 from the tools
- D. A check in code after each booking, and a loop that may not stop while it fails

#### [day3#lab-3-3] Verification inside the loop

Lab 3.3 · 25 min

Add a check of each booking against the schedule and the berth rules, and keep the loop going until the check passes or the budget ends.

[D3_3_loop_engineering.ipynb](https://sdaiaacademy.github.io/ae-302/labs/D3_3_loop_engineering.ipynb)

- [ ] The planted problem, by hand (4 min)
- [ ] Write the check (8 min)
- [ ] The loop may not stop while the check fails (7 min)
- [ ] With and without verification (6 min)
- [ ] ✱ Stretch: Verification by a second model call

### Session 4: Evaluating agents

#### [day3#s4] Evaluating agents

*Session 4*

- Grade agent runs with code and model graders
- Compute success in any and in every trial
- Compute cost per completed task

#### [day3#why-repeated-trials] One run is an anecdote; five trials are a measurement

*Evaluating agents*

- The model samples, so the same task can pass and then fail.
- Twenty tasks, five trials each, a hundred runs.
- Fresh samples only: switch the response cache off, or five trials are one answer replayed.

- **Two questions.** **Can** the agent do the task? It passed at least once. **Can we rely** on it? It passed every time.

#### [day3#code-and-model-graders] Code where you can, a model where you must, and check the model

*Two kinds of grader*

- **Code grader.** Strings in the answer, the database after the run, no write when none was asked. Exact, cheap, repeatable.
- **Model grader.** A rubric: "refuses without saying whose booking it is, cites TC-05". A verdict and a reason.

> **A grader is a model too.** Label five answers yourself and compare. Disagreement is a finding about the grader or the rubric.

#### [day3#pass-any-every] Any trial and every trial tell different stories

*Lab 3.4 on the shipped recordings*

- **1.00** pass@5: tasks passed in at least one trial
- **0.60** pass^5: tasks passed in all five trials
- **0.90** success per trial

Every task can be done; eight of twenty cannot be relied on. The shipped recordings are synthetic: your own trials replace them.

#### [day3#cost-per-completed-task] Divide the cost of every run by the runs that succeeded

*Cost per completed task*

```python
# file: Lab 3.4
PRICE_IN, PRICE_OUT = 0.20, 0.80  # assumption
total = (in_tokens * PRICE_IN
         + out_tokens * PRICE_OUT) / 1e6
cost_per_completed = total / passed_runs
```

- Failed runs cost money too; the task still has to be done.
- Free models cost nothing: price the tokens as if on the model you would deploy.
- A cheaper design that fails more can cost more per completed task.

#### [day3#checkpoint-4] Four of five

*Checkpoint*

**Question:** T04 ("do not book yet") passed in four of five trials. In the fifth, Bosla booked anyway. What do you report?

- A. It passes: pass@5 is true
- B. It is in pass@5 but not in pass^5, and the failure is an unwanted write: fix before release
- C. 80% is good enough for a free model
- D. Remove T04: it is flaky

#### [day3#lab-3-4] Grading over five trials

Lab 3.4 · 25 min

Grade recorded runs of 20 tasks over five trials with code and model graders, compute success in any and every trial, and the cost per completed task.

[D3_4_evals.ipynb](https://sdaiaacademy.github.io/ae-302/labs/D3_4_evals.ipynb)

- [ ] A code grader for recorded runs (6 min)
- [ ] A model grader for the rubric tasks (6 min)
- [ ] Success in any and in every trial (7 min)
- [ ] Cost per completed task (6 min)
- [ ] ✱ Stretch: Record your own five trials of three tasks

#### [day3#day-3-recap] The harness, tested part by part and run by run

*Day 3 recap*

- A **harness** is tools, context, state and feedback; remove a part to learn what it protects.
- An **SDK** trades code for configuration; compare on the same tasks.

- **Verification** in the loop: stopping is not succeeding.
- **Evaluation** over trials: any and every, and cost per completed task.

#### [day3#tomorrow-graph] Graph and production: approvals, several agents, containment, an API

*Tomorrow · Day 4*

Rebuild the booking flow as a checkpointed graph that pauses for the harbour master, split work between two agents, plant an instruction in a circular and contain it, and ship Bosla behind an API with a smoke evaluation in CI.
