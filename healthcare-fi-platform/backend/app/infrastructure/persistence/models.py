"""
SQLAlchemy persistence models for the Healthcare Financial Intelligence Platform.
These map domain entities to database tables.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, Numeric, LargeBinary, Date,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint, text
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class SoftDeleteMixin:
    """Mixin for soft delete fields."""
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)
    
    @hybrid_property
    def is_deleted(self):
        return self.deleted_at is not None


class AuditMixin:
    """Mixin for audit fields."""
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    version = Column(Integer, nullable=False, default=1)


# ============================
# TENANT HIERARCHY TABLES
# ============================

class TenantModel(Base, TimestampMixin):
    """Tenant root entity."""
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    plan = Column(String(50), nullable=False, default="professional")
    settings = Column(JSON, nullable=False, default=dict)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class HospitalGroupModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Hospital group entity."""
    __tablename__ = "hospital_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    tax_id = Column(String(50), nullable=True)
    settings = Column(JSON, nullable=False, default=dict)
    headquarters_address = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    __table_args__ = (
        Index('idx_hospital_groups_tenant', 'tenant_id'),
    )


class HospitalModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Hospital entity."""
    __tablename__ = "hospitals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("hospital_groups.id"), nullable=False)
    name = Column(String(255), nullable=False)
    license_number = Column(String(100), nullable=True)
    npi_number = Column(String(20), nullable=True)
    settings = Column(JSON, nullable=False, default=dict)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    total_beds = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    group = relationship("HospitalGroupModel", backref="hospitals")
    
    __table_args__ = (
        Index('idx_hospitals_tenant', 'tenant_id'),
        Index('idx_hospitals_group', 'group_id'),
    )


class BranchModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Branch entity."""
    __tablename__ = "branches_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    settings = Column(JSON, nullable=False, default=dict)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    total_beds = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    hospital = relationship("HospitalModel", backref="branches")
    
    __table_args__ = (
        Index('idx_branches_tenant', 'tenant_id'),
        Index('idx_branches_hospital', 'hospital_id'),
        UniqueConstraint('hospital_id', 'code', name='uq_branch_hospital_code'),
    )


class DepartmentModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Department entity."""
    __tablename__ = "departments_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches_v2.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    department_type = Column(String(50), nullable=True)
    settings = Column(JSON, nullable=False, default=dict)
    head_id = Column(UUID(as_uuid=True), nullable=True)
    total_beds = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    branch = relationship("BranchModel", backref="departments")
    
    __table_args__ = (
        Index('idx_departments_tenant', 'tenant_id'),
        Index('idx_departments_branch', 'branch_id'),
        UniqueConstraint('branch_id', 'code', name='uq_department_branch_code'),
    )


class UserModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """User entity with RBAC."""
    __tablename__ = "users_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    preferences = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_users_tenant', 'tenant_id'),
        UniqueConstraint('tenant_id', 'email', name='uq_user_tenant_email'),
    )


class PayerModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Payer entity."""
    __tablename__ = "payers_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    payer_type = Column(String(50), nullable=False)
    contract_id = Column(String(100), nullable=True)
    reimbursement_rate = Column(Float, nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    settings = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    
    __table_args__ = (
        Index('idx_payers_tenant', 'tenant_id'),
        UniqueConstraint('tenant_id', 'code', name='uq_payer_tenant_code'),
    )


class DoctorModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Doctor entity."""
    __tablename__ = "doctors_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments_v2.id"), nullable=False)
    name = Column(String(255), nullable=False)
    npi_number = Column(String(20), nullable=True)
    specialization = Column(String(255), nullable=True)
    employment_type = Column(String(50), nullable=True)
    hire_date = Column(DateTime, nullable=True)
    settings = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    
    department = relationship("DepartmentModel", backref="doctors")
    
    __table_args__ = (
        Index('idx_doctors_tenant', 'tenant_id'),
        Index('idx_doctors_department', 'department_id'),
    )


# ============================
# METRIC DEFINITION TABLES
# ============================

class MetricDefinitionModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """MetricDefinition entity."""
    __tablename__ = "metric_definitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Identity
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    
    # Governance
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(100), nullable=True)
    
    # Definition
    description = Column(Text, nullable=True)
    formula = Column(Text, nullable=True)
    sql_expression = Column(Text, nullable=True)
    python_expression = Column(Text, nullable=True)
    
    # Metric properties
    unit = Column(String(50), nullable=False)
    aggregation = Column(String(50), nullable=False)
    direction = Column(Integer, nullable=False, default=1)
    
    # Validation
    validation_rules = Column(JSON, nullable=False, default=list)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    
    # Dependencies
    depends_on = Column(JSON, nullable=False, default=list)
    
    # Versioning
    status = Column(String(50), nullable=False, default="draft")
    published_at = Column(DateTime, nullable=True)
    deprecated_at = Column(DateTime, nullable=True)
    deprecation_reason = Column(Text, nullable=True)
    
    # Lineage
    source_tables = Column(JSON, nullable=False, default=list)
    source_fields = Column(JSON, nullable=False, default=list)
    transformation_steps = Column(JSON, nullable=False, default=list)
    
    # Trust signals
    quality_score = Column(Float, nullable=False, default=0.0)
    trust_level = Column(String(50), nullable=False, default="experimental")
    certified_by = Column(UUID(as_uuid=True), nullable=True)
    certified_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_metric_definitions_tenant', 'tenant_id'),
        UniqueConstraint('tenant_id', 'slug', name='uq_metric_def_tenant_slug'),
        UniqueConstraint('tenant_id', 'code', name='uq_metric_def_tenant_code'),
    )


class MetricComputedValueModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """MetricComputedValue entity."""
    __tablename__ = "metric_computed_values"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Definition reference
    metric_id = Column(UUID(as_uuid=True), ForeignKey("metric_definitions.id"), nullable=False)
    metric_version = Column(Integer, nullable=False)
    
    # Computation context
    computed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    computed_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Scope
    hospital_id = Column(UUID(as_uuid=True), nullable=True)
    branch_id = Column(UUID(as_uuid=True), nullable=True)
    department_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Time window
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(50), nullable=False)
    
    # Result
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    
    # Confidence and quality
    confidence_score = Column(Float, nullable=False, default=0.0)
    quality_score = Column(Float, nullable=False, default=0.0)
    sample_size = Column(Integer, nullable=False, default=0)
    null_values_excluded = Column(Integer, nullable=False, default=0)
    
    # For comparison
    previous_value = Column(Float, nullable=True)
    previous_period_start = Column(DateTime, nullable=True)
    previous_period_end = Column(DateTime, nullable=True)
    change_absolute = Column(Float, nullable=True)
    change_percent = Column(Float, nullable=True)
    trend = Column(String(20), nullable=False, default="stable")
    
    # Provenance
    computation_duration_ms = Column(Integer, nullable=False, default=0)
    cache_hit = Column(Boolean, nullable=False, default=False)
    source_query_hash = Column(String(64), nullable=True)
    
    # Lineage snapshot
    lineage_snapshot = Column(JSON, nullable=False, default=dict)
    
    metric = relationship("MetricDefinitionModel", backref="computed_values")
    
    __table_args__ = (
        Index('idx_metric_computed_values_tenant', 'tenant_id'),
        Index('idx_metric_computed_values_metric', 'metric_id'),
        Index('idx_metric_computed_values_period', 'period_start', 'period_end'),
    )


# ============================
# QUALITY TABLES
# ============================

class QualityRuleModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """QualityRule entity."""
    __tablename__ = "quality_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    entity_type = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False)
    
    # Configuration
    configuration = Column(JSON, nullable=False, default=dict)
    severity = Column(String(50), nullable=False, default="medium")
    scope = Column(String(50), nullable=False, default="column")
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    alert_on_failure = Column(Boolean, nullable=False, default=True)
    alert_channels = Column(JSON, nullable=False, default=list)
    
    # Thresholds
    threshold = Column(Float, nullable=True)
    sample_size = Column(Integer, nullable=True)
    
    # Scope filtering
    applies_to_hospital_id = Column(UUID(as_uuid=True), nullable=True)
    applies_to_branch_id = Column(UUID(as_uuid=True), nullable=True)
    applies_to_period = Column(String(50), nullable=True)
    
    __table_args__ = (
        Index('idx_quality_rules_tenant', 'tenant_id'),
    )


class QualityIssueModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """QualityIssue entity."""
    __tablename__ = "quality_issues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Issue identification
    rule_id = Column(UUID(as_uuid=True), ForeignKey("quality_rules.id"), nullable=False)
    rule_name = Column(String(255), nullable=True)
    
    # Severity and status
    severity = Column(String(50), nullable=False, default="medium")
    status = Column(String(50), nullable=False, default="open")
    priority = Column(Integer, nullable=False, default=3)
    
    # Context
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    field_name = Column(String(255), nullable=True)
    hospital_id = Column(UUID(as_uuid=True), nullable=True)
    branch_id = Column(UUID(as_uuid=True), nullable=True)
    department_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Issue details
    issue_code = Column(String(50), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    detected_value = Column(Text, nullable=True)  # JSON serialized
    expected_value = Column(Text, nullable=True)  # JSON serialized
    deviation = Column(Float, nullable=True)
    z_score = Column(Float, nullable=True)
    
    # Time context
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    # Resolution
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Recommendation
    recommended_action = Column(Text, nullable=True)
    estimated_effort = Column(String(100), nullable=True)
    
    # Audit trail
    history = Column(JSON, nullable=False, default=list)
    
    rule = relationship("QualityRuleModel", backref="issues")
    
    __table_args__ = (
        Index('idx_quality_issues_tenant', 'tenant_id'),
        Index('idx_quality_issues_severity', 'severity'),
        Index('idx_quality_issues_status', 'status'),
    )


class DataQualityScoreModel(Base, TimestampMixin, AuditMixin):
    """DataQualityScore entity."""
    __tablename__ = "data_quality_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Scope
    scope_type = Column(String(50), nullable=False)
    scope_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Time
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(50), nullable=False)
    
    # Scores (all 0.0-1.0)
    overall_score = Column(Float, nullable=False, default=0.0)
    completeness_score = Column(Float, nullable=False, default=0.0)
    validity_score = Column(Float, nullable=False, default=0.0)
    consistency_score = Column(Float, nullable=False, default=0.0)
    timeliness_score = Column(Float, nullable=False, default=0.0)
    uniqueness_score = Column(Float, nullable=False, default=0.0)
    
    # Issue counts by severity
    critical_issues = Column(Integer, nullable=False, default=0)
    high_issues = Column(Integer, nullable=False, default=0)
    medium_issues = Column(Integer, nullable=False, default=0)
    low_issues = Column(Integer, nullable=False, default=0)
    info_issues = Column(Integer, nullable=False, default=0)
    
    # Trend
    previous_score = Column(Float, nullable=True)
    score_change = Column(Float, nullable=True)
    score_change_percent = Column(Float, nullable=True)
    
    # Audit
    computed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_data_quality_scores_tenant', 'tenant_id'),
        Index('idx_data_quality_scores_scope', 'scope_type', 'scope_id'),
    )


# ============================
# LINEAGE TABLES
# ============================

class LineageNodeModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """LineageNode entity."""
    __tablename__ = "lineage_nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Node identity
    node_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    qualified_name = Column(String(500), nullable=False)
    
    # Node details
    node_subtype = Column(String(100), nullable=True)
    
    # For SOURCE nodes
    source_system = Column(String(100), nullable=True)
    source_id = Column(String(255), nullable=True)
    
    # For TRANSFORM nodes
    transform_type = Column(String(50), nullable=True)
    transform_logic = Column(Text, nullable=True)
    transform_order = Column(Integer, nullable=True)
    
    # For METRIC nodes
    metric_id = Column(UUID(as_uuid=True), nullable=True)
    computation_context = Column(JSON, nullable=True)
    
    # Graph metadata
    description = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_lineage_nodes_tenant', 'tenant_id'),
        Index('idx_lineage_nodes_type', 'node_type'),
        UniqueConstraint('tenant_id', 'qualified_name', name='uq_lineage_node_tenantQualifiedName'),
    )


class LineageEdgeModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """LineageEdge entity."""
    __tablename__ = "lineage_edges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Edge identity
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("lineage_nodes.id"), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("lineage_nodes.id"), nullable=False)
    
    # Edge metadata
    edge_type = Column(String(50), nullable=False, default="direct")
    dependency_type = Column(String(100), nullable=True)
    
    # Field-level lineage
    source_field = Column(String(500), nullable=True)
    target_field = Column(String(500), nullable=True)
    
    # Propagation
    is_active = Column(Boolean, nullable=False, default=True)
    deprecated_at = Column(DateTime, nullable=True)
    
    source_node = relationship("LineageNodeModel", foreign_keys=[source_node_id], backref="outgoing_edges")
    target_node = relationship("LineageNodeModel", foreign_keys=[target_node_id], backref="incoming_edges")
    
    __table_args__ = (
        Index('idx_lineage_edges_tenant', 'tenant_id'),
        Index('idx_lineage_edges_source', 'source_node_id'),
        Index('idx_lineage_edges_target', 'target_node_id'),
    )


class LineageComputationRecordModel(Base, TimestampMixin, AuditMixin):
    """LineageComputationRecord entity."""
    __tablename__ = "lineage_computation_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Computation context
    computation_id = Column(UUID(as_uuid=True), nullable=False)
    metric_id = Column(UUID(as_uuid=True), nullable=True)
    computed_value_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Time
    computed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Execution details
    executed_by = Column(UUID(as_uuid=True), nullable=True)
    execution_type = Column(String(50), nullable=False, default="scheduled")
    duration_ms = Column(Integer, nullable=False, default=0)
    
    # Lineage snapshot
    lineage_snapshot = Column(JSON, nullable=False, default=dict)
    
    # Source records affected
    source_record_count = Column(Integer, nullable=False, default=0)
    source_records_sample = Column(JSON, nullable=False, default=list)
    
    # Transformation steps
    transformation_log = Column(JSON, nullable=False, default=list)
    
    # Result
    input_record_count = Column(Integer, nullable=False, default=0)
    output_record_count = Column(Integer, nullable=False, default=0)
    null_values_excluded = Column(Integer, nullable=False, default=0)
    duplicates_removed = Column(Integer, nullable=False, default=0)
    
    __table_args__ = (
        Index('idx_lineage_computation_records_tenant', 'tenant_id'),
        Index('idx_lineage_computation_records_computation', 'computation_id'),
    )


# ============================
# DOMAIN EVENT TABLES
# ============================

class DomainEventModel(Base, TimestampMixin):
    """DomainEvent entity - immutable event log."""
    __tablename__ = "domain_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Event taxonomy
    event_type = Column(String(100), nullable=False)
    event_version = Column(String(20), nullable=False, default="1.0")
    
    # Causality
    correlation_id = Column(UUID(as_uuid=True), nullable=False)
    causation_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Actor
    initiated_by = Column(UUID(as_uuid=True), nullable=True)
    initiated_by_type = Column(String(50), nullable=False, default="system")
    
    # Scope
    hospital_id = Column(UUID(as_uuid=True), nullable=True)
    branch_id = Column(UUID(as_uuid=True), nullable=True)
    department_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Payload
    payload = Column(JSON, nullable=False, default=dict)
    
    # Metadata
    event_metadata = Column(JSON, nullable=False, default=dict)
    
    __table_args__ = (
        Index('idx_domain_events_tenant', 'tenant_id'),
        Index('idx_domain_events_type', 'event_type'),
        Index('idx_domain_events_occurred', 'occurred_at'),
        Index('idx_domain_events_correlation', 'correlation_id'),
    )


# ============================
# OUTBOX TABLE
# ============================

class OutboxMessageModel(Base):
    """Outbox message for guaranteed event delivery."""
    __tablename__ = "outbox_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type = Column(String(100), nullable=False)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    status = Column(String(50), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_outbox_messages_status', 'status'),
        Index('idx_outbox_messages_created', 'created_at'),
    )


# ============================
# AUDIT LOG TABLE
# ============================

class AuditLogModel(Base):
    """Immutable audit log entry."""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # When
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Who
    actor_type = Column(String(50), nullable=False)
    actor_id = Column(UUID(as_uuid=True), nullable=True)
    actor_email = Column(String(255), nullable=True)
    
    # What
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_name = Column(String(255), nullable=True)
    
    # Change details
    change_type = Column(String(50), nullable=False)
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    # Context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True)
    workflow_id = Column(String(100), nullable=True)
    
    # Result
    success = Column(Boolean, nullable=False, default=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_audit_logs_tenant', 'tenant_id'),
        Index('idx_audit_logs_actor', 'actor_id'),
        Index('idx_audit_logs_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_logs_occurred', 'occurred_at'),
    )


# ============================
# FINANCIAL DATA TABLES (Existing, Updated)
# ============================

class FinancialPeriodModel(Base, TimestampMixin):
    """Financial period entity."""
    __tablename__ = "financial_periods"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_closed = Column(Boolean, nullable=False, default=False)
    
    __table_args__ = (
        Index('idx_financial_periods_tenant', 'tenant_id'),
    )


class RevenueModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Revenue entity."""
    __tablename__ = "revenues_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    period_id = Column(UUID(as_uuid=True), ForeignKey("financial_periods.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches_v2.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments_v2.id"), nullable=False)
    payer_id = Column(UUID(as_uuid=True), ForeignKey("payers_v2.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors_v2.id"), nullable=True)
    amount = Column(Float, nullable=False)
    net_amount = Column(Float, nullable=False)
    service_date = Column(DateTime, nullable=False)
    
    period = relationship("FinancialPeriodModel", backref="revenues")
    branch = relationship("BranchModel", backref="revenues")
    department = relationship("DepartmentModel", backref="revenues")
    payer = relationship("PayerModel", backref="revenues")
    doctor = relationship("DoctorModel", backref="revenues")
    
    __table_args__ = (
        Index('idx_revenues_tenant', 'tenant_id'),
        Index('idx_revenues_period', 'period_id'),
        Index('idx_revenues_branch', 'branch_id'),
        Index('idx_revenues_department', 'department_id'),
        Index('idx_revenues_service_date', 'service_date'),
    )


class ExpenseModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Expense entity."""
    __tablename__ = "expenses_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    period_id = Column(UUID(as_uuid=True), ForeignKey("financial_periods.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches_v2.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments_v2.id"), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    expense_date = Column(DateTime, nullable=False)
    
    period = relationship("FinancialPeriodModel", backref="expenses")
    branch = relationship("BranchModel", backref="expenses")
    department = relationship("DepartmentModel", backref="expenses")
    
    __table_args__ = (
        Index('idx_expenses_tenant', 'tenant_id'),
        Index('idx_expenses_period', 'period_id'),
        Index('idx_expenses_branch', 'branch_id'),
        Index('idx_expenses_department', 'department_id'),
    )


class ClaimModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Claim entity."""
    __tablename__ = "claims_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    claim_number = Column(String(100), nullable=False)
    patient_id = Column(String(100), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches_v2.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments_v2.id"), nullable=False)
    payer_id = Column(UUID(as_uuid=True), ForeignKey("payers_v2.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors_v2.id"), nullable=True)
    total_amount = Column(Float, nullable=False)
    approved_amount = Column(Float, nullable=True)
    status = Column(String(50), nullable=False)
    submitted_date = Column(DateTime, nullable=False)
    resolved_date = Column(DateTime, nullable=True)
    
    branch = relationship("BranchModel", backref="claims")
    department = relationship("DepartmentModel", backref="claims")
    payer = relationship("PayerModel", backref="claims")
    doctor = relationship("DoctorModel", backref="claims")
    
    __table_args__ = (
        Index('idx_claims_tenant', 'tenant_id'),
        Index('idx_claims_branch', 'branch_id'),
        Index('idx_claims_department', 'department_id'),
        Index('idx_claims_status', 'status'),
        UniqueConstraint('tenant_id', 'claim_number', name='uq_claim_tenant_number'),
    )


class OccupancyModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Occupancy entity."""
    __tablename__ = "occupancy_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches_v2.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments_v2.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    total_beds = Column(Integer, nullable=False)
    occupied_beds = Column(Integer, nullable=False)
    occupancy_rate = Column(Float, nullable=False)
    
    branch = relationship("BranchModel", backref="occupancy")
    department = relationship("DepartmentModel", backref="occupancy")
    
    __table_args__ = (
        Index('idx_occupancy_tenant', 'tenant_id'),
        Index('idx_occupancy_branch', 'branch_id'),
        Index('idx_occupancy_date', 'date'),
    )


# ============================
# INTELLIGENCE ENGINE TABLES
# ============================


class IntelligenceInsightModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Intelligence Insight artifact."""
    __tablename__ = "intelligence_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    insight_type = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    detailed_analysis = Column(Text, nullable=True)

    pattern_type = Column(String(50), nullable=True)
    pattern_detected = Column(JSON, nullable=True)
    statistical_properties = Column(JSON, nullable=True)

    statistical_test = Column(String(100), nullable=True)
    test_statistic = Column(Float, nullable=True)
    p_value = Column(Float, nullable=True)
    p_value_corrected = Column(Float, nullable=True)
    is_significant = Column(Boolean, nullable=False, default=False)
    confidence_level = Column(Float, nullable=True)
    effect_size = Column(Float, nullable=True)

    magnitude = Column(Float, nullable=True)
    magnitude_unit = Column(String(20), nullable=True)
    relative_magnitude = Column(Float, nullable=True)

    previous_insight_id = Column(UUID(as_uuid=True), nullable=True)
    next_insight_id = Column(UUID(as_uuid=True), nullable=True)
    insight_sequence = Column(Integer, nullable=False, default=1)

    comparison_period_start = Column(DateTime(timezone=True), nullable=True)
    comparison_period_end = Column(DateTime(timezone=True), nullable=True)
    comparison_value = Column(Float, nullable=True)
    comparison_change_absolute = Column(Float, nullable=True)
    comparison_change_percent = Column(Float, nullable=True)

    related_metric_ids = Column(JSON, nullable=False, default=list)
    related_root_cause_ids = Column(JSON, nullable=False, default=list)
    related_anomaly_ids = Column(JSON, nullable=False, default=list)
    related_opportunity_ids = Column(JSON, nullable=False, default=list)
    related_recommendation_ids = Column(JSON, nullable=False, default=list)

    scores = Column(JSON, nullable=False)

    discovery_method = Column(String(50), nullable=True)
    triggered_by_event = Column(String(100), nullable=True)

    status = Column(String(20), nullable=False, default="discovered", index=True)
    is_notified = Column(Boolean, nullable=False, default=False)
    notified_at = Column(DateTime(timezone=True), nullable=True)
    notification_channel = Column(String(50), nullable=True)

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=True)
    scope_type = Column(String(20), nullable=True)
    scope_id = Column(UUID(as_uuid=True), nullable=True)
    scope_name = Column(String(200), nullable=True)

    metric_id = Column(UUID(as_uuid=True), nullable=True)
    metric_code = Column(String(50), nullable=True)

    generated_by = Column(String(50), nullable=True)
    generated_by_model = Column(String(100), nullable=True)
    generation_method = Column(String(50), nullable=True)

    __table_args__ = (
        Index('idx_insights_tenant', 'tenant_id'),
        Index('idx_insights_scope', 'scope_type', 'scope_id'),
        Index('idx_insights_period', 'period_start', 'period_end'),
    )


class IntelligenceRootCauseModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Intelligence Root Cause artifact."""
    __tablename__ = "intelligence_root_causes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    subject_metric_id = Column(UUID(as_uuid=True), nullable=True)
    subject_metric_code = Column(String(50), nullable=True)
    subject_previous_value = Column(Float, nullable=True)
    subject_current_value = Column(Float, nullable=True)
    subject_change_absolute = Column(Float, nullable=True)
    subject_change_percent = Column(Float, nullable=True)

    cause_type = Column(String(50), nullable=False)
    cause_category = Column(String(100), nullable=True)
    cause_name = Column(String(500), nullable=False)
    cause_description = Column(Text, nullable=True)

    attribution_weight = Column(Float, nullable=True)
    attribution_absolute = Column(Float, nullable=True)
    attribution_percent = Column(Float, nullable=True)
    is_primary_cause = Column(Boolean, nullable=False, default=False)
    cause_rank = Column(Integer, nullable=True)

    statistical_significance = Column(Float, nullable=True)
    confidence_interval = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)

    cause_evidence = Column(JSON, nullable=False, default=list)
    breakdown = Column(JSON, nullable=False, default=list)

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    comparison_period_start = Column(DateTime(timezone=True), nullable=True)
    comparison_period_end = Column(DateTime(timezone=True), nullable=True)

    scope_type = Column(String(20), nullable=True)
    scope_id = Column(UUID(as_uuid=True), nullable=True)
    scope_name = Column(String(200), nullable=True)

    related_insight_id = Column(UUID(as_uuid=True), nullable=True)
    related_anomaly_id = Column(UUID(as_uuid=True), nullable=True)
    related_recommendation_ids = Column(JSON, nullable=False, default=list)

    scores = Column(JSON, nullable=False)

    status = Column(String(20), nullable=False, default="discovered", index=True)

    __table_args__ = (
        Index('idx_root_causes_tenant', 'tenant_id'),
        Index('idx_root_causes_metric', 'subject_metric_id'),
        Index('idx_root_causes_period', 'period_start', 'period_end'),
    )


class IntelligenceAnomalyModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Intelligence Anomaly artifact."""
    __tablename__ = "intelligence_anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    anomaly_type = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=True)
    severity = Column(String(20), nullable=False, index=True)

    detection_method = Column(String(50), nullable=True)
    detection_algorithm = Column(String(100), nullable=True)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    detailed_explanation = Column(Text, nullable=True)

    metric_id = Column(UUID(as_uuid=True), nullable=True)
    metric_code = Column(String(50), nullable=True)

    observed_value = Column(Float, nullable=True)
    expected_value = Column(Float, nullable=True)
    deviation_absolute = Column(Float, nullable=True)
    deviation_percent = Column(Float, nullable=True)

    z_score = Column(Float, nullable=True)
    p_value = Column(Float, nullable=True)
    confidence_interval = Column(JSON, nullable=True)

    baseline_value = Column(Float, nullable=True)
    baseline_type = Column(String(50), nullable=True)
    baseline_period_start = Column(DateTime(timezone=True), nullable=True)
    baseline_period_end = Column(DateTime(timezone=True), nullable=True)
    baseline_std_dev = Column(Float, nullable=True)

    root_cause_id = Column(UUID(as_uuid=True), nullable=True)
    root_cause_description = Column(Text, nullable=True)

    business_impact = Column(JSON, nullable=True)
    impact_amount = Column(Float, nullable=True)
    affected_transactions = Column(Integer, nullable=True)
    affected_scope = Column(String(500), nullable=True)

    recommendation_id = Column(UUID(as_uuid=True), nullable=True)
    recommended_action = Column(Text, nullable=True)

    anomaly_duration_periods = Column(Integer, nullable=False, default=1)
    is_persistent = Column(Boolean, nullable=False, default=False)

    anomaly_status = Column(String(20), nullable=False, default="detected", index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    related_insight_ids = Column(JSON, nullable=False, default=list)
    related_root_cause_ids = Column(JSON, nullable=False, default=list)

    scores = Column(JSON, nullable=False)

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=True)
    scope_type = Column(String(20), nullable=True)
    scope_id = Column(UUID(as_uuid=True), nullable=True)
    scope_name = Column(String(200), nullable=True)

    status = Column(String(20), nullable=False, default="discovered")

    __table_args__ = (
        Index('idx_anomalies_tenant', 'tenant_id'),
        Index('idx_anomalies_metric', 'metric_id'),
        Index('idx_anomalies_period', 'period_start', 'period_end'),
    )


class IntelligenceOpportunityModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Intelligence Opportunity artifact."""
    __tablename__ = "intelligence_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    opportunity_type = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=True)
    subcategory = Column(String(100), nullable=True)

    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    detailed_description = Column(Text, nullable=True)

    estimated_value = Column(Float, nullable=True)
    value_unit = Column(String(20), nullable=True)
    value_range_low = Column(Float, nullable=True)
    value_range_high = Column(Float, nullable=True)
    value_confidence = Column(Float, nullable=True)

    value_breakdown = Column(JSON, nullable=True)
    baseline_metric_id = Column(UUID(as_uuid=True), nullable=True)
    baseline_value = Column(Float, nullable=True)
    target_value = Column(Float, nullable=True)
    improvement_potential = Column(Float, nullable=True)

    effort_level = Column(String(20), nullable=True)
    risk_level = Column(String(20), nullable=True)
    implementation_effort_hours = Column(Float, nullable=True)
    time_to_realize_months = Column(Float, nullable=True)
    roi = Column(Float, nullable=True)
    roi_rank = Column(Integer, nullable=True)

    prerequisites = Column(JSON, nullable=False, default=list)
    dependencies_on_opportunities = Column(JSON, nullable=False, default=list)
    blocks_opportunities = Column(JSON, nullable=False, default=list)

    recommended_actions = Column(JSON, nullable=False, default=list)
    success_criteria = Column(JSON, nullable=False, default=list)
    failure_risks = Column(JSON, nullable=False, default=list)

    suggested_owner_id = Column(UUID(as_uuid=True), nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    owner_name = Column(String(200), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)

    opportunity_status = Column(String(20), nullable=False, default="identified", index=True)
    realized_value = Column(Float, nullable=True)
    realized_at = Column(DateTime(timezone=True), nullable=True)
    realized_notes = Column(Text, nullable=True)

    discovery_method = Column(String(50), nullable=True)
    source_opportunity_id = Column(UUID(as_uuid=True), nullable=True)
    related_metric_ids = Column(JSON, nullable=False, default=list)
    related_insight_ids = Column(JSON, nullable=False, default=list)
    related_recommendation_ids = Column(JSON, nullable=False, default=list)

    scores = Column(JSON, nullable=False)

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=True)
    scope_type = Column(String(20), nullable=True)
    scope_id = Column(UUID(as_uuid=True), nullable=True)
    scope_name = Column(String(200), nullable=True)

    status = Column(String(20), nullable=False, default="discovered")

    __table_args__ = (
        Index('idx_opportunities_tenant', 'tenant_id'),
        Index('idx_opportunities_value', 'estimated_value'),
        Index('idx_opportunities_period', 'period_start', 'period_end'),
    )


class IntelligenceRecommendationModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Intelligence Recommendation artifact."""
    __tablename__ = "intelligence_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    recommendation_type = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=True)

    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    detailed_recommendation = Column(Text, nullable=True)

    evidence_chain = Column(JSON, nullable=False, default=list)
    supporting_insight_ids = Column(JSON, nullable=False, default=list)
    supporting_anomaly_ids = Column(JSON, nullable=False, default=list)
    supporting_root_cause_ids = Column(JSON, nullable=False, default=list)
    supporting_opportunity_ids = Column(JSON, nullable=False, default=list)

    expected_impact_value = Column(Float, nullable=True)
    expected_impact_unit = Column(String(20), nullable=True)
    impact_direction = Column(String(50), nullable=True)
    confidence_in_impact = Column(Float, nullable=True)
    impact_calculation = Column(Text, nullable=True)

    recommended_actions = Column(JSON, nullable=False, default=list)
    estimated_effort_hours = Column(Float, nullable=True)
    time_to_implement_months = Column(Float, nullable=True)
    success_metrics = Column(JSON, nullable=False, default=list)
    failure_risks = Column(JSON, nullable=False, default=list)

    priority_score = Column(Float, nullable=True)
    priority_rank = Column(Integer, nullable=True)
    priority_rationale = Column(Text, nullable=True)

    recommendation_status = Column(String(20), nullable=False, default="proposed", index=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    implemented_by = Column(UUID(as_uuid=True), nullable=True)
    implemented_at = Column(DateTime(timezone=True), nullable=True)
    implementation_result = Column(Text, nullable=True)
    actual_vs_expected_impact = Column(Float, nullable=True)

    assigned_to_id = Column(UUID(as_uuid=True), nullable=True)
    assigned_to_name = Column(String(200), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)

    generation_method = Column(String(50), nullable=True)
    generated_by_model = Column(String(100), nullable=True)

    scores = Column(JSON, nullable=False)

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=True)
    scope_type = Column(String(20), nullable=True)
    scope_id = Column(UUID(as_uuid=True), nullable=True)
    scope_name = Column(String(200), nullable=True)

    status = Column(String(20), nullable=False, default="discovered")

    __table_args__ = (
        Index('idx_recommendations_tenant', 'tenant_id'),
        Index('idx_recommendations_priority', 'priority_score'),
        Index('idx_recommendations_period', 'period_start', 'period_end'),
    )


class IntelligenceBriefingModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Intelligence Briefing artifact."""
    __tablename__ = "intelligence_briefings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    briefing_type = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=True)

    comparison_period_start = Column(DateTime(timezone=True), nullable=True)
    comparison_period_end = Column(DateTime(timezone=True), nullable=True)

    recipient_ids = Column(JSON, nullable=False, default=list)
    recipient_emails = Column(JSON, nullable=False, default=list)
    recipient_roles = Column(JSON, nullable=False, default=list)

    sections = Column(JSON, nullable=False, default=list)
    executive_summary = Column(JSON, nullable=True)
    key_highlights = Column(JSON, nullable=False, default=list)
    metrics_snapshot = Column(JSON, nullable=False, default=list)
    narrative = Column(Text, nullable=True)

    attachment_urls = Column(JSON, nullable=False, default=list)

    briefing_status = Column(String(20), nullable=False, default="draft", index=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    finalized_by = Column(UUID(as_uuid=True), nullable=True)

    distributed_at = Column(DateTime(timezone=True), nullable=True)
    distribution_channels = Column(JSON, nullable=False, default=list)

    is_update = Column(Boolean, nullable=False, default=False)
    previous_briefing_id = Column(UUID(as_uuid=True), nullable=True)

    generation_method = Column(String(50), nullable=True)
    generation_duration_ms = Column(Integer, nullable=True)
    generation_prompts = Column(JSON, nullable=False, default=list)

    scores = Column(JSON, nullable=True)

    scope_type = Column(String(20), nullable=True)
    scope_id = Column(UUID(as_uuid=True), nullable=True)
    scope_name = Column(String(200), nullable=True)

    status = Column(String(20), nullable=False, default="discovered")

    __table_args__ = (
        Index('idx_briefings_tenant', 'tenant_id'),
        Index('idx_briefings_period', 'period_start', 'period_end'),
    )


class IntelligenceGraphNodeModel(Base, TimestampMixin, AuditMixin):
    """Intelligence Graph Node."""
    __tablename__ = "intelligence_graph_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    node_type = Column(String(50), nullable=False, index=True)
    node_subtype = Column(String(100), nullable=True)

    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)

    label = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    primary_value = Column(Float, nullable=True)

    importance_score = Column(Float, nullable=False, default=0)
    influence_score = Column(Float, nullable=False, default=0)

    first_observed_at = Column(DateTime(timezone=True), nullable=True)
    last_observed_at = Column(DateTime(timezone=True), nullable=True)
    observation_count = Column(Integer, nullable=False, default=1)

    status = Column(String(20), nullable=False, default="active", index=True)
    merged_into_id = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index('idx_graph_nodes_tenant', 'tenant_id'),
        Index('idx_graph_nodes_entity', 'entity_type', 'entity_id'),
    )


class IntelligenceRelationshipModel(Base, TimestampMixin, AuditMixin):
    """Intelligence Relationship edge."""
    __tablename__ = "intelligence_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    source_node_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    target_node_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    relationship_type = Column(String(50), nullable=False, index=True)
    relationship_subtype = Column(String(100), nullable=True)

    correlation_strength = Column(Float, nullable=False, default=0)
    causal_strength = Column(Float, nullable=True)
    confidence = Column(Float, nullable=False, default=0)

    context = Column(Text, nullable=True)
    evidence_count = Column(Integer, nullable=False, default=0)

    first_observed_at = Column(DateTime(timezone=True), nullable=True)
    last_observed_at = Column(DateTime(timezone=True), nullable=True)
    is_historical = Column(Boolean, nullable=False, default=False)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_relationships_tenant', 'tenant_id'),
        Index('idx_relationships_source', 'source_node_id'),
        Index('idx_relationships_target', 'target_node_id'),
    )


# ============================
# DECISION INTELLIGENCE TABLES (Phase 3.5)
# ============================

class DecisionModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Decision entity ORM model."""
    __tablename__ = "decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    decision_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, server_default="proposed")
    priority = Column(String(10), nullable=False, server_default="P2")
    urgency = Column(String(20), nullable=False, server_default="scheduled")

    trigger_type = Column(String(50), nullable=True)
    trigger_id = Column(UUID(as_uuid=True), nullable=True)
    trigger_summary = Column(Text, nullable=True)

    category = Column(String(50), nullable=False, server_default="operational")
    department_ids = Column(JSON, nullable=False, server_default="[]")
    scope_type = Column(String(50), nullable=False, server_default="tenant")
    scope_id = Column(UUID(as_uuid=True), nullable=True)

    estimated_value = Column(Float, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    currency = Column(String(10), nullable=False, server_default="INR")

    review_deadline = Column(DateTime(timezone=True), nullable=True)
    approval_deadline = Column(DateTime(timezone=True), nullable=True)
    implementation_target_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime(timezone=True), nullable=True)

    proposed_by = Column(UUID(as_uuid=True), nullable=True)
    proposed_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    reviewed_by = Column(JSON, nullable=False, server_default="[]")
    approved_by = Column(JSON, nullable=False, server_default="[]")
    rejected_by = Column(UUID(as_uuid=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    implemented_by = Column(UUID(as_uuid=True), nullable=True)

    outcome_id = Column(UUID(as_uuid=True), nullable=True)

    tags = Column(JSON, nullable=False, server_default="[]")
    metadata_ = Column("metadata", JSON, nullable=False, server_default="{}")

    __table_args__ = (
        Index('ix_decisions_tenant_id', 'tenant_id'),
        Index('ix_decisions_status', 'tenant_id', 'status'),
        Index('ix_decisions_type', 'tenant_id', 'decision_type'),
        Index('ix_decisions_category', 'tenant_id', 'category'),
        Index('ix_decisions_created_at', 'tenant_id', 'created_at'),
    )


class DecisionEvidenceModel(Base):
    """Decision evidence ORM model."""
    __tablename__ = "decision_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False, index=True)

    evidence_type = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    weight = Column(Float, nullable=False, server_default="1.0")
    source_type = Column(String(50), nullable=True)
    source_id = Column(UUID(as_uuid=True), nullable=True)
    source_metric_code = Column(String(100), nullable=True)
    data_payload = Column(JSON, nullable=False, server_default="{}")

    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class DecisionOutcomeModel(Base, TimestampMixin):
    """Decision outcome ORM model."""
    __tablename__ = "decision_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id"), nullable=False, index=True)

    measurement_start = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    measurement_end = Column(DateTime(timezone=True), nullable=True)

    expected_metrics = Column(JSON, nullable=False, server_default="[]")
    actual_metrics = Column(JSON, nullable=False, server_default="[]")

    accuracy_score = Column(Float, nullable=False, server_default="0")
    variance_absolute = Column(Float, nullable=False, server_default="0")
    variance_percent = Column(Float, nullable=False, server_default="0")
    outcome_status = Column(String(50), nullable=False, server_default="inconclusive")

    causal_impact = Column(JSON, nullable=True)

    realized_value = Column(Float, nullable=False, server_default="0")
    roi_actual = Column(Float, nullable=True)

    measured_by = Column(UUID(as_uuid=True), nullable=True)
    measured_at = Column(DateTime(timezone=True), nullable=True)

    version = Column(Integer, nullable=False, server_default="1")


class DecisionReviewModel(Base, TimestampMixin):
    """Decision review ORM model."""
    __tablename__ = "decision_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False, index=True)

    review_type = Column(String(50), nullable=False, server_default="initial_review")
    review_round = Column(Integer, nullable=False, server_default="1")
    status = Column(String(50), nullable=False, server_default="pending")

    reviewer_id = Column(UUID(as_uuid=True), nullable=True)
    reviewer_role = Column(String(100), nullable=True)
    review_decision = Column(String(50), nullable=True)

    comments = Column(JSON, nullable=False, server_default="[]")
    conditions = Column(JSON, nullable=True)
    escalation_required = Column(Boolean, nullable=False, server_default="false")
    escalation_to = Column(UUID(as_uuid=True), nullable=True)

    decided_at = Column(DateTime(timezone=True), nullable=True)

    version = Column(Integer, nullable=False, server_default="1")


class DecisionTimelineModel(Base):
    """Decision timeline audit log — immutable."""
    __tablename__ = "decision_timeline"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(50), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    actor_id = Column(UUID(as_uuid=True), nullable=True)
    actor_role = Column(String(100), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=False, server_default="{}")
    ip_address = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


# ============================
# OUTCOME MEASUREMENT + FEATURE STORE + MODEL REGISTRY (Phase 3.5)
# ============================

class OutcomeDefinitionModel(Base):
    __tablename__ = "outcome_definitions"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id"), nullable=False, index=True)
    metrics = Column(JSON, nullable=False, server_default="[]")
    measurement_window_start = Column(DateTime, nullable=False)
    measurement_window_end = Column(DateTime, nullable=False)
    comparison_period_start = Column(DateTime, nullable=True)
    comparison_period_end = Column(DateTime, nullable=True)
    use_control_group = Column(Boolean, nullable=False, server_default="false")
    control_group_definition = Column(JSON, nullable=True)
    confidence_level = Column(Float, nullable=False, server_default="0.95")
    min_sample_size = Column(Integer, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class OutcomeMeasurementModel(Base):
    __tablename__ = "outcome_measurements"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    outcome_definition_id = Column(UUID(as_uuid=True), ForeignKey("outcome_definitions.id"), nullable=False, index=True)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id"), nullable=False)
    measurement_time = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    checkpoint_type = Column(String(50), nullable=False, server_default="monthly")
    metric_values = Column(JSON, nullable=False, server_default="[]")
    status = Column(String(50), nullable=False, server_default="on_track")
    alerts_triggered = Column(JSON, nullable=False, server_default="[]")
    measured_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class CausalImpactAnalysisModel(Base):
    __tablename__ = "causal_impact_analyses"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    outcome_id = Column(UUID(as_uuid=True), ForeignKey("decision_outcomes.id"), nullable=False, index=True)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id"), nullable=False)
    method = Column(String(50), nullable=False, server_default="before_after")
    causal_effect_size = Column(Float, nullable=False, server_default="0")
    causal_effect_confidence = Column(Float, nullable=False, server_default="0")
    confidence_interval_lower = Column(Float, nullable=False, server_default="0")
    confidence_interval_upper = Column(Float, nullable=False, server_default="0")
    attribution_score = Column(Float, nullable=False, server_default="0")
    confounding_factors = Column(JSON, nullable=False, server_default="[]")
    counterfactual_value = Column(Float, nullable=False, server_default="0")
    counterfactual_confidence = Column(Float, nullable=False, server_default="0")
    treatment_vs_control = Column(Float, nullable=False, server_default="0")
    statistical_significance = Column(Float, nullable=False, server_default="1")
    effect_hypothesis_test = Column(Text, nullable=True)
    analysis_time = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    analyzed_by = Column(UUID(as_uuid=True), nullable=True)


class FeatureDefinitionModel(Base):
    __tablename__ = "feature_definitions"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(200), nullable=False)
    namespace = Column(String(50), nullable=False, server_default="finance")
    description = Column(Text, nullable=True)
    feature_type = Column(String(50), nullable=False, server_default="aggregation")
    computation_type = Column(String(50), nullable=False, server_default="sql")
    computation_source = Column(Text, nullable=True)
    computation_params = Column(JSON, nullable=False, server_default="{}")
    entity_type = Column(String(50), nullable=False, server_default="department")
    entity_id_path = Column(String(200), nullable=True)
    temporal_type = Column(String(50), nullable=False, server_default="static")
    window_size = Column(Integer, nullable=True)
    window_unit = Column(String(20), nullable=True)
    refresh_frequency = Column(String(50), nullable=False, server_default="daily")
    value_type = Column(String(20), nullable=False, server_default="float")
    default_value = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    tags = Column(JSON, nullable=False, server_default="[]")
    source_metrics = Column(JSON, nullable=False, server_default="[]")
    source_features = Column(JSON, nullable=False, server_default="[]")
    status = Column(String(50), nullable=False, server_default="draft")
    version = Column(Integer, nullable=False, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class ModelArtifactModel(Base):
    __tablename__ = "model_artifacts"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(200), nullable=False)
    model_type = Column(String(50), nullable=False, server_default="statistical")
    framework = Column(String(100), nullable=True)
    version = Column(String(50), nullable=False, server_default="1.0.0")
    version_notes = Column(Text, nullable=True)
    model_location = Column(String(500), nullable=True)
    artifact_size_bytes = Column(Integer, nullable=False, server_default="0")
    checksum = Column(String(100), nullable=True)
    model_format = Column(String(50), nullable=False, server_default="json")
    metrics = Column(JSON, nullable=False, server_default="[]")
    entity_type = Column(String(50), nullable=True)
    use_cases = Column(JSON, nullable=False, server_default="[]")
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    approval_status = Column(String(50), nullable=False, server_default="draft")
    tags = Column(JSON, nullable=False, server_default="[]")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    version_int = Column(Integer, nullable=False, server_default="1")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5 MODELS (Migration 006)
# ═══════════════════════════════════════════════════════════════════════════════

class CFOProfileModel(Base, TimestampMixin):
    __tablename__ = "cfo_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    preferences = Column(JSON, nullable=False, server_default="{}")
    is_active = Column(Boolean, nullable=False, server_default="true")


class CFOQuestionModel(Base):
    __tablename__ = "cfo_questions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_query = Column(Text, nullable=False)
    intent = Column(String(50), nullable=False)
    answer = Column(JSON, nullable=False, server_default="{}")
    evidence_chain = Column(JSON, nullable=False, server_default="[]")
    confidence = Column(Float, nullable=False, server_default="0.0")
    processing_time_ms = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class CFOBriefingModel(Base):
    __tablename__ = "cfo_briefings"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    mode = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False, server_default="generated")
    period = Column(String(20), nullable=False)
    sections = Column(JSON, nullable=False, server_default="[]")
    score = Column(Integer, nullable=False, server_default="0")
    executive_summary = Column(Text, nullable=True)
    key_findings = Column(JSON, nullable=False, server_default="[]")
    actions = Column(JSON, nullable=False, server_default="[]")
    narrative = Column(Text, nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class CFOWorkspaceModel(Base, TimestampMixin):
    __tablename__ = "cfo_workspaces"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    widgets = Column(JSON, nullable=False, server_default="[]")
    layout = Column(JSON, nullable=False, server_default="{}")
    shared = Column(Boolean, nullable=False, server_default="false")


class CFOAlertConfigModel(Base):
    __tablename__ = "cfo_alert_configs"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    metric_id = Column(UUID(as_uuid=True), nullable=False)
    metric_name = Column(String(255), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    condition = Column(JSON, nullable=False, server_default="{}")
    thresholds = Column(JSON, nullable=False, server_default="{}")
    channels = Column(JSON, nullable=False, server_default="[]")
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class CFOAlertModel(Base):
    __tablename__ = "cfo_alerts"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    config_id = Column(UUID(as_uuid=True), nullable=False)
    metric_id = Column(UUID(as_uuid=True), nullable=False)
    metric_name = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)
    value = Column(Numeric(18, 4), nullable=True)
    threshold = Column(Numeric(18, 4), nullable=True)
    is_read = Column(Boolean, nullable=False, server_default="false")
    is_dismissed = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    read_at = Column(DateTime(timezone=True), nullable=True)


class StrategicScenarioModel(Base, TimestampMixin):
    __tablename__ = "strategic_scenarios"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(30), nullable=False, server_default="base")
    status = Column(String(30), nullable=False, server_default="active")
    assumptions = Column(JSON, nullable=False, server_default="[]")
    driver_values = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)
    created_by = Column(String(100), nullable=True)


