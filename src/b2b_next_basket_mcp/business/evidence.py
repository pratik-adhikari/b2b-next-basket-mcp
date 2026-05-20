from __future__ import annotations

from typing import Any

from b2b_next_basket_mcp.config import (
    DEFAULT_MAX_GENERATE,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
)


def _make_reason_codes(
    readable_items: list[str],
    time_prediction: str | None,
    history_token_count: int,
) -> list[str]:
    reason_codes = ["ACCOUNT_HISTORY_AVAILABLE", "MODEL_GENERATED_REORDER_SIGNAL"]
    if history_token_count > 0:
        reason_codes.append("HISTORY_SEQUENCE_USED")
    if readable_items:
        reason_codes.append("PREDICTED_ITEMS_AVAILABLE")
    else:
        reason_codes.append("NO_CLEAR_ITEM_PREDICTION")
    if time_prediction:
        reason_codes.append("TIMING_SIGNAL_PRESENT")
    return reason_codes


def _make_evidence_summary(
    readable_items: list[str],
    time_prediction: str | None,
    history_preview: dict[str, str | int],
) -> str:
    item_preview = ", ".join(readable_items[:5]) if readable_items else "no clear item set"
    timing_part = time_prediction or "no explicit timing token"
    return (
        f"Brief built from a sample account history with "
        f"{history_preview['estimated_order_events']} estimated order events and "
        f"{history_preview['total_tokens']} total tokens. Model surfaced {item_preview} "
        f"with timing signal: {timing_part}."
    )


def _generation_parameters_fallback() -> dict[str, Any]:
    return {
        "max_generate": DEFAULT_MAX_GENERATE,
        "temperature": DEFAULT_TEMPERATURE,
        "top_k": DEFAULT_TOP_K,
        "source": "account_brief_defaults",
    }


def _make_model_signals(
    prediction: dict[str, Any],
    time_prediction: str | None,
    history_token_count: int,
) -> dict[str, Any]:
    return {
        "history_token_count": history_token_count,
        "predicted_token_count": len(prediction["predicted_tokens"]),
        "time_signal_present": time_prediction is not None,
        "generated_item_count": len(prediction["readable_items"]),
        "generation_parameters": prediction.get(
            "generation_parameters",
            _generation_parameters_fallback(),
        ),
    }


def _make_limitations() -> list[str]:
    return [
        "This brief is based on one sample history sequence, not a full account review.",
        "The output is recommendation-only and does not place orders or contact customers.",
        "Readable item names are simplified token conversions and may need human interpretation.",
        "No calibrated probability or confidence score is exposed by this demo tool.",
    ]
