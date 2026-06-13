'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  LayoutDashboard,
  GitMerge,
  FileText,
  CheckSquare,
  Bell,
  Settings,
  Eye,
  Mail,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  ChevronRight,
  Sparkles,
  BookOpen,
  Save,
  Palette,
  Rows3,
} from 'lucide-react';
import { workspaceAPI, intelligenceAPI, decisionsAPI } from '@/lib/api/client';

interface WorkspaceSection {
  id: string;
  section_type: string;
  title: string;
  is_visible: boolean;
  order: number;
  config?: Record<string, unknown>;
}

interface Briefing {
  id: string;
  title: string;
  summary?: string;
  content?: string;
  briefing_type: string;
  status: string;
  is_read: boolean;
  priority?: string;
  created_at: string;
  read_at?: string;
}

interface NotificationConfig {
  email_enabled: boolean;
  digest_frequency: string;
  briefings_enabled: boolean;
  alerts_enabled: boolean;
  decisions_enabled: boolean;
  comments_enabled: boolean;
}

interface WorkspaceData {
  id?: string;
  sections?: WorkspaceSection[];
  layout?: {
    compact_mode: boolean;
    theme: string;
  };
}

function getBriefingTypeBadge(type: string) {
  switch (type?.toLowerCase()) {
    case 'daily':
      return <Badge variant="default" className="gap-1">Daily</Badge>;
    case 'weekly':
      return <Badge variant="secondary" className="gap-1 bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300">Weekly</Badge>;
    case 'monthly':
      return <Badge variant="secondary" className="gap-1 bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300">Monthly</Badge>;
    case 'ad_hoc':
      return <Badge variant="outline" className="gap-1">Ad Hoc</Badge>;
    default:
      return <Badge variant="outline">{type}</Badge>;
  }
}

function getBriefingPriorityBadge(priority?: string) {
  switch (priority?.toLowerCase()) {
    case 'urgent':
      return <Badge variant="destructive" className="gap-1">Urgent</Badge>;
    case 'high':
      return <Badge variant="secondary" className="gap-1 bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300">High</Badge>;
    default:
      return null;
  }
}

function SectionSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-5 rounded" />
              <Skeleton className="h-4 w-32" />
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-4/5" />
            <Skeleton className="h-3 w-3/5" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function BriefingSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="rounded-lg border p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-5 w-20 rounded-full" />
          </div>
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-3/4" />
        </div>
      ))}
    </div>
  );
}

