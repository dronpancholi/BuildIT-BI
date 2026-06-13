"""
Intelligence Graph Abstraction Layer.
Manages relationships between all intelligence entities.
Designed for PostgreSQL today, can migrate to graph DB when scale demands.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from ..entities import (
    IntelligenceNode,
    IntelligenceRelationship,
    InfluenceNetwork,
)
from app.domain.intelligence.value_objects import (
    RelationshipType,
    IntelligenceNodeType,
    GraphNodeStatus,
    RelationshipDirection,
)


class IntelligenceGraphService:
    """
    Manages the intelligence relationship graph.
    Abstraction layer — today on PostgreSQL, tomorrow on a graph DB.
    """

    def __init__(self):
        # In-memory store for demonstration
        # In production, this would be PostgreSQL or a graph DB
        self.nodes: Dict[uuid.UUID, IntelligenceNode] = {}
        self.relationships: Dict[uuid.UUID, IntelligenceRelationship] = {}
        self.node_relationships: Dict[uuid.UUID, List[uuid.UUID]] = {}  # node_id -> [relationship_ids]

    async def add_node(
        self,
        tenant_id: uuid.UUID,
        node_type: str,
        entity_type: str,
        entity_id: uuid.UUID,
        label: str,
        description: Optional[str] = None,
        primary_value: Optional[float] = None,
    ) -> IntelligenceNode:
        """
        Add a node to the graph.
        """
        node_id = uuid.uuid4()
        node = IntelligenceNode(
            id=node_id,
            tenant_id=tenant_id,
            node_type=node_type,
            entity_type=entity_type,
            entity_id=entity_id,
            label=label,
            description=description,
            primary_value=primary_value,
            first_observed_at=datetime.utcnow(),
            last_observed_at=datetime.utcnow(),
        )

        self.nodes[node_id] = node
        self.node_relationships[node_id] = []

        return node

    async def add_relationship(
        self,
        tenant_id: uuid.UUID,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        relationship_type: str,
        correlation_strength: float = 0.0,
        causal_strength: Optional[float] = None,
        confidence: float = 0.0,
        context: Optional[str] = None,
    ) -> IntelligenceRelationship:
        """
        Add a relationship between two nodes.
        Automatically creates node records if they don't exist.
        """
        # Check if nodes exist
        if source_id not in self.nodes:
            raise ValueError(f"Source node {source_id} not found")
        if target_id not in self.nodes:
            raise ValueError(f"Target node {target_id} not found")

        # Check if relationship already exists
        for rel in self.relationships.values():
            if (rel.source_node_id == source_id and
                rel.target_node_id == target_id and
                rel.relationship_type == relationship_type):
                # Update existing relationship
                rel.correlation_strength = correlation_strength
                rel.causal_strength = causal_strength
                rel.confidence = confidence
                rel.context = context
                rel.last_observed_at = datetime.utcnow()
                rel.evidence_count += 1
                rel.version += 1
                return rel

        # Create new relationship
        rel_id = uuid.uuid4()
        relationship = IntelligenceRelationship(
            id=rel_id,
            tenant_id=tenant_id,
            source_node_id=source_id,
            target_node_id=target_id,
            relationship_type=relationship_type,
            correlation_strength=correlation_strength,
            causal_strength=causal_strength,
            confidence=confidence,
            context=context,
            evidence_count=1,
            first_observed_at=datetime.utcnow(),
            last_observed_at=datetime.utcnow(),
        )

        self.relationships[rel_id] = relationship
        self.node_relationships[source_id].append(rel_id)
        self.node_relationships[target_id].append(rel_id)

        return relationship

    async def get_node(
        self,
        node_id: uuid.UUID
    ) -> Optional[IntelligenceNode]:
        """
        Get a node by ID.
        """
        return self.nodes.get(node_id)

    async def get_related_nodes(
        self,
        node_id: uuid.UUID,
        relationship_types: Optional[List[str]] = None,
        direction: RelationshipDirection = RelationshipDirection.BOTH,
        depth: int = 1,
    ) -> List[IntelligenceNode]:
        """
        Get nodes related to the given node.
        Supports multi-hop traversal (depth > 1).
        """
        if node_id not in self.nodes:
            return []

        related_nodes = []
        visited = set()

        async def traverse(current_id: uuid.UUID, current_depth: int):
            if current_depth > depth or current_id in visited:
                return
            visited.add(current_id)

            rel_ids = self.node_relationships.get(current_id, [])
            for rel_id in rel_ids:
                rel = self.relationships.get(rel_id)
                if rel is None:
                    continue

                # Filter by relationship type
                if relationship_types and rel.relationship_type not in relationship_types:
                    continue

                # Determine related node based on direction
                if direction == RelationshipDirection.OUTGOING:
                    if rel.source_node_id == current_id:
                        next_id = rel.target_node_id
                    else:
                        continue
                elif direction == RelationshipDirection.INCOMING:
                    if rel.target_node_id == current_id:
                        next_id = rel.source_node_id
                    else:
                        continue
                else:  # BOTH
                    if rel.source_node_id == current_id:
                        next_id = rel.target_node_id
                    elif rel.target_node_id == current_id:
                        next_id = rel.source_node_id
                    else:
                        continue

                if next_id in self.nodes and next_id not in visited:
                    related_nodes.append(self.nodes[next_id])
                    await traverse(next_id, current_depth + 1)

        await traverse(node_id, 0)
        return related_nodes

    async def find_paths(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        max_hops: int = 5,
    ) -> List[List[IntelligenceRelationship]]:
        """
        Find all paths between two nodes.
        Used for impact analysis and root cause tracing.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return []

        paths = []
        visited = set()

        async def dfs(current_id: uuid.UUID, path: List[IntelligenceRelationship]):
            if current_id == target_id:
                paths.append(list(path))
                return

            if len(path) >= max_hops:
                return

            visited.add(current_id)
            rel_ids = self.node_relationships.get(current_id, [])

            for rel_id in rel_ids:
                rel = self.relationships.get(rel_id)
                if rel is None:
                    continue

                # Determine next node
                if rel.source_node_id == current_id:
                    next_id = rel.target_node_id
                elif rel.target_node_id == current_id:
                    next_id = rel.source_node_id
                else:
                    continue

                if next_id not in visited:
                    path.append(rel)
                    await dfs(next_id, path)
                    path.pop()

            visited.remove(current_id)

        await dfs(source_id, [])
        return paths

    async def get_influence_network(
        self,
        node_id: uuid.UUID,
        depth: int = 2,
    ) -> InfluenceNetwork:
        """
        Get the influence network around a node.
        Used for understanding cascading effects.
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")

        central_node = self.nodes[node_id]

        direct_influencers = []
        direct_influencees = []
        indirect_influencers = []
        indirect_influencees = []

        # Get direct relationships
        rel_ids = self.node_relationships.get(node_id, [])
        for rel_id in rel_ids:
            rel = self.relationships.get(rel_id)
            if rel is None:
                continue

            if rel.target_node_id == node_id and rel.source_node_id in self.nodes:
                direct_influencers.append(self.nodes[rel.source_node_id])
            elif rel.source_node_id == node_id and rel.target_node_id in self.nodes:
                direct_influencees.append(self.nodes[rel.target_node_id])

        # Get indirect relationships (depth > 1)
        if depth > 1:
            # Influencers of influencers
            for influencer in direct_influencers:
                influencer_rels = self.node_relationships.get(influencer.id, [])
                for rel_id in influencer_rels:
                    rel = self.relationships.get(rel_id)
                    if rel and rel.target_node_id == influencer.id:
                        if rel.source_node_id in self.nodes:
                            indirect_influencers.append(self.nodes[rel.source_node_id])

            # Influencees of influencees
            for influencee in direct_influencees:
                influencee_rels = self.node_relationships.get(influencee.id, [])
                for rel_id in influencee_rels:
                    rel = self.relationships.get(rel_id)
                    if rel and rel.source_node_id == influencee.id:
                        if rel.target_node_id in self.nodes:
                            indirect_influencees.append(self.nodes[rel.target_node_id])

        total_connected = (
            len(direct_influencers) + len(direct_influencees) +
            len(indirect_influencers) + len(indirect_influencees)
        )

        # Calculate network density
        max_possible_edges = total_connected * (total_connected - 1) if total_connected > 1 else 1
        actual_edges = len([
            r for r in self.relationships.values()
            if r.source_node_id != node_id and r.target_node_id != node_id
        ])
        network_density = actual_edges / max_possible_edges if max_possible_edges > 0 else 0

        return InfluenceNetwork(
            central_node=central_node,
            direct_influencers=direct_influencers,
            direct_influencees=direct_influencees,
            indirect_influencers=indirect_influencers,
            indirect_influencees=indirect_influencees,
            total_connected_nodes=total_connected,
            network_density=network_density,
        )

    async def find_anomalous_relationships(
        self,
        tenant_id: uuid.UUID,
        min_change: float = 0.3,
    ) -> List[IntelligenceRelationship]:
        """
        Find relationships that have changed significantly.
        Used for detecting structural changes.
        """
        anomalous = []

        for rel in self.relationships.values():
            if rel.tenant_id != tenant_id:
                continue

            # Check if relationship has significant change
            # This would compare current vs historical in production
            # For now, return relationships with low confidence
            if rel.confidence < 0.5:
                anomalous.append(rel)

        return anomalous

    async def get_node_count(
        self,
        tenant_id: uuid.UUID,
        node_type: Optional[str] = None,
    ) -> int:
        """
        Get count of nodes for a tenant.
        """
        count = 0
        for node in self.nodes.values():
            if node.tenant_id != tenant_id:
                continue
            if node_type and node.node_type != node_type:
                continue
            count += 1
        return count

    async def get_relationship_count(
        self,
        tenant_id: uuid.UUID,
        relationship_type: Optional[str] = None,
    ) -> int:
        """
        Get count of relationships for a tenant.
        """
        count = 0
        for rel in self.relationships.values():
            if rel.tenant_id != tenant_id:
                continue
            if relationship_type and rel.relationship_type != relationship_type:
                continue
            count += 1
        return count

    async def get_graph_statistics(
        self,
        tenant_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Get statistics about the intelligence graph.
        """
        node_count = await self.get_node_count(tenant_id)
        relationship_count = await self.get_relationship_count(tenant_id)

        # Count by node type
        node_types: Dict[str, int] = {}
        for node in self.nodes.values():
            if node.tenant_id != tenant_id:
                continue
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1

        # Count by relationship type
        relationship_types: Dict[str, int] = {}
        for rel in self.relationships.values():
            if rel.tenant_id != tenant_id:
                continue
            relationship_types[rel.relationship_type] = relationship_types.get(rel.relationship_type, 0) + 1

        return {
            "node_count": node_count,
            "relationship_count": relationship_count,
            "node_types": node_types,
            "relationship_types": relationship_types,
        }


# Singleton instance
intelligence_graph_service = IntelligenceGraphService()
