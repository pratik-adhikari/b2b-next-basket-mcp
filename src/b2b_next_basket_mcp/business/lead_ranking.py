from __future__ import annotations


NEAR_TERM_REORDER_PHRASES = (
    "0 day",
    "1 day",
    "4 day",
    "5 day",
    "6 day",
    "7 day",
    "1 week",
    "next order after 1 week",
)


def score_reorder_opportunity(
    readable_items: list[str],
    time_prediction: str | None,
    history_token_count: int,
    estimated_order_events: int,
) -> dict:
    score = 0
    reason_codes: list[str] = []
    scoring_notes: list[str] = [
        f"History contains {history_token_count} tokens.",
        f"History contains {estimated_order_events} estimated order events.",
    ]

    if time_prediction:
        score += 40
        reason_codes.append("TIMING_SIGNAL_PRESENT")
        scoring_notes.append("Timing signal present in model output.")

        normalized_timing = time_prediction.lower()
        if any(phrase in normalized_timing for phrase in NEAR_TERM_REORDER_PHRASES):
            score += 30
            reason_codes.append("NEAR_TERM_REORDER_SIGNAL")
            scoring_notes.append("Timing signal suggests a near-term reorder.")

    if len(readable_items) >= 3:
        score += 20
        reason_codes.append("PREDICTED_ITEMS_AVAILABLE")
        scoring_notes.append("Model output includes at least three readable items.")

    if estimated_order_events >= 10:
        score += 10
        reason_codes.append("SUFFICIENT_HISTORY_AVAILABLE")
        scoring_notes.append("Sample history includes enough repeated order events for this demo heuristic.")

    if not readable_items:
        score -= 20
        reason_codes.append("NO_CLEAR_ITEM_PREDICTION")
        scoring_notes.append("No clear readable item prediction was available.")

    return {
        "score": max(0, min(100, score)),
        "reason_codes": reason_codes,
        "scoring_notes": scoring_notes,
    }


def make_lead_evidence_summary(
    client_id: str,
    score: int,
    readable_items: list[str],
    time_prediction: str | None,
    reason_codes: list[str],
) -> str:
    item_preview = ", ".join(readable_items[:5]) if readable_items else "no clear item set"
    timing = time_prediction or "no explicit timing signal"
    reasons = ", ".join(reason_codes) if reason_codes else "no reason codes"
    return (
        f"Client {client_id} scored {score}/100 from demo reorder signals. "
        f"Timing: {timing}. Likely items: {item_preview}. Reason codes: {reasons}."
    )


def make_lead_limitations() -> list[str]:
    return [
        "Ranking is based on demo heuristics over model outputs.",
        "No calibrated probability or confidence score is exposed.",
        "Recommendations require human review before customer contact.",
        "The ranking uses local sample histories available in the demo dataset.",
    ]
