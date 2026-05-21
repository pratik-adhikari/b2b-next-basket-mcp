# Three-minute MCP Demo Script

## 0:00-0:30 Problem

"A next-basket model can produce useful reorder signals, but raw model output is not enough for a business workflow. A sales user does not want token sequences, ONNX details, or backend internals. They need a bounded, explainable account brief that is safe to review."

## 0:30-1:00 Why MCP

"MCP lets us expose this local capability as tools with structured arguments and structured responses. The model stays local. The client does not need direct database, dataset, or ONNX access. It only calls bounded tools such as `get_account_reorder_brief`."

## 1:00-1:30 Architecture

"The MCP client starts a stdio MCP server. `server.py` creates the FastMCP app and registers tools and resources. `mcp/tools.py` receives tool calls. It lazily loads the predictor only when a prediction-related tool is called. The backend adapter calls the local ONNX model and dataset. The business layer turns predicted tokens into a recommendation-only brief with readable items, timing, evidence summaries, reason codes, model signals, limitations, and safety boundaries."

## 1:30-2:00 Demo Command

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/mcp_sales_demo_client.py
```

What the client sends:

- `ListToolsRequest`
- `CallToolRequest` for `get_server_capabilities`
- `CallToolRequest` for `get_account_reorder_brief`

Example sales question:

```text
Give me a reorder brief for this account.
```

## 2:00-2:35 What the Server Returns

"The server returns a structured account reorder brief. The sales-facing output includes expected timing, likely items, a recommended action, talking points, evidence summary, limitations, and safety boundary."

Key fields to point out:

- `prediction.expected_timing`
- `prediction.readable_items`
- `sales_brief.recommended_action`
- `sales_brief.talking_points`
- `evidence.reason_codes`
- `evidence.model_signals`
- `evidence.limitations`
- `safety`

## 2:35-2:50 Safety Boundary

"This does not contact the customer. It does not place an order. It does not expose chain-of-thought. Instead, it exposes evidence summaries, reason codes, model signals, and limitations. A human must approve any business action."

## 2:50-3:00 Final Value Statement

"The value is not just prediction. The value is turning a local model capability into a clean MCP connector: bounded tools, structured responses, local-only protected assets, and a sales-ready brief that an AI assistant or MCP client can safely consume."

