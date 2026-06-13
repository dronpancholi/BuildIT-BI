"""
Repository interfaces for Intelligence domain entities.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.domain.intelligence.value_objects import (
    ArtifactType,
    ArtifactStatus,
    InsightType,
    AnomalyType,
    AnomalySeverity,
    OpportunityType,
    OpportunityStatus,
    RecommendationType,
    RecommendationStatus,
    BriefingType,
    BriefingStatus,
    ScopeType,
    PeriodType,
)

T = TypeVar("T")


class BaseIntelligenceRepository(ABC, Generic[T]):
    """Generic CRUD contract for intelligence artifacts."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        ...

    @abstractmethod
    async def get_by_id_with_tenant(self, id: UUID, tenant_id: UUID) -> Optional[T]:
        ...

    @abstractmethod
    async def list(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
        status: Optional[ArtifactStatus] = None,
        scope_type: Optional[ScopeType] = None,
        scope_id: Optional[UUID] = None,
        period_type: Optional[PeriodType] = None,
        period_start_after: Optional[datetime] = None,
        period_start_before: Optional[datetime] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[T]:
        ...

    @abstractmethod
    async def count(
        self,
        tenant_id: UUID,
        *,
        status: Optional[ArtifactStatus] = None,
        scope_type: Optional[ScopeType] = None,
        scope_id: Optional[UUID] = None,
    ) -> int:
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        ...

    @abstractmethod
    async def soft_delete(self, id: UUID, tenant_id: UUID, deleted_by: Optional[UUID] = None) -> bool:
        ...

    @abstractmethod
    async def exists(self, id: UUID, tenant_id: UUID) -> bool:
        ...


class InsightRepository(BaseIntelligenceRepository):
    """Repository for Insight artifacts."""

    @abstractmethod
    async def list_by_type(
        self, tenant_id: UUID, insight_type: InsightType, *, offset: int = 0, limit: int = 100
    ) -> list:
        ...

    @abstractmethod
    async def list_significant(self, tenant_id: UUID, *, min_confidence: float = 0.8) -> list:
        ...

    @abstractmethod
    async def list_unnotified(self, tenant_id: UUID) -> list:
        ...

    @abstractmethod
    async def get_latest_for_metric(
        self, tenant_id: UUID, metric_id: UUID
    ) -> Optional[T]:
        ...


class RootCauseRepository(BaseIntelligenceRepository):
    """Repository for RootCause artifacts."""

    @abstractmethod
    async def list_by_metric(self, tenant_id: UUID, metric_id: UUID) -> list:
        ...

    @abstractmethod
    async def list_primary_causes(self, tenant_id: UUID) -> list:
        ...

    @abstractmethod
    async def get_by_insight(self, tenant_id: UUID, insight_id: UUID) -> Optional[T]:
        ...


class AnomalyRepository(BaseIntelligenceRepository):
    """Repository for Anomaly artifacts."""

    @abstractmethod
    async def list_by_type(
        self, tenant_id: UUID, anomaly_type: AnomalyType, *, offset: int = 0, limit: int = 100
    ) -> list:
        ...

    @abstractmethod
    async def list_by_severity(
        self, tenant_id: UUID, severity: AnomalySeverity
    ) -> list:
        ...

    @abstractmethod
    async def list_unresolved(self, tenant_id: UUID) -> list:
        ...

    @abstractmethod
    async def list_persistent(self, tenant_id: UUID, *, min_periods: int = 3) -> list:
        ...

    @abstractmethod
    async def get_latest_for_metric(
        self, tenant_id: UUID, metric_id: UUID
    ) -> Optional[T]:
        ...


class OpportunityRepository(BaseIntelligenceRepository):
    """Repository for Opportunity artifacts."""

    @abstractmethod
    async def list_by_type(
        self, tenant_id: UUID, opportunity_type: OpportunityType, *, offset: int = 0, limit: int = 100
    ) -> list:
        ...

    @abstractmethod
    async def list_active(self, tenant_id: UUID) -> list:
        ...

    @abstractmethod
    async def list_by_status(
        self, tenant_id: UUID, status: OpportunityStatus
    ) -> list:
        ...

    @abstractmethod
    async def get_top_by_value(
        self, tenant_id: UUID, *, limit: int = 10
    ) -> list:
        ...

    @abstractmethod
    async def list_by_owner(self, tenant_id: UUID, owner_id: UUID) -> list:
        ...


class RecommendationRepository(BaseIntelligenceRepository):
    """Repository for Recommendation artifacts."""

    @abstractmethod
    async def list_by_type(
        self, tenant_id: UUID, recommendation_type: RecommendationType, *, offset: int = 0, limit: int = 100
    ) -> list:
        ...

    @abstractmethod
    async def list_by_status(
        self, tenant_id: UUID, status: RecommendationStatus
    ) -> list:
        ...

    @abstractmethod
    async def list_pending_review(self, tenant_id: UUID) -> list:
        ...

    @abstractmethod
    async def list_by_assignee(self, tenant_id: UUID, assignee_id: UUID) -> list:
        ...

    @abstractmethod
    async def get_top_by_priority(
        self, tenant_id: UUID, *, limit: int = 10
    ) -> list:
        ...


class BriefingRepository(BaseIntelligenceRepository):
    """Repository for Briefing artifacts."""

    @abstractmethod
    async def list_by_type(
        self, tenant_id: UUID, briefing_type: BriefingType, *, offset: int = 0, limit: int = 100
    ) -> list:
        ...

    @abstractmethod
    async def list_by_status(
        self, tenant_id: UUID, status: BriefingStatus
    ) -> list:
        ...

    @abstractmethod
    async def get_latest(
        self, tenant_id: UUID, briefing_type: BriefingType
    ) -> Optional[T]:
        ...

    @abstractmethod
    async def list_for_recipient(
        self, tenant_id: UUID, recipient_id: UUID
    ) -> list:
        ...


class IntelligenceNodeRepository(BaseIntelligenceRepository):
    """Repository for IntelligenceNode graph nodes."""

    @abstractmethod
    async def get_by_entity(
        self, tenant_id: UUID, entity_type: str, entity_id: UUID
    ) -> Optional[T]:
        ...

    @abstractmethod
    async def list_by_type(
        self, tenant_id: UUID, node_type: str
    ) -> list:
        ...

    @abstractmethod
    async def get_neighbors(
        self, tenant_id: UUID, node_id: UUID, *, depth: int = 1
    ) -> list:
        ...


class IntelligenceRelationshipRepository(BaseIntelligenceRepository):
    """Repository for IntelligenceRelationship edges."""

    @abstractmethod
    async def get_by_nodes(
        self, tenant_id: UUID, source_id: UUID, target_id: UUID
    ) -> Optional[T]:
        ...

    @abstractmethod
    async def list_from_node(self, tenant_id: UUID, source_id: UUID) -> list:
        ...

    @abstractmethod
    async def list_to_node(self, tenant_id: UUID, target_id: UUID) -> list:
        ...

    @abstractmethod
    async def list_by_type(
        self, tenant_id: UUID, relationship_type: str
    ) -> list:
        ...
