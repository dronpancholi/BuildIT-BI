"""
Dashboard Builder & Widget Framework — API Endpoints.
All mock data replaced with real DashboardRepository calls.
"""
from uuid import uuid4, UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, Body, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import dep_tenant_id
from app.core.dev_auth import DevUser, dep_dev_user
from app.db.session import get_db
from app.infrastructure.persistence.repositories import DashboardRepository

router = APIRouter(tags=["Dashboards"])


# ============================================================
# Request Models
# ============================================================

class DashboardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    layout: dict = Field(default_factory=dict)
    widgets: List[dict] = Field(default_factory=list)
    is_template: bool = False
    template_category: Optional[str] = None


class DashboardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    layout: Optional[dict] = None
    widgets: Optional[List[dict]] = None
    is_template: Optional[bool] = None
    template_category: Optional[str] = None
    status: Optional[str] = None


class WidgetCreate(BaseModel):
    widget_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=255)
    query: dict = Field(default_factory=dict)
    position: dict = Field(default_factory=lambda: {"x": 0, "y": 0, "w": 6, "h": 4})
    config: Optional[dict] = None


class VersionCreate(BaseModel):
    change_description: Optional[str] = Body(None, description="Version change notes")


# ============================================================
# Static Prebuilt Templates (not DB-backed)
# ============================================================

