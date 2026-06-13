"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SkeletonCard, SkeletonStatCard } from "@/components/ui/skeleton";
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
import { formatDate, formatCurrency, formatPercentage, getConfidenceColor } from "@/lib/utils/format";
import {
  AlertTriangle,
  AlertCircle,
  Lightbulb,
  DollarSign,
  Activity,
  CheckCircle2,
  RefreshCw,
  Info,
} from "lucide-react";

interface IntelligenceItem {
  id: string;
  type: "insight" | "anomaly" | "opportunity" | "recommendation" | "briefing";
  title: string;
  summary: string;
  severity?: string;
  priority?: string;
  confidence?: number;
  impact?: number;
  scores?: {
    confidence: number;
    impact: number;
    priority: number;
    urgency: number;
    priority_label: string;
    impact_label: string;
    urgency_label: string;
  };
  status: string;
  created_at: string;
  metric_code?: string;
  estimated_value?: number;
  why_this_matters?: string;
  trend_data?: number[];
  department?: string;
}

type ErrorType = "network" | "auth" | "downstream" | "unknown";

interface ErrorInfo {
  type: ErrorType;
  title: string;
  message: string;
  action?: string;
}

function classifyError(err: unknown): ErrorInfo {
  const error = err as { response?: { status: number } };
  if (!error?.response) {
    return {
      type: "network",
      title: "Connection Lost",
      message: "Unable to reach the intelligence service. Check your network connection and try again.",
      action: "Retry Connection",
    };
  }
  if (error.response?.status === 401 || error.response?.status === 403) {
    return {
      type: "auth",
      title: "Authentication Required",
      message: "Your session has expired or you lack permission to access intelligence data.",
      action: "Sign In Again",
    };
  }
  if (error.response?.status >= 500) {
    return {
      type: "downstream",
      title: "Intelligence Service Unavailable",
      message: "The analytics backend is temporarily unavailable. Our team has been automatically notified.",
      action: "Retry",
    };
  }
  return {
    type: "unknown",
    title: "Something Went Wrong",
    message: "An unexpected error occurred while loading intelligence data.",
    action: "Try Again",
  };
}

const TYPE_CONFIG: Record<
  string,
  { icon: React.ReactNode; color: string; label: string; bgClass: string }
> = {
  insight: {
    icon: <Lightbulb className="size-4" />,
    color: "text-healthcare-blue",
    label: "Insight",
    bgClass: "bg-healthcare-blue/10 text-healthcare-blue border-healthcare-blue/20",
  },
  anomaly: {
    icon: <AlertTriangle className="size-4" />,
    color: "text-healthcare-red",
    label: "Anomaly",
    bgClass: "bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20",
  },
  opportunity: {
    icon: <DollarSign className="size-4" />,
    color: "text-healthcare-green",
    label: "Opportunity",
    bgClass: "bg-healthcare-green/10 text-healthcare-green border-healthcare-green/20",
  },
  recommendation: {
    icon: <CheckCircle2 className="size-4" />,
    color: "text-[#7c3aed]",
    label: "Recommendation",
    bgClass: "bg-[#7c3aed]/10 text-[#7c3aed] border-[#7c3aed]/20",
  },
  briefing: {
    icon: <Info className="size-4" />,
    color: "text-healthcare-amber",
    label: "Briefing",
    bgClass: "bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20",
  },
};

const SEVERITY_CONFIG: Record<string, { class: string; dotClass: string }> = {
  critical: {
    class: "bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20",
    dotClass: "bg-healthcare-red",
  },
  high: {
    class: "bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20",
    dotClass: "bg-healthcare-red",
  },
  warning: {
    class: "bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20",
    dotClass: "bg-healthcare-amber",
  },
  medium: {
    class: "bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20",
    dotClass: "bg-healthcare-amber",
  },
  info: {
    class: "bg-healthcare-blue/10 text-healthcare-blue border-healthcare-blue/20",
    dotClass: "bg-healthcare-blue",
  },
  low: {
    class: "bg-healthcare-blue/10 text-healthcare-blue border-healthcare-blue/20",
    dotClass: "bg-healthcare-blue",
  },
  success: {
    class: "bg-healthcare-green/10 text-healthcare-green border-healthcare-green/20",
    dotClass: "bg-healthcare-green",
  },
};

