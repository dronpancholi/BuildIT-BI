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
import { strategicAPI } from '@/lib/api/client';
import {
  Target, BarChart3, Shuffle, ShieldAlert, Play, Plus, Trash2,
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle, X, Loader2, GitCompareArrows,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

// --- Types ---
interface Scenario {
  id: string;
  name: string;
  description?: string;
  type: 'base' | 'best_case' | 'worst_case' | 'stress_test' | 'custom';
  status: 'draft' | 'completed' | 'running' | 'failed';
  assumptions: Record<string, number>;
}

interface MonteCarloResult {
  mean: number;
  median: number;
  std_dev: number;
  var_95: number;
  var_99: number;
  histogram_bins: { bin_start: number; bin_end: number; count: number }[];
  percentiles?: Record<string, number>;
}

interface WhatIfResult {
  base_values: Record<string, number>;
  new_values: Record<string, number>;
  delta: Record<string, number>;
  percentage_change: Record<string, number>;
  driver_breakdown: { variable: string; contribution: number; pct_contribution: number }[];
}

interface RiskItem {
  id: string;
  name: string;
  probability: number;
  impact: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  mitigation: string;
}

// --- Helpers ---
const typeBadgeClass = (t: string) => {
  switch (t) {
    case 'best_case': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    case 'worst_case': return 'bg-red-100 text-red-800 border-red-200';
    case 'stress_test': return 'bg-amber-100 text-amber-800 border-amber-200';
    case 'base': return 'bg-blue-100 text-blue-800 border-blue-200';
    default: return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const statusBadgeClass = (s: string) => {
  switch (s) {
    case 'completed': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    case 'running': return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'failed': return 'bg-red-100 text-red-800 border-red-200';
    default: return 'bg-gray-100 text-gray-600 border-gray-200';
  }
};

const severityColor = (s: string) => {
  switch (s) {
    case 'critical': return 'bg-red-100 text-red-800 border-red-200';
    case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'medium': return 'bg-amber-100 text-amber-800 border-amber-200';
    default: return 'bg-green-100 text-green-800 border-green-200';
  }
};

const fmt = (n: number | undefined | null) =>
  n != null ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—';

// --- Sub-components ---
function SkeletonCard() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-5 w-2/5" />
      <Skeleton className="h-3 w-4/5" />
      <Skeleton className="h-3 w-3/5" />
      <div className="flex gap-2 pt-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
    </div>
  );
}

function EmptyState({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description: string }) {
  return (
    <Card>
      <CardContent className="p-12 text-center">
        <Icon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-gray-700">{title}</h3>
        <p className="text-sm text-gray-500 mt-1 max-w-md mx-auto">{description}</p>
      </CardContent>
    </Card>
  );
}

function Histogram({ bins }: { bins: { bin_start: number; bin_end: number; count: number }[] }) {
  if (!bins.length) return null;
  const maxCount = Math.max(...bins.map((b) => b.count));
  return (
    <div className="flex items-end gap-0.5 h-32 mt-2">
      {bins.map((b, i) => (
        <div key={i} className="flex-1 flex flex-col items-center justify-end">
          <div
            className="w-full bg-violet-500 rounded-t-sm"
            style={{ height: `${(b.count / maxCount) * 100}%` }}
            title={`${b.bin_start.toFixed(1)}–${b.bin_end.toFixed(1)}: ${b.count}`}
          />
        </div>
      ))}
    </div>
  );
}

// --- Page ---
export default function StrategicPage() {
  const [activeTab, setActiveTab] = useState('scenarios');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // --- Scenarios state ---
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [scName, setScName] = useState('');
  const [scDesc, setScDesc] = useState('');
  const [scType, setScType] = useState<Scenario['type']>('base');
  const [scAssumptions, setScAssumptions] = useState<{ key: string; value: string }[]>([{ key: '', value: '' }]);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);

  // --- Monte Carlo state ---
  const [mcScenarioId, setMcScenarioId] = useState('');
  const [mcSimCount, setMcSimCount] = useState(1000);
  const [mcResult, setMcResult] = useState<MonteCarloResult | null>(null);
  const [mcLoading, setMcLoading] = useState(false);

  // --- What-If state ---
  const [wiBaseValues, setWiBaseValues] = useState<{ key: string; value: string }[]>([
    { key: 'revenue', value: '1000000' },
  ]);
  const [wiChanges, setWiChanges] = useState<{ variable: string; base_value: string; new_value: string }[]>([
    { variable: 'revenue', base_value: '1000000', new_value: '1200000' },
  ]);
  const [wiResult, setWiResult] = useState<WhatIfResult | null>(null);
  const [wiLoading, setWiLoading] = useState(false);

  // --- Risk state ---
  const [riskScenarioId, setRiskScenarioId] = useState('');
  const [risks, setRisks] = useState<RiskItem[]>([]);
  const [riskLoading, setRiskLoading] = useState(false);

  // --- Comparison state ---
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [comparisonDialogOpen, setComparisonDialogOpen] = useState(false);

  // --- Load data ---
  useEffect(() => {
    loadScenarios();
  }, []);

  async function loadScenarios() {
    setLoading(true);
    setError(null);
    try {
      const res = await strategicAPI.listScenarios();
      setScenarios(res.data?.scenarios || res.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scenarios');
    } finally {
      setLoading(false);
    }
  }

  // --- Scenario CRUD ---
  async function handleCreateScenario() {
    if (!scName.trim()) return;
    try {
      const assumptions: Record<string, number> = {};
      scAssumptions.forEach((a) => {
        if (a.key.trim()) assumptions[a.key.trim()] = parseFloat(a.value) || 0;
      });
      await strategicAPI.createScenario({
        name: scName,
        description: scDesc,
        type: scType,
        assumptions,
      });
      setScName('');
      setScDesc('');
      setScType('base');
      setScAssumptions([{ key: '', value: '' }]);
      loadScenarios();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create scenario');
    }
  }

  async function handleRunScenario(id: string) {
    setRunningId(id);
    try {
      await strategicAPI.runScenario(id, {});
      loadScenarios();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run scenario');
    } finally {
      setRunningId(null);
    }
  }

  async function handleCompareScenarios() {
    if (compareIds.length < 2) return;
    try {
      const res = await strategicAPI.compareScenarios({ scenario_ids: compareIds });
      setComparisonResult(res.data);
      setComparisonDialogOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare');
    }
  }

  async function handleDeleteScenario(id: string) {
    try {
      await strategicAPI.deleteScenario(id);
      loadScenarios();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete');
    }
  }

  function toggleCompare(id: string) {
    setCompareIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  // --- Monte Carlo ---
  async function handleRunMonteCarlo() {
    if (!mcScenarioId) return;
    setMcLoading(true);
    setMcResult(null);
    try {
      const res = await strategicAPI.runMonteCarlo({ scenario_id: mcScenarioId, num_simulations: mcSimCount });
      setMcResult(res.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Monte Carlo simulation failed');
    } finally {
      setMcLoading(false);
    }
  }

  // --- What-If ---
  async function handleRunWhatIf() {
    setWiLoading(true);
    setWiResult(null);
    try {
      const base_values: Record<string, number> = {};
      wiBaseValues.forEach((v) => {
        if (v.key.trim()) base_values[v.key.trim()] = parseFloat(v.value) || 0;
      });
      const changes = wiChanges
        .filter((c) => c.variable.trim())
        .map((c) => ({
          variable: c.variable,
          base_value: parseFloat(c.base_value) || 0,
          new_value: parseFloat(c.new_value) || 0,
        }));

      const createRes = await strategicAPI.createWhatIf({ base_values, changes });
      const whatIfId = createRes.data?.id;
      if (whatIfId) {
        const runRes = await strategicAPI.runWhatIf(whatIfId, {});
        setWiResult(runRes.data);
      } else {
        setWiResult(createRes.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'What-If analysis failed');
    } finally {
      setWiLoading(false);
    }
  }

  // --- Risk Assessment ---
  async function handleAssessRisks() {
    if (!riskScenarioId) return;
    setRiskLoading(true);
    setRisks([]);
    try {
      const res = await strategicAPI.assessRisks({ scenario_id: riskScenarioId });
      setRisks(res.data?.risks || res.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Risk assessment failed');
    } finally {
      setRiskLoading(false);
    }
  }

  // --- Render ---
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Target className="h-8 w-8 text-blue-600" />
              Strategic Planning
            </h1>
            <p className="text-gray-500 mt-1">
              Scenario modeling, Monte Carlo simulation, what-if analysis, and risk assessment
            </p>
          </div>
          <Badge className="bg-blue-100 text-blue-800 border-blue-200 text-lg px-3 py-1">Enterprise</Badge>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
              Dismiss
            </button>
          </div>
        )}

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="scenarios">
              <Target className="h-4 w-4 mr-1" /> Scenarios ({scenarios.length})
            </TabsTrigger>
            <TabsTrigger value="monte-carlo">
              <BarChart3 className="h-4 w-4 mr-1" /> Monte Carlo
            </TabsTrigger>
            <TabsTrigger value="what-if">
              <Shuffle className="h-4 w-4 mr-1" /> What-If Analysis
            </TabsTrigger>
            <TabsTrigger value="risk">
              <ShieldAlert className="h-4 w-4 mr-1" /> Risk Assessment
            </TabsTrigger>
          </TabsList>

          {/* ======================== SCENARIOS TAB ======================== */}
          <TabsContent value="scenarios" className="space-y-4">
            {/* Create Form */}
            <Card>
              <CardHeader>
                <CardTitle>Create Scenario</CardTitle>
                <CardDescription>Define assumptions for a new financial scenario</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Name</Label>
                    <Input
                      value={scName}
                      onChange={(e) => setScName(e.target.value)}
                      placeholder="FY2027 Base Case"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Input
                      value={scDesc}
                      onChange={(e) => setScDesc(e.target.value)}
                      placeholder="Baseline forecast with current growth"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Type</Label>
                    <select
                      value={scType}
                      onChange={(e) => setScType(e.target.value as Scenario['type'])}
                      className="w-full p-2 border rounded-md text-sm"
                    >
                      <option value="base">Base</option>
                      <option value="best_case">Best Case</option>
                      <option value="worst_case">Worst Case</option>
                      <option value="stress_test">Stress Test</option>
                      <option value="custom">Custom</option>
                    </select>
                  </div>
                </div>

                {/* Assumptions key-value pairs */}
                <div className="space-y-2">
                  <Label className="flex items-center justify-between">
                    Assumptions
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setScAssumptions([...scAssumptions, { key: '', value: '' }])}
                    >
                      <Plus className="h-3 w-3 mr-1" /> Add
                    </Button>
                  </Label>
                  {scAssumptions.map((a, i) => (
                    <div key={i} className="flex gap-2 items-center">
                      <Input
                        placeholder="Key (e.g. growth_rate)"
                        value={a.key}
                        onChange={(e) => {
                          const next = [...scAssumptions];
                          next[i].key = e.target.value;
                          setScAssumptions(next);
                        }}
                        className="flex-1"
                      />
                      <Input
                        placeholder="Value"
                        type="number"
                        value={a.value}
                        onChange={(e) => {
                          const next = [...scAssumptions];
                          next[i].value = e.target.value;
                          setScAssumptions(next);
                        }}
                        className="w-32"
                      />
                      {scAssumptions.length > 1 && (
                        <button
                          onClick={() => setScAssumptions(scAssumptions.filter((_, j) => j !== i))}
                          className="text-gray-400 hover:text-red-500"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex gap-2">
                  <Button onClick={handleCreateScenario} className="bg-blue-600 hover:bg-blue-700">
                    <Plus className="h-4 w-4 mr-2" /> Create Scenario
                  </Button>
                  {compareIds.length >= 2 && (
                    <Button onClick={handleCompareScenarios} className="bg-violet-600 hover:bg-violet-700">
                      <GitCompareArrows className="h-4 w-4 mr-2" /> Compare ({compareIds.length})
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Scenario List */}
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => (
                  <Card key={i}>
                    <CardContent className="p-4">
                      <SkeletonCard />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : scenarios.length === 0 ? (
              <EmptyState
                icon={Target}
                title="No scenarios yet"
                description="Create your first scenario to start modeling financial outcomes."
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {scenarios.map((sc) => (
                  <Card
                    key={sc.id}
                    className={`hover:border-blue-300 transition-colors ${
                      compareIds.includes(sc.id) ? 'border-violet-400 ring-1 ring-violet-200' : ''
                    }`}
                  >
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="font-semibold text-gray-900">{sc.name}</div>
                        <div className="flex gap-1">
                          <Badge className={typeBadgeClass(sc.type)}>{sc.type.replace('_', ' ')}</Badge>
                          <Badge className={statusBadgeClass(sc.status)}>{sc.status}</Badge>
                        </div>
                      </div>
                      {sc.description && (
                        <p className="text-sm text-gray-500 line-clamp-2">{sc.description}</p>
                      )}
                      {sc.assumptions && Object.keys(sc.assumptions).length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(sc.assumptions).slice(0, 4).map(([k, v]) => (
                            <span key={k} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                              {k}: {v}
                            </span>
                          ))}
                          {Object.keys(sc.assumptions).length > 4 && (
                            <span className="text-xs text-gray-400">
                              +{Object.keys(sc.assumptions).length - 4} more
                            </span>
                          )}
                        </div>
                      )}
                      <div className="flex gap-2 pt-1">
                        <Button
                          size="sm"
                          onClick={() => handleRunScenario(sc.id)}
                          disabled={runningId === sc.id || sc.status === 'running'}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white"
                        >
                          {runningId === sc.id ? (
                            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                          ) : (
                            <Play className="h-3 w-3 mr-1" />
                          )}
                          Run
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => toggleCompare(sc.id)}
                          className={compareIds.includes(sc.id) ? 'bg-violet-50 border-violet-300' : ''}
                        >
                          <GitCompareArrows className="h-3 w-3 mr-1" />
                          {compareIds.includes(sc.id) ? 'Selected' : 'Compare'}
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDeleteScenario(sc.id)}
                          className="ml-auto text-gray-400 hover:text-red-500"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* ======================== MONTE CARLO TAB ======================== */}
          <TabsContent value="monte-carlo" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Monte Carlo Simulation</CardTitle>
                <CardDescription>Run probabilistic simulations on a scenario</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Scenario</Label>
                    <select
                      value={mcScenarioId}
                      onChange={(e) => setMcScenarioId(e.target.value)}
                      className="w-full p-2 border rounded-md text-sm"
                    >
                      <option value="">Select a scenario...</option>
                      {scenarios.map((sc) => (
                        <option key={sc.id} value={sc.id}>
                          {sc.name} ({sc.type})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label>Number of Simulations</Label>
                    <Input
                      type="number"
                      min={100}
                      max={10000}
                      step={100}
                      value={mcSimCount}
                      onChange={(e) => setMcSimCount(Math.min(10000, Math.max(100, parseInt(e.target.value) || 100)))}
                    />
                  </div>
                  <div className="flex items-end">
                    <Button
                      onClick={handleRunMonteCarlo}
                      disabled={!mcScenarioId || mcLoading}
                      className="bg-violet-600 hover:bg-violet-700 w-full"
                    >
                      {mcLoading ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <BarChart3 className="h-4 w-4 mr-2" />
                      )}
                      Run Simulation
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Results */}
            {mcLoading && (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <Card key={i}>
                    <CardContent className="p-3">
                      <Skeleton className="h-3 w-16 mb-2" />
                      <Skeleton className="h-6 w-20" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {mcResult && !mcLoading && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                  {[
                    { label: 'Mean', value: mcResult.mean, color: 'text-gray-900' },
                    { label: 'Median', value: mcResult.median, color: 'text-gray-900' },
                    { label: 'Std Dev', value: mcResult.std_dev, color: 'text-gray-600' },
                    { label: 'VaR 95%', value: mcResult.var_95, color: 'text-amber-700' },
                    { label: 'VaR 99%', value: mcResult.var_99, color: 'text-red-700' },
                    { label: 'Simulations', value: mcSimCount, color: 'text-blue-700' },
                  ].map((stat) => (
                    <Card key={stat.label}>
                      <CardContent className="p-3">
                        <div className="text-xs text-gray-500 uppercase">{stat.label}</div>
                        <div className={`text-lg font-bold ${stat.color}`}>{fmt(stat.value)}</div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {mcResult.histogram_bins.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Distribution Histogram</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Histogram bins={mcResult.histogram_bins} />
                      <div className="flex justify-between text-xs text-gray-400 mt-1">
                        <span>{fmt(mcResult.histogram_bins[0]?.bin_start)}</span>
                        <span>{fmt(mcResult.histogram_bins[mcResult.histogram_bins.length - 1]?.bin_end)}</span>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            )}

            {!mcResult && !mcLoading && (
              <EmptyState
                icon={BarChart3}
                title="No simulation results"
                description="Select a scenario and run a Monte Carlo simulation to view probabilistic outcomes."
              />
            )}
          </TabsContent>

          {/* ======================== WHAT-IF ANALYSIS TAB ======================== */}
          <TabsContent value="what-if" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>What-If Analysis</CardTitle>
                <CardDescription>Model the impact of changes to key financial variables</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Base Values */}
                <div className="space-y-2">
                  <Label className="flex items-center justify-between">
                    Base Values
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setWiBaseValues([...wiBaseValues, { key: '', value: '' }])}
                    >
                      <Plus className="h-3 w-3 mr-1" /> Add
                    </Button>
                  </Label>
                  {wiBaseValues.map((v, i) => (
                    <div key={i} className="flex gap-2 items-center">
                      <Input
                        placeholder="Variable name"
                        value={v.key}
                        onChange={(e) => {
                          const next = [...wiBaseValues];
                          next[i].key = e.target.value;
                          setWiBaseValues(next);
                        }}
                        className="flex-1"
                      />
                      <Input
                        placeholder="Value"
                        type="number"
                        value={v.value}
                        onChange={(e) => {
                          const next = [...wiBaseValues];
                          next[i].value = e.target.value;
                          setWiBaseValues(next);
                        }}
                        className="w-36"
                      />
                      {wiBaseValues.length > 1 && (
                        <button
                          onClick={() => setWiBaseValues(wiBaseValues.filter((_, j) => j !== i))}
                          className="text-gray-400 hover:text-red-500"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                {/* Changes */}
                <div className="space-y-2">
                  <Label className="flex items-center justify-between">
                    Proposed Changes
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        setWiChanges([...wiChanges, { variable: '', base_value: '', new_value: '' }])
                      }
                    >
                      <Plus className="h-3 w-3 mr-1" /> Add
                    </Button>
                  </Label>
                  {wiChanges.map((c, i) => (
                    <div key={i} className="flex gap-2 items-center">
                      <Input
                        placeholder="Variable"
                        value={c.variable}
                        onChange={(e) => {
                          const next = [...wiChanges];
                          next[i].variable = e.target.value;
                          setWiChanges(next);
                        }}
                        className="flex-1"
                      />
                      <Input
                        placeholder="Base"
                        type="number"
                        value={c.base_value}
                        onChange={(e) => {
                          const next = [...wiChanges];
                          next[i].base_value = e.target.value;
                          setWiChanges(next);
                        }}
                        className="w-28"
                      />
                      <Input
                        placeholder="New"
                        type="number"
                        value={c.new_value}
                        onChange={(e) => {
                          const next = [...wiChanges];
                          next[i].new_value = e.target.value;
                          setWiChanges(next);
                        }}
                        className="w-28"
                      />
                      {wiChanges.length > 1 && (
                        <button
                          onClick={() => setWiChanges(wiChanges.filter((_, j) => j !== i))}
                          className="text-gray-400 hover:text-red-500"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                <Button
                  onClick={handleRunWhatIf}
                  disabled={wiLoading}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  {wiLoading ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Shuffle className="h-4 w-4 mr-2" />
                  )}
                  Run What-If Analysis
                </Button>
              </CardContent>
            </Card>

            {/* Results */}
            {wiLoading && (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Card key={i}>
                    <CardContent className="p-4">
                      <Skeleton className="h-4 w-full mb-2" />
                      <Skeleton className="h-3 w-3/4" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {wiResult && !wiLoading && (
              <div className="space-y-4">
                {/* Delta Cards */}
                {Object.keys(wiResult.delta || {}).length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.entries(wiResult.delta).map(([key, delta]) => {
                      const pct = wiResult.percentage_change?.[key] ?? 0;
                      const isPositive = delta >= 0;
                      return (
                        <Card key={key}>
                          <CardContent className="p-4">
                            <div className="text-xs text-gray-500 uppercase">{key}</div>
                            <div className="flex items-center gap-2 mt-1">
                              {isPositive ? (
                                <TrendingUp className="h-4 w-4 text-emerald-600" />
                              ) : (
                                <TrendingDown className="h-4 w-4 text-red-600" />
                              )}
                              <span
                                className={`text-lg font-bold ${isPositive ? 'text-emerald-700' : 'text-red-700'}`}
                              >
                                {isPositive ? '+' : ''}
                                {fmt(delta)}
                              </span>
                              <span
                                className={`text-sm ${isPositive ? 'text-emerald-600' : 'text-red-600'}`}
                              >
                                ({isPositive ? '+' : ''}
                                {fmt(pct)}%)
                              </span>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                )}

                {/* Driver Breakdown */}
                {wiResult.driver_breakdown && wiResult.driver_breakdown.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Driver Breakdown</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {wiResult.driver_breakdown.map((d, i) => (
                        <div key={i} className="flex items-center gap-3">
                          <span className="text-sm text-gray-700 w-32 truncate">{d.variable}</span>
                          <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500 rounded-full"
                              style={{ width: `${Math.min(100, Math.abs(d.pct_contribution))}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500 w-16 text-right">{fmt(d.contribution)}</span>
                          <span className="text-xs text-gray-400 w-14 text-right">
                            {fmt(d.pct_contribution)}%
                          </span>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {!wiResult && !wiLoading && (
              <EmptyState
                icon={Shuffle}
                title="No what-if results"
                description="Define base values and proposed changes, then run the analysis to see the impact."
              />
            )}
          </TabsContent>

          {/* ======================== RISK ASSESSMENT TAB ======================== */}
          <TabsContent value="risk" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Risk Assessment</CardTitle>
                <CardDescription>Identify and evaluate risks for a given scenario</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Scenario</Label>
                    <select
                      value={riskScenarioId}
                      onChange={(e) => setRiskScenarioId(e.target.value)}
                      className="w-full p-2 border rounded-md text-sm"
                    >
                      <option value="">Select a scenario...</option>
                      {scenarios.map((sc) => (
                        <option key={sc.id} value={sc.id}>
                          {sc.name} ({sc.type})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end">
                    <Button
                      onClick={handleAssessRisks}
                      disabled={!riskScenarioId || riskLoading}
                      className="bg-amber-600 hover:bg-amber-700 w-full"
                    >
                      {riskLoading ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <ShieldAlert className="h-4 w-4 mr-2" />
                      )}
                      Assess Risks
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Risk Results */}
            {riskLoading && (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Card key={i}>
                    <CardContent className="p-4">
                      <Skeleton className="h-5 w-1/3 mb-2" />
                      <Skeleton className="h-3 w-2/3 mb-1" />
                      <Skeleton className="h-3 w-1/2" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {risks.length > 0 && !riskLoading && (
              <div className="space-y-3">
                {risks.map((risk) => (
                  <Card key={risk.id}>
                    <CardContent className="p-4 space-y-2">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-semibold text-gray-900">{risk.name}</h4>
                          <div className="flex gap-4 mt-1 text-sm text-gray-600">
                            <span>Probability: {fmt(risk.probability * 100)}%</span>
                            <span>Impact: {fmt(risk.impact * 100)}%</span>
                          </div>
                        </div>
                        <Badge className={severityColor(risk.severity)}>{risk.severity}</Badge>
                      </div>
                      {risk.mitigation && (
                        <div className="mt-2 p-2 bg-blue-50 border border-blue-100 rounded text-sm text-blue-800">
                          <span className="font-medium">Mitigation:</span> {risk.mitigation}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {risks.length === 0 && !riskLoading && (
              <EmptyState
                icon={ShieldAlert}
                title="No risk assessment yet"
                description="Select a scenario and run a risk assessment to identify potential threats."
              />
            )}
          </TabsContent>
        </Tabs>

        <Dialog open={comparisonDialogOpen} onOpenChange={setComparisonDialogOpen}>
          <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold flex items-center gap-2">
                <GitCompareArrows className="h-6 w-6 text-violet-600" />
                Scenario Comparison Dashboard
              </DialogTitle>
              <DialogDescription>
                Compare financial outcomes and assumptions across modeled scenarios.
              </DialogDescription>
            </DialogHeader>

            {comparisonResult && (
              <div className="space-y-6 py-4">
                <div className="rounded-md border overflow-hidden bg-card">
                  <Table>
                    <TableHeader className="bg-muted/50">
                      <TableRow>
                        <TableHead className="font-semibold text-foreground">Metric</TableHead>
                        {comparisonResult.detailed?.map((sc: any) => (
                          <TableHead key={sc.scenario_id} className="font-semibold text-foreground text-right">
                            {sc.scenario_name}
                            <span className="block text-xs font-normal text-muted-foreground capitalize">
                              ({sc.type.replace('_', ' ')})
                            </span>
                          </TableHead>
                        ))}
                        <TableHead className="font-semibold text-foreground text-right">Max Delta</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {comparisonResult.metrics?.map((metric: string) => {
                        const delta = comparisonResult.summary?.[metric]?.delta ?? 0;
                        return (
                          <TableRow key={metric} className="hover:bg-muted/30 transition-colors">
                            <TableCell className="font-medium capitalize text-foreground">
                              {metric.replace('_', ' ')}
                            </TableCell>
                            {comparisonResult.detailed?.map((sc: any) => {
                              const val = sc.metrics?.[metric] ?? 0;
                              return (
                                <TableCell key={sc.scenario_id} className="text-right tabular-nums text-foreground">
                                  {val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </TableCell>
                              );
                            })}
                            <TableCell className="text-right tabular-nums font-semibold text-violet-600 bg-violet-50/20">
                              {delta.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
