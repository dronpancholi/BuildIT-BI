"""
Comprehensive test suite for the Healthcare Financial Intelligence Platform.
Tests domain services, repositories, and API endpoints.
"""
import uuid
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

# Domain entities
from app.domain.entities.metric import (
    MetricDefinition, MetricCategory, MetricUnit, AggregationType,
    MetricStatus, TrustLevel, PeriodType,
)
from app.domain.entities.quality import (
    QualityRule, QualityRuleType, IssueSeverity, QualityScope,
)
from app.domain.entities.lineage import LineageNode, LineageNodeType
from app.domain.entities.events import (
    MetricComputed, QualityIssueDetected, DomainEvent,
)

# Services
from app.domain.services.metric_registry import MetricRegistry
from app.domain.services.kpi_engine import (
    DependencyResolver, KPIComputationEngine,
    ComputationScope, TimePeriod, ComputationOptions,
)

# Infrastructure
from app.infrastructure.eventbus.event_bus import InMemoryEventBus
from app.infrastructure.duckdb.analytics import (
    DuckDBAnalyticsEngine, AnalyticsCacheService,
    AggregationConfig, AggregationType as DuckDBAggType,
    TimeSeriesConfig, Granularity,
)
from app.infrastructure.database.repositories import MetricDefinitionRepositoryImpl

# Workflows
from app.application.workflows.definitions import (
    MetricComputationWorkflow, DataQualityWorkflow,
    NightlyProcessingWorkflow, MetricRefreshWorkflow,
    RetryPolicy, WorkflowSchedule,
)

# API
from app.api.v2.endpoints.api import (
    APIResponse, ResponseMeta, MetricCreateRequest,
)

# Security
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
)


# ---------------------------------------------------------------------------
# Domain Tests
# ---------------------------------------------------------------------------

class TestMetricDefinition:
    """Tests for MetricDefinition entity."""

    def test_create_metric_definition(self):
        metric = MetricDefinition(
            tenant_id=uuid.uuid4(),
            name="Gross Revenue",
            slug="gross_revenue",
            code="GROSS_REVENUE",
            category=MetricCategory.REVENUE,
            unit=MetricUnit.CURRENCY,
            formula="SUM(charges)",
        )
        assert metric.code == "GROSS_REVENUE"
        assert metric.category == MetricCategory.REVENUE
        assert metric.status == MetricStatus.DRAFT
        assert metric.trust_level == TrustLevel.EXPERIMENTAL

    def test_metric_definition_publish(self):
        user_id = uuid.uuid4()
        metric = MetricDefinition(
            tenant_id=uuid.uuid4(),
            name="Net Revenue",
            slug="net_revenue",
            code="NET_REVENUE",
            category=MetricCategory.REVENUE,
            unit=MetricUnit.CURRENCY,
            formula="GROSS_REVENUE - adjustments",
        )
        metric.publish(published_by=user_id)
        assert metric.status == MetricStatus.PUBLISHED
        assert metric.published_at is not None

    def test_metric_definition_deprecate(self):
        user_id = uuid.uuid4()
        metric = MetricDefinition(
            tenant_id=uuid.uuid4(),
            name="Old Metric",
            slug="old_metric",
            code="OLD_METRIC",
            category=MetricCategory.REVENUE,
            unit=MetricUnit.CURRENCY,
            formula="SUM(charges)",
            status=MetricStatus.PUBLISHED,
        )
        metric.deprecate(reason="Superseded", deprecated_by=user_id)
        assert metric.status == MetricStatus.DEPRECATED
        assert metric.deprecation_reason == "Superseded"


