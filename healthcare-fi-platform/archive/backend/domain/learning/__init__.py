"""
Learning Engine Domain.
Measures recommendation quality, detects patterns, suggests scoring adjustments.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from app.domain.outcome.value_objects import (
    LearningMetricType, TrendDirection, AcceptanceStatus,
)


@dataclass(kw_only=True)
class LearningMetric:
    id: uuid.UUID
    tenant_id: uuid.UUID
    metric_type: str = "recommendation_accuracy"
    target_entity_type: str = "recommendation"
    metric_value: float = 0.0
    sample_size: int = 0
    confidence_interval_lower: float = 0.0
    confidence_interval_upper: float = 0.0
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)
    breakdown: Dict[str, float] = field(default_factory=dict)
    vs_previous_period: float = 0.0
    trend_direction: str = "stable"
    computed_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id), "tenant_id": str(self.tenant_id),
            "metric_type": self.metric_type, "metric_value": self.metric_value,
            "sample_size": self.sample_size, "trend_direction": self.trend_direction,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "computed_at": self.computed_at.isoformat(),
        }


@dataclass(kw_only=True)
class RecommendationAccuracyTracker:
    id: uuid.UUID
    tenant_id: uuid.UUID
    recommendation_id: uuid.UUID
    recommended_action: str = ""
    expected_outcome: str = ""
    estimated_value: float = 0.0
    actual_outcome: str = ""
    actual_value: float = 0.0
    accuracy_score: float = 0.0
    directional_accuracy: bool = False
    magnitude_accuracy: float = 0.0
    timing_accuracy: float = 0.0
    was_decision_made: bool = False
    decision_id: Optional[uuid.UUID] = None
    decision_implemented: bool = False
    prediction_error: float = 0.0
    prediction_error_percent: float = 0.0
    outcome_recorded_at: Optional[datetime] = None
    computed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id), "recommendation_id": str(self.recommendation_id),
            "accuracy_score": self.accuracy_score,
            "directional_accuracy": self.directional_accuracy,
            "actual_value": self.actual_value, "estimated_value": self.estimated_value,
        }


class ILearningEngine:
    async def record_outcome(self, tenant_id, entity_type, entity_id, actual_value, outcome_data):
        pass
    async def compute_recommendation_accuracy(self, tenant_id, start_date, end_date):
        pass
    async def get_top_performing_recommendation_types(self, tenant_id):
        pass
    async def get_bottom_performing_recommendation_types(self, tenant_id):
        pass
    async def get_executive_adoption_summary(self, tenant_id):
        pass
    async def detect_recommendation_patterns(self, tenant_id):
        pass
    async def suggest_scoring_adjustments(self, tenant_id):
        pass
    async def get_learning_dashboard(self, tenant_id):
        pass
