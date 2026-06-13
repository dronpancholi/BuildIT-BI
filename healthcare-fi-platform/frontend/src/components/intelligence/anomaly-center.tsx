"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton, SkeletonStatCard, SkeletonTableRow } from "@/components/ui/skeleton";
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
import { formatCurrency, formatDate, formatPercentage, getConfidenceColor } from "@/lib/utils/format";
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Shield,
} from "lucide-react";

interface Anomaly {
  id: string;
  anomaly_type: string;
  severity: string;
  title: string;
  description: string;
  metric_code: string;
  observed_value: number;
  expected_value: number;
  z_score: number;
  anomaly_status: string;
  period_start: string;
  period_end: string;
  scores: Record<string, number>;
  auto_escalated?: boolean;
  trend_data?: number[];
  baseline?: number;
  deviation_percent?: number;
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
    return { type: "network", title: "Connection Lost", message: "Unable to reach the anomaly detection service. Check your network and retry." };
  }
  if (error.response?.status === 401 || error.response?.status === 403) {
    return { type: "auth", title: "Authentication Required", message: "Your session has expired. Please sign in again to access anomaly data." };
  }
  if (error.response?.status >= 500) {
    return { type: "downstream", title: "Analytics Service Unavailable", message: "The anomaly detection backend is temporarily down. Our team has been notified." };
  }
  return { type: "unknown", title: "Unexpected Error", message: "An error occurred while loading anomalies." };
}

const SEVERITY_CONFIG: Record<string, { class: string; dotClass: string; order: number }> = {
  critical: { class: "bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20", dotClass: "bg-healthcare-red", order: 0 },
  high: { class: "bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20", dotClass: "bg-healthcare-red", order: 1 },
  warning: { class: "bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20", dotClass: "bg-healthcare-amber", order: 2 },
  medium: { class: "bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20", dotClass: "bg-healthcare-amber", order: 2 },
  info: { class: "bg-healthcare-blue/10 text-healthcare-blue border-healthcare-blue/20", dotClass: "bg-healthcare-blue", order: 3 },
  low: { class: "bg-healthcare-blue/10 text-healthcare-blue border-healthcare-blue/20", dotClass: "bg-healthcare-blue", order: 3 },
};

const STATUS_CONFIG: Record<string, { class: string }> = {
  detected: { class: "bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20" },
  investigating: { class: "bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20" },
  confirmed: { class: "bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20" },
  resolved: { class: "bg-healthcare-green/10 text-healthcare-green border-healthcare-green/20" },
  dismissed: { class: "bg-muted text-muted-foreground border-border" },
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

function TableSkeleton() {
  return (
    <div className="rounded-xl border border-border overflow-hidden">
      <div className="bg-muted/50 px-4 py-3 flex gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {Array.from({ length: 5 }).map((_, i) => (
        <SkeletonTableRow key={i} />
      ))}
    </div>
  );
}

function EmptyState({ severityFilter, statusFilter }: { severityFilter: string; statusFilter: string }) {
  const isFiltered = severityFilter !== "all" || statusFilter !== "all";
  return (
    <div className="flex flex-col items-center justify-center py-16 px-8 text-center">
      <div className="mb-4">
        <CheckCircle2 className="size-10 text-healthcare-green/50" />
      </div>
      <h3 className="text-lg font-semibold mb-1">
        {isFiltered
          ? "No anomalies match the selected filters"
          : "No anomalies detected — system is operating within normal parameters"}
      </h3>
      <p className="text-sm text-muted-foreground max-w-md">
        {isFiltered
          ? "Try adjusting your severity or status filters to see more results."
          : "All monitored metrics are within expected ranges. Anomalies will be automatically flagged when deviations exceed statistical thresholds."}
      </p>
    </div>
  );
}