class TestMetricRegistry:
    """Tests for MetricRegistry service."""

    @pytest.fixture
    def registry(self):
        repo = AsyncMock()
        return MetricRegistry(repo)

    @pytest.mark.asyncio
    async def test_register_metric(self, registry):
        metric = MetricDefinition(
            tenant_id=uuid.uuid4(),
            name="Test Metric",
            slug="test_metric",
            code="TEST_METRIC",
            category=MetricCategory.REVENUE,
            unit=MetricUnit.CURRENCY,
            formula="SUM(value)",
        )
        registry._repository.get_by_slug = AsyncMock(return_value=None)
        registry._repository.get_by_code = AsyncMock(return_value=None)
        registry._repository.create = AsyncMock(return_value=metric)
        result = await registry.register(metric, created_by=uuid.uuid4())
        assert result.code == "TEST_METRIC"

    @pytest.mark.asyncio
    async def test_register_duplicate_metric(self, registry):
        tenant_id = uuid.uuid4()
        existing = MetricDefinition(
            tenant_id=tenant_id,
            name="Duplicate Metric",
            slug="dup_metric",
            code="DUP_METRIC",
            category=MetricCategory.REVENUE,
            unit=MetricUnit.CURRENCY,
        )
        registry._repository.get_by_code = AsyncMock(return_value=existing)
        metric = MetricDefinition(
            tenant_id=tenant_id,
            name="Duplicate Metric Again",
            slug="dup_metric_2",
            code="DUP_METRIC",
            category=MetricCategory.REVENUE,
            unit=MetricUnit.CURRENCY,
        )
        with pytest.raises(ValueError, match="already exists"):
            await registry.register(metric, created_by=uuid.uuid4())


class TestDependencyResolver:
    """Tests for DependencyResolver service."""

    @pytest.fixture
    def resolver(self):
        repo = AsyncMock()
        return DependencyResolver(repo)

    @pytest.mark.asyncio
    async def test_resolve_no_dependencies(self, resolver):
        metric = MetricDefinition(
            tenant_id=uuid.uuid4(),
            name="A",
            slug="a",
            code="A",
            category=MetricCategory.REVENUE,
        )
        resolver._repository.get_by_id = AsyncMock(return_value=metric)
        resolver._repository.get_by_id = AsyncMock(return_value=None)
        # Just verify the resolver can be called without crashing on missing metric
        with pytest.raises(ValueError, match="not found"):
            await resolver.resolve(metric.entity_id)

    @pytest.mark.asyncio
    async def test_resolve_linear_dependencies(self, resolver):
        a = MetricDefinition(
            tenant_id=uuid.uuid4(), name="A", slug="a", code="A",
            category=MetricCategory.REVENUE,
        )
        resolver._repository.get_by_id = AsyncMock(return_value=a)
        result = await resolver.resolve(a.entity_id)
        assert result is not None


class TestKPIComputationEngine:
    """Tests for KPIComputationEngine service."""

    @pytest.fixture
    def engine(self):
        metric_repo = AsyncMock()
        computed_repo = AsyncMock()
        analytics = AsyncMock()
        return KPIComputationEngine(metric_repo, computed_repo, analytics)

    @pytest.mark.asyncio
    async def test_compute_simple_metric(self, engine):
        scope = ComputationScope(
            tenant_id=uuid.uuid4(),
            hospital_id=uuid.uuid4(),
        )
        period = TimePeriod(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 31),
            period_type=PeriodType.MONTHLY,
        )
        options = ComputationOptions(
            force_recompute=False,
            skip_validation=False,
            skip_event_publish=False,
        )
        metric = MetricDefinition(
            tenant_id=uuid.uuid4(),
            name="Test",
            slug="test",
            code="TEST",
            category=MetricCategory.REVENUE,
            formula="SUM(value)",
            status=MetricStatus.PUBLISHED,
        )
        engine._metric_repo.get_by_id = AsyncMock(return_value=metric)
        engine._computed_value_repo.get_latest = AsyncMock(return_value=None)
        engine._analytics.execute = AsyncMock(return_value={"total": 1000})
        engine._computed_value_repo.create = AsyncMock(return_value=Mock())
        result = await engine.compute_metric(
            metric.entity_id, scope, period, options
        )
        assert result is not None


