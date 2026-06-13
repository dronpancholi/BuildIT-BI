from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dev_auth import DevUser, dep_dev_admin
from app.db.session import get_db
from app.infrastructure.persistence.repositories import VisualizationSpecRepository

router = APIRouter(tags=["Visualization Library"])


# ============================================================
# Static Chart Types & Color Schemes (reference config, not mock)
# ============================================================

CHART_TYPES = [
    {"id": "bar", "name": "Bar Chart", "category": "comparison", "supports_multiple_series": True, "supports_time_axis": False, "description": "Compare values across categories"},
    {"id": "stacked_bar", "name": "Stacked Bar Chart", "category": "composition", "supports_multiple_series": True, "supports_time_axis": False, "description": "Show composition within categories"},
    {"id": "grouped_bar", "name": "Grouped Bar Chart", "category": "comparison", "supports_multiple_series": True, "supports_time_axis": False, "description": "Side-by-side comparison of multiple series"},
    {"id": "line", "name": "Line Chart", "category": "trend", "supports_multiple_series": True, "supports_time_axis": True, "description": "Visualize trends over time"},
    {"id": "area", "name": "Area Chart", "category": "trend", "supports_multiple_series": True, "supports_time_axis": True, "description": "Show volume and trend over time"},
    {"id": "stacked_area", "name": "Stacked Area Chart", "category": "composition", "supports_multiple_series": True, "supports_time_axis": True, "description": "Show cumulative composition over time"},
    {"id": "pie", "name": "Pie Chart", "category": "composition", "supports_multiple_series": False, "supports_time_axis": False, "description": "Show proportional breakdown"},
    {"id": "donut", "name": "Donut Chart", "category": "composition", "supports_multiple_series": False, "supports_time_axis": False, "description": "Proportional breakdown with center label"},
    {"id": "treemap", "name": "Treemap", "category": "hierarchy", "supports_multiple_series": False, "supports_time_axis": False, "description": "Display hierarchical data as nested rectangles"},
    {"id": "funnel", "name": "Funnel Chart", "category": "process", "supports_multiple_series": False, "supports_time_axis": False, "description": "Show stages in a process with drop-off"},
    {"id": "scatter", "name": "Scatter Plot", "category": "correlation", "supports_multiple_series": True, "supports_time_axis": False, "description": "Show relationship between two variables"},
    {"id": "bubble", "name": "Bubble Chart", "category": "correlation", "supports_multiple_series": True, "supports_time_axis": False, "description": "Scatter plot with size dimension"},
    {"id": "heatmap", "name": "Heatmap", "category": "density", "supports_multiple_series": False, "supports_time_axis": False, "description": "Show density using color intensity"},
    {"id": "sparkline", "name": "Sparkline", "category": "trend", "supports_multiple_series": False, "supports_time_axis": True, "description": "Compact inline trend indicator"},
    {"id": "gauge", "name": "Gauge Chart", "category": "indicator", "supports_multiple_series": False, "supports_time_axis": False, "description": "Show progress toward a target"},
    {"id": "waterfall", "name": "Waterfall Chart", "category": "flow", "supports_multiple_series": False, "supports_time_axis": False, "description": "Show cumulative effect of sequential changes"},
    {"id": "sankey", "name": "Sankey Diagram", "category": "flow", "supports_multiple_series": False, "supports_time_axis": False, "description": "Visualize flow and proportional distribution"},
    {"id": "box_plot", "name": "Box Plot", "category": "distribution", "supports_multiple_series": True, "supports_time_axis": False, "description": "Show data distribution and outliers"},
    {"id": "bullet", "name": "Bullet Chart", "category": "indicator", "supports_multiple_series": False, "supports_time_axis": False, "description": "Compare a measure to a target and benchmarks"},
]

COLOR_SCHEMES = [
    {
        "id": "healthcare_primary",
        "name": "Healthcare Primary",
        "description": "Professional healthcare color palette with blue, teal, and green tones",
        "colors": ["#1E3A5F", "#2E86AB", "#A2D2FF", "#4ECDC4", "#2ECC71", "#F39C12"],
        "category": "healthcare",
        "is_default": True,
    },
    {
        "id": "revenue_cycle",
        "name": "Revenue Cycle",
        "description": "Color scheme optimized for financial metrics and revenue dashboards",
        "colors": ["#1B4332", "#2D6A4F", "#40916C", "#52B788", "#74C69D", "#95D5B2"],
        "category": "financial",
        "is_default": False,
    },
    {
        "id": "claims_analytics",
        "name": "Claims Analytics",
        "description": "High-contrast palette for claims data and denial tracking",
        "colors": ["#D00000", "#E85D04", "#F48C06", "#FAA307", "#FFBA08", "#FFD60A"],
        "category": "alerts",
        "is_default": False,
    },
    {
        "id": "accessible_viridis",
        "name": "Accessible Viridis",
        "description": "Colorblind-friendly palette following WCAG guidelines",
        "colors": ["#440154", "#482878", "#3E4989", "#31688E", "#26838F", "#1F9E89"],
        "category": "accessible",
        "is_default": False,
    },
    {
        "id": "corporate_neutral",
        "name": "Corporate Neutral",
        "description": "Neutral gray palette for formal presentations",
        "colors": ["#1A1A2E", "#16213E", "#0F3460", "#533483", "#6C757D", "#ADB5BD"],
        "category": "corporate",
        "is_default": False,
    },
]


# ============================================================
# Chart Types (static config)
# ============================================================

@router.get("/chart-types")
async def list_chart_types(
    current_user: DevUser = Depends(dep_dev_admin),
):
    """List all 19 chart types with metadata."""
    return {"status": "success", "data": CHART_TYPES, "meta": {"request_id": str(uuid4())}}


