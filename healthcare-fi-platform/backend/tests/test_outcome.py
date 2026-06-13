"""
Comprehensive test suite for Outcome, Feature Store, and Model Registry domains.
"""
import uuid
import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, AsyncMock, MagicMock

from app.domain.outcome.entities import (
    OutcomeDefinition,
    OutcomeMeasurement,
    CausalImpactAnalysis,
    FeatureDefinition,
    ModelArtifact,
)
from app.domain.outcome.value_objects import (
    FeatureType,
    ModelType,
    EvalType,
    ApprovalStatus,
    Environment,
    FitQuality,
    LearningMetricType,
    AcceptanceStatus,
    MemoryDocType,
    MeasurementFrequency,
    CheckpointType,
    MeasurementStatus,
    CausalMethod,
)


@pytest.fixture
def tenant_id():
    return uuid.uuid4()

@pytest.fixture
def decision_id():
    return uuid.uuid4()

@pytest.fixture
def outcome_def_id():
    return uuid.uuid4()

@pytest.fixture
def feature_id():
    return uuid.uuid4()

@pytest.fixture
def model_id():
    return uuid.uuid4()


class TestOutcomeDefinition:
    def test_create_definition(self, tenant_id, outcome_def_id, decision_id):
        defn = OutcomeDefinition(
            id=outcome_def_id,
            tenant_id=tenant_id,
            decision_id=decision_id,
            metrics=[
                {"metric_code": "rev_per_patient_day", "baseline_value": 1200.0, "target_value": 1500.0, "direction": "increase"},
            ],
            measurement_window_start=date(2026, 1, 1),
            measurement_window_end=date(2026, 6, 30),
            confidence_level=0.95,
        )
        assert defn.decision_id == decision_id
        assert len(defn.metrics) == 1
        assert defn.metrics[0]["metric_code"] == "rev_per_patient_day"
        assert defn.confidence_level == 0.95

    def test_definition_to_dict(self, tenant_id, outcome_def_id, decision_id):
        defn = OutcomeDefinition(
            id=outcome_def_id,
            tenant_id=tenant_id,
            decision_id=decision_id,
            metrics=[{"metric_code": "claim_denial_rate", "baseline_value": 0.12, "target_value": 0.08, "direction": "decrease"}],
        )
        d = defn.to_dict()
        assert d["decision_id"] == str(decision_id)
        assert len(d["metrics"]) == 1
        assert d["metrics"][0]["metric_code"] == "claim_denial_rate"


class TestOutcomeMeasurement:
    def test_create_measurement(self, tenant_id, outcome_def_id, decision_id):
        meas = OutcomeMeasurement(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            outcome_definition_id=outcome_def_id,
            decision_id=decision_id,
            metric_values=[
                {"metric_code": "rev_per_patient_day", "raw_value": 1350.0, "computed_value": 1350.0, "change_from_baseline": 150.0, "change_from_previous": 50.0, "is_within_expected_range": True},
            ],
            checkpoint_type=CheckpointType.MONTHLY,
            status=MeasurementStatus.ON_TRACK,
        )
        assert len(meas.metric_values) == 1
        assert meas.metric_values[0]["raw_value"] == 1350.0
        assert meas.checkpoint_type == CheckpointType.MONTHLY
        assert meas.status == MeasurementStatus.ON_TRACK

    def test_measurement_to_dict(self, tenant_id, outcome_def_id, decision_id):
        meas = OutcomeMeasurement(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            outcome_definition_id=outcome_def_id,
            decision_id=decision_id,
            metric_values=[{"metric_code": "x", "raw_value": 0.09}],
        )
        d = meas.to_dict()
        assert len(d["metric_values"]) == 1
        assert d["metric_values"][0]["raw_value"] == 0.09


class TestCausalImpactAnalysis:
    def test_create_causal_impact(self, tenant_id, outcome_def_id, decision_id):
        impact = CausalImpactAnalysis(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            outcome_id=outcome_def_id,
            decision_id=decision_id,
            method=CausalMethod.BEFORE_AFTER,
            causal_effect_size=0.15,
            causal_effect_confidence=0.88,
            confidence_interval_lower=0.05,
            confidence_interval_upper=0.25,
            statistical_significance=0.02,
        )
        assert impact.method == CausalMethod.BEFORE_AFTER
        assert impact.causal_effect_size == 0.15
        assert impact.statistical_significance == 0.02

    def test_causal_impact_to_dict(self, tenant_id, outcome_def_id, decision_id):
        impact = CausalImpactAnalysis(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            outcome_id=outcome_def_id,
            decision_id=decision_id,
            method=CausalMethod.DIFF_IN_DIFF,
            causal_effect_size=0.08,
        )
        d = impact.to_dict()
        assert d["method"] == "diff_in_diff"
        assert d["causal_effect_size"] == 0.08


