"""002 Intelligence Engine

Revision ID: 002
Revises: 001
Create Date: 2026-06-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Intelligence Insights
    op.create_table(
        'intelligence_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        
        # Classification
        sa.Column('insight_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('detailed_analysis', sa.Text, nullable=True),
        
        # Pattern
        sa.Column('pattern_type', sa.String(50), nullable=True),
        sa.Column('pattern_detected', postgresql.JSONB, nullable=True),
        sa.Column('statistical_properties', postgresql.JSONB, nullable=True),
        
        # Statistics
        sa.Column('statistical_test', sa.String(100), nullable=True),
        sa.Column('test_statistic', sa.Float, nullable=True),
        sa.Column('p_value', sa.Float, nullable=True),
        sa.Column('p_value_corrected', sa.Float, nullable=True),
        sa.Column('is_significant', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('confidence_level', sa.Float, nullable=True),
        sa.Column('effect_size', sa.Float, nullable=True),
        
        # Magnitude
        sa.Column('magnitude', sa.Float, nullable=True),
        sa.Column('magnitude_unit', sa.String(20), nullable=True),
        sa.Column('relative_magnitude', sa.Float, nullable=True),
        
        # Change tracking
        sa.Column('previous_insight_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('next_insight_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('insight_sequence', sa.Integer(), server_default='1', nullable=False),
        
        # Comparison
        sa.Column('comparison_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('comparison_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('comparison_value', sa.Float, nullable=True),
        sa.Column('comparison_change_absolute', sa.Float, nullable=True),
        sa.Column('comparison_change_percent', sa.Float, nullable=True),
        
        # Related intelligence
        sa.Column('related_metric_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('related_root_cause_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('related_anomaly_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('related_opportunity_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('related_recommendation_ids', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Scores
        sa.Column('scores', postgresql.JSONB, nullable=False),
        
        # Discovery context
        sa.Column('discovery_method', sa.String(50), nullable=True),
        sa.Column('triggered_by_event', sa.String(100), nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), server_default='discovered', nullable=False),
        sa.Column('is_notified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notification_channel', sa.String(50), nullable=True),
        
        # Period and scope
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=True),
        sa.Column('scope_type', sa.String(20), nullable=True),
        sa.Column('scope_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope_name', sa.String(200), nullable=True),
        
        # Metric context
        sa.Column('metric_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('metric_definitions.id'), nullable=True),
        sa.Column('metric_code', sa.String(50), nullable=True),
        
        # Generation
        sa.Column('generated_by', sa.String(50), nullable=True),
        sa.Column('generated_by_model', sa.String(100), nullable=True),
        sa.Column('generation_method', sa.String(50), nullable=True),
        
        # Audit
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intelligence_insights_tenant_id', 'intelligence_insights', ['tenant_id'])
    op.create_index('ix_intelligence_insights_type', 'intelligence_insights', ['insight_type'])
    op.create_index('ix_intelligence_insights_status', 'intelligence_insights', ['status'])
    op.create_index('ix_intelligence_insights_priority', 'intelligence_insights', [text("((scores->>'priority')::float)")])
    op.create_index('ix_intelligence_insights_scope', 'intelligence_insights', ['scope_type', 'scope_id'])
    op.create_index('ix_intelligence_insights_period', 'intelligence_insights', ['period_start', 'period_end'])
    op.create_index('ix_intelligence_insights_notified', 'intelligence_insights', ['tenant_id', 'is_notified', 'created_at'], postgresql_where=sa.text('deleted_at IS NULL'))

    # Intelligence Root Causes
    op.create_table(
        'intelligence_root_causes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        
        # Context
        sa.Column('subject_metric_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('subject_metric_code', sa.String(50), nullable=True),
        sa.Column('subject_previous_value', sa.Float, nullable=True),
        sa.Column('subject_current_value', sa.Float, nullable=True),
        sa.Column('subject_change_absolute', sa.Float, nullable=True),
        sa.Column('subject_change_percent', sa.Float, nullable=True),
        
        # Root cause
        sa.Column('cause_type', sa.String(50), nullable=False),
        sa.Column('cause_category', sa.String(100), nullable=True),
        sa.Column('cause_name', sa.String(500), nullable=False),
        sa.Column('cause_description', sa.Text, nullable=True),
        
        # Attribution
        sa.Column('attribution_weight', sa.Float, nullable=True),
        sa.Column('attribution_absolute', sa.Float, nullable=True),
        sa.Column('attribution_percent', sa.Float, nullable=True),
        sa.Column('is_primary_cause', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('cause_rank', sa.Integer(), nullable=True),
        
        # Statistical basis
        sa.Column('statistical_significance', sa.Float, nullable=True),
        sa.Column('confidence_interval', postgresql.JSONB, nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        
        # Evidence
        sa.Column('cause_evidence', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('breakdown', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Period context
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('comparison_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('comparison_period_end', sa.DateTime(timezone=True), nullable=True),
        
        # Scope
        sa.Column('scope_type', sa.String(20), nullable=True),
        sa.Column('scope_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope_name', sa.String(200), nullable=True),
        
        # Linked intelligence
        sa.Column('related_insight_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_anomaly_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_recommendation_ids', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Scores
        sa.Column('scores', postgresql.JSONB, nullable=False),
        
        # Status
        sa.Column('status', sa.String(20), server_default='discovered', nullable=False),
        
        # Audit
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intelligence_root_causes_tenant_id', 'intelligence_root_causes', ['tenant_id'])
    op.create_index('ix_intelligence_root_causes_metric', 'intelligence_root_causes', ['subject_metric_id'])
    op.create_index('ix_intelligence_root_causes_status', 'intelligence_root_causes', ['status'])
    op.create_index('ix_intelligence_root_causes_period', 'intelligence_root_causes', ['period_start', 'period_end'])

    # Intelligence Anomalies
    op.create_table(
        'intelligence_anomalies',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        
        # Classification
        sa.Column('anomaly_type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False),
        
        # Detection
        sa.Column('detection_method', sa.String(50), nullable=True),
        sa.Column('detection_algorithm', sa.String(100), nullable=True),
        
        # Context
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('detailed_explanation', sa.Text, nullable=True),
        
        # Metric context
        sa.Column('metric_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('metric_definitions.id'), nullable=True),
        sa.Column('metric_code', sa.String(50), nullable=True),
        
        # What was observed
        sa.Column('observed_value', sa.Float, nullable=True),
        sa.Column('expected_value', sa.Float, nullable=True),
        sa.Column('deviation_absolute', sa.Float, nullable=True),
        sa.Column('deviation_percent', sa.Float, nullable=True),
        
        # Statistical properties
        sa.Column('z_score', sa.Float, nullable=True),
        sa.Column('p_value', sa.Float, nullable=True),
        sa.Column('confidence_interval', postgresql.JSONB, nullable=True),
        
        # Baseline
        sa.Column('baseline_value', sa.Float, nullable=True),
        sa.Column('baseline_type', sa.String(50), nullable=True),
        sa.Column('baseline_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('baseline_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('baseline_std_dev', sa.Float, nullable=True),
        
        # Root cause
        sa.Column('root_cause_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('root_cause_description', sa.Text, nullable=True),
        
        # Business impact
        sa.Column('business_impact', postgresql.JSONB, nullable=True),
        sa.Column('impact_amount', sa.Float, nullable=True),
        sa.Column('affected_transactions', sa.Integer(), nullable=True),
        sa.Column('affected_scope', sa.String(500), nullable=True),
        
        # Recommendation
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recommended_action', sa.Text, nullable=True),
        
        # Temporal
        sa.Column('anomaly_duration_periods', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_persistent', sa.Boolean(), server_default='false', nullable=False),
        
        # Status
        sa.Column('anomaly_status', sa.String(20), server_default='detected', nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        
        # Related intelligence
        sa.Column('related_insight_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('related_root_cause_ids', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Scores
        sa.Column('scores', postgresql.JSONB, nullable=False),
        
        # Period and scope
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=True),
        sa.Column('scope_type', sa.String(20), nullable=True),
        sa.Column('scope_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope_name', sa.String(200), nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), server_default='discovered', nullable=False),
        
        # Audit
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intelligence_anomalies_tenant_id', 'intelligence_anomalies', ['tenant_id'])
    op.create_index('ix_intelligence_anomalies_type', 'intelligence_anomalies', ['anomaly_type'])
    op.create_index('ix_intelligence_anomalies_severity', 'intelligence_anomalies', ['severity'])
    op.create_index('ix_intelligence_anomalies_status', 'intelligence_anomalies', ['anomaly_status'])
    op.create_index('ix_intelligence_anomalies_metric', 'intelligence_anomalies', ['metric_id'])
    op.create_index('ix_intelligence_anomalies_period', 'intelligence_anomalies', ['period_start', 'period_end'])

    # Intelligence Opportunities
    op.create_table(
        'intelligence_opportunities',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        
        # Classification
        sa.Column('opportunity_type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('subcategory', sa.String(100), nullable=True),
        
        # Content
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('detailed_description', sa.Text, nullable=True),
        
        # Financial value
        sa.Column('estimated_value', sa.Float, nullable=True),
        sa.Column('value_unit', sa.String(20), nullable=True),
        sa.Column('value_range_low', sa.Float, nullable=True),
        sa.Column('value_range_high', sa.Float, nullable=True),
        sa.Column('value_confidence', sa.Float, nullable=True),
        
        # Value breakdown
        sa.Column('value_breakdown', postgresql.JSONB, nullable=True),
        sa.Column('baseline_metric_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('baseline_value', sa.Float, nullable=True),
        sa.Column('target_value', sa.Float, nullable=True),
        sa.Column('improvement_potential', sa.Float, nullable=True),
        
        # Effort and risk
        sa.Column('effort_level', sa.String(20), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=True),
        sa.Column('implementation_effort_hours', sa.Float, nullable=True),
        sa.Column('time_to_realize_months', sa.Float, nullable=True),
        sa.Column('roi', sa.Float, nullable=True),
        sa.Column('roi_rank', sa.Integer(), nullable=True),
        
        # Dependencies
        sa.Column('prerequisites', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('dependencies_on_opportunities', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('blocks_opportunities', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Actions
        sa.Column('recommended_actions', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('success_criteria', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('failure_risks', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Owner
        sa.Column('suggested_owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('owner_name', sa.String(200), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        
        # Status
        sa.Column('opportunity_status', sa.String(20), server_default='identified', nullable=False),
        sa.Column('realized_value', sa.Float, nullable=True),
        sa.Column('realized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('realized_notes', sa.Text, nullable=True),
        
        # Context
        sa.Column('discovery_method', sa.String(50), nullable=True),
        sa.Column('source_opportunity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_metric_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('related_insight_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('related_recommendation_ids', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Scores
        sa.Column('scores', postgresql.JSONB, nullable=False),
        
        # Period and scope
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=True),
        sa.Column('scope_type', sa.String(20), nullable=True),
        sa.Column('scope_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope_name', sa.String(200), nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), server_default='discovered', nullable=False),
        
        # Audit
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intelligence_opportunities_tenant_id', 'intelligence_opportunities', ['tenant_id'])
    op.create_index('ix_intelligence_opportunities_type', 'intelligence_opportunities', ['opportunity_type'])
    op.create_index('ix_intelligence_opportunities_status', 'intelligence_opportunities', ['opportunity_status'])
    op.create_index('ix_intelligence_opportunities_value', 'intelligence_opportunities', ['estimated_value'])
    op.create_index('ix_intelligence_opportunities_period', 'intelligence_opportunities', ['period_start', 'period_end'])

    # Intelligence Recommendations
    op.create_table(
        'intelligence_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        
        # Classification
        sa.Column('recommendation_type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        
        # Content
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('detailed_recommendation', sa.Text, nullable=True),
        
        # Evidence chain
        sa.Column('evidence_chain', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('supporting_insight_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('supporting_anomaly_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('supporting_root_cause_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('supporting_opportunity_ids', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Expected impact
        sa.Column('expected_impact_value', sa.Float, nullable=True),
        sa.Column('expected_impact_unit', sa.String(20), nullable=True),
        sa.Column('impact_direction', sa.String(50), nullable=True),
        sa.Column('confidence_in_impact', sa.Float, nullable=True),
        sa.Column('impact_calculation', sa.Text, nullable=True),
        
        # Implementation
        sa.Column('recommended_actions', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('estimated_effort_hours', sa.Float, nullable=True),
        sa.Column('time_to_implement_months', sa.Float, nullable=True),
        sa.Column('success_metrics', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('failure_risks', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Prioritization
        sa.Column('priority_score', sa.Float, nullable=True),
        sa.Column('priority_rank', sa.Integer(), nullable=True),
        sa.Column('priority_rationale', sa.Text, nullable=True),
        
        # Status
        sa.Column('recommendation_status', sa.String(20), server_default='proposed', nullable=False),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text, nullable=True),
        sa.Column('implemented_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('implemented_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('implementation_result', sa.Text, nullable=True),
        sa.Column('actual_vs_expected_impact', sa.Float, nullable=True),
        
        # Assignment
        sa.Column('assigned_to_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_to_name', sa.String(200), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        
        # Generation
        sa.Column('generation_method', sa.String(50), nullable=True),
        sa.Column('generated_by_model', sa.String(100), nullable=True),
        
        # Scores
        sa.Column('scores', postgresql.JSONB, nullable=False),
        
        # Period and scope
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=True),
        sa.Column('scope_type', sa.String(20), nullable=True),
        sa.Column('scope_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope_name', sa.String(200), nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), server_default='discovered', nullable=False),
        
        # Audit
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intelligence_recommendations_tenant_id', 'intelligence_recommendations', ['tenant_id'])
    op.create_index('ix_intelligence_recommendations_type', 'intelligence_recommendations', ['recommendation_type'])
    op.create_index('ix_intelligence_recommendations_status', 'intelligence_recommendations', ['recommendation_status'])
    op.create_index('ix_intelligence_recommendations_priority', 'intelligence_recommendations', ['priority_score'])
    op.create_index('ix_intelligence_recommendations_period', 'intelligence_recommendations', ['period_start', 'period_end'])

    # Intelligence Briefings
    op.create_table(
        'intelligence_briefings',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        
        # Briefing identity
        sa.Column('briefing_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        
        # Period
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=True),
        
        # Comparison
        sa.Column('comparison_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('comparison_period_end', sa.DateTime(timezone=True), nullable=True),
        
        # Recipients
        sa.Column('recipient_ids', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('recipient_emails', postgresql.JSONB, server_default='[]', nullable=False),
        sa.Column('recipient_roles', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Sections
        sa.Column('sections', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Summary
        sa.Column('executive_summary', postgresql.JSONB, nullable=True),
        
        # Highlights
        sa.Column('key_highlights', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Metrics snapshot
        sa.Column('metrics_snapshot', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Narrative
        sa.Column('narrative', sa.Text, nullable=True),
        
        # Attachments
        sa.Column('attachment_urls', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Status
        sa.Column('briefing_status', sa.String(20), server_default='draft', nullable=False),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finalized_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Distribution
        sa.Column('distributed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('distribution_channels', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Versioning
        sa.Column('is_update', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('previous_briefing_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Generation
        sa.Column('generation_method', sa.String(50), nullable=True),
        sa.Column('generation_duration_ms', sa.Integer(), nullable=True),
        sa.Column('generation_prompts', postgresql.JSONB, server_default='[]', nullable=False),
        
        # Scores
        sa.Column('scores', postgresql.JSONB, nullable=True),
        
        # Scope
        sa.Column('scope_type', sa.String(20), nullable=True),
        sa.Column('scope_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope_name', sa.String(200), nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), server_default='discovered', nullable=False),
        
        # Audit
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intelligence_briefings_tenant_id', 'intelligence_briefings', ['tenant_id'])
    op.create_index('ix_intelligence_briefings_type', 'intelligence_briefings', ['briefing_type'])
    op.create_index('ix_intelligence_briefings_status', 'intelligence_briefings', ['briefing_status'])
    op.create_index('ix_intelligence_briefings_period', 'intelligence_briefings', ['period_start', 'period_end'])

    # Intelligence Graph Nodes
    op.create_table(
        'intelligence_graph_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        
        # Node type
        sa.Column('node_type', sa.String(50), nullable=False),
        sa.Column('node_subtype', sa.String(100), nullable=True),
        
        # Entity reference
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Node properties
        sa.Column('label', sa.String(500), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('primary_value', sa.Float, nullable=True),
        
        # Graph-specific
        sa.Column('importance_score', sa.Float, server_default='0', nullable=False),
        sa.Column('influence_score', sa.Float, server_default='0', nullable=False),
        
        # Temporal
        sa.Column('first_observed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_observed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('observation_count', sa.Integer(), server_default='1', nullable=False),
        
        # Status
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('merged_into_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Audit
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intelligence_graph_nodes_tenant_id', 'intelligence_graph_nodes', ['tenant_id'])
    op.create_index('ix_intelligence_graph_nodes_type', 'intelligence_graph_nodes', ['node_type'])
    op.create_index('ix_intelligence_graph_nodes_entity', 'intelligence_graph_nodes', ['entity_type', 'entity_id'])
    op.create_index('ix_intelligence_graph_nodes_status', 'intelligence_graph_nodes', ['status'])

    # Intelligence Relationships
    op.create_table(
        'intelligence_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        
        # Endpoints
        sa.Column('source_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('intelligence_graph_nodes.id'), nullable=False),
        sa.Column('target_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('intelligence_graph_nodes.id'), nullable=False),
        
        # Relationship type
        sa.Column('relationship_type', sa.String(50), nullable=False),
        sa.Column('relationship_subtype', sa.String(100), nullable=True),
        
        # Strength metrics
        sa.Column('correlation_strength', sa.Float, server_default='0', nullable=False),
        sa.Column('causal_strength', sa.Float, nullable=True),
        sa.Column('confidence', sa.Float, server_default='0', nullable=False),
        
        # Context
        sa.Column('context', sa.Text, nullable=True),
        sa.Column('evidence_count', sa.Integer(), server_default='0', nullable=False),
        
        # Temporal
        sa.Column('first_observed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_observed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_historical', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deprecated_at', sa.DateTime(timezone=True), nullable=True),
        
        # Audit
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intelligence_relationships_tenant_id', 'intelligence_relationships', ['tenant_id'])
    op.create_index('ix_intelligence_relationships_source', 'intelligence_relationships', ['source_node_id'])
    op.create_index('ix_intelligence_relationships_target', 'intelligence_relationships', ['target_node_id'])
    op.create_index('ix_intelligence_relationships_type', 'intelligence_relationships', ['relationship_type'])


def downgrade() -> None:
    op.drop_table('intelligence_relationships')
    op.drop_table('intelligence_graph_nodes')
    op.drop_table('intelligence_briefings')
    op.drop_table('intelligence_recommendations')
    op.drop_table('intelligence_opportunities')
    op.drop_table('intelligence_anomalies')
    op.drop_table('intelligence_root_causes')
    op.drop_table('intelligence_insights')
