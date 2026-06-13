"""
Analytics Governance Domain — Healthcare Financial Intelligence Platform.
Entities for dashboard/report versioning, metric certification, approval workflows,
and usage analytics.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================
# ENUMS
# ============================================================

class ChangeType(Enum):
    LAYOUT = "LAYOUT"
    WIDGET_ADDED = "WIDGET_ADDED"
    WIDGET_REMOVED = "WIDGET_REMOVED"
    WIDGET_CHANGED = "WIDGET_CHANGED"
    FILTER_CHANGED = "FILTER_CHANGED"
    METRIC_ADDED = "METRIC_ADDED"
    METRIC_REMOVED = "METRIC_REMOVED"
    METRIC_CHANGED = "METRIC_CHANGED"


class CertificationStatus(Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    CERTIFIED = "CERTIFIED"
    EXPIRED = "EXPIRED"


class ApprovalStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ApprovalTarget(Enum):
    DASHBOARD = "DASHBOARD"
    REPORT = "REPORT"
    METRIC = "METRIC"


class ApprovalPolicy(Enum):
    ANY_ONE = "ANY_ONE"
    ALL = "ALL"
    MAJORITY = "MAJORITY"


# ============================================================
# VALUE OBJECTS
# ============================================================

@dataclass(frozen=True, kw_only=True)
class AuditEntry:
    """Immutable audit trail entry."""
    action: str
    performed_by: uuid.UUID
    performed_at: datetime
    details: Optional[str] = None


# ============================================================
# VERSION ENTITIES (IMMUTABLE SNAPSHOTS)
# ============================================================

@dataclass(frozen=True, kw_only=True)
class DashboardVersion:
    """Immutable snapshot of a dashboard at a point in time."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    dashboard_id: uuid.UUID
    version: int
    snapshot: Dict[str, Any]
    changed_by: uuid.UUID
    changed_at: datetime = field(default_factory=datetime.utcnow)
    change_type: ChangeType
    change_summary: str


