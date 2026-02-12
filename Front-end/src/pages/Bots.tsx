import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Pencil, Trash2, Copy, Bot as BotIcon, Clock, DollarSign, TrendingUp, AlertCircle, Link2, Activity, Search, ArrowUp, ArrowDown, Loader2, X, Power, PowerOff, Download, Bitcoin } from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { Bot as BotType, CreateBotPayload, UpdateBotPayload, WebhookToken, BatchCreateBotPayload } from '@/types/api';

const TIMEFRAMES = ['1 Min', '5 Min', '15 Min', '30 Min', '1 Hour', '4 Hour', 'Daily'];

// Convert display timeframe to API format: "15 Min" -> "15min", "1 Hour" -> "1h", "Daily" -> "1d"
const toApiTimeframe = (display: string): string => {
  const map: Record<string, string> = {
    '1 Min': '1min',
    '5 Min': '5min',
    '15 Min': '15min',
    '30 Min': '30min',
    '1 Hour': '1h',
    '4 Hour': '4h',
    'Daily': '1d',
  };
  return map[display] || display.toLowerCase().replace(' ', '');
};

// Symbol search result type
interface SymbolResult {
  symbol: string;
  name: string;
  asset_type: 'stock' | 'crypto';
}

// Helper to detect if a symbol is crypto
const isCryptoSymbol = (symbol: string): boolean => {
  const normalized = symbol.toUpperCase();
  // Check for /USD suffix or common crypto symbols without suffix
  if (normalized.includes('/USD')) return true;
  const cryptoSymbols = ['BTC', 'ETH', 'SOL', 'DOGE', 'XRP', 'ADA', 'LTC', 'LINK', 'DOT', 'AVAX', 'MATIC', 'SHIB', 'UNI', 'AAVE', 'ATOM', 'BCH', 'ALGO', 'XLM', 'NEAR', 'APE'];
  // Check if symbol is exactly a crypto symbol (without USD) - common for display
  return cryptoSymbols.some(crypto => normalized === crypto || normalized === `${crypto}USD`);
};

interface StockQuote {
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
}

// Batch form data interface
interface BatchFormData {
  symbols: string[];
  timeframes: string[];
  position_size: number;
  strategy_name?: string;
}

