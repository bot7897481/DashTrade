// Trade Detail API Response Types

export interface TradeDetailResponse {
  trade: {
    id: number;
    symbol: string;
    timeframe: string;
    action: string;
    status: string;
    created_at: string;
    filled_at: string | null;
  };

  execution: {
    notional: number;
    filled_qty: number;
    filled_avg_price: number;
    expected_price: number;
    slippage: number;
    slippage_percent: number;
    bid_price: number;
    ask_price: number;
    spread: number;
    spread_percent: number;
    order_id: string;
    order_type: string;
    time_in_force: string;
  };

  timing: {
    signal_received_at: string;
    order_submitted_at: string;
    execution_latency_ms: number;
    time_to_fill_ms: number;
    market_open: boolean;
    extended_hours: boolean;
    signal_source: string;
  };

  stock: {
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    prev_close: number;
    change_percent: number;
    avg_volume: number;
    volume_ratio: number;
  };

  fundamentals: {
    market_cap: number;
    pe_ratio: number;
    forward_pe: number;
    eps: number;
    beta: number;
    dividend_yield: number;
    shares_outstanding: number;
    short_ratio: number;
    fifty_two_week_high: number;
    fifty_two_week_low: number;
    fifty_day_ma: number;
    two_hundred_day_ma: number;
  };

  market_indices: {
    sp500: { price: number; change_percent: number };
    nasdaq: { price: number; change_percent: number };
    dji: { price: number; change_percent: number };
    russell: { price: number; change_percent: number };
    vix: { price: number; change_percent: number };
  };

  treasury: {
    yield_10y: number;
    yield_2y: number;
    yield_curve_spread: number;
  };

  sector: {
    etf_symbol: string;
    etf_price: number;
    etf_change_percent: number;
    sector_etfs: {
      XLK: number;
      XLF: number;
      XLE: number;
      XLV: number;
      XLY: number;
      XLP: number;
      XLI: number;
      XLB: number;
      XLU: number;
      XLRE: number;
    };
  };

  position: {
    before: string;
    after: string;
    qty_before: number;
    value_before: number;
    avg_entry: number;
    unrealized_pl: number;
  };

  account: {
    equity: number;
    cash: number;
    buying_power: number;
    portfolio_value: number;
    total_positions_count: number;
    total_positions_value: number;
  };

  technical: {
    rsi_14: number;
    price_vs_50ma_percent: number;
    price_vs_200ma_percent: number;
    price_vs_52w_high_percent: number;
    price_vs_52w_low_percent: number;
  };

  metadata: {
    context_captured_at: string;
    data_source: string;
    fetch_latency_ms: number;
    errors: string | null;
  };
}

// Performance API Response Types
export interface PerformanceResponse {
  summary: {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    total_pnl_dollars: number;
    avg_pnl_percent: number;
    profit_factor: number;
    avg_hold_duration_minutes: number;
  };
  by_indicator: Array<{
    entry_indicator: string;
    total_trades: number;
    win_rate: number;
    avg_return: number;
  }>;
  by_market_condition: Array<{
    vix_regime: string;
    total_trades: number;
    win_rate: number;
    avg_return: number;
  }>;
}

// Trade Outcomes API Response Types
export interface TradeOutcome {
  trade_id: number;
  symbol: string;
  position_type: string;
  entry_price: number;
  exit_price: number;
  entry_time: string;
  exit_time: string;
  exit_reason: string;
  pnl_dollars: number;
  pnl_percent: number;
  hold_duration_minutes: number;
  is_winner: boolean;
}

export interface TradeOutcomesResponse {
  outcomes: TradeOutcome[];
  summary: {
    total_pnl: number;
    today_pnl: number;
    this_week_pnl: number;
  };
}

// AI Insights API Response Types
export interface Insight {
  id: number;
  insight_type: string;
  confidence_score: number;
  sample_size?: number;
  title: string;
  description: string;
  observed_win_rate: number;
  observed_avg_return: number;
  observed_trades: number;
  recommendation: string;
  recommended_params?: Record<string, unknown>;
  conditions?: Record<string, string>;
  created_at?: string;
  is_active?: boolean;
}

export interface InsightsResponse {
  insights: Insight[];
  total?: number;
}

// AI Analysis Response Types
export interface AnalysisResponse {
  success: boolean;
  error?: string;
  insights_generated?: number;
  insights_saved?: number;
  total_trades_analyzed?: number;
  total_trades?: number;
  min_required?: number;
  claude_api_used?: boolean;
  overall_stats?: {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    total_pnl: number;
    avg_return: number;
    avg_win: number;
    avg_loss: number;
    avg_hold_minutes: number;
  };
  insights?: Insight[];
}

// Pattern Types
export interface RsiPattern {
  rsi_range: string;
  total_trades: number;
  win_rate: number;
  avg_return: number;
  total_pnl: number;
}

export interface VixPattern {
  vix_regime: string;
  total_trades: number;
  win_rate: number;
  avg_return: number;
  avg_vix: number;
}

export interface TimeframePattern {
  timeframe: string;
  total_trades: number;
  win_rate: number;
  avg_return: number;
  avg_hold_minutes: number;
}

export interface TimeOfDayPattern {
  time_period: string;
  total_trades: number;
  win_rate: number;
  avg_return: number;
}

export interface TrendPattern {
  trend: string;
  total_trades: number;
  win_rate: number;
  avg_return: number;
}

export interface PatternsResponse {
  overall_stats: {
    total_trades: number;
    win_rate: number;
    total_pnl: number;
  };
  patterns: {
    rsi?: RsiPattern[];
    vix?: VixPattern[];
    timeframe?: TimeframePattern[];
    time_of_day?: TimeOfDayPattern[];
    trend?: TrendPattern[];
  };
  min_trades_filter: number;
}

// TradingView Setup Types
export interface TradingViewSetup {
  basic_message: string;
  exit_message: string;
  ai_learning_message: string;
  instructions: string[];
  ai_learning_params?: Record<string, string>;
}
