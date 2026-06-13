"""
MetricDefinition and related entities for the Semantic Metrics Layer.
Every metric is a managed, versioned, governed business object.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from app.domain.entities.base import TenantAwareEntity


class MetricCategory(str, Enum):
    REVENUE = "revenue"
    EXPENSE = "expense"
    PROFITABILITY = "profitability"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"
    OCCUPANCY = "occupancy"
    CLAIMS = "claims"
    CASH_FLOW = "cash_flow"
    PATIENT = "patient"
    WORKFORCE = "workforce"


class MetricUnit(str, Enum):
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    COUNT = "count"
    DAYS = "days"
    RATE = "rate"
    RATIO = "ratio"
    INDEX = "index"


class AggregationType(str, Enum):
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    COUNT_DISTINCT = "count_distinct"
    MEDIAN = "median"


class MetricStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class TrustLevel(str, Enum):
    EXPERIMENTAL = "experimental"
    PROVISIONAL = "provisional"
    TRUSTED = "trusted"
    CERTIFIED = "certified"


class PeriodType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


@dataclass(kw_only=True)
class TransformationStep:
    """A single step in a metric transformation pipeline."""
    step_order: int
    step_type: str  # filter, aggregate, join, calculate
    description: str
    sql_fragment: Optional[str] = None
    python_code: Optional[str] = None


@dataclass(kw_only=True)
class ValidationRule:
    """A validation rule for metric values."""
    rule_type: str  # not_null, range, custom
    configuration: Dict[str, Any] = field(default_factory=dict)
    severity: str = "medium"  # critical, high, medium, low


@dataclass(kw_only=True)
class MetricDefinition(TenantAwareEntity):
    """
    The canonical definition of a business metric.
    This is the SINGLE SOURCE OF TRUTH for every KPI in the platform.
    """
    # Identity
    name: str
    slug: str  # Programmatic: "net_revenue" (unique per tenant)
    code: str  # Short code: "NR" (unique per tenant)
    
    # Governance
    owner_id: Optional[uuid.UUID] = None
    category: MetricCategory = MetricCategory.REVENUE
    subcategory: Optional[str] = None
    
    # Definition (immutable once published)
    description: str = ""
    formula: str = ""  # Human-readable: "Gross Revenue - Deductions"
    sql_expression: str = ""  # Production SQL
    python_expression: str = ""  # Equivalent Python for DuckDB
    
    # Metric properties
    unit: MetricUnit = MetricUnit.CURRENCY
    aggregation: AggregationType = AggregationType.SUM
    direction: int = 1  # 1 = higher is better, -1 = lower is better
    
    # Validation
    validation_rules: List[ValidationRule] = field(default_factory=list)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    # Dependencies
    depends_on: List[uuid.UUID] = field(default_factory=list)  # Other MetricDefinition IDs
    
    # Versioning
    status: MetricStatus = MetricStatus.DRAFT
    published_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    deprecation_reason: Optional[str] = None
    
    # Lineage
    source_tables: List[str] = field(default_factory=list)
    source_fields: List[str] = field(default_factory=list)
    transformation_steps: List[TransformationStep] = field(default_factory=list)
    
    # Trust signals
    quality_score: float = 0.0  # 0.0-1.0
    trust_level: TrustLevel = TrustLevel.EXPERIMENTAL
    certified_by: Optional[uuid.UUID] = None
    certified_at: Optional[datetime] = None
    
    def publish(self, published_by: uuid.UUID) -> None:
        """Publish this metric definition."""
        if self.status != MetricStatus.DRAFT:
            raise ValueError(f"Cannot publish metric in {self.status} status")
        self.status = MetricStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self.update_version(published_by)
    
    def deprecate(self, reason: str, deprecated_by: uuid.UUID) -> None:
        """Deprecate this metric definition."""
        if self.status == MetricStatus.ARCHIVED:
            raise ValueError("Cannot deprecate archived metric")
        self.status = MetricStatus.DEPRECATED
        self.deprecated_at = datetime.utcnow()
        self.deprecation_reason = reason
        self.update_version(deprecated_by)
    
    def certify(self, certified_by: uuid.UUID) -> None:
        """Certify this metric for audit readiness."""
        if self.status != MetricStatus.PUBLISHED:
            raise ValueError("Can only certify published metrics")
        self.trust_level = TrustLevel.CERTIFIED
        self.certified_by = certified_by
        self.certified_at = datetime.utcnow()
        self.update_version(certified_by)
    
    def has_dependency(self, metric_id: uuid.UUID) -> bool:
        """Check if this metric depends on another."""
        return metric_id in self.depends_on


@dataclass(kw_only=True)
class MetricComputedValue(TenantAwareEntity):
    """
    The result of computing a MetricDefinition at a specific time,
    for a specific scope, with a specific time window.
    """
    # Definition reference
    metric_id: uuid.UUID
    metric_version: int
    
    # Computation context
    computed_at: datetime = field(default_factory=datetime.utcnow)
    computed_by: Optional[uuid.UUID] = None
    
    # Scope
    hospital_id: Optional[uuid.UUID] = None
    branch_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    
    # Time window
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    period_type: PeriodType = PeriodType.MONTHLY
    
    # Result
    value: float = 0.0
    unit: MetricUnit = MetricUnit.CURRENCY
    
    # Confidence and quality
    confidence_score: float = 0.0  # 0.0-1.0
    quality_score: float = 0.0  # 0.0-1.0
    sample_size: int = 0
    null_values_excluded: int = 0
    
    # For comparison
    previous_value: Optional[float] = None
    previous_period_start: Optional[datetime] = None
    previous_period_end: Optional[datetime] = None
    change_absolute: Optional[float] = None
    change_percent: Optional[float] = None
    trend: TrendDirection = TrendDirection.STABLE
    
    # Provenance
    computation_duration_ms: int = 0
    cache_hit: bool = False
    source_query_hash: str = ""  # SHA256 of the SQL used
    
    # Lineage snapshot
    lineage_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    def compute_change(self) -> None:
        """Compute change metrics from previous value."""
        if self.previous_value is not None and self.previous_value != 0:
            self.change_absolute = self.value - self.previous_value
            self.change_percent = (self.change_absolute / self.previous_value) * 100
            
            if self.change_percent > 1.0:
                self.trend = TrendDirection.UP
            elif self.change_percent < -1.0:
                self.trend = TrendDirection.DOWN
            else:
                self.trend = TrendDirection.STABLE