const PRIORITY_CONFIG: Record<string, { class: string }> = {
  P0: { class: "bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20" },
  P1: { class: "bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20" },
  P2: { class: "bg-healthcare-blue/10 text-healthcare-blue border-healthcare-blue/20" },
  P3: { class: "bg-muted text-muted-foreground border-border" },
};

function FeedSummarySkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <SkeletonStatCard key={i} />
      ))}
    </div>
  );
}

function FeedCardSkeleton() {
  return <SkeletonCard />;
}

function FeedEmptyState({ filter }: { filter: string }) {
  const messages: Record<string, { title: string; description: string; icon: React.ReactNode }> = {
    all: {
      title: "No intelligence items yet",
      description:
        "The system is initializing intelligence gathering. Insights, anomalies, and recommendations will appear here as they are discovered.",
      icon: <Activity className="size-10 text-muted-foreground/50" />,
    },
    insight: {
      title: "No insights detected",
      description:
        "The system hasn't identified any statistically significant patterns yet. Insights will appear as data accumulates.",
      icon: <Lightbulb className="size-10 text-muted-foreground/50" />,
    },
    anomaly: {
      title: "No anomalies detected — system is operating within normal parameters",
      description:
        "All monitored metrics are within expected ranges. Anomalies will be surfaced automatically when deviations exceed thresholds.",
      icon: <CheckCircle2 className="size-10 text-healthcare-green/50" />,
    },
    opportunity: {
      title: "No opportunities identified",
      description:
        "The system is analyzing operational patterns. Revenue and efficiency opportunities will be flagged as they are discovered.",
      icon: <DollarSign className="size-10 text-muted-foreground/50" />,
    },
    recommendation: {
      title: "No recommendations pending",
      description:
        "All recommendations have been reviewed or none have been generated yet. New recommendations will appear as the system learns.",
      icon: <CheckCircle2 className="size-10 text-muted-foreground/50" />,
    },
  };

  const msg = messages[filter] || messages.all;

  return (
    <div className="flex flex-col items-center justify-center py-16 px-8 text-center">
      <div className="mb-4">{msg.icon}</div>
      <h3 className="text-lg font-semibold mb-1">{msg.title}</h3>
      <p className="text-sm text-muted-foreground max-w-md">{msg.description}</p>
    </div>
  );
}