export default function WorkspacePage() {
  const [workspace, setWorkspace] = useState<WorkspaceData | null>(null);
  const [briefings, setBriefings] = useState<Briefing[]>([]);
  const [notifications, setNotifications] = useState<NotificationConfig>({
    email_enabled: true,
    digest_frequency: 'daily',
    briefings_enabled: true,
    alerts_enabled: true,
    decisions_enabled: true,
    comments_enabled: true,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);

  const [compactMode, setCompactMode] = useState(false);
  const [theme, setTheme] = useState('default');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [workspaceRes, briefingsRes, notificationsRes] = await Promise.allSettled([
        workspaceAPI.get(),
        workspaceAPI.listBriefings(),
        workspaceAPI.getNotifications(),
      ]);

      if (workspaceRes.status === 'fulfilled') {
        const data = workspaceRes.value.data;
        setWorkspace(data);
        setCompactMode(data?.layout?.compact_mode || false);
        setTheme(data?.layout?.theme || 'default');
      }
      if (briefingsRes.status === 'fulfilled') {
        setBriefings(briefingsRes.value.data?.briefings || briefingsRes.value.data || []);
      }
      if (notificationsRes.status === 'fulfilled') {
        setNotifications(notificationsRes.value.data || notifications);
      }

      const anyFailed = [workspaceRes, briefingsRes, notificationsRes].some(r => r.status === 'rejected');
      if (anyFailed) {
        setError('Some workspace data failed to load.');
      }
    } catch (err) {
      setError('Failed to load workspace. Please try again.');
      console.error('Failed to fetch workspace:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleMarkBriefingRead = async (id: string) => {
    try {
      await workspaceAPI.markBriefingRead(id);
      setBriefings(briefings.map(b => (b.id === id ? { ...b, is_read: true, read_at: new Date().toISOString() } : b)));
    } catch (err) {
      console.error('Failed to mark briefing as read:', err);
    }
  };

  const handleGenerateBriefing = async () => {
    setGenerating(true);
    try {
      await workspaceAPI.generateBriefing();
      fetchData();
    } catch (err) {
      console.error('Failed to generate briefing:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleUpdateNotifications = async () => {
    setSaving(true);
    try {
      await workspaceAPI.updateNotifications(notifications);
    } catch (err) {
      console.error('Failed to update notifications:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateLayout = async () => {
    setSaving(true);
    try {
      await workspaceAPI.update({
        layout: { compact_mode: compactMode, theme },
      });
    } catch (err) {
      console.error('Failed to update layout:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleToggleSection = async (sectionId: string, isVisible: boolean) => {
    try {
      const section = workspace?.sections?.find(s => s.id === sectionId);
      if (section) {
        await workspaceAPI.updateSection(section.section_type, { is_visible: isVisible });
        setWorkspace(prev => ({
          ...prev,
          sections: prev?.sections?.map(s => (s.id === sectionId ? { ...s, is_visible: isVisible } : s)),
        }));
      }
    } catch (err) {
      console.error('Failed to update section:', err);
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

  const defaultSections: WorkspaceSection[] = [
    { id: '1', section_type: 'dashboard', title: 'My Dashboard', is_visible: true, order: 0 },
    { id: '2', section_type: 'decisions', title: 'My Decisions', is_visible: true, order: 1 },
    { id: '3', section_type: 'briefings', title: 'My Briefings', is_visible: true, order: 2 },
    { id: '4', section_type: 'assignments', title: 'My Assignments', is_visible: true, order: 3 },
  ];

  const sections = workspace?.sections || defaultSections;

  const unreadBriefings = briefings.filter(b => !b.is_read);

  const sectionIcons: Record<string, React.ElementType> = {
    dashboard: LayoutDashboard,
    decisions: GitMerge,
    briefings: FileText,
    assignments: CheckSquare,
  };

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <LayoutDashboard className="h-8 w-8 text-primary" />
              Executive Workspace
            </h1>
            <p className="text-muted-foreground">
              Your personalized command center for financial insights and decisions
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
            <TabsTrigger value="dashboard">My Dashboard</TabsTrigger>
            <TabsTrigger value="briefings">My Briefings</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="settings">Layout Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-6">
            {loading ? (
              <SectionSkeleton />
            ) : error ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
                    <h3 className="text-lg font-medium">Error Loading Workspace</h3>
                    <p className="text-muted-foreground mt-1">{error}</p>
                    <Button onClick={fetchData} variant="outline" className="mt-4">
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Retry
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {sections
                  .filter(s => s.is_visible)
                  .sort((a, b) => a.order - b.order)
                  .map((section) => {
                    const Icon = sectionIcons[section.section_type] || LayoutDashboard;
                    return (
                      <Card key={section.id}>
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Icon className="h-5 w-5 text-primary" />
                              <CardTitle>{section.title}</CardTitle>
                            </div>
                            <Button variant="ghost" size="icon-sm">
                              <ChevronRight className="h-4 w-4" />
                            </Button>
                          </div>
                        </CardHeader>
                        <CardContent>
                          {section.section_type === 'dashboard' && (
                            <div className="space-y-2">
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">Quick Overview</span>
                              </div>
                              <p className="text-sm text-muted-foreground">
                                View key financial metrics at a glance with real-time data from your healthcare operations.
                              </p>
                              <div className="grid grid-cols-2 gap-2 mt-3">
                                <div className="rounded-lg bg-muted/50 p-3 text-center">
                                  <p className="text-xs text-muted-foreground">Active Alerts</p>
                                  <p className="text-lg font-bold">{unreadBriefings.length}</p>
                                </div>
                                <div className="rounded-lg bg-muted/50 p-3 text-center">
                                  <p className="text-xs text-muted-foreground">Briefings</p>
                                  <p className="text-lg font-bold">{briefings.length}</p>
                                </div>
                              </div>
                            </div>
                          )}
                          {section.section_type === 'decisions' && (
                            <div className="space-y-2">
                              <p className="text-sm text-muted-foreground">
                                Track pending decisions and their outcomes across your organization.
                              </p>
                              <Link href="/decisions">
                                <Button variant="outline" size="sm" className="mt-2">View Decisions</Button>
                              </Link>
                            </div>
                          )}
                          {section.section_type === 'briefings' && (
                            <div className="space-y-2">
                              {unreadBriefings.length > 0 ? (
                                <div className="space-y-2">
                                  {unreadBriefings.slice(0, 3).map((briefing) => (
                                    <div
                                      key={briefing.id}
                                      className="flex items-center gap-2 text-sm p-2 rounded-md bg-primary/5 border border-primary/10"
                                    >
                                      <Sparkles className="h-3 w-3 text-primary shrink-0" />
                                      <span className="truncate">{briefing.title}</span>
                                      <Badge variant="outline" className="ml-auto text-xs shrink-0">New</Badge>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-muted-foreground">No unread briefings</p>
                              )}
                            </div>
                          )}
                          {section.section_type === 'assignments' && (
                            <div className="space-y-2">
                              <p className="text-sm text-muted-foreground">
                                Manage your assigned tasks and track completion status.
                              </p>
                              <Link href="/collaboration">
                                <Button variant="outline" size="sm" className="mt-2">View Assignments</Button>
                              </Link>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
              </div>
            )}
          </TabsContent>

          <TabsContent value="briefings" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <p className="text-sm text-muted-foreground">
                  {briefings.length} {briefings.length === 1 ? 'briefing' : 'briefings'}
                  {unreadBriefings.length > 0 && (
                    <span className="text-primary"> · {unreadBriefings.length} unread</span>
                  )}
                </p>
              </div>
              <Button onClick={handleGenerateBriefing} disabled={generating}>
                {generating ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4 mr-2" />
                )}
                Generate Briefing
              </Button>
            </div>

            {loading ? (
              <BriefingSkeleton />
            ) : error ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
                    <h3 className="text-lg font-medium">Error Loading Briefings</h3>
                    <p className="text-muted-foreground mt-1">{error}</p>
                    <Button onClick={fetchData} variant="outline" className="mt-4">
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Retry
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : briefings.length === 0 ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium">No Briefings</h3>
                    <p className="text-muted-foreground mt-1">
                      Generate your first executive briefing to get AI-powered insights
                    </p>
                    <Button onClick={handleGenerateBriefing} className="mt-4" disabled={generating}>
                      <Sparkles className="h-4 w-4 mr-2" />
                      Generate Briefing
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {briefings.map((briefing) => (
                  <Card
                    key={briefing.id}
                    className={briefing.is_read ? '' : 'border-primary/30 bg-primary/[0.02]'}
                  >
                    <CardContent className="py-4">
                      <div className="flex items-start gap-4">
                        <div className={`h-10 w-10 rounded-lg flex items-center justify-center shrink-0 ${briefing.is_read ? 'bg-muted' : 'bg-primary/10'}`}>
                          <FileText className={`h-5 w-5 ${briefing.is_read ? 'text-muted-foreground' : 'text-primary'}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className={`font-medium ${briefing.is_read ? '' : 'text-foreground'}`}>
                              {briefing.title}
                            </h3>
                            {getBriefingTypeBadge(briefing.briefing_type)}
                            {getBriefingPriorityBadge(briefing.priority)}
                            {!briefing.is_read && (
                              <Badge variant="default" className="gap-1 text-xs">New</Badge>
                            )}
                          </div>
                          {briefing.summary && (
                            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{briefing.summary}</p>
                          )}
                          <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {formatDate(briefing.created_at)}
                            </span>
                            {briefing.read_at && (
                              <span className="flex items-center gap-1">
                                <CheckCircle className="h-3 w-3" />
                                Read {formatDate(briefing.read_at)}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="shrink-0">
                          {!briefing.is_read && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleMarkBriefingRead(briefing.id)}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              Mark Read
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

          <TabsContent value="notifications" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5" />
                  Notification Preferences
                </CardTitle>
                <CardDescription>
                  Configure how and when you receive notifications
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="text-base">Email Notifications</Label>
                      <p className="text-sm text-muted-foreground">
                        Receive notifications via email
                      </p>
                    </div>
                    <Button
                      variant={notifications.email_enabled ? 'default' : 'outline'}
                      size="sm"
                      onClick={() =>
                        setNotifications({ ...notifications, email_enabled: !notifications.email_enabled })
                      }
                    >
                      {notifications.email_enabled ? 'Enabled' : 'Disabled'}
                    </Button>
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <Label>Digest Frequency</Label>
                    <Select
                      value={notifications.digest_frequency}
                      onValueChange={(val) =>
                        val && setNotifications({ ...notifications, digest_frequency: val })
                      }
                    >
                      <SelectTrigger className="w-full max-w-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="realtime">Real-time</SelectItem>
                        <SelectItem value="daily">Daily Digest</SelectItem>
                        <SelectItem value="weekly">Weekly Digest</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Separator />

                  <div className="space-y-3">
                    <Label>Notification Categories</Label>
                    {[
                      { key: 'briefings_enabled' as const, label: 'Executive Briefings', icon: FileText, desc: 'AI-generated insights and summaries' },
                      { key: 'alerts_enabled' as const, label: 'Financial Alerts', icon: Bell, desc: 'Critical alerts and anomalies' },
                      { key: 'decisions_enabled' as const, label: 'Decision Updates', icon: GitMerge, desc: 'Decision approvals and status changes' },
                      { key: 'comments_enabled' as const, label: 'Comments & Mentions', icon: Mail, desc: 'Team discussions and @mentions' },
                    ].map(({ key, label, icon: Icon, desc }) => (
                      <div
                        key={key}
                        className="flex items-center justify-between rounded-lg border p-4"
                      >
                        <div className="flex items-center gap-3">
                          <div className="h-9 w-9 rounded-lg bg-muted flex items-center justify-center">
                            <Icon className="h-4 w-4 text-muted-foreground" />
                          </div>
                          <div>
                            <p className="text-sm font-medium">{label}</p>
                            <p className="text-xs text-muted-foreground">{desc}</p>
                          </div>
                        </div>
                        <Button
                          variant={notifications[key] ? 'default' : 'outline'}
                          size="sm"
                          onClick={() =>
                            setNotifications({ ...notifications, [key]: !notifications[key] })
                          }
                        >
                          {notifications[key] ? 'On' : 'Off'}
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button onClick={handleUpdateNotifications} disabled={saving}>
                    {saving ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4 mr-2" />
                    )}
                    Save Preferences
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Layout Customization
                </CardTitle>
                <CardDescription>
                  Customize the appearance and layout of your workspace
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="text-base flex items-center gap-2">
                        <Rows3 className="h-4 w-4" />
                        Compact Mode
                      </Label>
                      <p className="text-sm text-muted-foreground">
                        Reduce spacing and padding for a denser layout
                      </p>
                    </div>
                    <Button
                      variant={compactMode ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setCompactMode(!compactMode)}
                    >
                      {compactMode ? 'On' : 'Off'}
                    </Button>
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <Palette className="h-4 w-4" />
                      Theme
                    </Label>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { id: 'default', name: 'Default', colors: ['bg-primary', 'bg-muted', 'bg-card'] },
                        { id: 'ocean', name: 'Ocean', colors: ['bg-blue-500', 'bg-blue-100', 'bg-blue-50'] },
                        { id: 'forest', name: 'Forest', colors: ['bg-emerald-500', 'bg-emerald-100', 'bg-emerald-50'] },
                      ].map((t) => (
                        <button
                          key={t.id}
                          className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-colors ${
                            theme === t.id
                              ? 'border-primary bg-primary/5'
                              : 'border-transparent hover:bg-muted/50'
                          }`}
                          onClick={() => setTheme(t.id)}
                        >
                          <div className="flex gap-1">
                            {t.colors.map((color, i) => (
                              <div key={i} className={`h-4 w-4 rounded-full ${color}`} />
                            ))}
                          </div>
                          <span className="text-sm font-medium">{t.name}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-3">
                    <Label>Visible Sections</Label>
                    <p className="text-sm text-muted-foreground">
                      Choose which sections appear on your dashboard
                    </p>
                    <div className="space-y-2">
                      {sections.map((section) => {
                        const Icon = sectionIcons[section.section_type] || LayoutDashboard;
                        return (
                          <div
                            key={section.id}
                            className="flex items-center justify-between rounded-lg border p-3"
                          >
                            <div className="flex items-center gap-3">
                              <Icon className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm font-medium">{section.title}</span>
                            </div>
                            <Button
                              variant={section.is_visible ? 'default' : 'outline'}
                              size="sm"
                              onClick={() => handleToggleSection(section.id, !section.is_visible)}
                            >
                              {section.is_visible ? 'Visible' : 'Hidden'}
                            </Button>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button onClick={handleUpdateLayout} disabled={saving}>
                    {saving ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4 mr-2" />
                    )}
                    Save Layout
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
