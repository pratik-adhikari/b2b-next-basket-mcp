from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from b2b_next_basket_mcp.business_logic import make_sales_recommendation
from b2b_next_basket_mcp.inference import OrderPredictor
from b2b_next_basket_mcp.token_utils import (
    compact_token_preview,
    extract_time_prediction,
    readable_items_from_tokens,
    split_tokens,
)

mcp = FastMCP("b2b-next-basket-prediction")
ALLOWED_DETAIL_LEVELS = ("compact", "sales_summary", "technical_debug")

_predictor: OrderPredictor | None = None


def get_predictor() -> OrderPredictor:
    global _predictor
    # Lazy loading keeps MCP server import lightweight, avoids heavy model
    # construction during import, and improves direct Ctrl+C behavior.
    if _predictor is None:
        _predictor = OrderPredictor()
    return _predictor


@mcp.tool()
def get_server_capabilities() -> dict[str, Any]:
    """Describe this MCP server's tools, defaults, and safety boundaries."""
    return {
        "ok": True,
        "server_name": "b2b-next-basket-prediction",
        "purpose": (
            "Expose local next-basket prediction and recommendation capabilities "
            "through MCP tools for demos and learning."
        ),
        "model_loading_behavior": "Model and dataset load lazily on first prediction-related tool call.",
        "default_generation_parameters": {
            "max_generate": 20,
            "temperature": 1.0,
            "top_k": 20,
            "sensor_size": 128,
            "seed": 42,
        },
        "available_tools": [
            "list_clients",
            "get_sample_history",
            "get_prediction_input_sample",
            "predict_next_basket",
            "recommend_next_action",
            "get_account_reorder_brief",
            "get_server_capabilities",
        ],
        "recommended_sales_tool": "get_account_reorder_brief",
        "safety_boundaries": {
            "recommendation_only": True,
            "no_automatic_customer_contact": True,
            "no_automatic_order_placement": True,
            "no_raw_database_access": True,
            "human_approval_required": True,
        },
        "notes": [
            "stdout is reserved for MCP protocol in stdio mode",
            "direct server run waits for an MCP client",
            "model loads lazily on first prediction-related tool call",
        ],
    }


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
        "max_generate": 20,
        "temperature": 1.0,
        "top_k": 20,
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


def _make_talking_points(
    client_id: str,
    readable_items: list[str],
    time_prediction: str | None,
) -> list[str]:
    top_items = ", ".join(readable_items[:3]) if readable_items else "core replenishment needs"
    talking_points = [
        f"Open with a reorder check-in for account {client_id}.",
        f"Lead with likely replenishment areas: {top_items}.",
    ]
    if time_prediction:
        talking_points.append(f"Use the timing signal to frame urgency: {time_prediction}.")
    talking_points.append("Keep the conversation recommendation-only until a human confirms next steps.")
    return talking_points


def _make_reorder_safety() -> dict[str, bool]:
    return {
        "recommendation_only": True,
        "requires_human_approval": True,
        "can_contact_customer_automatically": False,
        "can_place_order_automatically": False,
    }


@mcp.tool()
def list_clients(limit: int = 20) -> dict[str, Any]:
    """List available B2B client IDs in the local demo dataset."""
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200.")
    predictor = get_predictor()
    clients = predictor.list_clients()
    return {
        "total_clients": len(clients),
        "clients": clients[:limit],
    }


@mcp.tool()
def get_sample_history(client_id: str) -> dict[str, Any]:
    """Return a compact summary of one sample historical order sequence."""
    predictor = get_predictor()
    history = predictor.get_sample_history(client_id)
    preview = compact_token_preview(history)
    return {
        "client_id": client_id,
        "total_tokens": preview["total_tokens"],
        "estimated_order_events": preview["estimated_order_events"],
        "preview_start": preview["preview_start"],
        "recent_history": preview["recent_history"],
        "full_history_available": False,
        "note": (
            "Sample history is intentionally compact for demos. "
            "Use the full raw sequence internally when passing history into prediction."
        ),
    }


@mcp.tool()
def get_prediction_input_sample(client_id: str) -> dict[str, Any]:
    """Return full raw history for dev/demo prediction input, not normal display output."""
    predictor = get_predictor()
    history = predictor.get_sample_history(client_id)
    return {
        "client_id": client_id,
        "start_text": history,
        "total_tokens": len(split_tokens(history)),
        "note": (
            "This full raw sequence exists only to seed prediction during local demos "
            "and development. Prefer get_sample_history for readable display output."
        ),
    }


@mcp.tool()
def predict_next_basket(
    client_id: str,
    start_text: str,
    max_generate: int = 30,
    temperature: float = 1.0,
    top_k: int = 20,
) -> dict[str, Any]:
    """Predict the next likely B2B order basket for a selected client."""
    predictor = get_predictor()
    result = predictor.predict_next_basket(
        client_id=client_id,
        start_text=start_text,
        max_generate=max_generate,
        temperature=temperature,
        top_k=top_k,
    )

    readable_items = readable_items_from_tokens(result["predicted_tokens"])
    time_prediction = extract_time_prediction(result["predicted_tokens"])

    return {
        **result,
        "time_prediction": time_prediction,
        "readable_items": readable_items,
        "note": "Prediction generated by local ONNX backend. This is not an automatic order.",
    }


