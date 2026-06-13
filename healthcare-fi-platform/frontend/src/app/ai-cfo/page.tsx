'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Brain,
  FileText,
  LayoutDashboard,
  Bell,
  Send,
  RefreshCw,
  Plus,
  X,
  Check,
  AlertTriangle,
  Clock,
  ChevronDown,
  ChevronRight,
  Trash2,
  Eye,
  EyeOff,
} from 'lucide-react';
import { aiCfoAPI } from '@/lib/api/client';

interface QuestionAnswer {
  id: string;
  user_query: string;
  answer: string;
  confidence: number;
  evidence_chain: string[];
  reasoning_trace: string;
  created_at: string;
}

interface BriefingSection {
  title: string;
  content: string;
  metrics?: { label: string; value: string }[];
}

interface Briefing {
  id: string;
  mode: string;
  period: string;
  score: number;
  executive_summary: string;
  key_findings: string[];
  actions: string[];
  sections: BriefingSection[];
  created_at: string;
}

interface Widget {
  id: string;
  type: string;
  title: string;
  config: Record<string, any>;
}

interface Workspace {
  id: string;
  name: string;
  description?: string;
  widgets: Widget[];
  created_at: string;
}

interface Alert {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  read: boolean;
  dismissed: boolean;
  created_at: string;
}

const severityStyles: Record<string, string> = {
  low: 'bg-blue-100 text-blue-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
};

