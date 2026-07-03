"""
Robinhood MCP Client - Connects to Robinhood's Agentic Trading MCP server
Uses the MCP Python SDK with Streamable HTTP transport

MCP endpoint: https://agent.robinhood.com/mcp/trading
Auth: OAuth 2.0 (Bearer token obtained via browser-based OAuth flow)
"""
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import requests

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)

ROBINHOOD_MCP_URL = "https://agent.robinhood.com/mcp/trading"

# OAuth token endpoint, verified against Robinhood's authorization server
# metadata (https://agent.robinhood.com/.well-known/oauth-authorization-server).
ROBINHOOD_OAUTH_TOKEN_URL = os.environ.get(
    'ROBINHOOD_OAUTH_TOKEN_URL', 'https://api.robinhood.com/oauth2/token/'
)
ROBINHOOD_CLIENT_ID = os.environ.get('ROBINHOOD_CLIENT_ID', '')


def _get_client_id() -> str:
    """Client ID from env, falling back to the dynamically registered client in DB."""
    if ROBINHOOD_CLIENT_ID:
        return ROBINHOOD_CLIENT_ID
    try:
        from bot_database import RobinhoodOAuthDB
        client = RobinhoodOAuthDB.get_client()
        return client['client_id'] if client else ''
    except Exception:
        return ''

# Preferred tool names → known aliases. The Robinhood MCP server's real
# tool names are discovered at runtime; we resolve our canonical names
# against the live tool list so a server-side rename doesn't break us.
TOOL_ALIASES = {
    "get_account": ["get_account", "account", "get_account_info", "get_account_details"],
    "get_portfolio": ["get_portfolio", "portfolio", "get_portfolio_summary"],
    "get_positions": ["get_positions", "positions", "list_positions", "get_holdings"],
    "place_order": ["place_order", "create_order", "submit_order", "place_trade"],
    "get_order": ["get_order", "get_order_status", "order_status"],
    "cancel_order": ["cancel_order", "cancel"],
    "get_quote": ["get_quote", "quote", "get_quotes", "get_price", "get_market_data"],
}


def refresh_access_token(refresh_token: str) -> Optional[Dict]:
    """
    Exchange a refresh token for a new access token via OAuth 2.0.

    Returns {'access_token', 'refresh_token', 'expires_at'} on success,
    or None on failure (caller should keep using the old token and alert).
    """
    try:
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'resource': ROBINHOOD_MCP_URL,
        }
        client_id = _get_client_id()
        if client_id:
            payload['client_id'] = client_id

        resp = requests.post(ROBINHOOD_OAUTH_TOKEN_URL, data=payload, timeout=15)
        if resp.status_code != 200:
            logger.error(f"Robinhood token refresh failed: HTTP {resp.status_code} {resp.text[:200]}")
            return None

        data = resp.json()
        access_token = data.get('access_token')
        if not access_token:
            logger.error(f"Robinhood token refresh: no access_token in response")
            return None

        expires_at = None
        if data.get('expires_in'):
            expires_at = datetime.utcnow() + timedelta(seconds=int(data['expires_in']))

        return {
            'access_token': access_token,
            'refresh_token': data.get('refresh_token', refresh_token),
            'expires_at': expires_at,
        }
    except Exception as e:
        logger.error(f"Robinhood token refresh error: {e}")
        return None


class RobinhoodMCPClient:
    """
    Wrapper around the Robinhood Trading MCP server.
    Discovers available tools at runtime and provides typed method access.
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self._session: Optional[ClientSession] = None
        self._tools: Dict[str, Any] = {}
        self._tool_name_cache: Dict[str, str] = {}  # canonical name → real server name
        self._headers = {
            "Authorization": f"Bearer {access_token}",
        }

    async def _resolve_tool_name(self, canonical_name: str) -> str:
        """
        Resolve a canonical tool name to the real name exposed by the
        Robinhood MCP server, using the alias table and live tool list.
        """
        if canonical_name in self._tool_name_cache:
            return self._tool_name_cache[canonical_name]

        # Fetch the live tool list if we don't have it yet
        if not self._tools:
            try:
                tools = await self.list_tools()
                self._tools = {t['name']: t for t in tools}
            except Exception as e:
                logger.warning(f"Could not list Robinhood MCP tools ({e}); "
                               f"using canonical name '{canonical_name}' as-is")
                return canonical_name

        available = list(self._tools.keys())

        # 1. Exact match on any alias
        for alias in TOOL_ALIASES.get(canonical_name, [canonical_name]):
            if alias in self._tools:
                self._tool_name_cache[canonical_name] = alias
                if alias != canonical_name:
                    logger.info(f"Resolved MCP tool '{canonical_name}' → '{alias}'")
                return alias

        # 2. Substring match (e.g. 'rh_place_order' for 'place_order')
        for name in available:
            for alias in TOOL_ALIASES.get(canonical_name, [canonical_name]):
                if alias in name or name in alias:
                    self._tool_name_cache[canonical_name] = name
                    logger.info(f"Resolved MCP tool '{canonical_name}' → '{name}' (fuzzy)")
                    return name

        raise ValueError(
            f"No Robinhood MCP tool found for '{canonical_name}'. "
            f"Available tools: {available}"
        )

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
        resolved_name = await self._resolve_tool_name(tool_name)

        async with streamablehttp_client(
            url=ROBINHOOD_MCP_URL,
            headers=self._headers
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(resolved_name, arguments)

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
