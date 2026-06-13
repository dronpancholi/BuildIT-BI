"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { intelligenceAPI } from "@/lib/api/client";

interface GraphNode {
  id: string;
  node_type: string;
  entity_type: string;
  entity_id: string;
  label: string;
  description: string;
  primary_value: number;
  importance_score: number;
  influence_score: number;
  status: string;
}

interface GraphRelationship {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relationship_type: string;
  correlation_strength: number;
  confidence: number;
}

const NODE_COLORS: Record<string, string> = {
  insight: "bg-blue-100 border-blue-400 text-blue-800",
  root_cause: "bg-red-100 border-red-400 text-red-800",
  anomaly: "bg-orange-100 border-orange-400 text-orange-800",
  opportunity: "bg-green-100 border-green-400 text-green-800",
  recommendation: "bg-purple-100 border-purple-400 text-purple-800",
  metric: "bg-gray-100 border-gray-400 text-gray-800",
};

const REL_COLORS: Record<string, string> = {
  caused_by: "stroke-red-400",
  correlated_with: "stroke-blue-400",
  leads_to: "stroke-green-400",
  informs: "stroke-purple-400",
  affects: "stroke-orange-400",
};

export function IntelligenceGraphExplorer() {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [relationships, setRelationships] = useState<GraphRelationship[]>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [neighbors, setNeighbors] = useState<GraphNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [nodeTypeFilter, setNodeTypeFilter] = useState<string>("");

  useEffect(() => {
    fetchGraph();
  }, [nodeTypeFilter]);

  async function fetchGraph() {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { limit: 100 };
      if (nodeTypeFilter) params.node_type = nodeTypeFilter;
      const [nodesRes, relsRes] = await Promise.all([
        intelligenceAPI.getGraphNodes(params),
        intelligenceAPI.listRelationships({ limit: 200 }),
      ]);
      setNodes(nodesRes.data?.data || []);
      setRelationships(relsRes.data?.data || []);
    } catch {
      setNodes([]);
      setRelationships([]);
    } finally {
      setLoading(false);
    }
  }

  const handleNodeClick = useCallback(async (node: GraphNode) => {
    setSelectedNode(node);
    try {
      const res = await intelligenceAPI.getGraphNeighbors(node.id);
      setNeighbors(res.data?.data || []);
    } catch {
      setNeighbors([]);
    }
  }, []);

  const nodeMap = React.useMemo(() => {
    const m: Record<string, GraphNode> = {};
    nodes.forEach((n) => (m[n.id] = n));
    return m;
  }, [nodes]);

  const getEdges = (nodeId: string) =>
    relationships.filter(
      (r) => r.source_node_id === nodeId || r.target_node_id === nodeId
    );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <select
          value={nodeTypeFilter}
          onChange={(e) => setNodeTypeFilter(e.target.value)}
          className="border rounded-md px-3 py-2 text-sm"
        >
          <option value="">All Types</option>
          <option value="insight">Insights</option>
          <option value="root_cause">Root Causes</option>
          <option value="anomaly">Anomalies</option>
          <option value="opportunity">Opportunities</option>
          <option value="recommendation">Recommendations</option>
          <option value="metric">Metrics</option>
        </select>
        <div className="text-sm text-muted-foreground">
          {nodes.length} nodes, {relationships.length} relationships
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Intelligence Graph</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-12 text-muted-foreground">Loading graph...</div>
              ) : nodes.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  No graph nodes found. Run intelligence discovery to populate the graph.
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-2">
                    {nodes.map((node) => {
                      const edges = getEdges(node.id);
                      return (
                        <button
                          key={node.id}
                          onClick={() => handleNodeClick(node)}
                          className={`border-2 rounded-lg px-3 py-2 text-left transition-all hover:shadow-md ${
                            NODE_COLORS[node.node_type] || "bg-gray-50 border-gray-300"
                          } ${selectedNode?.id === node.id ? "ring-2 ring-primary shadow-md" : ""}`}
                        >
                          <div className="text-xs font-medium capitalize">{node.node_type?.replace(/_/g, " ")}</div>
                          <div className="text-sm font-semibold line-clamp-1">{node.label || node.entity_type}</div>
                          <div className="text-xs opacity-70">{edges.length} connections</div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          {selectedNode && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Selected Node</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <Badge className={NODE_COLORS[selectedNode.node_type] || ""}>
                    {selectedNode.node_type?.replace(/_/g, " ")}
                  </Badge>
                </div>
                <h3 className="font-semibold">{selectedNode.label || selectedNode.entity_type}</h3>
                {selectedNode.description && (
                  <p className="text-sm text-muted-foreground">{selectedNode.description}</p>
                )}
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Importance:</span>{" "}
                    <span className="font-medium">{(selectedNode.importance_score * 100).toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Influence:</span>{" "}
                    <span className="font-medium">{(selectedNode.influence_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {neighbors.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Connected Nodes ({neighbors.length})</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {neighbors.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => handleNodeClick(n)}
                    className={`w-full border rounded-lg px-3 py-2 text-left hover:shadow-sm transition-shadow ${
                      NODE_COLORS[n.node_type] || "bg-gray-50 border-gray-300"
                    }`}
                  >
                    <div className="text-xs font-medium capitalize">{n.node_type?.replace(/_/g, " ")}</div>
                    <div className="text-sm font-medium line-clamp-1">{n.label || n.entity_type}</div>
                  </button>
                ))}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Legend</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {Object.entries(NODE_COLORS).map(([type, colors]) => (
                <div key={type} className="flex items-center gap-2 text-sm">
                  <div className={`w-4 h-4 rounded border-2 ${colors}`} />
                  <span className="capitalize">{type.replace(/_/g, " ")}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
