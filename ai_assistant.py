"""
AI Assistant Backend Logic
Handles secure key storage and interaction with Anthropic API
"""
import os
import secrets
from typing import Optional, Dict, List, Generator
import anthropic
from database import get_db_connection
from encryption import encrypt_alpaca_keys, decrypt_alpaca_keys # Reusing encryption logic

class LLMKeysDB:
    """Database operations for LLM API keys"""
    
    @staticmethod
    def save_key(user_id: int, api_key: str, provider: str = 'anthropic') -> bool:
        """Save or update user's LLM API key (encrypted)"""
        try:
            # Reuse Alpaca encryption (encrypts two strings, so we pass dummy for the second)
            # This keeps encryption logic centralized
            enc_key, _ = encrypt_alpaca_keys(api_key, "dummy_secret")
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # SQLite syntax for upsert
                    if 'sqlite' in str(conn):
                         cur.execute("""
                            INSERT INTO user_llm_keys (user_id, provider, api_key_encrypted, is_active, updated_at)
                            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                            ON CONFLICT(user_id) DO UPDATE SET
                                provider=excluded.provider,
                                api_key_encrypted=excluded.api_key_encrypted,
                                is_active=1,
                                updated_at=CURRENT_TIMESTAMP
                        """, (user_id, provider, enc_key))
                    else:
                        # PostgreSQL syntax
                        cur.execute("""
                            INSERT INTO user_llm_keys (user_id, provider, api_key_encrypted, updated_at)
                            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (user_id) DO UPDATE
                            SET provider = %s,
                                api_key_encrypted = %s,
                                is_active = TRUE,
                                updated_at = CURRENT_TIMESTAMP
                        """, (user_id, provider, enc_key, provider, enc_key))
            return True
        except Exception as e:
            print(f"Error saving LLM key: {e}")
            return False

    @staticmethod
    def get_key(user_id: int) -> Optional[str]:
        """Get user's decrypted API key"""
        try:
            with get_db_connection() as conn:
                # Use standard cursor for compatibility
                with conn.cursor() as cur:
                    if 'sqlite' in str(conn):
                        cur.execute("SELECT api_key_encrypted FROM user_llm_keys WHERE user_id = ? AND is_active = 1", (user_id,))
                    else:
                        cur.execute("SELECT api_key_encrypted FROM user_llm_keys WHERE user_id = %s AND is_active = TRUE", (user_id,))
                    
                    row = cur.fetchone()
                    if not row:
                        return None
                        
                    # Handle both Row object and tuple/dict return types
                    if isinstance(row, tuple):
                        enc_key = row[0]
                    else:
                        enc_key = row['api_key_encrypted']
                    
                    # Decrypt (returns tuple, we only want the first part)
                    api_key, _ = decrypt_alpaca_keys(enc_key, "dummy_encrypted_secret")
                    return api_key
        except Exception as e:
            print(f"Error retrieving LLM key: {e}")
            return None

class AIAssistant:
    """Manages interactions with Claude including Tool Use"""
    
    def __init__(self, api_key: str, user_id: int = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20240620"
        self.user_id = user_id
        
        # Define available tools
        self.tools = [
            {
                "name": "get_account_summary",
                "description": "Get the user's Alpaca account summary including equity, cash, and buying power.",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_active_positions",
                "description": "Get a list of all currently open trading positions.",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_stock_price",
                "description": "Get the latest bid and ask price for a specific stock symbol.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "The stock symbol, e.g., AAPL"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_market_clock",
                "description": "Check if the US stock market is currently open and see when it next opens or closes.",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "place_trading_order",
                "description": "Place a buy or sell order for a stock. Use paper trading for safety.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol (e.g., TSLA)"},
                        "qty": {"type": "number", "description": "Number of shares"},
                        "side": {"type": "string", "enum": ["buy", "sell"], "description": "Direction of trade"},
                        "order_type": {"type": "string", "enum": ["market", "limit"], "default": "market"},
                        "limit_price": {"type": "number", "description": "Price for limit orders"}
                    },
                    "required": ["symbol", "qty", "side"]
                }
            }
        ]

    def chat_stream(self, messages: List[Dict], system_prompt: str = None) -> Generator[str, None, None]:
        """Stream response from Claude with Support for Tools"""
        from bot_engine import TradingEngine
        
        # Default system prompt
        if not system_prompt:
            system_prompt = """You are DashTrade AI, a powerful financial assistant.
            You can analyze markets AND help users manage their Alpaca accounts.
            You have tools to check balances, see positions, get quotes, and even place trades.
            Always confirm with the user before placing a large trade.
            Keep responses professional and actionable."""
            
        try:
            # First, send message to Claude (not streaming yet to handle potential tool calls)
            # Actually, to stream AND handle tools, we need a slight bit more logic.
            # For simplicity in this UI, we'll do non-streaming for tool-calling turns if needed,
            # or just use the tool loop.
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                tools=self.tools,
                messages=messages
            )
            
            # Check for tool use
            if response.stop_reason == "tool_use":
                # Add assistant's tool use message to context
                messages.append({"role": "assistant", "content": response.content})
                
                # Execute tool
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_id = content_block.id
                        tool_input = content_block.input
                        
                        yield f"🔍 *AI is using tool: {tool_name}...*\n\n"
                        
                        tool_result = self._execute_tool(tool_name, tool_input)
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": str(tool_result),
                                }
                            ],
                        })
                
                # Get final response from Claude after tool result
                # We can stream THIS part
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=2048,
                    system=system_prompt,
                    tools=self.tools,
                    messages=messages
                ) as stream:
                    for text in stream.text_stream:
                        yield text
            else:
                # Normal text response
                for content_block in response.content:
                    if content_block.type == "text":
                        yield content_block.text
                        
        except Exception as e:
            yield f"Error in AI logic: {str(e)}"

    def _execute_tool(self, tool_name: str, tool_input: Dict) -> Dict:
        """Helper to execute the requested tool"""
        from bot_engine import TradingEngine
        
        if not self.user_id:
            return {"error": "User ID not provided to AI Assistant"}
            
        try:
            engine = TradingEngine(self.user_id)
            
            if tool_name == "get_account_summary":
                return engine.get_account_info()
            elif tool_name == "get_active_positions":
                return engine.get_all_positions()
            elif tool_name == "get_stock_price":
                return engine.get_price_quote(tool_input['symbol'])
            elif tool_name == "get_market_clock":
                return engine.get_market_clock()
            elif tool_name == "place_trading_order":
                return engine.place_manual_order(
                    tool_input['symbol'], 
                    tool_input['qty'], 
                    tool_input['side'],
                    tool_input.get('order_type', 'market'),
                    tool_input.get('limit_price')
                )
            else:
                return {"error": f"Tool {tool_name} not implemented"}
        except Exception as e:
            return {"error": str(e)}
