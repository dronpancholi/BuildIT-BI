'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Download,
  FileText,
  FileSpreadsheet,
  FileImage,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  Plus,
  RefreshCw,
  Trash2,
  Calendar,
  Mail,
  AlertTriangle,
} from 'lucide-react';
import { exportsAPI } from '@/lib/api/client';

interface ExportJob {
  id: string;
  query_id?: string;
  format: string;
  status: string;
  created_at: string;
  completed_at?: string;
  file_url?: string;
  error_message?: string;
  filename?: string;
  options?: Record<string, unknown>;
}

interface ScheduledExport {
  id: string;
  name: string;
  query_id?: string;
  format: string;
  schedule_cron: string;
  next_run: string;
  last_run?: string;
  is_active: boolean;
  delivery_email?: string;
  created_at: string;
}

interface ReportSubscription {
  id: string;
  report_id: string;
  frequency: string;
  delivery_email?: string;
  delivery_format: string;
  include_data: boolean;
  include_charts: boolean;
  is_active: boolean;
  created_at: string;
  last_sent?: string;
}

function getStatusBadge(status: string) {
  switch (status.toUpperCase()) {
    case 'PENDING':
      return (
        <Badge variant="secondary" className="gap-1">
          <Clock className="h-3 w-3" />
          Pending
        </Badge>
      );
    case 'PROCESSING':
      return (
        <Badge variant="default" className="gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          Processing
        </Badge>
      );
    case 'COMPLETED':
      return (
        <Badge variant="secondary" className="gap-1 text-healthcare-green border-healthcare-green/30 bg-healthcare-green/10">
          <CheckCircle className="h-3 w-3" />
          Completed
        </Badge>
      );
    case 'FAILED':
      return (
        <Badge variant="destructive" className="gap-1">
          <XCircle className="h-3 w-3" />
          Failed
        </Badge>
      );
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

function getFrequencyBadge(frequency: string) {
  const colors: Record<string, string> = {
    daily: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    weekly: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
    monthly: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
    quarterly: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300',
  };
  return (
    <Badge variant="outline" className={colors[frequency?.toLowerCase()] || ''}>
      {frequency}
    </Badge>
  );
}

function getFormatIcon(format: string) {
  switch (format?.toLowerCase()) {
    case 'pdf':
      return <FileText className="h-4 w-4 text-red-500" />;
    case 'excel':
    case 'xlsx':
      return <FileSpreadsheet className="h-4 w-4 text-green-600" />;
    case 'csv':
      return <FileText className="h-4 w-4 text-blue-500" />;
    case 'png':
    case 'image':
      return <FileImage className="h-4 w-4 text-purple-500" />;
    default:
      return <FileText className="h-4 w-4 text-muted-foreground" />;
  }
}

function JobsSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 rounded-lg border p-4">
          <Skeleton className="h-8 w-8 rounded-lg" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-3 w-32" />
          </div>
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-8 w-8 rounded-lg" />
        </div>
      ))}
    </div>
  );
}

