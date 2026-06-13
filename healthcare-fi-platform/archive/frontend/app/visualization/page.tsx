'use client';

import React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { visualizationAPI } from '@/lib/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Palette,
  BarChart3,
  Plus,
  Eye,
  RefreshCw,
  Layers,
  Grid3X3,
  Paintbrush,
  AlertTriangle,
  CheckCircle,
  Activity,
  PieChart,
  TrendingUp,
  GitBranch,
  AreaChart,
} from 'lucide-react';

interface ChartType {
  id: string;
  name: string;
  description: string;
  category: string;
  icon?: string;
}

interface ColorScheme {
  id: string;
  name: string;
  colors: string[];
  description: string;
}

interface ChartSpec {
  id?: string;
  chart_type: string;
  title: string;
  metrics: string[];
  dimensions: string[];
  color_scheme: string;
  filters?: Record<string, any>;
}

const CHART_CATEGORIES: Record<string, React.ElementType> = {
  bar: BarChart3,
  line: TrendingUp,
  pie: PieChart,
  area: AreaChart,
  scatter: Grid3X3,
  treemap: Layers,
  sankey: GitBranch,
};

function ChartTypeSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="pt-6">
            <div className="space-y-3">
              <Skeleton className="h-10 w-10 rounded-lg" />
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-3/4" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function BuilderSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-4">
        <Card>
          <CardContent className="pt-6 space-y-4">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
      <div className="space-y-4">
        <Card>
          <CardContent className="pt-6 space-y-3">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-24 w-full rounded-lg" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function VisualizationPage() {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [chartTypes, setChartTypes] = React.useState<ChartType[]>([]);
  const [colorSchemes, setColorSchemes] = React.useState<ColorScheme[]>([]);
  const [selectedChartType, setSelectedChartType] = React.useState('');
  const [specTitle, setSpecTitle] = React.useState('');
  const [specMetrics, setSpecMetrics] = React.useState('');
  const [specDimensions, setSpecDimensions] = React.useState('');
  const [selectedColorScheme, setSelectedColorScheme] = React.useState('');
  const [previewing, setPreviewing] = React.useState(false);
  const [savedSpec, setSavedSpec] = React.useState<ChartSpec | null>(null);

  React.useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [typesRes, schemesRes] = await Promise.all([
        visualizationAPI.getChartTypes(),
        visualizationAPI.getColorSchemes(),
      ]);
      setChartTypes(typesRes.data.chart_types || typesRes.data || []);
      setColorSchemes(schemesRes.data.color_schemes || schemesRes.data || []);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load visualization data');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSpec = async () => {
    setPreviewing(true);
    try {
      const spec: ChartSpec = {
        chart_type: selectedChartType,
        title: specTitle,
        metrics: specMetrics ? specMetrics.split(',').map(m => m.trim()) : [],
        dimensions: specDimensions ? specDimensions.split(',').map(d => d.trim()) : [],
        color_scheme: selectedColorScheme,
      };
      const res = await visualizationAPI.createSpec(spec);
      setSavedSpec({ ...spec, id: res.data.id || res.data.spec_id });
    } catch (err) {
      console.error('Failed to save spec:', err);
    } finally {
      setPreviewing(false);
    }
  };

  const handleRenderSpec = async () => {
    if (!savedSpec?.id) return;
    setPreviewing(true);
    try {
      await visualizationAPI.renderSpec(savedSpec.id);
    } catch (err) {
      console.error('Failed to render spec:', err);
    } finally {
      setPreviewing(false);
    }
  };

  const getChartIcon = (type: string): React.ElementType => {
    const key = type.toLowerCase();
    for (const [cat, Icon] of Object.entries(CHART_CATEGORIES)) {
      if (key.includes(cat)) return Icon;
    }
    return BarChart3;
  };

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Palette className="h-8 w-8 text-primary" />
              Visualization Library
            </h1>
            <p className="text-muted-foreground">
              19 chart types, spec builder, and color schemes for data visualization
            </p>
          </div>
          <Button onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <Separator />

        {error && (
          <Card className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
                <AlertTriangle className="h-4 w-4" />
                <p className="text-sm font-medium">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        <div>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Chart Types ({chartTypes.length})
          </h2>
          {loading ? (
            <ChartTypeSkeleton />
          ) : chartTypes.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-12">
                  <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium">No Chart Types Available</h3>
                  <p className="text-muted-foreground mt-1">
                    Chart types will appear once the visualization service is configured
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {chartTypes.map(chartType => {
                const ChartIcon = getChartIcon(chartType.name || chartType.id);
                const isSelected = selectedChartType === (chartType.id || chartType.name);
                return (
                  <Card
                    key={chartType.id}
                    className={`cursor-pointer transition-all hover:ring-2 hover:ring-primary/50 ${
                      isSelected ? 'ring-2 ring-primary bg-primary/5' : ''
                    }`}
                    onClick={() => setSelectedChartType(chartType.id || chartType.name)}
                  >
                    <CardContent className="pt-6">
                      <div className="space-y-2">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <ChartIcon className="h-5 w-5 text-primary" />
                        </div>
                        <h3 className="font-medium text-sm">{chartType.name}</h3>
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {chartType.description}
                        </p>
                        {chartType.category && (
                          <Badge variant="secondary" className="text-[10px]">
                            {chartType.category}
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        <Separator />

        <div>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Chart Spec Builder
          </h2>
          {loading ? (
            <BuilderSkeleton />
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Configure Visualization</CardTitle>
                    <CardDescription>
                      Select chart type, metrics, dimensions, and color scheme
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Chart Type</Label>
                      <Select value={selectedChartType} onValueChange={(val) => setSelectedChartType(val ?? '')}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select a chart type" />
                        </SelectTrigger>
                        <SelectContent>
                          {chartTypes.map(ct => (
                            <SelectItem key={ct.id || ct.name} value={ct.id || ct.name}>
                              {ct.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="spec_title">Title</Label>
                      <Input
                        id="spec_title"
                        value={specTitle}
                        onChange={e => setSpecTitle(e.target.value)}
                        placeholder="e.g. Monthly Revenue by Department"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="spec_metrics">Metrics (comma-separated)</Label>
                      <Input
                        id="spec_metrics"
                        value={specMetrics}
                        onChange={e => setSpecMetrics(e.target.value)}
                        placeholder="e.g. revenue, profit_margin, patient_count"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="spec_dimensions">Dimensions (comma-separated)</Label>
                      <Input
                        id="spec_dimensions"
                        value={specDimensions}
                        onChange={e => setSpecDimensions(e.target.value)}
                        placeholder="e.g. department, month, region"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Color Scheme</Label>
                      <Select value={selectedColorScheme} onValueChange={(val) => setSelectedColorScheme(val ?? '')}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select a color scheme" />
                        </SelectTrigger>
                        <SelectContent>
                          {colorSchemes.map(scheme => (
                            <SelectItem key={scheme.id} value={scheme.id}>
                              <div className="flex items-center gap-2">
                                <span>{scheme.name}</span>
                                <div className="flex gap-0.5">
                                  {scheme.colors.slice(0, 6).map((color, i) => (
                                    <div
                                      key={i}
                                      className="h-3 w-3 rounded-full border"
                                      style={{ backgroundColor: color }}
                                    />
                                  ))}
                                </div>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex gap-2 pt-2">
                      <Button
                        onClick={handleSaveSpec}
                        disabled={!selectedChartType || !specTitle}
                      >
                        <CheckCircle className="h-4 w-4 mr-2" />
                        {savedSpec?.id ? 'Update Spec' : 'Save Spec'}
                      </Button>
                      {savedSpec?.id && (
                        <Button
                          variant="outline"
                          onClick={handleRenderSpec}
                          disabled={previewing}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          {previewing ? 'Rendering...' : 'Preview'}
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {savedSpec && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Spec Output</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="bg-muted p-4 rounded-lg text-xs overflow-auto max-h-48">
                        {JSON.stringify(savedSpec, null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                )}
              </div>

              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Paintbrush className="h-4 w-4" />
                      Color Schemes
                    </CardTitle>
                    <CardDescription>{colorSchemes.length} available</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {loading ? (
                      <div className="space-y-3">
                        {Array.from({ length: 4 }).map((_, i) => (
                          <div key={i} className="space-y-2">
                            <Skeleton className="h-4 w-24" />
                            <div className="flex gap-1">
                              {Array.from({ length: 6 }).map((_, j) => (
                                <Skeleton key={j} className="h-6 w-6 rounded-full" />
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : colorSchemes.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        No color schemes available
                      </p>
                    ) : (
                      colorSchemes.map(scheme => (
                        <div
                          key={scheme.id}
                          className={`p-3 rounded-lg border cursor-pointer transition-all hover:bg-muted/50 ${
                            selectedColorScheme === scheme.id
                              ? 'border-primary bg-primary/5'
                              : ''
                          }`}
                          onClick={() => setSelectedColorScheme(scheme.id)}
                        >
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-sm font-medium">{scheme.name}</span>
                            {selectedColorScheme === scheme.id && (
                              <Badge variant="default" className="text-[10px]">Selected</Badge>
                            )}
                          </div>
                          <div className="flex gap-1">
                            {scheme.colors.map((color, i) => (
                              <div
                                key={i}
                                className="h-6 w-6 rounded-full border shadow-sm"
                                style={{ backgroundColor: color }}
                                title={color}
                              />
                            ))}
                          </div>
                          {scheme.description && (
                            <p className="text-xs text-muted-foreground mt-1.5">
                              {scheme.description}
                            </p>
                          )}
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Quick Reference</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-xs text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <BarChart3 className="h-3.5 w-3.5" />
                      <span>Bar charts for comparisons</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-3.5 w-3.5" />
                      <span>Line charts for trends over time</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <PieChart className="h-3.5 w-3.5" />
                      <span>Pie charts for proportions</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <AreaChart className="h-3.5 w-3.5" />
                      <span>Area charts for cumulative values</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Grid3X3 className="h-3.5 w-3.5" />
                      <span>Scatter plots for correlations</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Layers className="h-3.5 w-3.5" />
                      <span>Treemaps for hierarchical data</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <GitBranch className="h-3.5 w-3.5" />
                      <span>Sankey diagrams for flows</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
