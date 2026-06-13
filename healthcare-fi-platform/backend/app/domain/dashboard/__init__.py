"""
Dashboard Builder Domain — Entities for the healthcare financial dashboard system.

Provides widget types, grid layout, dashboard versioning, personal dashboards,
and pre-built templates for common healthcare finance workflows.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Widget Type Enum
# ---------------------------------------------------------------------------

class WidgetType(Enum):
    """Supported visualization widget types."""

    KPI_CARD = "kpi_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    AREA_CHART = "area_chart"
    PIE_CHART = "pie_chart"
    TREEMAP = "treemap"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    WATERFALL = "waterfall"
    GAUGE = "gauge"
    MATRIX = "matrix"
    TABLE = "table"
    INSIGHT_FEED = "insight_feed"
    FORECAST = "forecast"


# ---------------------------------------------------------------------------
# Grid Position
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class GridPosition:
    """Position and size of a widget on a 12-column responsive grid."""

    col_start: int = 1
    col_span: int = 6
    row_start: int = 1
    row_span: int = 4

    def __post_init__(self) -> None:
        if not (1 <= self.col_start <= 12):
            raise ValueError(f"col_start must be 1-12, got {self.col_start}")
        if not (1 <= self.col_span <= 12):
            raise ValueError(f"col_span must be 1-12, got {self.col_span}")
        if self.col_start + self.col_span - 1 > 12:
            raise ValueError(
                f"Widget extends beyond grid: col_start={self.col_start} + "
                f"col_span={self.col_span} > 12"
            )
        if self.row_start < 1:
            raise ValueError(f"row_start must be >= 1, got {self.row_start}")
        if self.row_span < 1:
            raise ValueError(f"row_span must be >= 1, got {self.row_span}")


# ---------------------------------------------------------------------------
# Dashboard Widget
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class DashboardWidget:
    """A single widget rendered inside a dashboard."""

    widget_id: uuid.UUID = field(default_factory=uuid.uuid4)
    widget_type: WidgetType = WidgetType.KPI_CARD
    title: str = ""
    position: GridPosition = field(default_factory=GridPosition)
    metric_ids: list[str] = field(default_factory=list)
    dimension_ids: list[str] = field(default_factory=list)
    filters: list[dict[str, Any]] = field(default_factory=list)
    time_range: dict[str, Any] = field(default_factory=dict)
    visualization_config: dict[str, Any] = field(default_factory=dict)
    link_filters: dict[str, Any] = field(default_factory=dict)
    refresh_interval: Optional[int] = None


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class Dashboard:
    """Top-level dashboard entity."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    description: str = ""
    widgets: list[DashboardWidget] = field(default_factory=list)
    layout_version: int = 1
    is_template: bool = False
    template_category: Optional[str] = None
    owner_id: uuid.UUID = field(default_factory=uuid.uuid4)
    tenant_id: uuid.UUID = field(default_factory=uuid.uuid4)
    variables: dict[str, Any] = field(default_factory=dict)
    auto_refresh: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Dashboard Version
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class DashboardVersion:
    """Immutable snapshot of a dashboard at a point in time."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    dashboard_id: uuid.UUID = field(default_factory=uuid.uuid4)
    version: int = 1
    snapshot: dict[str, Any] = field(default_factory=dict)
    changed_by: uuid.UUID = field(default_factory=uuid.uuid4)
    changed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    change_type: str = "update"
    change_summary: str = ""


# ---------------------------------------------------------------------------
# Personal Dashboard
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class PersonalDashboard:
    """Per-user customisation overlay on top of a shared dashboard."""

    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    dashboard_id: uuid.UUID = field(default_factory=uuid.uuid4)
    layout_snapshot: list[dict[str, Any]] = field(default_factory=list)
    is_default: bool = False
    notifications_enabled: bool = True
    refresh_override: Optional[int] = None


# ---------------------------------------------------------------------------
# Dashboard Template
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class DashboardTemplate:
    """Pre-built dashboard template that can be instantiated for a tenant."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    description: str = ""
    category: str = ""
    widgets: list[DashboardWidget] = field(default_factory=list)
    default_filters: list[dict[str, Any]] = field(default_factory=list)
    target_audience: str = ""


