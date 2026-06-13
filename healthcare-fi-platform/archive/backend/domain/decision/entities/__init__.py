"""
Decision Domain Entities.
Core entities: Decision, DecisionEvidence, DecisionOutcome, DecisionReview, DecisionTimeline.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from app.domain.decision.value_objects import (
    DecisionStatus,
    DecisionType,
    DecisionCategory,
    TriggerType,
    PriorityLabel,
    UrgencyLabel,
    ScopeType,
    Currency,
    EvidenceType,
    SourceType,
    ReviewType,
    ReviewStatus,
    ReviewDecision,
    ReviewComment,
    TimelineEventType,
    OutcomeStatus,
    OutcomeMetricDefinition,
    MeasuredMetric,
    ConfoundingFactor,
    CausalImpactResult,
    OutcomeMetric,
)


@dataclass(kw_only=True)
class Decision:
    """
    The central artifact. Every business decision is a Decision record.
    """
    id: uuid.UUID
    tenant_id: uuid.UUID
    title: str
    description: str
    decision_type: DecisionType
    status: DecisionStatus = DecisionStatus.PROPOSED
    priority: PriorityLabel = PriorityLabel.P2
    urgency: UrgencyLabel = UrgencyLabel.SCHEDULED

    # Context — what intelligence triggered this?
    trigger_type: TriggerType = TriggerType.MANUAL
    trigger_id: Optional[uuid.UUID] = None
    trigger_summary: str = ""

    # Classification
    category: DecisionCategory = DecisionCategory.OPERATIONAL
    department_ids: List[uuid.UUID] = field(default_factory=list)
    scope_type: ScopeType = ScopeType.TENANT
    scope_id: Optional[uuid.UUID] = None

    # Financial
    estimated_value: Optional[float] = None
    estimated_cost: Optional[float] = None
    currency: Currency = Currency.INR

    # Timing
    review_deadline: Optional[datetime] = None
    approval_deadline: Optional[datetime] = None
    implementation_target_date: Optional[date] = None
    completion_date: Optional[datetime] = None

    # People
    proposed_by: Optional[uuid.UUID] = None
    proposed_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_by: List[uuid.UUID] = field(default_factory=list)
    approved_by: List[uuid.UUID] = field(default_factory=list)
    rejected_by: Optional[uuid.UUID] = None
    rejection_reason: Optional[str] = None
    implemented_by: Optional[uuid.UUID] = None

    # Outcome
    outcome_id: Optional[uuid.UUID] = None

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Lifecycle
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[uuid.UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[uuid.UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None

    def submit_for_review(self, user_id: uuid.UUID) -> None:
        """Submit decision for review."""
        if self.status != DecisionStatus.PROPOSED:
            raise ValueError(f"Cannot submit decision in {self.status} status")
        self.status = DecisionStatus.REVIEWING
        self.updated_at = datetime.utcnow()
        self.updated_by = user_id
        self.version += 1

    def approve(self, reviewer_id: uuid.UUID) -> None:
        """Approve the decision."""
        if self.status != DecisionStatus.REVIEWING:
            raise ValueError(f"Cannot approve decision in {self.status} status")
        self.status = DecisionStatus.APPROVED
        if reviewer_id not in self.approved_by:
            self.approved_by.append(reviewer_id)
        self.updated_at = datetime.utcnow()
        self.updated_by = reviewer_id
        self.version += 1

    def reject(self, reviewer_id: uuid.UUID, reason: str = "") -> None:
        """Reject the decision."""
        if self.status != DecisionStatus.REVIEWING:
            raise ValueError(f"Cannot reject decision in {self.status} status")
        self.status = DecisionStatus.REJECTED
        self.rejected_by = reviewer_id
        self.rejection_reason = reason
        self.updated_at = datetime.utcnow()
        self.updated_by = reviewer_id
        self.version += 1

    def start_implementation(self, user_id: uuid.UUID) -> None:
        """Start implementation."""
        if self.status != DecisionStatus.APPROVED:
            raise ValueError(f"Cannot start implementation in {self.status} status")
        self.status = DecisionStatus.IN_PROGRESS
        self.implemented_by = user_id
        self.updated_at = datetime.utcnow()
        self.updated_by = user_id
        self.version += 1

    def complete_implementation(self, user_id: uuid.UUID) -> None:
        """Mark implementation as complete."""
        if self.status != DecisionStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete implementation in {self.status} status")
        self.status = DecisionStatus.COMPLETED
        self.completion_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.updated_by = user_id
        self.version += 1

    def measure(self, user_id: uuid.UUID) -> None:
        """Mark decision as measured (outcome recorded)."""
        if self.status != DecisionStatus.COMPLETED:
            raise ValueError(f"Cannot measure decision in {self.status} status")
        self.status = DecisionStatus.MEASURED
        self.updated_at = datetime.utcnow()
        self.updated_by = user_id
        self.version += 1

    def archive(self, user_id: uuid.UUID) -> None:
        """Archive the decision."""
        self.status = DecisionStatus.ARCHIVED
        self.updated_at = datetime.utcnow()
        self.updated_by = user_id
        self.version += 1

    def soft_delete(self, user_id: uuid.UUID) -> None:
        """Soft delete the decision."""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user_id
        self.updated_at = datetime.utcnow()
        self.updated_by = user_id
        self.version += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "title": self.title,
            "description": self.description,
            "decision_type": self.decision_type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "urgency": self.urgency.value,
            "trigger_type": self.trigger_type.value,
            "trigger_id": str(self.trigger_id) if self.trigger_id else None,
            "trigger_summary": self.trigger_summary,
            "category": self.category.value,
            "department_ids": [str(d) for d in self.department_ids],
            "scope_type": self.scope_type.value,
            "scope_id": str(self.scope_id) if self.scope_id else None,
            "estimated_value": self.estimated_value,
            "estimated_cost": self.estimated_cost,
            "currency": self.currency.value,
            "review_deadline": self.review_deadline.isoformat() if self.review_deadline else None,
            "approval_deadline": self.approval_deadline.isoformat() if self.approval_deadline else None,
            "implementation_target_date": self.implementation_target_date.isoformat() if self.implementation_target_date else None,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "proposed_by": str(self.proposed_by) if self.proposed_by else None,
            "proposed_at": self.proposed_at.isoformat(),
            "reviewed_by": [str(r) for r in self.reviewed_by],
            "approved_by": [str(a) for a in self.approved_by],
            "rejected_by": str(self.rejected_by) if self.rejected_by else None,
            "rejection_reason": self.rejection_reason,
            "implemented_by": str(self.implemented_by) if self.implemented_by else None,
            "outcome_id": str(self.outcome_id) if self.outcome_id else None,
            "tags": self.tags,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(kw_only=True)
class DecisionEvidence:
    """
    Evidence supporting a decision. No evidence = invalid decision.
    """
    id: uuid.UUID
    tenant_id: uuid.UUID
    decision_id: uuid.UUID

    evidence_type: EvidenceType
    title: str
    description: str
    weight: float = 1.0  # 0.0–1.0
    source_type: SourceType = SourceType.USER_INPUT
    source_id: Optional[uuid.UUID] = None
    source_metric_code: Optional[str] = None
    data_payload: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[uuid.UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "decision_id": str(self.decision_id),
            "evidence_type": self.evidence_type.value,
            "title": self.title,
            "description": self.description,
            "weight": self.weight,
            "source_type": self.source_type.value,
            "source_id": str(self.source_id) if self.source_id else None,
            "source_metric_code": self.source_metric_code,
            "data_payload": self.data_payload,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(kw_only=True)
class DecisionOutcome:
    """
    Links a decision to its measured business result.
    """
    id: uuid.UUID
    tenant_id: uuid.UUID
    decision_id: uuid.UUID

    # Measurement period
    measurement_start: datetime = field(default_factory=datetime.utcnow)
    measurement_end: Optional[datetime] = None

    # What was expected
    expected_metrics: List[OutcomeMetric] = field(default_factory=list)

    # What actually happened
    actual_metrics: List[OutcomeMetric] = field(default_factory=list)

    # Computed
    accuracy_score: float = 0.0
    variance_absolute: float = 0.0
    variance_percent: float = 0.0
    outcome_status: OutcomeStatus = OutcomeStatus.INCONCLUSIVE

    # Causal analysis
    causal_impact: Optional[CausalImpactResult] = None

    # Financial realization
    realized_value: float = 0.0
    roi_actual: Optional[float] = None

    # Status
    measured_by: Optional[uuid.UUID] = None
    measured_at: Optional[datetime] = None

    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "decision_id": str(self.decision_id),
            "measurement_start": self.measurement_start.isoformat(),
            "measurement_end": self.measurement_end.isoformat() if self.measurement_end else None,
            "accuracy_score": self.accuracy_score,
            "variance_absolute": self.variance_absolute,
            "variance_percent": self.variance_percent,
            "outcome_status": self.outcome_status.value,
            "realized_value": self.realized_value,
            "roi_actual": self.roi_actual,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(kw_only=True)
class DecisionReview:
    """
    Formal review record with approvals, rejections, and comments.
    """
    id: uuid.UUID
    tenant_id: uuid.UUID
    decision_id: uuid.UUID

    review_type: ReviewType = ReviewType.INITIAL_REVIEW
    review_round: int = 1
    status: ReviewStatus = ReviewStatus.PENDING

    reviewer_id: Optional[uuid.UUID] = None
    reviewer_role: str = ""
    review_decision: Optional[ReviewDecision] = None

    comments: List[ReviewComment] = field(default_factory=list)
    conditions: Optional[List[str]] = None
    escalation_required: bool = False
    escalation_to: Optional[uuid.UUID] = None

    decided_at: Optional[datetime] = None

    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "decision_id": str(self.decision_id),
            "review_type": self.review_type.value,
            "review_round": self.review_round,
            "status": self.status.value,
            "reviewer_id": str(self.reviewer_id) if self.reviewer_id else None,
            "reviewer_role": self.reviewer_role,
            "review_decision": self.review_decision.value if self.review_decision else None,
            "conditions": self.conditions,
            "escalation_required": self.escalation_required,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class DecisionTimeline:
    """
    Immutable audit log of every state change.
    """
    id: uuid.UUID
    tenant_id: uuid.UUID
    decision_id: uuid.UUID

    event_type: TimelineEventType
    from_status: Optional[DecisionStatus] = None
    to_status: DecisionStatus = DecisionStatus.PROPOSED
    actor_id: Optional[uuid.UUID] = None
    actor_role: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "decision_id": str(self.decision_id),
            "event_type": self.event_type.value,
            "from_status": self.from_status.value if self.from_status else None,
            "to_status": self.to_status.value,
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "actor_role": self.actor_role,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