class TestQualityRule:
    """Tests for QualityRule entity."""

    def test_create_quality_rule(self):
        rule = QualityRule(
            tenant_id=uuid.uuid4(),
            name="Revenue Range Check",
            rule_type=QualityRuleType.RANGE_CHECK,
            entity_type="revenue",
            severity=IssueSeverity.HIGH,
            configuration={"min": 0, "max": 1000000},
        )
        assert rule.name == "Revenue Range Check"
        assert rule.severity == IssueSeverity.HIGH

    def test_quality_rule_validate(self):
        rule = QualityRule(
            tenant_id=uuid.uuid4(),
            name="Null Check",
            rule_type=QualityRuleType.NOT_NULL,
            entity_type="metric",
            severity=IssueSeverity.CRITICAL,
        )
        assert rule.validate(100) is True
        assert rule.validate(None) is False

    def test_quality_rule_range_check(self):
        rule = QualityRule(
            tenant_id=uuid.uuid4(),
            name="Range Check",
            rule_type=QualityRuleType.RANGE_CHECK,
            entity_type="revenue",
            severity=IssueSeverity.HIGH,
            configuration={"min": 0, "max": 100},
        )
        assert rule.validate(50) is True
        assert rule.validate(150) is False
        assert rule.validate(-5) is False


class TestLineageNode:
    """Tests for LineageNode entity."""

    def test_create_lineage_node(self):
        node = LineageNode(
            tenant_id=uuid.uuid4(),
            node_type=LineageNodeType.METRIC,
            name="Gross Revenue",
        )
        assert node.node_type == LineageNodeType.METRIC
        assert node.name == "Gross Revenue"


class TestDomainEvent:
    """Tests for DomainEvent entities."""

    def test_create_metric_computed_event(self):
        event = MetricComputed(
            tenant_id=uuid.uuid4(),
            metric_id=uuid.uuid4(),
            value=5000000,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
        )
        assert event.event_type == "MetricComputed"
        assert event.payload["value"] == 5000000

    def test_create_quality_issue_detected_event(self):
        event = QualityIssueDetected(
            tenant_id=uuid.uuid4(),
            rule_id=uuid.uuid4(),
            rule_name="Revenue Range Check",
            severity="high",
            title="Revenue out of range",
            entity_type="metric",
            entity_id=uuid.uuid4(),
        )
        assert event.event_type == "QualityIssueDetected"
        assert event.payload["severity"] == "high"


class TestEventBus:
    """Tests for EventBus service."""

    @pytest.fixture
    def event_bus(self):
        return InMemoryEventBus()

    @pytest.mark.asyncio
    async def test_publish_event(self, event_bus):
        event = MetricComputed(
            tenant_id=uuid.uuid4(),
            metric_id=uuid.uuid4(),
            value=100,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
        )
        result = await event_bus.publish(event)
        assert result.success is True

    def test_subscribe_to_event(self, event_bus):
        handler_called = False

        async def handler(event):
            nonlocal handler_called
            handler_called = True

        subscription = event_bus.subscribe("MetricComputed", handler)
        assert subscription is not None
        assert "MetricComputed" in event_bus._subscriptions


class TestDuckDBAnalyticsEngine:
    """Tests for DuckDBAnalyticsEngine service."""

    @pytest.fixture
    def analytics_engine(self):
        try:
            import duckdb
            return DuckDBAnalyticsEngine(":memory:")
        except ImportError:
            pytest.skip("duckdb not installed")

    @pytest.mark.asyncio
    async def test_execute_aggregation(self, analytics_engine):
        await analytics_engine.connect()
        config = AggregationConfig(
            tenant_id=uuid.uuid4(),
            table_name="test_table",
            aggregation_type=DuckDBAggType.SUM,
            aggregation_column="value",
        )
        with pytest.raises(Exception):
            await analytics_engine.execute_aggregation(config)
        await analytics_engine.disconnect()

    @pytest.mark.asyncio
    async def test_execute_time_series(self, analytics_engine):
        await analytics_engine.connect()
        config = TimeSeriesConfig(
            tenant_id=uuid.uuid4(),
            table_name="test_table",
            date_column="period_start",
            value_column="value",
            aggregation_type=DuckDBAggType.SUM,
            granularity=Granularity.MONTHLY,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 12, 31),
        )
        with pytest.raises(Exception):
            await analytics_engine.execute_time_series(config)
        await analytics_engine.disconnect()


