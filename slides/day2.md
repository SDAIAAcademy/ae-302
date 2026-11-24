---
course: "Agentic Systems Engineering: Loops, Context and Harnesses"
code: "AE-302"
version: "2027.2.0"
deck: "day2"
day: 2
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-302/slides/day2.html"
---

# Agentic Systems Engineering: Loops, Context and Harnesses

## Day 2: Context Engineering

#### [day2#title] Context Engineering

*SDAIA Academy · Agentic Systems Engineering: Loops, Context and Harnesses*

Day 2

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-302

#### [day2#agenda] Context Engineering

*Today*

- **Session 1 · Context as a budget**: Every call resends the history: measure it, then cut it with offloading and compaction
- **Session 2 · Retrieval for agents**: Keyword and vector search over bilingual circulars, offered to the agent as tools
- **Session 3 · Memory, skills and context files**: What every session needs, what only some tasks need, and loading it in stages
- **Session 4 · Model Context Protocol**: A server over the circular store, discovered by the agent at run time

### Session 1: Context as a budget

#### [day2#s1] Context as a budget

*Session 1*

- Measure tokens per turn on a long agent task
- Offload large tool results to files the agent can page through
- Compact old turns into notes without losing what the answer needs

#### [day2#what-fills-the-window] Everything the model sees, on every call, is a budget

*Context engineering*

