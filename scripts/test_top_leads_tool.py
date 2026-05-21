from __future__ import annotations

from b2b_next_basket_mcp.mcp.tools import get_top_reorder_leads


def main() -> None:
    result = get_top_reorder_leads(limit=5, max_clients_to_scan=10)

    print(f"returned_leads: {result['returned_leads']}")
    print(f"scanned_clients: {result['scanned_clients']}")
    for lead in result["leads"]:
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

    clamp_result = get_top_reorder_leads(limit=100, max_clients_to_scan=10)
    print("limit_clamp_check:")
    print(f"ok: {clamp_result['ok']}")
    print(f"requested_limit: {clamp_result['requested_limit']}")
    print(f"effective_limit: {clamp_result['effective_limit']}")
    print(f"max_allowed_limit: {clamp_result['max_allowed_limit']}")


if __name__ == "__main__":
    main()
