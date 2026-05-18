from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]


async def main() -> None:
    """Small learning client that starts the local MCP server over stdio."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(PROJECT_ROOT / "scripts" / "run_mcp_server.py")],
        env={"PYTHONPATH": str(PROJECT_ROOT / "src")},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("TOOLS")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            clients_result = await session.call_tool("list_clients", {"limit": 5})
            print("\nLIST CLIENTS RESULT")
            print(clients_result.content)

            # Extracting structured tool content varies slightly by SDK/client version.
            # Use a known demo client when available; otherwise ask the server for sample history manually.
            sample_result = await session.call_tool(
                "get_sample_history",
                {"client_id": "nexus_lab_solutions"},
            )
            print("\nSAMPLE HISTORY RESULT")
            print(sample_result.content)

            print(
                "\nIf this printed tool results, your MCP server/client path is working. "
                "For full interactive use, connect the server to an MCP-compatible host."
            )


if __name__ == "__main__":
    asyncio.run(main())
