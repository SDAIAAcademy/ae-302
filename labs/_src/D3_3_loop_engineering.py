# %% [markdown]
# # Lab 3.3 · Verification inside the loop
#
# Day 3 · Session 3 · 25 min. A model that says "done" has stopped; it has not proved anything. In this lab you add
# a check of every booking against the schedule and the berth rules, and the loop may not stop while the check
# fails. The planted problem: the booking service accepts Najm Coral at B03, where it has 0.8 m under the keel and
# circular TC-03 asks for 1.0 m.
#
# **Reference state.** `bosla.py`, a fresh port database. Nothing from Labs 3.1 or 3.2.
#
# **Tasks**
# - [ ] 1 · The planted problem, by hand (4')
# - [ ] 2 · Write the check (8')
# - [ ] 3 · The loop may not stop while the check fails (7')
# - [ ] 4 · With and without verification (6')
# - [ ] ✱ Stretch · Verification by a second model call

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/agentic-ai.git"
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
from datetime import date

import bosla
import port

# %% [markdown]
# ## 1 · The planted problem (4')
#
# ✏️ **Exercise** · On a fresh port, call `create_booking` yourself for Najm Coral (V-108) at B03, arriving
# 2026-11-15 for 2 days, agent NJM-4417. Then compute the under-keel clearance from `list_berths` and
# `get_vessel`. The service said yes; does TC-03?

# %%
p = port.Port(K.lab_dir("D3_3/by_hand", reset=True))
# BEGIN SOLUTION
made = p.create_booking("V-108", "B03", "2026-11-15", 2, "NJM-4417")
depth = next(b["depth_m"] for b in p.list_berths() if b["berth_id"] == "B03")
ukc = round(depth - p.get_vessel("V-108")["draft_m"], 1)
# END SOLUTION
print(made, "| under-keel clearance:", ukc, "m")
K.check(ukc < 1.0, "the service accepted a booking that breaks TC-03")

# %% [markdown]
# ## 2 · Write the check (8')
#
# ✏️ **Exercise** · Write `check_bookings(p, booking_ids)` returning a list of problems, one string per problem,
# each with the booking ID, what is wrong, the circular, and what to do: kind of vessel against kind of berth,
# length plus 20 m against berth length, depth minus draft against 1.0 m, and overlaps with other bookings
# (`p._busy(berth, start, days, ignore=booking_id)`). Skip cancelled bookings.

# %%
def check_bookings(p: port.Port, booking_ids: list[str]) -> list[str]:
    # BEGIN SOLUTION
    problems = []
    for bid in booking_ids:
        rows = p.sql("SELECT b.*, v.name, v.kind AS vkind, v.loa_m, v.draft_m, t.kind AS bkind, t.length_m, t.depth_m "
                     "FROM bookings b JOIN vessels v USING (vessel_id) JOIN berths t USING (berth_id) "
                     "WHERE booking_id = ?", (bid,))
        if not rows or rows[0]["status"] == "cancelled":
            continue
        b = rows[0]
        if b["vkind"] != b["bkind"]:
            problems.append(f"{bid}: {b['name']} is {b['vkind']}, {b['berth_id']} takes {b['bkind']} (TC-03)")
        if b["loa_m"] + 20 > b["length_m"]:
            problems.append(f"{bid}: {b['name']} is too long for {b['berth_id']} (TC-03)")
        if round(b["depth_m"] - b["draft_m"], 1) < port.MIN_UKC_M:
            problems.append(f"{bid}: under-keel clearance at {b['berth_id']} is {round(b['depth_m'] - b['draft_m'], 1)} m,"
                            " below 1.0 m (TC-03). Amend to a berth from find_windows, or cancel.")
        clash = p._busy(b["berth_id"], date.fromisoformat(b["arrival"]), b["days"], ignore=bid)
        if clash:
            problems.append(f"{bid}: overlaps {', '.join(clash)} on {b['berth_id']}")
    return problems
    # END SOLUTION


print(check_bookings(p, [made["booking_id"], "BK-24017", "BK-24022"]))
K.check(len(check_bookings(p, [made["booking_id"]])) == 1 and check_bookings(p, ["BK-24017"]) == [],
        "one problem on the new booking, none on a good one")

# %% [markdown]
# 🔍 BK-24022 is Najm Coral at B03 too, booked before the course started. Your check flags it. Should Bosla touch a
# booking it did not make in this run? Who should hear about it?

# %% [markdown]
# ## 3 · The loop may not stop while the check fails (7')
#
# ✏️ **Exercise** · Write `verified_run(task, p, rounds=2)`: run `bosla.run`; collect the bookings this run created
# or amended (`bosla.touched(run, p)`); if `check_bookings` finds problems and the run stopped with `done`, continue
# the same conversation with a user message that starts "Verification failed." and lists them; at most `rounds`
# times. Record each continuation as a `guard` event in the trace.

# %%
def verified_run(task: str, p: port.Port, rounds: int = 2) -> K.Run:
    # BEGIN SOLUTION
    r = bosla.run(task, p)
    for _ in range(rounds):
        problems = check_bookings(p, bosla.touched(r, p))
        if not problems or r.stopped != "done":
            break
        note = "Verification failed. Fix these before you finish:\n" + "\n".join(f"- {x}" for x in problems)
        trace = r.trace + [K.Event("guard", note)]
        history = [m for m in r.state if m.get("role") != "system"]
        nxt = K.run_agent(note, p.tools(), system=port.SYSTEM_PROMPT + "\n\n" + bosla.CONTEXT_FILE, history=history,
                          max_steps=8, permission=bosla.write_gate(task), verbose=False)
        nxt.trace, nxt.tool_calls = trace + nxt.trace, r.tool_calls + nxt.tool_calls
        r = nxt
    return r
    # END SOLUTION


# %% [markdown]
# ## 4 · With and without verification (6')
#
# ✏️ **Exercise** · Run the task below on two fresh ports, once with `bosla.run` and once with `verified_run`.
# For each: the bookings of V-108 created in the run, and what `check_bookings` says about them at the end.

# %%
TASK = "Agent code NJM-4417. Book Najm Coral (V-108) at berth B03 arriving 2026-11-15 for 2 days. I confirm."
results = {}
for name, runner in [("without", bosla.run), ("with", verified_run)]:
    # BEGIN SOLUTION
    q = port.Port(K.lab_dir(f"D3_3/{name}", reset=True))
    r = runner(TASK, q)
    mine = bosla.touched(r, q)
    results[name] = {"bookings": q.sql("SELECT booking_id, berth_id, status FROM bookings WHERE vessel_id = 'V-108' "
                                       "AND created = '2026-11-01'"), "problems": check_bookings(q, mine),
                     "guards": sum(e.kind == "guard" for e in r.trace)}
    # END SOLUTION
for name, res in results.items():
    print(name, res)
K.check(results["with"]["problems"] == [], "with verification, the run ends with no rule broken")

# %% [markdown]
# 🔍 The agent asked for B03 because the agent's message did. Verification did not refuse the request: it made the
# loop fix it, or say why it could not. Read the final answer: does it tell Faisal that B03 was not possible?

# %% [markdown]
# ## ✱ Stretch · A model as the checker
#
# Replace `check_bookings` with a model call that reads TC-03 and the booking and answers pass or fail with a
# reason (Day 1's structured outputs). On the planted case, does it agree with your code? Which would you trust?

# %% [markdown]
# ## Checkpoint
#
# 1. Why put the check in the loop instead of in the prompt ("check the under-keel clearance")?
# 2. The check failed twice and the loop gave up. What must the final answer say?
# 3. Why did the booking service not enforce TC-03 itself, and should it?
