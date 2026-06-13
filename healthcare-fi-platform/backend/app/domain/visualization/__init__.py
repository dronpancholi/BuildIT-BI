"""
Domain 9: Visualization Library — Chart specifications, rendering, interactions, and accessibility.
Defines the full vocabulary for chart types, colour schemes, interactions, and widget output.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


# ============================================================
# CHART TYPE
# ============================================================

class ChartType(Enum):
    """All supported chart types in the visualization library."""
    LINE = "line"
    BAR = "bar"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    WATERFALL = "waterfall"
    GAUGE = "gauge"
    TREEMAP = "treemap"
    MATRIX = "matrix"
    TABLE = "table"
    KPI_CARD = "kpi_card"
    INSIGHT_FEED = "insight_feed"
    FORECAST = "forecast"
    FUNNEL = "funnel"
    BOX_PLOT = "box_plot"
    COMBO = "combo"
    SPARKLINE = "sparkline"


# ============================================================
# INTERACTION TYPE
# ============================================================

class InteractionType(Enum):
    """User interactions that can be enabled on visualizations."""
    HOVER_TOOLTIP = "hover_tooltip"
    CLICK_FILTER = "click_filter"
    ZOOM = "zoom"
    PAN = "pan"
    DRILL_DOWN = "drill_down"
    BRUSH_SELECT = "brush_select"
    TOGGLE_SERIES = "toggle_series"
    EXPAND_COLLAPSE = "expand_collapse"


# ============================================================
# ANIMATION TYPE
# ============================================================

class AnimationType(Enum):
    """Animation presets applied when data or view state changes."""
    NONE = "none"
    FADE_IN = "fade_in"
    GROW = "grow"
    MORPH = "morph"
    STAGGER = "stagger"
    SMOOTH_TRANSITION = "smooth_transition"


# ============================================================
# COLOR SCHEME
# ============================================================

class ColorScheme(Enum):
    """Built-in colour palettes for charts."""
    DEFAULT = "default"
    QUALITATIVE = "qualitative"
    SEQUENTIAL = "sequential"
    DIVERGING = "diverging"
    COLORBLIND_SAFE = "colorblind_safe"


# ============================================================
# CHART SPEC
# ============================================================

@dataclass(kw_only=True)
class ChartSpec:
    """Complete specification for a single chart / widget."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    chart_type: ChartType
    title: str
    metric_ids: List[uuid.UUID] = field(default_factory=list)
    dimension_ids: List[uuid.UUID] = field(default_factory=list)
    filters: List[Dict[str, Any]] = field(default_factory=list)
    color_scheme: ColorScheme = ColorScheme.DEFAULT
    interactions: List[InteractionType] = field(default_factory=list)
    animation: AnimationType = AnimationType.NONE
    accessibility_description: str = ""
    responsive_config: Dict[str, Any] = field(default_factory=dict)
    export_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_metric(self, metric_id: uuid.UUID) -> None:
        """Add a metric to the chart spec."""
        if metric_id not in self.metric_ids:
            self.metric_ids.append(metric_id)
            self.updated_at = datetime.utcnow()

    def remove_metric(self, metric_id: uuid.UUID) -> bool:
        """Remove a metric. Returns True if removed."""
        if metric_id in self.metric_ids:
            self.metric_ids.remove(metric_id)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def add_dimension(self, dimension_id: uuid.UUID) -> None:
        """Add a dimension to the chart spec."""
        if dimension_id not in self.dimension_ids:
            self.dimension_ids.append(dimension_id)
            self.updated_at = datetime.utcnow()

    def remove_dimension(self, dimension_id: uuid.UUID) -> bool:
        """Remove a dimension. Returns True if removed."""
        if dimension_id in self.dimension_ids:
            self.dimension_ids.remove(dimension_id)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def add_filter(self, filter_config: Dict[str, Any]) -> None:
        """Add a filter to the chart spec."""
        self.filters.append(filter_config)
        self.updated_at = datetime.utcnow()

    def remove_filter(self, index: int) -> bool:
        """Remove a filter by index. Returns True if removed."""
        if 0 <= index < len(self.filters):
            self.filters.pop(index)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def enable_interaction(self, interaction: InteractionType) -> None:
        """Enable a user interaction."""
        if interaction not in self.interactions:
            self.interactions.append(interaction)
            self.updated_at = datetime.utcnow()

    def disable_interaction(self, interaction: InteractionType) -> bool:
        """Disable a user interaction. Returns True if removed."""
        if interaction in self.interactions:
            self.interactions.remove(interaction)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def has_interaction(self, interaction: InteractionType) -> bool:
        """Check whether a specific interaction is enabled."""
        return interaction in self.interactions

    def set_color_scheme(self, scheme: ColorScheme) -> None:
        """Change the colour scheme."""
        self.color_scheme = scheme
        self.updated_at = datetime.utcnow()

    def set_animation(self, animation: AnimationType) -> None:
        """Change the animation type."""
        self.animation = animation
        self.updated_at = datetime.utcnow()

    def set_accessibility_description(self, description: str) -> None:
        """Set the accessibility description for screen readers."""
        self.accessibility_description = description
        self.updated_at = datetime.utcnow()

    def update_responsive_config(self, config: Dict[str, Any]) -> None:
        """Merge new responsive configuration."""
        self.responsive_config.update(config)
        self.updated_at = datetime.utcnow()

    def update_export_config(self, config: Dict[str, Any]) -> None:
        """Merge new export configuration."""
        self.export_config.update(config)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "chart_type": self.chart_type.value,
            "title": self.title,
            "metric_ids": [str(m) for m in self.metric_ids],
            "dimension_ids": [str(d) for d in self.dimension_ids],
            "filters": self.filters,
            "color_scheme": self.color_scheme.value,
            "interactions": [i.value for i in self.interactions],
            "animation": self.animation.value,
            "accessibility_description": self.accessibility_description,
            "responsive_config": self.responsive_config,
            "export_config": self.export_config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ============================================================