export default function ExportsPage() {
  const [activeTab, setActiveTab] = useState('jobs');
  const [jobs, setJobs] = useState<ExportJob[]>([]);
  const [schedules, setSchedules] = useState<ScheduledExport[]>([]);
  const [subscriptions, setSubscriptions] = useState<ReportSubscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [subscriptionDialogOpen, setSubscriptionDialogOpen] = useState(false);
  const [creating, setCreating] = useState(false);

  const [newJob, setNewJob] = useState({
    query_id: '',
    format: 'pdf',
  });

  const [newSchedule, setNewSchedule] = useState({
    name: '',
    query_id: '',
    format: 'pdf',
    schedule_cron: '0 9 * * 1',
  });

  const [newSubscription, setNewSubscription] = useState({
    report_id: '',
    frequency: 'weekly',
    delivery_email: '',
    delivery_format: 'pdf',
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [jobsRes, schedulesRes, subscriptionsRes] = await Promise.allSettled([
        exportsAPI.listJobs(),
        exportsAPI.listSchedules(),
        exportsAPI.listSubscriptions(),
      ]);

      if (jobsRes.status === 'fulfilled') {
        setJobs(jobsRes.value.data?.jobs || jobsRes.value.data || []);
      }
      if (schedulesRes.status === 'fulfilled') {
        setSchedules(schedulesRes.value.data?.schedules || schedulesRes.value.data || []);
      }
      if (subscriptionsRes.status === 'fulfilled') {
        setSubscriptions(subscriptionsRes.value.data?.subscriptions || subscriptionsRes.value.data || []);
      }

      const anyFailed = [jobsRes, schedulesRes, subscriptionsRes].some(r => r.status === 'rejected');
      if (anyFailed) {
        setError('Some data failed to load. Showing available data.');
      }
    } catch (err) {
      setError('Failed to load export data. Please try again.');
      console.error('Failed to fetch exports:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateJob = async () => {
    setCreating(true);
    try {
      await exportsAPI.createJob(newJob);
      setCreateDialogOpen(false);
      setNewJob({ query_id: '', format: 'pdf' });
      fetchData();
    } catch (err) {
      console.error('Failed to create export job:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleCancelJob = async (id: string) => {
    try {
      await exportsAPI.cancelJob(id);
      setJobs(jobs.map(j => (j.id === id ? { ...j, status: 'CANCELLED' } : j)));
    } catch (err) {
      console.error('Failed to cancel job:', err);
    }
  };

  const handleCreateSchedule = async () => {
    setCreating(true);
    try {
      await exportsAPI.createSchedule(newSchedule);
      setScheduleDialogOpen(false);
      setNewSchedule({ name: '', query_id: '', format: 'pdf', schedule_cron: '0 9 * * 1' });
      fetchData();
    } catch (err) {
      console.error('Failed to create schedule:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleCancelSchedule = async (id: string) => {
    try {
      await exportsAPI.cancelSchedule(id);
      setSchedules(schedules.filter(s => s.id !== id));
    } catch (err) {
      console.error('Failed to cancel schedule:', err);
    }
  };

  const handleCreateSubscription = async () => {
    setCreating(true);
    try {
      await exportsAPI.subscribe(newSubscription);
      setSubscriptionDialogOpen(false);
      setNewSubscription({ report_id: '', frequency: 'weekly', delivery_email: '', delivery_format: 'pdf' });
      fetchData();
    } catch (err) {
      console.error('Failed to create subscription:', err);
    } finally {
      setCreating(false);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Download className="h-8 w-8 text-primary" />
              Export Engine
            </h1>
            <p className="text-muted-foreground">
              Generate, schedule, and manage report exports and subscriptions
            </p>
          </div>
          <Button onClick={fetchData} variant="outline" disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <Separator />

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="jobs">Active Jobs</TabsTrigger>
            <TabsTrigger value="schedules">Scheduled</TabsTrigger>
            <TabsTrigger value="subscriptions">Subscriptions</TabsTrigger>
          </TabsList>

          <TabsContent value="jobs" className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {jobs.length} export {jobs.length === 1 ? 'job' : 'jobs'}
              </p>
              <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    New Export
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>Create Export Job</DialogTitle>
                    <DialogDescription>
                      Generate a new report export by providing a query ID and format
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-2">
                    <div className="space-y-2">
                      <Label htmlFor="job-query-id">Query ID</Label>
                      <Input
                        id="job-query-id"
                        placeholder="e.g. query_abc123 or saved-query-name"
                        value={newJob.query_id}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setNewJob({ ...newJob, query_id: e.target.value })
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        Enter a saved query ID or query plan reference
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label>Export Format</Label>
                      <div className="grid grid-cols-4 gap-2">
                        {['pdf', 'xlsx', 'csv', 'json', 'parquet'].map((fmt) => (
                          <Button
                            key={fmt}
                            variant={newJob.format === fmt ? 'default' : 'outline'}
                            className="justify-center gap-2"
                            onClick={() => setNewJob({ ...newJob, format: fmt })}
                          >
                            {getFormatIcon(fmt)}
                            <span className="uppercase text-xs">{fmt}</span>
                          </Button>
                        ))}
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      variant="outline"
                      onClick={() => setCreateDialogOpen(false)}
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleCreateJob}
                      disabled={!newJob.query_id.trim() || creating}
                    >
                      {creating ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Download className="h-4 w-4 mr-2" />
                      )}
                      Create Export
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            {loading ? (
              <JobsSkeleton />
            ) : error ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
                    <h3 className="text-lg font-medium">Error Loading Jobs</h3>
                    <p className="text-muted-foreground mt-1">{error}</p>
                    <Button onClick={fetchData} variant="outline" className="mt-4">
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Retry
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : jobs.length === 0 ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <Download className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium">No Export Jobs</h3>
                    <p className="text-muted-foreground mt-1">
                      Create your first export job to get started
                    </p>
                    <Button onClick={() => setCreateDialogOpen(true)} className="mt-4">
                      <Plus className="h-4 w-4 mr-2" />
                      Create Export
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {jobs.map((job) => (
                  <Card key={job.id}>
                    <CardContent className="py-4">
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center shrink-0">
                          {getFormatIcon(job.format)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium truncate">{job.query_id ? `Query: ${job.query_id}` : `Export ${job.id}`}</h3>
                            {getStatusBadge(job.status)}
                          </div>
                          <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                            <span className="uppercase font-medium">{job.format}</span>
                            {job.filename && (
                              <>
                                <span>·</span>
                                <span>{job.filename}</span>
                              </>
                            )}
                            <span>·</span>
                            <span>Created {formatDate(job.created_at)}</span>
                          </div>
                          {job.error_message && (
                            <p className="text-xs text-destructive mt-1">{job.error_message}</p>
                          )}
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          {job.file_url && (
                            <a href={job.file_url} download>
                              <Button variant="outline" size="sm">
                                <Download className="h-4 w-4" />
                              </Button>
                            </a>
                          )}
                          {(job.status === 'PENDING' || job.status === 'PROCESSING') && (
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              onClick={() => handleCancelJob(job.id)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="schedules" className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {schedules.length} scheduled {schedules.length === 1 ? 'export' : 'exports'}
              </p>
              <Dialog open={scheduleDialogOpen} onOpenChange={setScheduleDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    New Schedule
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>Create Scheduled Export</DialogTitle>
                    <DialogDescription>
                      Set up recurring report exports on a schedule
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-2">
                    <div className="space-y-2">
                      <Label htmlFor="schedule-name">Schedule Name</Label>
                      <Input
                        id="schedule-name"
                        placeholder="e.g. Weekly Revenue Report"
                        value={newSchedule.name}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setNewSchedule({ ...newSchedule, name: e.target.value })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="schedule-query-id">Query ID</Label>
                      <Input
                        id="schedule-query-id"
                        placeholder="e.g. query_abc123 or saved-query-name"
                        value={newSchedule.query_id}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setNewSchedule({ ...newSchedule, query_id: e.target.value })
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        Enter a saved query ID to schedule
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Format</Label>
                        <Select
                          value={newSchedule.format}
                          onValueChange={(val) => val && setNewSchedule({ ...newSchedule, format: val })}
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pdf">PDF</SelectItem>
                            <SelectItem value="xlsx">Excel</SelectItem>
                            <SelectItem value="csv">CSV</SelectItem>
                            <SelectItem value="json">JSON</SelectItem>
                            <SelectItem value="parquet">Parquet</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Cron Schedule</Label>
                        <Select
                          value={newSchedule.schedule_cron}
                          onValueChange={(val) => val && setNewSchedule({ ...newSchedule, schedule_cron: val })}
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="0 9 * * 1">Weekly (Monday 9:00 AM)</SelectItem>
                            <SelectItem value="0 9 * * *">Daily (9:00 AM)</SelectItem>
                            <SelectItem value="0 9 1 * *">Monthly (1st at 9:00 AM)</SelectItem>
                            <SelectItem value="0 9 1 */3 *">Quarterly (1st at 9:00 AM)</SelectItem>
                            <SelectItem value="0 */6 * * *">Every 6 hours</SelectItem>
                          </SelectContent>
                        </Select>
                        <p className="text-xs text-muted-foreground">
                          Cron expression (UTC)
                        </p>
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setScheduleDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      onClick={handleCreateSchedule}
                      disabled={!newSchedule.name.trim() || creating}
                    >
                      {creating ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Calendar className="h-4 w-4 mr-2" />
                      )}
                      Create Schedule
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            {loading ? (
              <JobsSkeleton />
            ) : error ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
                    <h3 className="text-lg font-medium">Error Loading Schedules</h3>
                    <p className="text-muted-foreground mt-1">{error}</p>
                    <Button onClick={fetchData} variant="outline" className="mt-4">
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Retry
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : schedules.length === 0 ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium">No Scheduled Exports</h3>
                    <p className="text-muted-foreground mt-1">
                      Set up recurring exports to automate your reporting
                    </p>
                    <Button onClick={() => setScheduleDialogOpen(true)} className="mt-4">
                      <Plus className="h-4 w-4 mr-2" />
                      Create Schedule
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {schedules.map((schedule) => (
                  <Card key={schedule.id}>
                    <CardContent className="py-4">
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                          <Calendar className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium truncate">{schedule.name}</h3>
                            <Badge variant="outline" className="text-xs">
                              {schedule.schedule_cron}
                            </Badge>
                            {!schedule.is_active && (
                              <Badge variant="outline" className="text-muted-foreground">Paused</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                            <span className="uppercase font-medium">{schedule.format}</span>
                            {schedule.query_id && (
                              <>
                                <span>·</span>
                                <span>Query: {schedule.query_id}</span>
                              </>
                            )}
                            {schedule.delivery_email && (
                              <>
                                <span>·</span>
                                <span>{schedule.delivery_email}</span>
                              </>
                            )}
                            <span>·</span>
                            <span>Next: {formatDate(schedule.next_run)}</span>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleCancelSchedule(schedule.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="subscriptions" className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {subscriptions.length} active {subscriptions.length === 1 ? 'subscription' : 'subscriptions'}
              </p>
              <Dialog open={subscriptionDialogOpen} onOpenChange={setSubscriptionDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    New Subscription
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>Create Report Subscription</DialogTitle>
                    <DialogDescription>
                      Subscribe to receive reports via email on a schedule
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-2">
                    <div className="space-y-2">
                      <Label htmlFor="sub-report-id">Report ID</Label>
                      <Input
                        id="sub-report-id"
                        placeholder="e.g. executive_summary_report"
                        value={newSubscription.report_id}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setNewSubscription({ ...newSubscription, report_id: e.target.value })
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        Enter the report identifier to subscribe to
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="sub-email">Email Address</Label>
                      <Input
                        id="sub-email"
                        type="email"
                        placeholder="report@hospital.org"
                        value={newSubscription.delivery_email}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setNewSubscription({ ...newSubscription, delivery_email: e.target.value })
                        }
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Delivery Format</Label>
                        <Select
                          value={newSubscription.delivery_format}
                          onValueChange={(val) =>
                            val && setNewSubscription({ ...newSubscription, delivery_format: val })
                          }
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pdf">PDF</SelectItem>
                            <SelectItem value="xlsx">Excel</SelectItem>
                            <SelectItem value="csv">CSV</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Frequency</Label>
                        <Select
                          value={newSubscription.frequency}
                          onValueChange={(val) =>
                            val && setNewSubscription({ ...newSubscription, frequency: val })
                          }
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="daily">Daily</SelectItem>
                            <SelectItem value="weekly">Weekly</SelectItem>
                            <SelectItem value="monthly">Monthly</SelectItem>
                            <SelectItem value="quarterly">Quarterly</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setSubscriptionDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      onClick={handleCreateSubscription}
                      disabled={!newSubscription.report_id.trim() || !newSubscription.delivery_email.trim() || creating}
                    >
                      {creating ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Mail className="h-4 w-4 mr-2" />
                      )}
                      Subscribe
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            {loading ? (
              <JobsSkeleton />
            ) : error ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
                    <h3 className="text-lg font-medium">Error Loading Subscriptions</h3>
                    <p className="text-muted-foreground mt-1">{error}</p>
                    <Button onClick={fetchData} variant="outline" className="mt-4">
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Retry
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : subscriptions.length === 0 ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <Mail className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium">No Subscriptions</h3>
                    <p className="text-muted-foreground mt-1">
                      Subscribe to reports to receive them automatically via email
                    </p>
                    <Button onClick={() => setSubscriptionDialogOpen(true)} className="mt-4">
                      <Plus className="h-4 w-4 mr-2" />
                      Create Subscription
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {subscriptions.map((sub) => (
                  <Card key={sub.id}>
                    <CardContent className="py-4">
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center shrink-0">
                          <Mail className="h-5 w-5 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium truncate">{sub.report_id}</h3>
                            {getFrequencyBadge(sub.frequency)}
                            {!sub.is_active && (
                              <Badge variant="outline" className="text-muted-foreground">Inactive</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                            <span>{sub.delivery_email || 'No email'}</span>
                            <span>·</span>
                            <span className="uppercase font-medium">{sub.delivery_format}</span>
                            {sub.last_sent && (
                              <>
                                <span>·</span>
                                <span>Last sent: {formatDate(sub.last_sent)}</span>
                              </>
                            )}
                          </div>
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
