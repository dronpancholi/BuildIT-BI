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
import { featuresAPI } from "@/lib/api/client";
import { formatDate } from "@/lib/utils/format";
import { Plus, CheckCircle, AlertCircle, Database } from "lucide-react";

interface Feature {
  id: string;
  name: string;
  description: string;
  feature_type: string;
  data_type: string;
  source_table: string | null;
  source_column: string | null;
  entity_level: string;
  refresh_frequency: string;
  is_active: boolean;
  last_materialized_at: string | null;
}

export function FeatureCatalog() {
  const [features, setFeatures] = useState<Feature[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [showRegisterDialog, setShowRegisterDialog] = useState(false);
  const [registerForm, setRegisterForm] = useState({
    name: "", description: "", feature_type: "numerical",
    data_type: "float", entity_level: "patient", refresh_frequency: "daily",
    source_table: "", source_column: "",
  });
  const [validatingId, setValidatingId] = useState<string | null>(null);

  useEffect(() => { fetchFeatures(); }, [searchQuery, typeFilter]);

  async function fetchFeatures() {
    setLoading(true);
    try {
      let res;
      if (searchQuery) {
        res = await featuresAPI.search(searchQuery);
      } else {
        res = await featuresAPI.list({ limit: 50 });
      }
      setFeatures(res.data?.data || []);
    } catch { setFeatures([]); } finally { setLoading(false); }
  }

  async function handleRegister() {
    try {
      await featuresAPI.register({
        ...registerForm,
        is_active: true,
      });
      setShowRegisterDialog(false);
      setRegisterForm({ name: "", description: "", feature_type: "numerical", data_type: "float", entity_level: "patient", refresh_frequency: "daily", source_table: "", source_column: "" });
      fetchFeatures();
    } catch (e) { console.error(e); }
  }

  async function handleValidate(id: string) {
    setValidatingId(id);
    try {
      await featuresAPI.validate(id);
    } catch (e) { console.error(e); }
    setValidatingId(null);
  }

  const stats = {
    total: features.length,
    active: features.filter(f => f.is_active).length,
    numerical: features.filter(f => f.feature_type === "numerical").length,
    categorical: features.filter(f => f.feature_type === "categorical").length,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Feature Catalog</h2>
          <p className="text-muted-foreground">Register, validate, and manage ML features</p>
        </div>
        <Dialog open={showRegisterDialog} onOpenChange={setShowRegisterDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" /> Register Feature
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>Register Feature</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={registerForm.name} onChange={e => setRegisterForm({ ...registerForm, name: e.target.value })} /></div>
              <div><Label>Description</Label><Input value={registerForm.description} onChange={e => setRegisterForm({ ...registerForm, description: e.target.value })} /></div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Type</Label>
                  <Select value={registerForm.feature_type} onValueChange={v => { if (v) setRegisterForm({ ...registerForm, feature_type: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="numerical">Numerical</SelectItem>
                      <SelectItem value="categorical">Categorical</SelectItem>
                      <SelectItem value="binary">Binary</SelectItem>
                      <SelectItem value="text">Text</SelectItem>
                      <SelectItem value="temporal">Temporal</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Data Type</Label>
                  <Select value={registerForm.data_type} onValueChange={v => { if (v) setRegisterForm({ ...registerForm, data_type: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="float">Float</SelectItem>
                      <SelectItem value="integer">Integer</SelectItem>
                      <SelectItem value="string">String</SelectItem>
                      <SelectItem value="boolean">Boolean</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Entity Level</Label>
                  <Select value={registerForm.entity_level} onValueChange={v => { if (v) setRegisterForm({ ...registerForm, entity_level: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="patient">Patient</SelectItem>
                      <SelectItem value="encounter">Encounter</SelectItem>
                      <SelectItem value="department">Department</SelectItem>
                      <SelectItem value="branch">Branch</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Refresh</Label>
                  <Select value={registerForm.refresh_frequency} onValueChange={v => { if (v) setRegisterForm({ ...registerForm, refresh_frequency: v }); }}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="realtime">Real-time</SelectItem>
                      <SelectItem value="hourly">Hourly</SelectItem>
                      <SelectItem value="daily">Daily</SelectItem>
                      <SelectItem value="weekly">Weekly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Source Table</Label><Input value={registerForm.source_table} onChange={e => setRegisterForm({ ...registerForm, source_table: e.target.value })} /></div>
                <div><Label>Source Column</Label><Input value={registerForm.source_column} onChange={e => setRegisterForm({ ...registerForm, source_column: e.target.value })} /></div>
              </div>
              <Button onClick={handleRegister} className="w-full">Register Feature</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <Card><CardContent className="p-4"><div className="text-2xl font-bold">{stats.total}</div><div className="text-sm text-muted-foreground">Total Features</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-2xl font-bold text-green-600">{stats.active}</div><div className="text-sm text-muted-foreground">Active</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-2xl font-bold text-blue-600">{stats.numerical}</div><div className="text-sm text-muted-foreground">Numerical</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-2xl font-bold text-purple-600">{stats.categorical}</div><div className="text-sm text-muted-foreground">Categorical</div></CardContent></Card>
      </div>

      <div className="flex gap-4">
        <Input placeholder="Search features..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="w-64" />
        <Select value={typeFilter} onValueChange={v => setTypeFilter(v ?? "all")}>
          <SelectTrigger className="w-[160px]"><SelectValue placeholder="Type" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="numerical">Numerical</SelectItem>
            <SelectItem value="categorical">Categorical</SelectItem>
            <SelectItem value="binary">Binary</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardHeader><CardTitle>Features</CardTitle></CardHeader>
        <CardContent>
          {loading ? <div className="text-center py-8 text-muted-foreground">Loading...</div>
          : features.length === 0 ? <div className="text-center py-8 text-muted-foreground">No features registered yet</div>
          : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Data Type</TableHead>
                  <TableHead>Entity Level</TableHead>
                  <TableHead>Refresh</TableHead>
                  <TableHead>Active</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {features.map(f => (
                  <TableRow key={f.id}>
                    <TableCell>
                      <div className="font-medium">{f.name}</div>
                      <div className="text-xs text-muted-foreground max-w-[200px] truncate">{f.description}</div>
                    </TableCell>
                    <TableCell><Badge variant="outline" className="capitalize">{f.feature_type}</Badge></TableCell>
                    <TableCell className="capitalize">{f.data_type}</TableCell>
                    <TableCell className="capitalize">{f.entity_level}</TableCell>
                    <TableCell className="capitalize">{f.refresh_frequency}</TableCell>
                    <TableCell>
                      {f.is_active ? <CheckCircle className="h-4 w-4 text-green-600" /> : <AlertCircle className="h-4 w-4 text-gray-400" />}
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={() => handleValidate(f.id)} disabled={validatingId === f.id}>
                        {validatingId === f.id ? "Validating..." : "Validate"}
                      </Button>
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
