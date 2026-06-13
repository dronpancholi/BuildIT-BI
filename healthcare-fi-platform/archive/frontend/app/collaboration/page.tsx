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
  MessageSquare,
  CheckSquare,
  Eye,
  Plus,
  RefreshCw,
  Send,
  CheckCircle,
  Circle,
  Clock,
  AlertTriangle,
  MoreHorizontal,
  Edit2,
  Archive,
  User,
  Bell,
  Target,
} from 'lucide-react';
import { collaborationAPI } from '@/lib/api/client';

interface Comment {
  id: string;
  content: string;
  author: string;
  author_name?: string;
  target_type: string;
  target_id: string;
  is_resolved: boolean;
  created_at: string;
  updated_at?: string;
  parent_id?: string;
  replies?: Comment[];
}

interface Assignment {
  id: string;
  title: string;
  description?: string;
  assigned_to: string;
  assigned_by?: string;
  status: string;
  priority: string;
  due_date?: string;
  created_at: string;
  completed_at?: string;
  target_type?: string;
  target_id?: string;
}

interface WatchlistItem {
  id: string;
  name: string;
  target_type: string;
  target_id: string;
  notify_on_changes: boolean;
  notify_on_comments: boolean;
  notify_on_alerts: boolean;
  created_at: string;
}

function getPriorityBadge(priority: string) {
  switch (priority?.toLowerCase()) {
    case 'critical':
      return <Badge variant="destructive" className="gap-1">Critical</Badge>;
    case 'high':
      return <Badge variant="secondary" className="gap-1 bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300">High</Badge>;
    case 'medium':
      return <Badge variant="secondary" className="gap-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">Medium</Badge>;
    case 'low':
      return <Badge variant="outline" className="gap-1">Low</Badge>;
    default:
      return <Badge variant="outline">{priority}</Badge>;
  }
}

function getAssignmentStatusBadge(status: string) {
  switch (status?.toLowerCase()) {
    case 'completed':
      return (
        <Badge variant="secondary" className="gap-1 text-healthcare-green border-healthcare-green/30 bg-healthcare-green/10">
          <CheckCircle className="h-3 w-3" />
          Completed
        </Badge>
      );
    case 'in_progress':
      return (
        <Badge variant="default" className="gap-1">
          <Clock className="h-3 w-3" />
          In Progress
        </Badge>
      );
    case 'open':
      return (
        <Badge variant="outline" className="gap-1">
          <Circle className="h-3 w-3" />
          Open
        </Badge>
      );
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

function ListSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="rounded-lg border p-4 space-y-3">
          <div className="flex items-center gap-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <div className="flex-1 space-y-1">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-3 w-24" />
            </div>
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-3/4" />
        </div>
      ))}
    </div>
  );
}