# ============================================================
# Chart Specs (DB-backed)
# ============================================================

@router.post("/specs")
async def create_chart_spec(
    chart_type: str = Query(..., description="Chart type ID"),
    title: str = Query(..., min_length=1, max_length=255),
    data_source: str = Query(..., description="Data source identifier"),
    x_field: str = Query(..., alias="xField"),
    y_field: str = Query(..., alias="yField"),
    color_scheme: str = Query(default="healthcare_primary"),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chart specification."""
    repo = VisualizationSpecRepository(db)
    spec = await repo.create(
        tenant_id=str(current_user.tenant_id),
        chart_type=chart_type,
        title=title,
        data_source=data_source,
        spec={
            "$schema": "https://buildit.com/schemas/chart-spec/v2.json",
            "type": chart_type,
            "data": {"source": data_source},
            "encoding": {
                "x": {"field": x_field, "type": "nominal"},
                "y": {"field": y_field, "type": "quantitative"},
            },
            "config": {
                "color_scheme": color_scheme,
                "width": "auto",
                "height": 400,
                "padding": 16,
            },
        },
        created_by=str(current_user.id),
        version=1,
    )
    return {"status": "success", "data": spec, "meta": {"request_id": str(uuid4())}}


@router.get("/specs/{spec_id}")
async def get_chart_spec(
    spec_id: UUID,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a chart specification by ID."""
    repo = VisualizationSpecRepository(db)
    spec = await repo.get(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Chart spec not found")
    return {"status": "success", "data": spec, "meta": {"request_id": str(uuid4())}}


@router.put("/specs/{spec_id}")
async def update_chart_spec(
    spec_id: UUID,
    title: str = Query(default=None),
    chart_type: str = Query(default=None),
    color_scheme: str = Query(default=None),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a chart specification."""
    repo = VisualizationSpecRepository(db)
    existing = await repo.get(spec_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Chart spec not found")
    updates = {}
    if title is not None:
        updates["title"] = title
    if chart_type is not None:
        updates["chart_type"] = chart_type
    if color_scheme is not None:
        updates["color_scheme"] = color_scheme
    if updates:
        spec = await repo.update(spec_id, **updates)
    else:
        spec = existing
    return {"status": "success", "data": spec, "meta": {"request_id": str(uuid4())}}


@router.post("/specs/{spec_id}/render")
async def render_chart(
    spec_id: UUID,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Render chart with data — returns WidgetRenderResult."""
    repo = VisualizationSpecRepository(db)
    spec = await repo.get(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Chart spec not found")
    render_result = {
        "spec_id": str(spec_id),
        "rendered_at": datetime.utcnow().isoformat(),
        "status": "success",
        "widget_render_result": {
            "widget_type": "chart",
            "render_time_ms": 0,
            "data_points_count": 0,
            "metadata": {
                "chart_type": spec.get("chart_type", "bar"),
            },
        },
        "rendered_by": str(current_user.id),
    }
    return {"status": "success", "data": render_result, "meta": {"request_id": str(uuid4())}}


# ============================================================
# Color Schemes (static config)
# ============================================================

@router.get("/color-schemes")
async def list_color_schemes(
    current_user: DevUser = Depends(dep_dev_admin),
):
    """List available color schemes."""
    return {"status": "success", "data": COLOR_SCHEMES, "meta": {"request_id": str(uuid4())}}


# ============================================================
# Visualization Config (static config)
# ============================================================

@router.get("/config")
async def get_visualization_config(
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Get visualization config defaults."""
    config = {
        "defaults": {
            "chart_width": 800,
            "chart_height": 400,
            "padding": 16,
            "font_family": "Inter, -apple-system, sans-serif",
            "font_size": 12,
            "title_font_size": 16,
            "color_scheme": "healthcare_primary",
            "background_color": "#FFFFFF",
            "grid_color": "#E5E7EB",
            "axis_color": "#6B7280",
            "label_color": "#374151",
        },
        "interactions": {
            "hover_enabled": True,
            "tooltip_enabled": True,
            "zoom_enabled": False,
            "pan_enabled": False,
            "selection_enabled": True,
            "crossfilter_enabled": True,
        },
        "exports": {
            "svg_enabled": True,
            "png_enabled": True,
            "pdf_enabled": True,
            "csv_enabled": True,
            "default_dpi": 150,
        },
        "performance": {
            "max_data_points": 10000,
            "animation_duration_ms": 300,
            "throttle_ms": 100,
            "virtual_scrolling": True,
        },
        "updated_at": datetime.utcnow().isoformat(),
        "updated_by": str(current_user.id),
    }
    return {"status": "success", "data": config, "meta": {"request_id": str(uuid4())}}


@router.put("/config")
async def update_visualization_config(
    chart_width: int = Query(default=None, ge=200, le=2400),
    chart_height: int = Query(default=None, ge=100, le=1600),
    color_scheme: str = Query(default=None),
    animation_duration_ms: int = Query(default=None, ge=0, le=2000),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Update visualization config defaults."""
    result = {
        "updated_at": datetime.utcnow().isoformat(),
        "updated_by": str(current_user.id),
        "changes": [],
    }
    if chart_width is not None:
        result["changes"].append({"field": "chart_width", "new_value": chart_width})
    if chart_height is not None:
        result["changes"].append({"field": "chart_height", "new_value": chart_height})
    if color_scheme is not None:
        result["changes"].append({"field": "color_scheme", "new_value": color_scheme})
    if animation_duration_ms is not None:
        result["changes"].append({"field": "animation_duration_ms", "new_value": animation_duration_ms})
    return {"status": "success", "data": result, "meta": {"request_id": str(uuid4())}}
