"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { learningAPI } from "@/lib/api/client";
import { formatCurrency, formatDate, getConfidenceColor } from "@/lib/utils/format";
import { Brain, TrendingUp, Target, AlertTriangle, BarChart3, Lightbulb } from "lucide-react";

interface LearningMetric {
  id: string;
  metric_type: string;
  metric_name: string;
  metric_value: number;
  measured_at: string;
}

interface RecommendationAccuracy {
  id: string;
  recommendation_id: string;
  recommendation_type: string;
  predicted_impact: number;
  actual_impact: number | null;
  accuracy_score: number | null;
  accuracy_status: string;
  created_at: string;
}

interface AdoptionSummary {
  total_recommendations: number;
  adopted: number;
  acceptance_rate: number;
}

interface CausalResult {
  method: string;
  effect_size: number;
  confidence_interval: [number, number] | null;
  p_value: number | null;
  is_significant: boolean;
}

export function LearningDashboard() {
  const [activeTab, setActiveTab] = useState("overview");
  const [metrics, setMetrics] = useState<LearningMetric[]>([]);
  const [accuracy, setAccuracy] = useState<RecommendationAccuracy[]>([]);
  const [adoption, setAdoption] = useState<AdoptionSummary | null>(null);
  const [patterns, setPatterns] = useState<any[]>([]);
  const [adjustments, setAdjustments] = useState<any[]>([]);
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchAll(); }, []);

  async function fetchAll() {
    setLoading(true);
    try {
      const [metricsRes, accuracyRes, adoptionRes, patternsRes, adjustRes, dashRes] = await Promise.allSettled([
        learningAPI.getMetrics(),
        learningAPI.getRecommendationAccuracy(),
        learningAPI.getAdoptionSummary(),
        learningAPI.getPatterns(),
        learningAPI.getScoringAdjustments(),
        learningAPI.getDashboard(),
      ]);
      if (metricsRes.status === "fulfilled") setMetrics(metricsRes.value.data?.data || []);
      if (accuracyRes.status === "fulfilled") setAccuracy(accuracyRes.value.data?.data || []);
      if (adoptionRes.status === "fulfilled") setAdoption(adoptionRes.value.data?.data || null);
      if (patternsRes.status === "fulfilled") setPatterns(patternsRes.value.data?.data || []);
      if (adjustRes.status === "fulfilled") setAdjustments(adjustRes.value.data?.data || []);
      if (dashRes.status === "fulfilled") setDashboard(dashRes.value.data?.data || null);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }

  const avgAccuracy = accuracy.length > 0
    ? accuracy.filter(a => a.accuracy_score !== null).reduce((sum, a) => sum + (a.accuracy_score || 0), 0) / accuracy.filter(a => a.accuracy_score !== null).length
    : 0;

  const accuracyDist = {
    excellent: accuracy.filter(a => (a.accuracy_score || 0) >= 0.8).length,
    good: accuracy.filter(a => (a.accuracy_score || 0) >= 0.6 && (a.accuracy_score || 0) < 0.8).length,
    fair: accuracy.filter(a => (a.accuracy_score || 0) >= 0.4 && (a.accuracy_score || 0) < 0.6).length,
    poor: accuracy.filter(a => (a.accuracy_score || 0) < 0.4).length,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Learning Dashboard</h2>
          <p className="text-muted-foreground">Track recommendation accuracy, adoption, and continuous improvement</p>
        </div>
        <Button variant="outline" onClick={fetchAll}>Refresh</Button>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <Card><CardContent className="p-4">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-purple-600" />
            <div className="text-2xl font-bold">{metrics.length}</div>
          </div>
          <div className="text-sm text-muted-foreground">Learning Metrics</div>
        </CardContent></Card>
        <Card><CardContent className="p-4">
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-green-600" />
            <div className="text-2xl font-bold" style={{ color: getConfidenceColor(avgAccuracy) }}>{(avgAccuracy * 100).toFixed(1)}%</div>
          </div>
          <div className="text-sm text-muted-foreground">Avg Accuracy</div>
        </CardContent></Card>
        <Card><CardContent className="p-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            <div className="text-2xl font-bold">{adoption ? (adoption.acceptance_rate * 100).toFixed(1) : "0"}%</div>
          </div>
          <div className="text-sm text-muted-foreground">Adoption Rate</div>
        </CardContent></Card>
        <Card><CardContent className="p-4">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-yellow-600" />
            <div className="text-2xl font-bold">{patterns.length}</div>
          </div>
          <div className="text-sm text-muted-foreground">Patterns Found</div>
        </CardContent></Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="accuracy">Accuracy</TabsTrigger>
          <TabsTrigger value="adoption">Adoption</TabsTrigger>
          <TabsTrigger value="patterns">Patterns</TabsTrigger>
          <TabsTrigger value="adjustments">Adjustments</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle className="text-lg">Accuracy Distribution</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center"><span className="text-sm">Excellent (≥80%)</span><Badge className="bg-emerald-100 text-emerald-800">{accuracyDist.excellent}</Badge></div>
                <div className="flex justify-between items-center"><span className="text-sm">Good (60-80%)</span><Badge className="bg-green-100 text-green-800">{accuracyDist.good}</Badge></div>
                <div className="flex justify-between items-center"><span className="text-sm">Fair (40-60%)</span><Badge className="bg-yellow-100 text-yellow-800">{accuracyDist.fair}</Badge></div>
                <div className="flex justify-between items-center"><span className="text-sm">Poor (&lt;40%)</span><Badge className="bg-red-100 text-red-800">{accuracyDist.poor}</Badge></div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-lg">Adoption Summary</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center"><span className="text-sm">Total Recommendations</span><span className="font-bold">{adoption?.total_recommendations || 0}</span></div>
                <div className="flex justify-between items-center"><span className="text-sm">Adopted</span><span className="font-bold text-green-600">{adoption?.adopted || 0}</span></div>
                <div className="flex justify-between items-center"><span className="text-sm">Acceptance Rate</span><span className="font-bold">{adoption ? (adoption.acceptance_rate * 100).toFixed(1) : "0"}%</span></div>
              </CardContent>
            </Card>
          </div>
          {dashboard && (
            <Card>
              <CardHeader><CardTitle className="text-lg">Learning Summary</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                {dashboard.key_metrics && typeof dashboard.key_metrics === 'object' && (
                  <div className="grid grid-cols-4 gap-4">
                    {Object.entries(dashboard.key_metrics as Record<string, unknown>).map(([key, value]) => (
                      <div key={key} className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground">{key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
                        <div className="text-2xl font-bold">{typeof value === 'number' ? value.toLocaleString() : String(value)}</div>
                      </div>
                    ))}
                  </div>
                )}
                {dashboard.trends && typeof dashboard.trends === 'object' && (
                  <div className="space-y-2">
                    <h4 className="font-medium">Trends</h4>
                    <div className="grid grid-cols-2 gap-3">
                      {Object.entries(dashboard.trends as Record<string, unknown>).map(([key, value]) => (
                        <div key={key} className="p-3 border rounded-lg">
                          <div className="text-sm text-muted-foreground">{key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
                          <div className="font-medium">{String(value)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {dashboard.recent_insights && dashboard.recent_insights.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-medium">Recent Insights</h4>
                    <ul className="space-y-1">
                      {dashboard.recent_insights.map((insight: string, i: number) => (
                        <li key={i} className="text-sm text-muted-foreground flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {dashboard.alerts && dashboard.alerts.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-medium">Active Alerts</h4>
                    <div className="space-y-1">
                      {dashboard.alerts.map((alert: any, i: number) => (
                        <Badge key={i} variant="outline" className="w-full justify-start gap-2">
                          <AlertTriangle className="h-3 w-3" />
                          {alert.message || alert}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {!dashboard.key_metrics && !dashboard.trends && !dashboard.recent_insights && !dashboard.alerts && (
                  <div className="text-sm text-muted-foreground">
                    <pre className="whitespace-pre-wrap">{JSON.stringify(dashboard, null, 2)}</pre>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="accuracy">
          <Card>
            <CardHeader><CardTitle>Recommendation Accuracy</CardTitle></CardHeader>
            <CardContent>
              {accuracy.length === 0 ? <div className="text-center py-8 text-muted-foreground">No accuracy data yet</div>
              : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Predicted Impact</TableHead>
                      <TableHead>Actual Impact</TableHead>
                      <TableHead>Accuracy</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {accuracy.map(a => (
                      <TableRow key={a.id}>
                        <TableCell className="capitalize">{a.recommendation_type}</TableCell>
                        <TableCell>{formatCurrency(a.predicted_impact)}</TableCell>
                        <TableCell>{a.actual_impact !== null ? formatCurrency(a.actual_impact) : "—"}</TableCell>
                        <TableCell style={{ color: getConfidenceColor(a.accuracy_score || 0) }}>{a.accuracy_score !== null ? (a.accuracy_score * 100).toFixed(1) + "%" : "—"}</TableCell>
                        <TableCell><Badge className={a.accuracy_status === "validated" ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"}>{a.accuracy_status}</Badge></TableCell>
                        <TableCell className="text-sm">{formatDate(a.created_at)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="adoption">
          <Card>
            <CardHeader><CardTitle>Adoption Metrics</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-4 border rounded-lg">
                  <div className="text-3xl font-bold text-green-600">{adoption?.adopted || 0}</div>
                  <div className="text-sm text-muted-foreground">Adopted</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-3xl font-bold text-gray-600">{(adoption?.total_recommendations || 0) - (adoption?.adopted || 0)}</div>
                  <div className="text-sm text-muted-foreground">Rejected</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-3xl font-bold text-blue-600">{adoption ? (adoption.acceptance_rate * 100).toFixed(1) : "0"}%</div>
                  <div className="text-sm text-muted-foreground">Acceptance Rate</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="patterns">
          <Card>
            <CardHeader><CardTitle>Discovered Patterns</CardTitle></CardHeader>
            <CardContent>
              {patterns.length === 0 ? <div className="text-center py-8 text-muted-foreground">No patterns discovered yet</div>
              : (
                <div className="space-y-3">
                  {patterns.map((p, i) => (
                    <div key={i} className="p-4 border rounded-lg">
                      <div className="font-medium">{p.pattern_type || p.type}</div>
                      <div className="text-sm text-muted-foreground mt-1">{p.description || JSON.stringify(p)}</div>
                      {p.confidence && <Badge className="mt-2" style={{ color: getConfidenceColor(p.confidence) }}>Confidence: {(p.confidence * 100).toFixed(1)}%</Badge>}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="adjustments">
          <Card>
            <CardHeader><CardTitle>Scoring Adjustments</CardTitle></CardHeader>
            <CardContent>
              {adjustments.length === 0 ? <div className="text-center py-8 text-muted-foreground">No scoring adjustments yet</div>
              : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Metric</TableHead>
                      <TableHead>Previous</TableHead>
                      <TableHead>Adjusted</TableHead>
                      <TableHead>Reason</TableHead>
                      <TableHead>Applied At</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {adjustments.map((adj, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium">{adj.metric_code || adj.metric}</TableCell>
                        <TableCell>{adj.previous_weight?.toFixed(3) || adj.previous_weight}</TableCell>
                        <TableCell className="text-green-600">{adj.new_weight?.toFixed(3) || adj.new_weight}</TableCell>
                        <TableCell className="max-w-[250px] truncate">{adj.reason || adj.adjustment_reason}</TableCell>
                        <TableCell className="text-sm">{formatDate(adj.applied_at || adj.created_at)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