# ---------------------------------------------------------------------------
# Pre-built Templates (class-level constants)
# ---------------------------------------------------------------------------

class PrebuiltDashboardTemplates:
    """Factory methods for the four standard healthcare-finance templates."""

    @staticmethod
    def cfo_monthly() -> DashboardTemplate:
        """CFO Monthly Overview — high-level KPIs and revenue trends."""
        return DashboardTemplate(
            name="CFO Monthly Overview",
            description="Executive-level monthly summary of revenue, margin, denials, and cash.",
            category="executive",
            widgets=[
                DashboardWidget(
                    title="Net Revenue",
                    widget_type=WidgetType.KPI_CARD,
                    position=GridPosition(col_start=1, col_span=3, row_start=1, row_span=2),
                    metric_ids=["net_revenue"],
                ),
                DashboardWidget(
                    title="Operating Margin %",
                    widget_type=WidgetType.GAUGE,
                    position=GridPosition(col_start=4, col_span=3, row_start=1, row_span=2),
                    metric_ids=["operating_margin_pct"],
                ),
                DashboardWidget(
                    title="Days in A/R",
                    widget_type=WidgetType.KPI_CARD,
                    position=GridPosition(col_start=7, col_span=3, row_start=1, row_span=2),
                    metric_ids=["days_in_ar"],
                ),
                DashboardWidget(
                    title="Denial Rate",
                    widget_type=WidgetType.KPI_CARD,
                    position=GridPosition(col_start=10, col_span=3, row_start=1, row_span=2),
                    metric_ids=["denial_rate_pct"],
                ),
                DashboardWidget(
                    title="Revenue Trend (12 months)",
                    widget_type=WidgetType.LINE_CHART,
                    position=GridPosition(col_start=1, col_span=8, row_start=3, row_span=4),
                    metric_ids=["net_revenue", "gross_revenue", "total_charges"],
                ),
                DashboardWidget(
                    title="Payer Mix",
                    widget_type=WidgetType.PIE_CHART,
                    position=GridPosition(col_start=9, col_span=4, row_start=3, row_span=4),
                    metric_ids=["revenue_by_payer"],
                    dimension_ids=["payer_name"],
                ),
            ],
            default_filters=[
                {"field": "report_date", "operator": "gte", "value": "first_day_of_current_month"},
            ],
            target_audience="CFO",
        )

    @staticmethod
    def revenue_waterfall() -> DashboardTemplate:
        """Revenue Waterfall — gross-to-net walk analysis."""
        return DashboardTemplate(
            name="Revenue Waterfall",
            description="Gross-to-net revenue waterfall with contractual adjustments, "
                        "charity care, and bad debt breakdowns.",
            category="revenue_cycle",
            widgets=[
                DashboardWidget(
                    title="Gross-to-Net Waterfall",
                    widget_type=WidgetType.WATERFALL,
                    position=GridPosition(col_start=1, col_span=12, row_start=1, row_span=6),
                    metric_ids=[
                        "gross_revenue",
                        "contractual_adjustments",
                        "charity_care",
                        "bad_debt",
                        "net_revenue",
                    ],
                ),
                DashboardWidget(
                    title="Adjustment Categories",
                    widget_type=WidgetType.BAR_CHART,
                    position=GridPosition(col_start=1, col_span=6, row_start=7, row_span=4),
                    metric_ids=["adjustment_amount"],
                    dimension_ids=["adjustment_category"],
                ),
                DashboardWidget(
                    title="Monthly Waterfall Trend",
                    widget_type=WidgetType.AREA_CHART,
                    position=GridPosition(col_start=7, col_span=6, row_start=7, row_span=4),
                    metric_ids=[
                        "contractual_adjustments",
                        "charity_care",
                        "bad_debt",
                    ],
                ),
            ],
            default_filters=[],
            target_audience="Revenue Cycle Analysts",
        )

    @staticmethod
    def denial_analysis() -> DashboardTemplate:
        """Denial Analysis — root-cause and trend analysis for claim denials."""
        return DashboardTemplate(
            name="Denial Analysis",
            description="Comprehensive denial tracking with root-cause categories, "
                        "payer breakdown, and recovery rates.",
            category="denials",
            widgets=[
                DashboardWidget(
                    title="Total Denials",
                    widget_type=WidgetType.KPI_CARD,
                    position=GridPosition(col_start=1, col_span=3, row_start=1, row_span=2),
                    metric_ids=["total_denials"],
                ),
                DashboardWidget(
                    title="Denial Rate %",
                    widget_type=WidgetType.GAUGE,
                    position=GridPosition(col_start=4, col_span=3, row_start=1, row_span=2),
                    metric_ids=["denial_rate_pct"],
                ),
                DashboardWidget(
                    title="Appeal Success Rate",
                    widget_type=WidgetType.GAUGE,
                    position=GridPosition(col_start=7, col_span=3, row_start=1, row_span=2),
                    metric_ids=["appeal_success_rate_pct"],
                ),
                DashboardWidget(
                    title="Net Denial Amount",
                    widget_type=WidgetType.KPI_CARD,
                    position=GridPosition(col_start=10, col_span=3, row_start=1, row_span=2),
                    metric_ids=["net_denial_amount"],
                ),
                DashboardWidget(
                    title="Denials by Root Cause",
                    widget_type=WidgetType.TREEMAP,
                    position=GridPosition(col_start=1, col_span=6, row_start=3, row_span=5),
                    metric_ids=["denial_amount"],
                    dimension_ids=["denial_reason_code"],
                ),
                DashboardWidget(
                    title="Denials by Payer",
                    widget_type=WidgetType.BAR_CHART,
                    position=GridPosition(col_start=7, col_span=6, row_start=3, row_span=5),
                    metric_ids=["denial_amount"],
                    dimension_ids=["payer_name"],
                ),
                DashboardWidget(
                    title="Denial Trend",
                    widget_type=WidgetType.LINE_CHART,
                    position=GridPosition(col_start=1, col_span=12, row_start=8, row_span=4),
                    metric_ids=["total_denials", "denial_amount", "appeal_amount"],
                ),
            ],
            default_filters=[],
            target_audience="Denial Management Team",
        )

    @staticmethod
    def capacity_report() -> DashboardTemplate:
        """Capacity Report — bed, staffing, and utilization overview."""
        return DashboardTemplate(
            name="Capacity Report",
            description="Hospital capacity metrics including bed occupancy, staffing ratios, "
                        "and elective surgery throughput.",
            category="operations",
            widgets=[
                DashboardWidget(
                    title="Bed Occupancy %",
                    widget_type=WidgetType.GAUGE,
                    position=GridPosition(col_start=1, col_span=3, row_start=1, row_span=2),
                    metric_ids=["bed_occupancy_pct"],
                ),
                DashboardWidget(
                    title="Avg Length of Stay",
                    widget_type=WidgetType.KPI_CARD,
                    position=GridPosition(col_start=4, col_span=3, row_start=1, row_span=2),
                    metric_ids=["avg_los_days"],
                ),
                DashboardWidget(
                    title="Staffing Ratio",
                    widget_type=WidgetType.KPI_CARD,
                    position=GridPosition(col_start=7, col_span=3, row_start=1, row_span=2),
                    metric_ids=["nurse_patient_ratio"],
                ),
                DashboardWidget(
                    title="OR Utilization %",
                    widget_type=WidgetType.GAUGE,
                    position=GridPosition(col_start=10, col_span=3, row_start=1, row_span=2),
                    metric_ids=["or_utilization_pct"],
                ),
                DashboardWidget(
                    title="Capacity Heatmap (by Unit)",
                    widget_type=WidgetType.HEATMAP,
                    position=GridPosition(col_start=1, col_span=8, row_start=3, row_span=5),
                    metric_ids=["capacity_pct"],
                    dimension_ids=["unit_name", "hour_of_day"],
                ),
                DashboardWidget(
                    title="Elective Surgery Throughput",
                    widget_type=WidgetType.BAR_CHART,
                    position=GridPosition(col_start=9, col_span=4, row_start=3, row_span=5),
                    metric_ids=["surgery_count"],
                    dimension_ids=["surgery_type"],
                ),
            ],
            default_filters=[],
            target_audience="COO / Operations",
        )
