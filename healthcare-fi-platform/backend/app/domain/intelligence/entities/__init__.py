"""
Intelligence Domain Entities.
Base entity and all intelligence artifact implementations.
"""
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any

from app.domain.intelligence.value_objects import (
    ArtifactType,
    ArtifactStatus,
    IntelligenceScores,
    Evidence,
    CauseEvidence,
    SubFactorBreakdown,
    ValueBreakdown,
    ActionStep,
    EvidenceItem,
    StatisticalTest,
    PatternDescription,
    BusinessImpact,
    CauseType,
    InsightType,
    PatternType,
    DiscoveryMethod,
    AnomalyType,
    DetectionMethod,
    AnomalySeverity,
    AnomalyCategory,
    AnomalyStatus,
    BaselineType,
    OpportunityType,
    OpportunityCategory,
    EffortLevel,
    RiskLevel,
    OpportunityStatus,
    RecommendationType,
    RecommendationStatus,
    ImpactDirection,
    BriefingType,
    BriefingStatus,
    HighlightType,
    SentimentLabel,
    NarrativeTone,
    PeriodType,
    ScopeType,
    GenerationSource,
)


@dataclass(kw_only=True)
class IntelligenceArtifact(ABC):
    """
    Abstract base for all intelligence entities.
    Every artifact in the intelligence domain shares this contract.
    """
    id: uuid.UUID
    tenant_id: uuid.UUID

    # Classification
    artifact_type: ArtifactType
    metric_id: Optional[uuid.UUID] = None
    metric_code: Optional[str] = None

    # Temporal context
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    period_type: PeriodType = PeriodType.MONTHLY

    # Scope
    scope_type: ScopeType = ScopeType.TENANT
    scope_id: Optional[uuid.UUID] = None
    scope_name: Optional[str] = None

    # Intelligence scoring
    scores: Optional[IntelligenceScores] = None

    # Evidence chain
    evidence: List[Evidence] = field(default_factory=list)

    # Generation metadata
    generated_by: GenerationSource = GenerationSource.SYSTEM
    generated_by_model: Optional[str] = None
    generation_method: str = "statistical"

    # Status lifecycle
    status: ArtifactStatus = ArtifactStatus.DISCOVERED
    validated_at: Optional[datetime] = None
    validated_by: Optional[uuid.UUID] = None
    published_at: Optional[datetime] = None

    # Audit
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[uuid.UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[uuid.UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None

    def validate(self, user_id: uuid.UUID) -> None:
        """Validate the artifact."""
        self.status = ArtifactStatus.VALIDATED
        self.validated_at = datetime.utcnow()
        self.validated_by = user_id
        self.version += 1
        self.updated_at = datetime.utcnow()

    def publish(self) -> None:
        """Publish the artifact."""
        self.status = ArtifactStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self.version += 1
        self.updated_at = datetime.utcnow()

    def dismiss(self, user_id: uuid.UUID, reason: Optional[str] = None) -> None:
        """Dismiss the artifact."""
        self.status = ArtifactStatus.DISMISSED
        self.updated_at = datetime.utcnow()
        self.updated_by = user_id
        self.version += 1

    def soft_delete(self, user_id: uuid.UUID) -> None:
        """Soft delete the artifact."""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user_id
        self.updated_at = datetime.utcnow()
        self.version += 1

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        pass


@dataclass(kw_only=True)
class Insight(IntelligenceArtifact):
    """
    An insight represents a discovered pattern or finding.
    """
    artifact_type: ArtifactType = ArtifactType.INSIGHT

    # Insight identity
    insight_type: InsightType = InsightType.REVENUE_GROWTH
    title: str = ""
    summary: str = ""
    detailed_analysis: str = ""

    # What was found
    pattern_detected: Optional[PatternDescription] = None
    pattern_type: PatternType = PatternType.TREND
    statistical_properties: Dict[str, Any] = field(default_factory=dict)

    # Statistical validation
    statistical_test: Optional[StatisticalTest] = None
    test_statistic: Optional[float] = None
    p_value: Optional[float] = None
    p_value_corrected: Optional[float] = None
    is_significant: bool = False
    confidence_level: float = 0.0
    effect_size: Optional[float] = None

    # Magnitude
    magnitude: float = 0.0
    magnitude_unit: str = ""
    relative_magnitude: float = 0.0

    # Change tracking
    previous_insight_id: Optional[uuid.UUID] = None
    next_insight_id: Optional[uuid.UUID] = None
    insight_sequence: int = 1

    # Comparison
    comparison_period_start: Optional[datetime] = None
    comparison_period_end: Optional[datetime] = None
    comparison_value: Optional[float] = None
    comparison_change_absolute: Optional[float] = None
    comparison_change_percent: Optional[float] = None

    # Related intelligence
    related_metric_ids: List[uuid.UUID] = field(default_factory=list)
    related_root_cause_ids: List[uuid.UUID] = field(default_factory=list)
    related_anomaly_ids: List[uuid.UUID] = field(default_factory=list)
    related_opportunity_ids: List[uuid.UUID] = field(default_factory=list)
    related_recommendation_ids: List[uuid.UUID] = field(default_factory=list)

    # Discovery context
    discovery_method: DiscoveryMethod = DiscoveryMethod.SCHEDULED
    triggered_by_event: Optional[str] = None

    # Notification
    is_notified: bool = False
    notified_at: Optional[datetime] = None
    notification_channel: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "artifact_type": self.artifact_type.value,
            "insight_type": self.insight_type.value,
            "title": self.title,
            "summary": self.summary,
            "detailed_analysis": self.detailed_analysis,
            "pattern_detected": self.pattern_detected.to_dict() if self.pattern_detected else None,
            "pattern_type": self.pattern_type.value,
            "statistical_properties": self.statistical_properties,
            "statistical_test": self.statistical_test.to_dict() if self.statistical_test else None,
            "test_statistic": self.test_statistic,
            "p_value": self.p_value,
            "p_value_corrected": self.p_value_corrected,
            "is_significant": self.is_significant,
            "confidence_level": self.confidence_level,
            "effect_size": self.effect_size,
            "magnitude": self.magnitude,
            "magnitude_unit": self.magnitude_unit,
            "relative_magnitude": self.relative_magnitude,
            "previous_insight_id": str(self.previous_insight_id) if self.previous_insight_id else None,
            "next_insight_id": str(self.next_insight_id) if self.next_insight_id else None,
            "insight_sequence": self.insight_sequence,
            "comparison_period_start": self.comparison_period_start.isoformat() if self.comparison_period_start else None,
            "comparison_period_end": self.comparison_period_end.isoformat() if self.comparison_period_end else None,
            "comparison_value": self.comparison_value,
            "comparison_change_absolute": self.comparison_change_absolute,
            "comparison_change_percent": self.comparison_change_percent,
            "related_metric_ids": [str(id) for id in self.related_metric_ids],
            "related_root_cause_ids": [str(id) for id in self.related_root_cause_ids],
            "related_anomaly_ids": [str(id) for id in self.related_anomaly_ids],
            "related_opportunity_ids": [str(id) for id in self.related_opportunity_ids],
            "related_recommendation_ids": [str(id) for id in self.related_recommendation_ids],
            "scores": self.scores.to_dict() if self.scores else None,
            "discovery_method": self.discovery_method.value,
            "triggered_by_event": self.triggered_by_event,
            "status": self.status.value,
            "is_notified": self.is_notified,
            "notified_at": self.notified_at.isoformat() if self.notified_at else None,
            "notification_channel": self.notification_channel,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "period_type": self.period_type.value,
            "scope_type": self.scope_type.value,
            "scope_id": str(self.scope_id) if self.scope_id else None,
            "scope_name": self.scope_name,
            "metric_id": str(self.metric_id) if self.metric_id else None,
            "metric_code": self.metric_code,
            "generated_by": self.generated_by.value,
            "generated_by_model": self.generated_by_model,
            "generation_method": self.generation_method,
            "evidence": [e.to_dict() for e in self.evidence],
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None,
        }


@dataclass(kw_only=True)
class RootCause(IntelligenceArtifact):
    """
    Represents a root cause analysis finding.
    """
    artifact_type: ArtifactType = ArtifactType.ROOT_CAUSE

    # Context
    subject_metric_id: Optional[uuid.UUID] = None
    subject_metric_code: Optional[str] = None
    subject_previous_value: float = 0.0
    subject_current_value: float = 0.0
    subject_change_absolute: float = 0.0
    subject_change_percent: float = 0.0

    # Root cause itself
    cause_type: CauseType = CauseType.REVENUE_DEPARTMENT
    cause_category: str = ""
    cause_name: str = ""
    cause_description: str = ""

    # Attribution
    attribution_weight: float = 0.0
    attribution_absolute: float = 0.0
    attribution_percent: float = 0.0
    is_primary_cause: bool = False
    cause_rank: int = 1

    # Statistical basis
    statistical_significance: float = 0.0
    confidence_interval: Optional[tuple] = None
    confidence: float = 0.0

    # Evidence
    cause_evidence: List[CauseEvidence] = field(default_factory=list)

    # Drill-down details
    breakdown: List[SubFactorBreakdown] = field(default_factory=list)

    # Period context
    comparison_period_start: Optional[datetime] = None
    comparison_period_end: Optional[datetime] = None

    # Linked intelligence
    related_insight_id: Optional[uuid.UUID] = None
    related_anomaly_id: Optional[uuid.UUID] = None
    related_recommendation_ids: List[uuid.UUID] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "artifact_type": self.artifact_type.value,
            "subject_metric_id": str(self.subject_metric_id) if self.subject_metric_id else None,
            "subject_metric_code": self.subject_metric_code,
            "subject_previous_value": self.subject_previous_value,
            "subject_current_value": self.subject_current_value,
            "subject_change_absolute": self.subject_change_absolute,
            "subject_change_percent": self.subject_change_percent,
            "cause_type": self.cause_type.value,
            "cause_category": self.cause_category,
            "cause_name": self.cause_name,
            "cause_description": self.cause_description,
            "attribution_weight": self.attribution_weight,
            "attribution_absolute": self.attribution_absolute,
            "attribution_percent": self.attribution_percent,
            "is_primary_cause": self.is_primary_cause,
            "cause_rank": self.cause_rank,
            "statistical_significance": self.statistical_significance,
            "confidence_interval": self.confidence_interval,
            "confidence": self.confidence,
            "cause_evidence": [e.to_dict() for e in self.cause_evidence],
            "breakdown": [b.to_dict() for b in self.breakdown],
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "comparison_period_start": self.comparison_period_start.isoformat() if self.comparison_period_start else None,
            "comparison_period_end": self.comparison_period_end.isoformat() if self.comparison_period_end else None,
            "scope_type": self.scope_type.value,
            "scope_id": str(self.scope_id) if self.scope_id else None,
            "scope_name": self.scope_name,
            "related_insight_id": str(self.related_insight_id) if self.related_insight_id else None,
            "related_anomaly_id": str(self.related_anomaly_id) if self.related_anomaly_id else None,
            "related_recommendation_ids": [str(id) for id in self.related_recommendation_ids],
            "scores": self.scores.to_dict() if self.scores else None,
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(kw_only=True)
class Anomaly(IntelligenceArtifact):
    """
    Represents a detected anomaly.
    """
    artifact_type: ArtifactType = ArtifactType.ANOMALY

    # Anomaly classification
    anomaly_type: AnomalyType = AnomalyType.SPIKE
    category: AnomalyCategory = AnomalyCategory.REVENUE
    severity: AnomalySeverity = AnomalySeverity.MEDIUM

    # What triggered detection
    detection_method: DetectionMethod = DetectionMethod.Z_SCORE
    detection_algorithm: str = "z_score"

    # Context
    title: str = ""
    description: str = ""
    detailed_explanation: str = ""

    # What was observed
    observed_value: float = 0.0
    expected_value: float = 0.0
    deviation_absolute: float = 0.0
    deviation_percent: float = 0.0

    # Statistical properties
    z_score: Optional[float] = None
    p_value: Optional[float] = None
    confidence_interval: Optional[tuple] = None

    # Baseline
    baseline_value: float = 0.0
    baseline_type: BaselineType = BaselineType.HISTORICAL_MEAN
    baseline_period_start: Optional[datetime] = None
    baseline_period_end: Optional[datetime] = None
    baseline_std_dev: Optional[float] = None

    # Root cause link
    root_cause_id: Optional[uuid.UUID] = None
    root_cause_description: Optional[str] = None

    # Business impact
    business_impact: Optional[BusinessImpact] = None
    impact_amount: Optional[float] = None
    affected_transactions: Optional[int] = None
    affected_scope: Optional[str] = None

    # Recommendation link
    recommendation_id: Optional[uuid.UUID] = None
    recommended_action: Optional[str] = None

    # Temporal properties
    anomaly_duration_periods: int = 1
    is_persistent: bool = False

    # Status
    anomaly_status: AnomalyStatus = AnomalyStatus.DETECTED
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None

    # Related intelligence
    related_insight_ids: List[uuid.UUID] = field(default_factory=list)
    related_root_cause_ids: List[uuid.UUID] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "artifact_type": self.artifact_type.value,
            "anomaly_type": self.anomaly_type.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "detection_method": self.detection_method.value,
            "detection_algorithm": self.detection_algorithm,
            "title": self.title,
            "description": self.description,
            "detailed_explanation": self.detailed_explanation,
            "metric_id": str(self.metric_id) if self.metric_id else None,
            "metric_code": self.metric_code,
            "observed_value": self.observed_value,
            "expected_value": self.expected_value,
            "deviation_absolute": self.deviation_absolute,
            "deviation_percent": self.deviation_percent,
            "z_score": self.z_score,
            "p_value": self.p_value,
            "confidence_interval": self.confidence_interval,
            "baseline_value": self.baseline_value,
            "baseline_type": self.baseline_type.value,
            "baseline_period_start": self.baseline_period_start.isoformat() if self.baseline_period_start else None,
            "baseline_period_end": self.baseline_period_end.isoformat() if self.baseline_period_end else None,
            "baseline_std_dev": self.baseline_std_dev,
            "root_cause_id": str(self.root_cause_id) if self.root_cause_id else None,
            "root_cause_description": self.root_cause_description,
            "business_impact": self.business_impact.to_dict() if self.business_impact else None,
            "impact_amount": self.impact_amount,
            "affected_transactions": self.affected_transactions,
            "affected_scope": self.affected_scope,
            "recommendation_id": str(self.recommendation_id) if self.recommendation_id else None,
            "recommended_action": self.recommended_action,
            "anomaly_duration_periods": self.anomaly_duration_periods,
            "is_persistent": self.is_persistent,
            "anomaly_status": self.anomaly_status.value,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": str(self.resolved_by) if self.resolved_by else None,
            "resolution_notes": self.resolution_notes,
            "related_insight_ids": [str(id) for id in self.related_insight_ids],
            "related_root_cause_ids": [str(id) for id in self.related_root_cause_ids],
            "scores": self.scores.to_dict() if self.scores else None,
            "status": self.status.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "period_type": self.period_type.value,
            "scope_type": self.scope_type.value,
            "scope_id": str(self.scope_id) if self.scope_id else None,
            "scope_name": self.scope_name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(kw_only=True)
class Opportunity(IntelligenceArtifact):
    """
    Represents a quantified business opportunity.
    """
    artifact_type: ArtifactType = ArtifactType.OPPORTUNITY

    # Classification
    opportunity_type: OpportunityType = OpportunityType.REVENUE_GROWTH
    category: OpportunityCategory = OpportunityCategory.REVENUE
    subcategory: Optional[str] = None

    # What it is
    title: str = ""
    summary: str = ""
    detailed_description: str = ""

    # Financial value
    estimated_value: float = 0.0
    value_unit: str = "annual"
    value_range_low: Optional[float] = None
    value_range_high: Optional[float] = None
    value_confidence: float = 0.0

    # Value breakdown
    value_breakdown: Optional[ValueBreakdown] = None
    baseline_metric_id: Optional[uuid.UUID] = None
    baseline_value: float = 0.0
    target_value: float = 0.0
    improvement_potential: float = 0.0

    # Effort and risk
    effort_level: EffortLevel = EffortLevel.MEDIUM
    risk_level: RiskLevel = RiskLevel.MEDIUM
    implementation_effort_hours: Optional[float] = None
    time_to_realize_months: float = 0.0
    roi: float = 0.0
    roi_rank: int = 0

    # Dependencies
    prerequisites: List[str] = field(default_factory=list)
    dependencies_on_opportunities: List[uuid.UUID] = field(default_factory=list)
    blocks_opportunities: List[uuid.UUID] = field(default_factory=list)

    # Actions
    recommended_actions: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    failure_risks: List[str] = field(default_factory=list)

    # Owner and tracking
    suggested_owner_id: Optional[uuid.UUID] = None
    owner_id: Optional[uuid.UUID] = None
    owner_name: Optional[str] = None
    assigned_at: Optional[datetime] = None

    # Status
    opportunity_status: OpportunityStatus = OpportunityStatus.IDENTIFIED
    realized_value: Optional[float] = None
    realized_at: Optional[datetime] = None
    realized_notes: Optional[str] = None

    # Context
    discovery_method: str = "root_cause_analysis"
    source_opportunity_id: Optional[uuid.UUID] = None
    related_metric_ids: List[uuid.UUID] = field(default_factory=list)
    related_insight_ids: List[uuid.UUID] = field(default_factory=list)
    related_recommendation_ids: List[uuid.UUID] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "artifact_type": self.artifact_type.value,
            "opportunity_type": self.opportunity_type.value,
            "category": self.category.value,
            "subcategory": self.subcategory,
            "title": self.title,
            "summary": self.summary,
            "detailed_description": self.detailed_description,
            "estimated_value": self.estimated_value,
            "value_unit": self.value_unit,
            "value_range_low": self.value_range_low,
            "value_range_high": self.value_range_high,
            "value_confidence": self.value_confidence,
            "value_breakdown": self.value_breakdown.to_dict() if self.value_breakdown else None,
            "baseline_metric_id": str(self.baseline_metric_id) if self.baseline_metric_id else None,
            "baseline_value": self.baseline_value,
            "target_value": self.target_value,
            "improvement_potential": self.improvement_potential,
            "effort_level": self.effort_level.value,
            "risk_level": self.risk_level.value,
            "implementation_effort_hours": self.implementation_effort_hours,
            "time_to_realize_months": self.time_to_realize_months,
            "roi": self.roi,
            "roi_rank": self.roi_rank,
            "prerequisites": self.prerequisites,
            "dependencies_on_opportunities": [str(id) for id in self.dependencies_on_opportunities],
            "blocks_opportunities": [str(id) for id in self.blocks_opportunities],
            "recommended_actions": self.recommended_actions,
            "success_criteria": self.success_criteria,
            "failure_risks": self.failure_risks,
            "suggested_owner_id": str(self.suggested_owner_id) if self.suggested_owner_id else None,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "owner_name": self.owner_name,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "opportunity_status": self.opportunity_status.value,
            "realized_value": self.realized_value,
            "realized_at": self.realized_at.isoformat() if self.realized_at else None,
            "realized_notes": self.realized_notes,
            "discovery_method": self.discovery_method,
            "source_opportunity_id": str(self.source_opportunity_id) if self.source_opportunity_id else None,
            "related_metric_ids": [str(id) for id in self.related_metric_ids],
            "related_insight_ids": [str(id) for id in self.related_insight_ids],
            "related_recommendation_ids": [str(id) for id in self.related_recommendation_ids],
            "scores": self.scores.to_dict() if self.scores else None,
            "status": self.status.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "period_type": self.period_type.value,
            "scope_type": self.scope_type.value,
            "scope_id": str(self.scope_id) if self.scope_id else None,
            "scope_name": self.scope_name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(kw_only=True)
class Recommendation(IntelligenceArtifact):
    """
    Represents an actionable recommendation.
    """
    artifact_type: ArtifactType = ArtifactType.RECOMMENDATION

    # Classification
    recommendation_type: RecommendationType = RecommendationType.REVENUE_OPTIMIZATION
    category: str = "FINANCIAL"

    # Content
    title: str = ""
    summary: str = ""
    detailed_recommendation: str = ""

    # Evidence chain
    evidence_chain: List[EvidenceItem] = field(default_factory=list)
    supporting_insight_ids: List[uuid.UUID] = field(default_factory=list)
    supporting_anomaly_ids: List[uuid.UUID] = field(default_factory=list)
    supporting_root_cause_ids: List[uuid.UUID] = field(default_factory=list)
    supporting_opportunity_ids: List[uuid.UUID] = field(default_factory=list)

    # Expected impact
    expected_impact_value: float = 0.0
    expected_impact_unit: str = "annual"
    impact_direction: ImpactDirection = ImpactDirection.INCREASE_REVENUE
    confidence_in_impact: float = 0.0
    impact_calculation: str = ""

    # Implementation
    recommended_actions: List[ActionStep] = field(default_factory=list)
    estimated_effort_hours: float = 0.0
    time_to_implement_months: float = 0.0
    success_metrics: List[str] = field(default_factory=list)
    failure_risks: List[str] = field(default_factory=list)

    # Prioritization
    priority_score: float = 0.0
    priority_rank: int = 0
    priority_rationale: str = ""

    # Status
    recommendation_status: RecommendationStatus = RecommendationStatus.PROPOSED
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    implemented_by: Optional[uuid.UUID] = None
    implemented_at: Optional[datetime] = None
    implementation_result: Optional[str] = None
    actual_vs_expected_impact: Optional[float] = None

    # Assignment
    assigned_to_id: Optional[uuid.UUID] = None
    assigned_to_name: Optional[str] = None
    assigned_at: Optional[datetime] = None
    due_date: Optional[datetime] = None

    # Generated by
    generation_method: str = "rule_based"
    generated_by_model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "artifact_type": self.artifact_type.value,
            "recommendation_type": self.recommendation_type.value,
            "category": self.category,
            "title": self.title,
            "summary": self.summary,
            "detailed_recommendation": self.detailed_recommendation,
            "evidence_chain": [e.to_dict() for e in self.evidence_chain],
            "supporting_insight_ids": [str(id) for id in self.supporting_insight_ids],
            "supporting_anomaly_ids": [str(id) for id in self.supporting_anomaly_ids],
            "supporting_root_cause_ids": [str(id) for id in self.supporting_root_cause_ids],
            "supporting_opportunity_ids": [str(id) for id in self.supporting_opportunity_ids],
            "expected_impact_value": self.expected_impact_value,
            "expected_impact_unit": self.expected_impact_unit,
            "impact_direction": self.impact_direction.value,
            "confidence_in_impact": self.confidence_in_impact,
            "impact_calculation": self.impact_calculation,
            "recommended_actions": [a.to_dict() for a in self.recommended_actions],
            "estimated_effort_hours": self.estimated_effort_hours,
            "time_to_implement_months": self.time_to_implement_months,
            "success_metrics": self.success_metrics,
            "failure_risks": self.failure_risks,
            "priority_score": self.priority_score,
            "priority_rank": self.priority_rank,
            "priority_rationale": self.priority_rationale,
            "recommendation_status": self.recommendation_status.value,
            "reviewed_by": str(self.reviewed_by) if self.reviewed_by else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_notes": self.review_notes,
            "implemented_by": str(self.implemented_by) if self.implemented_by else None,
            "implemented_at": self.implemented_at.isoformat() if self.implemented_at else None,
            "implementation_result": self.implementation_result,
            "actual_vs_expected_impact": self.actual_vs_expected_impact,
            "assigned_to_id": str(self.assigned_to_id) if self.assigned_to_id else None,
            "assigned_to_name": self.assigned_to_name,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "generation_method": self.generation_method,
            "generated_by_model": self.generated_by_model,
            "scores": self.scores.to_dict() if self.scores else None,
            "status": self.status.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "period_type": self.period_type.value,
            "scope_type": self.scope_type.value,
            "scope_id": str(self.scope_id) if self.scope_id else None,
            "scope_name": self.scope_name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(kw_only=True)
class BriefingSection:
    """
    A section within a briefing.
    """
    section_id: str
    section_type: str
    title: str
    order: int
    content: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    visualizations: List[Dict[str, Any]] = field(default_factory=list)
    narrative_generated: bool = False
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "section_type": self.section_type,
            "title": self.title,
            "order": self.order,
            "content": self.content,
            "data": self.data,
            "visualizations": self.visualizations,
            "narrative_generated": self.narrative_generated,
            "confidence": self.confidence,
            "sources": self.sources,
        }


