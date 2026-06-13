"""
Comprehensive test suite for Domain 7: Executive Workspace.
Tests all workspace entities, sections, briefings, layouts, and notifications.
"""
import uuid
import pytest
from datetime import datetime, timedelta, date

from app.domain.workspace import (
    SectionType,
    WorkspaceSection,
    ExecutiveWorkspace,
    BriefingSection,
    ExecutiveBriefing,
    NotificationConfig,
    WorkspaceLayout,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def section_id():
    return uuid.uuid4()


@pytest.fixture
def briefing_id():
    return uuid.uuid4()


@pytest.fixture
def sample_section():
    return WorkspaceSection(
        section_type=SectionType.MY_DASHBOARD,
        position=0,
        config={"show_kpis": True},
        is_collapsed=False,
    )


@pytest.fixture
def sample_workspace(user_id):
    return ExecutiveWorkspace(
        user_id=user_id,
        layout={"columns": 2, "theme": "dark"},
        notification_preferences={"email": True, "push": False},
    )


@pytest.fixture
def sample_briefing_section():
    return BriefingSection(
        title="Revenue Overview",
        content="Revenue increased by 12% compared to the previous quarter.",
        metric_values=[
            {"metric_name": "total_revenue", "value": 5200000, "unit": "USD", "trend": "up"},
            {"metric_name": "operating_margin", "value": 0.18, "unit": "%", "trend": "stable"},
        ],
        highlights=["Revenue exceeded forecast by 8%", "Operating margin stable at 18%"],
    )


@pytest.fixture
def sample_briefing(user_id):
    return ExecutiveBriefing(
        user_id=user_id,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 6, 30),
        ai_generated_summary="Q2 showed strong revenue growth driven by outpatient services.",
        is_read=False,
    )


@pytest.fixture
def sample_notification_config():
    return NotificationConfig(
        email_enabled=True,
        push_enabled=True,
        frequency="real_time",
        quiet_hours_start="22:00",
        quiet_hours_end="07:00",
    )


@pytest.fixture
def sample_layout():
    return WorkspaceLayout(
        columns=3,
        theme="dark",
        compact_mode=False,
        show_sidebar=True,
    )


# ============================================================
# TEST SECTION TYPE
# ============================================================

class TestSectionType:
    def test_all_section_types_exist(self):
        expected = {
            "my_dashboard", "my_decisions", "my_recommendations",
            "my_watchlists", "my_reports", "my_briefings",
            "my_anomalies", "my_assignments",
        }
        actual = {st.value for st in SectionType}
        assert actual == expected

    def test_section_type_count(self):
        assert len(SectionType) == 8

    def test_section_type_is_enum(self):
        assert isinstance(SectionType.MY_DASHBOARD, SectionType)


# ============================================================
# TEST WORKSPACE SECTION
# ============================================================

class TestWorkspaceSection:
    def test_create_section(self, sample_section):
        assert sample_section.id is not None
        assert sample_section.section_type == SectionType.MY_DASHBOARD
        assert sample_section.position == 0
        assert sample_section.config == {"show_kpis": True}
        assert sample_section.is_collapsed is False

    def test_section_defaults(self):
        section = WorkspaceSection(section_type=SectionType.MY_DECISIONS, position=1)
        assert section.id is not None
        assert section.config == {}
        assert section.is_collapsed is False

    def test_section_to_dict(self, sample_section):
        d = sample_section.to_dict()
        assert d["section_type"] == "my_dashboard"
        assert d["position"] == 0
        assert d["is_collapsed"] is False
        assert "id" in d
        assert "created_at" in d
        assert "updated_at" in d


# ============================================================
# TEST EXECUTIVE WORKSPACE
# ============================================================