@dataclass(frozen=True, kw_only=True)
class ReportVersion:
    """Immutable snapshot of a report at a point in time."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    report_id: uuid.UUID
    version: int
    snapshot: Dict[str, Any]
    changed_by: uuid.UUID
    changed_at: datetime = field(default_factory=datetime.utcnow)
    change_type: ChangeType
    change_summary: str


# ============================================================
# CERTIFICATION ENTITIES
# ============================================================

@dataclass(kw_only=True)
class CertifiedMetric:
    """Tracks certification lifecycle of an analytics metric."""
    metric_id: uuid.UUID
    certification_status: CertificationStatus = CertificationStatus.DRAFT
    certified_by: Optional[uuid.UUID] = None
    certified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    certification_criteria: List[str] = field(default_factory=list)
    review_frequency_days: int = 90

    def is_certified(self) -> bool:
        return self.certification_status == CertificationStatus.CERTIFIED

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def certify(self, certified_by: uuid.UUID, expires_at: Optional[datetime] = None) -> None:
        self.certification_status = CertificationStatus.CERTIFIED
        self.certified_by = certified_by
        self.certified_at = datetime.utcnow()
        if expires_at:
            self.expires_at = expires_at

    def expire(self) -> None:
        self.certification_status = CertificationStatus.EXPIRED

    def submit_for_review(self) -> None:
        self.certification_status = CertificationStatus.IN_REVIEW

    def reset_to_draft(self) -> None:
        self.certification_status = CertificationStatus.DRAFT
        self.certified_by = None
        self.certified_at = None


@dataclass(kw_only=True)
class CertifiedReport:
    """Tracks certification lifecycle of an analytics report."""
    report_id: uuid.UUID
    certification_status: CertificationStatus = CertificationStatus.DRAFT
    certified_by: Optional[uuid.UUID] = None
    certified_at: Optional[datetime] = None
    audit_trail: List[AuditEntry] = field(default_factory=list)

    def is_certified(self) -> bool:
        return self.certification_status == CertificationStatus.CERTIFIED

    def certify(self, certified_by: uuid.UUID) -> None:
        self.certification_status = CertificationStatus.CERTIFIED
        self.certified_by = certified_by
        self.certified_at = datetime.utcnow()
        self._add_audit("CERTIFIED", certified_by)

    def expire(self) -> None:
        self.certification_status = CertificationStatus.EXPIRED

    def submit_for_review(self) -> None:
        self.certification_status = CertificationStatus.IN_REVIEW

    def reset_to_draft(self) -> None:
        self.certification_status = CertificationStatus.DRAFT
        self.certified_by = None
        self.certified_at = None

    def _add_audit(self, action: str, performed_by: uuid.UUID, details: Optional[str] = None) -> None:
        self.audit_trail.append(
            AuditEntry(
                action=action,
                performed_by=performed_by,
                performed_at=datetime.utcnow(),
                details=details,
            )
        )

    def add_audit_entry(self, action: str, performed_by: uuid.UUID, details: Optional[str] = None) -> None:
        self._add_audit(action, performed_by, details)


# ============================================================
# APPROVAL WORKFLOW
# ============================================================

@dataclass(kw_only=True)
class ApprovalWorkflow:
    """Manages multi-approver workflows for dashboards, reports, and metrics."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    target_type: ApprovalTarget
    target_id: uuid.UUID
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_by: uuid.UUID
    requested_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    approver_ids: List[uuid.UUID] = field(default_factory=list)
    approval_policy: ApprovalPolicy = ApprovalPolicy.ANY_ONE

    def approve(self, reviewer: uuid.UUID, note: Optional[str] = None) -> None:
        if self.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot approve workflow in {self.status.value} status")
        if reviewer not in self.approver_ids:
            raise PermissionError("Reviewer is not an authorized approver")
        self.status = ApprovalStatus.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = datetime.utcnow()
        self.review_note = note

    def reject(self, reviewer: uuid.UUID, note: Optional[str] = None) -> None:
        if self.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot reject workflow in {self.status.value} status")
        if reviewer not in self.approver_ids:
            raise PermissionError("Reviewer is not an authorized approver")
        self.status = ApprovalStatus.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = datetime.utcnow()
        self.review_note = note

    def expire(self) -> None:
        if self.status == ApprovalStatus.PENDING:
            self.status = ApprovalStatus.EXPIRED

    def is_pending(self) -> bool:
        return self.status == ApprovalStatus.PENDING

    def is_approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED

    def is_rejected(self) -> bool:
        return self.status == ApprovalStatus.REJECTED

    def is_expired(self) -> bool:
        return self.status == ApprovalStatus.EXPIRED


# ============================================================
# USAGE METRICS
# ============================================================

@dataclass(kw_only=True)
class AnalyticsUsageMetrics:
    """Tracks dashboard usage and staleness for governance insights."""
    dashboard_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    total_views: int = 0
    unique_viewers: int = 0
    avg_session_duration_seconds: float = 0.0
    export_counts: Dict[str, int] = field(default_factory=dict)
    shared_count: int = 0
    last_viewed_at: Optional[datetime] = None
    staleness_score: float = 0.0

    def compute_staleness(self, reference_date: Optional[datetime] = None) -> float:
        """Compute staleness score: 0.0 = fresh, 1.0 = completely stale."""
        if self.last_viewed_at is None:
            return 1.0
        ref = reference_date or datetime.utcnow()
        days_since_view = (ref - self.last_viewed_at).days
        if days_since_view <= 1:
            return 0.0
        if days_since_view >= 90:
            return 1.0
        return days_since_view / 90.0

    def total_exports(self) -> int:
        return sum(self.export_counts.values())

    def viewer_ratio(self) -> float:
        if self.total_views == 0:
            return 0.0
        return self.unique_viewers / self.total_views

    def is_stale(self, threshold: float = 0.7) -> bool:
        return self.staleness_score >= threshold
