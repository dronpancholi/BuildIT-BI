"""
Comprehensive test suite for Domain 9: Visualization Library.
Tests all chart types, interactions, color schemes, accessibility, and rendering.
"""
import uuid
import pytest
from datetime import datetime

from app.domain.visualization import (
    ChartType,
    InteractionType,
    AnimationType,
    ColorScheme,
    ChartSpec,
    WidgetRenderResult,
    VisualizationConfig,
    ConditionalFormat,
    ChartInteraction,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def widget_id():
    return uuid.uuid4()


@pytest.fixture
def metric_ids():
    return [uuid.uuid4() for _ in range(3)]


@pytest.fixture
def dimension_ids():
    return [uuid.uuid4() for _ in range(2)]


@pytest.fixture
def sample_chart_spec(metric_ids, dimension_ids):
    return ChartSpec(
        chart_type=ChartType.BAR,
        title="Revenue by Department",
        metric_ids=metric_ids,
        dimension_ids=dimension_ids,
        filters=[{"field": "period", "operator": "equals", "value": "Q2-2026"}],
        color_scheme=ColorScheme.QUALITATIVE,
        interactions=[InteractionType.HOVER_TOOLTIP, InteractionType.CLICK_FILTER],
        animation=AnimationType.GROW,
        accessibility_description="Bar chart showing revenue breakdown by department for Q2 2026.",
        responsive_config={"mobile": {"stacked": True}},
        export_config={"formats": ["png", "svg"]},
    )


@pytest.fixture
def sample_render_result(widget_id):
    return WidgetRenderResult(
        widget_id=widget_id,
        chart_type=ChartType.LINE,
        data={"labels": ["Jan", "Feb", "Mar"], "values": [100, 150, 120]},
        metadata={"source": "finance_db", "refresh_interval": 300},
        render_time_ms=42.5,
        accessibility_text="Line chart displaying monthly revenue from January to March.",
    )


@pytest.fixture
def sample_visualization_config():
    return VisualizationConfig(
        theme="dark",
        color_palette=["#FF6384", "#36A2EB", "#FFCE56"],
        font_family="Roboto, sans-serif",
        animation_enabled=True,
        responsive_breakpoints={"mobile": 480, "tablet": 768, "desktop": 1200},
    )


@pytest.fixture
def sample_conditional_format():
    return ConditionalFormat(
        column="revenue",
        rules=[
            {"type": "color_scale", "min_color": "#ffcccc", "max_color": "#ccffcc"},
            {"type": "icon", "icon_set": "arrows"},
        ],
    )


@pytest.fixture
def sample_chart_interaction():
    return ChartInteraction(
        interaction_type=InteractionType.DRILL_DOWN,
        config={"levels": ["department", "service_line", "provider"], "max_depth": 3},
        is_enabled=True,
    )


# ============================================================
# TEST CHART TYPE
# ============================================================

class TestChartType:
    def test_all_chart_types_exist(self):
        expected = {
            "line", "bar", "area", "pie", "donut", "scatter", "heatmap",
            "waterfall", "gauge", "treemap", "matrix", "table", "kpi_card",
            "insight_feed", "forecast", "funnel", "box_plot", "combo", "sparkline",
        }
        actual = {ct.value for ct in ChartType}
        assert actual == expected

    def test_chart_type_count(self):
        assert len(ChartType) == 19

    def test_chart_type_enums(self):
        assert ChartType.LINE.value == "line"
        assert ChartType.BAR.value == "bar"
        assert ChartType.AREA.value == "area"
        assert ChartType.PIE.value == "pie"
        assert ChartType.DONUT.value == "donut"
        assert ChartType.SCATTER.value == "scatter"
        assert ChartType.HEATMAP.value == "heatmap"
        assert ChartType.WATERFALL.value == "waterfall"
        assert ChartType.GAUGE.value == "gauge"
        assert ChartType.TREEMAP.value == "treemap"
        assert ChartType.MATRIX.value == "matrix"
        assert ChartType.TABLE.value == "table"
        assert ChartType.KPI_CARD.value == "kpi_card"
        assert ChartType.INSIGHT_FEED.value == "insight_feed"
        assert ChartType.FORECAST.value == "forecast"
        assert ChartType.FUNNEL.value == "funnel"
        assert ChartType.BOX_PLOT.value == "box_plot"
        assert ChartType.COMBO.value == "combo"
        assert ChartType.SPARKLINE.value == "sparkline"


# ============================================================
# TEST INTERACTION TYPE
# ============================================================

class TestInteractionType:
    def test_all_interaction_types_exist(self):
        expected = {
            "hover_tooltip", "click_filter", "zoom", "pan",
            "drill_down", "brush_select", "toggle_series", "expand_collapse",
        }
        actual = {it.value for it in InteractionType}
        assert actual == expected

    def test_interaction_type_count(self):
        assert len(InteractionType) == 8


# ============================================================
# TEST ANIMATION TYPE
# ============================================================

class TestAnimationType:
    def test_all_animation_types_exist(self):
        expected = {
            "none", "fade_in", "grow", "morph", "stagger", "smooth_transition",
        }
        actual = {at.value for at in AnimationType}
        assert actual == expected

    def test_animation_type_count(self):
        assert len(AnimationType) == 6


# ============================================================
# TEST COLOR SCHEME
# ============================================================

class TestColorScheme:
    def test_all_color_schemes_exist(self):
        expected = {"default", "qualitative", "sequential", "diverging", "colorblind_safe"}
        actual = {cs.value for cs in ColorScheme}
        assert actual == expected

    def test_color_scheme_count(self):
        assert len(ColorScheme) == 5


# ============================================================
# TEST CHART SPEC
# ============================================================

class TestChartSpec:
    def test_create_chart_spec(self, sample_chart_spec, metric_ids, dimension_ids):
        assert sample_chart_spec.id is not None
        assert sample_chart_spec.chart_type == ChartType.BAR
        assert sample_chart_spec.title == "Revenue by Department"
        assert len(sample_chart_spec.metric_ids) == 3
        assert len(sample_chart_spec.dimension_ids) == 2
        assert sample_chart_spec.color_scheme == ColorScheme.QUALITATIVE
        assert len(sample_chart_spec.interactions) == 2
        assert sample_chart_spec.animation == AnimationType.GROW

    def test_add_metric(self, sample_chart_spec):
        new_metric = uuid.uuid4()
        sample_chart_spec.add_metric(new_metric)
        assert new_metric in sample_chart_spec.metric_ids

    def test_add_metric_no_duplicate(self, sample_chart_spec):
        original_len = len(sample_chart_spec.metric_ids)
        sample_chart_spec.add_metric(sample_chart_spec.metric_ids[0])
        assert len(sample_chart_spec.metric_ids) == original_len

    def test_remove_metric(self, sample_chart_spec):
        metric_to_remove = sample_chart_spec.metric_ids[0]
        result = sample_chart_spec.remove_metric(metric_to_remove)
        assert result is True
        assert metric_to_remove not in sample_chart_spec.metric_ids

    def test_remove_metric_not_found(self, sample_chart_spec):
        result = sample_chart_spec.remove_metric(uuid.uuid4())
        assert result is False

    def test_add_dimension(self, sample_chart_spec):
        new_dim = uuid.uuid4()
        sample_chart_spec.add_dimension(new_dim)
        assert new_dim in sample_chart_spec.dimension_ids

    def test_add_dimension_no_duplicate(self, sample_chart_spec):
        original_len = len(sample_chart_spec.dimension_ids)
        sample_chart_spec.add_dimension(sample_chart_spec.dimension_ids[0])
        assert len(sample_chart_spec.dimension_ids) == original_len

    def test_remove_dimension(self, sample_chart_spec):
        dim_to_remove = sample_chart_spec.dimension_ids[0]
        result = sample_chart_spec.remove_dimension(dim_to_remove)
        assert result is True
        assert dim_to_remove not in sample_chart_spec.dimension_ids

    def test_remove_dimension_not_found(self, sample_chart_spec):
        result = sample_chart_spec.remove_dimension(uuid.uuid4())
        assert result is False

    def test_add_filter(self, sample_chart_spec):
        original_len = len(sample_chart_spec.filters)
        sample_chart_spec.add_filter({"field": "payer", "operator": "equals", "value": "Medicare"})
        assert len(sample_chart_spec.filters) == original_len + 1

    def test_remove_filter(self, sample_chart_spec):
        result = sample_chart_spec.remove_filter(0)
        assert result is True
        assert len(sample_chart_spec.filters) == 0

    def test_remove_filter_invalid_index(self, sample_chart_spec):
        result = sample_chart_spec.remove_filter(999)
        assert result is False

    def test_enable_interaction(self, sample_chart_spec):
        sample_chart_spec.enable_interaction(InteractionType.ZOOM)
        assert InteractionType.ZOOM in sample_chart_spec.interactions

    def test_enable_interaction_no_duplicate(self, sample_chart_spec):
        original_len = len(sample_chart_spec.interactions)
        sample_chart_spec.enable_interaction(InteractionType.HOVER_TOOLTIP)
        assert len(sample_chart_spec.interactions) == original_len

    def test_disable_interaction(self, sample_chart_spec):
        result = sample_chart_spec.disable_interaction(InteractionType.HOVER_TOOLTIP)
        assert result is True
        assert InteractionType.HOVER_TOOLTIP not in sample_chart_spec.interactions

    def test_disable_interaction_not_found(self, sample_chart_spec):
        result = sample_chart_spec.disable_interaction(InteractionType.BRUSH_SELECT)
        assert result is False

    def test_has_interaction(self, sample_chart_spec):
        assert sample_chart_spec.has_interaction(InteractionType.HOVER_TOOLTIP) is True
        assert sample_chart_spec.has_interaction(InteractionType.BRUSH_SELECT) is False

    def test_set_color_scheme(self, sample_chart_spec):
        sample_chart_spec.set_color_scheme(ColorScheme.DIVERGING)
        assert sample_chart_spec.color_scheme == ColorScheme.DIVERGING

    def test_set_animation(self, sample_chart_spec):
        sample_chart_spec.set_animation(AnimationType.MORPH)
        assert sample_chart_spec.animation == AnimationType.MORPH

    def test_set_accessibility_description(self, sample_chart_spec):
        new_desc = "Updated accessibility text for screen readers."
        sample_chart_spec.set_accessibility_description(new_desc)
        assert sample_chart_spec.accessibility_description == new_desc

    def test_update_responsive_config(self, sample_chart_spec):
        sample_chart_spec.update_responsive_config({"tablet": {"legend_position": "bottom"}})
        assert "tablet" in sample_chart_spec.responsive_config
        assert sample_chart_spec.responsive_config["tablet"]["legend_position"] == "bottom"

    def test_update_export_config(self, sample_chart_spec):
        sample_chart_spec.update_export_config({"pdf_quality": "high"})
        assert sample_chart_spec.export_config["pdf_quality"] == "high"

    def test_defaults(self):
        spec = ChartSpec(chart_type=ChartType.LINE, title="Test")
        assert spec.id is not None
        assert spec.metric_ids == []
        assert spec.dimension_ids == []
        assert spec.filters == []
        assert spec.color_scheme == ColorScheme.DEFAULT
        assert spec.interactions == []
        assert spec.animation == AnimationType.NONE
        assert spec.accessibility_description == ""
        assert spec.responsive_config == {}
        assert spec.export_config == {}

    def test_to_dict(self, sample_chart_spec):
        d = sample_chart_spec.to_dict()
        assert "id" in d
        assert d["chart_type"] == "bar"
        assert d["title"] == "Revenue by Department"
        assert len(d["metric_ids"]) == 3
        assert len(d["dimension_ids"]) == 2
        assert d["color_scheme"] == "qualitative"
        assert "hover_tooltip" in d["interactions"]
        assert d["animation"] == "grow"
        assert d["accessibility_description"] != ""


# ============================================================
# TEST WIDGET RENDER RESULT
# ============================================================

class TestWidgetRenderResult:
    def test_create_render_result(self, sample_render_result, widget_id):
        assert sample_render_result.id is not None
        assert sample_render_result.widget_id == widget_id
        assert sample_render_result.chart_type == ChartType.LINE
        assert sample_render_result.render_time_ms == 42.5

    def test_render_result_data(self, sample_render_result):
        assert sample_render_result.data["labels"] == ["Jan", "Feb", "Mar"]
        assert sample_render_result.data["values"] == [100, 150, 120]

    def test_render_result_metadata(self, sample_render_result):
        assert sample_render_result.metadata["source"] == "finance_db"
        assert sample_render_result.metadata["refresh_interval"] == 300

    def test_render_result_accessibility(self, sample_render_result):
        assert "Line chart" in sample_render_result.accessibility_text

    def test_defaults(self):
        result = WidgetRenderResult(
            widget_id=uuid.uuid4(),
            chart_type=ChartType.KPI_CARD,
        )
        assert result.data == {}
        assert result.metadata == {}
        assert result.render_time_ms == 0.0
        assert result.accessibility_text == ""

    def test_to_dict(self, sample_render_result):
        d = sample_render_result.to_dict()
        assert "id" in d
        assert d["chart_type"] == "line"
        assert d["render_time_ms"] == 42.5
        assert d["accessibility_text"] != ""


# ============================================================
# TEST VISUALIZATION CONFIG
# ============================================================

class TestVisualizationConfig:
    def test_create_config(self, sample_visualization_config):
        assert sample_visualization_config.id is not None
        assert sample_visualization_config.theme == "dark"
        assert len(sample_visualization_config.color_palette) == 3
        assert sample_visualization_config.font_family == "Roboto, sans-serif"
        assert sample_visualization_config.animation_enabled is True

    def test_set_theme(self, sample_visualization_config):
        sample_visualization_config.set_theme("light")
        assert sample_visualization_config.theme == "light"

    def test_set_color_palette(self, sample_visualization_config):
        new_palette = ["#000000", "#FFFFFF", "#888888"]
        sample_visualization_config.set_color_palette(new_palette)
        assert sample_visualization_config.color_palette == new_palette

    def test_add_color(self, sample_visualization_config):
        sample_visualization_config.add_color("#FF0000")
        assert "#FF0000" in sample_visualization_config.color_palette

    def test_remove_color(self, sample_visualization_config):
        result = sample_visualization_config.remove_color("#FF6384")
        assert result is True
        assert "#FF6384" not in sample_visualization_config.color_palette

    def test_remove_color_not_found(self, sample_visualization_config):
        result = sample_visualization_config.remove_color("#000000")
        assert result is False

    def test_set_font_family(self, sample_visualization_config):
        sample_visualization_config.set_font_family("Arial, sans-serif")
        assert sample_visualization_config.font_family == "Arial, sans-serif"

    def test_toggle_animation(self, sample_visualization_config):
        sample_visualization_config.toggle_animation()
        assert sample_visualization_config.animation_enabled is False
        sample_visualization_config.toggle_animation()
        assert sample_visualization_config.animation_enabled is True

    def test_set_responsive_breakpoint(self, sample_visualization_config):
        sample_visualization_config.set_responsive_breakpoint("ultrawide", 2560)
        assert sample_visualization_config.responsive_breakpoints["ultrawide"] == 2560

    def test_remove_responsive_breakpoint(self, sample_visualization_config):
        result = sample_visualization_config.remove_responsive_breakpoint("mobile")
        assert result is True
        assert "mobile" not in sample_visualization_config.responsive_breakpoints

    def test_remove_responsive_breakpoint_not_found(self, sample_visualization_config):
        result = sample_visualization_config.remove_responsive_breakpoint("nonexistent")
        assert result is False

    def test_defaults(self):
        config = VisualizationConfig()
        assert config.theme == "light"
        assert len(config.color_palette) == 10
        assert config.font_family == "Inter, sans-serif"
        assert config.animation_enabled is True
        assert "mobile" in config.responsive_breakpoints
        assert "tablet" in config.responsive_breakpoints
        assert "desktop" in config.responsive_breakpoints
        assert "wide" in config.responsive_breakpoints

    def test_to_dict(self, sample_visualization_config):
        d = sample_visualization_config.to_dict()
        assert d["theme"] == "dark"
        assert len(d["color_palette"]) == 3
        assert d["animation_enabled"] is True
        assert "responsive_breakpoints" in d


# ============================================================
# TEST CONDITIONAL FORMAT
# ============================================================

class TestConditionalFormat:
    def test_create_conditional_format(self, sample_conditional_format):
        assert sample_conditional_format.id is not None
        assert sample_conditional_format.column == "revenue"
        assert len(sample_conditional_format.rules) == 2

    def test_add_rule(self, sample_conditional_format):
        sample_conditional_format.add_rule({"type": "data_bar", "color": "#36A2EB"})
        assert len(sample_conditional_format.rules) == 3

    def test_remove_rule(self, sample_conditional_format):
        result = sample_conditional_format.remove_rule(0)
        assert result is True
        assert len(sample_conditional_format.rules) == 1

    def test_remove_rule_invalid_index(self, sample_conditional_format):
        result = sample_conditional_format.remove_rule(999)
        assert result is False

    def test_clear_rules(self, sample_conditional_format):
        sample_conditional_format.clear_rules()
        assert len(sample_conditional_format.rules) == 0

    def test_has_rules(self, sample_conditional_format):
        assert sample_conditional_format.has_rules() is True

    def test_has_rules_empty(self):
        fmt = ConditionalFormat(column="cost")
        assert fmt.has_rules() is False

    def test_defaults(self):
        fmt = ConditionalFormat(column="margin")
        assert fmt.rules == []

    def test_to_dict(self, sample_conditional_format):
        d = sample_conditional_format.to_dict()
        assert d["column"] == "revenue"
        assert len(d["rules"]) == 2


# ============================================================
# TEST CHART INTERACTION
# ============================================================

class TestChartInteraction:
    def test_create_interaction(self, sample_chart_interaction):
        assert sample_chart_interaction.id is not None
        assert sample_chart_interaction.interaction_type == InteractionType.DRILL_DOWN
        assert sample_chart_interaction.is_enabled is True
        assert sample_chart_interaction.config["max_depth"] == 3

    def test_enable(self, sample_chart_interaction):
        sample_chart_interaction.disable()
        sample_chart_interaction.enable()
        assert sample_chart_interaction.is_enabled is True

    def test_disable(self, sample_chart_interaction):
        sample_chart_interaction.disable()
        assert sample_chart_interaction.is_enabled is False

    def test_update_config(self, sample_chart_interaction):
        sample_chart_interaction.update_config({"drill_path": ["hospital", "department"]})
        assert "drill_path" in sample_chart_interaction.config
        assert sample_chart_interaction.config["max_depth"] == 3

    def test_get_config_value(self, sample_chart_interaction):
        value = sample_chart_interaction.get_config_value("max_depth")
        assert value == 3

    def test_get_config_value_default(self, sample_chart_interaction):
        value = sample_chart_interaction.get_config_value("nonexistent", "default_val")
        assert value == "default_val"

    def test_set_config_value(self, sample_chart_interaction):
        sample_chart_interaction.set_config_value("new_key", "new_value")
        assert sample_chart_interaction.config["new_key"] == "new_value"

    def test_defaults(self):
        interaction = ChartInteraction(interaction_type=InteractionType.ZOOM)
        assert interaction.id is not None
        assert interaction.config == {}
        assert interaction.is_enabled is True

    def test_to_dict(self, sample_chart_interaction):
        d = sample_chart_interaction.to_dict()
        assert d["interaction_type"] == "drill_down"
        assert d["is_enabled"] is True
        assert d["config"]["max_depth"] == 3


# ============================================================
# TEST ACCESSIBILITY
# ============================================================

class TestAccessibility:
    def test_chart_spec_accessibility_description(self, sample_chart_spec):
        assert sample_chart_spec.accessibility_description != ""
        assert "bar chart" in sample_chart_spec.accessibility_description.lower()

    def test_render_result_accessibility_text(self, sample_render_result):
        assert sample_render_result.accessibility_text != ""
        assert "Line chart" in sample_render_result.accessibility_text

    def test_chart_spec_set_accessibility(self, sample_chart_spec):
        sample_chart_spec.set_accessibility_description("")
        assert sample_chart_spec.accessibility_description == ""
        sample_chart_spec.set_accessibility_description("Screen reader description")
        assert sample_chart_spec.accessibility_description == "Screen reader description"

    def test_all_chart_types_have_value(self):
        for chart_type in ChartType:
            assert chart_type.value != ""


# ============================================================
# TEST CROSS-ENTITY INTEGRATION
# ============================================================

class TestVisualizationIntegration:
    def test_chart_spec_with_all_chart_types(self):
        for chart_type in ChartType:
            spec = ChartSpec(chart_type=chart_type, title=f"Test {chart_type.value}")
            d = spec.to_dict()
            assert d["chart_type"] == chart_type.value

    def test_chart_spec_with_all_interactions(self):
        spec = ChartSpec(chart_type=ChartType.BAR, title="All Interactions")
        for interaction in InteractionType:
            spec.enable_interaction(interaction)
        assert len(spec.interactions) == len(InteractionType)
        for interaction in InteractionType:
            assert spec.has_interaction(interaction) is True

    def test_chart_spec_with_all_animations(self):
        for animation in AnimationType:
            spec = ChartSpec(chart_type=ChartType.LINE, title=f"Animation {animation.value}")
            spec.set_animation(animation)
            assert spec.animation == animation

    def test_chart_spec_with_all_color_schemes(self):
        for scheme in ColorScheme:
            spec = ChartSpec(chart_type=ChartType.BAR, title=f"Scheme {scheme.value}")
            spec.set_color_scheme(scheme)
            assert spec.color_scheme == scheme

    def test_conditional_format_multiple_rules(self):
        fmt = ConditionalFormat(column="status")
        rules = [
            {"type": "color", "condition": "equals", "value": "good", "color": "#00ff00"},
            {"type": "color", "condition": "equals", "value": "warning", "color": "#ffff00"},
            {"type": "color", "condition": "equals", "value": "critical", "color": "#ff0000"},
            {"type": "icon", "condition": "contains", "value": "up", "icon": "arrow_up"},
            {"type": "data_bar", "min": 0, "max": 100, "color": "#36A2EB"},
        ]
        for rule in rules:
            fmt.add_rule(rule)
        assert len(fmt.rules) == 5
        assert fmt.has_rules() is True

    def test_interaction_config_complex(self):
        interaction = ChartInteraction(
            interaction_type=InteractionType.BRUSH_SELECT,
            config={
                "mode": "rectangular",
                "highlight_color": "#FF6384",
                "selection_limit": 50,
                "callbacks": {
                    "on_select": "update_filters",
                    "on_clear": "reset_filters",
                },
            },
        )
        assert interaction.config["callbacks"]["on_select"] == "update_filters"
        assert interaction.config["selection_limit"] == 50
