"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SkeletonStatCard, SkeletonBriefingCard } from "@/components/ui/skeleton";
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
import { formatDate } from "@/lib/utils/format";
import {
  FileText,
  Calendar,
  AlertCircle,
  RefreshCw,
  ChevronRight,
  BookOpen,
  Clock,
} from "lucide-react";

interface Briefing {
  id: string;
  briefing_type: string;
  title: string;
  briefing_status: string;
  period_start: string;
  period_end: string;
  narrative: string;
  key_highlights: Array<{ title: string; description: string }>;
  scores: Record<string, number>;
  created_at: string;
  executive_summary?: string;
  metrics_summary?: Array<{ label: string; value: string; trend?: string }>;
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
    return { type: "network", title: "Connection Lost", message: "Unable to reach the briefing service. Check your network and retry." };
  }
  if (error.response?.status === 401 || error.response?.status === 403) {
    return { type: "auth", title: "Authentication Required", message: "Your session has expired. Please sign in again to access briefings." };
  }
  if (error.response?.status >= 500) {
    return { type: "downstream", title: "Service Unavailable", message: "The briefing generation service is temporarily down. Our team has been notified." };
  }
  return { type: "unknown", title: "Unexpected Error", message: "An error occurred while loading briefings." };
}

const TYPE_CONFIG: Record<string, { label: string; class: string; icon: React.ReactNode }> = {
  daily: { label: "Daily", class: "bg-healthcare-blue/10 text-healthcare-blue border-healthcare-blue/20", icon: <Calendar className="size-3" /> },
  weekly: { label: "Weekly", class: "bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20", icon: <Calendar className="size-3" /> },
  monthly: { label: "Monthly", class: "bg-healthcare-green/10 text-healthcare-green border-healthcare-green/20", icon: <Calendar className="size-3" /> },
  ad_hoc: { label: "Ad Hoc", class: "bg-muted text-muted-foreground border-border", icon: <FileText className="size-3" /> },
};

const STATUS_CONFIG: Record<string, { class: string }> = {
  draft: { class: "bg-muted text-muted-foreground border-border" },
  generated: { class: "bg-healthcare-blue/10 text-healthcare-blue border-healthcare-blue/20" },
  finalized: { class: "bg-healthcare-green/10 text-healthcare-green border-healthcare-green/20" },
  distributed: { class: "bg-healthcare-green/10 text-healthcare-green border-healthcare-green/20" },
};

function StatsSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <SkeletonStatCard key={i} />
      ))}
    </div>
  );
}

function CardsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <SkeletonBriefingCard key={i} />
      ))}
    </div>
  );
}

function EmptyState({ typeFilter }: { typeFilter: string }) {
  const isFiltered = typeFilter !== "all";
  return (
    <div className="flex flex-col items-center justify-center py-16 px-8 text-center">
      <div className="mb-4">
        <BookOpen className="size-10 text-muted-foreground/50" />
      </div>
      <h3 className="text-lg font-semibold mb-1">
        {isFiltered
          ? "No briefings match the selected filter"
          : "No briefings generated yet"}
      </h3>
      <p className="text-sm text-muted-foreground max-w-md">
        {isFiltered
          ? "Try adjusting your type filter to see more results."
          : "Briefings are automatically generated based on your intelligence data. They will appear here once created."}
      </p>
    </div>
  );
}

