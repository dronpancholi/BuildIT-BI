"""
Strategic Planning API endpoints.
Scenarios, driver trees, Monte Carlo, what-if, sensitivity, and risk assessment.
"""
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import dep_tenant_id
from app.core.dev_auth import DevUser, dep_dev_user
from app.db.session import get_db
from app.domain.strategic_planning import (
    StrategicPlanningService,
    Scenario,
    ScenarioComparison,
    DriverTree,
    MonteCarloResult,
    WhatIfAnalysis,
    SensitivityResult,
    RiskAssessment,
    ScenarioStatus,
    ScenarioType,
)
from app.infrastructure.persistence.repositories import (
    StrategicScenarioRepository,
    StrategicDriverTreeRepository,
    StrategicWhatIfRepository,
)

router = APIRouter(tags=["Strategic Planning"])

__all__ = ["router"]


class ScenarioCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=2000)
    type: str = Field("base", pattern="^(base|best_case|worst_case|stress_test|custom)$")
    assumptions: List[Dict] = Field(default_factory=list)
    created_by: str = Field(..., min_length=1)


class ScenarioRunRequest(BaseModel):
    data: Dict = Field(default_factory=dict)


class ScenarioCompareRequest(BaseModel):
    scenario_ids: List[str] = Field(..., min_length=2)
    metrics: List[str] = Field(..., min_length=1)


class DriverTreeCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=2000)
    metrics: List[Dict] = Field(..., min_length=1)


class DriverTreeCalculateRequest(BaseModel):
    actual_data: Dict = Field(default_factory=dict)


class MonteCarloRequest(BaseModel):
    scenario_id: str
    variable_distributions: Dict = Field(default_factory=dict)
    simulations: int = Field(1000, ge=100, le=100000)


class WhatIfCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    base_values: Dict = Field(default_factory=dict)
    changes: List[Dict] = Field(default_factory=list)


class WhatIfRunRequest(BaseModel):
    data: Dict = Field(default_factory=dict)


class SensitivityRequest(BaseModel):
    scenario_id: str
    base_values: Dict = Field(default_factory=dict)
    variable_ranges: Dict = Field(default_factory=dict)


class RiskAssessmentRequest(BaseModel):
    scenario_id: str
    data: Dict = Field(default_factory=dict)


def _serialize(obj):
    if hasattr(obj, "__dict__"):
        result = {}
        for key, value in obj.__dict__.items():
            if key.startswith("_"):
                continue
            result[key] = _serialize(value)
        return result
    if isinstance(obj, (list, tuple)):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return obj


def _serialize_scenario(scenario: Scenario) -> Dict:
    return {
        "id": str(scenario.id),
        "tenant_id": scenario.tenant_id,
        "name": scenario.name,
        "description": scenario.description,
        "type": scenario.type.value,
        "status": scenario.status.value,
        "assumptions": scenario.assumptions,
        "results": _serialize(scenario.results),
        "created_by": str(scenario.created_by),
        "created_at": scenario.created_at.isoformat(),
        "updated_at": scenario.updated_at.isoformat(),
    }


def _serialize_scenario_dict(data: Dict) -> Dict:
    return {
        "id": str(data["id"]),
        "tenant_id": data["tenant_id"],
        "name": data["name"],
        "description": data.get("description", ""),
        "type": data["type"],
        "status": data["status"],
        "assumptions": data.get("assumptions") or [],
        "results": _serialize(data.get("results") or {}),
        "created_by": str(data.get("created_by", "")),
        "created_at": data["created_at"].isoformat() if hasattr(data.get("created_at"), "isoformat") else str(data.get("created_at", "")),
        "updated_at": data["updated_at"].isoformat() if hasattr(data.get("updated_at"), "isoformat") else str(data.get("updated_at", "")),
    }


def _serialize_comparison(comparison: ScenarioComparison) -> Dict:
    return {
        "id": str(comparison.id),
        "scenario_ids": [str(sid) for sid in comparison.scenario_ids],
        "metrics": comparison.metrics,
        "summary": _serialize(comparison.summary),
        "detailed": _serialize(comparison.detailed),
        "created_at": comparison.created_at.isoformat(),
    }


