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
