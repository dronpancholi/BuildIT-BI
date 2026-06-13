'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { copilotAPI } from '@/lib/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Bot,
  User,
  Send,
  Loader2,
  MessageSquare,
  Copy,
  Check,
  Trash2,
  Archive,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  RotateCcw,
  Sparkles,
  Clock,
  Brain,
  ArrowRight,
  PanelLeftClose,
  PanelLeftOpen,
  Eye,
  EyeOff,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ReasoningStep {
  step: string;
  label: string;
  description: string;
  result: string;
  confidence: number;
  duration_ms: number;
  status: 'completed' | 'pending' | 'error';
}

interface MessageAction {
  type: string;
  label: string;
  detail: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  confidence?: number;
  reasoning_steps?: ReasoningStep[];
  actions_taken?: MessageAction[];
  error?: string;
  is_loading?: boolean;
}

interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  archived: boolean;
}

interface Suggestion {
  id: string;
  category: string;
  query: string;
  description: string;
  icon: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const REASONING_STEPS = [
  'PARSE',
  'CLASSIFY',
  'ROUTE',
  'RETRIEVE',
  'COMPUTE',
  'VALIDATE',
  'SYNTHESIZE',
  'EXPLAIN',
] as const;

const STEP_META: Record<string, { label: string; description: string }> = {
  PARSE: { label: 'Parse', description: 'Extracting intent and entities from the query' },
  CLASSIFY: { label: 'Classify', description: 'Determining query type and domain' },
  ROUTE: { label: 'Route', description: 'Selecting optimal data sources and models' },
  RETRIEVE: { label: 'Retrieve', description: 'Fetching relevant financial data' },
  COMPUTE: { label: 'Compute', description: 'Executing calculations and formulas' },
  VALIDATE: { label: 'Validate', description: 'Verifying data integrity and accuracy' },
  SYNTHESIZE: { label: 'Synthesize', description: 'Combining results into coherent answer' },
  EXPLAIN: { label: 'Explain', description: 'Generating human-readable explanation' },
};

const DEFAULT_SUGGESTIONS: Suggestion[] = [
  { id: '1', category: 'Financial Analysis', query: 'What is our current operating margin?', description: 'Calculate the operating margin percentage', icon: '📊' },
  { id: '2', category: 'Revenue', query: 'Show me YTD revenue by service line', description: 'Breakdown of revenue by department', icon: '💰' },
  { id: '3', category: 'Accounts Receivable', query: 'What are our AR days and aging breakdown?', description: 'Analyze receivables aging and days outstanding', icon: '📈' },
  { id: '4', category: 'Budget', query: 'Compare actual vs budgeted expenses', description: 'Variance analysis against budget', icon: '📉' },
  { id: '5', category: 'Payer Mix', query: 'Analyze payer mix and reimbursement rates', description: 'Breakdown of revenue by payer type', icon: '🏥' },
  { id: '6', category: 'Forecasting', query: 'Forecast next quarter revenue', description: 'AI-powered revenue prediction', icon: '🔮' },
];

// ---------------------------------------------------------------------------
// Helper Components
// ---------------------------------------------------------------------------

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const color =
    confidence >= 0.9
      ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
      : confidence >= 0.7
        ? 'bg-amber-100 text-amber-800 border-amber-200'
        : 'bg-red-100 text-red-800 border-red-200';

  return (
    <Badge className={`${color} text-xs`}>
      {Math.round(confidence * 100)}% confidence
    </Badge>
  );
}

function ActionChip({ action }: { action: MessageAction }) {
  return (
    <div className="flex items-center gap-1.5 text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded-full px-2.5 py-0.5">
      <ArrowRight className="h-3 w-3" />
      <span className="font-medium">{action.label}</span>
      {action.detail && <span className="text-blue-500">- {action.detail}</span>}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3 py-2">
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
      <span className="ml-2 text-sm text-gray-500">Thinking...</span>
    </div>
  );
}

