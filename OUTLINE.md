# AE-302 rebuild plan: from the Madar course to the catalog entry

The catalog entry is the plan. The old course (Madar Municipal Services, assistant Rafeeq) is a
source of slides and lab code where the teaching is the same. Every name, record, example, lab
and checkpoint moves to the entry's case.

## Case study (decided on the Director's behalf)

**Marsa Ports Authority** (هيئة موانئ مرسى), a fictional Red Sea port authority. Course clock:
Sunday 1 November 2026. Data is synthetic, generated with a fixed seed by `labs/prepare_data.py`.

- Three services, as typed Python tools over SQLite (`labs/port.py`): the **berth schedule**
  (berths, occupancy, free windows), the **tariff circulars** (bilingual English and Arabic
  circulars TC-01 to TC-08, a later one superseding an earlier one), the **booking service**
  (read, create, amend, cancel: write actions, checked against the shipping agent's code).
- Personas: **Bosla** (بوصلة), the booking assistant participants build; **Captain Huda
  Al-Harbi**, duty harbour master, the human approver; **Faisal Al-Otaibi**, shipping agent of
  Najm Lines; **Reem Al-Dosari**, tariff officer who writes the circulars.
- Planted problems: a superseded tariff circular; a vessel whose draft fits a berth with less
  than the safety margin; a booking change above the fee threshold; an agent code that does not
  own the booking; from Day 4, a circular carrying planted instructions and a booking list with
  synthetic personal data classified Restricted.
- Risk threshold for the approval gate (circular TC-06): dangerous goods, an under-keel margin
  below 1.0 m, or a fee effect above SAR 10,000.

## Reference states

Each lab starts from `Port(K.lab_dir(...))`, a fresh copy of the database, plus the files it
needs from `labs/reference/` (tool definitions, a working loop, a working agent). No lab reads
another lab's output.

## Per session

| Session (entry) | Kept from the old course | Re-cased | Lab under the entry's line |
|---|---|---|---|
| 1.1 Three API shapes | LLM basics, tokens, providers, free models, the three shapes table, fallbacks | Madar questions become berth and tariff questions; Arabic token tax on a circular | One open-weight model through Chat Completions, Responses and Messages; compare items, stop reasons, usage |
| 1.2 Structured outputs | JSON Schema, Pydantic, validate and repair | Inbox triage becomes berth-request extraction | Extract a berth request into a validated schema; recover from three malformed replies |
| 1.3 Tools | Tool call anatomy, schemas from type hints, tool design | Permit tools become schedule and booking tools | Typed schemas for the schedule and booking tools, with useful errors for bad arguments |
| 1.4 The agent loop | Loop pseudocode, trace, breaking it | Rafeeq becomes Bosla | Loop with a step budget and stop rule, written without AI, run on ten tasks with a trace each |
| 2.1 Context as a budget | Token anatomy, trimming, compaction, cache prefix | Long schedule dumps | Tokens per turn on a long task; compaction and offloading tool results to files |
| 2.2 Retrieval | BM25, Arabic normalisation, embeddings, agentic search | Policies become circulars | Keyword and vector search over circulars as two tools; trace which the agent picks |
| 2.3 Memory, skills, context files | Memory contract, SKILL.md, staged loading | Skills become a tariff skill | A context file and a tariff skill; staged loading shown in a trace |
| 2.4 MCP | Server, discovery, JSON-RPC by hand | Madar server becomes the circular store | Server over the circular store, passes a provided test client; agent connects by discovery |
| 3.1 Anatomy of a harness | Harness parts, teardown matrix | Pi teardown shortened | Remove one harness part from a working agent and record what breaks |
| 3.2 Agent SDKs | Agents SDK rebuild, approvals | Rafeeq becomes Bosla | Rebuild with one SDK; compare code size, traces, control with the own loop |
| 3.3 Loop engineering | Verification inside the loop, stop conditions | The Ralph coding loop is replaced | Check each booking against the schedule before the loop may stop |
| 3.4 Evaluating agents | Graders, pass@k and pass^k | 30 tasks become 20 recorded runs | Grade recorded runs of 20 tasks over five trials with code and model graders |
| 4.1 State graphs | LangGraph, interrupt, resume after crash | Permit review becomes booking changes | Booking flow as a state graph, approval interrupt at the TC-06 threshold, resume after restart |
| 4.2 Several agents | Orchestrator and workers, meter | A2A worker kept as a concept | Research and drafting split between two agents; quality and cost against one |
| 4.3 Securing agents | Trifecta, remove one leg, red-team suite | Staff inbox becomes a planted circular | Planted instruction leaks a booking list (Restricted, PDPL); remove one leg until it fails |
| 4.4 Production | FastAPI, spans, smoke eval with a gate | Rafeeq API becomes Bosla API | Behind an API, traced, smoke evaluation in CI that fails on a seeded regression |

Capstone (Day 5): a research agent over synthetic port documents, starter in `labs/capstone/`,
public repository whose README reports success over repeated trials, cost per completed task
and the containment design; eight-minute defence. Rubric from the entry.

## Cut from the old course

The Ralph loop that fixes code (3.3), the staff inbox (4.3), the permit-review graph's letter
step, the five-day "polish and submit" capstone shape. Topics the entry does not list are cut.

## Order of work

Day 1 first and complete (domain module, data, four labs run, deck re-cased), then Days 2, 3, 4,
then the capstone deck and manifest, then the gates. Labs run against a free OpenRouter model;
anything not run is reported.
