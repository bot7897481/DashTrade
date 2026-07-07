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
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import requests

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)

# Transports tried in order: current standard first, legacy SSE fallback.
# The Robinhood MCP server has been observed to accept streamable-http; SSE is
# kept as a fallback so a server-side transport change can't break us.
MCP_TRANSPORTS = ("streamable-http", "sse")

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
# Real names first (verified against the live Robinhood Agentic Trading MCP:
# get_accounts, get_portfolio, get_equity_positions, place_equity_order,
# get_equity_orders, cancel_equity_order, get_equity_quotes). Exact matches are
# tried before the fuzzy fallback, so resolution is deterministic and never
# accidentally grabs the option/crypto variant (e.g. place_option_order).
TOOL_ALIASES = {
    "get_account": ["get_accounts", "get_portfolio", "get_account", "account", "get_account_info"],
    "get_portfolio": ["get_portfolio", "portfolio", "get_portfolio_summary"],
    "get_positions": ["get_equity_positions", "get_positions", "positions", "list_positions"],
    "place_order": ["place_equity_order", "place_order", "create_order", "submit_order"],
    "get_order": ["get_equity_orders", "get_order", "get_order_status", "order_status"],
    "cancel_order": ["cancel_equity_order", "cancel_order", "cancel"],
    "get_quote": ["get_equity_quotes", "get_quote", "quote", "get_quotes", "get_price"],
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
        self._account_number: Optional[str] = None   # cached agentic account
        self._headers = {
            "Authorization": f"Bearer {access_token}",
        }

    async def _resolve_account_number(self) -> str:
        """Resolve the account number to trade on, caching the result.

        place_equity_order / get_equity_positions / get_equity_orders all REQUIRE
        an account_number, and placing orders requires agentic_allowed=true. We
        prefer the agentic account, then the default, then the first available.
        """
        if self._account_number:
            return self._account_number

        data = await self.call_tool("get_account")  # resolves to get_accounts
        accounts = []
        if isinstance(data, dict):
            accounts = data.get("data", {}).get("accounts", []) or data.get("accounts", [])

        chosen = (
            next((a for a in accounts if a.get("agentic_allowed")), None)
            or next((a for a in accounts if a.get("is_default")), None)
            or (accounts[0] if accounts else None)
        )
        if not chosen or not chosen.get("account_number"):
            raise ValueError(
                "Could not resolve a Robinhood account_number from get_accounts "
                f"(found {len(accounts)} accounts)"
            )
        self._account_number = chosen["account_number"]
        if not chosen.get("agentic_allowed"):
            logger.warning(
                "Selected Robinhood account %s is not agentic_allowed — "
                "order placement will be rejected by the server.",
                self._account_number[-4:] if self._account_number else "?"
            )
        return self._account_number

    async def _with_session(self, fn):
        """Open an MCP session (trying each transport in order) and run fn(session).

        MCP client contexts (anyio cancel scopes) must be entered and exited
        within the same task, so the session is opened, used, and closed inside
        this single coroutine — never held open across calls.
        """
        errors = []
        for transport in MCP_TRANSPORTS:
            try:
                if transport == "streamable-http":
                    async with streamablehttp_client(
                        url=ROBINHOOD_MCP_URL, headers=self._headers
                    ) as (read_stream, write_stream, _):
                        async with ClientSession(read_stream, write_stream) as session:
                            await session.initialize()
                            return await fn(session)
                else:
                    async with sse_client(
                        url=ROBINHOOD_MCP_URL, headers=self._headers
                    ) as (read_stream, write_stream):
                        async with ClientSession(read_stream, write_stream) as session:
                            await session.initialize()
                            return await fn(session)
            except Exception as e:
                errors.append(f"{transport}: {e}")
                logger.warning(f"Robinhood MCP transport '{transport}' failed: {e}")
        raise ConnectionError(
            f"All Robinhood MCP transports failed: {' | '.join(errors)}"
        )

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
        async def _do(session: ClientSession):
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

        return await self._with_session(_do)

    async def call_tool(self, tool_name: str, arguments: Dict = None) -> Any:
        """
        Call an MCP tool on the Robinhood server.

        Each call opens a fresh connection since MCP Streamable HTTP
        is stateless per-request.
        """
        arguments = arguments or {}
        resolved_name = await self._resolve_tool_name(tool_name)

        async def _do(session: ClientSession):
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

        return await self._with_session(_do)

    async def list_tools(self) -> List[Dict]:
        """List all available MCP tools from the server."""
        async def _do(session: ClientSession):
            tools_result = await session.list_tools()
            return [
                {
                    "name": t.name,
                    "description": t.description,
                    "schema": t.inputSchema
                }
                for t in tools_result.tools
            ]

        return await self._with_session(_do)

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
        """Get all open positions for the resolved account."""
        account_number = await self._resolve_account_number()
        result = await self.call_tool("get_positions", {"account_number": account_number})
        # get_equity_positions wraps the list under data.results/positions —
        # unwrap to a bare list so callers can iterate.
        if isinstance(result, dict):
            data = result.get("data", result)
            for key in ("results", "positions"):
                if isinstance(data.get(key), list):
                    return data[key]
        return result if isinstance(result, list) else []

    async def place_order(self, symbol: str, side: str, quantity: float = None,
                          notional: float = None, order_type: str = "market",
                          limit_price: float = None,
                          time_in_force: str = "day") -> Dict:
        """Place an order via the real place_equity_order schema.

        Maps our generic params to Robinhood's actual field names:
          order_type -> type, notional -> dollar_amount, day -> gfd,
          and adds the required account_number + an idempotency ref_id.
        All numeric values must be strings.
        """
        account_number = await self._resolve_account_number()
        tif = "gtc" if str(time_in_force).lower() in ("gtc", "good_till_cancelled") else "gfd"
        args = {
            "account_number": account_number,
            "symbol": symbol.upper(),
            "side": side.lower(),
            "type": order_type.lower(),        # real key is 'type', not 'order_type'
            "time_in_force": tif,              # real values: gfd | gtc (never 'day')
            "ref_id": str(uuid.uuid4()),       # idempotency key
        }
        if notional is not None:
            args["dollar_amount"] = f"{float(notional):.2f}"   # real key, string
        if quantity is not None:
            args["quantity"] = str(quantity)                    # string
        if limit_price is not None:
            args["limit_price"] = f"{float(limit_price):.2f}"

        return await self.call_tool("place_order", args)

    async def get_order(self, order_id: str) -> Dict:
        """Get a single order by ID (get_equity_orders with order_id filter)."""
        account_number = await self._resolve_account_number()
        result = await self.call_tool(
            "get_order", {"account_number": account_number, "order_id": order_id}
        )
        # get_equity_orders returns data.orders[] with at most one entry — unwrap.
        if isinstance(result, dict):
            orders = result.get("data", {}).get("orders")
            if isinstance(orders, list):
                return orders[0] if orders else {}
        return result if isinstance(result, dict) else {}

    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an open order."""
        account_number = await self._resolve_account_number()
        return await self.call_tool(
            "cancel_order", {"account_number": account_number, "order_id": order_id}
        )

    async def get_quote(self, symbol: str) -> Dict:
        """Get a price quote (get_equity_quotes takes a symbols array)."""
        return await self.call_tool("get_quote", {"symbols": [symbol.upper()]})


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
