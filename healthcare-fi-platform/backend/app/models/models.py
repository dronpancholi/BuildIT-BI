from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.db.session import Base

class UserRole(str, enum.Enum):
    EXECUTIVE = "executive"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    branch = relationship("Branch", backref="departments")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    patient_identifier = Column(String(100), unique=True, nullable=False)
    gender = Column(String(20))
    dob = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Revenue(Base):
    __tablename__ = "revenues"

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    amount = Column(Float, nullable=False)
    net_amount = Column(Float, nullable=False)
    service_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch", backref="revenues")
    department = relationship("Department", backref="revenues")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    expense_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch", backref="expenses")
    department = relationship("Department", backref="expenses")

class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String(100), unique=True, nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    approved_amount = Column(Float)
    status = Column(String(50), nullable=False) # submitted, approved, denied
    submitted_date = Column(DateTime, nullable=False)
    resolved_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", backref="claims")
    branch = relationship("Branch", backref="claims")
    department = relationship("Department", backref="claims")

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

class DataImport(Base):
    __tablename__ = "imports"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False) # pending, mapping, imported, failed
    imported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    records_processed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(100), nullable=False) # revenue, expense, patient_volume
    forecast_date = Column(DateTime, nullable=False)
    predicted_value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    format = Column(String(50), nullable=False) # excel, pdf, ppt
    s3_key = Column(String(255))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
