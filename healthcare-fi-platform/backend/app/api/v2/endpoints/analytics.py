from uuid import uuid4, UUID
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Body, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dev_auth import DevUser, dep_dev_admin
from app.db.session import get_db
from app.infrastructure.persistence.repositories import (
    SemanticMetricRepository,
    SemanticDimensionRepository,
)

router = APIRouter()


# ── Request / Response Models ────────────────────────────────────────────────


class SemanticMetricCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    expression: str
    description: Optional[str] = None
    category: Optional[str] = None
    data_type: str = "decimal"


class SemanticMetricUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    expression: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    data_type: Optional[str] = None
    status: Optional[str] = None


class DimensionCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    physical_name: str
    key_column: str
    data_type: str = "string"
    cardinality: Optional[str] = None


class DimensionUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    physical_name: Optional[str] = None
    key_column: Optional[str] = None
    data_type: Optional[str] = None
    cardinality: Optional[str] = None


class SemanticQuery(BaseModel):
    metrics: List[str]
    dimensions: List[str] = []
    filters: List[dict] = []
    order_by: List[dict] = []
    limit: int = 1000
    offset: int = 0


# ── Helpers ──────────────────────────────────────────────────────────────────


def _slug_from_name(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


# ── Metrics CRUD ─────────────────────────────────────────────────────────────


@router.get("/metrics")
async def list_metrics(
    category: Optional[str] = Query(None, description="Filter by metric category"),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    repo = SemanticMetricRepository(db)
    filters = {}
    if category:
        filters["category"] = category
    results = await repo.list(str(current_user.tenant_id), **filters)
    return {
        "status": "success",
        "data": {"metrics": results, "total": len(results)},
        "meta": {"request_id": str(uuid4())},
    }


@router.post("/metrics")
async def create_metric(
    metric: SemanticMetricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    repo = SemanticMetricRepository(db)
    slug = metric.slug or _slug_from_name(metric.name)
    existing = await repo.get_by_slug(str(current_user.tenant_id), slug)
    if existing:
        raise HTTPException(status_code=409, detail=f"Metric with slug '{slug}' already exists")
    created = await repo.create(
        tenant_id=str(current_user.tenant_id),
        name=metric.name,
        slug=slug,
        expression=metric.expression,
        description=metric.description,
        data_type=metric.data_type,
        category=metric.category,
    )
    return {
        "status": "success",
        "data": created,
        "meta": {"request_id": str(uuid4())},
    }


@router.get("/metrics/{metric_id}")
async def get_metric(
    metric_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    repo = SemanticMetricRepository(db)
    metric = await repo.get(metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return {
        "status": "success",
        "data": metric,
        "meta": {"request_id": str(uuid4())},
    }


@router.put("/metrics/{metric_id}")
async def update_metric(
    metric_id: UUID,
    payload: SemanticMetricUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    repo = SemanticMetricRepository(db)
    existing = await repo.get(metric_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Metric not found")
    updates = payload.dict(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "slug" in updates and updates["slug"] != existing.get("slug"):
        conflict = await repo.get_by_slug(str(current_user.tenant_id), updates["slug"])
        if conflict and str(conflict["id"]) != str(metric_id):
            raise HTTPException(status_code=409, detail=f"Metric with slug '{updates['slug']}' already exists")
    updated = await repo.update(metric_id, **updates)
    return {
        "status": "success",
        "data": updated,
        "meta": {"request_id": str(uuid4())},
    }


@router.delete("/metrics/{metric_id}")
async def delete_metric(
    metric_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    repo = SemanticMetricRepository(db)
    deleted = await repo.delete(metric_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Metric not found")
    return {
        "status": "success",
        "data": {"id": str(metric_id), "deleted": True},
        "meta": {"request_id": str(uuid4())},
    }


# ── Dimensions CRUD ──────────────────────────────────────────────────────────


@router.get("/dimensions")
async def list_dimensions(
    min_cardinality: Optional[int] = Query(None, description="Minimum cardinality"),
    max_cardinality: Optional[int] = Query(None, description="Maximum cardinality"),
    search: Optional[str] = Query(None, description="Search dimension name"),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    repo = SemanticDimensionRepository(db)
    results = await repo.list(str(current_user.tenant_id))
    if min_cardinality is not None:
        results = [d for d in results if d.get("cardinality") and int(d["cardinality"]) >= min_cardinality]
    if max_cardinality is not None:
        results = [d for d in results if d.get("cardinality") and int(d["cardinality"]) <= max_cardinality]
    if search:
        results = [d for d in results if search.lower() in (d.get("name") or "").lower()]
    return {
        "status": "success",
        "data": {"dimensions": results, "total": len(results)},
        "meta": {"request_id": str(uuid4())},
    }


@router.post("/dimensions")
async def create_dimension(
    dimension: DimensionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    repo = SemanticDimensionRepository(db)
    slug = dimension.slug or _slug_from_name(dimension.name)
    existing = await repo.get_by_slug(str(current_user.tenant_id), slug)
    if existing:
        raise HTTPException(status_code=409, detail=f"Dimension with slug '{slug}' already exists")
    created = await repo.create(
        tenant_id=str(current_user.tenant_id),
        name=dimension.name,
        slug=slug,
        description=dimension.description,
        physical_name=dimension.physical_name,
        key_column=dimension.key_column,
        data_type=dimension.data_type,
        cardinality=dimension.cardinality,
    )
    return {
        "status": "success",
        "data": created,
        "meta": {"request_id": str(uuid4())},
    }


@router.get("/dimensions/{dim_id}")
async def get_dimension(
    dim_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    repo = SemanticDimensionRepository(db)
    dim = await repo.get(dim_id)
    if not dim:
        raise HTTPException(status_code=404, detail="Dimension not found")
    return {
        "status": "success",
        "data": dim,
        "meta": {"request_id": str(uuid4())},
    }


@router.put("/dimensions/{dim_id}")
async def update_dimension(
    dim_id: UUID,
    payload: DimensionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    repo = SemanticDimensionRepository(db)
    existing = await repo.get(dim_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Dimension not found")
    updates = payload.dict(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "slug" in updates and updates["slug"] != existing.get("slug"):
        conflict = await repo.get_by_slug(str(current_user.tenant_id), updates["slug"])
        if conflict and str(conflict["id"]) != str(dim_id):
            raise HTTPException(status_code=409, detail=f"Dimension with slug '{updates['slug']}' already exists")
    updated = await repo.update(dim_id, **updates)
    return {
        "status": "success",
        "data": updated,
        "meta": {"request_id": str(uuid4())},
    }


@router.delete("/dimensions/{dim_id}")
async def delete_dimension(
    dim_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    repo = SemanticDimensionRepository(db)
    deleted = await repo.delete(dim_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dimension not found")
    return {
        "status": "success",
        "data": {"id": str(dim_id), "deleted": True},
        "meta": {"request_id": str(uuid4())},
    }


# ── Query Engine — Real Implementation ──────────────────────────────────────

@router.post("/query")
async def execute_semantic_query(
    query: SemanticQuery,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    from app.core.data_fabric.query_engine import QueryEngine
    
    engine = QueryEngine(db, UUID(str(current_user.tenant_id)))
    result = await engine.query(
        metrics=query.metrics,
        dimensions=query.dimensions,
        filters={f.get("field"): f.get("value") for f in query.filters} if query.filters else {},
        date_range=None,
        limit=query.limit,
    )
    return {
        "status": "success",
        "data": result,
        "meta": {"request_id": str(uuid4())},
    }


# ── Reports — Real DB via NLQueryLogRepository ──────────────────────────────


@router.get("/reports/saved")
async def list_saved_reports(
    folder: Optional[str] = Query(None, description="Filter by folder"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    from app.infrastructure.persistence.repositories import NLQueryLogRepository
    repo = NLQueryLogRepository(db)
    reports = await repo.list(str(current_user.tenant_id))
    return {
        "status": "success",
        "data": {"reports": reports, "total": len(reports)},
        "meta": {"request_id": str(uuid4())},
    }


@router.post("/reports/saved")
async def save_report(
    report: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    from app.infrastructure.persistence.repositories import NLQueryLogRepository
    repo = NLQueryLogRepository(db)
    created = await repo.create(
        tenant_id=str(current_user.tenant_id),
        query_text=report.get("query", ""),
        result_summary=report.get("name", "Untitled Report"),
    )
    return {
        "status": "success",
        "data": created,
        "meta": {"request_id": str(uuid4())},
    }


# ── Templates (static healthcare analytics presets) ──────────────────────────


@router.get("/templates")
async def list_query_templates(
    category: Optional[str] = Query(None, description="Filter by template category"),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    templates = [
        {
            "id": "tpl_revenue_by_payer",
            "name": "Revenue by Payer Pivot",
            "description": "Pivot table of revenue by payer and month",
            "category": "revenue",
            "metrics": ["net_patient_revenue"],
            "dimensions": ["payer", "date"],
            "visualization_type": "pivot_table",
        },
        {
            "id": "tpl_denial_waterfall",
            "name": "Denial Waterfall",
            "description": "Waterfall chart showing denial reasons",
            "category": "denials",
            "metrics": ["denial_count", "denial_amount"],
            "dimensions": ["denial_reason"],
            "visualization_type": "waterfall",
        },
        {
            "id": "tpl_ar_aging",
            "name": "AR Aging Summary",
            "description": "Accounts receivable aging buckets",
            "category": "collections",
            "metrics": ["ar_balance", "days_in_ar"],
            "dimensions": ["payer", "aging_bucket"],
            "visualization_type": "stacked_bar",
        },
        {
            "id": "tpl_cost_per_case",
            "name": "Cost Per Case by Service Line",
            "description": "Case cost comparison across service lines",
            "category": "cost",
            "metrics": ["cost_per_case"],
            "dimensions": ["service_line"],
            "visualization_type": "horizontal_bar",
        },
        {
            "id": "tpl_cmi_trend",
            "name": "Case Mix Index Trend",
            "description": "Monthly CMI trend across facilities",
            "category": "productivity",
            "metrics": ["case_mix_index"],
            "dimensions": ["facility", "month"],
            "visualization_type": "line_chart",
        },
    ]
    if category:
        templates = [t for t in templates if t["category"] == category]
    return {
        "status": "success",
        "data": {"templates": templates, "total": len(templates)},
        "meta": {"request_id": str(uuid4())},
    }


# ── Health ───────────────────────────────────────────────────────────────────


@router.get("/health")
async def analytics_health(
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin),
):
    return {
        "status": "success",
        "data": {
            "status": "healthy",
            "timestamp": _now_iso(),
            "components": {
                "database": "connected",
                "semantic_layer": "operational",
                "query_engine": "pending",
            },
        },
        "meta": {"request_id": str(uuid4())},
    }
