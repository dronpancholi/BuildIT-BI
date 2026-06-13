"""
Outcome Service Implementations.
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from app.domain.outcome.entities import (
    OutcomeDefinition, OutcomeMeasurement, CausalImpactAnalysis,
    FeatureDefinition, ModelArtifact,
)
from app.domain.outcome.services import (
    IOutcomeMeasurementService, IFeatureStoreService, IModelRegistryService,
    DefineOutcomeCommand, MeasurementInput, RegisterFeatureCommand, RegisterModelCommand,
)
from app.domain.outcome.repositories import (
    IOutcomeDefinitionRepository, IOutcomeMeasurementRepository,
    ICausalImpactRepository, IFeatureRepository, IModelRegistryRepository,
)
from app.domain.outcome.value_objects import CausalMethod, OutcomeStatus, MeasurementStatus


class OutcomeMeasurementService(IOutcomeMeasurementService):
    def __init__(self, def_repo: IOutcomeDefinitionRepository,
                 meas_repo: IOutcomeMeasurementRepository,
                 causal_repo: ICausalImpactRepository):
        self._defs = def_repo
        self._meas = meas_repo
        self._causal = causal_repo

    async def define_outcome(self, decision_id, tenant_id, user_id, command):
        obj = OutcomeDefinition(
            id=uuid.uuid4(), tenant_id=tenant_id, decision_id=decision_id,
            metrics=command.metrics,
            measurement_window_start=command.measurement_window_start,
            measurement_window_end=command.measurement_window_end,
            use_control_group=command.use_control_group,
            control_group_definition=command.control_group_definition,
            confidence_level=command.confidence_level,
            created_by=user_id,
        )
        return await self._defs.create(obj)

    async def record_measurement(self, outcome_def_id, data):
        defn = await self._defs.get_by_id(outcome_def_id)
        if not defn:
            raise ValueError(f"Outcome definition {outcome_def_id} not found")

        alerts = []
        status = MeasurementStatus.ON_TRACK
        for mv in (data.metric_values or []):
            if not mv.get("is_within_expected_range", True):
                alerts.append({"metric": mv.get("metric_code"), "alert": "out_of_range"})
                status = MeasurementStatus.DRIFTING

        obj = OutcomeMeasurement(
            id=uuid.uuid4(), tenant_id=defn.tenant_id,
            outcome_definition_id=outcome_def_id,
            decision_id=defn.decision_id,
            checkpoint_type=data.checkpoint_type,
            metric_values=data.metric_values or [],
            status=status, alerts_triggered=alerts,
            measured_by=data.measured_by,
        )
        return await self._meas.create(obj)

    async def compute_interim_status(self, outcome_def_id):
        measurements = await self._meas.get_by_definition(outcome_def_id)
        if not measurements:
            return {"status": "no_data", "checkpoints": 0}
        latest = measurements[0]
        return {
            "status": latest.status.value,
            "checkpoints": len(measurements),
            "latest_measurement": latest.to_dict(),
        }

    async def run_causal_analysis(self, outcome_id, method):
        from app.domain.decision.entities import DecisionOutcome
        obj = CausalImpactAnalysis(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            outcome_id=outcome_id,
            decision_id=uuid.uuid4(),
            method=CausalMethod(method),
            causal_effect_size=0.0,
            causal_effect_confidence=0.95,
        )
        return await self._causal.create(obj)

    async def finalize_outcome(self, outcome_def_id):
        measurements = await self._meas.get_by_definition(outcome_def_id)
        return {"outcome_def_id": str(outcome_def_id), "total_measurements": len(measurements)}

    async def get_outcome_trajectory(self, outcome_def_id):
        measurements = await self._meas.get_by_definition(outcome_def_id)
        return [m.to_dict() for m in measurements]


class FeatureStoreService(IFeatureStoreService):
    def __init__(self, repo: IFeatureRepository):
        self._repo = repo

    async def register_feature(self, tenant_id, user_id, command):
        obj = FeatureDefinition(
            id=uuid.uuid4(), tenant_id=tenant_id,
            name=command.name, namespace=command.namespace,
            description=command.description, feature_type=command.feature_type,
            computation_type=command.computation_type,
            computation_source=command.computation_source,
            computation_params=command.computation_params or {},
            entity_type=command.entity_type, value_type=command.value_type,
            refresh_frequency=command.refresh_frequency,
            tags=command.tags or [], source_metrics=command.source_metrics or [],
            owner_id=user_id,
        )
        return await self._repo.create(obj)

    async def get_feature_value(self, feature_name, entity_id, as_of=None):
        feature = await self._repo.get_by_name(feature_name, "finance")
        if not feature:
            return None
        return {"feature_id": str(feature.id), "entity_id": str(entity_id), "value": feature.default_value}

    async def list_features(self, tenant_id, offset=0, limit=50):
        return await self._repo.list(tenant_id, offset, limit)

    async def search_features(self, tenant_id, query):
        return await self._repo.search(tenant_id, query)

    async def validate_feature(self, feature_id):
        feature = await self._repo.get_by_id(feature_id)
        if not feature:
            return {"is_valid": False, "errors": ["Feature not found"]}
        errors = []
        if not feature.name:
            errors.append("Name is required")
        if not feature.computation_source and feature.computation_type == "sql":
            errors.append("SQL source is required for SQL computation type")
        return {"is_valid": len(errors) == 0, "errors": errors}


class ModelRegistryService(IModelRegistryService):
    def __init__(self, repo: IModelRegistryRepository):
        self._repo = repo

    async def register_model(self, tenant_id, user_id, command):
        obj = ModelArtifact(
            id=uuid.uuid4(), tenant_id=tenant_id,
            name=command.name, model_type=command.model_type,
            framework=command.framework, version=command.version,
            version_notes=command.version_notes,
            model_location=command.model_location,
            use_cases=command.use_cases or [], tags=command.tags or [],
            owner_id=user_id,
        )
        return await self._repo.create(obj)

    async def get_production_model(self, tenant_id, use_case):
        return await self._repo.get_by_use_case(tenant_id, use_case)

    async def list_models(self, tenant_id, offset=0, limit=50):
        return await self._repo.list(tenant_id, offset, limit)

    async def approve_model(self, model_id, reviewer_id, notes):
        model = await self._repo.get_by_id(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        model.approval_status = "approved"
        return await self._repo.update(model)

    async def retire_model(self, model_id):
        model = await self._repo.get_by_id(model_id)
        if not model:
            return False
        model.approval_status = "retired"
        await self._repo.update(model)
        return True
