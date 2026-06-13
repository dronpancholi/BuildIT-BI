"""
SQLAlchemy repository for the Vector Memory domain.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models import MemoryRecordModel


class MemoryRecordRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        tenant_id: str,
        memory_type: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "",
        confidence: float = 1.0,
    ) -> MemoryRecordModel:
        record = MemoryRecordModel(
            tenant_id=tenant_id,
            memory_type=memory_type,
            content=content,
            embedding=embedding,
            metadata_=metadata or {},
            source=source,
            confidence=confidence,
            access_count=0,
            status="ACTIVE",
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_id(self, record_id: uuid.UUID) -> Optional[MemoryRecordModel]:
        result = await self._session.execute(
            select(MemoryRecordModel).where(MemoryRecordModel.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_tenant(
        self, record_id: uuid.UUID, tenant_id: str
    ) -> Optional[MemoryRecordModel]:
        result = await self._session.execute(
            select(MemoryRecordModel).where(
                MemoryRecordModel.id == record_id,
                MemoryRecordModel.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def update(
        self, record_id: uuid.UUID, updates: Dict[str, Any]
    ) -> Optional[MemoryRecordModel]:
        record = await self.get_by_id(record_id)
        if record is None:
            return None
        field_map = {
            "content": "content",
            "metadata": "metadata_",
            "confidence": "confidence",
            "source": "source",
            "memory_type": "memory_type",
            "status": "status",
            "access_count": "access_count",
            "embedding": "embedding",
            "expires_at": "expires_at",
        }
        for key, value in updates.items():
            col_name = field_map.get(key, key)
            if hasattr(record, col_name):
                setattr(record, col_name, value)
        record.last_accessed = datetime.utcnow()
        await self._session.flush()
        return record

    async def list_by_tenant(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        memory_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[MemoryRecordModel]:
        query = select(MemoryRecordModel).where(
            MemoryRecordModel.tenant_id == tenant_id
        )
        if status:
            query = query.where(MemoryRecordModel.status == status)
        if memory_type:
            query = query.where(MemoryRecordModel.memory_type == memory_type)
        query = query.order_by(MemoryRecordModel.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_all_active(self, tenant_id: str) -> List[MemoryRecordModel]:
        result = await self._session.execute(
            select(MemoryRecordModel).where(
                MemoryRecordModel.tenant_id == tenant_id,
                MemoryRecordModel.status != "ARCHIVED",
            )
        )
        return list(result.scalars().all())

    async def count(self, tenant_id: str) -> int:
        q = await self._session.execute(
            select(func.count()).select_from(MemoryRecordModel).where(
                MemoryRecordModel.tenant_id == tenant_id
            )
        )
        return q.scalar() or 0

    async def count_by_status(self, tenant_id: str) -> Dict[str, int]:
        q = await self._session.execute(
            select(
                MemoryRecordModel.status,
                func.count(MemoryRecordModel.id),
            ).where(
                MemoryRecordModel.tenant_id == tenant_id
            ).group_by(MemoryRecordModel.status)
        )
        return {row[0]: row[1] for row in q.all()}

    async def count_by_type(self, tenant_id: str) -> Dict[str, int]:
        q = await self._session.execute(
            select(
                MemoryRecordModel.memory_type,
                func.count(MemoryRecordModel.id),
            ).where(
                MemoryRecordModel.tenant_id == tenant_id
            ).group_by(MemoryRecordModel.memory_type)
        )
        return {row[0]: row[1] for row in q.all()}

    async def avg_confidence(self, tenant_id: str) -> float:
        q = await self._session.execute(
            select(func.avg(MemoryRecordModel.confidence)).where(
                MemoryRecordModel.tenant_id == tenant_id
            )
        )
        return q.scalar() or 0.0

    async def avg_access_count(self, tenant_id: str) -> float:
        q = await self._session.execute(
            select(func.avg(MemoryRecordModel.access_count)).where(
                MemoryRecordModel.tenant_id == tenant_id
            )
        )
        return q.scalar() or 0.0
