'use client';

import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  TrendingUp,
  Brain,
  Trophy,
  Activity,
  Plus,
  ArrowUp,
  ArrowDown,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import { forecastingAPI } from '@/lib/api/client';
import { ForecastChart } from '@/components/charts/ForecastChart';

interface ForecastModel {
  id: string;
  name: string;
  model_type: string;
  status: string;
  parameters: Record<string, any>;
  hyperparameters: Record<string, any>;
  created_at: string;
}

interface ForecastResult {
  dates: string[];
  actual: (number | null)[];
  forecast: number[];
  lower_bound: number[];
  upper_bound: number[];
  metrics?: {
    mape?: number;
    rmse?: number;
    mae?: number;
    r2?: number;
  };
}

interface CompareResult {
  winner: string;
  confidence: number;
  recommendation: string;
  models: { id: string; name: string; metrics: Record<string, number> }[];
}

interface DriftAlert {
  severity: string;
  drift_type: string;
  detected_at: string;
  description: string;
  p_value?: number;
}

const MODEL_TYPES = [
  { value: 'prophet', label: 'Prophet' },
  { value: 'arima', label: 'ARIMA' },
  { value: 'exponential_smoothing', label: 'Exponential Smoothing' },
  { value: 'linear_regression', label: 'Linear Regression' },
  { value: 'ensemble', label: 'Ensemble' },
  { value: 'xgboost', label: 'XGBoost' },
];

const STATUS_COLORS: Record<string, string> = {
  champion: 'bg-amber-100 text-amber-800 border-amber-200',
  production: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  shadow: 'bg-blue-100 text-blue-800 border-blue-200',
  candidate: 'bg-purple-100 text-purple-800 border-purple-200',
  archived: 'bg-gray-100 text-gray-600 border-gray-200',
};

function ModelStatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
        STATUS_COLORS[status] || 'bg-gray-100 text-gray-600 border-gray-200'
      }`}
    >
      {status === 'champion' && <Trophy className="h-3 w-3 mr-1" />}
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function MetricCard({ label, value, decimals = 2 }: { label: string; value: number; decimals?: number }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 text-center">
      <div className="text-xs text-gray-500 uppercase tracking-wide">{label}</div>
      <div className="text-lg font-bold text-gray-900 mt-1">
        {value != null ? value.toFixed(decimals) : '—'}
      </div>
    </div>
  );
}

function LoadingSkeletons({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }, (_, i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-3">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-48" />
            <div className="flex gap-2 pt-2">
              <Skeleton className="h-8 w-20" />
              <Skeleton className="h-8 w-20" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function EmptyState({ icon: Icon, title, description }: { icon: any; title: string; description: string }) {
  return (
    <Card>
      <CardContent className="p-12 text-center">
        <Icon className="h-12 w-12 text-gray-300 mx-auto" />
        <h3 className="mt-4 text-lg font-medium text-gray-900">{title}</h3>
        <p className="mt-2 text-sm text-gray-500">{description}</p>
      </CardContent>
    </Card>
  );
}

export default function ForecastingPage() {
  const [activeTab, setActiveTab] = useState('models');
  const [models, setModels] = useState<ForecastModel[]>([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create model form
  const [modelName, setModelName] = useState('');
  const [modelType, setModelType] = useState('prophet');
  const [parameters, setParameters] = useState('{}');
  const [hyperparameters, setHyperparameters] = useState('{}');
  const [creating, setCreating] = useState(false);

  // Forecast state
  const [forecastModelId, setForecastModelId] = useState('');
  const [metricId, setMetricId] = useState('');
  const [metricName, setMetricName] = useState('');
  const [periods, setPeriods] = useState('12');
  const [confidenceLevel, setConfidenceLevel] = useState('0.95');
  const [forecastResult, setForecastResult] = useState<ForecastResult | null>(null);
  const [forecasting, setForecasting] = useState(false);

  // Compare state
  const [compareModelIds, setCompareModelIds] = useState<string[]>([]);
  const [compareResult, setCompareResult] = useState<CompareResult | null>(null);
  const [comparing, setComparing] = useState(false);

  // Drift state
  const [driftModelId, setDriftModelId] = useState('');
  const [recentData, setRecentData] = useState('[]');
  const [referenceData, setReferenceData] = useState('[]');
  const [driftAlerts, setDriftAlerts] = useState<DriftAlert[]>([]);
  const [detectingDrift, setDetectingDrift] = useState(false);

  useEffect(() => {
    loadModels();
  }, []);

  async function loadModels() {
    setLoadingModels(true);
    setError(null);
    try {
      const res = await forecastingAPI.listModels();
      setModels(res.data?.models || res.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load models');
    } finally {
      setLoadingModels(false);
    }
  }

  async function handleCreateModel() {
    if (!modelName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const params = parameters.trim() ? JSON.parse(parameters) : {};
      const hypers = hyperparameters.trim() ? JSON.parse(hyperparameters) : {};
      await forecastingAPI.createModel({
        name: modelName,
        model_type: modelType,
        parameters: params,
        hyperparameters: hypers,
      });
      setModelName('');
      setParameters('{}');
      setHyperparameters('{}');
      await loadModels();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create model');
    } finally {
      setCreating(false);
    }
  }

  async function handlePromote(id: string) {
    try {
      await forecastingAPI.promoteModel(id);
      await loadModels();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to promote model');
    }
  }

  async function handleDemote(id: string) {
    try {
      await forecastingAPI.demoteModel(id);
      await loadModels();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to demote model');
    }
  }

  async function handleGenerateForecast() {
    if (!forecastModelId) return;
    setForecasting(true);
    setError(null);
    try {
      const res = await forecastingAPI.generateForecast(forecastModelId, {
        metric_id: metricId,
        metric_name: metricName,
        periods: parseInt(periods),
        confidence_level: parseFloat(confidenceLevel),
      });
      setForecastResult(res.data || res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate forecast');
    } finally {
      setForecasting(false);
    }
  }

  async function handleCompare() {
    if (compareModelIds.length < 2) return;
    setComparing(true);
    setError(null);
    try {
      const res = await forecastingAPI.compareModels({ model_ids: compareModelIds });
      setCompareResult(res.data || res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare models');
    } finally {
      setComparing(false);
    }
  }

  async function handleDetectDrift() {
    if (!driftModelId) return;
    setDetectingDrift(true);
    setError(null);
    try {
      const recent = JSON.parse(recentData);
      const reference = JSON.parse(referenceData);
      const res = await forecastingAPI.detectDrift(driftModelId, {
        recent_data: recent,
        reference_data: reference,
      });
      setDriftAlerts(res.data?.alerts || res.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to detect drift');
    } finally {
      setDetectingDrift(false);
    }
  }

  function toggleCompareModel(id: string) {
    setCompareModelIds((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <TrendingUp className="h-8 w-8 text-blue-600" />
              Enterprise Forecasting
            </h1>
            <p className="text-gray-500 mt-1">Create, train, and compare forecast models with champion/challenger testing</p>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">Dismiss</button>
          </div>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="models">Models ({models.length})</TabsTrigger>
            <TabsTrigger value="forecast">Forecast</TabsTrigger>
            <TabsTrigger value="compare">Champion / Challenger</TabsTrigger>
            <TabsTrigger value="drift">Drift Detection</TabsTrigger>
          </TabsList>

          {/* MODELS TAB */}
          <TabsContent value="models" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Create Forecast Model</CardTitle>
                <CardDescription>Define a new forecast model configuration</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Model Name</Label>
                    <Input
                      value={modelName}
                      onChange={(e) => setModelName(e.target.value)}
                      placeholder="Revenue Prophet v1"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Model Type</Label>
                    <Select value={modelType} onValueChange={(v) => v && setModelType(v)}>
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {MODEL_TYPES.map((t) => (
                          <SelectItem key={t.value} value={t.value}>
                            {t.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Parameters (JSON)</Label>
                    <textarea
                      className="w-full h-20 p-3 font-mono text-sm border rounded-lg bg-gray-950 text-green-400"
                      value={parameters}
                      onChange={(e) => setParameters(e.target.value)}
                      placeholder='{"seasonality_mode": "multiplicative"}'
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Hyperparameters (JSON)</Label>
                    <textarea
                      className="w-full h-20 p-3 font-mono text-sm border rounded-lg bg-gray-950 text-green-400"
                      value={hyperparameters}
                      onChange={(e) => setHyperparameters(e.target.value)}
                      placeholder='{"changepoint_prior_scale": 0.05}'
                    />
                  </div>
                </div>
                <Button onClick={handleCreateModel} disabled={creating} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="h-4 w-4 mr-2" />
                  {creating ? 'Creating...' : 'Create Model'}
                </Button>
              </CardContent>
            </Card>

            {loadingModels ? (
              <LoadingSkeletons />
            ) : models.length === 0 ? (
              <EmptyState
                icon={Brain}
                title="No models yet"
                description="Create your first forecast model to get started."
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {models.map((model) => (
                  <Card key={model.id} className="hover:border-blue-300 transition-colors">
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-start justify-between">
                        <h3 className="font-semibold text-gray-900">{model.name}</h3>
                        <ModelStatusBadge status={model.status} />
                      </div>
                      <div className="text-sm text-gray-500">
                        <span className="font-mono bg-gray-100 px-1.5 py-0.5 rounded text-xs">
                          {model.model_type}
                        </span>
                      </div>
                      <div className="text-xs text-gray-400">
                        Created {new Date(model.created_at).toLocaleDateString()}
                      </div>
                      <div className="flex gap-2 pt-1">
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-xs"
                          onClick={() => handlePromote(model.id)}
                          disabled={model.status === 'champion'}
                        >
                          <ArrowUp className="h-3 w-3 mr-1" />
                          Promote
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-xs"
                          onClick={() => handleDemote(model.id)}
                          disabled={model.status === 'archived'}
                        >
                          <ArrowDown className="h-3 w-3 mr-1" />
                          Demote
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* FORECAST TAB */}
          <TabsContent value="forecast" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Generate Forecast</CardTitle>
                <CardDescription>Select a model and configure forecast parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <Label>Model</Label>
                    <Select value={forecastModelId} onValueChange={(v) => setForecastModelId(v || '')}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select model" />
                      </SelectTrigger>
                      <SelectContent>
                        {models.map((m) => (
                          <SelectItem key={m.id} value={m.id}>
                            {m.name} ({m.model_type})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Metric ID</Label>
                    <Input value={metricId} onChange={(e) => setMetricId(e.target.value)} placeholder="revenue_total" />
                  </div>
                  <div className="space-y-2">
                    <Label>Metric Name</Label>
                    <Input value={metricName} onChange={(e) => setMetricName(e.target.value)} placeholder="Total Revenue" />
                  </div>
                  <div className="space-y-2">
                    <Label>Periods (1-36)</Label>
                    <Input
                      type="number"
                      min={1}
                      max={36}
                      value={periods}
                      onChange={(e) => setPeriods(e.target.value)}
                    />
                  </div>
                </div>
                <div className="flex items-end gap-4">
                  <div className="space-y-2 w-40">
                    <Label>Confidence Level</Label>
                    <Select value={confidenceLevel} onValueChange={(v) => v && setConfidenceLevel(v)}>
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0.80">80%</SelectItem>
                        <SelectItem value="0.90">90%</SelectItem>
                        <SelectItem value="0.95">95%</SelectItem>
                        <SelectItem value="0.99">99%</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    onClick={handleGenerateForecast}
                    disabled={forecasting || !forecastModelId}
                    className="bg-emerald-600 hover:bg-emerald-700"
                  >
                    {forecasting ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <TrendingUp className="h-4 w-4 mr-2" />
                    )}
                    {forecasting ? 'Forecasting...' : 'Generate Forecast'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {forecastResult && (
              <div className="space-y-4">
                {forecastResult.metrics && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <MetricCard label="MAPE" value={forecastResult.metrics.mape ?? 0} decimals={2} />
                    <MetricCard label="RMSE" value={forecastResult.metrics.rmse ?? 0} decimals={4} />
                    <MetricCard label="MAE" value={forecastResult.metrics.mae ?? 0} decimals={4} />
                    <MetricCard label="R²" value={forecastResult.metrics.r2 ?? 0} decimals={4} />
                  </div>
                )}

                {/* Forecast Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-blue-400" />
                      Forecast Visualization
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ForecastChart
                      data={forecastResult.dates.map((date, i) => ({
                        date,
                        actual: forecastResult.actual[i] ?? undefined,
                        predicted: forecastResult.forecast[i],
                        lower: forecastResult.lower_bound[i],
                        upper: forecastResult.upper_bound[i],
                      }))}
                      height={340}
                      color="#6366f1"
                    />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Forecast Results Table</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b text-left text-gray-500">
                            <th className="pb-2 font-medium">Date</th>
                            <th className="pb-2 font-medium">Actual</th>
                            <th className="pb-2 font-medium">Forecast</th>
                            <th className="pb-2 font-medium">Lower Bound</th>
                            <th className="pb-2 font-medium">Upper Bound</th>
                          </tr>
                        </thead>
                        <tbody>
                          {forecastResult.dates.map((date, i) => (
                            <tr key={i} className="border-b border-gray-100 last:border-0">
                              <td className="py-2 font-mono text-xs">{date}</td>
                              <td className="py-2 font-semibold">
                                {forecastResult.actual[i] != null ? forecastResult.actual[i]?.toLocaleString() : '—'}
                              </td>
                              <td className="py-2 text-blue-600 font-semibold">
                                {forecastResult.forecast[i]?.toLocaleString()}
                              </td>
                              <td className="py-2 text-gray-500">
                                {forecastResult.lower_bound[i]?.toLocaleString()}
                              </td>
                              <td className="py-2 text-gray-500">
                                {forecastResult.upper_bound[i]?.toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* CHAMPION / CHALLENGER TAB */}
          <TabsContent value="compare" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Champion / Challenger Comparison</CardTitle>
                <CardDescription>Select 2 or more models to compare their performance</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {loadingModels ? (
                  <Skeleton className="h-24" />
                ) : (
                  <div className="space-y-2">
                    <Label>Select Models (min 2)</Label>
                    <div className="flex flex-wrap gap-2">
                      {models.map((m) => (
                        <button
                          key={m.id}
                          onClick={() => toggleCompareModel(m.id)}
                          className={`px-3 py-1.5 rounded-lg border text-sm font-medium transition-colors ${
                            compareModelIds.includes(m.id)
                              ? 'bg-blue-600 text-white border-blue-600'
                              : 'bg-white text-gray-700 border-gray-200 hover:border-blue-300'
                          }`}
                        >
                          {m.name}
                          <span className="ml-1.5 text-xs opacity-70">({m.model_type})</span>
                        </button>
                      ))}
                    </div>
                    {compareModelIds.length > 0 && compareModelIds.length < 2 && (
                      <p className="text-sm text-amber-600 flex items-center gap-1">
                        <AlertTriangle className="h-3 w-3" />
                        Select at least 2 models to compare
                      </p>
                    )}
                  </div>
                )}
                <Button
                  onClick={handleCompare}
                  disabled={comparing || compareModelIds.length < 2}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {comparing ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Activity className="h-4 w-4 mr-2" />
                  )}
                  {comparing ? 'Comparing...' : 'Run Comparison'}
                </Button>
              </CardContent>
            </Card>

            {compareResult && (
              <div className="space-y-4">
                <Card>
                  <CardContent className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
                      <div>
                        <div className="text-sm text-gray-500 uppercase tracking-wide">Winner</div>
                        <div className="text-2xl font-bold text-emerald-600 mt-1">{compareResult.winner}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500 uppercase tracking-wide">Confidence</div>
                        <div className="text-2xl font-bold text-blue-600 mt-1">
                          {(compareResult.confidence * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500 uppercase tracking-wide">Recommendation</div>
                        <div className="text-sm font-medium text-gray-700 mt-2">{compareResult.recommendation}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Model Metrics Comparison</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b text-left text-gray-500">
                            <th className="pb-2 font-medium">Model</th>
                            <th className="pb-2 font-medium">Type</th>
                            {compareResult.models[0] &&
                              Object.keys(compareResult.models[0].metrics).map((key) => (
                                <th key={key} className="pb-2 font-medium text-right">
                                  {key.toUpperCase()}
                                </th>
                              ))}
                          </tr>
                        </thead>
                        <tbody>
                          {compareResult.models.map((m) => (
                            <tr key={m.id} className="border-b border-gray-100 last:border-0">
                              <td className="py-2 font-semibold">{m.name}</td>
                              <td className="py-2 font-mono text-xs text-gray-500">{m.id}</td>
                              {Object.values(m.metrics).map((val, i) => (
                                <td key={i} className="py-2 text-right font-mono">
                                  {typeof val === 'number' ? val.toFixed(4) : val}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* DRIFT DETECTION TAB */}
          <TabsContent value="drift" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Concept Drift Detection</CardTitle>
                <CardDescription>Compare recent data against reference data to detect model drift</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Model</Label>
                    <Select value={driftModelId} onValueChange={(v) => setDriftModelId(v || '')}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select model" />
                      </SelectTrigger>
                      <SelectContent>
                        {models.map((m) => (
                          <SelectItem key={m.id} value={m.id}>
                            {m.name} ({m.model_type})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Reference Data (JSON array of values)</Label>
                    <textarea
                      className="w-full h-24 p-3 font-mono text-sm border rounded-lg bg-gray-950 text-green-400"
                      value={referenceData}
                      onChange={(e) => setReferenceData(e.target.value)}
                      placeholder="[100, 105, 102, 108, 110]"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Recent Data (JSON array of values)</Label>
                    <textarea
                      className="w-full h-24 p-3 font-mono text-sm border rounded-lg bg-gray-950 text-green-400"
                      value={recentData}
                      onChange={(e) => setRecentData(e.target.value)}
                      placeholder="[130, 135, 140, 142, 138]"
                    />
                  </div>
                </div>
                <Button
                  onClick={handleDetectDrift}
                  disabled={detectingDrift || !driftModelId}
                  className="bg-amber-600 hover:bg-amber-700"
                >
                  {detectingDrift ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Activity className="h-4 w-4 mr-2" />
                  )}
                  {detectingDrift ? 'Detecting...' : 'Detect Drift'}
                </Button>
              </CardContent>
            </Card>

            {driftAlerts.length > 0 && (
              <div className="space-y-3">
                {driftAlerts.map((alert, i) => (
                  <Card
                    key={i}
                    className={
                      alert.severity === 'critical'
                        ? 'border-red-300 bg-red-50'
                        : alert.severity === 'warning'
                          ? 'border-amber-300 bg-amber-50'
                          : 'border-blue-300 bg-blue-50'
                    }
                  >
                    <CardContent className="p-4 flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Badge
                            className={
                              alert.severity === 'critical'
                                ? 'bg-red-100 text-red-800 border-red-200'
                                : alert.severity === 'warning'
                                  ? 'bg-amber-100 text-amber-800 border-amber-200'
                                  : 'bg-blue-100 text-blue-800 border-blue-200'
                            }
                          >
                            {alert.severity}
                          </Badge>
                          <span className="text-sm font-semibold text-gray-900">{alert.drift_type}</span>
                        </div>
                        <p className="text-sm text-gray-600">{alert.description}</p>
                        {alert.p_value != null && (
                          <p className="text-xs text-gray-500">p-value: {alert.p_value.toFixed(4)}</p>
                        )}
                      </div>
                      <span className="text-xs text-gray-400 whitespace-nowrap ml-4">
                        {new Date(alert.detected_at).toLocaleString()}
                      </span>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {driftAlerts.length === 0 && !detectingDrift && (
              <EmptyState
                icon={Activity}
                title="No drift alerts"
                description="Submit reference and recent data to check for concept drift."
              />
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
