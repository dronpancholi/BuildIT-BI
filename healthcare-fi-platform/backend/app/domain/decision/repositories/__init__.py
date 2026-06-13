"""
Decision Domain Repository Interfaces.
Abstract repository contracts — no infrastructure dependencies.
"""
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from app.domain.decision.entities import (
    Decision,
    DecisionEvidence,
    DecisionOutcome,
    DecisionReview,
    DecisionTimeline,
)
from app.domain.decision.value_objects import (
    DecisionStatus,
    DecisionType,
    DecisionCategory,
    ScopeType,
)


@dataclass(frozen=True)
class Pagination:
    offset: int = 0
    limit: int = 50


@dataclass(frozen=True)
class DecisionFilter:
    status: Optional[DecisionStatus] = None
    decision_type: Optional[DecisionType] = None
    category: Optional[DecisionCategory] = None
    scope_type: Optional[ScopeType] = None
    scope_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    proposed_by: Optional[uuid.UUID] = None
    search_query: Optional[str] = None


class IDecisionRepository(ABC):
    """Abstract decision repository."""

    @abstractmethod
    async def get_by_id(self, decision_id: uuid.UUID) -> Optional[Decision]:
        pass

    @abstractmethod
    async def get_by_id_with_tenant(self, decision_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Decision]:
        pass

    @abstractmethod
    async def list(self, tenant_id: uuid.UUID, filters: DecisionFilter, pagination: Pagination) -> List[Decision]:
        pass

    @abstractmethod
    async def count(self, tenant_id: uuid.UUID, filters: DecisionFilter) -> int:
        pass

    @abstractmethod
    async def create(self, decision: Decision) -> Decision:
        pass

    @abstractmethod
    async def update(self, decision: Decision) -> Decision:
        pass

    @abstractmethod
    async def soft_delete(self, decision_id: uuid.UUID, deleted_by: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def get_by_status(self, tenant_id: uuid.UUID, status: DecisionStatus, pagination: Pagination) -> List[Decision]:
        pass

    @abstractmethod
    async def get_by_trigger(self, tenant_id: uuid.UUID, trigger_id: uuid.UUID) -> List[Decision]:
        pass

    @abstractmethod
    async def search(self, tenant_id: uuid.UUID, query: str, filters: DecisionFilter, pagination: Pagination) -> List[Decision]:
        pass


class IDecisionEvidenceRepository(ABC):
    """Abstract decision evidence repository."""

    @abstractmethod
    async def get_by_id(self, evidence_id: uuid.UUID) -> Optional[DecisionEvidence]:
        pass

    @abstractmethod
    async def get_by_decision(self, decision_id: uuid.UUID) -> List[DecisionEvidence]:
        pass

    @abstractmethod
    async def create(self, evidence: DecisionEvidence) -> DecisionEvidence:
        pass

    @abstractmethod
    async def delete(self, evidence_id: uuid.UUID) -> bool:
        pass


class IDecisionOutcomeRepository(ABC):
    """Abstract decision outcome repository."""

    @abstractmethod
    async def get_by_id(self, outcome_id: uuid.UUID) -> Optional[DecisionOutcome]:
        pass

    @abstractmethod
    async def get_by_decision(self, decision_id: uuid.UUID) -> Optional[DecisionOutcome]:
        pass

    @abstractmethod
    async def create(self, outcome: DecisionOutcome) -> DecisionOutcome:
        pass

    @abstractmethod
    async def update(self, outcome: DecisionOutcome) -> DecisionOutcome:
        pass


class IDecisionReviewRepository(ABC):
    """Abstract decision review repository."""

    @abstractmethod
    async def get_by_id(self, review_id: uuid.UUID) -> Optional[DecisionReview]:
        pass

    @abstractmethod
    async def get_by_decision(self, decision_id: uuid.UUID) -> List[DecisionReview]:
        pass

    @abstractmethod
    async def create(self, review: DecisionReview) -> DecisionReview:
        pass

    @abstractmethod
    async def update(self, review: DecisionReview) -> DecisionReview:
        pass


class IDecisionTimelineRepository(ABC):
    """Abstract decision timeline repository."""

    @abstractmethod
    async def get_by_decision(self, decision_id: uuid.UUID) -> List[DecisionTimeline]:
        pass

    @abstractmethod
    async def create(self, entry: DecisionTimeline) -> DecisionTimeline:
        pass