@dataclass(kw_only=True)
class BriefingSummary:
    """
    The one-paragraph executive summary.
    """
    narrative: str = ""
    primary_wins: List[str] = field(default_factory=list)
    primary_risks: List[str] = field(default_factory=list)
    primary_actions: List[str] = field(default_factory=list)
    overall_sentiment: SentimentLabel = SentimentLabel.NEUTRAL
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "narrative": self.narrative,
            "primary_wins": self.primary_wins,
            "primary_risks": self.primary_risks,
            "primary_actions": self.primary_actions,
            "overall_sentiment": self.overall_sentiment.value,
            "confidence": self.confidence,
        }


@dataclass(kw_only=True)
class BriefingHighlight:
    """
    A key highlight item requiring attention.
    """
    highlight_type: HighlightType = HighlightType.WIN
    priority: str = "P2"
    title: str = ""
    description: str = ""
    metric_value: Optional[str] = None
    action_required: Optional[str] = None
    related_intelligence_ids: List[uuid.UUID] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "highlight_type": self.highlight_type.value,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "metric_value": self.metric_value,
            "action_required": self.action_required,
            "related_intelligence_ids": [str(id) for id in self.related_intelligence_ids],
        }


@dataclass(kw_only=True)
class Briefing(IntelligenceArtifact):
    """
    A complete executive briefing document.
    """
    artifact_type: ArtifactType = ArtifactType.BRIEFING

    # Briefing identity
    briefing_type: BriefingType = BriefingType.MONTHLY
    title: str = ""

    # For comparisons
    comparison_period_start: Optional[datetime] = None
    comparison_period_end: Optional[datetime] = None

    # Recipients
    recipient_ids: List[uuid.UUID] = field(default_factory=list)
    recipient_emails: List[str] = field(default_factory=list)
    recipient_roles: List[str] = field(default_factory=list)

    # Sections
    sections: List[BriefingSection] = field(default_factory=list)

    # Summary
    executive_summary: Optional[BriefingSummary] = None

    # Key highlights
    key_highlights: List[BriefingHighlight] = field(default_factory=list)

    # Metrics snapshot
    metrics_snapshot: List[Dict[str, Any]] = field(default_factory=list)

    # AI-generated narrative
    narrative: str = ""

    # Attachments
    attachment_urls: List[str] = field(default_factory=list)

    # Status
    briefing_status: BriefingStatus = BriefingStatus.DRAFT
    finalized_at: Optional[datetime] = None
    finalized_by: Optional[uuid.UUID] = None

    # Distribution
    distributed_at: Optional[datetime] = None
    distribution_channels: List[str] = field(default_factory=list)

    # Versioning
    is_update: bool = False
    previous_briefing_id: Optional[uuid.UUID] = None

    # Generation
    generation_method: str = "template_generation"
    generation_duration_ms: int = 0
    generation_prompts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "artifact_type": self.artifact_type.value,
            "briefing_type": self.briefing_type.value,
            "title": self.title,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "period_type": self.period_type.value,
            "comparison_period_start": self.comparison_period_start.isoformat() if self.comparison_period_start else None,
            "comparison_period_end": self.comparison_period_end.isoformat() if self.comparison_period_end else None,
            "recipient_ids": [str(id) for id in self.recipient_ids],
            "recipient_emails": self.recipient_emails,
            "recipient_roles": self.recipient_roles,
            "sections": [s.to_dict() for s in self.sections],
            "executive_summary": self.executive_summary.to_dict() if self.executive_summary else None,
            "key_highlights": [h.to_dict() for h in self.key_highlights],
            "metrics_snapshot": self.metrics_snapshot,
            "narrative": self.narrative,
            "attachment_urls": self.attachment_urls,
            "briefing_status": self.briefing_status.value,
            "finalized_at": self.finalized_at.isoformat() if self.finalized_at else None,
            "finalized_by": str(self.finalized_by) if self.finalized_by else None,
            "distributed_at": self.distributed_at.isoformat() if self.distributed_at else None,
            "distribution_channels": self.distribution_channels,
            "is_update": self.is_update,
            "previous_briefing_id": str(self.previous_briefing_id) if self.previous_briefing_id else None,
            "generation_method": self.generation_method,
            "generation_duration_ms": self.generation_duration_ms,
            "generation_prompts": self.generation_prompts,
            "scores": self.scores.to_dict() if self.scores else None,
            "status": self.status.value,
            "scope_type": self.scope_type.value,
            "scope_id": str(self.scope_id) if self.scope_id else None,
            "scope_name": self.scope_name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(kw_only=True)