class TestExecutiveWorkspace:
    def test_create_workspace(self, sample_workspace, user_id):
        assert sample_workspace.id is not None
        assert sample_workspace.user_id == user_id
        assert sample_workspace.sections == []
        assert sample_workspace.layout == {"columns": 2, "theme": "dark"}

    def test_add_section(self, sample_workspace, sample_section):
        sample_workspace.add_section(sample_section)
        assert len(sample_workspace.sections) == 1
        assert sample_workspace.sections[0].section_type == SectionType.MY_DASHBOARD

    def test_add_multiple_sections(self, sample_workspace):
        sections = [
            WorkspaceSection(section_type=SectionType.MY_DASHBOARD, position=0),
            WorkspaceSection(section_type=SectionType.MY_DECISIONS, position=1),
            WorkspaceSection(section_type=SectionType.MY_RECOMMENDATIONS, position=2),
        ]
        for s in sections:
            sample_workspace.add_section(s)
        assert len(sample_workspace.sections) == 3

    def test_remove_section(self, sample_workspace, sample_section):
        sample_workspace.add_section(sample_section)
        result = sample_workspace.remove_section(sample_section.id)
        assert result is True
        assert len(sample_workspace.sections) == 0

    def test_remove_nonexistent_section(self, sample_workspace):
        result = sample_workspace.remove_section(uuid.uuid4())
        assert result is False

    def test_get_section(self, sample_workspace, sample_section):
        sample_workspace.add_section(sample_section)
        found = sample_workspace.get_section(sample_section.id)
        assert found is not None
        assert found.id == sample_section.id

    def test_get_section_not_found(self, sample_workspace):
        found = sample_workspace.get_section(uuid.uuid4())
        assert found is None

    def test_reorder_sections(self, sample_workspace):
        s1 = WorkspaceSection(section_type=SectionType.MY_DASHBOARD, position=0)
        s2 = WorkspaceSection(section_type=SectionType.MY_DECISIONS, position=1)
        s3 = WorkspaceSection(section_type=SectionType.MY_REPORTS, position=2)
        sample_workspace.add_section(s1)
        sample_workspace.add_section(s2)
        sample_workspace.add_section(s3)
        sample_workspace.reorder_sections([s3.id, s1.id, s2.id])
        assert sample_workspace.sections[0].id == s3.id
        assert sample_workspace.sections[1].id == s1.id
        assert sample_workspace.sections[2].id == s2.id

    def test_get_section_by_type(self, sample_workspace, sample_section):
        sample_workspace.add_section(sample_section)
        found = sample_workspace.get_section_by_type(SectionType.MY_DASHBOARD)
        assert found is not None
        assert found.section_type == SectionType.MY_DASHBOARD

    def test_get_section_by_type_not_found(self, sample_workspace):
        found = sample_workspace.get_section_by_type(SectionType.MY_ANOMALIES)
        assert found is None

    def test_collapse_section(self, sample_workspace, sample_section):
        sample_workspace.add_section(sample_section)
        result = sample_workspace.collapse_section(sample_section.id)
        assert result is True
        assert sample_section.is_collapsed is True

    def test_collapse_nonexistent_section(self, sample_workspace):
        result = sample_workspace.collapse_section(uuid.uuid4())
        assert result is False

    def test_expand_section(self, sample_workspace, sample_section):
        sample_workspace.add_section(sample_section)
        sample_workspace.collapse_section(sample_section.id)
        result = sample_workspace.expand_section(sample_section.id)
        assert result is True
        assert sample_section.is_collapsed is False

    def test_expand_nonexistent_section(self, sample_workspace):
        result = sample_workspace.expand_section(uuid.uuid4())
        assert result is False

    def test_update_layout(self, sample_workspace):
        new_layout = {"columns": 3, "theme": "light", "compact": True}
        sample_workspace.update_layout(new_layout)
        assert sample_workspace.layout == new_layout

    def test_update_notification_preferences(self, sample_workspace):
        prefs = {"email": False, "push": True, "sms": False}
        sample_workspace.update_notification_preferences(prefs)
        assert sample_workspace.notification_preferences == prefs

    def test_active_section_count(self, sample_workspace):
        s1 = WorkspaceSection(section_type=SectionType.MY_DASHBOARD, position=0)
        s2 = WorkspaceSection(section_type=SectionType.MY_DECISIONS, position=1, is_collapsed=True)
        s3 = WorkspaceSection(section_type=SectionType.MY_REPORTS, position=2)
        sample_workspace.add_section(s1)
        sample_workspace.add_section(s2)
        sample_workspace.add_section(s3)
        assert sample_workspace.active_section_count() == 2

    def test_to_dict(self, sample_workspace, sample_section):
        sample_workspace.add_section(sample_section)
        d = sample_workspace.to_dict()
        assert "id" in d
        assert "user_id" in d
        assert len(d["sections"]) == 1
        assert d["sections"][0]["section_type"] == "my_dashboard"
        assert d["layout"]["columns"] == 2

    def test_positions_reorder_on_add(self, sample_workspace):
        s1 = WorkspaceSection(section_type=SectionType.MY_DASHBOARD, position=5)
        s2 = WorkspaceSection(section_type=SectionType.MY_DECISIONS, position=10)
        sample_workspace.add_section(s1)
        sample_workspace.add_section(s2)
        assert sample_workspace.sections[0].position == 0
        assert sample_workspace.sections[1].position == 1

    def test_remove_reorders_positions(self, sample_workspace):
        s1 = WorkspaceSection(section_type=SectionType.MY_DASHBOARD, position=0)
        s2 = WorkspaceSection(section_type=SectionType.MY_DECISIONS, position=1)
        s3 = WorkspaceSection(section_type=SectionType.MY_REPORTS, position=2)
        sample_workspace.add_section(s1)
        sample_workspace.add_section(s2)
        sample_workspace.add_section(s3)
        sample_workspace.remove_section(s2.id)
        assert len(sample_workspace.sections) == 2
        assert sample_workspace.sections[0].position == 0
        assert sample_workspace.sections[1].position == 1


