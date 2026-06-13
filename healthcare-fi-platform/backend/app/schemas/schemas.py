from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    CEO = "ceo"
    CFO = "cfo"
    FINANCE_MANAGER = "finance_manager"
    DEPARTMENT_HEAD = "department_head"
    ANALYST = "analyst"
    VIEWER = "viewer"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_db_row(cls, row: dict) -> "UserResponse":
        """Construct from a raw-SQL row dict (mappings())."""
        return cls(
            id=str(row["id"]),
            email=row["email"],
            full_name=row.get("full_name") or "",
            role=row["role"],
            is_active=row["is_active"],
            created_at=row["created_at"],
        )

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None


class BranchBase(BaseModel):
    name: str
    code: str
    address: Optional[str] = None


class BranchCreate(BranchBase):
    pass


class BranchResponse(BranchBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DepartmentBase(BaseModel):
    name: str
    code: str
    branch_id: int


class DepartmentCreate(DepartmentBase):
    head_id: Optional[int] = None


class DepartmentResponse(DepartmentBase):
    id: int
    head_id: Optional[int]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PayerBase(BaseModel):
    name: str
    code: str
    payer_type: str


class PayerCreate(PayerBase):
    pass


class PayerResponse(PayerBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DoctorBase(BaseModel):
    name: str
    specialization: Optional[str] = None
    department_id: int


class DoctorCreate(DoctorBase):
    pass


class DoctorResponse(DoctorBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RevenueBase(BaseModel):
    period_id: int
    branch_id: int
    department_id: int
    payer_id: int
    doctor_id: Optional[int] = None
    amount: float
    net_amount: float
    service_date: datetime


class RevenueCreate(RevenueBase):
    pass


class RevenueResponse(RevenueBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExpenseBase(BaseModel):
    period_id: int
    branch_id: int
    department_id: int
    category: str
    amount: float
    description: Optional[str] = None
    expense_date: datetime


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseResponse(ExpenseBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ClaimBase(BaseModel):
    claim_number: str
    patient_id: str
    branch_id: int
    department_id: int
    payer_id: int
    doctor_id: Optional[int] = None
    total_amount: float
    approved_amount: Optional[float] = None
    status: str
    submitted_date: datetime
    resolved_date: Optional[datetime] = None


class ClaimCreate(ClaimBase):
    pass


class ClaimResponse(ClaimBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class KPICategory(str, Enum):
    REVENUE = "revenue"
    EXPENSE = "expense"
    PROFITABILITY = "profitability"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"
    OCCUPANCY = "occupancy"
    CLAIMS = "claims"
    CASH_FLOW = "cash_flow"


class KPIBase(BaseModel):
    name: str
    code: str
    category: KPICategory
    formula: str
    unit: Optional[str] = None
    target_value: Optional[float] = None


class KPICreate(KPIBase):
    owner_id: Optional[int] = None


class KPIResponse(KPIBase):
    id: int
    owner_id: Optional[int]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class KPIValueBase(BaseModel):
    kpi_id: int
    period_id: int
    branch_id: Optional[int] = None
    department_id: Optional[int] = None
    value: float
    target_value: Optional[float] = None
    previous_value: Optional[float] = None


class KPIValueCreate(KPIValueBase):
    pass


class KPIValueResponse(KPIValueBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertBase(BaseModel):
    title: str
    message: str
    severity: AlertSeverity
    category: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    recommendation: Optional[str] = None


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: Any
    is_read: bool
    is_resolved: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ForecastBase(BaseModel):
    name: str
    metric_type: str
    branch_id: Optional[int] = None
    department_id: Optional[int] = None
    forecast_date: datetime
    period_type: str
    predicted_value: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    confidence_score: Optional[float] = None
    methodology: Optional[str] = None


class ForecastCreate(ForecastBase):
    pass


class ForecastResponse(ForecastBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any]


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioResponse(ScenarioBase):
    id: int
    created_by: int
    results: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KPITrend(BaseModel):
    current_value: float
    previous_value: Optional[float]
    change_percent: Optional[float]
    trend: str  # up, down, stable


class KPIInsight(BaseModel):
    kpi_id: int
    kpi_name: str
    category: str
    current_value: float
    target_value: Optional[float]
    trend: KPITrend
    root_cause: Optional[str]
    recommendation: Optional[str]
    confidence_score: float


class ExecutiveSummary(BaseModel):
    total_revenue: float
    total_expenses: float
    net_profit: float
    profit_margin: float
    revenue_trend: KPITrend
    expense_trend: KPITrend
    key_insights: List[KPIInsight]
    alerts: List[AlertResponse]


class AIQuery(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = None


class AIResponse(BaseModel):
    answer: str
    confidence_score: float
    data: Optional[Dict[str, Any]] = None
    visualizations: Optional[List[Dict[str, Any]]] = None
    evidence: Optional[List[str]] = None


class ForecastRequest(BaseModel):
    metric_type: str
    branch_id: Optional[int] = None
    department_id: Optional[int] = None
    periods_ahead: int = 12
    include_confidence: bool = True


class ScenarioSimulation(BaseModel):
    scenario_type: str
    parameters: Dict[str, Any]
    simulation_periods: int = 12
