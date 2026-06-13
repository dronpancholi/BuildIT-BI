"""
Metric Studio API endpoints.
Wired to MetricStudioService for real lifecycle management with PostgreSQL persistence.
"""
from uuid import UUID, uuid4
from typing import Optional, List
import json
from datetime import datetime, date

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dev_auth import DevUser, dep_dev_admin
from app.core.deps import dep_tenant_id
from app.db.session import get_db
from app.infrastructure.persistence.repositories import SemanticMetricRepository
from app.domain.metric_studio import (
    Metric, MetricVersion, MetricApprovalWorkflow, MetricCategory, MetricStatus,
    ChangeType, ApprovalStep, StepStatus, ApprovalStatus, MetricStudioService,
)

router = APIRouter()
_service = MetricStudioService()

def safe_uuid(val):
    if not val:
        return None
    if isinstance(val, UUID):
        return val
    try:
        return UUID(str(val))
    except ValueError:
        import hashlib
        hex_digest = hashlib.md5(str(val).encode('utf-8')).hexdigest()
        return UUID(hex_digest)

def _metric_to_meta_dict(m: Metric) -> dict:
    return {
        "id": str(m.id),
        "name": m.name,
        "slug": m.slug,
        "category": m.category.value if hasattr(m.category, 'value') else str(m.category),
        "description": m.description,
        "formula_id": str(m.formula_id) if m.formula_id else None,
        "unit": m.unit,
        "tags": m.tags,
        "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
        "version": m.version,
        "is_certified": m.is_certified,
        "certified_by": str(m.certified_by) if m.certified_by else None,
        "certified_at": m.certified_at.isoformat() if m.certified_at else None,
        "certification_expires_at": m.certification_expires_at.isoformat() if m.certification_expires_at else None,
        "review_frequency": m.review_frequency,
        "owner_id": str(m.owner_id) if m.owner_id else None,
        "steward_id": str(m.steward_id) if m.steward_id else None,
        "department_id": str(m.department_id) if m.department_id else None,
        "default_time_range": m.default_time_range,
        "default_filters": m.default_filters,
        "default_dimensions": m.default_dimensions,
        "deprecated_at": m.deprecated_at.isoformat() if m.deprecated_at else None,
    }

def _meta_dict_to_metric(d: dict) -> Metric:
    return Metric(
        id=UUID(d["id"]),
        name=d.get("name", ""),
        slug=d.get("slug", ""),
        category=MetricCategory(d["category"]) if d.get("category") in [c.value for c in MetricCategory] else MetricCategory.FINANCIAL,
        description=d.get("description", ""),
        formula_id=safe_uuid(d.get("formula_id")),
        unit=d.get("unit", ""),
        tags=d.get("tags", []),
        status=MetricStatus(d["status"]) if d.get("status") in [s.value for s in MetricStatus] else MetricStatus.DRAFT,
        version=d.get("version", 1),
        is_certified=d.get("is_certified", False),
        certified_by=safe_uuid(d.get("certified_by")),
        certified_at=datetime.fromisoformat(d["certified_at"]) if d.get("certified_at") else None,
        certification_expires_at=date.fromisoformat(d["certification_expires_at"]) if d.get("certification_expires_at") else None,
        review_frequency=d.get("review_frequency"),
        owner_id=safe_uuid(d.get("owner_id")) or uuid4(),
        steward_id=safe_uuid(d.get("steward_id")),
        department_id=safe_uuid(d.get("department_id")),
        default_time_range=d.get("default_time_range", "current_month"),
        default_filters=d.get("default_filters", []),
        default_dimensions=d.get("default_dimensions", []),
        deprecated_at=datetime.fromisoformat(d["deprecated_at"]) if d.get("deprecated_at") else None,
    )

def _version_to_dict(v: MetricVersion) -> dict:
    return {
        "id": str(v.id),
        "metric_id": str(v.metric_id),
        "version": v.version,
        "snapshot": _metric_to_meta_dict(v.snapshot) if v.snapshot else None,
        "created_by": str(v.created_by),
        "created_at": v.created_at.isoformat(),
        "change_type": v.change_type.value if hasattr(v.change_type, 'value') else str(v.change_type),
        "change_summary": v.change_summary,
        "is_current": v.is_current
    }

