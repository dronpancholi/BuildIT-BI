"""
Decision Domain Value Objects.
All enums, value objects, and immutable data structures for the Decision domain.
"""
import uuid
from enum import Enum, StrEnum
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any


# ============================================================
# DECISION STATUS LIFECYCLE
# ============================================================

class DecisionStatus(StrEnum):
    PROPOSED = "proposed"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MEASURED = "measured"
    ARCHIVED = "archived"


class DecisionType(StrEnum):
    EXPANSION = "expansion"
    COST_REDUCTION = "cost_reduction"
    PROCESS_CHANGE = "process_change"
    RESOURCE_ALLOCATION = "resource_allocation"
    POLICY_CHANGE = "policy_change"
    STRATEGIC = "strategic"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    TECHNOLOGY_ADOPTION = "technology_adoption"
    PARTNERSHIP = "partnership"
    MERGER_ACQUISITION = "merger_acquisition"


class DecisionCategory(StrEnum):
    REVENUE = "revenue"
    COST = "cost"
    QUALITY = "quality"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"
    REGULATORY = "regulatory"
    PATIENT_SAFETY = "patient_safety"
    WORKFORCE = "workforce"


class TriggerType(StrEnum):
    INSIGHT = "insight"
    ANOMALY = "anomaly"
    RECOMMENDATION = "recommendation"
    OPPORTUNITY = "opportunity"
    MANUAL = "manual"
    SCHEDULED_REVIEW = "scheduled_review"
    EXECUTIVE_REQUEST = "executive_request"
    PATIENT_OUTCOME = "patient_outcome"
    REGULATORY_CHANGE = "regulatory_change"
    COMPETITOR_ACTION = "competitor_action"


class OutcomeStatus(StrEnum):
    ON_TRACK = "on_track"
    AHEAD = "ahead"
    BEHIND = "behind"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    DEFER = "defer"
    ABSTAIN = "abstain"


class ReviewType(StrEnum):
    INITIAL_REVIEW = "initial_review"
    RE_REVIEW = "re_review"
    FINAL_APPROVAL = "final_approval"
    URGENT_APPROVAL = "urgent_approval"
    PRE_IMPLEMENTATION = "pre_implementation"
    POST_MORTEM = "post_mortem"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED_FOR_REVISION = "returned_for_revision"
    EXPIRED = "expired"


class TimelineEventType(StrEnum):
    CREATED = "created"
    SUBMITTED_FOR_REVIEW = "submitted_for_review"
    REVIEW_STARTED = "review_started"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"
    IMPLEMENTATION_STARTED = "implementation_started"
    IMPLEMENTATION_COMPLETED = "implementation_completed"
    OUTCOME_MEASURED = "outcome_measured"
    ARCHIVED = "archived"
    EDITED = "edited"
    COMMENT_ADDED = "comment_added"
    EVIDENCE_ADDED = "evidence_added"


# ============================================================
# EVIDENCE TYPES
# ============================================================

class EvidenceType(StrEnum):
    INSIGHT = "insight"
    ANOMALY_DATA = "anomaly_data"
    HISTORICAL_TREND = "historical_trend"
    BENCHMARK = "benchmark"
    FINANCIAL_MODEL = "financial_model"
    REGULATORY = "regulatory"
    EXPERT_OPINION = "expert_opinion"
    PATIENT_FEEDBACK = "patient_feedback"
    COMPETITOR_ANALYSIS = "competitor_analysis"


class SourceType(StrEnum):
    INSIGHT = "insight"
    ANOMALY = "anomaly"
    RECOMMENDATION = "recommendation"
    MANUAL_UPLOAD = "manual_upload"
    EXTERNAL_API = "external_api"
    USER_INPUT = "user_input"


# ============================================================
# SHARED ENUMS (reuse from intelligence where possible)
# ============================================================