class TestFeatureDefinition:
    def test_create_feature(self, tenant_id, feature_id):
        feat = FeatureDefinition(
            id=feature_id,
            tenant_id=tenant_id,
            name="patient_age",
            namespace="clinical",
            description="Patient age in years",
            feature_type="aggregation",
            value_type="float",
            entity_type="patient",
            refresh_frequency="daily",
            status="active",
        )
        assert feat.name == "patient_age"
        assert feat.feature_type == "aggregation"
        assert feat.status == "active"

    def test_feature_to_dict(self, tenant_id, feature_id):
        feat = FeatureDefinition(
            id=feature_id,
            tenant_id=tenant_id,
            name="diagnosis_code",
            feature_type="point_in_time",
            value_type="string",
        )
        d = feat.to_dict()
        assert d["name"] == "diagnosis_code"
        assert d["feature_type"] == "point_in_time"


class TestModelArtifact:
    def test_create_model(self, tenant_id, model_id):
        model = ModelArtifact(
            id=model_id,
            tenant_id=tenant_id,
            name="RevenueForecaster",
            version="2.1.0",
            model_type="forecast",
            metrics=[{"metric_name": "mape", "value": 0.045}],
            approval_status="under_review",
        )
        assert model.name == "RevenueForecaster"
        assert model.version == "2.1.0"
        assert model.model_type == "forecast"
        assert model.approval_status == "under_review"

    def test_model_to_dict(self, tenant_id, model_id):
        model = ModelArtifact(
            id=model_id,
            tenant_id=tenant_id,
            name="AnomalyDetector",
            version="1.0.0",
            model_type="anomaly",
        )
        d = model.to_dict()
        assert d["name"] == "AnomalyDetector"
        assert d["model_type"] == "anomaly"


class TestOutcomeValueObjects:
    def test_feature_type_values(self):
        assert FeatureType.POINT_IN_TIME in list(FeatureType)
        assert FeatureType.AGGREGATION in list(FeatureType)
        assert FeatureType.DERIVED in list(FeatureType)
        assert FeatureType.EMBEDDING in list(FeatureType)

    def test_model_type_values(self):
        assert ModelType.STATISTICAL in list(ModelType)
        assert ModelType.FORECAST in list(ModelType)
        assert ModelType.ANOMALY in list(ModelType)
        assert ModelType.RECOMMENDATION in list(ModelType)
        assert ModelType.AI_LLM in list(ModelType)

    def test_approval_status_values(self):
        assert ApprovalStatus.DRAFT in list(ApprovalStatus)
        assert ApprovalStatus.UNDER_REVIEW in list(ApprovalStatus)
        assert ApprovalStatus.APPROVED in list(ApprovalStatus)
        assert ApprovalStatus.REJECTED in list(ApprovalStatus)
        assert ApprovalStatus.RETIRED in list(ApprovalStatus)

    def test_fit_quality_values(self):
        assert FitQuality.GOOD in list(FitQuality)
        assert FitQuality.ACCEPTABLE in list(FitQuality)
        assert FitQuality.POOR in list(FitQuality)

    def test_learning_metric_type_values(self):
        assert LearningMetricType.RECOMMENDATION_ACCURACY in list(LearningMetricType)
        assert LearningMetricType.DECISION_ACCURACY in list(LearningMetricType)
        assert LearningMetricType.FORECAST_ACCURACY in list(LearningMetricType)
        assert LearningMetricType.EXECUTIVE_ADOPTION_RATE in list(LearningMetricType)

    def test_acceptance_status_values(self):
        assert AcceptanceStatus.PENDING in list(AcceptanceStatus)
        assert AcceptanceStatus.ACCEPTED in list(AcceptanceStatus)
        assert AcceptanceStatus.REJECTED in list(AcceptanceStatus)
        assert AcceptanceStatus.IMPLEMENTED in list(AcceptanceStatus)

    def test_memory_doc_type_values(self):
        assert MemoryDocType.INSIGHT in list(MemoryDocType)
        assert MemoryDocType.DECISION in list(MemoryDocType)
        assert MemoryDocType.RECOMMENDATION in list(MemoryDocType)
        assert MemoryDocType.OUTCOME in list(MemoryDocType)
        assert MemoryDocType.BRIEFING in list(MemoryDocType)

    def test_measurement_frequency_values(self):
        assert MeasurementFrequency.DAILY in list(MeasurementFrequency)
        assert MeasurementFrequency.WEEKLY in list(MeasurementFrequency)
        assert MeasurementFrequency.MONTHLY in list(MeasurementFrequency)
        assert MeasurementFrequency.QUARTERLY in list(MeasurementFrequency)

    def test_causal_method_values(self):
        assert CausalMethod.BEFORE_AFTER in list(CausalMethod)
        assert CausalMethod.DIFF_IN_DIFF in list(CausalMethod)
        assert CausalMethod.ITS in list(CausalMethod)
        assert CausalMethod.SYNTHETIC_CONTROL in list(CausalMethod)
