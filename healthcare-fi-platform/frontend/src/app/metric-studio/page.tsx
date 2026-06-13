'use client';

import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { BarChart3, CheckCircle, Clock, AlertCircle, Plus, Trash2 } from 'lucide-react';
import { metricStudioAPI } from '@/lib/api/client';

interface Metric {
  id: string;
  name: string;
  formula_id: string;
  description?: string;
  category: string;
  status: string;
  version: number;
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  published: 'bg-blue-100 text-blue-700',
  certified: 'bg-emerald-100 text-emerald-700',
  deprecated: 'bg-amber-100 text-amber-700',
  archived: 'bg-red-100 text-red-700',
};

export default function MetricStudioPage() {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [activeTab, setActiveTab] = useState('all');
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newFormulaId, setNewFormulaId] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newCategory, setNewCategory] = useState('general');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { loadMetrics(); }, []);

  async function loadMetrics() {
    setError(null);
    try {
      const res = await metricStudioAPI.list();
      setMetrics(res.data.metrics || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!newName.trim() || !newFormulaId.trim()) return;
    try {
      await metricStudioAPI.create({ name: newName, formula_id: newFormulaId, description: newDesc, category: newCategory });
      setNewName(''); setNewFormulaId(''); setNewDesc(''); setShowCreate(false);
      loadMetrics();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed');
    }
  }

  async function handleAction(id: string, action: string) {
    try {
      if (action === 'publish') await metricStudioAPI.publish(id);
      else if (action === 'certify') await metricStudioAPI.certify(id);
      else if (action === 'deprecate') await metricStudioAPI.deprecate(id);
      else throw new Error(`Unknown action: ${action}`);
      loadMetrics();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed');
    }
  }

  async function handleDelete(id: string) {
    try {
      await metricStudioAPI.delete(id);
      loadMetrics();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  }

  const filtered = activeTab === 'all' ? metrics : metrics.filter(m => m.status === activeTab);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <BarChart3 className="h-8 w-8 text-blue-600" />
              Metric Studio
            </h1>
            <p className="text-gray-500 mt-1">Lifecycle management, certification, and dependency tracking for metrics</p>
          </div>
          <Button onClick={() => setShowCreate(!showCreate)} className="bg-blue-600 hover:bg-blue-700">
            <Plus className="h-4 w-4 mr-2" /> New Metric
          </Button>
        </div>

        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-4 flex items-center gap-2 text-red-700">
              <span>{error}</span>
              <Button size="sm" variant="ghost" onClick={() => setError(null)} className="ml-auto">Dismiss</Button>
            </CardContent>
          </Card>
        )}

        {showCreate && (
          <Card>
            <CardHeader><CardTitle>Create Metric</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1"><Label>Name</Label><Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="AR Days" /></div>
                <div className="space-y-1"><Label>Formula ID</Label><Input value={newFormulaId} onChange={(e) => setNewFormulaId(e.target.value)} placeholder="AR_DAYS_V1" /></div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1"><Label>Description</Label><Input value={newDesc} onChange={(e) => setNewDesc(e.target.value)} placeholder="Days to collect" /></div>
                <div className="space-y-1"><Label>Category</Label>
                  <select value={newCategory} onChange={(e) => setNewCategory(e.target.value)} className="w-full p-2 border rounded text-sm">
                    <option value="general">General</option>
                    <option value="financial">Financial</option>
                    <option value="operational">Operational</option>
                    <option value="clinical">Clinical</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleCreate} className="bg-emerald-600 hover:bg-emerald-700">Create</Button>
                <Button onClick={() => setShowCreate(false)} variant="outline">Cancel</Button>
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="all">All ({metrics.length})</TabsTrigger>
            <TabsTrigger value="draft">Draft ({metrics.filter(m => m.status === 'draft').length})</TabsTrigger>
            <TabsTrigger value="published">Published ({metrics.filter(m => m.status === 'published').length})</TabsTrigger>
            <TabsTrigger value="certified">Certified ({metrics.filter(m => m.status === 'certified').length})</TabsTrigger>
            <TabsTrigger value="deprecated">Deprecated ({metrics.filter(m => m.status === 'deprecated').length})</TabsTrigger>
          </TabsList>
        </Tabs>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{[1,2,3].map(i => <Skeleton key={i} className="h-32" />)}</div>
        ) : filtered.length === 0 ? (
          <Card><CardContent className="p-8 text-center text-gray-500">No metrics in this category</CardContent></Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {filtered.map((m) => (
              <Card key={m.id} className="hover:border-blue-300 transition-colors">
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">{m.name}</h3>
                    <Badge className={STATUS_COLORS[m.status] || 'bg-gray-100'}>{m.status}</Badge>
                  </div>
                  <div className="text-sm font-mono text-gray-600 bg-gray-50 p-2 rounded">{m.formula_id}</div>
                  {m.description && <div className="text-xs text-gray-500">{m.description}</div>}
                  <div className="flex gap-1 flex-wrap">
                    <Badge variant="outline" className="text-xs">{m.category}</Badge>
                    <Badge variant="outline" className="text-xs">v{m.version}</Badge>
                  </div>
                  <div className="flex gap-1 pt-2">
                    {m.status === 'draft' && <Button size="sm" onClick={() => handleAction(m.id, 'publish')} className="bg-blue-600 hover:bg-blue-700 text-xs">Publish</Button>}
                    {m.status === 'published' && <Button size="sm" onClick={() => handleAction(m.id, 'certify')} className="bg-emerald-600 hover:bg-emerald-700 text-xs">Certify</Button>}
                    {m.status === 'certified' && <Button size="sm" onClick={() => handleAction(m.id, 'deprecate')} variant="outline" className="text-xs">Deprecate</Button>}
                    <Button size="sm" onClick={() => handleDelete(m.id)} variant="outline" className="text-red-600 hover:text-red-700 text-xs ml-auto">
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
