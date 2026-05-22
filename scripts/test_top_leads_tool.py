from __future__ import annotations

import json
from typing import Any

from b2b_next_basket_mcp.mcp.tools import get_top_reorder_leads


def print_leads(label: str, result: dict[str, Any]) -> None:
    print(label)
    print(f"scan_mode: {result['scan_mode']}")
    print(f"scanned_clients: {result['scanned_clients']}")
    print(f"total_available_clients: {result['total_available_clients']}")
    print(f"generation_settings: {json.dumps(result['generation_settings'], sort_keys=True)}")
    print(f"runtime_note: {result['runtime_note']}")
    for lead in result["leads"][:3]:
        items = ", ".join(lead["likely_items"][:5]) if lead["likely_items"] else "none"
        print(
            f"rank={lead['rank']} "
            f"client_id={lead['client_id']} "
            f"display_name={lead['display_name']} "
            f"segment={lead['segment']} "
            f"priority={lead['priority']} "
            f"score={lead['score']} "
            f"timing={lead['expected_timing']} "
            f"items={items} "
            f"next_step={lead['recommended_next_step']}"
        )
    print()


def main() -> None:
    limited_result = get_top_reorder_leads(
        limit=3,
        scan_mode="limited",
        max_clients_to_scan=10,
        ranking_profile="balanced",
    )
    print_leads("fast_limited_scan", limited_result)

    full_result = get_top_reorder_leads(
        limit=3,
        scan_mode="all",
        ranking_profile="conservative",
    )
    print_leads("full_scan", full_result)

    override_result = get_top_reorder_leads(
        limit=3,
        scan_mode="limited",
        max_clients_to_scan=10,
        temperature=1.2,
        top_k=30,
        max_generate=25,
    )
    print_leads("explicit_override_scan", override_result)


if __name__ == "__main__":
    main()
