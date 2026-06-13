'use client';

import { useState, useEffect, useCallback } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import {
  Building2, TrendingUp, TrendingDown, Users,
  DollarSign, RefreshCw, Sparkles, Activity,
} from 'lucide-react';
import { kpiAPI, aiEverywhereAPI } from '@/lib/api/client';
import { DepartmentPerformanceChart } from '@/components/charts/DepartmentPerformanceChart';
import { RevenueCompositionChart } from '@/components/charts/RevenueCompositionChart';
import { formatCurrency } from '@/lib/utils/format';

interface DeptData {
  name: string;
  revenue: number;
  transaction_count: number;
}

export default function DepartmentsPage() {
  const [departments, setDepartments] = useState<DeptData[]>([]);
  const [loading, setLoading] = useState(true);
  const [aiSummary, setAISummary] = useState<string>('');
  const [loadingAI, setLoadingAI] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await kpiAPI.getRevenueByDepartment();
      const depts = res.data.departments || [];
      setDepartments(depts);
      // Trigger AI summary
      if (depts.length > 0) {
        setLoadingAI(true);
        try {
          const aiRes = await aiEverywhereAPI.ask({
            question: `Analyze the department revenue performance. Top: ${depts[0]?.name} (${formatCurrency(depts[0]?.revenue, true)}). Bottom: ${depts[depts.length - 1]?.name}. Provide 2-3 sentences on performance spread, top performers, and one specific recommendation.`,
            page_context: { page: 'departments', metrics: ['revenue_by_department'] },
          });
          const text = aiRes.data?.answer || aiRes.data?.response || aiRes.data || '';
          setAISummary(typeof text === 'string' ? text : JSON.stringify(text));
        } catch {
          setAISummary('');
        } finally {
          setLoadingAI(false);
        }
      }
    } catch (err) {
      console.error('Departments fetch failed:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const totalRevenue = departments.reduce((s, d) => s + d.revenue, 0);
  const totalTransactions = departments.reduce((s, d) => s + d.transaction_count, 0);
  const avgRevenue = departments.length > 0 ? totalRevenue / departments.length : 0;

  const DEPT_COLORS = [
    '#6366f1', '#22d3ee', '#10b981', '#f59e0b',
    '#f43f5e', '#a78bfa', '#34d399', '#fb923c',
  ];

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                <Building2 className="h-5 w-5 text-white" />
              </div>
              Department Performance
            </h1>
            <p className="text-muted-foreground mt-1">
              Revenue analytics, efficiency metrics, and performance rankings by department
            </p>
          </div>
          <Button size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <Separator />

        {/* Summary KPI tiles */}
        <div className="grid gap-4 md:grid-cols-4">
          {[
            { label: 'Total Departments', value: loading ? null : departments.length, icon: Building2, color: 'text-indigo-400' },
            { label: 'Total Revenue', value: loading ? null : formatCurrency(totalRevenue, true), icon: DollarSign, color: 'text-emerald-400' },
            { label: 'Avg Dept Revenue', value: loading ? null : formatCurrency(avgRevenue, true), icon: TrendingUp, color: 'text-cyan-400' },
            { label: 'Total Transactions', value: loading ? null : totalTransactions.toLocaleString(), icon: Users, color: 'text-purple-400' },
          ].map((tile) => (
            <Card key={tile.label}>
              <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-sm font-medium text-muted-foreground">{tile.label}</CardTitle>
                <tile.icon className={`h-4 w-4 ${tile.color}`} />
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-7 w-28" />
                ) : (
                  <div className="text-2xl font-bold">{tile.value}</div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Charts row */}
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <Activity className="h-4 w-4 text-indigo-400" />
                Revenue Ranking by Department
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-[300px] w-full" />
              ) : departments.length > 0 ? (
                <DepartmentPerformanceChart
                  data={departments.map((d) => ({ name: d.name, value: d.revenue }))}
                  height={300}
                />
              ) : (
                <div className="h-[300px] flex items-center justify-center text-sm text-muted-foreground">
                  No department data — seed the database
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <DollarSign className="h-4 w-4 text-cyan-400" />
                Revenue Share by Department
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-[300px] w-full" />
              ) : departments.length > 0 ? (
                <RevenueCompositionChart
                  data={departments.map((d) => ({ name: d.name, value: d.revenue }))}
                  height={300}
                  metric="Revenue"
                />
              ) : (
                <div className="h-[300px] flex items-center justify-center text-sm text-muted-foreground">
                  No department data
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* AI Summary */}
        {(aiSummary || loadingAI) && (
          <Card className="border-indigo-500/20 bg-indigo-500/5">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-400" />
                AI Department Analysis
                {loadingAI && <Badge variant="outline" className="text-xs animate-pulse">Generating…</Badge>}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loadingAI ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-4/5" />
                </div>
              ) : (
                <p className="text-sm text-muted-foreground leading-relaxed">{aiSummary}</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Department table */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold">Department Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {loading
                ? Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="grid grid-cols-5 gap-4 p-3 rounded-lg bg-muted/40">
                      {Array.from({ length: 5 }).map((_, j) => (
                        <Skeleton key={j} className="h-4" />
                      ))}
                    </div>
                  ))
                : departments.map((dept, idx) => {
                    const pct = totalRevenue > 0 ? (dept.revenue / totalRevenue) * 100 : 0;
                    const vsAvg = avgRevenue > 0 ? ((dept.revenue - avgRevenue) / avgRevenue) * 100 : 0;
                    const isAboveAvg = vsAvg >= 0;

                    return (
                      <div
                        key={dept.name}
                        className="grid grid-cols-5 items-center gap-4 p-3 rounded-lg bg-muted/40 hover:bg-muted/70 transition-colors"
                      >
                        <div className="col-span-2 flex items-center gap-2">
                          <div
                            className="h-3 w-3 rounded-full flex-shrink-0"
                            style={{ backgroundColor: DEPT_COLORS[idx % DEPT_COLORS.length] }}
                          />
                          <span className="text-sm font-medium">{dept.name}</span>
                        </div>
                        <div className="text-sm font-semibold">{formatCurrency(dept.revenue, true)}</div>
                        <div className="flex items-center gap-1.5">
                          <Progress value={pct} className="h-1.5 flex-1" />
                          <span className="text-xs text-muted-foreground w-8">{pct.toFixed(0)}%</span>
                        </div>
                        <div className="flex items-center gap-1">
                          {isAboveAvg ? (
                            <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                          ) : (
                            <TrendingDown className="h-3.5 w-3.5 text-red-400" />
                          )}
                          <span
                            className={`text-xs font-medium ${isAboveAvg ? 'text-emerald-400' : 'text-red-400'}`}
                          >
                            {isAboveAvg ? '+' : ''}{vsAvg.toFixed(1)}% vs avg
                          </span>
                        </div>
                      </div>
                    );
                  })}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
