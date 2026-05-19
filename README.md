# B2B Next-Basket MCP Demo

A neutral, NDA-safe demo project showing how to expose a B2B next-basket/order-prediction backend through an MCP server.

The repository is designed so the public code can be uploaded to GitHub while proprietary model/data/backend files remain local.

## Architecture

```text
AI / MCP Client
  ↓ MCP tool call
MCP Server
  ↓ clean Python wrapper
ONNX next-basket prediction backend
  ↓
Predicted products + safe business recommendation
```

## MCP tools

- `list_clients(limit=20)`
- `get_sample_history(client_id)`
- `predict_next_basket(client_id, start_text, max_generate=30, temperature=1.0, top_k=20)`
- `recommend_next_action(client_id, start_text, max_generate=30, temperature=1.0, top_k=20)`

## NDA note

This repo intentionally does **not** include proprietary model/data/protected backend files.

Place the provided files locally like this:

```text
data/model.onnx
data/dataset.joblib
vendor/protected_backend.py
vendor/protected_runtime/
```

Do not commit `data/` or `vendor/` to GitHub.

## Setup

Use Python 3.11.

```bash
python3.11 -m venv .venv
```

Creates a project-local Python virtual environment.

```bash
source .venv/bin/activate
```

Activates the virtual environment in your current shell.

```bash
pip install --upgrade pip
```

Updates Python's package installer inside the virtual environment.

```bash
pip install -r requirements.txt
```

Installs NumPy, ONNX Runtime, Joblib, and the MCP Python SDK.

## Prepare local proprietary files

After extracting the original provided hackathon package somewhere on your machine, run:

```bash
python scripts/prepare_local_assets.py "/path/to/extracted/Public Hackathon (NDA required)"
```

Copies and renames the protected model/data/backend files into neutral local paths.

On Linux, if the protected backend import fails because of a wrong binary format, the script also tries to copy the Linux runtime into the expected root runtime location.

## Run normal Python demo first

```bash
PYTHONPATH=src python scripts/demo_without_mcp.py
```

Runs the prediction backend through normal Python functions. This should work before testing MCP.

## Run the MCP server

```bash
PYTHONPATH=src python scripts/run_mcp_server.py
```

Starts the MCP server over stdio and prints a short human-readable status banner to `stderr` during manual direct runs. Standard output remains reserved for MCP protocol traffic. The server waits for MCP client JSON-RPC messages on stdin/stdout, so appearing idle is normal until a client connects. The model is loaded lazily on the first tool call, not when the server module is imported. Direct server runs are mainly useful for MCP host integration or low-level debugging; for normal testing, use `scripts/mcp_dev_client.py`. The dev client suppresses the direct-run banner in its server subprocess to keep client output clean. Press `Ctrl+C` once to stop a direct run. The wrapper uses a forced exit to avoid stdin background-thread shutdown noise from the stdio runtime.

## Test with a small MCP client

Open another terminal from the same project root:

```bash
source .venv/bin/activate
```

Activates the same virtual environment.

```bash
PYTHONPATH=src python scripts/mcp_dev_client.py
```

Starts the MCP server as a subprocess, lists tools, calls `list_clients`, then calls a prediction/recommendation flow.

## First-principles lesson

The prediction model is not the product interface.

```text
Model backend = computes prediction
MCP server = exposes safe, typed, agent-callable tools
LLM/client = chooses and calls tools, then explains results
```
