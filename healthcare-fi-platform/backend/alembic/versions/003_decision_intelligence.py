"""003 Decision Intelligence Foundation

Revision ID: 003
Revises: 002
Create Date: 2026-06-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================================
    # DECISIONS
    # ============================================================
    op.create_table(
        'decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Core
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('decision_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='proposed'),
        sa.Column('priority', sa.String(10), nullable=False, server_default='P2'),
        sa.Column('urgency', sa.String(20), nullable=False, server_default='scheduled'),

        # Trigger context
        sa.Column('trigger_type', sa.String(50), nullable=True),
        sa.Column('trigger_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('trigger_summary', sa.Text, nullable=True),

        # Classification
        sa.Column('category', sa.String(50), nullable=False, server_default='operational'),
        sa.Column('department_ids', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('scope_type', sa.String(50), nullable=False, server_default='tenant'),
        sa.Column('scope_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Financial
        sa.Column('estimated_value', sa.Float, nullable=True),
        sa.Column('estimated_cost', sa.Float, nullable=True),
        sa.Column('currency', sa.String(10), nullable=False, server_default='INR'),

        # Timing
        sa.Column('review_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('implementation_target_date', sa.Date, nullable=True),
        sa.Column('completion_date', sa.DateTime(timezone=True), nullable=True),

        # People
        sa.Column('proposed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('proposed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('reviewed_by', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('approved_by', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('rejected_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('implemented_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Outcome link
        sa.Column('outcome_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Metadata
        sa.Column('tags', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),

        # Lifecycle
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_decisions_tenant_id', 'decisions', ['tenant_id'])
    op.create_index('ix_decisions_status', 'decisions', ['tenant_id', 'status'])
    op.create_index('ix_decisions_decision_type', 'decisions', ['tenant_id', 'decision_type'])
    op.create_index('ix_decisions_category', 'decisions', ['tenant_id', 'category'])
    op.create_index('ix_decisions_proposed_by', 'decisions', ['proposed_by'])
    op.create_index('ix_decisions_created_at', 'decisions', ['tenant_id', 'created_at'])

    # ============================================================
    # DECISION EVIDENCE
    # ============================================================
    op.create_table(
        'decision_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('decisions.id', ondelete='CASCADE'), nullable=False),

        sa.Column('evidence_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('weight', sa.Float, nullable=False, server_default='1.0'),
        sa.Column('source_type', sa.String(50), nullable=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_metric_code', sa.String(100), nullable=True),
        sa.Column('data_payload', postgresql.JSONB, nullable=False, server_default='{}'),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_decision_evidence_decision_id', 'decision_evidence', ['decision_id'])

    # ============================================================
    # DECISION OUTCOMES
    # ============================================================
    op.create_table(
        'decision_outcomes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('decisions.id'), nullable=False),

        # Measurement period
        sa.Column('measurement_start', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('measurement_end', sa.DateTime(timezone=True), nullable=True),

        # Expected vs actual
        sa.Column('expected_metrics', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('actual_metrics', postgresql.JSONB, nullable=False, server_default='[]'),

        # Computed
        sa.Column('accuracy_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('variance_absolute', sa.Float, nullable=False, server_default='0'),
        sa.Column('variance_percent', sa.Float, nullable=False, server_default='0'),
        sa.Column('outcome_status', sa.String(50), nullable=False, server_default='inconclusive'),

        # Causal
        sa.Column('causal_impact', postgresql.JSONB, nullable=True),

        # Financial
        sa.Column('realized_value', sa.Float, nullable=False, server_default='0'),
        sa.Column('roi_actual', sa.Float, nullable=True),

        # Measurement
        sa.Column('measured_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('measured_at', sa.DateTime(timezone=True), nullable=True),

        # Lifecycle
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_decision_outcomes_decision_id', 'decision_outcomes', ['decision_id'])

    # ============================================================
    # DECISION REVIEWS
    # ============================================================
    op.create_table(
        'decision_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('decisions.id', ondelete='CASCADE'), nullable=False),

        sa.Column('review_type', sa.String(50), nullable=False, server_default='initial_review'),
        sa.Column('review_round', sa.Integer, nullable=False, server_default='1'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),

        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewer_role', sa.String(100), nullable=True),
        sa.Column('review_decision', sa.String(50), nullable=True),

        sa.Column('comments', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('conditions', postgresql.JSONB, nullable=True),
        sa.Column('escalation_required', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('escalation_to', postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),

        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_decision_reviews_decision_id', 'decision_reviews', ['decision_id'])

    # ============================================================
    # DECISION TIMELINE (immutable audit log)
    # ============================================================
    op.create_table(
        'decision_timeline',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('decisions.id', ondelete='CASCADE'), nullable=False),

        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('from_status', sa.String(50), nullable=True),
        sa.Column('to_status', sa.String(50), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_role', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('ip_address', sa.String(50), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_decision_timeline_decision_id', 'decision_timeline', ['decision_id'])


def downgrade() -> None:
    op.drop_table('decision_timeline')
    op.drop_table('decision_reviews')
    op.drop_table('decision_outcomes')
    op.drop_table('decision_evidence')
    op.drop_table('decisions')
