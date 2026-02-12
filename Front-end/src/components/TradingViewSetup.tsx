import { useState } from 'react';
import { Copy, Check, Info, Lightbulb } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import type { TradingViewSetup as TradingViewSetupType } from '@/types/trade-detail.ts';

interface TradingViewSetupProps {
  webhookUrl: string;
  setup?: TradingViewSetupType;
}

export function TradingViewSetup({ webhookUrl, setup }: TradingViewSetupProps) {
  const [messageType, setMessageType] = useState<'basic' | 'ai' | 'exit'>('basic');
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [copiedMessage, setCopiedMessage] = useState(false);

  // Default messages if setup is not provided
  const defaultMessages = {
    basic: '{"action": "{{strategy.order.action}}", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}',
    exit: '{"action": "CLOSE", "symbol": "{{ticker}}", "timeframe": "{{interval}}"}',
    ai: '{"action": "{{strategy.order.action}}", "symbol": "{{ticker}}", "timeframe": "{{interval}}", "strategy_type": "momentum", "entry_indicator": "RSI", "rsi_value": {{rsi}}, "rsi_period": 14}',
  };

  const messages = {
    basic: setup?.basic_message || defaultMessages.basic,
    ai: setup?.ai_learning_message || defaultMessages.ai,
    exit: setup?.exit_message || defaultMessages.exit,
  };

  const defaultInstructions = [
    'In TradingView, create an alert on your strategy',
    'Set "Webhook URL" to the URL above',
    'Paste the alert message into the message field',
    'Enable the Webhook checkbox',
    'Set alert to trigger "Once Per Bar Close" for best results',
  ];

  const instructions = setup?.instructions || defaultInstructions;

  const copyToClipboard = async (text: string, type: 'url' | 'message') => {
    try {
      await navigator.clipboard.writeText(text);
      if (type === 'url') {
        setCopiedUrl(true);
        setTimeout(() => setCopiedUrl(false), 2000);
      } else {
        setCopiedMessage(true);
        setTimeout(() => setCopiedMessage(false), 2000);
      }
      toast.success('Copied to clipboard!');
    } catch {
      toast.error('Failed to copy');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Info className="h-5 w-5 text-primary" />
          TradingView Webhook Setup
        </CardTitle>
        <CardDescription>
          Connect your TradingView alerts to this bot
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Webhook URL */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Webhook URL</label>
          <div className="flex gap-2">
            <Input 
              value={webhookUrl} 
              readOnly 
              className="font-mono text-xs bg-muted"
            />
            <Button 
              variant="outline" 
              size="icon"
              onClick={() => copyToClipboard(webhookUrl, 'url')}
            >
              {copiedUrl ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        {/* Message Type Tabs */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Alert Message</label>
          <Tabs value={messageType} onValueChange={(v) => setMessageType(v as 'basic' | 'ai' | 'exit')}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="basic">Basic</TabsTrigger>
              <TabsTrigger value="ai">
                <Lightbulb className="h-3 w-3 mr-1" />
                AI Learning
              </TabsTrigger>
              <TabsTrigger value="exit">Exit</TabsTrigger>
            </TabsList>

            <TabsContent value="basic" className="space-y-2">
              <p className="text-xs text-muted-foreground">
                Standard entry/exit signals for automated trading
              </p>
            </TabsContent>
            <TabsContent value="ai" className="space-y-2">
              <p className="text-xs text-muted-foreground">
                Enhanced format with indicator data to help improve strategy performance
              </p>
            </TabsContent>
            <TabsContent value="exit" className="space-y-2">
              <p className="text-xs text-muted-foreground">
                Use this for closing positions when your strategy exits
              </p>
            </TabsContent>
          </Tabs>

          <div className="flex gap-2">
            <div className="flex-1 bg-muted rounded-md p-3">
              <code className="text-xs font-mono break-all text-foreground whitespace-pre-wrap">
                {messages[messageType]}
              </code>
            </div>
            <Button 
              variant="outline" 
              size="icon"
              onClick={() => copyToClipboard(messages[messageType], 'message')}
            >
              {copiedMessage ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        {/* Instructions */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            <p className="font-medium mb-2">Setup Instructions:</p>
            <ol className="list-decimal list-inside space-y-1 text-sm">
              {instructions.map((instruction, i) => (
                <li key={i}>{instruction}</li>
              ))}
            </ol>
          </AlertDescription>
        </Alert>

        {/* AI Learning Tip */}
        {messageType === 'ai' && setup?.ai_learning_params && (
          <Alert className="border-primary/50 bg-primary/5">
            <Lightbulb className="h-4 w-4 text-primary" />
            <AlertDescription>
              <p className="font-medium mb-2 text-primary">AI Learning Parameters:</p>
              <ul className="text-sm space-y-1">
                {Object.entries(setup.ai_learning_params).map(([key, desc]) => (
                  <li key={key}>
                    <code className="text-xs bg-muted px-1 rounded">{key}</code>: {desc}
                  </li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
