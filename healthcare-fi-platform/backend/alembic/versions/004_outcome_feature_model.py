"""004 Outcome Measurement, Feature Store, Model Registry

Revision ID: 004
Revises: 003
Create Date: 2026-06-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================================
    # OUTCOME DEFINITIONS
    # ============================================================
    op.create_table(
        'outcome_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('decisions.id'), nullable=False),

        sa.Column('metrics', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('measurement_window_start', sa.Date, nullable=False),
        sa.Column('measurement_window_end', sa.Date, nullable=False),
        sa.Column('comparison_period_start', sa.Date, nullable=True),
        sa.Column('comparison_period_end', sa.Date, nullable=True),

        sa.Column('use_control_group', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('control_group_definition', postgresql.JSONB, nullable=True),
        sa.Column('confidence_level', sa.Float, nullable=False, server_default='0.95'),
        sa.Column('min_sample_size', sa.Integer, nullable=True),

        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_outcome_definitions_decision', 'outcome_definitions', ['decision_id'])

    # ============================================================
    # OUTCOME MEASUREMENTS
    # ============================================================
    op.create_table(
        'outcome_measurements',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('outcome_definition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('outcome_definitions.id'), nullable=False),
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('decisions.id'), nullable=False),

        sa.Column('measurement_time', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('checkpoint_type', sa.String(50), nullable=False, server_default='monthly'),

        sa.Column('metric_values', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('status', sa.String(50), nullable=False, server_default='on_track'),
        sa.Column('alerts_triggered', postgresql.JSONB, nullable=False, server_default='[]'),

        sa.Column('measured_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_outcome_measurements_def', 'outcome_measurements', ['outcome_definition_id'])

    # ============================================================
    # CAUSAL IMPACT ANALYSES
    # ============================================================
    op.create_table(
        'causal_impact_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('outcome_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('decision_outcomes.id'), nullable=False),
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('decisions.id'), nullable=False),

        sa.Column('method', sa.String(50), nullable=False, server_default='before_after'),
        sa.Column('causal_effect_size', sa.Float, nullable=False, server_default='0'),
        sa.Column('causal_effect_confidence', sa.Float, nullable=False, server_default='0'),
        sa.Column('confidence_interval_lower', sa.Float, nullable=False, server_default='0'),
        sa.Column('confidence_interval_upper', sa.Float, nullable=False, server_default='0'),

        sa.Column('attribution_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('confounding_factors', postgresql.JSONB, nullable=False, server_default='[]'),

        sa.Column('counterfactual_value', sa.Float, nullable=False, server_default='0'),
        sa.Column('counterfactual_confidence', sa.Float, nullable=False, server_default='0'),
        sa.Column('treatment_vs_control', sa.Float, nullable=False, server_default='0'),

        sa.Column('statistical_significance', sa.Float, nullable=False, server_default='1'),
        sa.Column('effect_hypothesis_test', sa.Text, nullable=True),

        sa.Column('analysis_time', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('analyzed_by', postgresql.UUID(as_uuid=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_causal_impact_outcome', 'causal_impact_analyses', ['outcome_id'])

    # ============================================================
    # FEATURE STORE
    # ============================================================
    op.create_table(
        'feature_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('namespace', sa.String(50), nullable=False, server_default='finance'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('feature_type', sa.String(50), nullable=False, server_default='aggregation'),

        sa.Column('computation_type', sa.String(50), nullable=False, server_default='sql'),
        sa.Column('computation_source', sa.Text, nullable=True),
        sa.Column('computation_params', postgresql.JSONB, nullable=False, server_default='{}'),

        sa.Column('entity_type', sa.String(50), nullable=False, server_default='department'),
        sa.Column('entity_id_path', sa.String(200), nullable=True),

        sa.Column('temporal_type', sa.String(50), nullable=False, server_default='static'),
        sa.Column('window_size', sa.Integer, nullable=True),
        sa.Column('window_unit', sa.String(20), nullable=True),
        sa.Column('refresh_frequency', sa.String(50), nullable=False, server_default='daily'),

        sa.Column('value_type', sa.String(20), nullable=False, server_default='float'),
        sa.Column('default_value', sa.Text, nullable=True),

        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tags', postgresql.JSONB, nullable=False, server_default='[]'),

        sa.Column('source_metrics', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('source_features', postgresql.JSONB, nullable=False, server_default='[]'),

        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_feature_definitions_name', 'feature_definitions', ['tenant_id', 'name'], unique=True)

    # ============================================================
    # MODEL REGISTRY
    # ============================================================
    op.create_table(
        'model_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('model_type', sa.String(50), nullable=False, server_default='statistical'),
        sa.Column('framework', sa.String(100), nullable=True),
        sa.Column('version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.Column('version_notes', sa.Text, nullable=True),

        sa.Column('model_location', sa.String(500), nullable=True),
        sa.Column('artifact_size_bytes', sa.BigInteger, nullable=False, server_default='0'),
        sa.Column('checksum', sa.String(100), nullable=True),
        sa.Column('model_format', sa.String(50), nullable=False, server_default='json'),

        sa.Column('metrics', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('use_cases', postgresql.JSONB, nullable=False, server_default='[]'),

        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approval_status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('tags', postgresql.JSONB, nullable=False, server_default='[]'),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version_int', sa.Integer, nullable=False, server_default='1'),

        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_model_artifacts_use_case', 'model_artifacts', ['tenant_id', 'use_cases'])


def downgrade() -> None:
    op.drop_table('model_artifacts')
    op.drop_table('feature_definitions')
    op.drop_table('causal_impact_analyses')
    op.drop_table('outcome_measurements')
    op.drop_table('outcome_definitions')
