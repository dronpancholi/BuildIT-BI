"""
LineageNode and LineageEdge entities for the Data Lineage System.
Full traceability from source records to computed values.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from app.domain.entities.base import TenantAwareEntity


class LineageNodeType(str, Enum):
    SOURCE_TABLE = "source_table"
    SOURCE_COLUMN = "source_column"
    TRANSFORM = "transform"
    METRIC = "metric"
    OUTPUT = "output"


class LineageEdgeType(str, Enum):
    DIRECT = "direct"  # Direct dependency (A reads from B)
    INDIRECT = "indirect"  # Transitive dependency (A reads from B via C)
    DERIVED = "derived"  # A is mathematically derived from B


@dataclass(kw_only=True)
class LineageNode(TenantAwareEntity):
    """
    A node in the lineage graph.
    Represents an entity that participates in data flow.
    """
    # Node identity
    node_type: LineageNodeType = LineageNodeType.SOURCE_TABLE
    name: str = ""
    qualified_name: str = ""  # Fully qualified: "public.revenues.amount"
    
    # Node details
    node_subtype: Optional[str] = None  # "postgresql_table", "duckdb_view", "kpi"
    
    # For SOURCE nodes
    source_system: Optional[str] = None  # "billing_system", "erp", "manual_import"
    source_id: Optional[str] = None  # External identifier
    
    # For TRANSFORM nodes
    transform_type: Optional[str] = None  # "filter", "aggregate", "join", "calculate"
    transform_logic: Optional[str] = None  # SQL or Python code
    transform_order: Optional[int] = None  # Order in a multi-step transform
    
    # For METRIC nodes
    metric_id: Optional[uuid.UUID] = None  # FK to MetricDefinition
    computation_context: Optional[Dict[str, Any]] = None
    
    # Graph metadata
    description: Optional[str] = None
    
    def is_source(self) -> bool:
        """Check if this is a source node."""
        return self.node_type in [LineageNodeType.SOURCE_TABLE, LineageNodeType.SOURCE_COLUMN]
    
    def is_transform(self) -> bool:
        """Check if this is a transform node."""
        return self.node_type == LineageNodeType.TRANSFORM
    
    def is_metric(self) -> bool:
        """Check if this is a metric node."""
        return self.node_type == LineageNodeType.METRIC


@dataclass(kw_only=True)
class LineageEdge(TenantAwareEntity):
    """
    A directed edge in the lineage graph: A -> B means B depends on A.
    """
    # Edge identity
    source_node_id: uuid.UUID  # The upstream node
    target_node_id: uuid.UUID  # The downstream node
    
    # Edge metadata
    edge_type: LineageEdgeType = LineageEdgeType.DIRECT
    dependency_type: Optional[str] = None  # "reads_from", "aggregates", "computes_from"
    
    # Field-level lineage (for column-level tracing)
    source_field: Optional[str] = None  # e.g., "revenue.amount"
    target_field: Optional[str] = None  # e.g., "net_revenue.value"
    
    # Propagation
    is_active: bool = True
    deprecated_at: Optional[datetime] = None
    
    def deactivate(self) -> None:
        """Mark edge as no longer active."""
        self.is_active = False
        self.deprecated_at = datetime.utcnow()


@dataclass(kw_only=True)
class LineageComputationRecord(TenantAwareEntity):
    """
    Records a specific computation event and its lineage.
    Immutable — once written, never modified.
    """
    # Computation context
    computation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    metric_id: Optional[uuid.UUID] = None
    computed_value_id: Optional[uuid.UUID] = None
    
    # Time
    computed_at: datetime = field(default_factory=datetime.utcnow)
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    
    # Execution details
    executed_by: Optional[uuid.UUID] = None
    execution_type: str = "scheduled"  # "scheduled", "on_demand", "import"
    duration_ms: int = 0
    
    # Lineage snapshot (JSON) — captures lineage at computation time
    lineage_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    # Source records affected
    source_record_count: int = 0
    source_records_sample: List[Dict[str, Any]] = field(default_factory=list)
    
    # Transformation steps (JSON)
    transformation_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Result
    input_record_count: int = 0
    output_record_count: int = 0
    null_values_excluded: int = 0
    duplicates_removed: int = 0


@dataclass(kw_only=True)
class LineageGraph:
    """
    A complete lineage graph for visualization and analysis.
    """
    nodes: List[LineageNode] = field(default_factory=list)
    edges: List[LineageEdge] = field(default_factory=list)
    
    def get_node_by_id(self, node_id: uuid.UUID) -> Optional[LineageNode]:
        """Get a node by its ID."""
        for node in self.nodes:
            if node.entity_id == node_id:
                return node
        return None
    
    def get_upstream_nodes(self, node_id: uuid.UUID) -> List[LineageNode]:
        """Get all nodes upstream of a given node."""
        upstream = []
        visited = set()
        
        def traverse(current_id: uuid.UUID):
            if current_id in visited:
                return
            visited.add(current_id)
            
            for edge in self.edges:
                if edge.target_node_id == current_id and edge.is_active:
                    source_node = self.get_node_by_id(edge.source_node_id)
                    if source_node:
                        upstream.append(source_node)
                        traverse(edge.source_node_id)
        
        traverse(node_id)
        return upstream
    
    def get_downstream_nodes(self, node_id: uuid.UUID) -> List[LineageNode]:
        """Get all nodes downstream of a given node."""
        downstream = []
        visited = set()
        
        def traverse(current_id: uuid.UUID):
            if current_id in visited:
                return
            visited.add(current_id)
            
            for edge in self.edges:
                if edge.source_node_id == current_id and edge.is_active:
                    target_node = self.get_node_by_id(edge.target_node_id)
                    if target_node:
                        downstream.append(target_node)
                        traverse(edge.target_node_id)
        
        traverse(node_id)
        return downstream
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary for serialization."""
        return {
            "nodes": [
                {
                    "id": str(n.entity_id),
                    "type": n.node_type.value,
                    "name": n.name,
                    "qualified_name": n.qualified_name
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source": str(e.source_node_id),
                    "target": str(e.target_node_id),
                    "type": e.edge_type.value
                }
                for e in self.edges
            ]
        }
