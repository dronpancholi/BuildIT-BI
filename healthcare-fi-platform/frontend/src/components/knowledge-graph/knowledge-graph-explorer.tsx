"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { graphAPI, intelligenceAPI } from "@/lib/api/client";
import { AlertTriangle, GitBranch, Network, Shield, Zap, RefreshCw, Eye, ListFilter } from "lucide-react";

interface GraphNode {
  id: string;
  node_type: string;
  title: string;
  description: string;
  created_at: string;
}

interface GraphEdge {
  id: string;
  source_id: string;
  target_id: string;
  relationship_type: string;
  weight: number;
  created_at: string;
}

interface GraphStats {
  total_nodes: number;
  total_edges: number;
  node_counts: Record<string, number>;
  edge_counts: Record<string, number>;
}

interface GraphPath {
  nodes: string[];
  edges: string[];
  length: number;
}

interface ImpactNetwork {
  source_id: string;
  impacted_entities: { entity_id: string; entity_type: string; impact_score: number }[];
  total_impact: number;
}

interface ValidationChain {
  decision_id: string;
  validations: { node_id: string; node_type: string; confidence: number; timestamp: string }[];
  overall_confidence: number;
}

interface Contradiction {
  node_a_id: string;
  node_b_id: string;
  relationship_a: string;
  relationship_b: string;
  severity: string;
}

