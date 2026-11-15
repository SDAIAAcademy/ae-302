# %% [markdown]
# # Lab 1.2 · Structured outputs: a berth request as a validated object
#
# Day 1 · Session 2 · 25 min. Shipping agents write berth requests as free text, in English or Arabic. The booking
# service needs a typed object. In this lab you define the schema, ask the model for it, and write the part that
# real systems need most: **recovering when the reply does not validate**.
#
# **Reference state.** Six requests with their correct answers in `data/berth_requests.jsonl`, and three malformed
# replies in this notebook. Nothing from Lab 1.1.
#
# **Tasks**
# - [ ] 1 · The schema: `BerthRequest` (5')
# - [ ] 2 · Ask for it with a JSON Schema response format (5')
# - [ ] 3 · Recover from three malformed replies (8')
# - [ ] 4 · Six requests, field accuracy (7')
# - [ ] ✱ Stretch · A request with a missing field: say so, do not invent

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/ae-302.git"
    if not Path("/content/agentic-ai").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/agentic-ai"], check=True)
    os.chdir("/content/agentic-ai/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("agentkit.py").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())

import agentkit as K
print("provider:", K.PROVIDER, "| model:", K.MODEL)

# %%
import json
import re
from datetime import date
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

REQUESTS = [json.loads(line) for line in (K.DATA / "berth_requests.jsonl").read_text(encoding="utf-8").splitlines()]
print(len(REQUESTS), "requests;", REQUESTS[1]["text"])

# %% [markdown]
# ## 1 · The schema (5')
#
# ✏️ **Exercise** · Define `BerthRequest` with: `vessel_name` (text), `arrival` (a `date`), `days` (1 to 14),
# `kind` (one of `container`, `general`, `dry_bulk`, `ro_ro`, `tanker`), `dangerous_goods` (bool) and
# `agent_code` (three capital letters, a dash, four digits). Each constraint you write here is one the model can no
# longer get wrong silently.

# %%
# BEGIN SOLUTION
class BerthRequest(BaseModel):
    vessel_name: str = Field(description="The vessel's name as written, without words like 'MV' or 'the tanker'")
    arrival: date = Field(description="Arrival date")
    days: int = Field(ge=1, le=14, description="Days at berth")
    kind: Literal["container", "general", "dry_bulk", "ro_ro", "tanker"]
    dangerous_goods: bool
    agent_code: str = Field(pattern=r"^[A-Z]{3}-\d{4}$", description="Shipping agent code, e.g. NJM-4417")
# END SOLUTION


print(json.dumps(BerthRequest.model_json_schema(), indent=1)[:600])
K.check(BerthRequest.model_fields["agent_code"] is not None, "BerthRequest defined")

# %% [markdown]
# ## 2 · Ask for it (5')
#
# `response_format={"type": "json_schema", ...}` asks the provider to constrain the reply to the schema. Not every
# free model or gateway honours it, so the schema also goes into the prompt, and the reply is **validated anyway**.
#
# ✏️ **Exercise** · Write `ask(text)` that sends one request with `K.chat(...)`, the schema in the system message
# and in `response_format`, `temperature=0`, and returns the reply's text.

# %%
SYSTEM = "Extract the berth request as one JSON object matching this JSON Schema, and nothing else:\n"


def ask(text: str) -> str:
    # BEGIN SOLUTION
    schema = BerthRequest.model_json_schema()
    fmt = {"type": "json_schema", "json_schema": {"name": "BerthRequest", "schema": schema}}
    resp = K.chat([{"role": "system", "content": SYSTEM + json.dumps(schema)}, {"role": "user", "content": text}],
                  response_format=fmt, temperature=0)
    return resp.choices[0].message.content or ""
    # END SOLUTION


raw = ask(REQUESTS[0]["text"])
print(raw)

# %% [markdown]
# ## 3 · Recover from three malformed replies (8')
#
# Below are three replies that a model really can send. Each fails differently:
# (a) right JSON wrapped in prose and a code fence; (b) a date and a number in words; (c) a missing field.
#
# ✏️ **Exercise** · Write `parse_or_repair(reply, request, repairs=2)`:
# 1. take the text between the first `{` and the last `}` and validate it with `BerthRequest.model_validate_json`;
# 2. on `ValidationError`, send the model the request, its own reply as an assistant message, and the validation
#    error as a user message ("That JSON is invalid: ... Reply with the corrected JSON only."), then try again;
# 3. after `repairs` failed repairs, raise the last error. Return `(obj, attempts)`.
#
# Step 1 alone fixes (a) without a model call. (b) and (c) need a repair round trip.

# %%
MALFORMED = [
    'Sure! Here is the request:\n```json\n{"vessel_name": "Najm Falcon", "arrival": "2026-11-07", "days": 2, '
    '"kind": "container", "dangerous_goods": false, "agent_code": "NJM-4417"}\n```\nLet me know if you need more.',
    '{"vessel_name": "Najm Falcon", "arrival": "7 November 2026", "days": "two", "kind": "container", '
    '"dangerous_goods": false, "agent_code": "NJM-4417"}',
    '{"vessel_name": "Najm Falcon", "arrival": "2026-11-07", "days": 2, "kind": "container", "dangerous_goods": false}',
]


def parse_or_repair(reply: str, request: str, repairs: int = 2) -> tuple[BerthRequest, int]:
    # BEGIN SOLUTION
    schema = json.dumps(BerthRequest.model_json_schema())
    messages = [{"role": "system", "content": SYSTEM + schema}, {"role": "user", "content": request}]
    for attempt in range(repairs + 1):
        start, end = reply.find("{"), reply.rfind("}")
        try:
            return BerthRequest.model_validate_json(reply[start: end + 1] if start >= 0 else reply), attempt
        except ValidationError as e:
            if attempt == repairs:
                raise
            messages += [{"role": "assistant", "content": reply},
                         {"role": "user", "content": f"That JSON is invalid: {e}\nReply with the corrected JSON only."}]
            reply = K.chat(messages, temperature=0).choices[0].message.content or ""
    # END SOLUTION


for bad in MALFORMED:
    obj, attempts = parse_or_repair(bad, REQUESTS[0]["text"])
    print(attempts, "repair(s) →", obj.model_dump(mode="json"))
    K.check(obj.agent_code == "NJM-4417" and obj.days == 2, "recovered a valid BerthRequest")

# %% [markdown]
# 🔍 Read the validation error of (b) and (c): it names the field and what was wrong. That message is the whole
# repair prompt. Session 3 gives tools the same kind of error.

# %% [markdown]
# ## 4 · Six requests, field accuracy (7')
#
# ✏️ **Exercise** · For every request: `ask`, then `parse_or_repair`. Compare each field with `gold` and collect one
# row per request with the number of correct fields (out of 6) and the repairs used. Which field fails most?

# %%
rows = []
for r in REQUESTS:
    # BEGIN SOLUTION
    try:
        obj, attempts = parse_or_repair(ask(r["text"]), r["text"])
        got = obj.model_dump(mode="json")
        right = [f for f, v in r["gold"].items() if got.get(f) == v]
        rows.append({"id": r["id"], "correct": len(right), "repairs": attempts,
                     "wrong": ", ".join(f for f in r["gold"] if f not in right)})
    except ValidationError:
        rows.append({"id": r["id"], "correct": 0, "repairs": 2, "wrong": "no valid object"})
    # END SOLUTION
acc = pd.DataFrame(rows)
print(acc.to_string(index=False))
print("field accuracy:", round(acc.correct.sum() / (6 * len(acc)), 2), "|", K.LEDGER)
K.check(acc.correct.sum() >= 30, "at least 30 of 36 fields right")

# %% [markdown]
# ## ✱ Stretch · Say "missing", do not invent
#
# "Najm Pearl needs a berth next week, containers." has no agent code, no date and no days. A schema that requires
# them pushes the model to invent them. Add `missing: list[str]` to a copy of the schema, make the three fields
# optional, and instruct the model to list what is missing instead of guessing.

# %%
# BEGIN SOLUTION
class MaybeBerthRequest(BerthRequest):
    arrival: date | None = None
    days: int | None = Field(default=None, ge=1, le=14)
    agent_code: str | None = Field(default=None, pattern=r"^[A-Z]{3}-\d{4}$")
    missing: list[str] = Field(default_factory=list, description="Fields the text does not state")


partial = K.structured("Najm Pearl needs a berth next week, containers.", MaybeBerthRequest,
                       system="Extract the berth request. Never guess a value: list unstated fields in `missing`.")
print(partial)
# END SOLUTION

# %% [markdown]
# ## Checkpoint
#
# 1. Which of the three malformed replies did not need a model call, and why?
# 2. Why validate a reply that was produced under a JSON Schema response format?
# 3. Request R2 is in Arabic and says "fuel". Which field is most at risk, and what in the schema protects it?