function BriefingCard({
  briefing,
  isSelected,
  onClick,
}: {
  briefing: Briefing;
  isSelected: boolean;
  onClick: () => void;
}) {
  const typeConfig = TYPE_CONFIG[briefing.briefing_type] || TYPE_CONFIG.ad_hoc;
  const statusConfig = STATUS_CONFIG[briefing.briefing_status] || STATUS_CONFIG.draft;

  return (
    <Card
      className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
        isSelected ? "ring-2 ring-primary shadow-md" : ""
      }`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <Badge className={typeConfig.class} variant="outline">
            {typeConfig.icon}
            <span className="ml-1">{typeConfig.label}</span>
          </Badge>
          <Badge className={statusConfig.class} variant="outline">
            {briefing.briefing_status}
          </Badge>
        </div>
        <h3 className="font-semibold text-sm line-clamp-2 mb-1">{briefing.title}</h3>
        <div className="flex items-center gap-1 text-xs text-muted-foreground mb-2">
          <Calendar className="size-3" />
          {formatDate(briefing.period_start)} — {formatDate(briefing.period_end)}
        </div>
        {briefing.key_highlights && briefing.key_highlights.length > 0 && (
          <div className="space-y-1 mb-2">
            {briefing.key_highlights.slice(0, 2).map((h, i) => (
              <div key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                <span className="text-primary mt-0.5">•</span>
                <span className="line-clamp-1">{h.title || h.description}</span>
              </div>
            ))}
          </div>
        )}
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <Clock className="size-3" />
            {formatDate(briefing.created_at)}
          </div>
          <ChevronRight className="size-4 text-muted-foreground" />
        </div>
      </CardContent>
    </Card>
  );
}

function BriefingDetailPanel({
  briefing,
  onClose,
  onOpenDialog,
}: {
  briefing: Briefing;
  onClose: () => void;
  onOpenDialog: () => void;
}) {
  const typeConfig = TYPE_CONFIG[briefing.briefing_type] || TYPE_CONFIG.ad_hoc;

  return (
    <Card className="sticky top-6">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{briefing.title}</CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onOpenDialog}>
              Open in Dialog
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Badge className={typeConfig.class} variant="outline">
            {typeConfig.label}
          </Badge>
          <span>•</span>
          <span>{formatDate(briefing.period_start)} — {formatDate(briefing.period_end)}</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {briefing.executive_summary && (
          <div>
            <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
              Executive Summary
            </h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {briefing.executive_summary}
            </p>
          </div>
        )}

        {briefing.narrative && (
          <div>
            <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
              Narrative
            </h4>
            <ScrollArea className="max-h-64">
              <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                {briefing.narrative}
              </p>
            </ScrollArea>
          </div>
        )}

        {briefing.metrics_summary && briefing.metrics_summary.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
              Key Metrics
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {briefing.metrics_summary.map((m, i) => (
                <div key={i} className="p-2 rounded-lg bg-muted/50">
                  <div className="text-[10px] text-muted-foreground uppercase tracking-wide">{m.label}</div>
                  <div className="text-sm font-bold tabular-nums">{m.value}</div>
                  {m.trend && (
                    <div className="text-[10px] text-muted-foreground">{m.trend}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {briefing.key_highlights && briefing.key_highlights.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
              Key Highlights
            </h4>
            <ul className="space-y-1.5">
              {briefing.key_highlights.map((h, i) => (
                <li key={i} className="text-sm flex items-start gap-2">
                  <span className="text-primary mt-1">•</span>
                  <span>
                    {h.title}
                    {h.description ? `: ${h.description}` : ""}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function BriefingDetailDialog({
  briefing,
  open,
  onClose,
}: {
  briefing: Briefing | null;
  open: boolean;
  onClose: () => void;
}) {
  if (!briefing) return null;
  const typeConfig = TYPE_CONFIG[briefing.briefing_type] || TYPE_CONFIG.ad_hoc;

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="pr-8">{briefing.title}</DialogTitle>
          <DialogDescription>
            {typeConfig.label} Briefing • {formatDate(briefing.period_start)} — {formatDate(briefing.period_end)}
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="flex-1 -mx-4 px-4">
          <div className="space-y-4">
            {briefing.executive_summary && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                  Executive Summary
                </h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {briefing.executive_summary}
                </p>
              </div>
            )}

            {briefing.narrative && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                  Narrative
                </h4>
                <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                  {briefing.narrative}
                </p>
              </div>
            )}

            {briefing.metrics_summary && briefing.metrics_summary.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                  Key Metrics
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {briefing.metrics_summary.map((m, i) => (
                    <div key={i} className="p-2 rounded-lg bg-muted/50">
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wide">{m.label}</div>
                      <div className="text-sm font-bold tabular-nums">{m.value}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {briefing.key_highlights && briefing.key_highlights.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                  Key Highlights
                </h4>
                <ul className="space-y-1.5">
                  {briefing.key_highlights.map((h, i) => (
                    <li key={i} className="text-sm flex items-start gap-2">
                      <span className="text-primary mt-1">•</span>
                      <span>
                        {h.title}
                        {h.description ? `: ${h.description}` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </ScrollArea>
        <DialogFooter>
          <DialogClose render={<Button variant="outline" />}>Close</DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function BriefingLibrary() {
  const [briefings, setBriefings] = useState<Briefing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ErrorInfo | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [selectedBriefing, setSelectedBriefing] = useState<Briefing | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const fetchBriefings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { limit: 50 };
      if (typeFilter !== "all") params.briefing_type = typeFilter;
      const res = await intelligenceAPI.listBriefings(params);
      setBriefings(res.data?.data || []);
    } catch (err: unknown) {
      setError(classifyError(err));
    } finally {
      setLoading(false);
    }
  }, [typeFilter]);

  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect -- data fetching on filter change is intentional */
    fetchBriefings();
  }, [fetchBriefings]);

  const stats = {
    total: briefings.length,
    daily: briefings.filter((b) => b.briefing_type === "daily").length,
    weekly: briefings.filter((b) => b.briefing_type === "weekly").length,
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
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Total Briefings</div>
              <div className="text-2xl font-bold tabular-nums">{stats.total}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Daily Briefings</div>
              <div className="text-2xl font-bold tabular-nums text-healthcare-blue">{stats.daily}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Weekly Briefings</div>
              <div className="text-2xl font-bold tabular-nums text-healthcare-amber">{stats.weekly}</div>
            </Card>
          </div>

          <div className="flex items-center gap-3">
            <Select value={typeFilter} onValueChange={(v) => setTypeFilter(v ?? "all")}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
                <SelectItem value="ad_hoc">Ad Hoc</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={fetchBriefings}>
              <RefreshCw className="size-3.5 mr-1.5" />
              Refresh
            </Button>
          </div>

          {briefings.length === 0 ? (
            <EmptyState typeFilter={typeFilter} />
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1 space-y-4">
                {briefings.map((b) => (
                  <BriefingCard
                    key={b.id}
                    briefing={b}
                    isSelected={selectedBriefing?.id === b.id}
                    onClick={() => setSelectedBriefing(b)}
                  />
                ))}
              </div>
              <div className="lg:col-span-2">
                {selectedBriefing ? (
                  <BriefingDetailPanel
                    briefing={selectedBriefing}
                    onClose={() => setSelectedBriefing(null)}
                    onOpenDialog={() => setDialogOpen(true)}
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center py-16 text-center">
                    <BookOpen className="size-10 text-muted-foreground/50 mb-4" />
                    <h3 className="text-lg font-semibold mb-1">Select a briefing</h3>
                    <p className="text-sm text-muted-foreground max-w-sm">
                      Click on a briefing card to view its full details, narrative, and key highlights.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      <BriefingDetailDialog
        briefing={selectedBriefing}
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
      />
    </div>
  );
}