function AnomalyDetailDialog({
  anomaly,
  open,
  onClose,
}: {
  anomaly: Anomaly | null;
  open: boolean;
  onClose: () => void;
}) {
  if (!anomaly) return null;

  const severityConfig = SEVERITY_CONFIG[anomaly.severity] || SEVERITY_CONFIG.info;
  const statusConfig = STATUS_CONFIG[anomaly.anomaly_status] || STATUS_CONFIG.detected;
  const deviation = anomaly.deviation_percent
    ? anomaly.deviation_percent
    : anomaly.expected_value
      ? ((anomaly.observed_value - anomaly.expected_value) / Math.abs(anomaly.expected_value)) * 100
      : 0;
  const isNegative = anomaly.observed_value < anomaly.expected_value;

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="pr-8">{anomaly.title}</DialogTitle>
          <DialogDescription>{anomaly.description}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge className={severityConfig.class} variant="outline">
              <span className={`size-1.5 rounded-full ${severityConfig.dotClass} mr-1`} />
              {anomaly.severity.toUpperCase()}
            </Badge>
            <Badge className={statusConfig.class} variant="outline">
              {anomaly.anomaly_status}
            </Badge>
            {anomaly.auto_escalated && (
              <Badge className="bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20" variant="outline">
                <Shield className="size-3 mr-1" />
                Auto-Escalated
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-lg bg-muted/50 text-center">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Observed</div>
              <div className="text-sm font-bold tabular-nums">
                {formatCurrency(anomaly.observed_value)}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-muted/50 text-center">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Baseline</div>
              <div className="text-sm font-bold tabular-nums">
                {formatCurrency(anomaly.expected_value)}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-muted/50 text-center">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Deviation</div>
              <div className={`text-sm font-bold tabular-nums ${isNegative ? "text-healthcare-red" : "text-healthcare-green"}`}>
                {isNegative ? "" : "+"}{formatPercentage(deviation, 1)}
              </div>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-muted/30 border border-border/50">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
              <span>Z-Score</span>
              <span className="font-medium">
                {anomaly.z_score?.toFixed(2)} ({Math.abs(anomaly.z_score) >= 3 ? "Extreme" : Math.abs(anomaly.z_score) >= 2 ? "Significant" : "Moderate"})
              </span>
            </div>
            <div className="relative h-2 w-full bg-muted rounded-full overflow-hidden">
              <div
                className="absolute inset-y-0 left-0 bg-healthcare-red rounded-full transition-all"
                style={{ width: `${Math.min(Math.abs(anomaly.z_score) / 5 * 100, 100)}%` }}
              />
            </div>
          </div>

          {anomaly.trend_data && (
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-2">Trend</div>
              <Sparkline
                data={anomaly.trend_data}
                width={320}
                height={48}
                color="var(--color-healthcare-red)"
                showDots
              />
            </div>
          )}

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {anomaly.metric_code && (
              <span className="font-mono bg-muted px-1.5 py-0.5 rounded">{anomaly.metric_code}</span>
            )}
            <span>{formatDate(anomaly.period_start)} — {formatDate(anomaly.period_end)}</span>
          </div>
        </div>
        <DialogFooter>
          <DialogClose render={<Button variant="outline" />}>Close</DialogClose>
          <Button onClick={() => onClose()}>
            <AlertTriangle className="size-4 mr-1.5" />
            Investigate
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function AnomalyCenter() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ErrorInfo | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const fetchAnomalies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { limit: 50 };
      if (severityFilter !== "all") params.severity = severityFilter;
      if (statusFilter !== "all") params.status = statusFilter;
      const res = await intelligenceAPI.listAnomalies(params);
      setAnomalies(res.data?.data || []);
    } catch (err: unknown) {
      setError(classifyError(err));
    } finally {
      setLoading(false);
    }
  }, [severityFilter, statusFilter]);

  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect -- data fetching on filter change is intentional */
    fetchAnomalies();
  }, [fetchAnomalies]);

  const stats = {
    total: anomalies.length,
    critical: anomalies.filter((a) => a.severity === "critical").length,
    unresolved: anomalies.filter((a) => ["detected", "investigating"].includes(a.anomaly_status)).length,
    avgZScore: anomalies.length
      ? (anomalies.reduce((sum, a) => sum + Math.abs(a.z_score || 0), 0) / anomalies.length).toFixed(2)
      : "0",
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
          <TableSkeleton />
        </>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Total Anomalies</div>
              <div className="text-2xl font-bold tabular-nums">{stats.total}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Critical</div>
              <div className="text-2xl font-bold tabular-nums text-healthcare-red">{stats.critical}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Unresolved</div>
              <div className="text-2xl font-bold tabular-nums text-healthcare-amber">{stats.unresolved}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Avg |Z-Score|</div>
              <div className="text-2xl font-bold tabular-nums">{stats.avgZScore}</div>
            </Card>
          </div>

          <div className="flex items-center gap-3">
            <Select value={severityFilter} onValueChange={(v) => setSeverityFilter(v ?? "all")}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severity</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v ?? "all")}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="detected">Detected</SelectItem>
                <SelectItem value="investigating">Investigating</SelectItem>
                <SelectItem value="confirmed">Confirmed</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={fetchAnomalies}>
              <RefreshCw className="size-3.5 mr-1.5" />
              Refresh
            </Button>
          </div>

          {anomalies.length === 0 ? (
            <EmptyState severityFilter={severityFilter} statusFilter={statusFilter} />
          ) : (
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[100px]">Severity</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead className="w-[120px]">Metric</TableHead>
                      <TableHead className="w-[100px]">Observed</TableHead>
                      <TableHead className="w-[100px]">Baseline</TableHead>
                      <TableHead className="w-[100px]">Deviation</TableHead>
                      <TableHead className="w-[80px]">Z-Score</TableHead>
                      <TableHead className="w-[100px]">Status</TableHead>
                      <TableHead className="w-[80px]">Escalated</TableHead>
                      <TableHead className="w-[80px]">Trend</TableHead>
                      <TableHead className="w-[100px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {anomalies.map((a) => {
                      const severityCfg = SEVERITY_CONFIG[a.severity] || SEVERITY_CONFIG.info;
                      const statusCfg = STATUS_CONFIG[a.anomaly_status] || STATUS_CONFIG.detected;
                      const deviation = a.deviation_percent
                        ? a.deviation_percent
                        : a.expected_value
                          ? ((a.observed_value - a.expected_value) / Math.abs(a.expected_value)) * 100
                          : 0;
                      const isNegative = a.observed_value < a.expected_value;

                      return (
                        <TableRow
                          key={a.id}
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => { setSelectedAnomaly(a); setDialogOpen(true); }}
                        >
                          <TableCell>
                            <Badge className={severityCfg.class} variant="outline">
                              <span className={`size-1.5 rounded-full ${severityCfg.dotClass} mr-1`} />
                              {a.severity}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="font-medium text-sm line-clamp-1">{a.title}</div>
                            {a.description && (
                              <div className="text-xs text-muted-foreground line-clamp-1">{a.description}</div>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="font-mono text-[10px]">
                              {a.metric_code}
                            </Badge>
                          </TableCell>
                          <TableCell className="tabular-nums text-sm font-medium">
                            {formatCurrency(a.observed_value)}
                          </TableCell>
                          <TableCell className="tabular-nums text-sm text-muted-foreground">
                            {formatCurrency(a.expected_value)}
                          </TableCell>
                          <TableCell>
                            <span className={`tabular-nums text-sm font-medium ${isNegative ? "text-healthcare-red" : "text-healthcare-green"}`}>
                              {isNegative ? "" : "+"}{formatPercentage(deviation, 1)}
                            </span>
                          </TableCell>
                          <TableCell>
                            <span className={`tabular-nums text-sm font-medium ${getConfidenceColor(Math.abs(a.z_score) > 3 ? 0.9 : 0.5)}`}>
                              {a.z_score?.toFixed(2)}
                            </span>
                          </TableCell>
                          <TableCell>
                            <Badge className={statusCfg.class} variant="outline">
                              {a.anomaly_status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {a.auto_escalated ? (
                              <Badge className="bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20" variant="outline">
                                <Shield className="size-3 mr-0.5" />
                                Yes
                              </Badge>
                            ) : (
                              <span className="text-xs text-muted-foreground">—</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Sparkline
                              data={a.trend_data || [10, 12, 11, 14, 13, 16, 18]}
                              width={48}
                              height={20}
                              color={isNegative ? "var(--color-healthcare-red)" : "var(--color-healthcare-green)"}
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => { e.stopPropagation(); setSelectedAnomaly(a); setDialogOpen(true); }}
                            >
                              Investigate
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </>
      )}

      <AnomalyDetailDialog
        anomaly={selectedAnomaly}
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
      />
    </div>
  );
}
