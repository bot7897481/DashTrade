import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowUpRight, ArrowDownRight, Clock, RefreshCw, Download, Search, ChevronDown, ChevronUp, Activity, Zap, TrendingUp, AlertCircle, Eye } from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { Trade } from '@/types/api';

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatCurrency(value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value)) return '-';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

function formatPercent(value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value)) return '-';
  return `${value >= 0 ? '+' : ''}${value.toFixed(3)}%`;
}

function formatMs(value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value)) return '-';
  return `${value.toFixed(0)}ms`;
}

export default function Trades() {
  const navigate = useNavigate();
  const [trades, setTrades] = useState<Trade[]>([]);
  const [filteredTrades, setFilteredTrades] = useState<Trade[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedTrades, setExpandedTrades] = useState<Set<number>>(new Set());

  const fetchTrades = async (showRefresh = false) => {
    if (showRefresh) setIsRefreshing(true);
    try {
      // Use database endpoint - it has all trades including CLOSE orders with auto-updated status
      const dbRes = await api.getTrades(100);
      setTrades(dbRes.trades);
      setFilteredTrades(dbRes.trades);
    } catch (error: any) {
      toast.error('Failed to load trades');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTrades();
  }, []);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredTrades(trades);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredTrades(
        trades.filter(
          (t) =>
            t.symbol.toLowerCase().includes(query) ||
            t.action.toLowerCase().includes(query) ||
            t.status?.toLowerCase().includes(query)
        )
      );
    }
  }, [searchQuery, trades]);

  const toggleExpand = (tradeId: number) => {
    setExpandedTrades(prev => {
      const next = new Set(prev);
      if (next.has(tradeId)) {
        next.delete(tradeId);
      } else {
        next.add(tradeId);
      }
      return next;
    });
  };

  const exportCSV = () => {
    const headers = [
      'Date', 'Symbol', 'Action', 'Quantity', 'Price', 'Notional', 'Status',
      'Bid', 'Ask', 'Spread', 'Spread %', 'Slippage', 'Slippage %',
      'Execution Latency (ms)', 'Time to Fill (ms)', 'Order Type', 'Time in Force'
    ];
    const rows = filteredTrades.map((t) => [
      t.created_at || t.timestamp || '',
      t.symbol,
      t.action,
      t.filled_qty || t.qty || '',
      t.filled_avg_price || t.price || '',
      t.notional || '',
      t.status || 'completed',
      t.bid_price || '',
      t.ask_price || '',
      t.spread || '',
      t.spread_percent || '',
      t.slippage || '',
      t.slippage_percent || '',
      t.execution_latency_ms || '',
      t.time_to_fill_ms || '',
      t.order_type || '',
      t.time_in_force || '',
    ]);
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trades-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Trades exported');
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-12 w-full max-w-md" />
          <Skeleton className="h-96 w-full" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Trade History</h1>
            <p className="text-muted-foreground mt-1">{trades.length} total trades</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => fetchTrades(true)} disabled={isRefreshing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline" onClick={exportCSV}>
              <Download className="h-4 w-4 mr-2" /> Export CSV
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by symbol, action, or status..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Trades Table */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardContent className="p-0">
              {filteredTrades.length === 0 ? (
                <div className="py-16 text-center">
                  <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-foreground mb-2">No trades found</h3>
                  <p className="text-muted-foreground">
                    {searchQuery ? 'Try a different search query' : 'Your trade history will appear here'}
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-10"></TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Symbol</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead className="text-right">Qty</TableHead>
                      <TableHead className="text-right">Price</TableHead>
                      <TableHead className="text-right">Notional</TableHead>
                      <TableHead className="text-right">P&L</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-20"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTrades.map((trade, index) => {
                      const isExpanded = expandedTrades.has(trade.id);
                      const hasDetails = trade.bid_price || trade.slippage !== undefined || trade.execution_latency_ms;
                      
                      return (
                        <Collapsible key={trade.id || index} open={isExpanded} onOpenChange={() => toggleExpand(trade.id)}>
                          <TableRow className={hasDetails ? 'cursor-pointer hover:bg-muted/50' : ''}>
                            <TableCell>
                              {hasDetails && (
                                <CollapsibleTrigger asChild>
                                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                                    {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                                  </Button>
                                </CollapsibleTrigger>
                              )}
                            </TableCell>
                            <TableCell className="text-muted-foreground">
                              {formatTime(trade.created_at || trade.timestamp)}
                            </TableCell>
                            <TableCell>
                              <div className="flex flex-col">
                                <span className="font-medium text-foreground">{trade.symbol}</span>
                                {trade.timeframe && (
                                  <span className="text-xs text-muted-foreground">{trade.timeframe}</span>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <span
                                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                                  trade.action.toLowerCase() === 'buy'
                                    ? 'bg-emerald-500/10 text-emerald-500'
                                    : 'bg-red-500/10 text-red-500'
                                }`}
                              >
                                {trade.action.toLowerCase() === 'buy' ? (
                                  <ArrowUpRight className="h-3 w-3" />
                                ) : (
                                  <ArrowDownRight className="h-3 w-3" />
                                )}
                                {trade.action.toUpperCase()}
                              </span>
                            </TableCell>
                            <TableCell className="text-right text-foreground">
                              {trade.filled_qty || trade.qty || '-'}
                            </TableCell>
                            <TableCell className="text-right text-foreground">
                              {formatCurrency(trade.filled_avg_price || trade.price)}
                            </TableCell>
                            <TableCell className="text-right text-foreground">
                              {formatCurrency(trade.notional)}
                            </TableCell>
                            <TableCell className="text-right">
                              {trade.action === 'CLOSE' && trade.realized_pnl !== null && trade.realized_pnl !== undefined ? (
                                <span className={trade.realized_pnl >= 0 ? 'text-green-500' : 'text-destructive'}>
                                  {trade.realized_pnl >= 0 ? '+' : ''}{formatCurrency(trade.realized_pnl)}
                                </span>
                              ) : (
                                <span className="text-muted-foreground">-</span>
                              )}
                            </TableCell>
                            <TableCell>
                              <span
                                className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                                  trade.status?.toLowerCase() === 'filled'
                                    ? 'bg-primary/10 text-primary'
                                    : trade.status?.toLowerCase() === 'submitted' || trade.status?.toLowerCase() === 'pending' || trade.status?.toLowerCase() === 'new'
                                    ? 'bg-yellow-500/10 text-yellow-500'
                                    : trade.status?.toLowerCase() === 'failed' || trade.status?.toLowerCase() === 'rejected'
                                    ? 'bg-red-500/10 text-red-500'
                                    : 'bg-muted text-muted-foreground'
                                }`}
                              >
                                {(trade.status || 'pending').toUpperCase()}
                              </span>
                            </TableCell>
                            <TableCell>
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigate(`/trades/${trade.id}`);
                                }}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                          
                          {hasDetails && (
                            <CollapsibleContent asChild>
                              <tr>
                                <td colSpan={10} className="p-0">
                                  <AnimatePresence>
                                    {isExpanded && (
                                      <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                        className="overflow-hidden"
                                      >
                                        <div className="bg-muted/30 p-4 border-t border-border">
                                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                            {/* Pricing Section */}
                                            <div className="space-y-2">
                                              <h4 className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                                                <TrendingUp className="h-3 w-3" /> Pricing
                                              </h4>
                                              <div className="space-y-1 text-sm">
                                                <div className="flex justify-between">
                                                  <span className="text-muted-foreground">Bid:</span>
                                                  <span className="text-foreground">{formatCurrency(trade.bid_price)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                  <span className="text-muted-foreground">Ask:</span>
                                                  <span className="text-foreground">{formatCurrency(trade.ask_price)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                  <span className="text-muted-foreground">Spread:</span>
                                                  <span className="text-foreground">
                                                    {formatCurrency(trade.spread)} {trade.spread_percent !== undefined && `(${formatPercent(trade.spread_percent)})`}
                                                  </span>
                                                </div>
                                              </div>
                                            </div>

                                            {/* Slippage Section */}
                                            <div className="space-y-2">
                                              <h4 className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                                                <Activity className="h-3 w-3" /> Slippage
                                              </h4>
                                              <div className="space-y-1 text-sm">
                                                <div className="flex justify-between">
                                                  <span className="text-muted-foreground">Expected:</span>
                                                  <span className="text-foreground">{formatCurrency(trade.expected_price)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                  <span className="text-muted-foreground">Slippage:</span>
                                                  <span className={`${trade.slippage && trade.slippage > 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                                                    {formatCurrency(trade.slippage)}
                                                  </span>
                                                </div>
                                                <div className="flex justify-between">
                                                  <span className="text-muted-foreground">Slippage %:</span>
                                                  <span className={`${trade.slippage_percent && trade.slippage_percent > 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                                                    {formatPercent(trade.slippage_percent)}
                                                  </span>
                                                </div>
                                              </div>
                                            </div>

                                            {/* Timing Section */}
                                            <div className="space-y-2">
                                              <h4 className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                                                <Zap className="h-3 w-3" /> Execution
                                              </h4>
                                              <div className="space-y-1 text-sm">
                                                <div className="flex justify-between">
                                                  <span className="text-muted-foreground">Latency:</span>
                                                  <span className="text-foreground">{formatMs(trade.execution_latency_ms)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                  <span className="text-muted-foreground">Fill Time:</span>
                                                  <span className="text-foreground">{formatMs(trade.time_to_fill_ms)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                  <span className="text-muted-foreground">Market:</span>
                                                  <span className="text-foreground">
                                                    {trade.market_open !== undefined 
                                                      ? (trade.market_open ? 'Open' : 'Closed')
                                                      : trade.extended_hours ? 'Extended Hours' : '-'}
                                                  </span>
                                                </div>
                                              </div>
                                            </div>

                                            {/* Order Details Section */}
                                            <div className="space-y-2">
                                              <h4 className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                                                <AlertCircle className="h-3 w-3" /> Order Details
                                              </h4>
                                              <div className="space-y-1 text-sm">
                                                <div className="flex justify-between">
                                                  <span className="text-muted-foreground">Type:</span>
                                                  <span className="text-foreground">{trade.order_type || '-'}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                  <span className="text-muted-foreground">TIF:</span>
                                                  <span className="text-foreground">{trade.time_in_force || '-'}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                  <span className="text-muted-foreground">Source:</span>
                                                  <span className="text-foreground">{trade.signal_source || '-'}</span>
                                                </div>
                                              </div>
                                            </div>
                                          </div>

                                          {/* Position & Account Row */}
                                          {(trade.position_before || trade.account_equity) && (
                                            <div className="mt-4 pt-4 border-t border-border grid grid-cols-2 md:grid-cols-4 gap-4">
                                              {trade.position_before && (
                                                <div className="text-sm">
                                                  <span className="text-muted-foreground">Position:</span>{' '}
                                                  <span className="text-foreground">{trade.position_before} → {trade.position_after}</span>
                                                </div>
                                              )}
                                              {trade.account_equity && (
                                                <div className="text-sm">
                                                  <span className="text-muted-foreground">Account Equity:</span>{' '}
                                                  <span className="text-foreground">{formatCurrency(trade.account_equity)}</span>
                                                </div>
                                              )}
                                              {trade.account_buying_power && (
                                                <div className="text-sm">
                                                  <span className="text-muted-foreground">Buying Power:</span>{' '}
                                                  <span className="text-foreground">{formatCurrency(trade.account_buying_power)}</span>
                                                </div>
                                              )}
                                            </div>
                                          )}

                                          {/* Error Message */}
                                          {trade.error_message && (
                                            <div className="mt-4 pt-4 border-t border-border">
                                              <div className="text-sm text-red-500 flex items-center gap-2">
                                                <AlertCircle className="h-4 w-4" />
                                                {trade.error_message}
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                      </motion.div>
                                    )}
                                  </AnimatePresence>
                                </td>
                              </tr>
                            </CollapsibleContent>
                          )}
                        </Collapsible>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </DashboardLayout>
  );
}