"""
SQLAlchemy repositories for the Institutional Knowledge domain.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models import KnowledgeNodeModel, KnowledgeEdgeModel


class KnowledgeNodeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        tenant_id: str,
        node_type: str,
        name: str,
        description: str = "",
        properties: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeNodeModel:
        node = KnowledgeNodeModel(
            tenant_id=tenant_id,
            node_type=node_type,
            name=name,
            description=description,
            properties=properties or {},
        )
        self._session.add(node)
        await self._session.flush()
        return node

    async def get_by_id(self, node_id: uuid.UUID) -> Optional[KnowledgeNodeModel]:
        result = await self._session.execute(
            select(KnowledgeNodeModel).where(KnowledgeNodeModel.id == node_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_tenant(
        self, node_id: uuid.UUID, tenant_id: str
    ) -> Optional[KnowledgeNodeModel]:
        result = await self._session.execute(
            select(KnowledgeNodeModel).where(
                KnowledgeNodeModel.id == node_id,
                KnowledgeNodeModel.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def update(
        self, node_id: uuid.UUID, updates: Dict[str, Any]
    ) -> Optional[KnowledgeNodeModel]:
        node = await self.get_by_id(node_id)
        if node is None:
            return None
        for key, value in updates.items():
            if hasattr(node, key):
                setattr(node, key, value)
        node.updated_at = datetime.utcnow()
        await self._session.flush()
        return node

    async def list_by_tenant(
        self, tenant_id: str, offset: int = 0, limit: int = 100
    ) -> List[KnowledgeNodeModel]:
        q = await self._session.execute(
            select(KnowledgeNodeModel)
            .where(KnowledgeNodeModel.tenant_id == tenant_id)
            .order_by(KnowledgeNodeModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(q.scalars().all())

    async def list_by_type(
        self, tenant_id: str, node_type: str
    ) -> List[KnowledgeNodeModel]:
        q = await self._session.execute(
            select(KnowledgeNodeModel).where(
                KnowledgeNodeModel.tenant_id == tenant_id,
                KnowledgeNodeModel.node_type == node_type,
            )
        )
        return list(q.scalars().all())

    async def count(self, tenant_id: str) -> int:
        q = await self._session.execute(
            select(func.count()).select_from(KnowledgeNodeModel).where(
                KnowledgeNodeModel.tenant_id == tenant_id
            )
        )
        return q.scalar() or 0

    async def count_by_type(self, tenant_id: str) -> Dict[str, int]:
        q = await self._session.execute(
            select(
                KnowledgeNodeModel.node_type,
                func.count(KnowledgeNodeModel.id),
            ).where(
                KnowledgeNodeModel.tenant_id == tenant_id
            ).group_by(KnowledgeNodeModel.node_type)
        )
        return {row[0]: row[1] for row in q.all()}

    async def exists(self, node_id: uuid.UUID) -> bool:
        q = await self._session.execute(
            select(func.count()).select_from(KnowledgeNodeModel).where(
                KnowledgeNodeModel.id == node_id
            )
        )
        return (q.scalar() or 0) > 0


class KnowledgeEdgeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        tenant_id: str,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        relation_type: str,
        weight: float = 1.0,
        confidence: float = 1.0,
        evidence: Optional[List[Dict]] = None,
    ) -> KnowledgeEdgeModel:
        edge = KnowledgeEdgeModel(
            tenant_id=tenant_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            confidence=confidence,
            evidence=evidence or [],
            properties={},
        )
        self._session.add(edge)
        await self._session.flush()
        return edge

    async def get_by_id(self, edge_id: uuid.UUID) -> Optional[KnowledgeEdgeModel]:
        result = await self._session.execute(
            select(KnowledgeEdgeModel).where(KnowledgeEdgeModel.id == edge_id)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self, tenant_id: str, offset: int = 0, limit: int = 100
    ) -> List[KnowledgeEdgeModel]:
        q = await self._session.execute(
            select(KnowledgeEdgeModel)
            .where(KnowledgeEdgeModel.tenant_id == tenant_id)
            .order_by(KnowledgeEdgeModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(q.scalars().all())

    async def list_from_node(
        self, tenant_id: str, source_id: uuid.UUID
    ) -> List[KnowledgeEdgeModel]:
        q = await self._session.execute(
            select(KnowledgeEdgeModel).where(
                KnowledgeEdgeModel.tenant_id == tenant_id,
                KnowledgeEdgeModel.source_id == source_id,
            )
        )
        return list(q.scalars().all())

    async def list_to_node(
        self, tenant_id: str, target_id: uuid.UUID
    ) -> List[KnowledgeEdgeModel]:
        q = await self._session.execute(
            select(KnowledgeEdgeModel).where(
                KnowledgeEdgeModel.tenant_id == tenant_id,
                KnowledgeEdgeModel.target_id == target_id,
            )
        )
        return list(q.scalars().all())

    async def list_for_node(
        self, tenant_id: str, node_id: uuid.UUID
    ) -> List[KnowledgeEdgeModel]:
        q = await self._session.execute(
            select(KnowledgeEdgeModel).where(
                KnowledgeEdgeModel.tenant_id == tenant_id,
                or_(
                    KnowledgeEdgeModel.source_id == node_id,
                    KnowledgeEdgeModel.target_id == node_id,
                ),
            )
        )
        return list(q.scalars().all())

    async def list_by_relation_type(
        self, tenant_id: str, relation_type: str
    ) -> List[KnowledgeEdgeModel]:
        q = await self._session.execute(
            select(KnowledgeEdgeModel).where(
                KnowledgeEdgeModel.tenant_id == tenant_id,
                KnowledgeEdgeModel.relation_type == relation_type,
            )
        )
        return list(q.scalars().all())

    async def count(self, tenant_id: str) -> int:
        q = await self._session.execute(
            select(func.count()).select_from(KnowledgeEdgeModel).where(
                KnowledgeEdgeModel.tenant_id == tenant_id
            )
        )
        return q.scalar() or 0

    async def count_by_type(self, tenant_id: str) -> Dict[str, int]:
        q = await self._session.execute(
            select(
                KnowledgeEdgeModel.relation_type,
                func.count(KnowledgeEdgeModel.id),
            ).where(
                KnowledgeEdgeModel.tenant_id == tenant_id
            ).group_by(KnowledgeEdgeModel.relation_type)
        )
        return {row[0]: row[1] for row in q.all()}

    async def get_by_nodes(
        self,
        tenant_id: str,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
    ) -> Optional[KnowledgeEdgeModel]:
        q = await self._session.execute(
            select(KnowledgeEdgeModel).where(
                KnowledgeEdgeModel.tenant_id == tenant_id,
                KnowledgeEdgeModel.source_id == source_id,
                KnowledgeEdgeModel.target_id == target_id,
            )
        )
        return q.scalar_one_or_none()
