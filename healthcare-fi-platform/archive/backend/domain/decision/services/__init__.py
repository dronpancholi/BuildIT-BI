"""
Decision Domain Service Interfaces.
Abstract service contracts for Decision Management.
"""
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.domain.decision.entities import (
    Decision,
    DecisionEvidence,
    DecisionOutcome,
    DecisionReview,
)
from app.domain.decision.value_objects import (
    DecisionStatus,
    DecisionType,
    DecisionCategory,
    ScopeType,
    PriorityLabel,
    UrgencyLabel,
    TriggerType,
    EvidenceType,
    SourceType,
    ReviewDecision,
)


@dataclass(frozen=True)
class ProposeDecisionCommand:
    title: str
    description: str
    decision_type: DecisionType
    category: DecisionCategory = DecisionCategory.OPERATIONAL
    priority: PriorityLabel = PriorityLabel.P2
    urgency: UrgencyLabel = UrgencyLabel.SCHEDULED
    trigger_type: TriggerType = TriggerType.MANUAL
    trigger_id: Optional[uuid.UUID] = None
    trigger_summary: str = ""
    department_ids: Optional[List[uuid.UUID]] = None
    scope_type: ScopeType = ScopeType.TENANT
    scope_id: Optional[uuid.UUID] = None
    estimated_value: Optional[float] = None
    estimated_cost: Optional[float] = None
    review_deadline: Optional[datetime] = None
    approval_deadline: Optional[datetime] = None
    implementation_target_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ApproveCommand:
    review_decision: ReviewDecision = ReviewDecision.APPROVE
    comments: Optional[str] = None
    conditions: Optional[List[str]] = None


@dataclass(frozen=True)
class EvidenceInput:
    evidence_type: EvidenceType
    title: str
    description: str
    weight: float = 1.0
    source_type: SourceType = SourceType.USER_INPUT
    source_id: Optional[uuid.UUID] = None
    source_metric_code: Optional[str] = None
    data_payload: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class DecisionContext:
    """Full decision context including evidence, timeline, outcome."""
    decision: Decision
    evidence: List[DecisionEvidence]
    timeline: List[Dict[str, Any]]
    outcome: Optional[DecisionOutcome]
    reviews: List[DecisionReview]


@dataclass(frozen=True)
class DecisionSummary:
    id: uuid.UUID
    title: str
    decision_type: DecisionType
    status: DecisionStatus
    priority: PriorityLabel
    category: DecisionCategory
    estimated_value: Optional[float]
    proposed_by: Optional[uuid.UUID]
    created_at: datetime
    evidence_count: int = 0


@dataclass(frozen=True)
class DecisionValueSummary:
    decision_id: uuid.UUID
    estimated_value: Optional[float]
    estimated_cost: Optional[float]
    realized_value: Optional[float]
    roi_expected: Optional[float]
    roi_actual: Optional[float]
    variance: Optional[float]


class IDecisionService(ABC):
    """Abstract decision management service."""

    @abstractmethod
    async def propose_decision(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID,
        command: ProposeDecisionCommand
    ) -> Decision:
        pass

    @abstractmethod
    async def submit_for_review(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Decision:
        pass

    @abstractmethod
    async def approve(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        reviewer_id: uuid.UUID, command: ApproveCommand
    ) -> Decision:
        pass

    @abstractmethod
    async def reject(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        reviewer_id: uuid.UUID, reason: str
    ) -> Decision:
        pass

    @abstractmethod
    async def start_implementation(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Decision:
        pass

    @abstractmethod
    async def complete_implementation(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Decision:
        pass

    @abstractmethod
    async def archive_decision(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Decision:
        pass

    @abstractmethod
    async def attach_evidence(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        user_id: uuid.UUID, evidence: EvidenceInput
    ) -> DecisionEvidence:
        pass

    @abstractmethod
    async def get_decision_with_context(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> DecisionContext:
        pass

    @abstractmethod
    async def get_decisions_requiring_review(
        self, tenant_id: uuid.UUID
    ) -> List[DecisionSummary]:
        pass

    @abstractmethod
    async def calculate_decision_value(
        self, decision_id: uuid.UUID
    ) -> DecisionValueSummary:
        pass
