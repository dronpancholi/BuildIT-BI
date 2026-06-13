"""
006: Phase 5 Domain Tables — AI CFO, Forecasting, Memory, Knowledge, Performance.
Also adds pgvector extension, indexes for mock data replacement tables, and performance indexes.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "006_phase5_domains"
down_revision = "005_financial_architecture"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── pgvector extension ──────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ═══════════════════════════════════════════════════════════════════════
    # AI CFO
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "cfo_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("preferences", JSONB, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "cfo_questions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_query", sa.Text, nullable=False),
        sa.Column("intent", sa.String(50), nullable=False),
        sa.Column("answer", JSONB, nullable=False, server_default="{}"),
        sa.Column("evidence_chain", JSONB, nullable=False, server_default="[]"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("processing_time_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "cfo_briefings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("mode", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="generated"),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("sections", JSONB, nullable=False, server_default="[]"),
        sa.Column("score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("executive_summary", sa.Text, nullable=True),
        sa.Column("key_findings", JSONB, nullable=False, server_default="[]"),
        sa.Column("actions", JSONB, nullable=False, server_default="[]"),
        sa.Column("narrative", sa.Text, nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "cfo_workspaces",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("owner_id", UUID(as_uuid=True), nullable=False),
        sa.Column("widgets", JSONB, nullable=False, server_default="[]"),
        sa.Column("layout", JSONB, nullable=False, server_default="{}"),
        sa.Column("shared", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "cfo_alert_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("metric_id", UUID(as_uuid=True), nullable=False),
        sa.Column("metric_name", sa.String(255), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("condition", JSONB, nullable=False, server_default="{}"),
        sa.Column("thresholds", JSONB, nullable=False, server_default="{}"),
        sa.Column("channels", JSONB, nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "cfo_alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("config_id", UUID(as_uuid=True), nullable=False),
        sa.Column("metric_id", UUID(as_uuid=True), nullable=False),
        sa.Column("metric_name", sa.String(255), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("value", sa.Numeric(18, 4), nullable=True),
        sa.Column("threshold", sa.Numeric(18, 4), nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_dismissed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ═══════════════════════════════════════════════════════════════════════
    # STRATEGIC PLANNING
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "strategic_scenarios",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("type", sa.String(30), nullable=False, server_default="base"),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("assumptions", JSONB, nullable=False, server_default="[]"),
        sa.Column("driver_values", JSONB, nullable=True),
        sa.Column("results", JSONB, nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "strategic_driver_trees",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("root_node_id", UUID(as_uuid=True), nullable=True),
        sa.Column("metrics", JSONB, nullable=False, server_default="[]"),
        sa.Column("calculated_results", JSONB, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "strategic_whatif_analyses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("base_values", JSONB, nullable=False, server_default="{}"),
        sa.Column("changes", JSONB, nullable=False, server_default="[]"),
        sa.Column("results", JSONB, nullable=True),
        sa.Column("impact_summary", JSONB, nullable=True),
        sa.Column("sensitivity", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ═══════════════════════════════════════════════════════════════════════
    # ENTERPRISE FORECASTING
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "forecast_models",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("parameters", JSONB, nullable=False, server_default="{}"),
        sa.Column("hyperparameters", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("training_metadata", JSONB, nullable=True),
        sa.Column("model_artifact", sa.LargeBinary, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "forecast_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("model_id", UUID(as_uuid=True), sa.ForeignKey("forecast_models.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("metric_id", sa.String(100), nullable=False),
        sa.Column("metric_name", sa.String(255), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("values", JSONB, nullable=False, server_default="[]"),
        sa.Column("metrics", JSONB, nullable=True),
        sa.Column("confidence_level", sa.Float, nullable=True),
        sa.Column("model_name", sa.String(255), nullable=True),
        sa.Column("model_type", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "forecast_monitoring_alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("model_id", UUID(as_uuid=True), sa.ForeignKey("forecast_models.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("metric_name", sa.String(255), nullable=True),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("drift_score", sa.Float, nullable=True),
        sa.Column("details", JSONB, nullable=True),
        sa.Column("is_resolved", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ═══════════════════════════════════════════════════════════════════════
    # VECTOR MEMORY (pgvector)
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "memory_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("memory_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", sa.ARRAY(sa.Float), nullable=True),
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("access_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_accessed", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_memory_records_type", "memory_records", ["tenant_id", "memory_type"])
    op.create_index("ix_memory_records_status", "memory_records", ["tenant_id", "status"])

    # ═══════════════════════════════════════════════════════════════════════
    # INSTITUTIONAL KNOWLEDGE GRAPH
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "knowledge_nodes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("node_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("properties", JSONB, nullable=False, server_default="{}"),
        sa.Column("importance_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_nodes_type", "knowledge_nodes", ["tenant_id", "node_type"])

    op.create_table(
        "knowledge_edges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("source_id", UUID(as_uuid=True), sa.ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_id", UUID(as_uuid=True), sa.ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(50), nullable=False),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("evidence", JSONB, nullable=True, server_default="[]"),
        sa.Column("properties", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_edges_source", "knowledge_edges", ["source_id"])
    op.create_index("ix_knowledge_edges_target", "knowledge_edges", ["target_id"])
    op.create_index("ix_knowledge_edges_relation", "knowledge_edges", ["tenant_id", "relation_type"])

    # ═══════════════════════════════════════════════════════════════════════
    # MULTI-CURRENCY
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "currency_entity_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("functional_currency", sa.String(3), nullable=False),
        sa.Column("reporting_currency", sa.String(3), nullable=False),
        sa.Column("consolidation_method", sa.String(30), nullable=False, server_default="full"),
        sa.Column("fx_rate_source", sa.String(100), nullable=True),
        sa.Column("is_consolidated", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "fx_rate_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column("target_currency", sa.String(3), nullable=False),
        sa.Column("rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("inverse_rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("rate_date", sa.Date, nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("is_estimated", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ═══════════════════════════════════════════════════════════════════════
    # EXECUTIVE CENTER
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "executive_decisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("impact_estimate", JSONB, nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("context", JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ═══════════════════════════════════════════════════════════════════════
    # COPILOT
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "copilot_conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("messages", JSONB, nullable=False, server_default="[]"),
        sa.Column("context", JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_copilot_conversations_user", "copilot_conversations", ["tenant_id", "user_id"])

    # ═══════════════════════════════════════════════════════════════════════
    # CAUSAL INFERENCE
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "causal_graphs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("nodes", JSONB, nullable=False, server_default="[]"),
        sa.Column("edges", JSONB, nullable=False, server_default="[]"),
        sa.Column("adjustment_set", JSONB, nullable=True, server_default="[]"),
        sa.Column("is_valid", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("validation_errors", JSONB, nullable=True, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "causal_estimates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("graph_id", UUID(as_uuid=True), sa.ForeignKey("causal_graphs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("method", sa.String(50), nullable=False),
        sa.Column("treatment", sa.String(255), nullable=False),
        sa.Column("outcome", sa.String(255), nullable=False),
        sa.Column("point_estimate", sa.Numeric(18, 8), nullable=False),
        sa.Column("confidence_interval", JSONB, nullable=True),
        sa.Column("p_value", sa.Float, nullable=True),
        sa.Column("standard_error", sa.Numeric(18, 8), nullable=True),
        sa.Column("sample_size", sa.Integer, nullable=True),
        sa.Column("assumptions", JSONB, nullable=True, server_default="[]"),
        sa.Column("is_valid", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ═══════════════════════════════════════════════════════════════════════
    # MOCK DATA REPLACEMENT TABLES
    # ═══════════════════════════════════════════════════════════════════════

    # NL Query Log (replaces mock nl_analytics history)
    op.create_table(
        "nl_query_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("intent", sa.String(50), nullable=True),
        sa.Column("entities", JSONB, nullable=True, server_default="[]"),
        sa.Column("result", JSONB, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("processing_time_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Export Jobs (replaces mock exports)
    op.create_table(
        "export_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("export_type", sa.String(20), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("file_size", sa.Integer, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Collaboration (replaces mock collaboration)
    op.create_table(
        "collaboration_comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_name", sa.String(255), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Dashboard persistence (replaces mock dashboards)
    op.create_table(
        "saved_dashboards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("owner_id", UUID(as_uuid=True), nullable=True),
        sa.Column("layout", JSONB, nullable=False, server_default="{}"),
        sa.Column("widgets", JSONB, nullable=False, server_default="[]"),
        sa.Column("is_template", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("template_category", sa.String(50), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Visualization specs (replaces mock visualization)
    op.create_table(
        "visualization_specs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("chart_type", sa.String(50), nullable=False),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        sa.Column("data_source", JSONB, nullable=True),
        sa.Column("color_scheme", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Semantic metrics + dimensions (replaces mock analytics)
    op.create_table(
        "semantic_metrics_v2",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("expression", sa.Text, nullable=False),
        sa.Column("data_type", sa.String(30), nullable=False, server_default="decimal"),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_semantic_metric_slug"),
    )

    op.create_table(
        "semantic_dimensions_v2",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("physical_name", sa.String(255), nullable=False),
        sa.Column("key_column", sa.String(255), nullable=False),
        sa.Column("data_type", sa.String(30), nullable=False, server_default="string"),
        sa.Column("cardinality", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_semantic_dimension_slug"),
    )

    # ═══════════════════════════════════════════════════════════════════════
    # PERFORMANCE INDEXES
    # ═══════════════════════════════════════════════════════════════════════

    # Intelligence layer indexes (tables from migration 002)
    op.create_index("ix_intelligence_anomalies_tenant_created", "intelligence_anomalies", ["tenant_id", "created_at"])
    op.create_index("ix_intelligence_insights_tenant_created", "intelligence_insights", ["tenant_id", "created_at"])
    op.create_index("ix_intelligence_recs_tenant_created", "intelligence_recommendations", ["tenant_id", "created_at"])

    # Materialized view cache (for performance)
    op.create_table(
        "materialized_view_cache",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("query_hash", sa.String(64), nullable=False),
        sa.Column("cached_data", JSONB, nullable=False),
        sa.Column("row_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_refreshed", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ttl_seconds", sa.Integer, nullable=False, server_default="300"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_mv_cache_lookup", "materialized_view_cache", ["tenant_id", "query_hash"])


def downgrade() -> None:
    op.drop_table("materialized_view_cache")
    op.drop_table("semantic_dimensions_v2")
    op.drop_table("semantic_metrics_v2")
    op.drop_table("visualization_specs")
    op.drop_table("saved_dashboards")
    op.drop_table("collaboration_comments")
    op.drop_table("export_jobs")
    op.drop_table("nl_query_log")
    op.drop_table("causal_estimates")
    op.drop_table("causal_graphs")
    op.drop_table("copilot_conversations")
    op.drop_table("executive_decisions")
    op.drop_table("fx_rate_snapshots")
    op.drop_table("currency_entity_configs")
    op.drop_table("knowledge_edges")
    op.drop_table("knowledge_nodes")
    op.drop_table("memory_records")
    op.drop_table("forecast_monitoring_alerts")
    op.drop_table("forecast_results")
    op.drop_table("forecast_models")
    op.drop_table("strategic_whatif_analyses")
    op.drop_table("strategic_driver_trees")
    op.drop_table("strategic_scenarios")
    op.drop_table("cfo_alerts")
    op.drop_table("cfo_alert_configs")
    op.drop_table("cfo_workspaces")
    op.drop_table("cfo_briefings")
    op.drop_table("cfo_questions")
    op.drop_table("cfo_profiles")
    op.execute("DROP EXTENSION IF EXISTS vector")
