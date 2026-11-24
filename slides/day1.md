---
course: "Agentic Systems Engineering: Loops, Context and Harnesses"
code: "AE-302"
version: "2027.2.0"
deck: "day1"
day: 1
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-302/slides/day1.html"
---

# Agentic Systems Engineering: Loops, Context and Harnesses

## Day 1: From Model to Agent

#### [day1#title] From Model to Agent

*SDAIA Academy · Agentic Systems Engineering: Loops, Context and Harnesses*

Day 1

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-302

#### [day1#four-days-one-agent] Four days, one agent that grows every day, and a capstone

*The course at a glance*

- **Day 1 · Model to agent.** Three API shapes, structured outputs, typed tools, the loop from scratch.
- **Day 2 · Context.** Context as a budget, retrieval, memory and skills, the Model Context Protocol.
- **Day 3 · Harness and loop.** Harness parts, an SDK against your own loop, verification, evaluation over trials.
- **Day 4 · Graph and production.** Checkpoints and approvals, several agents, containment, an API in CI.

> **Day 5 · Capstone.** A research agent over synthetic port documents, in a public repository, defended live for eight minutes.

#### [day1#build-by-hand-first] Build it by hand first, then compare with the frameworks

*How this course works*

- **First principles.** You write the calls, the tools and the loop. Every SDK this week is the same loop written by someone else.
- **Measure, do not guess.** Every change is judged on traces and repeated trials, not on one good run.
- **Free hosted models.** Open-weight models served for free over an API. Nothing runs a model on your laptop.

> **AI policy.** AI off for the entry check and for writing the first loop (Lab 1.4). In the other labs an assistant may hint but not write harness code. In the capstone, anything goes, with transcripts kept.

#### [day1#marsa-ports-authority] Marsa Ports Authority and its booking assistant, Bosla

*One case study all week*

A fictional Red Sea port with eight berths. Shipping agents book berth windows by the day. You build **Bosla** (بوصلة).

- **Berth schedule.** Eight berths by kind, length and depth; fourteen vessels; who is alongside on which days.
- **Tariff circulars.** Eight bilingual circulars, TC-01 to TC-08. One supersedes another.
- **Booking service.** Read, create, amend, cancel. Three of these write, and fees follow.

#### [day1#key-and-setup-check] Get a free key and run the setup check

*Lab environment*

1. Create a free key at **openrouter.ai/keys**. Put it in `labs/.env`, or in Colab's Secrets as `OPENROUTER_API_KEY`.
2. Run `00_setup_check.ipynb`.
3. Each lab starts from a **supplied reference state**: a fresh copy of the port database and the files it needs. No lab depends on an earlier one.

```bash
# file: terminal (local option)
git clone https://github.com/SDAIAAcademy/ae-302
cd agentic-ai/labs
cp .env.example .env    # paste your key
uv sync
uv run python port_data.py
uv run jupyter lab
```

#### [day1#agenda] From Model to Agent

*Today*

- **Session 1 · Three API shapes**: What a language model is, and one model called through Chat Completions, Responses and Messages
- **Session 2 · Structured outputs**: Turn free text into a typed object, and recover when the reply does not validate
- **Session 3 · Tools**: Typed tool schemas, and errors that tell the model what to send instead
- **Session 4 · The agent loop from scratch**: A model calling tools in a loop, with a step budget, a stop rule and a trace

### Session 1: Three API shapes

#### [day1#s1] Three API shapes

*Session 1*

- Explain what a language model predicts and why its output varies
- Call one open-weight model through three API shapes
- Read stop reasons and token usage in each shape

#### [day1#next-token-probabilities] Text in, a probability for every possible next token

*The one thing a language model computes*

Prompt for Input:

```text
Berth hire at Marsa is charged per
```

| Item | Value |
| --- | --- |
| " day" | 0.58 |
| " gross" | 0.21 |
| " hour" | 0.11 |

Illustrative numbers.

- **A function.** `model(tokens) → next-token probabilities`. No database, no memory.
- **Everything builds on it.** Answers, JSON, tool calls: all text, one token at a time.

#### [day1#generation-is-a-loop] Generation is a loop: predict, pick, append, repeat

*How a reply gets written*

1. **1 · Predict** next-token probabilities
2. **2 · Pick** one token
3. **3 · Append** it to the input
4. **4 · Stop** on a stop token or a length limit

- **Sampling.** The pick is random within limits: the same task can end differently. Day 3 grades over five trials.
- **Output costs more.** Input is read in one pass; each output token is another pass.
- **Length limits cut.** Hit the cap and the reply stops mid-sentence, or mid-tool-call.

#### [day1#model-remembers-nothing] The model remembers nothing between calls

*The answer to "how does it remember?"*

- call 1: system · **user**: "My booking is BK-24017."
- reply: "Thanks. What would you like to know?"
- call 2: system · user · assistant · **user**: "Which berth?"

- **Stateless.** Each call is independent: your code **resends the history**.
- **Context window.** The most tokens one call can hold, input plus output. All the model knows about the task must fit.
- **History costs money.** Every call pays for the whole conversation again. Day 2 budgets it.

#### [day1#fluent-is-not-correct] Fluent is not the same as correct

*What a model cannot know*

**Faisal:** Is berth B02 free for Najm Falcon on 2026-11-05?

**Model alone (weak example):** Yes, B02 is available from 5 November. I have reserved it for you.

- **Invented.** B02 is taken until 2026-11-06, and nothing was reserved. The model has never seen the schedule.
- **Two remedies.** **Put the facts in the context** (Day 2), or **let it fetch them** with tools (Session 3).

#### [day1#model-call-is-a-request] A model call is one HTTPS request

*Calling a model from code*

```python
# file: python
from openai import OpenAI

client = OpenAI(base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"])
resp = client.chat.completions.create(
    model=K.MODEL,          # a free open-weight model
    messages=[{"role": "user", "content": question}])
```

- **One client, many servers.** Change `base_url` and the same code talks to a gateway, a cloud host or your own server.
- **Free means shared.** Free models are rate-limited. A busy one answers HTTP 429: retry, then fall back to the next model.

#### [day1#three-api-shapes] Three API shapes carry almost every model call

*Why there is more than one API*

|  | Chat Completions | Responses | Messages |
| --- | --- | --- | --- |
| **From** | OpenAI | OpenAI | Anthropic |
| **Unit** | messages with roles | typed **items** | messages of typed **content blocks** |
| **System prompt** | a `system` message | `instructions` | `system` field |
| **Stop signal** | `finish_reason` | `status`, items | `stop_reason` |

The envelopes differ; the idea does not: a list of turns in, a reply out. OpenRouter serves all three for the same free model, so Lab 1.1 can compare them like for like.

#### [day1#items-and-blocks] Where the text is, and why the model stopped

*The same question, three replies*

```python
# file: Chat Completions
r.choices[0].message.content
r.choices[0].finish_reason
# stop | length | tool_calls
r.usage.prompt_tokens
```

```python
# file: Responses
r.output_text
[i.type for i in r.output]
# message | reasoning | function_call
r.usage.input_tokens
```

```python
# file: Messages
[b.type for b in m.content]
# text | thinking | tool_use
m.stop_reason
# end_turn | max_tokens | tool_use
m.usage.input_tokens
```

> **Check the stop signal first.** A reply cut by the length limit looks like a normal one until you do.

#### [day1#arabic-token-tax] The same three rules cost more tokens in Arabic

*Measured on circular TC-03*

- **142** tokens, English half of TC-03
- **183** tokens, Arabic half of TC-03
- **1.29** Arabic to English ratio

Counted with the open tokenizer in `agentkit.count_tokens`. Prices, limits and context windows are all counted in tokens, so a bilingual agent budgets for the larger half.

