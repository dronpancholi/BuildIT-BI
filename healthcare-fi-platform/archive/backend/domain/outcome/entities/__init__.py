"""
Outcome Domain Entities.
OutcomeDefinition, OutcomeMeasurement, CausalImpactAnalysis.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from app.domain.outcome.value_objects import (
    OutcomeStatus,
    MeasurementFrequency,
    CheckpointType,
    MeasurementStatus,
    CausalMethod,
    ConfoundingFactor,
    EvalType,
    Environment,
    FitQuality,
)


@dataclass(kw_only=True)
class OutcomeDefinition:
    """Defines how an outcome is measured before a decision is made."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    decision_id: uuid.UUID

    metrics: List[Dict[str, Any]] = field(default_factory=list)
    # Each dict: metric_code, baseline_value, target_value, direction,
    # min_acceptable_change, measurement_frequency, data_source, aggregation_method

    measurement_window_start: date = field(default_factory=date.today)
    measurement_window_end: date = field(default_factory=date.today)
    comparison_period_start: Optional[date] = None
    comparison_period_end: Optional[date] = None

    use_control_group: bool = False
    control_group_definition: Optional[Dict[str, Any]] = None

    confidence_level: float = 0.95
    min_sample_size: Optional[int] = None

    created_by: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "decision_id": str(self.decision_id),
            "metrics": self.metrics,
            "measurement_window_start": self.measurement_window_start.isoformat(),
            "measurement_window_end": self.measurement_window_end.isoformat(),
            "use_control_group": self.use_control_group,
            "confidence_level": self.confidence_level,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(kw_only=True)
class OutcomeMeasurement:
    """Records actual measurement data at each checkpoint."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    outcome_definition_id: uuid.UUID
    decision_id: uuid.UUID

    measurement_time: datetime = field(default_factory=datetime.utcnow)
    checkpoint_type: CheckpointType = CheckpointType.MONTHLY

    metric_values: List[Dict[str, Any]] = field(default_factory=list)
    # Each dict: metric_code, raw_value, computed_value, change_from_baseline,
    # change_from_previous, is_within_expected_range

    status: MeasurementStatus = MeasurementStatus.ON_TRACK
    alerts_triggered: List[Dict[str, Any]] = field(default_factory=list)

    measured_by: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "outcome_definition_id": str(self.outcome_definition_id),
            "decision_id": str(self.decision_id),
            "measurement_time": self.measurement_time.isoformat(),
            "checkpoint_type": self.checkpoint_type.value,
            "metric_values": self.metric_values,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(kw_only=True)
class CausalImpactAnalysis:
    """Formal causal analysis using multiple methods."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    outcome_id: uuid.UUID
    decision_id: uuid.UUID

    method: CausalMethod = CausalMethod.BEFORE_AFTER

    causal_effect_size: float = 0.0
    causal_effect_confidence: float = 0.0
    confidence_interval_lower: float = 0.0
    confidence_interval_upper: float = 0.0

    attribution_score: float = 0.0
    confounding_factors: List[ConfoundingFactor] = field(default_factory=list)

    counterfactual_value: float = 0.0
    counterfactual_confidence: float = 0.0

    treatment_vs_control: float = 0.0

    statistical_significance: float = 1.0
    effect_hypothesis_test: str = ""

    analysis_time: datetime = field(default_factory=datetime.utcnow)
    analyzed_by: Optional[uuid.UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "outcome_id": str(self.outcome_id),
            "decision_id": str(self.decision_id),
            "method": self.method.value,
            "causal_effect_size": self.causal_effect_size,
            "causal_effect_confidence": self.causal_effect_confidence,
            "confidence_interval_lower": self.confidence_interval_lower,
            "confidence_interval_upper": self.confidence_interval_upper,
            "attribution_score": self.attribution_score,
            "statistical_significance": self.statistical_significance,
            "analysis_time": self.analysis_time.isoformat(),
        }


@dataclass(kw_only=True)
class FeatureDefinition:
    """Feature store entry."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    namespace: str = "finance"
    description: str = ""
    feature_type: str = "aggregation"

    computation_type: str = "sql"
    computation_source: str = ""
    computation_params: Dict[str, Any] = field(default_factory=dict)

    entity_type: str = "department"
    entity_id_path: str = ""

    temporal_type: str = "static"
    window_size: Optional[int] = None
    window_unit: Optional[str] = None
    refresh_frequency: str = "daily"

    value_type: str = "float"
    default_value: Any = None

    owner_id: Optional[uuid.UUID] = None
    tags: List[str] = field(default_factory=list)

    source_metrics: List[str] = field(default_factory=list)
    source_features: List[str] = field(default_factory=list)

    status: str = "draft"
    version: int = 1

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "namespace": self.namespace,
            "description": self.description,
            "feature_type": self.feature_type,
            "entity_type": self.entity_type,
            "temporal_type": self.temporal_type,
            "value_type": self.value_type,
            "status": self.status,
            "version": self.version,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(kw_only=True)
class ModelArtifact:
    """Registered ML/statistical model."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    model_type: str = "statistical"
    framework: Optional[str] = None
    version: str = "1.0.0"
    version_notes: str = ""
    model_location: str = ""
    artifact_size_bytes: int = 0
    checksum: str = ""
    model_format: str = "json"

    metrics: List[Dict[str, Any]] = field(default_factory=list)
    entity_type: Optional[str] = None
    use_cases: List[str] = field(default_factory=list)

    owner_id: Optional[uuid.UUID] = None
    approval_status: str = "draft"
    tags: List[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version_int: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "model_type": self.model_type,
            "version": self.version,
            "approval_status": self.approval_status,
            "use_cases": self.use_cases,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }
