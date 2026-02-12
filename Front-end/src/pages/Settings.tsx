import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Key, Webhook, Shield, Copy, RefreshCw, Check, AlertTriangle, Bell, Mail, Send } from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { ApiKeyStatus, WebhookToken, NotificationSettings } from '@/types/api';

export default function Settings() {
  const [isLoading, setIsLoading] = useState(true);
  const [apiKeyStatus, setApiKeyStatus] = useState<ApiKeyStatus | null>(null);
  const [webhook, setWebhook] = useState<WebhookToken | null>(null);
  const [notifications, setNotifications] = useState<NotificationSettings | null>(null);

  // API Keys form state
  const [apiKey, setApiKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [mode, setMode] = useState<'paper' | 'live'>('paper');
  const [isSaving, setIsSaving] = useState(false);
  const [isSendingTest, setIsSendingTest] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statusRes = await api.getApiKeyStatus();
        setApiKeyStatus(statusRes);
        if (statusRes.mode) {
          setMode(statusRes.mode);
        }
      } catch (error) {
        console.error('Failed to load API key status:', error);
      }

      try {
        const webhookRes = await api.getWebhookToken();
        setWebhook(webhookRes);
      } catch (error) {
        // Webhook may not exist yet - user can generate one
        console.error('No webhook token found:', error);
        setWebhook(null);
      }

      try {
        const notificationsRes = await api.getNotificationSettings();
        setNotifications(notificationsRes);
      } catch (error) {
        console.error('Failed to load notification settings:', error);
        setNotifications(null);
      }

      setIsLoading(false);
    };
    fetchData();
  }, []);

  const handleSaveApiKeys = async () => {
    if (!apiKey || !secretKey) {
      toast.error('Please enter both API key and secret key');
      return;
    }
    setIsSaving(true);
    try {
      await api.setApiKeys({ api_key: apiKey, secret_key: secretKey, mode });
      setApiKeyStatus({ configured: true, mode });
      setApiKey('');
      setSecretKey('');
      toast.success('API keys saved successfully');
    } catch (error) {
      toast.error('Failed to save API keys');
    } finally {
      setIsSaving(false);
    }
  };

  const copyWebhook = () => {
    if (webhook?.webhook_url) {
      navigator.clipboard.writeText(webhook.webhook_url);
      toast.success('Webhook URL copied');
    }
  };

  const [isGenerating, setIsGenerating] = useState(false);

  const generateOrRegenerateToken = async () => {
    setIsGenerating(true);
    try {
      const result = await api.regenerateWebhookToken();
      setWebhook({ token: result.token, webhook_url: result.webhook_url });
      toast.success(webhook ? 'Webhook token regenerated' : 'Webhook token generated');
    } catch (error) {
      toast.error('Failed to generate webhook token');
    } finally {
      setIsGenerating(false);
    }
  };

  const updateNotificationSetting = async (updates: Partial<NotificationSettings>) => {
    if (!notifications) return;
    
    const previousSettings = { ...notifications };
    setNotifications({ ...notifications, ...updates });
    
    try {
      const result = await api.updateNotificationSettings(updates);
      setNotifications(result);
      toast.success('Notification settings updated');
    } catch (error) {
      setNotifications(previousSettings);
      toast.error('Failed to update notification settings');
    }
  };

  const handleSendTestEmail = async () => {
    setIsSendingTest(true);
    try {
      const result = await api.sendTestEmail();
      if (result.success) {
        toast.success(result.message || `Test email sent to ${notifications?.email}`);
      } else {
        toast.error(result.error || 'Failed to send test email');
      }
    } catch (error) {
      toast.error('Failed to send test email');
    } finally {
      setIsSendingTest(false);
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-12 w-64" />
          <Skeleton className="h-64 w-full" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Settings</h1>
          <p className="text-muted-foreground mt-1">Manage your API keys and webhook configuration</p>
        </div>

        <Tabs defaultValue="api-keys" className="w-full">
          <TabsList className="grid w-full max-w-lg grid-cols-3">
            <TabsTrigger value="api-keys" className="gap-2">
              <Key className="h-4 w-4" /> API Keys
            </TabsTrigger>
            <TabsTrigger value="webhook" className="gap-2">
              <Webhook className="h-4 w-4" /> Webhook
            </TabsTrigger>
            <TabsTrigger value="notifications" className="gap-2">
              <Bell className="h-4 w-4" /> Notifications
            </TabsTrigger>
          </TabsList>

          <TabsContent value="api-keys" className="mt-6">
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-primary" />
                    Alpaca API Keys
                  </CardTitle>
                  <CardDescription>
                    Connect your Alpaca account to enable trading. Your keys are encrypted and stored securely.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Status indicator */}
                  <div className={`flex items-center gap-2 px-4 py-3 rounded-lg ${apiKeyStatus?.configured ? 'bg-primary/10 border border-primary/20' : 'bg-muted'}`}>
                    {apiKeyStatus?.configured ? (
                      <>
                        <Check className="h-5 w-5 text-primary" />
                        <div>
                          <p className="font-medium text-foreground">API Keys Configured</p>
                          <p className="text-sm text-muted-foreground">Mode: {apiKeyStatus.mode === 'paper' ? 'Paper Trading' : 'Live Trading'}</p>
                        </div>
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="h-5 w-5 text-yellow-500" />
                        <div>
                          <p className="font-medium text-foreground">API Keys Not Configured</p>
                          <p className="text-sm text-muted-foreground">Add your Alpaca credentials to start trading</p>
                        </div>
                      </>
                    )}
                  </div>

                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="api-key">API Key</Label>
                      <Input
                        id="api-key"
                        type="text"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="PK..."
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="secret-key">Secret Key</Label>
                      <Input
                        id="secret-key"
                        type="password"
                        value={secretKey}
                        onChange={(e) => setSecretKey(e.target.value)}
                        placeholder="••••••••••••••••"
                      />
                    </div>
                    <div className="space-y-3">
                      <Label>Trading Mode</Label>
                      <RadioGroup value={mode} onValueChange={(v) => setMode(v as 'paper' | 'live')} className="flex gap-4">
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="paper" id="paper" />
                          <Label htmlFor="paper" className="cursor-pointer">Paper Trading</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="live" id="live" />
                          <Label htmlFor="live" className="cursor-pointer text-destructive">Live Trading</Label>
                        </div>
                      </RadioGroup>
                      {mode === 'live' && (
                        <p className="text-sm text-destructive flex items-center gap-1">
                          <AlertTriangle className="h-4 w-4" />
                          Live trading uses real money. Proceed with caution.
                        </p>
                      )}
                    </div>
                  </div>

                  <Button onClick={handleSaveApiKeys} disabled={isSaving} className="w-full sm:w-auto">
                    {isSaving ? 'Saving...' : 'Save API Keys'}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          <TabsContent value="webhook" className="mt-6">
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Webhook className="h-5 w-5 text-primary" />
                    Webhook Configuration
                  </CardTitle>
                  <CardDescription>
                    Use this webhook URL in TradingView alerts to trigger trades automatically.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {webhook ? (
                    <>
                      <div className="space-y-2">
                        <Label>Your Webhook URL</Label>
                        <div className="flex gap-2">
                          <Input
                            readOnly
                            value={webhook.webhook_url}
                            className="font-mono text-sm"
                          />
                          <Button variant="outline" onClick={copyWebhook}>
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label>Webhook Token</Label>
                        <div className="flex gap-2">
                          <Input
                            readOnly
                            value={webhook.token}
                            className="font-mono text-sm"
                          />
                          <Button variant="outline" onClick={generateOrRegenerateToken} disabled={isGenerating}>
                            <RefreshCw className={`h-4 w-4 ${isGenerating ? 'animate-spin' : ''}`} />
                          </Button>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Regenerating the token will invalidate the current webhook URL.
                        </p>
                      </div>

                      <div className="p-4 rounded-lg bg-muted space-y-4">
                        <h4 className="font-medium text-foreground">TradingView Setup</h4>
                        <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
                          <li>Create a new alert in TradingView</li>
                          <li>Set the webhook URL to your bot's URL</li>
                          <li>Use the dynamic alert messages below</li>
                          <li>TradingView auto-fills symbol, action, and timeframe</li>
                        </ol>
                        
                        <div className="space-y-3">
                          <div className="p-3 bg-background rounded border border-border">
                            <div className="flex items-center justify-between mb-1">
                              <p className="text-xs font-medium text-muted-foreground">Entry Alert Message:</p>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 px-2 text-xs"
                                onClick={() => {
                                  navigator.clipboard.writeText('{"action": "{{strategy.order.action}}", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}');
                                  toast.success('Entry alert copied');
                                }}
                              >
                                <Copy className="h-3 w-3 mr-1" /> Copy
                              </Button>
                            </div>
                            <code className="text-xs text-primary break-all">
                              {`{"action": "{{strategy.order.action}}", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}`}
                            </code>
                          </div>
                          
                          <div className="p-3 bg-background rounded border border-border">
                            <div className="flex items-center justify-between mb-1">
                              <p className="text-xs font-medium text-muted-foreground">Exit Alert Message:</p>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 px-2 text-xs"
                                onClick={() => {
                                  navigator.clipboard.writeText('{"action": "CLOSE", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}');
                                  toast.success('Exit alert copied');
                                }}
                              >
                                <Copy className="h-3 w-3 mr-1" /> Copy
                              </Button>
                            </div>
                            <code className="text-xs text-primary break-all">
                              {`{"action": "CLOSE", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}`}
                            </code>
                          </div>
                        </div>

                        <div className="p-3 bg-primary/5 rounded border border-primary/20">
                          <p className="text-xs font-medium text-primary mb-2">TradingView Variables:</p>
                          <ul className="text-xs text-muted-foreground space-y-1">
                            <li><code className="text-primary">{"{{strategy.order.action}}"}</code> → buy or sell</li>
                            <li><code className="text-primary">{"{{ticker}}"}</code> → SPY, AAPL, etc.</li>
                            <li><code className="text-primary">{"{{interval}}"}</code> → 5, 15, 60, D, etc.</li>
                          </ul>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-8 space-y-4">
                      <div className="flex justify-center">
                        <AlertTriangle className="h-12 w-12 text-yellow-500" />
                      </div>
                      <div>
                        <h4 className="font-medium text-foreground">No Webhook Token</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                          Generate a webhook token to receive TradingView alerts.
                        </p>
                      </div>
                      <Button onClick={generateOrRegenerateToken} disabled={isGenerating}>
                        {isGenerating ? 'Generating...' : 'Generate Webhook Token'}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          <TabsContent value="notifications" className="mt-6">
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Mail className="h-5 w-5 text-primary" />
                    Email Notifications
                  </CardTitle>
                  <CardDescription>
                    Receive email alerts when your bots execute trades.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {notifications ? (
                    <>
                      <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-muted">
                        <Mail className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="text-sm text-muted-foreground">Email</p>
                          <p className="font-medium text-foreground">{notifications.email}</p>
                        </div>
                      </div>

                      {/* Master Toggle */}
                      <div className="flex items-center justify-between p-4 rounded-lg border border-border">
                        <div className="space-y-0.5">
                          <Label htmlFor="notifications-enabled" className="text-base font-medium">
                            Enable Email Notifications
                          </Label>
                          <p className="text-sm text-muted-foreground">
                            Master switch for all email notifications
                          </p>
                        </div>
                        <Switch
                          id="notifications-enabled"
                          checked={notifications.email_notifications_enabled}
                          onCheckedChange={(checked) =>
                            updateNotificationSetting({ email_notifications_enabled: checked })
                          }
                        />
                      </div>

                      {/* Individual Toggles - only show when master is enabled */}
                      {notifications.email_notifications_enabled && (
                        <div className="space-y-4 pl-4 border-l-2 border-primary/20">
                          <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                              <Label htmlFor="notify-trade" className="font-medium">Trade Executions</Label>
                              <p className="text-sm text-muted-foreground">When a bot buys or sells</p>
                            </div>
                            <Switch
                              id="notify-trade"
                              checked={notifications.notify_on_trade}
                              onCheckedChange={(checked) =>
                                updateNotificationSetting({ notify_on_trade: checked })
                              }
                            />
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                              <Label htmlFor="notify-error" className="font-medium">Trade Errors</Label>
                              <p className="text-sm text-muted-foreground">When a trade fails</p>
                            </div>
                            <Switch
                              id="notify-error"
                              checked={notifications.notify_on_error}
                              onCheckedChange={(checked) =>
                                updateNotificationSetting({ notify_on_error: checked })
                              }
                            />
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                              <Label htmlFor="notify-risk" className="font-medium">Risk Events</Label>
                              <p className="text-sm text-muted-foreground">When risk limits trigger</p>
                            </div>
                            <Switch
                              id="notify-risk"
                              checked={notifications.notify_on_risk_event}
                              onCheckedChange={(checked) =>
                                updateNotificationSetting({ notify_on_risk_event: checked })
                              }
                            />
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                              <Label htmlFor="notify-summary" className="font-medium">Daily Summary</Label>
                              <p className="text-sm text-muted-foreground">Daily trading summary email</p>
                            </div>
                            <Switch
                              id="notify-summary"
                              checked={notifications.notify_daily_summary}
                              onCheckedChange={(checked) =>
                                updateNotificationSetting({ notify_daily_summary: checked })
                              }
                            />
                          </div>
                        </div>
                      )}

                      {/* Test Email Button */}
                      <div className="pt-4 border-t border-border">
                        <Button
                          variant="outline"
                          onClick={handleSendTestEmail}
                          disabled={!notifications.email_notifications_enabled || isSendingTest}
                          className="gap-2"
                        >
                          <Send className="h-4 w-4" />
                          {isSendingTest ? 'Sending...' : 'Send Test Email'}
                        </Button>
                        {!notifications.email_notifications_enabled && (
                          <p className="text-sm text-muted-foreground mt-2">
                            Enable notifications to send a test email
                          </p>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-8 space-y-4">
                      <div className="flex justify-center">
                        <AlertTriangle className="h-12 w-12 text-yellow-500" />
                      </div>
                      <div>
                        <h4 className="font-medium text-foreground">Unable to load notification settings</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                          Please try refreshing the page.
                        </p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
