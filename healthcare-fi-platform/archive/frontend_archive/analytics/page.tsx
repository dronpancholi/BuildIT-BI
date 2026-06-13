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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  BarChart3,
  Search,
  Plus,
  Save,
  Play,
  RefreshCw,
  Database,
  Layers,
  FileText,
  Calculator,
  Hash,
  Type,
  Calendar,
  ToggleLeft,
  AlertTriangle,
} from 'lucide-react';
import { analyticsAPI } from '@/lib/api/client';

interface Metric {
  id: string;
  name: string;
  description?: string;
  category: string;
  aggregation: string;
  format?: string;
  expression?: string;
  created_at?: string;
}

interface Dimension {
  id: string;
  name: string;
  description?: string;
  cardinality: string;
  source_table?: string;
  created_at?: string;
}

interface SavedReport {
  id: string;
  name: string;
  description?: string;
  query?: any;
  created_at?: string;
}

interface QueryFilter {
  field: string;
  operator: string;
  value: string;
}

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState('metrics');

  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [metricsLoading, setMetricsLoading] = useState(true);
  const [metricsError, setMetricsError] = useState<string | null>(null);

  const [dimensions, setDimensions] = useState<Dimension[]>([]);
  const [dimensionsLoading, setDimensionsLoading] = useState(true);
  const [dimensionsError, setDimensionsError] = useState<string | null>(null);

  const [savedReports, setSavedReports] = useState<SavedReport[]>([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [reportsError, setReportsError] = useState<string | null>(null);

  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [selectedDimensions, setSelectedDimensions] = useState<string[]>([]);
  const [filters, setFilters] = useState<QueryFilter[]>([]);
  const [queryResult, setQueryResult] = useState<any>(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);

  const [reportName, setReportName] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchMetrics();
    fetchDimensions();
    fetchSavedReports();
  }, []);

  const fetchMetrics = async () => {
    setMetricsLoading(true);
    setMetricsError(null);
    try {
      const response = await analyticsAPI.listMetrics({ limit: 100 });
      setMetrics(response.data?.metrics || response.data || []);
    } catch (error: any) {
      setMetricsError(error?.message || 'Failed to load metrics');
    } finally {
      setMetricsLoading(false);
    }
  };

  const fetchDimensions = async () => {
    setDimensionsLoading(true);
    setDimensionsError(null);
    try {
      const response = await analyticsAPI.listDimensions({ limit: 100 });
      setDimensions(response.data?.dimensions || response.data || []);
    } catch (error: any) {
      setDimensionsError(error?.message || 'Failed to load dimensions');
    } finally {
      setDimensionsLoading(false);
    }
  };

  const fetchSavedReports = async () => {
    setReportsLoading(true);
    setReportsError(null);
    try {
      const response = await analyticsAPI.listSavedReports({ limit: 100 });
      setSavedReports(response.data?.saved_reports || response.data || []);
    } catch (error: any) {
      setReportsError(error?.message || 'Failed to load saved reports');
    } finally {
      setReportsLoading(false);
    }
  };

  const handleExecuteQuery = async () => {
    if (selectedMetrics.length === 0) return;
    setQueryLoading(true);
    setQueryError(null);
    try {
      const response = await analyticsAPI.executeQuery({
        metrics: selectedMetrics,
        dimensions: selectedDimensions,
        filters,
      });
      setQueryResult(response.data);
    } catch (error: any) {
      setQueryError(error?.message || 'Query execution failed');
    } finally {
      setQueryLoading(false);
    }
  };

  const handleSaveReport = async () => {
    if (!reportName.trim() || selectedMetrics.length === 0) return;
    try {
      await analyticsAPI.saveReport({
        name: reportName,
        query: {
          metrics: selectedMetrics,
          dimensions: selectedDimensions,
          filters,
        },
      });
      setReportName('');
      fetchSavedReports();
    } catch (error) {
      console.error('Failed to save report:', error);
    }
  };

  const toggleMetricSelection = (metricId: string) => {
    setSelectedMetrics((prev) =>
      prev.includes(metricId) ? prev.filter((id) => id !== metricId) : [...prev, metricId]
    );
  };

  const toggleDimensionSelection = (dimId: string) => {
    setSelectedDimensions((prev) =>
      prev.includes(dimId) ? prev.filter((id) => id !== dimId) : [...prev, dimId]
    );
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

  const getAggregationIcon = (agg: string) => {
    switch (agg?.toLowerCase()) {
      case 'sum':
        return <Calculator className="h-4 w-4" />;
      case 'count':
        return <Hash className="h-4 w-4" />;
      case 'avg':
      case 'average':
        return <BarChart3 className="h-4 w-4" />;
      case 'min':
      case 'max':
        return <ToggleLeft className="h-4 w-4" />;
      default:
        return <Database className="h-4 w-4" />;
    }
  };

  const getCardinalityColor = (cardinality: string) => {
    switch (cardinality?.toLowerCase()) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'secondary';
      case 'low':
        return 'outline';
      default:
        return 'default';
    }
  };

  const filteredMetrics = metrics.filter(
    (m) =>
      m.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.category?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredDimensions = dimensions.filter(
    (d) =>
      d.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const renderSkeletons = (count: number) => (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center gap-3">
              <Skeleton className="h-10 w-10 rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-2/3" />
          </CardContent>
        </Card>
      ))}
    </div>
  );

  const renderError = (message: string, onRetry: () => void) => (
    <Card className="flex items-center justify-center py-12">
      <div className="text-center">
        <AlertTriangle className="h-10 w-10 text-destructive mx-auto mb-3" />
        <p className="text-sm font-medium mb-1">Something went wrong</p>
        <p className="text-xs text-muted-foreground mb-4">{message}</p>
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
          Retry
        </Button>
      </div>
    </Card>
  );

  const renderEmpty = (icon: React.ReactNode, title: string, description: string) => (
    <Card className="flex items-center justify-center py-12">
      <div className="text-center">
        <div className="text-muted-foreground mx-auto mb-3">{icon}</div>
        <p className="text-sm font-medium mb-1">{title}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
    </Card>
  );

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <BarChart3 className="h-8 w-8 text-primary" />
              Analytics Studio
            </h1>
            <p className="text-muted-foreground">
              Explore metrics, dimensions, and build custom queries
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 w-64"
              />
            </div>
            <Button variant="outline" onClick={() => { fetchMetrics(); fetchDimensions(); fetchSavedReports(); }}>
              <RefreshCw className="h-4 w-4 mr-1.5" />
              Refresh
            </Button>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="metrics" className="gap-1.5">
              <BarChart3 className="h-4 w-4" />
              Metrics
              {metrics.length > 0 && (
                <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-[10px]">
                  {metrics.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="dimensions" className="gap-1.5">
              <Layers className="h-4 w-4" />
              Dimensions
              {dimensions.length > 0 && (
                <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-[10px]">
                  {dimensions.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="query" className="gap-1.5">
              <Database className="h-4 w-4" />
              Query Builder
            </TabsTrigger>
            <TabsTrigger value="reports" className="gap-1.5">
              <FileText className="h-4 w-4" />
              Saved Reports
            </TabsTrigger>
          </TabsList>

          <TabsContent value="metrics" className="space-y-4">
            {metricsLoading ? (
              renderSkeletons(6)
            ) : metricsError ? (
              renderError(metricsError, fetchMetrics)
            ) : filteredMetrics.length === 0 ? (
              renderEmpty(
                <BarChart3 className="h-10 w-10" />,
                'No Metrics Found',
                searchTerm ? 'Try a different search term' : 'No metrics have been created yet'
              )
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {filteredMetrics.map((metric) => (
                  <Card
                    key={metric.id}
                    className={`cursor-pointer transition-all hover:shadow-md ${
                      selectedMetrics.includes(metric.id) ? 'ring-2 ring-primary' : ''
                    }`}
                    onClick={() => toggleMetricSelection(metric.id)}
                  >
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                          {getAggregationIcon(metric.aggregation)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{metric.name}</p>
                          <p className="text-xs text-muted-foreground truncate">
                            {metric.category}
                          </p>
                        </div>
                        {selectedMetrics.includes(metric.id) && (
                          <Badge className="h-5 px-1.5">Selected</Badge>
                        )}
                      </div>
                      {metric.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {metric.description}
                        </p>
                      )}
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className="text-[10px]">
                          {metric.aggregation?.toUpperCase()}
                        </Badge>
                        {metric.format && (
                          <Badge variant="secondary" className="text-[10px]">
                            {metric.format}
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="dimensions" className="space-y-4">
            {dimensionsLoading ? (
              renderSkeletons(6)
            ) : dimensionsError ? (
              renderError(dimensionsError, fetchDimensions)
            ) : filteredDimensions.length === 0 ? (
              renderEmpty(
                <Layers className="h-10 w-10" />,
                'No Dimensions Found',
                searchTerm ? 'Try a different search term' : 'No dimensions have been created yet'
              )
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {filteredDimensions.map((dim) => (
                  <Card
                    key={dim.id}
                    className={`cursor-pointer transition-all hover:shadow-md ${
                      selectedDimensions.includes(dim.id) ? 'ring-2 ring-primary' : ''
                    }`}
                    onClick={() => toggleDimensionSelection(dim.id)}
                  >
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-secondary/50 flex items-center justify-center text-secondary-foreground">
                          <Type className="h-5 w-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{dim.name}</p>
                          {dim.source_table && (
                            <p className="text-xs text-muted-foreground truncate">
                              {dim.source_table}
                            </p>
                          )}
                        </div>
                        {selectedDimensions.includes(dim.id) && (
                          <Badge className="h-5 px-1.5">Selected</Badge>
                        )}
                      </div>
                      {dim.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {dim.description}
                        </p>
                      )}
                      <div className="flex items-center gap-2">
                        <Badge variant={getCardinalityColor(dim.cardinality) as any} className="text-[10px]">
                          {dim.cardinality} cardinality
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="query" className="space-y-4">
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-1 space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Selected Metrics</CardTitle>
                    <CardDescription>
                      {selectedMetrics.length} metric{selectedMetrics.length !== 1 ? 's' : ''} selected
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {selectedMetrics.length === 0 ? (
                      <p className="text-xs text-muted-foreground py-4 text-center">
                        Click metrics in the Metrics tab to select them
                      </p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {selectedMetrics.map((id) => {
                          const m = metrics.find((x) => x.id === id);
                          return m ? (
                            <Badge
                              key={id}
                              variant="secondary"
                              className="gap-1 cursor-pointer hover:bg-destructive/10 hover:text-destructive"
                              onClick={() => toggleMetricSelection(id)}
                            >
                              {m.name}
                              <span className="text-[10px]">×</span>
                            </Badge>
                          ) : null;
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Selected Dimensions</CardTitle>
                    <CardDescription>
                      {selectedDimensions.length} dimension{selectedDimensions.length !== 1 ? 's' : ''} selected
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {selectedDimensions.length === 0 ? (
                      <p className="text-xs text-muted-foreground py-4 text-center">
                        Click dimensions in the Dimensions tab to select them
                      </p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {selectedDimensions.map((id) => {
                          const d = dimensions.find((x) => x.id === id);
                          return d ? (
                            <Badge
                              key={id}
                              variant="secondary"
                              className="gap-1 cursor-pointer hover:bg-destructive/10 hover:text-destructive"
                              onClick={() => toggleDimensionSelection(id)}
                            >
                              {d.name}
                              <span className="text-[10px]">×</span>
                            </Badge>
                          ) : null;
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>

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
                      <p className="text-xs text-muted-foreground py-4 text-center">
                        No filters applied
                      </p>
                    ) : (
                      filters.map((filter, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <Input
                            placeholder="Field"
                            value={filter.field}
                            onChange={(e) => updateFilter(idx, 'field', e.target.value)}
                            className="flex-1 h-7 text-xs"
                          />
                          <Select
                            value={filter.operator}
                            onValueChange={(val) => val && updateFilter(idx, 'operator', val)}
                          >
                            <SelectTrigger className="w-24 h-7 text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="equals">Equals</SelectItem>
                              <SelectItem value="not_equals">Not Equals</SelectItem>
                              <SelectItem value="greater_than">Greater Than</SelectItem>
                              <SelectItem value="less_than">Less Than</SelectItem>
                              <SelectItem value="contains">Contains</SelectItem>
                            </SelectContent>
                          </Select>
                          <Input
                            placeholder="Value"
                            value={filter.value}
                            onChange={(e) => updateFilter(idx, 'value', e.target.value)}
                            className="flex-1 h-7 text-xs"
                          />
                          <Button
                            variant="ghost"
                            size="icon-xs"
                            onClick={() => removeFilter(idx)}
                          >
                            ×
                          </Button>
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>

                <div className="flex gap-2">
                  <Button
                    className="flex-1"
                    onClick={handleExecuteQuery}
                    disabled={selectedMetrics.length === 0 || queryLoading}
                  >
                    {queryLoading ? (
                      <RefreshCw className="h-4 w-4 mr-1.5 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4 mr-1.5" />
                    )}
                    Execute
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleSaveReport}
                    disabled={selectedMetrics.length === 0 || !reportName.trim()}
                  >
                    <Save className="h-4 w-4 mr-1.5" />
                    Save
                  </Button>
                </div>
                <Input
                  placeholder="Report name..."
                  value={reportName}
                  onChange={(e) => setReportName(e.target.value)}
                />
              </div>

              <div className="lg:col-span-2">
                {queryLoading ? (
                  <Card className="min-h-[300px] flex items-center justify-center">
                    <div className="text-center">
                      <RefreshCw className="h-8 w-8 text-muted-foreground animate-spin mx-auto mb-3" />
                      <p className="text-sm text-muted-foreground">Executing query...</p>
                    </div>
                  </Card>
                ) : queryError ? (
                  renderError(queryError, handleExecuteQuery)
                ) : queryResult ? (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Query Results</CardTitle>
                      <CardDescription>
                        {queryResult.row_count || queryResult.rows?.length || 0} rows returned
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {queryResult.rows && queryResult.rows.length > 0 ? (
                        <div className="overflow-x-auto">
                          <Table>
                            <TableHeader>
                              <TableRow>
                                {queryResult.columns?.map((col: string, i: number) => (
                                  <TableHead key={i}>{col}</TableHead>
                                )) ||
                                  Object.keys(queryResult.rows[0]).map((key) => (
                                    <TableHead key={key}>{key}</TableHead>
                                  ))}
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {queryResult.rows.map((row: any, i: number) => (
                                <TableRow key={i}>
                                  {Object.values(row).map((val, j) => (
                                    <TableCell key={j}>
                                      {val === null ? (
                                        <span className="text-muted-foreground">—</span>
                                      ) : typeof val === 'number' ? (
                                        val.toLocaleString()
                                      ) : (
                                        String(val)
                                      )}
                                    </TableCell>
                                  ))}
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </div>
                      ) : (
                        <p className="text-center text-muted-foreground py-8">
                          No data returned
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ) : (
                  <Card className="min-h-[300px] flex items-center justify-center">
                    <div className="text-center">
                      <Database className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
                      <p className="text-sm font-medium">Query Builder</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Select metrics and dimensions, then execute your query
                      </p>
                    </div>
                  </Card>
                )}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="reports" className="space-y-4">
            {reportsLoading ? (
              renderSkeletons(4)
            ) : reportsError ? (
              renderError(reportsError, fetchSavedReports)
            ) : savedReports.length === 0 ? (
              renderEmpty(
                <FileText className="h-10 w-10" />,
                'No Saved Reports',
                'Execute a query and save it to create your first report'
              )
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {savedReports.map((report) => (
                  <Card key={report.id} className="hover:shadow-md transition-all">
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                          <FileText className="h-5 w-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{report.name}</p>
                          {report.created_at && (
                            <p className="text-xs text-muted-foreground">
                              {new Date(report.created_at).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                      {report.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {report.description}
                        </p>
                      )}
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={() => {
                            if (report.query) {
                              setSelectedMetrics(report.query.metrics || []);
                              setSelectedDimensions(report.query.dimensions || []);
                              setFilters(report.query.filters || []);
                              setActiveTab('query');
                            }
                          }}
                        >
                          Load
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
