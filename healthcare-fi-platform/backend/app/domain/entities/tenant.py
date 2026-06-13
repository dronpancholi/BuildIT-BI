"""
Tenant hierarchy entities for multi-tenant isolation.
Hierarchy: Tenant → HospitalGroup → Hospital → Branch → Department
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from app.domain.entities.base import BaseEntity, TenantAwareEntity


class TenantPlan(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass(kw_only=True)
class Tenant:
    """
    Root tenant entity. Represents a healthcare organization.
    Each tenant has complete data isolation.
    """
    name: str
    slug: str  # Unique, URL-friendly identifier
    plan: TenantPlan = TenantPlan.PROFESSIONAL
    settings: Dict[str, Any] = field(default_factory=dict)
    
    entity_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    
    # Contact info
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    def __post_init__(self):
        if not self.slug:
            self.slug = self.name.lower().replace(" ", "-").replace("_", "-")


@dataclass(kw_only=True)
class HospitalGroup(TenantAwareEntity):
    """
    A group of hospitals within a tenant.
    Represents a healthcare system or network.
    """
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Contact info
    headquarters_address: Optional[str] = None
    website: Optional[str] = None
    
    is_active: bool = True


@dataclass(kw_only=True)
class Hospital(TenantAwareEntity):
    """
    A hospital entity within a group.
    """
    group_id: uuid.UUID
    name: str
    license_number: Optional[str] = None
    npi_number: Optional[str] = None  # National Provider Identifier
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Contact info
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    
    # Capacity
    total_beds: Optional[int] = None
    
    is_active: bool = True


@dataclass(kw_only=True)
class Branch(TenantAwareEntity):
    """
    A branch/location of a hospital.
    A hospital IS a branch in single-branch deployments.
    """
    hospital_id: uuid.UUID
    name: str
    code: str  # Unique within hospital
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Location
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Capacity
    total_beds: Optional[int] = None
    
    is_active: bool = True


@dataclass(kw_only=True)
class Department(TenantAwareEntity):
    """
    A department within a branch.
    """
    branch_id: uuid.UUID
    name: str
    code: str  # Unique within branch
    department_type: Optional[str] = None  # clinical, administrative, support
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Leadership
    head_id: Optional[uuid.UUID] = None  # User ID of department head
    
    # Capacity
    total_beds: Optional[int] = None
    
    is_active: bool = True


@dataclass(kw_only=True)
class User(TenantAwareEntity):
    """
    User entity with role-based access control.
    """
    email: str
    full_name: str
    hashed_password: str
    role: str = "viewer"  # CEO, CFO, finance_manager, department_head, analyst, viewer
    
    # Profile
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Settings
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    is_active: bool = True
    last_login_at: Optional[datetime] = None


@dataclass(kw_only=True)
class Payer(TenantAwareEntity):
    """
    Insurance payer entity.
    """
    name: str
    code: str  # Unique payer code
    payer_type: str  # insurance, government, self-pay
    
    # Contract details
    contract_id: Optional[str] = None
    reimbursement_rate: Optional[float] = None
    
    # Contact
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    
    settings: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


@dataclass(kw_only=True)
class Doctor(TenantAwareEntity):
    """
    Doctor/physician entity.
    """
    department_id: uuid.UUID
    name: str
    npi_number: Optional[str] = None
    specialization: Optional[str] = None
    
    # Employment
    employment_type: Optional[str] = None  # full_time, part_time, contractor
    hire_date: Optional[datetime] = None
    
    settings: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
