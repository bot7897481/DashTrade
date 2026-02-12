import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  Activity, 
  DollarSign, 
  BarChart3, 
  Building2,
  Gauge,
  Wallet,
  Timer,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import { api } from '@/lib/api.ts';
import { 
  formatCurrency, 
  formatLargeNumber, 
  formatPercent, 
  formatVolume, 
  formatMs, 
  formatDateTime, 
  getChangeColor,
  getRsiStatus,
  getVolumeStatus
} from '@/lib/formatters.ts';
import type { TradeDetailResponse } from '@/types/trade-detail.ts';

function StatCard({ 
  label, 
  value, 
  subValue, 
  colorClass 
}: { 
  label: string; 
  value: string; 
  subValue?: string;
  colorClass?: string;
}) {
  return (
    <div className="text-center p-4 bg-muted/50 rounded-lg border border-border/50">
      <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
      <p className={`text-lg font-bold mt-1 ${colorClass || 'text-foreground'}`}>{value}</p>
      {subValue && <p className="text-xs text-muted-foreground mt-0.5">{subValue}</p>}
    </div>
  );
}

function DataRow({ label, value, colorClass }: { label: string; value: string; colorClass?: string }) {
  return (
    <div className="flex justify-between py-2 border-b border-border/50 last:border-0">
      <span className="text-muted-foreground text-sm">{label}</span>
      <span className={`font-medium text-sm ${colorClass || 'text-foreground'}`}>{value}</span>
    </div>
  );
}

