'use client';

import React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { governanceAPI } from '@/lib/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Shield,
  CheckCircle,
  Clock,
  XCircle,
  AlertTriangle,
  Send,
  ThumbsUp,
  ThumbsDown,
  BarChart3,
  FileText,
  RefreshCw,
  Eye,
  TrendingUp,
  Users,
} from 'lucide-react';

interface CertifiedMetric {
  id: string;
  metric_name: string;
  metric_code: string;
  description: string;
  status: 'DRAFT' | 'IN_REVIEW' | 'CERTIFIED' | 'EXPIRED';
  certified_by?: string;
  certified_at?: string;
  expires_at?: string;
  owner: string;
  created_at: string;
}

interface ApprovalWorkflow {
  id: string;
  title: string;
  description: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  requested_by: string;
  requested_at: string;
  target_type: string;
  target_name: string;
  reviewer?: string;
  reviewed_at?: string;
  rejection_reason?: string;
}

interface UsageRecord {
  id: string;
  dashboard_id?: string;
  dashboard_name?: string;
  report_id?: string;
  report_name?: string;
  view_count: number;
  unique_users: number;
  last_accessed: string;
  staleness_score: number;
  avg_session_duration_seconds: number;
}

const statusConfig: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ElementType }> = {
  DRAFT: { label: 'Draft', variant: 'secondary', icon: FileText },
  IN_REVIEW: { label: 'In Review', variant: 'outline', icon: Clock },
  CERTIFIED: { label: 'Certified', variant: 'default', icon: CheckCircle },
  EXPIRED: { label: 'Expired', variant: 'destructive', icon: AlertTriangle },
  PENDING: { label: 'Pending', variant: 'outline', icon: Clock },
  APPROVED: { label: 'Approved', variant: 'default', icon: CheckCircle },
  REJECTED: { label: 'Rejected', variant: 'destructive', icon: XCircle },
};

function getStalenessColor(score: number): string {
  if (score <= 30) return 'text-green-600';
  if (score <= 60) return 'text-yellow-600';
  return 'text-red-600';
}

function CertificationsSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div className="flex-1 space-y-3">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-5 w-40" />
                  <Skeleton className="h-5 w-20 rounded-full" />
                </div>
                <Skeleton className="h-3 w-64" />
                <div className="flex gap-4">
                  <Skeleton className="h-3 w-24" />
                  <Skeleton className="h-3 w-32" />
                  <Skeleton className="h-3 w-28" />
                </div>
              </div>
              <Skeleton className="h-8 w-24 rounded-lg" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ApprovalsSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div className="flex-1 space-y-3">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-5 w-36" />
                  <Skeleton className="h-5 w-16 rounded-full" />
                </div>
                <Skeleton className="h-3 w-56" />
                <div className="flex gap-4">
                  <Skeleton className="h-3 w-28" />
                  <Skeleton className="h-3 w-24" />
                  <Skeleton className="h-3 w-20" />
                </div>
              </div>
              <div className="flex gap-2">
                <Skeleton className="h-8 w-20 rounded-lg" />
                <Skeleton className="h-8 w-20 rounded-lg" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function UsageSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="pt-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Skeleton className="h-5 w-44" />
                <Skeleton className="h-4 w-12" />
              </div>
              <div className="grid grid-cols-4 gap-4">
                <div className="space-y-1">
                  <Skeleton className="h-3 w-16" />
                  <Skeleton className="h-6 w-10" />
                </div>
                <div className="space-y-1">
                  <Skeleton className="h-3 w-20" />
                  <Skeleton className="h-6 w-8" />
                </div>
                <div className="space-y-1">
                  <Skeleton className="h-3 w-18" />
                  <Skeleton className="h-6 w-14" />
                </div>
                <div className="space-y-1">
                  <Skeleton className="h-3 w-20" />
                  <Skeleton className="h-4 w-24" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function GovernancePage() {
  const [activeTab, setActiveTab] = React.useState('certifications');
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [certifiedMetrics, setCertifiedMetrics] = React.useState<CertifiedMetric[]>([]);
  const [approvals, setApprovals] = React.useState<ApprovalWorkflow[]>([]);
  const [usageData, setUsageData] = React.useState<UsageRecord[]>([]);
  const [submittingId, setSubmittingId] = React.useState<string | null>(null);
  const [actionId, setActionId] = React.useState<string | null>(null);
  const [showNewCertForm, setShowNewCertForm] = React.useState(false);
  const [newMetric, setNewMetric] = React.useState({ metric_name: '', metric_code: '', description: '', owner: '' });

  React.useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [certsRes, usageRes] = await Promise.all([
        governanceAPI.listCertifiedMetrics(),
        governanceAPI.listUsage(),
      ]);
      setCertifiedMetrics(certsRes.data.metrics || certsRes.data || []);
      setUsageData(usageRes.data.usage || usageRes.data || []);

      try {
        const approvalsRes = await governanceAPI.listUsage();
        setApprovals(approvalsRes.data.approvals || []);
      } catch {
        setApprovals([]);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load governance data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitForReview = async (metricId: string) => {
    setSubmittingId(metricId);
    try {
      await governanceAPI.submitMetricForCertification({ metric_id: metricId });
      setCertifiedMetrics(prev =>
        prev.map(m => (m.id === metricId ? { ...m, status: 'IN_REVIEW' as const } : m))
      );
    } catch (err) {
      console.error('Failed to submit for review:', err);
    } finally {
      setSubmittingId(null);
    }
  };

  const handleApprove = async (id: string) => {
    setActionId(id);
    try {
      await governanceAPI.approve(id);
      setApprovals(prev => prev.map(a => (a.id === id ? { ...a, status: 'APPROVED' as const } : a)));
    } catch (err) {
      console.error('Failed to approve:', err);
    } finally {
      setActionId(null);
    }
  };

  const handleReject = async (id: string) => {
    setActionId(id);
    try {
      await governanceAPI.reject(id);
      setApprovals(prev => prev.map(a => (a.id === id ? { ...a, status: 'REJECTED' as const } : a)));
    } catch (err) {
      console.error('Failed to reject:', err);
    } finally {
      setActionId(null);
    }
  };

  const handleCreateMetric = async () => {
    try {
      await governanceAPI.submitMetricForCertification(newMetric);
      setShowNewCertForm(false);
      setNewMetric({ metric_name: '', metric_code: '', description: '', owner: '' });
      fetchData();
    } catch (err) {
      console.error('Failed to create metric:', err);
    }
  };

  const pendingApprovals = approvals.filter(a => a.status === 'PENDING');

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Shield className="h-8 w-8 text-primary" />
              Analytics Governance
            </h1>
            <p className="text-muted-foreground">
              Certify metrics, manage approval workflows, and monitor data usage
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

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="certifications">
              <FileText className="h-4 w-4 mr-1.5" />
              Certifications
            </TabsTrigger>
            <TabsTrigger value="approvals">
              <Users className="h-4 w-4 mr-1.5" />
              Approvals {pendingApprovals.length > 0 && `(${pendingApprovals.length})`}
            </TabsTrigger>
            <TabsTrigger value="usage">
              <BarChart3 className="h-4 w-4 mr-1.5" />
              Usage Analytics
            </TabsTrigger>
          </TabsList>

          <TabsContent value="certifications" className="space-y-4 mt-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {certifiedMetrics.length} certified metric{certifiedMetrics.length !== 1 ? 's' : ''}
              </p>
              <Button onClick={() => setShowNewCertForm(!showNewCertForm)}>
                <Send className="h-4 w-4 mr-2" />
                Submit for Certification
              </Button>
            </div>

            {showNewCertForm && (
              <Card>
                <CardHeader>
                  <CardTitle>Submit New Metric for Certification</CardTitle>
                  <CardDescription>
                    Submit a metric for governance review and certification
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="metric_name">Metric Name</Label>
                      <Input
                        id="metric_name"
                        value={newMetric.metric_name}
                        onChange={e => setNewMetric(prev => ({ ...prev, metric_name: e.target.value }))}
                        placeholder="e.g. Revenue per Bed Day"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="metric_code">Metric Code</Label>
                      <Input
                        id="metric_code"
                        value={newMetric.metric_code}
                        onChange={e => setNewMetric(prev => ({ ...prev, metric_code: e.target.value }))}
                        placeholder="e.g. rev_per_bed_day"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="description">Description</Label>
                      <Input
                        id="description"
                        value={newMetric.description}
                        onChange={e => setNewMetric(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Describe what this metric measures"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="owner">Owner</Label>
                      <Input
                        id="owner"
                        value={newMetric.owner}
                        onChange={e => setNewMetric(prev => ({ ...prev, owner: e.target.value }))}
                        placeholder="e.g. Finance Team"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2 mt-4">
                    <Button variant="outline" onClick={() => setShowNewCertForm(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleCreateMetric}>Submit for Review</Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {loading ? (
              <CertificationsSkeleton />
            ) : certifiedMetrics.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-12">
                    <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium">No Certified Metrics</h3>
                    <p className="text-muted-foreground mt-1">
                      Submit your first metric for governance certification
                    </p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {certifiedMetrics.map(metric => {
                  const statusCfg = statusConfig[metric.status] || statusConfig.DRAFT;
                  const StatusIcon = statusCfg.icon;
                  return (
                    <Card key={metric.id}>
                      <CardContent className="pt-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h3 className="font-medium">{metric.metric_name}</h3>
                              <Badge variant={statusCfg.variant}>
                                <StatusIcon className="h-3 w-3 mr-1" />
                                {statusCfg.label}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground mt-1">{metric.description}</p>
                            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <FileText className="h-3 w-3" />
                                {metric.metric_code}
                              </span>
                              <span>Owner: {metric.owner}</span>
                              {metric.certified_by && <span>Certified by: {metric.certified_by}</span>}
                              {metric.expires_at && (
                                <span className={new Date(metric.expires_at) < new Date() ? 'text-red-500' : ''}>
                                  Expires: {new Date(metric.expires_at).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </div>
                          {(metric.status === 'DRAFT' || metric.status === 'EXPIRED') && (
                            <Button
                              size="sm"
                              onClick={() => handleSubmitForReview(metric.id)}
                              disabled={submittingId === metric.id}
                            >
                              <Send className="h-3.5 w-3.5 mr-1.5" />
                              {submittingId === metric.id ? 'Submitting...' : 'Submit'}
                            </Button>
                          )}
                          {metric.status === 'CERTIFIED' && (
                            <div className="flex items-center gap-1 text-green-600">
                              <CheckCircle className="h-4 w-4" />
                              <span className="text-sm font-medium">Active</span>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>

          <TabsContent value="approvals" className="space-y-4 mt-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {pendingApprovals.length} pending approval{pendingApprovals.length !== 1 ? 's' : ''}
              </p>
            </div>

            {loading ? (
              <ApprovalsSkeleton />
            ) : approvals.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-12">
                    <CheckCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium">No Pending Approvals</h3>
                    <p className="text-muted-foreground mt-1">
                      All governance approval workflows are up to date
                    </p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {approvals.map(approval => {
                  const statusCfg = statusConfig[approval.status] || statusConfig.PENDING;
                  const StatusIcon = statusCfg.icon;
                  return (
                    <Card key={approval.id}>
                      <CardContent className="pt-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h3 className="font-medium">{approval.title}</h3>
                              <Badge variant={statusCfg.variant}>
                                <StatusIcon className="h-3 w-3 mr-1" />
                                {statusCfg.label}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground mt-1">{approval.description}</p>
                            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                              <span>Type: {approval.target_type}</span>
                              <span>Target: {approval.target_name}</span>
                              <span>Requested by: {approval.requested_by}</span>
                              <span>
                                <Clock className="h-3 w-3 inline mr-1" />
                                {new Date(approval.requested_at).toLocaleDateString()}
                              </span>
                              {approval.reviewer && <span>Reviewed by: {approval.reviewer}</span>}
                              {approval.rejection_reason && (
                                <span className="text-red-500">Reason: {approval.rejection_reason}</span>
                              )}
                            </div>
                          </div>
                          {approval.status === 'PENDING' && (
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleReject(approval.id)}
                                disabled={actionId === approval.id}
                              >
                                <ThumbsDown className="h-3.5 w-3.5 mr-1.5" />
                                Reject
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => handleApprove(approval.id)}
                                disabled={actionId === approval.id}
                              >
                                <ThumbsUp className="h-3.5 w-3.5 mr-1.5" />
                                Approve
                              </Button>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>

          <TabsContent value="usage" className="space-y-4 mt-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Dashboard and report usage metrics with staleness scores
              </p>
            </div>

            {loading ? (
              <UsageSkeleton />
            ) : usageData.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-12">
                    <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium">No Usage Data</h3>
                    <p className="text-muted-foreground mt-1">
                      Usage analytics will appear once dashboards and reports are accessed
                    </p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {usageData.map(record => (
                  <Card key={record.id}>
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium">
                              {record.dashboard_name || record.report_name || 'Unknown'}
                            </h3>
                            <Badge variant="outline" className="text-xs">
                              {record.dashboard_id ? 'Dashboard' : 'Report'}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-4 gap-6 mt-3">
                            <div>
                              <p className="text-xs text-muted-foreground">Views</p>
                              <p className="text-lg font-semibold flex items-center gap-1">
                                <Eye className="h-4 w-4 text-muted-foreground" />
                                {record.view_count}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">Unique Users</p>
                              <p className="text-lg font-semibold flex items-center gap-1">
                                <Users className="h-4 w-4 text-muted-foreground" />
                                {record.unique_users}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">Avg Session</p>
                              <p className="text-lg font-semibold">
                                {Math.round(record.avg_session_duration_seconds / 60)}m
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">Staleness</p>
                              <p className={`text-lg font-semibold ${getStalenessColor(record.staleness_score)}`}>
                                {record.staleness_score}%
                              </p>
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground mt-2">
                            Last accessed: {new Date(record.last_accessed).toLocaleString()}
                          </p>
                        </div>
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
