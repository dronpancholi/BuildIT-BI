"""
Async SQLAlchemy repository classes for all Phase 5 domains.
Healthcare Financial Intelligence Platform — persistence backbone.
"""
from uuid import UUID
from typing import Optional, List, Any, Dict
from datetime import datetime

from sqlalchemy import select, update, delete, func, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.infrastructure.persistence.models import (
    CFOProfileModel, CFOQuestionModel, CFOBriefingModel, CFOWorkspaceModel,
    CFOAlertConfigModel, CFOAlertModel, StrategicScenarioModel, StrategicDriverTreeModel,
    StrategicWhatIfModel, ForecastModelModel, ForecastResultModel, ForecastMonitoringAlertModel,
    MemoryRecordModel, KnowledgeNodeModel, KnowledgeEdgeModel,
    CurrencyEntityConfigModel, FXRateSnapshotModel, ExecutiveDecisionModel,
    CopilotConversationModel, CausalGraphModel, CausalEstimateModel,
    NLQueryLogModel, ExportJobModel, CollaborationCommentModel,
    SavedDashboardModel, VisualizationSpecModel, SemanticMetricV2Model, SemanticDimensionV2Model,
    MaterializedViewCacheModel,
)


def _to_dict(model) -> dict:
    """Convert SQLAlchemy model instance to dict."""
    return {c.name: getattr(model, c.name) for c in model.__table__.columns}


# ═══════════════════════════════════════════════════════════════════════════════
# CFO COPILOT DOMAIN
# ═══════════════════════════════════════════════════════════════════════════════