export default function TradeDetail() {
  const { tradeId } = useParams<{ tradeId: string }>();
  const navigate = useNavigate();
  const [trade, setTrade] = useState<TradeDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTradeDetail = async () => {
    if (!tradeId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await api.getTradeDetail(parseInt(tradeId));
      setTrade(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load trade details';
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTradeDetail();
  }, [tradeId]);

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </DashboardLayout>
    );
  }

  if (error || !trade) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-[60vh]">
          <AlertCircle className="h-16 w-16 text-red-500 mb-4" />
          <h2 className="text-2xl font-bold mb-2">Error Loading Trade</h2>
          <p className="text-muted-foreground mb-6">{error || 'Trade not found'}</p>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => navigate(-1)}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
            <Button onClick={fetchTradeDetail}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const isLong = trade.trade.action.toUpperCase() === 'LONG' || trade.trade.action.toUpperCase() === 'BUY';
  const rsiStatus = getRsiStatus(trade.technical?.rsi_14);
  const volumeStatus = getVolumeStatus(trade.stock?.volume_ratio);

  return (
    <DashboardLayout>
      <motion.div 
        initial={{ opacity: 0, y: 10 }} 
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        </div>

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              {trade.trade.symbol}
              <span className={`flex items-center gap-1 text-xl ${isLong ? 'text-emerald-500' : 'text-red-500'}`}>
                {isLong ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
                {trade.trade.action} Trade
              </span>
            </h1>
            <p className="text-muted-foreground mt-1">
              {formatDateTime(trade.trade.filled_at || trade.trade.created_at)}
            </p>
          </div>
          <Badge 
            variant={trade.trade.status === 'filled' ? 'default' : 'secondary'}
            className="text-sm px-4 py-1"
          >
            {trade.trade.status}
          </Badge>
        </div>

        {/* Execution Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Trade Execution Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <StatCard 
                label="Filled Price" 
                value={formatCurrency(trade.execution?.filled_avg_price)} 
              />
              <StatCard 
                label="Quantity" 
                value={`${trade.execution?.filled_qty || 'N/A'} shares`} 
              />
              <StatCard 
                label="Notional" 
                value={formatCurrency(trade.execution?.notional)} 
              />
              <StatCard 
                label="Slippage" 
                value={formatPercent(trade.execution?.slippage_percent)} 
                colorClass={getChangeColor(-(trade.execution?.slippage_percent || 0))}
              />
              <StatCard 
                label="Spread" 
                value={formatPercent(trade.execution?.spread_percent)} 
              />
              <StatCard 
                label="Fill Time" 
                value={formatMs(trade.timing?.time_to_fill_ms)} 
              />
            </div>
          </CardContent>
        </Card>

        {/* Tabbed Content */}
        <Tabs defaultValue="market" className="w-full">
          <TabsList className="grid grid-cols-3 lg:grid-cols-6 w-full">
            <TabsTrigger value="market" className="gap-1">
              <BarChart3 className="h-4 w-4" />
              <span className="hidden sm:inline">Market</span>
            </TabsTrigger>
            <TabsTrigger value="stock" className="gap-1">
              <TrendingUp className="h-4 w-4" />
              <span className="hidden sm:inline">Stock</span>
            </TabsTrigger>
            <TabsTrigger value="fundamentals" className="gap-1">
              <Building2 className="h-4 w-4" />
              <span className="hidden sm:inline">Fundamentals</span>
            </TabsTrigger>
            <TabsTrigger value="technical" className="gap-1">
              <Gauge className="h-4 w-4" />
              <span className="hidden sm:inline">Technical</span>
            </TabsTrigger>
            <TabsTrigger value="account" className="gap-1">
              <Wallet className="h-4 w-4" />
              <span className="hidden sm:inline">Account</span>
            </TabsTrigger>
            <TabsTrigger value="timing" className="gap-1">
              <Timer className="h-4 w-4" />
              <span className="hidden sm:inline">Timing</span>
            </TabsTrigger>
          </TabsList>

          {/* Market Tab */}
          <TabsContent value="market" className="mt-6">
            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Market Indices at Trade Time</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataRow 
                    label="S&P 500" 
                    value={`${formatCurrency(trade.market_indices?.sp500?.price)} ${formatPercent(trade.market_indices?.sp500?.change_percent)}`}
                    colorClass={getChangeColor(trade.market_indices?.sp500?.change_percent)}
                  />
                  <DataRow 
                    label="NASDAQ" 
                    value={`${formatCurrency(trade.market_indices?.nasdaq?.price)} ${formatPercent(trade.market_indices?.nasdaq?.change_percent)}`}
                    colorClass={getChangeColor(trade.market_indices?.nasdaq?.change_percent)}
                  />
                  <DataRow 
                    label="DOW" 
                    value={`${formatCurrency(trade.market_indices?.dji?.price)} ${formatPercent(trade.market_indices?.dji?.change_percent)}`}
                    colorClass={getChangeColor(trade.market_indices?.dji?.change_percent)}
                  />
                  <DataRow 
                    label="Russell 2000" 
                    value={`${formatCurrency(trade.market_indices?.russell?.price)} ${formatPercent(trade.market_indices?.russell?.change_percent)}`}
                    colorClass={getChangeColor(trade.market_indices?.russell?.change_percent)}
                  />
                  <DataRow 
                    label="VIX" 
                    value={`${trade.market_indices?.vix?.price?.toFixed(2) || 'N/A'} ${formatPercent(trade.market_indices?.vix?.change_percent)}`}
                    colorClass={getChangeColor(-(trade.market_indices?.vix?.change_percent || 0))}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Treasury Yields</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataRow label="10-Year Yield" value={`${trade.treasury?.yield_10y?.toFixed(2) || 'N/A'}%`} />
                  <DataRow label="2-Year Yield" value={`${trade.treasury?.yield_2y?.toFixed(2) || 'N/A'}%`} />
                  <DataRow 
                    label="Yield Curve Spread" 
                    value={`${trade.treasury?.yield_curve_spread?.toFixed(2) || 'N/A'}%`}
                    colorClass={getChangeColor(trade.treasury?.yield_curve_spread)}
                  />
                  {trade.treasury?.yield_curve_spread && trade.treasury.yield_curve_spread < 0 && (
                    <p className="text-xs text-yellow-500 mt-2">⚠️ Inverted yield curve - potential recession signal</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Stock Tab */}
          <TabsContent value="stock" className="mt-6">
            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Price Action</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataRow label="Open" value={formatCurrency(trade.stock?.open)} />
                  <DataRow label="High" value={formatCurrency(trade.stock?.high)} />
                  <DataRow label="Low" value={formatCurrency(trade.stock?.low)} />
                  <DataRow label="Close" value={formatCurrency(trade.stock?.close)} />
                  <DataRow label="Previous Close" value={formatCurrency(trade.stock?.prev_close)} />
                  <DataRow 
                    label="Day Change" 
                    value={formatPercent(trade.stock?.change_percent)}
                    colorClass={getChangeColor(trade.stock?.change_percent)}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Volume Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataRow label="Today's Volume" value={formatVolume(trade.stock?.volume)} />
                  <DataRow label="Avg Volume (20d)" value={formatVolume(trade.stock?.avg_volume)} />
                  <DataRow 
                    label="Volume Ratio" 
                    value={`${trade.stock?.volume_ratio?.toFixed(2) || 'N/A'}x`}
                    colorClass={volumeStatus.color}
                  />
                  <p className={`text-xs mt-2 ${volumeStatus.color}`}>{volumeStatus.label}</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Fundamentals Tab */}
          <TabsContent value="fundamentals" className="mt-6">
            <div className="grid md:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Valuation</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataRow label="Market Cap" value={formatLargeNumber(trade.fundamentals?.market_cap)} />
                  <DataRow label="P/E Ratio" value={trade.fundamentals?.pe_ratio?.toFixed(2) || 'N/A'} />
                  <DataRow label="Forward P/E" value={trade.fundamentals?.forward_pe?.toFixed(2) || 'N/A'} />
                  <DataRow label="EPS" value={formatCurrency(trade.fundamentals?.eps)} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Company Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataRow label="Beta" value={trade.fundamentals?.beta?.toFixed(2) || 'N/A'} />
                  <DataRow label="Dividend Yield" value={`${trade.fundamentals?.dividend_yield?.toFixed(2) || 0}%`} />
                  <DataRow label="Short Ratio" value={trade.fundamentals?.short_ratio?.toFixed(1) || 'N/A'} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">52-Week Range</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataRow label="52W High" value={formatCurrency(trade.fundamentals?.fifty_two_week_high)} />
                  <DataRow label="52W Low" value={formatCurrency(trade.fundamentals?.fifty_two_week_low)} />
                  {trade.fundamentals?.fifty_two_week_high && trade.fundamentals?.fifty_two_week_low && trade.stock?.close && (
                    <div className="mt-4">
                      <Progress 
                        value={((trade.stock.close - trade.fundamentals.fifty_two_week_low) / 
                               (trade.fundamentals.fifty_two_week_high - trade.fundamentals.fifty_two_week_low)) * 100} 
                      />
                      <div className="flex justify-between text-xs text-muted-foreground mt-1">
                        <span>{formatCurrency(trade.fundamentals.fifty_two_week_low)}</span>
                        <span>{formatCurrency(trade.fundamentals.fifty_two_week_high)}</span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Technical Tab */}
          <TabsContent value="technical" className="mt-6">
            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Moving Averages</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataRow label="50-Day MA" value={formatCurrency(trade.fundamentals?.fifty_day_ma)} />
                  <DataRow 
                    label="Price vs 50MA" 
                    value={formatPercent(trade.technical?.price_vs_50ma_percent)}
                    colorClass={getChangeColor(trade.technical?.price_vs_50ma_percent)}
                  />
                  <DataRow label="200-Day MA" value={formatCurrency(trade.fundamentals?.two_hundred_day_ma)} />
                  <DataRow 
                    label="Price vs 200MA" 
                    value={formatPercent(trade.technical?.price_vs_200ma_percent)}
                    colorClass={getChangeColor(trade.technical?.price_vs_200ma_percent)}
                  />
                  {trade.technical?.price_vs_50ma_percent && trade.technical?.price_vs_200ma_percent && 
                   trade.technical.price_vs_50ma_percent > 0 && trade.technical.price_vs_200ma_percent > 0 && (
                    <p className="text-xs text-emerald-500 mt-2">✓ Above both MAs - Bullish</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">RSI Indicator</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataRow label="RSI (14)" value={trade.technical?.rsi_14?.toFixed(1) || 'N/A'} />
                  <div className="mt-4">
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>Oversold</span>
                      <span>Neutral</span>
                      <span>Overbought</span>
                    </div>
                    <div className="h-3 bg-gradient-to-r from-emerald-500 via-muted to-red-500 rounded-full relative">
                      {trade.technical?.rsi_14 && (
                        <div 
                          className="absolute w-3 h-3 bg-foreground rounded-full border-2 border-background"
                          style={{ left: `${trade.technical.rsi_14}%`, transform: 'translateX(-50%)' }}
                        />
                      )}
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>0</span>
                      <span>30</span>
                      <span>70</span>
                      <span>100</span>
                    </div>
                  </div>
                  <p className={`text-xs mt-3 ${rsiStatus.color}`}>Status: {rsiStatus.label}</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Account Tab */}
          <TabsContent value="account" className="mt-6">
            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Account Snapshot</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataRow label="Total Equity" value={formatCurrency(trade.account?.equity)} />
                  <DataRow label="Cash Available" value={formatCurrency(trade.account?.cash)} />
                  <DataRow label="Buying Power" value={formatCurrency(trade.account?.buying_power)} />
                  <DataRow label="Portfolio Value" value={formatCurrency(trade.account?.portfolio_value)} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Position Context</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataRow label="Position Before" value={trade.position?.before?.toUpperCase() || 'N/A'} />
                  <DataRow label="Position After" value={trade.position?.after?.toUpperCase() || 'N/A'} />
                  <DataRow label="Qty Before" value={trade.position?.qty_before?.toString() || '0'} />
                  <DataRow label="Value Before" value={formatCurrency(trade.position?.value_before)} />
                  <DataRow label="Total Positions" value={trade.account?.total_positions_count?.toString() || 'N/A'} />
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Timing Tab */}
          <TabsContent value="timing" className="mt-6">
            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Execution Timeline</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <div className="w-2 h-2 rounded-full bg-primary mt-2" />
                      <div>
                        <p className="text-sm font-medium">Signal Received</p>
                        <p className="text-xs text-muted-foreground">{formatDateTime(trade.timing?.signal_received_at)}</p>
                      </div>
                    </div>
                    <div className="ml-1 border-l-2 border-dashed border-border h-4" />
                    <div className="flex items-center gap-2 ml-8 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {formatMs(trade.timing?.execution_latency_ms)}
                    </div>
                    <div className="ml-1 border-l-2 border-dashed border-border h-4" />
                    <div className="flex items-start gap-3">
                      <div className="w-2 h-2 rounded-full bg-yellow-500 mt-2" />
                      <div>
                        <p className="text-sm font-medium">Order Submitted</p>
                        <p className="text-xs text-muted-foreground">{formatDateTime(trade.timing?.order_submitted_at)}</p>
                      </div>
                    </div>
                    <div className="ml-1 border-l-2 border-dashed border-border h-4" />
                    <div className="flex items-center gap-2 ml-8 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {formatMs(trade.timing?.time_to_fill_ms)}
                    </div>
                    <div className="ml-1 border-l-2 border-dashed border-border h-4" />
                    <div className="flex items-start gap-3">
                      <div className="w-2 h-2 rounded-full bg-emerald-500 mt-2" />
                      <div>
                        <p className="text-sm font-medium">Order Filled</p>
                        <p className="text-xs text-muted-foreground">{formatDateTime(trade.trade?.filled_at)}</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Market Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataRow 
                    label="Market Open" 
                    value={trade.timing?.market_open ? 'Yes' : 'No'}
                    colorClass={trade.timing?.market_open ? 'text-emerald-500' : 'text-yellow-500'}
                  />
                  <DataRow 
                    label="Extended Hours" 
                    value={trade.timing?.extended_hours ? 'Yes' : 'No'}
                  />
                  <DataRow label="Signal Source" value={trade.timing?.signal_source || 'N/A'} />
                  <DataRow label="Order Type" value={trade.execution?.order_type?.toUpperCase() || 'N/A'} />
                  <DataRow label="Time in Force" value={trade.execution?.time_in_force?.toUpperCase() || 'N/A'} />
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        {/* Metadata Footer */}
        {trade.metadata && (
          <div className="text-sm text-muted-foreground border-t border-border pt-4">
            Data captured at {formatDateTime(trade.metadata.context_captured_at)} from {trade.metadata.data_source}
            {trade.metadata.fetch_latency_ms && ` (latency: ${trade.metadata.fetch_latency_ms}ms)`}
            {trade.metadata.errors && (
              <span className="text-yellow-500 ml-2">⚠️ Some data unavailable: {trade.metadata.errors}</span>
            )}
          </div>
        )}
      </motion.div>
    </DashboardLayout>
  );
}