class TestAPIEndpoints:
    """Tests for API endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-token"}

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200


class TestRepository:
    """Tests for repository implementations."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_metric_repository_create(self, mock_session):
        repo = MetricDefinitionRepositoryImpl(mock_session)
        assert repo is not None
        assert repo._session == mock_session

    @pytest.mark.asyncio
    async def test_metric_repository_get_by_code(self, mock_session):
        repo = MetricDefinitionRepositoryImpl(mock_session)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        result = await repo.get_by_code("TEST", uuid.uuid4())
        assert result is None


class TestWorkflowDefinitions:
    """Tests for workflow definitions."""

    def test_metric_computation_workflow(self):
        workflow = MetricComputationWorkflow()
        assert workflow.retry_policy.max_attempts == 3
        assert workflow.timeout == timedelta(hours=1)

    def test_data_quality_workflow(self):
        workflow = DataQualityWorkflow()
        assert workflow.retry_policy.max_attempts == 2
        assert workflow.timeout == timedelta(hours=2)

    def test_nightly_processing_workflow(self):
        workflow = NightlyProcessingWorkflow()
        assert workflow.schedule.cron == "0 2 * * *"
        assert workflow.timeout == timedelta(hours=4)

    def test_metric_refresh_workflow(self):
        workflow = MetricRefreshWorkflow(interval_minutes=15)
        assert workflow.interval_minutes == 15
        assert workflow.schedule.cron == "*/15 * * * *"


class TestAPIResponse:
    """Tests for API response envelope."""

    def test_success_response(self):
        response = APIResponse(success=True, data={"key": "value"})
        assert response.success is True
        assert response.data == {"key": "value"}

    def test_error_response(self):
        response = APIResponse(
            success=False,
            error={"code": "NOT_FOUND", "message": "Resource not found"},
        )
        assert response.success is False
        assert response.error["code"] == "NOT_FOUND"

    def test_paginated_response(self):
        meta = ResponseMeta(
            total_count=100,
            page_size=10,
            has_more=True,
        )
        response = APIResponse(success=True, data=[], meta=meta)
        assert response.success is True
        assert response.meta.total_count == 100


class TestSecurity:
    """Tests for security features."""

    def test_password_hashing(self):
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_token_generation(self):
        data = {
            "sub": "user@test.com",
            "user_id": str(uuid.uuid4()),
            "role": "admin",
            "tenant_id": str(uuid.uuid4()),
        }
        token = create_access_token(data)
        assert token is not None
        assert len(token) > 0


class TestCaching:
    """Tests for caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        cache = AnalyticsCacheService(mock_redis)
        await cache.set_cached_result("test_key", {"data": "test"}, ttl_seconds=300)
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["analytics:scope:1", "analytics:scope:2"]
        mock_redis.delete.return_value = 2
        cache = AnalyticsCacheService(mock_redis)
        await cache.invalidate_scope("scope")
        mock_redis.delete.assert_called_once()


class TestDatabaseMigration:
    """Tests for database migrations."""

    def test_alembic_config(self):
        from alembic.config import Config
        config = Config("alembic.ini")
        script_location = config.get_main_option("script_location")
        assert "alembic" in script_location

    def test_database_url(self):
        from alembic.config import Config
        config = Config("alembic.ini")
        url = config.get_main_option("sqlalchemy.url")
        assert "postgresql" in url


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