#### [day1#checkpoint-1] Where does the conversation live?

*Checkpoint*

**Question:** Faisal names his booking in one call and asks "which berth?" in the next. Where was the booking ID kept?

- A. In the model's weights, updated after the first call
- B. In the history your code resent with the second call
- C. In a session the model server keeps for each key
- D. Nowhere: the model guessed it from the question

#### [day1#lab-1-1] One model, three API shapes

Lab 1.1 · 25 min

Send one berth-hire question to one free open-weight model through Chat Completions, Responses and Messages, compare what each returns, and measure the Arabic token tax on a circular.

[D1_1_three_shapes.ipynb](https://sdaiaacademy.github.io/ae-302/labs/D1_1_three_shapes.ipynb)

- [ ] Chat Completions: one call, read every field (6 min)
- [ ] Responses: the same question as items (5 min)
- [ ] Messages: the same question as content blocks (5 min)
- [ ] One table: text, stop reason, tokens per shape (5 min)
- [ ] The Arabic token tax on one circular (4 min)
- [ ] ✱ Stretch: Cut the answer short and read each shape's stop reason

### Session 2: Structured outputs

#### [day1#s2] Structured outputs

*Session 2*

- Define a schema whose constraints catch wrong values
- Request output under a JSON Schema response format
- Recover from malformed replies with validation and repair

#### [day1#code-needs-data] The booking service needs data, not prose

*The problem*

**Faisal's email:** Najm Lines (NJM-4417) requests a berth for Najm Falcon, arriving 7 November 2026, for two days. Containers only.

**Free text (weak example):** This seems to be a request for about two days, probably early November…

**Structured (good example):** `{"vessel_name": "Najm Falcon", "arrival": "2026-11-07", "days": 2, "kind": "container", "dangerous_goods": false, "agent_code": "NJM-4417"}`

- **Prose breaks programs.** You cannot pass "probably early November" to `create_booking`. A regular expression fails on the next phrasing, and the next language.

#### [day1#schema-from-pydantic] A schema is a contract the model cannot break silently

*Describing the shape of the data*

```python
# file: Lab 1.2
class BerthRequest(BaseModel):
    vessel_name: str
    arrival: date
    days: int = Field(ge=1, le=14)
    kind: Literal["container", "general",
                  "dry_bulk", "ro_ro", "tanker"]
    dangerous_goods: bool
    agent_code: str = Field(
        pattern=r"^[A-Z]{3}-\d{4}$")
```

- **Types and enums.** A date is a date; a kind is one of five.
- **Constraints.** Days from 1 to 14 is circular TC-08 written as code.
- **One source.** Pydantic writes the JSON Schema from this class and validates replies against it.

#### [day1#ask-then-validate] Ask for the schema; validate anyway

*Structured outputs*

```python
# file: Chat Completions
schema = BerthRequest.model_json_schema()
fmt = {"type": "json_schema",
       "json_schema": {"name": "BerthRequest",
                       "schema": schema}}
r = K.chat(messages, response_format=fmt)
req = BerthRequest.model_validate_json(text)
```

- **Constrained generation.** Where the server enforces the schema, only tokens that keep the JSON valid can be picked.
- **Not every server enforces it.** Some free models treat it as a hint. So the schema also goes in the prompt, and every reply is validated.

#### [day1#three-malformed-replies] Three malformed replies, three different failures

*What comes back in practice*

| Reply | What is wrong | Fix |
| --- | --- | --- |
| (a) JSON inside prose and a code fence | the JSON is fine, the wrapping is not | cut from the first `{` to the last `}`: no model call |
| (b) `"arrival": "7 November 2026", "days": "two"` | a date and a number in words | one repair round trip |
| (c) no `agent_code` | a required field is missing | one repair round trip, or ask the agent |

#### [day1#repair-loop] The validation error is the whole repair prompt

*Recovery*

```python
# file: parse_or_repair (core)
for attempt in range(repairs + 1):
    try:
        return BerthRequest.model_validate_json(
            cut(reply)), attempt
    except ValidationError as e:
        if attempt == repairs:
            raise
        messages += [
          {"role": "assistant", "content": reply},
          {"role": "user", "content":
           f"That JSON is invalid: {e}\n"
           "Reply with the corrected JSON only."}]
        reply = K.chat(messages).choices[0]...
```

- error: `days: Input should be a valid integer, unable to parse string as an integer`
- repair: `"days": 2`

#### [day1#field-accuracy] Validation proves the shape; a gold set proves the values

*Valid is not the same as right*

- A valid object can still carry the wrong date or the wrong kind.
- Six requests with correct answers: count right fields out of 36.
- Look at **which field** fails most, not only the total.

- **The Arabic tanker.** Request R2 says الناقلة and وقود. Both `kind` and `dangerous_goods` depend on reading them right.

#### [day1#checkpoint-2] Is a response format enough?

*Checkpoint*

**Question:** Your extractor sends a JSON Schema response format, and the server accepts it. What else must your code do?

- A. Nothing: the reply is guaranteed to match the schema
- B. Retry the same request until a reply parses
- C. Repair until valid, with no limit on attempts
- D. Validate every reply, repair a bounded number of times with the error, then fail loudly

#### [day1#lab-1-2] A berth request as a validated object

Lab 1.2 · 25 min

Extract shipping agents' berth requests, in English and Arabic, into a validated schema; recover from three malformed replies; measure field accuracy on six requests.

[D1_2_structured_outputs.ipynb](https://sdaiaacademy.github.io/ae-302/labs/D1_2_structured_outputs.ipynb)

- [ ] The schema: BerthRequest (5 min)
- [ ] Ask for it with a JSON Schema response format (5 min)
- [ ] Recover from three malformed replies (8 min)
- [ ] Six requests, field accuracy (7 min)
- [ ] ✱ Stretch: A request with missing fields: say so, do not invent

### Session 3: Tools

#### [day1#s3] Tools

*Session 3*

- Describe a tool call as a request the application executes
- Write typed argument schemas for schedule and booking tools
- Return errors a model can act on

#### [day1#model-asks-code-runs] A tool call: the model asks, your code runs

*Back to "fluent is not correct"*

1. **1 · Send** the question and tool descriptions
2. **2 · Model** "call `find_windows` with these arguments"
3. **3 · Your code** runs it
4. **4 · Send** the result back
5. **5 · Model** answers from real data

- **The model never executes.** It writes a name and JSON arguments. Running them is your decision.
- **Arguments are text.** Written by a model: parse and validate before you act.

#### [day1#bosla-three-services] Bosla's tools: three services, eleven functions

*The case study in code*

| Schedule | Tariff | Booking |
| --- | --- | --- |
| `list_berths` | `search_circulars` | `get_booking` |
| `get_vessel` | `get_circular` | `create_booking` writes |
| `berth_schedule` | `compute_dues` | `amend_booking` writes |
| `find_windows` |  | `cancel_booking` writes |

> **Rules live in the tools.** Ownership of a booking, overlaps and lead times are checked in code; a violation raises `ToolError` with what to do next.

#### [day1#schema-from-function] The model sees a name, a description and a JSON Schema

*What the model sees*

```python
# file: labs/port.py (excerpt)
def create_booking(self, vessel_id: str,
        berth_id: str, arrival: str, days: int,
        agent_code: str,
        dangerous_goods: bool = False) -> dict:
    """Create a berth booking. Writes to the
    schedule: confirm with the agent first.

    Args:
        berth_id: B01 to B08.
        arrival: arrival date, YYYY-MM-DD.
        ..."""
```

`K.tool_schema(fn)` turns hints into JSON Schema and the docstring into descriptions.

- **Loose types.** `berth_id` is any string, `arrival` any text, `days` any integer. The service will refuse many of them.

#### [day1#typed-arguments] Typed arguments turn guesses into enums and ranges

*Tightening the contract*

```python
# file: Lab 1.3
class BookingArgs(BaseModel):
    vessel_id: str = Field(pattern=r"^V-\d{3}$")
    berth_id: Literal["B01", "B02", ..., "B08"]
    arrival: date
    days: int = Field(ge=1, le=14)
    agent_code: str = Field(
        pattern=r"^[A-Z]{3}-\d{4}$")
    dangerous_goods: bool = False
```

- **Enums for closed sets**: the model reads the eight berths in the schema itself.
- **Formats and ranges**: dates as dates, days 1 to 14.
- **An example in each description**: `"V-110"`, `"NJM-4417"`.

#### [day1#overlapping-tool-descriptions] Two descriptions that say the same thing send calls to the wrong tool

*A second Marsa desk · pilotage*

Prompt for find_pilot_slots:

```text
Find pilot availability for a vessel.
```

Prompt for pilot_roster:

```text
Show the pilots and when they are available.
```

| Request needs | First call: slots | First call: roster |
| --- | --- | --- |
| `find_pilot_slots` (20) | 14 | 6 |
| `pilot_roster` (20) | 8 | 12 |

> **Read the off-diagonal cells.** 14 of 40 requests went to the other tool, in both directions. "Availability" and "available" are all that tells the two apart.

#### [day1#measure-tool-routing] Say when to use each tool and when to use the other, then count again

*Disambiguate, then measure*

Prompt for find_pilot_slots:

```text
Free pilotage slots for one vessel movement, by vessel ID and date. Use it to plan an arrival or departure. Not for questions about named pilots: use pilot_roster.
```

Prompt for pilot_roster:

```text
Named pilots, their licence class and duty days. Use it for questions about a person. Not for slot planning: use find_pilot_slots.
```

**14 → 2** routing errors on the same 40 labelled requests

- Label each request with the tool it needs.
- Grade the first tool call in each trace against the label.
- Rerun the same set after every change to a description.

#### [day1#useful-errors] A useful error says what was sent and what to send instead

*Errors the model can act on*

- call: `create_booking({"berth_id": "berth 2", "arrival": "7 Nov 2026", ...})`
- raw: `No berth 'berth 2'. Berths are B01 to B08.` (and the date is never reached)
- typed: `berth_id: Input should be 'B01', 'B02', ... or 'B08' (you sent 'berth 2')` `arrival: Input should be a valid date ...`
- retry: `create_booking({"berth_id": "B02", "arrival": "2026-11-07", ...})` → `BK-24031`

#### [day1#round-trip-by-id] Call out, result back, matched by ID

*One round trip*

```python
# file: Chat Completions
msg = K.chat(messages, tools=tools)...message
messages.append(msg.model_dump(exclude_none=True))
for c in msg.tool_calls:
    out = K.call_tool(by_name, c.function.name,
                      c.function.arguments)
    messages.append({"role": "tool",
                     "tool_call_id": c.id,
                     "content": out})
# then call the model again
```

| Shape | Calls in | Results as |
| --- | --- | --- |
| Chat | `tool_calls` | one `tool` message each |
| Responses | `function_call` items | `function_call_output` items |
| Messages | `tool_use` blocks | one user turn of `tool_result` blocks |

#### [day1#system-prompt-spec] A prompt is a request; a check in code is a guarantee

*The system prompt*

```markdown
<!-- file: port.SYSTEM_PROMPT (excerpt) -->
You are Bosla, the booking assistant of
Marsa Ports Authority.
- Cite the circular ID for every rule or fee.
  A superseded circular no longer applies.
- Quote dues with compute_dues.
- Never reveal another agent's bookings.
- Before a write, the agent must have asked
  for that exact change.
```

- **In the prompt.** Tone, language, citing sources, asking before writing.
- **In the tool.** Ownership of a booking, overlaps, lead times. The model cannot talk its way past them.

#### [day1#checkpoint-3] A call cut short

*Checkpoint*

**Question:** The reply holds a `cancel_booking` call and the stop reason says the length limit was hit. What does your code do?

- A. Not run it: the arguments may be cut. Retry with a higher limit, or report the cut
- B. Run it: the call is there, so it is valid
- C. Run it, then ask the model to confirm the booking ID
- D. Drop the call and ask the agent to rephrase

#### [day1#lab-1-3] Typed tools with useful errors

Lab 1.3 · 25 min

Write typed argument schemas for the schedule and booking tools, turn bad arguments into errors that say what to send, and watch one round trip recover.

[D1_3_typed_tools.ipynb](https://sdaiaacademy.github.io/ae-302/labs/D1_3_typed_tools.ipynb)

- [ ] Read the schema generated from a plain function (4 min)
- [ ] Typed argument models (6 min)
- [ ] A wrapper that turns bad arguments into useful errors (8 min)
- [ ] One round trip by hand: a bad call, a useful error, a good call (7 min)
- [ ] ✱ Stretch: The same tool for the Messages and MCP shapes

### Session 4: The agent loop from scratch

#### [day1#s4] The agent loop from scratch

*Session 4*

- Write an agent loop without a framework or AI assistance
- Bound it with a step budget and explicit stop rules
- Grade it on ten tasks from their traces

#### [day1#which-is-an-agent] Which of these is an agent?

*Before we start · poll*

- **A.** A chatbot that answers tariff questions from a long system prompt
- **B.** A program: extract the request, find a window, create the booking
- **C.** A model that picks tools, reads results and decides when it is done
- **D.** A booking process where C runs in one step and the harbour master signs the next

#### [day1#agent-tools-in-loop] An agent is a model using tools in a loop

*Definitions*

Prompt for Anthropic, Building effective agents:

```text
Workflows: models and tools orchestrated through predefined code paths. Agents: models dynamically direct their own processes and tool usage.
```

- **Who picks the next step?** Your code: a workflow. The model: an agent.
- **Who says it is done?** The model proposes; your stop rules decide.
- **Start simple.** One call if it works, a workflow if the path is known, an agent only when it is not.

#### [day1#loop-on-one-slide] The loop fits on one slide

*The core of every agent*

```python
# file: Lab 1.4 (core)
for step in range(1, max_steps + 1):
    msg = K.chat(messages, tools=tools)...message
    messages.append(msg.model_dump(exclude_none=True))
    if not msg.tool_calls:
        return done(msg.content)        # model: done
    this = [(c.function.name, c.function.arguments)
            for c in msg.tool_calls]
    if this == last:
        return stop("repeat")           # no progress
    last = this
    for c in msg.tool_calls:
        out = K.call_tool(by_name, ...)
        messages.append({"role": "tool", ...})
return stop("max_steps")                # budget spent
```

- **Three exits.** The model stops calling tools; the same calls repeat; the step budget runs out.
- **The history is the memory.** Every step resends everything, so input grows each step.
- **Tools never raise into the loop.** Errors come back as results.

#### [day1#completion-criteria] Decide in advance what "done" means, and what "stuck" means

*Explicit completion criteria*

| Exit | Decided by | Returned as |
| --- | --- | --- |
| No tool calls in the reply | the model | `stopped: "done"` and the answer |
| The same calls as the last turn | the loop | `stopped: "repeat"`, no answer |
| Step budget spent | the loop | `stopped: "max_steps"`, no answer |
| Cost budget spent | the loop (Day 3) | `stopped: "max_cost"` |

> **A stop is not a success.** "done" means the model stopped; whether the task was done is the grader's call.

#### [day1#trace-of-a-booking] A trace: the evidence of what the agent did

*What a run leaves behind*

- user: "Agent code NJM-4417. Please book Najm Falcon (V-110) for 2 days at the earliest free window arriving between 2026-11-05 and 2026-11-12. I confirm."
- call: `find_windows({"vessel_id": "V-110", "days": 2, "date_from": "2026-11-05", "date_to": "2026-11-12"})`
- result: `[{"berth_id": "B02", "arrival": "2026-11-07", "under_keel_m": 2.1}]`
- call: `create_booking({"vessel_id": "V-110", "berth_id": "B02", "arrival": "2026-11-07", ...})`
- result: `{"booking_id": "BK-24031", ..., "berth_hire_sar": 7800}`

#### [day1#ten-tasks] Ten tasks across the three services, graded by code

*Lab 1.4 · step 3*

| Task | Checked by |
| --- | --- |
| T01 to T04 · berths, dues, a booking, a window | strings in the answer |
| T05 to T07 · book, amend, cancel | the database after the run |
| T08 · an Arabic tariff question | 500 in the answer |
| T09 · Najm's code on Sahil's booking | the booking is still confirmed |
| T10 · customs clearance | no write, at most two tool calls |

**7 / 10** the outcome's bar, with a trace per run

- **A fresh port per task.** One task's booking must not change the next task's world.

#### [day1#tool-that-never-finishes] A tool that never finishes, and the rule that stops it

*Why stop rules exist*

- step 1: `vessel_position({"vessel_id": "V-110"})`
- result: `"Position not yet received. Call vessel_position again."`
- step 2: `vessel_position({"vessel_id": "V-110"})`
- stop: `repeat`: same calls as the previous turn

- **The loop's fix.** The repeat rule and the step budget bound the run.
- **The tool's fix.** A result that says what to do: "positions arrive about every 6 hours; tell the agent to ask later".

#### [day1#harness-around-loop] A harness is the loop plus everything around it

*The map for the week*

| Around the loop | What it does | Day |
| --- | --- | --- |
| Context management | keeps the input within budget: compaction, offloading, retrieval, skills | 2 |
| Permissions, hooks, verification | allow, ask or deny per tool; checks before the loop may stop | 3 |
| Evaluation and tracing | repeated trials, graders, spans | 3, 4 |
| Graphs, approvals, containment | checkpoints, a human at a risk threshold, one leg removed | 4 |

#### [day1#checkpoint-4] A tool refuses

*Checkpoint*

**Question:** `cancel_booking` raises because the agent code does not own the booking. What should the loop do?

- A. Raise, so the developer sees the bug
- B. Retry the same call until it succeeds
- C. Return the error to the model as the tool result, so it can tell the agent to check the code
- D. Tell the agent the booking belongs to someone else

#### [day1#lab-1-4] The agent loop from scratch

Lab 1.4 · 25 min

Write the loop without AI assistance, with a step budget and stop rules, save a trace per run, and run it on ten port tasks graded by code.

[D1_4_agent_loop.ipynb](https://sdaiaacademy.github.io/ae-302/labs/D1_4_agent_loop.ipynb)

- [ ] Write my_loop() with a step budget and a stop rule (8 min)
- [ ] A trace per run (5 min)
- [ ] Ten tasks, graded by code (8 min)
- [ ] Break it: a tool that never finishes (4 min)
- [ ] ✱ Stretch: Run one turn's tool calls in parallel

#### [day1#day-1-recap] From a next-token predictor to a loop with stop rules

*Day 1 recap*

- A model is **stateless**; your code keeps the history.
- **Three API shapes**, one idea; read the stop signal first.
- **Structured outputs**: ask for the schema, validate always, repair a bounded number of times.

- **Typed tools** with errors that say what to send instead.
- The **loop**: a step budget, explicit exits, a trace per run.
- Stopping is not succeeding: **grade by code**.

#### [day1#tomorrow-context] Context engineering: what the model sees, and what it costs

*Tomorrow · Day 2*

Long tasks overflow the window. Tomorrow you measure tokens per turn, cut them with compaction and offloading, search the circulars, load a tariff skill on demand, and serve the circulars over the Model Context Protocol.
