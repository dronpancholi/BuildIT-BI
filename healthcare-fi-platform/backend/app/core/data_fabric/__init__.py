"""
BuildIT Canonical Data Model — Single Source of Truth.
Every module consumes these entities. No exceptions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4


# ============================================================
# ORGANIZATIONAL ENTITIES
# ============================================================

@dataclass
class Hospital:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    name: str = ""
    code: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    country: str = "IN"
    total_beds: int = 0
    available_beds: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Department:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    hospital_id: Optional[UUID] = None
    name: str = ""
    code: str = ""
    head_doctor_id: Optional[UUID] = None
    budget: Decimal = Decimal("0")
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Doctor:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    department_id: Optional[UUID] = None
    name: str = ""
    specialty: str = ""
    employment_type: str = "full_time"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Payer:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    name: str = ""
    code: str = ""
    payer_type: str = "commercial"  # commercial, government, self_pay
    reimbursement_rate: Decimal = Decimal("0")
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================
# FINANCIAL ENTITIES
# ============================================================

@dataclass
class Revenue:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    department_id: Optional[UUID] = None
    payer_id: Optional[UUID] = None
    service_date: date = field(default_factory=date.today)
    amount: Decimal = Decimal("0")
    net_amount: Decimal = Decimal("0")
    service_line: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Expense:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    department_id: Optional[UUID] = None
    category: str = ""  # labor, supplies, equipment, overhead
    amount: Decimal = Decimal("0")
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Claim:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    payer_id: Optional[UUID] = None
    claim_amount: Decimal = Decimal("0")
    paid_amount: Decimal = Decimal("0")
    status: str = "pending"  # pending, approved, denied, appealed
    submitted_date: date = field(default_factory=date.today)
    resolved_date: Optional[date] = None
    denial_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Occupancy:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    department_id: Optional[UUID] = None
    occupancy_date: date = field(default_factory=date.today)
    total_beds: int = 0
    occupied_beds: int = 0
    occupancy_rate: Decimal = Decimal("0")
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================
# INTELLIGENCE ENTITIES
# ============================================================

@dataclass
class KPI:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    name: str = ""
    code: str = ""
    category: str = ""
    unit: str = "number"
    target_value: Optional[Decimal] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Alert:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    title: str = ""
    message: str = ""
    severity: str = "medium"  # low, medium, high, critical
    category: str = ""
    source: str = ""
    is_read: bool = False
    is_resolved: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Forecast:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    metric_code: str = ""
    forecast_value: Decimal = Decimal("0")
    confidence_lower: Optional[Decimal] = None
    confidence_upper: Optional[Decimal] = None
    forecast_date: date = field(default_factory=date.today)
    model_type: str = "linear"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Decision:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    decision_type: str = ""
    category: str = ""
    status: str = "proposed"
    priority: str = "P2"
    estimated_value: Optional[Decimal] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Scenario:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    scenario_type: str = "base"
    assumptions: List[Dict[str, Any]] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Briefing:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    title: str = ""
    briefing_type: str = "daily"
    narrative: str = ""
    sections: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "draft"
    created_at: datetime = field(default_factory=datetime.utcnow)
