"""
Export Engine Domain — Healthcare Financial Intelligence Platform.
Entities for report export, scheduling, subscriptions, and templates.
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

class ExportFormat(Enum):
    PDF = "PDF"
    EXCEL = "EXCEL"
    CSV = "CSV"
    PNG = "PNG"


class JobStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class ScheduleFrequency(Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    CUSTOM = "CUSTOM"


class SubscriptionTrigger(Enum):
    ON_NEW_DATA = "ON_NEW_DATA"
    ON_THRESHOLD_BREACH = "ON_THRESHOLD_BREACH"
    ON_SCHEDULE = "ON_SCHEDULE"


# ============================================================
# VALUE OBJECTS
# ============================================================

@dataclass(frozen=True, kw_only=True)
class ExportParameters:
    """Configuration parameters for a report export."""
    include_raw_data: bool = True
    include_charts: bool = True
    include_metadata: bool = True
    page_orientation: str = "landscape"
    paper_size: str = "A4"


# ============================================================
# EXPORT JOB
# ============================================================

@dataclass(kw_only=True)
class ExportJob:
    """Represents a report export job with full lifecycle tracking."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    report_id: uuid.UUID
    format: ExportFormat
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    created_by: uuid.UUID
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def start(self) -> None:
        if self.status != JobStatus.PENDING:
            raise ValueError(f"Cannot start job in {self.status.value} status")
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.utcnow()

    def complete(self, file_url: str, expires_at: Optional[datetime] = None) -> None:
        if self.status != JobStatus.PROCESSING:
            raise ValueError(f"Cannot complete job in {self.status.value} status")
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.file_url = file_url
        self.expires_at = expires_at

    def fail(self, error_message: str) -> None:
        if self.status not in (JobStatus.PENDING, JobStatus.PROCESSING):
            raise ValueError(f"Cannot fail job in {self.status.value} status")
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def expire(self) -> None:
        if self.status == JobStatus.PENDING:
            self.status = JobStatus.EXPIRED
            self.completed_at = datetime.utcnow()

    def is_terminal(self) -> bool:
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.EXPIRED)

    def duration_seconds(self) -> Optional[float]:
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


# ============================================================
# SCHEDULE CONFIGURATION
# ============================================================

@dataclass(kw_only=True)
class ScheduleConfig:
    """Defines a recurring export schedule for a report."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    report_id: uuid.UUID
    frequency: ScheduleFrequency
    params: Dict[str, Any] = field(default_factory=dict)
    timezone: str = "UTC"
    recipients: List[Dict[str, Any]] = field(default_factory=list)
    subject_template: str = ""
    body_template: str = ""
    include_attachment: bool = True
    attachment_format: ExportFormat = ExportFormat.PDF
    is_active: bool = True
    last_run_at: Optional[datetime] = None
    next_run_at: datetime = field(default_factory=datetime.utcnow)
    failure_count: int = 0
    failure_alert_recipients: List[Dict[str, Any]] = field(default_factory=list)

    def record_success(self) -> None:
        self.last_run_at = datetime.utcnow()
        self.failure_count = 0
        self._compute_next_run()

    def record_failure(self) -> None:
        self.failure_count += 1
        self._compute_next_run()

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def should_alert(self) -> bool:
        return self.failure_count >= 3 and len(self.failure_alert_recipients) > 0

    def _compute_next_run(self) -> None:
        from datetime import timedelta
        now = datetime.utcnow()
        if self.frequency == ScheduleFrequency.DAILY:
            self.next_run_at = now + timedelta(days=1)
        elif self.frequency == ScheduleFrequency.WEEKLY:
            self.next_run_at = now + timedelta(weeks=1)
        elif self.frequency == ScheduleFrequency.MONTHLY:
            self.next_run_at = now + timedelta(days=30)
        elif self.frequency == ScheduleFrequency.QUARTERLY:
            self.next_run_at = now + timedelta(days=91)
        else:
            self.next_run_at = now + timedelta(days=1)


# ============================================================
# REPORT SUBSCRIPTION
# ============================================================

@dataclass(kw_only=True)
class ReportSubscription:
    """Subscription to a report that triggers on data or threshold events."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    report_id: uuid.UUID
    recipient_id: uuid.UUID
    trigger_type: SubscriptionTrigger
    threshold_config: Optional[Dict[str, Any]] = None
    include_context: bool = True
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def is_threshold_based(self) -> bool:
        return self.trigger_type == SubscriptionTrigger.ON_THRESHOLD_BREACH

    def validate_threshold_config(self) -> bool:
        if not self.is_threshold_based():
            return True
        if self.threshold_config is None:
            return False
        required_keys = {"metric", "operator", "value"}
        return required_keys.issubset(self.threshold_config.keys())


# ============================================================
# EXPORT TEMPLATE
# ============================================================

@dataclass(kw_only=True)
class ExportTemplate:
    """Reusable template for styled report exports."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str
    format: ExportFormat
    template_config: Dict[str, Any] = field(default_factory=dict)
    header_html: Optional[str] = None
    footer_html: Optional[str] = None
    css_override: Optional[str] = None

    def has_branding(self) -> bool:
        return self.header_html is not None or self.footer_html is not None

    def has_custom_styles(self) -> bool:
        return self.css_override is not None

    def merge_config(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(self.template_config)
        merged.update(overrides)
        return merged