class RootCauseAnalysisResult:
    """
    The complete output of a root cause analysis run.
    """
    id: uuid.UUID
    tenant_id: uuid.UUID
    analysis_id: uuid.UUID

    # Analysis metadata
    analyzed_metric_id: uuid.UUID
    analyzed_metric_code: str

    # Values
    previous_value: float = 0.0
    current_value: float = 0.0
    change_absolute: float = 0.0
    change_percent: float = 0.0

    # Period
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    comparison_start: datetime = field(default_factory=datetime.utcnow)
    comparison_end: datetime = field(default_factory=datetime.utcnow)

    # Causes
    primary_cause: Optional[RootCause] = None
    secondary_causes: List[RootCause] = field(default_factory=list)
    all_causes: List[RootCause] = field(default_factory=list)

    # Attribution validation
    total_attribution: float = 0.0
    unattributed_amount: float = 0.0
    attribution_coverage: float = 0.0
    is_fully_attributed: bool = False

    # Statistical summary
    overall_confidence: float = 0.0
    statistical_power: float = 0.0
    minimum_detectable_effect: float = 0.0

    # Method used
    analysis_method: str = "variance_decomposition"
    method_parameters: Dict[str, Any] = field(default_factory=dict)

    # Execution
    generated_by: GenerationSource = GenerationSource.SYSTEM
    generated_at: datetime = field(default_factory=datetime.utcnow)
    computation_duration_ms: int = 0

    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "analysis_id": str(self.analysis_id),
            "analyzed_metric_id": str(self.analyzed_metric_id),
            "analyzed_metric_code": self.analyzed_metric_code,
            "previous_value": self.previous_value,
            "current_value": self.current_value,
            "change_absolute": self.change_absolute,
            "change_percent": self.change_percent,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "comparison_start": self.comparison_start.isoformat(),
            "comparison_end": self.comparison_end.isoformat(),
            "primary_cause": self.primary_cause.to_dict() if self.primary_cause else None,
            "secondary_causes": [c.to_dict() for c in self.secondary_causes],
            "all_causes": [c.to_dict() for c in self.all_causes],
            "total_attribution": self.total_attribution,
            "unattributed_amount": self.unattributed_amount,
            "attribution_coverage": self.attribution_coverage,
            "is_fully_attributed": self.is_fully_attributed,
            "overall_confidence": self.overall_confidence,
            "statistical_power": self.statistical_power,
            "minimum_detectable_effect": self.minimum_detectable_effect,
            "analysis_method": self.analysis_method,
            "method_parameters": self.method_parameters,
            "generated_by": self.generated_by.value,
            "generated_at": self.generated_at.isoformat(),
            "computation_duration_ms": self.computation_duration_ms,
            "version": self.version,
        }


