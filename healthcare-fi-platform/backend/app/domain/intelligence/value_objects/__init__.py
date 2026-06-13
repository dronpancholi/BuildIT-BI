"""
Intelligence Domain Value Objects.
Immutable objects that represent concepts within the intelligence domain.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any


# ============================
# ENUMS
# ============================

class ArtifactType(str, Enum):
    INSIGHT = "insight"
    ROOT_CAUSE = "root_cause"
    ANOMALY = "anomaly"
    OPPORTUNITY = "opportunity"
    RECOMMENDATION = "recommendation"
    BRIEFING = "briefing"


class ArtifactStatus(str, Enum):
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    PUBLISHED = "published"
    DISMISSED = "dismissed"
    ACTIONED = "actioned"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTING = "implementing"
    COMPLETED = "completed"


class ConfidenceLabel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImpactLabel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PriorityLabel(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class UrgencyLabel(str, Enum):
    IMMEDIATE = "immediate"
    SOON = "soon"
    SCHEDULED = "scheduled"
    BACKLOG = "backlog"


class CauseType(str, Enum):
    # Revenue causes
    REVENUE_VOLUME = "revenue_volume"
    REVENUE_MIX = "revenue_mix"
    REVENUE_RATE = "revenue_rate"
    REVENUE_PAYER_MIX = "revenue_payer_mix"
    REVENUE_DEPARTMENT = "revenue_department"
    REVENUE_DOCTOR = "revenue_doctor"
    REVENUE_SEASONAL = "revenue_seasonal"
    REVENUE_TREND = "revenue_trend"

    # Expense causes
    EXPENSE_VOLUME = "expense_volume"
    EXPENSE_RATE = "expense_rate"
    EXPENSE_CATEGORY = "expense_category"
    EXPENSE_DEPARTMENT = "expense_department"
    EXPENSE_LABOR = "expense_labor"
    EXPENSE_SUPPLY = "expense_supply"

    # Claims causes
    CLAIMS_VOLUME = "claims_volume"
    CLAIMS_APPROVAL = "claims_approval"
    CLAIMS_DENIAL = "claims_denial"
    CLAIMS_MIX = "claims_mix"
    CLAIMS_DAYS = "claims_days"

    # Profitability causes
    MARGIN_PRESSURE = "margin_pressure"
    OPERATING_LEVERAGE = "operating_leverage"

    # Quality causes
    QUALITY_ISSUE = "quality_issue"

    # External causes
    EXTERNAL_REGULATORY = "external_regulatory"
    EXTERNAL_MARKET = "external_market"
    EXTERNAL_COMPETITIVE = "external_competitive"


class InsightType(str, Enum):
    # Growth insights
    REVENUE_GROWTH = "revenue_growth"
    REVENUE_DECLINE = "revenue_decline"
    MARGIN_IMPROVEMENT = "margin_improvement"
    MARGIN_DECLINE = "margin_decline"
    COST_REDUCTION = "cost_reduction"
    COST_INCREASE = "cost_increase"

    # Trend insights
    SUSTAINED_TREND = "sustained_trend"
    TREND_REVERSAL = "trend_reversal"
    TREND_ACCELERATION = "trend_acceleration"
    TREND_DECELERATION = "trend_deceleration"

    # Segment insights
    SEGMENT_OUTPERFORMANCE = "segment_outperformance"
    SEGMENT_UNDERPERFORMANCE = "segment_underperformance"
    SEGMENT_SHIFT = "segment_shift"

    # Correlation insights
    CORRELATION_DISCOVERED = "correlation_discovered"
    CORRELATION_BROKEN = "correlation_broken"

    # Anomaly insights
    VALUE_ANOMALY = "value_anomaly"
    PATTERN_ANOMALY = "pattern_anomaly"

    # Operational insights
    CAPACITY_UNDERUTILIZATION = "capacity_underutilization"
    CAPACITY_OVERUTILIZATION = "capacity_overutilization"
    SEASONALITY_DETECTED = "seasonality_detected"

    # Claims insights
    CLAIMS_APPROVAL_IMPROVEMENT = "claims_approval_improvement"
    CLAIMS_APPROVAL_DECLINE = "claims_approval_decline"
    PAYER_SHIFTS = "payer_shifts"


class PatternType(str, Enum):
    TREND = "trend"
    CORRELATION = "correlation"
    CYCLICAL = "cyclical"
    SEGMENT_SHIFT = "segment_shift"
    OUTLIER = "outlier"
    DISTRIBUTION_CHANGE = "distribution_change"
    RELATIONSHIP_CHANGE = "relationship_change"


class DiscoveryMethod(str, Enum):
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    MANUAL = "manual"
    BASELINE_COMPARISON = "baseline_comparison"
    PEER_COMPARISON = "peer_comparison"


class AnomalyType(str, Enum):
    # Value anomalies
    SPIKE = "spike"
    DROP = "drop"
    FLATLINE = "flatline"

    # Pattern anomalies
    SEASONAL_DEVIATION = "seasonal_deviation"
    TREND_DEVIATION = "trend_deviation"
    CYCLICAL_DEVIATION = "cyclical_deviation"

    # Distribution anomalies
    DISTRIBUTION_SHIFT = "distribution_shift"
    OUTLIER_BURST = "outlier_burst"

    # Relationship anomalies
    CORRELATION_BREAK = "correlation_break"
    RATIO_DEVIATION = "ratio_deviation"

    # Quality anomalies
    DATA_QUALITY_ANOMALY = "data_quality_anomaly"
    COMPLETENESS_DROP = "completeness_drop"

    # Timing anomalies
    TIMING_IRREGULARITY = "timing_irregularity"


class DetectionMethod(str, Enum):
    Z_SCORE = "z_score"
    IQR = "iqr"
    EWMA = "ewma"
    CUSUM = "cusum"
    ISOLATION_FOREST = "isolation_forest"
    FORECAST_DEVIATION = "forecast_deviation"
    RULE_BASED = "rule_based"
    CHANGE_POINT = "change_point"


class AnomalySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AnomalyCategory(str, Enum):
    REVENUE = "revenue"
    EXPENSE = "expense"
    CLAIMS = "claims"
    OPERATIONAL = "operational"
    CLINICAL = "clinical"
    QUALITY = "quality"


class AnomalyStatus(str, Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"


class BaselineType(str, Enum):
    HISTORICAL_MEAN = "historical_mean"
    FORECAST = "forecast"
    PEER_BASELINE = "peer_baseline"
    TARGET = "target"
    ROLLING_AVERAGE = "rolling_average"


class OpportunityType(str, Enum):
    # Revenue opportunities
    REVENUE_GROWTH = "revenue_growth"
    SERVICE_EXPANSION = "service_expansion"
    NEW_PAYER_CONTRACT = "new_payer_contract"
    PRICING_OPTIMIZATION = "pricing_optimization"
    MARKET_EXPANSION = "market_expansion"

    # Claims opportunities
    CLAIMS_APPROVAL_IMPROVEMENT = "claims_approval_improvement"
    DENIAL_MANAGEMENT = "denial_management"
    REVENUE_CAPTURE = "revenue_capture"

    # Cost opportunities
    COST_REDUCTION = "cost_reduction"
    LABOR_OPTIMIZATION = "labor_optimization"
    SUPPLY_CHAIN = "supply_chain"
    ENERGY_EFFICIENCY = "energy_efficiency"

    # Efficiency opportunities
    CAPACITY_UTILIZATION = "capacity_utilization"
    THROUGHPUT_IMPROVEMENT = "throughput_improvement"
    PROCESS_AUTOMATION = "process_automation"

    # Profitability
    MARGIN_IMPROVEMENT = "margin_improvement"
    PAYER_MIX_OPTIMIZATION = "payer_mix_optimization"
    SERVICE_MIX_OPTIMIZATION = "service_mix_optimization"


class OpportunityCategory(str, Enum):
    REVENUE = "revenue"
    COST = "cost"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"
    COMPLIANCE = "compliance"


class EffortLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class OpportunityStatus(str, Enum):
    IDENTIFIED = "identified"
    EVALUATING = "evaluating"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    REALIZED = "realized"
    DISMISSED = "dismissed"


class RecommendationType(str, Enum):
    REVENUE_OPTIMIZATION = "revenue_optimization"
    COST_REDUCTION = "cost_reduction"
    PROCESS_IMPROVEMENT = "process_improvement"
    CLAIMS_OPTIMIZATION = "claims_optimization"
    CAPACITY_OPTIMIZATION = "capacity_optimization"
    QUALITY_IMPROVEMENT = "quality_improvement"
    COMPLIANCE = "compliance"
    GROWTH = "growth"


class RecommendationStatus(str, Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTING = "implementing"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


class ImpactDirection(str, Enum):
    INCREASE_REVENUE = "increase_revenue"
    REDUCE_COST = "reduce_cost"
    IMPROVE_QUALITY = "improve_quality"
    IMPROVE_EFFICIENCY = "improve_efficiency"
    REDUCE_RISK = "reduce_risk"


class BriefingType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    AD_HOC = "ad_hoc"


class BriefingStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    FINALIZED = "finalized"
    DISTRIBUTED = "distributed"


class HighlightType(str, Enum):
    WIN = "win"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    ACTION = "action"
    TREND = "trend"


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    CONCERNED = "concerned"
    CRITICAL = "critical"


class NarrativeTone(str, Enum):
    EXECUTIVE = "executive"
    ANALYTICAL = "analytical"
    OPERATIONAL = "operational"
    CLINICAL = "clinical"


class EvidenceType(str, Enum):
    DATA_POINT = "data_point"
    STATISTICAL_TEST = "statistical_test"
    COMPARISON = "comparison"
    REFERENCE = "reference"
    METRIC_VALUE = "metric_value"


class RelationshipType(str, Enum):
    # Causal relationships
    CAUSES = "causes"
    CONTRIBUTES_TO = "contributes_to"
    ENABLES = "enables"

    # Correlation relationships
    CORRELATED_WITH = "correlated_with"
    INVERSELY_CORRELATED_WITH = "inversely_correlated_with"
    TRENDS_WITH = "trends_with"

    # Hierarchical relationships
    PART_OF = "part_of"
    CONTAINS = "contains"
    DRILLS_DOWN_TO = "drills_down_to"

    # Temporal relationships
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    TRIGGERS = "triggers"

    # Supporting relationships
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    RELATED_TO = "related_to"


class IntelligenceNodeType(str, Enum):
    METRIC = "metric"
    INSIGHT = "insight"
    ANOMALY = "anomaly"
    OPPORTUNITY = "opportunity"
    RECOMMENDATION = "recommendation"
    ROOT_CAUSE = "root_cause"
    BRIEFING = "briefing"


class GraphNodeStatus(str, Enum):
    ACTIVE = "active"
    DECAYED = "decayed"
    ARCHIVED = "archived"
    MERGED = "merged"


class RelationshipDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    BOTH = "both"


# ============================
# VALUE OBJECTS
# ============================

@dataclass(frozen=True)
class IntelligenceScores:
    """
    Every intelligence artifact carries the same four scores.
    Enables consistent ranking and prioritization across types.
    """
    confidence: float  # 0.0-1.0 — How reliable is this finding?
    impact: float  # 0.0-1.0 — How significant is this to the business?
    priority: float  # 0.0-1.0 — Composite rank (computed from others)
    urgency: float  # 0.0-1.0 — How time-sensitive is this?

    # Human-readable labels
    confidence_label: ConfidenceLabel
    impact_label: ImpactLabel
    priority_label: PriorityLabel
    urgency_label: UrgencyLabel

    # Raw inputs used to compute scores (for debugging/audit)
    score_inputs: Dict[str, Any] = field(default_factory=dict)
    score_algorithm_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": self.confidence,
            "impact": self.impact,
            "priority": self.priority,
            "urgency": self.urgency,
            "confidence_label": self.confidence_label.value,
            "impact_label": self.impact_label.value,
            "priority_label": self.priority_label.value,
            "urgency_label": self.urgency_label.value,
            "score_inputs": self.score_inputs,
            "score_algorithm_version": self.score_algorithm_version,
        }


@dataclass(frozen=True)
class Evidence:
    """
    A single piece of evidence supporting an intelligence artifact.
    """
    evidence_type: EvidenceType
    title: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    visualization_type: Optional[str] = None
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_type": self.evidence_type.value,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "visualization_type": self.visualization_type,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class CauseEvidence:
    """
    Evidence supporting or contradicting a root cause.
    """
    evidence_type: EvidenceType
    title: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    visualization_type: Optional[str] = None
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_type": self.evidence_type.value,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "visualization_type": self.visualization_type,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class SubFactorBreakdown:
    """
    For hierarchical decomposition (e.g., "Emergency Dept" → "Dr. Smith" → "Cardiac cases")
    """
    factor_name: str
    factor_id: Optional[uuid.UUID]
    previous_value: float
    current_value: float
    change_absolute: float
    attribution_weight: float
    children: Optional[List['SubFactorBreakdown']] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "factor_name": self.factor_name,
            "factor_id": str(self.factor_id) if self.factor_id else None,
            "previous_value": self.previous_value,
            "current_value": self.current_value,
            "change_absolute": self.change_absolute,
            "attribution_weight": self.attribution_weight,
        }
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        return result


@dataclass(frozen=True)
class ValueBreakdown:
    """
    Formal calculation of opportunity value.
    """
    calculation_method: str
    baseline_value: float
    target_value: float
    metric_unit: str
    affected_volume: float
    time_horizon_months: float
    gross_value: float
    risk_adjustment: float
    net_value: float
    benchmark_value: Optional[float] = None
    benchmark_source: Optional[str] = None
    is_calculation_validated: bool = False
    validated_by: Optional[uuid.UUID] = None
    validation_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "calculation_method": self.calculation_method,
            "baseline_value": self.baseline_value,
            "target_value": self.target_value,
            "metric_unit": self.metric_unit,
            "affected_volume": self.affected_volume,
            "time_horizon_months": self.time_horizon_months,
            "gross_value": self.gross_value,
            "risk_adjustment": self.risk_adjustment,
            "net_value": self.net_value,
            "benchmark_value": self.benchmark_value,
            "benchmark_source": self.benchmark_source,
            "is_calculation_validated": self.is_calculation_validated,
            "validated_by": str(self.validated_by) if self.validated_by else None,
            "validation_notes": self.validation_notes,
        }


@dataclass(frozen=True)
class ActionStep:
    """
    A step in a recommendation's implementation plan.
    """
    step_number: int
    action_description: str
    owner_role: Optional[str] = None
    estimated_effort_hours: float = 0
    required_resources: List[str] = field(default_factory=list)
    success_criteria: str = ""
    is_blocker: bool = False
    can_automate: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "action_description": self.action_description,
            "owner_role": self.owner_role,
            "estimated_effort_hours": self.estimated_effort_hours,
            "required_resources": self.required_resources,
            "success_criteria": self.success_criteria,
            "is_blocker": self.is_blocker,
            "can_automate": self.can_automate,
        }


@dataclass(frozen=True)
class EvidenceItem:
    """
    Evidence supporting a recommendation.
    """
    evidence_id: uuid.UUID
    evidence_type: str
    title: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": str(self.evidence_id),
            "evidence_type": self.evidence_type,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class StatisticalTest:
    """
    Result of a statistical test.
    """
    test_name: str
    test_statistic: float
    p_value: float
    p_value_corrected: Optional[float] = None
    confidence_level: float = 0.95
    effect_size: Optional[float] = None
    effect_size_type: Optional[str] = None  # "cohens_d", "eta_squared", etc.
    degrees_of_freedom: Optional[int] = None
    sample_size: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "test_statistic": self.test_statistic,
            "p_value": self.p_value,
            "p_value_corrected": self.p_value_corrected,
            "confidence_level": self.confidence_level,
            "effect_size": self.effect_size,
            "effect_size_type": self.effect_size_type,
            "degrees_of_freedom": self.degrees_of_freedom,
            "sample_size": self.sample_size,
        }


@dataclass(frozen=True)
class PatternDescription:
    """
    Formal description of a detected pattern.
    """
    pattern_type: PatternType
    description: str
    confidence: float
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    magnitude: Optional[float] = None
    direction: Optional[str] = None  # "up", "down", "stable"
    is_sustained: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "description": self.description,
            "confidence": self.confidence,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "magnitude": self.magnitude,
            "direction": self.direction,
            "is_sustained": self.is_sustained,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class BusinessImpact:
    """
    Quantified business impact of an anomaly.
    """
    impact_type: str  # "revenue_loss", "cost_increase", "quality_issue"
    impact_amount: Optional[float] = None
    impact_unit: str = "USD"
    affected_transactions: Optional[int] = None
    affected_scope: Optional[str] = None
    duration_estimate: Optional[str] = None
    is_material: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "impact_type": self.impact_type,
            "impact_amount": self.impact_amount,
            "impact_unit": self.impact_unit,
            "affected_transactions": self.affected_transactions,
            "affected_scope": self.affected_scope,
            "duration_estimate": self.duration_estimate,
            "is_material": self.is_material,
        }


@dataclass(frozen=True)
class ForecastSummary:
    """
    Summary of forecast for briefing.
    """
    narrative: str
    revenue_forecast: float
    revenue_confidence: float
    expense_forecast: float
    expense_confidence: float
    margin_forecast: float
    key_assumptions: List[str] = field(default_factory=list)
    scenario_comparison: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "narrative": self.narrative,
            "revenue_forecast": self.revenue_forecast,
            "revenue_confidence": self.revenue_confidence,
            "expense_forecast": self.expense_forecast,
            "expense_confidence": self.expense_confidence,
            "margin_forecast": self.margin_forecast,
            "key_assumptions": self.key_assumptions,
            "scenario_comparison": self.scenario_comparison,
        }


class PeriodType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ScopeType(str, Enum):
    TENANT = "tenant"
    HOSPITAL = "hospital"
    BRANCH = "branch"
    DEPARTMENT = "department"
    METRIC = "metric"


class GenerationSource(str, Enum):
    SYSTEM = "system"
    SCHEDULED = "scheduled"
    ON_DEMAND = "on_demand"
    EVENT_TRIGGERED = "event_triggered"
    USER_REQUESTED = "user_requested"
