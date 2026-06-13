"""
SQLAlchemy Repository Implementations for Phase 2.
Concrete implementations of all repository interfaces.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Type, TypeVar, Generic
from abc import ABC, abstractmethod

from sqlalchemy import select, func, and_, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.domain.repositories.interfaces import (
    BaseRepository,
    MetricDefinitionRepository,
    MetricComputedValueRepository,
    QualityRuleRepository,
    QualityIssueRepository,
    LineageNodeRepository,
    LineageEdgeRepository,
    TenantRepository,
    UserRepository,
    DomainEventRepository
)
from app.domain.entities.base import TenantAwareEntity
from app.infrastructure.persistence.models import (
    MetricDefinitionModel,
    MetricComputedValueModel,
    QualityRuleModel,
    QualityIssueModel,
    DataQualityScoreModel,
    LineageNodeModel,
    LineageEdgeModel,
    LineageComputationRecordModel,
    TenantModel,
    UserModel,
    DomainEventModel,
    Base
)

T = TypeVar('T', bound=TenantAwareEntity)


class BaseRepositoryImpl(BaseRepository, Generic[T]):
    """
    Base repository implementation with common CRUD operations.
    """
    
    def __init__(self, session: AsyncSession, model_class: Type):
        self._session = session
        self._model_class = model_class
    
    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[T]:
        """Get entity by ID."""
        query = select(self._model_class).where(
            self._model_class.id == entity_id,
            self._model_class.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None
    
    async def get_by_id_with_tenant(self, entity_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[T]:
        """Get entity by ID with tenant scoping."""
        query = select(self._model_class).where(
            self._model_class.id == entity_id,
            self._model_class.tenant_id == tenant_id,
            self._model_class.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None
    
    async def list(
        self,
        tenant_id: uuid.UUID,
        filters: Optional[Dict] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[T]:
        """List entities with pagination."""
        query = select(self._model_class).where(
            self._model_class.tenant_id == tenant_id,
            self._model_class.deleted_at.is_(None)
        )
        
        if filters:
            for key, value in filters.items():
                if hasattr(self._model_class, key):
                    query = query.where(getattr(self._model_class, key) == value)
        
        query = query.offset(offset).limit(limit)
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]
    
    async def count(self, tenant_id: uuid.UUID, filters: Optional[Dict] = None) -> int:
        """Count entities."""
        query = select(func.count()).select_from(self._model_class).where(
            self._model_class.tenant_id == tenant_id,
            self._model_class.deleted_at.is_(None)
        )
        
        if filters:
            for key, value in filters.items():
                if hasattr(self._model_class, key):
                    query = query.where(getattr(self._model_class, key) == value)
        
        result = await self._session.execute(query)
        return result.scalar() or 0
    
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        query = select(self._model_class).where(
            self._model_class.id == entity.entity_id
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Entity {entity.entity_id} not found")
        
        # Update fields
        for key, value in entity.__dict__.items():
            if not key.startswith('_') and key != 'entity_id':
                setattr(model, key, value)
        
        model.updated_at = datetime.utcnow()
        model.version = entity.version
        
        await self._session.flush()
        return self._to_domain(model)
    
    async def soft_delete(self, entity_id: uuid.UUID, deleted_by: uuid.UUID) -> bool:
        """Soft delete an entity."""
        query = select(self._model_class).where(
            self._model_class.id == entity_id
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        model.deleted_at = datetime.utcnow()
        model.deleted_by = deleted_by
        model.updated_at = datetime.utcnow()
        model.updated_by = deleted_by
        model.version += 1
        
        await self._session.flush()
        return True
    
    async def exists(self, entity_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        """Check if entity exists."""
        query = select(func.count()).select_from(self._model_class).where(
            self._model_class.id == entity_id,
            self._model_class.tenant_id == tenant_id,
            self._model_class.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return (result.scalar() or 0) > 0
    
    def _to_domain(self, model) -> T:
        """Convert model to domain entity. Override in subclasses."""
        raise NotImplementedError
    
    def _to_model(self, entity: T):
        """Convert domain entity to model. Override in subclasses."""
        raise NotImplementedError


class MetricDefinitionRepositoryImpl(BaseRepositoryImpl[MetricDefinitionModel]):
    """
    Repository implementation for MetricDefinition.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, MetricDefinitionModel)
    
    async def get_by_slug(self, slug: str, tenant_id: uuid.UUID) -> Optional[MetricDefinitionModel]:
        """Get metric by slug."""
        query = select(MetricDefinitionModel).where(
            MetricDefinitionModel.slug == slug,
            MetricDefinitionModel.tenant_id == tenant_id,
            MetricDefinitionModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_code(self, code: str, tenant_id: uuid.UUID) -> Optional[MetricDefinitionModel]:
        """Get metric by code."""
        query = select(MetricDefinitionModel).where(
            MetricDefinitionModel.code == code,
            MetricDefinitionModel.tenant_id == tenant_id,
            MetricDefinitionModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_published(self, tenant_id: uuid.UUID) -> List[MetricDefinitionModel]:
        """List all published metrics."""
        query = select(MetricDefinitionModel).where(
            MetricDefinitionModel.tenant_id == tenant_id,
            MetricDefinitionModel.status == "published",
            MetricDefinitionModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def list_by_category(
        self,
        tenant_id: uuid.UUID,
        category: str
    ) -> List[MetricDefinitionModel]:
        """List metrics by category."""
        query = select(MetricDefinitionModel).where(
            MetricDefinitionModel.tenant_id == tenant_id,
            MetricDefinitionModel.category == category,
            MetricDefinitionModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def list_by_status(
        self,
        tenant_id: uuid.UUID,
        status: str
    ) -> List[MetricDefinitionModel]:
        """List metrics by status."""
        query = select(MetricDefinitionModel).where(
            MetricDefinitionModel.tenant_id == tenant_id,
            MetricDefinitionModel.status == status,
            MetricDefinitionModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def list(
        self,
        tenant_id: uuid.UUID,
        filters: Optional[Dict] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[MetricDefinitionModel]:
        """List metrics with filtering."""
        query = select(MetricDefinitionModel).where(
            MetricDefinitionModel.tenant_id == tenant_id,
            MetricDefinitionModel.deleted_at.is_(None)
        )
        
        if filters:
            for key, value in filters.items():
                if hasattr(MetricDefinitionModel, key):
                    query = query.where(getattr(MetricDefinitionModel, key) == value)
        
        query = query.offset(offset).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())


class MetricComputedValueRepositoryImpl(BaseRepositoryImpl[MetricComputedValueModel]):
    """
    Repository implementation for MetricComputedValue.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, MetricComputedValueModel)
    
    async def get_latest(
        self,
        metric_id: uuid.UUID,
        tenant_id: uuid.UUID,
        hospital_id: Optional[uuid.UUID] = None,
        branch_id: Optional[uuid.UUID] = None,
        department_id: Optional[uuid.UUID] = None
    ) -> Optional[MetricComputedValueModel]:
        """Get latest computed value for a metric."""
        query = select(MetricComputedValueModel).where(
            MetricComputedValueModel.metric_id == metric_id,
            MetricComputedValueModel.tenant_id == tenant_id,
            MetricComputedValueModel.deleted_at.is_(None)
        )
        
        if hospital_id:
            query = query.where(MetricComputedValueModel.hospital_id == hospital_id)
        if branch_id:
            query = query.where(MetricComputedValueModel.branch_id == branch_id)
        if department_id:
            query = query.where(MetricComputedValueModel.department_id == department_id)
        
        query = query.order_by(MetricComputedValueModel.period_end.desc()).limit(1)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_period(
        self,
        metric_id: uuid.UUID,
        tenant_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime
    ) -> Optional[MetricComputedValueModel]:
        """Get computed value for a specific period."""
        query = select(MetricComputedValueModel).where(
            MetricComputedValueModel.metric_id == metric_id,
            MetricComputedValueModel.tenant_id == tenant_id,
            MetricComputedValueModel.period_start == period_start,
            MetricComputedValueModel.period_end == period_end,
            MetricComputedValueModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_by_metric(
        self,
        metric_id: uuid.UUID,
        tenant_id: uuid.UUID,
        limit: int = 100
    ) -> List[MetricComputedValueModel]:
        """List computed values for a metric."""
        query = select(MetricComputedValueModel).where(
            MetricComputedValueModel.metric_id == metric_id,
            MetricComputedValueModel.tenant_id == tenant_id,
            MetricComputedValueModel.deleted_at.is_(None)
        ).order_by(MetricComputedValueModel.period_end.desc()).limit(limit)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())


class QualityRuleRepositoryImpl(BaseRepositoryImpl[QualityRuleModel]):
    """
    Repository implementation for QualityRule.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, QualityRuleModel)
    
    async def list_active(self, tenant_id: uuid.UUID) -> List[QualityRuleModel]:
        """List all active quality rules."""
        query = select(QualityRuleModel).where(
            QualityRuleModel.tenant_id == tenant_id,
            QualityRuleModel.is_active == True,
            QualityRuleModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def list_by_entity_type(
        self,
        tenant_id: uuid.UUID,
        entity_type: str
    ) -> List[QualityRuleModel]:
        """List rules by entity type."""
        query = select(QualityRuleModel).where(
            QualityRuleModel.tenant_id == tenant_id,
            QualityRuleModel.entity_type == entity_type,
            QualityRuleModel.is_active == True,
            QualityRuleModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def list_by_severity(
        self,
        tenant_id: uuid.UUID,
        severity: str
    ) -> List[QualityRuleModel]:
        """List rules by severity."""
        query = select(QualityRuleModel).where(
            QualityRuleModel.tenant_id == tenant_id,
            QualityRuleModel.severity == severity,
            QualityRuleModel.is_active == True,
            QualityRuleModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())


class QualityIssueRepositoryImpl(BaseRepositoryImpl[QualityIssueModel]):
    """
    Repository implementation for QualityIssue.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, QualityIssueModel)
    
    async def list_open(self, tenant_id: uuid.UUID) -> List[QualityIssueModel]:
        """List all open issues."""
        query = select(QualityIssueModel).where(
            QualityIssueModel.tenant_id == tenant_id,
            QualityIssueModel.status.in_(["open", "acknowledged", "investigating"]),
            QualityIssueModel.deleted_at.is_(None)
        ).order_by(QualityIssueModel.detected_at.desc())
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def list_by_severity(
        self,
        tenant_id: uuid.UUID,
        severity: str
    ) -> List[QualityIssueModel]:
        """List issues by severity."""
        query = select(QualityIssueModel).where(
            QualityIssueModel.tenant_id == tenant_id,
            QualityIssueModel.severity == severity,
            QualityIssueModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def list_by_status(
        self,
        tenant_id: uuid.UUID,
        status: str
    ) -> List[QualityIssueModel]:
        """List issues by status."""
        query = select(QualityIssueModel).where(
            QualityIssueModel.tenant_id == tenant_id,
            QualityIssueModel.status == status,
            QualityIssueModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def count_by_severity(self, tenant_id: uuid.UUID) -> Dict[str, int]:
        """Count issues grouped by severity."""
        query = select(
            QualityIssueModel.severity,
            func.count(QualityIssueModel.id)
        ).where(
            QualityIssueModel.tenant_id == tenant_id,
            QualityIssueModel.deleted_at.is_(None)
        ).group_by(QualityIssueModel.severity)
        
        result = await self._session.execute(query)
        counts = {row[0]: row[1] for row in result.all()}
        
        return {
            "critical": counts.get("critical", 0),
            "high": counts.get("high", 0),
            "medium": counts.get("medium", 0),
            "low": counts.get("low", 0),
            "info": counts.get("info", 0)
        }


class LineageNodeRepositoryImpl(BaseRepositoryImpl[LineageNodeModel]):
    """
    Repository implementation for LineageNode.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, LineageNodeModel)
    
    async def get_by_qualified_name(
        self,
        qualified_name: str,
        tenant_id: uuid.UUID
    ) -> Optional[LineageNodeModel]:
        """Get node by qualified name."""
        query = select(LineageNodeModel).where(
            LineageNodeModel.qualified_name == qualified_name,
            LineageNodeModel.tenant_id == tenant_id,
            LineageNodeModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_by_type(
        self,
        tenant_id: uuid.UUID,
        node_type: str
    ) -> List[LineageNodeModel]:
        """List nodes by type."""
        query = select(LineageNodeModel).where(
            LineageNodeModel.tenant_id == tenant_id,
            LineageNodeModel.node_type == node_type,
            LineageNodeModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())


class LineageEdgeRepositoryImpl(BaseRepositoryImpl[LineageEdgeModel]):
    """
    Repository implementation for LineageEdge.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, LineageEdgeModel)
    
    async def get_upstream_edges(
        self,
        target_node_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> List[LineageEdgeModel]:
        """Get all edges pointing to a node."""
        query = select(LineageEdgeModel).where(
            LineageEdgeModel.target_node_id == target_node_id,
            LineageEdgeModel.tenant_id == tenant_id,
            LineageEdgeModel.is_active == True,
            LineageEdgeModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def get_downstream_edges(
        self,
        source_node_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> List[LineageEdgeModel]:
        """Get all edges from a node."""
        query = select(LineageEdgeModel).where(
            LineageEdgeModel.source_node_id == source_node_id,
            LineageEdgeModel.tenant_id == tenant_id,
            LineageEdgeModel.is_active == True,
            LineageEdgeModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())


class TenantRepositoryImpl(BaseRepositoryImpl[TenantModel]):
    """
    Repository implementation for Tenant.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, TenantModel)
    
    async def get_by_slug(self, slug: str) -> Optional[TenantModel]:
        """Get tenant by slug."""
        query = select(TenantModel).where(TenantModel.slug == slug)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[TenantModel]:
        """Get tenant by name."""
        query = select(TenantModel).where(TenantModel.name == name)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()


class UserRepositoryImpl(BaseRepositoryImpl[UserModel]):
    """
    Repository implementation for User.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel)
    
    async def get_by_email(self, email: str, tenant_id: uuid.UUID) -> Optional[UserModel]:
        """Get user by email."""
        query = select(UserModel).where(
            UserModel.email == email,
            UserModel.tenant_id == tenant_id,
            UserModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_by_role(
        self,
        tenant_id: uuid.UUID,
        role: str
    ) -> List[UserModel]:
        """List users by role."""
        query = select(UserModel).where(
            UserModel.tenant_id == tenant_id,
            UserModel.role == role,
            UserModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())


class DomainEventRepositoryImpl(DomainEventRepository):
    """
    Repository implementation for DomainEvent.
    Events are immutable - only create and read operations.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, event) -> None:
        """Store an event."""
        model = DomainEventModel(
            id=event.event_id,
            tenant_id=event.tenant_id,
            occurred_at=event.occurred_at,
            event_type=event.event_type,
            event_version=event.event_version,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            initiated_by=event.initiated_by,
            initiated_by_type=event.initiated_by_type.value,
            hospital_id=event.hospital_id,
            branch_id=event.branch_id,
            department_id=event.department_id,
            payload=event.payload,
            metadata=event.metadata
        )
        self._session.add(model)
        await self._session.flush()
    
    async def get_by_id(self, event_id: uuid.UUID) -> Optional[DomainEventModel]:
        """Get event by ID."""
        query = select(DomainEventModel).where(DomainEventModel.id == event_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_by_type(
        self,
        tenant_id: uuid.UUID,
        event_type: str,
        limit: int = 100
    ) -> List[DomainEventModel]:
        """List events by type."""
        query = select(DomainEventModel).where(
            DomainEventModel.tenant_id == tenant_id,
            DomainEventModel.event_type == event_type
        ).order_by(DomainEventModel.occurred_at.desc()).limit(limit)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def list_by_time_range(
        self,
        tenant_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100
    ) -> List[DomainEventModel]:
        """List events by time range."""
        query = select(DomainEventModel).where(
            DomainEventModel.tenant_id == tenant_id,
            DomainEventModel.occurred_at >= start_time,
            DomainEventModel.occurred_at <= end_time
        ).order_by(DomainEventModel.occurred_at.desc()).limit(limit)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())


# Repository registry for dependency injection
class RepositoryRegistry:
    """
    Central registry for all repositories.
    Provides dependency injection support.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._repositories = {}
    
    def get_metric_definition_repo(self) -> MetricDefinitionRepositoryImpl:
        if "metric_definition" not in self._repositories:
            self._repositories["metric_definition"] = MetricDefinitionRepositoryImpl(self._session)
        return self._repositories["metric_definition"]
    
    def get_metric_computed_value_repo(self) -> MetricComputedValueRepositoryImpl:
        if "metric_computed_value" not in self._repositories:
            self._repositories["metric_computed_value"] = MetricComputedValueRepositoryImpl(self._session)
        return self._repositories["metric_computed_value"]
    
    def get_quality_rule_repo(self) -> QualityRuleRepositoryImpl:
        if "quality_rule" not in self._repositories:
            self._repositories["quality_rule"] = QualityRuleRepositoryImpl(self._session)
        return self._repositories["quality_rule"]
    
    def get_quality_issue_repo(self) -> QualityIssueRepositoryImpl:
        if "quality_issue" not in self._repositories:
            self._repositories["quality_issue"] = QualityIssueRepositoryImpl(self._session)
        return self._repositories["quality_issue"]
    
    def get_lineage_node_repo(self) -> LineageNodeRepositoryImpl:
        if "lineage_node" not in self._repositories:
            self._repositories["lineage_node"] = LineageNodeRepositoryImpl(self._session)
        return self._repositories["lineage_node"]
    
    def get_lineage_edge_repo(self) -> LineageEdgeRepositoryImpl:
        if "lineage_edge" not in self._repositories:
            self._repositories["lineage_edge"] = LineageEdgeRepositoryImpl(self._session)
        return self._repositories["lineage_edge"]
    
    def get_tenant_repo(self) -> TenantRepositoryImpl:
        if "tenant" not in self._repositories:
            self._repositories["tenant"] = TenantRepositoryImpl(self._session)
        return self._repositories["tenant"]
    
    def get_user_repo(self) -> UserRepositoryImpl:
        if "user" not in self._repositories:
            self._repositories["user"] = UserRepositoryImpl(self._session)
        return self._repositories["user"]
    
    def get_event_repo(self) -> DomainEventRepositoryImpl:
        if "event" not in self._repositories:
            self._repositories["event"] = DomainEventRepositoryImpl(self._session)
        return self._repositories["event"]


# ============================
# INTELLIGENCE REPOSITORY IMPLEMENTATIONS
# ============================

from app.infrastructure.persistence.models import (
    IntelligenceInsightModel,
    IntelligenceRootCauseModel,
    IntelligenceAnomalyModel,
    IntelligenceOpportunityModel,
    IntelligenceRecommendationModel,
    IntelligenceBriefingModel,
    IntelligenceGraphNodeModel,
    IntelligenceRelationshipModel,
)


class BaseIntelligenceRepositoryImpl:
    """Base for intelligence repos — handles soft-delete filter."""

    def __init__(self, session: AsyncSession, model_class: type):
        self._session = session
        self._model_class = model_class

    def _base_query(self, tenant_id):
        return select(self._model_class).where(
            self._model_class.tenant_id == tenant_id,
            self._model_class.deleted_at.is_(None),
        )


class IntelligenceRootCauseRepositoryImpl(BaseIntelligenceRepositoryImpl):
    """SQLAlchemy implementation for RootCause repository."""

    async def get_by_id(self, id):
        result = await self._session.execute(
            select(IntelligenceRootCauseModel).where(IntelligenceRootCauseModel.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_tenant(self, id, tenant_id):
        result = await self._session.execute(
            self._base_query(tenant_id).where(IntelligenceRootCauseModel.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, tenant_id, *, offset=0, limit=100, status=None,
                   scope_type=None, scope_id=None, period_type=None,
                   period_start_after=None, period_start_before=None,
                   order_by="created_at", order_desc=True):
        q = self._base_query(tenant_id)
        if status:
            q = q.where(IntelligenceRootCauseModel.status == status.value)
        if scope_type:
            q = q.where(IntelligenceRootCauseModel.scope_type == scope_type.value)
        if scope_id:
            q = q.where(IntelligenceRootCauseModel.scope_id == scope_id)
        col = getattr(IntelligenceRootCauseModel, order_by, IntelligenceRootCauseModel.created_at)
        q = q.order_by(col.desc() if order_desc else col.asc()).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def count(self, tenant_id, *, status=None, scope_type=None, scope_id=None):
        q = select(func.count()).select_from(IntelligenceRootCauseModel).where(
            IntelligenceRootCauseModel.tenant_id == tenant_id,
            IntelligenceRootCauseModel.deleted_at.is_(None),
        )
        if status:
            q = q.where(IntelligenceRootCauseModel.status == status.value)
        result = await self._session.execute(q)
        return result.scalar()

    async def create(self, entity):
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def update(self, entity):
        await self._session.flush()
        return entity

    async def soft_delete(self, id, tenant_id, deleted_by=None):
        result = await self._session.execute(
            select(IntelligenceRootCauseModel).where(
                IntelligenceRootCauseModel.id == id,
                IntelligenceRootCauseModel.tenant_id == tenant_id,
            )
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        obj.deleted_at = datetime.utcnow()
        obj.deleted_by = deleted_by
        return True

    async def exists(self, id, tenant_id):
        result = await self._session.execute(
            select(func.count()).select_from(IntelligenceRootCauseModel).where(
                IntelligenceRootCauseModel.id == id,
                IntelligenceRootCauseModel.tenant_id == tenant_id,
                IntelligenceRootCauseModel.deleted_at.is_(None),
            )
        )
        return result.scalar() > 0

    async def list_by_metric(self, tenant_id, metric_id):
        q = self._base_query(tenant_id).where(
            IntelligenceRootCauseModel.subject_metric_id == metric_id
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_primary_causes(self, tenant_id):
        q = self._base_query(tenant_id).where(
            IntelligenceRootCauseModel.is_primary_cause == True
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_by_insight(self, tenant_id, insight_id):
        q = self._base_query(tenant_id).where(
            IntelligenceRootCauseModel.related_insight_id == insight_id
        ).limit(1)
        result = await self._session.execute(q)
        return result.scalar_one_or_none()


class IntelligenceInsightRepositoryImpl(BaseIntelligenceRepositoryImpl):
    """SQLAlchemy implementation for Insight repository."""

    async def get_by_id(self, id):
        result = await self._session.execute(
            select(IntelligenceInsightModel).where(IntelligenceInsightModel.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_tenant(self, id, tenant_id):
        result = await self._session.execute(
            self._base_query(tenant_id).where(IntelligenceInsightModel.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, tenant_id, *, offset=0, limit=100, status=None,
                   scope_type=None, scope_id=None, period_type=None,
                   period_start_after=None, period_start_before=None,
                   order_by="created_at", order_desc=True):
        q = self._base_query(tenant_id)
        if status:
            q = q.where(IntelligenceInsightModel.status == status.value)
        if scope_type:
            q = q.where(IntelligenceInsightModel.scope_type == scope_type.value)
        if scope_id:
            q = q.where(IntelligenceInsightModel.scope_id == scope_id)
        if period_type:
            q = q.where(IntelligenceInsightModel.period_type == period_type.value)
        if period_start_after:
            q = q.where(IntelligenceInsightModel.period_start >= period_start_after)
        if period_start_before:
            q = q.where(IntelligenceInsightModel.period_start <= period_start_before)
        col = getattr(IntelligenceInsightModel, order_by, IntelligenceInsightModel.created_at)
        q = q.order_by(col.desc() if order_desc else col.asc())
        q = q.offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def count(self, tenant_id, *, status=None, scope_type=None, scope_id=None):
        q = select(func.count()).select_from(IntelligenceInsightModel).where(
            IntelligenceInsightModel.tenant_id == tenant_id,
            IntelligenceInsightModel.deleted_at.is_(None),
        )
        if status:
            q = q.where(IntelligenceInsightModel.status == status.value)
        if scope_type:
            q = q.where(IntelligenceInsightModel.scope_type == scope_type.value)
        if scope_id:
            q = q.where(IntelligenceInsightModel.scope_id == scope_id)
        result = await self._session.execute(q)
        return result.scalar()

    async def create(self, entity):
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def update(self, entity):
        await self._session.flush()
        return entity

    async def soft_delete(self, id, tenant_id, deleted_by=None):
        result = await self._session.execute(
            select(IntelligenceInsightModel).where(
                IntelligenceInsightModel.id == id,
                IntelligenceInsightModel.tenant_id == tenant_id,
            )
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        obj.deleted_at = datetime.utcnow()
        obj.deleted_by = deleted_by
        return True

    async def exists(self, id, tenant_id):
        result = await self._session.execute(
            select(func.count()).select_from(IntelligenceInsightModel).where(
                IntelligenceInsightModel.id == id,
                IntelligenceInsightModel.tenant_id == tenant_id,
                IntelligenceInsightModel.deleted_at.is_(None),
            )
        )
        return result.scalar() > 0

    async def list_by_type(self, tenant_id, insight_type, *, offset=0, limit=100):
        q = self._base_query(tenant_id).where(
            IntelligenceInsightModel.insight_type == insight_type.value
        ).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_significant(self, tenant_id, *, min_confidence=0.8):
        q = self._base_query(tenant_id).where(
            IntelligenceInsightModel.is_significant == True,
            IntelligenceInsightModel.confidence_level >= min_confidence,
        ).order_by(IntelligenceInsightModel.confidence_level.desc())
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_unnotified(self, tenant_id):
        q = self._base_query(tenant_id).where(
            IntelligenceInsightModel.is_notified == False,
            IntelligenceInsightModel.status == "published",
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_latest_for_metric(self, tenant_id, metric_id):
        q = self._base_query(tenant_id).where(
            IntelligenceInsightModel.metric_id == metric_id
        ).order_by(IntelligenceInsightModel.period_end.desc()).limit(1)
        result = await self._session.execute(q)
        return result.scalar_one_or_none()


class IntelligenceAnomalyRepositoryImpl(BaseIntelligenceRepositoryImpl):
    """SQLAlchemy implementation for Anomaly repository."""

    async def get_by_id(self, id):
        result = await self._session.execute(
            select(IntelligenceAnomalyModel).where(IntelligenceAnomalyModel.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_tenant(self, id, tenant_id):
        result = await self._session.execute(
            self._base_query(tenant_id).where(IntelligenceAnomalyModel.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, tenant_id, *, offset=0, limit=100, status=None,
                   scope_type=None, scope_id=None, period_type=None,
                   period_start_after=None, period_start_before=None,
                   order_by="created_at", order_desc=True):
        q = self._base_query(tenant_id)
        if status:
            q = q.where(IntelligenceAnomalyModel.status == status.value)
        if scope_type:
            q = q.where(IntelligenceAnomalyModel.scope_type == scope_type.value)
        if scope_id:
            q = q.where(IntelligenceAnomalyModel.scope_id == scope_id)
        col = getattr(IntelligenceAnomalyModel, order_by, IntelligenceAnomalyModel.created_at)
        q = q.order_by(col.desc() if order_desc else col.asc()).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def count(self, tenant_id, *, status=None, scope_type=None, scope_id=None):
        q = select(func.count()).select_from(IntelligenceAnomalyModel).where(
            IntelligenceAnomalyModel.tenant_id == tenant_id,
            IntelligenceAnomalyModel.deleted_at.is_(None),
        )
        if status:
            q = q.where(IntelligenceAnomalyModel.status == status.value)
        result = await self._session.execute(q)
        return result.scalar()

    async def create(self, entity):
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def update(self, entity):
        await self._session.flush()
        return entity

    async def soft_delete(self, id, tenant_id, deleted_by=None):
        result = await self._session.execute(
            select(IntelligenceAnomalyModel).where(
                IntelligenceAnomalyModel.id == id,
                IntelligenceAnomalyModel.tenant_id == tenant_id,
            )
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        obj.deleted_at = datetime.utcnow()
        obj.deleted_by = deleted_by
        return True

    async def exists(self, id, tenant_id):
        result = await self._session.execute(
            select(func.count()).select_from(IntelligenceAnomalyModel).where(
                IntelligenceAnomalyModel.id == id,
                IntelligenceAnomalyModel.tenant_id == tenant_id,
                IntelligenceAnomalyModel.deleted_at.is_(None),
            )
        )
        return result.scalar() > 0

    async def list_by_type(self, tenant_id, anomaly_type, *, offset=0, limit=100):
        q = self._base_query(tenant_id).where(
            IntelligenceAnomalyModel.anomaly_type == anomaly_type.value
        ).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_by_severity(self, tenant_id, severity):
        q = self._base_query(tenant_id).where(
            IntelligenceAnomalyModel.severity == severity.value
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_unresolved(self, tenant_id):
        q = self._base_query(tenant_id).where(
            IntelligenceAnomalyModel.anomaly_status.in_(["detected", "investigating"])
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_persistent(self, tenant_id, *, min_periods=3):
        q = self._base_query(tenant_id).where(
            IntelligenceAnomalyModel.is_persistent == True,
            IntelligenceAnomalyModel.anomaly_duration_periods >= min_periods,
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_latest_for_metric(self, tenant_id, metric_id):
        q = self._base_query(tenant_id).where(
            IntelligenceAnomalyModel.metric_id == metric_id
        ).order_by(IntelligenceAnomalyModel.period_end.desc()).limit(1)
        result = await self._session.execute(q)
        return result.scalar_one_or_none()


class IntelligenceOpportunityRepositoryImpl(BaseIntelligenceRepositoryImpl):
    """SQLAlchemy implementation for Opportunity repository."""

    async def get_by_id(self, id):
        result = await self._session.execute(
            select(IntelligenceOpportunityModel).where(IntelligenceOpportunityModel.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_tenant(self, id, tenant_id):
        result = await self._session.execute(
            self._base_query(tenant_id).where(IntelligenceOpportunityModel.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, tenant_id, *, offset=0, limit=100, status=None,
                   scope_type=None, scope_id=None, period_type=None,
                   period_start_after=None, period_start_before=None,
                   order_by="created_at", order_desc=True):
        q = self._base_query(tenant_id)
        if status:
            q = q.where(IntelligenceOpportunityModel.status == status.value)
        if scope_type:
            q = q.where(IntelligenceOpportunityModel.scope_type == scope_type.value)
        if scope_id:
            q = q.where(IntelligenceOpportunityModel.scope_id == scope_id)
        col = getattr(IntelligenceOpportunityModel, order_by, IntelligenceOpportunityModel.created_at)
        q = q.order_by(col.desc() if order_desc else col.asc()).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def count(self, tenant_id, *, status=None, scope_type=None, scope_id=None):
        q = select(func.count()).select_from(IntelligenceOpportunityModel).where(
            IntelligenceOpportunityModel.tenant_id == tenant_id,
            IntelligenceOpportunityModel.deleted_at.is_(None),
        )
        if status:
            q = q.where(IntelligenceOpportunityModel.status == status.value)
        result = await self._session.execute(q)
        return result.scalar()

    async def create(self, entity):
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def update(self, entity):
        await self._session.flush()
        return entity

    async def soft_delete(self, id, tenant_id, deleted_by=None):
        result = await self._session.execute(
            select(IntelligenceOpportunityModel).where(
                IntelligenceOpportunityModel.id == id,
                IntelligenceOpportunityModel.tenant_id == tenant_id,
            )
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        obj.deleted_at = datetime.utcnow()
        obj.deleted_by = deleted_by
        return True

    async def exists(self, id, tenant_id):
        result = await self._session.execute(
            select(func.count()).select_from(IntelligenceOpportunityModel).where(
                IntelligenceOpportunityModel.id == id,
                IntelligenceOpportunityModel.tenant_id == tenant_id,
                IntelligenceOpportunityModel.deleted_at.is_(None),
            )
        )
        return result.scalar() > 0

    async def list_by_type(self, tenant_id, opportunity_type, *, offset=0, limit=100):
        q = self._base_query(tenant_id).where(
            IntelligenceOpportunityModel.opportunity_type == opportunity_type.value
        ).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_active(self, tenant_id):
        q = self._base_query(tenant_id).where(
            IntelligenceOpportunityModel.opportunity_status.in_(["identified", "prioritized", "approved"])
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_by_status(self, tenant_id, status):
        q = self._base_query(tenant_id).where(
            IntelligenceOpportunityModel.opportunity_status == status.value
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_top_by_value(self, tenant_id, *, limit=10):
        q = self._base_query(tenant_id).where(
            IntelligenceOpportunityModel.estimated_value.isnot(None)
        ).order_by(IntelligenceOpportunityModel.estimated_value.desc()).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_by_owner(self, tenant_id, owner_id):
        q = self._base_query(tenant_id).where(
            IntelligenceOpportunityModel.owner_id == owner_id
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())


class IntelligenceRecommendationRepositoryImpl(BaseIntelligenceRepositoryImpl):
    """SQLAlchemy implementation for Recommendation repository."""

    async def get_by_id(self, id):
        result = await self._session.execute(
            select(IntelligenceRecommendationModel).where(IntelligenceRecommendationModel.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_tenant(self, id, tenant_id):
        result = await self._session.execute(
            self._base_query(tenant_id).where(IntelligenceRecommendationModel.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, tenant_id, *, offset=0, limit=100, status=None,
                   scope_type=None, scope_id=None, period_type=None,
                   period_start_after=None, period_start_before=None,
                   order_by="created_at", order_desc=True):
        q = self._base_query(tenant_id)
        if status:
            q = q.where(IntelligenceRecommendationModel.status == status.value)
        if scope_type:
            q = q.where(IntelligenceRecommendationModel.scope_type == scope_type.value)
        if scope_id:
            q = q.where(IntelligenceRecommendationModel.scope_id == scope_id)
        col = getattr(IntelligenceRecommendationModel, order_by, IntelligenceRecommendationModel.created_at)
        q = q.order_by(col.desc() if order_desc else col.asc()).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def count(self, tenant_id, *, status=None, scope_type=None, scope_id=None):
        q = select(func.count()).select_from(IntelligenceRecommendationModel).where(
            IntelligenceRecommendationModel.tenant_id == tenant_id,
            IntelligenceRecommendationModel.deleted_at.is_(None),
        )
        if status:
            q = q.where(IntelligenceRecommendationModel.status == status.value)
        result = await self._session.execute(q)
        return result.scalar()

    async def create(self, entity):
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def update(self, entity):
        await self._session.flush()
        return entity

    async def soft_delete(self, id, tenant_id, deleted_by=None):
        result = await self._session.execute(
            select(IntelligenceRecommendationModel).where(
                IntelligenceRecommendationModel.id == id,
                IntelligenceRecommendationModel.tenant_id == tenant_id,
            )
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        obj.deleted_at = datetime.utcnow()
        obj.deleted_by = deleted_by
        return True

    async def exists(self, id, tenant_id):
        result = await self._session.execute(
            select(func.count()).select_from(IntelligenceRecommendationModel).where(
                IntelligenceRecommendationModel.id == id,
                IntelligenceRecommendationModel.tenant_id == tenant_id,
                IntelligenceRecommendationModel.deleted_at.is_(None),
            )
        )
        return result.scalar() > 0

    async def list_by_type(self, tenant_id, recommendation_type, *, offset=0, limit=100):
        q = self._base_query(tenant_id).where(
            IntelligenceRecommendationModel.recommendation_type == recommendation_type.value
        ).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_by_status(self, tenant_id, status):
        q = self._base_query(tenant_id).where(
            IntelligenceRecommendationModel.recommendation_status == status.value
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_pending_review(self, tenant_id):
        q = self._base_query(tenant_id).where(
            IntelligenceRecommendationModel.recommendation_status == "proposed"
        ).order_by(IntelligenceRecommendationModel.priority_score.desc())
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_by_assignee(self, tenant_id, assignee_id):
        q = self._base_query(tenant_id).where(
            IntelligenceRecommendationModel.assigned_to_id == assignee_id
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_top_by_priority(self, tenant_id, *, limit=10):
        q = self._base_query(tenant_id).where(
            IntelligenceRecommendationModel.priority_score.isnot(None)
        ).order_by(IntelligenceRecommendationModel.priority_score.desc()).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())


class IntelligenceBriefingRepositoryImpl(BaseIntelligenceRepositoryImpl):
    """SQLAlchemy implementation for Briefing repository."""

    async def get_by_id(self, id):
        result = await self._session.execute(
            select(IntelligenceBriefingModel).where(IntelligenceBriefingModel.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_tenant(self, id, tenant_id):
        result = await self._session.execute(
            self._base_query(tenant_id).where(IntelligenceBriefingModel.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, tenant_id, *, offset=0, limit=100, status=None,
                   scope_type=None, scope_id=None, period_type=None,
                   period_start_after=None, period_start_before=None,
                   order_by="created_at", order_desc=True):
        q = self._base_query(tenant_id)
        if status:
            q = q.where(IntelligenceBriefingModel.status == status.value)
        if scope_type:
            q = q.where(IntelligenceBriefingModel.scope_type == scope_type)
        if scope_id:
            q = q.where(IntelligenceBriefingModel.scope_id == scope_id)
        col = getattr(IntelligenceBriefingModel, order_by, IntelligenceBriefingModel.created_at)
        q = q.order_by(col.desc() if order_desc else col.asc()).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def count(self, tenant_id, *, status=None, scope_type=None, scope_id=None):
        q = select(func.count()).select_from(IntelligenceBriefingModel).where(
            IntelligenceBriefingModel.tenant_id == tenant_id,
            IntelligenceBriefingModel.deleted_at.is_(None),
        )
        if status:
            q = q.where(IntelligenceBriefingModel.status == status.value)
        result = await self._session.execute(q)
        return result.scalar()

    async def create(self, entity):
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def update(self, entity):
        await self._session.flush()
        return entity

    async def soft_delete(self, id, tenant_id, deleted_by=None):
        result = await self._session.execute(
            select(IntelligenceBriefingModel).where(
                IntelligenceBriefingModel.id == id,
                IntelligenceBriefingModel.tenant_id == tenant_id,
            )
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        obj.deleted_at = datetime.utcnow()
        obj.deleted_by = deleted_by
        return True

    async def exists(self, id, tenant_id):
        result = await self._session.execute(
            select(func.count()).select_from(IntelligenceBriefingModel).where(
                IntelligenceBriefingModel.id == id,
                IntelligenceBriefingModel.tenant_id == tenant_id,
                IntelligenceBriefingModel.deleted_at.is_(None),
            )
        )
        return result.scalar() > 0

    async def list_by_type(self, tenant_id, briefing_type, *, offset=0, limit=100):
        q = self._base_query(tenant_id).where(
            IntelligenceBriefingModel.briefing_type == briefing_type.value
        ).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_by_status(self, tenant_id, status):
        q = self._base_query(tenant_id).where(
            IntelligenceBriefingModel.briefing_status == status.value
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_latest(self, tenant_id, briefing_type):
        q = self._base_query(tenant_id).where(
            IntelligenceBriefingModel.briefing_type == briefing_type.value
        ).order_by(IntelligenceBriefingModel.period_end.desc()).limit(1)
        result = await self._session.execute(q)
        return result.scalar_one_or_none()

    async def list_for_recipient(self, tenant_id, recipient_id):
        q = self._base_query(tenant_id).where(
            IntelligenceBriefingModel.recipient_ids.op("@>")(f'["{str(recipient_id)}"]')
        ).order_by(IntelligenceBriefingModel.created_at.desc())
        result = await self._session.execute(q)
        return list(result.scalars().all())


class IntelligenceGraphNodeRepositoryImpl(BaseIntelligenceRepositoryImpl):
    """SQLAlchemy implementation for IntelligenceGraphNode repository."""

    async def get_by_id(self, id):
        result = await self._session.execute(
            select(IntelligenceGraphNodeModel).where(IntelligenceGraphNodeModel.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_tenant(self, id, tenant_id):
        result = await self._session.execute(
            self._base_query(tenant_id).where(IntelligenceGraphNodeModel.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, tenant_id, *, offset=0, limit=100, **kwargs):
        q = self._base_query(tenant_id).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def count(self, tenant_id, **kwargs):
        q = select(func.count()).select_from(IntelligenceGraphNodeModel).where(
            IntelligenceGraphNodeModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(q)
        return result.scalar()

    async def create(self, entity):
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def update(self, entity):
        await self._session.flush()
        return entity

    async def soft_delete(self, id, tenant_id, deleted_by=None):
        return False

    async def exists(self, id, tenant_id):
        result = await self._session.execute(
            select(func.count()).select_from(IntelligenceGraphNodeModel).where(
                IntelligenceGraphNodeModel.id == id,
                IntelligenceGraphNodeModel.tenant_id == tenant_id,
            )
        )
        return result.scalar() > 0

    async def get_by_entity(self, tenant_id, entity_type, entity_id):
        q = self._base_query(tenant_id).where(
            IntelligenceGraphNodeModel.entity_type == entity_type,
            IntelligenceGraphNodeModel.entity_id == entity_id,
        )
        result = await self._session.execute(q)
        return result.scalar_one_or_none()

    async def list_by_type(self, tenant_id, node_type):
        q = self._base_query(tenant_id).where(
            IntelligenceGraphNodeModel.node_type == node_type
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_neighbors(self, tenant_id, node_id, *, depth=1):
        rel_q = (
            select(IntelligenceRelationshipModel)
            .where(
                IntelligenceRelationshipModel.tenant_id == tenant_id,
                or_(
                    IntelligenceRelationshipModel.source_node_id == node_id,
                    IntelligenceRelationshipModel.target_node_id == node_id,
                ),
            )
        )
        result = await self._session.execute(rel_q)
        rels = list(result.scalars().all())
        neighbor_ids = set()
        for r in rels:
            if r.source_node_id == node_id:
                neighbor_ids.add(r.target_node_id)
            else:
                neighbor_ids.add(r.source_node_id)
        if not neighbor_ids:
            return []
        node_q = self._base_query(tenant_id).where(
            IntelligenceGraphNodeModel.id.in_(neighbor_ids)
        )
        result = await self._session.execute(node_q)
        return list(result.scalars().all())


class IntelligenceRelationshipRepositoryImpl(BaseIntelligenceRepositoryImpl):
    """SQLAlchemy implementation for IntelligenceRelationship repository."""

    async def get_by_id(self, id):
        result = await self._session.execute(
            select(IntelligenceRelationshipModel).where(IntelligenceRelationshipModel.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_tenant(self, id, tenant_id):
        result = await self._session.execute(
            self._base_query(tenant_id).where(IntelligenceRelationshipModel.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, tenant_id, *, offset=0, limit=100, **kwargs):
        q = self._base_query(tenant_id).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def count(self, tenant_id, **kwargs):
        q = select(func.count()).select_from(IntelligenceRelationshipModel).where(
            IntelligenceRelationshipModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(q)
        return result.scalar()

    async def create(self, entity):
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def update(self, entity):
        await self._session.flush()
        return entity

    async def soft_delete(self, id, tenant_id, deleted_by=None):
        return False

    async def exists(self, id, tenant_id):
        result = await self._session.execute(
            select(func.count()).select_from(IntelligenceRelationshipModel).where(
                IntelligenceRelationshipModel.id == id,
                IntelligenceRelationshipModel.tenant_id == tenant_id,
            )
        )
        return result.scalar() > 0

    async def get_by_nodes(self, tenant_id, source_id, target_id):
        q = self._base_query(tenant_id).where(
            IntelligenceRelationshipModel.source_node_id == source_id,
            IntelligenceRelationshipModel.target_node_id == target_id,
        )
        result = await self._session.execute(q)
        return result.scalar_one_or_none()

    async def list_from_node(self, tenant_id, source_id):
        q = self._base_query(tenant_id).where(
            IntelligenceRelationshipModel.source_node_id == source_id
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_to_node(self, tenant_id, target_id):
        q = self._base_query(tenant_id).where(
            IntelligenceRelationshipModel.target_node_id == target_id
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_by_type(self, tenant_id, relationship_type):
        q = self._base_query(tenant_id).where(
            IntelligenceRelationshipModel.relationship_type == relationship_type
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())
