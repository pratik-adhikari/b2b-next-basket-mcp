from __future__ import annotations

from b2b_next_basket_mcp.business_logic import make_sales_recommendation
from b2b_next_basket_mcp.inference import OrderPredictor
from b2b_next_basket_mcp.utils.token_utils import (
    compact_token_preview,
    extract_time_prediction,
    readable_items_from_tokens,
)


def main() -> None:
    predictor = OrderPredictor()
    clients = predictor.list_clients()
    client_id = "nexus_lab_solutions" if "nexus_lab_solutions" in clients else clients[0]

    history = predictor.get_sample_history(client_id)
    history_preview = compact_token_preview(history)
    prediction = predictor.predict_next_basket(
        client_id=client_id,
        start_text=history,
        max_generate=20,
        top_k=20,
    )

    readable_items = readable_items_from_tokens(prediction["predicted_tokens"])
    time_prediction = extract_time_prediction(prediction["predicted_tokens"])
    recommendation = make_sales_recommendation(client_id, readable_items, time_prediction)

    print("CLIENT")
    print(client_id)

    print("\nHISTORY SUMMARY")
    print(f"total_tokens: {history_preview['total_tokens']}")
    print(f"estimated_order_events: {history_preview['estimated_order_events']}")
    print("preview_start:")
    print(history_preview["preview_start"])
    print("recent_history:")
    print(history_preview["recent_history"])

    print("\nPREDICTED TOKENS")
    print(prediction["predicted_tokens"])

    print("\nREADABLE ITEMS")
    for item in readable_items:
        print(f"- {item}")

    print("\nRECOMMENDATION")
    print(recommendation["recommended_action"])

    print("\nSAFETY")
    print(recommendation["safety"])


if __name__ == "__main__":
    main()
