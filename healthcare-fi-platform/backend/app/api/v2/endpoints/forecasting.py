"""
Domain 4: Enterprise Forecasting — API Endpoints.
Model lifecycle, forecast generation, drift detection, champion/challenger evaluation.
"""
from uuid import UUID, uuid4
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dev_auth import DevUser, dep_dev_admin
from app.db.session import get_db
from app.domain.forecasting import (
    ForecastingService,
    ForecastModelConfig,
    ForecastResult,
    MonitoringAlert,
    ChampionChallengerResult,
    ForecastModel,
    ModelStatus,
)
from app.infrastructure.database.repositories.forecasting_repository import (
    ForecastModelRepository,
    ForecastResultRepository,
    ForecastAlertRepository,
)

router = APIRouter(tags=["Forecasting"])

__all__ = ["router"]


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    model_type: str = Field(..., min_length=1, max_length=50)
    parameters: dict = Field(default_factory=dict)
    hyperparameters: dict = Field(default_factory=dict)


class TrainRequest(BaseModel):
    training_data: List[dict]
    target_column: str = Field(..., min_length=1, max_length=200)
    date_column: str = Field(..., min_length=1, max_length=200)


class ForecastRequest(BaseModel):
    metric_id: str = Field(..., min_length=1, max_length=200)
    metric_name: str = Field(..., min_length=1, max_length=200)
    periods: int = Field(..., ge=1, le=1000)
    historical_data: List[dict]
    confidence_level: float = Field(0.95, ge=0.5, le=0.99)


class EvaluateRequest(BaseModel):
    test_data: List[dict]


class CompareRequest(BaseModel):
    model_ids: List[str] = Field(..., min_length=2)
    metric_name: str = Field(..., min_length=1, max_length=200)
    comparison_data: List[dict]


class EnsembleMember(BaseModel):
    model_id: str
    weight: float = Field(1.0, ge=0.0)


class EnsembleRequest(BaseModel):
    models: List[EnsembleMember] = Field(..., min_length=1)
    metric_name: str = Field(..., min_length=1, max_length=200)


class DriftRequest(BaseModel):
    recent_data: List[dict]
    reference_data: List[dict]


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _model_to_dict(m) -> dict:
    if isinstance(m, ForecastModelConfig):
        return {
            "id": str(m.id),
            "name": m.name,
            "model_type": m.model_type.value if hasattr(m.model_type, "value") else str(m.model_type),
            "parameters": m.parameters,
            "hyperparameters": m.hyperparameters,
            "status": m.status.value if hasattr(m.status, "value") else str(m.status),
            "tenant_id": m.tenant_id,
            "created_at": m.created_at.isoformat(),
            "updated_at": m.updated_at.isoformat(),
            "training_metadata": m.training_metadata,
        }
    # SQLAlchemy model
    return {
        "id": str(m.id),
        "name": m.name,
        "model_type": m.model_type,
        "parameters": m.parameters or {},
        "hyperparameters": m.hyperparameters or {},
        "status": m.status,
        "tenant_id": m.tenant_id,
        "created_at": m.created_at.isoformat() if m.created_at else "",
        "updated_at": m.updated_at.isoformat() if m.updated_at else "",
        "training_metadata": m.training_metadata or {},
    }


def _forecast_to_dict(r) -> dict:
    if isinstance(r, ForecastResult):
        return {
            "id": str(r.id),
            "model_id": str(r.model_id),
            "metric_id": str(r.metric_id),
            "metric_name": r.metric_name,
            "period": r.period,
            "values": r.values,
            "metrics": r.metrics,
            "model_name": r.model_name,
            "model_type": r.model_type.value if hasattr(r.model_type, "value") else str(r.model_type),
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat(),
        }
    # SQLAlchemy model
    return {
        "id": str(r.id),
        "model_id": str(r.model_id),
        "metric_id": r.metric_id,
        "metric_name": r.metric_name,
        "period": r.period,
        "values": r.values or [],
        "metrics": r.metrics or {},
        "model_name": r.model_name or "",
        "model_type": r.model_type or "",
        "created_at": r.created_at.isoformat() if r.created_at else "",
    }


