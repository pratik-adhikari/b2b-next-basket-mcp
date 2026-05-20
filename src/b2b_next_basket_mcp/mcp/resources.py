from __future__ import annotations

from mcp.server.fastmcp import FastMCP


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


def register_resources(mcp: FastMCP) -> None:
    mcp.resource("b2b://model-card/next-basket-prediction")(model_card)

