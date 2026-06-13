"""Tests for the Dashboard Builder domain."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.domain.dashboard import (
    Dashboard,
    DashboardTemplate,
    DashboardVersion,
    DashboardWidget,
    GridPosition,
    PersonalDashboard,
    PrebuiltDashboardTemplates,
    WidgetType,
)


# ---------------------------------------------------------------------------
# WidgetType
# ---------------------------------------------------------------------------

class TestWidgetType:
    def test_all_member_values(self) -> None:
        expected = [
            "kpi_card",
            "line_chart",
            "bar_chart",
            "area_chart",
            "pie_chart",
            "treemap",
            "scatter_plot",
            "heatmap",
            "waterfall",
            "gauge",
            "matrix",
            "table",
            "insight_feed",
            "forecast",
        ]
        actual = [wt.value for wt in WidgetType]
        assert actual == expected

    def test_member_count(self) -> None:
        assert len(WidgetType) == 14

    def test_member_access(self) -> None:
        assert WidgetType.KPI_CARD.value == "kpi_card"
        assert WidgetType.WATERFALL.value == "waterfall"
        assert WidgetType.TREEMAP.value == "treemap"
        assert WidgetType.HEATMAP.value == "heatmap"


# ---------------------------------------------------------------------------
# GridPosition
# ---------------------------------------------------------------------------

class TestGridPosition:
    def test_default_construction(self) -> None:
        pos = GridPosition()
        assert pos.col_start == 1
        assert pos.col_span == 6
        assert pos.row_start == 1
        assert pos.row_span == 4

    def test_construction_with_values(self) -> None:
        pos = GridPosition(col_start=7, col_span=3, row_start=5, row_span=2)
        assert pos.col_start == 7
        assert pos.col_span == 3
        assert pos.row_start == 5
        assert pos.row_span == 2

    def test_valid_full_width(self) -> None:
        pos = GridPosition(col_start=1, col_span=12, row_start=1, row_span=1)
        assert pos.col_start == 1
        assert pos.col_span == 12

    def test_valid_edge(self) -> None:
        pos = GridPosition(col_start=12, col_span=1, row_start=1, row_span=1)
        assert pos.col_start == 12

    def test_invalid_col_start_zero(self) -> None:
        with pytest.raises(ValueError, match="col_start must be 1-12"):
            GridPosition(col_start=0, col_span=6, row_start=1, row_span=4)

    def test_invalid_col_start_thirteen(self) -> None:
        with pytest.raises(ValueError, match="col_start must be 1-12"):
            GridPosition(col_start=13, col_span=1, row_start=1, row_span=4)

    def test_invalid_col_span_zero(self) -> None:
        with pytest.raises(ValueError, match="col_span must be 1-12"):
            GridPosition(col_start=1, col_span=0, row_start=1, row_span=4)

    def test_invalid_col_span_thirteen(self) -> None:
        with pytest.raises(ValueError, match="col_span must be 1-12"):
            GridPosition(col_start=1, col_span=13, row_start=1, row_span=4)

    def test_extends_beyond_grid(self) -> None:
        with pytest.raises(ValueError, match="Widget extends beyond grid"):
            GridPosition(col_start=8, col_span=6, row_start=1, row_span=4)

    def test_invalid_row_start_zero(self) -> None:
        with pytest.raises(ValueError, match="row_start must be >= 1"):
            GridPosition(col_start=1, col_span=6, row_start=0, row_span=4)

    def test_invalid_row_span_zero(self) -> None:
        with pytest.raises(ValueError, match="row_span must be >= 1"):
            GridPosition(col_start=1, col_span=6, row_start=1, row_span=0)


# ---------------------------------------------------------------------------
# DashboardWidget
# ---------------------------------------------------------------------------

class TestDashboardWidget:
    def test_default_construction(self) -> None:
        w = DashboardWidget()
        assert isinstance(w.widget_id, uuid.UUID)
        assert w.widget_type == WidgetType.KPI_CARD
        assert w.title == ""
        assert isinstance(w.position, GridPosition)
        assert w.metric_ids == []
        assert w.dimension_ids == []
        assert w.filters == []
        assert w.time_range == {}
        assert w.visualization_config == {}
        assert w.link_filters == {}
        assert w.refresh_interval is None

    def test_construction_with_values(self) -> None:
        w = DashboardWidget(
            widget_type=WidgetType.BAR_CHART,
            title="Revenue by Department",
            position=GridPosition(col_start=1, col_span=6, row_start=1, row_span=4),
            metric_ids=["net_revenue", "gross_revenue"],
            dimension_ids=["department_name"],
            filters=[{"field": "status", "operator": "eq", "value": "active"}],
            time_range={"range": "last_30_days"},
            visualization_config={"color_scheme": "healthcare_blue"},
            link_filters={"payer_filter": True},
            refresh_interval=300,
        )
        assert w.widget_type == WidgetType.BAR_CHART
        assert w.title == "Revenue by Department"
        assert len(w.metric_ids) == 2
        assert w.refresh_interval == 300

    def test_unique_widget_ids(self) -> None:
        w1 = DashboardWidget()
        w2 = DashboardWidget()
        assert w1.widget_id != w2.widget_id

    def test_all_widget_types(self) -> None:
        for wt in WidgetType:
            w = DashboardWidget(widget_type=wt)
            assert w.widget_type == wt


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_default_construction(self) -> None:
        d = Dashboard()
        assert isinstance(d.id, uuid.UUID)
        assert d.name == ""
        assert d.description == ""
        assert d.widgets == []
        assert d.layout_version == 1
        assert d.is_template is False
        assert d.template_category is None
        assert isinstance(d.owner_id, uuid.UUID)
        assert isinstance(d.tenant_id, uuid.UUID)
        assert d.variables == {}
        assert d.auto_refresh is None
        assert isinstance(d.created_at, datetime)
        assert isinstance(d.updated_at, datetime)

    def test_construction_with_widgets(self) -> None:
        widgets = [
            DashboardWidget(title="KPI 1", widget_type=WidgetType.KPI_CARD),
            DashboardWidget(title="Chart 1", widget_type=WidgetType.LINE_CHART),
        ]
        d = Dashboard(
            name="Revenue Overview",
            description="Monthly revenue dashboard.",
            widgets=widgets,
            layout_version=2,
            is_template=False,
            owner_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            variables={"currency": "USD"},
            auto_refresh=600,
        )
        assert d.name == "Revenue Overview"
        assert len(d.widgets) == 2
        assert d.layout_version == 2
        assert d.variables["currency"] == "USD"
        assert d.auto_refresh == 600

    def test_template_dashboard(self) -> None:
        d = Dashboard(
            name="Template Dashboard",
            is_template=True,
            template_category="executive",
        )
        assert d.is_template is True
        assert d.template_category == "executive"

    def test_unique_dashboard_ids(self) -> None:
        d1 = Dashboard()
        d2 = Dashboard()
        assert d1.id != d2.id


# ---------------------------------------------------------------------------
# DashboardVersion
# ---------------------------------------------------------------------------

class TestDashboardVersion:
    def test_default_construction(self) -> None:
        v = DashboardVersion()
        assert isinstance(v.id, uuid.UUID)
        assert isinstance(v.dashboard_id, uuid.UUID)
        assert v.version == 1
        assert v.snapshot == {}
        assert isinstance(v.changed_by, uuid.UUID)
        assert isinstance(v.changed_at, datetime)
        assert v.change_type == "update"
        assert v.change_summary == ""

    def test_construction_with_values(self) -> None:
        dash_id = uuid.uuid4()
        v = DashboardVersion(
            dashboard_id=dash_id,
            version=3,
            snapshot={
                "name": "Revenue Dashboard",
                "widgets": [{"title": "KPI", "type": "kpi_card"}],
                "layout_version": 3,
            },
            changed_by=uuid.uuid4(),
            change_type="widget_added",
            change_summary="Added denial rate KPI card.",
        )
        assert v.dashboard_id == dash_id
        assert v.version == 3
        assert "widgets" in v.snapshot
        assert v.change_type == "widget_added"

    def test_unique_version_ids(self) -> None:
        v1 = DashboardVersion()
        v2 = DashboardVersion()
        assert v1.id != v2.id

    def test_version_history(self) -> None:
        dash_id = uuid.uuid4()
        versions = [
            DashboardVersion(dashboard_id=dash_id, version=i, change_summary=f"Change {i}")
            for i in range(1, 6)
        ]
        assert len(versions) == 5
        assert versions[0].version == 1
        assert versions[4].version == 5


# ---------------------------------------------------------------------------
# PersonalDashboard
# ---------------------------------------------------------------------------

class TestPersonalDashboard:
    def test_default_construction(self) -> None:
        pd = PersonalDashboard()
        assert isinstance(pd.user_id, uuid.UUID)
        assert isinstance(pd.dashboard_id, uuid.UUID)
        assert pd.layout_snapshot == []
        assert pd.is_default is False
        assert pd.notifications_enabled is True
        assert pd.refresh_override is None

    def test_construction_with_values(self) -> None:
        pd = PersonalDashboard(
            user_id=uuid.uuid4(),
            dashboard_id=uuid.uuid4(),
            layout_snapshot=[
                {"widget_id": str(uuid.uuid4()), "position": {"col_start": 1, "col_span": 6}},
                {"widget_id": str(uuid.uuid4()), "position": {"col_start": 7, "col_span": 6}},
            ],
            is_default=True,
            notifications_enabled=False,
            refresh_override=120,
        )
        assert pd.is_default is True
        assert pd.notifications_enabled is False
        assert pd.refresh_override == 120
        assert len(pd.layout_snapshot) == 2

    def test_unique_user_dashboard_pairs(self) -> None:
        pd1 = PersonalDashboard()
        pd2 = PersonalDashboard()
        assert pd1.user_id != pd2.user_id


# ---------------------------------------------------------------------------
# DashboardTemplate
# ---------------------------------------------------------------------------

class TestDashboardTemplate:
    def test_default_construction(self) -> None:
        t = DashboardTemplate()
        assert isinstance(t.id, uuid.UUID)
        assert t.name == ""
        assert t.description == ""
        assert t.category == ""
        assert t.widgets == []
        assert t.default_filters == []
        assert t.target_audience == ""

    def test_construction_with_widgets(self) -> None:
        t = DashboardTemplate(
            name="Custom Template",
            description="A custom template.",
            category="custom",
            widgets=[
                DashboardWidget(title="Metric 1", widget_type=WidgetType.KPI_CARD),
            ],
            default_filters=[{"field": "tenant_id", "operator": "eq", "value": "current"}],
            target_audience="Analysts",
        )
        assert t.name == "Custom Template"
        assert len(t.widgets) == 1
        assert len(t.default_filters) == 1

    def test_unique_template_ids(self) -> None:
        t1 = DashboardTemplate()
        t2 = DashboardTemplate()
        assert t1.id != t2.id


# ---------------------------------------------------------------------------
# Pre-built Templates
# ---------------------------------------------------------------------------

class TestPrebuiltTemplates:
    def test_cfo_monthly(self) -> None:
        t = PrebuiltDashboardTemplates.cfo_monthly()
        assert t.name == "CFO Monthly Overview"
        assert t.category == "executive"
        assert t.target_audience == "CFO"
        assert len(t.widgets) == 6
        widget_types = {w.widget_type for w in t.widgets}
        assert WidgetType.KPI_CARD in widget_types
        assert WidgetType.GAUGE in widget_types
        assert WidgetType.LINE_CHART in widget_types
        assert WidgetType.PIE_CHART in widget_types
        assert len(t.default_filters) == 1

    def test_revenue_waterfall(self) -> None:
        t = PrebuiltDashboardTemplates.revenue_waterfall()
        assert t.name == "Revenue Waterfall"
        assert t.category == "revenue_cycle"
        assert t.target_audience == "Revenue Cycle Analysts"
        assert len(t.widgets) == 3
        widget_types = {w.widget_type for w in t.widgets}
        assert WidgetType.WATERFALL in widget_types
        assert WidgetType.BAR_CHART in widget_types
        assert WidgetType.AREA_CHART in widget_types

    def test_denial_analysis(self) -> None:
        t = PrebuiltDashboardTemplates.denial_analysis()
        assert t.name == "Denial Analysis"
        assert t.category == "denials"
        assert t.target_audience == "Denial Management Team"
        assert len(t.widgets) == 7
        widget_types = {w.widget_type for w in t.widgets}
        assert WidgetType.KPI_CARD in widget_types
        assert WidgetType.GAUGE in widget_types
        assert WidgetType.TREEMAP in widget_types
        assert WidgetType.BAR_CHART in widget_types
        assert WidgetType.LINE_CHART in widget_types

    def test_capacity_report(self) -> None:
        t = PrebuiltDashboardTemplates.capacity_report()
        assert t.name == "Capacity Report"
        assert t.category == "operations"
        assert t.target_audience == "COO / Operations"
        assert len(t.widgets) == 6
        widget_types = {w.widget_type for w in t.widgets}
        assert WidgetType.GAUGE in widget_types
        assert WidgetType.KPI_CARD in widget_types
        assert WidgetType.HEATMAP in widget_types
        assert WidgetType.BAR_CHART in widget_types

    def test_all_templates_are_independent(self) -> None:
        """Each call to a factory method returns a distinct template instance."""
        t1 = PrebuiltDashboardTemplates.cfo_monthly()
        t2 = PrebuiltDashboardTemplates.cfo_monthly()
        assert t1.id != t2.id

    def test_template_widget_positions_valid(self) -> None:
        """All pre-built template widgets have valid grid positions."""
        templates = [
            PrebuiltDashboardTemplates.cfo_monthly(),
            PrebuiltDashboardTemplates.revenue_waterfall(),
            PrebuiltDashboardTemplates.denial_analysis(),
            PrebuiltDashboardTemplates.capacity_report(),
        ]
        for tmpl in templates:
            for widget in tmpl.widgets:
                assert 1 <= widget.position.col_start <= 12
                assert 1 <= widget.position.col_span <= 12
                assert widget.position.col_start + widget.position.col_span - 1 <= 12
                assert widget.position.row_start >= 1
                assert widget.position.row_span >= 1

    def test_template_widget_ids_unique_per_template(self) -> None:
        """Within a single template, all widget IDs are unique."""
        templates = [
            PrebuiltDashboardTemplates.cfo_monthly(),
            PrebuiltDashboardTemplates.revenue_waterfall(),
            PrebuiltDashboardTemplates.denial_analysis(),
            PrebuiltDashboardTemplates.capacity_report(),
        ]
        for tmpl in templates:
            ids = [w.widget_id for w in tmpl.widgets]
            assert len(ids) == len(set(ids))

    def test_dashboard_versioning_workflow(self) -> None:
        """Simulate a dashboard versioning workflow."""
        dash_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Version 1 — initial creation
        v1 = DashboardVersion(
            dashboard_id=dash_id,
            version=1,
            snapshot={"widgets": [], "layout_version": 1},
            changed_by=user_id,
            change_type="created",
            change_summary="Initial dashboard.",
        )
        assert v1.version == 1
        assert v1.change_type == "created"

        # Version 2 — add widget
        v2 = DashboardVersion(
            dashboard_id=dash_id,
            version=2,
            snapshot={
                "widgets": [{"title": "Revenue KPI", "type": "kpi_card"}],
                "layout_version": 2,
            },
            changed_by=user_id,
            change_type="widget_added",
            change_summary="Added revenue KPI.",
        )
        assert v2.version == 2
        assert v2.snapshot["layout_version"] == 2

        # Version 3 — remove widget
        v3 = DashboardVersion(
            dashboard_id=dash_id,
            version=3,
            snapshot={"widgets": [], "layout_version": 3},
            changed_by=user_id,
            change_type="widget_removed",
            change_summary="Removed revenue KPI.",
        )
        assert v3.version == 3
        assert v3.change_type == "widget_removed"

        versions = [v1, v2, v3]
        assert all(v.dashboard_id == dash_id for v in versions)
        assert [v.version for v in versions] == [1, 2, 3]

    def test_personal_dashboard_customization(self) -> None:
        """Simulate a user personalizing a dashboard."""
        user_id = uuid.uuid4()
        dash_id = uuid.uuid4()

        # User creates personal layout
        pd = PersonalDashboard(
            user_id=user_id,
            dashboard_id=dash_id,
            layout_snapshot=[
                {"widget_id": str(uuid.uuid4()), "col_start": 1, "col_span": 4, "row_start": 1, "row_span": 2},
                {"widget_id": str(uuid.uuid4()), "col_start": 5, "col_span": 8, "row_start": 1, "row_span": 4},
            ],
            is_default=True,
            notifications_enabled=True,
            refresh_override=60,
        )

        assert pd.user_id == user_id
        assert pd.dashboard_id == dash_id
        assert pd.is_default is True
        assert pd.refresh_override == 60
        assert len(pd.layout_snapshot) == 2

    def test_dashboard_with_multiple_widget_types(self) -> None:
        """Dashboard construction with every widget type present."""
        all_types = list(WidgetType)
        widgets = [
            DashboardWidget(widget_type=wt, title=f"Widget {wt.value}")
            for wt in all_types
        ]
        d = Dashboard(
            name="All Widget Types Dashboard",
            widgets=widgets,
        )
        assert len(d.widgets) == 14
        widget_type_set = {w.widget_type for w in d.widgets}
        assert widget_type_set == set(all_types)

    def test_grid_positions_multiple_widgets(self) -> None:
        """Multiple widgets can coexist on the grid without overlap errors."""
        widgets = [
            DashboardWidget(
                title="Top Left",
                widget_type=WidgetType.KPI_CARD,
                position=GridPosition(col_start=1, col_span=4, row_start=1, row_span=2),
            ),
            DashboardWidget(
                title="Top Right",
                widget_type=WidgetType.KPI_CARD,
                position=GridPosition(col_start=5, col_span=4, row_start=1, row_span=2),
            ),
            DashboardWidget(
                title="Bottom Left",
                widget_type=WidgetType.LINE_CHART,
                position=GridPosition(col_start=1, col_span=6, row_start=3, row_span=4),
            ),
            DashboardWidget(
                title="Bottom Right",
                widget_type=WidgetType.BAR_CHART,
                position=GridPosition(col_start=7, col_span=6, row_start=3, row_span=4),
            ),
        ]
        d = Dashboard(name="Grid Test", widgets=widgets)
        assert len(d.widgets) == 4
        for w in d.widgets:
            assert 1 <= w.position.col_start <= 12
            assert w.position.col_start + w.position.col_span - 1 <= 12
