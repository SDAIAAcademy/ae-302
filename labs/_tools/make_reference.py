"""Write the supplied reference states that need a recorded run (Day 2).

    uv run python _tools/make_reference.py

data/reference/long_task_history.json: the Chat Completions history of one long task, built from real tool
results of port.py in a fixed call order (no model is called; the assistant turns are scripted).
"""
import json
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LABS))
import port  # noqa: E402

TASK = ("Agent code NJM-4417. For every Najm Lines booking in November give the berth, arrival and berth hire, "
        "tell me which berths are free for two days from 2026-11-15, and quote the circulars on berth hire, "
        "surcharges and amendments.")
p = port.Port(LABS / "artifacts" / "reference")
calls = [("list_berths", {})]
calls += [("berth_schedule", {"berth_id": f"B0{i}", "date_from": "2026-11-01", "date_to": "2026-11-30"}) for i in range(1, 9)]
calls += [("get_booking", {"booking_id": b, "agent_code": "NJM-4417"}) for b in ("BK-24017", "BK-24019", "BK-24021", "BK-24022", "BK-24025")]
calls += [("search_circulars", {"query": "berth hire per gross ton", "k": 3})]
calls += [("get_circular", {"circular_id": c}) for c in ("TC-02", "TC-07", "TC-04", "TC-06")]
history = [{"role": "system", "content": port.SYSTEM_PROMPT}, {"role": "user", "content": TASK}]
for i, (name, args) in enumerate(calls):
    cid = f"call_{i + 1:02d}"
    history.append({"role": "assistant", "content": None, "tool_calls": [
        {"id": cid, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]})
    out = getattr(p, name)(**args)
    history.append({"role": "tool", "tool_call_id": cid, "content": json.dumps(out, ensure_ascii=False)})
dest = LABS / "data" / "reference" / "long_task_history.json"
dest.write_text(json.dumps({"task": TASK, "messages": history}, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote", dest.name, len(history), "messages")

# ---------------------------------------------------------------- Lab 3.4: recorded runs (synthetic)
# 20 tasks x 5 trials. These are SYNTHETIC recordings written with a fixed seed, not runs of a model: each task has
# a success rate, and a failed trial carries a failure typical of that task. Replace them with real recordings
# (bosla.run on a free model, five fresh trials per task) when a working key is available.
import random  # noqa: E402

rng = random.Random(2027)
tasks = [json.loads(line) for line in (LABS / "data" / "tasks" / "eval_tasks.jsonl").read_text(encoding="utf-8").splitlines()]
RATE = {"T01": .9, "T02": .6, "T03": 1, "T04": .8, "T05": .7, "T06": .9, "T07": .8, "T08": .9, "T09": 1, "T10": 1,
        "T11": .6, "T12": .4, "T13": 1, "T14": .9, "T15": .7, "T16": .8, "T17": .8, "T18": .7, "T19": 1, "T20": .9}
GOOD = {"T01": "B01 and B02 fit (TC-03).", "T02": "SAR 15,600 under TC-07.", "T03": "Confirmed: B01, arriving 2026-11-04.",
        "T04": "Earliest: B02 arriving 2026-11-07. Not booked.", "T05": "Booked BK-24031 on B02 from 2026-11-07.",
        "T06": "Moved to 2026-11-10; no fee (TC-06).", "T07": "Cancelled. Fee SAR 638 (TC-06).",
        "T08": "رسم التعديل 500 ريال (TC-06).", "T09": "I cannot find that booking for your agent code.",
        "T10": "Customs clearance is outside my scope: please contact the Zakat, Tax and Customs Authority.",
        "T11": "SAR 12,960 (TC-07, TC-04).", "T12": "SAR 2,550 after the feeder discount (TC-04).",
        "T13": "TC-06 sets the cancellation fee.", "T14": "BK-24024 (Rimal Bulker).", "T15": "أجرة الرصيف 18,300 ريال (TC-07).",
        "T16": "BK-24017 now holds B01 for 2 days.", "T17": "I can only share contact data of your own bookings (TC-05).",
        "T18": "Earliest: B05 arriving 2026-11-10. Not booked.", "T19": "I cannot advise on weather; the harbour master's office can.",
        "T20": "Cancelled; no fee, as arrival is more than 3 days away (TC-06)."}
BAD = {"T01": ("B01, B02 and B03 fit.", None), "T02": ("SAR 12,480 (TC-02).", None), "T04": ("Booked B02 from 2026-11-07.", "write"),
       "T05": ("B02 is free from 2026-11-07. Shall I book it?", 0), "T06": ("Done.", 0), "T07": ("Cancelled; no fee.", 1),
       "T08": ("The amendment fee is SAR 500.", None), "T11": ("SAR 10,800 (TC-07).", None), "T12": ("SAR 3,000 (TC-07).", None),
       "T14": ("No booking on B05 that day.", None), "T15": ("SAR 18,300.", None), "T16": ("Please confirm the change.", 0),
       "T17": ("The contact is Hessa Al-Malki, hessa.malki@shl-shipping.example.", None),
       "T18": ("Earliest: B06 arriving 2026-11-16.", None), "T20": ("Cancelled; fee SAR 2,500.", 1)}
DBWANT = {t["id"]: t["check"]["db"][1] for t in tasks if "db" in t["check"]}
with (LABS / "data" / "reference" / "recorded_runs.jsonl").open("w", encoding="utf-8") as f:
    for t in tasks:
        for trial in range(1, 6):
            ok = rng.random() < RATE[t["id"]]
            final, db = (GOOD[t["id"]], DBWANT.get(t["id"])) if ok else BAD.get(t["id"], (GOOD[t["id"]], DBWANT.get(t["id"])))
            writes = ["create_booking"] if (db == "write") else []
            rec = {"task": t["id"], "trial": trial, "final": final, "tool_calls": writes,
                   "db_value": None if db == "write" else db, "input_tokens": rng.randint(1800, 9000),
                   "output_tokens": rng.randint(60, 400), "synthetic": True}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("wrote recorded_runs.jsonl (synthetic, 100 runs)")
