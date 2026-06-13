'use client';

import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Sparkles, X, Send, Loader2, Lightbulb, AlertTriangle, CheckCircle } from 'lucide-react';
import { aiEverywhereAPI } from '@/lib/api/client';

interface AskAIButtonProps {
  page: string;
  metrics?: string[];
  filters?: Record<string, any>;
  dateRange?: [string, string];
  selectedEntity?: Record<string, any>;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg';
}

interface AIResponse {
  answer: string;
  metrics_used: Array<{
    code: string;
    name: string;
    value: number;
    status: string;
  }>;
  insights: string[];
  actions: string[];
  confidence: number;
}

export function AskAIButton({
  page,
  metrics = [],
  filters = {},
  dateRange,
  selectedEntity,
  variant = 'outline',
  size = 'sm',
}: AskAIButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AIResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAsk = useCallback(async () => {
    if (!question.trim()) return;
    
    setLoading(true);
    setError(null);
    setResponse(null);
    
    try {
      const res = await aiEverywhereAPI.ask({
        question: question.trim(),
        page_context: {
          page,
          metrics,
          filters,
          date_range: dateRange,
          selected_entity: selectedEntity,
        },
      });
      setResponse(res.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get AI response');
    } finally {
      setLoading(false);
    }
  }, [question, page, metrics, filters, dateRange, selectedEntity]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  const quickQuestions = [
    'What are the key risks?',
    'How is revenue trending?',
    'Any anomalies to worry about?',
    'What actions should I take?',
  ];

  return (
    <>
      <Button
        variant={variant}
        size={size}
        onClick={() => setIsOpen(true)}
        className="gap-2"
      >
        <Sparkles className="h-4 w-4" />
        Ask AI
      </Button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-2xl mx-4 max-h-[80vh] overflow-hidden flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-500" />
                Ask AI About This Page
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setIsOpen(false);
                  setResponse(null);
                  setQuestion('');
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            
            <CardContent className="flex-1 overflow-auto">
              {!response ? (
                <div className="space-y-4">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Ask anything about this page..."
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      onKeyDown={handleKeyDown}
                      disabled={loading}
                      className="flex-1"
                    />
                    <Button
                      onClick={handleAsk}
                      disabled={loading || !question.trim()}
                    >
                      {loading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  
                  <div className="flex flex-wrap gap-2">
                    {quickQuestions.map((q) => (
                      <Button
                        key={q}
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setQuestion(q);
                        }}
                        className="text-xs"
                      >
                        {q}
                      </Button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-purple-50 dark:bg-purple-950/30 rounded-lg p-4">
                    <p className="text-sm text-purple-900 dark:text-purple-100 whitespace-pre-wrap">
                      {response.answer}
                    </p>
                  </div>
                  
                  {response.insights.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <Lightbulb className="h-4 w-4 text-yellow-500" />
                        Key Insights
                      </h4>
                      <ul className="space-y-1">
                        {response.insights.map((insight, i) => (
                          <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-xs mt-0.5">•</span>
                            {insight}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {response.actions.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Recommended Actions
                      </h4>
                      <ul className="space-y-1">
                        {response.actions.map((action, i) => (
                          <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-xs mt-0.5">→</span>
                            {action}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {response.metrics_used.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Metrics Referenced</h4>
                      <div className="flex flex-wrap gap-2">
                        {response.metrics_used.map((m) => (
                          <Badge
                            key={m.code}
                            variant={
                              m.status === 'critical' ? 'destructive' :
                              m.status === 'warning' ? 'default' : 'secondary'
                            }
                          >
                            {m.name}: {m.value.toFixed(1)}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between pt-2 border-t">
                    <span className="text-xs text-muted-foreground">
                      Confidence: {(response.confidence * 100).toFixed(0)}%
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setResponse(null);
                        setQuestion('');
                      }}
                    >
                      Ask Another Question
                    </Button>
                  </div>
                </div>
              )}
              
              {error && (
                <div className="mt-4 bg-red-50 dark:bg-red-950/30 rounded-lg p-3">
                  <p className="text-sm text-red-600 dark:text-red-400 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    {error}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}
