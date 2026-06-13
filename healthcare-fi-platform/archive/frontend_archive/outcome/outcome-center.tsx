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
import { outcomesAPI } from "@/lib/api/client";
import { formatDate, formatCurrency } from "@/lib/utils/format";
import { Plus, TrendingUp, TrendingDown, Target, BarChart3 } from "lucide-react";

interface OutcomeDefinition {
  id: string;
  name: string;
  description: string;
  metric_code: string;
  baseline_value: number;
  target_value: number;
  target_direction: string;
  measurement_frequency: string;
  status: string;
}

interface OutcomeMeasurement {
  id: string;
  definition_id: string;
  actual_value: number;
  measured_at: string;
  data_source: string;
  notes: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  inactive: "bg-gray-100 text-gray-800",
  achieved: "bg-emerald-100 text-emerald-800",
  missed: "bg-red-100 text-red-800",
};

export function OutcomeCenter() {
  const [definitions, setDefinitions] = useState<OutcomeDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDef, setSelectedDef] = useState<OutcomeDefinition | null>(null);
  const [measurements, setMeasurements] = useState<OutcomeMeasurement[]>([]);
  const [trajectory, setTrajectory] = useState<any>(null);
  const [causalResult, setCausalResult] = useState<any>(null);
  const [showDefineDialog, setShowDefineDialog] = useState(false);
  const [defineForm, setDefineForm] = useState({
    name: "", description: "", metric_code: "rev_per_patient_day",
    baseline_value: "", target_value: "", target_direction: "increase",
    measurement_frequency: "monthly",
  });

  useEffect(() => { fetchDefinitions(); }, []);

  async function fetchDefinitions() {
    setLoading(true);
    try {
      const res = await outcomesAPI.list();
      setDefinitions(res.data?.data || []);
    } catch { setDefinitions([]); } finally { setLoading(false); }
  }

  async function handleDefine() {
    try {
      await outcomesAPI.defineOutcome({
        ...defineForm,
        baseline_value: parseFloat(defineForm.baseline_value),
        target_value: parseFloat(defineForm.target_value),
        decision_id: null,
      });
      setShowDefineDialog(false);
      setDefineForm({ name: "", description: "", metric_code: "rev_per_patient_day", baseline_value: "", target_value: "", target_direction: "increase", measurement_frequency: "monthly" });
      fetchDefinitions();
    } catch (e) { console.error(e); }
  }

  async function selectDefinition(def: OutcomeDefinition) {
    setSelectedDef(def);
    try {
      const [measRes, trajRes] = await Promise.all([
        outcomesAPI.getMeasurements(def.id),
        outcomesAPI.getTrajectory(def.id),
      ]);
      setMeasurements(measRes.data?.data || []);
      setTrajectory(trajRes.data?.data || null);
    } catch (e) { console.error(e); }
  }

  const totalProgress = trajectory?.progress_percent ?? 0;
  const trendDirection = trajectory?.trend_direction ?? "stable";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Outcome Center</h2>
          <p className="text-muted-foreground">Define, measure, and track decision outcomes</p>
        </div>
        <Dialog open={showDefineDialog} onOpenChange={setShowDefineDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" /> Define Outcome
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>Define Outcome</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={defineForm.name} onChange={e => setDefineForm({ ...defineForm, name: e.target.value })} /></div>
              <div><Label>Description</Label><Input value={defineForm.description} onChange={e => setDefineForm({ ...defineForm, description: e.target.value })} /></div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Metric</Label>
                  <Select value={defineForm.metric_code} onValueChange={v => { if (v) setDefineForm({ ...defineForm, metric_code: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rev_per_patient_day">Rev/Patient Day</SelectItem>
                      <SelectItem value="claim_denial_rate">Claim Denial Rate</SelectItem>
                      <SelectItem value="bed_occupancy">Bed Occupancy</SelectItem>
                      <SelectItem value="cost_per_case">Cost/Case</SelectItem>
                      <SelectItem value="patient_satisfaction">Patient Satisfaction</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Direction</Label>
                  <Select value={defineForm.target_direction} onValueChange={v => { if (v) setDefineForm({ ...defineForm, target_direction: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="increase">Increase</SelectItem>
                      <SelectItem value="decrease">Decrease</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Baseline</Label><Input type="number" value={defineForm.baseline_value} onChange={e => setDefineForm({ ...defineForm, baseline_value: e.target.value })} /></div>
                <div><Label>Target</Label><Input type="number" value={defineForm.target_value} onChange={e => setDefineForm({ ...defineForm, target_value: e.target.value })} /></div>
              </div>
              <Button onClick={handleDefine} className="w-full">Create Outcome Definition</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <Card><CardContent className="p-4"><div className="text-2xl font-bold">{definitions.length}</div><div className="text-sm text-muted-foreground">Total Outcomes</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-2xl font-bold text-green-600">{definitions.filter(d => d.status === "active").length}</div><div className="text-sm text-muted-foreground">Active</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-2xl font-bold text-blue-600">{totalProgress.toFixed(1)}%</div><div className="text-sm text-muted-foreground">Overall Progress</div></CardContent></Card>
        <Card><CardContent className="p-4">
          <div className="flex items-center gap-2">
            {trendDirection === "improving" ? <TrendingUp className="h-5 w-5 text-green-600" /> : trendDirection === "declining" ? <TrendingDown className="h-5 w-5 text-red-600" /> : <Target className="h-5 w-5 text-gray-600" />}
            <div className="text-2xl font-bold capitalize">{trendDirection}</div>
          </div>
          <div className="text-sm text-muted-foreground">Trend</div>
        </CardContent></Card>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className={selectedDef ? "col-span-2" : "col-span-3"}>
          <Card>
            <CardHeader><CardTitle>Outcome Definitions</CardTitle></CardHeader>
            <CardContent>
              {loading ? <div className="text-center py-8 text-muted-foreground">Loading...</div>
              : definitions.length === 0 ? <div className="text-center py-8 text-muted-foreground">No outcomes defined yet</div>
              : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Metric</TableHead>
                      <TableHead>Baseline</TableHead>
                      <TableHead>Target</TableHead>
                      <TableHead>Direction</TableHead>
                      <TableHead>Frequency</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {definitions.map(def => (
                      <TableRow key={def.id} className="cursor-pointer hover:bg-muted/50" onClick={() => selectDefinition(def)}>
                        <TableCell className="font-medium">{def.name}</TableCell>
                        <TableCell><Badge variant="outline">{def.metric_code}</Badge></TableCell>
                        <TableCell>{formatCurrency(def.baseline_value)}</TableCell>
                        <TableCell>{formatCurrency(def.target_value)}</TableCell>
                        <TableCell className="capitalize">{def.target_direction}</TableCell>
                        <TableCell className="capitalize">{def.measurement_frequency}</TableCell>
                        <TableCell><Badge className={STATUS_COLORS[def.status] || ""}>{def.status}</Badge></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>

        {selectedDef && (
          <div className="space-y-4">
            <Card>
              <CardHeader><CardTitle className="text-lg">{selectedDef.name}</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground">{selectedDef.description}</p>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{selectedDef.metric_code}</Badge>
                  <Badge className={STATUS_COLORS[selectedDef.status]}>{selectedDef.status}</Badge>
                </div>
                {trajectory && (
                  <div className="space-y-2 text-sm">
                    <div>Progress: <span className="font-bold">{trajectory.progress_percent?.toFixed(1)}%</span></div>
                    <div>Current: <span className="font-bold">{formatCurrency(trajectory.current_value || 0)}</span></div>
                    <div>Target: <span className="font-bold">{formatCurrency(selectedDef.target_value)}</span></div>
                    <div>Trend: <span className="font-bold capitalize">{trajectory.trend_direction}</span></div>
                    {trajectory.estimated_completion && <div>Est. Completion: <span className="font-bold">{formatDate(trajectory.estimated_completion)}</span></div>}
                  </div>
                )}
                <Button variant="outline" size="sm" onClick={() => setSelectedDef(null)}>Close</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-sm">Measurements</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {measurements.map(m => (
                    <div key={m.id} className="flex justify-between text-sm">
                      <span>{formatDate(m.measured_at)}</span>
                      <span className="font-medium">{formatCurrency(m.actual_value)}</span>
                    </div>
                  ))}
                  {measurements.length === 0 && <div className="text-muted-foreground text-sm">No measurements yet</div>}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