export default function CollaborationPage() {
  const [activeTab, setActiveTab] = useState('comments');
  const [comments, setComments] = useState<Comment[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [watchlists, setWatchlists] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [assignmentDialogOpen, setAssignmentDialogOpen] = useState(false);
  const [watchlistDialogOpen, setWatchlistDialogOpen] = useState(false);
  const [creating, setCreating] = useState(false);

  const [newComment, setNewComment] = useState({
    content: '',
    target_type: 'dashboard',
    target_id: '00000000-0000-0000-0000-000000000001',
  });

  const [newAssignment, setNewAssignment] = useState({
    title: '',
    description: '',
    assigned_to: '',
    priority: 'medium',
    due_date: '',
  });

  const [newWatchlist, setNewWatchlist] = useState({
    name: '',
    target_type: 'dashboard',
    target_id: '00000000-0000-0000-0000-000000000001',
    notify_on_changes: true,
    notify_on_comments: true,
    notify_on_alerts: true,
  });

  const [commentFilter, setCommentFilter] = useState<'all' | 'unresolved' | 'resolved'>('all');
  const [assignmentFilter, setAssignmentFilter] = useState<string>('all');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [assignmentsRes, watchlistsRes] = await Promise.allSettled([
        collaborationAPI.listAssignments(),
        collaborationAPI.listWatchlists(),
      ]);

      if (assignmentsRes.status === 'fulfilled') {
        setAssignments(assignmentsRes.value.data?.assignments || assignmentsRes.value.data || []);
      }
      if (watchlistsRes.status === 'fulfilled') {
        setWatchlists(watchlistsRes.value.data?.watchlists || watchlistsRes.value.data || []);
      }

      try {
        const commentsRes = await collaborationAPI.listComments({
          target_type: 'dashboard',
          target_id: '00000000-0000-0000-0000-000000000001',
        });
        setComments(commentsRes.data?.comments || commentsRes.data || []);
      } catch {
        setComments([]);
      }

      const anyFailed = [assignmentsRes, watchlistsRes].some(r => r.status === 'rejected');
      if (anyFailed) {
        setError('Some data failed to load. Showing available data.');
      }
    } catch (err) {
      setError('Failed to load collaboration data. Please try again.');
      console.error('Failed to fetch collaboration data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateComment = async () => {
    setCreating(true);
    try {
      await collaborationAPI.createComment(newComment);
      setCommentDialogOpen(false);
      setNewComment({ content: '', target_type: 'dashboard', target_id: '00000000-0000-0000-0000-000000000001' });
      fetchData();
    } catch (err) {
      console.error('Failed to create comment:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleResolveComment = async (id: string) => {
    try {
      await collaborationAPI.resolveComment(id);
      setComments(comments.map(c => (c.id === id ? { ...c, is_resolved: true } : c)));
    } catch (err) {
      console.error('Failed to resolve comment:', err);
    }
  };

  const handleCreateAssignment = async () => {
    setCreating(true);
    try {
      await collaborationAPI.createAssignment(newAssignment);
      setAssignmentDialogOpen(false);
      setNewAssignment({ title: '', description: '', assigned_to: '', priority: 'medium', due_date: '' });
      fetchData();
    } catch (err) {
      console.error('Failed to create assignment:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleCompleteAssignment = async (id: string) => {
    try {
      await collaborationAPI.completeAssignment(id);
      setAssignments(assignments.map(a => (a.id === id ? { ...a, status: 'completed', completed_at: new Date().toISOString() } : a)));
    } catch (err) {
      console.error('Failed to complete assignment:', err);
    }
  };

  const handleReopenAssignment = async (id: string) => {
    try {
      await collaborationAPI.updateAssignment(id, { status: 'open' });
      setAssignments(assignments.map(a => (a.id === id ? { ...a, status: 'open', completed_at: undefined } : a)));
    } catch (err) {
      console.error('Failed to reopen assignment:', err);
    }
  };

  const handleCreateWatchlist = async () => {
    setCreating(true);
    try {
      await collaborationAPI.createWatchlist(newWatchlist);
      setWatchlistDialogOpen(false);
      setNewWatchlist({
        name: '',
        target_type: 'dashboard',
        target_id: '00000000-0000-0000-0000-000000000001',
        notify_on_changes: true,
        notify_on_comments: true,
        notify_on_alerts: true,
      });
      fetchData();
    } catch (err) {
      console.error('Failed to create watchlist:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleToggleNotification = async (id: string, field: keyof Pick<WatchlistItem, 'notify_on_changes' | 'notify_on_comments' | 'notify_on_alerts'>) => {
    const item = watchlists.find(w => w.id === id);
    if (!item) return;
    const updated = { ...item, [field]: !item[field] };
    try {
      await collaborationAPI.updateWatchlist(id, updated);
      setWatchlists(watchlists.map(w => (w.id === id ? updated : w)));
    } catch (err) {
      console.error('Failed to update watchlist:', err);
    }
  };

  const handleRemoveWatchlistItem = async (watchlistId: string, itemId: string) => {
    try {
      await collaborationAPI.removeWatchlistItem(watchlistId, itemId);
      setWatchlists(watchlists.filter(w => w.id !== watchlistId));
    } catch (err) {
      console.error('Failed to remove watchlist item:', err);
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

  const formatShortDate = (dateStr?: string) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  const filteredComments = comments.filter(c => {
    if (commentFilter === 'unresolved') return !c.is_resolved;
    if (commentFilter === 'resolved') return c.is_resolved;
    return true;
  });

  const filteredAssignments = assignments.filter(a => {
    if (assignmentFilter === 'all') return true;
    return a.status?.toLowerCase() === assignmentFilter;
  });

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <MessageSquare className="h-8 w-8 text-primary" />
              Collaboration Hub
            </h1>
            <p className="text-muted-foreground">
              Discuss, assign, and track financial insights across your team
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
            <TabsTrigger value="comments">Comments</TabsTrigger>
            <TabsTrigger value="assignments">Assignments</TabsTrigger>
            <TabsTrigger value="watchlists">Watchlists</TabsTrigger>
          </TabsList>

          <TabsContent value="comments" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button
                  variant={commentFilter === 'all' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setCommentFilter('all')}
                >
                  All ({comments.length})
                </Button>
                <Button
                  variant={commentFilter === 'unresolved' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setCommentFilter('unresolved')}
                >
                  Unresolved ({comments.filter(c => !c.is_resolved).length})
                </Button>
                <Button
                  variant={commentFilter === 'resolved' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setCommentFilter('resolved')}
                >
                  Resolved ({comments.filter(c => c.is_resolved).length})
                </Button>
              </div>
              <Dialog open={commentDialogOpen} onOpenChange={setCommentDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    New Comment
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-lg">
                  <DialogHeader>
                    <DialogTitle>Add Comment</DialogTitle>
                    <DialogDescription>
                      Start a discussion or leave feedback on a financial insight
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-2">
                    <div className="space-y-2">
                      <Label>Target</Label>
                      <Select
                        value={newComment.target_type}
                        onValueChange={(val) => val && setNewComment({ ...newComment, target_type: val })}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="dashboard">Dashboard</SelectItem>
                          <SelectItem value="report">Report</SelectItem>
                          <SelectItem value="insight">Insight</SelectItem>
                          <SelectItem value="decision">Decision</SelectItem>
                          <SelectItem value="kpi">KPI</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="comment-content">Comment</Label>
                      <textarea
                        id="comment-content"
                        className="flex min-h-[120px] w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                        placeholder="Share your thoughts..."
                        value={newComment.content}
                        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                          setNewComment({ ...newComment, content: e.target.value })
                        }
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setCommentDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      onClick={handleCreateComment}
                      disabled={!newComment.content.trim() || creating}
                    >
                      {creating ? (
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4 mr-2" />
                      )}
                      Post Comment
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            {loading ? (
              <ListSkeleton />
            ) : error ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
                    <h3 className="text-lg font-medium">Error Loading Comments</h3>
                    <p className="text-muted-foreground mt-1">{error}</p>
                    <Button onClick={fetchData} variant="outline" className="mt-4">
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Retry
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : filteredComments.length === 0 ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium">
                      {commentFilter === 'all' ? 'No Comments Yet' : `No ${commentFilter} comments`}
                    </h3>
                    <p className="text-muted-foreground mt-1">
                      {commentFilter === 'all'
                        ? 'Start a discussion by adding the first comment'
                        : 'Try a different filter or add new comments'}
                    </p>
                    {commentFilter === 'all' && (
                      <Button onClick={() => setCommentDialogOpen(true)} className="mt-4">
                        <Plus className="h-4 w-4 mr-2" />
                        Add Comment
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {filteredComments.map((comment) => (
                  <Card key={comment.id} className={comment.is_resolved ? 'opacity-60' : ''}>
                    <CardContent className="py-4">
                      <div className="flex items-start gap-3">
                        <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                          <User className="h-4 w-4 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-sm">
                              {comment.author_name || comment.author || 'Unknown'}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {formatDate(comment.created_at)}
                            </span>
                            {comment.is_resolved && (
                              <Badge variant="secondary" className="gap-1 text-healthcare-green">
                                <CheckCircle className="h-3 w-3" />
                                Resolved
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm mt-1 text-foreground/90">{comment.content}</p>
                          <div className="flex items-center gap-3 mt-2">
                            <Badge variant="outline" className="text-xs">
                              {comment.target_type}
                            </Badge>
                            {!comment.is_resolved && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 text-xs"
                                onClick={() => handleResolveComment(comment.id)}
                              >
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Resolve
                              </Button>
                            )}
                            <Button variant="ghost" size="sm" className="h-6 text-xs">
                              <Edit2 className="h-3 w-3 mr-1" />
                              Edit
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="assignments" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button
                  variant={assignmentFilter === 'all' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setAssignmentFilter('all')}
                >
                  All ({assignments.length})
                </Button>
                <Button
                  variant={assignmentFilter === 'open' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setAssignmentFilter('open')}
                >
                  Open ({assignments.filter(a => a.status?.toLowerCase() === 'open').length})
                </Button>
                <Button
                  variant={assignmentFilter === 'in_progress' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setAssignmentFilter('in_progress')}
                >
                  In Progress ({assignments.filter(a => a.status?.toLowerCase() === 'in_progress').length})
                </Button>
                <Button
                  variant={assignmentFilter === 'completed' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setAssignmentFilter('completed')}
                >
                  Completed ({assignments.filter(a => a.status?.toLowerCase() === 'completed').length})
                </Button>
              </div>
              <Dialog open={assignmentDialogOpen} onOpenChange={setAssignmentDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    New Assignment
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>Create Assignment</DialogTitle>
                    <DialogDescription>
                      Assign a task to a team member with priority and due date
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-2">
                    <div className="space-y-2">
                      <Label htmlFor="assignment-title">Task Title</Label>
                      <Input
                        id="assignment-title"
                        placeholder="e.g. Review Q3 revenue forecast"
                        value={newAssignment.title}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setNewAssignment({ ...newAssignment, title: e.target.value })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="assignment-desc">Description</Label>
                      <textarea
                        id="assignment-desc"
                        className="flex min-h-[80px] w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
                        placeholder="Optional description..."
                        value={newAssignment.description}
                        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                          setNewAssignment({ ...newAssignment, description: e.target.value })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="assignment-assignee">Assign To</Label>
                      <Input
                        id="assignment-assignee"
                        placeholder="Email or user ID"
                        value={newAssignment.assigned_to}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setNewAssignment({ ...newAssignment, assigned_to: e.target.value })
                        }
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Priority</Label>
                        <Select
                          value={newAssignment.priority}
                          onValueChange={(val) => val && setNewAssignment({ ...newAssignment, priority: val })}
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="low">Low</SelectItem>
                            <SelectItem value="medium">Medium</SelectItem>
                            <SelectItem value="high">High</SelectItem>
                            <SelectItem value="critical">Critical</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="assignment-due">Due Date</Label>
                        <Input
                          id="assignment-due"
                          type="date"
                          value={newAssignment.due_date}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                            setNewAssignment({ ...newAssignment, due_date: e.target.value })
                          }
                        />
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setAssignmentDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      onClick={handleCreateAssignment}
                      disabled={!newAssignment.title.trim() || !newAssignment.assigned_to.trim() || creating}
                    >
                      {creating ? (
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <CheckSquare className="h-4 w-4 mr-2" />
                      )}
                      Create Assignment
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            {loading ? (
              <ListSkeleton />
            ) : error ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
                    <h3 className="text-lg font-medium">Error Loading Assignments</h3>
                    <p className="text-muted-foreground mt-1">{error}</p>
                    <Button onClick={fetchData} variant="outline" className="mt-4">
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Retry
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : filteredAssignments.length === 0 ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <CheckSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium">
                      {assignmentFilter === 'all' ? 'No Assignments' : `No ${assignmentFilter} assignments`}
                    </h3>
                    <p className="text-muted-foreground mt-1">
                      {assignmentFilter === 'all'
                        ? 'Create your first assignment to track team tasks'
                        : 'Try a different filter or create new assignments'}
                    </p>
                    {assignmentFilter === 'all' && (
                      <Button onClick={() => setAssignmentDialogOpen(true)} className="mt-4">
                        <Plus className="h-4 w-4 mr-2" />
                        Create Assignment
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {filteredAssignments.map((assignment) => (
                  <Card key={assignment.id}>
                    <CardContent className="py-4">
                      <div className="flex items-start gap-4">
                        <div className="mt-1">
                          {assignment.status?.toLowerCase() === 'completed' ? (
                            <CheckCircle className="h-5 w-5 text-healthcare-green" />
                          ) : (
                            <Circle className="h-5 w-5 text-muted-foreground" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className={`font-medium ${assignment.status?.toLowerCase() === 'completed' ? 'line-through text-muted-foreground' : ''}`}>
                              {assignment.title}
                            </h3>
                            {getAssignmentStatusBadge(assignment.status)}
                            {getPriorityBadge(assignment.priority)}
                          </div>
                          {assignment.description && (
                            <p className="text-sm text-muted-foreground mt-1">{assignment.description}</p>
                          )}
                          <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {assignment.assigned_to}
                            </span>
                            {assignment.due_date && (
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                Due {formatShortDate(assignment.due_date)}
                              </span>
                            )}
                            {assignment.completed_at && (
                              <span>Completed {formatShortDate(assignment.completed_at)}</span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          {assignment.status?.toLowerCase() !== 'completed' ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleCompleteAssignment(assignment.id)}
                            >
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleReopenAssignment(assignment.id)}
                            >
                              <Circle className="h-4 w-4" />
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

          <TabsContent value="watchlists" className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {watchlists.length} {watchlists.length === 1 ? 'watchlist' : 'watchlists'}
              </p>
              <Dialog open={watchlistDialogOpen} onOpenChange={setWatchlistDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    New Watchlist
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>Create Watchlist</DialogTitle>
                    <DialogDescription>
                      Monitor financial entities and receive notifications on changes
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-2">
                    <div className="space-y-2">
                      <Label htmlFor="watchlist-name">Watchlist Name</Label>
                      <Input
                        id="watchlist-name"
                        placeholder="e.g. Revenue KPIs"
                        value={newWatchlist.name}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setNewWatchlist({ ...newWatchlist, name: e.target.value })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Entity Type</Label>
                      <Select
                        value={newWatchlist.target_type}
                        onValueChange={(val) => val && setNewWatchlist({ ...newWatchlist, target_type: val })}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="dashboard">Dashboard</SelectItem>
                          <SelectItem value="kpi">KPI</SelectItem>
                          <SelectItem value="report">Report</SelectItem>
                          <SelectItem value="decision">Decision</SelectItem>
                          <SelectItem value="insight">Insight</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-3">
                      <Label>Notifications</Label>
                      <div className="space-y-2">
                        {[
                          { key: 'notify_on_changes' as const, label: 'Changes', icon: Target },
                          { key: 'notify_on_comments' as const, label: 'Comments', icon: MessageSquare },
                          { key: 'notify_on_alerts' as const, label: 'Alerts', icon: Bell },
                        ].map(({ key, label, icon: Icon }) => (
                          <label
                            key={key}
                            className="flex items-center gap-3 rounded-lg border p-3 cursor-pointer hover:bg-muted/50"
                          >
                            <input
                              type="checkbox"
                              className="h-4 w-4 rounded border-input"
                              checked={newWatchlist[key]}
                              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                setNewWatchlist({ ...newWatchlist, [key]: e.target.checked })
                              }
                            />
                            <Icon className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm">{label}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setWatchlistDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      onClick={handleCreateWatchlist}
                      disabled={!newWatchlist.name.trim() || creating}
                    >
                      {creating ? (
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Eye className="h-4 w-4 mr-2" />
                      )}
                      Create Watchlist
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            {loading ? (
              <ListSkeleton />
            ) : error ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
                    <h3 className="text-lg font-medium">Error Loading Watchlists</h3>
                    <p className="text-muted-foreground mt-1">{error}</p>
                    <Button onClick={fetchData} variant="outline" className="mt-4">
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Retry
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : watchlists.length === 0 ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <Eye className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium">No Watchlists</h3>
                    <p className="text-muted-foreground mt-1">
                      Create watchlists to monitor financial metrics and receive notifications
                    </p>
                    <Button onClick={() => setWatchlistDialogOpen(true)} className="mt-4">
                      <Plus className="h-4 w-4 mr-2" />
                      Create Watchlist
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {watchlists.map((item) => (
                  <Card key={item.id}>
                    <CardContent className="py-4">
                      <div className="flex items-start gap-4">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                          <Eye className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium">{item.name}</h3>
                            <Badge variant="outline" className="text-xs">
                              {item.target_type}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 mt-2">
                            {[
                              { key: 'notify_on_changes' as const, label: 'Changes', icon: Target },
                              { key: 'notify_on_comments' as const, label: 'Comments', icon: MessageSquare },
                              { key: 'notify_on_alerts' as const, label: 'Alerts', icon: Bell },
                            ].map(({ key, label, icon: Icon }) => (
                              <button
                                key={key}
                                className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-md transition-colors ${
                                  item[key]
                                    ? 'bg-primary/10 text-primary'
                                    : 'bg-muted text-muted-foreground'
                                }`}
                                onClick={() => handleToggleNotification(item.id, key)}
                              >
                                <Icon className="h-3 w-3" />
                                {label}
                              </button>
                            ))}
                          </div>
                          <p className="text-xs text-muted-foreground mt-2">
                            Created {formatDate(item.created_at)}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleRemoveWatchlistItem(item.id, item.id)}
                        >
                          <Archive className="h-4 w-4 text-muted-foreground" />
                        </Button>
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