def _dict_to_version(d: dict) -> MetricVersion:
    snapshot_dict = d.get("snapshot")
    snapshot = _meta_dict_to_metric(snapshot_dict) if snapshot_dict else None
    return MetricVersion(
        id=UUID(d["id"]),
        metric_id=UUID(d["metric_id"]),
        version=d["version"],
        snapshot=snapshot,
        created_by=UUID(d["created_by"]),
        created_at=datetime.fromisoformat(d["created_at"]),
        change_type=ChangeType(d["change_type"]) if d["change_type"] in [c.value for c in ChangeType] else ChangeType.CREATED,
        change_summary=d.get("change_summary", ""),
        is_current=d.get("is_current", True)
    )

def _metric_to_db_dict(m: Metric, tenant_id: str) -> dict:
    meta = {
        "description": m.description,
        "unit": m.unit,
        "tags": m.tags,
        "version": m.version,
        "is_certified": m.is_certified,
        "certified_by": str(m.certified_by) if m.certified_by else None,
        "certified_at": m.certified_at.isoformat() if m.certified_at else None,
        "certification_expires_at": m.certification_expires_at.isoformat() if m.certification_expires_at else None,
        "review_frequency": m.review_frequency,
        "owner_id": str(m.owner_id) if m.owner_id else None,
        "steward_id": str(m.steward_id) if m.steward_id else None,
        "department_id": str(m.department_id) if m.department_id else None,
        "default_time_range": m.default_time_range,
        "default_filters": m.default_filters,
        "default_dimensions": m.default_dimensions,
        "deprecated_at": m.deprecated_at.isoformat() if m.deprecated_at else None,
        "versions": [_version_to_dict(v) for v in _service.versions.get(m.id, [])],
        "graph_edges": [
            {"source": str(e["source"]), "target": str(e["target"]), "relationship": e.get("relationship", "depends_on")}
            for e in _service.graph.edges
        ]
    }
    
    return {
        "id": m.id,
        "tenant_id": str(tenant_id),
        "name": m.name,
        "slug": m.slug,
        "description": json.dumps(meta),
        "expression": str(m.formula_id) if m.formula_id else "",
        "data_type": "decimal",
        "category": m.category.value if hasattr(m.category, 'value') else str(m.category),
        "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
    }

def _db_dict_to_metric(row: dict) -> Metric:
    m = Metric(
        id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
        name=row["name"],
        slug=row["slug"],
        formula_id=safe_uuid(row["expression"]),
        category=MetricCategory(row["category"]) if row["category"] in [c.value for c in MetricCategory] else MetricCategory.FINANCIAL,
        status=MetricStatus(row["status"]) if row["status"] in [s.value for s in MetricStatus] else MetricStatus.DRAFT,
    )
    
    desc_str = row.get("description") or ""
    if desc_str.startswith("{") and desc_str.endswith("}"):
        try:
            meta = json.loads(desc_str)
            m.description = meta.get("description", "")
            m.unit = meta.get("unit", "")
            m.tags = meta.get("tags", [])
            m.version = meta.get("version", 1)
            m.is_certified = meta.get("is_certified", False)
            m.certified_by = safe_uuid(meta.get("certified_by"))
            m.certified_at = datetime.fromisoformat(meta["certified_at"]) if meta.get("certified_at") else None
            m.certification_expires_at = date.fromisoformat(meta["certification_expires_at"]) if meta.get("certification_expires_at") else None
            m.review_frequency = meta.get("review_frequency")
            m.owner_id = safe_uuid(meta.get("owner_id")) or m.owner_id
            m.steward_id = safe_uuid(meta.get("steward_id"))
            m.department_id = safe_uuid(meta.get("department_id"))
            m.default_time_range = meta.get("default_time_range", "current_month")
            m.default_filters = meta.get("default_filters", [])
            m.default_dimensions = meta.get("default_dimensions", [])
            m.deprecated_at = datetime.fromisoformat(meta["deprecated_at"]) if meta.get("deprecated_at") else None
            
            versions_list = meta.get("versions", [])
            _service.versions[m.id] = [_dict_to_version(v) for v in versions_list]
        except Exception:
            m.description = desc_str
    else:
        m.description = desc_str
        
    return m

