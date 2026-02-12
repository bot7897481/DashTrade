import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, Users, BarChart3, Check, Plus, Loader2 } from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { api } from '@/lib/api.ts';
import type { Strategy, Bot } from '@/types/api.ts';

export default function Strategies() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [bots, setBots] = useState<Bot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [selectedBotId, setSelectedBotId] = useState<string>('');
  const [isSubscribing, setIsSubscribing] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [strategiesRes, botsRes] = await Promise.all([
          api.getStrategies(),
          api.getBots(),
        ]);
        setStrategies(strategiesRes.strategies);
        setBots(botsRes.bots);
      } catch (error) {
        toast.error('Failed to load strategies');
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleSubscribe = async () => {
    if (!selectedStrategy || !selectedBotId) return;
    setIsSubscribing(true);
    try {
      await api.subscribeToStrategy(selectedStrategy.id, Number(selectedBotId));
      setStrategies(strategies.map(s => 
        s.id === selectedStrategy.id ? { ...s, is_subscribed: true } : s
      ));
      toast.success(`Subscribed to ${selectedStrategy.name}`);
      setIsDialogOpen(false);
      setSelectedStrategy(null);
      setSelectedBotId('');
    } catch (error) {
      toast.error('Failed to subscribe');
    } finally {
      setIsSubscribing(false);
    }
  };

  const handleUnsubscribe = async (strategy: Strategy) => {
    try {
      await api.unsubscribeFromStrategy(strategy.id);
      setStrategies(strategies.map(s => 
        s.id === strategy.id ? { ...s, is_subscribed: false } : s
      ));
      toast.success(`Unsubscribed from ${strategy.name}`);
    } catch (error) {
      toast.error('Failed to unsubscribe');
    }
  };

  const openSubscribeDialog = (strategy: Strategy) => {
    setSelectedStrategy(strategy);
    setIsDialogOpen(true);
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <Skeleton className="h-10 w-48" />
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
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
        <div>
          <h1 className="text-3xl font-bold text-foreground">Strategy Marketplace</h1>
          <p className="text-muted-foreground mt-1">Subscribe to proven trading strategies from experienced traders</p>
        </div>

        {/* Strategies Grid */}
        {strategies.length === 0 ? (
          <Card className="py-16">
            <CardContent className="flex flex-col items-center justify-center text-center">
              <TrendingUp className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No strategies available</h3>
              <p className="text-muted-foreground">Check back later for new trading strategies</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <AnimatePresence>
              {strategies.map((strategy, index) => (
                <motion.div
                  key={strategy.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className={`h-full flex flex-col ${strategy.is_subscribed ? 'border-primary/30 bg-primary/5' : ''}`}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <CardTitle className="text-xl text-foreground">{strategy.name}</CardTitle>
                          <CardDescription>{strategy.description}</CardDescription>
                        </div>
                        {strategy.is_subscribed && (
                          <span className="flex items-center gap-1 text-xs font-medium text-primary bg-primary/10 px-2 py-1 rounded-full">
                            <Check className="h-3 w-3" /> Subscribed
                          </span>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="flex-1 flex flex-col justify-between">
                      <div className="space-y-4">
                        {/* Stats */}
                        <div className="grid grid-cols-2 gap-4">
                          {strategy.win_rate && (
                            <div className="space-y-1">
                              <p className="text-xs text-muted-foreground flex items-center gap-1">
                                <BarChart3 className="h-3 w-3" /> Win Rate
                              </p>
                              <p className="text-lg font-semibold text-foreground">{strategy.win_rate}%</p>
                            </div>
                          )}
                          {strategy.avg_return && (
                            <div className="space-y-1">
                              <p className="text-xs text-muted-foreground flex items-center gap-1">
                                <TrendingUp className="h-3 w-3" /> Avg Return
                              </p>
                              <p className={`text-lg font-semibold ${strategy.avg_return >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                {strategy.avg_return >= 0 ? '+' : ''}{strategy.avg_return}%
                              </p>
                            </div>
                          )}
                          {strategy.subscribers !== undefined && (
                            <div className="space-y-1">
                              <p className="text-xs text-muted-foreground flex items-center gap-1">
                                <Users className="h-3 w-3" /> Subscribers
                              </p>
                              <p className="text-lg font-semibold text-foreground">{strategy.subscribers}</p>
                            </div>
                          )}
                        </div>

                        {/* Tags */}
                        {strategy.tags && strategy.tags.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            {strategy.tags.map(tag => (
                              <span
                                key={tag}
                                className="text-xs px-2 py-1 rounded-full bg-muted text-muted-foreground"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Action button */}
                      <div className="mt-6">
                        {strategy.is_subscribed ? (
                          <Button
                            variant="outline"
                            className="w-full"
                            onClick={() => handleUnsubscribe(strategy)}
                          >
                            Unsubscribe
                          </Button>
                        ) : (
                          <Button
                            className="w-full"
                            onClick={() => openSubscribeDialog(strategy)}
                          >
                            <Plus className="h-4 w-4 mr-2" /> Subscribe
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Subscribe Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Subscribe to {selectedStrategy?.name}</DialogTitle>
            <DialogDescription>
              Select a bot to receive signals from this strategy. The bot will automatically execute trades based on the strategy's signals.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label>Select Bot</Label>
            <Select value={selectedBotId} onValueChange={setSelectedBotId}>
              <SelectTrigger className="mt-2">
                <SelectValue placeholder="Choose a bot..." />
              </SelectTrigger>
              <SelectContent>
                {bots.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-muted-foreground">
                    No bots available. Create a bot first.
                  </div>
                ) : (
                  bots.map(bot => (
                    <SelectItem key={bot.id} value={String(bot.id)}>
                      {bot.symbol} - {bot.timeframe}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSubscribe} disabled={!selectedBotId || isSubscribing}>
              {isSubscribing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Subscribing...
                </>
              ) : (
                'Subscribe'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
