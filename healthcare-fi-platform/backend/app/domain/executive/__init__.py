"""
Executive Memory Domain.
Tracks executive behavior, preferences, and recommendation adoption patterns.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any


@dataclass(kw_only=True)
class ExecutiveProfile:
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID

    insights_viewed: List[Dict[str, Any]] = field(default_factory=list)
    insights_dismissed: List[Dict[str, Any]] = field(default_factory=list)
    recommendations_received: List[Dict[str, Any]] = field(default_factory=list)
    decisions_made: List[Dict[str, Any]] = field(default_factory=list)

    average_time_to_decision: Optional[float] = None
    acceptance_rate: Optional[float] = None
    most_active_hours: Optional[List[int]] = None

    preferred_insight_types: List[str] = field(default_factory=list)
    preferred_briefing_frequency: str = "daily"

    role: str = ""
    department_ids: List[uuid.UUID] = field(default_factory=list)
    seniority_level: str = "executive"

    last_active_at: Optional[datetime] = None
    profile_version: int = 1
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id), "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id), "role": self.role,
            "acceptance_rate": self.acceptance_rate,
            "average_time_to_decision": self.average_time_to_decision,
            "preferred_insight_types": self.preferred_insight_types,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
        }


@dataclass(kw_only=True)
class ExecutiveInsightReaction:
    id: uuid.UUID
    tenant_id: uuid.UUID
    insight_id: uuid.UUID
    executor_id: uuid.UUID
    reaction: str = "viewed"
    depth: str = "brief"
    time_spent_seconds: Optional[int] = None
    actions_taken: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id), "insight_id": str(self.insight_id),
            "executor_id": str(self.executor_id), "reaction": self.reaction,
            "depth": self.depth, "created_at": self.created_at.isoformat(),
        }


@dataclass(kw_only=True)
class RecommendationAcceptance:
    id: uuid.UUID
    tenant_id: uuid.UUID
    recommendation_id: uuid.UUID
    recipient_id: uuid.UUID
    status: str = "pending"
    received_at: datetime = field(default_factory=datetime.utcnow)
    decision_at: Optional[datetime] = None
    implementation_at: Optional[datetime] = None
    outcome_measured_at: Optional[datetime] = None
    outcome_id: Optional[uuid.UUID] = None
    actual_value_realized: Optional[float] = None
    acceptance_reason: Optional[str] = None
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id), "recommendation_id": str(self.recommendation_id),
            "recipient_id": str(self.recipient_id), "status": self.status,
            "received_at": self.received_at.isoformat(),
        }