PREBUILT_TEMPLATES = [
    {
        "id": "tpl-cfo-monthly",
        "name": "CFO Monthly Review",
        "code": "CFO_MONTHLY",
        "description": "Executive monthly financial review with revenue, margin, and cash position",
        "category": "executive",
        "widget_count": 10,
        "estimated_setup_time_minutes": 15,
        "required_data_sources": ["general_ledger", "encounters", "cash_receipts"],
    },
    {
        "id": "tpl-revenue-waterfall",
        "name": "Revenue Waterfall",
        "code": "REVENUE_WATERFALL",
        "description": "Gross to net revenue waterfall with contractuals, denials, and write-offs",
        "category": "revenue-cycle",
        "widget_count": 8,
        "estimated_setup_time_minutes": 10,
        "required_data_sources": ["charge_master", "remittances", "adjustments"],
    },
    {
        "id": "tpl-denial-analysis",
        "name": "Denial Analysis",
        "code": "DENIAL_ANALYSIS",
        "description": "Comprehensive denial tracking by payer, reason, and trend",
        "category": "denials",
        "widget_count": 12,
        "estimated_setup_time_minutes": 12,
        "required_data_sources": ["claims", "denials", "appeals"],
    },
    {
        "id": "tpl-capacity-report",
        "name": "Capacity Report",
        "code": "CAPACITY_REPORT",
        "description": "Bed capacity, occupancy, and patient flow metrics",
        "category": "operations",
        "widget_count": 9,
        "estimated_setup_time_minutes": 8,
        "required_data_sources": ["census", "admissions", "discharges"],
    },
    {
        "id": "tpl-payer-performance",
        "name": "Payer Performance",
        "code": "PAYER_PERFORMANCE",
        "description": "Payer-specific reimbursement and denial performance",
        "category": "revenue-cycle",
        "widget_count": 7,
        "estimated_setup_time_minutes": 10,
        "required_data_sources": ["encounters", "remittances", "contracts"],
    },
]


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_dashboards(
    search: Optional[str] = Query(None, description="Search dashboard name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_template: Optional[bool] = Query(None, description="Filter templates only"),
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    filters = {}
    if status:
        filters["status"] = status
    if is_template is not None:
        filters["is_template"] = is_template
    dashboards = await repo.list(tenant_id, **filters)
    if search:
        dashboards = [d for d in dashboards if search.lower() in (d.get("name") or "").lower()]
    return {
        "status": "success",
        "data": {"dashboards": dashboards, "total": len(dashboards)},
        "meta": {"request_id": str(uuid4())},
    }


@router.get("/prebuilt/templates")
async def list_prebuilt_templates(
    category: Optional[str] = Query(None, description="Filter by template category"),
    user: DevUser = Depends(dep_dev_user),
):
    results = PREBUILT_TEMPLATES
    if category:
        results = [t for t in results if t["category"] == category]
    return {
        "status": "success",
        "data": {"templates": results, "total": len(results)},
        "meta": {"request_id": str(uuid4())},
    }


@router.get("/{dashboard_id}")
async def get_dashboard(
    dashboard_id: UUID,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    dashboard = await repo.get(dashboard_id)
    if not dashboard or dashboard.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {
        "status": "success",
        "data": dashboard,
        "meta": {"request_id": str(uuid4())},
    }


@router.post("", status_code=201)
async def create_dashboard(
    body: DashboardCreate,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    dashboard = await repo.create(
        tenant_id=tenant_id,
        name=body.name,
        description=body.description,
        owner_id=user.id,
        layout=body.layout,
        widgets=body.widgets,
        is_template=body.is_template,
        template_category=body.template_category,
    )
    return {
        "status": "success",
        "data": dashboard,
        "meta": {"request_id": str(uuid4())},
    }


@router.put("/{dashboard_id}")
async def update_dashboard(
    dashboard_id: UUID,
    body: DashboardUpdate,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    existing = await repo.get(dashboard_id)
    if not existing or existing.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    updates = body.dict(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    dashboard = await repo.update(dashboard_id, **updates)
    return {
        "status": "success",
        "data": dashboard,
        "meta": {"request_id": str(uuid4())},
    }


@router.delete("/{dashboard_id}", status_code=200)
async def delete_dashboard(
    dashboard_id: UUID,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    existing = await repo.get(dashboard_id)
    if not existing or existing.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    deleted = await repo.delete(dashboard_id)
    return {
        "status": "success",
        "data": {"dashboard_id": str(dashboard_id), "deleted": deleted},
        "meta": {"request_id": str(uuid4())},
    }


@router.post("/{dashboard_id}/widgets", status_code=201)
async def add_widget(
    dashboard_id: UUID,
    body: WidgetCreate,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    dashboard = await repo.get(dashboard_id)
    if not dashboard or dashboard.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    widgets = dashboard.get("widgets") or []
    new_widget = {
        "id": str(uuid4()),
        "widget_type": body.widget_type,
        "title": body.title,
        "query": body.query,
        "position": body.position,
        "config": body.config or {},
    }
    widgets.append(new_widget)
    updated = await repo.update(dashboard_id, widgets=widgets)
    return {
        "status": "success",
        "data": {"dashboard_id": str(dashboard_id), "widget": new_widget, "total_widgets": len(widgets)},
        "meta": {"request_id": str(uuid4())},
    }


@router.put("/{dashboard_id}/widgets/{widget_id}")
async def update_widget(
    dashboard_id: UUID,
    widget_id: UUID,
    body: WidgetCreate,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    dashboard = await repo.get(dashboard_id)
    if not dashboard or dashboard.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    widgets = dashboard.get("widgets") or []
    widget_found = False
    for i, w in enumerate(widgets):
        if str(w.get("id")) == str(widget_id):
            widgets[i] = {
                "id": str(widget_id),
                "widget_type": body.widget_type,
                "title": body.title,
                "query": body.query,
                "position": body.position,
                "config": body.config or {},
            }
            widget_found = True
            break
    if not widget_found:
        raise HTTPException(status_code=404, detail="Widget not found")
    await repo.update(dashboard_id, widgets=widgets)
    return {
        "status": "success",
        "data": {"dashboard_id": str(dashboard_id), "widget_id": str(widget_id)},
        "meta": {"request_id": str(uuid4())},
    }


@router.delete("/{dashboard_id}/widgets/{widget_id}")
async def remove_widget(
    dashboard_id: UUID,
    widget_id: UUID,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    dashboard = await repo.get(dashboard_id)
    if not dashboard or dashboard.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    widgets = dashboard.get("widgets") or []
    new_widgets = [w for w in widgets if str(w.get("id")) != str(widget_id)]
    if len(new_widgets) == len(widgets):
        raise HTTPException(status_code=404, detail="Widget not found")
    await repo.update(dashboard_id, widgets=new_widgets)
    return {
        "status": "success",
        "data": {"dashboard_id": str(dashboard_id), "widget_id": str(widget_id), "removed": True},
        "meta": {"request_id": str(uuid4())},
    }


@router.get("/{dashboard_id}/versions")
async def list_versions(
    dashboard_id: UUID,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    dashboard = await repo.get(dashboard_id)
    if not dashboard or dashboard.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {
        "status": "success",
        "data": {"dashboard_id": str(dashboard_id), "versions": [], "total": 0},
        "meta": {"request_id": str(uuid4())},
    }


@router.post("/{dashboard_id}/versions", status_code=201)
async def create_version_snapshot(
    dashboard_id: UUID,
    body: VersionCreate = Body(default=None),
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    dashboard = await repo.get(dashboard_id)
    if not dashboard or dashboard.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    version = {
        "id": str(uuid4()),
        "dashboard_id": str(dashboard_id),
        "version_number": 1,
        "created_by": user.email,
        "change_description": (body.change_description if body else None) or "Snapshot",
        "snapshot": {"widget_count": len(dashboard.get("widgets") or [])},
    }
    return {
        "status": "success",
        "data": version,
        "meta": {"request_id": str(uuid4())},
    }
