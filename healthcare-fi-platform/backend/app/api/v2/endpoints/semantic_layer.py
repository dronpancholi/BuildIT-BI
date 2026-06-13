"""
Semantic Layer API endpoints.
Wired to SemanticLayerService for SCD2 dimensions, fact tables, hierarchies, relationships.
"""
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.dev_auth import DevUser, dep_dev_admin
from app.domain.semantic_layer import SemanticLayerService, Cardinality

router = APIRouter()

_service = SemanticLayerService()


class DimensionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    physical_name: str = Field(..., min_length=1, max_length=200)
    key_column: str = Field(..., min_length=1, max_length=200)
    name_column: Optional[str] = None
    description_column: Optional[str] = None
    cardinality: str = Field("medium", pattern="^(high|medium|low)$")
    scd_type: str = Field("SCD1")
    valid_from_column: Optional[str] = None
    valid_to_column: Optional[str] = None
    surrogate_key_column: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
    tags: List[str] = Field(default_factory=list)


class FactTableCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    physical_name: str = Field(..., min_length=1, max_length=200)
    grain: str = Field("transaction", max_length=100)
    grain_columns: List[str] = Field(default_factory=list)
    description: Optional[str] = Field(None, max_length=2000)
    partition_column: Optional[str] = None
    partition_type: Optional[str] = None
    cluster_columns: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class RelationshipCreate(BaseModel):
    source_table: str = Field(..., min_length=1)
    target_table: str = Field(..., min_length=1)
    join_type: str = Field("INNER", pattern="^(INNER|LEFT|RIGHT|FULL|CROSS)$")
    join_condition: str = Field(..., min_length=1)
    source_cardinality: Optional[str] = None
    target_cardinality: Optional[str] = None
    is_one_to_one: bool = False
    is_optional: bool = False


class HierarchyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    dimension_id: str
    levels: List[dict] = Field(default_factory=list)


class AliasCreate(BaseModel):
    canonical_name: str = Field(..., min_length=1)
    alias: str = Field(..., min_length=1)
    entity_type: str = Field("dimension")
    entity_id: str


class SCD2RecordCreate(BaseModel):
    dimension_slug: str = Field(..., min_length=1)
    natural_key: str = Field(..., min_length=1)
    attributes: dict = Field(default_factory=dict)
    valid_from: str = Field(..., description="ISO datetime string")


def _dim_to_dict(d) -> dict:
    return {
        "id": str(d.id),
        "name": d.name,
        "slug": d.slug,
        "physical_name": d.physical_name,
        "key_column": d.key_column,
        "name_column": d.name_column,
        "description_column": d.description_column,
        "cardinality": d.cardinality.value if hasattr(d.cardinality, 'value') else d.cardinality,
        "scd_type": d.scd_type.value if hasattr(d.scd_type, 'value') else d.scd_type,
        "is_sensitive": d.is_sensitive,
        "tags": d.tags,
    }


def _fact_to_dict(f) -> dict:
    return {
        "id": str(f.id),
        "name": f.name,
        "slug": f.slug,
        "physical_name": f.physical_name,
        "grain": f.grain,
        "grain_columns": f.grain_columns,
        "partition_column": f.partition_column,
        "cluster_columns": f.cluster_columns,
        "tags": f.tags,
    }


def _rel_to_dict(r) -> dict:
    return {
        "id": str(r.id),
        "source_table": r.source_table,
        "target_table": r.target_table,
        "join_type": r.join_type.value if hasattr(r.join_type, 'value') else r.join_type,
        "join_condition": r.join_condition,
        "source_cardinality": r.source_cardinality,
        "target_cardinality": r.target_cardinality,
        "is_one_to_one": r.is_one_to_one,
        "is_optional": r.is_optional,
    }


def _hier_to_dict(h) -> dict:
    return {
        "id": str(h.id),
        "name": h.name,
        "dimension_id": str(h.dimension_id),
        "levels": [
            {"name": l.name, "key_column": l.key_column, "name_column": l.name_column}
            for l in h.levels
        ] if h.levels else [],
    }


@router.get("/dimensions")
async def list_dimensions(
    cardinality: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: DevUser = Depends(dep_dev_admin),
):
    card_enum = Cardinality(cardinality) if cardinality else None
    dims = _service.list_dimensions(cardinality=card_enum)
    total = len(dims)
    page = dims[skip:skip + limit]
    return {"dimensions": [_dim_to_dict(d) for d in page], "total": total, "skip": skip, "limit": limit}


@router.post("/dimensions")
async def create_dimension(req: DimensionCreate, _user: DevUser = Depends(dep_dev_admin)):
    card_enum = Cardinality(req.cardinality) if req.cardinality else Cardinality.MEDIUM
    d = _service.create_dimension(
        name=req.name, physical_name=req.physical_name, key_column=req.key_column,
        name_column=req.name_column, description_column=req.description_column,
        cardinality=card_enum, tags=req.tags,
    )
    return _dim_to_dict(d)