function IntelligenceCard({
  item,
  onExpand,
}: {
  item: IntelligenceItem;
  onExpand: (item: IntelligenceItem) => void;
}) {
  const typeConfig = TYPE_CONFIG[item.type] || TYPE_CONFIG.insight;
  const severityConfig = item.severity
    ? SEVERITY_CONFIG[item.severity]
    : undefined;
  const priorityConfig = item.scores?.priority_label
    ? PRIORITY_CONFIG[item.scores.priority_label]
    : undefined;

  const trend: "up" | "down" | "stable" = item.trend_data
    ? item.trend_data[item.trend_data.length - 1] > item.trend_data[0]
      ? "up"
      : item.trend_data[item.trend_data.length - 1] < item.trend_data[0]
        ? "down"
        : "stable"
    : "stable";

  const trendColor =
    trend === "up"
      ? "var(--color-healthcare-green)"
      : trend === "down"
        ? "var(--color-healthcare-red)"
        : "var(--color-healthcare-blue)";

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    if (diffHours < 1) return "Just now";
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return formatDate(dateString);
  };

  return (
    <Card className="group hover:shadow-md transition-all duration-200 cursor-pointer" onClick={() => onExpand(item)}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div
            className={`flex size-9 shrink-0 items-center justify-center rounded-lg border ${typeConfig.bgClass}`}
          >
            {typeConfig.icon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <Badge className={typeConfig.bgClass} variant="outline">
                {typeConfig.label}
              </Badge>
              {severityConfig && (
                <Badge className={severityConfig.class} variant="outline">
                  <span className={`size-1.5 rounded-full ${severityConfig.dotClass} mr-1`} />
                  {item.severity!.toUpperCase()}
                </Badge>
              )}
              {priorityConfig && (
                <Badge className={priorityConfig.class} variant="outline">
                  {item.scores!.priority_label}
                </Badge>
              )}
            </div>
            <h3 className="text-sm font-semibold leading-snug mb-0.5 line-clamp-2">
              {item.title}
            </h3>
            <p className="text-xs text-muted-foreground line-clamp-1 mb-2">
              {item.summary}
            </p>
            <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
              {item.metric_code && (
                <span className="font-mono text-[10px] bg-muted px-1.5 py-0.5 rounded">
                  {item.metric_code}
                </span>
              )}
              {item.estimated_value && (
                <span className="font-medium text-healthcare-green">
                  {formatCurrency(item.estimated_value)}
                </span>
              )}
              {item.department && (
                <span>{item.department}</span>
              )}
              <span>{getTimeAgo(item.created_at)}</span>
            </div>
            {item.why_this_matters && (
              <div className="mt-2 text-xs text-muted-foreground bg-muted/50 rounded-md px-2.5 py-1.5 border border-border/50">
                <span className="font-medium text-foreground">Why this matters: </span>
                {item.why_this_matters}
              </div>
            )}
          </div>
          <div className="flex flex-col items-end gap-2 shrink-0">
            <Sparkline
              data={item.trend_data || [10, 12, 11, 14, 13, 16, 18]}
              width={56}
              height={20}
              color={trendColor}
            />
            {item.scores && (
              <div className="flex gap-3 text-center">
                <div>
                  <div className="text-[10px] text-muted-foreground leading-none mb-0.5">Conf</div>
                  <div className={`text-xs font-semibold tabular-nums ${getConfidenceColor(item.scores.confidence)}`}>
                    {formatPercentage(item.scores.confidence * 100, 0)}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-muted-foreground leading-none mb-0.5">Impact</div>
                  <div className={`text-xs font-semibold tabular-nums ${getConfidenceColor(item.scores.impact)}`}>
                    {formatPercentage(item.scores.impact * 100, 0)}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ExpandedItemDialog({
  item,
  open,
  onClose,
}: {
  item: IntelligenceItem | null;
  open: boolean;
  onClose: () => void;
}) {
  if (!item) return null;
  const typeConfig = TYPE_CONFIG[item.type] || TYPE_CONFIG.insight;
  const itemTrend: "up" | "down" | "stable" = item.trend_data
    ? item.trend_data[item.trend_data.length - 1] > item.trend_data[0]
      ? "up"
      : item.trend_data[item.trend_data.length - 1] < item.trend_data[0]
        ? "down"
        : "stable"
    : "stable";

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="pr-8">{item.title}</DialogTitle>
          <DialogDescription>{item.summary}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge className={typeConfig.bgClass} variant="outline">
              {typeConfig.icon}
              <span className="ml-1">{typeConfig.label}</span>
            </Badge>
            {item.severity && (
              <Badge
                className={SEVERITY_CONFIG[item.severity]?.class || ""}
                variant="outline"
              >
                {item.severity.toUpperCase()}
              </Badge>
            )}
            {item.scores?.priority_label && (
              <Badge
                className={PRIORITY_CONFIG[item.scores.priority_label]?.class || ""}
                variant="outline"
              >
                {item.scores.priority_label}
              </Badge>
            )}
          </div>

          {item.scores && (
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: "Confidence", value: item.scores.confidence },
                { label: "Impact", value: item.scores.impact },
                { label: "Priority", value: item.scores.priority },
                { label: "Urgency", value: item.scores.urgency },
              ].map((s) => (
                <div key={s.label} className="text-center p-2 rounded-lg bg-muted/50">
                  <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">
                    {s.label}
                  </div>
                  <div
                    className={`text-sm font-bold tabular-nums ${getConfidenceColor(s.value)}`}
                  >
                    {formatPercentage(s.value * 100, 0)}
                  </div>
                </div>
              ))}
            </div>
          )}

          {item.trend_data && (
            <div className="p-3 rounded-lg bg-muted/30 border border-border/50">
              <div className="text-xs font-medium text-muted-foreground mb-2">
                Trend
              </div>
              <Sparkline
                data={item.trend_data}
                width={320}
                height={48}
                color={
                  itemTrend === "up"
                    ? "var(--color-healthcare-green)"
                    : itemTrend === "down"
                      ? "var(--color-healthcare-red)"
                      : "var(--color-healthcare-blue)"
                }
                showDots
              />
            </div>
          )}

          {item.why_this_matters && (
            <div className="text-sm bg-muted/50 rounded-lg p-3 border border-border/50">
              <span className="font-medium">Why this matters: </span>
              {item.why_this_matters}
            </div>
          )}

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {item.metric_code && (
              <span className="font-mono bg-muted px-1.5 py-0.5 rounded">
                {item.metric_code}
              </span>
            )}
            {item.estimated_value && (
              <span className="font-medium text-healthcare-green">
                {formatCurrency(item.estimated_value)}
              </span>
            )}
            <span>{formatDate(item.created_at)}</span>
          </div>
        </div>
        <DialogFooter>
          <DialogClose render={<Button variant="outline" />}>Close</DialogClose>
          {item.type === "recommendation" && (
            <Button onClick={() => onClose()}>
              <CheckCircle2 className="size-4 mr-1.5" />
              Approve
            </Button>
          )}
          {item.type === "anomaly" && (
            <Button onClick={() => onClose()}>
              <AlertTriangle className="size-4 mr-1.5" />
              Investigate
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function IntelligenceFeed() {
  const [items, setItems] = useState<IntelligenceItem[]>([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ErrorInfo | null>(null);
  const [expandedItem, setExpandedItem] = useState<IntelligenceItem | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const fetchIntelligence = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params: Record<string, string | number> = { limit: 50 };
      if (filter !== "all") params.type = filter;
      const res = await intelligenceAPI.getFeed(params);
      setItems(res.data?.data || []);
    } catch (err: unknown) {
      setError(classifyError(err));
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect -- data fetching on mount is intentional */
    fetchIntelligence();
  }, [fetchIntelligence]);

  const handleExpand = (item: IntelligenceItem) => {
    setExpandedItem(item);
    setDialogOpen(true);
  };

  const handleRetry = () => {
    fetchIntelligence();
  };

  const stats = {
    total: items.length,
    insights: items.filter((i) => i.type === "insight").length,
    anomalies: items.filter((i) => i.type === "anomaly").length,
    opportunities: items.filter((i) => i.type === "opportunity").length,
    recommendations: items.filter((i) => i.type === "recommendation").length,
  };

  const filteredItems = items.filter((item) => {
    if (filter === "all") return true;
    return item.type === filter;
  });

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
          <FeedSummarySkeleton />
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <FeedCardSkeleton key={i} />
            ))}
          </div>
        </>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Total Items</div>
              <div className="text-2xl font-bold tabular-nums">{stats.total}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Insights</div>
              <div className="text-2xl font-bold tabular-nums text-healthcare-blue">{stats.insights}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Anomalies</div>
              <div className="text-2xl font-bold tabular-nums text-healthcare-red">{stats.anomalies}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Opportunities</div>
              <div className="text-2xl font-bold tabular-nums text-healthcare-green">{stats.opportunities}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Recommendations</div>
              <div className="text-2xl font-bold tabular-nums text-[#7c3aed]">{stats.recommendations}</div>
            </Card>
          </div>

          <div className="flex items-center gap-3">
            <Select value={filter} onValueChange={(v) => v && setFilter(v)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="insight">Insights</SelectItem>
                <SelectItem value="anomaly">Anomalies</SelectItem>
                <SelectItem value="opportunity">Opportunities</SelectItem>
                <SelectItem value="recommendation">Recommendations</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={handleRetry}>
              <RefreshCw className="size-3.5 mr-1.5" />
              Refresh
            </Button>
          </div>

          <div className="space-y-3">
            {filteredItems.length === 0 ? (
              <FeedEmptyState filter={filter} />
            ) : (
              filteredItems.map((item) => (
                <IntelligenceCard
                  key={item.id}
                  item={item}
                  onExpand={handleExpand}
                />
              ))
            )}
          </div>
        </>
      )}

      <ExpandedItemDialog
        item={expandedItem}
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
      />
    </div>
  );
}
