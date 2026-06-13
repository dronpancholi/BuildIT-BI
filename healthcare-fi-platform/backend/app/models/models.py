from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.db.session import Base


class UserRole(str, enum.Enum):
    CEO = "ceo"
    CFO = "cfo"
    FINANCE_MANAGER = "finance_manager"
    DEPARTMENT_HEAD = "department_head"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column('password_hash', String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), nullable=False, default="viewer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    address = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"))
    head_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch", backref="departments")


class Payer(Base):
    __tablename__ = "payers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    payer_type = Column(String(50))  # insurance, government, self-pay
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    specialization = Column(String(255))
    department_id = Column(Integer, ForeignKey("departments.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", backref="doctors")


class FinancialPeriod(Base):
    __tablename__ = "financial_periods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_closed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Revenue(Base):
    __tablename__ = "revenues"

    id = Column(Integer, primary_key=True, index=True)
    period_id = Column(Integer, ForeignKey("financial_periods.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    payer_id = Column(Integer, ForeignKey("payers.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    amount = Column(Float, nullable=False)
    net_amount = Column(Float, nullable=False)
    service_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    period = relationship("FinancialPeriod", backref="revenues")
    branch = relationship("Branch", backref="revenues")
    department = relationship("Department", backref="revenues")
    payer = relationship("Payer", backref="revenues")
    doctor = relationship("Doctor", backref="revenues")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    period_id = Column(Integer, ForeignKey("financial_periods.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    category = Column(String(100), nullable=False)  # salary, supplies, equipment, etc.
    amount = Column(Float, nullable=False)
    description = Column(Text)
    expense_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    period = relationship("FinancialPeriod", backref="expenses")
    branch = relationship("Branch", backref="expenses")
    department = relationship("Department", backref="expenses")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String(100), unique=True, nullable=False)
    patient_id = Column(String(100), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    payer_id = Column(Integer, ForeignKey("payers.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    total_amount = Column(Float, nullable=False)
    approved_amount = Column(Float)
    status = Column(String(50), nullable=False)  # submitted, approved, denied, pending
    submitted_date = Column(DateTime, nullable=False)
    resolved_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch", backref="claims")
    department = relationship("Department", backref="claims")
    payer = relationship("Payer", backref="claims")
    doctor = relationship("Doctor", backref="claims")


class Occupancy(Base):
    __tablename__ = "occupancy"

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    total_beds = Column(Integer, nullable=False)
    occupied_beds = Column(Integer, nullable=False)
    occupancy_rate = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch", backref="occupancy")
    department = relationship("Department", backref="occupancy")


class KPI(Base):
    __tablename__ = "kpis"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    category = Column(String(100), nullable=False)
    formula = Column(Text, nullable=False)
    unit = Column(String(50))
    target_value = Column(Float)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", backref="kpis")


class KPICategory(str, enum.Enum):
    REVENUE = "revenue"
    EXPENSE = "expense"
    PROFITABILITY = "profitability"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"
    OCCUPANCY = "occupancy"
    CLAIMS = "claims"
    CASH_FLOW = "cash_flow"


class KPIValue(Base):
    __tablename__ = "kpi_values"

    id = Column(Integer, primary_key=True, index=True)
    kpi_id = Column(Integer, ForeignKey("kpis.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("financial_periods.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    value = Column(Float, nullable=False)
    target_value = Column(Float)
    previous_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    kpi = relationship("KPI", backref="values")
    period = relationship("FinancialPeriod", backref="kpi_values")
    branch = relationship("Branch", backref="kpi_values")
    department = relationship("Department", backref="kpi_values")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False)  # critical, warning, info
    category = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    recommendation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    metric_type = Column(String(100), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    forecast_date = Column(DateTime, nullable=False)
    period_type = Column(String(50), nullable=False)  # daily, weekly, monthly, quarterly
    predicted_value = Column(Float, nullable=False)
    confidence_lower = Column(Float)
    confidence_upper = Column(Float)
    confidence_score = Column(Float)
    methodology = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch", backref="forecasts")
    department = relationship("Department", backref="forecasts")


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    parameters = Column(JSON, nullable=False)
    results = Column(JSON)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("User", backref="scenarios")
