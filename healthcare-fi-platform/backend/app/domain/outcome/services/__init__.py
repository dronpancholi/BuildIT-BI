"""
Outcome Domain Service Interfaces.
"""
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import date, datetime

from app.domain.outcome.entities import (
    OutcomeDefinition,
    OutcomeMeasurement,
    CausalImpactAnalysis,
    FeatureDefinition,
    ModelArtifact,
)


@dataclass(frozen=True)
class DefineOutcomeCommand:
    metrics: List[Dict[str, Any]]
    measurement_window_start: date
    measurement_window_end: date
    use_control_group: bool = False
    control_group_definition: Optional[Dict[str, Any]] = None
    confidence_level: float = 0.95


@dataclass(frozen=True)
class MeasurementInput:
    checkpoint_type: str = "monthly"
    metric_values: List[Dict[str, Any]] = None
    measured_by: Optional[uuid.UUID] = None

    def __post_init__(self):
        if self.metric_values is None:
            object.__setattr__(self, 'metric_values', [])


@dataclass(frozen=True)
class RegisterFeatureCommand:
    name: str
    namespace: str = "finance"
    description: str = ""
    feature_type: str = "aggregation"
    computation_type: str = "sql"
    computation_source: str = ""
    computation_params: Optional[Dict[str, Any]] = None
    entity_type: str = "department"
    value_type: str = "float"
    refresh_frequency: str = "daily"
    tags: Optional[List[str]] = None
    source_metrics: Optional[List[str]] = None


@dataclass(frozen=True)
class RegisterModelCommand:
    name: str
    model_type: str = "statistical"
    framework: Optional[str] = None
    version: str = "1.0.0"
    version_notes: str = ""
    model_location: str = ""
    use_cases: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class IOutcomeMeasurementService(ABC):
    @abstractmethod
    async def define_outcome(self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
                             user_id: uuid.UUID, command: DefineOutcomeCommand) -> OutcomeDefinition: pass
    @abstractmethod
    async def record_measurement(self, outcome_def_id: uuid.UUID, data: MeasurementInput) -> OutcomeMeasurement: pass
    @abstractmethod
    async def compute_interim_status(self, outcome_def_id: uuid.UUID) -> Dict[str, Any]: pass
    @abstractmethod
    async def run_causal_analysis(self, outcome_id: uuid.UUID, method: str) -> CausalImpactAnalysis: pass
    @abstractmethod
    async def finalize_outcome(self, outcome_def_id: uuid.UUID) -> Dict[str, Any]: pass
    @abstractmethod
    async def get_outcome_trajectory(self, outcome_def_id: uuid.UUID) -> List[Dict[str, Any]]: pass


class IFeatureStoreService(ABC):
    @abstractmethod
    async def register_feature(self, tenant_id: uuid.UUID, user_id: uuid.UUID,
                               command: RegisterFeatureCommand) -> FeatureDefinition: pass
    @abstractmethod
    async def get_feature_value(self, feature_name: str, entity_id: uuid.UUID,
                                as_of: Optional[datetime] = None) -> Optional[Any]: pass
    @abstractmethod
    async def list_features(self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50) -> List[FeatureDefinition]: pass
    @abstractmethod
    async def search_features(self, tenant_id: uuid.UUID, query: str) -> List[FeatureDefinition]: pass
    @abstractmethod
    async def validate_feature(self, feature_id: uuid.UUID) -> Dict[str, Any]: pass


class IModelRegistryService(ABC):
    @abstractmethod
    async def register_model(self, tenant_id: uuid.UUID, user_id: uuid.UUID,
                             command: RegisterModelCommand) -> ModelArtifact: pass
    @abstractmethod
    async def get_production_model(self, tenant_id: uuid.UUID, use_case: str) -> Optional[ModelArtifact]: pass
    @abstractmethod
    async def list_models(self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50) -> List[ModelArtifact]: pass
    @abstractmethod
    async def approve_model(self, model_id: uuid.UUID, reviewer_id: uuid.UUID, notes: str) -> ModelArtifact: pass
    @abstractmethod
    async def retire_model(self, model_id: uuid.UUID) -> bool: pass
