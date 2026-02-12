import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Lightbulb, 
  TrendingUp, 
  Target, 
  Sparkles,
  ChevronRight,
  Loader2,
  Filter,
  BarChart3,
  Play,
  Clock,
  DollarSign,
  Percent,
  Trophy,
  TrendingDown,
  Check,
  X
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer,
  Cell
} from 'recharts';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import { formatCurrency, formatPercent, getChangeColor, formatDuration } from '@/lib/formatters';
import type { 
  InsightsResponse, 
  Insight, 
  AnalysisResponse, 
  PatternsResponse,
  TradeOutcomesResponse 
} from '@/types/trade-detail';

const getInsightTypeIcon = (type: string) => {
  switch (type) {
    case 'rsi':
      return <TrendingUp className="h-5 w-5" />;
    case 'vix':
      return <BarChart3 className="h-5 w-5" />;
    case 'timeframe':
      return <Clock className="h-5 w-5" />;
    case 'time_of_day':
      return <Clock className="h-5 w-5" />;
    case 'trend':
      return <TrendingDown className="h-5 w-5" />;
    case 'entry_pattern':
      return <TrendingUp className="h-5 w-5" />;
    case 'exit_pattern':
      return <Target className="h-5 w-5" />;
    case 'market_condition':
      return <BarChart3 className="h-5 w-5" />;
    default:
      return <Lightbulb className="h-5 w-5" />;
  }
};

const getInsightTypeBadge = (type: string) => {
  const typeColors: Record<string, string> = {
    rsi: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    vix: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    timeframe: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    time_of_day: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    trend: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    entry_pattern: 'bg-primary/20 text-primary border-primary/30',
    exit_pattern: 'bg-secondary/20 text-secondary border-secondary/30',
    market_condition: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  };
  
  return (
    <Badge variant="default" className={typeColors[type] || 'bg-muted text-muted-foreground'}>
      {type.replace(/_/g, ' ').toUpperCase()}
    </Badge>
  );
};

const getConfidenceColor = (score: number) => {
  const normalizedScore = score > 1 ? score / 100 : score;
  if (normalizedScore >= 0.8) return 'text-emerald-500';
  if (normalizedScore >= 0.6) return 'text-primary';
  if (normalizedScore >= 0.4) return 'text-yellow-500';
  return 'text-muted-foreground';
};

const normalizeConfidence = (score: number) => {
  return score > 1 ? score : score * 100;
};

