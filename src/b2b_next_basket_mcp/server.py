from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from b2b_next_basket_mcp.config import SERVER_NAME
from b2b_next_basket_mcp.mcp.resources import register_resources
from b2b_next_basket_mcp.mcp.tools import register_tools

mcp = FastMCP(SERVER_NAME)
register_tools(mcp)
register_resources(mcp)


def main() -> None:
    # Stdio MCP servers may appear idle when run directly because they wait
    # for protocol messages from a client on stdin/stdout.
    mcp.run()


if __name__ == "__main__":
    main()