class StrategicDriverTreeModel(Base):
    __tablename__ = "strategic_driver_trees"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    root_node_id = Column(UUID(as_uuid=True), nullable=True)
    metrics = Column(JSON, nullable=False, server_default="[]")
    calculated_results = Column(JSON, nullable=True)
    status = Column(String(30), nullable=False, server_default="draft")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class StrategicWhatIfModel(Base):
    __tablename__ = "strategic_whatif_analyses"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    base_values = Column(JSON, nullable=False, server_default="{}")
    changes = Column(JSON, nullable=False, server_default="[]")
    results = Column(JSON, nullable=True)
    impact_summary = Column(JSON, nullable=True)
    sensitivity = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class ForecastModelModel(Base, TimestampMixin):
    __tablename__ = "forecast_models"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    model_type = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=False, server_default="{}")
    hyperparameters = Column(JSON, nullable=False, server_default="{}")
    status = Column(String(30), nullable=False, server_default="draft")
    training_metadata = Column(JSON, nullable=True)
    model_artifact = Column(LargeBinary, nullable=True)


class ForecastResultModel(Base):
    __tablename__ = "forecast_results"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    model_id = Column(UUID(as_uuid=True), ForeignKey("forecast_models.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    metric_id = Column(String(100), nullable=False)
    metric_name = Column(String(255), nullable=False)
    period = Column(String(20), nullable=False)
    values = Column(JSON, nullable=False, server_default="[]")
    metrics = Column(JSON, nullable=True)
    confidence_level = Column(Float, nullable=True)
    model_name = Column(String(255), nullable=True)
    model_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class ForecastMonitoringAlertModel(Base):
    __tablename__ = "forecast_monitoring_alerts"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    model_id = Column(UUID(as_uuid=True), ForeignKey("forecast_models.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    metric_name = Column(String(255), nullable=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=True)
    drift_score = Column(Float, nullable=True)
    details = Column(JSON, nullable=True)
    is_resolved = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class MemoryRecordModel(Base):
    __tablename__ = "memory_records"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    memory_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(ARRAY(Float), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True, server_default="{}")
    source = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=False, server_default="1.0")
    access_count = Column(Integer, nullable=False, server_default="0")
    status = Column(String(30), nullable=False, server_default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    last_accessed = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    expires_at = Column(DateTime(timezone=True), nullable=True)


class KnowledgeNodeModel(Base, TimestampMixin):
    __tablename__ = "knowledge_nodes"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    node_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    properties = Column(JSON, nullable=False, server_default="{}")
    importance_score = Column(Float, nullable=False, server_default="0.0")


class KnowledgeEdgeModel(Base):
    __tablename__ = "knowledge_edges"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String(50), nullable=False)
    weight = Column(Float, nullable=False, server_default="1.0")
    confidence = Column(Float, nullable=False, server_default="1.0")
    evidence = Column(JSON, nullable=True, server_default="[]")
    properties = Column(JSON, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class CurrencyEntityConfigModel(Base, TimestampMixin):
    __tablename__ = "currency_entity_configs"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_name = Column(String(255), nullable=False)
    functional_currency = Column(String(3), nullable=False)
    reporting_currency = Column(String(3), nullable=False)
    consolidation_method = Column(String(30), nullable=False, server_default="full")
    fx_rate_source = Column(String(100), nullable=True)
    is_consolidated = Column(Boolean, nullable=False, server_default="true")


class FXRateSnapshotModel(Base):
    __tablename__ = "fx_rate_snapshots"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    base_currency = Column(String(3), nullable=False)
    target_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(18, 8), nullable=False)
    inverse_rate = Column(Numeric(18, 8), nullable=False)
    rate_date = Column(Date, nullable=False)
    source = Column(String(100), nullable=False)
    is_estimated = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class ExecutiveDecisionModel(Base, TimestampMixin):
    __tablename__ = "executive_decisions"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False)
    status = Column(String(30), nullable=False, server_default="pending")
    impact_estimate = Column(JSON, nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    context = Column(JSON, nullable=True, server_default="{}")


class CopilotConversationModel(Base, TimestampMixin):
    __tablename__ = "copilot_conversations"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False)
    title = Column(String(255), nullable=True)
    status = Column(String(30), nullable=False, server_default="active")
    messages = Column(JSON, nullable=False, server_default="[]")
    context = Column(JSON, nullable=True, server_default="{}")


class CausalGraphModel(Base):
    __tablename__ = "causal_graphs"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    nodes = Column(JSON, nullable=False, server_default="[]")
    edges = Column(JSON, nullable=False, server_default="[]")
    adjustment_set = Column(JSON, nullable=True, server_default="[]")
    is_valid = Column(Boolean, nullable=False, server_default="true")
    validation_errors = Column(JSON, nullable=True, server_default="[]")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class CausalEstimateModel(Base):
    __tablename__ = "causal_estimates"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    graph_id = Column(UUID(as_uuid=True), ForeignKey("causal_graphs.id", ondelete="SET NULL"), nullable=True)
    method = Column(String(50), nullable=False)
    treatment = Column(String(255), nullable=False)
    outcome = Column(String(255), nullable=False)
    point_estimate = Column(Numeric(18, 8), nullable=False)
    confidence_interval = Column(JSON, nullable=True)
    p_value = Column(Float, nullable=True)
    standard_error = Column(Numeric(18, 8), nullable=True)
    sample_size = Column(Integer, nullable=True)
    assumptions = Column(JSON, nullable=True, server_default="[]")
    is_valid = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class NLQueryLogModel(Base):
    __tablename__ = "nl_query_log"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    query = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)
    entities = Column(JSON, nullable=True, server_default="[]")
    result = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class ExportJobModel(Base):
    __tablename__ = "export_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    export_type = Column(String(20), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, server_default="pending")
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    completed_at = Column(DateTime(timezone=True), nullable=True)


class CollaborationCommentModel(Base):
    __tablename__ = "collaboration_comments"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    user_name = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class SavedDashboardModel(Base, TimestampMixin):
    __tablename__ = "saved_dashboards"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    layout = Column(JSON, nullable=False, server_default="{}")
    widgets = Column(JSON, nullable=False, server_default="[]")
    is_template = Column(Boolean, nullable=False, server_default="false")
    template_category = Column(String(50), nullable=True)
    status = Column(String(30), nullable=False, server_default="active")


class VisualizationSpecModel(Base, TimestampMixin):
    __tablename__ = "visualization_specs"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    chart_type = Column(String(50), nullable=False)
    config = Column(JSON, nullable=False, server_default="{}")
    data_source = Column(JSON, nullable=True)
    color_scheme = Column(String(50), nullable=True)


class SemanticMetricV2Model(Base, TimestampMixin):
    __tablename__ = "semantic_metrics_v2"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    expression = Column(Text, nullable=False)
    data_type = Column(String(30), nullable=False, server_default="decimal")
    category = Column(String(50), nullable=True)
    status = Column(String(30), nullable=False, server_default="draft")
    __table_args__ = (UniqueConstraint("tenant_id", "slug", name="uq_semantic_metric_slug_v2"),)


class SemanticDimensionV2Model(Base, TimestampMixin):
    __tablename__ = "semantic_dimensions_v2"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    physical_name = Column(String(255), nullable=False)
    key_column = Column(String(255), nullable=False)
    data_type = Column(String(30), nullable=False, server_default="string")
    cardinality = Column(String(20), nullable=True)
    __table_args__ = (UniqueConstraint("tenant_id", "slug", name="uq_semantic_dimension_slug_v2"),)


class MaterializedViewCacheModel(Base):
    __tablename__ = "materialized_view_cache"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    query_hash = Column(String(64), nullable=False)
    cached_data = Column(JSON, nullable=False)
    row_count = Column(Integer, nullable=False, server_default="0")
    last_refreshed = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    ttl_seconds = Column(Integer, nullable=False, server_default="300")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