export default function Insights() {
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [patterns, setPatterns] = useState<PatternsResponse | null>(null);
  const [outcomes, setOutcomes] = useState<TradeOutcomesResponse | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [minConfidence, setMinConfidence] = useState(0.5);
  const [expandedInsight, setExpandedInsight] = useState<number | null>(null);
  const [outcomeFilter, setOutcomeFilter] = useState<'all' | 'closed' | 'open'>('closed');

  useEffect(() => {
    fetchAllData();
  }, []);

  useEffect(() => {
    fetchInsights();
  }, [minConfidence]);

  const fetchAllData = async () => {
    setIsLoading(true);
    try {
      const [insightsData, patternsData, outcomesData] = await Promise.all([
        api.getInsights(minConfidence),
        api.getPatterns({ pattern_type: 'all', min_trades: 5 }),
        api.getTradeOutcomes({ status: 'closed', limit: 50 }),
      ]);
      setInsights(insightsData);
      setPatterns(patternsData);
      setOutcomes(outcomesData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchInsights = async () => {
    try {
      const data = await api.getInsights(minConfidence);
      setInsights(data);
    } catch (error) {
      console.error('Failed to load insights:', error);
    }
  };

  const fetchOutcomes = async (status: 'all' | 'closed' | 'open') => {
    try {
      const data = await api.getTradeOutcomes({ 
        status: status === 'all' ? undefined : status, 
        limit: 50 
      });
      setOutcomes(data);
    } catch (error) {
      console.error('Failed to load outcomes:', error);
    }
  };

  const handleOutcomeFilterChange = (value: string) => {
    const filter = value as 'all' | 'closed' | 'open';
    setOutcomeFilter(filter);
    fetchOutcomes(filter);
  };

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const result = await api.runAnalysis(10);
      setAnalysisResult(result);
      
      if (result.success) {
        toast.success(`Analysis complete! Generated ${result.insights_generated} insights from ${result.total_trades_analyzed} trades.`);
        // Refresh insights and patterns
        await fetchAllData();
      } else {
        toast.error(result.error || 'Analysis failed');
      }
    } catch (error) {
      console.error('Analysis failed:', error);
      toast.error('Failed to run analysis. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const overallStats = analysisResult?.overall_stats || patterns?.overall_stats;

  if (isLoading && !insights) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-32 w-full" />
          <div className="grid gap-4 md:grid-cols-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-24" />)}
          </div>
          <div className="grid gap-4">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-48" />)}
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header with Analyze Button */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
              <Sparkles className="h-8 w-8 text-primary" />
              AI Strategy Insights
            </h1>
            <p className="text-muted-foreground mt-1">AI-powered pattern discovery from your trades</p>
          </div>
          <Button 
            onClick={runAnalysis} 
            disabled={isAnalyzing}
            size="lg"
            className="gap-2"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Play className="h-5 w-5" />
                Analyze My Trades
              </>
            )}
          </Button>
        </div>

        {/* Overall Stats */}
        {overallStats && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-primary" />
                  Overall Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <p className="text-xs text-muted-foreground mb-1">Total Trades</p>
                    <p className="text-2xl font-bold text-foreground">{overallStats.total_trades}</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <p className="text-xs text-muted-foreground mb-1">Win Rate</p>
                    <p className="text-2xl font-bold text-emerald-500">
                      {typeof overallStats.win_rate === 'number' ? overallStats.win_rate.toFixed(1) : 'N/A'}%
                    </p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <p className="text-xs text-muted-foreground mb-1">Total P&L</p>
                    <p className={`text-2xl font-bold ${getChangeColor(overallStats.total_pnl)}`}>
                      {formatCurrency(overallStats.total_pnl, true)}
                    </p>
                  </div>
                  {'avg_return' in overallStats && typeof overallStats.avg_return === 'number' && (
                    <div className="text-center p-3 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground mb-1">Avg Return</p>
                      <p className={`text-2xl font-bold ${getChangeColor(overallStats.avg_return)}`}>
                        {formatPercent(overallStats.avg_return / 100, true)}
                      </p>
                    </div>
                  )}
                  {'avg_win' in overallStats && typeof overallStats.avg_win === 'number' && (
                    <div className="text-center p-3 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground mb-1">Avg Win</p>
                      <p className="text-2xl font-bold text-emerald-500">+{overallStats.avg_win.toFixed(2)}%</p>
                    </div>
                  )}
                  {'avg_loss' in overallStats && typeof overallStats.avg_loss === 'number' && (
                    <div className="text-center p-3 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground mb-1">Avg Loss</p>
                      <p className="text-2xl font-bold text-destructive">{overallStats.avg_loss.toFixed(2)}%</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Pattern Charts */}
        {patterns?.patterns && Object.keys(patterns.patterns).length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  Performance Patterns
                </CardTitle>
                <CardDescription>Statistical patterns discovered from your trading data</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="rsi" className="space-y-4">
                  <TabsList className="grid w-full grid-cols-5">
                    <TabsTrigger value="rsi" disabled={!patterns.patterns.rsi}>RSI</TabsTrigger>
                    <TabsTrigger value="vix" disabled={!patterns.patterns.vix}>VIX</TabsTrigger>
                    <TabsTrigger value="timeframe" disabled={!patterns.patterns.timeframe}>Timeframe</TabsTrigger>
                    <TabsTrigger value="time_of_day" disabled={!patterns.patterns.time_of_day}>Time of Day</TabsTrigger>
                    <TabsTrigger value="trend" disabled={!patterns.patterns.trend}>Trend</TabsTrigger>
                  </TabsList>

                  {patterns.patterns.rsi && (
                    <TabsContent value="rsi">
                      <PatternChart 
                        data={patterns.patterns.rsi} 
                        title="Win Rate by RSI Level"
                        xKey="rsi_range"
                        yKey="win_rate"
                      />
                    </TabsContent>
                  )}

                  {patterns.patterns.vix && (
                    <TabsContent value="vix">
                      <PatternChart 
                        data={patterns.patterns.vix} 
                        title="Win Rate by VIX Regime"
                        xKey="vix_regime"
                        yKey="win_rate"
                      />
                    </TabsContent>
                  )}

                  {patterns.patterns.timeframe && (
                    <TabsContent value="timeframe">
                      <PatternChart 
                        data={patterns.patterns.timeframe} 
                        title="Win Rate by Timeframe"
                        xKey="timeframe"
                        yKey="win_rate"
                      />
                    </TabsContent>
                  )}

                  {patterns.patterns.time_of_day && (
                    <TabsContent value="time_of_day">
                      <PatternChart 
                        data={patterns.patterns.time_of_day} 
                        title="Win Rate by Time of Day"
                        xKey="time_period"
                        yKey="win_rate"
                      />
                    </TabsContent>
                  )}

                  {patterns.patterns.trend && (
                    <TabsContent value="trend">
                      <PatternChart 
                        data={patterns.patterns.trend} 
                        title="Win Rate by Trend Direction"
                        xKey="trend"
                        yKey="win_rate"
                      />
                    </TabsContent>
                  )}
                </Tabs>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Confidence Filter */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }} 
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-primary/20 bg-primary/5">
            <CardContent className="py-4">
              <div className="flex items-center gap-4">
                <Filter className="h-5 w-5 text-primary" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-foreground">Minimum Confidence</span>
                    <span className="text-sm text-primary font-mono">{Math.round(minConfidence * 100)}%</span>
                  </div>
                  <Slider
                    value={[minConfidence]}
                    onValueChange={([value]) => setMinConfidence(value)}
                    min={0}
                    max={1}
                    step={0.05}
                    className="w-full"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Insights List */}
        {insights?.insights && insights.insights.length > 0 ? (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-secondary" />
              AI Insights ({insights.insights.length})
            </h2>
            {insights.insights.map((insight, index) => (
              <motion.div
                key={insight.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <InsightCard 
                  insight={insight} 
                  isExpanded={expandedInsight === insight.id}
                  onToggle={() => setExpandedInsight(expandedInsight === insight.id ? null : insight.id)}
                />
              </motion.div>
            ))}
          </div>
        ) : (
          <Card className="py-16">
            <CardContent className="flex flex-col items-center justify-center text-center">
              <Sparkles className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No insights yet</h3>
              <p className="text-muted-foreground max-w-md mb-4">
                Click "Analyze My Trades" to discover AI-powered patterns from your trading history.
              </p>
              <Button onClick={runAnalysis} disabled={isAnalyzing} className="gap-2">
                {isAnalyzing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Start Analysis
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Trade Outcomes Table */}
        {outcomes && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card>
              <CardHeader>
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <DollarSign className="h-5 w-5 text-primary" />
                      Trade Outcomes
                    </CardTitle>
                    <CardDescription>Individual trade results with P&L</CardDescription>
                  </div>
                  <Tabs value={outcomeFilter} onValueChange={handleOutcomeFilterChange}>
                    <TabsList>
                      <TabsTrigger value="closed">Closed</TabsTrigger>
                      <TabsTrigger value="open">Open</TabsTrigger>
                      <TabsTrigger value="all">All</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Symbol</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead className="text-right">Entry</TableHead>
                        <TableHead className="text-right">Exit</TableHead>
                        <TableHead className="text-right">P&L</TableHead>
                        <TableHead className="text-right">Duration</TableHead>
                        <TableHead className="text-center">Win</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {outcomes.outcomes.length > 0 ? (
                        outcomes.outcomes.map((outcome) => (
                          <TableRow key={outcome.trade_id}>
                            <TableCell className="font-medium">{outcome.symbol}</TableCell>
                            <TableCell>
                              <Badge variant={outcome.position_type === 'long' ? 'default' : 'secondary'}>
                                {outcome.position_type}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right font-mono">
                              {formatCurrency(outcome.entry_price)}
                            </TableCell>
                            <TableCell className="text-right font-mono">
                              {outcome.exit_price ? formatCurrency(outcome.exit_price) : '-'}
                            </TableCell>
                            <TableCell className={`text-right font-mono font-medium ${getChangeColor(outcome.pnl_dollars)}`}>
                              {formatCurrency(outcome.pnl_dollars, true)}
                              <span className="text-xs ml-1 text-muted-foreground">
                                ({formatPercent(outcome.pnl_percent / 100, true)})
                              </span>
                            </TableCell>
                            <TableCell className="text-right text-muted-foreground">
                              {formatDuration(outcome.hold_duration_minutes)}
                            </TableCell>
                            <TableCell className="text-center">
                              {outcome.is_winner ? (
                                <Check className="h-5 w-5 text-emerald-500 mx-auto" />
                              ) : (
                                <X className="h-5 w-5 text-destructive mx-auto" />
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                            No trade outcomes found
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  );
}

// Insight Card Component
interface InsightCardProps {
  insight: Insight;
  isExpanded: boolean;
  onToggle: () => void;
}

function InsightCard({ insight, isExpanded, onToggle }: InsightCardProps) {
  const confidenceNormalized = normalizeConfidence(insight.confidence_score);
  
  return (
    <Card 
      className={`transition-all cursor-pointer hover:border-primary/30 ${
        isExpanded ? 'border-primary/50 bg-primary/5' : ''
      }`}
      onClick={onToggle}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className={`p-2 rounded-lg bg-primary/10 ${getConfidenceColor(insight.confidence_score)}`}>
              {getInsightTypeIcon(insight.insight_type)}
            </div>
            <div>
              <CardTitle className="text-lg text-foreground">{insight.title}</CardTitle>
              <CardDescription className="mt-1">{insight.description}</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {getInsightTypeBadge(insight.insight_type)}
            <ChevronRight className={`h-5 w-5 text-muted-foreground transition-transform ${
              isExpanded ? 'rotate-90' : ''
            }`} />
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Metrics Row */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center p-3 rounded-lg bg-muted/50">
            <p className="text-xs text-muted-foreground mb-1">Confidence</p>
            <p className={`text-lg font-bold ${getConfidenceColor(insight.confidence_score)}`}>
              {confidenceNormalized.toFixed(0)}%
            </p>
          </div>
          <div className="text-center p-3 rounded-lg bg-muted/50">
            <p className="text-xs text-muted-foreground mb-1">Win Rate</p>
            <p className="text-lg font-bold text-foreground">
              {insight.observed_win_rate?.toFixed(1)}%
            </p>
          </div>
          <div className="text-center p-3 rounded-lg bg-muted/50">
            <p className="text-xs text-muted-foreground mb-1">Avg Return</p>
            <p className={`text-lg font-bold ${getChangeColor(insight.observed_avg_return)}`}>
              {insight.observed_avg_return > 0 ? '+' : ''}{insight.observed_avg_return?.toFixed(2)}%
            </p>
          </div>
        </div>

        {/* Confidence Bar */}
        <div className="space-y-1 mb-4">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Pattern strength</span>
            <span className="text-muted-foreground">{insight.observed_trades} trades observed</span>
          </div>
          <Progress value={confidenceNormalized} className="h-1.5" />
        </div>

        {/* Expanded Content */}
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="pt-4 border-t border-border"
          >
            <div className="space-y-4">
              {/* Recommendation */}
              <div className="p-4 rounded-lg bg-card border border-border">
                <p className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-secondary" />
                  Recommendation
                </p>
                <p className="text-sm text-muted-foreground">{insight.recommendation}</p>
              </div>

              {/* Conditions */}
              {insight.conditions && Object.keys(insight.conditions).length > 0 && (
                <div className="p-4 rounded-lg bg-muted/30">
                  <p className="text-sm font-medium text-foreground mb-2">Conditions</p>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(insight.conditions).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{key}:</span>
                        <code className="text-primary text-xs bg-primary/10 px-2 py-0.5 rounded">
                          {String(value)}
                        </code>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Params */}
              {insight.recommended_params && Object.keys(insight.recommended_params).length > 0 && (
                <div className="p-4 rounded-lg bg-muted/30">
                  <p className="text-sm font-medium text-foreground mb-2">Suggested Parameters</p>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(insight.recommended_params).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{key}:</span>
                        <code className="text-primary text-xs bg-primary/10 px-2 py-0.5 rounded">
                          {String(value)}
                        </code>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Apply Button */}
              <Button className="w-full gap-2">
                <Sparkles className="h-4 w-4" />
                Apply to Strategy
              </Button>
            </div>
          </motion.div>
        )}
      </CardContent>
    </Card>
  );
}

// Pattern Chart Component
interface PatternChartProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any[];
  title: string;
  xKey: string;
  yKey: string;
}

function PatternChart({ data, title, xKey, yKey }: PatternChartProps) {
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-foreground">{title}</h4>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 40 }}>
          <XAxis 
            dataKey={xKey} 
            tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
            tickLine={false}
            axisLine={false}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis 
            domain={[0, 100]} 
            tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px',
            }}
            labelStyle={{ color: 'hsl(var(--foreground))' }}
            formatter={(value: number) => [`${value.toFixed(1)}%`, 'Win Rate']}
          />
          <Bar dataKey={yKey} radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => {
              const winRate = Number(entry[yKey]) || 0;
              let fill = 'hsl(var(--muted))';
              if (winRate >= 60) fill = 'hsl(var(--chart-1))';
              else if (winRate >= 50) fill = 'hsl(var(--primary))';
              else if (winRate >= 40) fill = 'hsl(var(--chart-3))';
              else fill = 'hsl(var(--destructive))';
              return <Cell key={`cell-${index}`} fill={fill} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