@mcp.tool()
def recommend_next_action(
    client_id: str,
    start_text: str,
    max_generate: int = 30,
    temperature: float = 1.0,
    top_k: int = 20,
) -> dict[str, Any]:
    """Predict the next basket and convert it into a safe sales recommendation."""
    prediction = predict_next_basket(
        client_id=client_id,
        start_text=start_text,
        max_generate=max_generate,
        temperature=temperature,
        top_k=top_k,
    )

    recommendation = make_sales_recommendation(
        client_id=client_id,
        readable_items=prediction["readable_items"],
        time_prediction=prediction["time_prediction"],
    )

    return {
        "prediction": prediction,
        "recommendation": recommendation,
    }


@mcp.tool()
def get_account_reorder_brief(
    client_id: str,
    detail_level: str = "sales_summary",
    include_raw_tokens: bool = False,
    include_evidence: bool = True,
    include_talking_points: bool = True,
) -> dict[str, Any]:
    """Return one sales-facing reorder brief for an account using the MCP interface layer."""
    if detail_level not in ALLOWED_DETAIL_LEVELS:
        return {
            "ok": False,
            "error": {
                "type": "ValidationError",
                "message": f"Invalid detail_level '{detail_level}'.",
                "allowed_values": list(ALLOWED_DETAIL_LEVELS),
            },
        }

    predictor = get_predictor()
    history = predictor.get_sample_history(client_id)
    history_tokens = split_tokens(history)
    history_preview = compact_token_preview(history)
    prediction = predictor.predict_next_basket(
        client_id=client_id,
        start_text=history,
        max_generate=20,
        temperature=1.0,
        top_k=20,
    )
    readable_items = readable_items_from_tokens(prediction["predicted_tokens"])
    time_prediction = extract_time_prediction(prediction["predicted_tokens"])
    recommendation = make_sales_recommendation(
        client_id=client_id,
        readable_items=readable_items,
        time_prediction=time_prediction,
    )

    reason_codes = _make_reason_codes(
        readable_items=readable_items,
        time_prediction=time_prediction,
        history_token_count=len(history_tokens),
    )
    evidence = {
        "reason_codes": reason_codes,
        "evidence_summary": _make_evidence_summary(
            readable_items=readable_items,
            time_prediction=time_prediction,
            history_preview=history_preview,
        ),
        "model_signals": _make_model_signals(
            prediction={
                **prediction,
                "readable_items": readable_items,
            },
            time_prediction=time_prediction,
            history_token_count=len(history_tokens),
        ),
        "limitations": _make_limitations(),
    }
    talking_points = _make_talking_points(client_id, readable_items, time_prediction)
    summary = (
        f"Account {client_id} shows a likely reorder opportunity"
        f"{f' around {time_prediction}' if time_prediction else ''} "
        f"with likely items: {', '.join(readable_items[:5]) if readable_items else 'no clear item set'}."
    )
    safety = _make_reorder_safety()

    if detail_level == "compact":
        return {
            "ok": True,
            "client_id": client_id,
            "expected_timing": time_prediction,
            "readable_items": readable_items,
            "recommended_action": recommendation["recommended_action"],
            "safety": safety,
        }

    prediction_block: dict[str, Any] = {
        "expected_timing": time_prediction,
        "readable_items": readable_items,
    }
    if include_raw_tokens:
        prediction_block["raw_tokens"] = prediction["predicted_tokens"]

    sales_brief: dict[str, Any] = {
        "summary": summary,
        "recommended_action": recommendation["recommended_action"],
    }
    if include_talking_points:
        sales_brief["talking_points"] = talking_points

    if detail_level == "sales_summary":
        response: dict[str, Any] = {
            "ok": True,
            "client_id": client_id,
            "detail_level": detail_level,
            "prediction": prediction_block,
            "sales_brief": sales_brief,
            "safety": safety,
        }
        if include_evidence:
            response["evidence"] = evidence
        return response

    debug_response: dict[str, Any] = {
        "ok": True,
        "client_id": client_id,
        "detail_level": detail_level,
        "history_token_count": len(history_tokens),
        "prediction": {
            "expected_timing": time_prediction,
            "readable_items": readable_items,
            "raw_tokens": prediction["predicted_tokens"],
            "generation_parameters": prediction.get(
                "generation_parameters",
                _generation_parameters_fallback(),
            ),
        },
        "sales_brief": sales_brief,
        "evidence": evidence,
        "safety": safety,
    }
    return debug_response


@mcp.resource("b2b://model-card/next-basket-prediction")
def model_card() -> str:
    return """
    Model: B2B next-basket order prediction

    Purpose:
    Predict likely next products/items for a selected B2B client based on historical order-token sequences.

    Inputs:
    - client_id
    - historical order sequence
    - generation parameters such as top_k and temperature

    Outputs:
    - predicted product tokens
    - readable item names
    - optional timing token
    - safe sales recommendation

    Safety:
    - This server provides recommendation-only output.
    - It does not place orders.
    - It does not contact customers.
    - Human approval is required before business action.
    """


def main() -> None:
    # Stdio MCP servers may appear idle when run directly because they wait
    # for protocol messages from a client on stdin/stdout.
    mcp.run()


if __name__ == "__main__":
    main()
