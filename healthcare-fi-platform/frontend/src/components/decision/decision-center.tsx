"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { decisionsAPI, intelligenceAPI } from "@/lib/api/client";
import { formatDate, formatCurrency } from "@/lib/utils/format";
import { CheckCircle, XCircle, Clock, Play, Archive, Plus } from "lucide-react";

interface Decision {
  id: string;
  title: string;
  description: string;
  decision_type: string;
  category: string;
  status: string;
  priority_label: string;
  urgency_label: string;
  owner_id: string;
  estimated_value: number | null;
  confidence_score: number | null;
  created_at: string;
  updated_at: string;
  review_required: boolean;
}

interface TimelineEvent {
  event_type: string;
  from_status: string | null;
  to_status: string;
  event_timestamp: string;
  notes: string | null;
}

interface Evidence {
  id: string;
  evidence_type: string;
  title: string;
  description: string;
  source_id: string | null;
  weight: number;
}

const STATUS_COLORS: Record<string, string> = {
  proposed: "bg-blue-100 text-blue-800",
  reviewing: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  in_progress: "bg-purple-100 text-purple-800",
  completed: "bg-emerald-100 text-emerald-800",
  measured: "bg-cyan-100 text-cyan-800",
  archived: "bg-gray-100 text-gray-800",
};

const PRIORITY_COLORS: Record<string, string> = {
  P0: "bg-red-100 text-red-800 border-red-300",
  P1: "bg-orange-100 text-orange-800 border-orange-300",
  P2: "bg-yellow-100 text-yellow-800 border-yellow-300",
  P3: "bg-blue-100 text-blue-800 border-blue-300",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  proposed: <Clock className="h-4 w-4" />,
  reviewing: <Clock className="h-4 w-4" />,
  approved: <CheckCircle className="h-4 w-4" />,
  rejected: <XCircle className="h-4 w-4" />,
  in_progress: <Play className="h-4 w-4" />,
  completed: <CheckCircle className="h-4 w-4" />,
  measured: <CheckCircle className="h-4 w-4" />,
  archived: <Archive className="h-4 w-4" />,
};

