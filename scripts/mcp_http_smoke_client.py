from __future__ import annotations

import argparse
import json

import anyio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def run_smoke(url: str) -> None:
    async with streamablehttp_client(url) as (read_stream, write_stream, _get_session_id):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tool_names = [tool.name for tool in tools_result.tools]
            print("tools:")
            for name in tool_names:
                print(f"- {name}")

            brief_result = await session.call_tool(
                "get_account_reorder_brief",
                {
                    "client_id": "nexus_lab_solutions",
                    "detail_level": "compact",
                    "include_raw_tokens": False,
                    "include_evidence": True,
                    "include_talking_points": True,
                },
            )

            print("\nget_account_reorder_brief result:")
            print(json.dumps(brief_result.model_dump(mode="json"), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the network MCP server.")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8010/mcp",
        help="Streamable HTTP MCP endpoint URL.",
    )
    args = parser.parse_args()

    anyio.run(run_smoke, args.url)


if __name__ == "__main__":
    main()