async def _sync_from_db(db: AsyncSession, tenant_id: str):
    repo = SemanticMetricRepository(db)
    db_metrics = await repo.list(tenant_id=str(tenant_id))
    
    _service.metrics = {}
    _service.versions = {}
    _service.graph.nodes = []
    _service.graph.edges = []
    
    all_edges = []
    
    for row in db_metrics:
        m = _db_dict_to_metric(row)
        _service.metrics[m.id] = m
        _service.graph.add_node(m.id, m.name, m.formula_id)
        
        desc_str = row.get("description") or ""
        if desc_str.startswith("{") and desc_str.endswith("}"):
            try:
                meta = json.loads(desc_str)
                edges = meta.get("graph_edges", [])
                for e in edges:
                    all_edges.append(e)
            except Exception:
                pass

    seen_edges = set()
    for e in all_edges:
        source = UUID(e["source"])
        target = UUID(e["target"])
        rel = e.get("relationship", "depends_on")
        edge_key = (source, target, rel)
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            _service.graph.add_edge(source, target, rel)



class MetricCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    formula_id: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: str = Field("FINANCIAL")
    unit: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class MetricUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    formula_id: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = None
    tags: Optional[List[str]] = None


def _metric_to_dict(m) -> dict:
    return {
        "id": str(m.id),
        "name": m.name,
        "slug": m.slug,
        "formula_id": m.formula_id,
        "description": m.description,
        "category": m.category.value if hasattr(m.category, 'value') else m.category,
        "unit": m.unit,
        "tags": m.tags,
        "status": m.status.value if hasattr(m.status, 'value') else m.status,
        "version": m.version,
        "is_certified": m.is_certified,
    }


@router.get("/")
async def list_metrics(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(dep_tenant_id),
    _user: DevUser = Depends(dep_dev_admin),
):
    await _sync_from_db(db, tenant_id)
    cat_enum = MetricCategory(category) if category else None
    stat_enum = MetricStatus(status) if status else None
    metrics = _service.list_metrics(category=cat_enum, status=stat_enum)
    total = len(metrics)
    page = metrics[skip:skip + limit]
    return {"metrics": [_metric_to_dict(m) for m in page], "total": total, "skip": skip, "limit": limit}


@router.post("/")
async def create_metric(
    req: MetricCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(dep_tenant_id),
    _user: DevUser = Depends(dep_dev_admin),
):
    await _sync_from_db(db, tenant_id)
    try:
        cat_enum = MetricCategory(req.category) if req.category else MetricCategory.FINANCIAL
    except ValueError:
        cat_enum = MetricCategory.FINANCIAL
    m = _service.create_metric(
        name=req.name, formula_id=req.formula_id, description=req.description,
        category=cat_enum, unit=req.unit, tags=req.tags,
    )
    repo = SemanticMetricRepository(db)
    db_dict = _metric_to_db_dict(m, tenant_id)
    await repo.create(**db_dict)
    return _metric_to_dict(m)


