'use client';

import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  LayoutDashboard,
  Plus,
  Grid3x3,
  Clock,
  User,
  Tag,
  RefreshCw,
  AlertTriangle,
  Eye,
  Pencil,
  Trash2,
  Copy,
  History,
  Layers,
} from 'lucide-react';
import { dashboardsAPI } from '@/lib/api/client';

interface DashboardWidget {
  id: string;
  type: string;
  title: string;
  config?: any;
  position?: { x: number; y: number; w: number; h: number };
}

interface Dashboard {
  id: string;
  name: string;
  description?: string;
  owner?: string;
  tags?: string[];
  widgets?: DashboardWidget[];
  created_at?: string;
  updated_at?: string;
}

interface DashboardVersion {
  id: string;
  version: number;
  created_at?: string;
  created_by?: string;
  description?: string;
}

interface PrebuiltTemplate {
  id: string;
  name: string;
  description?: string;
  widget_count?: number;
  category?: string;
}

export default function DashboardsPage() {
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedDashboard, setSelectedDashboard] = useState<Dashboard | null>(null);
  const [selectedVersions, setSelectedVersions] = useState<DashboardVersion[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);

  const [templates, setTemplates] = useState<PrebuiltTemplate[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);

  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newTags, setNewTags] = useState('');
  const [creating, setCreating] = useState(false);

  const [previewDashboard, setPreviewDashboard] = useState<Dashboard | null>(null);

  useEffect(() => {
    fetchDashboards();
    fetchTemplates();
  }, []);

  const fetchDashboards = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await dashboardsAPI.list();
      setDashboards(response.data?.items || response.data || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load dashboards');
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    setTemplatesLoading(true);
    try {
      const response = await dashboardsAPI.getPrebuiltTemplates();
      setTemplates(response.data?.items || response.data || []);
    } catch {
      setTemplates([]);
    } finally {
      setTemplatesLoading(false);
    }
  };

  const fetchVersions = async (dashboardId: string) => {
    setVersionsLoading(true);
    try {
      const response = await dashboardsAPI.getVersions(dashboardId);
      setSelectedVersions(response.data?.items || response.data || []);
    } catch {
      setSelectedVersions([]);
    } finally {
      setVersionsLoading(false);
    }
  };

  const handleCreateDashboard = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const tags = newTags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);
      await dashboardsAPI.create({
        name: newName,
        description: newDescription,
        tags,
      });
      setNewName('');
      setNewDescription('');
      setNewTags('');
      setCreateDialogOpen(false);
      fetchDashboards();
    } catch (err) {
      console.error('Failed to create dashboard:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleSelectDashboard = (dashboard: Dashboard) => {
    setSelectedDashboard(dashboard);
    setPreviewDashboard(dashboard);
    fetchVersions(dashboard.id);
  };

  const handleDuplicateDashboard = async (dashboard: Dashboard) => {
    try {
      await dashboardsAPI.create({
        name: `${dashboard.name} (Copy)`,
        description: dashboard.description,
        tags: dashboard.tags,
      });
      fetchDashboards();
    } catch (err) {
      console.error('Failed to duplicate dashboard:', err);
    }
  };

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
            </div>
            <Skeleton className="h-3 w-full" />
            <div className="flex gap-2">
              <Skeleton className="h-5 w-14 rounded-full" />
              <Skeleton className="h-5 w-20 rounded-full" />
            </div>
            <div className="flex items-center justify-between pt-2 border-t">
              <Skeleton className="h-3 w-24" />
              <div className="flex gap-2">
                <Skeleton className="h-8 w-16 rounded-lg" />
                <Skeleton className="h-8 w-16 rounded-lg" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  const renderError = () => (
    <Card className="flex items-center justify-center py-12">
      <div className="text-center">
        <AlertTriangle className="h-10 w-10 text-destructive mx-auto mb-3" />
        <p className="text-sm font-medium mb-1">Failed to load dashboards</p>
        <p className="text-xs text-muted-foreground mb-4">{error}</p>
        <Button variant="outline" size="sm" onClick={fetchDashboards}>
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
          Retry
        </Button>
      </div>
    </Card>
  );

  const renderEmpty = () => (
    <Card className="flex items-center justify-center py-12">
      <div className="text-center">
        <LayoutDashboard className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm font-medium mb-1">No Dashboards</p>
        <p className="text-xs text-muted-foreground mb-4">
          Create your first dashboard to get started
        </p>
        <Button size="sm" onClick={() => setCreateDialogOpen(true)}>
          <Plus className="h-3.5 w-3.5 mr-1.5" />
          Create Dashboard
        </Button>
      </div>
    </Card>
  );

  const renderWidgetGrid = (widgets: DashboardWidget[]) => {
    if (!widgets || widgets.length === 0) {
      return (
        <div className="grid grid-cols-3 gap-2 p-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-24 rounded-lg border border-dashed border-border bg-muted/30 flex items-center justify-center"
            >
              <span className="text-[10px] text-muted-foreground">Widget {i + 1}</span>
            </div>
          ))}
        </div>
      );
    }

    return (
      <div className="grid grid-cols-3 gap-2 p-4">
        {widgets.map((widget) => (
          <div
            key={widget.id}
            className="h-24 rounded-lg border bg-card p-2 flex flex-col justify-between"
          >
            <p className="text-[10px] font-medium truncate">{widget.title}</p>
            <Badge variant="outline" className="text-[9px] w-fit">
              {widget.type}
            </Badge>
          </div>
        ))}
      </div>
    );
  };

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <LayoutDashboard className="h-8 w-8 text-primary" />
              Dashboard Builder
            </h1>
            <p className="text-muted-foreground">
              Create and manage interactive financial dashboards
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={fetchDashboards}>
              <RefreshCw className="h-4 w-4 mr-1.5" />
              Refresh
            </Button>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-1.5" />
                  New Dashboard
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Create Dashboard</DialogTitle>
                  <DialogDescription>
                    Build a new dashboard to visualize your financial data
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-2">
                  <div className="space-y-2">
                    <Label htmlFor="dash-name">Name</Label>
                    <Input
                      id="dash-name"
                      placeholder="e.g. Revenue Overview"
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="dash-desc">Description</Label>
                    <Input
                      id="dash-desc"
                      placeholder="Brief description of this dashboard"
                      value={newDescription}
                      onChange={(e) => setNewDescription(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="dash-tags">Tags (comma separated)</Label>
                    <Input
                      id="dash-tags"
                      placeholder="e.g. revenue, finance, Q4"
                      value={newTags}
                      onChange={(e) => setNewTags(e.target.value)}
                    />
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
                    onClick={handleCreateDashboard}
                    disabled={!newName.trim() || creating}
                  >
                    {creating ? (
                      <RefreshCw className="h-4 w-4 mr-1.5 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4 mr-1.5" />
                    )}
                    Create
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-4">
          <div className={`${selectedDashboard ? 'lg:col-span-3' : 'lg:col-span-4'} space-y-4`}>
            <h2 className="text-lg font-semibold">Your Dashboards</h2>

            {loading ? (
              renderSkeletons(6)
            ) : error ? (
              renderError()
            ) : dashboards.length === 0 ? (
              renderEmpty()
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {dashboards.map((dashboard) => (
                  <Card
                    key={dashboard.id}
                    className={`cursor-pointer transition-all hover:shadow-md ${
                      selectedDashboard?.id === dashboard.id ? 'ring-2 ring-primary' : ''
                    }`}
                    onClick={() => handleSelectDashboard(dashboard)}
                  >
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                          <LayoutDashboard className="h-5 w-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{dashboard.name}</p>
                          {dashboard.owner && (
                            <p className="text-xs text-muted-foreground flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {dashboard.owner}
                            </p>
                          )}
                        </div>
                      </div>

                      {dashboard.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {dashboard.description}
                        </p>
                      )}

                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-[10px] gap-1">
                          <Grid3x3 className="h-3 w-3" />
                          {dashboard.widgets?.length || 0} widgets
                        </Badge>
                        {dashboard.tags?.slice(0, 2).map((tag) => (
                          <Badge key={tag} variant="secondary" className="text-[10px] gap-1">
                            <Tag className="h-3 w-3" />
                            {tag}
                          </Badge>
                        ))}
                        {(dashboard.tags?.length || 0) > 2 && (
                          <Badge variant="secondary" className="text-[10px]">
                            +{(dashboard.tags?.length || 0) - 2}
                          </Badge>
                        )}
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t">
                        {dashboard.updated_at && (
                          <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {new Date(dashboard.updated_at).toLocaleDateString()}
                          </span>
                        )}
                        <div className="flex gap-1 ml-auto">
                          <Button
                            variant="ghost"
                            size="icon-xs"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSelectDashboard(dashboard);
                            }}
                          >
                            <Eye className="h-3 w-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-xs"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDuplicateDashboard(dashboard);
                            }}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            <div className="space-y-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Layers className="h-5 w-5 text-muted-foreground" />
                Pre-built Templates
              </h2>
              {templatesLoading ? (
                renderSkeletons(3)
              ) : templates.length === 0 ? (
                <Card className="py-8">
                  <div className="text-center text-sm text-muted-foreground">
                    No templates available
                  </div>
                </Card>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {templates.map((template) => (
                    <Card key={template.id} className="hover:shadow-md transition-all">
                      <CardContent className="p-4 space-y-3">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-lg bg-secondary/50 flex items-center justify-center text-secondary-foreground">
                            <LayoutDashboard className="h-5 w-5" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{template.name}</p>
                            {template.category && (
                              <p className="text-xs text-muted-foreground">{template.category}</p>
                            )}
                          </div>
                        </div>
                        {template.description && (
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {template.description}
                          </p>
                        )}
                        <div className="flex items-center justify-between pt-2 border-t">
                          <Badge variant="outline" className="text-[10px]">
                            {template.widget_count || 0} widgets
                          </Badge>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={async () => {
                              try {
                                await dashboardsAPI.create({
                                  name: template.name,
                                  description: template.description,
                                  template_id: template.id,
                                });
                                fetchDashboards();
                              } catch (err) {
                                console.error('Failed to create from template:', err);
                              }
                            }}
                          >
                            Use Template
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>

          {selectedDashboard && (
            <div className="lg:col-span-1 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    <span className="truncate">{selectedDashboard.name}</span>
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => {
                        setSelectedDashboard(null);
                        setPreviewDashboard(null);
                        setSelectedVersions([]);
                      }}
                    >
                      ×
                    </Button>
                  </CardTitle>
                  <CardDescription>Widget Preview</CardDescription>
                </CardHeader>
                <CardContent>
                  {renderWidgetGrid(previewDashboard?.widgets || [])}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <History className="h-4 w-4" />
                    Version History
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {versionsLoading ? (
                    <div className="space-y-2">
                      {Array.from({ length: 3 }).map((_, i) => (
                        <div key={i} className="flex items-center gap-3">
                          <Skeleton className="h-8 w-8 rounded-full" />
                          <div className="flex-1 space-y-1">
                            <Skeleton className="h-3 w-3/4" />
                            <Skeleton className="h-2 w-1/2" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : selectedVersions.length === 0 ? (
                    <p className="text-xs text-muted-foreground text-center py-4">
                      No version history
                    </p>
                  ) : (
                    <div className="space-y-2 max-h-60 overflow-auto">
                      {selectedVersions.map((version) => (
                        <div
                          key={version.id}
                          className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50"
                        >
                          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-medium">
                            v{version.version}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium">
                              {version.description || `Version ${version.version}`}
                            </p>
                            {version.created_at && (
                              <p className="text-[10px] text-muted-foreground">
                                {new Date(version.created_at).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
                <div className="px-4 pb-4">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => fetchVersions(selectedDashboard.id)}
                  >
                    <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
                    Refresh History
                  </Button>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
