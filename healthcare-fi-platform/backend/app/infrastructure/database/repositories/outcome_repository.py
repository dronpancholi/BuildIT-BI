"""
Outcome Repository Implementations.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.outcome.repositories import (
    IOutcomeDefinitionRepository,
    IOutcomeMeasurementRepository,
    ICausalImpactRepository,
    IFeatureRepository,
    IModelRegistryRepository,
)
from app.domain.outcome.entities import (
    OutcomeDefinition,
    OutcomeMeasurement,
    CausalImpactAnalysis,
    FeatureDefinition,
    ModelArtifact,
)
from app.infrastructure.persistence.models import (
    OutcomeDefinitionModel,
    OutcomeMeasurementModel,
    CausalImpactAnalysisModel,
    FeatureDefinitionModel,
    ModelArtifactModel,
)


def _def_to_domain(m) -> OutcomeDefinition:
    return OutcomeDefinition(
        id=m.id, tenant_id=m.tenant_id, decision_id=m.decision_id,
        metrics=m.metrics or [], measurement_window_start=m.measurement_window_start,
        measurement_window_end=m.measurement_window_end,
        comparison_period_start=m.comparison_period_start,
        comparison_period_end=m.comparison_period_end,
        use_control_group=m.use_control_group,
        control_group_definition=m.control_group_definition,
        confidence_level=m.confidence_level,
        min_sample_size=m.min_sample_size,
        created_by=m.created_by, created_at=m.created_at,
    )

def _meas_to_domain(m) -> OutcomeMeasurement:
    return OutcomeMeasurement(
        id=m.id, tenant_id=m.tenant_id, outcome_definition_id=m.outcome_definition_id,
        decision_id=m.decision_id, measurement_time=m.measurement_time,
        checkpoint_type=m.checkpoint_type, metric_values=m.metric_values or [],
        status=m.status, alerts_triggered=m.alerts_triggered or [],
        measured_by=m.measured_by, created_at=m.created_at,
    )

def _causal_to_domain(m) -> CausalImpactAnalysis:
    return CausalImpactAnalysis(
        id=m.id, tenant_id=m.tenant_id, outcome_id=m.outcome_id,
        decision_id=m.decision_id, method=m.method,
        causal_effect_size=m.causal_effect_size,
        causal_effect_confidence=m.causal_effect_confidence,
        confidence_interval_lower=m.confidence_interval_lower,
        confidence_interval_upper=m.confidence_interval_upper,
        attribution_score=m.attribution_score,
        counterfactual_value=m.counterfactual_value,
        counterfactual_confidence=m.counterfactual_confidence,
        treatment_vs_control=m.treatment_vs_control,
        statistical_significance=m.statistical_significance,
        effect_hypothesis_test=m.effect_hypothesis_test or "",
        analysis_time=m.analysis_time, analyzed_by=m.analyzed_by,
    )

def _feature_to_domain(m) -> FeatureDefinition:
    return FeatureDefinition(
        id=m.id, tenant_id=m.tenant_id, name=m.name, namespace=m.namespace,
        description=m.description or "", feature_type=m.feature_type,
        computation_type=m.computation_type, computation_source=m.computation_source or "",
        computation_params=m.computation_params or {}, entity_type=m.entity_type,
        entity_id_path=m.entity_id_path or "", temporal_type=m.temporal_type,
        window_size=m.window_size, window_unit=m.window_unit,
        refresh_frequency=m.refresh_frequency, value_type=m.value_type,
        default_value=m.default_value, owner_id=m.owner_id,
        tags=m.tags or [], source_metrics=m.source_metrics or [],
        source_features=m.source_features or [], status=m.status,
        version=m.version, created_at=m.created_at, updated_at=m.updated_at,
    )

def _model_to_domain(m) -> ModelArtifact:
    return ModelArtifact(
        id=m.id, tenant_id=m.tenant_id, name=m.name,
        model_type=m.model_type, framework=m.framework,
        version=m.version, version_notes=m.version_notes or "",
        model_location=m.model_location or "",
        artifact_size_bytes=m.artifact_size_bytes or 0,
        checksum=m.checksum or "", model_format=m.model_format,
        metrics=m.metrics or [], entity_type=m.entity_type,
        use_cases=m.use_cases or [], owner_id=m.owner_id,
        approval_status=m.approval_status, tags=m.tags or [],
        created_at=m.created_at, updated_at=m.updated_at,
        version_int=m.version_int,
    )


class OutcomeDefinitionRepository(IOutcomeDefinitionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[OutcomeDefinition]:
        q = select(OutcomeDefinitionModel).where(OutcomeDefinitionModel.id == id)
        r = await self._session.execute(q)
        m = r.scalar_one_or_none()
        return _def_to_domain(m) if m else None

    async def get_by_decision(self, decision_id: uuid.UUID) -> Optional[OutcomeDefinition]:
        q = select(OutcomeDefinitionModel).where(OutcomeDefinitionModel.decision_id == decision_id)
        r = await self._session.execute(q)
        m = r.scalar_one_or_none()
        return _def_to_domain(m) if m else None

    async def create(self, obj: OutcomeDefinition) -> OutcomeDefinition:
        m = OutcomeDefinitionModel(
            id=obj.id, tenant_id=obj.tenant_id, decision_id=obj.decision_id,
            metrics=obj.metrics, measurement_window_start=obj.measurement_window_start,
            measurement_window_end=obj.measurement_window_end,
            comparison_period_start=obj.comparison_period_start,
            comparison_period_end=obj.comparison_period_end,
            use_control_group=obj.use_control_group,
            control_group_definition=obj.control_group_definition,
            confidence_level=obj.confidence_level,
            min_sample_size=obj.min_sample_size,
            created_by=obj.created_by,
        )
        self._session.add(m)
        await self._session.flush()
        return _def_to_domain(m)

    async def update(self, obj: OutcomeDefinition) -> OutcomeDefinition:
        q = select(OutcomeDefinitionModel).where(OutcomeDefinitionModel.id == obj.id)
        r = await self._session.execute(q)
        m = r.scalar_one()
        m.metrics = obj.metrics
        m.confidence_level = obj.confidence_level
        await self._session.flush()
        return _def_to_domain(m)


class OutcomeMeasurementRepository(IOutcomeMeasurementRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[OutcomeMeasurement]:
        q = select(OutcomeMeasurementModel).where(OutcomeMeasurementModel.id == id)
        r = await self._session.execute(q)
        m = r.scalar_one_or_none()
        return _meas_to_domain(m) if m else None

    async def get_by_definition(self, definition_id: uuid.UUID) -> List[OutcomeMeasurement]:
        q = select(OutcomeMeasurementModel).where(
            OutcomeMeasurementModel.outcome_definition_id == definition_id
        ).order_by(OutcomeMeasurementModel.measurement_time.desc())
        r = await self._session.execute(q)
        return [_meas_to_domain(m) for m in r.scalars().all()]

    async def create(self, obj: OutcomeMeasurement) -> OutcomeMeasurement:
        m = OutcomeMeasurementModel(
            id=obj.id, tenant_id=obj.tenant_id,
            outcome_definition_id=obj.outcome_definition_id,
            decision_id=obj.decision_id, measurement_time=obj.measurement_time,
            checkpoint_type=obj.checkpoint_type.value,
            metric_values=obj.metric_values, status=obj.status.value,
            alerts_triggered=obj.alerts_triggered, measured_by=obj.measured_by,
        )
        self._session.add(m)
        await self._session.flush()
        return _meas_to_domain(m)


class CausalImpactRepository(ICausalImpactRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[CausalImpactAnalysis]:
        q = select(CausalImpactAnalysisModel).where(CausalImpactAnalysisModel.id == id)
        r = await self._session.execute(q)
        m = r.scalar_one_or_none()
        return _causal_to_domain(m) if m else None

    async def get_by_outcome(self, outcome_id: uuid.UUID) -> Optional[CausalImpactAnalysis]:
        q = select(CausalImpactAnalysisModel).where(CausalImpactAnalysisModel.outcome_id == outcome_id)
        r = await self._session.execute(q)
        m = r.scalar_one_or_none()
        return _causal_to_domain(m) if m else None

    async def create(self, obj: CausalImpactAnalysis) -> CausalImpactAnalysis:
        m = CausalImpactAnalysisModel(
            id=obj.id, tenant_id=obj.tenant_id, outcome_id=obj.outcome_id,
            decision_id=obj.decision_id, method=obj.method.value,
            causal_effect_size=obj.causal_effect_size,
            causal_effect_confidence=obj.causal_effect_confidence,
            confidence_interval_lower=obj.confidence_interval_lower,
            confidence_interval_upper=obj.confidence_interval_upper,
            attribution_score=obj.attribution_score,
            confounding_factors=[],
            counterfactual_value=obj.counterfactual_value,
            counterfactual_confidence=obj.counterfactual_confidence,
            treatment_vs_control=obj.treatment_vs_control,
            statistical_significance=obj.statistical_significance,
            effect_hypothesis_test=obj.effect_hypothesis_test,
            analyzed_by=obj.analyzed_by,
        )
        self._session.add(m)
        await self._session.flush()
        return _causal_to_domain(m)


class FeatureRepository(IFeatureRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[FeatureDefinition]:
        q = select(FeatureDefinitionModel).where(FeatureDefinitionModel.id == id)
        r = await self._session.execute(q)
        m = r.scalar_one_or_none()
        return _feature_to_domain(m) if m else None

    async def get_by_name(self, name: str, namespace: str) -> Optional[FeatureDefinition]:
        q = select(FeatureDefinitionModel).where(
            FeatureDefinitionModel.name == name,
            FeatureDefinitionModel.namespace == namespace,
        )
        r = await self._session.execute(q)
        m = r.scalar_one_or_none()
        return _feature_to_domain(m) if m else None

    async def list(self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50) -> List[FeatureDefinition]:
        q = select(FeatureDefinitionModel).where(
            FeatureDefinitionModel.tenant_id == tenant_id
        ).order_by(FeatureDefinitionModel.created_at.desc()).offset(offset).limit(limit)
        r = await self._session.execute(q)
        return [_feature_to_domain(m) for m in r.scalars().all()]

    async def create(self, obj: FeatureDefinition) -> FeatureDefinition:
        m = FeatureDefinitionModel(
            id=obj.id, tenant_id=obj.tenant_id, name=obj.name,
            namespace=obj.namespace, description=obj.description,
            feature_type=obj.feature_type, computation_type=obj.computation_type,
            computation_source=obj.computation_source,
            computation_params=obj.computation_params,
            entity_type=obj.entity_type, entity_id_path=obj.entity_id_path,
            temporal_type=obj.temporal_type, window_size=obj.window_size,
            window_unit=obj.window_unit, refresh_frequency=obj.refresh_frequency,
            value_type=obj.value_type, default_value=obj.default_value,
            owner_id=obj.owner_id, tags=obj.tags,
            source_metrics=obj.source_metrics,
            source_features=obj.source_features,
            status=obj.status, version=obj.version,
        )
        self._session.add(m)
        await self._session.flush()
        return _feature_to_domain(m)

    async def update(self, obj: FeatureDefinition) -> FeatureDefinition:
        q = select(FeatureDefinitionModel).where(FeatureDefinitionModel.id == obj.id)
        r = await self._session.execute(q)
        m = r.scalar_one()
        m.status = obj.status
        m.version = obj.version
        m.updated_at = datetime.utcnow()
        await self._session.flush()
        return _feature_to_domain(m)

    async def search(self, tenant_id: uuid.UUID, query: str) -> List[FeatureDefinition]:
        q = select(FeatureDefinitionModel).where(
            FeatureDefinitionModel.tenant_id == tenant_id,
            FeatureDefinitionModel.name.ilike(f"%{query}%"),
        ).limit(20)
        r = await self._session.execute(q)
        return [_feature_to_domain(m) for m in r.scalars().all()]


class ModelRegistryRepository(IModelRegistryRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelArtifact]:
        q = select(ModelArtifactModel).where(ModelArtifactModel.id == id)
        r = await self._session.execute(q)
        m = r.scalar_one_or_none()
        return _model_to_domain(m) if m else None

    async def list(self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50) -> List[ModelArtifact]:
        q = select(ModelArtifactModel).where(
            ModelArtifactModel.tenant_id == tenant_id
        ).order_by(ModelArtifactModel.created_at.desc()).offset(offset).limit(limit)
        r = await self._session.execute(q)
        return [_model_to_domain(m) for m in r.scalars().all()]

    async def create(self, obj: ModelArtifact) -> ModelArtifact:
        m = ModelArtifactModel(
            id=obj.id, tenant_id=obj.tenant_id, name=obj.name,
            model_type=obj.model_type, framework=obj.framework,
            version=obj.version, version_notes=obj.version_notes,
            model_location=obj.model_location,
            artifact_size_bytes=obj.artifact_size_bytes,
            checksum=obj.checksum, model_format=obj.model_format,
            metrics=obj.metrics, entity_type=obj.entity_type,
            use_cases=obj.use_cases, owner_id=obj.owner_id,
            approval_status=obj.approval_status, tags=obj.tags,
            version_int=obj.version_int,
        )
        self._session.add(m)
        await self._session.flush()
        return _model_to_domain(m)

    async def update(self, obj: ModelArtifact) -> ModelArtifact:
        q = select(ModelArtifactModel).where(ModelArtifactModel.id == obj.id)
        r = await self._session.execute(q)
        m = r.scalar_one()
        m.approval_status = obj.approval_status
        m.version = obj.version
        m.updated_at = datetime.utcnow()
        await self._session.flush()
        return _model_to_domain(m)

    async def get_by_use_case(self, tenant_id: uuid.UUID, use_case: str) -> Optional[ModelArtifact]:
        q = select(ModelArtifactModel).where(
            ModelArtifactModel.tenant_id == tenant_id,
            ModelArtifactModel.use_cases.op("@>")(f'["{use_case}"]'),
            ModelArtifactModel.approval_status == "approved",
        ).order_by(ModelArtifactModel.created_at.desc()).limit(1)
        r = await self._session.execute(q)
        m = r.scalar_one_or_none()
        return _model_to_domain(m) if m else None