@dataclass(kw_only=True)
class IntelligenceNode:
    """
    A node in the intelligence relationship graph.
    """
    id: uuid.UUID
    tenant_id: uuid.UUID
    node_type: str = "metric"
    node_subtype: Optional[str] = None
    entity_type: str = ""
    entity_id: uuid.UUID = field(default_factory=uuid.uuid4)
    label: str = ""
    description: Optional[str] = None
    primary_value: Optional[float] = None
    importance_score: float = 0.0
    influence_score: float = 0.0
    first_observed_at: datetime = field(default_factory=datetime.utcnow)
    last_observed_at: datetime = field(default_factory=datetime.utcnow)
    observation_count: int = 1
    status: str = "active"
    merged_into_id: Optional[uuid.UUID] = None
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "node_type": self.node_type,
            "node_subtype": self.node_subtype,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id),
            "label": self.label,
            "description": self.description,
            "primary_value": self.primary_value,
            "importance_score": self.importance_score,
            "influence_score": self.influence_score,
            "first_observed_at": self.first_observed_at.isoformat(),
            "last_observed_at": self.last_observed_at.isoformat(),
            "observation_count": self.observation_count,
            "status": self.status,
            "merged_into_id": str(self.merged_into_id) if self.merged_into_id else None,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(kw_only=True)
