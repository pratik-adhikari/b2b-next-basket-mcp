from __future__ import annotations


LAB_SEGMENT = "lab supplies / scientific procurement"
GROCERY_SEGMENT = "grocery / consumer goods"
GENERAL_SEGMENT = "general B2B account"

LAB_KEYWORDS = (
    "lab",
    "goggles",
    "gloves",
    "solv",
    "reag",
    "acid",
    "flask",
    "condenser",
    "spatula",
    "stir",
    "vacuum",
    "chiller",
)

GROCERY_KEYWORDS = (
    "beer",
    "bread",
    "milk",
    "pork",
    "juice",
    "potato",
    "canned",
    "pasta",
    "cola",
    "wine",
    "deli",
    "nuts",
    "chicken",
)


def infer_account_segment(readable_items: list[str]) -> str:
    normalized_items = [item.lower() for item in readable_items]
    if any(keyword in item for item in normalized_items for keyword in LAB_KEYWORDS):
        return LAB_SEGMENT
    if any(keyword in item for item in normalized_items for keyword in GROCERY_KEYWORDS):
        return GROCERY_SEGMENT
    return GENERAL_SEGMENT


def make_display_name(client_id: str, segment: str) -> str:
    if client_id == "nexus_lab_solutions":
        return "Nexus Lab Solutions"
    if segment == LAB_SEGMENT:
        return f"Lab Account {client_id}"
    if segment == GROCERY_SEGMENT:
        return f"Grocery Account {client_id}"
    return f"Account {client_id}"


def make_priority_label(score: int, time_prediction: str | None) -> str:
    if score >= 90:
        return "high"
    if score >= 70:
        return "medium"
    return "low"


def make_recommended_next_step(
    display_name: str,
    readable_items: list[str],
    time_prediction: str | None,
    priority: str,
) -> str:
    item_preview = ", ".join(readable_items[:3]) if readable_items else "the predicted reorder categories"
    timing = f" Timing signal: {time_prediction}." if time_prediction else ""

    if priority == "high":
        return f"Review {display_name} and prepare a replenishment proposal for {item_preview}.{timing}"
    if priority == "medium":
        return f"Queue {display_name} for sales follow-up around {item_preview}.{timing}"
    return f"Monitor {display_name}; do not prioritize outreach until stronger reorder signals appear.{timing}"


def make_sales_talk_track(
    display_name: str,
    readable_items: list[str],
    time_prediction: str | None,
) -> list[str]:
    item_preview = ", ".join(readable_items[:3]) if readable_items else "recent reorder needs"
    timing = time_prediction or "the next expected reorder window"
    return [
        f"Open with a reorder check-in for {display_name}.",
        f"Mention likely needs around {item_preview} and timing signal: {timing}.",
        "Ask for human confirmation before any customer contact or order action.",
    ]
