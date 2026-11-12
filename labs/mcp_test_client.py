"""The provided test client for Lab 2.4: the checks a circular-store MCP server must pass.

    import mcp_test_client
    results = mcp_test_client.run(server)      # server: an MCPServer object, stdio parameters or a URL
    mcp_test_client.report(results)

Each check discovers or calls the server only through the protocol, never through Python imports.
"""

from __future__ import annotations

import json

import agentkit as K


def run(server) -> list[tuple[str, bool, str]]:
    out = []

    def check(name, fn):
        try:
            ok, detail = fn()
        except Exception as e:  # noqa: BLE001 - a crash is a failed check
            ok, detail = False, f"{type(e).__name__}: {e}"
        out.append((name, bool(ok), str(detail)[:160]))

    with K.MCPBridge(server) as mcp:
        tools = {t.name: t for t in mcp.list_tools()}
        check("discovers search_circulars and get_circular",
              lambda: ({"search_circulars", "get_circular"} <= set(tools), sorted(tools)))
        check("each tool has a description and a typed input schema",
              lambda: (all(t.description and t.input_schema.get("properties") for t in tools.values()), "ok"))
        check("get_circular TC-07 returns the rate in force",
              lambda: (lambda r: (not r.is_error and "0.10" in K.mcp_result_text(r), K.mcp_result_text(r)[:80]))(
                  mcp.call("get_circular", {"circular_id": "TC-07"})))
        check("an unknown circular is an error result, not a crash",
              lambda: (lambda r: (r.is_error and "TC-" in K.mcp_result_text(r), K.mcp_result_text(r)[:80]))(
                  mcp.call("get_circular", {"circular_id": "TC-99"})))
        check("an Arabic query finds the amendment circular",
              lambda: (lambda r: ("TC-06" in K.mcp_result_text(r), K.mcp_result_text(r)[:80]))(
                  mcp.call("search_circulars", {"query": "رسم تعديل الحجز", "k": 3})))
        check("results carry the circular's status",
              lambda: (lambda r: ("superseded" in K.mcp_result_text(r), "status present"))(
                  mcp.call("search_circulars", {"query": "berth hire per gross ton", "k": 3})))
        check("the index resource lists eight circulars",
              lambda: (lambda t: (t.count("TC-") >= 8, f"{t.count('TC-')} IDs"))(
                  mcp.read_resource("circulars://index").contents[0].text))
        check("a circular resource reads by ID",
              lambda: (lambda t: ("1.0" in t, t[:60]))(mcp.read_resource("circular://TC-03").contents[0].text))
    return out


def report(results) -> int:
    for name, ok, detail in results:
        print(("✅ " if ok else "❌ ") + name + ("" if ok else f"  ({detail})"))
    passed = sum(ok for _, ok, _ in results)
    print(f"{passed} of {len(results)} checks passed")
    return passed


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(K.LABS / "servers"))
    import marsa_mcp

    print(json.dumps(report(run(marsa_mcp.build()))))
