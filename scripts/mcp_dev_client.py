from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_CLIENT_ID = "nexus_lab_solutions"


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

    extracted: list[Any] = []
    for item in content:
        text = getattr(item, "text", None)
        if text is not None:
            try:
                extracted.append(json.loads(text))
            except json.JSONDecodeError:
                extracted.append(text)
            continue
        extracted.append(str(item))
    return extracted


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


async def main() -> None:
    """Run an end-to-end MCP demo against the local next-basket server."""
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

            clients = await call_tool_payload(session, "list_clients", {"limit": 5})
            print_section("CLIENTS")
            print(f"total_clients: {clients['total_clients']}")
            for client_id in clients["clients"]:
                print(f"- {client_id}")

            history_summary = await call_tool_payload(
                session,
                "get_sample_history",
                {"client_id": DEMO_CLIENT_ID},
            )
            print_section("HISTORY SUMMARY")
            print(f"client_id: {history_summary['client_id']}")
            print(f"total_tokens: {history_summary['total_tokens']}")
            print(
                f"estimated_order_events: {history_summary['estimated_order_events']}"
            )
            print(f"full_history_available: {history_summary['full_history_available']}")
            print("preview_start:")
            print(history_summary["preview_start"])
            print("recent_history:")
            print(history_summary["recent_history"])
            print(f"note: {history_summary['note']}")

            prediction_input = await call_tool_payload(
                session,
                "get_prediction_input_sample",
                {"client_id": DEMO_CLIENT_ID},
            )
            start_text = prediction_input["start_text"]
            print_section("PREDICTION INPUT STATUS")
            print(f"client_id: {prediction_input['client_id']}")
            print(f"total_tokens: {prediction_input['total_tokens']}")
            print("start_text_available: true")
            print(f"note: {prediction_input['note']}")

            prediction_args = {
                "client_id": DEMO_CLIENT_ID,
                "start_text": start_text,
                "max_generate": 20,
                "top_k": 20,
                "temperature": 1.0,
            }

            try:
                prediction = await call_tool_payload(
                    session,
                    "predict_next_basket",
                    prediction_args,
                )
            except Exception as exc:
                print_section("PREDICTED TOKENS")
                print(f"ERROR: {exc}")
                raise

            print_section("PREDICTED TOKENS")
            print(prediction["predicted_tokens"])

            print_section("READABLE ITEMS")
            for item in prediction["readable_items"]:
                print(f"- {item}")

            try:
                recommendation_result = await call_tool_payload(
                    session,
                    "recommend_next_action",
                    prediction_args,
                )
            except Exception as exc:
                print_section("RECOMMENDATION")
                print(f"ERROR: {exc}")
                raise

            recommendation = recommendation_result["recommendation"]
            print_section("RECOMMENDATION")
            print(recommendation["recommended_action"])

            print_section("SAFETY")
            print(recommendation["safety"])


if __name__ == "__main__":
    asyncio.run(main())
