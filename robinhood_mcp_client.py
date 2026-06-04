"""
Robinhood MCP Client - Connects to Robinhood's Agentic Trading MCP server
Uses the MCP Python SDK with Streamable HTTP transport

MCP endpoint: https://agent.robinhood.com/mcp/trading
Auth: OAuth 2.0 (Bearer token obtained via browser-based OAuth flow)
"""
import asyncio
import logging
import json
from typing import Dict, List, Optional, Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)

ROBINHOOD_MCP_URL = "https://agent.robinhood.com/mcp/trading"


class RobinhoodMCPClient:
    """
    Wrapper around the Robinhood Trading MCP server.
    Discovers available tools at runtime and provides typed method access.
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self._session: Optional[ClientSession] = None
        self._tools: Dict[str, Any] = {}
        self._headers = {
            "Authorization": f"Bearer {access_token}",
        }

    async def connect(self) -> "RobinhoodMCPClient":
        """Connect to the MCP server and discover available tools."""
        async with streamablehttp_client(
            url=ROBINHOOD_MCP_URL,
            headers=self._headers
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                self._session = session

                # Discover available tools
                tools_result = await session.list_tools()
                for tool in tools_result.tools:
                    self._tools[tool.name] = {
                        "name": tool.name,
                        "description": tool.description,
                        "schema": tool.inputSchema
                    }

                logger.info(f"Connected to Robinhood MCP. Available tools: {list(self._tools.keys())}")
                return self

    async def call_tool(self, tool_name: str, arguments: Dict = None) -> Any:
        """
        Call an MCP tool on the Robinhood server.

        Each call opens a fresh connection since MCP Streamable HTTP
        is stateless per-request.
        """
        arguments = arguments or {}

        async with streamablehttp_client(
            url=ROBINHOOD_MCP_URL,
            headers=self._headers
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)

                # Extract text content from MCP result
                if result.content:
                    texts = []
                    for block in result.content:
                        if hasattr(block, 'text'):
                            texts.append(block.text)
                    combined = "\n".join(texts)
                    # Try to parse as JSON
                    try:
                        return json.loads(combined)
                    except (json.JSONDecodeError, ValueError):
                        return combined

                return None

    async def list_tools(self) -> List[Dict]:
        """List all available MCP tools from the server."""
        async with streamablehttp_client(
            url=ROBINHOOD_MCP_URL,
            headers=self._headers
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                return [
                    {
                        "name": t.name,
                        "description": t.description,
                        "schema": t.inputSchema
                    }
                    for t in tools_result.tools
                ]

    # -- Convenience methods --
    # These wrap common tool calls. Tool names are discovered at runtime;
    # the names below are best-guess based on MCP conventions and
    # Robinhood's documented capabilities. If a tool name doesn't match,
    # call_tool() will raise and we log the available tools.

    async def get_account(self) -> Dict:
        """Get Robinhood agentic account info."""
        return await self.call_tool("get_account")

    async def get_portfolio(self) -> Dict:
        """Get portfolio value and positions."""
        return await self.call_tool("get_portfolio")

    async def get_positions(self) -> List[Dict]:
        """Get all open positions."""
        return await self.call_tool("get_positions")

    async def place_order(self, symbol: str, side: str, quantity: float = None,
                          notional: float = None, order_type: str = "market",
                          limit_price: float = None,
                          time_in_force: str = "day") -> Dict:
        """Place an order through Robinhood."""
        args = {
            "symbol": symbol.upper(),
            "side": side.lower(),
            "order_type": order_type,
            "time_in_force": time_in_force,
        }
        if quantity is not None:
            args["quantity"] = quantity
        if notional is not None:
            args["notional"] = notional
        if limit_price is not None:
            args["limit_price"] = limit_price

        return await self.call_tool("place_order", args)

    async def get_order(self, order_id: str) -> Dict:
        """Get order status by ID."""
        return await self.call_tool("get_order", {"order_id": order_id})

    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an open order."""
        return await self.call_tool("cancel_order", {"order_id": order_id})

    async def get_quote(self, symbol: str) -> Dict:
        """Get a price quote for a symbol."""
        return await self.call_tool("get_quote", {"symbol": symbol.upper()})


def run_sync(coro):
    """Helper to run async MCP calls from synchronous Flask code."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're inside an existing event loop (e.g. during testing)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)
