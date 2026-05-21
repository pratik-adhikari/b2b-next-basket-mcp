from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLIENT_ID = "nexus_lab_solutions"


def print_section(title: str) -> None:
    print(f"\n{title}")


def extract_tool_payload(result: Any) -> Any:
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured

    structured = getattr(result, "structured_content", None)
    if structured is not None:
        return structured

    content = getattr(result, "content", None)
    if not content:
        return None

    if len(content) == 1:
        text = getattr(content[0], "text", None)
        if text is not None:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text

    return [getattr(item, "text", str(item)) for item in content]


async def call_tool_payload(
    session: ClientSession,
    tool_name: str,
    arguments: dict[str, Any],
) -> Any:
    result = await session.call_tool(tool_name, arguments)
    payload = extract_tool_payload(result)
    if payload is None:
        raise RuntimeError(f"{tool_name} returned no structured content")
    return payload


def print_capabilities(capabilities: dict[str, Any]) -> None:
    print_section("SERVER CAPABILITIES")
    print(f"server_name: {capabilities['server_name']}")
    print(f"model_loading_behavior: {capabilities['model_loading_behavior']}")
    print(f"recommended_sales_tool: {capabilities['recommended_sales_tool']}")
    print("default_generation_parameters:")
    for key, value in capabilities["default_generation_parameters"].items():
        print(f"- {key}: {value}")
    print("safety_boundaries:")
    for key, value in capabilities["safety_boundaries"].items():
        print(f"- {key}: {value}")


def print_reorder_brief(brief: dict[str, Any]) -> None:
    prediction = brief["prediction"]
    sales_brief = brief["sales_brief"]
    evidence = brief.get("evidence", {})

    print_section("EXPECTED TIMING")
    print(prediction["expected_timing"] or "No explicit timing signal.")

    print_section("LIKELY ITEMS")
    for item in prediction["readable_items"]:
        print(f"- {item}")

    print_section("RECOMMENDED ACTION")
    print(sales_brief["recommended_action"])

    print_section("TALKING POINTS")
    for point in sales_brief.get("talking_points", []):
        print(f"- {point}")

    print_section("EVIDENCE SUMMARY")
    print(evidence.get("evidence_summary", "No evidence summary returned."))

    print_section("LIMITATIONS")
    for limitation in evidence.get("limitations", []):
        print(f"- {limitation}")

    print_section("SAFETY BOUNDARY")
    for key, value in brief["safety"].items():
        print(f"- {key}: {value}")


async def run_demo(client_id: str, show_json: bool) -> None:
    server_env = os.environ.copy()
    server_env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    server_env["B2B_MCP_SUPPRESS_BANNER"] = "1"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(PROJECT_ROOT / "scripts" / "run_mcp_server.py")],
        env=server_env,
    )

    with open(os.devnull, "w", encoding="utf-8") as server_errlog:
        async with stdio_client(server_params, errlog=server_errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools = await session.list_tools()
                print("TOOLS")
                print(f"available_tool_count: {len(tools.tools)}")
                print("recommended_sales_tool: get_account_reorder_brief")

                capabilities = await call_tool_payload(session, "get_server_capabilities", {})
                print_capabilities(capabilities)

                print_section("SALES QUESTION")
                print(f'"Give me a reorder brief for {client_id}."')

                brief = await call_tool_payload(
                    session,
                    "get_account_reorder_brief",
                    {
                        "client_id": client_id,
                        "detail_level": "sales_summary",
                        "include_raw_tokens": False,
                        "include_evidence": True,
                        "include_talking_points": True,
                    },
                )
                print_reorder_brief(brief)

                if show_json:
                    print_section("RAW JSON")
                    print(json.dumps(brief, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the short sales-facing MCP demo.")
    parser.add_argument("--client-id", default=DEFAULT_CLIENT_ID)
    parser.add_argument("--json", action="store_true", help="Print the full raw JSON response.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(run_demo(client_id=args.client_id, show_json=args.json))


if __name__ == "__main__":
    main()