| Part of each request | Grows? |
| --- | --- |
| System prompt and context file | no |
| Tool definitions (Bosla's eleven: 1,755 tokens) | no |
| The task | no |
| Assistant turns and tool calls | every step |
| Tool results | every step, fastest |

- **Cost.** Each step pays for all earlier steps again.
- **Quality.** A long context buries the facts that matter among the ones that do not.

#### [day2#tokens-per-turn] A nineteen-call task crosses a 4,000-token budget at turn 9

*Measured on the reference long task*

- **2,030** tokens in the first request
- **6,691** tokens in the last request
- **9** first turn over the 4,000-token budget

The task: every Najm booking in November with berth and dues, free berths from 2026-11-15, and the circulars that apply. Most of the growth is tool results: schedules and whole circulars.

#### [day2#offload-to-files] Offload: keep big results in files, give the model a stub

*Cut 1*

```python
# file: Lab 2.1 · after_tool hook
def offload(name, args, result):
    if len(result) <= LIMIT:
        return None                 # keep it
    path = RESULTS / f"{name}_{n}.json"
    path.write_text(result)
    return json.dumps({
        "offloaded": path.name,
        "chars": len(result),
        "preview": result[:120]})
# plus a tool: read_result(file, start, length)
```

**5,414 → 4,150** history tokens, six results offloaded

- **Nothing is lost.** The full result is one tool call away.

#### [day2#compact-old-turns] Compaction: replace old turns with notes, keep recent ones

*Cut 2*

- keep: system prompt, the task
- notes: "Notes from earlier steps:" one line per old call: name, arguments, start of the result
- keep: the last six messages, never starting with a tool result

**5,414 → 3,027** history tokens after one compaction

- **A bug we hit.** The second compaction dropped the first one's notes. Carry them forward.

#### [day2#before-after-table] A cut that saves tokens and fails the task is not a saving

*The evidence the outcome asks for*

| Configuration | Largest request | Input tokens, whole run | Cost | Success |
| --- | --- | --- | --- | --- |
| none | filled in by your live run in Lab 2.1 step 4 |  |  |  |
| offload |  |  |  |  |
| offload + compact |  |  |  |  |

> **Read the success column first.** Then the traces of any failure: which ID did the cut lose?

#### [day2#cache-aware-layout] Stable first, volatile last: the prefix is what providers reuse

*Cache-aware layout*

| Where the date goes | Shared prefix of two days' requests |
| --- | --- |
| Top of the system prompt | 12 of 195 tokens |
| Bottom of the system prompt | 193 of 195 tokens |

- Providers can reuse the work on an unchanged request prefix, often at a lower price.
- Order: system prompt, tool definitions, context file, then the conversation.
- Compaction rewrites the middle: do it rarely, not every turn.

#### [day2#checkpoint-1] Which cut loses information?

*Checkpoint*

**Question:** Bosla's history is over budget. You can offload big tool results to files, or compact old turns into notes. Which statement is right?

- A. Offloading loses information; compaction only moves it
- B. Compaction can lose information; offloading only moves it behind a tool
- C. Neither loses information if the model is good
- D. Both lose the same amount, since both save tokens

#### [day2#lab-2-1] Context as a budget

Lab 2.1 · 25 min

Measure tokens per turn on a long task, cut them by offloading tool results to files and by compaction, and build the before-and-after table of tokens, cost and success.

[D2_1_context_budget.ipynb](https://sdaiaacademy.github.io/ae-302/labs/D2_1_context_budget.ipynb)

- [ ] Tokens per turn on the long task (5 min)
- [ ] Offload big tool results to files (7 min)
- [ ] Compact old turns into notes (7 min)
- [ ] Before and after: tokens, cost and success, live (6 min)
- [ ] ✱ Stretch: A cache-aware layout: stable first, volatile last

### Session 2: Retrieval for agents

#### [day2#s2] Retrieval for agents

*Session 2*

- Score retrieval on the top hit, not only the top three
- Build keyword search with Arabic normalisation and a vector search
- Read from a trace which search tool the agent chose

#### [day2#retrieval-is-a-tool] For an agent, search is a tool it decides to call

*Retrieval for agents*

- **Classic retrieval.** Search once, paste the passages into the prompt, answer.
- **Agentic retrieval.** The agent chooses the query, the tool, whether to read a whole document, and when it has enough.

- **So the tool's contract matters.** What it is good at, in its description. What it returns: IDs to cite, the status of each circular, short passages.

#### [day2#top-hit-matters] Score the top hit: that is the passage the agent quotes

*Measure first*

- Twelve questions, eight English and four Arabic, each with its correct circular.
- On eight circulars, the baseline finds the right one in the top three every time.
- In first place: 7 of 12.

- question: "How much is berth hire per gross ton now?"
- top hit: `TC-02`, status: superseded by TC-07

#### [day2#bm25-arabic] BM25, Arabic normalisation, and a penalty for superseded

*Keyword search done properly*

```python
# file: Lab 2.2
def normalise(text):
    text = re.sub(r"[ً-ْـ]", "", text)
    text = re.sub("[أإآ]", "ا", text)
    text = text.replace("ة", "ه").replace("ى", "ي")
    return text.lower()
# BM25: rare words count more, repeats less
# superseded chunks: score x 0.5
```

- **Normalise.** One Arabic letter has several written forms. Unify them before matching.
- **Rank by status.** The protection against TC-02 lives in the ranking, where code enforces it.

#### [day2#vector-search] Vector search matches word parts and paraphrases

*Similarity search*

| Search | hit@1, twelve questions |
| --- | --- |
| Keyword baseline | 0.58 |
| BM25, normalised, status-aware | 0.92 |
| Vector, character n-grams | 1.00 |

> **No model download.** The vectors are TF-IDF weights of character 3- to 5-grams, computed on the laptop. Production systems use learned embeddings from a hosted API; the tool contract is the same.

#### [day2#answer-ignores-middle] Retrieval found the section; the answer still ignored it

*A second Marsa desk · the pilotage handbook*

- search: 20 sections returned; the right one, `PH-14`, ranked first
- prompt: 20 sections packed in handbook order: `PH-14` is passage 10 of 20
- answer: quotes a neighbouring section, not `PH-14`

- Retrieval is healthy: the right section is retrieved for 10 of 10 questions, first for 9.
- The fact was in the context on every failed run.
- Suspect where it sat, not whether it was found.

#### [day2#position-ablation] Keep the 20 sections, move only the right one, count correct answers

*Diagnose with a position ablation*

| Right section at | Correct, 10 questions × 5 trials |
| --- | --- |
| position 1 of 20 | 44 of 50 |
| position 5 of 20 | 41 of 50 |
| position 10 of 20 | 24 of 50 |
| position 15 of 20 | 30 of 50 |
| position 20 of 20 | 42 of 50 |
| best 5, best first | 46 of 50 |

- **The diagnosis.** Same content, same question: only the position changed, and accuracy fell in the middle. The cause is position.
- **The fix.** Keep the ranking when packing: best first, fewer passages. Then run the ablation again.

#### [day2#which-tool-it-picks] Give the agent both searches, then read which it picks

*Lab 2.2 · step 4*

Prompt for keyword_search_circulars:

```text
Best for exact terms, IDs and numbers. English or Arabic.
```

Prompt for vector_search_circulars:

```text
Best for paraphrases and questions in other words. English or Arabic.
```

- Record per run: tools called, in order, and whether the answer cites the right circular.
- Swap the order of the two tools and run again.
- If the picks follow the order, the descriptions are not doing their job.

#### [day2#checkpoint-2] Where should the superseded rule live?

*Checkpoint*

**Question:** Bosla sometimes quotes TC-02, which TC-07 replaced. Which fix is the most reliable?

- A. Add "never quote TC-02" to the system prompt and nothing else
- B. Delete TC-02 from the repository
- C. Return each circular's status with the result and rank superseded ones lower, then keep the prompt rule too
- D. Switch to a larger model that knows the tariff

#### [day2#lab-2-2] Keyword and vector search over circulars

Lab 2.2 · 25 min

Score retrieval on twelve bilingual questions, build BM25 with Arabic normalisation and a character n-gram vector search, give both to the agent as tools and trace which it picks.

[D2_2_retrieval.ipynb](https://sdaiaacademy.github.io/ae-302/labs/D2_2_retrieval.ipynb)

- [ ] The eval and the baseline (4 min)
- [ ] BM25 with Arabic normalisation (7 min)
- [ ] Vector search with character n-grams (6 min)
- [ ] Both as tools: which does the agent pick? (8 min)
- [ ] ✱ Stretch: When the corpus fits, skip retrieval

### Session 3: Memory, skills and context files

#### [day2#s3] Memory, skills and context files

*Session 3*

- Write a short context file for an agent
- Package a procedure as a skill with an index line
- Show staged loading of a skill in a trace

#### [day2#three-kinds-of-context] Context file, skills, memory: three stores, three lifetimes

*What goes where*

- **Context file.** Every session needs it: the port, how to work, what never to do. Short. Always loaded.
- **Skill.** Some tasks need it: how to quote a tariff, how to change a booking. A one-line index entry; the body on demand.
- **Memory.** Learned in one session, needed in another: "Faisal prefers Arabic". Written by the agent, capped.

#### [day2#bosla-context-file] A context file is short on purpose

*data/bosla/AGENTS.md*

```markdown
<!-- file: AGENTS.md (excerpt) -->
## How to work
- Look up before you answer.
- For any price, load the skill tariff-quote.
- For any amendment or cancellation,
  load the skill booking-change.
- TC-02 is superseded by TC-07.

## Never
- Reveal another agent's bookings (TC-05).
- Write without an explicit request.
```

- **Pointers, not procedures.** It says when to load a skill; the skill says how.
- **Paid on every call.** Every line is in every request, for the whole session.

#### [day2#skill-anatomy] Front matter for the index, a body for the procedure

*A skill is a folder*

```markdown
<!-- file: skills/tariff-quote/SKILL.md -->
---
name: tariff-quote
description: Quote berth hire for a vessel and
  a number of days, with the feeder discount
  and the dangerous goods surcharge, citing
  the circulars in force.
---
1. Find the gross tonnage with get_vessel.
2. Dangerous goods? Ask or read the request.
3. Call compute_dues. No arithmetic.
4. Cite TC-07 and TC-04.
5. Need the working? Read reference.md.
```

- **The description is a trigger.** It is all the model sees until it loads the skill. Write when to use it, not what it is.

#### [day2#staged-loading] Index always, body on demand, files only when asked

*Three stages*

1. **1 · Index** one line per skill, in the prompt
2. **2 · Body** `load_skill("tariff-quote")`
3. **3 · File** `read_skill_file(..., "reference.md")`

- **75** tokens for the index of two skills
- **508** tokens for every body and file in the prompt

#### [day2#skill-in-trace] The trace shows the skill loaded before the tariff was computed

*The evidence*

- user: "Agent code SHL-2290. Berth hire for Sahil Tide for 3 days? It carries fuel, dangerous goods."
- call: `load_skill({"name": "tariff-quote"})`
- call: `get_vessel({"vessel": "Sahil Tide"})` → 36,000 GT
- call: `compute_dues({"gross_tonnage": 36000, "days": 3, "dangerous_goods": true})`
- final: "SAR 12,960 (TC-07, TC-04)."

#### [day2#checkpoint-3] Where does the new rule go?

*Checkpoint*

**Question:** Reem issues a circular: amendments to bookings with dangerous goods now need a form. Only booking changes need this. Where does it go?

- A. In the booking-change skill, with a pointer in the circular store
- B. In the context file, so every session sees it
- C. In the agent's memory file
- D. In the description of every tool

#### [day2#lab-2-3] A context file and a tariff skill

Lab 2.3 · 25 min

Write the context file into Bosla's prompt, parse two skills into an index, load a skill and its reference file on demand, and show the staged loading in a trace.

[D2_3_context_skills.ipynb](https://sdaiaacademy.github.io/ae-302/labs/D2_3_context_skills.ipynb)

- [ ] The context file in the system prompt (5 min)
- [ ] Parse the skills and build the index (6 min)
- [ ] Staged loading: load_skill and read_skill_file (6 min)
- [ ] Show it in a trace (8 min)
- [ ] ✱ Stretch: A memory file per agent

### Session 4: Model Context Protocol

#### [day2#s4] Model Context Protocol

*Session 4*

- Build an MCP server with tools and resources
- Pass a provided test client in-process and over stdio
- Connect an agent through capability discovery, with a trace

#### [day2#why-a-protocol] A protocol lets any host discover tools it was not written with

*Model Context Protocol*

- **Without it.** Every host imports every tool: Bosla's code, an IDE's plugin and a desktop app each wrap the circulars their own way.
- **With it.** One server over the circulars. Each host connects, asks what is there, and calls it.

| A server offers | Example |
| --- | --- |
| tools | `search_circulars`, `get_circular` |
| resources | `circulars://index`, `circular://TC-07` |
| instructions | "A superseded circular no longer applies." |

#### [day2#server-in-code] A server is decorated functions

*Lab 2.4 · step 2*

```python
# file: Lab 2.4 (excerpt)
server = MCPServer("marsa-circulars", instructions="...")

@server.tool()
def get_circular(circular_id: str) -> dict:
    """Read one whole circular by ID (TC-01 to TC-08)."""
    try:
        return p.get_circular(circular_id)
    except port.ToolError as e:
        raise ToolError(str(e)) from e     # the model reads it

@server.resource("circular://{circular_id}")
def circular(circular_id: str) -> str: ...
```

#### [day2#provided-test-client] The provided test client speaks only the protocol

*The outcome's evidence*

- Discovers both tools, each with a description and a typed schema
- `TC-07` returns the rate in force; `TC-99` is an error result
- An Arabic query finds TC-06; results carry each circular's status
- The index resource lists eight circulars; a circular reads by ID

**8 / 8** checks passed by the reference server, in-process and over stdio

#### [day2#discovery-trace] Bosla learns the tools at run time: discovery, then calls

*Lab 2.4 · step 4*

- discover: `search_circulars(k, query)`
- discover: `get_circular(circular_id)`
- call: `search_circulars({"query": "cancellation fee", "k": 3})`
- result: `{"circular_id": "TC-06", "status": "in force", ...}`
- final: "25% of berth hire when less than 3 days before arrival (TC-06)."

#### [day2#agent-to-agent-concept] Agent-to-agent: delegate a task, not a function call

*A concept for Day 4*

|  | MCP | Agent-to-agent |
| --- | --- | --- |
| Other side | a server of tools and documents | another agent with its own model and tools |
| You send | a tool call with arguments | a task in words |
| You get | a result, at once | a result, possibly later, with status |

> **The A2A protocol** describes an agent with a card (what it can do) and a task lifecycle. Day 4 splits research and drafting between two agents and asks when that pays.

#### [day2#checkpoint-4] How did Bosla learn the tool names?

*Checkpoint*

**Question:** In Lab 2.4 Bosla calls `search_circulars` on the MCP server. Where did it get that tool's name and arguments?

- A. From an import of the server's Python module
- B. From the model's training data
- C. From the server's instructions text
- D. From the server's tool list, asked for at connection (discovery)

#### [day2#lab-2-4] An MCP server over the circular store

Lab 2.4 · 25 min

Build an MCP server over the circulars, pass the provided test client, and connect Bosla to it through discovery with a trace of discovery and calls.

[D2_4_mcp.ipynb](https://sdaiaacademy.github.io/ae-302/labs/D2_4_mcp.ipynb)

- [ ] Read the shape of a server (3 min)
- [ ] Build the server (8 min)
- [ ] Pass the provided tests, in-process and over stdio (6 min)
- [ ] Bosla discovers the server and uses it, with a trace (8 min)
- [ ] ✱ Stretch: Speak the protocol by hand over HTTP

#### [day2#day-2-recap] Context is a budget you spend on purpose

*Day 2 recap*

- **Measure** tokens per turn; tool results grow fastest.
- **Offload** moves information; **compaction** can lose it. Judge both on success.
- **Retrieval**: score the top hit; protect against superseded text in the ranking.

- **Context file** always, **skills** on demand, **memory** capped.
- **MCP**: tools and resources discovered at run time, tested through the protocol.

#### [day2#tomorrow-harness] Harness and loop: the parts around the model, and proof they work

*Tomorrow · Day 3*

Remove one harness part and watch what breaks, rebuild Bosla on an agent SDK, check every booking against the schedule before the loop may stop, and grade twenty tasks over five trials.
