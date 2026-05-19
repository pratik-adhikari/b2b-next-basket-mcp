# MCP Anatomy

## What this project is really about

This project is not mainly about order prediction. The prediction model is only the backend capability.

The real learning goal is to understand how to expose an existing backend capability through MCP so that a client can discover tools, call them in a structured way, and receive machine-usable results.

In this repo:

```text
prediction backend = local capability
MCP server = interface layer
MCP client = caller
```

The model computes likely next-basket outputs. The MCP layer makes that capability callable by an MCP-aware client.

## MCP roles in this project

### MCP server

The MCP server lives in [src/b2b_next_basket_mcp/mcp_server.py](/home/pratik/Downloads/b2b-next-basket-mcp/b2b-next-basket-mcp-public/src/b2b_next_basket_mcp/mcp_server.py:1).

Its job is to:

- define tools
- validate or shape inputs
- call inference or business-logic functions
- return structured outputs

### MCP client

The MCP client in this repo is [scripts/mcp_dev_client.py](/home/pratik/Downloads/b2b-next-basket-mcp/b2b-next-basket-mcp-public/scripts/mcp_dev_client.py:1).

Its job is to:

- start or connect to the MCP server
- ask which tools are available
- call tools with arguments
- display the returned results

This is a development client for learning. It is not a production MCP host.

### MCP tool

An MCP tool is a callable server-side function exposed through the MCP protocol.

Examples in this project:

- `list_clients`
- `get_sample_history`
- `get_prediction_input_sample`
- `predict_next_basket`
- `recommend_next_action`

### MCP resource

An MCP resource is read-only contextual information exposed by the server.

This project currently includes a model-card style resource in [src/b2b_next_basket_mcp/mcp_server.py](/home/pratik/Downloads/b2b-next-basket-mcp/b2b-next-basket-mcp-public/src/b2b_next_basket_mcp/mcp_server.py:1):

- `b2b://model-card/next-basket-prediction`

Resources are useful for documentation and context. Tools are for actions or computations.

### B2B client/customer

A B2B client or customer is the business entity whose order history is being analyzed by the prediction backend.

This is not the same as the MCP client.

### MCP client vs B2B client/customer

This distinction matters:

```text
MCP client = software caller using the MCP protocol
B2B client/customer = business account inside the dataset/domain
```

In other words:

- the MCP client is the program making tool calls
- the B2B client/customer is the subject of those tool calls

## Runtime flow

The runtime flow in this project is:

```text
scripts/mcp_dev_client.py
  -> starts/connects to
MCP server
  -> exposes tools from mcp_server.py
  -> calls inference/business logic
  -> returns structured results
```

Step by step:

1. `scripts/mcp_dev_client.py` starts the local MCP server process or connects to it over stdio.
2. The MCP client sends a `ListToolsRequest`.
3. The server returns the available tools and their descriptions.
4. The client sends a `CallToolRequest` such as `list_clients` or `predict_next_basket`.
5. The server routes that tool call to the corresponding Python function in `mcp_server.py`.
6. That function may call inference code in [src/b2b_next_basket_mcp/inference.py](/home/pratik/Downloads/b2b-next-basket-mcp/b2b-next-basket-mcp-public/src/b2b_next_basket_mcp/inference.py:1) and/or business logic in [src/b2b_next_basket_mcp/business_logic.py](/home/pratik/Downloads/b2b-next-basket-mcp/b2b-next-basket-mcp-public/src/b2b_next_basket_mcp/business_logic.py:1).
7. The function returns a structured dictionary.
8. The server sends that result back to the MCP client.
9. The client prints or otherwise uses the returned data.

## Tool registration

Tool registration in this project happens through `@mcp.tool()`.

That decorator marks a normal Python function as MCP-callable. Once decorated, the function becomes visible to MCP clients through tool discovery.

Example pattern:

```python
@mcp.tool()
def list_clients(limit: int = 20) -> dict[str, Any]:
    ...
```

In this repo, the main tools are:

- `list_clients`
  - returns a structured list of available business client IDs
- `get_sample_history`
  - returns a compact, display-safe summary of sample history
- `get_prediction_input_sample`
  - returns full raw `start_text` for local dev/demo prediction input
- `predict_next_basket`
  - calls the inference layer and returns predicted tokens plus readable fields
- `recommend_next_action`
  - calls prediction first, then turns the result into a recommendation-only business action

The important idea is that MCP tools are not separate from Python code. They are normal Python functions with an MCP exposure layer on top.

## Why two history tools exist

Two history tools exist because the display use case and the prediction-input use case are different.

### `get_sample_history`

This tool returns:

- total token count
- estimated order-event count
- preview of the beginning
- recent history slice

It is meant for readable display during demos and exploration.

### `get_prediction_input_sample`

This tool returns the full raw history string as `start_text`.

It exists only so the development client can feed a valid raw sequence into `predict_next_basket` and `recommend_next_action`.

The full raw sequence should not be used as normal display output because it is too long and too noisy for human-readable demos.

## Tool output design

MCP tools should return structured JSON-style dictionaries instead of uncontrolled text dumps.

That choice improves:

- readability
  - fields such as `client_id`, `total_tokens`, and `readable_items` are easier to scan than a long text blob
- debugging
  - it is clearer which part of the result is missing or malformed
- agent usability
  - MCP-aware clients and agents can reliably access named fields
- safer boundaries
  - structured outputs reduce ambiguity and make it easier to avoid leaking unnecessary raw internals

Bad pattern:

```text
one giant unstructured text response
```

Better pattern:

```json
{
  "client_id": "example",
  "total_tokens": 123,
  "recent_history": "...",
  "note": "..."
}
```

## Safety boundary

The MCP layer in this repo is intentionally narrow.

It does not:

- expose raw database access
- place orders
- contact customers

`recommend_next_action` is recommendation-only. It does not perform real-world actions.

The intended safety model is:

```text
prediction -> recommendation -> human review -> any external action
```

Human approval is required before any real-world action should happen.

## Current limitations

Current limitations of the MCP learning setup:

- the dev client is not a production MCP host
- there is no real authentication or authorization layer yet
- prediction confidence is not calibrated or exposed clearly
- protected model/data assets are local-only and not part of the public repo
- token readability is still basic and only loosely human-friendly

## What to improve next

Useful next steps for learning MCP more deeply:

- add more MCP resources for model notes, tool usage guidance, and safety notes
- add an even smaller minimal MCP client script focused only on protocol learning
- add structured validation errors so tool failures are clearer to clients
- test the server with MCP Inspector or another real MCP host
