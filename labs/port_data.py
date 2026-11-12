"""Generate the Marsa Ports Authority course data (deterministic, synthetic, offline).

    uv run python port_data.py          # writes data/port.sqlite

The circulars (data/circulars/*.md) and the task files (data/tasks/*.jsonl) are hand-written and committed.
This script builds the operational database: berths, vessels, shipping agents, bookings with their contact
persons (synthetic personal data, classified Restricted by TC-05) and an empty audit log.
The course clock is fixed at Sunday 1 November 2026, so every lab sees the same "today".

Planted problems (the answer key for the trainer):
- V-108 Najm Coral fits B03 by length but leaves 0.8 m under the keel (TC-03 asks for 1.0 m); the booking
  service accepts it, find_windows does not (Lab 3.3).
- TC-02 (old berth hire) is superseded by TC-07 from 1 October 2026: 52,000 GT for 3 days is SAR 15,600, not 12,480.
- BK-24030 belongs to Sahil Feeders: Najm's agent code must not read or cancel it.
- BK-24029 carries dangerous goods: any change needs the duty harbour master (TC-06, Lab 4.1).
"""

from __future__ import annotations

import json
import random
import sqlite3
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
DB_PATH = DATA / "port.sqlite"
SEED = 2027

BERTHS = [  # berth_id, kind, length_m, depth_m
    ("B01", "container", 350, 16.0), ("B02", "container", 300, 14.5), ("B03", "container", 250, 13.0),
    ("B04", "general", 220, 12.0), ("B05", "dry_bulk", 280, 15.0), ("B06", "dry_bulk", 200, 11.5),
    ("B07", "ro_ro", 230, 10.5), ("B08", "tanker", 260, 17.0),
]
AGENTS = [  # agent_code, company, company_ar
    ("NJM-4417", "Najm Lines", "خطوط نجم"), ("SHL-2290", "Sahil Feeders", "ساحل للسفن المغذية"),
    ("RML-8805", "Rimal Bulk", "رمال للبضائع السائبة"),
]
VESSELS = [  # vessel_id, name, kind, loa_m, draft_m, gross_tonnage, agent_code
    ("V-103", "Najm Sky", "container", 280, 13.8, 47000, "NJM-4417"),
    ("V-104", "Najm Horizon", "container", 294, 13.2, 52000, "NJM-4417"),
    ("V-105", "Sahil Wave", "container", 200, 10.5, 22000, "SHL-2290"),
    ("V-106", "Najm Dune", "container", 300, 14.0, 61000, "NJM-4417"),
    ("V-107", "Najm Pearl", "container", 210, 10.8, 28500, "NJM-4417"),
    ("V-108", "Najm Coral", "container", 225, 12.2, 33000, "NJM-4417"),
    ("V-109", "Sahil Gulf", "container", 230, 11.0, 30000, "SHL-2290"),
    ("V-110", "Najm Falcon", "container", 255, 12.4, 39000, "NJM-4417"),
    ("V-201", "Sahil Ferry", "ro_ro", 180, 7.5, 15000, "SHL-2290"),
    ("V-202", "Sahil Breeze", "ro_ro", 140, 8.1, 8400, "SHL-2290"),
    ("V-301", "Rimal Trader", "general", 170, 9.0, 12000, "RML-8805"),
    ("V-302", "Rimal Bulker", "dry_bulk", 250, 13.6, 45000, "RML-8805"),
    ("V-303", "Rimal Grain", "dry_bulk", 175, 10.0, 18000, "RML-8805"),
    ("V-401", "Sahil Tide", "tanker", 230, 12.5, 36000, "SHL-2290"),
]
BOOKINGS = [  # booking_id, vessel_id, berth_id, arrival, days, status, dangerous_goods
    ("BK-24017", "V-104", "B01", "2026-11-04", 3, "confirmed", 0),
    ("BK-24018", "V-105", "B01", "2026-11-07", 4, "confirmed", 0),
    ("BK-24019", "V-103", "B02", "2026-11-03", 4, "confirmed", 0),
    ("BK-24020", "V-109", "B02", "2026-11-12", 2, "cancelled", 0),
    ("BK-24021", "V-107", "B03", "2026-11-09", 2, "confirmed", 0),
    ("BK-24022", "V-108", "B03", "2026-11-03", 2, "confirmed", 0),
    ("BK-24023", "V-301", "B04", "2026-11-05", 3, "confirmed", 0),
    ("BK-24024", "V-302", "B05", "2026-11-02", 5, "confirmed", 0),
    ("BK-24025", "V-106", "B01", "2026-11-11", 3, "confirmed", 0),
    ("BK-24026", "V-109", "B02", "2026-11-09", 2, "confirmed", 0),
    ("BK-24027", "V-303", "B06", "2026-11-12", 4, "confirmed", 0),
    ("BK-24028", "V-201", "B07", "2026-11-06", 1, "confirmed", 0),
    ("BK-24029", "V-401", "B08", "2026-11-08", 3, "confirmed", 1),
    ("BK-24030", "V-202", "B07", "2026-11-02", 2, "confirmed", 0),
]
FIRST = ["Faisal", "Noura", "Majed", "Lama", "Turki", "Hessa", "Nawaf", "Dana", "Bandar", "Asma"]
LAST = ["Al-Otaibi", "Al-Shehri", "Al-Zahrani", "Al-Ghamdi", "Al-Mutairi", "Al-Subaie", "Al-Malki", "Al-Anazi"]


def build(path: Path = DB_PATH) -> Path:
    rng = random.Random(SEED)
    path.unlink(missing_ok=True)
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE berths (berth_id TEXT PRIMARY KEY, kind TEXT, length_m INT, depth_m REAL);
    CREATE TABLE agents (agent_code TEXT PRIMARY KEY, company TEXT, company_ar TEXT);
    CREATE TABLE vessels (vessel_id TEXT PRIMARY KEY, name TEXT, kind TEXT, loa_m INT, draft_m REAL,
                          gross_tonnage INT, agent_code TEXT);
    CREATE TABLE bookings (booking_id TEXT PRIMARY KEY, vessel_id TEXT, berth_id TEXT, arrival TEXT, days INT,
                           status TEXT, dangerous_goods INT, agent_code TEXT, contact_name TEXT,
                           contact_mobile TEXT, contact_email TEXT, created TEXT);
    CREATE TABLE audit_log (at TEXT, actor TEXT, action TEXT, detail TEXT);
    """)
    con.executemany("INSERT INTO berths VALUES (?,?,?,?)", BERTHS)
    con.executemany("INSERT INTO agents VALUES (?,?,?)", AGENTS)
    con.executemany("INSERT INTO vessels VALUES (?,?,?,?,?,?,?)", VESSELS)
    owner = {v[0]: v[6] for v in VESSELS}
    for b in BOOKINGS:
        first, last = rng.choice(FIRST), rng.choice(LAST)
        mobile = "05" + "".join(str(rng.randint(0, 9)) for _ in range(8))
        email = f"{first.lower()}.{last.lower().replace('al-', '')}@{owner[b[1]][:3].lower()}-shipping.example"
        con.execute("INSERT INTO bookings VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (*b[:5], b[5], b[6], owner[b[1]], f"{first} {last}", mobile, email, "2026-10-20"))
    con.commit()
    con.close()
    return path


if __name__ == "__main__":
    print("wrote", build())
    print(json.dumps({"berths": len(BERTHS), "vessels": len(VESSELS), "bookings": len(BOOKINGS)}))
