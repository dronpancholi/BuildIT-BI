"""
Base entity contracts for the Healthcare Financial Intelligence Platform.
These contracts define the foundational patterns for all domain entities.
"""
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


@dataclass(kw_only=True)
class TenantAwareEntity:
    """
    Base contract for all tenant-scoped entities.
    Every table is tenant-partitioned from day one.
    """
    tenant_id: uuid.UUID
    entity_id: uuid.UUID = field(default_factory=uuid.uuid4)
    
    # Audit metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[uuid.UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[uuid.UUID] = None
    version: int = 1
    
    # Soft delete (NOT hard delete — ever)
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None
    
    def soft_delete(self, deleted_by: uuid.UUID) -> None:
        """Mark entity as soft deleted."""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
        self.updated_at = datetime.utcnow()
        self.updated_by = deleted_by
        self.version += 1
    
    def update_version(self, updated_by: uuid.UUID) -> None:
        """Increment version on mutation."""
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
        self.version += 1
    
    def is_deleted(self) -> bool:
        """Check if entity is soft deleted."""
        return self.deleted_at is not None


@dataclass(kw_only=True)
class BaseEntity:
    """
    Base contract for non-tenant entities (e.g., Tenant itself).
    """
    entity_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    
    def update_version(self) -> None:
        """Increment version on mutation."""
        self.updated_at = datetime.utcnow()
        self.version += 1


# Type aliases for clarity
EntityID = uuid.UUID
TenantID = uuid.UUID
UserID = uuid.UUID
PeriodStart = datetime
PeriodEnd = datetime
