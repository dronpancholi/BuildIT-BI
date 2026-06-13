"""
Domain entities for the Healthcare Financial Intelligence Platform.
"""
from app.domain.entities.base import (
    TenantAwareEntity,
    BaseEntity,
    EntityID,
    TenantID,
    UserID,
    PeriodStart,
    PeriodEnd
)

from app.domain.entities.tenant import (
    Tenant,
    HospitalGroup,
    Hospital,
    Branch,
    Department,
    User,
    Payer,
    Doctor,
    TenantPlan
)

from app.domain.entities.metric import (
    MetricDefinition,
    MetricComputedValue,
    MetricCategory,
    MetricUnit,
    AggregationType,
    MetricStatus,
    TrustLevel,
    PeriodType,
    TrendDirection,
    TransformationStep,
    ValidationRule
)

from app.domain.entities.quality import (
    QualityRule,
    QualityIssue,
    DataQualityScore,
    QualityRuleType,
    IssueSeverity,
    IssueStatus,
    QualityScope,
    ScopeType
)

from app.domain.entities.lineage import (
    LineageNode,
    LineageEdge,
    LineageComputationRecord,
    LineageGraph,
    LineageNodeType,
    LineageEdgeType
)

from app.domain.entities.events import (
    DomainEvent,
    ActorType,
    RevenueRecorded,
    RevenueAmended,
    ExpenseRecorded,
    ClaimCreated,
    ClaimApproved,
    ClaimDenied,
    MetricDefinitionCreated,
    MetricDefinitionPublished,
    MetricComputed,
    MetricThresholdBreached,
    QualityIssueDetected,
    QualityIssueResolved,
    DataImportStarted,
    DataImportCompleted,
    DataImportFailed,
    WorkflowStarted,
    WorkflowCompleted,
    WorkflowFailed,
    EVENT_CATALOG
)

__all__ = [
    # Base
    "TenantAwareEntity",
    "BaseEntity",
    "EntityID",
    "TenantID",
    "UserID",
    "PeriodStart",
    "PeriodEnd",
    
    # Tenant
    "Tenant",
    "HospitalGroup",
    "Hospital",
    "Branch",
    "Department",
    "User",
    "Payer",
    "Doctor",
    "TenantPlan",
    
    # Metric
    "MetricDefinition",
    "MetricComputedValue",
    "MetricCategory",
    "MetricUnit",
    "AggregationType",
    "MetricStatus",
    "TrustLevel",
    "PeriodType",
    "TrendDirection",
    "TransformationStep",
    "ValidationRule",
    
    # Quality
    "QualityRule",
    "QualityIssue",
    "DataQualityScore",
    "QualityRuleType",
    "IssueSeverity",
    "IssueStatus",
    "QualityScope",
    "ScopeType",
    
    # Lineage
    "LineageNode",
    "LineageEdge",
    "LineageComputationRecord",
    "LineageGraph",
    "LineageNodeType",
    "LineageEdgeType",
    
    # Events
    "DomainEvent",
    "ActorType",
    "RevenueRecorded",
    "RevenueAmended",
    "ExpenseRecorded",
    "ClaimCreated",
    "ClaimApproved",
    "ClaimDenied",
    "MetricDefinitionCreated",
    "MetricDefinitionPublished",
    "MetricComputed",
    "MetricThresholdBreached",
    "QualityIssueDetected",
    "QualityIssueResolved",
    "DataImportStarted",
    "DataImportCompleted",
    "DataImportFailed",
    "WorkflowStarted",
    "WorkflowCompleted",
    "WorkflowFailed",
    "EVENT_CATALOG"
]