export function KnowledgeGraphExplorer() {
  const [activeTab, setActiveTab] = useState("graph");
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [nodeTypeFilter, setNodeTypeFilter] = useState("");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [pathResult, setPathResult] = useState<GraphPath | null>(null);
  const [impactResult, setImpactResult] = useState<ImpactNetwork | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationChain | null>(null);
  const [contradictions, setContradictions] = useState<Contradiction[]>([]);
  const [pathFrom, setPathFrom] = useState("");
  const [pathTo, setPathTo] = useState("");
  const [impactDecisionId, setImpactDecisionId] = useState("");

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [statsRes, contraRes, nodesRes, edgesRes] = await Promise.allSettled([
        graphAPI.getStats(),
        graphAPI.findContradictions(),
        intelligenceAPI.getGraphNodes({ limit: 100 }),
        intelligenceAPI.listRelationships({ limit: 200 }),
      ]);
      
      if (statsRes.status === "fulfilled") {
        setStats(statsRes.value.data?.data || statsRes.value.data || null);
      }
      if (contraRes.status === "fulfilled") {
        setContradictions(contraRes.value.data?.data || contraRes.value.data || []);
      }
      if (nodesRes.status === "fulfilled") {
        setNodes(nodesRes.value.data?.data || nodesRes.value.data?.nodes || nodesRes.value.data || []);
      }
      if (edgesRes.status === "fulfilled") {
        setEdges(edgesRes.value.data?.data || edgesRes.value.data?.relationships || edgesRes.value.data || []);
      }
    } catch (e) {
      console.error("Failed to fetch graph data", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  async function findPath() {
    if (!pathFrom || !pathTo) return;
    try {
      const res = await graphAPI.findPathway(pathFrom, pathTo);
      setPathResult(res.data?.data || res.data || null);
    } catch (e) {
      console.error(e);
    }
  }

  async function getImpact() {
    if (!impactDecisionId) return;
    try {
      const res = await graphAPI.getImpactNetwork(impactDecisionId);
      setImpactResult(res.data?.data || res.data || null);
    } catch (e) {
      console.error(e);
    }
  }

  async function getValidation() {
    if (!impactDecisionId) return;
    try {
      const res = await graphAPI.getValidationChain(impactDecisionId);
      setValidationResult(res.data?.data || res.data || null);
    } catch (e) {
      console.error(e);
    }
  }

  const nodeColors: Record<string, string> = {
    hospital: '#0066CC',       // healthcare-blue
    department: '#00A86B',     // healthcare-green
    metric: '#9333EA',         // purple
    insight: '#00A3A3',        // teal
    anomaly: '#CC3333',        // red
    opportunity: '#FF9900',    // amber
    recommendation: '#D946EF',  // magenta
    default: '#6B7280',        // gray
  };

  const filteredNodes = nodeTypeFilter ? nodes.filter(n => n.node_type === nodeTypeFilter) : nodes;

  // Render SVG Force/Circular Directed Graph
  const renderGraphVisualization = () => {
    if (loading) {
      return (
        <div className="flex flex-col items-center justify-center h-[500px] text-muted-foreground">
          <RefreshCw className="h-8 w-8 animate-spin text-primary mb-4" />
          <p>Analyzing knowledge graph topologies...</p>
        </div>
      );
    }

    if (!nodes || nodes.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-[500px] text-muted-foreground text-center p-6">
          <Network className="h-16 w-16 mb-4 opacity-40 text-primary" />
          <h3 className="text-lg font-semibold mb-2">No Active Graph Topology Detected</h3>
          <p className="max-w-md mb-4 text-sm">
            To populate the knowledge network and explore node connections, run the database seeding script.
          </p>
          <Button onClick={fetchAll} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" /> Retry Connection
          </Button>
        </div>
      );
    }

    const width = 800;
    const height = 500;
    const cx = width / 2;
    const cy = height / 2;
    const radius = Math.min(width, height) * 0.38;
    const angleStep = (2 * Math.PI) / nodes.length;

    const positions = nodes.map((node, i) => {
      const angle = angleStep * i - Math.PI / 2;
      return {
        id: node.id,
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
        node,
      };
    });

    const posMap = new Map(positions.map(p => [p.id, p]));

    return (
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 relative border rounded-xl overflow-hidden bg-muted/5 shadow-inner">
          <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="w-full h-auto min-h-[400px]">
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="28"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
              </marker>
            </defs>

            {/* Edges */}
            {edges.map((edge, i) => {
              const source = posMap.get(edge.source_id);
              const target = posMap.get(edge.target_id);
              if (!source || !target) return null;

              return (
                <g key={`edge-${edge.id || i}`}>
                  <line
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke="#94a3b8"
                    strokeWidth={1.5 + (edge.weight || 0) * 2}
                    strokeOpacity={0.4}
                    markerEnd="url(#arrow)"
                    className="transition-opacity hover:stroke-primary hover:stroke-opacity-80 cursor-pointer"
                  />
                  {/* Subtle label in middle */}
                  <text
                    x={(source.x + target.x) / 2}
                    y={(source.y + target.y) / 2 - 4}
                    textAnchor="middle"
                    fontSize={8}
                    className="fill-muted-foreground pointer-events-none select-none opacity-0 hover:opacity-100 transition-opacity bg-background"
                  >
                    {edge.relationship_type}
                  </text>
                </g>
              );
            })}

            {/* Nodes */}
            {positions.map(({ x, y, node }) => {
              const isSelected = selectedNode?.id === node.id;
              const color = nodeColors[node.node_type] || nodeColors.default;

              return (
                <g
                  key={`node-${node.id}`}
                  onClick={() => setSelectedNode(node)}
                  className="cursor-pointer group"
                >
                  <circle
                    cx={x}
                    cy={y}
                    r={isSelected ? 26 : 20}
                    fill={color}
                    fillOpacity={isSelected ? 0.95 : 0.85}
                    stroke={isSelected ? "#ffffff" : "transparent"}
                    strokeWidth={isSelected ? 3 : 0}
                    className="transition-all duration-200 group-hover:scale-110 shadow-lg"
                    style={{ filter: isSelected ? 'drop-shadow(0px 0px 8px rgba(0,0,0,0.35))' : 'none' }}
                  />
                  {/* Icon placeholder/type symbol */}
                  <text
                    x={x}
                    y={y + 4}
                    textAnchor="middle"
                    fill="#ffffff"
                    fontSize={10}
                    fontWeight="bold"
                    className="pointer-events-none select-none"
                  >
                    {node.node_type.substring(0, 2).toUpperCase()}
                  </text>
                  {/* Text Label */}
                  <text
                    x={x}
                    y={y + 36}
                    textAnchor="middle"
                    fontSize={9}
                    fontWeight={isSelected ? "bold" : "normal"}
                    className={`${isSelected ? "fill-foreground" : "fill-muted-foreground"} pointer-events-none select-none`}
                  >
                    {node.title.length > 15 ? `${node.title.substring(0, 12)}...` : node.title}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 flex flex-wrap gap-3 p-3 bg-background/90 backdrop-blur-sm rounded-lg border text-xs shadow-sm max-w-sm">
            {Object.entries(nodeColors).map(([type, color]) => (
              <div key={type} className="flex items-center gap-1.5">
                <div className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
                <span className="capitalize text-muted-foreground font-medium">{type}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Node Details Panel */}
        <div className="space-y-4">
          {selectedNode ? (
            <Card className="shadow-sm border-primary/10">
              <CardHeader className="pb-3 border-b bg-muted/20">
                <CardTitle className="text-sm font-semibold flex items-center justify-between gap-2">
                  <span className="truncate">Node Inspector</span>
                  <Badge style={{ backgroundColor: nodeColors[selectedNode.node_type] || nodeColors.default, color: 'white' }}>
                    {selectedNode.node_type}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4 text-xs">
                <div>
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Node Name</label>
                  <div className="text-sm font-semibold mt-0.5 text-foreground">{selectedNode.title}</div>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Description</label>
                  <div className="text-muted-foreground leading-relaxed mt-1 text-sm">{selectedNode.description}</div>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Entity UUID</label>
                  <div className="font-mono bg-muted p-1.5 rounded mt-1 overflow-x-auto select-all">{selectedNode.id}</div>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Created Timestamp</label>
                  <div className="text-muted-foreground mt-0.5">{new Date(selectedNode.created_at).toLocaleString()}</div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-dashed flex items-center justify-center text-center p-6 h-full min-h-[200px]">
              <CardContent className="p-0 text-muted-foreground space-y-2">
                <Eye className="h-8 w-8 mx-auto opacity-30 text-primary" />
                <p className="text-xs">Select a node in the visualizer network to inspect details.</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Knowledge Graph Explorer</h2>
          <p className="text-muted-foreground">
            Visualize hospital structures, metrics, dynamic decisions, and validate causality pathways.
          </p>
        </div>
        <Button onClick={fetchAll} disabled={loading} variant="outline" size="sm">
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh Network
        </Button>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="shadow-sm">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Knowledge Nodes</p>
              <h3 className="text-2xl font-bold mt-1">{stats?.total_nodes || 0}</h3>
            </div>
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <Network className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Causal Edges</p>
              <h3 className="text-2xl font-bold mt-1">{stats?.total_edges || 0}</h3>
            </div>
            <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
              <GitBranch className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Contradictions</p>
              <h3 className="text-2xl font-bold mt-1">{contradictions.length}</h3>
            </div>
            <div className="p-2 rounded-lg bg-yellow-100 dark:bg-yellow-900/30">
              <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Validation Health</p>
              <h3 className="text-2xl font-bold mt-1">
                {validationResult?.overall_confidence ? (validationResult.overall_confidence * 100).toFixed(1) + "%" : "100.0%"}
              </h3>
            </div>
            <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
              <Shield className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs list */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid grid-cols-2 md:flex md:w-auto h-auto p-1 bg-muted rounded-lg flex-wrap gap-1">
          <TabsTrigger value="graph" className="py-2 text-xs md:text-sm">Network Viz</TabsTrigger>
          <TabsTrigger value="nodes" className="py-2 text-xs md:text-sm">Nodes list</TabsTrigger>
          <TabsTrigger value="edges" className="py-2 text-xs md:text-sm">Relationships</TabsTrigger>
          <TabsTrigger value="pathway" className="py-2 text-xs md:text-sm">Pathway Finder</TabsTrigger>
          <TabsTrigger value="impact" className="py-2 text-xs md:text-sm">Impact Network</TabsTrigger>
          <TabsTrigger value="validation" className="py-2 text-xs md:text-sm">Validation</TabsTrigger>
          <TabsTrigger value="contradictions" className="py-2 text-xs md:text-sm">Contradictions</TabsTrigger>
        </TabsList>

        {/* Tab 1: SVG Visualizer */}
        <TabsContent value="graph" className="space-y-4 outline-none">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <Network className="h-5 w-5 text-primary" />
                Topology Mapping Canvas
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              {renderGraphVisualization()}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Nodes Table */}
        <TabsContent value="nodes" className="space-y-4 outline-none">
          <Card>
            <CardHeader className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b gap-4">
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <Eye className="h-5 w-5 text-primary" />
                Entity Nodes Catalog
              </CardTitle>
              <div className="flex items-center gap-2 text-xs">
                <ListFilter className="h-4 w-4 text-muted-foreground" />
                <select
                  value={nodeTypeFilter}
                  onChange={(e) => setNodeTypeFilter(e.target.value)}
                  className="bg-transparent border rounded p-1"
                >
                  <option value="">All Node Types</option>
                  <option value="hospital">Hospital</option>
                  <option value="department">Department</option>
                  <option value="metric">Metric</option>
                  <option value="decision">Decision</option>
                  <option value="insight">Insight</option>
                </select>
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="rounded-lg border overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Registered</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredNodes.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center py-6 text-muted-foreground">
                          No nodes found.
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredNodes.map((n) => (
                        <TableRow key={n.id}>
                          <TableCell>
                            <Badge
                              style={{
                                backgroundColor: nodeColors[n.node_type] || nodeColors.default,
                                color: 'white'
                              }}
                            >
                              {n.node_type}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-medium">{n.title}</TableCell>
                          <TableCell className="max-w-xs truncate">{n.description}</TableCell>
                          <TableCell className="text-muted-foreground text-xs">
                            {new Date(n.created_at).toLocaleDateString()}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Edges Table */}
        <TabsContent value="edges" className="space-y-4 outline-none">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <GitBranch className="h-5 w-5 text-primary" />
                Causal Edges Registry
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="rounded-lg border overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Source Node ID</TableHead>
                      <TableHead>Relationship</TableHead>
                      <TableHead>Target Node ID</TableHead>
                      <TableHead>Weight</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {edges.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center py-6 text-muted-foreground">
                          No relationships registered.
                        </TableCell>
                      </TableRow>
                    ) : (
                      edges.map((e) => (
                        <TableRow key={e.id}>
                          <TableCell className="font-mono text-xs truncate max-w-[150px]">{e.source_id}</TableCell>
                          <TableCell><Badge variant="outline">{e.relationship_type}</Badge></TableCell>
                          <TableCell className="font-mono text-xs truncate max-w-[150px]">{e.target_id}</TableCell>
                          <TableCell className="font-medium">{e.weight?.toFixed(2)}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 4: Pathway Finder */}
        <TabsContent value="pathway" className="space-y-4 outline-none">
          <Card>
            <CardHeader><CardTitle>Pathway Finder</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">From Node ID</label>
                  <Input value={pathFrom} onChange={e => setPathFrom(e.target.value)} placeholder="e.g. Hospital or Metric UUID" className="mt-1" />
                </div>
                <div className="flex-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">To Node ID</label>
                  <Input value={pathTo} onChange={e => setPathTo(e.target.value)} placeholder="e.g. Department or Decision UUID" className="mt-1" />
                </div>
                <Button onClick={findPath} size="sm">Find Pathway</Button>
              </div>
              {pathResult && (
                <div className="mt-4 p-4 border rounded-lg bg-muted/20 space-y-2 text-sm">
                  <div className="font-bold flex items-center gap-1.5">
                    <Zap className="h-4 w-4 text-healthcare-amber" />
                    Causal Path Length: {pathResult.length}
                  </div>
                  <div className="text-muted-foreground leading-relaxed">
                    Nodes: {pathResult.nodes.map(id => id.substring(0, 8)).join(" → ")}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 5: Impact Network */}
        <TabsContent value="impact" className="space-y-4 outline-none">
          <Card>
            <CardHeader><CardTitle>Impact Network</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Decision Node ID</label>
                  <Input value={impactDecisionId} onChange={e => setImpactDecisionId(e.target.value)} placeholder="e.g. Decision UUID" className="mt-1" />
                </div>
                <Button onClick={getImpact} size="sm">Analyze Impact</Button>
              </div>
              {impactResult && (
                <div className="mt-4 space-y-3">
                  <div className="text-sm font-semibold">
                    Total Network Impact: <span className="font-bold text-healthcare-blue">{impactResult.total_impact?.toFixed(3)}</span>
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Entity</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Impact Score</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {impactResult.impacted_entities.map((e, i) => (
                        <TableRow key={i}>
                          <TableCell className="font-mono text-xs">{e.entity_id}</TableCell>
                          <TableCell><Badge variant="outline">{e.entity_type}</Badge></TableCell>
                          <TableCell className="font-bold text-healthcare-green">{e.impact_score?.toFixed(3)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 6: Validation */}
        <TabsContent value="validation" className="space-y-4 outline-none">
          <Card>
            <CardHeader><CardTitle>Validation Chain</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-4 items-end mb-4">
                <div className="flex-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Decision ID</label>
                  <Input value={impactDecisionId} onChange={e => setImpactDecisionId(e.target.value)} placeholder="e.g. Decision UUID" className="mt-1" />
                </div>
                <Button onClick={getValidation} size="sm">Validate Chain</Button>
              </div>
              {validationResult && (
                <div className="space-y-3">
                  <div className="text-sm font-semibold">
                    Overall Confidence Score: <span className="font-bold text-green-600">{(validationResult.overall_confidence * 100).toFixed(1)}%</span>
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Validation Node</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Confidence</TableHead>
                        <TableHead>Timestamp</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {validationResult.validations.map((v, i) => (
                        <TableRow key={i}>
                          <TableCell className="font-mono text-xs">{v.node_id}</TableCell>
                          <TableCell><Badge variant="outline">{v.node_type}</Badge></TableCell>
                          <TableCell className="font-bold text-healthcare-green">{(v.confidence * 100).toFixed(1)}%</TableCell>
                          <TableCell className="text-muted-foreground text-xs">{v.timestamp}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 7: Contradictions */}
        <TabsContent value="contradictions" className="space-y-4 outline-none">
          <Card>
            <CardHeader><CardTitle>Contradictions ({contradictions.length})</CardTitle></CardHeader>
            <CardContent>
              {contradictions.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground space-y-2">
                  <Shield className="h-10 w-10 mx-auto opacity-30 text-green-500" />
                  <p className="text-sm font-semibold">No Logic Contradictions Detected</p>
                  <p className="text-xs max-w-sm mx-auto">The knowledge network data conforms perfectly to causal logic validation filters.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Node A</TableHead>
                      <TableHead>Node B</TableHead>
                      <TableHead>Relationship A</TableHead>
                      <TableHead>Relationship B</TableHead>
                      <TableHead>Severity</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {contradictions.map((c, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-mono text-xs">{c.node_a_id.substring(0, 8)}...</TableCell>
                        <TableCell className="font-mono text-xs">{c.node_b_id.substring(0, 8)}...</TableCell>
                        <TableCell><Badge variant="outline">{c.relationship_a}</Badge></TableCell>
                        <TableCell><Badge variant="outline">{c.relationship_b}</Badge></TableCell>
                        <TableCell>
                          <Badge className={c.severity === "high" ? "bg-red-100 text-red-800 border-red-200" : "bg-yellow-100 text-yellow-800 border-yellow-200"}>
                            {c.severity}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
