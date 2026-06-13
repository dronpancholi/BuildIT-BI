"""
Comprehensive test suite for the Intelligence Engine.
Tests all intelligence services, entities, and value objects.
"""
import uuid
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

# Import intelligence entities and services
from app.domain.intelligence import (
    IntelligenceArtifact,
    Insight,
    RootCause,
    Anomaly,
    Opportunity,
    Recommendation,
    Briefing,
    RootCauseAnalysisResult,
    IntelligenceNode,
    IntelligenceRelationship,
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
)
from app.domain.intelligence.value_objects import (
    ArtifactType,
    ArtifactStatus,
    ConfidenceLabel,
    ImpactLabel,
    PriorityLabel,
    UrgencyLabel,
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
    EvidenceType,
    RelationshipType,
    IntelligenceNodeType,
    GraphNodeStatus,
    RelationshipDirection,
    PeriodType,
    ScopeType,
    GenerationSource,
)
from app.domain.intelligence.services import (
    IntelligenceScoreCalculator,
    ScoringContext,
    RootCauseEngine,
    AnomalyDetectionEngine,
    InsightDiscoveryEngine,
    OpportunityDiscoveryEngine,
    RecommendationEngine,
    ComputationScope,
    TimePeriod,
    SegmentData,
    MetricTimeSeries,
    OpportunityData,
)
from app.domain.intelligence.services.graph import IntelligenceGraphService


# ============================
# VALUE OBJECT TESTS
# ============================

class TestIntelligenceScores:
    """Tests for IntelligenceScores value object."""

    def test_create_scores(self):
        scores = IntelligenceScores(
            confidence=0.85,
            impact=0.72,
            priority=0.78,
            urgency=0.65,
            confidence_label=ConfidenceLabel.HIGH,
            impact_label=ImpactLabel.HIGH,
            priority_label=PriorityLabel.P1,
            urgency_label=UrgencyLabel.SOON,
        )
        assert scores.confidence == 0.85
        assert scores.impact == 0.72
        assert scores.priority_label == PriorityLabel.P1

    def test_scores_to_dict(self):
        scores = IntelligenceScores(
            confidence=0.85,
            impact=0.72,
            priority=0.78,
            urgency=0.65,
            confidence_label=ConfidenceLabel.HIGH,
            impact_label=ImpactLabel.HIGH,
            priority_label=PriorityLabel.P1,
            urgency_label=UrgencyLabel.SOON,
        )
        d = scores.to_dict()
        assert d["confidence"] == 0.85
        assert d["priority_label"] == "P1"


class TestEvidence:
    """Tests for Evidence value object."""

    def test_create_evidence(self):
        evidence = Evidence(
            evidence_type=EvidenceType.DATA_POINT,
            title="Test Evidence",
            description="Test description",
            data={"key": "value"},
        )
        assert evidence.title == "Test Evidence"
        assert evidence.evidence_type == EvidenceType.DATA_POINT

    def test_evidence_to_dict(self):
        evidence = Evidence(
            evidence_type=EvidenceType.STATISTICAL_TEST,
            title="Statistical Test",
            description="p < 0.05",
            data={"p_value": 0.03},
        )
        d = evidence.to_dict()
        assert d["evidence_type"] == "statistical_test"
        assert d["data"]["p_value"] == 0.03


# ============================
# ENTITY TESTS
# ============================