class PriorityLabel(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class UrgencyLabel(StrEnum):
    IMMEDIATE = "immediate"
    SOON = "soon"
    SCHEDULED = "scheduled"
    BACKLOG = "backlog"


class ScopeType(StrEnum):
    TENANT = "tenant"
    HOSPITAL = "hospital"
    BRANCH = "branch"
    DEPARTMENT = "department"
    SYSTEM = "system"


class Currency(str, Enum):
    INR = "INR"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


# ============================================================
# MEASUREMENT TYPES
# ============================================================

class MeasurementFrequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class AggregationMethod(StrEnum):
    AVG = "avg"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    LAST = "last"


class Direction(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    STABLE = "stable"


class CheckpointType(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    FINAL = "final"


class MeasurementStatus(StrEnum):
    ON_TRACK = "on_track"
    DRIFTING = "drifting"
    CRITICAL = "critical"
    INCONCLUSIVE = "inconclusive"


# ============================================================
# CAUSAL ANALYSIS TYPES
# ============================================================

class CausalMethod(StrEnum):
    BEFORE_AFTER = "before_after"
    CONTROL_GROUP = "control_group"
    ITS = "its"
    SYNTHETIC_CONTROL = "synthetic_control"
    DIFF_IN_DIFF = "diff_in_diff"
    REGRESSION_DISCONTINUITY = "regression_discontinuity"


# ============================================================
# VALUE OBJECTS
# ============================================================

@dataclass(frozen=True)
class OutcomeMetricDefinition:
    """Defines a single metric to track in an outcome."""
    metric_code: str
    baseline_value: float
    target_value: float
    direction: Direction
    min_acceptable_change: Optional[float] = None
    measurement_frequency: MeasurementFrequency = MeasurementFrequency.MONTHLY
    data_source: Optional[str] = None
    aggregation_method: AggregationMethod = AggregationMethod.AVG


@dataclass(frozen=True)
class MeasuredMetric:
    """A single measured value at a checkpoint."""
    metric_code: str
    raw_value: float
    computed_value: float
    change_from_baseline: float
    change_from_previous: float
    is_within_expected_range: bool


@dataclass(frozen=True)
class ConfoundingFactor:
    """A factor that may confound causal analysis."""
    factor: str
    estimated_contribution: float
    is_controlled: bool = False
    notes: Optional[str] = None


@dataclass(frozen=True)
class CausalImpactResult:
    """Result of a causal impact analysis."""
    attribution_weight: float
    confounding_factors: List[ConfoundingFactor]
    confidence_interval_lower: float
    confidence_interval_upper: float
    control_group_comparison: Optional[float] = None
    statistical_significance: Optional[float] = None


@dataclass(frozen=True)
class ReviewComment:
    """A comment on a decision review."""
    comment_id: uuid.UUID
    author_id: uuid.UUID
    author_role: str
    text: str
    created_at: datetime
    edited_at: Optional[datetime] = None
    is_internal: bool = False


@dataclass(frozen=True)
class OutcomeMetric:
    """Metric used in outcome measurement."""
    metric_code: str
    expected_value: Optional[float] = None
    expected_direction: Optional[Direction] = None
    expected_change_percent: Optional[float] = None
    actual_value: Optional[float] = None
    actual_change_percent: Optional[float] = None
    actual_direction: Optional[Direction] = None


@dataclass(frozen=True)
class FeatureGroupServingConfig:
    """Serving configuration for a feature group."""
    serving_mode: str = "on_demand"  # on_demand, cached, pre_computed
    cache_ttl_seconds: int = 300
    preferred_store: str = "redis"  # redis, postgresql, feature_db


@dataclass(frozen=True)
class TrainingConfig:
    """Training configuration for a model."""
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    feature_group_id: Optional[uuid.UUID] = None
    training_data_scope: Optional[str] = None
    training_start_date: Optional[date] = None
    training_end_date: Optional[date] = None
    compute_resource_used: Optional[str] = None


@dataclass(frozen=True)
class ModelMetric:
    """A single model evaluation metric."""
    metric_name: str
    value: float
    threshold: Optional[float] = None
    is_acceptable: bool = True
    benchmark_value: Optional[float] = None


@dataclass(frozen=True)
class ModelDeployment:
    """Deployment record for a model."""
    deployment_id: uuid.UUID
    environment: str  # DEV, STAGING, PROD
    region: Optional[str] = None
    deployed_at: datetime = field(default_factory=datetime.utcnow)
    deployed_by: Optional[uuid.UUID] = None
    active_version: Optional[str] = None
    endpoints: List[str] = field(default_factory=list)
    traffic_split: Optional[Dict[str, float]] = None
    rollback_version: Optional[str] = None


@dataclass(frozen=True)
class ValueRange:
    """Valid range for a feature value."""
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass(frozen=True)
class ComputationScope:
    """Defines the scope for feature computation."""
    scope_type: ScopeType = ScopeType.TENANT
    scope_id: Optional[uuid.UUID] = None
    entity_type: Optional[str] = None
    entity_id: Optional[uuid.UUID] = None
