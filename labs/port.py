"""Marsa Ports Authority: the course case study as three services of typed Python tools over SQLite.

- Schedule service: list_berths, get_vessel, berth_schedule, find_windows
- Tariff service: search_circulars, get_circular, compute_dues
- Booking service: get_booking, create_booking, amend_booking, cancel_booking (the last three write)

Every lab starts from a reference state: `Port(K.lab_dir("D1_4", reset=True))` copies a fresh database, so write
tools never change the shared data and no lab depends on another. Rules come from data/circulars (TC-01 to TC-08).
The course clock is fixed: Sunday 1 November 2026.
"""

from __future__ import annotations

import json
import math
import re
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

LABS = Path(__file__).resolve().parent
DATA = LABS / "data"
CIRCULARS = DATA / "circulars"
DB_TEMPLATE = DATA / "port.sqlite"
TODAY = date(2026, 11, 1)

BerthId = Literal["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08"]
KIND_OF_BERTH = {"B01": "container", "B02": "container", "B03": "container", "B04": "general", "B05": "dry_bulk",
                 "B06": "dry_bulk", "B07": "ro_ro", "B08": "tanker"}
MIN_UKC_M = 1.0  # TC-03 under-keel clearance
APPROVAL_FEE_DELTA = 10_000  # TC-06 (c)


class ToolError(Exception):
    """A tool failure the model should see and recover from (wrong ID, failed check, policy limit)."""