class TestInsight:
    """Tests for Insight entity."""

    def test_create_insight(self):
        insight = Insight(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.INSIGHT,
            insight_type=InsightType.REVENUE_GROWTH,
            title="Test Insight",
            summary="Test summary",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert insight.insight_type == InsightType.REVENUE_GROWTH
        assert insight.status == ArtifactStatus.DISCOVERED

    def test_insight_validate(self):
        insight = Insight(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.INSIGHT,
            insight_type=InsightType.REVENUE_GROWTH,
            title="Test Insight",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        user_id = uuid.uuid4()
        insight.validate(user_id)
        assert insight.status == ArtifactStatus.VALIDATED
        assert insight.validated_by == user_id

    def test_insight_publish(self):
        insight = Insight(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.INSIGHT,
            insight_type=InsightType.REVENUE_GROWTH,
            title="Test Insight",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        insight.publish()
        assert insight.status == ArtifactStatus.PUBLISHED
        assert insight.published_at is not None

    def test_insight_to_dict(self):
        insight = Insight(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.INSIGHT,
            insight_type=InsightType.REVENUE_GROWTH,
            title="Test Insight",
            summary="Test summary",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        d = insight.to_dict()
        assert d["insight_type"] == "revenue_growth"
        assert d["title"] == "Test Insight"


class TestRootCause:
    """Tests for RootCause entity."""

    def test_create_root_cause(self):
        cause = RootCause(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.ROOT_CAUSE,
            cause_type=CauseType.REVENUE_DEPARTMENT,
            cause_name="Test Cause",
            cause_description="Test description",
            attribution_weight=0.65,
            attribution_absolute=-340000,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert cause.cause_type == CauseType.REVENUE_DEPARTMENT
        assert cause.attribution_weight == 0.65

    def test_root_cause_primary(self):
        cause = RootCause(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.ROOT_CAUSE,
            cause_type=CauseType.REVENUE_DEPARTMENT,
            cause_name="Primary Cause",
            cause_description="Primary cause description",
            attribution_weight=0.65,
            is_primary_cause=True,
            cause_rank=1,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert cause.is_primary_cause is True
        assert cause.cause_rank == 1


class TestAnomaly:
    """Tests for Anomaly entity."""

    def test_create_anomaly(self):
        anomaly = Anomaly(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.ANOMALY,
            anomaly_type=AnomalyType.DROP,
            category=AnomalyCategory.REVENUE,
            severity=AnomalySeverity.CRITICAL,
            title="Revenue Drop",
            description="Revenue dropped 23%",
            metric_id=uuid.uuid4(),
            metric_code="REVENUE",
            observed_value=42000,
            expected_value=54500,
            deviation_absolute=-12500,
            deviation_percent=-23.0,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert anomaly.anomaly_type == AnomalyType.DROP
        assert anomaly.severity == AnomalySeverity.CRITICAL

    def test_anomaly_update_status(self):
        anomaly = Anomaly(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.ANOMALY,
            anomaly_type=AnomalyType.DROP,
            category=AnomalyCategory.REVENUE,
            severity=AnomalySeverity.HIGH,
            title="Test Anomaly",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        anomaly.anomaly_status = AnomalyStatus.INVESTIGATING
        assert anomaly.anomaly_status == AnomalyStatus.INVESTIGATING


class TestOpportunity:
    """Tests for Opportunity entity."""

    def test_create_opportunity(self):
        opportunity = Opportunity(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.OPPORTUNITY,
            opportunity_type=OpportunityType.REVENUE_GROWTH,
            category=OpportunityCategory.REVENUE,
            title="Revenue Growth Opportunity",
            summary="Improve revenue by $2.1M",
            estimated_value=2100000,
            value_unit="annual",
            effort_level=EffortLevel.MEDIUM,
            risk_level=RiskLevel.MEDIUM,
            time_to_realize_months=6,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert opportunity.estimated_value == 2100000
        assert opportunity.effort_level == EffortLevel.MEDIUM

    def test_opportunity_realize(self):
        opportunity = Opportunity(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.OPPORTUNITY,
            opportunity_type=OpportunityType.REVENUE_GROWTH,
            category=OpportunityCategory.REVENUE,
            title="Test Opportunity",
            estimated_value=100000,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        opportunity.opportunity_status = OpportunityStatus.REALIZED
        opportunity.realized_value = 95000
        opportunity.realized_at = datetime.now()
        assert opportunity.opportunity_status == OpportunityStatus.REALIZED
        assert opportunity.realized_value == 95000


class TestRecommendation:
    """Tests for Recommendation entity."""

    def test_create_recommendation(self):
        recommendation = Recommendation(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.RECOMMENDATION,
            recommendation_type=RecommendationType.REVENUE_OPTIMIZATION,
            title="Revenue Optimization",
            summary="Improve revenue processes",
            expected_impact_value=500000,
            impact_direction=ImpactDirection.INCREASE_REVENUE,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert recommendation.expected_impact_value == 500000
        assert recommendation.impact_direction == ImpactDirection.INCREASE_REVENUE

    def test_recommendation_approve(self):
        recommendation = Recommendation(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.RECOMMENDATION,
            recommendation_type=RecommendationType.REVENUE_OPTIMIZATION,
            title="Test Recommendation",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        recommendation.recommendation_status = RecommendationStatus.APPROVED
        recommendation.reviewed_by = uuid.uuid4()
        recommendation.reviewed_at = datetime.now()
        assert recommendation.recommendation_status == RecommendationStatus.APPROVED


# ============================
# SERVICE TESTS
# ============================

class TestIntelligenceScoreCalculator:
    """Tests for IntelligenceScoreCalculator service."""

    @pytest.fixture
    def calculator(self):
        return IntelligenceScoreCalculator()

    @pytest.mark.asyncio
    async def test_calculate_scores(self, calculator):
        context = ScoringContext(
            tenant_id=uuid.uuid4(),
            artifact_data={
                "p_value": 0.03,
                "dollar_impact": 500000,
                "severity": "high",
                "sample_size": 100,
                "historical_consistency": 0.8,
            }
        )
        scores = await calculator.calculate_scores(
            ArtifactType.INSIGHT,
            context.artifact_data,
            context
        )
        assert 0.0 <= scores.confidence <= 1.0
        assert 0.0 <= scores.impact <= 1.0
        assert 0.0 <= scores.urgency <= 1.0
        assert 0.0 <= scores.priority <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_confidence(self, calculator):
        confidence, label = await calculator.calculate_confidence(
            ArtifactType.INSIGHT,
            {"p_value": 0.03, "sample_size": 100}
        )
        assert 0.0 <= confidence <= 1.0
        assert label in [ConfidenceLabel.HIGH, ConfidenceLabel.MEDIUM, ConfidenceLabel.LOW]

    @pytest.mark.asyncio
    async def test_calculate_impact(self, calculator):
        impact, label = await calculator.calculate_impact(
            ArtifactType.INSIGHT,
            {"dollar_impact": 500000, "severity": "high"}
        )
        assert 0.0 <= impact <= 1.0
        assert label in [ImpactLabel.CRITICAL, ImpactLabel.HIGH, ImpactLabel.MEDIUM, ImpactLabel.LOW]

    @pytest.mark.asyncio
    async def test_calculate_urgency(self, calculator):
        urgency, label = await calculator.calculate_urgency(
            ArtifactType.INSIGHT,
            {"trend": "worsening", "time_to_impact_days": 7}
        )
        assert 0.0 <= urgency <= 1.0
        assert label in [UrgencyLabel.IMMEDIATE, UrgencyLabel.SOON, UrgencyLabel.SCHEDULED, UrgencyLabel.BACKLOG]

    @pytest.mark.asyncio
    async def test_calculate_priority(self, calculator):
        priority, label = await calculator.calculate_priority(
            confidence=0.85,
            impact=0.72,
            urgency=0.65
        )
        assert 0.0 <= priority <= 1.0
        assert label in [PriorityLabel.P0, PriorityLabel.P1, PriorityLabel.P2, PriorityLabel.P3]


class TestRootCauseEngine:
    """Tests for RootCauseEngine service."""

    @pytest.fixture
    def engine(self):
        return RootCauseEngine()

    @pytest.mark.asyncio
    async def test_analyze_metric_change(self, engine):
        scope = ComputationScope(
            tenant_id=uuid.uuid4(),
            hospital_id=uuid.uuid4(),
        )

        current_period = TimePeriod(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 31),
        )

        comparison_period = TimePeriod(
            start=datetime(2023, 12, 1),
            end=datetime(2023, 12, 31),
        )

        segments = [
            SegmentData(
                segment_name="Cardiology",
                segment_id=uuid.uuid4(),
                current_value=550000,
                previous_value=890000,
                change_absolute=-340000,
                change_percent=0,
                dimension="department",
            ),
            SegmentData(
                segment_name="Radiology",
                segment_id=uuid.uuid4(),
                current_value=200000,
                previous_value=297000,
                change_absolute=-97000,
                change_percent=0,
                dimension="department",
            ),
        ]

        result = await engine.analyze_metric_change(
            metric_id=uuid.uuid4(),
            metric_code="NET_REVENUE",
            current_value=2450000,
            previous_value=2990000,
            current_period=current_period,
            comparison_period=comparison_period,
            scope=scope,
            segments=segments,
        )

        assert result is not None
        assert result.change_absolute == -540000
        assert result.all_causes is not None
        assert len(result.all_causes) > 0


class TestAnomalyDetectionEngine:
    """Tests for AnomalyDetectionEngine service."""

    @pytest.fixture
    def engine(self):
        return AnomalyDetectionEngine()

    @pytest.mark.asyncio
    async def test_detect_anomalies(self, engine):
        data = MetricTimeSeries(
            metric_id=uuid.uuid4(),
            metric_code="REVENUE",
            values=[100, 105, 102, 108, 110, 50, 105, 103],
            timestamps=[
                datetime(2024, 1, 1),
                datetime(2024, 1, 2),
                datetime(2024, 1, 3),
                datetime(2024, 1, 4),
                datetime(2024, 1, 5),
                datetime(2024, 1, 6),  # Anomaly
                datetime(2024, 1, 7),
                datetime(2024, 1, 8),
            ],
        )

        anomalies = await engine.detect_anomalies(data=data)

        assert anomalies is not None
        assert isinstance(anomalies, list)

    @pytest.mark.asyncio
    async def test_detect_statistical_anomalies(self, engine):
        data = MetricTimeSeries(
            metric_id=uuid.uuid4(),
            metric_code="REVENUE",
            values=[100, 105, 102, 108, 110, 50, 105, 103],
            timestamps=[
                datetime(2024, 1, 1),
                datetime(2024, 1, 2),
                datetime(2024, 1, 3),
                datetime(2024, 1, 4),
                datetime(2024, 1, 5),
                datetime(2024, 1, 6),
                datetime(2024, 1, 7),
                datetime(2024, 1, 8),
            ],
        )

        anomalies = await engine.detect_statistical_anomalies(data=data)

        assert anomalies is not None


class TestInsightDiscoveryEngine:
    """Tests for InsightDiscoveryEngine service."""

    @pytest.fixture
    def engine(self):
        return InsightDiscoveryEngine()

    @pytest.mark.asyncio
    async def test_discover_trend_insights(self, engine):
        metrics = [
            MetricTimeSeries(
                metric_id=uuid.uuid4(),
                metric_code="NET_REVENUE",
                values=[100, 105, 110, 115, 120, 125],
                timestamps=[
                    datetime(2024, 1, 1),
                    datetime(2024, 2, 1),
                    datetime(2024, 3, 1),
                    datetime(2024, 4, 1),
                    datetime(2024, 5, 1),
                    datetime(2024, 6, 1),
                ],
            )
        ]

        period = TimePeriod(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 6, 30),
        )

        insights = await engine.discover_trend_insights(
            tenant_id=uuid.uuid4(),
            metrics=metrics,
            period=period,
        )

        assert insights is not None
        assert isinstance(insights, list)


class TestOpportunityDiscoveryEngine:
    """Tests for OpportunityDiscoveryEngine service."""

    @pytest.fixture
    def engine(self):
        return OpportunityDiscoveryEngine()

    @pytest.mark.asyncio
    async def test_discover_opportunities(self, engine):
        opportunities_data = [
            OpportunityData(
                metric_id=uuid.uuid4(),
                metric_code="CLAIMS_APPROVAL",
                current_value=78,
                target_value=90,
                benchmark_value=92,
                volume=1000000,
                category="revenue",
            )
        ]

        opportunities = await engine.discover_opportunities(
            tenant_id=uuid.uuid4(),
            opportunities_data=opportunities_data,
        )

        assert opportunities is not None
        assert isinstance(opportunities, list)


class TestRecommendationEngine:
    """Tests for RecommendationEngine service."""

    @pytest.fixture
    def engine(self):
        return RecommendationEngine()

    @pytest.mark.asyncio
    async def test_generate_recommendations_from_insight(self, engine):
        insight_data = {
            "id": str(uuid.uuid4()),
            "insight_type": "revenue_decline",
            "change_percent": -8.2,
            "current_value": 2450000,
            "metric_code": "NET_REVENUE",
            "metric_id": str(uuid.uuid4()),
            "title": "Revenue decline detected",
        }

        recommendations = await engine.generate_recommendations_from_insight(
            tenant_id=uuid.uuid4(),
            insight_data=insight_data,
        )

        assert recommendations is not None
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0


# ============================
# GRAPH TESTS
# ============================

class TestIntelligenceGraphService:
    """Tests for IntelligenceGraphService."""

    @pytest.fixture
    def service(self):
        return IntelligenceGraphService()

    @pytest.mark.asyncio
    async def test_add_node(self, service):
        node = await service.add_node(
            tenant_id=uuid.uuid4(),
            node_type="metric",
            entity_type="MetricDefinition",
            entity_id=uuid.uuid4(),
            label="Net Revenue",
        )
        assert node is not None
        assert node.label == "Net Revenue"

    @pytest.mark.asyncio
    async def test_add_relationship(self, service):
        # Create nodes first
        node1 = await service.add_node(
            tenant_id=uuid.uuid4(),
            node_type="metric",
            entity_type="MetricDefinition",
            entity_id=uuid.uuid4(),
            label="Metric A",
        )
        node2 = await service.add_node(
            tenant_id=uuid.uuid4(),
            node_type="insight",
            entity_type="Insight",
            entity_id=uuid.uuid4(),
            label="Insight B",
        )

        # Add relationship
        rel = await service.add_relationship(
            tenant_id=node1.tenant_id,
            source_id=node1.id,
            target_id=node2.id,
            relationship_type="causes",
            confidence=0.85,
        )

        assert rel is not None
        assert rel.relationship_type == "causes"

    @pytest.mark.asyncio
    async def test_get_related_nodes(self, service):
        # Create nodes and relationship
        node1 = await service.add_node(
            tenant_id=uuid.uuid4(),
            node_type="metric",
            entity_type="MetricDefinition",
            entity_id=uuid.uuid4(),
            label="Metric A",
        )
        node2 = await service.add_node(
            tenant_id=uuid.uuid4(),
            node_type="insight",
            entity_type="Insight",
            entity_id=uuid.uuid4(),
            label="Insight B",
        )

        await service.add_relationship(
            tenant_id=node1.tenant_id,
            source_id=node1.id,
            target_id=node2.id,
            relationship_type="causes",
        )

        related = await service.get_related_nodes(node1.id)

        assert len(related) == 1
        assert related[0].id == node2.id


# ============================
# ENTITY RELATIONSHIP TESTS
# ============================

class TestIntelligenceRelationships:
    """Tests for intelligence entity relationships."""

    def test_insight_to_root_cause(self):
        insight = Insight(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.INSIGHT,
            insight_type=InsightType.REVENUE_DECLINE,
            title="Revenue Decline Insight",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )

        root_cause = RootCause(
            id=uuid.uuid4(),
            tenant_id=insight.tenant_id,
            artifact_type=ArtifactType.ROOT_CAUSE,
            cause_type=CauseType.REVENUE_DEPARTMENT,
            cause_name="Department Decline",
            cause_description="Department revenue declined",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )

        # Link insight to root cause
        insight.related_root_cause_ids.append(root_cause.id)

        assert root_cause.id in insight.related_root_cause_ids

    def test_anomaly_to_recommendation(self):
        anomaly = Anomaly(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.ANOMALY,
            anomaly_type=AnomalyType.DROP,
            category=AnomalyCategory.REVENUE,
            severity=AnomalySeverity.HIGH,
            title="Revenue Anomaly",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )

        recommendation = Recommendation(
            id=uuid.uuid4(),
            tenant_id=anomaly.tenant_id,
            artifact_type=ArtifactType.RECOMMENDATION,
            recommendation_type=RecommendationType.REVENUE_OPTIMIZATION,
            title="Investigate Anomaly",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )

        # Link anomaly to recommendation
        anomaly.recommendation_id = recommendation.id

        assert anomaly.recommendation_id == recommendation.id

    def test_opportunity_to_recommendation(self):
        opportunity = Opportunity(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.OPPORTUNITY,
            opportunity_type=OpportunityType.REVENUE_GROWTH,
            category=OpportunityCategory.REVENUE,
            title="Revenue Opportunity",
            estimated_value=100000,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )

        recommendation = Recommendation(
            id=uuid.uuid4(),
            tenant_id=opportunity.tenant_id,
            artifact_type=ArtifactType.RECOMMENDATION,
            recommendation_type=RecommendationType.REVENUE_OPTIMIZATION,
            title="Realize Opportunity",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )

        # Link opportunity to recommendation
        opportunity.related_recommendation_ids.append(recommendation.id)

        assert recommendation.id in opportunity.related_recommendation_ids


class TestNarrativeEngine:
    """Tests for the Narrative Engine."""

    def test_narrative_engine_import(self):
        from app.domain.intelligence.services.narrative_engine import NarrativeEngine
        assert NarrativeEngine is not None

    def test_narrative_engine_instantiation(self):
        from app.domain.intelligence.services.narrative_engine import NarrativeEngine
        engine = NarrativeEngine()
        assert engine is not None

    def test_narrative_engine_has_methods(self):
        from app.domain.intelligence.services.narrative_engine import NarrativeEngine
        engine = NarrativeEngine()
        assert hasattr(engine, 'generate_metric_narrative')

    def test_metric_narrative_generation(self):
        from app.domain.intelligence.services.narrative_engine import NarrativeEngine
        engine = NarrativeEngine()
        if hasattr(engine, 'generate_narrative'):
            result = engine.generate_narrative(
                metric_name="Revenue",
                current_value=500000,
                previous_value=450000,
                change_percent=11.1,
            )
            assert isinstance(result, str)
            assert len(result) > 0


class TestBriefingEngine:
    """Tests for the Briefing Engine."""

    def test_briefing_engine_import(self):
        from app.domain.intelligence.services.briefing_engine import BriefingEngine
        assert BriefingEngine is not None

    def test_briefing_engine_instantiation(self):
        from app.domain.intelligence.services.briefing_engine import BriefingEngine
        engine = BriefingEngine()
        assert engine is not None

    def test_briefing_engine_has_methods(self):
        from app.domain.intelligence.services.briefing_engine import BriefingEngine
        engine = BriefingEngine()
        assert hasattr(engine, 'generate_daily_briefing') or hasattr(engine, 'generate_briefing')


class TestIntelligenceValueObjects:
    """Extended tests for intelligence value objects."""

    def test_all_artifact_types_exist(self):
        for at in ArtifactType:
            assert isinstance(at.value, str)

    def test_all_artifact_statuses_exist(self):
        for s in ArtifactStatus:
            assert isinstance(s.value, str)

    def test_confidence_labels(self):
        assert ConfidenceLabel.HIGH.value == "high"
        assert ConfidenceLabel.MEDIUM.value == "medium"
        assert ConfidenceLabel.LOW.value == "low"

    def test_impact_labels(self):
        assert ImpactLabel.CRITICAL.value == "critical"
        assert ImpactLabel.HIGH.value == "high"

    def test_priority_labels(self):
        assert PriorityLabel.P0.value == "P0"
        assert PriorityLabel.P3.value == "P3"

    def test_cause_types_completeness(self):
        assert CauseType.REVENUE_VOLUME.value == "revenue_volume"
        assert CauseType.EXPENSE_RATE.value == "expense_rate"

    def test_anomaly_severities(self):
        assert AnomalySeverity.CRITICAL.value is not None
        assert AnomalySeverity.HIGH.value is not None
        assert AnomalySeverity.MEDIUM.value is not None
        assert AnomalySeverity.LOW.value is not None

    def test_opportunity_statuses(self):
        assert OpportunityStatus.IDENTIFIED.value is not None
        assert OpportunityStatus.REALIZED.value is not None

    def test_recommendation_statuses(self):
        assert RecommendationStatus.PROPOSED.value is not None
        assert RecommendationStatus.COMPLETED.value is not None

    def test_briefing_types(self):
        assert BriefingType.DAILY.value is not None
        assert BriefingType.WEEKLY.value is not None
        assert BriefingType.MONTHLY.value is not None


class TestIntelligenceEntitiesExtended:
    """Extended tests for intelligence entity lifecycle."""

    def test_insight_status_lifecycle(self):
        insight = Insight(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.INSIGHT,
            insight_type=InsightType.SUSTAINED_TREND,
            title="Test Insight",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert insight.status == ArtifactStatus.DISCOVERED

        insight.validate(user_id=uuid.uuid4())
        assert insight.status == ArtifactStatus.VALIDATED

        insight.publish()
        assert insight.status == ArtifactStatus.PUBLISHED

    def test_anomaly_lifecycle(self):
        anomaly = Anomaly(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.ANOMALY,
            anomaly_type=AnomalyType.SPIKE,
            title="Test Anomaly",
            severity=AnomalySeverity.HIGH,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert anomaly.status == ArtifactStatus.DISCOVERED

        anomaly.validate(user_id=uuid.uuid4())
        assert anomaly.status == ArtifactStatus.VALIDATED

    def test_opportunity_lifecycle(self):
        opp = Opportunity(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.OPPORTUNITY,
            opportunity_type=OpportunityType.REVENUE_GROWTH,
            title="Test Opportunity",
            estimated_value=50000,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert opp.status == ArtifactStatus.DISCOVERED

        opp.validate(user_id=uuid.uuid4())
        assert opp.status == ArtifactStatus.VALIDATED

        opp.publish()
        assert opp.status == ArtifactStatus.PUBLISHED

    def test_recommendation_lifecycle(self):
        rec = Recommendation(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.RECOMMENDATION,
            recommendation_type=RecommendationType.REVENUE_OPTIMIZATION,
            title="Test Recommendation",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert rec.status == ArtifactStatus.DISCOVERED

        rec.validate(user_id=uuid.uuid4())
        assert rec.status == ArtifactStatus.VALIDATED

    def test_briefing_creation(self):
        briefing = Briefing(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            artifact_type=ArtifactType.BRIEFING,
            briefing_type=BriefingType.DAILY,
            title="Daily Briefing",
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert briefing.status == ArtifactStatus.DISCOVERED
        assert briefing.briefing_type == BriefingType.DAILY

    def test_intelligence_node_creation(self):
        node = IntelligenceNode(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            node_type="insight",
            entity_type="insight",
            entity_id=uuid.uuid4(),
            label="Revenue Insight",
        )
        assert node.node_type == "insight"
        assert node.importance_score == 0

    def test_intelligence_relationship_creation(self):
        rel = IntelligenceRelationship(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            source_node_id=uuid.uuid4(),
            target_node_id=uuid.uuid4(),
            relationship_type="caused_by",
        )
        assert rel.relationship_type == "caused_by"
        assert rel.correlation_strength == 0


class TestScoringFramework:
    """Tests for the scoring framework."""

    def test_intelligence_scores_to_dict(self):
        scores = IntelligenceScores(
            confidence=0.9,
            impact=0.8,
            priority=0.85,
            urgency=0.7,
            confidence_label=ConfidenceLabel.HIGH,
            impact_label=ImpactLabel.CRITICAL,
            priority_label=PriorityLabel.P0,
            urgency_label=UrgencyLabel.IMMEDIATE,
        )
        d = scores.to_dict()
        assert d["confidence"] == 0.9
        assert d["impact"] == 0.8
        assert d["urgency"] == 0.7
        assert d["priority"] == 0.85
        assert d["confidence_label"] == "high"
        assert d["impact_label"] == "critical"
        assert d["priority_label"] == "P0"
        assert d["urgency_label"] == "immediate"

    def test_evidence_to_dict(self):
        evidence = Evidence(
            evidence_type=EvidenceType.STATISTICAL_TEST,
            title="Z-score Test",
            description="Z-score > 3",
            weight=0.95,
        )
        d = evidence.to_dict()
        assert d["evidence_type"] == "statistical_test"
        assert d["title"] == "Z-score Test"
        assert d["weight"] == 0.95

    def test_action_step_to_dict(self):
        step = ActionStep(
            step_number=1,
            action_description="Investigate revenue data",
            owner_role="analyst",
            estimated_effort_hours=2.0,
        )
        d = step.to_dict()
        assert d["step_number"] == 1
        assert d["action_description"] == "Investigate revenue data"
        assert d["owner_role"] == "analyst"

    def test_business_impact_to_dict(self):
        impact = BusinessImpact(
            impact_type="revenue_loss",
            impact_amount=50000,
            impact_unit="USD",
            affected_scope="Emergency Department",
        )
        d = impact.to_dict()
        assert d["impact_type"] == "revenue_loss"
        assert d["impact_amount"] == 50000
        assert d["impact_unit"] == "USD"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
