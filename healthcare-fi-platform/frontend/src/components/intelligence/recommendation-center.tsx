"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SkeletonStatCard, SkeletonCard } from "@/components/ui/skeleton";
import { Sparkline } from "@/components/ui/sparkline";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { intelligenceAPI } from "@/lib/api/client";
import { formatPercentage, formatCurrency, getConfidenceColor } from "@/lib/utils/format";
import {
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  User,
  Target,
  Shield,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";

interface Recommendation {
  id: string;
  recommendation_type: string;
  title: string;
  summary: string;
  expected_impact_value: number;
  expected_impact_unit: string;
  confidence_in_impact: number;
  priority_score: number;
  priority_rank: number;
  recommendation_status: string;
  assigned_to_name: string;
  period_start: string;
  scores: Record<string, number>;
  detailed_description?: string;
  rationale?: string;
  success_metrics?: string[];
  timeline_months?: number;
  trend_data?: number[];
  department?: string;
}

type ErrorType = "network" | "auth" | "downstream" | "unknown";

interface ErrorInfo {
  type: ErrorType;
  title: string;
  message: string;
}

function classifyError(err: unknown): ErrorInfo {
  const error = err as { response?: { status: number } };
  if (!error?.response) {
    return { type: "network", title: "Connection Lost", message: "Unable to reach the recommendation service. Check your network and retry." };
  }
  if (error.response?.status === 401 || error.response?.status === 403) {
    return { type: "auth", title: "Authentication Required", message: "Your session has expired. Please sign in again to access recommendations." };
  }
  if (error.response?.status >= 500) {
    return { type: "downstream", title: "Service Unavailable", message: "The recommendation engine is temporarily down. Our team has been notified." };
  }
  return { type: "unknown", title: "Unexpected Error", message: "An error occurred while loading recommendations." };
}

const STATUS_CONFIG: Record<string, { class: string; label: string; icon: React.ReactNode }> = {
  proposed: { class: "bg-healthcare-blue/10 text-healthcare-blue border-healthcare-blue/20", label: "Proposed", icon: <Clock className="size-3" /> },
  under_review: { class: "bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20", label: "Under Review", icon: <Target className="size-3" /> },
  approved: { class: "bg-healthcare-green/10 text-healthcare-green border-healthcare-green/20", label: "Approved", icon: <CheckCircle2 className="size-3" /> },
  implementing: { class: "bg-[#7c3aed]/10 text-[#7c3aed] border-[#7c3aed]/20", label: "Implementing", icon: <Shield className="size-3" /> },
  completed: { class: "bg-healthcare-green/10 text-healthcare-green border-healthcare-green/20", label: "Completed", icon: <CheckCircle2 className="size-3" /> },
  rejected: { class: "bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20", label: "Rejected", icon: <XCircle className="size-3" /> },
};

function StatsSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <SkeletonStatCard key={i} />
      ))}
    </div>
  );
}

function CardsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

function EmptyState({ statusFilter }: { statusFilter: string }) {
  const isFiltered = statusFilter !== "all";
  return (
    <div className="flex flex-col items-center justify-center py-16 px-8 text-center">
      <div className="mb-4">
        <CheckCircle2 className="size-10 text-muted-foreground/50" />
      </div>
      <h3 className="text-lg font-semibold mb-1">
        {isFiltered
          ? "No recommendations match the selected filter"
          : "No recommendations pending"}
      </h3>
      <p className="text-sm text-muted-foreground max-w-md">
        {isFiltered
          ? "Try adjusting your status filter to see more results."
          : "All recommendations have been reviewed or none have been generated yet. New recommendations will appear as the system learns from your data."}
      </p>
    </div>
  );
}

