from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID

class UserRole(str, Enum):
    EXECUTIVE = "executive"
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

class BranchBase(BaseModel):
    name: str
    code: str

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

class DepartmentResponse(DepartmentBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RevenueBase(BaseModel):
    branch_id: int
    department_id: int
    amount: float
    net_amount: float
    service_date: datetime

class RevenueResponse(RevenueBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ExpenseBase(BaseModel):
    branch_id: int
    department_id: int
    category: str
    amount: float
    expense_date: datetime

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
    total_amount: float
    approved_amount: Optional[float] = None
    status: str
    submitted_date: datetime
    resolved_date: Optional[datetime] = None

class ClaimResponse(ClaimBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ForecastBase(BaseModel):
    metric_type: str
    forecast_date: datetime
    predicted_value: float

class ForecastResponse(ForecastBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ExecutiveSummary(BaseModel):
    total_revenue: float
    total_expenses: float
    net_profit: float
    profit_margin: float
    alerts: List[str] = []

class AIQuery(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = None

class AIResponse(BaseModel):
    answer: str
    confidence_score: float
    data: Optional[Dict[str, Any]] = None
