"""
DomainEvent base class and event catalog for the Event Architecture.
Events are immutable records of something that happened in the domain.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, fields
from enum import Enum


class ActorType(str, Enum):
    USER = "user"
    SYSTEM = "system"
    SCHEDULER = "scheduler"
    IMPORT = "import"


@dataclass(kw_only=True)
class DomainEvent:
    """
    Base class for all domain events.
    Every event is immutable once published.
    """
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    tenant_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    
    # Event taxonomy
    event_type: str = ""
    event_version: str = "1.0"
    
    # Causality
    correlation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    causation_id: Optional[uuid.UUID] = None
    
    # Actor
    initiated_by: Optional[uuid.UUID] = None
    initiated_by_type: ActorType = ActorType.SYSTEM
    
    # Scope
    hospital_id: Optional[uuid.UUID] = None
    branch_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    
    # Payload
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================
# REVENUE EVENTS
# ============================

@dataclass(kw_only=True)
class RevenueRecorded(DomainEvent):
    event_type: str = "RevenueRecorded"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "RevenueRecorded"
        self.payload = kwargs.get("payload", {
            "revenue_id": kwargs.get("revenue_id"),
            "branch_id": kwargs.get("branch_id"),
            "department_id": kwargs.get("department_id"),
            "payer_id": kwargs.get("payer_id"),
            "doctor_id": kwargs.get("doctor_id"),
            "amount": kwargs.get("amount"),
            "net_amount": kwargs.get("net_amount"),
            "service_date": kwargs.get("service_date"),
            "period_id": kwargs.get("period_id"),
            "record_version": kwargs.get("record_version")
        })


@dataclass(kw_only=True)
class RevenueAmended(DomainEvent):
    event_type: str = "RevenueAmended"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "RevenueAmended"
        self.payload = kwargs.get("payload", {
            "revenue_id": kwargs.get("revenue_id"),
            "previous_amount": kwargs.get("previous_amount"),
            "new_amount": kwargs.get("new_amount"),
            "amendment_reason": kwargs.get("amendment_reason"),
            "amended_by": kwargs.get("amended_by")
        })


# ============================
# EXPENSE EVENTS
# ============================

@dataclass(kw_only=True)
class ExpenseRecorded(DomainEvent):
    event_type: str = "ExpenseRecorded"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "ExpenseRecorded"
        self.payload = kwargs.get("payload", {
            "expense_id": kwargs.get("expense_id"),
            "branch_id": kwargs.get("branch_id"),
            "department_id": kwargs.get("department_id"),
            "category": kwargs.get("category"),
            "amount": kwargs.get("amount"),
            "expense_date": kwargs.get("expense_date"),
            "period_id": kwargs.get("period_id"),
            "record_version": kwargs.get("record_version")
        })


# ============================
# CLAIMS EVENTS
# ============================

@dataclass(kw_only=True)
class ClaimCreated(DomainEvent):
    event_type: str = "ClaimCreated"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "ClaimCreated"
        self.payload = kwargs.get("payload", {
            "claim_id": kwargs.get("claim_id"),
            "claim_number": kwargs.get("claim_number"),
            "branch_id": kwargs.get("branch_id"),
            "department_id": kwargs.get("department_id"),
            "payer_id": kwargs.get("payer_id"),
            "total_amount": kwargs.get("total_amount"),
            "submitted_date": kwargs.get("submitted_date")
        })


@dataclass(kw_only=True)
class ClaimApproved(DomainEvent):
    event_type: str = "ClaimApproved"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "ClaimApproved"
        self.payload = kwargs.get("payload", {
            "claim_id": kwargs.get("claim_id"),
            "approved_amount": kwargs.get("approved_amount"),
            "approval_date": kwargs.get("approval_date"),
            "approval_lead_time_days": kwargs.get("approval_lead_time_days")
        })


@dataclass(kw_only=True)
class ClaimDenied(DomainEvent):
    event_type: str = "ClaimDenied"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "ClaimDenied"
        self.payload = kwargs.get("payload", {
            "claim_id": kwargs.get("claim_id"),
            "denial_reason": kwargs.get("denial_reason"),
            "denial_date": kwargs.get("denial_date")
        })


# ============================
# KPI / METRIC EVENTS
# ============================

@dataclass(kw_only=True)
class MetricDefinitionCreated(DomainEvent):
    event_type: str = "MetricDefinitionCreated"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "MetricDefinitionCreated"
        self.payload = kwargs.get("payload", {
            "metric_id": kwargs.get("metric_id"),
            "metric_code": kwargs.get("metric_code"),
            "metric_name": kwargs.get("metric_name"),
            "category": kwargs.get("category"),
            "version": kwargs.get("version")
        })


@dataclass(kw_only=True)
class MetricDefinitionPublished(DomainEvent):
    event_type: str = "MetricDefinitionPublished"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "MetricDefinitionPublished"
        self.payload = kwargs.get("payload", {
            "metric_id": kwargs.get("metric_id"),
            "version": kwargs.get("version"),
            "published_by": kwargs.get("published_by")
        })


@dataclass(kw_only=True)
class MetricComputed(DomainEvent):
    event_type: str = "MetricComputed"
    
    def __init__(self, **kwargs):
        domain_fields = {f.name for f in fields(DomainEvent)}
        filtered = {k: v for k, v in kwargs.items() if k in domain_fields}
        super().__init__(**filtered)
        self.event_type = "MetricComputed"
        self.payload = kwargs.get("payload", {
            "computed_value_id": kwargs.get("computed_value_id"),
            "metric_id": kwargs.get("metric_id"),
            "metric_version": kwargs.get("metric_version"),
            "value": kwargs.get("value"),
            "unit": kwargs.get("unit"),
            "period_start": kwargs.get("period_start"),
            "period_end": kwargs.get("period_end"),
            "confidence_score": kwargs.get("confidence_score"),
            "quality_score": kwargs.get("quality_score"),
            "scope": kwargs.get("scope")
        })


@dataclass(kw_only=True)
class MetricThresholdBreached(DomainEvent):
    event_type: str = "MetricThresholdBreached"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "MetricThresholdBreached"
        self.event_type = "MetricComputed"
        self.payload = kwargs.get("payload", {
            "value": kwargs.get("value"),
            "threshold": kwargs.get("threshold"),
            "breach_type": kwargs.get("breach_type")  # "above_max", "below_min", "below_target"
        })


# ============================
# DATA QUALITY EVENTS
# ============================

@dataclass(kw_only=True)
class QualityIssueDetected(DomainEvent):
    event_type: str = "QualityIssueDetected"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "QualityIssueDetected"
        self.payload = kwargs.get("payload", {
            "issue_id": kwargs.get("issue_id"),
            "rule_id": kwargs.get("rule_id"),
            "rule_name": kwargs.get("rule_name"),
            "severity": kwargs.get("severity"),
            "entity_type": kwargs.get("entity_type"),
            "entity_id": kwargs.get("entity_id"),
            "field_name": kwargs.get("field_name"),
            "detected_value": kwargs.get("detected_value"),
            "expected_value": kwargs.get("expected_value"),
            "recommended_action": kwargs.get("recommended_action")
        })


@dataclass(kw_only=True)
class QualityIssueResolved(DomainEvent):
    event_type: str = "QualityIssueResolved"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "QualityIssueResolved"
        self.payload = kwargs.get("payload", {
            "issue_id": kwargs.get("issue_id"),
            "resolved_by": kwargs.get("resolved_by"),
            "resolution_notes": kwargs.get("resolution_notes")
        })


# ============================
# IMPORT EVENTS
# ============================

@dataclass(kw_only=True)
class DataImportStarted(DomainEvent):
    event_type: str = "DataImportStarted"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "DataImportStarted"
        self.payload = kwargs.get("payload", {
            "import_id": kwargs.get("import_id"),
            "import_type": kwargs.get("import_type"),
            "source_system": kwargs.get("source_system"),
            "record_count": kwargs.get("record_count"),
            "file_name": kwargs.get("file_name"),
            "initiated_by": kwargs.get("initiated_by")
        })


@dataclass(kw_only=True)
class DataImportCompleted(DomainEvent):
    event_type: str = "DataImportCompleted"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "DataImportCompleted"
        self.payload = kwargs.get("payload", {
            "import_id": kwargs.get("import_id"),
            "records_processed": kwargs.get("records_processed"),
            "records_succeeded": kwargs.get("records_succeeded"),
            "records_failed": kwargs.get("records_failed"),
            "duration_ms": kwargs.get("duration_ms"),
            "quality_score": kwargs.get("quality_score")
        })


@dataclass(kw_only=True)
class DataImportFailed(DomainEvent):
    event_type: str = "DataImportFailed"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "DataImportFailed"
        self.payload = kwargs.get("payload", {
            "import_id": kwargs.get("import_id"),
            "error_code": kwargs.get("error_code"),
            "error_message": kwargs.get("error_message"),
            "failed_at_step": kwargs.get("failed_at_step"),
            "partial_records_processed": kwargs.get("partial_records_processed")
        })


# ============================
# WORKFLOW EVENTS
# ============================

@dataclass(kw_only=True)
class WorkflowStarted(DomainEvent):
    event_type: str = "WorkflowStarted"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "WorkflowStarted"
        self.payload = kwargs.get("payload", {
            "workflow_id": kwargs.get("workflow_id"),
            "workflow_type": kwargs.get("workflow_type"),
            "workflow_name": kwargs.get("workflow_name"),
            "triggered_by": kwargs.get("triggered_by"),
            "trigger_type": kwargs.get("trigger_type")
        })


@dataclass(kw_only=True)
class WorkflowCompleted(DomainEvent):
    event_type: str = "WorkflowCompleted"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "WorkflowCompleted"
        self.payload = kwargs.get("payload", {
            "workflow_id": kwargs.get("workflow_id"),
            "duration_ms": kwargs.get("duration_ms"),
            "steps_completed": kwargs.get("steps_completed"),
            "output": kwargs.get("output")
        })


@dataclass(kw_only=True)
class WorkflowFailed(DomainEvent):
    event_type: str = "WorkflowFailed"
    
    def __init__(self, **kwargs):
        _df = {f.name for f in fields(DomainEvent)}
        super().__init__(**{k: v for k, v in kwargs.items() if k in _df})
        self.event_type = "WorkflowFailed"
        self.payload = kwargs.get("payload", {
            "workflow_id": kwargs.get("workflow_id"),
            "failed_at_step": kwargs.get("failed_at_step"),
            "error_code": kwargs.get("error_code"),
            "error_message": kwargs.get("error_message"),
            "retry_count": kwargs.get("retry_count")
        })


# Event catalog for reference
EVENT_CATALOG = {
    "RevenueRecorded": RevenueRecorded,
    "RevenueAmended": RevenueAmended,
    "ExpenseRecorded": ExpenseRecorded,
    "ClaimCreated": ClaimCreated,
    "ClaimApproved": ClaimApproved,
    "ClaimDenied": ClaimDenied,
    "MetricDefinitionCreated": MetricDefinitionCreated,
    "MetricDefinitionPublished": MetricDefinitionPublished,
    "MetricComputed": MetricComputed,
    "MetricThresholdBreached": MetricThresholdBreached,
    "QualityIssueDetected": QualityIssueDetected,
    "QualityIssueResolved": QualityIssueResolved,
    "DataImportStarted": DataImportStarted,
    "DataImportCompleted": DataImportCompleted,
    "DataImportFailed": DataImportFailed,
    "WorkflowStarted": WorkflowStarted,
    "WorkflowCompleted": WorkflowCompleted,
    "WorkflowFailed": WorkflowFailed,
}
