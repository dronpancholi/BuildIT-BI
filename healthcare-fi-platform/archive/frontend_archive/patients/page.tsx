'use client';

import { useState, useEffect, useCallback } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import {
  Users, Activity, TrendingUp, TrendingDown,
  RefreshCw, Sparkles, UserPlus, UserMinus, Clock
} from 'lucide-react';
import { aiEverywhereAPI } from '@/lib/api/client';
import { RevenueTimelineChart } from '@/components/charts/RevenueTimelineChart';

// Mock data for patient volume and metrics
const PATIENT_METRICS = {
  total_admissions: { value: 12450, prev: 11800, change: 5.5 },
  total_discharges: { value: 12100, prev: 11600, change: 4.3 },
  average_length_of_stay: { value: 4.2, prev: 4.5, change: -6.7 },
  readmission_rate: { value: 11.2, prev: 12.5, change: -10.4 },
};

function buildVolumeTrend(currentVolume: number) {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const now = new Date();
  return Array.from({ length: 12 }, (_, i) => {
    const monthIdx = (now.getMonth() - 11 + i + 12) % 12;
    const base = currentVolume * (1 - (11 - i) * 0.02);
    const noise = (Math.random() * 0.1 - 0.05);
    return { date: months[monthIdx], value: Math.round(base * (1 + noise)) };
  });
}

export default function PatientsPage() {
  const [loading, setLoading] = useState(true);
  const [aiSummary, setAISummary] = useState('');
  const [loadingAI, setLoadingAI] = useState(false);
  const [trendData, setTrendData] = useState<Array<{ date: string; value: number }>>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 600));
    setTrendData(buildVolumeTrend(1100)); // monthly average ~1100
    setLoading(false);

    setLoadingAI(true);
    try {
      const aiRes = await aiEverywhereAPI.ask({
        question: 'Provide a 2-3 sentence analysis of patient volume and length of stay (ALOS). Mention the positive trend in reduced readmissions and any potential capacity impact.',
        page_context: { 
          page: 'patients', 
          metrics: ['total_admissions', 'average_length_of_stay', 'readmission_rate'],
          filters: {
            alos: PATIENT_METRICS.average_length_of_stay.value,
            readmission: PATIENT_METRICS.readmission_rate.value
          }
        },
      });
      const text = aiRes.data?.answer || aiRes.data?.response || aiRes.data || '';
      setAISummary(typeof text === 'string' ? text : '');
    } catch { 
      setAISummary('Patient volumes are up 5.5% YoY, but capacity strain is offset by a 6.7% reduction in Average Length of Stay (ALOS). Additionally, the 30-day readmission rate has improved to 11.2%, indicating better care outcomes and discharge planning.'); 
    }
    finally { setLoadingAI(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center">
                <Users className="h-5 w-5 text-white" />
              </div>
              Patient Analytics
            </h1>
            <p className="text-muted-foreground mt-1">
              Analyze patient volumes, admission/discharge flows, and length of stay metrics
            </p>
          </div>
          <Button size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <Separator />

        {/* Summary KPIs */}
        <div className="grid gap-4 md:grid-cols-4">
          {[
            { label: 'Total Admissions (YTD)', value: PATIENT_METRICS.total_admissions.value.toLocaleString(), icon: UserPlus, sub: `${PATIENT_METRICS.total_admissions.change}% vs prev`, trend: 'up' },
            { label: 'Total Discharges (YTD)', value: PATIENT_METRICS.total_discharges.value.toLocaleString(), icon: UserMinus, sub: `${PATIENT_METRICS.total_discharges.change}% vs prev`, trend: 'up' },
            { label: 'Average Length of Stay', value: `${PATIENT_METRICS.average_length_of_stay.value} days`, icon: Clock, sub: `${Math.abs(PATIENT_METRICS.average_length_of_stay.change)}% vs prev`, trend: 'down' },
            { label: '30-Day Readmission Rate', value: `${PATIENT_METRICS.readmission_rate.value}%`, icon: Activity, sub: `${Math.abs(PATIENT_METRICS.readmission_rate.change)}% vs prev`, trend: 'down' },
          ].map((tile) => (
            <Card key={tile.label}>
              <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-sm font-medium text-muted-foreground">{tile.label}</CardTitle>
                <tile.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-7 w-24" />
                ) : (
                  <div>
                    <div className="text-2xl font-bold">{tile.value}</div>
                    <div className="flex items-center gap-1 text-xs mt-1">
                      {tile.trend === 'up' ? <TrendingUp className="h-3 w-3 text-emerald-500" /> : <TrendingDown className="h-3 w-3 text-emerald-500" />}
                      <span className="text-emerald-500 font-medium">{tile.sub}</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* AI Summary */}
          <Card className="lg:col-span-1 border-indigo-500/20 bg-indigo-500/5">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-400" />
                AI Volume Analysis
                {loadingAI && <Badge variant="outline" className="text-xs animate-pulse">Analyzing…</Badge>}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loadingAI ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
              ) : (
                <p className="text-sm text-muted-foreground leading-relaxed">{aiSummary}</p>
              )}
            </CardContent>
          </Card>

          {/* Timeline Chart */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-blue-400" />
                Monthly Admission Volume — 12 Month Trend
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-[280px] w-full" />
              ) : (
                <RevenueTimelineChart
                  data={trendData}
                  height={280}
                  color="#3b82f6"
                />
              )}
            </CardContent>
          </Card>
        </div>

      </div>
    </DashboardLayout>
  );
}
