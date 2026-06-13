"""
Outcome Domain Value Objects.
Enums and value objects for the Outcome Measurement Engine.
"""
from enum import StrEnum
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from app.domain.decision.value_objects import (
    OutcomeStatus,
    MeasurementFrequency,
    AggregationMethod,
    Direction,
    CheckpointType,
    MeasurementStatus,
    CausalMethod,
    OutcomeMetricDefinition,
    MeasuredMetric,
    ConfoundingFactor,
    ScopeType,
)


class EvalType(StrEnum):
    OFFLINE = "offline"
    ONLINE = "online"
    SHADOW = "shadow"
    A_B_TEST = "a_b_test"


class FeatureType(StrEnum):
    POINT_IN_TIME = "point_in_time"
    AGGREGATION = "aggregation"
    DERIVED = "derived"
    EMBEDDING = "embedding"


class TemporalType(StrEnum):
    STATIC = "static"
    TUMBLING_WINDOW = "tumbling_window"
    SLIDING_WINDOW = "sliding_window"
    EVENT_DRIVEN = "event_driven"


class TimeUnit(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class RefreshFrequency(StrEnum):
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class ValueType(StrEnum):
    FLOAT = "float"
    INT = "int"
    STRING = "string"
    BOOL = "bool"
    VECTOR = "vector"


class FeatureStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class FeatureGroupStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class ModelType(StrEnum):
    STATISTICAL = "statistical"
    FORECAST = "forecast"
    ANOMALY = "anomaly"
    RECOMMENDATION = "recommendation"
    AI_LLM = "ai_llm"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    HYBRID = "hybrid"


class ModelFormat(StrEnum):
    PICKLE = "pickle"
    ONNX = "onnx"
    TORCH = "torch"
    TENSORFLOW = "tensorflow"
    PMML = "pmml"
    JSON = "json"


class ApprovalStatus(StrEnum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETIRED = "retired"


class Environment(StrEnum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class FitQuality(StrEnum):
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"


class TrendDirection(StrEnum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class LearningMetricType(StrEnum):
    RECOMMENDATION_ACCURACY = "recommendation_accuracy"
    DECISION_ACCURACY = "decision_accuracy"
    OPPORTUNITY_VALUE_ACCURACY = "opportunity_value_accuracy"
    FORECAST_ACCURACY = "forecast_accuracy"
    EXECUTIVE_ADOPTION_RATE = "executive_adoption_rate"


class AcceptanceStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    PROVEN_INEFFECTIVE = "proven_ineffective"


class MemoryDocType(StrEnum):
    INSIGHT = "insight"
    RECOMMENDATION = "recommendation"
    DECISION = "decision"
    OUTCOME = "outcome"
    BRIEFING = "briefing"
    EXECUTIVE_MEMORY = "executive_memory"
    AI_CFO_CONVERSATION = "ai_cfo_conversation"


@dataclass(frozen=True)
class BackfillJob:
    job_id: str
    feature_id: str
    status: str
    start_date: date
    end_date: date
    rows_computed: int = 0


@dataclass(frozen=True)
class DriftReport:
    feature_id: str
    drift_detected: bool
    drift_score: float
    baseline_distribution: Dict[str, float] = field(default_factory=dict)
    current_distribution: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class FeatureImportance:
    feature_name: str
    importance_score: float
    rank: int


@dataclass(frozen=True)
class ServingStats:
    feature_id: str
    total_serves: int
    avg_latency_ms: float
    p99_latency_ms: float
    cache_hit_rate: float


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ModelComparison:
    model_a_id: str
    model_a_version: str
    model_b_id: str
    model_b_version: str
    metrics_delta: Dict[str, float] = field(default_factory=dict)
    is_better: bool = False
