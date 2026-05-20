from __future__ import annotations


def _make_reorder_safety() -> dict[str, bool]:
    return {
        "recommendation_only": True,
        "requires_human_approval": True,
        "can_contact_customer_automatically": False,
        "can_place_order_automatically": False,
    }

