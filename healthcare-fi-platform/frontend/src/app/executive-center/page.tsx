'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import {
  executiveAPI,
  alertsAPI,
  decisionsAPI,
} from '@/lib/api/client';
import {
  Shield,
  AlertTriangle,
  Bell,
  Target,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Activity,
  DollarSign,
  BarChart3,
  Briefcase,
  Zap,
  ChevronRight,
  Plus,
  X,
  Send,
  Eye,
  EyeOff,
  Gauge,
} from 'lucide-react';
import { AskAIButton } from '@/components/ai/ask-ai-button';

interface KPI {
  id: string;
  name: string;
  value: number;
  target: number;
  status: 'healthy' | 'warning' | 'critical';
  trend: 'up' | 'down' | 'stable';
  trend_percentage: number;
  last_updated: string;
}

interface Alert {
  id: string;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'critical';
  category: string;
  is_read: boolean;
  created_at: string;
}

interface Decision {
  id: string;
  title: string;
  description: string;
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'approved' | 'rejected' | 'implemented';
  created_at: string;
}

interface RevenueForecast {
  period: string;
  forecasted: number;
  confidence_low: number;
  confidence_high: number;
  model: string;
  accuracy: number;
}

interface CostForecast {
  period: string;
  forecasted: number;
  breakdown: Record<string, number>;
  drivers: string[];
  recommendations: string[];
}