class CFOProfileRepository:
    """Repository for CFO profiles."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = CFOProfileModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(CFOProfileModel).where(CFOProfileModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(CFOProfileModel).where(CFOProfileModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(CFOProfileModel, key):
                stmt = stmt.where(getattr(CFOProfileModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(CFOProfileModel)
            .where(CFOProfileModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(CFOProfileModel).where(CFOProfileModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class CFOQuestionRepository:
    """Repository for CFO questions / copilot queries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = CFOQuestionModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(CFOQuestionModel).where(CFOQuestionModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(CFOQuestionModel).where(CFOQuestionModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(CFOQuestionModel, key):
                stmt = stmt.where(getattr(CFOQuestionModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(CFOQuestionModel)
            .where(CFOQuestionModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(CFOQuestionModel).where(CFOQuestionModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class CFOBriefingRepository:
    """Repository for CFO briefings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = CFOBriefingModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(CFOBriefingModel).where(CFOBriefingModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(CFOBriefingModel).where(CFOBriefingModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(CFOBriefingModel, key):
                stmt = stmt.where(getattr(CFOBriefingModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(CFOBriefingModel)
            .where(CFOBriefingModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(CFOBriefingModel).where(CFOBriefingModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class CFOWorkspaceRepository:
    """Repository for CFO workspaces."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = CFOWorkspaceModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(CFOWorkspaceModel).where(CFOWorkspaceModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(CFOWorkspaceModel).where(CFOWorkspaceModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(CFOWorkspaceModel, key):
                stmt = stmt.where(getattr(CFOWorkspaceModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(CFOWorkspaceModel)
            .where(CFOWorkspaceModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(CFOWorkspaceModel).where(CFOWorkspaceModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class CFOAlertRepository:
    """Repository for CFO alert configs and alerts."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Alert Config CRUD ──

    async def create_config(self, **kwargs) -> dict:
        model = CFOAlertConfigModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get_config(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(CFOAlertConfigModel).where(CFOAlertConfigModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list_configs(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(CFOAlertConfigModel).where(CFOAlertConfigModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(CFOAlertConfigModel, key):
                stmt = stmt.where(getattr(CFOAlertConfigModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update_config(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(CFOAlertConfigModel)
            .where(CFOAlertConfigModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get_config(id)

    async def delete_config(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(CFOAlertConfigModel).where(CFOAlertConfigModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    # ── Alert CRUD ──

    async def create(self, **kwargs) -> dict:
        model = CFOAlertModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(CFOAlertModel).where(CFOAlertModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(CFOAlertModel).where(CFOAlertModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(CFOAlertModel, key):
                stmt = stmt.where(getattr(CFOAlertModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(CFOAlertModel)
            .where(CFOAlertModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(CFOAlertModel).where(CFOAlertModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGIC PLANNING DOMAIN
# ═══════════════════════════════════════════════════════════════════════════════


class StrategicScenarioRepository:
    """Repository for strategic planning scenarios."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = StrategicScenarioModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(StrategicScenarioModel).where(StrategicScenarioModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(StrategicScenarioModel).where(StrategicScenarioModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(StrategicScenarioModel, key):
                stmt = stmt.where(getattr(StrategicScenarioModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(StrategicScenarioModel)
            .where(StrategicScenarioModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(StrategicScenarioModel).where(StrategicScenarioModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class StrategicDriverTreeRepository:
    """Repository for strategic driver trees."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = StrategicDriverTreeModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(StrategicDriverTreeModel).where(StrategicDriverTreeModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(StrategicDriverTreeModel).where(StrategicDriverTreeModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(StrategicDriverTreeModel, key):
                stmt = stmt.where(getattr(StrategicDriverTreeModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(StrategicDriverTreeModel)
            .where(StrategicDriverTreeModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(StrategicDriverTreeModel).where(StrategicDriverTreeModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class StrategicWhatIfRepository:
    """Repository for strategic what-if analyses."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = StrategicWhatIfModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(StrategicWhatIfModel).where(StrategicWhatIfModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(StrategicWhatIfModel).where(StrategicWhatIfModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(StrategicWhatIfModel, key):
                stmt = stmt.where(getattr(StrategicWhatIfModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(StrategicWhatIfModel)
            .where(StrategicWhatIfModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(StrategicWhatIfModel).where(StrategicWhatIfModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# FORECASTING DOMAIN
# ═══════════════════════════════════════════════════════════════════════════════


class ForecastModelRepository:
    """Repository for forecast model definitions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = ForecastModelModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(ForecastModelModel).where(ForecastModelModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(ForecastModelModel).where(ForecastModelModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(ForecastModelModel, key):
                stmt = stmt.where(getattr(ForecastModelModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(ForecastModelModel)
            .where(ForecastModelModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(ForecastModelModel).where(ForecastModelModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class ForecastResultRepository:
    """Repository for forecast results."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = ForecastResultModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(ForecastResultModel).where(ForecastResultModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(ForecastResultModel).where(ForecastResultModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(ForecastResultModel, key):
                stmt = stmt.where(getattr(ForecastResultModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(ForecastResultModel)
            .where(ForecastResultModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(ForecastResultModel).where(ForecastResultModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class ForecastAlertRepository:
    """Repository for forecast monitoring alerts."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = ForecastMonitoringAlertModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(ForecastMonitoringAlertModel).where(ForecastMonitoringAlertModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(ForecastMonitoringAlertModel).where(
            ForecastMonitoringAlertModel.tenant_id == tenant_id
        )
        for key, value in filters.items():
            if hasattr(ForecastMonitoringAlertModel, key):
                stmt = stmt.where(getattr(ForecastMonitoringAlertModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(ForecastMonitoringAlertModel)
            .where(ForecastMonitoringAlertModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(ForecastMonitoringAlertModel).where(ForecastMonitoringAlertModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY & KNOWLEDGE GRAPH DOMAIN
# ═══════════════════════════════════════════════════════════════════════════════


class MemoryRecordRepository:
    """Repository for memory records (episodic / semantic / procedural)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = MemoryRecordModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(MemoryRecordModel).where(MemoryRecordModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(MemoryRecordModel).where(MemoryRecordModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(MemoryRecordModel, key):
                stmt = stmt.where(getattr(MemoryRecordModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(MemoryRecordModel)
            .where(MemoryRecordModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(MemoryRecordModel).where(MemoryRecordModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def search_by_memory_type(self, tenant_id: str, memory_type: str) -> List[dict]:
        """Find memory records by type."""
        stmt = select(MemoryRecordModel).where(
            MemoryRecordModel.tenant_id == tenant_id,
            MemoryRecordModel.memory_type == memory_type,
        )
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]


class KnowledgeNodeRepository:
    """Repository for knowledge graph nodes."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = KnowledgeNodeModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(KnowledgeNodeModel).where(KnowledgeNodeModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(KnowledgeNodeModel).where(KnowledgeNodeModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(KnowledgeNodeModel, key):
                stmt = stmt.where(getattr(KnowledgeNodeModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(KnowledgeNodeModel)
            .where(KnowledgeNodeModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(KnowledgeNodeModel).where(KnowledgeNodeModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class KnowledgeEdgeRepository:
    """Repository for knowledge graph edges."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = KnowledgeEdgeModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(KnowledgeEdgeModel).where(KnowledgeEdgeModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(KnowledgeEdgeModel).where(KnowledgeEdgeModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(KnowledgeEdgeModel, key):
                stmt = stmt.where(getattr(KnowledgeEdgeModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(KnowledgeEdgeModel)
            .where(KnowledgeEdgeModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(KnowledgeEdgeModel).where(KnowledgeEdgeModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def get_edges_for_node(self, tenant_id: str, node_id: UUID) -> List[dict]:
        """Get all edges where the given node is the source or target."""
        stmt = select(KnowledgeEdgeModel).where(
            KnowledgeEdgeModel.tenant_id == tenant_id,
            (KnowledgeEdgeModel.source_id == node_id) | (KnowledgeEdgeModel.target_id == node_id),
        )
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]


# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-CURRENCY / FX DOMAIN
# ═══════════════════════════════════════════════════════════════════════════════


class CurrencyEntityConfigRepository:
    """Repository for currency entity configurations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = CurrencyEntityConfigModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(CurrencyEntityConfigModel).where(CurrencyEntityConfigModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(CurrencyEntityConfigModel).where(CurrencyEntityConfigModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(CurrencyEntityConfigModel, key):
                stmt = stmt.where(getattr(CurrencyEntityConfigModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(CurrencyEntityConfigModel)
            .where(CurrencyEntityConfigModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(CurrencyEntityConfigModel).where(CurrencyEntityConfigModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class FXRateSnapshotRepository:
    """Repository for FX rate snapshots."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = FXRateSnapshotModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(FXRateSnapshotModel).where(FXRateSnapshotModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(FXRateSnapshotModel).where(FXRateSnapshotModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(FXRateSnapshotModel, key):
                stmt = stmt.where(getattr(FXRateSnapshotModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(FXRateSnapshotModel)
            .where(FXRateSnapshotModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(FXRateSnapshotModel).where(FXRateSnapshotModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def get_latest_rate(
        self, tenant_id: str, base_currency: str, target_currency: str
    ) -> Optional[dict]:
        """Get the most recent FX rate snapshot for a currency pair."""
        stmt = (
            select(FXRateSnapshotModel)
            .where(
                FXRateSnapshotModel.tenant_id == tenant_id,
                FXRateSnapshotModel.base_currency == base_currency,
                FXRateSnapshotModel.target_currency == target_currency,
            )
            .order_by(FXRateSnapshotModel.rate_date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE DECISION INTELLIGENCE DOMAIN
# ═══════════════════════════════════════════════════════════════════════════════


class ExecutiveDecisionRepository:
    """Repository for executive decisions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = ExecutiveDecisionModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(ExecutiveDecisionModel).where(ExecutiveDecisionModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(ExecutiveDecisionModel).where(ExecutiveDecisionModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(ExecutiveDecisionModel, key):
                stmt = stmt.where(getattr(ExecutiveDecisionModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(ExecutiveDecisionModel)
            .where(ExecutiveDecisionModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(ExecutiveDecisionModel).where(ExecutiveDecisionModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class CopilotConversationRepository:
    """Repository for copilot conversations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = CopilotConversationModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(CopilotConversationModel).where(CopilotConversationModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(CopilotConversationModel).where(
            CopilotConversationModel.tenant_id == cast(tenant_id, String(100))
        )
        for key, value in filters.items():
            if key == "user_id":
                # user_id column is VARCHAR(100) but filter value may be UUID
                stmt = stmt.where(
                    CopilotConversationModel.user_id == cast(str(value), String(100))
                )
            elif hasattr(CopilotConversationModel, key):
                stmt = stmt.where(getattr(CopilotConversationModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(CopilotConversationModel)
            .where(CopilotConversationModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(CopilotConversationModel).where(CopilotConversationModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# CAUSAL INFERENCE DOMAIN
# ═══════════════════════════════════════════════════════════════════════════════


class CausalGraphRepository:
    """Repository for causal graphs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = CausalGraphModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(CausalGraphModel).where(CausalGraphModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(CausalGraphModel).where(CausalGraphModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(CausalGraphModel, key):
                stmt = stmt.where(getattr(CausalGraphModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(CausalGraphModel)
            .where(CausalGraphModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(CausalGraphModel).where(CausalGraphModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class CausalEstimateRepository:
    """Repository for causal effect estimates."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = CausalEstimateModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(CausalEstimateModel).where(CausalEstimateModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(CausalEstimateModel).where(CausalEstimateModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(CausalEstimateModel, key):
                stmt = stmt.where(getattr(CausalEstimateModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(CausalEstimateModel)
            .where(CausalEstimateModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(CausalEstimateModel).where(CausalEstimateModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def list_by_graph(self, tenant_id: str, graph_id: UUID) -> List[dict]:
        """Get all estimates linked to a specific causal graph."""
        stmt = select(CausalEstimateModel).where(
            CausalEstimateModel.tenant_id == tenant_id,
            CausalEstimateModel.graph_id == graph_id,
        )
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]


# ═══════════════════════════════════════════════════════════════════════════════
# NL QUERY & EXPORT DOMAIN
# ═══════════════════════════════════════════════════════════════════════════════


class NLQueryLogRepository:
    """Repository for natural-language query audit logs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = NLQueryLogModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(NLQueryLogModel).where(NLQueryLogModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(NLQueryLogModel).where(NLQueryLogModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(NLQueryLogModel, key):
                stmt = stmt.where(getattr(NLQueryLogModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(NLQueryLogModel)
            .where(NLQueryLogModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(NLQueryLogModel).where(NLQueryLogModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class ExportJobRepository:
    """Repository for export jobs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = ExportJobModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(ExportJobModel).where(ExportJobModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(ExportJobModel).where(ExportJobModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(ExportJobModel, key):
                stmt = stmt.where(getattr(ExportJobModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(ExportJobModel)
            .where(ExportJobModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(ExportJobModel).where(ExportJobModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# COLLABORATION DOMAIN
# ═══════════════════════════════════════════════════════════════════════════════


class CollaborationCommentRepository:
    """Repository for collaboration comments / threads."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = CollaborationCommentModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(CollaborationCommentModel).where(CollaborationCommentModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(CollaborationCommentModel).where(CollaborationCommentModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(CollaborationCommentModel, key):
                stmt = stmt.where(getattr(CollaborationCommentModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(CollaborationCommentModel)
            .where(CollaborationCommentModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(CollaborationCommentModel).where(CollaborationCommentModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def get_thread(self, tenant_id: str, resource_type: str, resource_id: str) -> List[dict]:
        """Get all comments for a resource, ordered by creation time."""
        stmt = (
            select(CollaborationCommentModel)
            .where(
                CollaborationCommentModel.tenant_id == tenant_id,
                CollaborationCommentModel.resource_type == resource_type,
                CollaborationCommentModel.resource_id == resource_id,
            )
            .order_by(CollaborationCommentModel.created_at)
        )
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARDING & VISUALIZATION DOMAIN
# ═══════════════════════════════════════════════════════════════════════════════


class DashboardRepository:
    """Repository for saved dashboards."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = SavedDashboardModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(SavedDashboardModel).where(SavedDashboardModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(SavedDashboardModel).where(SavedDashboardModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(SavedDashboardModel, key):
                stmt = stmt.where(getattr(SavedDashboardModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(SavedDashboardModel)
            .where(SavedDashboardModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(SavedDashboardModel).where(SavedDashboardModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


class VisualizationSpecRepository:
    """Repository for visualization specifications."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = VisualizationSpecModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(VisualizationSpecModel).where(VisualizationSpecModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(VisualizationSpecModel).where(VisualizationSpecModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(VisualizationSpecModel, key):
                stmt = stmt.where(getattr(VisualizationSpecModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(VisualizationSpecModel)
            .where(VisualizationSpecModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(VisualizationSpecModel).where(VisualizationSpecModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# SEMANTIC LAYER / METRICS CATALOG V2
# ═══════════════════════════════════════════════════════════════════════════════


class SemanticMetricRepository:
    """Repository for semantic metrics v2."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = SemanticMetricV2Model(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(SemanticMetricV2Model).where(SemanticMetricV2Model.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(SemanticMetricV2Model).where(SemanticMetricV2Model.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(SemanticMetricV2Model, key):
                stmt = stmt.where(getattr(SemanticMetricV2Model, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(SemanticMetricV2Model)
            .where(SemanticMetricV2Model.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(SemanticMetricV2Model).where(SemanticMetricV2Model.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def get_by_slug(self, tenant_id: str, slug: str) -> Optional[dict]:
        """Look up a metric by its unique slug within a tenant."""
        result = await self.session.execute(
            select(SemanticMetricV2Model).where(
                SemanticMetricV2Model.tenant_id == tenant_id,
                SemanticMetricV2Model.slug == slug,
            )
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None


class SemanticDimensionRepository:
    """Repository for semantic dimensions v2."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = SemanticDimensionV2Model(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(SemanticDimensionV2Model).where(SemanticDimensionV2Model.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(SemanticDimensionV2Model).where(SemanticDimensionV2Model.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(SemanticDimensionV2Model, key):
                stmt = stmt.where(getattr(SemanticDimensionV2Model, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(SemanticDimensionV2Model)
            .where(SemanticDimensionV2Model.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(SemanticDimensionV2Model).where(SemanticDimensionV2Model.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def get_by_slug(self, tenant_id: str, slug: str) -> Optional[dict]:
        """Look up a dimension by its unique slug within a tenant."""
        result = await self.session.execute(
            select(SemanticDimensionV2Model).where(
                SemanticDimensionV2Model.tenant_id == tenant_id,
                SemanticDimensionV2Model.slug == slug,
            )
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None


# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE CACHE DOMAIN
# ═══════════════════════════════════════════════════════════════════════════════


class MaterializedViewCacheRepository:
    """Repository for materialized view / query result cache entries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> dict:
        model = MaterializedViewCacheModel(**kwargs)
        self.session.add(model)
        await self.session.flush()
        return _to_dict(model)

    async def get(self, id: UUID) -> Optional[dict]:
        result = await self.session.execute(
            select(MaterializedViewCacheModel).where(MaterializedViewCacheModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def list(self, tenant_id: str, **filters) -> List[dict]:
        stmt = select(MaterializedViewCacheModel).where(MaterializedViewCacheModel.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(MaterializedViewCacheModel, key):
                stmt = stmt.where(getattr(MaterializedViewCacheModel, key) == value)
        result = await self.session.execute(stmt)
        return [_to_dict(r) for r in result.scalars().all()]

    async def update(self, id: UUID, **updates) -> dict:
        await self.session.execute(
            update(MaterializedViewCacheModel)
            .where(MaterializedViewCacheModel.id == id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(MaterializedViewCacheModel).where(MaterializedViewCacheModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def get_by_query_hash(self, tenant_id: str, query_hash: str) -> Optional[dict]:
        """Retrieve a cache entry by query hash within a tenant."""
        result = await self.session.execute(
            select(MaterializedViewCacheModel).where(
                MaterializedViewCacheModel.tenant_id == tenant_id,
                MaterializedViewCacheModel.query_hash == query_hash,
            )
        )
        row = result.scalar_one_or_none()
        return _to_dict(row) if row else None

    async def invalidate(self, tenant_id: str, name: str) -> int:
        """Delete all cache entries matching a view name. Returns count of deleted rows."""
        result = await self.session.execute(
            delete(MaterializedViewCacheModel).where(
                MaterializedViewCacheModel.tenant_id == tenant_id,
                MaterializedViewCacheModel.name == name,
            )
        )
        await self.session.flush()
        return result.rowcount
