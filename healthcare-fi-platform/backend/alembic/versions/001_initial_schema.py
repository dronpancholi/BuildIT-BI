"""001 Initial Schema

Revision ID: 001
Revises: 
Create Date: 2026-06-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create extensions
    op.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
    op.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
    op.execute(text('CREATE EXTENSION IF NOT EXISTS "pg_trgm"'))

    # Tenants
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('domain', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('subscription_tier', sa.String(50), server_default='professional', nullable=False),
        sa.Column('metadata_json', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tenants_tenant_id', 'tenants', ['tenant_id'])
    op.create_index('ix_tenants_code', 'tenants', ['code'], unique=True)
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'])

    # Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), server_default='viewer', nullable=False),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_users_username', 'users', ['tenant_id', 'username'], unique=True)
    op.create_index('ix_users_email', 'users', ['tenant_id', 'email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])

    # Hospital Groups
    op.create_table(
        'hospital_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_hospital_groups_tenant_id', 'hospital_groups', ['tenant_id'])
    op.create_index('ix_hospital_groups_code', 'hospital_groups', ['tenant_id', 'code'], unique=True)

    # Hospitals
    op.create_table(
        'hospitals',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('hospital_group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hospital_groups.id'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('zip_code', sa.String(20), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('hospital_type', sa.String(50), nullable=True),
        sa.Column('bed_count', sa.Integer(), nullable=True),
        sa.Column('license_number', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_hospitals_tenant_id', 'hospitals', ['tenant_id'])
    op.create_index('ix_hospitals_code', 'hospitals', ['tenant_id', 'code'], unique=True)
    op.create_index('ix_hospitals_hospital_group_id', 'hospitals', ['hospital_group_id'])

    # Branches
    op.create_table(
        'branches',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('hospital_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hospitals.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('branch_type', sa.String(50), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_branches_tenant_id', 'branches', ['tenant_id'])
    op.create_index('ix_branches_code', 'branches', ['hospital_id', 'code'], unique=True)
    op.create_index('ix_branches_hospital_id', 'branches', ['hospital_id'])

    # Departments
    op.create_table(
        'departments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branches.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('department_type', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('head_doctor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('budget_allocation', sa.Numeric(15, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_departments_tenant_id', 'departments', ['tenant_id'])
    op.create_index('ix_departments_code', 'departments', ['branch_id', 'code'], unique=True)
    op.create_index('ix_departments_branch_id', 'departments', ['branch_id'])

    # Payers (Insurance Companies)
    op.create_table(
        'payers',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('payer_type', sa.String(50), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payers_tenant_id', 'payers', ['tenant_id'])
    op.create_index('ix_payers_code', 'payers', ['tenant_id', 'code'], unique=True)

    # Doctors
    op.create_table(
        'doctors',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('hospital_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hospitals.id'), nullable=True),
        sa.Column('employee_id', sa.String(50), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('specialization', sa.String(100), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_doctors_tenant_id', 'doctors', ['tenant_id'])
    op.create_index('ix_doctors_employee_id', 'doctors', ['tenant_id', 'employee_id'], unique=True)
    op.create_index('ix_doctors_hospital_id', 'doctors', ['hospital_id'])

    # Metric Definitions
    op.create_table(
        'metric_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('formula', sa.Text, nullable=True),
        sa.Column('formula_language', sa.String(20), nullable=True),
        sa.Column('sql_query', sa.Text, nullable=True),
        sa.Column('dependencies', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('output_schema', postgresql.JSONB, nullable=True),
        sa.Column('trust_level', sa.String(20), server_default='draft', nullable=False),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('refresh_frequency', sa.String(20), nullable=True),
        sa.Column('cache_ttl_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_metric_definitions_tenant_id', 'metric_definitions', ['tenant_id'])
    op.create_index('ix_metric_definitions_code', 'metric_definitions', ['tenant_id', 'code'], unique=True)
    op.create_index('ix_metric_definitions_category', 'metric_definitions', ['category'])
    op.create_index('ix_metric_definitions_trust_level', 'metric_definitions', ['trust_level'])

    # Metric Computed Values
    op.create_table(
        'metric_computed_values',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('metric_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('metric_definitions.id'), nullable=False),
        sa.Column('value', sa.Numeric(20, 6), nullable=False),
        sa.Column('previous_value', sa.Numeric(20, 6), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('scope_tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope_hospital_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope_branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope_department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('computation_time_ms', sa.Integer(), nullable=True),
        sa.Column('computation_method', sa.String(50), nullable=True),
        sa.Column('formula_version', sa.String(50), nullable=True),
        sa.Column('data_hash', sa.String(64), nullable=True),
        sa.Column('lineage_snapshot', postgresql.JSONB, nullable=True),
        sa.Column('quality_flags', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('cached_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_valid', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('validation_errors', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_metric_computed_values_tenant_id', 'metric_computed_values', ['tenant_id'])
    op.create_index('ix_metric_computed_values_metric_id', 'metric_computed_values', ['metric_id'])
    op.create_index('ix_metric_computed_values_period', 'metric_computed_values', ['period_start', 'period_end'])
    op.create_index('ix_metric_computed_values_scope', 'metric_computed_values', ['scope_hospital_id', 'scope_branch_id'])
    op.create_index('ix_metric_computed_values_is_valid', 'metric_computed_values', ['is_valid'])

    # Data Sources
    op.create_table(
        'data_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('connection_config', postgresql.JSONB, nullable=True),
        sa.Column('schema_config', postgresql.JSONB, nullable=True),
        sa.Column('sync_frequency', sa.String(20), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_data_sources_tenant_id', 'data_sources', ['tenant_id'])

    # Data Source Mappings
    op.create_table(
        'data_source_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_sources.id'), nullable=False),
        sa.Column('source_table', sa.String(255), nullable=False),
        sa.Column('source_column', sa.String(255), nullable=False),
        sa.Column('target_entity', sa.String(100), nullable=False),
        sa.Column('target_field', sa.String(100), nullable=False),
        sa.Column('transformation', sa.Text, nullable=True),
        sa.Column('is_required', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_data_source_mappings_tenant_id', 'data_source_mappings', ['tenant_id'])
    op.create_index('ix_data_source_mappings_data_source_id', 'data_source_mappings', ['data_source_id'])

    # Quality Rules
    op.create_table(
        'quality_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('rule_category', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), server_default='medium', nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('configuration', postgresql.JSONB, nullable=False),
        sa.Column('threshold', sa.Numeric(10, 4), nullable=True),
        sa.Column('expected_value', sa.Text, nullable=True),
        sa.Column('sql_check', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_system_rule', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('execution_frequency', sa.String(20), nullable=True),
        sa.Column('last_executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_execution_status', sa.String(20), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quality_rules_tenant_id', 'quality_rules', ['tenant_id'])
    op.create_index('ix_quality_rules_rule_type', 'quality_rules', ['rule_type'])
    op.create_index('ix_quality_rules_rule_category', 'quality_rules', ['rule_category'])
    op.create_index('ix_quality_rules_entity', 'quality_rules', ['entity_type', 'entity_id'])

    # Quality Issues
    op.create_table(
        'quality_issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_rules.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), server_default='open', nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('field_name', sa.String(100), nullable=True),
        sa.Column('expected_value', sa.Text, nullable=True),
        sa.Column('actual_value', sa.Text, nullable=True),
        sa.Column('impact_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('root_cause', sa.Text, nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('resolution_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quality_issues_tenant_id', 'quality_issues', ['tenant_id'])
    op.create_index('ix_quality_issues_rule_id', 'quality_issues', ['rule_id'])
    op.create_index('ix_quality_issues_status', 'quality_issues', ['status'])
    op.create_index('ix_quality_issues_severity', 'quality_issues', ['severity'])
    op.create_index('ix_quality_issues_entity', 'quality_issues', ['entity_type', 'entity_id'])

    # Data Quality Scores
    op.create_table(
        'data_quality_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score_date', sa.Date, nullable=False),
        sa.Column('overall_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('completeness_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('accuracy_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('timeliness_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('consistency_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('validity_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('issues_open', sa.Integer(), server_default='0', nullable=False),
        sa.Column('issues_critical', sa.Integer(), server_default='0', nullable=False),
        sa.Column('issues_high', sa.Integer(), server_default='0', nullable=False),
        sa.Column('issues_medium', sa.Integer(), server_default='0', nullable=False),
        sa.Column('issues_low', sa.Integer(), server_default='0', nullable=False),
        sa.Column('rules_passed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('rules_failed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_checks', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_data_quality_scores_tenant_id', 'data_quality_scores', ['tenant_id'])
    op.create_index('ix_data_quality_scores_entity', 'data_quality_scores', ['entity_type', 'entity_id'])
    op.create_index('ix_data_quality_scores_date', 'data_quality_scores', ['score_date'])

    # Lineage Nodes
    op.create_table(
        'lineage_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('node_type', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('metadata_json', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lineage_nodes_tenant_id', 'lineage_nodes', ['tenant_id'])
    op.create_index('ix_lineage_nodes_entity', 'lineage_nodes', ['entity_type', 'entity_id'])
    op.create_index('ix_lineage_nodes_node_type', 'lineage_nodes', ['node_type'])

    # Lineage Edges
    op.create_table(
        'lineage_edges',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('source_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lineage_nodes.id'), nullable=False),
        sa.Column('target_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lineage_nodes.id'), nullable=False),
        sa.Column('edge_type', sa.String(50), nullable=False),
        sa.Column('transformation_type', sa.String(100), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('metadata_json', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lineage_edges_tenant_id', 'lineage_edges', ['tenant_id'])
    op.create_index('ix_lineage_edges_source', 'lineage_edges', ['source_node_id'])
    op.create_index('ix_lineage_edges_target', 'lineage_edges', ['target_node_id'])
    op.create_index('ix_lineage_edges_edge_type', 'lineage_edges', ['edge_type'])

    # Lineage Graphs
    op.create_table(
        'lineage_graphs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('node_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('edge_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('node_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('edge_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('root_nodes', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('leaf_nodes', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('metadata_json', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lineage_graphs_tenant_id', 'lineage_graphs', ['tenant_id'])

    # Lineage Computation Records
    op.create_table(
        'lineage_computation_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('graph_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lineage_graphs.id'), nullable=True),
        sa.Column('metric_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('metric_definitions.id'), nullable=True),
        sa.Column('computed_value_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('metric_computed_values.id'), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('cache_hit', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('validation_passed', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('validation_errors', postgresql.JSONB, nullable=True),
        sa.Column('metadata_json', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lineage_computation_records_tenant_id', 'lineage_computation_records', ['tenant_id'])
    op.create_index('ix_lineage_computation_records_graph_id', 'lineage_computation_records', ['graph_id'])
    op.create_index('ix_lineage_computation_records_metric_id', 'lineage_computation_records', ['metric_id'])

    # Domain Events
    op.create_table(
        'domain_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('aggregate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aggregate_type', sa.String(50), nullable=False),
        sa.Column('event_data', postgresql.JSONB, nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('causation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('schema_version', sa.String(20), nullable=True),
        sa.Column('is_processed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_domain_events_tenant_id', 'domain_events', ['tenant_id'])
    op.create_index('ix_domain_events_event_type', 'domain_events', ['event_type'])
    op.create_index('ix_domain_events_aggregate', 'domain_events', ['aggregate_type', 'aggregate_id'])
    op.create_index('ix_domain_events_correlation_id', 'domain_events', ['correlation_id'])
    op.create_index('ix_domain_events_is_processed', 'domain_events', ['is_processed'])

    # Outbox Events
    op.create_table(
        'outbox_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('aggregate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aggregate_type', sa.String(50), nullable=False),
        sa.Column('event_data', postgresql.JSONB, nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('is_published', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('max_retries', sa.Integer(), server_default='3', nullable=False),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_outbox_events_is_published', 'outbox_events', ['is_published'])
    op.create_index('ix_outbox_events_event_type', 'outbox_events', ['event_type'])

    # Import Templates
    op.create_table(
        'import_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('column_mappings', postgresql.JSONB, nullable=False),
        sa.Column('validation_rules', postgresql.JSONB, nullable=True),
        sa.Column('transformation_rules', postgresql.JSONB, nullable=True),
        sa.Column('is_system_template', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_import_templates_tenant_id', 'import_templates', ['tenant_id'])

    # Import Jobs
    op.create_table(
        'import_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('import_templates.id'), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('total_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('processed_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('successful_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('failed_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_summary', postgresql.JSONB, nullable=True),
        sa.Column('validation_summary', postgresql.JSONB, nullable=True),
        sa.Column('quality_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('initiated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_import_jobs_tenant_id', 'import_jobs', ['tenant_id'])
    op.create_index('ix_import_jobs_template_id', 'import_jobs', ['template_id'])
    op.create_index('ix_import_jobs_status', 'import_jobs', ['status'])

    # Import Checkpoints
    op.create_table(
        'import_checkpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('import_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('import_jobs.id'), nullable=False),
        sa.Column('stage', sa.String(50), nullable=False),
        sa.Column('row_start', sa.Integer(), nullable=False),
        sa.Column('row_end', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('records_processed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('records_failed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_ids', postgresql.JSONB, nullable=True),
        sa.Column('checkpoint_data', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_import_checkpoints_tenant_id', 'import_checkpoints', ['tenant_id'])
    op.create_index('ix_import_checkpoints_import_id', 'import_checkpoints', ['import_id'])

    # Workflow Executions
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('workflow_type', sa.String(100), nullable=False),
        sa.Column('workflow_id', sa.String(255), nullable=True),
        sa.Column('run_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('trigger', sa.String(50), nullable=True),
        sa.Column('input_data', postgresql.JSONB, nullable=True),
        sa.Column('output_data', postgresql.JSONB, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workflow_executions_tenant_id', 'workflow_executions', ['tenant_id'])
    op.create_index('ix_workflow_executions_workflow_type', 'workflow_executions', ['workflow_type'])
    op.create_index('ix_workflow_executions_status', 'workflow_executions', ['status'])

    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_values', postgresql.JSONB, nullable=True),
        sa.Column('new_values', postgresql.JSONB, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_tenant_id', 'audit_logs', ['tenant_id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

    # Notifications
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=True),
        sa.Column('severity', sa.String(20), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_tenant_id', 'notifications', ['tenant_id'])
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])

    # System Configuration
    op.create_table(
        'system_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.Text, nullable=True),
        sa.Column('value_type', sa.String(20), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_system_config_tenant_id', 'system_config', ['tenant_id'])
    op.create_index('ix_system_config_key', 'system_config', ['tenant_id', 'key'], unique=True)


def downgrade() -> None:
    op.drop_table('system_config')
    op.drop_table('notifications')
    op.drop_table('audit_logs')
    op.drop_table('workflow_executions')
    op.drop_table('import_checkpoints')
    op.drop_table('import_jobs')
    op.drop_table('import_templates')
    op.drop_table('outbox_events')
    op.drop_table('domain_events')
    op.drop_table('lineage_computation_records')
    op.drop_table('lineage_graphs')
    op.drop_table('lineage_edges')
    op.drop_table('lineage_nodes')
    op.drop_table('data_quality_scores')
    op.drop_table('quality_issues')
    op.drop_table('quality_rules')
    op.drop_table('data_source_mappings')
    op.drop_table('data_sources')
    op.drop_table('metric_computed_values')
    op.drop_table('metric_definitions')
    op.drop_table('doctors')
    op.drop_table('payers')
    op.drop_table('departments')
    op.drop_table('branches')
    op.drop_table('hospitals')
    op.drop_table('hospital_groups')
    op.drop_table('users')
    op.drop_table('tenants')
