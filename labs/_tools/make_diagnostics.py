"""Write the two synthetic logs behind the Day 1 tool-routing slides and the Day 2 position-ablation slides.

    uv run python _tools/make_diagnostics.py

Both logs are SYNTHETIC: drawn with a fixed seed from stated rates, not runs of a model. They are teaching artifacts
for reading a log and deciding, set at a second Marsa desk (pilotage) so they give away no lab answer. The script
prints every number the slides quote and checks them, so a slide and the data cannot drift apart.

data/reference/routing_log.jsonl      40 labelled pilotage requests, first tool called, before and after the
                                      two overlapping descriptions were rewritten
data/reference/position_ablation.jsonl 10 pilotage-handbook questions x 5 trials x 5 positions of the right
                                      section among 20 packed sections, plus the fix (best 5 sections, best first)
"""
import json
import random
from collections import Counter
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]
REF = LABS / "data" / "reference"
SEED = 2027

# ------------------------------------------------------------------ 1. Tool routing (Day 1, session 3)
# Two read tools of a pilotage assistant whose descriptions overlap, then the same two rewritten.
DESCRIPTIONS = {
    "before": {
        "find_pilot_slots": "Find pilot availability for a vessel.",
        "pilot_roster": "Show the pilots and when they are available.",
    },
    "after": {
        "find_pilot_slots": "Free pilotage slots for one vessel movement, by vessel ID and date. Use it to plan an "
                            "arrival or departure. Not for questions about named pilots: use pilot_roster.",
        "pilot_roster": "Named pilots, their licence class and duty days. Use it for questions about a person. "
                        "Not for slot planning: use find_pilot_slots.",
    },
}
# Probability of each first call, given the tool the request needs (rows) and the description set.
ROUTING_RATES = {
    "before": {"find_pilot_slots": {"find_pilot_slots": .65, "pilot_roster": .30, "none": .05},
               "pilot_roster": {"find_pilot_slots": .40, "pilot_roster": .60, "none": .00}},
    "after": {"find_pilot_slots": {"find_pilot_slots": .95, "pilot_roster": .05, "none": .00},
              "pilot_roster": {"find_pilot_slots": .05, "pilot_roster": .95, "none": .00}},
}
REQUESTS = {
    "find_pilot_slots": ["V-{:03d}: when can a pilot bring her in on 2026-12-{:02d}?",
                         "Is there a pilot for V-{:03d} leaving on 2026-12-{:02d}?"],
    "pilot_roster": ["Which pilots hold the class A licence on duty 2026-12-{1:02d}? (ref V-{0:03d})",
                     "Is pilot P-{0:03d} on duty on 2026-12-{1:02d}?"],
}
COLUMNS = ["find_pilot_slots", "pilot_roster", "none"]


def draw(rng, rates):
    x, acc = rng.random(), 0.0
    for name in COLUMNS:
        acc += rates[name]
        if x < acc:
            return name
    return COLUMNS[-1]


def routing():
    rng = random.Random(SEED)
    rows = []
    for expected in ("find_pilot_slots", "pilot_roster"):
        for i in range(20):
            text = REQUESTS[expected][i % 2].format(200 + i, 1 + i)
            rows.append({"request": f"R{len(rows) + 1:02d}", "text": text, "expected": expected})
    for cfg in ("before", "after"):
        for r in rows:
            r[f"first_call_{cfg}"] = draw(rng, ROUTING_RATES[cfg][r["expected"]])
    return rows


def confusion(rows, cfg):
    return {e: Counter(r[f"first_call_{cfg}"] for r in rows if r["expected"] == e) for e in ("find_pilot_slots", "pilot_roster")}


# ------------------------------------------------------------------ 2. Position ablation (Day 2, session 2)
# Retrieval is healthy: the right section is in the 20 retrieved sections for every question (recall@20 = 1.0)
# and first in 9 of 10. The prompt builder packs the 20 sections in handbook order, so the right one lands
# wherever its section number puts it. The ablation keeps the 20 sections and moves only the right one.
POSITIONS = [1, 5, 10, 15, 20]
ANSWER_RATES = {1: .92, 5: .78, 10: .52, 15: .62, 20: .86}
FIX_RATE = .94  # the best 5 sections, best first
QUESTIONS, TRIALS = 10, 5
HIT_AT_1 = [True] * 9 + [False]


def ablation():
    rng = random.Random(SEED + 1)
    rows = []
    for q in range(QUESTIONS):
        for pos in POSITIONS:
            for t in range(TRIALS):
                rows.append({"question": f"H{q + 1:02d}", "config": "20 sections, handbook order moved",
                             "position": pos, "of": 20, "trial": t + 1, "gold_in_context": True,
                             "correct": rng.random() < ANSWER_RATES[pos]})
        for t in range(TRIALS):
            rows.append({"question": f"H{q + 1:02d}", "config": "best 5, best first", "position": 1, "of": 5,
                         "trial": t + 1, "gold_in_context": True, "correct": rng.random() < FIX_RATE})
    return rows


def main():
    REF.mkdir(parents=True, exist_ok=True)
    r_rows = routing()
    (REF / "routing_log.jsonl").write_text("".join(json.dumps(r) + "\n" for r in r_rows), encoding="utf-8")
    print("Tool routing, 40 labelled requests (synthetic)")
    errors = {}
    for cfg in ("before", "after"):
        m = confusion(r_rows, cfg)
        print(f"  {cfg}: needed -> first call")
        for e in m:
            print(f"    {e:17s} " + "  ".join(f"{c}={m[e][c]}" for c in COLUMNS))
        errors[cfg] = sum(r[f"first_call_{cfg}"] != r["expected"] for r in r_rows)
        print(f"    routing errors: {errors[cfg]} of {len(r_rows)} = {errors[cfg] / len(r_rows):.0%}")

    a_rows = ablation()
    (REF / "position_ablation.jsonl").write_text("".join(json.dumps(r) + "\n" for r in a_rows), encoding="utf-8")
    print("Position ablation, 10 questions x 5 trials per position (synthetic)")
    print(f"  retrieval: right section retrieved in 10 of 10, first in {sum(HIT_AT_1)} of 10")
    acc = {}
    for pos in POSITIONS:
        acc[pos] = sum(r["correct"] for r in a_rows if r["of"] == 20 and r["position"] == pos)
        print(f"  position {pos:2d} of 20: {acc[pos]} of {QUESTIONS * TRIALS} correct")
    fix = sum(r["correct"] for r in a_rows if r["of"] == 5)
    print(f"  best 5, best first: {fix} of {QUESTIONS * TRIALS} correct")

    # The slides quote these numbers; the checks fail if the seed or the rates change them.
    m = confusion(r_rows, "before")
    assert [m["find_pilot_slots"][c] for c in COLUMNS] == [14, 6, 0], m
    assert [m["pilot_roster"][c] for c in COLUMNS] == [8, 12, 0], m
    assert errors == {"before": 14, "after": 2}, errors
    assert acc == {1: 44, 5: 41, 10: 24, 15: 30, 20: 42}, acc
    assert fix == 46, fix
    assert all(r["gold_in_context"] for r in a_rows)
    print("checks passed")


if __name__ == "__main__":
    main()
