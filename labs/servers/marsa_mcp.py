# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=2.3"]
# ///
"""The Marsa circular store as an MCP server (Lab 2.4 reference solution).

    uv run servers/marsa_mcp.py                  # stdio: a host launches it as a subprocess
    uv run servers/marsa_mcp.py --http 8765      # Streamable HTTP on http://127.0.0.1:8765/mcp

It exposes:
- tools: search_circulars(query, k) and get_circular(circular_id), read only;
- resources: the index `circulars://index` and each circular as `circular://TC-07`.
`mcp_test_client.py` holds the tests a server must pass.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LABS))  # port.py lives in labs/ and only uses the standard library

import port  # noqa: E402
from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError  # noqa: E402


def build() -> MCPServer:
    server = MCPServer("marsa-circulars", title="Marsa Ports Authority circulars", version="1.0.0", log_level="WARNING",
                       instructions="Tariff circulars of Marsa Ports Authority (fictional), English and Arabic. "
                                    "A superseded circular no longer applies: check its status.")
    p = port.Port()

    @server.tool()
    def search_circulars(query: str, k: int = 3) -> list[dict]:
        """Search the tariff circulars in English or Arabic. Returns passages with circular ID and status.

        Args:
            query: what you are looking for, e.g. "cancellation fee".
            k: how many passages, 1 to 5.
        """
        return p.search_circulars(query, k)

    @server.tool()
    def get_circular(circular_id: str) -> dict:
        """Read one whole circular by ID (TC-01 to TC-08).

        Args:
            circular_id: e.g. "TC-07".
        """
        try:
            return p.get_circular(circular_id)
        except port.ToolError as e:
            raise ToolError(str(e)) from e

    @server.resource("circulars://index", mime_type="text/markdown")
    def index() -> str:
        """Every circular with its ID, title and status."""
        return "\n".join(f"- {d['id']}: {d['title']} ({d['status']})" for d in port.load_circulars())

    @server.resource("circular://{circular_id}", mime_type="text/markdown")
    def circular(circular_id: str) -> str:
        """One circular, English then Arabic, e.g. circular://TC-07."""
        for d in port.load_circulars():
            if d["id"].lower() == circular_id.lower():
                return d["text"]
        raise ResourceNotFoundError(f"No circular {circular_id!r}. Read circulars://index.")

    return server


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--http", type=int, metavar="PORT", help="serve Streamable HTTP on this port instead of stdio")
    a = ap.parse_args()
    srv = build()
    if a.http:
        srv.run(transport="streamable-http", host="127.0.0.1", port=a.http)
    else:
        srv.run()
