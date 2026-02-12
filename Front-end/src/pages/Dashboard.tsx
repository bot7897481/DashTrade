import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { api } from '@/lib/api.ts';
import type { DashboardData, Position, Trade } from '@/types/api.ts';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { 
  TrendingUp, 
  TrendingDown, 
  Wallet, 
  DollarSign, 
  Bot, 
  Activity,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast.ts';
import { Link } from 'react-router-dom';

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { toast } = useToast();

  const fetchDashboard = async (showRefresh = false) => {
    if (showRefresh) setIsRefreshing(true);
    try {
      const dashboardData = await api.getDashboard();
      setData(dashboardData);
    } catch (error) {
      toast({
        title: 'Failed to load dashboard',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    
    // Refresh every 30 seconds
    const interval = setInterval(() => fetchDashboard(), 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => fetchDashboard(true);

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-10 w-24" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-32 rounded-xl" />
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Skeleton className="h-80 rounded-xl" />
            <Skeleton className="h-80 rounded-xl" />
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const todayPL = data?.account 
    ? (data.account.portfolio_value - (data.account.last_equity || data.account.portfolio_value))
    : 0;
  const todayPLPercent = data?.account?.last_equity 
    ? ((todayPL / data.account.last_equity) * 100)
    : 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl lg:text-3xl font-display font-bold text-foreground">
              Dashboard
            </h1>
            <p className="text-muted-foreground mt-1">
              Your trading overview at a glance
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="border-border"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0 }}
            className="feature-card"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Portfolio Value</p>
                <p className="text-2xl font-bold text-foreground mt-1">
                  {formatCurrency(data?.account?.portfolio_value || 0)}
                </p>
              </div>
              <div className="p-2 rounded-lg bg-primary/10">
                <TrendingUp className="h-5 w-5 text-primary" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="feature-card"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Buying Power</p>
                <p className="text-2xl font-bold text-foreground mt-1">
                  {formatCurrency(data?.account?.buying_power || 0)}
                </p>
              </div>
              <div className="p-2 rounded-lg bg-secondary/10">
                <Wallet className="h-5 w-5 text-secondary" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="feature-card"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total P&L</p>
                <p className={`text-2xl font-bold mt-1 ${(data?.pnl?.total_pnl || 0) >= 0 ? 'text-green-500' : 'text-destructive'}`}>
                  {formatCurrency(data?.pnl?.total_pnl || 0)}
                </p>
                <div className="flex gap-2 text-xs mt-1">
                  <span className={`${(data?.pnl?.realized_pnl || 0) >= 0 ? 'text-green-500' : 'text-destructive'}`}>
                    Realized: {formatCurrency(data?.pnl?.realized_pnl || 0)}
                  </span>
                  <span className={`${(data?.pnl?.unrealized_pnl || 0) >= 0 ? 'text-green-500' : 'text-destructive'}`}>
                    Unrealized: {formatCurrency(data?.pnl?.unrealized_pnl || 0)}
                  </span>
                </div>
              </div>
              <div className={`p-2 rounded-lg ${(data?.pnl?.total_pnl || 0) >= 0 ? 'bg-green-500/10' : 'bg-destructive/10'}`}>
                {(data?.pnl?.total_pnl || 0) >= 0 ? (
                  <TrendingUp className="h-5 w-5 text-green-500" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-destructive" />
                )}
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="feature-card"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Bots</p>
                <p className="text-2xl font-bold text-foreground mt-1">
                  {data?.bots?.active || 0} / {data?.bots?.total || 0}
                </p>
                {data?.bots?.total_trades !== undefined && (
                  <p className="text-xs text-muted-foreground mt-1">
                    {data.bots.total_trades} total trades
                  </p>
                )}
              </div>
              <div className="p-2 rounded-lg bg-cyan/10">
                <Bot className="h-5 w-5 text-cyan" />
              </div>
            </div>
            <Link 
              to="/bots" 
              className="inline-flex items-center text-sm text-primary hover:underline mt-2"
            >
              Manage Bots <ArrowUpRight className="h-3 w-3 ml-1" />
            </Link>
          </motion.div>
        </div>

        {/* Positions and Trades */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Positions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="feature-card"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-display font-semibold text-foreground">
                Open Positions
              </h2>
              <Activity className="h-5 w-5 text-muted-foreground" />
            </div>
            
            {data?.positions && data.positions.length > 0 ? (
              <div className="space-y-3">
                {data.positions.map((position: Position, index: number) => (
                  <div 
                    key={index}
                    className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                  >
                    <div>
                      <p className="font-medium text-foreground">{position.symbol}</p>
                      <p className="text-sm text-muted-foreground">
                        {position.qty} shares @ {formatCurrency(position.avg_entry_price || 0)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-foreground">
                        {formatCurrency(position.market_value)}
                      </p>
                      <p className={`text-sm flex items-center justify-end ${
                        position.unrealized_pl >= 0 ? 'text-green-500' : 'text-destructive'
                      }`}>
                        {position.unrealized_pl >= 0 ? (
                          <ArrowUpRight className="h-3 w-3 mr-1" />
                        ) : (
                          <ArrowDownRight className="h-3 w-3 mr-1" />
                        )}
                        {formatCurrency(position.unrealized_pl)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No open positions</p>
              </div>
            )}
          </motion.div>

          {/* Recent Trades */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="feature-card"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-display font-semibold text-foreground">
                Recent Trades
              </h2>
              <Link 
                to="/trades"
                className="text-sm text-primary hover:underline flex items-center"
              >
                View All <ArrowUpRight className="h-3 w-3 ml-1" />
              </Link>
            </div>
            
            {data?.recent_trades && data.recent_trades.length > 0 ? (
              <div className="space-y-3">
                {data.recent_trades.slice(0, 5).map((trade: Trade, index: number) => {
                  const tradeQty = trade.qty ?? trade.filled_qty ?? 0;
                  const tradePrice = trade.price ?? trade.filled_avg_price ?? 0;
                  const tradeTime = trade.timestamp ?? trade.filled_at ?? trade.created_at;
                  const tradeAction = trade.action ?? (trade as any).side ?? 'UNKNOWN';
                  
                  return (
                    <div 
                      key={trade.order_id || index}
                      className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${
                          tradeAction === 'BUY' ? 'bg-green-500' : 
                          tradeAction === 'SELL' ? 'bg-destructive' : 'bg-secondary'
                        }`} />
                        <div>
                          <p className="font-medium text-foreground">
                            {tradeAction} {trade.symbol}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {tradeTime ? formatTime(tradeTime) : '-'}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-foreground">
                          {tradeQty} @ {formatCurrency(tradePrice)}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {formatCurrency(tradeQty * tradePrice)}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <DollarSign className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No recent trades</p>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </DashboardLayout>
  );
}
