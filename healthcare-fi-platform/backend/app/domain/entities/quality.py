"""
QualityRule and QualityIssue entities for the Data Quality Platform.
Every quality issue is actionable with recommended remediation.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from app.domain.entities.base import TenantAwareEntity


class QualityRuleType(str, Enum):
    # Completeness
    NOT_NULL = "not_null"
    COMPLETENESS_THRESHOLD = "completeness_threshold"
    
    # Uniqueness
    UNIQUE = "unique"
    DUPLICATE_DETECTION = "duplicate_detection"
    
    # Validity
    TYPE_CHECK = "type_check"
    RANGE_CHECK = "range_check"
    PATTERN_MATCH = "pattern_match"
    ENUM_VALUES = "enum_values"
    CROSS_FIELD_VALIDATION = "cross_field_validation"
    
    # Freshness
    FRESHNESS_THRESHOLD = "freshness_threshold"
    STALENESS_DETECTION = "staleness_detection"
    
    # Consistency
    REFERENTIAL_INTEGRITY = "referential_integrity"
    CROSS_TABLE_CONSISTENCY = "cross_table_consistency"
    TEMPORAL_CONSISTENCY = "temporal_consistency"
    
    # Business Rules
    SUM_CHECK = "sum_check"
    BALANCE_CHECK = "balance_check"
    OUTLIER_DETECTION = "outlier_detection"
    TREND_ANOMALY = "trend_anomaly"
    DISTRIBUTION_SHIFT = "distribution_shift"


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class QualityScope(str, Enum):
    TABLE = "table"
    COLUMN = "column"
    CROSS_TABLE = "cross_table"


class ScopeType(str, Enum):
    TENANT = "tenant"
    HOSPITAL = "hospital"
    BRANCH = "branch"
    DEPARTMENT = "department"
    TABLE = "table"


class PeriodType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass(kw_only=True)
class QualityRule(TenantAwareEntity):
    """
    A validation rule that checks data for a specific quality property.
    """
    name: str  # "revenue.amount_not_negative"
    description: str = ""
    entity_type: str = ""  # "revenue", "expense", "claim"
    rule_type: QualityRuleType = QualityRuleType.NOT_NULL
    
    # Configuration
    configuration: Dict[str, Any] = field(default_factory=dict)
    severity: IssueSeverity = IssueSeverity.MEDIUM
    scope: QualityScope = QualityScope.COLUMN
    
    # Status
    is_active: bool = True
    alert_on_failure: bool = True
    alert_channels: List[str] = field(default_factory=lambda: ["dashboard"])
    
    # Thresholds
    threshold: Optional[float] = None
    sample_size: Optional[int] = None
    
    # Scope filtering
    applies_to_hospital_id: Optional[uuid.UUID] = None
    applies_to_branch_id: Optional[uuid.UUID] = None
    applies_to_period: Optional[str] = None  # "monthly", "weekly", None=all
    
    def validate(self, value: Any) -> bool:
        """Validate a value against this rule."""
        if self.rule_type == QualityRuleType.NOT_NULL:
            return value is not None
        elif self.rule_type == QualityRuleType.RANGE_CHECK:
            min_val = self.configuration.get("min")
            max_val = self.configuration.get("max")
            if min_val is not None and value < min_val:
                return False
            if max_val is not None and value > max_val:
                return False
            return True
        elif self.rule_type == QualityRuleType.ENUM_VALUES:
            allowed = self.configuration.get("allowed_values", [])
            return value in allowed
        # Add more rule types as needed
        return True


@dataclass(kw_only=True)
class QualityIssue(TenantAwareEntity):
    """
    A detected violation of a QualityRule.
    Every issue is actionable with recommended remediation.
    """
    # Issue identification
    rule_id: uuid.UUID
    rule_name: str = ""  # Denormalized for readability
    
    # Severity and status
    severity: IssueSeverity = IssueSeverity.MEDIUM
    status: IssueStatus = IssueStatus.OPEN
    priority: int = 3  # 1-5, for sorting
    
    # Context
    entity_type: str = ""
    entity_id: Optional[uuid.UUID] = None
    field_name: Optional[str] = None
    hospital_id: Optional[uuid.UUID] = None
    branch_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    
    # Issue details
    issue_code: str = ""  # "DQ-001" (human-readable code)
    title: str = ""
    description: str = ""
    detected_value: Any = None
    expected_value: Any = None
    deviation: Optional[float] = None
    z_score: Optional[float] = None
    
    # Time context
    detected_at: datetime = field(default_factory=datetime.utcnow)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    # Resolution
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None
    
    # Recommendation
    recommended_action: str = ""
    estimated_effort: str = ""  # "5 minutes", "2 hours", "1 week"
    
    # Audit trail
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    def acknowledge(self, acknowledged_by: uuid.UUID) -> None:
        """Acknowledge this issue."""
        self.status = IssueStatus.ACKNOWLEDGED
        self.history.append({
            "action": "acknowledged",
            "by": str(acknowledged_by),
            "at": datetime.utcnow().isoformat()
        })
        self.update_version(acknowledged_by)
    
    def resolve(self, resolved_by: uuid.UUID, notes: str = "") -> None:
        """Resolve this issue."""
        self.status = IssueStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolved_by
        self.resolution_notes = notes
        self.history.append({
            "action": "resolved",
            "by": str(resolved_by),
            "at": datetime.utcnow().isoformat(),
            "notes": notes
        })
        self.update_version(resolved_by)
    
    def ignore(self, ignored_by: uuid.UUID, reason: str = "") -> None:
        """Ignore this issue."""
        self.status = IssueStatus.IGNORED
        self.history.append({
            "action": "ignored",
            "by": str(ignored_by),
            "at": datetime.utcnow().isoformat(),
            "reason": reason
        })
        self.update_version(ignored_by)


@dataclass(kw_only=True)
class DataQualityScore(TenantAwareEntity):
    """
    A composite quality score for a given scope and time period.
    """
    # Scope
    scope_type: ScopeType = ScopeType.TENANT
    scope_id: Optional[uuid.UUID] = None
    
    # Time
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    period_type: PeriodType = PeriodType.MONTHLY
    
    # Scores (all 0.0-1.0)
    overall_score: float = 0.0
    completeness_score: float = 0.0
    validity_score: float = 0.0
    consistency_score: float = 0.0
    timeliness_score: float = 0.0
    uniqueness_score: float = 0.0
    
    # Issue counts by severity
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    info_issues: int = 0
    
    # Trend
    previous_score: Optional[float] = None
    score_change: Optional[float] = None
    score_change_percent: Optional[float] = None
    
    # Audit
    computed_at: datetime = field(default_factory=datetime.utcnow)
    
    def compute_overall_score(self) -> None:
        """Compute overall score as weighted average of component scores."""
        weights = {
            "completeness": 0.25,
            "validity": 0.25,
            "consistency": 0.20,
            "timeliness": 0.15,
            "uniqueness": 0.15
        }
        
        self.overall_score = (
            self.completeness_score * weights["completeness"] +
            self.validity_score * weights["validity"] +
            self.consistency_score * weights["consistency"] +
            self.timeliness_score * weights["timeliness"] +
            self.uniqueness_score * weights["uniqueness"]
        )
        
        # Compute trend
        if self.previous_score is not None:
            self.score_change = self.overall_score - self.previous_score
            if self.previous_score != 0:
                self.score_change_percent = (self.score_change / self.previous_score) * 100