function RecommendationCard({
  recommendation,
  isExpanded,
  onToggleExpand,
  onApprove,
  onReject,
  approvingId,
  rejectingId,
  onClick,
}: {
  recommendation: Recommendation;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  approvingId: string | null;
  rejectingId: string | null;
  onClick?: () => void;
}) {
  const statusCfg = STATUS_CONFIG[recommendation.recommendation_status] || STATUS_CONFIG.proposed;
  const confidence = recommendation.confidence_in_impact || recommendation.scores?.confidence || 0;
  const impact = recommendation.expected_impact_value
    ? formatCurrency(recommendation.expected_impact_value, true)
    : "—";

  const isActionable = ["proposed", "under_review"].includes(recommendation.recommendation_status);

  return (
    <Card className="group hover:shadow-md transition-all duration-200 cursor-pointer" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <Badge className={statusCfg.class} variant="outline">
                {statusCfg.icon}
                <span className="ml-1">{statusCfg.label}</span>
              </Badge>
              {recommendation.priority_rank && (
                <Badge variant="outline" className="text-[10px]">
                  Priority #{recommendation.priority_rank}
                </Badge>
              )}
              {recommendation.department && (
                <Badge variant="outline" className="text-[10px]">
                  {recommendation.department}
                </Badge>
              )}
            </div>
            <h3 className="text-sm font-semibold leading-snug mb-0.5 line-clamp-2">
              {recommendation.title}
            </h3>
            {recommendation.summary && (
              <p className="text-xs text-muted-foreground line-clamp-1 mb-2">
                {recommendation.summary}
              </p>
            )}
          </div>
          <div className="flex flex-col items-end gap-2 shrink-0">
            {recommendation.trend_data && (
              <Sparkline
                data={recommendation.trend_data}
                width={56}
                height={20}
                color={
                  confidence >= 0.8
                    ? "var(--color-healthcare-green)"
                    : confidence >= 0.6
                      ? "var(--color-healthcare-amber)"
                      : "var(--color-healthcare-red)"
                }
              />
            )}
            <div className="text-right">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide">Impact</div>
              <div className="text-sm font-bold tabular-nums text-healthcare-green">{impact}</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mt-3">
          <div className="p-2 rounded-lg bg-muted/50 text-center">
            <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-0.5">Confidence</div>
            <div className="flex items-center justify-center gap-1.5">
              <div className="relative h-1.5 w-16 bg-muted rounded-full overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 rounded-full transition-all"
                  style={{
                    width: `${confidence * 100}%`,
                    backgroundColor:
                      confidence >= 0.8
                        ? "var(--color-healthcare-green)"
                        : confidence >= 0.6
                          ? "var(--color-healthcare-amber)"
                          : "var(--color-healthcare-red)",
                  }}
                />
              </div>
              <span className={`text-xs font-bold tabular-nums ${getConfidenceColor(confidence)}`}>
                {formatPercentage(confidence * 100, 0)}
              </span>
            </div>
          </div>
          <div className="p-2 rounded-lg bg-muted/50 text-center">
            <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-0.5">Timeline</div>
            <div className="text-sm font-bold tabular-nums">
              {recommendation.timeline_months ? `${recommendation.timeline_months}mo` : "TBD"}
            </div>
          </div>
        </div>

        {recommendation.assigned_to_name && (
          <div className="flex items-center gap-1.5 mt-2 text-xs text-muted-foreground">
            <User className="size-3" />
            {recommendation.assigned_to_name}
          </div>
        )}

        <div className="flex items-center justify-between mt-3">
          <button
            onClick={onToggleExpand}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {isExpanded ? (
              <><ChevronUp className="size-3" />Show less</>
            ) : (
              <><ChevronDown className="size-3" />Show details</>
            )}
          </button>
          {isActionable && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => { e.stopPropagation(); onReject(recommendation.id); }}
                disabled={rejectingId === recommendation.id}
              >
                <ThumbsDown className="size-3.5 mr-1" />
                {rejectingId === recommendation.id ? "Rejecting..." : "Dismiss"}
              </Button>
              <Button
                size="sm"
                onClick={(e) => { e.stopPropagation(); onApprove(recommendation.id); }}
                disabled={approvingId === recommendation.id}
              >
                <ThumbsUp className="size-3.5 mr-1" />
                {approvingId === recommendation.id ? "Approving..." : "Approve"}
              </Button>
            </div>
          )}
        </div>

        {isExpanded && (
          <div className="mt-3 pt-3 border-t border-border space-y-3">
            {recommendation.rationale && (
              <div>
                <div className="text-xs font-medium mb-1">Rationale</div>
                <p className="text-xs text-muted-foreground">{recommendation.rationale}</p>
              </div>
            )}
            {recommendation.detailed_description && (
              <div>
                <div className="text-xs font-medium mb-1">Description</div>
                <p className="text-xs text-muted-foreground">{recommendation.detailed_description}</p>
              </div>
            )}
            {recommendation.success_metrics && recommendation.success_metrics.length > 0 && (
              <div>
                <div className="text-xs font-medium mb-1">Success Metrics</div>
                <ul className="space-y-1">
                  {recommendation.success_metrics.map((m, i) => (
                    <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                      <span className="text-healthcare-green mt-0.5">•</span>
                      {m}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function RecommendationDetailDialog({
  recommendation,
  open,
  onClose,
  onApprove,
  onReject,
}: {
  recommendation: Recommendation | null;
  open: boolean;
  onClose: () => void;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}) {
  if (!recommendation) return null;
  const statusCfg = STATUS_CONFIG[recommendation.recommendation_status] || STATUS_CONFIG.proposed;
  const confidence = recommendation.confidence_in_impact || recommendation.scores?.confidence || 0;

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="pr-8">{recommendation.title}</DialogTitle>
          <DialogDescription>{recommendation.summary}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge className={statusCfg.class} variant="outline">
              {statusCfg.icon}
              <span className="ml-1">{statusCfg.label}</span>
            </Badge>
            {recommendation.department && (
              <Badge variant="outline">{recommendation.department}</Badge>
            )}
            {recommendation.assigned_to_name && (
              <Badge variant="outline">
                <User className="size-3 mr-1" />
                {recommendation.assigned_to_name}
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-muted/50 text-center">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Confidence</div>
              <div className="text-xl font-bold tabular-nums" style={{
                color: confidence >= 0.8 ? "var(--color-healthcare-green)" : confidence >= 0.6 ? "var(--color-healthcare-amber)" : "var(--color-healthcare-red)",
              }}>
                {formatPercentage(confidence * 100, 0)}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-muted/50 text-center">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Expected Impact</div>
              <div className="text-xl font-bold tabular-nums text-healthcare-green">
                {recommendation.expected_impact_value
                  ? formatCurrency(recommendation.expected_impact_value, true)
                  : "—"}
              </div>
            </div>
          </div>

          {recommendation.rationale && (
            <div>
              <div className="text-xs font-medium mb-1">Rationale</div>
              <p className="text-xs text-muted-foreground">{recommendation.rationale}</p>
            </div>
          )}

          {recommendation.success_metrics && recommendation.success_metrics.length > 0 && (
            <div>
              <div className="text-xs font-medium mb-1">Success Metrics</div>
              <ul className="space-y-1">
                {recommendation.success_metrics.map((m, i) => (
                  <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                    <span className="text-healthcare-green mt-0.5">•</span>
                    {m}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        <DialogFooter>
          <DialogClose render={<Button variant="outline" />}>Close</DialogClose>
          {["proposed", "under_review"].includes(recommendation.recommendation_status) && (
            <>
              <Button variant="destructive" onClick={() => { onReject(recommendation.id); onClose(); }}>
                <XCircle className="size-4 mr-1.5" />
                Dismiss
              </Button>
              <Button onClick={() => { onApprove(recommendation.id); onClose(); }}>
                <CheckCircle2 className="size-4 mr-1.5" />
                Approve
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function RecommendationCenter() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ErrorInfo | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [selectedRecommendation, setSelectedRecommendation] = useState<Recommendation | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [approvingId, setApprovingId] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);

  const fetchRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { limit: 50 };
      if (statusFilter !== "all") params.status = statusFilter;
      const res = await intelligenceAPI.listRecommendations(params);
      setRecommendations(res.data?.data || []);
    } catch (err: unknown) {
      setError(classifyError(err));
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect -- data fetching on filter change is intentional */
    fetchRecommendations();
  }, [fetchRecommendations]);

  const stats = {
    total: recommendations.length,
    pending: recommendations.filter((r) => r.recommendation_status === "proposed").length,
    implementing: recommendations.filter((r) => r.recommendation_status === "implementing").length,
    completed: recommendations.filter((r) => r.recommendation_status === "completed").length,
  };

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleApprove = async (id: string) => {
    setApprovingId(id);
    try {
      await intelligenceAPI.approveRecommendation(id);
      setRecommendations((prev) =>
        prev.map((r) =>
          r.id === id ? { ...r, recommendation_status: "approved" } : r
        )
      );
    } catch {
    } finally {
      setApprovingId(null);
    }
  };

  const handleReject = async (id: string) => {
    setRejectingId(id);
    try {
      await intelligenceAPI.rejectRecommendation(id, { reason: "Dismissed by user" });
      setRecommendations((prev) =>
        prev.map((r) =>
          r.id === id ? { ...r, recommendation_status: "rejected" } : r
        )
      );
    } catch {
    } finally {
      setRejectingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="size-4" />
          <AlertTitle>{error.title}</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      {loading ? (
        <>
          <StatsSkeleton />
          <CardsSkeleton />
        </>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Total Recommendations</div>
              <div className="text-2xl font-bold tabular-nums">{stats.total}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Pending Review</div>
              <div className="text-2xl font-bold tabular-nums text-healthcare-blue">{stats.pending}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Implementing</div>
              <div className="text-2xl font-bold tabular-nums text-[#7c3aed]">{stats.implementing}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Completed</div>
              <div className="text-2xl font-bold tabular-nums text-healthcare-green">{stats.completed}</div>
            </Card>
          </div>

          <div className="flex items-center gap-3">
            <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v ?? "all")}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="proposed">Proposed</SelectItem>
                <SelectItem value="under_review">Under Review</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="implementing">Implementing</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={fetchRecommendations}>
              <RefreshCw className="size-3.5 mr-1.5" />
              Refresh
            </Button>
          </div>

          {recommendations.length === 0 ? (
            <EmptyState statusFilter={statusFilter} />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recommendations.map((r) => (
                <RecommendationCard
                  key={r.id}
                  recommendation={r}
                  isExpanded={expandedIds.has(r.id)}
                  onToggleExpand={() => toggleExpand(r.id)}
                  onApprove={handleApprove}
                  onReject={handleReject}
                  approvingId={approvingId}
                  rejectingId={rejectingId}
                  onClick={() => { setSelectedRecommendation(r); setDialogOpen(true); }}
                />
              ))}
            </div>
          )}
        </>
      )}

      <RecommendationDetailDialog
        recommendation={selectedRecommendation}
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </div>
  );
}