# WIDGET RENDER RESULT
# ============================================================

@dataclass(kw_only=True)
class WidgetRenderResult:
    """Output produced by a widget renderer after binding data to a chart spec."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    widget_id: uuid.UUID
    chart_type: ChartType
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    render_time_ms: float = 0.0
    accessibility_text: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "widget_id": str(self.widget_id),
            "chart_type": self.chart_type.value,
            "data": self.data,
            "metadata": self.metadata,
            "render_time_ms": self.render_time_ms,
            "accessibility_text": self.accessibility_text,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================
# VISUALIZATION CONFIG
# ============================================================

@dataclass(kw_only=True)
class VisualizationConfig:
    """Global configuration for the visualization engine."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    theme: str = "light"
    color_palette: List[str] = field(default_factory=lambda: [
        "#4E79A7", "#F28E2B", "#E15759", "#76B7B2",
        "#59A14F", "#EDC948", "#B07AA1", "#FF9DA7",
        "#9C755F", "#BAB0AC",
    ])
    font_family: str = "Inter, sans-serif"
    animation_enabled: bool = True
    responsive_breakpoints: Dict[str, int] = field(default_factory=lambda: {
        "mobile": 480,
        "tablet": 768,
        "desktop": 1024,
        "wide": 1440,
    })
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def set_theme(self, theme: str) -> None:
        """Set the global theme."""
        self.theme = theme
        self.updated_at = datetime.utcnow()

    def set_color_palette(self, colors: List[str]) -> None:
        """Replace the global colour palette."""
        self.color_palette = colors
        self.updated_at = datetime.utcnow()

    def add_color(self, color: str) -> None:
        """Append a colour to the palette."""
        self.color_palette.append(color)
        self.updated_at = datetime.utcnow()

    def remove_color(self, color: str) -> bool:
        """Remove a colour from the palette. Returns True if removed."""
        if color in self.color_palette:
            self.color_palette.remove(color)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def set_font_family(self, font_family: str) -> None:
        """Set the global font family."""
        self.font_family = font_family
        self.updated_at = datetime.utcnow()

    def toggle_animation(self) -> None:
        """Toggle animation on/off."""
        self.animation_enabled = not self.animation_enabled
        self.updated_at = datetime.utcnow()

    def set_responsive_breakpoint(self, name: str, width: int) -> None:
        """Set a named responsive breakpoint width in pixels."""
        self.responsive_breakpoints[name] = width
        self.updated_at = datetime.utcnow()

    def remove_responsive_breakpoint(self, name: str) -> bool:
        """Remove a named breakpoint. Returns True if removed."""
        if name in self.responsive_breakpoints:
            del self.responsive_breakpoints[name]
            self.updated_at = datetime.utcnow()
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "theme": self.theme,
            "color_palette": self.color_palette,
            "font_family": self.font_family,
            "animation_enabled": self.animation_enabled,
            "responsive_breakpoints": self.responsive_breakpoints,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ============================================================
# CONDITIONAL FORMAT
# ============================================================

@dataclass(kw_only=True)
class ConditionalFormat:
    """Conditional formatting rules applied to a specific column in a table or matrix."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    column: str
    rules: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_rule(self, rule: Dict[str, Any]) -> None:
        """Add a conditional formatting rule."""
        self.rules.append(rule)
        self.updated_at = datetime.utcnow()

    def remove_rule(self, index: int) -> bool:
        """Remove a rule by index. Returns True if removed."""
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def clear_rules(self) -> None:
        """Remove all rules."""
        self.rules.clear()
        self.updated_at = datetime.utcnow()

    def has_rules(self) -> bool:
        """Check whether any rules are defined."""
        return len(self.rules) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "column": self.column,
            "rules": self.rules,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ============================================================
# CHART INTERACTION
# ============================================================

@dataclass(kw_only=True)
class ChartInteraction:
    """A configured interaction on a chart with its associated settings."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    interaction_type: InteractionType
    config: Dict[str, Any] = field(default_factory=dict)
    is_enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def enable(self) -> None:
        """Enable this interaction."""
        self.is_enabled = True
        self.updated_at = datetime.utcnow()

    def disable(self) -> None:
        """Disable this interaction."""
        self.is_enabled = False
        self.updated_at = datetime.utcnow()

    def update_config(self, config: Dict[str, Any]) -> None:
        """Merge new configuration into the existing config."""
        self.config.update(config)
        self.updated_at = datetime.utcnow()

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a single configuration value."""
        return self.config.get(key, default)

    def set_config_value(self, key: str, value: Any) -> None:
        """Set a single configuration value."""
        self.config[key] = value
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "interaction_type": self.interaction_type.value,
            "config": self.config,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
