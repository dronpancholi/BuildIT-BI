'use client';

import { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { KPICard } from '@/components/kpi/kpi-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Building,
  RefreshCw,
  Download,
  Filter,
} from 'lucide-react';
import { kpiAPI } from '@/lib/api/client';
import { KPIMetric } from '@/lib/types';
import { formatCurrency } from '@/lib/utils/format';

interface DepartmentRevenue {
  name: string;
  revenue: number;
  transaction_count: number;
}

interface PayerRevenue {
  name: string;
  payer_type: string;
  revenue: number;
  percentage: number;
  transaction_count: number;
}

export default function RevenuePage() {
  const [revenueKPIs, setRevenueKPIs] = useState<Record<string, KPIMetric>>({});
  const [departments, setDepartments] = useState<DepartmentRevenue[]>([]);
  const [payers, setPayers] = useState<PayerRevenue[]>([]);
  const [loadingDepartments, setLoadingDepartments] = useState(false);
  const [loadingPayers, setLoadingPayers] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchRevenueData = async () => {
    try {
      const response = await kpiAPI.getRevenueKPIs();
      setRevenueKPIs(response.data);
    } catch (error) {
      console.error('Failed to fetch revenue data:', error);
    }
  };

  const fetchRevenueByDepartment = async () => {
    setLoadingDepartments(true);
    try {
      const response = await kpiAPI.getRevenueByDepartment();
      setDepartments(response.data.departments || []);
    } catch (error) {
      console.error('Failed to fetch revenue by department:', error);
    } finally {
      setLoadingDepartments(false);
    }
  };

  const fetchRevenueByPayer = async () => {
    setLoadingPayers(true);
    try {
      const response = await kpiAPI.getRevenueByPayer();
      setPayers(response.data.payers || []);
    } catch (error) {
      console.error('Failed to fetch revenue by payer:', error);
    } finally {
      setLoadingPayers(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchRevenueData();
  }, []);

  useEffect(() => {
    if (activeTab === 'by-department' && departments.length === 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      fetchRevenueByDepartment();
    }
    if (activeTab === 'by-payer' && payers.length === 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      fetchRevenueByPayer();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <TrendingUp className="h-8 w-8 text-healthcare-green" />
              Revenue Intelligence
            </h1>
            <p className="text-muted-foreground">
              Deep analysis of revenue streams, trends, and opportunities
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button size="sm" onClick={fetchRevenueData}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        <Separator />

        {/* Revenue KPIs */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Object.entries(revenueKPIs).map(([code, metric]) => (
            <KPICard key={code} metric={metric} />
          ))}
        </div>

        {/* Revenue Analysis Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="by-department" className="flex items-center gap-2">
              <Building className="h-4 w-4" />
              By Department
            </TabsTrigger>
            <TabsTrigger value="by-payer" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              By Payer
            </TabsTrigger>
            <TabsTrigger value="trends" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Trends
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Revenue Trend Chart Placeholder */}
              <Card>
                <CardHeader>
                  <CardTitle>Revenue Trend</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-[300px] flex items-center justify-center bg-muted/50 rounded-lg">
                    <div className="text-center">
                      <TrendingUp className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">Revenue trend chart will be displayed here</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        Connect ECharts to visualize data
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Revenue Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle>Revenue Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-[300px] flex items-center justify-center bg-muted/50 rounded-lg">
                    <div className="text-center">
                      <DollarSign className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">Revenue breakdown chart will be displayed here</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        Pie/donut chart for revenue composition
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Revenue Insights */}
            <Card>
              <CardHeader>
                <CardTitle>Revenue Insights</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-healthcare-green/10 border border-healthcare-green/20">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-healthcare-green" />
                    <h4 className="font-medium text-healthcare-green">Positive Trend</h4>
                  </div>
                  <p className="text-sm mt-2">
                    Revenue has increased by 8.3% compared to the previous period, driven primarily by
                    growth in surgical services and cardiology.
                  </p>
                </div>

                <div className="p-4 rounded-lg bg-healthcare-amber/10 border border-healthcare-amber/20">
                  <div className="flex items-center gap-2">
                    <TrendingDown className="h-5 w-5 text-healthcare-amber" />
                    <h4 className="font-medium text-healthcare-amber">Payer Mix Shift</h4>
                  </div>
                  <p className="text-sm mt-2">
                    Medicaid volume has increased by 5.2%, which may impact overall reimbursement rates.
                    Consider negotiating better rates with Medicaid.
                  </p>
                </div>

                <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5 text-primary" />
                    <h4 className="font-medium text-primary">Opportunity</h4>
                  </div>
                  <p className="text-sm mt-2">
                    Outpatient services show strong growth potential. Expanding ambulatory surgery
                    could generate an additional $2.1M annually.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="by-department" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Revenue by Department</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {loadingDepartments ? (
                    Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                        <div>
                          <Skeleton className="h-4 w-48" />
                          <Skeleton className="h-3 w-32 mt-2" />
                        </div>
                        <Skeleton className="h-5 w-24" />
                      </div>
                    ))
                  ) : departments.length > 0 ? (
                    departments.map((dept) => (
                      <div key={dept.name} className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                        <div>
                          <p className="font-medium">{dept.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {formatCurrency(dept.revenue, true)}
                          </p>
                        </div>
                        <Button variant="outline" size="sm" onClick={fetchRevenueByDepartment}>
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Building className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No department revenue data available</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="by-payer" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Revenue by Payer</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {loadingPayers ? (
                    Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Skeleton className="h-4 w-48" />
                          <Skeleton className="h-3 w-32" />
                        </div>
                        <Skeleton className="h-2 w-full" />
                      </div>
                    ))
                  ) : payers.length > 0 ? (
                    payers.map((payer) => (
                      <div key={payer.name} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <p className="font-medium">{payer.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {formatCurrency(payer.revenue, true)}
                          </p>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary"
                            style={{ width: `${payer.percentage}%` }}
                          />
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No payer revenue data available</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trends" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Revenue Trends Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[400px] flex items-center justify-center bg-muted/50 rounded-lg">
                  <div className="text-center">
                    <TrendingUp className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">Revenue trend analysis chart</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Time series visualization with forecasts
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