@router.get("/dimensions/{dimension_id}")
async def get_dimension(dimension_id: str, _user: DevUser = Depends(dep_dev_admin)):
    try:
        did = UUID(dimension_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dimension ID")
    d = _service.get_dimension(did)
    if not d:
        raise HTTPException(status_code=404, detail="Dimension not found")
    return _dim_to_dict(d)


@router.get("/dimensions/{dimension_id}/history")
async def get_dimension_history(dimension_id: str, _user: DevUser = Depends(dep_dev_admin)):
    try:
        did = UUID(dimension_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dimension ID")
    d = _service.get_dimension(did)
    if not d:
        raise HTTPException(status_code=404, detail="Dimension not found")
    records = _service.scd2_records.get(d.slug, [])
    return {
        "dimension_id": dimension_id,
        "records": [
            {
                "surrogate_key": str(r.surrogate_key),
                "natural_key": r.natural_key,
                "attributes": r.attributes,
                "valid_from": str(r.valid_from),
                "valid_to": str(r.valid_to) if r.valid_to else None,
                "version": r.version,
                "is_current": r.is_current,
            }
            for r in records
        ],
        "total": len(records),
    }


@router.post("/dimensions/scd2")
async def add_scd2_record(req: SCD2RecordCreate, _user: DevUser = Depends(dep_dev_admin)):
    try:
        valid_from = datetime.fromisoformat(req.valid_from)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid valid_from datetime format")
    try:
        record = _service.add_scd2_record(
            dimension_slug=req.dimension_slug, natural_key=req.natural_key,
            attributes=req.attributes, valid_from=valid_from,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "surrogate_key": str(record.surrogate_key),
        "natural_key": record.natural_key,
        "attributes": record.attributes,
        "valid_from": str(record.valid_from),
        "version": record.version,
        "is_current": record.is_current,
    }


@router.get("/dimensions/scd2/{dimension_slug}/{natural_key}")
async def get_scd2_current(dimension_slug: str, natural_key: str, _user: DevUser = Depends(dep_dev_admin)):
    record = _service.get_current_scd2(dimension_slug, natural_key)
    if not record:
        raise HTTPException(status_code=404, detail="No current SCD2 record found")
    return {
        "surrogate_key": str(record.surrogate_key),
        "natural_key": record.natural_key,
        "attributes": record.attributes,
        "valid_from": str(record.valid_from),
        "valid_to": str(record.valid_to) if record.valid_to else None,
        "version": record.version,
    }


@router.get("/fact-tables")
async def list_fact_tables(_user: DevUser = Depends(dep_dev_admin)):
    facts = _service.list_fact_tables()
    return {"fact_tables": [_fact_to_dict(f) for f in facts], "total": len(facts)}


@router.post("/fact-tables")
async def create_fact_table(req: FactTableCreate, _user: DevUser = Depends(dep_dev_admin)):
    f = _service.create_fact_table(
        name=req.name, physical_name=req.physical_name, grain=req.grain,
        grain_columns=req.grain_columns, description=req.description,
        partition_column=req.partition_column, cluster_columns=req.cluster_columns, tags=req.tags,
    )
    return _fact_to_dict(f)


@router.get("/relationships")
async def list_relationships(
    source: Optional[str] = Query(None),
    target: Optional[str] = Query(None),
    _user: DevUser = Depends(dep_dev_admin),
):
    rels = _service.relationships
    if source:
        rels = [r for r in rels if r.source_table == source]
    if target:
        rels = [r for r in rels if r.target_table == target]
    return {"relationships": [_rel_to_dict(r) for r in rels], "total": len(rels)}


@router.post("/relationships")
async def create_relationship(req: RelationshipCreate, _user: DevUser = Depends(dep_dev_admin)):
    r = _service.add_relationship(
        source_table=req.source_table, target_table=req.target_table,
        join_type=req.join_type, join_condition=req.join_condition,
        source_cardinality=req.source_cardinality, target_cardinality=req.target_cardinality,
        is_one_to_one=req.is_one_to_one, is_optional=req.is_optional,
    )
    return _rel_to_dict(r)


@router.get("/hierarchies")
async def list_hierarchies(_user: DevUser = Depends(dep_dev_admin)):
    return {"hierarchies": [_hier_to_dict(h) for h in _service.hierarchies.values()], "total": len(_service.hierarchies)}


@router.post("/hierarchies")
async def create_hierarchy(req: HierarchyCreate, _user: DevUser = Depends(dep_dev_admin)):
    try:
        dim_id = UUID(req.dimension_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dimension ID")
    h = _service.add_hierarchy(dimension_id=dim_id, name=req.name, levels=req.levels)
    return _hier_to_dict(h)


@router.get("/aliases")
async def list_aliases(_user: DevUser = Depends(dep_dev_admin)):
    aliases = [
        {"canonical_name": a.canonical_name, "alias": a.alias, "entity_type": a.entity_type}
        for a in _service.aliases.values()
    ]
    return {"aliases": aliases, "total": len(aliases)}


@router.post("/aliases")
async def create_alias(req: AliasCreate, _user: DevUser = Depends(dep_dev_admin)):
    try:
        eid = UUID(req.entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity ID")
    a = _service.add_alias(canonical_name=req.canonical_name, alias=req.alias, entity_type=req.entity_type, entity_id=eid)
    return {"canonical_name": a.canonical_name, "alias": a.alias, "entity_type": a.entity_type}


@router.get("/resolve/{name}")
async def resolve_alias(name: str, _user: DevUser = Depends(dep_dev_admin)):
    resolved = _service.resolve_alias(name)
    return {"input": name, "resolved": resolved, "was_alias": resolved != name}
