'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Brain, Send, User, Loader2, Sparkles, AlertCircle, ChevronRight, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import { aiCfoAPI } from '@/lib/api/client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  confidence?: number;
  evidence_chain?: string[];
  reasoning_trace?: string;
}

const SUGGESTED_QUESTIONS = [
  "Why did revenue decline last month?",
  "Which department has the strongest margin?",
  "Forecast next quarter's revenue",
  "Find financial risks in our operations",
  "Suggest growth opportunities",
];

export function AICFOChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (question?: string) => {
    const query = question || input;
    if (!query.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const res = await aiCfoAPI.askQuestion({ user_query: query }) as any;
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.answer || res.data?.answer || 'No answer received.',
        timestamp: new Date(),
        confidence: res.confidence || res.data?.confidence || 0,
        evidence_chain: res.evidence_chain || res.data?.evidence_chain || [],
        reasoning_trace: res.reasoning_trace || res.data?.reasoning_trace || '',
      };
      setMessages((prev) => [...prev, aiResponse]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get answer from AI CFO');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="flex flex-col h-[600px]">
      <CardHeader className="flex flex-row items-center gap-2 pb-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
          <Brain className="h-4 w-4 text-primary-foreground" />
        </div>
        <CardTitle className="text-lg">AI CFO Assistant</CardTitle>
        <Badge variant="secondary" className="ml-auto">
          <Sparkles className="h-3 w-3 mr-1" />
          AI-Powered
        </Badge>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col overflow-hidden p-0">
        <ScrollArea className="flex-1 px-4" ref={scrollRef}>
          <div className="space-y-4 py-4">
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
                <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
                  Dismiss
                </button>
              </div>
            )}

            {messages.length === 0 && !error && (
              <div className="text-center space-y-4">
                <div className="flex justify-center">
                  <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                    <Brain className="h-8 w-8 text-primary" />
                  </div>
                </div>
                <div>
                  <h3 className="font-medium">Welcome to AI CFO</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    Ask me anything about your financial data
                  </p>
                </div>
                <div className="grid gap-2 max-w-sm mx-auto">
                  {SUGGESTED_QUESTIONS.map((question, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      className="text-left text-sm h-auto py-2 px-3"
                      onClick={() => handleSend(question)}
                      disabled={isLoading}
                    >
                      {question}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  'flex gap-3',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                {message.role === 'assistant' && (
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary shrink-0">
                    <Brain className="h-4 w-4 text-primary-foreground" />
                  </div>
                )}
                <div
                  className={cn(
                    'rounded-lg px-4 py-3 max-w-[80%]',
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  )}
                >
                  <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                  {message.confidence != null && message.confidence > 0 && (
                    <div className="mt-2 text-xs opacity-70">
                      Confidence: {(message.confidence * 100).toFixed(0)}%
                    </div>
                  )}
                  {message.evidence_chain && message.evidence_chain.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-border/50">
                      <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Evidence</p>
                      <div className="flex flex-wrap gap-1">
                        {message.evidence_chain.map((evidence, i) => (
                          <Badge key={i} variant="outline" className="text-[10px]">
                            {evidence}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {message.reasoning_trace && (
                    <details className="mt-2 group">
                      <summary className="text-xs font-semibold text-muted-foreground cursor-pointer hover:text-foreground flex items-center gap-1">
                        <ChevronRight className="h-3 w-3 transition-transform group-open:rotate-90" />
                        Reasoning
                      </summary>
                      <p className="text-xs text-muted-foreground mt-1 pl-4 whitespace-pre-wrap">{message.reasoning_trace}</p>
                    </details>
                  )}
                  <div className="mt-2 text-[10px] text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
                {message.role === 'user' && (
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted shrink-0">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary shrink-0">
                  <Brain className="h-4 w-4 text-primary-foreground" />
                </div>
                <div className="rounded-lg px-4 py-3 bg-muted">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="p-4 border-t">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex gap-2"
          >
            <Input
              placeholder="Ask about revenue, expenses, forecasts..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" size="icon" disabled={isLoading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  );
}
