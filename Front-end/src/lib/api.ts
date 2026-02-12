import type {
  User,
  AuthResponse,
  LoginCredentials,
  RegisterCredentials,
  BotListResponse,
  Bot,
  CreateBotPayload,
  CreateBotResponse,
  BatchCreateBotPayload,
  BatchCreateBotResponse,
  UpdateBotPayload,
  RegenerateBotTokenResponse,
  Account,
  Position,
  Trade,
  DashboardData,
  ApiKeyPayload,
  ApiKeyStatus,
  WebhookToken,
  StrategyListResponse,
  NotificationSettings,
  NotificationSettingsPayload,
  TestEmailResponse,
} from '@/types/api.ts';

import type {
  TradeDetailResponse,
  PerformanceResponse,
  TradeOutcomesResponse,
  InsightsResponse,
  AnalysisResponse,
  PatternsResponse,
} from '@/types/trade-detail.ts';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://overflowing-spontaneity-production.up.railway.app';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/auth';
      throw new Error('Session expired. Please log in again.');
    }

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'An error occurred');
    }

    return data;
  }

  // Auth endpoints
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    return this.request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    return this.request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async getMe(): Promise<User> {
    return this.request<User>('/api/auth/me');
  }

  async forgotPassword(email: string): Promise<{ success: boolean; message: string }> {
    return this.request('/api/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async resetPassword(token: string, newPassword: string): Promise<{ success: boolean; message: string }> {
    return this.request('/api/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword }),
    });
  }

  // Bot endpoints
  async getBots(): Promise<BotListResponse> {
    return this.request<BotListResponse>('/api/bots');
  }

  async createBot(payload: CreateBotPayload): Promise<CreateBotResponse> {
    return this.request('/api/bots', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async createBotsBatch(payload: BatchCreateBotPayload): Promise<BatchCreateBotResponse> {
    return this.request('/api/bots', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateBot(id: number, payload: UpdateBotPayload): Promise<{ success: boolean }> {
    return this.request(`/api/bots/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async deleteBot(id: number): Promise<{ success: boolean }> {
    return this.request(`/api/bots/${id}`, {
      method: 'DELETE',
    });
  }

  async toggleBot(id: number): Promise<{ success: boolean; is_active: boolean }> {
    return this.request(`/api/bots/${id}/toggle`, {
      method: 'POST',
    });
  }

  async regenerateBotToken(id: number): Promise<RegenerateBotTokenResponse> {
    return this.request(`/api/bots/${id}/regenerate-token`, {
      method: 'POST',
    });
  }

  // Trading endpoints
  async getAccount(): Promise<Account> {
    return this.request<Account>('/api/account');
  }

  async getPositions(): Promise<{ positions: Position[]; total: number }> {
    return this.request('/api/positions');
  }

  async getTrades(limit = 50): Promise<{ trades: Trade[]; total: number }> {
    return this.request(`/api/trades?limit=${limit}`);
  }

  // Get recent trades directly from Alpaca API (fixes $NaN issue)
  async getRecentTrades(days = 7, limit = 20): Promise<{
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
  }> {
    return this.request(`/api/trades/recent?days=${days}&limit=${limit}`);
  }

  async getDashboard(): Promise<DashboardData> {
    return this.request<DashboardData>('/api/dashboard');
  }

  // Settings endpoints
  async setApiKeys(payload: ApiKeyPayload): Promise<{ success: boolean }> {
    return this.request('/api/settings/api-keys', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getApiKeyStatus(): Promise<ApiKeyStatus> {
    return this.request<ApiKeyStatus>('/api/settings/api-keys/status');
  }

  async getWebhookToken(): Promise<WebhookToken> {
    return this.request<WebhookToken>('/api/webhook-token');
  }

  async regenerateWebhookToken(): Promise<WebhookToken & { success: boolean }> {
    return this.request('/api/webhook-token/regenerate', {
      method: 'POST',
    });
  }

  // Notification settings endpoints
  async getNotificationSettings(): Promise<NotificationSettings> {
    return this.request<NotificationSettings>('/api/settings/notifications');
  }

  async updateNotificationSettings(payload: NotificationSettingsPayload): Promise<NotificationSettings> {
    return this.request<NotificationSettings>('/api/settings/notifications', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async sendTestEmail(): Promise<TestEmailResponse> {
    return this.request<TestEmailResponse>('/api/settings/notifications/test', {
      method: 'POST',
    });
  }

  // Strategy endpoints
  async getStrategies(): Promise<StrategyListResponse> {
    return this.request<StrategyListResponse>('/api/strategies');
  }

  async subscribeToStrategy(
    strategyId: number,
    botConfigId: number
  ): Promise<{ success: boolean }> {
    return this.request(`/api/strategies/${strategyId}/subscribe`, {
      method: 'POST',
      body: JSON.stringify({ bot_config_id: botConfigId }),
    });
  }

  async unsubscribeFromStrategy(strategyId: number): Promise<{ success: boolean }> {
    return this.request(`/api/strategies/${strategyId}/unsubscribe`, {
      method: 'POST',
    });
  }

  // Stock quote endpoint (fetches from Alpaca)
  async getStockQuote(symbol: string): Promise<{
    symbol: string;
    name: string;
    price: number;
    change: number;
    changePercent: number;
    open: number;
    high: number;
    low: number;
    previousClose: number;
    week52High: number;
    week52Low: number;
    volume: number;
    avgVolume: number;
    marketCap: string;
  }> {
    return this.request(`/api/stocks/quote?symbol=${encodeURIComponent(symbol)}`);
  }

  // Search stocks endpoint (supports stocks and crypto)
  async searchStocks(query: string, type?: 'stock' | 'crypto' | 'all'): Promise<{
    results: Array<{ symbol: string; name: string; asset_type: 'stock' | 'crypto' }>;
  }> {
    const params = new URLSearchParams({ query });
    if (type) params.append('type', type);
    return this.request(`/api/stocks/search?${params.toString()}`);
  }

  // Get popular symbols endpoint
  async getPopularSymbols(type?: 'stock' | 'crypto'): Promise<{
    results: Array<{ symbol: string; name: string; asset_type: 'stock' | 'crypto' }>;
  }> {
    const params = new URLSearchParams();
    if (type) params.append('type', type);
    const query = params.toString();
    return this.request(`/api/stocks/popular${query ? `?${query}` : ''}`);
  }

  // Trade detail endpoint (comprehensive market context)
  async getTradeDetail(tradeId: number): Promise<TradeDetailResponse> {
    return this.request<TradeDetailResponse>(`/api/trades/${tradeId}`);
  }

  // Performance dashboard endpoint
  async getPerformance(params?: { 
    strategy_type?: string; 
    symbol?: string 
  }): Promise<PerformanceResponse> {
    const searchParams = new URLSearchParams();
    if (params?.strategy_type) searchParams.append('strategy_type', params.strategy_type);
    if (params?.symbol) searchParams.append('symbol', params.symbol);
    const query = searchParams.toString();
    return this.request<PerformanceResponse>(`/api/performance${query ? `?${query}` : ''}`);
  }

  // Trade outcomes with P&L
  async getTradeOutcomes(params?: { 
    status?: string; 
    limit?: number 
  }): Promise<TradeOutcomesResponse> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append('status', params.status);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    const query = searchParams.toString();
    return this.request<TradeOutcomesResponse>(`/api/trades/outcomes${query ? `?${query}` : ''}`);
  }

  // AI Insights endpoint
  async getInsights(minConfidence?: number): Promise<InsightsResponse> {
    const searchParams = new URLSearchParams();
    if (minConfidence !== undefined) searchParams.append('min_confidence', String(Math.round(minConfidence * 100)));
    const query = searchParams.toString();
    return this.request<InsightsResponse>(`/api/insights${query ? `?${query}` : ''}`);
  }

  // Run AI Analysis (POST /api/analyze)
  async runAnalysis(minTrades: number = 10): Promise<AnalysisResponse> {
    return this.request<AnalysisResponse>('/api/analyze', {
      method: 'POST',
      body: JSON.stringify({ min_trades: minTrades }),
    });
  }

  // Get Raw Patterns (GET /api/analyze/patterns)
  async getPatterns(params?: {
    pattern_type?: 'rsi' | 'vix' | 'timeframe' | 'time_of_day' | 'trend' | 'all';
    min_trades?: number;
  }): Promise<PatternsResponse> {
    const searchParams = new URLSearchParams();
    if (params?.pattern_type) searchParams.append('pattern_type', params.pattern_type);
    if (params?.min_trades) searchParams.append('min_trades', params.min_trades.toString());
    const query = searchParams.toString();
    return this.request<PatternsResponse>(`/api/analyze/patterns${query ? `?${query}` : ''}`);
  }
}

export const api = new ApiClient(API_BASE_URL);