class IntelligenceRelationship:
    """
    A typed, directed relationship between two IntelligenceNodes.
    """
    id: uuid.UUID
    tenant_id: uuid.UUID
    source_node_id: uuid.UUID
    target_node_id: uuid.UUID
    relationship_type: str = "related_to"
    relationship_subtype: Optional[str] = None
    correlation_strength: float = 0.0
    causal_strength: Optional[float] = None
    confidence: float = 0.0
    context: Optional[str] = None
    evidence_count: int = 0
    first_observed_at: datetime = field(default_factory=datetime.utcnow)
    last_observed_at: datetime = field(default_factory=datetime.utcnow)
    is_historical: bool = False
    deprecated_at: Optional[datetime] = None
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "source_node_id": str(self.source_node_id),
            "target_node_id": str(self.target_node_id),
            "relationship_type": self.relationship_type,
            "relationship_subtype": self.relationship_subtype,
            "correlation_strength": self.correlation_strength,
            "causal_strength": self.causal_strength,
            "confidence": self.confidence,
            "context": self.context,
            "evidence_count": self.evidence_count,
            "first_observed_at": self.first_observed_at.isoformat(),
            "last_observed_at": self.last_observed_at.isoformat(),
            "is_historical": self.is_historical,
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(kw_only=True)
class InfluenceNetwork:
    """
    Represents the influence relationships around a node.
    """
    central_node: IntelligenceNode
    direct_influencers: List[IntelligenceNode] = field(default_factory=list)
    direct_influencees: List[IntelligenceNode] = field(default_factory=list)
    indirect_influencers: List[IntelligenceNode] = field(default_factory=list)
    indirect_influencees: List[IntelligenceNode] = field(default_factory=list)
    total_connected_nodes: int = 0
    network_density: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "central_node": self.central_node.to_dict(),
            "direct_influencers": [n.to_dict() for n in self.direct_influencers],
            "direct_influencees": [n.to_dict() for n in self.direct_influencees],
            "indirect_influencers": [n.to_dict() for n in self.indirect_influencers],
            "indirect_influencees": [n.to_dict() for n in self.indirect_influencees],
            "total_connected_nodes": self.total_connected_nodes,
            "network_density": self.network_density,
        }