def _serialize_tree(tree: DriverTree) -> Dict:
    nodes = []
    for node in tree.nodes:
        nodes.append({
            "id": str(node.id),
            "parent_id": str(node.parent_id) if node.parent_id else None,
            "name": node.name,
            "node_type": node.node_type.value,
            "metric_id": str(node.metric_id) if node.metric_id else None,
            "formula": node.formula,
            "weight": float(node.weight),
            "value": float(node.value) if node.value is not None else None,
            "children": [str(cid) for cid in node.children],
            "level": node.level,
        })
    return {
        "id": str(tree.id),
        "tenant_id": tree.tenant_id,
        "name": tree.name,
        "description": tree.description,
        "root_node_id": str(tree.root_node_id),
        "nodes": nodes,
        "status": tree.status,
        "created_at": tree.created_at.isoformat(),
    }


def _serialize_tree_dict(data: Dict) -> Dict:
    return {
        "id": str(data["id"]),
        "tenant_id": data["tenant_id"],
        "name": data["name"],
        "description": data.get("description", ""),
        "root_node_id": str(data["root_node_id"]) if data.get("root_node_id") else None,
        "metrics": data.get("metrics") or [],
        "status": data["status"],
        "created_at": data["created_at"].isoformat() if hasattr(data.get("created_at"), "isoformat") else str(data.get("created_at", "")),
    }


def _serialize_monte_carlo(result: MonteCarloResult) -> Dict:
    percentiles = {k: float(v) for k, v in result.percentiles.items()}
    return {
        "id": str(result.id),
        "scenario_id": str(result.scenario_id),
        "simulations": result.simulations,
        "distribution": result.distribution,
        "mean": float(result.mean),
        "median": float(result.median),
        "std_dev": float(result.std_dev),
        "var_95": float(result.var_95),
        "var_99": float(result.var_99),
        "percentiles": percentiles,
        "histogram": result.histogram,
        "convergence": result.convergence,
        "created_at": result.created_at.isoformat(),
    }


def _serialize_what_if(analysis: WhatIfAnalysis) -> Dict:
    return {
        "id": str(analysis.id),
        "tenant_id": analysis.tenant_id,
        "name": analysis.name,
        "base_values": analysis.base_values,
        "changes": analysis.changes,
        "results": _serialize(analysis.results),
        "impact_summary": _serialize(analysis.impact_summary),
        "sensitivity": _serialize(analysis.sensitivity),
        "created_at": analysis.created_at.isoformat(),
    }


def _serialize_what_if_dict(data: Dict) -> Dict:
    return {
        "id": str(data["id"]),
        "tenant_id": data["tenant_id"],
        "name": data["name"],
        "base_values": data.get("base_values") or {},
        "changes": data.get("changes") or [],
        "results": _serialize(data.get("results") or {}),
        "impact_summary": _serialize(data.get("impact_summary") or {}),
        "sensitivity": _serialize(data.get("sensitivity") or {}),
        "created_at": data["created_at"].isoformat() if hasattr(data.get("created_at"), "isoformat") else str(data.get("created_at", "")),
    }


def _serialize_sensitivity(results: List[SensitivityResult]) -> List[Dict]:
    return [
        {
            "variable": r.variable,
            "elasticity": r.elasticity,
            "rank": r.rank,
            "range": [float(r.range[0]), float(r.range[1])],
        }
        for r in results
    ]


def _serialize_risk(assessment: RiskAssessment) -> Dict:
    return {
        "id": str(assessment.id),
        "scenario_id": str(assessment.scenario_id),
        "risks": assessment.risks,
        "overall_score": assessment.overall_score,
        "created_at": assessment.created_at.isoformat(),
    }


async def _load_scenario_to_service(
    service: StrategicPlanningService,
    repo: StrategicScenarioRepository,
    tenant_id: str,
    scenario_id: UUID,
) -> None:
    data = await repo.get(scenario_id)
    if data is None:
        raise ValueError(f"Scenario {scenario_id} not found")

    scenario = Scenario(
        id=UUID(str(data["id"])),
        tenant_id=str(data["tenant_id"]),
        name=data["name"],
        description=data.get("description", ""),
        type=ScenarioType(data["type"]),
        status=ScenarioStatus(data["status"]),
        assumptions=data.get("assumptions") or [],
        results=data.get("results") or {},
        created_by=UUID(str(data["created_by"])) if data.get("created_by") else uuid4(),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )

    if tenant_id not in service._scenarios:
        service._scenarios[tenant_id] = {}
    service._scenarios[tenant_id][str(scenario_id)] = scenario


