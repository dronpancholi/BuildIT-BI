'use client';

import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Database, Plus, Trash2, AlertTriangle, History, GitBranch, Link } from 'lucide-react';
import { semanticLayerAPI } from '@/lib/api/client';

interface Dimension { id: string; name: string; source_table: string; source_column: string; cardinality: number; scd_type: string; version: number; is_current: boolean; description?: string; }
interface FactTable { id: string; name: string; source_table: string; grain: string; description?: string; partition_by?: string; }
interface Relationship { id: string; source_entity: string; target_entity: string; relationship_type: string; join_columns: string[]; }
interface Hierarchy { id: string; name: string; dimension_id: string; levels: { name: string; key_column: string; name_column: string }[]; }
interface Alias { canonical_name: string; alias: string; entity_type: string; }

export default function SemanticPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState<Dimension[]>([]);
  const [factTables, setFactTables] = useState<FactTable[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [hierarchies, setHierarchies] = useState<Hierarchy[]>([]);
  const [aliases, setAliases] = useState<Alias[]>([]);
  const [activeTab, setActiveTab] = useState('dimensions');

  const [showCreateDim, setShowCreateDim] = useState(false);
  const [dimName, setDimName] = useState('');
  const [dimSourceTable, setDimSourceTable] = useState('');
  const [dimSourceCol, setDimSourceCol] = useState('');
  const [dimCardinality, setDimCardinality] = useState('100');

  const [showCreateFact, setShowCreateFact] = useState(false);
  const [factName, setFactName] = useState('');
  const [factSourceTable, setFactSourceTable] = useState('');
  const [factGrain, setFactGrain] = useState('transaction');

  const [showCreateRel, setShowCreateRel] = useState(false);
  const [relSource, setRelSource] = useState('');
  const [relTarget, setRelTarget] = useState('');
  const [relType, setRelType] = useState('many_to_one');
  const [relJoinCols, setRelJoinCols] = useState('');

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    setError(null);
    try {
      const [dRes, fRes, rRes, hRes, aRes] = await Promise.all([
        semanticLayerAPI.listDimensions(),
        semanticLayerAPI.listFactTables(),
        semanticLayerAPI.listRelationships(),
        semanticLayerAPI.listHierarchies(),
        semanticLayerAPI.listAliases(),
      ]);
      setDimensions(dRes.data.dimensions || []);
      setFactTables(fRes.data.fact_tables || []);
      setRelationships(rRes.data.relationships || []);
      setHierarchies(hRes.data.hierarchies || []);
      setAliases(aRes.data.aliases || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load semantic layer');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateDimension() {
    if (!dimName || !dimSourceTable || !dimSourceCol) return;
    try {
      await semanticLayerAPI.createDimension({ name: dimName, source_table: dimSourceTable, source_column: dimSourceCol, cardinality: parseInt(dimCardinality) || 100 });
      setDimName(''); setDimSourceTable(''); setDimSourceCol(''); setDimCardinality('100');
      setShowCreateDim(false);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed');
    }
  }

  async function handleCreateFactTable() {
    if (!factName || !factSourceTable) return;
    try {
      await semanticLayerAPI.createFactTable({ name: factName, source_table: factSourceTable, grain: factGrain });
      setFactName(''); setFactSourceTable(''); setFactGrain('transaction');
      setShowCreateFact(false);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed');
    }
  }

  async function handleCreateRelationship() {
    if (!relSource || !relTarget) return;
    try {
      await semanticLayerAPI.createRelationship({ source_entity: relSource, target_entity: relTarget, relationship_type: relType, join_columns: relJoinCols.split(',').map(s => s.trim()).filter(Boolean) });
      setRelSource(''); setRelTarget(''); setRelJoinCols('');
      setShowCreateRel(false);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed');
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Database className="h-8 w-8 text-emerald-600" />
              Semantic Layer
            </h1>
            <p className="text-gray-500 mt-1">SCD2 dimensions, fact tables, hierarchies, and relationships</p>
          </div>
          <Badge className="bg-emerald-100 text-emerald-800">Kimball Methodology</Badge>
        </div>

        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-4 flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-4 w-4" /> {error}
              <Button size="sm" variant="ghost" onClick={() => setError(null)} className="ml-auto">Dismiss</Button>
            </CardContent>
          </Card>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="dimensions">Dimensions ({dimensions.length})</TabsTrigger>
            <TabsTrigger value="facts">Fact Tables ({factTables.length})</TabsTrigger>
            <TabsTrigger value="relationships">Relationships ({relationships.length})</TabsTrigger>
            <TabsTrigger value="aliases">Aliases ({aliases.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="dimensions" className="space-y-4">
            <div className="flex justify-end">
              <Button onClick={() => setShowCreateDim(!showCreateDim)} className="bg-emerald-600 hover:bg-emerald-700">
                <Plus className="h-4 w-4 mr-2" /> New Dimension
              </Button>
            </div>
            {showCreateDim && (
              <Card>
                <CardHeader><CardTitle>Create Dimension</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1"><Label>Name</Label><Input value={dimName} onChange={e => setDimName(e.target.value)} placeholder="department" /></div>
                    <div className="space-y-1"><Label>Source Table</Label><Input value={dimSourceTable} onChange={e => setDimSourceTable(e.target.value)} placeholder="dim_department" /></div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1"><Label>Source Column</Label><Input value={dimSourceCol} onChange={e => setDimSourceCol(e.target.value)} placeholder="department_id" /></div>
                    <div className="space-y-1"><Label>Cardinality</Label><Input type="number" value={dimCardinality} onChange={e => setDimCardinality(e.target.value)} /></div>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleCreateDimension} className="bg-emerald-600 hover:bg-emerald-700">Create</Button>
                    <Button onClick={() => setShowCreateDim(false)} variant="outline">Cancel</Button>
                  </div>
                </CardContent>
              </Card>
            )}
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{[1,2,3].map(i => <Skeleton key={i} className="h-28" />)}</div>
            ) : dimensions.length === 0 ? (
              <Card><CardContent className="p-8 text-center text-gray-500">No dimensions defined. Click "New Dimension" to create one.</CardContent></Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {dimensions.map((d) => (
                  <Card key={d.id} className="hover:border-emerald-300 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold">{d.name}</h3>
                        <Badge className={d.scd_type === 'SCD2' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}>{d.scd_type}</Badge>
                      </div>
                      <div className="text-sm text-gray-600 mt-1 font-mono">{d.source_table}.{d.source_column}</div>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-gray-500">Cardinality: {d.cardinality?.toLocaleString()}</span>
                        <Badge variant="outline" className="text-xs">v{d.version}</Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="facts" className="space-y-4">
            <div className="flex justify-end">
              <Button onClick={() => setShowCreateFact(!showCreateFact)} className="bg-emerald-600 hover:bg-emerald-700">
                <Plus className="h-4 w-4 mr-2" /> New Fact Table
              </Button>
            </div>
            {showCreateFact && (
              <Card>
                <CardHeader><CardTitle>Create Fact Table</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-1"><Label>Name</Label><Input value={factName} onChange={e => setFactName(e.target.value)} placeholder="fact_encounters" /></div>
                    <div className="space-y-1"><Label>Source Table</Label><Input value={factSourceTable} onChange={e => setFactSourceTable(e.target.value)} placeholder="encounters" /></div>
                    <div className="space-y-1"><Label>Grain</Label>
                      <select value={factGrain} onChange={e => setFactGrain(e.target.value)} className="w-full p-2 border rounded text-sm">
                        <option value="transaction">Transaction</option>
                        <option value="daily">Daily</option>
                        <option value="monthly">Monthly</option>
                        <option value="patient">Patient</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleCreateFactTable} className="bg-emerald-600 hover:bg-emerald-700">Create</Button>
                    <Button onClick={() => setShowCreateFact(false)} variant="outline">Cancel</Button>
                  </div>
                </CardContent>
              </Card>
            )}
            {factTables.length === 0 ? (
              <Card><CardContent className="p-8 text-center text-gray-500">No fact tables defined</CardContent></Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {factTables.map((f) => (
                  <Card key={f.id} className="hover:border-emerald-300 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold">{f.name}</h3>
                        <Badge className="bg-blue-100 text-blue-700">{f.grain}</Badge>
                      </div>
                      <div className="text-sm text-gray-600 mt-1 font-mono">{f.source_table}</div>
                      {f.partition_by && <div className="text-xs text-gray-500 mt-1">Partitioned by: {f.partition_by}</div>}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="relationships" className="space-y-4">
            <div className="flex justify-end">
              <Button onClick={() => setShowCreateRel(!showCreateRel)} className="bg-emerald-600 hover:bg-emerald-700">
                <Plus className="h-4 w-4 mr-2" /> New Relationship
              </Button>
            </div>
            {showCreateRel && (
              <Card>
                <CardHeader><CardTitle>Create Relationship</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1"><Label>Source Entity</Label><Input value={relSource} onChange={e => setRelSource(e.target.value)} placeholder="dim_department" /></div>
                    <div className="space-y-1"><Label>Target Entity</Label><Input value={relTarget} onChange={e => setRelTarget(e.target.value)} placeholder="fact_encounters" /></div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1"><Label>Join Columns (comma-separated)</Label><Input value={relJoinCols} onChange={e => setRelJoinCols(e.target.value)} placeholder="department_id, department_id" /></div>
                    <div className="space-y-1"><Label>Type</Label>
                      <select value={relType} onChange={e => setRelType(e.target.value)} className="w-full p-2 border rounded text-sm">
                        <option value="many_to_one">Many to One</option>
                        <option value="one_to_many">One to Many</option>
                        <option value="one_to_one">One to One</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleCreateRelationship} className="bg-emerald-600 hover:bg-emerald-700">Create</Button>
                    <Button onClick={() => setShowCreateRel(false)} variant="outline">Cancel</Button>
                  </div>
                </CardContent>
              </Card>
            )}
            {relationships.length === 0 ? (
              <Card><CardContent className="p-8 text-center text-gray-500">No relationships defined</CardContent></Card>
            ) : (
              <div className="space-y-3">
                {relationships.map((r) => (
                  <Card key={r.id}>
                    <CardContent className="p-4 flex items-center gap-4">
                      <Badge className="bg-emerald-100 text-emerald-700">{r.relationship_type}</Badge>
                      <span className="font-mono text-sm">{r.source_entity}</span>
                      <Link className="h-4 w-4 text-gray-400" />
                      <span className="font-mono text-sm">{r.target_entity}</span>
                      <span className="text-xs text-gray-500 ml-auto">Join: {r.join_columns.join(', ')}</span>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="aliases" className="space-y-4">
            {aliases.length === 0 ? (
              <Card><CardContent className="p-8 text-center text-gray-500">No aliases defined</CardContent></Card>
            ) : (
              <div className="space-y-2">
                {aliases.map((a, i) => (
                  <Card key={i}>
                    <CardContent className="p-3 flex items-center gap-3">
                      <Badge variant="outline">{a.entity_type}</Badge>
                      <span className="font-mono text-sm text-gray-500">{a.alias}</span>
                      <span className="text-gray-400">→</span>
                      <span className="font-mono text-sm font-semibold">{a.canonical_name}</span>
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