export function DecisionCenter() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDecision, setSelectedDecision] = useState<Decision | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [valueData, setValueData] = useState<any>(null);
  const [showProposeDialog, setShowProposeDialog] = useState(false);
  const [proposeForm, setProposeForm] = useState({
    title: "", description: "", decision_type: "strategic",
    category: "revenue", priority_label: "P1", urgency_label: "medium",
    estimated_value: "", rationale: "",
  });

  useEffect(() => { fetchDecisions(); }, [statusFilter, typeFilter, searchQuery]);

  async function fetchDecisions() {
    setLoading(true);
    try {
      const params: Record<string, any> = { limit: 50 };
      if (statusFilter !== "all") params.status = statusFilter;
      if (typeFilter !== "all") params.decision_type = typeFilter;
      if (searchQuery) params.search = searchQuery;
      const res = await decisionsAPI.list(params);
      setDecisions(res.data?.data || []);
    } catch { setDecisions([]); } finally { setLoading(false); }
  }

  async function handlePropose() {
    try {
      await decisionsAPI.propose({
        title: proposeForm.title,
        description: proposeForm.description,
        decision_type: proposeForm.decision_type,
        category: proposeForm.category,
        priority: proposeForm.priority_label,
        urgency: proposeForm.urgency_label,
        estimated_value: proposeForm.estimated_value ? parseFloat(proposeForm.estimated_value) : null,
        trigger_type: "manual",
        trigger_summary: proposeForm.rationale,
      });
      setShowProposeDialog(false);
      setProposeForm({ title: "", description: "", decision_type: "strategic", category: "revenue", priority_label: "P1", urgency_label: "medium", estimated_value: "", rationale: "" });
      fetchDecisions();
    } catch (e) { console.error("Failed to propose:", e); }
  }

  async function handleAction(action: string, decisionId: string) {
    try {
      switch (action) {
        case "submit": await decisionsAPI.submit(decisionId); break;
        case "approve": await decisionsAPI.approve(decisionId); break;
        case "start": await decisionsAPI.startImplementation(decisionId); break;
        case "complete": await decisionsAPI.complete(decisionId); break;
      }
      fetchDecisions();
      if (selectedDecision?.id === decisionId) selectDecision(decisions.find(d => d.id === decisionId)!);
    } catch (e) { console.error("Action failed:", e); }
  }

  async function selectDecision(d: Decision) {
    setSelectedDecision(d);
    try {
      const [tlRes, valRes] = await Promise.all([
        decisionsAPI.getTimeline(d.id),
        decisionsAPI.getValue(d.id),
      ]);
      setTimeline(tlRes.data?.data || []);
      setValueData(valRes.data?.data || null);
    } catch (e) { console.error(e); }
  }

  const stats = {
    total: decisions.length,
    active: decisions.filter(d => ["approved", "in_progress"].includes(d.status)).length,
    completed: decisions.filter(d => d.status === "completed").length,
    pendingReview: decisions.filter(d => d.review_required && d.status === "reviewing").length,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Decision Center</h2>
          <p className="text-muted-foreground">Propose, review, and track strategic decisions</p>
        </div>
        <Dialog open={showProposeDialog} onOpenChange={setShowProposeDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" /> Propose Decision
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>Propose New Decision</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Title</Label><Input value={proposeForm.title} onChange={e => setProposeForm({ ...proposeForm, title: e.target.value })} /></div>
              <div><Label>Description</Label><Input value={proposeForm.description} onChange={e => setProposeForm({ ...proposeForm, description: e.target.value })} /></div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Type</Label>
                  <Select value={proposeForm.decision_type} onValueChange={v => { if (v) setProposeForm({ ...proposeForm, decision_type: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="strategic">Strategic</SelectItem>
                      <SelectItem value="operational">Operational</SelectItem>
                      <SelectItem value="tactical">Tactical</SelectItem>
                      <SelectItem value="emergency">Emergency</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Category</Label>
                  <Select value={proposeForm.category} onValueChange={v => { if (v) setProposeForm({ ...proposeForm, category: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="revenue">Revenue</SelectItem>
                      <SelectItem value="cost">Cost</SelectItem>
                      <SelectItem value="quality">Quality</SelectItem>
                      <SelectItem value="compliance">Compliance</SelectItem>
                      <SelectItem value="operational">Operational</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div><Label>Priority</Label>
                  <Select value={proposeForm.priority_label} onValueChange={v => { if (v) setProposeForm({ ...proposeForm, priority_label: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="P0">P0 - Critical</SelectItem>
                      <SelectItem value="P1">P1 - High</SelectItem>
                      <SelectItem value="P2">P2 - Medium</SelectItem>
                      <SelectItem value="P3">P3 - Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Urgency</Label>
                  <Select value={proposeForm.urgency_label} onValueChange={v => { if (v) setProposeForm({ ...proposeForm, urgency_label: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Est. Value</Label><Input type="number" value={proposeForm.estimated_value} onChange={e => setProposeForm({ ...proposeForm, estimated_value: e.target.value })} /></div>
              </div>
              <div><Label>Rationale</Label><Input value={proposeForm.rationale} onChange={e => setProposeForm({ ...proposeForm, rationale: e.target.value })} /></div>
              <Button onClick={handlePropose} className="w-full">Submit Proposal</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <Card><CardContent className="p-4"><div className="text-2xl font-bold">{stats.total}</div><div className="text-sm text-muted-foreground">Total Decisions</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-2xl font-bold text-purple-600">{stats.active}</div><div className="text-sm text-muted-foreground">Active</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-2xl font-bold text-green-600">{stats.completed}</div><div className="text-sm text-muted-foreground">Completed</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-2xl font-bold text-yellow-600">{stats.pendingReview}</div><div className="text-sm text-muted-foreground">Pending Review</div></CardContent></Card>
      </div>

      <div className="flex gap-4">
        <Input placeholder="Search decisions..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="w-64" />
        <Select value={statusFilter} onValueChange={v => setStatusFilter(v ?? "all")}>
          <SelectTrigger className="w-[160px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="proposed">Proposed</SelectItem>
            <SelectItem value="reviewing">Reviewing</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
        <Select value={typeFilter} onValueChange={v => setTypeFilter(v ?? "all")}>
          <SelectTrigger className="w-[160px]"><SelectValue placeholder="Type" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="strategic">Strategic</SelectItem>
            <SelectItem value="operational">Operational</SelectItem>
            <SelectItem value="tactical">Tactical</SelectItem>
            <SelectItem value="emergency">Emergency</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className={selectedDecision ? "col-span-2" : "col-span-3"}>
          <Card>
            <CardHeader><CardTitle>Decisions</CardTitle></CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8 text-muted-foreground">Loading decisions...</div>
              ) : decisions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">No decisions found. Propose your first decision.</div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Priority</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Value</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {decisions.map((d) => (
                      <TableRow key={d.id} className="cursor-pointer hover:bg-muted/50" onClick={() => selectDecision(d)}>
                        <TableCell><Badge className={PRIORITY_COLORS[d.priority_label] || ""}>{d.priority_label}</Badge></TableCell>
                        <TableCell className="font-medium max-w-[250px] truncate">{d.title}</TableCell>
                        <TableCell className="capitalize">{d.decision_type}</TableCell>
                        <TableCell className="capitalize">{d.category}</TableCell>
                        <TableCell>{d.estimated_value ? formatCurrency(d.estimated_value) : "—"}</TableCell>
                        <TableCell><Badge className={STATUS_COLORS[d.status] || ""}>{d.status}</Badge></TableCell>
                        <TableCell onClick={e => e.stopPropagation()}>
                          <div className="flex gap-1">
                            {d.status === "proposed" && <Button variant="ghost" size="sm" onClick={() => handleAction("submit", d.id)}>Submit</Button>}
                            {d.status === "reviewing" && <Button variant="ghost" size="sm" onClick={() => handleAction("approve", d.id)}>Approve</Button>}
                            {d.status === "approved" && <Button variant="ghost" size="sm" onClick={() => handleAction("start", d.id)}>Start</Button>}
                            {d.status === "in_progress" && <Button variant="ghost" size="sm" onClick={() => handleAction("complete", d.id)}>Complete</Button>}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>

        {selectedDecision && (
          <div className="space-y-4">
            <Card>
              <CardHeader><CardTitle className="text-lg">{selectedDecision.title}</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground">{selectedDecision.description}</p>
                <div className="flex items-center gap-2">
                  <Badge className={STATUS_COLORS[selectedDecision.status]}>{selectedDecision.status}</Badge>
                  <Badge className={PRIORITY_COLORS[selectedDecision.priority_label]}>{selectedDecision.priority_label}</Badge>
                </div>
                {valueData && (
                  <div className="text-sm">
                    <div className="font-medium">Estimated Value</div>
                    <div className="text-xl font-bold text-green-600">{formatCurrency(valueData.total_estimated_value || 0)}</div>
                  </div>
                )}
                <Button variant="outline" size="sm" onClick={() => setSelectedDecision(null)}>Close</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-sm">Timeline</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {timeline.map((ev, i) => (
                    <div key={i} className="flex items-start gap-3 text-sm">
                      {STATUS_ICONS[ev.to_status] || <Clock className="h-4 w-4" />}
                      <div>
                        <div className="font-medium capitalize">{ev.event_type.replace(/_/g, " ")}</div>
                        <div className="text-muted-foreground text-xs">{formatDate(ev.event_timestamp)}</div>
                        {ev.notes && <div className="text-xs text-muted-foreground mt-1">{ev.notes}</div>}
                      </div>
                    </div>
                  ))}
                  {timeline.length === 0 && <div className="text-muted-foreground text-sm">No timeline events</div>}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