@router.get("/{metric_id}")
async def get_metric(
    metric_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(dep_tenant_id),
    _user: DevUser = Depends(dep_dev_admin),
):
    await _sync_from_db(db, tenant_id)
    try:
        mid = UUID(metric_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric ID format")
    m = _service.get_metric(mid)
    if not m:
        raise HTTPException(status_code=404, detail="Metric not found")
    return _metric_to_dict(m)


@router.put("/{metric_id}")
async def update_metric(
    metric_id: str,
    req: MetricUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(dep_tenant_id),
    _user: DevUser = Depends(dep_dev_admin),
):
    await _sync_from_db(db, tenant_id)
    try:
        mid = UUID(metric_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric ID format")
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "category" in updates:
        try:
            updates["category"] = MetricCategory(updates["category"])
        except ValueError:
            pass
    try:
        m = _service.update_metric(mid, **updates)
    except KeyError:
        raise HTTPException(status_code=404, detail="Metric not found")
    repo = SemanticMetricRepository(db)
    db_dict = _metric_to_db_dict(m, tenant_id)
    await repo.update(mid, **db_dict)
    return _metric_to_dict(m)


@router.post("/{metric_id}/publish")
async def publish_metric(
    metric_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(dep_tenant_id),
    _user: DevUser = Depends(dep_dev_admin),
):
    await _sync_from_db(db, tenant_id)
    try:
        mid = UUID(metric_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric ID format")
    try:
        m = _service.publish_metric(mid)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    repo = SemanticMetricRepository(db)
    db_dict = _metric_to_db_dict(m, tenant_id)
    await repo.update(mid, **db_dict)
    return _metric_to_dict(m)


@router.post("/{metric_id}/certify")
async def certify_metric(
    metric_id: str,
    certifier_id: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(dep_tenant_id),
    _user: DevUser = Depends(dep_dev_admin),
):
    await _sync_from_db(db, tenant_id)
    try:
        mid = UUID(metric_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric ID format")
    cid = UUID(certifier_id) if certifier_id else _user.id
    try:
        m = _service.certify_metric(mid, certifier_id=cid)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    repo = SemanticMetricRepository(db)
    db_dict = _metric_to_db_dict(m, tenant_id)
    await repo.update(mid, **db_dict)
    return _metric_to_dict(m)


@router.post("/{metric_id}/deprecate")
async def deprecate_metric(
    metric_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(dep_tenant_id),
    _user: DevUser = Depends(dep_dev_admin),
):
    await _sync_from_db(db, tenant_id)
    try:
        mid = UUID(metric_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric ID format")
    try:
        m = _service.deprecate_metric(mid)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    repo = SemanticMetricRepository(db)
    db_dict = _metric_to_db_dict(m, tenant_id)
    await repo.update(mid, **db_dict)
    return _metric_to_dict(m)


@router.get("/{metric_id}/versions")
async def get_versions(
    metric_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(dep_tenant_id),
    _user: DevUser = Depends(dep_dev_admin),
):
    await _sync_from_db(db, tenant_id)
    try:
        mid = UUID(metric_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric ID format")
    m = _service.get_metric(mid)
    if not m:
        raise HTTPException(status_code=404, detail="Metric not found")
    versions = _service.get_version_history(mid)
    return {
        "metric_id": metric_id,
        "versions": [
            {"version": v.version, "formula_id": v.formula_id, "changed_at": str(v.changed_at) if hasattr(v, 'changed_at') else None}
            for v in versions
        ],
        "current_version": m.version,
    }


@router.post("/{metric_id}/rollback")
async def rollback_metric(
    metric_id: str,
    target_version: int = Body(..., embed=True, ge=1),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(dep_tenant_id),
    _user: DevUser = Depends(dep_dev_admin),
):
    await _sync_from_db(db, tenant_id)
    try:
        mid = UUID(metric_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric ID format")
    try:
        m = _service.rollback_metric(mid, target_version)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    repo = SemanticMetricRepository(db)
    db_dict = _metric_to_db_dict(m, tenant_id)
    await repo.update(mid, **db_dict)
    return _metric_to_dict(m)


@router.get("/{metric_id}/dependencies")
async def get_dependencies(
    metric_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(dep_tenant_id),
    _user: DevUser = Depends(dep_dev_admin),
):
    await _sync_from_db(db, tenant_id)
    try:
        mid = UUID(metric_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric ID format")
    m = _service.get_metric(mid)
    if not m:
        raise HTTPException(status_code=404, detail="Metric not found")
    graph = _service.graph
    upstream = graph.get_upstream(mid)
    downstream = graph.get_downstream(mid)
    has_cycle = graph.detect_cycles()
    return {
        "metric_id": metric_id,
        "upstream": [str(uid) for uid in upstream],
        "downstream": [str(did) for did in downstream],
        "has_cycle": len(has_cycle) > 0,
        "cycle_paths": [[str(n) for n in c] for c in has_cycle] if has_cycle else [],
    }


@router.get("/{metric_id}/impact")
async def get_impact(
    metric_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(dep_tenant_id),
    _user: DevUser = Depends(dep_dev_admin),
):
    await _sync_from_db(db, tenant_id)
    try:
        mid = UUID(metric_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric ID format")
    m = _service.get_metric(mid)
    if not m:
        raise HTTPException(status_code=404, detail="Metric not found")
    impact = _service.analyze_impact(mid)
    return {
        "metric_id": metric_id,
        "impact_score": impact.impact_score if hasattr(impact, 'impact_score') else 0,
        "affected_metrics": [str(m) for m in (impact.affected_metrics if hasattr(impact, 'affected_metrics') else [])],
        "affected_dashboards": impact.affected_dashboards if hasattr(impact, 'affected_dashboards') else [],
        "affected_reports": impact.affected_reports if hasattr(impact, 'affected_reports') else [],
    }


@router.delete("/{metric_id}")
async def delete_metric(
    metric_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(dep_tenant_id),
    _user: DevUser = Depends(dep_dev_admin),
):
    await _sync_from_db(db, tenant_id)
    try:
        mid = UUID(metric_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric ID format")
    if mid not in _service.metrics:
        raise HTTPException(status_code=404, detail="Metric not found")
    repo = SemanticMetricRepository(db)
    await repo.delete(mid)
    del _service.metrics[mid]
    return {"deleted": True, "id": metric_id}