def _alert_to_dict(a) -> dict:
    if isinstance(a, MonitoringAlert):
        return {
            "id": str(a.id),
            "model_id": str(a.model_id),
            "metric_name": a.metric_name,
            "alert_type": a.alert_type.value if hasattr(a.alert_type, "value") else str(a.alert_type),
            "severity": a.severity,
            "details": a.details,
            "detected_at": a.detected_at.isoformat(),
            "is_resolved": a.is_resolved,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        }
    # SQLAlchemy model
    return {
        "id": str(a.id),
        "model_id": str(a.model_id),
        "metric_name": a.metric_name or "",
        "alert_type": a.alert_type,
        "severity": a.severity,
        "details": a.details or {},
        "detected_at": a.created_at.isoformat() if a.created_at else "",
        "is_resolved": a.is_resolved,
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
    }


def _comparison_to_dict(c: ChampionChallengerResult) -> dict:
    return {
        "id": str(c.id),
        "champion_model_id": str(c.champion_model_id),
        "challenger_model_id": str(c.challenger_model_id),
        "metric_name": c.metric_name,
        "comparison_period": c.comparison_period,
        "champion_metrics": c.champion_metrics,
        "challenger_metrics": c.challenger_metrics,
        "winner": c.winner,
        "confidence": c.confidence,
        "recommendation": c.recommendation,
        "created_at": c.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# 1. Create model
# ---------------------------------------------------------------------------

@router.post("/models")
async def create_model(
    req: ModelCreate,
    db: AsyncSession = Depends(get_db),
    _user: DevUser = Depends(dep_dev_admin),
):
    try:
        model_type = ForecastModel(req.model_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid model_type: {req.model_type}")

    repo = ForecastModelRepository(db)
    model = await repo.create(
        tenant_id=str(_user.tenant_id),
        name=req.name,
        model_type=req.model_type,
        parameters=req.parameters,
        hyperparameters=req.hyperparameters,
    )
    return {"status": "success", "data": _model_to_dict(model), "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# 2. Get model
# ---------------------------------------------------------------------------

@router.get("/models/{model_id}")
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    _user: DevUser = Depends(dep_dev_admin),
):
    try:
        mid = UUID(model_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid model_id")

    repo = ForecastModelRepository(db)
    model = await repo.get_by_id_with_tenant(mid, str(_user.tenant_id))
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"status": "success", "data": _model_to_dict(model), "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# 3. List models
# ---------------------------------------------------------------------------

@router.get("/models")
async def list_models(
    status: Optional[str] = Query(None),
    metric_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: DevUser = Depends(dep_dev_admin),
):
    repo = ForecastModelRepository(db)
    models = await repo.list_models(str(_user.tenant_id), status=status, offset=skip, limit=limit)
    total = await repo.count(str(_user.tenant_id), status=status)

    return {
        "status": "success",
        "data": {
            "models": [_model_to_dict(m) for m in models],
            "total": total,
            "skip": skip,
            "limit": limit,
        },
        "meta": {"request_id": str(uuid4())},
    }


# ---------------------------------------------------------------------------
# 4. Train model
# ---------------------------------------------------------------------------

@router.post("/models/{model_id}/train")
async def train_model(
    model_id: str,
    req: TrainRequest,
    db: AsyncSession = Depends(get_db),
    _user: DevUser = Depends(dep_dev_admin),
):
    try:
        mid = UUID(model_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid model_id")

    repo = ForecastModelRepository(db)
    db_model = await repo.get_by_id_with_tenant(mid, str(_user.tenant_id))
    if db_model is None:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    service = ForecastingService()
    model_config = ForecastModelConfig(
        id=mid,
        name=db_model.name,
        model_type=ForecastModel(db_model.model_type),
        parameters=db_model.parameters or {},
        hyperparameters=db_model.hyperparameters or {},
        status=ModelStatus(db_model.status),
        tenant_id=str(_user.tenant_id),
        created_at=db_model.created_at,
        updated_at=db_model.updated_at or db_model.created_at,
        training_metadata=db_model.training_metadata or {},
    )

    try:
        trained = service.train_model(
            tenant_id=str(_user.tenant_id),
            model_id=mid,
            training_data=req.training_data,
            target_column=req.target_column,
            date_column=req.date_column,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    await repo.update_model(
        model_id=mid,
        status=trained.status.value if hasattr(trained.status, "value") else str(trained.status),
        training_metadata=trained.training_metadata,
    )

    updated = await repo.get_by_id(mid)
    return {"status": "success", "data": _model_to_dict(updated), "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# 5. Generate forecast
# ---------------------------------------------------------------------------

@router.post("/models/{model_id}/forecast")
async def generate_forecast(
    model_id: str,
    req: ForecastRequest,
    db: AsyncSession = Depends(get_db),
    _user: DevUser = Depends(dep_dev_admin),
):
    try:
        mid = UUID(model_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid model_id")

    try:
        metric_uuid = UUID(req.metric_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric_id")

    model_repo = ForecastModelRepository(db)
    db_model = await model_repo.get_by_id_with_tenant(mid, str(_user.tenant_id))
    if db_model is None:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    service = ForecastingService()
    result = service.generate_forecast(
        tenant_id=str(_user.tenant_id),
        model_id=mid,
        metric_id=metric_uuid,
        metric_name=req.metric_name,
        periods=req.periods,
        historical_data=req.historical_data,
        confidence_level=req.confidence_level,
    )

    result_repo = ForecastResultRepository(db)
    persisted = await result_repo.create(
        tenant_id=str(_user.tenant_id),
        model_id=mid,
        metric_id=req.metric_id,
        metric_name=req.metric_name,
        period=str(req.periods),
        values=result.values,
        metrics=result.metrics,
        model_name=db_model.name,
        model_type=db_model.model_type,
        confidence_level=req.confidence_level,
    )

    return {"status": "success", "data": _forecast_to_dict(persisted), "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# 6. Evaluate model
# ---------------------------------------------------------------------------

@router.post("/models/{model_id}/evaluate")
async def evaluate_model(
    model_id: str,
    req: EvaluateRequest,
    db: AsyncSession = Depends(get_db),
    _user: DevUser = Depends(dep_dev_admin),
):
    try:
        mid = UUID(model_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid model_id")

    model_repo = ForecastModelRepository(db)
    db_model = await model_repo.get_by_id_with_tenant(mid, str(_user.tenant_id))
    if db_model is None:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    service = ForecastingService()
    metrics = service.evaluate_model(
        tenant_id=str(_user.tenant_id),
        model_id=mid,
        test_data=req.test_data,
    )

    return {"status": "success", "data": metrics, "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# 7. Compare models
# ---------------------------------------------------------------------------

@router.post("/compare")
async def compare_models(
    req: CompareRequest,
    db: AsyncSession = Depends(get_db),
    _user: DevUser = Depends(dep_dev_admin),
):
    model_uuids = []
    for mid_str in req.model_ids:
        try:
            model_uuids.append(UUID(mid_str))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid model_id: {mid_str}")

    model_repo = ForecastModelRepository(db)
    for mid in model_uuids:
        db_model = await model_repo.get_by_id_with_tenant(mid, str(_user.tenant_id))
        if db_model is None:
            raise HTTPException(status_code=404, detail=f"Model {mid} not found")

    service = ForecastingService()
    try:
        result = service.compare_models(
            tenant_id=str(_user.tenant_id),
            model_ids=model_uuids,
            metric_name=req.metric_name,
            comparison_data=req.comparison_data,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success", "data": _comparison_to_dict(result), "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# 8. Create ensemble
# ---------------------------------------------------------------------------

@router.post("/ensemble")
async def create_ensemble(
    req: EnsembleRequest,
    db: AsyncSession = Depends(get_db),
    _user: DevUser = Depends(dep_dev_admin),
):
    model_repo = ForecastModelRepository(db)
    models: List[ForecastModelConfig] = []
    weights: List[float] = []

    for member in req.models:
        try:
            mid = UUID(member.model_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid model_id: {member.model_id}")

        db_model = await model_repo.get_by_id_with_tenant(mid, str(_user.tenant_id))
        if db_model is None:
            raise HTTPException(status_code=404, detail=f"Model {member.model_id} not found")

        models.append(ForecastModelConfig(
            id=mid,
            name=db_model.name,
            model_type=ForecastModel(db_model.model_type),
            parameters=db_model.parameters or {},
            hyperparameters=db_model.hyperparameters or {},
            status=ModelStatus(db_model.status),
            tenant_id=str(_user.tenant_id),
            training_metadata=db_model.training_metadata or {},
        ))
        weights.append(member.weight)

    service = ForecastingService()
    try:
        result = service.create_ensemble(
            tenant_id=str(_user.tenant_id),
            models=models,
            weights=weights,
            metric_name=req.metric_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result_repo = ForecastResultRepository(db)
    persisted = await result_repo.create(
        tenant_id=str(_user.tenant_id),
        model_id=result.model_id,
        metric_id=str(result.metric_id),
        metric_name=result.metric_name,
        period=result.period,
        values=result.values,
        metrics=result.metrics,
        model_name=result.model_name,
        model_type="ENSEMBLE",
        confidence_level=0.95,
    )

    return {"status": "success", "data": _forecast_to_dict(persisted), "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# 9. Detect drift
# ---------------------------------------------------------------------------

@router.post("/models/{model_id}/drift")
async def detect_drift(
    model_id: str,
    req: DriftRequest,
    db: AsyncSession = Depends(get_db),
    _user: DevUser = Depends(dep_dev_admin),
):
    try:
        mid = UUID(model_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid model_id")

    model_repo = ForecastModelRepository(db)
    db_model = await model_repo.get_by_id_with_tenant(mid, str(_user.tenant_id))
    if db_model is None:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    service = ForecastingService()
    alerts = service.detect_drift(
        tenant_id=str(_user.tenant_id),
        model_id=mid,
        recent_data=req.recent_data,
        reference_data=req.reference_data,
    )

    alert_repo = ForecastAlertRepository(db)
    alerts_data = [
        {
            "metric_name": a.metric_name,
            "alert_type": a.alert_type.value if hasattr(a.alert_type, "value") else str(a.alert_type),
            "severity": a.severity,
            "details": a.details,
        }
        for a in alerts
    ]
    await alert_repo.create_many(str(_user.tenant_id), mid, alerts_data)

    return {
        "status": "success",
        "data": {"alerts": [_alert_to_dict(a) for a in alerts], "count": len(alerts)},
        "meta": {"request_id": str(uuid4())},
    }


# ---------------------------------------------------------------------------
# 10. Promote model
# ---------------------------------------------------------------------------

@router.put("/models/{model_id}/promote")
async def promote_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    _user: DevUser = Depends(dep_dev_admin),
):
    try:
        mid = UUID(model_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid model_id")

    repo = ForecastModelRepository(db)
    db_model = await repo.get_by_id_with_tenant(mid, str(_user.tenant_id))
    if db_model is None:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    promotion_order = [
        "TRAINING", "VALIDATED", "SHADOW", "CHAMPION", "PRODUCTION",
    ]
    current_status = db_model.status
    try:
        idx = promotion_order.index(current_status)
        if idx < len(promotion_order) - 1:
            new_status = promotion_order[idx + 1]
        else:
            new_status = current_status
    except ValueError:
        new_status = current_status

    updated = await repo.update_status(mid, new_status)
    return {"status": "success", "data": _model_to_dict(updated), "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# 11. Demote model
# ---------------------------------------------------------------------------

@router.put("/models/{model_id}/demote")
async def demote_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    _user: DevUser = Depends(dep_dev_admin),
):
    try:
        mid = UUID(model_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid model_id")

    repo = ForecastModelRepository(db)
    db_model = await repo.get_by_id_with_tenant(mid, str(_user.tenant_id))
    if db_model is None:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    demotion_order = [
        "PRODUCTION", "CHAMPION", "SHADOW", "VALIDATED", "TRAINING", "RETIRED",
    ]
    current_status = db_model.status
    try:
        idx = demotion_order.index(current_status)
        if idx < len(demotion_order) - 1:
            new_status = demotion_order[idx + 1]
        else:
            new_status = current_status
    except ValueError:
        new_status = current_status

    updated = await repo.update_status(mid, new_status)
    return {"status": "success", "data": _model_to_dict(updated), "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# 12. List available model types
# ---------------------------------------------------------------------------

@router.get("/methods")
async def list_methods(_user: DevUser = Depends(dep_dev_admin)):
    methods = [
        {
            "value": m.value,
            "name": m.name,
            "description": {
                "PROPHET": "Facebook Prophet time-series forecasting",
                "ARIMA": "Auto-Regressive Integrated Moving Average",
                "EXPONENTIAL_SMOOTHING": "Single/double/triple exponential smoothing",
                "LINEAR_REGRESSION": "Ordinary least squares linear trend",
                "ENSEMBLE": "Weighted combination of multiple models",
                "XGBOOST": "Gradient-boosted tree ensemble",
            }.get(m.value, ""),
        }
        for m in ForecastModel
    ]
    return {"status": "success", "data": {"methods": methods, "total": len(methods)}, "meta": {"request_id": str(uuid4())}}
