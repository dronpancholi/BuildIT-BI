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
import { Code, Play, Check, X, Search, Plus, Trash2, BookOpen } from 'lucide-react';
import { bflAPI } from '@/lib/api/client';

interface Formula {
  id: string;
  name: string;
  expression: string;
  description?: string;
  category: string;
  tags: string[];
  version: number;
}

interface FuncInfo {
  name: string;
  category: string;
  description: string;
}

export default function FormulasPage() {
  const [loading, setLoading] = useState(true);
  const [expression, setExpression] = useState('');
  const [validationResult, setValidationResult] = useState<any>(null);
  const [sqlResult, setSqlResult] = useState<any>(null);
  const [published, setPublished] = useState<Formula[]>([]);
  const [functions, setFunctions] = useState<FuncInfo[]>([]);
  const [dialect, setDialect] = useState('postgresql');
  const [publishName, setPublishName] = useState('');
  const [publishDesc, setPublishDesc] = useState('');
  const [activeTab, setActiveTab] = useState('editor');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setError(null);
    try {
      const [funcData, pubData] = await Promise.all([
        bflAPI.listFunctions(),
        bflAPI.listPublished(),
      ]);
      setFunctions(funcData.data.functions || []);
      setPublished(pubData.data.formulas || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }

  async function handleParse() {
    if (!expression.trim()) return;
    try {
      const result = await bflAPI.validate({ expression });
      setValidationResult(result);
    } catch (err) {
      setValidationResult({ valid: false, errors: ['Network error'] });
    }
  }

  async function handleGenerateSQL() {
    if (!expression.trim()) return;
    try {
      const result = await bflAPI.generateSql({ expression, dialect });
      setSqlResult(result);
    } catch (err) {
      setSqlResult({ valid: false, sql: '', errors: ['Network error'] });
    }
  }

  async function handlePublish() {
    if (!publishName.trim() || !expression.trim()) return;
    try {
      await bflAPI.publish({ name: publishName, expression, description: publishDesc, category: 'custom' });
      setPublishName('');
      setPublishDesc('');
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Publish failed');
    }
  }

  const healthFormulas = [
    { name: 'Revenue YTD', expr: 'YTD(net_patient_revenue)', desc: 'Revenue from Oct 1 of fiscal year' },
    { name: 'AR Days', expr: 'ROUND(accounts_receivable / (net_patient_revenue / 365), 0)', desc: 'Average days to collect' },
    { name: 'Operating Margin', expr: 'ROUND((net_patient_revenue - operating_expenses) / net_patient_revenue * 100, 1)', desc: 'Operating margin %' },
    { name: 'Bad Debt Rate', expr: 'ROUND(bad_debt / net_patient_revenue * 100, 2)', desc: 'Bad debt percentage' },
    { name: 'Case Mix Index', expr: 'ROUND(total_reimbursement / total_cases, 2)', desc: 'Revenue per case' },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Code className="h-8 w-8 text-violet-600" />
              BuildIT Formula Language
            </h1>
            <p className="text-gray-500 mt-1">Parse, validate, and publish healthcare financial formulas</p>
          </div>
          <Badge className="bg-violet-100 text-violet-800 border-violet-200 text-lg px-3 py-1">v1.0</Badge>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="editor">Formula Editor</TabsTrigger>
            <TabsTrigger value="functions">Functions ({functions.length})</TabsTrigger>
            <TabsTrigger value="published">Published ({published.length})</TabsTrigger>
            <TabsTrigger value="templates">Healthcare Templates</TabsTrigger>
          </TabsList>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2 mt-3">
              <span>{error}</span>
              <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">Dismiss</button>
            </div>
          )}

          <TabsContent value="editor" className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Formula Editor</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Expression</Label>
                  <textarea
                    className="w-full h-32 p-3 font-mono text-sm border rounded-lg bg-gray-950 text-green-400"
                    value={expression}
                    onChange={(e) => setExpression(e.target.value)}
                    placeholder="YTD(net_patient_revenue) / accounts_receivable * 365"
                  />
                </div>
                <div className="flex gap-3">
                  <Button onClick={handleParse} className="bg-blue-600 hover:bg-blue-700">
                    <Check className="h-4 w-4 mr-2" /> Validate
                  </Button>
                  <Button onClick={handleGenerateSQL} className="bg-emerald-600 hover:bg-emerald-700">
                    <Play className="h-4 w-4 mr-2" /> Generate SQL
                  </Button>
                  <div className="flex items-center gap-2 ml-auto">
                    <Label className="text-sm">Dialect:</Label>
                    <select value={dialect} onChange={(e) => setDialect(e.target.value)} className="p-1 border rounded text-sm">
                      <option value="postgresql">PostgreSQL</option>
                      <option value="snowflake">Snowflake</option>
                      <option value="bigquery">BigQuery</option>
                    </select>
                  </div>
                </div>

                {validationResult && (
                  <div className={`p-3 rounded-lg border ${validationResult.valid ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
                    {validationResult.valid ? (
                      <span className="text-emerald-700 font-medium flex items-center gap-1"><Check className="h-4 w-4" /> Valid expression</span>
                    ) : (
                      <div className="text-red-700">
                        {(validationResult.errors || []).map((e: string, i: number) => <div key={i}>Error: {e}</div>)}
                      </div>
                    )}
                  </div>
                )}

                {sqlResult && (
                  <div className="p-3 rounded-lg border bg-gray-50 border-gray-200">
                    <Label className="text-xs text-gray-500 uppercase">Generated SQL ({sqlResult.dialect})</Label>
                    <pre className="mt-1 text-sm font-mono text-gray-800 whitespace-pre-wrap">{sqlResult.sql || 'No SQL generated'}</pre>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="functions" className="space-y-4">
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1,2,3,4,5,6].map(i => <Skeleton key={i} className="h-24" />)}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {functions.map((f, i) => (
                  <Card key={i} className="hover:border-blue-300 transition-colors">
                    <CardContent className="p-3">
                      <div className="font-mono text-sm font-semibold text-blue-700">{f.name}()</div>
                      <div className="text-xs text-gray-500 mt-1">{f.category}</div>
                      <div className="text-xs text-gray-600 mt-1">{f.description}</div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="published" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Publish New Formula</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Name</Label>
                    <Input value={publishName} onChange={(e) => setPublishName(e.target.value)} placeholder="AR Days" />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Input value={publishDesc} onChange={(e) => setPublishDesc(e.target.value)} placeholder="Days to collect receivables" />
                  </div>
                </div>
                <Button onClick={handlePublish} className="mt-3 bg-violet-600 hover:bg-violet-700">
                  <Plus className="h-4 w-4 mr-2" /> Publish
                </Button>
              </CardContent>
            </Card>
            {published.length === 0 ? (
              <Card><CardContent className="p-8 text-center text-gray-500">No published formulas yet</CardContent></Card>
            ) : (
              published.map((f, i) => (
                <Card key={i}>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <div className="font-semibold">{f.name}</div>
                      <div className="text-sm font-mono text-gray-600">{f.expression}</div>
                    </div>
                    <Badge className="bg-violet-100 text-violet-800">v{f.version}</Badge>
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>

          <TabsContent value="templates" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {healthFormulas.map((f, i) => (
                <Card key={i} className="hover:border-violet-300 cursor-pointer transition-colors" onClick={() => { setExpression(f.expr); setActiveTab('editor'); }}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="font-semibold">{f.name}</div>
                      <BookOpen className="h-4 w-4 text-gray-400" />
                    </div>
                    <div className="text-sm font-mono text-violet-600 mt-1">{f.expr}</div>
                    <div className="text-xs text-gray-500 mt-1">{f.desc}</div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
