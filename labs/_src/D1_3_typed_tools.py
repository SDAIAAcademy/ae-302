# %% [markdown]
# # Lab 1.3 · Typed tools with useful errors
#
# Day 1 · Session 3 · 25 min. A tool is a contract: a name, a description, typed arguments, and results and
# **errors** the model can act on. In this lab you write typed argument schemas for two of Marsa's tools (the
# schedule's `find_windows` and the booking service's `create_booking`), make bad arguments come back as errors
# that say what to send instead, and watch one round trip recover from a mistake.
#
# **Reference state.** A fresh copy of the port database and the plain tools of `port.py`. Nothing from Labs 1.1
# or 1.2.
#
# **Tasks**
# - [ ] 1 · Read the schema generated from a plain function (4')
# - [ ] 2 · Typed argument models (6')
# - [ ] 3 · A wrapper that turns bad arguments into useful errors (8')
# - [ ] 4 · One round trip by hand: a bad call, a useful error, a good call (7')
# - [ ] ✱ Stretch · The same tool for the Messages and MCP shapes

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
import functools
import json
from datetime import date

from pydantic import BaseModel, Field, ValidationError

import port

p = port.Port(K.lab_dir("D1_3", reset=True))

# %% [markdown]
# ## 1 · The schema of a plain function (4')
#
# `K.tool_schema(fn)` builds a tool definition from type hints and the docstring. The model sees only this: the
# name, the description and the parameters. Not your code.
#
# ✏️ **Exercise** · Print the schema of `p.create_booking` and answer in `weak`: which parameters accept values the
# service will refuse (name two)?

# %%
K.show(K.tool_schema(p.create_booking))
# BEGIN SOLUTION
weak = ["berth_id is any string (the service knows only B01 to B08)",
        "arrival is any string (the service needs YYYY-MM-DD)",
        "days is any integer (the service accepts 1 to 14)"]
# END SOLUTION
print(weak)

# %% [markdown]
# ## 2 · Typed argument models (6')
#
# ✏️ **Exercise** · Write `WindowArgs` for `find_windows` and `BookingArgs` for `create_booking` with Pydantic:
# `vessel_id` matches `V-` and three digits; `berth_id` is one of `port.BerthId`; dates are `date`; `days` is 1 to
# 14; `agent_code` matches three capitals, a dash and four digits. Give every field a description with an example.

# %%
# BEGIN SOLUTION
VESSEL = Field(pattern=r"^V-\d{3}$", description='Vessel ID, e.g. "V-110" (get_vessel finds it from a name)')
DAYS = Field(ge=1, le=14, description="Days at berth, 1 to 14")


class WindowArgs(BaseModel):
    vessel_id: str = VESSEL
    days: int = DAYS
    date_from: date = Field(description="Earliest arrival, YYYY-MM-DD, e.g. 2026-11-05")
    date_to: date = Field(description="Latest arrival, YYYY-MM-DD, e.g. 2026-11-12")


class BookingArgs(BaseModel):
    vessel_id: str = VESSEL
    berth_id: port.BerthId = Field(description="Berth, B01 to B08")
    arrival: date = Field(description="Arrival date, YYYY-MM-DD, e.g. 2026-11-07")
    days: int = DAYS
    agent_code: str = Field(pattern=r"^[A-Z]{3}-\d{4}$", description='Shipping agent code, e.g. "NJM-4417"')
    dangerous_goods: bool = Field(default=False, description="True when the cargo includes dangerous goods")
# END SOLUTION


print(json.dumps(BookingArgs.model_json_schema()["properties"]["berth_id"]))
K.check("enum" in json.dumps(BookingArgs.model_json_schema()), "berth_id is an enum the model can read")

# %% [markdown]
# ## 3 · Useful errors (8')
#
# A useful error names the argument, says what was wrong, and gives a valid example. It goes back to the model as
# a **result**, so the model can try again.
#
# ✏️ **Exercise** · Write `typed(fn, Args)`: a function with the same name and docstring that validates its
# keyword arguments with `Args`, and on `ValidationError` raises `port.ToolError` with one line per problem:
# `"<field>: <message> (you sent <value>)"`, then a last line listing the valid fields. On success it calls `fn`
# with the validated values (dates as `YYYY-MM-DD` text). Attach `__tool_schema__` so the model sees `Args`'s
# schema.

