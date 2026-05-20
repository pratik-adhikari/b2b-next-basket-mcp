from __future__ import annotations

from b2b_next_basket_mcp.backend.predictor import OrderPredictor


def main() -> None:
    predictor = OrderPredictor()

    clients = predictor.list_clients()
    print(f"Loaded {len(clients)} clients")
    print("First 10 clients:")
    for client in clients[:10]:
        print(f"  - {client}")

    client_id = "nexus_lab_solutions" if "nexus_lab_solutions" in clients else clients[0]
    history = predictor.get_sample_history(client_id)

    print("\nSelected client:")
    print(client_id)

    print("\nSample history:")
    print(history)

    print("\nPrediction:")
    result = predictor.predict_next_basket(
        client_id=client_id,
        start_text=history,
        max_generate=20,
        top_k=20,
    )
    print(result)


if __name__ == "__main__":
    main()
