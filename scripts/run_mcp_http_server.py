from __future__ import annotations

import os
import sys

from b2b_next_basket_mcp.server import mcp


def _tool_names() -> list[str]:
    return [tool.name for tool in mcp._tool_manager.list_tools()]  # noqa: SLF001


def main() -> None:
    transport = os.environ.get("B2B_MCP_HTTP_TRANSPORT", "streamable-http")
    host = os.environ.get("B2B_MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.environ.get("B2B_MCP_HTTP_PORT", "8010"))

    if transport not in {"streamable-http", "sse"}:
        raise ValueError("B2B_MCP_HTTP_TRANSPORT must be 'streamable-http' or 'sse'")

    mcp.settings.host = host
    mcp.settings.port = port

    # This runner is for a local n8n visual demo. Docker/rootless proxying can
    # present non-local Host headers even though the service is local-only.
    mcp.settings.transport_security = None

    endpoint_path = mcp.settings.streamable_http_path if transport == "streamable-http" else mcp.settings.sse_path
    endpoint_url = f"http://{host}:{port}{endpoint_path}"
    local_url = f"http://127.0.0.1:{port}{endpoint_path}"

    print("MCP HTTP server starting.", file=sys.stderr, flush=True)
    print(f"Transport: {transport}", file=sys.stderr, flush=True)
    print(f"Listening on: {endpoint_url}", file=sys.stderr, flush=True)
    print(f"Local endpoint: {local_url}", file=sys.stderr, flush=True)
    print("n8n rootless Docker endpoint via host_proxy: http://172.19.0.1:18010/mcp", file=sys.stderr, flush=True)
    print("Tools exposed:", file=sys.stderr, flush=True)
    for name in _tool_names():
        print(f"- {name}", file=sys.stderr, flush=True)

    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
