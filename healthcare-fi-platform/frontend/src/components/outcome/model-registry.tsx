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
import { modelsAPI } from "@/lib/api/client";
import { formatDate, formatCurrency } from "@/lib/utils/format";
import { Plus, CheckCircle, XCircle, Package } from "lucide-react";

interface ModelArtifact {
  id: string;
  name: string;
  version: string;
  model_type: string;
  eval_metric: string;
  eval_value: number;
  fit_quality: string;
  approval_status: string;
  is_production: boolean;
  trained_at: string;
  registered_at: string;
}

const APPROVAL_COLORS: Record<string, string> = {
  pending_review: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  deprecated: "bg-gray-100 text-gray-800",
};

const FIT_COLORS: Record<string, string> = {
  excellent: "bg-emerald-100 text-emerald-800",
  good: "bg-green-100 text-green-800",
  acceptable: "bg-yellow-100 text-yellow-800",
  poor: "bg-orange-100 text-orange-800",
  failing: "bg-red-100 text-red-800",
};

export function ModelRegistry() {
  const [models, setModels] = useState<ModelArtifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [showRegisterDialog, setShowRegisterDialog] = useState(false);
  const [registerForm, setRegisterForm] = useState({
    name: "", version: "", model_type: "forecasting",
    eval_metric: "mape", eval_value: "", fit_quality: "good",
    training_data_hash: "", hyperparameters: "{}", training_duration_seconds: "",
  });

  useEffect(() => { fetchModels(); }, []);

  async function fetchModels() {
    setLoading(true);
    try {
      const res = await modelsAPI.list({ limit: 50 });
      setModels(res.data?.data || []);
    } catch { setModels([]); } finally { setLoading(false); }
  }

  async function handleRegister() {
    try {
      await modelsAPI.register({
        ...registerForm,
        eval_value: parseFloat(registerForm.eval_value),
        training_duration_seconds: registerForm.training_duration_seconds ? parseInt(registerForm.training_duration_seconds) : null,
        is_production: false,
      });
      setShowRegisterDialog(false);
      setRegisterForm({ name: "", version: "", model_type: "forecasting", eval_metric: "mape", eval_value: "", fit_quality: "good", training_data_hash: "", hyperparameters: "{}", training_duration_seconds: "" });
      fetchModels();
    } catch (e) { console.error(e); }
  }

  async function handleApprove(id: string) {
    try { await modelsAPI.approve(id); fetchModels(); } catch (e) { console.error(e); }
  }

  async function handleRetire(id: string) {
    try { await modelsAPI.retire(id); fetchModels(); } catch (e) { console.error(e); }
  }

  const stats = {
    total: models.length,
    production: models.filter(m => m.is_production).length,
    approved: models.filter(m => m.approval_status === "approved").length,
    pending: models.filter(m => m.approval_status === "pending_review").length,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Model Registry</h2>
          <p className="text-muted-foreground">Register, approve, and track ML model artifacts</p>
        </div>
        <Dialog open={showRegisterDialog} onOpenChange={setShowRegisterDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" /> Register Model
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>Register Model</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Name</Label><Input value={registerForm.name} onChange={e => setRegisterForm({ ...registerForm, name: e.target.value })} /></div>
                <div><Label>Version</Label><Input value={registerForm.version} onChange={e => setRegisterForm({ ...registerForm, version: e.target.value })} /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Model Type</Label>
                  <Select value={registerForm.model_type} onValueChange={v => { if (v) setRegisterForm({ ...registerForm, model_type: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="forecasting">Forecasting</SelectItem>
                      <SelectItem value="anomaly_detection">Anomaly Detection</SelectItem>
                      <SelectItem value="classification">Classification</SelectItem>
                      <SelectItem value="regression">Regression</SelectItem>
                      <SelectItem value="causal">Causal</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Fit Quality</Label>
                  <Select value={registerForm.fit_quality} onValueChange={v => { if (v) setRegisterForm({ ...registerForm, fit_quality: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="excellent">Excellent</SelectItem>
                      <SelectItem value="good">Good</SelectItem>
                      <SelectItem value="acceptable">Acceptable</SelectItem>
                      <SelectItem value="poor">Poor</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Eval Metric</Label>
                  <Select value={registerForm.eval_metric} onValueChange={v => { if (v) setRegisterForm({ ...registerForm, eval_metric: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="mape">MAPE</SelectItem>
                      <SelectItem value="rmse">RMSE</SelectItem>
                      <SelectItem value="mae">MAE</SelectItem>
                      <SelectItem value="r2">R²</SelectItem>
                      <SelectItem value="auc">AUC</SelectItem>
                      <SelectItem value="f1">F1</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Eval Value</Label><Input type="number" step="0.001" value={registerForm.eval_value} onChange={e => setRegisterForm({ ...registerForm, eval_value: e.target.value })} /></div>
              </div>
              <Button onClick={handleRegister} className="w-full">Register Model</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <Card><CardContent className="p-4"><div className="text-2xl font-bold">{stats.total}</div><div className="text-sm text-muted-foreground">Total Models</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-2xl font-bold text-green-600">{stats.production}</div><div className="text-sm text-muted-foreground">In Production</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-2xl font-bold text-blue-600">{stats.approved}</div><div className="text-sm text-muted-foreground">Approved</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-2xl font-bold text-yellow-600">{stats.pending}</div><div className="text-sm text-muted-foreground">Pending Review</div></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Registered Models</CardTitle></CardHeader>
        <CardContent>
          {loading ? <div className="text-center py-8 text-muted-foreground">Loading...</div>
          : models.length === 0 ? <div className="text-center py-8 text-muted-foreground">No models registered yet</div>
          : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Eval</TableHead>
                  <TableHead>Fit Quality</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Production</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {models.map(m => (
                  <TableRow key={m.id}>
                    <TableCell className="font-medium">{m.name}</TableCell>
                    <TableCell><Badge variant="outline">{m.version}</Badge></TableCell>
                    <TableCell className="capitalize">{m.model_type.replace(/_/g, " ")}</TableCell>
                    <TableCell>{m.eval_metric.toUpperCase()}: {m.eval_value?.toFixed(4)}</TableCell>
                    <TableCell><Badge className={FIT_COLORS[m.fit_quality] || ""}>{m.fit_quality}</Badge></TableCell>
                    <TableCell><Badge className={APPROVAL_COLORS[m.approval_status] || ""}>{m.approval_status.replace(/_/g, " ")}</Badge></TableCell>
                    <TableCell>{m.is_production ? <CheckCircle className="h-4 w-4 text-green-600" /> : <XCircle className="h-4 w-4 text-gray-400" />}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {m.approval_status === "pending_review" && (
                          <Button variant="ghost" size="sm" onClick={() => handleApprove(m.id)}>Approve</Button>
                        )}
                        {m.is_production && (
                          <Button variant="ghost" size="sm" onClick={() => handleRetire(m.id)}>Retire</Button>
                        )}
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
  );
}
