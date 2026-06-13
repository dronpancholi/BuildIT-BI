"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
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
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import {
  DollarSign,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Calendar,
  Building2,
  ArrowUpRight,
} from "lucide-react";

interface Opportunity {
  id: string;
  opportunity_type: string;
  title: string;
  summary: string;
  estimated_value: number;
  value_unit: string;
  effort_level: string;
  risk_level: string;
  roi: number;
  opportunity_status: string;
  period_start: string;
  scores: Record<string, number>;
  timeline_months?: number;
  department?: string;
  detailed_description?: string;
  success_metrics?: string[];
  dependencies?: string[];
  trend_data?: number[];
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
    return { type: "network", title: "Connection Lost", message: "Unable to reach the opportunity analysis service. Check your network and retry." };
  }
  if (error.response?.status === 401 || error.response?.status === 403) {
    return { type: "auth", title: "Authentication Required", message: "Your session has expired. Please sign in again to access opportunity data." };
  }
  if (error.response?.status >= 500) {
    return { type: "downstream", title: "Analytics Service Unavailable", message: "The opportunity analysis backend is temporarily down. Our team has been notified." };
  }
  return { type: "unknown", title: "Unexpected Error", message: "An error occurred while loading opportunities." };
}

const STATUS_CONFIG: Record<string, { class: string; label: string }> = {
  identified: { class: "bg-healthcare-blue/10 text-healthcare-blue border-healthcare-blue/20", label: "Identified" },
  prioritized: { class: "bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20", label: "Prioritized" },
  approved: { class: "bg-healthcare-green/10 text-healthcare-green border-healthcare-green/20", label: "Approved" },
  implementing: { class: "bg-[#7c3aed]/10 text-[#7c3aed] border-[#7c3aed]/20", label: "In Progress" },
  realized: { class: "bg-healthcare-green/10 text-healthcare-green border-healthcare-green/20", label: "Realized" },
};

const EFFORT_CONFIG: Record<string, { class: string; color: string }> = {
  low: { class: "bg-healthcare-green/10 text-healthcare-green border-healthcare-green/20", color: "var(--color-healthcare-green)" },
  medium: { class: "bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20", color: "var(--color-healthcare-amber)" },
  high: { class: "bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20", color: "var(--color-healthcare-red)" },
};

const RISK_CONFIG: Record<string, { class: string }> = {
  low: { class: "bg-healthcare-green/10 text-healthcare-green border-healthcare-green/20" },
  medium: { class: "bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20" },
  high: { class: "bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20" },
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
        <DollarSign className="size-10 text-muted-foreground/50" />
      </div>
      <h3 className="text-lg font-semibold mb-1">
        {isFiltered
          ? "No opportunities match the selected filter"
          : "No opportunities identified yet"}
      </h3>
      <p className="text-sm text-muted-foreground max-w-md">
        {isFiltered
          ? "Try adjusting your status filter to see more results."
          : "The system is analyzing operational patterns. Revenue and efficiency opportunities will appear as they are discovered."}
      </p>
    </div>
  );
}

