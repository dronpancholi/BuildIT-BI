"""
V2 Outcome, Feature Store, Model Registry API Endpoints.
"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dev_auth import dep_dev_admin
from app.domain.outcome.services import (
    DefineOutcomeCommand, MeasurementInput, RegisterFeatureCommand, RegisterModelCommand,
)
from app.domain.outcome.services.service_impl import (
    OutcomeMeasurementService, FeatureStoreService, ModelRegistryService,
)
from app.infrastructure.database.repositories.outcome_repository import (
    OutcomeDefinitionRepository, OutcomeMeasurementRepository,
    CausalImpactRepository, FeatureRepository, ModelRegistryRepository,
)

router = APIRouter()


# ============================================================
# SCHEMAS
# ============================================================

class DefineOutcomeRequest(BaseModel):
    decision_id: str
    metrics: List[Dict[str, Any]]
    measurement_window_start: str  # ISO date
    measurement_window_end: str
    use_control_group: bool = False
    confidence_level: float = 0.95

class RecordMeasurementRequest(BaseModel):
    outcome_definition_id: str
    checkpoint_type: str = "monthly"
    metric_values: List[Dict[str, Any]] = []
    measured_by: Optional[str] = None

class RegisterFeatureRequest(BaseModel):
    name: str
    namespace: str = "finance"
    description: str = ""
    feature_type: str = "aggregation"
    computation_type: str = "sql"
    computation_source: str = ""
    entity_type: str = "department"
    value_type: str = "float"
    refresh_frequency: str = "daily"
    tags: Optional[List[str]] = None
    source_metrics: Optional[List[str]] = None

class RegisterModelRequest(BaseModel):
    model_config = {'protected_namespaces': ()}
    name: str
    model_type: str = "statistical"
    framework: Optional[str] = None
    version: str = "1.0.0"
    version_notes: str = ""
    model_location: str = ""
    use_cases: Optional[List[str]] = None
    tags: Optional[List[str]] = None


# ============================================================
# HELPERS
# ============================================================

def _get_outcome_service(db):
    return OutcomeMeasurementService(
        OutcomeDefinitionRepository(db),
        OutcomeMeasurementRepository(db),
        CausalImpactRepository(db),
    )

def _get_feature_service(db):
    return FeatureStoreService(FeatureRepository(db))

def _get_model_service(db):
    return ModelRegistryService(ModelRegistryRepository(db))

def _uid(user):
    return uuid.UUID(str(user.id))

def _tid(user):
    return uuid.UUID(str(user.tenant_id)) if hasattr(user, 'tenant_id') else uuid.uuid4()


# ============================================================
# OUTCOMES
# ============================================================

@router.post("/outcomes/definitions", status_code=status.HTTP_201_CREATED)
async def define_outcome(
    request: DefineOutcomeRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_outcome_service(db)
    command = DefineOutcomeCommand(
        metrics=request.metrics,
        measurement_window_start=date.fromisoformat(request.measurement_window_start),
        measurement_window_end=date.fromisoformat(request.measurement_window_end),
        use_control_group=request.use_control_group,
        confidence_level=request.confidence_level,
    )
    result = await service.define_outcome(
        uuid.UUID(request.decision_id), _tid(current_user), _uid(current_user), command
    )
    return result.to_dict()


@router.get("/outcomes/definitions/{definition_id}")
async def get_outcome_definition(
    definition_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_outcome_service(db)
    result = await service._defs.get_by_id(definition_id)
    if not result:
        raise HTTPException(status_code=404, detail="Outcome definition not found")
    return result.to_dict()


@router.post("/outcomes/measurements", status_code=status.HTTP_201_CREATED)
async def record_measurement(
    request: RecordMeasurementRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_outcome_service(db)
    data = MeasurementInput(
        checkpoint_type=request.checkpoint_type,
        metric_values=request.metric_values,
        measured_by=uuid.UUID(request.measured_by) if request.measured_by else _uid(current_user),
    )
    result = await service.record_measurement(uuid.UUID(request.outcome_definition_id), data)
    return result.to_dict()


@router.get("/outcomes/definitions/{definition_id}/measurements")
async def get_measurements(
    definition_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_outcome_service(db)
    measurements = await service._meas.get_by_definition(definition_id)
    return [m.to_dict() for m in measurements]


@router.get("/outcomes/definitions/{definition_id}/trajectory")
async def get_trajectory(
    definition_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_outcome_service(db)
    return await service.get_outcome_trajectory(definition_id)


# ============================================================
# FEATURES
# ============================================================

@router.post("/features", status_code=status.HTTP_201_CREATED)
async def register_feature(
    request: RegisterFeatureRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_feature_service(db)
    command = RegisterFeatureCommand(
        name=request.name, namespace=request.namespace,
        description=request.description, feature_type=request.feature_type,
        computation_type=request.computation_type,
        computation_source=request.computation_source,
        entity_type=request.entity_type, value_type=request.value_type,
        refresh_frequency=request.refresh_frequency,
        tags=request.tags, source_metrics=request.source_metrics,
    )
    result = await service.register_feature(_tid(current_user), _uid(current_user), command)
    return result.to_dict()


@router.get("/features")
async def list_features(
    offset: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_feature_service(db)
    features = await service.list_features(_tid(current_user), offset, limit)
    return [f.to_dict() for f in features]


@router.get("/features/search")
async def search_features(
    q: str = "",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_feature_service(db)
    features = await service.search_features(_tid(current_user), q)
    return [f.to_dict() for f in features]


@router.get("/features/{feature_id}")
async def get_feature(
    feature_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_feature_service(db)
    feature = await service._repo.get_by_id(feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature.to_dict()


@router.post("/features/{feature_id}/validate")
async def validate_feature(
    feature_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_feature_service(db)
    return await service.validate_feature(feature_id)


# ============================================================
# MODELS
# ============================================================

@router.post("/models", status_code=status.HTTP_201_CREATED)
async def register_model(
    request: RegisterModelRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_model_service(db)
    command = RegisterModelCommand(
        name=request.name, model_type=request.model_type,
        framework=request.framework, version=request.version,
        version_notes=request.version_notes,
        model_location=request.model_location,
        use_cases=request.use_cases, tags=request.tags,
    )
    result = await service.register_model(_tid(current_user), _uid(current_user), command)
    return result.to_dict()


@router.get("/models")
async def list_models(
    offset: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_model_service(db)
    models = await service.list_models(_tid(current_user), offset, limit)
    return [m.to_dict() for m in models]


@router.get("/models/{model_id}")
async def get_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_model_service(db)
    model = await service._repo.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model.to_dict()


@router.post("/models/{model_id}/approve")
async def approve_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_model_service(db)
    try:
        result = await service.approve_model(model_id, _uid(current_user), "Approved via API")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result.to_dict()


@router.post("/models/{model_id}/retire")
async def retire_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_model_service(db)
    success = await service.retire_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"success": True}
