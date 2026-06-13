"""
BuildIT Formula Language (BFL) API endpoints.
Parse, validate, execute, and publish formulas.
"""
from uuid import uuid4
from typing import Optional, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.dev_auth import DevUser, dep_dev_admin

router = APIRouter()


class FormulaParseRequest(BaseModel):
    expression: str = Field(..., min_length=1, max_length=5000)
    dialect: str = Field("postgresql", pattern="^(postgresql|snowflake|bigquery)$")


class FormulaValidateRequest(BaseModel):
    expression: str = Field(..., min_length=1, max_length=5000)
    metrics: List[str] = Field(default_factory=list)
    dimensions: List[str] = Field(default_factory=list)


class FormulaPublishRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    expression: str = Field(..., min_length=1, max_length=5000)
    description: Optional[str] = Field(None, max_length=2000)
    category: str = Field("custom", max_length=100)
    tags: List[str] = Field(default_factory=list)


_published_formulas: dict = {}


@router.post("/parse")
async def parse_formula(req: FormulaParseRequest, _user: DevUser = Depends(dep_dev_admin)):
    try:
        from app.domain.bfl import parse_formula as _parse
        ast = _parse(req.expression)
        child_count = len(ast.children) if ast.children else 0
        return {
            "valid": True,
            "formula_id": str(uuid4()),
            "ast_summary": ast.node_type.value if hasattr(ast.node_type, 'value') else str(ast.node_type),
            "expression": req.expression,
            "node_count": child_count,
        }
    except SyntaxError as e:
        raise HTTPException(status_code=422, detail={"valid": False, "errors": [str(e)]})
    except Exception as e:
        raise HTTPException(status_code=422, detail={"valid": False, "errors": [str(e)]})


@router.post("/validate")
async def validate_formula(req: FormulaValidateRequest, _user: DevUser = Depends(dep_dev_admin)):
    try:
        from app.domain.bfl import parse_formula as _parse, FormulaSemanticAnalyzer
        ast = _parse(req.expression)
        analyzer = FormulaSemanticAnalyzer()
        errors = analyzer.analyze(ast, set(req.metrics + req.dimensions))
        if errors:
            return {"valid": False, "errors": [str(e) for e in errors]}
        return {"valid": True, "expression": req.expression, "errors": []}
    except (SyntaxError, Exception) as e:
        return {"valid": False, "errors": [str(e)]}


@router.post("/generate-sql")
async def generate_sql(
    expression: str = Body(..., embed=True),
    dialect: str = Body("postgresql", embed=True),
    _user: DevUser = Depends(dep_dev_admin),
):
    try:
        from app.domain.bfl import compile_formula
        ast, errors, sql = compile_formula(expression, dialect=dialect)
        if errors:
            return {"sql": "", "dialect": dialect, "valid": False, "errors": [str(e) for e in errors]}
        return {"sql": sql, "dialect": dialect, "valid": True, "ast_type": type(ast).__name__ if ast else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"sql": "", "dialect": dialect, "valid": False, "errors": [str(e)]})


@router.get("/functions")
async def list_functions(
    category: Optional[str] = Query(None),
    _user: DevUser = Depends(dep_dev_admin),
):
    from app.domain.bfl import FunctionRegistry
    all_funcs = FunctionRegistry.FUNCTIONS
    funcs = []
    for name, spec in all_funcs.items():
        funcs.append({
            "name": name,
            "arg_count": spec.get("args", 0),
            "return_type": spec.get("returns", "numeric"),
        })
    if category:
        funcs = [f for f in funcs if f.get("category") == category]
    return {"functions": funcs, "total": len(funcs)}


@router.post("/publish")
async def publish_formula(req: FormulaPublishRequest, _user: DevUser = Depends(dep_dev_admin)):
    try:
        from app.domain.bfl import parse_formula as _parse
        _parse(req.expression)
    except (SyntaxError, Exception) as e:
        raise HTTPException(status_code=422, detail={"error": f"Invalid formula: {e}"})

    fid = str(uuid4())
    _published_formulas[fid] = {
        "id": fid,
        "name": req.name,
        "expression": req.expression,
        "description": req.description,
        "category": req.category,
        "tags": req.tags,
        "version": 1,
        "created_by": str(_user.id),
    }
    return {"formula_id": fid, "version": 1, "status": "published"}


@router.get("/published")
async def list_published(
    category: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: DevUser = Depends(dep_dev_admin),
):
    formulas = list(_published_formulas.values())
    if category:
        formulas = [f for f in formulas if f.get("category") == category]
    total = len(formulas)
    page = formulas[skip:skip + limit]
    return {"formulas": page, "total": total, "skip": skip, "limit": limit}


@router.get("/published/{formula_id}")
async def get_published(formula_id: str, _user: DevUser = Depends(dep_dev_admin)):
    f = _published_formulas.get(formula_id)
    if not f:
        raise HTTPException(status_code=404, detail="Formula not found")
    return f


@router.delete("/published/{formula_id}")
async def delete_published(formula_id: str, _user: DevUser = Depends(dep_dev_admin)):
    if formula_id not in _published_formulas:
        raise HTTPException(status_code=404, detail="Formula not found")
    del _published_formulas[formula_id]
    return {"deleted": True}