export default function Bots() {
  const [bots, setBots] = useState<BotType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedBot, setSelectedBot] = useState<BotType | null>(null);
  const [formData, setFormData] = useState<CreateBotPayload & { is_active?: boolean }>({
    symbol: 'SPY',
    timeframe: '15 Min',
    position_size: 100,
    is_active: true,
  });
  // Batch creation state
  const [batchFormData, setBatchFormData] = useState<BatchFormData & { is_active?: boolean }>({
    symbols: [],
    timeframes: ['15 Min'],
    position_size: 100,
    strategy_name: '',
    is_active: true,
  });
  const [isBatchMode, setIsBatchMode] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [webhook, setWebhook] = useState<WebhookToken | null>(null);
  
  // Symbol search states
  const [symbolSearchOpen, setSymbolSearchOpen] = useState(false);
  const [symbolInput, setSymbolInput] = useState('');
  const [stockQuote, setStockQuote] = useState<StockQuote | null>(null);
  const [isLoadingQuote, setIsLoadingQuote] = useState(false);
  const [searchResults, setSearchResults] = useState<SymbolResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Fetch symbol search results from API
  useEffect(() => {
    const searchSymbols = async () => {
      if (!symbolInput || symbolInput.length < 1) {
        // Load popular symbols when no input
        try {
          const data = await api.getPopularSymbols();
          setSearchResults(data.results || []);
        } catch {
          setSearchResults([]);
        }
        return;
      }
      
      setIsSearching(true);
      try {
        const data = await api.searchStocks(symbolInput);
        setSearchResults(data.results || []);
      } catch (error) {
        console.error('Symbol search failed:', error);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    };

    const debounce = setTimeout(searchSymbols, 300);
    return () => clearTimeout(debounce);
  }, [symbolInput]);

  // Load popular symbols on mount
  useEffect(() => {
    api.getPopularSymbols().then(data => setSearchResults(data.results || [])).catch(() => {});
  }, []);

  // Fetch stock quote from Alpaca via backend
  const fetchStockQuote = async (symbol: string) => {
    if (!symbol) {
      setStockQuote(null);
      return;
    }
    
    setIsLoadingQuote(true);
    try {
      const quote = await api.getStockQuote(symbol.toUpperCase());
      setStockQuote(quote);
    } catch (error) {
      console.error('Failed to fetch stock quote:', error);
      toast.error(`Could not fetch data for ${symbol.toUpperCase()}`);
      setStockQuote(null);
    } finally {
      setIsLoadingQuote(false);
    }
  };

  // Fetch quote when symbol changes in form
  useEffect(() => {
    if (formData.symbol && isFormOpen) {
      fetchStockQuote(formData.symbol);
    }
  }, [formData.symbol, isFormOpen]);

  const handleSymbolSelect = (symbol: string) => {
    const upperSymbol = symbol.toUpperCase();
    setFormData({ ...formData, symbol: upperSymbol });
    setSymbolInput(upperSymbol);
    setSymbolSearchOpen(false);
    fetchStockQuote(upperSymbol);
  };

  const handleSymbolInputChange = (value: string) => {
    setSymbolInput(value.toUpperCase());
  };

  const handleSymbolInputBlur = () => {
    if (symbolInput && symbolInput !== formData.symbol) {
      handleSymbolSelect(symbolInput);
    }
  };

  const fetchData = async () => {
    try {
      const [botsRes, webhookRes] = await Promise.all([
        api.getBots(),
        api.getWebhookToken().catch(() => null)
      ]);
      setBots(botsRes.bots);
      setWebhook(webhookRes);
    } catch (error) {
      toast.error('Failed to load bots');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleToggle = async (bot: BotType) => {
    try {
      const result = await api.toggleBot(bot.id);
      setBots(bots.map(b => b.id === bot.id ? { ...b, is_active: result.is_active } : b));
      toast.success(`Bot ${result.is_active ? 'activated' : 'deactivated'}`);
    } catch (error) {
      toast.error('Failed to toggle bot');
    }
  };

  const handleEnableAll = async () => {
    const inactiveBots = bots.filter(b => !b.is_active);
    if (inactiveBots.length === 0) {
      toast.info('All bots are already active');
      return;
    }
    
    try {
      const results = await Promise.allSettled(
        inactiveBots.map(bot => api.toggleBot(bot.id))
      );
      const successCount = results.filter(r => r.status === 'fulfilled').length;
      
      if (successCount > 0) {
        toast.success(`Enabled ${successCount} bot${successCount === 1 ? '' : 's'}`);
        fetchData();
      }
      if (successCount < inactiveBots.length) {
        toast.error(`${inactiveBots.length - successCount} bot(s) failed to enable`);
      }
    } catch (error) {
      toast.error('Failed to enable bots');
    }
  };

  const handleDisableAll = async () => {
    const activeBots = bots.filter(b => b.is_active);
    if (activeBots.length === 0) {
      toast.info('All bots are already inactive');
      return;
    }
    
    try {
      const results = await Promise.allSettled(
        activeBots.map(bot => api.toggleBot(bot.id))
      );
      const successCount = results.filter(r => r.status === 'fulfilled').length;
      
      if (successCount > 0) {
        toast.success(`Disabled ${successCount} bot${successCount === 1 ? '' : 's'}`);
        fetchData();
      }
      if (successCount < activeBots.length) {
        toast.error(`${activeBots.length - successCount} bot(s) failed to disable`);
      }
    } catch (error) {
      toast.error('Failed to disable bots');
    }
  };

  const exportBotForTradingView = (bot: BotType) => {
    const config = {
      webhook_url: webhook?.webhook_url || 'YOUR_WEBHOOK_URL',
      symbol: bot.symbol,
      timeframe: bot.timeframe,
      entry_alert: '{"action": "{{strategy.order.action}}", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}',
      exit_alert: '{"action": "CLOSE", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}',
    };
    
    const exportText = `
=== TradingView Setup for ${bot.symbol} (${bot.timeframe}) ===

WEBHOOK URL:
${config.webhook_url}

ENTRY ALERT MESSAGE:
${config.entry_alert}

EXIT ALERT MESSAGE:
${config.exit_alert}

SETUP INSTRUCTIONS:
1. In TradingView, create an alert on your strategy
2. Set "Webhook URL" to the URL above
3. Paste the appropriate alert message into the message field
4. Enable the Webhook checkbox
5. Set alert to trigger "Once Per Bar Close" for best results
`.trim();

    // Copy to clipboard
    navigator.clipboard.writeText(exportText);
    toast.success(`TradingView config for ${bot.symbol} copied to clipboard`);
  };

  const exportAllBots = () => {
    if (bots.length === 0) {
      toast.info('No bots to export');
      return;
    }

    // CSV headers
    const headers = [
      'ID',
      'Symbol',
      'Timeframe',
      'Position Size',
      'Status',
      'Strategy',
      'Order Status',
      'Position Side',
      'Last Signal',
      'Last Signal Time',
      'Total Trades',
      'Total P&L',
      'Created',
      'Last Error',
      'Entry Alert',
      'Exit Alert'
    ];

    // CSV rows
    const rows = bots.map(bot => [
      bot.id,
      bot.symbol,
      bot.timeframe,
      bot.position_size,
      bot.is_active ? 'ACTIVE' : 'INACTIVE',
      bot.strategy_name || '',
      bot.order_status || 'IDLE',
      bot.current_position_side || 'FLAT',
      bot.last_signal || '',
      bot.last_signal_time ? new Date(bot.last_signal_time).toISOString() : '',
      bot.total_trades || 0,
      bot.total_pnl || 0,
      bot.created_at ? new Date(bot.created_at).toISOString() : '',
      bot.last_error || '',
      '{"action": "{{strategy.order.action}}", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}',
      '{"action": "CLOSE", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}'
    ]);

    // Escape CSV values
    const escapeCSV = (value: string | number) => {
      const str = String(value);
      if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    };

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(escapeCSV).join(','))
    ].join('\n');

    // Download as CSV file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trading-bots-export-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success(`Exported ${bots.length} bot(s) to CSV`);
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      if (selectedBot) {
        // Edit mode - single bot update (only updatable fields)
        const payload: UpdateBotPayload = {
          position_size: formData.position_size,
          strategy_name: formData.strategy_name,
        };
        await api.updateBot(selectedBot.id, payload);
        toast.success('Bot updated');
      } else if (isBatchMode && batchFormData.symbols.length > 0 && batchFormData.timeframes.length > 0) {
        // Batch creation mode (client-side fan-out)
        // The backend may not support batch payloads yet, so we create one bot per (symbol x timeframe).
        const combos: CreateBotPayload[] = batchFormData.symbols.flatMap((symbol) =>
          batchFormData.timeframes.map((tf) => ({
            symbol,
            timeframe: toApiTimeframe(tf),
            position_size: batchFormData.position_size,
            strategy_name: batchFormData.strategy_name || undefined,
            is_active: batchFormData.is_active ?? true,
          }))
        );

        const results = await Promise.allSettled(combos.map((p) => api.createBot(p)));
        const createdCount = results.filter((r) => r.status === 'fulfilled').length;
        const errorCount = results.length - createdCount;

        if (createdCount > 0) toast.success(`Created ${createdCount} bot${createdCount === 1 ? '' : 's'}`);
        if (errorCount > 0) toast.error(`${errorCount} bot${errorCount === 1 ? '' : 's'} failed to create`);
      } else {
        // Single bot creation - convert timeframe to API format
        const payload: CreateBotPayload = {
          symbol: formData.symbol,
          timeframe: toApiTimeframe(formData.timeframe),
          position_size: formData.position_size,
          strategy_name: formData.strategy_name,
          is_active: formData.is_active ?? true,
        };
        await api.createBot(payload);
        toast.success('Bot created');
      }
      setIsFormOpen(false);
      setSelectedBot(null);
      setIsBatchMode(false);
      fetchData();
    } catch (error) {
      console.error('Bot creation error:', error);
      toast.error(selectedBot ? 'Failed to update bot' : 'Failed to create bot(s)');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedBot) return;
    setIsSubmitting(true);
    try {
      await api.deleteBot(selectedBot.id);
      toast.success('Bot deleted');
      setIsDeleteOpen(false);
      setSelectedBot(null);
      fetchData();
    } catch (error) {
      toast.error('Failed to delete bot');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openEditForm = (bot: BotType) => {
    setSelectedBot(bot);
    setFormData({
      symbol: bot.symbol,
      timeframe: bot.timeframe,
      position_size: bot.position_size,
      strategy_name: bot.strategy_name,
    });
    setSymbolInput(bot.symbol);
    setStockQuote(null);
    setIsFormOpen(true);
  };

  const openCreateForm = () => {
    setSelectedBot(null);
    setFormData({ symbol: 'SPY', timeframe: '15 Min', position_size: 100, is_active: true });
    setBatchFormData({ symbols: [], timeframes: ['15 Min'], position_size: 100, strategy_name: '', is_active: true });
    setSymbolInput('SPY');
    setStockQuote(null);
    setIsBatchMode(false);
    setIsFormOpen(true);
  };

  // Batch mode helpers
  const addSymbolToBatch = (symbol: string) => {
    const upperSymbol = symbol.toUpperCase();
    if (!batchFormData.symbols.includes(upperSymbol)) {
      setBatchFormData({ ...batchFormData, symbols: [...batchFormData.symbols, upperSymbol] });
    }
    setSymbolInput('');
    setSymbolSearchOpen(false);
  };

  const removeSymbolFromBatch = (symbol: string) => {
    setBatchFormData({ ...batchFormData, symbols: batchFormData.symbols.filter(s => s !== symbol) });
  };

  const toggleTimeframe = (timeframe: string) => {
    if (batchFormData.timeframes.includes(timeframe)) {
      if (batchFormData.timeframes.length > 1) {
        setBatchFormData({ ...batchFormData, timeframes: batchFormData.timeframes.filter(t => t !== timeframe) });
      }
    } else {
      setBatchFormData({ ...batchFormData, timeframes: [...batchFormData.timeframes, timeframe] });
    }
  };

  // Calculate batch stats
  const batchBotCount = batchFormData.symbols.length * batchFormData.timeframes.length;
  const totalPosition = batchBotCount * batchFormData.position_size;

  const copyWebhook = () => {
    if (webhook?.webhook_url) {
      navigator.clipboard.writeText(webhook.webhook_url);
      toast.success('Webhook URL copied');
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <Skeleton className="h-10 w-48" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-64" />)}
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Trading Bots</h1>
            <p className="text-muted-foreground mt-1">Manage your automated trading strategies</p>
          </div>
          <div className="flex items-center gap-2">
            {bots.length > 0 && (
              <Button variant="outline" onClick={exportAllBots} className="gap-2">
                <Download className="h-4 w-4" /> Export All
              </Button>
            )}
            {bots.some(b => b.is_active) && (
              <Button variant="outline" onClick={handleDisableAll} className="gap-2">
                <PowerOff className="h-4 w-4" /> Disable All
              </Button>
            )}
            {bots.some(b => !b.is_active) && (
              <Button variant="outline" onClick={handleEnableAll} className="gap-2">
                <Power className="h-4 w-4" /> Enable All
              </Button>
            )}
            <Button onClick={openCreateForm} className="gap-2">
              <Plus className="h-4 w-4" /> Create Bot
            </Button>
          </div>
        </div>

        {/* Setup Instructions */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="border-primary/20 bg-primary/5">
            <CardContent className="py-4">
              <div className="flex items-start gap-3">
                <Link2 className="h-5 w-5 text-primary mt-0.5" />
                <div className="space-y-3 w-full">
                  <div>
                    <p className="text-sm font-medium text-primary">TradingView Webhook Setup</p>
                    <p className="text-xs text-muted-foreground">
                      Use one webhook URL for all your bots. TradingView auto-fills symbol, action, and timeframe.
                    </p>
                  </div>
                  
                  {/* Webhook URL */}
                  {webhook ? (
                    <div className="flex items-center gap-2 p-2 bg-background rounded border border-border">
                      <code className="flex-1 text-xs text-muted-foreground break-all">{webhook.webhook_url}</code>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 shrink-0"
                        onClick={copyWebhook}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  ) : (
                    <div className="p-2 bg-background rounded border border-border">
                      <p className="text-xs text-muted-foreground">
                        No webhook configured. <a href="/settings" className="text-primary underline">Generate one in Settings</a>
                      </p>
                    </div>
                  )}

                  <div className="grid gap-2">
                    <div className="flex items-center justify-between gap-2 p-2 bg-background rounded border border-border">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-muted-foreground mb-0.5">Entry Alert:</p>
                        <code className="text-xs text-primary break-all">
                          {`{"action": "{{strategy.order.action}}", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}`}
                        </code>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 shrink-0"
                        onClick={() => {
                          navigator.clipboard.writeText('{"action": "{{strategy.order.action}}", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}');
                          toast.success('Entry alert copied');
                        }}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                    <div className="flex items-center justify-between gap-2 p-2 bg-background rounded border border-border">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-muted-foreground mb-0.5">Exit Alert:</p>
                        <code className="text-xs text-primary break-all">
                          {`{"action": "CLOSE", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}`}
                        </code>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 shrink-0"
                        onClick={() => {
                          navigator.clipboard.writeText('{"action": "CLOSE", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}');
                          toast.success('Exit alert copied');
                        }}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Bots Grid */}
        {bots.length === 0 ? (
          <Card className="py-16">
            <CardContent className="flex flex-col items-center justify-center text-center">
              <BotIcon className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No bots yet</h3>
              <p className="text-muted-foreground mb-4">Create your first trading bot to get started</p>
              <Button onClick={openCreateForm}>
                <Plus className="h-4 w-4 mr-2" /> Create Bot
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <AnimatePresence>
              {bots.map((bot, index) => (
                  <motion.div
                    key={bot.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card className={`relative overflow-hidden transition-all ${bot.is_active ? 'border-primary/30' : 'border-border'}`}>
                      {bot.is_active && (
                        <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-primary to-cyan-400" />
                      )}
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {isCryptoSymbol(bot.symbol) && (
                              <Bitcoin className="h-5 w-5 text-amber-500" />
                            )}
                            <span className="text-xl font-bold text-foreground">{bot.symbol}</span>
                            {isCryptoSymbol(bot.symbol) && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-600 dark:text-amber-400">
                                Crypto
                              </span>
                            )}
                            <span className={`text-xs px-2 py-0.5 rounded-full ${bot.is_active ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'}`}>
                              {bot.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                          <Switch checked={bot.is_active} onCheckedChange={() => handleToggle(bot)} />
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Clock className="h-4 w-4" />
                            <span>{bot.timeframe}</span>
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <DollarSign className="h-4 w-4" />
                            <span>${bot.position_size}</span>
                          </div>
                          {/* Trading hours indicator */}
                          <div className="flex items-center gap-2 text-muted-foreground col-span-2">
                            <Activity className="h-4 w-4" />
                            <span className={isCryptoSymbol(bot.symbol) ? 'text-emerald-500' : ''}>
                              {isCryptoSymbol(bot.symbol) ? '24/7 Trading' : 'Market Hours'}
                            </span>
                          </div>
                          {bot.strategy_name && (
                            <div className="flex items-center gap-2 text-muted-foreground col-span-2">
                              <TrendingUp className="h-4 w-4" />
                              <span>{bot.strategy_name}</span>
                            </div>
                          )}
                        </div>

                        {/* Bot Stats */}
                        {(bot.last_signal || bot.order_status) && (
                          <div className="pt-2 border-t border-border space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-muted-foreground flex items-center gap-1">
                                <Activity className="h-3 w-3" /> Order Status
                              </span>
                              <span className={`px-1.5 py-0.5 rounded text-xs ${
                                bot.order_status === 'IDLE' ? 'bg-muted text-muted-foreground' :
                                bot.order_status === 'FILLED' ? 'bg-emerald-500/10 text-emerald-500' :
                                bot.order_status?.includes('SUBMITTED') ? 'bg-yellow-500/10 text-yellow-500' :
                                bot.order_status === 'FAILED' ? 'bg-destructive/10 text-destructive' :
                                'bg-muted text-muted-foreground'
                              }`}>
                                {bot.order_status || 'IDLE'}
                              </span>
                            </div>
                            {/* Show error reason when FAILED */}
                            {bot.order_status === 'FAILED' && bot.last_error && (
                              <div className="flex items-start gap-2 p-2 mt-1 bg-destructive/5 border border-destructive/20 rounded text-xs">
                                <AlertCircle className="h-3 w-3 text-destructive mt-0.5 shrink-0" />
                                <span className="text-destructive">{bot.last_error}</span>
                              </div>
                            )}
                            {bot.last_signal && (
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-muted-foreground">Last Signal</span>
                                <span className={`${bot.last_signal === 'BUY' ? 'text-emerald-500' : 'text-red-500'}`}>
                                  {bot.last_signal}
                                </span>
                              </div>
                            )}
                            {bot.total_trades !== undefined && (
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-muted-foreground">Total Trades</span>
                                <span className="text-foreground">{bot.total_trades}</span>
                              </div>
                            )}
                          </div>
                        )}


                        <div className="flex gap-2 pt-2 border-t border-border">
                          <Button variant="ghost" size="sm" className="flex-1" onClick={() => openEditForm(bot)}>
                            <Pencil className="h-4 w-4 mr-1" /> Edit
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="flex-1"
                            onClick={() => exportBotForTradingView(bot)}
                            title="Export TradingView config"
                          >
                            <Download className="h-4 w-4 mr-1" /> Export
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive hover:text-destructive"
                            onClick={() => { setSelectedBot(bot); setIsDeleteOpen(true); }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedBot ? 'Edit Bot' : 'Create Bots'}</DialogTitle>
            <DialogDescription>
              {selectedBot ? 'Update your bot configuration' : 'Configure one or multiple trading bots at once'}
            </DialogDescription>
          </DialogHeader>

          {/* Mode Toggle - only show in create mode */}
          {!selectedBot && (
            <div className="flex items-center gap-4 p-3 bg-muted/30 rounded-lg border border-border">
              <div className="flex items-center gap-2 flex-1">
                <Switch 
                  id="batch-mode" 
                  checked={isBatchMode}
                  onCheckedChange={setIsBatchMode}
                />
                <Label htmlFor="batch-mode" className="cursor-pointer">
                  Batch Mode
                </Label>
              </div>
              <p className="text-xs text-muted-foreground">
                {isBatchMode ? 'Create multiple bots at once' : 'Create a single bot'}
              </p>
            </div>
          )}

          <div className="space-y-4 py-4">
            {/* Single Bot Mode or Edit Mode */}
            {(!isBatchMode || selectedBot) ? (
              <>
                {/* Symbol Search */}
                <div className="space-y-2">
                  <Label>Symbol</Label>
                  <Popover open={symbolSearchOpen} onOpenChange={setSymbolSearchOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={symbolSearchOpen}
                        className="w-full justify-between font-normal"
                      >
                        <span className="flex items-center gap-2">
                          <Search className="h-4 w-4 text-muted-foreground" />
                          {formData.symbol || 'Search symbol...'}
                        </span>
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-[350px] p-0" align="start">
                      <Command shouldFilter={false}>
                        <CommandInput 
                          placeholder="Type symbol (e.g., AAPL, BTC/USD)..." 
                          value={symbolInput}
                          onValueChange={handleSymbolInputChange}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && symbolInput) {
                              handleSymbolSelect(symbolInput);
                            }
                          }}
                        />
                        <CommandList>
                          <CommandEmpty>
                            {symbolInput ? (
                              <button
                                className="w-full p-2 text-left hover:bg-accent cursor-pointer"
                                onClick={() => handleSymbolSelect(symbolInput)}
                              >
                                <span className="font-medium">{symbolInput.toUpperCase()}</span>
                                <span className="text-muted-foreground ml-2">Press Enter to use</span>
                              </button>
                            ) : (
                              'Start typing a symbol...'
                            )}
                          </CommandEmpty>
                          {isSearching ? (
                            <div className="flex items-center justify-center py-4">
                              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                            </div>
                          ) : (
                            <>
                              {searchResults.filter(s => s.asset_type === 'stock').length > 0 && (
                                <CommandGroup heading="Stocks">
                                  {searchResults.filter(s => s.asset_type === 'stock').map((s) => (
                                    <CommandItem
                                      key={s.symbol}
                                      value={s.symbol}
                                      onSelect={() => handleSymbolSelect(s.symbol)}
                                      className="cursor-pointer"
                                    >
                                      <span className="font-medium w-16">{s.symbol}</span>
                                      <span className="text-muted-foreground text-sm truncate">{s.name}</span>
                                    </CommandItem>
                                  ))}
                                </CommandGroup>
                              )}
                              {searchResults.filter(s => s.asset_type === 'crypto').length > 0 && (
                                <CommandGroup heading="Crypto">
                                  {searchResults.filter(s => s.asset_type === 'crypto').map((s) => (
                                    <CommandItem
                                      key={s.symbol}
                                      value={s.symbol}
                                      onSelect={() => handleSymbolSelect(s.symbol)}
                                      className="cursor-pointer"
                                    >
                                      <Bitcoin className="h-4 w-4 text-amber-500 mr-1" />
                                      <span className="font-medium w-20">{s.symbol}</span>
                                      <span className="text-muted-foreground text-sm truncate">{s.name}</span>
                                    </CommandItem>
                                  ))}
                                </CommandGroup>
                              )}
                            </>
                          )}
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                  <p className="text-xs text-muted-foreground">Type any stock or crypto symbol (e.g., AAPL, BTC/USD)</p>
                </div>

                {/* Stock Quote Details */}
                {formData.symbol && (
                  <div className="rounded-lg border border-border bg-muted/30 p-3 space-y-3">
                    {isLoadingQuote ? (
                      <div className="flex items-center justify-center py-4">
                        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                      </div>
                    ) : stockQuote ? (
                      <>
                        {/* Header with price */}
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-lg font-bold">{stockQuote.symbol}</span>
                              <span className={`flex items-center gap-0.5 text-sm font-medium ${(stockQuote.change ?? 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                {(stockQuote.change ?? 0) >= 0 ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                                {(stockQuote.change ?? 0) >= 0 ? '+' : ''}{(stockQuote.changePercent ?? 0).toFixed(2)}%
                              </span>
                            </div>
                            <p className="text-xs text-muted-foreground truncate max-w-[200px]">{stockQuote.name}</p>
                          </div>
                          <div className="text-right">
                            <span className="text-xl font-bold">${(stockQuote.price ?? 0).toFixed(2)}</span>
                            <p className={`text-xs ${(stockQuote.change ?? 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                              {(stockQuote.change ?? 0) >= 0 ? '+' : ''}${(stockQuote.change ?? 0).toFixed(2)}
                            </p>
                          </div>
                        </div>

                        {/* Price stats grid */}
                        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs border-t border-border pt-3">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Open</span>
                            <span className="font-medium">${(stockQuote.open ?? 0).toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Prev Close</span>
                            <span className="font-medium">${(stockQuote.previousClose ?? 0).toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Day High</span>
                            <span className="font-medium text-emerald-500">${(stockQuote.high ?? 0).toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Day Low</span>
                            <span className="font-medium text-red-500">${(stockQuote.low ?? 0).toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">52W High</span>
                            <span className="font-medium text-emerald-500">${(stockQuote.week52High ?? 0).toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">52W Low</span>
                            <span className="font-medium text-red-500">${(stockQuote.week52Low ?? 0).toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Volume</span>
                            <span className="font-medium">{((stockQuote.volume ?? 0) / 1000000).toFixed(2)}M</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Market Cap</span>
                            <span className="font-medium">{stockQuote.marketCap ?? 'N/A'}</span>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="text-center py-2 text-muted-foreground text-sm">
                        Unable to load quote data
                      </div>
                    )}
                  </div>
                )}

                <div className="space-y-2">
                  <Label>Timeframe</Label>
                  <Select value={formData.timeframe} onValueChange={(v) => setFormData({ ...formData, timeframe: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TIMEFRAMES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Position Size ($)</Label>
                  <Input
                    type="number"
                    value={formData.position_size}
                    onChange={(e) => setFormData({ ...formData, position_size: Number(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Strategy Name (optional)</Label>
                  <Input
                    value={formData.strategy_name || ''}
                    onChange={(e) => setFormData({ ...formData, strategy_name: e.target.value })}
                    placeholder="e.g., momentum, mean_reversion"
                  />
                </div>
                {/* Active Toggle - only show in create mode */}
                {!selectedBot && (
                  <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg border border-border">
                    <div>
                      <Label htmlFor="single-active" className="cursor-pointer">Start Active</Label>
                      <p className="text-xs text-muted-foreground">Enable bot immediately after creation</p>
                    </div>
                    <Switch
                      id="single-active"
                      checked={formData.is_active ?? true}
                      onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                    />
                  </div>
                )}
              </>
            ) : (
              /* Batch Mode */
              <>
                {/* Multiple Symbols Input */}
                <div className="space-y-2">
                  <Label>Symbols</Label>
                  {/* Selected symbols display */}
                  {batchFormData.symbols.length > 0 && (
                    <div className="flex flex-wrap gap-2 p-2 bg-muted/30 rounded-lg border border-border min-h-[40px]">
                      {batchFormData.symbols.map((symbol) => (
                        <Badge key={symbol} variant="secondary" className="gap-1 pr-1">
                          {symbol}
                          <button
                            onClick={() => removeSymbolFromBatch(symbol)}
                            className="ml-1 hover:bg-destructive/20 rounded p-0.5"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                  
                  {/* Symbol search for batch */}
                  <Popover open={symbolSearchOpen} onOpenChange={setSymbolSearchOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={symbolSearchOpen}
                        className="w-full justify-between font-normal"
                      >
                        <span className="flex items-center gap-2">
                          <Search className="h-4 w-4 text-muted-foreground" />
                          Add symbol...
                        </span>
                        <Plus className="h-4 w-4 text-muted-foreground" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-[350px] p-0" align="start">
                      <Command shouldFilter={false}>
                        <CommandInput 
                          placeholder="Type symbol and press Enter..." 
                          value={symbolInput}
                          onValueChange={handleSymbolInputChange}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && symbolInput) {
                              addSymbolToBatch(symbolInput);
                            }
                          }}
                        />
                        <CommandList>
                          <CommandEmpty>
                            {symbolInput ? (
                              <button
                                className="w-full p-2 text-left hover:bg-accent cursor-pointer"
                                onClick={() => addSymbolToBatch(symbolInput)}
                              >
                                <span className="font-medium">{symbolInput.toUpperCase()}</span>
                                <span className="text-muted-foreground ml-2">Press Enter to add</span>
                              </button>
                            ) : (
                              'Start typing a symbol...'
                            )}
                          </CommandEmpty>
                          {isSearching ? (
                            <div className="flex items-center justify-center py-4">
                              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                            </div>
                          ) : (
                            <>
                              {searchResults.filter(s => s.asset_type === 'stock' && !batchFormData.symbols.includes(s.symbol)).length > 0 && (
                                <CommandGroup heading="Stocks">
                                  {searchResults
                                    .filter(s => s.asset_type === 'stock' && !batchFormData.symbols.includes(s.symbol))
                                    .map((s) => (
                                      <CommandItem
                                        key={s.symbol}
                                        value={s.symbol}
                                        onSelect={() => addSymbolToBatch(s.symbol)}
                                        className="cursor-pointer"
                                      >
                                        <span className="font-medium w-16">{s.symbol}</span>
                                        <span className="text-muted-foreground text-sm truncate">{s.name}</span>
                                      </CommandItem>
                                    ))}
                                </CommandGroup>
                              )}
                              {searchResults.filter(s => s.asset_type === 'crypto' && !batchFormData.symbols.includes(s.symbol)).length > 0 && (
                                <CommandGroup heading="Crypto">
                                  {searchResults
                                    .filter(s => s.asset_type === 'crypto' && !batchFormData.symbols.includes(s.symbol))
                                    .map((s) => (
                                      <CommandItem
                                        key={s.symbol}
                                        value={s.symbol}
                                        onSelect={() => addSymbolToBatch(s.symbol)}
                                        className="cursor-pointer"
                                      >
                                        <Bitcoin className="h-4 w-4 text-amber-500 mr-1" />
                                        <span className="font-medium w-20">{s.symbol}</span>
                                        <span className="text-muted-foreground text-sm truncate">{s.name}</span>
                                      </CommandItem>
                                    ))}
                                </CommandGroup>
                              )}
                            </>
                          )}
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                  <p className="text-xs text-muted-foreground">Add multiple symbols to create bots for each</p>
                </div>

                {/* Timeframes Checkboxes */}
                <div className="space-y-2">
                  <Label>Timeframes</Label>
                  <div className="grid grid-cols-4 gap-2">
                    {TIMEFRAMES.map(timeframe => (
                      <div
                        key={timeframe}
                        className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-colors ${
                          batchFormData.timeframes.includes(timeframe)
                            ? 'bg-primary/10 border-primary/50'
                            : 'bg-muted/30 border-border hover:border-primary/30'
                        }`}
                        onClick={() => toggleTimeframe(timeframe)}
                      >
                        <Checkbox
                          id={`tf-${timeframe}`}
                          checked={batchFormData.timeframes.includes(timeframe)}
                          onCheckedChange={() => toggleTimeframe(timeframe)}
                        />
                        <Label htmlFor={`tf-${timeframe}`} className="text-xs cursor-pointer">
                          {timeframe}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Position Size ($) per bot</Label>
                  <Input
                    type="number"
                    value={batchFormData.position_size}
                    onChange={(e) => setBatchFormData({ ...batchFormData, position_size: Number(e.target.value) })}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Strategy Name (optional)</Label>
                  <Input
                    value={batchFormData.strategy_name || ''}
                    onChange={(e) => setBatchFormData({ ...batchFormData, strategy_name: e.target.value })}
                    placeholder="e.g., Tech Momentum"
                  />
                </div>

                {/* Active Toggle for Batch */}
                <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg border border-border">
                  <div>
                    <Label htmlFor="batch-active" className="cursor-pointer">Start Active</Label>
                    <p className="text-xs text-muted-foreground">Enable bots immediately after creation</p>
                  </div>
                  <Switch
                    id="batch-active"
                    checked={batchFormData.is_active ?? true}
                    onCheckedChange={(checked) => setBatchFormData({ ...batchFormData, is_active: checked })}
                  />
                </div>

                {/* Batch Summary */}
                {batchFormData.symbols.length > 0 && batchFormData.timeframes.length > 0 && (
                  <div className="p-3 bg-primary/5 border border-primary/20 rounded-lg space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Will create:</span>
                      <span className="font-bold text-primary">
                        {batchBotCount} bot{batchBotCount !== 1 ? 's' : ''} 
                        <span className="text-muted-foreground font-normal ml-1">
                          ({batchFormData.symbols.length} symbol{batchFormData.symbols.length !== 1 ? 's' : ''} × {batchFormData.timeframes.length} timeframe{batchFormData.timeframes.length !== 1 ? 's' : ''})
                        </span>
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Total position:</span>
                      <span className="font-bold">${totalPosition.toLocaleString()}</span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsFormOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleSubmit} 
              disabled={isSubmitting || (isBatchMode && !selectedBot && (batchFormData.symbols.length === 0 || batchFormData.timeframes.length === 0))}
            >
              {isSubmitting ? 'Creating...' : (
                selectedBot ? 'Update' : (
                  isBatchMode ? `Create ${batchBotCount} Bot${batchBotCount !== 1 ? 's' : ''}` : 'Create'
                )
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" /> Delete Bot
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete the <strong>{selectedBot?.symbol}</strong> bot? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete} disabled={isSubmitting}>
              {isSubmitting ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}