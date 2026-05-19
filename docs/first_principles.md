# First Principles of MCP

## Core problem

An LLM cannot safely and reliably access external systems by itself. MCP provides a standard protocol through which an AI client can discover and call tools exposed by a server.

## Components

```text
Host/client: AI application that wants to use tools
MCP server: process that exposes tools/resources
Tool: typed callable function
Resource: readable context/document/schema
Backend: real system hidden behind the tool
```

## This project

```text
AI/MCP client
  ↓ calls tool
MCP server
  ↓ calls Python wrapper
ONNX prediction backend
  ↓ returns predicted tokens
Business layer
  ↓ returns safe recommendation
```

## Tool design rule

Expose business-safe tools, not raw internals.

Bad:

```text
run_sql(query)
run_raw_model(features)
```

Better:

```text
predict_next_basket(client_id, start_text)
recommend_next_action(client_id, start_text)
```

## Safety rule

This demo does not place orders and does not contact customers. It returns recommendation-only output requiring human approval.