# %%
def typed(fn, Args: type[BaseModel]):
    # BEGIN SOLUTION
    @functools.wraps(fn)
    def wrapper(**kwargs):
        try:
            args = Args(**kwargs)
        except ValidationError as e:
            lines = [f"{'.'.join(map(str, err['loc'])) or 'arguments'}: {err['msg']} (you sent {err.get('input')!r})"
                     for err in e.errors()]
            lines.append(f"Valid arguments: {', '.join(Args.model_fields)}.")
            raise port.ToolError("\n".join(lines)) from None
        return fn(**args.model_dump(mode="json"))

    description, _ = K._parse_doc(fn)
    schema = Args.model_json_schema()
    schema.pop("title", None)
    wrapper.__tool_schema__ = {"name": fn.__name__, "description": description, "parameters": schema}
    return wrapper
    # END SOLUTION


find_windows = typed(p.find_windows, WindowArgs)
create_booking = typed(p.create_booking, BookingArgs)
by_name = {"find_windows": find_windows, "create_booking": create_booking}

BAD = [
    ("find_windows", {"vessel_id": "Najm Falcon", "days": 2, "date_from": "2026-11-05", "date_to": "2026-11-12"}),
    ("find_windows", {"vessel_id": "V-110", "days": 20, "date_from": "2026-11-05", "date_to": "2026-11-12"}),
    ("find_windows", {"vessel_id": "V-110", "days": 2, "date_from": "next Sunday", "date_to": "2026-11-12"}),
    ("create_booking", {"vessel_id": "V-110", "berth_id": "berth 2", "arrival": "2026-11-07", "days": 2, "agent_code": "NJM-4417"}),
    ("create_booking", {"vessel_id": "V-110", "berth_id": "B02", "arrival": "2026-11-07", "days": 2, "agent_code": "najm"}),
    ("create_booking", {"vessel_id": "V-110", "berth_id": "B02", "arrival": "2026-11-07", "days": 2}),
]
for name, args in BAD:
    raw = K.call_tool({"find_windows": p.find_windows, "create_booking": p.create_booking}, name, args)
    useful = K.call_tool(by_name, name, args)
    print(f"{name}: raw    → {raw[:110]}\n{' ' * len(name)}  useful → {useful[:160]}\n")
K.check(all("error" in K.call_tool(by_name, n, a) for n, a in BAD), "all six bad calls come back as errors")
K.check(all("you sent" in K.call_tool(by_name, n, a) or "missing" in K.call_tool(by_name, n, a).lower() for n, a in BAD),
        "every error names what was sent or what is missing")

# %% [markdown]
# 🔍 Compare the raw and useful lines. One raw call does not fail at all (the service accepts a name), and one
# fails for a misleading reason. Find both: which would a model misread?

# %% [markdown]
# ## 4 · One round trip by hand (7')
#
# ✏️ **Exercise** · Send Faisal's request with the two typed tools to `K.chat`. Run whatever tool calls the model
# returns with `K.call_tool(by_name, ...)`, append the assistant message and one `role="tool"` message per call,
# and ask again, at most four times. Count the error results and the good ones in `counts`. Then read the
# database: was the booking made?

# %%
FAISAL = ("Agent code NJM-4417. Book Najm Falcon (V-110) at berth 2 arriving 7 Nov 2026 for two days. I confirm. "
          "Use the tools; do not ask me again.")
messages = [{"role": "system", "content": port.SYSTEM_PROMPT}, {"role": "user", "content": FAISAL}]
counts = {"error": 0, "ok": 0}
# BEGIN SOLUTION
for _ in range(4):
    msg = K.chat(messages, tools=[find_windows, create_booking], temperature=0).choices[0].message
    messages.append(msg.model_dump(exclude_none=True))
    if not msg.tool_calls:
        print("final:", msg.content)
        break
    for c in msg.tool_calls:
        out = K.call_tool(by_name, c.function.name, c.function.arguments)
        counts["error" if out.startswith('{"error"') else "ok"] += 1
        print(f"{c.function.name}({c.function.arguments}) → {out[:140]}")
        messages.append({"role": "tool", "tool_call_id": c.id, "content": out})
# END SOLUTION
made = p.sql("SELECT booking_id, berth_id, arrival FROM bookings WHERE vessel_id = 'V-110'")
print(counts, made)
K.check(len(made) == 1 and made[0]["berth_id"] == "B02", "the booking exists, on B02")

# %% [markdown]
# ## ✱ Stretch · One tool, three more shapes
#
# Print `K.tool_schema(create_booking, shape)` for `"responses"`, `"anthropic"` and `"mcp"`. Which key holds the
# parameters in each? Day 2 serves the same contract over the Model Context Protocol.

# %%
# BEGIN SOLUTION
for shape in ("responses", "anthropic", "mcp"):
    print(shape, sorted(K.tool_schema(create_booking, shape)))
# END SOLUTION

# %% [markdown]
# ## Checkpoint
#
# 1. Why is `berth_id: Literal[...]` better than a description that lists the berths?
# 2. Which part of a tool error does the model use to try again?
# 3. `create_booking` does not check under-keel clearance. Should the schema check it? Where should that check live?