interface Risk {
  id: string;
  name: string;
  description: string;
  probability: number;
  impact: number;
  mitigation: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

interface RiskSummary {
  overall_score: number;
  risk_level: string;
  risks: Risk[];
}

interface Briefing {
  executive_summary: string;
  narrative: string;
  overall_health: string;
  financial_score: number;
  operational_score: number;
  strategic_score: number;
  key_actions: string[];
  risks: string[];
}

export default function ExecutiveCenterPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [kpis, setKpis] = useState<KPI[]>([]);
  const [kpisLoading, setKpisLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(true);

  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [decisionsLoading, setDecisionsLoading] = useState(true);

  const [revenueForecasts, setRevenueForecasts] = useState<RevenueForecast[]>([]);
  const [costForecasts, setCostForecasts] = useState<CostForecast[]>([]);
  const [forecastsLoading, setForecastsLoading] = useState(true);

  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [risksLoading, setRisksLoading] = useState(true);

  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [briefingLoading, setBriefingLoading] = useState(false);

  const [showDecisionForm, setShowDecisionForm] = useState(false);
  const [newDecision, setNewDecision] = useState({
    title: '',
    description: '',
    category: '',
    priority: 'medium' as const,
  });

  const fetchKPIs = useCallback(async () => {
    setKpisLoading(true);
    try {
      const res = await executiveAPI.getKPIs({ time_range: timeRange });
      setKpis(res.data.kpis || []);
    } catch (err) {
      console.error('Failed to fetch KPIs:', err);
    } finally {
      setKpisLoading(false);
    }
  }, [timeRange]);

  const fetchAlerts = useCallback(async () => {
    setAlertsLoading(true);
    try {
      const res = await executiveAPI.getAlerts({ limit: 20 });
      setAlerts(res.data.alerts || []);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setAlertsLoading(false);
    }
  }, []);

  const fetchDecisions = useCallback(async () => {
    setDecisionsLoading(true);
    try {
      const res = await executiveAPI.getDecisions({ status: 'pending' });
      setDecisions(res.data.decisions || []);
    } catch (err) {
      console.error('Failed to fetch decisions:', err);
    } finally {
      setDecisionsLoading(false);
    }
  }, []);

  const fetchForecasts = useCallback(async () => {
    setForecastsLoading(true);
    try {
      const [revRes, costRes] = await Promise.all([
        executiveAPI.getRevenueForecast({ periods_ahead: 6 }),
        executiveAPI.getCostForecast({ periods_ahead: 6 }),
      ]);
      setRevenueForecasts(revRes.data.forecasts || []);
      setCostForecasts(costRes.data.forecasts || []);
    } catch (err) {
      console.error('Failed to fetch forecasts:', err);
    } finally {
      setForecastsLoading(false);
    }
  }, []);

  const fetchRisks = useCallback(async () => {
    setRisksLoading(true);
    try {
      const res = await executiveAPI.getRisks();
      setRiskSummary(res.data);
    } catch (err) {
      console.error('Failed to fetch risks:', err);
    } finally {
      setRisksLoading(false);
    }
  }, []);

  useEffect(() => {
    async function loadAll() {
      setError(null);
      setLoading(true);
      try {
        await Promise.all([
          fetchKPIs(),
          fetchAlerts(),
          fetchDecisions(),
          fetchForecasts(),
          fetchRisks(),
        ]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }
    loadAll();
  }, [fetchKPIs, fetchAlerts, fetchDecisions, fetchForecasts, fetchRisks]);

  const handleMarkAlertRead = async (id: string) => {
    try {
      await executiveAPI.markAlertRead(id);
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, is_read: true } : a))
      );
    } catch (err) {
      console.error('Failed to mark alert read:', err);
    }
  };

  const handleDismissAlert = async (id: string) => {
    try {
      await executiveAPI.dismissAlert(id);
      setAlerts((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    }
  };

  const handleCreateDecision = async () => {
    if (!newDecision.title.trim()) return;
    try {
      await executiveAPI.createDecision(newDecision);
      setNewDecision({ title: '', description: '', category: '', priority: 'medium' });
      setShowDecisionForm(false);
      fetchDecisions();
    } catch (err) {
      console.error('Failed to create decision:', err);
    }
  };

  const handleGenerateBriefing = async () => {
    setBriefingLoading(true);
    try {
      const res = await executiveAPI.generateBriefing({
        period: timeRange,
        context: {},
      });
      setBriefing(res.data);
    } catch (err) {
      console.error('Failed to generate briefing:', err);
    } finally {
      setBriefingLoading(false);
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'warning':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const severityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'warning':
        return 'bg-amber-100 text-amber-800';
      case 'info':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const priorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const riskLevelColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'text-red-600';
      case 'high':
        return 'text-orange-600';
      case 'medium':
        return 'text-yellow-600';
      case 'low':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(val);

  const formatPercent = (val: number) => `${val.toFixed(1)}%`;

  const gaugeColor = (score: number) => {
    if (score >= 70) return '#10b981';
    if (score >= 40) return '#f59e0b';
    return '#ef4444';
  };

  const renderKPISkeletons = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-3">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-3 w-32" />
          </CardContent>
        </Card>
      ))}
    </div>
  );

  const renderAlertsSkeletons = () => (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Skeleton className="h-5 w-5 rounded" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-3 w-full" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  const renderForecastsSkeletons = () => (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-3 w-48" />
          </CardContent>
        </Card>
      ))}
    </div>
  );

  const renderRiskSkeletons = () => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center gap-6">
          <Skeleton className="h-32 w-32 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-48" />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Briefcase className="h-8 w-8 text-indigo-600" />
              Executive Command Center
            </h1>
            <p className="text-gray-500 mt-1">
              Real-time KPIs, alerts, forecasts, and risk intelligence
            </p>
          </div>
          <div className="flex items-center gap-3">
            <AskAIButton
              page="executive-center"
              metrics={['GROSS_REVENUE', 'NET_REVENUE', 'EBITDA', 'OCCUPANCY_RATE', 'CLAIM_DENIAL_RATE']}
              variant="outline"
              size="sm"
            />
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="p-2 border rounded-lg text-sm"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="1y">Last year</option>
            </select>
            <Button
              onClick={handleGenerateBriefing}
              disabled={briefingLoading}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              {briefingLoading ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <FileText className="h-4 w-4 mr-2" />
              )}
              Generate Briefing
            </Button>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
              Dismiss
            </button>
          </div>
        )}

        {/* Section 1: KPI Dashboard */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-600" />
              KPI Dashboard
            </h2>
            <Button variant="outline" size="sm" onClick={fetchKPIs}>
              <RefreshCw className="h-4 w-4 mr-1" /> Refresh
            </Button>
          </div>
          {kpisLoading ? (
            renderKPISkeletons()
          ) : kpis.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center text-gray-500">
                <BarChart3 className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                No KPI data available for this period
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {kpis.map((kpi) => (
                <Card key={kpi.id} className="hover:border-blue-300 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-500">{kpi.name}</span>
                      <Badge className={statusColor(kpi.status)}>
                        {kpi.status}
                      </Badge>
                    </div>
                    <div className="text-2xl font-bold">{kpi.value.toLocaleString()}</div>
                    <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                      <span>Target: {kpi.target.toLocaleString()}</span>
                      <span className={`flex items-center gap-1 ${kpi.trend === 'up' ? 'text-emerald-600' : kpi.trend === 'down' ? 'text-red-600' : 'text-gray-600'}`}>
                        {kpi.trend === 'up' ? <TrendingUp className="h-3 w-3" /> : kpi.trend === 'down' ? <TrendingDown className="h-3 w-3" /> : null}
                        {kpi.trend_percentage > 0 ? '+' : ''}{kpi.trend_percentage}%
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-2">
                      Updated: {new Date(kpi.last_updated).toLocaleDateString()}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>

        {/* Section 2: Alerts & Decisions */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Bell className="h-5 w-5 text-amber-600" />
              Alerts & Decisions
            </h2>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={fetchAlerts}>
                <RefreshCw className="h-4 w-4 mr-1" /> Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDecisionForm(!showDecisionForm)}
              >
                <Plus className="h-4 w-4 mr-1" /> New Decision
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Alerts */}
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Active Alerts</h3>
              {alertsLoading ? (
                renderAlertsSkeletons()
              ) : alerts.length === 0 ? (
                <Card>
                  <CardContent className="p-6 text-center text-gray-500">
                    <CheckCircle className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                    No active alerts
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {alerts.map((alert) => (
                    <Card key={alert.id} className={alert.is_read ? 'opacity-60' : ''}>
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5">
                            {alert.severity === 'critical' ? (
                              <XCircle className="h-5 w-5 text-red-500" />
                            ) : alert.severity === 'warning' ? (
                              <AlertTriangle className="h-5 w-5 text-amber-500" />
                            ) : (
                              <AlertCircle className="h-5 w-5 text-blue-500" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-sm">{alert.title}</span>
                              <Badge className={severityColor(alert.severity)}>
                                {alert.severity}
                              </Badge>
                              {alert.is_read && (
                                <EyeOff className="h-3 w-3 text-gray-400" />
                              )}
                            </div>
                            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{alert.message}</p>
                            <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                              <span>{alert.category}</span>
                              <span>{new Date(alert.created_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            {!alert.is_read && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleMarkAlertRead(alert.id)}
                                title="Mark as read"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDismissAlert(alert.id)}
                              title="Dismiss"
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            {/* Decisions */}
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Pending Decisions</h3>

              {showDecisionForm && (
                <Card className="mb-3">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Create Decision</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <Input
                      placeholder="Decision title"
                      value={newDecision.title}
                      onChange={(e) => setNewDecision((p) => ({ ...p, title: e.target.value }))}
                    />
                    <textarea
                      className="w-full h-20 p-2 border rounded text-sm"
                      placeholder="Description"
                      value={newDecision.description}
                      onChange={(e) => setNewDecision((p) => ({ ...p, description: e.target.value }))}
                    />
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label className="text-xs">Category</Label>
                        <Input
                          placeholder="e.g. budget, staffing"
                          value={newDecision.category}
                          onChange={(e) => setNewDecision((p) => ({ ...p, category: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label className="text-xs">Priority</Label>
                        <select
                          className="w-full p-2 border rounded text-sm"
                          value={newDecision.priority}
                          onChange={(e) => setNewDecision((p) => ({ ...p, priority: e.target.value as any }))}
                        >
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                          <option value="critical">Critical</option>
                        </select>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={handleCreateDecision} className="bg-indigo-600 hover:bg-indigo-700">
                        <Send className="h-3 w-3 mr-1" /> Create
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setShowDecisionForm(false)}>
                        Cancel
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {decisionsLoading ? (
                renderAlertsSkeletons()
              ) : decisions.length === 0 ? (
                <Card>
                  <CardContent className="p-6 text-center text-gray-500">
                    <CheckCircle className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                    No pending decisions
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {decisions.map((d) => (
                    <Card key={d.id}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-sm">{d.title}</span>
                              <Badge className={priorityColor(d.priority)}>{d.priority}</Badge>
                            </div>
                            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{d.description}</p>
                            <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                              <span>{d.category}</span>
                              <span className="capitalize">{d.status}</span>
                              <span>{new Date(d.created_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                          <Badge variant="outline" className="capitalize text-xs">
                            {d.status}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Section 3: Forecasts */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-emerald-600" />
              Forecasts
            </h2>
            <Button variant="outline" size="sm" onClick={fetchForecasts}>
              <RefreshCw className="h-4 w-4 mr-1" /> Refresh
            </Button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Revenue Forecast */}
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Revenue Forecast</h3>
              {forecastsLoading ? (
                renderForecastsSkeletons()
              ) : revenueForecasts.length === 0 ? (
                <Card>
                  <CardContent className="p-6 text-center text-gray-500">
                    <TrendingUp className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                    No revenue forecast data
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {revenueForecasts.map((f, i) => (
                    <Card key={i}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-500">{f.period}</span>
                          <Badge className="bg-emerald-100 text-emerald-800">
                            {(f.accuracy * 100).toFixed(0)}% accurate
                          </Badge>
                        </div>
                        <div className="text-xl font-bold">{formatCurrency(f.forecasted)}</div>
                        <div className="text-xs text-gray-500 mt-1">
                          Range: {formatCurrency(f.confidence_low)} - {formatCurrency(f.confidence_high)}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">Model: {f.model}</div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            {/* Cost Forecast */}
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Cost Forecast</h3>
              {forecastsLoading ? (
                renderForecastsSkeletons()
              ) : costForecasts.length === 0 ? (
                <Card>
                  <CardContent className="p-6 text-center text-gray-500">
                    <DollarSign className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                    No cost forecast data
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {costForecasts.map((f, i) => (
                    <Card key={i}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-500">{f.period}</span>
                          <Badge className="bg-orange-100 text-orange-800">
                            {f.drivers.length} drivers
                          </Badge>
                        </div>
                        <div className="text-xl font-bold">{formatCurrency(f.forecasted)}</div>
                        {Object.keys(f.breakdown).length > 0 && (
                          <div className="mt-2 space-y-1">
                            {Object.entries(f.breakdown).map(([key, val]) => (
                              <div key={key} className="flex justify-between text-xs">
                                <span className="text-gray-500">{key}</span>
                                <span>{formatCurrency(val)}</span>
                              </div>
                            ))}
                          </div>
                        )}
                        {f.recommendations.length > 0 && (
                          <div className="mt-2 text-xs text-gray-500">
                            <Zap className="h-3 w-3 inline mr-1" />
                            {f.recommendations[0]}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Section 4: Risk Summary */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Shield className="h-5 w-5 text-red-600" />
              Risk Summary
            </h2>
            <Button variant="outline" size="sm" onClick={fetchRisks}>
              <RefreshCw className="h-4 w-4 mr-1" /> Refresh
            </Button>
          </div>

          {risksLoading ? (
            renderRiskSkeletons()
          ) : !riskSummary ? (
            <Card>
              <CardContent className="p-8 text-center text-gray-500">
                <Shield className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                No risk data available
              </CardContent>
            </Card>
          ) : (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                {/* Risk Gauge */}
                <Card>
                  <CardContent className="p-6 flex flex-col items-center">
                    <div className="relative w-32 h-32">
                      <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                        <circle
                          cx="50" cy="50" r="40"
                          fill="none"
                          stroke="#e5e7eb"
                          strokeWidth="8"
                        />
                        <circle
                          cx="50" cy="50" r="40"
                          fill="none"
                          stroke={gaugeColor(riskSummary.overall_score)}
                          strokeWidth="8"
                          strokeDasharray={`${(riskSummary.overall_score / 100) * 251.2} 251.2`}
                          strokeLinecap="round"
                        />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-2xl font-bold">{riskSummary.overall_score}</span>
                        <span className="text-xs text-gray-500">/ 100</span>
                      </div>
                    </div>
                    <div className={`mt-3 text-sm font-semibold ${riskLevelColor(riskSummary.risk_level)}`}>
                      {riskSummary.risk_level?.toUpperCase()} RISK
                    </div>
                  </CardContent>
                </Card>

                {/* Risk List */}
                <Card className="lg:col-span-2">
                  <CardContent className="p-4">
                    <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Top Risks</h3>
                    {riskSummary.risks.length === 0 ? (
                      <p className="text-sm text-gray-500 text-center py-4">No risks identified</p>
                    ) : (
                      <div className="space-y-3">
                        {riskSummary.risks.map((risk) => (
                          <div key={risk.id} className="border rounded-lg p-3">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-sm">{risk.name}</span>
                              <Badge className={severityColor(risk.risk_level)}>{risk.risk_level}</Badge>
                            </div>
                            <p className="text-xs text-gray-500 mt-1">{risk.description}</p>
                            <div className="flex items-center gap-4 mt-2 text-xs">
                              <span className="text-gray-500">
                                Probability: <strong>{(risk.probability * 100).toFixed(0)}%</strong>
                              </span>
                              <span className="text-gray-500">
                                Impact: <strong>{(risk.impact * 100).toFixed(0)}%</strong>
                              </span>
                            </div>
                            {risk.mitigation && (
                              <div className="mt-2 text-xs text-gray-500 bg-gray-50 rounded p-2">
                                <Target className="h-3 w-3 inline mr-1" />
                                {risk.mitigation}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </section>

        {/* Briefing Display */}
        {briefing && (
          <section>
            <h2 className="text-xl font-semibold flex items-center gap-2 mb-4">
              <FileText className="h-5 w-5 text-indigo-600" />
              Executive Briefing
            </h2>
            <Card>
              <CardContent className="p-6 space-y-6">
                <div className="flex items-center gap-4">
                  <Badge className={`text-lg px-3 py-1 ${
                    briefing.overall_health === 'healthy' ? 'bg-emerald-100 text-emerald-800' :
                    briefing.overall_health === 'warning' ? 'bg-amber-100 text-amber-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {briefing.overall_health}
                  </Badge>
                  <div className="flex gap-4 text-sm">
                    <span>Financial: <strong>{briefing.financial_score}</strong></span>
                    <span>Operational: <strong>{briefing.operational_score}</strong></span>
                    <span>Strategic: <strong>{briefing.strategic_score}</strong></span>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Executive Summary</h3>
                  <p className="text-sm text-gray-700">{briefing.executive_summary}</p>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Narrative</h3>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{briefing.narrative}</p>
                </div>

                {briefing.key_actions.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Key Actions</h3>
                    <ul className="space-y-1">
                      {briefing.key_actions.map((action, i) => (
                        <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                          <ChevronRight className="h-4 w-4 text-indigo-500 mt-0.5 shrink-0" />
                          {action}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {briefing.risks.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Risks</h3>
                    <ul className="space-y-1">
                      {briefing.risks.map((risk, i) => (
                        <li key={i} className="text-sm text-red-700 flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                          {risk}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          </section>
        )}
      </div>
    </DashboardLayout>
  );
}
