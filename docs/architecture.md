# Architecture

## V1 scope

The V1 goal is to convert notebook-based model inference into a clean MCP server.

```text
scripts/demo_without_mcp.py
  ↓
src/b2b_next_basket_mcp/inference.py
  ↓
provided ONNX model + dataset + protected backend
```

For MCP:

```text
scripts/mcp_dev_client.py
  ↓ starts subprocess
src/b2b_next_basket_mcp/mcp_server.py
  ↓ calls
src/b2b_next_basket_mcp/inference.py
  ↓ calls
ONNX backend
```

## Files

- `inference.py`: loads protected backend, dataset, ONNX model, and performs next-basket generation.
- `token_utils.py`: converts model tokens into readable item names.
- `business_logic.py`: turns predictions into recommendation-only business actions.
- `mcp_server.py`: exposes MCP tools and a model-card resource.
- `scripts/demo_without_mcp.py`: fallback demo without MCP.
- `scripts/mcp_dev_client.py`: minimal MCP client for learning/testing.