function ReasoningTimeline({ steps }: { steps: ReasoningStep[] }) {
  return (
    <div className="relative ml-2 mt-2">
      {steps.map((step, idx) => {
        const meta = STEP_META[step.step] || { label: step.step, description: '' };
        const isLast = idx === steps.length - 1;

        return (
          <div key={`${step.step}-${idx}`} className="relative flex gap-3 pb-3 last:pb-0">
            {/* Vertical line */}
            {!isLast && (
              <div className="absolute left-[9px] top-5 w-0.5 h-[calc(100%-8px)] bg-gray-200" />
            )}

            {/* Step circle */}
            <div
              className={`relative z-10 flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                step.status === 'completed'
                  ? 'bg-emerald-500 border-emerald-500'
                  : step.status === 'error'
                    ? 'bg-red-500 border-red-500'
                    : 'bg-white border-gray-300'
              }`}
            >
              {step.status === 'completed' && <Check className="h-3 w-3 text-white" />}
              {step.status === 'error' && <AlertCircle className="h-3 w-3 text-white" />}
            </div>

            {/* Step content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-gray-900">
                  {meta.label}
                </span>
                <span className="text-xs text-gray-400 font-mono">{step.step}</span>
                {step.confidence > 0 && (
                  <span className="text-xs text-gray-500">{Math.round(step.confidence * 100)}%</span>
                )}
                {step.duration_ms > 0 && (
                  <span className="text-xs text-gray-400">{step.duration_ms}ms</span>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-0.5">{meta.description}</p>
              {step.result && (
                <div className="mt-1 p-2 bg-gray-50 border border-gray-100 rounded text-xs text-gray-700 font-mono max-h-20 overflow-y-auto">
                  {step.result}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function CopilotPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [expandedReasoning, setExpandedReasoning] = useState<string | null>(null);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [retryMessageId, setRetryMessageId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // ------- Auto-scroll -------

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // ------- Keyboard shortcut -------

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [inputValue, isProcessing],
  );

  // ------- Load conversations -------

  useEffect(() => {
    loadConversations();
  }, []);

  async function loadConversations() {
    try {
      const res = await copilotAPI.listConversations();
      setConversations(res.data.conversations || []);
    } catch {
      // optional
    }
  }

  async function loadConversation(id: string) {
    setActiveConversationId(id);
    try {
      const res = await copilotAPI.getConversation(id);
      setMessages(res.data.messages || []);
    } catch {
      setMessages([
        {
          id: 'error-conv',
          role: 'system',
          content: 'Failed to load conversation.',
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  }

  async function archiveConversation(id: string) {
    try {
      await copilotAPI.archiveConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConversationId === id) {
        setActiveConversationId(null);
        setMessages([]);
      }
    } catch {
      // optional
    }
  }

  function clearConversation() {
    setMessages([]);
    setActiveConversationId(null);
  }

  // ------- Clipboard -------

  function copyToClipboard(text: string, messageId: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    });
  }

  // ------- Send message -------

  async function sendMessage(retryQuery?: string) {
    const query = retryQuery || inputValue.trim();
    if (!query || isProcessing) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };

    if (!retryQuery) setInputValue('');
    setRetryMessageId(null);

    setMessages((prev) => [...prev.filter((m) => !m.is_loading), userMessage]);
    setIsProcessing(true);

    const loadingMsg: ChatMessage = {
      id: `loading-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      is_loading: true,
    };
    setMessages((prev) => [...prev, loadingMsg]);

    try {
      const res = await copilotAPI.processQuery({
        user_query: query,
        context: activeConversationId ? { conversation_id: activeConversationId } : undefined,
      });

      const msg = res.data.data?.message;

      const assistantMessage: ChatMessage = {
        id: msg?.id || `assistant-${Date.now()}`,
        role: 'assistant',
        content: msg?.content || 'No response received.',
        timestamp: new Date().toISOString(),
        confidence: msg?.confidence,
        reasoning_steps: msg?.reasoning_steps || [],
        actions_taken: msg?.actions_taken || [],
      };

      setMessages((prev) => prev.filter((m) => !m.is_loading).concat([assistantMessage]));

      if (res.data.data?.conversation_id) {
        setActiveConversationId(res.data.data.conversation_id);
        loadConversations();
      }
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        error: err instanceof Error ? err.message : 'Unknown error',
      };
      setMessages((prev) => prev.filter((m) => !m.is_loading).concat([errorMsg]));
    } finally {
      setIsProcessing(false);
      inputRef.current?.focus();
    }
  }

  // ------- Retry -------

  function retryMessage(messageId: string) {
    const msg = messages.find((m) => m.id === messageId);
    if (!msg) return;
    const prevUserMsg = messages
      .slice(0, messages.indexOf(msg))
      .reverse()
      .find((m) => m.role === 'user');
    if (prevUserMsg) {
      setMessages((prev) => prev.filter((m) => m.id !== messageId));
      sendMessage(prevUserMsg.content);
    }
  }

  // ------- Suggestion click -------

  function handleSuggestionClick(query: string) {
    setInputValue(query);
    setShowSuggestions(false);
    inputRef.current?.focus();
  }

  // ------- Toggle reasoning -------

  function toggleReasoning(messageId: string) {
    setExpandedReasoning((prev) => (prev === messageId ? null : messageId));
  }

  // ------- Helpers -------

  function formatDate(iso: string) {
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function truncateText(text: string, len: number) {
    return text.length > len ? text.slice(0, len) + '...' : text;
  }

  // ------- Render -------

  return (
    <DashboardLayout>
      <div className="flex h-[calc(100vh-4rem)] gap-0 overflow-hidden">
        {/* ================================================================
            Conversations Sidebar
        ================================================================ */}
        {sidebarOpen && (
          <div className="w-72 flex-shrink-0 border-r bg-gray-50 flex flex-col">
            <div className="p-3 border-b flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                Conversations
              </h2>
              <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(false)} className="h-7 px-2">
                <PanelLeftClose className="h-4 w-4" />
              </Button>
            </div>
            <ScrollArea className="flex-1">
              {conversations.length === 0 ? (
                <div className="p-4 text-center text-sm text-gray-400">No conversations yet</div>
              ) : (
                <div className="p-2 space-y-1">
                  {conversations
                    .filter((c) => !c.archived)
                    .map((conv) => (
                      <div
                        key={conv.id}
                        className={`group p-2.5 rounded-lg cursor-pointer text-sm transition-colors ${
                          activeConversationId === conv.id
                            ? 'bg-blue-100 text-blue-900 border border-blue-200'
                            : 'hover:bg-gray-100 text-gray-700'
                        }`}
                        onClick={() => loadConversation(conv.id)}
                      >
                        <div className="flex items-center justify-between">
                          <span className="truncate font-medium">{conv.title}</span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              archiveConversation(conv.id);
                            }}
                            className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-gray-600"
                          >
                            <Archive className="h-3.5 w-3.5" />
                          </button>
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                          <Clock className="h-3 w-3" />
                          {formatDate(conv.updated_at)}
                          <span className="text-gray-300">|</span>
                          {conv.message_count} messages
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </ScrollArea>
          </div>
        )}

        {/* ================================================================
            Main Chat Area
        ================================================================ */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Chat Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b bg-white">
            <div className="flex items-center gap-3">
              {!sidebarOpen && (
                <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(true)} className="h-8 px-2">
                  <PanelLeftOpen className="h-4 w-4" />
                </Button>
              )}
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-white" />
                </div>
                <div>
                  <h1 className="text-sm font-semibold text-gray-900">AI CFO Copilot</h1>
                  <p className="text-xs text-gray-500">Healthcare Financial Intelligence</p>
                </div>
              </div>
              {isProcessing && (
                <Badge className="bg-blue-100 text-blue-700 border-blue-200 text-xs animate-pulse">
                  Processing
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSuggestions(!showSuggestions)}
                className="h-8 px-2 text-gray-500"
              >
                <Sparkles className="h-4 w-4 mr-1" />
                {showSuggestions ? 'Hide' : 'Show'} Suggestions
              </Button>
              <Separator orientation="vertical" className="h-6" />
              <Button
                variant="ghost"
                size="sm"
                onClick={clearConversation}
                className="h-8 px-2 text-gray-500 hover:text-red-600"
                disabled={messages.length === 0}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Clear
              </Button>
            </div>
          </div>

          {/* Messages + Suggestions layout */}
          <div className="flex-1 flex overflow-hidden">
            {/* Messages Column */}
            <div className="flex-1 flex flex-col min-w-0">
              <ScrollArea className="flex-1 px-4">
                {/* Empty state */}
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full py-12 text-center">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-4 shadow-lg">
                      <Bot className="h-8 w-8 text-white" />
                    </div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-1">AI CFO Copilot</h2>
                    <p className="text-sm text-gray-500 max-w-md">
                      Ask questions about your healthcare financial data. I can analyze margins, revenue,
                      AR aging, budgets, payer mix, and more.
                    </p>
                    <div className="mt-6 grid grid-cols-2 gap-3 max-w-lg">
                      {DEFAULT_SUGGESTIONS.slice(0, 4).map((s) => (
                        <button
                          key={s.id}
                          onClick={() => handleSuggestionClick(s.query)}
                          className="p-3 text-left border border-gray-200 rounded-xl hover:border-blue-300 hover:bg-blue-50 transition-colors group"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-lg">{s.icon}</span>
                            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                              {s.category}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 font-medium group-hover:text-blue-700">
                            {s.query}
                          </p>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Message list */}
                <div className="py-4 space-y-4">
                  {messages.map((msg) => {
                    const isUser = msg.role === 'user';
                    const isSystem = msg.role === 'system';

                    if (isSystem) {
                      return (
                        <div key={msg.id} className="flex justify-center">
                          <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 text-sm px-4 py-2 rounded-lg flex items-center gap-2">
                            <AlertCircle className="h-4 w-4" />
                            {msg.content}
                          </div>
                        </div>
                      );
                    }

                    if (msg.is_loading) {
                      return (
                        <div key={msg.id} className="flex gap-3">
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                            <Loader2 className="h-4 w-4 text-white animate-spin" />
                          </div>
                          <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-2">
                            <TypingIndicator />
                          </div>
                        </div>
                      );
                    }

                    return (
                      <div key={msg.id} className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
                        {/* Avatar */}
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                            isUser
                              ? 'bg-gray-200'
                              : 'bg-gradient-to-br from-blue-500 to-purple-600'
                          }`}
                        >
                          {isUser ? (
                            <User className="h-4 w-4 text-gray-600" />
                          ) : (
                            <Bot className="h-4 w-4 text-white" />
                          )}
                        </div>

                        {/* Bubble */}
                        <div className={`flex flex-col max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
                          <div
                            className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                              isUser
                                ? 'bg-blue-600 text-white rounded-tr-sm'
                                : msg.error
                                  ? 'bg-red-50 border border-red-200 text-red-800 rounded-tl-sm'
                                  : 'bg-gray-100 text-gray-900 rounded-tl-sm'
                            }`}
                          >
                            <div className="whitespace-pre-wrap break-words">{msg.content}</div>
                          </div>

                          {/* Metadata — assistant only */}
                          {!isUser && (
                            <div className="mt-1.5 space-y-1.5 w-full">
                              {/* Actions */}
                              {msg.actions_taken && msg.actions_taken.length > 0 && (
                                <div className="flex flex-wrap gap-1.5">
                                  {msg.actions_taken.map((action, i) => (
                                    <ActionChip key={i} action={action} />
                                  ))}
                                </div>
                              )}

                              {/* Confidence + reasoning toggle */}
                              <div className="flex items-center gap-2 flex-wrap">
                                {msg.confidence !== undefined && msg.confidence !== null && (
                                  <ConfidenceBadge confidence={msg.confidence} />
                                )}

                                {msg.reasoning_steps && msg.reasoning_steps.length > 0 && (
                                  <button
                                    onClick={() => toggleReasoning(msg.id)}
                                    className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
                                  >
                                    {expandedReasoning === msg.id ? (
                                      <EyeOff className="h-3.5 w-3.5" />
                                    ) : (
                                      <Eye className="h-3.5 w-3.5" />
                                    )}
                                    Reasoning trace
                                    {expandedReasoning === msg.id ? (
                                      <ChevronDown className="h-3 w-3" />
                                    ) : (
                                      <ChevronRight className="h-3 w-3" />
                                    )}
                                  </button>
                                )}

                                {/* Copy */}
                                <button
                                  onClick={() => copyToClipboard(msg.content, msg.id)}
                                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
                                >
                                  {copiedMessageId === msg.id ? (
                                    <Check className="h-3.5 w-3.5 text-emerald-500" />
                                  ) : (
                                    <Copy className="h-3.5 w-3.5" />
                                  )}
                                  {copiedMessageId === msg.id ? 'Copied' : 'Copy'}
                                </button>

                                {/* Retry */}
                                {msg.error && (
                                  <button
                                    onClick={() => retryMessage(msg.id)}
                                    className="flex items-center gap-1 text-xs text-gray-400 hover:text-blue-600 transition-colors"
                                  >
                                    <RotateCcw className="h-3.5 w-3.5" />
                                    Retry
                                  </button>
                                )}
                              </div>

                              {/* Reasoning chain */}
                              {expandedReasoning === msg.id && msg.reasoning_steps && (
                                <Card className="border-gray-200">
                                  <CardContent className="p-3">
                                    <div className="flex items-center gap-2 mb-2">
                                      <Brain className="h-4 w-4 text-purple-600" />
                                      <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                                        Reasoning Chain
                                      </span>
                                    </div>
                                    <ReasoningTimeline steps={msg.reasoning_steps} />
                                  </CardContent>
                                </Card>
                              )}

                              {/* Timestamp */}
                              <div className="text-xs text-gray-400">{formatDate(msg.timestamp)}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              {/* Input Bar */}
              <div className="p-4 border-t bg-white">
                <div className="flex items-center gap-3">
                  <div className="flex-1 relative">
                    <Input
                      ref={inputRef}
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Ask about financial data, metrics, forecasts..."
                      disabled={isProcessing}
                      className="pr-10 h-12 text-sm"
                    />
                  </div>
                  <Button
                    onClick={() => sendMessage()}
                    disabled={!inputValue.trim() || isProcessing}
                    className="h-12 w-12 p-0 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 rounded-xl"
                  >
                    {isProcessing ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      <Send className="h-5 w-5" />
                    )}
                  </Button>
                </div>
                <p className="text-xs text-gray-400 mt-1.5 text-center">
                  Press <kbd className="px-1 py-0.5 bg-gray-100 border border-gray-200 rounded text-[10px] font-mono">Enter</kbd> to send
                </p>
              </div>
            </div>

            {/* ================================================================
                Suggestions Sidebar
            ================================================================ */}
            {showSuggestions && (
              <div className="w-80 flex-shrink-0 border-l bg-white overflow-y-auto hidden lg:block">
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-4">
                    <Sparkles className="h-4 w-4 text-purple-600" />
                    <h3 className="text-sm font-semibold text-gray-900">Suggested Queries</h3>
                  </div>
                  <div className="space-y-3">
                    {DEFAULT_SUGGESTIONS.map((s) => (
                      <button
                        key={s.id}
                        onClick={() => handleSuggestionClick(s.query)}
                        className="w-full text-left p-3 border border-gray-200 rounded-xl hover:border-blue-300 hover:bg-blue-50 transition-all group"
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-base">{s.icon}</span>
                          <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                            {s.category}
                          </span>
                        </div>
                        <p className="text-sm font-medium text-gray-800 group-hover:text-blue-700 leading-snug">
                          {s.query}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">{s.description}</p>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
