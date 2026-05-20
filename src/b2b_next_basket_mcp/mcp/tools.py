from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from b2b_next_basket_mcp.backend.predictor import OrderPredictor
from b2b_next_basket_mcp.business.evidence import (
    _generation_parameters_fallback,
    _make_evidence_summary,
    _make_limitations,
    _make_model_signals,
    _make_reason_codes,
)
from b2b_next_basket_mcp.business.sales_brief import (
    _make_talking_points,
    make_sales_recommendation,
)
from b2b_next_basket_mcp.business.safety import _make_reorder_safety
from b2b_next_basket_mcp.config import (
    ALLOWED_DETAIL_LEVELS,
    DEFAULT_MAX_GENERATE,
    DEFAULT_SEED,
    DEFAULT_SENSOR_SIZE,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
    SERVER_NAME,
)
from b2b_next_basket_mcp.utils.token_utils import (
    compact_token_preview,
    extract_time_prediction,
    readable_items_from_tokens,
    split_tokens,
)

_predictor: OrderPredictor | None = None


def get_predictor() -> OrderPredictor:
    global _predictor
    # Lazy loading keeps MCP server import lightweight, avoids heavy model
    # construction during import, and improves direct Ctrl+C behavior.
    if _predictor is None:
        _predictor = OrderPredictor()
    return _predictor


def get_server_capabilities() -> dict[str, Any]:
    """Describe this MCP server's tools, defaults, and safety boundaries."""
    return {
        "ok": True,
        "server_name": SERVER_NAME,
        "purpose": (
            "Expose local next-basket prediction and recommendation capabilities "
            "through MCP tools for demos and learning."
        ),
        "model_loading_behavior": "Model and dataset load lazily on first prediction-related tool call.",
        "default_generation_parameters": {
            "max_generate": DEFAULT_MAX_GENERATE,
            "temperature": DEFAULT_TEMPERATURE,
            "top_k": DEFAULT_TOP_K,
            "sensor_size": DEFAULT_SENSOR_SIZE,
            "seed": DEFAULT_SEED,
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


def predict_next_basket(
    client_id: str,
    start_text: str,
    max_generate: int = 30,
    temperature: float = DEFAULT_TEMPERATURE,
    top_k: int = DEFAULT_TOP_K,
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


def recommend_next_action(
    client_id: str,
    start_text: str,
    max_generate: int = 30,
    temperature: float = DEFAULT_TEMPERATURE,
    top_k: int = DEFAULT_TOP_K,
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


def get_account_reorder_brief(
    client_id: str,
    detail_level: str = ALLOWED_DETAIL_LEVELS[1],
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
        max_generate=DEFAULT_MAX_GENERATE,
        temperature=DEFAULT_TEMPERATURE,
        top_k=DEFAULT_TOP_K,
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

    if detail_level == ALLOWED_DETAIL_LEVELS[0]:
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

    if detail_level == ALLOWED_DETAIL_LEVELS[1]:
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


def register_tools(mcp: FastMCP) -> None:
    mcp.tool()(get_server_capabilities)
    mcp.tool()(list_clients)
    mcp.tool()(get_sample_history)
    mcp.tool()(get_prediction_input_sample)
    mcp.tool()(predict_next_basket)
    mcp.tool()(recommend_next_action)
    mcp.tool()(get_account_reorder_brief)
