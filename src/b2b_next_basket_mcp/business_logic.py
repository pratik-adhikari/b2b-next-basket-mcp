from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def make_sales_recommendation(
    client_id: str,
    readable_items: list[str],
    time_prediction: str | None = None,
) -> dict:
    """
    Convert model output into a safe, business-readable recommendation.

    This layer is intentionally separate from inference: prediction is not the
    same thing as a business action.
    """
    if not readable_items:
        action = "No clear basket prediction. Review this customer manually."
        priority = "low"
    else:
        item_preview = ", ".join(readable_items[:5])
        action = (
            f"Prepare a replenishment offer for client '{client_id}' "
            f"including: {item_preview}."
        )
        priority = "medium"

    if time_prediction:
        action += f" Timing signal: {time_prediction}."

    return {
        "client_id": client_id,
        "recommended_action": action,
        "priority": priority,
        "safety": {
            "action_type": "recommendation_only",
            "requires_human_approval": True,
            "can_place_order_automatically": False,
            "can_contact_customer_automatically": False,
        },
        "audit": {
            "audit_id": str(uuid4()),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    }