# ============================================================
# TEST BRIEFING SECTION
# ============================================================

class TestBriefingSection:
    def test_create_briefing_section(self, sample_briefing_section):
        assert sample_briefing_section.id is not None
        assert sample_briefing_section.title == "Revenue Overview"
        assert len(sample_briefing_section.metric_values) == 2
        assert len(sample_briefing_section.highlights) == 2

    def test_add_metric_value(self, sample_briefing_section):
        sample_briefing_section.add_metric_value("patient_volume", 12500, "count", "up")
        assert len(sample_briefing_section.metric_values) == 3
        assert sample_briefing_section.metric_values[-1]["metric_name"] == "patient_volume"

    def test_add_metric_value_without_optional(self, sample_briefing_section):
        sample_briefing_section.add_metric_value("simple_metric", 42)
        entry = sample_briefing_section.metric_values[-1]
        assert entry["metric_name"] == "simple_metric"
        assert entry["value"] == 42
        assert "unit" not in entry
        assert "trend" not in entry

    def test_add_highlight(self, sample_briefing_section):
        sample_briefing_section.add_highlight("New record high achieved")
        assert len(sample_briefing_section.highlights) == 3
        assert sample_briefing_section.highlights[-1] == "New record high achieved"

    def test_to_dict(self, sample_briefing_section):
        d = sample_briefing_section.to_dict()
        assert d["title"] == "Revenue Overview"
        assert len(d["metric_values"]) == 2
        assert len(d["highlights"]) == 2


# ============================================================
# TEST EXECUTIVE BRIEFING
# ============================================================

class TestExecutiveBriefing:
    def test_create_briefing(self, sample_briefing, user_id):
        assert sample_briefing.id is not None
        assert sample_briefing.user_id == user_id
        assert sample_briefing.period_start == date(2026, 4, 1)
        assert sample_briefing.period_end == date(2026, 6, 30)
        assert sample_briefing.is_read is False
        assert sample_briefing.read_at is None

    def test_mark_as_read(self, sample_briefing):
        sample_briefing.mark_as_read()
        assert sample_briefing.is_read is True
        assert sample_briefing.read_at is not None

    def test_mark_as_read_idempotent(self, sample_briefing):
        sample_briefing.mark_as_read()
        first_read_at = sample_briefing.read_at
        sample_briefing.mark_as_read()
        assert sample_briefing.read_at == first_read_at

    def test_add_section(self, sample_briefing, sample_briefing_section):
        sample_briefing.add_section(sample_briefing_section)
        assert len(sample_briefing.sections) == 1
        assert sample_briefing.sections[0].title == "Revenue Overview"

    def test_get_section_by_title(self, sample_briefing, sample_briefing_section):
        sample_briefing.add_section(sample_briefing_section)
        found = sample_briefing.get_section_by_title("Revenue Overview")
        assert found is not None
        assert found.title == "Revenue Overview"

    def test_get_section_by_title_not_found(self, sample_briefing):
        found = sample_briefing.get_section_by_title("Nonexistent Section")
        assert found is None

    def test_total_highlights(self, sample_briefing, sample_briefing_section):
        sample_briefing.add_section(sample_briefing_section)
        section2 = BriefingSection(
            title="Expense Summary",
            content="Expenses decreased by 5%.",
            highlights=["Cost savings in procurement", "IT spend up 10%"],
        )
        sample_briefing.add_section(section2)
        assert sample_briefing.total_highlights() == 4

    def test_total_metric_values(self, sample_briefing, sample_briefing_section):
        sample_briefing.add_section(sample_briefing_section)
        assert sample_briefing.total_metric_values() == 2

    def test_to_dict(self, sample_briefing, sample_briefing_section):
        sample_briefing.add_section(sample_briefing_section)
        d = sample_briefing.to_dict()
        assert "id" in d
        assert d["is_read"] is False
        assert d["ai_generated_summary"] is not None
        assert len(d["sections"]) == 1
        assert d["period_start"] == "2026-04-01"

    def test_multiple_sections(self, sample_briefing):
        for i in range(5):
            sample_briefing.add_section(
                BriefingSection(title=f"Section {i}", content=f"Content {i}")
            )
        assert len(sample_briefing.sections) == 5


