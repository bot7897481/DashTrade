// User types
export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  full_name?: string;
}

export interface AuthResponse {
  success: boolean;
  token: string;
  user?: User;
  user_id?: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  email: string;
  password: string;
  full_name: string;
}

// Bot types
export interface Bot {
  id: number;
  user_id?: number;
  symbol: string;
  timeframe: string;
  position_size: number;
  is_active: boolean;
  strategy_name?: string;
  risk_limit_percent?: number;
  daily_loss_limit?: number;
  max_position_size?: number;
  order_status?: 'IDLE' | 'READY' | 'SUBMITTED' | 'FILLED' | 'FAILED' | 'ORDER SUBMITTED';
  current_position_side?: 'FLAT' | 'LONG' | 'SHORT';
  signal_source?: 'webhook' | 'bot_webhook' | 'user_webhook' | 'system';
  created_at?: string;
  updated_at?: string;
  // Per-bot webhook
  webhook_token?: string;
  webhook_url?: string;
  // Additional bot stats
  last_signal?: string;
  last_signal_time?: string;
  total_pnl?: number;
  total_trades?: number;
  // Error tracking
  last_error?: string;
  last_error_at?: string;
}

export interface BotListResponse {
  bots: Bot[];
  total: number;
  active: number;
}

export interface CreateBotPayload {
  symbol: string;
  timeframe: string;
  position_size: number;
  strategy_name?: string;
  risk_limit_percent?: number;
  daily_loss_limit?: number;
  max_position_size?: number;
  signal_source?: 'webhook';
  is_active?: boolean;
}

// Batch bot creation payload
export interface BatchCreateBotPayload {
  symbols: string[];
  timeframes: string[];
  position_size: number;
  strategy_name?: string;
}

export interface CreateBotResponse {
  success: boolean;
  bot_id: number;
  message: string;
  webhook_url: string;
  webhook_payload: string;
}

// Batch bot creation response
export interface BatchCreateBotResponse {
  success: boolean;
  created_count: number;
  error_count: number;
  created_bots: Array<{
    id: number;
    symbol: string;
    timeframe: string;
    position_size: number;
  }>;
  webhook_url: string;
  message: string;
}

export interface UpdateBotPayload {
  position_size?: number;
  strategy_name?: string;
  risk_limit_percent?: number;
  daily_loss_limit?: number;
  max_position_size?: number;
  is_active?: boolean;
}

export interface RegenerateBotTokenResponse {
  success: boolean;
  webhook_token: string;
  webhook_url: string;
  webhook_payload: string;
  message: string;
}

// Trading types
export interface Position {
  symbol: string;
  qty: number;
  market_value: number;
  unrealized_pl: number;
  unrealized_plpc?: number;
  avg_entry_price?: number;
  side?: string;
  current_price?: number;
}

export interface Trade {
  id: number;
  user_id?: number;
  bot_config_id?: number;
  symbol: string;
  timeframe?: string;
  action: 'BUY' | 'SELL' | 'CLOSE';
  notional?: number;
  order_id?: string;
  status?: string;
  
  // Filled details
  filled_qty?: number;
  filled_avg_price?: number;
  filled_at?: string;
  
  // Legacy fields (kept for compatibility)
  qty?: number;
  price?: number;
  timestamp?: string;
  bot_id?: number;
  
  // P&L (for CLOSE orders)
  realized_pnl?: number;
  
  // Pricing fields
  bid_price?: number;
  ask_price?: number;
  spread?: number;
  spread_percent?: number;
  expected_price?: number;
  
  // Slippage
  slippage?: number;
  slippage_percent?: number;
  
  // Timing
  signal_received_at?: string;
  order_submitted_at?: string;
  execution_latency_ms?: number;
  time_to_fill_ms?: number;
  
  // Market conditions
  market_open?: boolean;
  extended_hours?: boolean;
  
  // Position tracking
  position_before?: 'LONG' | 'SHORT' | 'FLAT' | string;
  position_after?: 'LONG' | 'SHORT' | 'FLAT' | string;
  position_qty_before?: number;
  position_value_before?: number;
  
  // Account state
  account_equity?: number;
  account_buying_power?: number;
  
  // Order details
  order_type?: string;
  time_in_force?: string;
  signal_source?: 'bot_webhook' | 'user_webhook' | 'system' | string;
  limit_price?: number;
  stop_price?: number;
  
  // Alpaca specific
  alpaca_order_status?: string;
  alpaca_client_order_id?: string;
  
  // Error handling
  error_message?: string;
  created_at?: string;
}

export interface Account {
  buying_power: number;
  portfolio_value: number;
  cash: number;
  equity?: number;
  last_equity?: number;
  long_market_value?: number;
  short_market_value?: number;
  pattern_day_trader?: boolean;
  trading_blocked?: boolean;
  transfers_blocked?: boolean;
}

// P&L Summary
export interface PnLSummary {
  total_pnl: number;
  realized_pnl: number;
  unrealized_pnl: number;
}

// Extended bots response with P&L
export interface DashboardBotsData extends BotListResponse {
  total_pnl?: number;
  total_trades?: number;
}

// Dashboard aggregate
export interface DashboardData {
  account: Account;
  bots: DashboardBotsData;
  positions: Position[];
  recent_trades: Trade[];
  recent_trades_source?: 'alpaca' | 'database';
  api_keys_configured?: boolean;
  pnl?: PnLSummary;
}

// Recent trades response (from Alpaca API)
export interface RecentTradesResponse {
  trades: Array<{
    symbol: string;
    side: string;
    action: string;
    qty: number;
    price: number;
    transaction_time: string;
    order_id: string;
    value: number;
  }>;
  total: number;
  source: string;
}

// Settings types
export interface ApiKeyPayload {
  api_key: string;
  secret_key: string;
  mode: 'paper' | 'live';
}

export interface ApiKeyStatus {
  configured: boolean;
  mode: 'paper' | 'live';
}

export interface WebhookToken {
  token: string;
  webhook_url: string;
}

// Notification settings types
export interface NotificationSettings {
  email: string;
  email_notifications_enabled: boolean;
  notify_on_trade: boolean;
  notify_on_error: boolean;
  notify_on_risk_event: boolean;
  notify_daily_summary: boolean;
}

export interface NotificationSettingsPayload {
  email_notifications_enabled?: boolean;
  notify_on_trade?: boolean;
  notify_on_error?: boolean;
  notify_on_risk_event?: boolean;
  notify_daily_summary?: boolean;
}

export interface TestEmailResponse {
  success: boolean;
  message: string;
  error?: string;
}

// Strategy types
export interface Strategy {
  id: number;
  name: string;
  description?: string;
  token?: string;
  created_at?: string;
  performance_stats?: {
    total_trades?: number;
    win_rate?: number;
    avg_return?: number;
  };
  is_subscribed?: boolean;
  win_rate?: number;
  avg_return?: number;
  subscribers?: number;
  tags?: string[];
}

export interface StrategyListResponse {
  strategies: Strategy[];
  total: number;
}

// API Error
export interface ApiError {
  error: string;
  status?: number;
}