@router.post("/scenarios")
async def create_scenario(
    req: ScenarioCreateRequest,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        scenario_type = ScenarioType(req.type)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid scenario type: {req.type}")

    repo = StrategicScenarioRepository(db)
    scenario = await repo.create(
        tenant_id=str(tenant_id),
        name=req.name,
        description=req.description,
        type=scenario_type.value,
        status="draft",
        assumptions=req.assumptions,
        created_by=req.created_by,
    )
    return {"data": _serialize_scenario_dict(dict(scenario)), "meta": {"total": 1}}


@router.get("/scenarios/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        sid = UUID(scenario_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid scenario ID")

    repo = StrategicScenarioRepository(db)
    scenario = await repo.get(sid)
    if scenario is None or str(scenario["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"data": _serialize_scenario_dict(dict(scenario)), "meta": {"total": 1}}


@router.get("/scenarios")
async def list_scenarios(
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = StrategicScenarioRepository(db)
    rows = await repo.list(str(tenant_id))
    items = [_serialize_scenario_dict(dict(r)) for r in rows]
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/scenarios/{scenario_id}/run")
async def run_scenario(
    scenario_id: str,
    req: ScenarioRunRequest,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        sid = UUID(scenario_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid scenario ID")

    repo = StrategicScenarioRepository(db)
    existing = await repo.get(sid)
    if existing is None or str(existing["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Scenario not found")

    service = StrategicPlanningService()
    await _load_scenario_to_service(service, repo, str(tenant_id), sid)

    try:
        result = service.run_scenario(str(tenant_id), sid, req.data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    await repo.update(sid, results=result.results, status=result.status.value)
    return {"data": _serialize_scenario(result), "meta": {"total": 1}}


@router.post("/scenarios/compare")
async def compare_scenarios(
    req: ScenarioCompareRequest,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        scenario_ids = [UUID(sid) for sid in req.scenario_ids]
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid scenario ID(s)")

    repo = StrategicScenarioRepository(db)
    service = StrategicPlanningService()
    for sid in scenario_ids:
        await _load_scenario_to_service(service, repo, str(tenant_id), sid)

    try:
        comparison = service.compare_scenarios(str(tenant_id), scenario_ids, req.metrics)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"data": _serialize_comparison(comparison), "meta": {"total": 1}}


@router.post("/driver-trees")
async def build_driver_tree(
    req: DriverTreeCreateRequest,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = StrategicDriverTreeRepository(db)
    tree = await repo.create(
        tenant_id=str(tenant_id),
        name=req.name,
        description=req.description,
        metrics=req.metrics,
        status="draft",
    )
    return {"data": _serialize_tree_dict(dict(tree)), "meta": {"total": 1}}


@router.get("/driver-trees")
async def list_driver_trees(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """List all driver trees for the tenant."""
    repo = StrategicDriverTreeRepository(db)
    trees = await repo.list(str(tenant_id))

    if status:
        trees = [t for t in trees if t.get("status") == status]

    total = len(trees)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = trees[start:end]

    return {
        "data": [_serialize_tree_dict(t) for t in paginated],
        "meta": {"page": page, "page_size": page_size, "total": total},
    }


@router.put("/driver-trees/{tree_id}/calculate")
async def calculate_driver_values(
    tree_id: str,
    req: DriverTreeCalculateRequest,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        tid = UUID(tree_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid tree ID")

    repo = StrategicDriverTreeRepository(db)
    existing = await repo.get(tid)
    if existing is None or str(existing["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Driver tree not found")

    service = StrategicPlanningService()
    tree_data = dict(existing)
    nodes = tree_data.get("metrics") or []
    tree = DriverTree(
        id=tid,
        tenant_id=str(tenant_id),
        name=tree_data["name"],
        description=tree_data.get("description", ""),
        root_node_id=UUID(str(tree_data["root_node_id"])) if tree_data.get("root_node_id") else uuid4(),
        nodes=[],
        status=tree_data.get("status", "active"),
    )
    if str(tenant_id) not in service._trees:
        service._trees[str(tenant_id)] = {}
    service._trees[str(tenant_id)][str(tid)] = tree

    try:
        result = service.calculate_driver_values(tid, req.actual_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"data": _serialize_tree(result), "meta": {"total": 1}}


@router.post("/monte-carlo")
async def run_monte_carlo(
    req: MonteCarloRequest,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        scenario_id = UUID(req.scenario_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid scenario ID")

    repo = StrategicScenarioRepository(db)
    existing = await repo.get(scenario_id)
    if existing is None or str(existing["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Scenario not found")

    service = StrategicPlanningService()
    await _load_scenario_to_service(service, repo, str(tenant_id), scenario_id)

    try:
        result = service.run_monte_carlo(
            tenant_id=str(tenant_id),
            scenario_id=scenario_id,
            variable_distributions=req.variable_distributions,
            simulations=req.simulations,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"data": _serialize_monte_carlo(result), "meta": {"total": 1}}


@router.post("/what-if")
async def create_what_if(
    req: WhatIfCreateRequest,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    repo = StrategicWhatIfRepository(db)
    analysis = await repo.create(
        tenant_id=str(tenant_id),
        name=req.name,
        base_values=req.base_values,
        changes=req.changes,
    )
    return {"data": _serialize_what_if_dict(dict(analysis)), "meta": {"total": 1}}


@router.post("/what-if/{what_if_id}/run")
async def run_what_if(
    what_if_id: str,
    req: WhatIfRunRequest,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        wid = UUID(what_if_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid what-if ID")

    repo = StrategicWhatIfRepository(db)
    existing = await repo.get(wid)
    if existing is None or str(existing["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="What-if analysis not found")

    service = StrategicPlanningService()
    what_if_data = dict(existing)
    analysis = WhatIfAnalysis(
        id=wid,
        tenant_id=str(tenant_id),
        name=what_if_data["name"],
        base_values=what_if_data.get("base_values") or {},
        changes=what_if_data.get("changes") or [],
        results=what_if_data.get("results") or [],
    )
    if str(tenant_id) not in service._what_ifs:
        service._what_ifs[str(tenant_id)] = {}
    service._what_ifs[str(tenant_id)][str(wid)] = analysis

    try:
        result = service.run_what_if(str(tenant_id), wid, req.data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"data": _serialize_what_if(result), "meta": {"total": 1}}


@router.post("/sensitivity")
async def sensitivity_analysis(
    req: SensitivityRequest,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        scenario_id = UUID(req.scenario_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid scenario ID")

    repo = StrategicScenarioRepository(db)
    existing = await repo.get(scenario_id)
    if existing is None or str(existing["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Scenario not found")

    service = StrategicPlanningService()
    await _load_scenario_to_service(service, repo, str(tenant_id), scenario_id)

    variable_ranges = {
        k: (float(v[0]), float(v[1]))
        for k, v in req.variable_ranges.items()
    }

    try:
        results = service.sensitivity_analysis(
            tenant_id=str(tenant_id),
            scenario_id=scenario_id,
            base_values=req.base_values,
            variable_ranges=variable_ranges,
            n_points=10,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"data": _serialize_sensitivity(results), "meta": {"total": len(results)}}


@router.post("/risks")
async def assess_risks(
    req: RiskAssessmentRequest,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        scenario_id = UUID(req.scenario_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid scenario ID")

    repo = StrategicScenarioRepository(db)
    existing = await repo.get(scenario_id)
    if existing is None or str(existing["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Scenario not found")

    service = StrategicPlanningService()
    await _load_scenario_to_service(service, repo, str(tenant_id), scenario_id)

    try:
        assessment = service.assess_risks(str(tenant_id), scenario_id, req.data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"data": _serialize_risk(assessment), "meta": {"total": 1}}


@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(
    scenario_id: str,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        sid = UUID(scenario_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid scenario ID")

    repo = StrategicScenarioRepository(db)
    existing = await repo.get(sid)
    if existing is None or str(existing["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Scenario not found")
    await repo.delete(sid)
    return {"data": {"deleted": True}, "meta": {"total": 1}}