export default function AiCfoPage() {
  const [activeTab, setActiveTab] = useState('ask');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [answers, setAnswers] = useState<QuestionAnswer[]>([]);

  const [briefings, setBriefings] = useState<Briefing[]>([]);
  const [briefingMode, setBriefingMode] = useState('daily');
  const [briefingPeriod, setBriefingPeriod] = useState(new Date().toISOString().split('T')[0]);
  const [generatingBriefing, setGeneratingBriefing] = useState(false);

  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [newWorkspaceDesc, setNewWorkspaceDesc] = useState('');
  const [widgetType, setWidgetType] = useState('metric');
  const [widgetTitle, setWidgetTitle] = useState('');
  const [selectedWorkspace, setSelectedWorkspace] = useState<string | null>(null);

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (activeTab === 'alerts') loadAlerts();
  }, [activeTab, showUnreadOnly]);

  async function loadData() {
    setError(null);
    try {
      const [wsRes] = await Promise.all([
        aiCfoAPI.listWorkspaces(),
      ]);
      const wsData = await wsRes as any;
      setWorkspaces(wsData.workspaces || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }

  async function handleAskQuestion() {
    if (!question.trim() || asking) return;
    setAsking(true);
    try {
      const res = await aiCfoAPI.askQuestion({ user_query: question }) as any;
      setAnswers((prev) => [res, ...prev]);
      setQuestion('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get answer');
    } finally {
      setAsking(false);
    }
  }

  async function handleGenerateBriefing() {
    if (generatingBriefing) return;
    setGeneratingBriefing(true);
    try {
      const res = await aiCfoAPI.generateBriefing({
        mode: briefingMode,
        period: briefingPeriod,
      }) as any;
      setBriefings((prev) => [res, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate briefing');
    } finally {
      setGeneratingBriefing(false);
    }
  }

  async function handleCreateWorkspace() {
    if (!newWorkspaceName.trim()) return;
    try {
      const res = await aiCfoAPI.createWorkspace({
        name: newWorkspaceName,
        description: newWorkspaceDesc,
      }) as any;
      setWorkspaces((prev) => [...prev, res]);
      setNewWorkspaceName('');
      setNewWorkspaceDesc('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create workspace');
    }
  }

  async function handleAddWidget(workspaceId: string) {
    if (!widgetTitle.trim()) return;
    try {
      const res = await aiCfoAPI.addWidget(workspaceId, {
        type: widgetType,
        title: widgetTitle,
        config: {},
      }) as any;
      setWorkspaces((prev) =>
        prev.map((ws) =>
          ws.id === workspaceId ? { ...ws, widgets: [...ws.widgets, res] } : ws
        )
      );
      setWidgetTitle('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add widget');
    }
  }

  async function handleDeleteWorkspace(id: string) {
    try {
      await aiCfoAPI.deleteWorkspace(id);
      setWorkspaces((prev) => prev.filter((ws) => ws.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete workspace');
    }
  }

  async function loadAlerts() {
    setAlertsLoading(true);
    try {
      const res = await aiCfoAPI.getAlerts({ unread_only: showUnreadOnly }) as any;
      setAlerts(res.alerts || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alerts');
    } finally {
      setAlertsLoading(false);
    }
  }

  async function handleDismissAlert(id: string) {
    try {
      await aiCfoAPI.dismissAlert(id);
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, dismissed: true } : a)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to dismiss alert');
    }
  }

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleAskQuestion();
      }
    },
    [question, asking]
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Brain className="h-8 w-8 text-indigo-600" />
              AI CFO Core
            </h1>
            <p className="text-gray-500 mt-1">AI-powered financial intelligence and analysis</p>
          </div>
          <Badge className="bg-indigo-100 text-indigo-800 border-indigo-200 text-lg px-3 py-1">v1.0</Badge>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="ask">Ask CFO</TabsTrigger>
            <TabsTrigger value="briefings">Briefings</TabsTrigger>
            <TabsTrigger value="workspaces">Workspaces ({workspaces.length})</TabsTrigger>
            <TabsTrigger value="alerts">Alerts</TabsTrigger>
          </TabsList>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2 mt-3">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
              <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
                Dismiss
              </button>
            </div>
          )}

          <TabsContent value="ask" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Ask the CFO</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-3">
                  <Input
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask a financial question... (e.g., What is our current operating margin?)"
                    disabled={asking}
                  />
                  <Button onClick={handleAskQuestion} disabled={asking || !question.trim()} className="bg-indigo-600 hover:bg-indigo-700 shrink-0">
                    {asking ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
                    {asking ? 'Thinking...' : 'Ask'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {answers.length === 0 && !asking && (
              <Card>
                <CardContent className="p-8 text-center text-gray-500">
                  <Brain className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p className="font-medium">No questions asked yet</p>
                  <p className="text-sm mt-1">Ask a financial question to get started</p>
                </CardContent>
              </Card>
            )}

            {answers.map((qa) => (
              <Card key={qa.id}>
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 flex-1">
                      <p className="text-sm font-medium text-indigo-900">{qa.user_query}</p>
                    </div>
                    <Badge className={qa.confidence >= 0.8 ? 'bg-emerald-100 text-emerald-800' : qa.confidence >= 0.5 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}>
                      {Math.round(qa.confidence * 100)}% confidence
                    </Badge>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">
                      {typeof qa.answer === 'string' ? qa.answer : (qa.answer as any)?.summary || JSON.stringify(qa.answer, null, 2)}
                    </p>
                  </div>
                  {qa.evidence_chain && qa.evidence_chain.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Evidence Chain</p>
                      <div className="flex flex-wrap gap-2">
                        {qa.evidence_chain.map((evidence, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {evidence}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {qa.reasoning_trace && (
                    <details className="group">
                      <summary className="text-xs font-semibold text-gray-500 uppercase cursor-pointer hover:text-gray-700 flex items-center gap-1">
                        <ChevronRight className="h-3 w-3 transition-transform group-open:rotate-90" />
                        Reasoning Trace
                      </summary>
                      <p className="text-xs text-gray-600 mt-2 pl-4 whitespace-pre-wrap">{qa.reasoning_trace}</p>
                    </details>
                  )}
                  <div className="text-xs text-gray-400 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(qa.created_at).toLocaleString()}
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="briefings" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Generate Briefing</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Mode</Label>
                    <select
                      value={briefingMode}
                      onChange={(e) => setBriefingMode(e.target.value)}
                      className="w-full p-2 border rounded-lg text-sm"
                    >
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label>Period</Label>
                    <Input
                      type="date"
                      value={briefingPeriod}
                      onChange={(e) => setBriefingPeriod(e.target.value)}
                    />
                  </div>
                  <div className="flex items-end">
                    <Button onClick={handleGenerateBriefing} disabled={generatingBriefing} className="bg-indigo-600 hover:bg-indigo-700">
                      {generatingBriefing ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <FileText className="h-4 w-4 mr-2" />}
                      {generatingBriefing ? 'Generating...' : 'Generate'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {briefings.length === 0 && !generatingBriefing && (
              <Card>
                <CardContent className="p-8 text-center text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p className="font-medium">No briefings generated</p>
                  <p className="text-sm mt-1">Generate a briefing to get a financial summary</p>
                </CardContent>
              </Card>
            )}

            {briefings.map((briefing) => (
              <Card key={briefing.id}>
                <CardContent className="p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge className="bg-indigo-100 text-indigo-800">{briefing.mode}</Badge>
                      <span className="text-sm text-gray-500">{briefing.period}</span>
                    </div>
                    <Badge className={briefing.score >= 80 ? 'bg-emerald-100 text-emerald-800' : briefing.score >= 60 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}>
                      Score: {briefing.score}
                    </Badge>
                  </div>

                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Executive Summary</p>
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">{briefing.executive_summary}</p>
                  </div>

                  {briefing.key_findings.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Key Findings</p>
                      <ul className="space-y-1">
                        {briefing.key_findings.map((finding, i) => (
                          <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                            <Check className="h-4 w-4 text-emerald-500 mt-0.5 shrink-0" />
                            {finding}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {briefing.actions.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Recommended Actions</p>
                      <ul className="space-y-1">
                        {briefing.actions.map((action, i) => (
                          <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                            <span className="text-indigo-500 font-bold shrink-0">{i + 1}.</span>
                            {action}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {briefing.sections && briefing.sections.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Sections</p>
                      <div className="space-y-3">
                        {briefing.sections.map((section, i) => (
                          <div key={i} className="border border-gray-200 rounded-lg p-3">
                            <p className="font-medium text-sm text-gray-800">{section.title}</p>
                            <p className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">{section.content}</p>
                            {section.metrics && section.metrics.length > 0 && (
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2">
                                {section.metrics.map((metric, j) => (
                                  <div key={j} className="bg-gray-50 rounded p-2">
                                    <p className="text-xs text-gray-500">{metric.label}</p>
                                    <p className="text-sm font-semibold text-gray-800">{metric.value}</p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-gray-400 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(briefing.created_at).toLocaleString()}
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="workspaces" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Create Workspace</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Name</Label>
                    <Input
                      value={newWorkspaceName}
                      onChange={(e) => setNewWorkspaceName(e.target.value)}
                      placeholder="Q4 Financial Dashboard"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Input
                      value={newWorkspaceDesc}
                      onChange={(e) => setNewWorkspaceDesc(e.target.value)}
                      placeholder="Key metrics for Q4"
                    />
                  </div>
                </div>
                <Button onClick={handleCreateWorkspace} className="bg-indigo-600 hover:bg-indigo-700">
                  <Plus className="h-4 w-4 mr-2" /> Create Workspace
                </Button>
              </CardContent>
            </Card>

            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-48" />
                ))}
              </div>
            ) : workspaces.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center text-gray-500">
                  <LayoutDashboard className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p className="font-medium">No workspaces created</p>
                  <p className="text-sm mt-1">Create a workspace to organize your financial widgets</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {workspaces.map((ws) => (
                  <Card key={ws.id} className={selectedWorkspace === ws.id ? 'border-indigo-300' : ''}>
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-gray-800">{ws.name}</h3>
                          {ws.description && <p className="text-sm text-gray-500 mt-1">{ws.description}</p>}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteWorkspace(ws.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>

                      <div className="space-y-2">
                        {ws.widgets.length === 0 ? (
                          <p className="text-xs text-gray-400 text-center py-2">No widgets yet</p>
                        ) : (
                          ws.widgets.map((widget) => (
                            <div key={widget.id} className="bg-gray-50 border border-gray-200 rounded-lg p-2 flex items-center justify-between">
                              <div>
                                <span className="text-xs font-medium text-gray-700">{widget.title}</span>
                                <Badge variant="outline" className="ml-2 text-xs">{widget.type}</Badge>
                              </div>
                            </div>
                          ))
                        )}
                      </div>

                      <div className="border-t pt-3 space-y-2">
                        <p className="text-xs font-semibold text-gray-500 uppercase">Add Widget</p>
                        <div className="flex gap-2">
                          <select
                            value={widgetType}
                            onChange={(e) => setWidgetType(e.target.value)}
                            className="p-1.5 border rounded text-sm"
                          >
                            <option value="metric">Metric</option>
                            <option value="chart">Chart</option>
                            <option value="table">Table</option>
                            <option value="text">Text</option>
                          </select>
                          <Input
                            value={widgetTitle}
                            onChange={(e) => setWidgetTitle(e.target.value)}
                            placeholder="Widget title"
                            className="flex-1"
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleAddWidget(ws.id);
                            }}
                          />
                          <Button
                            onClick={() => handleAddWidget(ws.id)}
                            disabled={!widgetTitle.trim()}
                            size="sm"
                            className="bg-indigo-600 hover:bg-indigo-700"
                          >
                            <Plus className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="alerts" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Alerts</CardTitle>
                <div className="flex items-center gap-2">
                  <Button
                    variant={showUnreadOnly ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setShowUnreadOnly(!showUnreadOnly)}
                  >
                    {showUnreadOnly ? <EyeOff className="h-4 w-4 mr-1" /> : <Eye className="h-4 w-4 mr-1" />}
                    {showUnreadOnly ? 'Show All' : 'Unread Only'}
                  </Button>
                  <Button variant="outline" size="sm" onClick={loadAlerts}>
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {alertsLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} className="h-20" />
                    ))}
                  </div>
                ) : alerts.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Bell className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                    <p className="font-medium">No alerts</p>
                    <p className="text-sm mt-1">
                      {showUnreadOnly ? 'All alerts have been read' : 'No alerts to display'}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {alerts.map((alert) => (
                      <div
                        key={alert.id}
                        className={`border rounded-lg p-3 flex items-start gap-3 transition-opacity ${
                          alert.dismissed ? 'opacity-40' : alert.read ? 'bg-gray-50' : 'bg-white'
                        }`}
                      >
                        <div className={`shrink-0 w-2 h-2 rounded-full mt-2 ${
                          alert.severity === 'critical' ? 'bg-red-500' :
                          alert.severity === 'high' ? 'bg-orange-500' :
                          alert.severity === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className={`text-sm font-medium ${alert.read ? 'text-gray-600' : 'text-gray-900'}`}>
                              {alert.title}
                            </p>
                            <Badge className={severityStyles[alert.severity] || 'bg-gray-100 text-gray-800'}>
                              {alert.severity}
                            </Badge>
                            {!alert.read && (
                              <Badge className="bg-indigo-100 text-indigo-800">New</Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                          <p className="text-xs text-gray-400 mt-2 flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {new Date(alert.created_at).toLocaleString()}
                          </p>
                        </div>
                        <div className="shrink-0 flex gap-1">
                          {!alert.dismissed && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDismissAlert(alert.id)}
                              className="text-gray-400 hover:text-red-600"
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
