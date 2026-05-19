from __future__ import annotations

import os
import signal
import sys
from types import FrameType


def handle_sigint(_signum: int, _frame: FrameType | None) -> None:
    print("\nMCP server stopped.\n", file=sys.stderr, flush=True)
    os._exit(0)


if __name__ == "__main__":
    # Manual direct server runs show the banner. Subprocess runs suppress it
    # to keep dev-client output clean. Stderr is safe because stdout is
    # reserved for MCP stdio protocol messages between client and server.
    if os.environ.get("B2B_MCP_SUPPRESS_BANNER") != "1":
        print("MCP stdio server starting.", file=sys.stderr, flush=True)
        print(
            "Waiting for MCP client messages on stdin/stdout.",
            file=sys.stderr,
            flush=True,
        )
        print(
            "No output here is normal unless a client connects.",
            file=sys.stderr,
            flush=True,
        )
        print(
            "For local testing, run: PYTHONPATH=src python scripts/mcp_dev_client.py",
            file=sys.stderr,
            flush=True,
        )
        print("Press Ctrl+C once to stop.", file=sys.stderr, flush=True)

    # Stdio MCP servers block waiting for client protocol messages. Handle
    # SIGINT directly so manual direct runs avoid messy async/stdin shutdown
    # behavior and exit immediately on Ctrl+C.
    signal.signal(signal.SIGINT, handle_sigint)

    from b2b_next_basket_mcp.mcp_server import main

    main()
