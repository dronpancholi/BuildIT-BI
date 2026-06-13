'use client';

import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  ScrollArea,
  ScrollBar,
} from '@/components/ui/scroll-area';
import {
  Code2,
  Play,
  Save,
  Trash2,
  RefreshCw,
  AlertTriangle,
  Plus,
  FileCode2,
  Database,
  Copy,
  Check,
  BookOpen,
  ChevronRight,
  X,
} from 'lucide-react';
import { queryAPI } from '@/lib/api/client';

interface QueryMetric {
  id: string;
  name: string;
  aggregation?: string;
}

interface QueryDimension {
  id: string;
  name: string;
}

interface QueryFilter {
  field: string;
  operator: string;
  value: string;
}

interface SavedQuery {
  id: string;
  name: string;
  sql?: string;
  config?: any;
  created_at?: string;
}

interface QueryTemplate {
  id: string;
  name: string;
  description?: string;
  sql?: string;
  category?: string;
  config?: {
    metrics?: string[];
    dimensions?: string[];
    filters?: QueryFilter[];
  };
}

interface QueryResult {
  columns: string[];
  rows: any[];
  row_count?: number;
  execution_time_ms?: number;
  sql?: string;
}

export default function QueryEnginePage() {
  const [availableMetrics, setAvailableMetrics] = useState<QueryMetric[]>([]);
  const [availableDimensions, setAvailableDimensions] = useState<QueryDimension[]>([]);

  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [selectedDimensions, setSelectedDimensions] = useState<string[]>([]);
  const [filters, setFilters] = useState<QueryFilter[]>([]);

  const [generatedSQL, setGeneratedSQL] = useState<string | null>(null);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);

  const [loading, setLoading] = useState({
    metrics: true,
    dimensions: true,
    generate: false,
    execute: false,
    saved: true,
    templates: true,
  });
  const [errors, setErrors] = useState<Record<string, string | null>>({});

  const [savedQueries, setSavedQueries] = useState<SavedQuery[]>([]);
  const [templates, setTemplates] = useState<QueryTemplate[]>([]);

  const [queryName, setQueryName] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchMetrics();
    fetchDimensions();
    fetchSavedQueries();
    fetchTemplates();
  }, []);

  const fetchMetrics = async () => {
    setLoading((prev) => ({ ...prev, metrics: true }));
    setErrors((prev) => ({ ...prev, metrics: null }));
    try {
      const response = await queryAPI.execute({ type: 'list_metrics' }).catch(() => {
        return { data: { metrics: [] } };
      });
      setAvailableMetrics(response.data?.metrics || response.data || []);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, metrics: err?.message || 'Failed' }));
    } finally {
      setLoading((prev) => ({ ...prev, metrics: false }));
    }
  };

  const fetchDimensions = async () => {
    setLoading((prev) => ({ ...prev, dimensions: true }));
    setErrors((prev) => ({ ...prev, dimensions: null }));
    try {
      const response = await queryAPI.execute({ type: 'list_dimensions' }).catch(() => {
        return { data: { dimensions: [] } };
      });
      setAvailableDimensions(response.data?.dimensions || response.data || []);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, dimensions: err?.message || 'Failed' }));
    } finally {
      setLoading((prev) => ({ ...prev, dimensions: false }));
    }
  };

  const fetchSavedQueries = async () => {
    setLoading((prev) => ({ ...prev, saved: true }));
    try {
      const response = await queryAPI.listSaved();
      setSavedQueries(response.data?.queries || response.data || []);
    } catch {
      setSavedQueries([]);
    } finally {
      setLoading((prev) => ({ ...prev, saved: false }));
    }
  };

  const fetchTemplates = async () => {
    setLoading((prev) => ({ ...prev, templates: true }));
    try {
      const response = await queryAPI.listTemplates();
      setTemplates(response.data?.templates || response.data || []);
    } catch {
      setTemplates([]);
    } finally {
      setLoading((prev) => ({ ...prev, templates: false }));
    }
  };

  const handleGenerateSQL = async () => {
    if (selectedMetrics.length === 0) return;
    setLoading((prev) => ({ ...prev, generate: true }));
    setErrors((prev) => ({ ...prev, generate: null }));
    try {
      const response = await queryAPI.generateSQL({
        metrics: selectedMetrics,
        dimensions: selectedDimensions,
        filters,
      });
      setGeneratedSQL(response.data?.sql || response.data?.query || null);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, generate: err?.message || 'Failed to generate SQL' }));
    } finally {
      setLoading((prev) => ({ ...prev, generate: false }));
    }
  };

  const handleExecuteQuery = async () => {
    if (selectedMetrics.length === 0 && !generatedSQL) return;
    setLoading((prev) => ({ ...prev, execute: true }));
    setErrors((prev) => ({ ...prev, execute: null }));
    try {
      const response = await queryAPI.execute({
        metrics: selectedMetrics,
        dimensions: selectedDimensions,
        filters,
        sql: generatedSQL,
      });
      setQueryResult(response.data);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, execute: err?.message || 'Query execution failed' }));
    } finally {
      setLoading((prev) => ({ ...prev, execute: false }));
    }
  };

  const handleSaveQuery = async () => {
    if (!queryName.trim() || selectedMetrics.length === 0) return;
    try {
      await queryAPI.saveQuery({
        name: queryName,
        sql: generatedSQL,
        config: {
          metrics: selectedMetrics,
          dimensions: selectedDimensions,
          filters,
        },
      });
      setQueryName('');
      fetchSavedQueries();
    } catch (err) {
      console.error('Failed to save query:', err);
    }
  };

  const handleDeleteSaved = async (id: string) => {
    try {
      await queryAPI.deleteSaved(id);
      setSavedQueries((prev) => prev.filter((q) => q.id !== id));
    } catch (err) {
      console.error('Failed to delete query:', err);
    }
  };

  const handleLoadTemplate = (template: QueryTemplate) => {
    if (template.sql) {
      setGeneratedSQL(template.sql);
    }
    if (template.config) {
      setSelectedMetrics(template.config.metrics || []);
      setSelectedDimensions(template.config.dimensions || []);
      setFilters(template.config.filters || []);
    }
  };

  const handleCopySQL = () => {
    if (generatedSQL) {
      navigator.clipboard.writeText(generatedSQL);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const addFilter = () => {
    setFilters((prev) => [...prev, { field: '', operator: 'equals', value: '' }]);
  };

  const updateFilter = (index: number, field: keyof QueryFilter, value: string) => {
    setFilters((prev) =>
      prev.map((f, i) => (i === index ? { ...f, [field]: value } : f))
    );
  };

  const removeFilter = (index: number) => {
    setFilters((prev) => prev.filter((_, i) => i !== index));
  };

  const toggleMetric = (id: string) => {
    setSelectedMetrics((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
    setGeneratedSQL(null);
    setQueryResult(null);
  };

  const toggleDimension = (id: string) => {
    setSelectedDimensions((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
    setGeneratedSQL(null);
    setQueryResult(null);
  };

  const renderSkeletons = (count: number) => (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-2 rounded-lg">
          <Skeleton className="h-4 w-4 rounded" />
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-3 w-20 ml-auto" />
        </div>
      ))}
    </div>
  );

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Code2 className="h-8 w-8 text-primary" />
              Query Engine
            </h1>
            <p className="text-muted-foreground">
              Build, generate, and execute SQL queries against your data
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => { fetchMetrics(); fetchDimensions(); fetchSavedQueries(); fetchTemplates(); }}>
              <RefreshCw className="h-4 w-4 mr-1.5" />
              Refresh
            </Button>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-12">
          {/* Left Sidebar - Config */}
          <div className="lg:col-span-3 space-y-4">
            {/* Metrics Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Metrics</CardTitle>
                <CardDescription>{selectedMetrics.length} selected</CardDescription>
              </CardHeader>
              <CardContent>
                {loading.metrics ? (
                  renderSkeletons(5)
                ) : errors.metrics ? (
                  <p className="text-xs text-destructive">{errors.metrics}</p>
                ) : availableMetrics.length === 0 ? (
                  <p className="text-xs text-muted-foreground text-center py-4">
                    No metrics available
                  </p>
                ) : (
                  <ScrollArea className="max-h-48">
                    <div className="space-y-1">
                      {availableMetrics.map((metric) => (
                        <button
                          key={metric.id}
                          onClick={() => toggleMetric(metric.id)}
                          className={`w-full flex items-center gap-2 p-2 rounded-lg text-left text-xs transition-colors ${
                            selectedMetrics.includes(metric.id)
                              ? 'bg-primary/10 text-primary'
                              : 'hover:bg-muted'
                          }`}
                        >
                          <div
                            className={`h-3.5 w-3.5 rounded border flex items-center justify-center ${
                              selectedMetrics.includes(metric.id)
                                ? 'bg-primary border-primary'
                                : 'border-border'
                            }`}
                          >
                            {selectedMetrics.includes(metric.id) && (
                              <Check className="h-2.5 w-2.5 text-primary-foreground" />
                            )}
                          </div>
                          <span className="flex-1 truncate">{metric.name}</span>
                          {metric.aggregation && (
                            <Badge variant="outline" className="text-[9px] h-4 px-1">
                              {metric.aggregation}
                            </Badge>
                          )}
                        </button>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>

            {/* Dimensions Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Dimensions</CardTitle>
                <CardDescription>{selectedDimensions.length} selected</CardDescription>
              </CardHeader>
              <CardContent>
                {loading.dimensions ? (
                  renderSkeletons(4)
                ) : errors.dimensions ? (
                  <p className="text-xs text-destructive">{errors.dimensions}</p>
                ) : availableDimensions.length === 0 ? (
                  <p className="text-xs text-muted-foreground text-center py-4">
                    No dimensions available
                  </p>
                ) : (
                  <ScrollArea className="max-h-48">
                    <div className="space-y-1">
                      {availableDimensions.map((dim) => (
                        <button
                          key={dim.id}
                          onClick={() => toggleDimension(dim.id)}
                          className={`w-full flex items-center gap-2 p-2 rounded-lg text-left text-xs transition-colors ${
                            selectedDimensions.includes(dim.id)
                              ? 'bg-primary/10 text-primary'
                              : 'hover:bg-muted'
                          }`}
                        >
                          <div
                            className={`h-3.5 w-3.5 rounded border flex items-center justify-center ${
                              selectedDimensions.includes(dim.id)
                                ? 'bg-primary border-primary'
                                : 'border-border'
                            }`}
                          >
                            {selectedDimensions.includes(dim.id) && (
                              <Check className="h-2.5 w-2.5 text-primary-foreground" />
                            )}
                          </div>
                          <span className="flex-1 truncate">{dim.name}</span>
                        </button>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>

            {/* Filters */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center justify-between">
                  Filters
                  <Button variant="ghost" size="icon-sm" onClick={addFilter}>
                    <Plus className="h-3.5 w-3.5" />
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {filters.length === 0 ? (
                  <p className="text-xs text-muted-foreground text-center py-4">
                    No filters
                  </p>
                ) : (
                  filters.map((filter, idx) => (
                    <div key={idx} className="space-y-1.5">
                      <div className="flex items-center gap-1.5">
                        <Input
                          placeholder="Field"
                          value={filter.field}
                          onChange={(e) => updateFilter(idx, 'field', e.target.value)}
                          className="h-7 text-xs flex-1"
                        />
                        <Button
                          variant="ghost"
                          size="icon-xs"
                          onClick={() => removeFilter(idx)}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                      <div className="flex gap-1.5">
                        <Select
                          value={filter.operator}
                          onValueChange={(val) => val && updateFilter(idx, 'operator', val)}
                        >
                          <SelectTrigger className="h-7 text-xs flex-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="equals">Equals</SelectItem>
                            <SelectItem value="not_equals">Not Equals</SelectItem>
                            <SelectItem value="gt">Greater Than</SelectItem>
                            <SelectItem value="lt">Less Than</SelectItem>
                            <SelectItem value="gte">Greater or Equal</SelectItem>
                            <SelectItem value="lte">Less or Equal</SelectItem>
                            <SelectItem value="contains">Contains</SelectItem>
                            <SelectItem value="in">In</SelectItem>
                          </SelectContent>
                        </Select>
                        <Input
                          placeholder="Value"
                          value={filter.value}
                          onChange={(e) => updateFilter(idx, 'value', e.target.value)}
                          className="h-7 text-xs flex-1"
                        />
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Center - SQL & Results */}
          <div className="lg:col-span-6 space-y-4">
            {/* SQL Generator Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Code2 className="h-4 w-4" />
                    SQL Generator
                  </span>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleGenerateSQL}
                      disabled={selectedMetrics.length === 0 || loading.generate}
                    >
                      {loading.generate ? (
                        <RefreshCw className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                      ) : (
                        <FileCode2 className="h-3.5 w-3.5 mr-1.5" />
                      )}
                      Generate SQL
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleExecuteQuery}
                      disabled={loading.execute || (selectedMetrics.length === 0 && !generatedSQL)}
                    >
                      {loading.execute ? (
                        <RefreshCw className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                      ) : (
                        <Play className="h-3.5 w-3.5 mr-1.5" />
                      )}
                      Execute
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {errors.generate && (
                  <div className="mb-3 p-2 rounded-lg bg-destructive/10 text-destructive text-xs flex items-center gap-2">
                    <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                    {errors.generate}
                  </div>
                )}
                {generatedSQL ? (
                  <div className="relative">
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant="outline" className="text-[10px]">Generated SQL</Badge>
                      <Button variant="ghost" size="sm" onClick={handleCopySQL} className="h-7 text-xs">
                        {copied ? (
                          <Check className="h-3.5 w-3.5 mr-1" />
                        ) : (
                          <Copy className="h-3.5 w-3.5 mr-1" />
                        )}
                        {copied ? 'Copied' : 'Copy'}
                      </Button>
                    </div>
                    <pre className="p-4 rounded-lg bg-muted/50 text-xs font-mono overflow-x-auto whitespace-pre-wrap border">
                      {generatedSQL}
                    </pre>
                  </div>
                ) : (
                  <div className="py-12 text-center">
                    <Code2 className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                    <p className="text-xs text-muted-foreground">
                      Select metrics and dimensions, then click Generate SQL
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Query Results */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Database className="h-4 w-4" />
                    Query Results
                  </span>
                  {queryResult && (
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-[10px]">
                        {queryResult.rows?.length || queryResult.row_count || 0} rows
                      </Badge>
                      {queryResult.execution_time_ms !== undefined && (
                        <Badge variant="outline" className="text-[10px]">
                          {queryResult.execution_time_ms}ms
                        </Badge>
                      )}
                    </div>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {errors.execute && (
                  <div className="mb-3 p-2 rounded-lg bg-destructive/10 text-destructive text-xs flex items-center gap-2">
                    <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                    {errors.execute}
                  </div>
                )}
                {loading.execute ? (
                  <div className="py-12 text-center">
                    <RefreshCw className="h-8 w-8 text-muted-foreground animate-spin mx-auto mb-2" />
                    <p className="text-xs text-muted-foreground">Executing query...</p>
                  </div>
                ) : queryResult && queryResult.rows && queryResult.rows.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {queryResult.columns?.map((col: string, i: number) => (
                          <TableHead key={i}>{col}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {queryResult.rows.map((row: any, i: number) => (
                        <TableRow key={i}>
                          {queryResult.columns?.map((col: string, j: number) => (
                            <TableCell key={j}>
                              {row[col] === null || row[col] === undefined ? (
                                <span className="text-muted-foreground">—</span>
                              ) : typeof row[col] === 'number' ? (
                                row[col].toLocaleString()
                              ) : (
                                String(row[col])
                              )}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : queryResult ? (
                  <div className="py-12 text-center">
                    <Database className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                    <p className="text-xs text-muted-foreground">Query returned no results</p>
                  </div>
                ) : (
                  <div className="py-12 text-center">
                    <Database className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                    <p className="text-xs text-muted-foreground">
                      Results will appear here after query execution
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Sidebar - Saved & Templates */}
          <div className="lg:col-span-3 space-y-4">
            {/* Save Query */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Save Query</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Input
                  placeholder="Query name..."
                  value={queryName}
                  onChange={(e) => setQueryName(e.target.value)}
                />
                <Button
                  className="w-full"
                  size="sm"
                  onClick={handleSaveQuery}
                  disabled={!queryName.trim() || selectedMetrics.length === 0}
                >
                  <Save className="h-3.5 w-3.5 mr-1.5" />
                  Save Current Query
                </Button>
              </CardContent>
            </Card>

            {/* Saved Queries */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Saved Queries</CardTitle>
                <CardDescription>{savedQueries.length} saved</CardDescription>
              </CardHeader>
              <CardContent>
                {loading.saved ? (
                  renderSkeletons(4)
                ) : savedQueries.length === 0 ? (
                  <p className="text-xs text-muted-foreground text-center py-4">
                    No saved queries
                  </p>
                ) : (
                  <ScrollArea className="max-h-64">
                    <div className="space-y-1.5">
                      {savedQueries.map((query) => (
                        <div
                          key={query.id}
                          className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted group"
                        >
                          <FileCode2 className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium truncate">{query.name}</p>
                            {query.created_at && (
                              <p className="text-[10px] text-muted-foreground">
                                {new Date(query.created_at).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                          <div className="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button
                              variant="ghost"
                              size="icon-xs"
                              onClick={() => {
                                if (query.sql) setGeneratedSQL(query.sql);
                                if (query.config) {
                                  setSelectedMetrics(query.config.metrics || []);
                                  setSelectedDimensions(query.config.dimensions || []);
                                  setFilters(query.config.filters || []);
                                }
                              }}
                            >
                              <ChevronRight className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon-xs"
                              onClick={() => handleDeleteSaved(query.id)}
                            >
                              <Trash2 className="h-3 w-3 text-destructive" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>

            {/* Query Templates */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <BookOpen className="h-4 w-4" />
                  Query Templates
                </CardTitle>
                <CardDescription>{templates.length} templates</CardDescription>
              </CardHeader>
              <CardContent>
                {loading.templates ? (
                  renderSkeletons(3)
                ) : templates.length === 0 ? (
                  <p className="text-xs text-muted-foreground text-center py-4">
                    No templates available
                  </p>
                ) : (
                  <ScrollArea className="max-h-64">
                    <div className="space-y-1.5">
                      {templates.map((template) => (
                        <button
                          key={template.id}
                          onClick={() => handleLoadTemplate(template)}
                          className="w-full text-left p-2 rounded-lg hover:bg-muted transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <FileCode2 className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-medium truncate">{template.name}</p>
                              {template.category && (
                                <p className="text-[10px] text-muted-foreground">
                                  {template.category}
                                </p>
                              )}
                            </div>
                          </div>
                          {template.description && (
                            <p className="text-[10px] text-muted-foreground mt-1 ml-5.5 line-clamp-2">
                              {template.description}
                            </p>
                          )}
                        </button>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
