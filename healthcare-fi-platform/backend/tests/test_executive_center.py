import pytest
from uuid import uuid4
from decimal import Decimal
from app.domain.executive_center import (
    ExecutiveCenterService, KPIStatus, AlertItem, DecisionNeed,
    PerformanceSummary, RevenueForecast, CostForecast, RiskSummary, ExecutiveBriefing,
    HealthStatus, PriorityLevel, DecisionCategory,
)


class TestExecutiveCenterService:
    def setup_method(self):
        self.service = ExecutiveCenterService()
        self.tenant_id = "test-tenant"

    def test_get_kpi_dashboard(self):
        kpis = self.service.get_kpi_dashboard(self.tenant_id, "30d")
        assert isinstance(kpis, list)
        for kpi in kpis:
            assert isinstance(kpi, KPIStatus)
            assert kpi.status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]

    def test_get_active_alerts(self):
        alerts = self.service.get_active_alerts(self.tenant_id, limit=10)
        assert isinstance(alerts, list)

    def test_get_active_alerts_filters_severity(self):
        alerts = self.service.get_active_alerts(self.tenant_id, severity_filter="critical")
        assert all(a.severity == PriorityLevel.CRITICAL for a in alerts)

    def test_mark_alert_read(self):
        alerts = self.service.get_active_alerts(self.tenant_id)
        if alerts:
            read_alert = self.service.mark_alert_read(self.tenant_id, alerts[0].id)
            assert read_alert.is_read is True

    def test_dismiss_alert(self):
        alerts = self.service.get_active_alerts(self.tenant_id)
        if alerts:
            alert_id = alerts[0].id
            dismissed = self.service.dismiss_alert(self.tenant_id, alert_id)
            assert dismissed.id == alert_id
            remaining = self.service.get_active_alerts(self.tenant_id)
            assert all(a.id != alert_id for a in remaining)

    def test_get_decision_needs(self):
        decisions = self.service.get_decision_needs(self.tenant_id)
        assert isinstance(decisions, list)

    def test_create_decision_need(self):
        decision = self.service.create_decision_need(
            self.tenant_id, "Budget Review", "Review Q2 budget",
            DecisionCategory.COST_REDUCTION, PriorityLevel.HIGH,
            {"savings": 500000}, "2025-06-30", {}
        )
        assert isinstance(decision, DecisionNeed)
        assert decision.title == "Budget Review"
        assert decision.priority == PriorityLevel.HIGH

    def test_update_decision_status(self):
        decision = self.service.create_decision_need(
            self.tenant_id, "Test", "Desc", DecisionCategory.INVESTMENT, PriorityLevel.MEDIUM, {}, None, {}
        )
        updated = self.service.update_decision_status(self.tenant_id, decision.id, "completed")
        assert updated.status == "completed"

    def test_get_performance_summary(self):
        summary = self.service.get_performance_summary(self.tenant_id, "30d")
        assert isinstance(summary, PerformanceSummary)
        assert 0 <= summary.score <= 100

    def test_get_revenue_forecast(self):
        forecasts = self.service.get_revenue_forecast(self.tenant_id, 3)
        assert isinstance(forecasts, list)
        assert len(forecasts) == 3
        for f in forecasts:
            assert isinstance(f, RevenueForecast)
            assert isinstance(f.forecasted_revenue, Decimal)

    def test_get_cost_forecast(self):
        forecasts = self.service.get_cost_forecast(self.tenant_id, 3)
        assert isinstance(forecasts, list)
        assert len(forecasts) == 3
        for f in forecasts:
            assert isinstance(f, CostForecast)
            assert isinstance(f.forecasted_cost, Decimal)

    def test_get_risk_summary(self):
        summary = self.service.get_risk_summary(self.tenant_id)
        assert isinstance(summary, RiskSummary)
        assert 0 <= summary.overall_risk_score <= 1

    def test_generate_executive_briefing(self):
        briefing = self.service.generate_executive_briefing(self.tenant_id, "2025-01", "monthly")
        assert isinstance(briefing, ExecutiveBriefing)
        assert briefing.period == "2025-01"
        assert len(briefing.sections) == 5
        assert briefing.overall_health in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]
        assert len(briefing.key_actions) > 0

    def test_health_status_enum(self):
        assert len(HealthStatus) == 3

    def test_decision_category_enum(self):
        assert len(DecisionCategory) == 6