# ---------------------------------------------------------------- circulars
def load_circulars(folder: Path = CIRCULARS) -> list[dict]:
    """All circulars: id, title, title_ar, issued, status, text (markdown body, English then Arabic)."""
    docs = []
    for path in sorted(folder.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta, body = {}, raw
        if raw.startswith("---"):
            head, body = raw[3:].split("---", 1)
            meta = dict(line.split(": ", 1) for line in head.strip().splitlines())
        docs.append(dict(id=meta.get("id", path.stem), title=meta.get("title", path.stem), title_ar=meta.get("title_ar", ""),
                         issued=meta.get("issued", ""), status=meta.get("status", ""), file=path.name, text=body.strip()))
    return docs


def chunk_circulars(max_chars: int = 900) -> list[dict]:
    """Split each circular at headings (so English and Arabic become separate chunks), keeping its ID."""
    chunks = []
    for doc in load_circulars():
        for i, part in enumerate(p for p in re.split(r"\n(?=## |# )", doc["text"]) if p.strip()):
            chunks.append(dict(circular_id=doc["id"], title=doc["title"], status=doc["status"], text=part.strip()[:max_chars],
                               chunk_id=f"{doc['id']}#{i}"))
    return chunks


def keyword_search(query: str, k: int = 3) -> list[dict]:
    """A deliberately simple baseline: rank chunks by shared word prefixes. Lab 2.2 replaces it."""
    words = {w[:5] for w in re.findall(r"\w+", query.lower()) if len(w) > 2}
    scored = [(sum(c["text"].lower().count(w) for w in words), c) for c in chunk_circulars()]
    scored = [t for t in scored if t[0]]
    scored.sort(key=lambda t: -t[0])
    return [c for _, c in scored[:k]]


# ---------------------------------------------------------------- tariff (TC-04, TC-06, TC-07)
def berth_hire(gross_tonnage: int, days: int, dangerous_goods: bool = False) -> int:
    """TC-07 rate and minimum per day, then the TC-04 feeder discount, then the dangerous goods surcharge."""
    hire = max(1500.0, 0.10 * gross_tonnage) * days
    if gross_tonnage < 10_000:
        hire *= 0.85
    if dangerous_goods:
        hire *= 1.20
    return int(round(hire))


def _day(text: str, what: str) -> date:
    try:
        return date.fromisoformat(str(text).strip()[:10])
    except ValueError:
        raise ToolError(f"{what} must be a date written YYYY-MM-DD, for example 2026-11-07; got {text!r}.") from None


@dataclass
class Port:
    """One lab's private copy of the port database plus the tools Bosla can call.

    actor: who is acting (recorded in the audit log).
    """

    workdir: Path | str | None = None
    actor: str = "bosla"
    db_path: Path = field(init=False)

    READ_TOOLS = ("search_circulars", "get_circular", "list_berths", "get_vessel", "berth_schedule", "find_windows",
                  "compute_dues", "get_booking")
    WRITE_TOOLS = ("create_booking", "amend_booking", "cancel_booking")

    def __post_init__(self):
        if not DB_TEMPLATE.exists():
            import port_data  # noqa: PLC0415 - generate on first use (Colab, fresh clone)
            port_data.build()
        if self.workdir is None:
            self.db_path = DB_TEMPLATE
        else:
            self.workdir = Path(self.workdir)
            self.workdir.mkdir(parents=True, exist_ok=True)
            self.db_path = self.workdir / "port.sqlite"
            shutil.copy(DB_TEMPLATE, self.db_path)

    # -- plumbing
    def sql(self, query: str, params: tuple | dict = ()) -> list[dict]:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            rows = [dict(r) for r in con.execute(query, params)]
            con.commit()
            return rows
        finally:
            con.close()

    def _audit(self, action: str, detail: dict) -> None:
        self.sql("INSERT INTO audit_log VALUES (?,?,?,?)", (TODAY.isoformat(), self.actor, action, json.dumps(detail)))

    def _vessel(self, vessel: str) -> dict:
        key = vessel.strip()
        rows = self.sql("SELECT * FROM vessels WHERE vessel_id = ? OR lower(name) = lower(?)", (key.upper(), key))
        if not rows:
            raise ToolError(f"No vessel {vessel!r}. Use a vessel ID like V-110 or the vessel's exact name.")
        return rows[0]

    def _berth(self, berth_id: str) -> dict:
        rows = self.sql("SELECT * FROM berths WHERE berth_id = ?", (str(berth_id).strip().upper(),))
        if not rows:
            raise ToolError(f"No berth {berth_id!r}. Berths are B01 to B08.")
        return rows[0]

    def _owned(self, booking_id: str, agent_code: str) -> dict:
        rows = self.sql("SELECT b.*, v.name AS vessel, v.gross_tonnage, v.loa_m, v.draft_m FROM bookings b "
                        "JOIN vessels v USING (vessel_id) WHERE b.booking_id = ?", (str(booking_id).strip().upper(),))
        if not rows or rows[0]["agent_code"] != str(agent_code).strip().upper():
            raise ToolError("No booking with that ID for this agent code. Ask the agent to check both; do not say "
                            "whether the booking exists for another agent (TC-05).")
        return rows[0]

    def _busy(self, berth_id: str, start: date, days: int, ignore: str = "") -> list[str]:
        end = start + timedelta(days=days - 1)
        clash = []
        for b in self.sql("SELECT booking_id, arrival, days FROM bookings WHERE berth_id = ? AND status != 'cancelled' "
                          "AND booking_id != ?", (berth_id, ignore)):
            b_start = date.fromisoformat(b["arrival"])
            b_end = b_start + timedelta(days=b["days"] - 1)
            if b_start <= end and start <= b_end:
                clash.append(b["booking_id"])
        return clash

    # ================================================================ tariff service
    def search_circulars(self, query: str, k: int = 3) -> list[dict]:
        """Search the port's tariff circulars (berth hire, dangerous goods, fit rules, amendments, privacy).

        Works with English or Arabic queries. Returns passages with their circular ID and status (cite the ID;
        a superseded circular no longer applies).

        Args:
            query: what you are looking for, e.g. "cancellation fee" or "رسم التعديل".
            k: how many passages to return (1-5).
        """
        hits = keyword_search(query, k=max(1, min(int(k), 5)))
        if not hits:
            return [{"note": "No passage matched. Try other words, or read a circular by ID (TC-01 to TC-08)."}]
        return [{"circular_id": h["circular_id"], "status": h["status"], "text": h["text"]} for h in hits]

    def get_circular(self, circular_id: str) -> dict:
        """Read one whole circular by its ID.

        Args:
            circular_id: TC-01 to TC-08.
        """
        for d in load_circulars():
            if d["id"] == circular_id.strip().upper():
                return {k: d[k] for k in ("id", "title", "issued", "status", "text")}
        raise ToolError(f"No circular {circular_id!r}. IDs run from TC-01 to TC-08.")

    def compute_dues(self, gross_tonnage: int, days: int, dangerous_goods: bool = False) -> dict:
        """Berth hire in SAR under the tariff in force (TC-07 with TC-04). No agent code needed.

        Args:
            gross_tonnage: the vessel's gross tonnage (GT), a whole number.
            days: days at berth, 1 to 14.
            dangerous_goods: true when the booking declares dangerous goods (20% surcharge).
        """
        if not 1 <= int(days) <= 14:
            raise ToolError("days must be between 1 and 14 (TC-08).")
        if int(gross_tonnage) <= 0:
            raise ToolError("gross_tonnage must be a positive whole number, for example 39000.")
        return {"berth_hire_sar": berth_hire(int(gross_tonnage), int(days), bool(dangerous_goods)),
                "circulars": ["TC-07", "TC-04"]}

    # ================================================================ schedule service
    def list_berths(self) -> list[dict]:
        """List the eight berths with the kind of vessel each takes, its length and its depth in metres."""
        return self.sql("SELECT berth_id, kind, length_m, depth_m FROM berths ORDER BY berth_id")

    def get_vessel(self, vessel: str) -> dict:
        """Look up a vessel by ID or exact name: kind, length overall (loa_m), draft, gross tonnage, owning agent.

        Args:
            vessel: a vessel ID such as "V-110" or a name such as "Najm Falcon".
        """
        v = self._vessel(vessel)
        return {k: v[k] for k in ("vessel_id", "name", "kind", "loa_m", "draft_m", "gross_tonnage", "agent_code")}

    def berth_schedule(self, berth_id: str, date_from: str, date_to: str) -> list[dict]:
        """List the bookings that occupy a berth between two dates (inclusive). No contact data.

        Args:
            berth_id: B01 to B08.
            date_from: first date, YYYY-MM-DD.
            date_to: last date, YYYY-MM-DD.
        """
        b = self._berth(berth_id)
        start, end = _day(date_from, "date_from"), _day(date_to, "date_to")
        out = []
        for r in self.sql("SELECT booking_id, vessel_id, arrival, days, status FROM bookings WHERE berth_id = ? "
                          "AND status != 'cancelled' ORDER BY arrival", (b["berth_id"],)):
            a = date.fromisoformat(r["arrival"])
            last = a + timedelta(days=r["days"] - 1)
            if a <= end and start <= last:
                out.append({**r, "last_day": last.isoformat()})
        return out

    def find_windows(self, vessel_id: str, days: int, date_from: str, date_to: str) -> list[dict]:
        """Find the earliest free arrival date on every berth that fits the vessel (kind, length and under-keel
        clearance under TC-03), for a stay of `days` days starting between two dates.

        Args:
            vessel_id: e.g. "V-110".
            days: days at berth, 1 to 14.
            date_from: earliest arrival date, YYYY-MM-DD.
            date_to: latest arrival date, YYYY-MM-DD.
        """
        v = self._vessel(vessel_id)
        start, end = max(_day(date_from, "date_from"), TODAY + timedelta(days=1)), _day(date_to, "date_to")
        if not 1 <= int(days) <= 14:
            raise ToolError("days must be between 1 and 14 (TC-08).")
        out = []
        for b in self.list_berths():
            fits = (b["kind"] == v["kind"] and v["loa_m"] + 20 <= b["length_m"] and b["depth_m"] - v["draft_m"] >= MIN_UKC_M)
            if not fits:
                continue
            d = start
            while d <= end and self._busy(b["berth_id"], d, int(days)):
                d += timedelta(days=1)
            if d <= end:
                out.append({"berth_id": b["berth_id"], "arrival": d.isoformat(),
                            "under_keel_m": round(b["depth_m"] - v["draft_m"], 1)})
        if not out:
            return [{"note": "No fitting berth is free in that range. Try a later range or fewer days."}]
        return sorted(out, key=lambda w: w["arrival"])

    # ================================================================ booking service
    def get_booking(self, booking_id: str, agent_code: str) -> dict:
        """Read one booking for the shipping agent who owns it: vessel, berth, arrival, days, status, dues.

        Args:
            booking_id: e.g. "BK-24017".
            agent_code: the shipping agent's code, e.g. "NJM-4417".
        """
        b = self._owned(booking_id, agent_code)
        self._audit("get_booking", {"booking_id": b["booking_id"]})
        return {"booking_id": b["booking_id"], "vessel": b["vessel"], "vessel_id": b["vessel_id"], "berth_id": b["berth_id"],
                "arrival": b["arrival"], "days": b["days"], "status": b["status"],
                "dangerous_goods": bool(b["dangerous_goods"]),
                "berth_hire_sar": berth_hire(b["gross_tonnage"], b["days"], bool(b["dangerous_goods"]))}

    def create_booking(self, vessel_id: str, berth_id: str, arrival: str, days: int, agent_code: str,
                       dangerous_goods: bool = False) -> dict:
        """Create a berth booking. Writes to the schedule: confirm berth, arrival and days with the agent first.

        The service checks ownership, berth kind, length, lead time and overlaps. It does NOT check under-keel
        clearance: check TC-03 yourself first (find_windows does).

        Args:
            vessel_id: e.g. "V-110".
            berth_id: B01 to B08.
            arrival: arrival date, YYYY-MM-DD, 1 to 60 days after today.
            days: days at berth, 1 to 14.
            agent_code: the shipping agent's code; must own the vessel.
            dangerous_goods: true when the cargo includes dangerous goods.
        """
        v, b = self._vessel(vessel_id), self._berth(berth_id)
        if v["agent_code"] != str(agent_code).strip().upper():
            raise ToolError("This agent code does not act for that vessel. Ask the agent to check the code.")
        a = _day(arrival, "arrival")
        if not 1 <= (a - TODAY).days <= 60:
            raise ToolError(f"arrival must be 1 to 60 days after today ({TODAY.isoformat()}), see TC-08.")
        if not 1 <= int(days) <= 14:
            raise ToolError("days must be between 1 and 14 (TC-08).")
        if b["kind"] != v["kind"]:
            raise ToolError(f"{b['berth_id']} takes {b['kind']} vessels; {v['name']} is {v['kind']} (TC-03).")
        if v["loa_m"] + 20 > b["length_m"]:
            raise ToolError(f"{v['name']} ({v['loa_m']} m) is too long for {b['berth_id']} ({b['length_m']} m, TC-03).")
        clash = self._busy(b["berth_id"], a, int(days))
        if clash:
            raise ToolError(f"{b['berth_id']} is taken on those days by {', '.join(clash)}. Use find_windows.")
        n = 1 + max(int(r["booking_id"][3:]) for r in self.sql("SELECT booking_id FROM bookings"))
        bid = f"BK-{n}"
        self.sql("INSERT INTO bookings VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                 (bid, v["vessel_id"], b["berth_id"], a.isoformat(), int(days), "confirmed", int(bool(dangerous_goods)),
                  v["agent_code"], "", "", "", TODAY.isoformat()))
        self._audit("create_booking", {"booking_id": bid})
        return {"booking_id": bid, "vessel": v["name"], "berth_id": b["berth_id"], "arrival": a.isoformat(), "days": int(days),
                "status": "confirmed", "berth_hire_sar": berth_hire(v["gross_tonnage"], int(days), bool(dangerous_goods))}

    def amend_booking(self, booking_id: str, agent_code: str, arrival: str | None = None, berth_id: str | None = None,
                      days: int | None = None) -> dict:
        """Change a booking's arrival date, berth or days. Writes: confirm the change with the agent first.

        Charges SAR 500 when made less than 2 days before the current arrival date (TC-06).

        Args:
            booking_id: e.g. "BK-24021".
            agent_code: the shipping agent's code; must own the booking.
            arrival: new arrival date, YYYY-MM-DD (leave out to keep).
            berth_id: new berth, B01 to B08 (leave out to keep).
            days: new number of days, 1 to 14 (leave out to keep).
        """
        b = self._owned(booking_id, agent_code)
        if b["status"] == "cancelled":
            raise ToolError("That booking is cancelled; create a new one instead.")
        new_arrival = _day(arrival, "arrival") if arrival else date.fromisoformat(b["arrival"])
        new_berth = self._berth(berth_id)["berth_id"] if berth_id else b["berth_id"]
        new_days = int(days) if days else b["days"]
        if not 1 <= new_days <= 14:
            raise ToolError("days must be between 1 and 14 (TC-08).")
        clash = self._busy(new_berth, new_arrival, new_days, ignore=b["booking_id"])
        if clash:
            raise ToolError(f"{new_berth} is taken on those days by {', '.join(clash)}. Use find_windows.")
        fee = 500 if (date.fromisoformat(b["arrival"]) - TODAY).days < 2 else 0
        self.sql("UPDATE bookings SET arrival = ?, berth_id = ?, days = ? WHERE booking_id = ?",
                 (new_arrival.isoformat(), new_berth, new_days, b["booking_id"]))
        self._audit("amend_booking", {"booking_id": b["booking_id"], "fee_sar": fee})
        return {"booking_id": b["booking_id"], "berth_id": new_berth, "arrival": new_arrival.isoformat(), "days": new_days,
                "amendment_fee_sar": fee, "circular": "TC-06"}

    def cancel_booking(self, booking_id: str, agent_code: str) -> dict:
        """Cancel a booking. Writes and cannot be undone: confirm with the agent first.

        Free 3 or more days before arrival, otherwise 25% of the booking's berth hire (TC-06).

        Args:
            booking_id: e.g. "BK-24030".
            agent_code: the shipping agent's code; must own the booking.
        """
        b = self._owned(booking_id, agent_code)
        if b["status"] == "cancelled":
            raise ToolError("That booking is already cancelled.")
        hire = berth_hire(b["gross_tonnage"], b["days"], bool(b["dangerous_goods"]))
        fee = 0 if (date.fromisoformat(b["arrival"]) - TODAY).days >= 3 else int(round(hire * 0.25))
        self.sql("UPDATE bookings SET status = 'cancelled' WHERE booking_id = ?", (b["booking_id"],))
        self._audit("cancel_booking", {"booking_id": b["booking_id"], "fee_sar": fee})
        return {"booking_id": b["booking_id"], "status": "cancelled", "cancellation_fee_sar": fee, "circular": "TC-06"}

    # -- tool lists
    def tools(self, names: tuple[str, ...] | list[str] | None = None) -> list:
        """Bound methods for the named tools (default: all), ready for agentkit.tool_schema / run_agent."""
        return [getattr(self, n) for n in (names or self.READ_TOOLS + self.WRITE_TOOLS)]

    def is_write(self, name: str) -> bool:
        return name in self.WRITE_TOOLS


SYSTEM_PROMPT = """You are Bosla (بوصلة), the booking assistant of Marsa Ports Authority. You serve shipping agents.

- Answer from the tools and the circulars only; cite the circular ID (TC-xx) for every rule or fee. A superseded
  circular no longer applies: use the one in force.
- Quote dues with compute_dues; never do tariff arithmetic in your head.
- Bookings belong to the agent whose agent code is given. Never reveal another agent's bookings or contacts (TC-05).
- Before create_booking, amend_booking or cancel_booking, the agent must have asked for that exact change.
- Out of scope (customs, pilotage, weather, waivers): say so briefly and name the right office.
- Reply in the language of the question. Dates are YYYY-MM-DD. Today is 2026-11-01."""
