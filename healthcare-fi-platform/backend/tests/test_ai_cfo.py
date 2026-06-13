import pytest
from uuid import uuid4
from datetime import datetime
from decimal import Decimal
from app.domain.ai_cfo import (
    CFOCoreService, CFOProfile, Question, Briefing, Workspace, AlertConfig, Alert,
    Intent, BriefingMode, BriefingStatus, Urgency, RiskSeverity, RecommendationPriority,
)


class TestCFOCoreService:
    def setup_method(self):
        self.service = CFOCoreService()
        self.tenant_id = str(uuid4())

    def test_create_profile(self):
        prefs = {"preferred_language": "en", "risk_tolerance": "conservative"}
        profile = self.service.create_profile(self.tenant_id, "John Doe", "CFO", prefs)
        assert isinstance(profile, CFOProfile)
        assert profile.name == "John Doe"
        assert profile.role == "CFO"
        assert profile.preferences["risk_tolerance"] == "conservative"
        assert profile.is_active is True

    def test_get_profile_returns_profile(self):
        profile = self.service.create_profile(self.tenant_id, "Jane", "CFO", {})
        result = self.service.get_profile(self.tenant_id, profile.id)
        assert result is not None
        assert result.id == profile.id

    def test_get_profile_returns_none(self):
        result = self.service.get_profile(self.tenant_id, uuid4())
        assert result is None

    def test_update_profile(self):
        profile = self.service.create_profile(self.tenant_id, "Jane", "CFO", {})
        updated = self.service.update_profile(self.tenant_id, profile.id, {"role": "VP Finance"})
        assert updated.role == "VP Finance"

    def test_ask_question_root_cause(self):
        q = self.service.ask_question(self.tenant_id, uuid4(), "Why is revenue declining?", {})
        assert isinstance(q, Question)
        assert q.intent == Intent.ROOT_CAUSE
        assert q.user_query == "Why is revenue declining?"
        assert q.confidence > 0

    def test_ask_question_forecast(self):
        q = self.service.ask_question(self.tenant_id, uuid4(), "What will revenue be next quarter?", {})
        assert q.intent == Intent.FORECAST_EXPLAIN

    def test_ask_question_what_if(self):
        q = self.service.ask_question(self.tenant_id, uuid4(), "What if we cut costs by 10%?", {})
        assert q.intent == Intent.WHAT_IF

    def test_ask_question_risk(self):
        q = self.service.ask_question(self.tenant_id, uuid4(), "What are the risks?", {})
        assert q.intent == Intent.RISK_ASSESSMENT

    def test_ask_question_benchmark(self):
        q = self.service.ask_question(self.tenant_id, uuid4(), "Compare with last year", {})
        assert q.intent == Intent.BENCHMARKING

    def test_ask_question_trend(self):
        q = self.service.ask_question(self.tenant_id, uuid4(), "Show me the trend", {})
        assert q.intent == Intent.TREND_ANALYSIS

    def test_ask_question_anomaly(self):
        q = self.service.ask_question(self.tenant_id, uuid4(), "There's an anomaly in revenue", {})
        assert q.intent == Intent.ANOMALY_EXPLAIN

    def test_ask_question_variance(self):
        q = self.service.ask_question(self.tenant_id, uuid4(), "Show me the budget variance analysis", {})
        assert q.intent == Intent.VARIANCE_ANALYSIS

    def test_ask_question_scenario(self):
        q = self.service.ask_question(self.tenant_id, uuid4(), "Run a scenario for Q2", {})
        assert q.intent == Intent.SCENARIO_PLANNING

    def test_ask_question_recommendation(self):
        q = self.service.ask_question(self.tenant_id, uuid4(), "Recommend an action", {})
        assert q.intent == Intent.RECOMMENDATION

    def test_ask_question_briefing(self):
        q = self.service.ask_question(self.tenant_id, uuid4(), "Give me a briefing", {})
        assert q.intent == Intent.BRIEFING

    def test_ask_question_performance(self):
        q = self.service.ask_question(self.tenant_id, uuid4(), "How is the department performing?", {})
        assert q.intent == Intent.PERFORMANCE_ANALYSIS

    def test_generate_briefing(self):
        briefing = self.service.generate_briefing(
            self.tenant_id, BriefingMode.ON_DEMAND, "2025-01", {"metrics": []}
        )
        assert isinstance(briefing, Briefing)
        assert briefing.mode == BriefingMode.ON_DEMAND
        assert briefing.status == BriefingStatus.GENERATED
        assert briefing.period == "2025-01"
        assert isinstance(briefing.sections, list)

    def test_create_workspace(self):
        members = [{"user_id": str(uuid4()), "role": "viewer"}]
        ws = self.service.create_workspace(self.tenant_id, "Finance View", "Main dashboard", uuid4(), members)
        assert isinstance(ws, Workspace)
        assert ws.name == "Finance View"
        assert len(ws.members) == 1

    def test_add_widget(self):
        ws = self.service.create_workspace(self.tenant_id, "View", "Desc", uuid4(), [])
        updated = self.service.add_widget(self.tenant_id, ws.id, "metric", {"metric_id": "rev"})
        assert len(updated.widgets) == 1
        assert updated.widgets[0]["type"] == "metric"

    def test_delete_workspace(self):
        ws = self.service.create_workspace(self.tenant_id, "View", "Desc", uuid4(), [])
        result = self.service.delete_workspace(self.tenant_id, ws.id)
        assert result is True
        assert self.service.get_workspace(self.tenant_id, ws.id) is None

    def test_create_alert_config(self):
        config = self.service.create_alert_config(
            self.tenant_id, str(uuid4()), "Revenue", uuid4(),
            {"operator": "less_than"}, {"warning": 100000, "critical": 50000}, ["email"]
        )
        assert isinstance(config, AlertConfig)
        assert config.metric_name == "Revenue"
        assert config.enabled is True

    def test_get_alerts_filters_unread(self):
        config = self.service.create_alert_config(
            self.tenant_id, str(uuid4()), "Rev", uuid4(), {}, {}, []
        )
        user_id = uuid4()
        # No alerts yet
        alerts = self.service.get_alerts(self.tenant_id, user_id, unread_only=False)
        assert isinstance(alerts, list)

    def test_dismiss_alert(self):
        user_id = uuid4()
        config = self.service.create_alert_config(
            self.tenant_id, str(uuid4()), "Rev", user_id, {}, {}, []
        )
        alert = Alert(
            tenant_id=self.tenant_id, config_id=config.id, metric_id=uuid4(),
            metric_name="Rev", message="Low", severity=RiskSeverity.HIGH,
            value=Decimal("80000"), threshold=Decimal("100000"), is_read=False, is_dismissed=False,
        )
        self.service._alerts[alert.id] = alert
        dismissed = self.service.dismiss_alert(self.tenant_id, alert.id)
        assert dismissed.is_dismissed is True

    def test_intent_enum_values(self):
        assert len(Intent) == 12
        assert Intent.PERFORMANCE_ANALYSIS.value == "performance_analysis"

    def test_briefing_mode_values(self):
        assert BriefingMode.ON_DEMAND.value == "on_demand"
        assert BriefingMode.SCHEDULED.value == "scheduled"
        assert BriefingMode.EVENT_DRIVEN.value == "event_driven"