function OpportunityCard({
  opportunity,
  isExpanded,
  onToggleExpand,
  onClick,
}: {
  opportunity: Opportunity;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onClick?: () => void;
}) {
  const statusCfg = STATUS_CONFIG[opportunity.opportunity_status] || STATUS_CONFIG.identified;
  const effortCfg = EFFORT_CONFIG[opportunity.effort_level] || EFFORT_CONFIG.medium;
  const riskCfg = RISK_CONFIG[opportunity.risk_level] || RISK_CONFIG.medium;

  const effortPercent =
    opportunity.effort_level === "low" ? 33 : opportunity.effort_level === "high" ? 100 : 66;

  return (
    <Card className="group hover:shadow-md transition-all duration-200 cursor-pointer" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <Badge className={statusCfg.class} variant="outline">
                {statusCfg.label}
              </Badge>
              <Badge className={effortCfg.class} variant="outline">
                {opportunity.effort_level} effort
              </Badge>
              <Badge className={riskCfg.class} variant="outline">
                {opportunity.risk_level} risk
              </Badge>
              {opportunity.department && (
                <Badge variant="outline" className="text-[10px]">
                  <Building2 className="size-3 mr-0.5" />
                  {opportunity.department}
                </Badge>
              )}
            </div>
            <h3 className="text-sm font-semibold leading-snug mb-0.5 line-clamp-2">
              {opportunity.title}
            </h3>
            {opportunity.summary && (
              <p className="text-xs text-muted-foreground line-clamp-1 mb-2">
                {opportunity.summary}
              </p>
            )}
          </div>
          <div className="flex flex-col items-end gap-2 shrink-0">
            <div className="text-right">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide">Est. Value</div>
              <div className="text-lg font-bold tabular-nums text-healthcare-green">
                {formatCurrency(opportunity.estimated_value, true)}
              </div>
            </div>
            {opportunity.trend_data && (
              <Sparkline
                data={opportunity.trend_data}
                width={56}
                height={20}
                color="var(--color-healthcare-green)"
              />
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3 mt-3">
          <div className="p-2 rounded-lg bg-muted/50 text-center">
            <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-0.5">ROI</div>
            <div className="text-sm font-bold tabular-nums text-healthcare-green">
              {opportunity.roi ? formatPercentage(opportunity.roi, 0) : "N/A"}
            </div>
          </div>
          <div className="p-2 rounded-lg bg-muted/50 text-center">
            <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-0.5">Timeline</div>
            <div className="text-sm font-bold tabular-nums">
              {opportunity.timeline_months ? `${opportunity.timeline_months}mo` : "TBD"}
            </div>
          </div>
          <div className="p-2 rounded-lg bg-muted/50 text-center">
            <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-0.5">Effort</div>
            <div className="mt-1">
              <Progress value={effortPercent}>
                <div className="h-1 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: `${effortPercent}%`, backgroundColor: effortCfg.color }}
                  />
                </div>
              </Progress>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between mt-3">
          <button
            onClick={onToggleExpand}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="size-3" />
                Show less
              </>
            ) : (
              <>
                <ChevronDown className="size-3" />
                Show details
              </>
            )}
          </button>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={onClick}>
              View
            </Button>
            {opportunity.opportunity_status === "identified" && (
              <Button size="sm" onClick={onClick}>
                <ArrowUpRight className="size-3.5 mr-1" />
                Prioritize
              </Button>
            )}
          </div>
        </div>

        {isExpanded && (
          <div className="mt-3 pt-3 border-t border-border space-y-3">
            {opportunity.detailed_description && (
              <p className="text-xs text-muted-foreground">{opportunity.detailed_description}</p>
            )}
            {opportunity.success_metrics && opportunity.success_metrics.length > 0 && (
              <div>
                <div className="text-xs font-medium mb-1">Success Metrics</div>
                <ul className="space-y-1">
                  {opportunity.success_metrics.map((m, i) => (
                    <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                      <span className="text-healthcare-green mt-0.5">•</span>
                      {m}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {opportunity.dependencies && opportunity.dependencies.length > 0 && (
              <div>
                <div className="text-xs font-medium mb-1">Dependencies</div>
                <div className="flex flex-wrap gap-1.5">
                  {opportunity.dependencies.map((d, i) => (
                    <Badge key={i} variant="outline" className="text-[10px]">
                      {d}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function OpportunityDetailDialog({
  opportunity,
  open,
  onClose,
}: {
  opportunity: Opportunity | null;
  open: boolean;
  onClose: () => void;
}) {
  if (!opportunity) return null;
  const statusCfg = STATUS_CONFIG[opportunity.opportunity_status] || STATUS_CONFIG.identified;

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="pr-8">{opportunity.title}</DialogTitle>
          <DialogDescription>{opportunity.summary}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge className={statusCfg.class} variant="outline">{statusCfg.label}</Badge>
            {opportunity.department && (
              <Badge variant="outline"><Building2 className="size-3 mr-1" />{opportunity.department}</Badge>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-muted/50 text-center">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Estimated Value</div>
              <div className="text-xl font-bold tabular-nums text-healthcare-green">
                {formatCurrency(opportunity.estimated_value)}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-muted/50 text-center">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">ROI</div>
              <div className="text-xl font-bold tabular-nums">
                {opportunity.roi ? formatPercentage(opportunity.roi, 0) : "N/A"}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-muted/50 text-center">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Timeline</div>
              <div className="text-sm font-bold tabular-nums">
                <Calendar className="size-4 inline mr-1 text-muted-foreground" />
                {opportunity.timeline_months ? `${opportunity.timeline_months} months` : "TBD"}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-muted/50 text-center">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Effort</div>
              <div className="text-sm font-bold capitalize">{opportunity.effort_level}</div>
            </div>
          </div>

          {opportunity.success_metrics && opportunity.success_metrics.length > 0 && (
            <div>
              <div className="text-xs font-medium mb-1">Success Metrics</div>
              <ul className="space-y-1">
                {opportunity.success_metrics.map((m, i) => (
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
          <Button onClick={() => onClose()}>
            <ArrowUpRight className="size-4 mr-1.5" />
            Take Action
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function OpportunityCenter() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ErrorInfo | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const fetchOpportunities = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { limit: 50 };
      if (statusFilter !== "all") params.status = statusFilter;
      const res = await intelligenceAPI.listOpportunities(params);
      setOpportunities(res.data?.data || []);
    } catch (err: unknown) {
      setError(classifyError(err));
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect -- data fetching on filter change is intentional */
    fetchOpportunities();
  }, [fetchOpportunities]);

  const totalValue = opportunities.reduce((sum, o) => sum + (o.estimated_value || 0), 0);
  const avgROI = opportunities.length
    ? opportunities.filter((o) => o.roi).reduce((sum, o) => sum + o.roi, 0) /
      opportunities.filter((o) => o.roi).length
    : 0;

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
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
              <div className="text-xs text-muted-foreground mb-1">Total Opportunities</div>
              <div className="text-2xl font-bold tabular-nums">{opportunities.length}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Total Estimated Value</div>
              <div className="text-2xl font-bold tabular-nums text-healthcare-green">
                {formatCurrency(totalValue, true)}
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Average ROI</div>
              <div className="text-2xl font-bold tabular-nums">
                {avgROI ? formatPercentage(avgROI, 0) : "N/A"}
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">In Progress</div>
              <div className="text-2xl font-bold tabular-nums text-[#7c3aed]">
                {opportunities.filter((o) => o.opportunity_status === "implementing").length}
              </div>
            </Card>
          </div>

          <div className="flex items-center gap-3">
            <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v ?? "all")}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="identified">Identified</SelectItem>
                <SelectItem value="prioritized">Prioritized</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="implementing">Implementing</SelectItem>
                <SelectItem value="realized">Realized</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={fetchOpportunities}>
              <RefreshCw className="size-3.5 mr-1.5" />
              Refresh
            </Button>
          </div>

          {opportunities.length === 0 ? (
            <EmptyState statusFilter={statusFilter} />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {opportunities.map((o) => (
                <OpportunityCard
                  key={o.id}
                  opportunity={o}
                  isExpanded={expandedIds.has(o.id)}
                  onToggleExpand={() => toggleExpand(o.id)}
                  onClick={() => { setSelectedOpportunity(o); setDialogOpen(true); }}
                />
              ))}
            </div>
          )}
        </>
      )}

      <OpportunityDetailDialog
        opportunity={selectedOpportunity}
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
      />
    </div>
  );
}
