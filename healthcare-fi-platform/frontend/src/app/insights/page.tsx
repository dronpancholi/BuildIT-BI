'use client';

import { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { AICFOChat } from '@/components/ai/ai-cfo-chat';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  Brain,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  RefreshCw,
  MessageSquare,
} from 'lucide-react';
import { insightsAPI } from '@/lib/api/client';
import { ComprehensiveInsights, Insight, Anomaly, Opportunity } from '@/lib/types';
import { getSeverityColor, formatPercentage } from '@/lib/utils/format';

export default function InsightsPage() {
  const [insights, setInsights] = useState<ComprehensiveInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const response = await insightsAPI.getComprehensiveInsights();
      setInsights(response.data);
    } catch (error) {
      console.error('Failed to fetch insights:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Brain className="h-8 w-8 text-primary" />
              AI Insights Engine
            </h1>
            <p className="text-muted-foreground">
              Intelligent analysis of your financial data with actionable recommendations
            </p>
          </div>
          <Button onClick={fetchInsights} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh Insights
          </Button>
        </div>

        <Separator />

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <Brain className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="anomalies" className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Anomalies
              {insights?.anomalies && insights.anomalies.length > 0 && (
                <Badge variant="destructive" className="ml-1 h-5 px-1.5">
                  {insights.anomalies.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="trends" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Trends
            </TabsTrigger>
            <TabsTrigger value="opportunities" className="flex items-center gap-2">
              <Lightbulb className="h-4 w-4" />
              Opportunities
            </TabsTrigger>
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              AI CFO Chat
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* Narrative Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-primary" />
                  Financial Intelligence Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground leading-relaxed text-lg">
                  {insights?.narrative || 'Loading insights...'}
                </p>
              </CardContent>
            </Card>

            {/* Summary Stats */}
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Anomalies Detected</p>
                      <p className="text-3xl font-bold text-healthcare-amber">
                        {insights?.summary?.anomaly_count || 0}
                      </p>
                    </div>
                    <div className="h-12 w-12 rounded-lg bg-healthcare-amber/10 flex items-center justify-center">
                      <AlertTriangle className="h-6 w-6 text-healthcare-amber" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Significant Trends</p>
                      <p className="text-3xl font-bold text-healthcare-blue">
                        {insights?.summary?.trend_count || 0}
                      </p>
                    </div>
                    <div className="h-12 w-12 rounded-lg bg-healthcare-blue/10 flex items-center justify-center">
                      <TrendingUp className="h-6 w-6 text-healthcare-blue" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Growth Opportunities</p>
                      <p className="text-3xl font-bold text-healthcare-green">
                        {insights?.summary?.opportunity_count || 0}
                      </p>
                    </div>
                    <div className="h-12 w-12 rounded-lg bg-healthcare-green/10 flex items-center justify-center">
                      <Lightbulb className="h-6 w-6 text-healthcare-green" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Quick Insights */}
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Key Trends</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {insights?.trends?.slice(0, 3).map((trend, index) => (
                    <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                      <div>
                        <p className="font-medium">{trend.kpi_name}</p>
                        <p className="text-sm text-muted-foreground">{trend.description}</p>
                      </div>
                      <Badge variant={trend.severity === 'warning' ? 'destructive' : 'secondary'}>
                        {trend.change_percent && trend.change_percent > 0 ? '+' : ''}
                        {formatPercentage(trend.change_percent || 0)}
                      </Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Top Opportunities</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {insights?.opportunities?.slice(0, 3).map((opp, index) => (
                    <div key={index} className="p-3 rounded-lg border border-primary/20 bg-primary/5">
                      <p className="font-medium">{opp.description}</p>
                      <p className="text-sm text-muted-foreground mt-1">{opp.recommendation}</p>
                      <Badge variant="outline" className="mt-2">
                        +{formatPercentage(opp.potential_improvement)} potential
                      </Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="anomalies" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-healthcare-amber" />
                  Detected Anomalies
                </CardTitle>
              </CardHeader>
              <CardContent>
                {insights?.anomalies && insights.anomalies.length > 0 ? (
                  <div className="space-y-4">
                    {insights.anomalies.map((anomaly, index) => (
                      <div
                        key={index}
                        className={`p-4 rounded-lg border ${getSeverityColor(anomaly.severity as any)}`}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium">{anomaly.description}</p>
                            <p className="text-sm mt-1 opacity-80">
                              Expected: ${anomaly.expected_amount.toLocaleString()} | 
                              Actual: ${anomaly.amount.toLocaleString()}
                            </p>
                          </div>
                          <Badge variant="outline">
                            Z-Score: {anomaly.z_score.toFixed(2)}
                          </Badge>
                        </div>
                        <p className="text-sm mt-2 opacity-80">
                          {new Date(anomaly.date).toLocaleDateString('en-US', {
                            weekday: 'long',
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                          })}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-muted-foreground py-8">
                    No anomalies detected in the current period
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trends" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-healthcare-blue" />
                  Significant Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                {insights?.trends && insights.trends.length > 0 ? (
                  <div className="space-y-4">
                    {insights.trends.map((trend, index) => (
                      <div key={index} className="p-4 rounded-lg border bg-muted/30">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium">{trend.kpi_name}</p>
                            <p className="text-sm text-muted-foreground mt-1">{trend.description}</p>
                          </div>
                          <div className="text-right">
                            <Badge variant={trend.severity === 'warning' ? 'destructive' : 'secondary'}>
                              {trend.change_percent && trend.change_percent > 0 ? '+' : ''}
                              {formatPercentage(trend.change_percent || 0)}
                            </Badge>
                            <p className="text-xs text-muted-foreground mt-1 capitalize">
                              {trend.trend_direction?.replace('_', ' ')}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-muted-foreground py-8">
                    No significant trends detected
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="opportunities" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5 text-healthcare-green" />
                  Growth Opportunities
                </CardTitle>
              </CardHeader>
              <CardContent>
                {insights?.opportunities && insights.opportunities.length > 0 ? (
                  <div className="space-y-4">
                    {insights.opportunities.map((opp, index) => (
                      <div key={index} className="p-4 rounded-lg border border-primary/20 bg-primary/5">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-medium">{opp.description}</p>
                            <p className="text-sm text-muted-foreground mt-2">{opp.recommendation}</p>
                          </div>
                          <div className="text-right ml-4">
                            <div className="text-2xl font-bold text-primary">
                              +{formatPercentage(opp.potential_improvement)}
                            </div>
                            <p className="text-xs text-muted-foreground">potential improvement</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 mt-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">Current: </span>
                            <span className="font-medium">{formatPercentage(opp.current_rate)}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Target: </span>
                            <span className="font-medium">{formatPercentage(opp.target_rate)}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-muted-foreground py-8">
                    No opportunities identified at this time
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="chat" className="space-y-6">
            <AICFOChat />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
