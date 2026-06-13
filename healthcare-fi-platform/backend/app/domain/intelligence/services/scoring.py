"""
Intelligence Scoring Framework.
Every intelligence artifact uses the same scoring framework for consistent ranking.
"""
import uuid
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from app.domain.intelligence.value_objects import (
    IntelligenceScores,
    ConfidenceLabel,
    ImpactLabel,
    PriorityLabel,
    UrgencyLabel,
    ArtifactType,
    AnomalySeverity,
    OpportunityStatus,
    RecommendationStatus,
)


@dataclass
class ScoringContext:
    """
    Context for scoring calculations.
    """
    tenant_id: uuid.UUID
    scope_id: Optional[uuid.UUID] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    artifact_type: Optional[ArtifactType] = None
    artifact_data: Dict[str, Any] = field(default_factory=dict)
    historical_scores: List[IntelligenceScores] = field(default_factory=list)
    peer_scores: List[IntelligenceScores] = field(default_factory=list)


class IntelligenceScoreCalculator:
    """
    Calculates consistent scores for all intelligence artifacts.
    """

    def __init__(self):
        self.scoring_algorithm_version = "1.0"

    async def calculate_scores(
        self,
        artifact_type: ArtifactType,
        artifact_data: Dict[str, Any],
        context: ScoringContext
    ) -> IntelligenceScores:
        """
        Calculate all four scores for an intelligence artifact.
        """
        confidence, confidence_label = await self.calculate_confidence(artifact_type, artifact_data)
        impact, impact_label = await self.calculate_impact(artifact_type, artifact_data)
        urgency, urgency_label = await self.calculate_urgency(artifact_type, artifact_data)
        priority, priority_label = await self.calculate_priority(confidence, impact, urgency)

        score_inputs = {
            "confidence": confidence,
            "impact": impact,
            "urgency": urgency,
            "priority": priority,
            "confidence_label": confidence_label.value,
            "impact_label": impact_label.value,
            "priority_label": priority_label.value,
            "urgency_label": urgency_label.value,
            "artifact_type": artifact_type.value,
            "artifact_data_keys": list(artifact_data.keys()),
            "context": {
                "tenant_id": str(context.tenant_id),
                "scope_id": str(context.scope_id) if context.scope_id else None,
                "period_start": context.period_start.isoformat() if context.period_start else None,
                "period_end": context.period_end.isoformat() if context.period_end else None,
            }
        }

        return IntelligenceScores(
            confidence=confidence,
            impact=impact,
            priority=priority,
            urgency=urgency,
            confidence_label=confidence_label,
            impact_label=impact_label,
            priority_label=priority_label,
            urgency_label=urgency_label,
            score_inputs=score_inputs,
            score_algorithm_version=self.scoring_algorithm_version,
        )

    async def calculate_confidence(
        self,
        artifact_type: ArtifactType,
        artifact_data: Dict[str, Any]
    ) -> Tuple[float, ConfidenceLabel]:
        """
        Confidence: How reliable is this finding?
        Inputs:
        - Statistical significance (p-value)
        - Data quality score
        - Sample size
        - Historical consistency
        """
        factors = {
            "statistical": self._calculate_statistical_confidence(artifact_data),
            "data_quality": artifact_data.get("data_quality_score", 1.0),
            "sample_size": self._calculate_sample_size_confidence(artifact_data),
            "consistency": self._calculate_historical_consistency(artifact_data),
        }

        # Weighted combination
        weights = {"statistical": 0.40, "data_quality": 0.25, "sample_size": 0.20, "consistency": 0.15}
        confidence = sum(factors[k] * weights[k] for k in weights)

        # Bound to [0, 1]
        confidence = max(0.0, min(1.0, confidence))

        label = ConfidenceLabel.HIGH if confidence >= 0.75 else (
            ConfidenceLabel.MEDIUM if confidence >= 0.50 else ConfidenceLabel.LOW
        )
        return confidence, label

    async def calculate_impact(
        self,
        artifact_type: ArtifactType,
        artifact_data: Dict[str, Any]
    ) -> Tuple[float, ImpactLabel]:
        """
        Impact: How significant is this to the business?
        Inputs:
        - Dollar value (revenue, cost, margin impact)
        - Scope (how many entities affected)
        - Severity (how critical)
        - Duration (how long-lasting)
        """
        factors = {
            "dollar_impact": self._calculate_dollar_impact_score(artifact_data),
            "scope_impact": self._calculate_scope_impact_score(artifact_data),
            "severity": self._calculate_severity_score(artifact_data),
            "duration": self._calculate_duration_score(artifact_data),
        }

        weights = {"dollar_impact": 0.45, "scope_impact": 0.20, "severity": 0.25, "duration": 0.10}
        impact = sum(factors[k] * weights[k] for k in weights)

        # Bound to [0, 1]
        impact = max(0.0, min(1.0, impact))

        label = ImpactLabel.CRITICAL if impact >= 0.85 else (
            ImpactLabel.HIGH if impact >= 0.65 else (
                ImpactLabel.MEDIUM if impact >= 0.35 else ImpactLabel.LOW
            )
        )
        return impact, label

    async def calculate_urgency(
        self,
        artifact_type: ArtifactType,
        artifact_data: Dict[str, Any]
    ) -> Tuple[float, UrgencyLabel]:
        """
        Urgency: How time-sensitive is this?
        Inputs:
        - Trend direction (worsening = more urgent)
        - Time to impact (sooner = more urgent)
        - External deadline (regulatory, contract)
        - Seasonal factors
        """
        factors = {
            "trend": self._calculate_trend_urgency(artifact_data),
            "time_to_impact": self._calculate_time_to_impact_score(artifact_data),
            "external_deadline": self._calculate_deadline_score(artifact_data),
            "seasonality": self._calculate_seasonal_urgency(artifact_data),
        }

        weights = {"trend": 0.30, "time_to_impact": 0.40, "external_deadline": 0.20, "seasonality": 0.10}
        urgency = sum(factors[k] * weights[k] for k in weights)

        # Bound to [0, 1]
        urgency = max(0.0, min(1.0, urgency))

        label = UrgencyLabel.IMMEDIATE if urgency >= 0.85 else (
            UrgencyLabel.SOON if urgency >= 0.60 else (
                UrgencyLabel.SCHEDULED if urgency >= 0.30 else UrgencyLabel.BACKLOG
            )
        )
        return urgency, label

    async def calculate_priority(
        self,
        confidence: float,
        impact: float,
        urgency: float
    ) -> Tuple[float, PriorityLabel]:
        """
        Priority: Composite score combining all three.
        Formula: priority = (impact × 0.50) + (confidence × 0.30) + (urgency × 0.20)
        """
        priority = (impact * 0.50) + (confidence * 0.30) + (urgency * 0.20)

        # Bound to [0, 1]
        priority = max(0.0, min(1.0, priority))

        label = PriorityLabel.P0 if priority >= 0.85 else (
            PriorityLabel.P1 if priority >= 0.70 else (
                PriorityLabel.P2 if priority >= 0.50 else PriorityLabel.P3
            )
        )
        return priority, label

    def _calculate_statistical_confidence(self, artifact_data: Dict[str, Any]) -> float:
        """
        Calculate confidence based on statistical significance.
        """
        p_value = artifact_data.get("p_value")
        if p_value is None:
            return 0.5  # Default if no p-value

        # Convert p-value to confidence
        # p < 0.01 → 0.95 confidence
        # p < 0.05 → 0.80 confidence
        # p < 0.10 → 0.60 confidence
        # p >= 0.10 → 0.30 confidence
        if p_value < 0.01:
            return 0.95
        elif p_value < 0.05:
            return 0.80
        elif p_value < 0.10:
            return 0.60
        else:
            return 0.30

    def _calculate_sample_size_confidence(self, artifact_data: Dict[str, Any]) -> float:
        """
        Calculate confidence based on sample size.
        """
        sample_size = artifact_data.get("sample_size", 0)
        if sample_size <= 0:
            return 0.5  # Default if no sample size

        # Larger samples give more confidence
        # 1000+ → 0.95
        # 500-999 → 0.85
        # 100-499 → 0.70
        # 30-99 → 0.55
        # <30 → 0.30
        if sample_size >= 1000:
            return 0.95
        elif sample_size >= 500:
            return 0.85
        elif sample_size >= 100:
            return 0.70
        elif sample_size >= 30:
            return 0.55
        else:
            return 0.30

    def _calculate_historical_consistency(self, artifact_data: Dict[str, Any]) -> float:
        """
        Calculate confidence based on historical consistency.
        """
        historical_consistency = artifact_data.get("historical_consistency")
        if historical_consistency is None:
            return 0.5  # Default if no historical data

        # Higher consistency → higher confidence
        return max(0.0, min(1.0, historical_consistency))

    def _calculate_dollar_impact_score(self, artifact_data: Dict[str, Any]) -> float:
        """
        Calculate impact score based on dollar value.
        """
        dollar_impact = artifact_data.get("dollar_impact", 0)
        if dollar_impact is None:
            return 0.0

        # Absolute value
        abs_impact = abs(dollar_impact)

        # Scale: $10M+ → 1.0, $1M → 0.8, $100K → 0.6, $10K → 0.4, $1K → 0.2
        if abs_impact >= 10_000_000:
            return 1.0
        elif abs_impact >= 1_000_000:
            return 0.8
        elif abs_impact >= 100_000:
            return 0.6
        elif abs_impact >= 10_000:
            return 0.4
        elif abs_impact >= 1_000:
            return 0.2
        else:
            return 0.1

    def _calculate_scope_impact_score(self, artifact_data: Dict[str, Any]) -> float:
        """
        Calculate impact score based on scope.
        """
        scope_type = artifact_data.get("scope_type", "tenant")
        affected_count = artifact_data.get("affected_count", 1)

        # Scope multiplier
        scope_multiplier = {
            "tenant": 1.0,
            "hospital": 0.8,
            "branch": 0.6,
            "department": 0.4,
        }.get(scope_type, 0.5)

        # Affected count multiplier
        count_multiplier = min(1.0, affected_count / 10)

        return scope_multiplier * 0.7 + count_multiplier * 0.3

    def _calculate_severity_score(self, artifact_data: Dict[str, Any]) -> float:
        """
        Calculate impact score based on severity.
        """
        severity = artifact_data.get("severity", "medium")

        severity_scores = {
            "critical": 1.0,
            "high": 0.75,
            "medium": 0.50,
            "low": 0.25,
            "info": 0.10,
        }
        return severity_scores.get(severity, 0.50)

    def _calculate_duration_score(self, artifact_data: Dict[str, Any]) -> float:
        """
        Calculate impact score based on duration.
        """
        is_persistent = artifact_data.get("is_persistent", False)
        duration_periods = artifact_data.get("duration_periods", 1)

        if is_persistent:
            return 0.9  # Persistent issues have high impact
        elif duration_periods > 3:
            return 0.7
        elif duration_periods > 1:
            return 0.5
        else:
            return 0.3

    def _calculate_trend_urgency(self, artifact_data: Dict[str, Any]) -> float:
        """
        Calculate urgency based on trend direction.
        """
        trend = artifact_data.get("trend", "stable")

        # Worsening trends are more urgent
        trend_scores = {
            "worsening": 0.9,
            "declining": 0.7,
            "stable": 0.3,
            "improving": 0.2,
            "improved": 0.1,
        }
        return trend_scores.get(trend, 0.3)

    def _calculate_time_to_impact_score(self, artifact_data: Dict[str, Any]) -> float:
        """
        Calculate urgency based on time to impact.
        """
        time_to_impact_days = artifact_data.get("time_to_impact_days", 30)

        # Sooner impact → higher urgency
        if time_to_impact_days <= 1:
            return 1.0
        elif time_to_impact_days <= 7:
            return 0.8
        elif time_to_impact_days <= 30:
            return 0.6
        elif time_to_impact_days <= 90:
            return 0.4
        else:
            return 0.2

    def _calculate_deadline_score(self, artifact_data: Dict[str, Any]) -> float:
        """
        Calculate urgency based on external deadline.
        """
        has_deadline = artifact_data.get("has_external_deadline", False)
        deadline_days = artifact_data.get("deadline_days", 365)

        if not has_deadline:
            return 0.0

        # Closer deadline → higher urgency
        if deadline_days <= 7:
            return 1.0
        elif deadline_days <= 30:
            return 0.8
        elif deadline_days <= 90:
            return 0.5
        else:
            return 0.2

    def _calculate_seasonal_urgency(self, artifact_data: Dict[str, Any]) -> float:
        """
        Calculate urgency based on seasonal factors.
        """
        is_seasonal = artifact_data.get("is_seasonal", False)
        seasonal_weight = artifact_data.get("seasonal_weight", 0.5)

        if not is_seasonal:
            return 0.0

        return seasonal_weight


# Singleton instance
score_calculator = IntelligenceScoreCalculator()
