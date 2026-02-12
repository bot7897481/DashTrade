import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Clock, 
  DollarSign, 
  BarChart3, 
  Activity,
  Loader2,
  Filter
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { api } from '@/lib/api';
import { formatCurrency, formatPercent, getChangeColor } from '@/lib/formatters';
import type { PerformanceResponse } from '@/types/trade-detail';

export default function Performance() {
  const [performance, setPerformance] = useState<PerformanceResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [strategyFilter, setStrategyFilter] = useState<string>('all');
  const [symbolFilter, setSymbolFilter] = useState<string>('all');

  useEffect(() => {
    fetchPerformance();
  }, [strategyFilter, symbolFilter]);

  const fetchPerformance = async () => {
    setIsLoading(true);
    try {
      const params: { strategy_type?: string; symbol?: string } = {};
      if (strategyFilter !== 'all') params.strategy_type = strategyFilter;
      if (symbolFilter !== 'all') params.symbol = symbolFilter;
      
      const data = await api.getPerformance(params);
      setPerformance(data);
    } catch (error) {
      console.error('Failed to load performance:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading && !performance) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <Skeleton className="h-10 w-64" />
          <div className="grid gap-4 md:grid-cols-4">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32" />)}
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Skeleton className="h-80" />
            <Skeleton className="h-80" />
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const summary = performance?.summary;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Performance</h1>
            <p className="text-muted-foreground mt-1">Strategy analytics and trade metrics</p>
          </div>
          
          {/* Filters */}
          <div className="flex gap-3">
            <Select value={strategyFilter} onValueChange={setStrategyFilter}>
              <SelectTrigger className="w-[160px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Strategy" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Strategies</SelectItem>
                <SelectItem value="momentum">Momentum</SelectItem>
                <SelectItem value="mean_reversion">Mean Reversion</SelectItem>
                <SelectItem value="breakout">Breakout</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={symbolFilter} onValueChange={setSymbolFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Symbol" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Symbols</SelectItem>
                <SelectItem value="SPY">SPY</SelectItem>
                <SelectItem value="QQQ">QQQ</SelectItem>
                <SelectItem value="AAPL">AAPL</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0 }}>
            <Card className="border-primary/20">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total P&L</p>
                    <p className={`text-2xl font-bold ${getChangeColor(summary?.total_pnl_dollars || 0)}`}>
                      {formatCurrency(summary?.total_pnl_dollars || 0, true)}
                    </p>
                  </div>
                  <div className={`p-3 rounded-full ${(summary?.total_pnl_dollars || 0) >= 0 ? 'bg-emerald-500/10' : 'bg-destructive/10'}`}>
                    {(summary?.total_pnl_dollars || 0) >= 0 ? (
                      <TrendingUp className="h-5 w-5 text-emerald-500" />
                    ) : (
                      <TrendingDown className="h-5 w-5 text-destructive" />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Win Rate</p>
                    <p className="text-2xl font-bold text-foreground">
                      {formatPercent(summary?.win_rate || 0)}
                    </p>
                  </div>
                  <div className="p-3 rounded-full bg-primary/10">
                    <Target className="h-5 w-5 text-primary" />
                  </div>
                </div>
                <Progress 
                  value={(summary?.win_rate || 0) * 100} 
                  className="mt-3 h-2" 
                />
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Profit Factor</p>
                    <p className="text-2xl font-bold text-foreground">
                      {summary?.profit_factor?.toFixed(2) || '0.00'}
                    </p>
                  </div>
                  <div className="p-3 rounded-full bg-secondary/10">
                    <BarChart3 className="h-5 w-5 text-secondary" />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  {(summary?.profit_factor || 0) >= 1.5 ? 'Strong edge' : (summary?.profit_factor || 0) >= 1 ? 'Profitable' : 'Needs improvement'}
                </p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Avg Hold Time</p>
                    <p className="text-2xl font-bold text-foreground">
                      {Math.round(summary?.avg_hold_duration_minutes || 0)}m
                    </p>
                  </div>
                  <div className="p-3 rounded-full bg-muted">
                    <Clock className="h-5 w-5 text-muted-foreground" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Trade Count Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-full bg-muted">
                    <Activity className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Trades</p>
                    <p className="text-3xl font-bold text-foreground">{summary?.total_trades || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
            <Card className="border-emerald-500/20">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-full bg-emerald-500/10">
                    <TrendingUp className="h-5 w-5 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Winners</p>
                    <p className="text-3xl font-bold text-emerald-500">{summary?.winning_trades || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <Card className="border-destructive/20">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-full bg-destructive/10">
                    <TrendingDown className="h-5 w-5 text-destructive" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Losers</p>
                    <p className="text-3xl font-bold text-destructive">{summary?.losing_trades || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Performance by Indicator & Market Condition */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* By Indicator */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  Performance by Indicator
                </CardTitle>
              </CardHeader>
              <CardContent>
                {performance?.by_indicator && performance.by_indicator.length > 0 ? (
                  <div className="space-y-4">
                    {performance.by_indicator.map((item, index) => (
                      <div key={item.entry_indicator} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-foreground">{item.entry_indicator}</span>
                          <span className="text-sm text-muted-foreground">{item.total_trades} trades</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <Progress value={item.win_rate * 100} className="flex-1 h-2" />
                          <span className={`text-sm font-medium ${getChangeColor(item.avg_return)}`}>
                            {formatPercent(item.avg_return, true)}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Win rate: {formatPercent(item.win_rate)}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                    <BarChart3 className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-sm">No indicator data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* By Market Condition */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Activity className="h-5 w-5 text-secondary" />
                  Performance by Market Condition
                </CardTitle>
              </CardHeader>
              <CardContent>
                {performance?.by_market_condition && performance.by_market_condition.length > 0 ? (
                  <div className="space-y-4">
                    {performance.by_market_condition.map((item) => (
                      <div key={item.vix_regime} className="p-4 rounded-lg border border-border bg-card/50">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-foreground capitalize">
                            {item.vix_regime.replace('_', ' ')} VIX
                          </span>
                          <span className={`text-sm font-medium ${getChangeColor(item.avg_return)}`}>
                            {formatPercent(item.avg_return, true)}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span>{item.total_trades} trades</span>
                          <span>•</span>
                          <span>{formatPercent(item.win_rate)} win rate</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                    <Activity className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-sm">No market condition data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </DashboardLayout>
  );
}
