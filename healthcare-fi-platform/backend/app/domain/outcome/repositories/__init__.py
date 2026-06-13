"""
Outcome Domain Repository Interfaces.
"""
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List

from app.domain.outcome.entities import (
    OutcomeDefinition,
    OutcomeMeasurement,
    CausalImpactAnalysis,
    FeatureDefinition,
    ModelArtifact,
)


class IOutcomeDefinitionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Optional[OutcomeDefinition]: pass
    @abstractmethod
    async def get_by_decision(self, decision_id: uuid.UUID) -> Optional[OutcomeDefinition]: pass
    @abstractmethod
    async def create(self, obj: OutcomeDefinition) -> OutcomeDefinition: pass
    @abstractmethod
    async def update(self, obj: OutcomeDefinition) -> OutcomeDefinition: pass


class IOutcomeMeasurementRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Optional[OutcomeMeasurement]: pass
    @abstractmethod
    async def get_by_definition(self, definition_id: uuid.UUID) -> List[OutcomeMeasurement]: pass
    @abstractmethod
    async def create(self, obj: OutcomeMeasurement) -> OutcomeMeasurement: pass


class ICausalImpactRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Optional[CausalImpactAnalysis]: pass
    @abstractmethod
    async def get_by_outcome(self, outcome_id: uuid.UUID) -> Optional[CausalImpactAnalysis]: pass
    @abstractmethod
    async def create(self, obj: CausalImpactAnalysis) -> CausalImpactAnalysis: pass


class IFeatureRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Optional[FeatureDefinition]: pass
    @abstractmethod
    async def get_by_name(self, name: str, namespace: str) -> Optional[FeatureDefinition]: pass
    @abstractmethod
    async def list(self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50) -> List[FeatureDefinition]: pass
    @abstractmethod
    async def create(self, obj: FeatureDefinition) -> FeatureDefinition: pass
    @abstractmethod
    async def update(self, obj: FeatureDefinition) -> FeatureDefinition: pass
    @abstractmethod
    async def search(self, tenant_id: uuid.UUID, query: str) -> List[FeatureDefinition]: pass


class IModelRegistryRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelArtifact]: pass
    @abstractmethod
    async def list(self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50) -> List[ModelArtifact]: pass
    @abstractmethod
    async def create(self, obj: ModelArtifact) -> ModelArtifact: pass
    @abstractmethod
    async def update(self, obj: ModelArtifact) -> ModelArtifact: pass
    @abstractmethod
    async def get_by_use_case(self, tenant_id: uuid.UUID, use_case: str) -> Optional[ModelArtifact]: pass
