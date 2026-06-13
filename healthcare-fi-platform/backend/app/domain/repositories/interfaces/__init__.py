"""
Repository interfaces for the Healthcare Financial Intelligence Platform.
These are abstract contracts - implementations are in infrastructure layer.
"""
import uuid
from abc import ABC, abstractmethod
from typing import Optional, List, Generic, TypeVar, Type
from datetime import datetime

from app.domain.entities.base import TenantAwareEntity

# Generic type for entities
T = TypeVar('T', bound=TenantAwareEntity)


class BaseRepository(ABC, Generic[T]):
    """
    Base repository interface with common CRUD operations.
    """
    
    @abstractmethod
    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def get_by_id_with_tenant(self, entity_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[T]:
        """Get entity by ID with tenant scoping."""
        pass
    
    @abstractmethod
    async def list(
        self,
        tenant_id: uuid.UUID,
        filters: Optional[dict] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[T]:
        """List entities with pagination."""
        pass
    
    @abstractmethod
    async def count(self, tenant_id: uuid.UUID, filters: Optional[dict] = None) -> int:
        """Count entities."""
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    async def soft_delete(self, entity_id: uuid.UUID, deleted_by: uuid.UUID) -> bool:
        """Soft delete an entity."""
        pass
    
    @abstractmethod
    async def exists(self, entity_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        """Check if entity exists."""
        pass


class MetricDefinitionRepository(BaseRepository):
    """
    Repository interface for MetricDefinition entities.
    """
    
    @abstractmethod
    async def get_by_slug(self, slug: str, tenant_id: uuid.UUID) -> Optional[T]:
        """Get metric by slug."""
        pass
    
    @abstractmethod
    async def get_by_code(self, code: str, tenant_id: uuid.UUID) -> Optional[T]:
        """Get metric by code."""
        pass
    
    @abstractmethod
    async def list_published(self, tenant_id: uuid.UUID) -> List[T]:
        """List all published metrics."""
        pass
    
    @abstractmethod
    async def list_by_category(
        self,
        tenant_id: uuid.UUID,
        category: str
    ) -> List[T]:
        """List metrics by category."""
        pass
    
    @abstractmethod
    async def list_by_status(
        self,
        tenant_id: uuid.UUID,
        status: str
    ) -> List[T]:
        """List metrics by status."""
        pass


class MetricComputedValueRepository(BaseRepository):
    """
    Repository interface for MetricComputedValue entities.
    """
    
    @abstractmethod
    async def get_latest(
        self,
        metric_id: uuid.UUID,
        tenant_id: uuid.UUID,
        hospital_id: Optional[uuid.UUID] = None,
        branch_id: Optional[uuid.UUID] = None,
        department_id: Optional[uuid.UUID] = None
    ) -> Optional[T]:
        """Get latest computed value for a metric."""
        pass
    
    @abstractmethod
    async def get_by_period(
        self,
        metric_id: uuid.UUID,
        tenant_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime
    ) -> Optional[T]:
        """Get computed value for a specific period."""
        pass
    
    @abstractmethod
    async def list_by_metric(
        self,
        metric_id: uuid.UUID,
        tenant_id: uuid.UUID,
        limit: int = 100
    ) -> List[T]:
        """List computed values for a metric."""
        pass


class QualityRuleRepository(BaseRepository):
    """
    Repository interface for QualityRule entities.
    """
    
    @abstractmethod
    async def list_active(self, tenant_id: uuid.UUID) -> List[T]:
        """List all active quality rules."""
        pass
    
    @abstractmethod
    async def list_by_entity_type(
        self,
        tenant_id: uuid.UUID,
        entity_type: str
    ) -> List[T]:
        """List rules by entity type."""
        pass
    
    @abstractmethod
    async def list_by_severity(
        self,
        tenant_id: uuid.UUID,
        severity: str
    ) -> List[T]:
        """List rules by severity."""
        pass


class QualityIssueRepository(BaseRepository):
    """
    Repository interface for QualityIssue entities.
    """
    
    @abstractmethod
    async def list_open(self, tenant_id: uuid.UUID) -> List[T]:
        """List all open issues."""
        pass
    
    @abstractmethod
    async def list_by_severity(
        self,
        tenant_id: uuid.UUID,
        severity: str
    ) -> List[T]:
        """List issues by severity."""
        pass
    
    @abstractmethod
    async def list_by_status(
        self,
        tenant_id: uuid.UUID,
        status: str
    ) -> List[T]:
        """List issues by status."""
        pass
    
    @abstractmethod
    async def count_by_severity(self, tenant_id: uuid.UUID) -> dict:
        """Count issues grouped by severity."""
        pass


class LineageNodeRepository(BaseRepository):
    """
    Repository interface for LineageNode entities.
    """
    
    @abstractmethod
    async def get_by_qualified_name(
        self,
        qualified_name: str,
        tenant_id: uuid.UUID
    ) -> Optional[T]:
        """Get node by qualified name."""
        pass
    
    @abstractmethod
    async def list_by_type(
        self,
        tenant_id: uuid.UUID,
        node_type: str
    ) -> List[T]:
        """List nodes by type."""
        pass


class LineageEdgeRepository(BaseRepository):
    """
    Repository interface for LineageEdge entities.
    """
    
    @abstractmethod
    async def get_upstream_edges(
        self,
        target_node_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> List[T]:
        """Get all edges pointing to a node."""
        pass
    
    @abstractmethod
    async def get_downstream_edges(
        self,
        source_node_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> List[T]:
        """Get all edges from a node."""
        pass


class TenantRepository(BaseRepository):
    """
    Repository interface for Tenant entities.
    """
    
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[T]:
        """Get tenant by slug."""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[T]:
        """Get tenant by name."""
        pass


class UserRepository(BaseRepository):
    """
    Repository interface for User entities.
    """
    
    @abstractmethod
    async def get_by_email(self, email: str, tenant_id: uuid.UUID) -> Optional[T]:
        """Get user by email."""
        pass
    
    @abstractmethod
    async def list_by_role(
        self,
        tenant_id: uuid.UUID,
        role: str
    ) -> List[T]:
        """List users by role."""
        pass


class DomainEventRepository(ABC):
    """
    Repository interface for DomainEvent entities.
    Events are immutable - only create and read operations.
    """
    
    @abstractmethod
    async def create(self, event: 'DomainEvent') -> None:
        """Store an event."""
        pass
    
    @abstractmethod
    async def get_by_id(self, event_id: uuid.UUID) -> Optional['DomainEvent']:
        """Get event by ID."""
        pass
    
    @abstractmethod
    async def list_by_type(
        self,
        tenant_id: uuid.UUID,
        event_type: str,
        limit: int = 100
    ) -> List['DomainEvent']:
        """List events by type."""
        pass
    
    @abstractmethod
    async def list_by_time_range(
        self,
        tenant_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100
    ) -> List['DomainEvent']:
        """List events by time range."""
        pass