# ============================================================
# TEST NOTIFICATION CONFIG
# ============================================================

class TestNotificationConfig:
    def test_create_notification_config(self, sample_notification_config):
        assert sample_notification_config.id is not None
        assert sample_notification_config.email_enabled is True
        assert sample_notification_config.push_enabled is True
        assert sample_notification_config.frequency == "real_time"
        assert sample_notification_config.quiet_hours_start == "22:00"
        assert sample_notification_config.quiet_hours_end == "07:00"

    def test_set_quiet_hours(self, sample_notification_config):
        sample_notification_config.set_quiet_hours("21:00", "06:00")
        assert sample_notification_config.quiet_hours_start == "21:00"
        assert sample_notification_config.quiet_hours_end == "06:00"

    def test_clear_quiet_hours(self, sample_notification_config):
        sample_notification_config.clear_quiet_hours()
        assert sample_notification_config.quiet_hours_start is None
        assert sample_notification_config.quiet_hours_end is None

    def test_is_any_channel_enabled(self, sample_notification_config):
        assert sample_notification_config.is_any_channel_enabled() is True

    def test_is_any_channel_disabled(self):
        config = NotificationConfig(email_enabled=False, push_enabled=False)
        assert config.is_any_channel_enabled() is False

    def test_is_any_channel_email_only(self):
        config = NotificationConfig(email_enabled=True, push_enabled=False)
        assert config.is_any_channel_enabled() is True

    def test_defaults(self):
        config = NotificationConfig()
        assert config.email_enabled is True
        assert config.push_enabled is True
        assert config.frequency == "real_time"
        assert config.quiet_hours_start is None
        assert config.quiet_hours_end is None

    def test_to_dict(self, sample_notification_config):
        d = sample_notification_config.to_dict()
        assert d["email_enabled"] is True
        assert d["push_enabled"] is True
        assert d["frequency"] == "real_time"
        assert d["quiet_hours_start"] == "22:00"
        assert d["quiet_hours_end"] == "07:00"


# ============================================================
# TEST WORKSPACE LAYOUT
# ============================================================

class TestWorkspaceLayout:
    def test_create_layout(self, sample_layout):
        assert sample_layout.id is not None
        assert sample_layout.columns == 3
        assert sample_layout.theme == "dark"
        assert sample_layout.compact_mode is False
        assert sample_layout.show_sidebar is True

    def test_set_theme(self, sample_layout):
        sample_layout.set_theme("light")
        assert sample_layout.theme == "light"

    def test_toggle_compact_mode(self, sample_layout):
        sample_layout.toggle_compact_mode()
        assert sample_layout.compact_mode is True
        sample_layout.toggle_compact_mode()
        assert sample_layout.compact_mode is False

    def test_toggle_sidebar(self, sample_layout):
        sample_layout.toggle_sidebar()
        assert sample_layout.show_sidebar is False
        sample_layout.toggle_sidebar()
        assert sample_layout.show_sidebar is True

    def test_set_columns_valid(self, sample_layout):
        sample_layout.set_columns(1)
        assert sample_layout.columns == 1
        sample_layout.set_columns(4)
        assert sample_layout.columns == 4

    def test_set_columns_invalid_low(self, sample_layout):
        with pytest.raises(ValueError, match="Columns must be between 1 and 4"):
            sample_layout.set_columns(0)

    def test_set_columns_invalid_high(self, sample_layout):
        with pytest.raises(ValueError, match="Columns must be between 1 and 4"):
            sample_layout.set_columns(5)

    def test_defaults(self):
        layout = WorkspaceLayout()
        assert layout.columns == 2
        assert layout.theme == "light"
        assert layout.compact_mode is False
        assert layout.show_sidebar is True

    def test_to_dict(self, sample_layout):
        d = sample_layout.to_dict()
        assert d["columns"] == 3
        assert d["theme"] == "dark"
        assert d["compact_mode"] is False
        assert d["show_sidebar"] is True
