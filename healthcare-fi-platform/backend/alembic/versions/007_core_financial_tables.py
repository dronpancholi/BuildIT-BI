"""
007: Core Financial Tables — revenues, expenses, claims, occupancy, kpis, kpi_values, alerts, forecasts.
Creates tables with UUID PKs matching the existing schema (branches, departments, payers, doctors use UUID).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "007_core_financial_tables"
down_revision = "006_phase5_domains"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    ))
    existing = {row[0] for row in result}

    if "financial_periods" not in existing:
        op.create_table(
            "financial_periods",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("start_date", sa.DateTime, nullable=False),
            sa.Column("end_date", sa.DateTime, nullable=False),
            sa.Column("is_closed", sa.Boolean, server_default="false"),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        )

    if "revenues" not in existing:
        op.create_table(
            "revenues",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
            sa.Column("period_id", UUID(as_uuid=True), sa.ForeignKey("financial_periods.id"), nullable=False),
            sa.Column("branch_id", UUID(as_uuid=True), sa.ForeignKey("branches.id"), nullable=False),
            sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=False),
            sa.Column("payer_id", UUID(as_uuid=True), sa.ForeignKey("payers.id"), nullable=False),
            sa.Column("doctor_id", UUID(as_uuid=True), sa.ForeignKey("doctors.id"), nullable=True),
            sa.Column("amount", sa.Float, nullable=False),
            sa.Column("net_amount", sa.Float, nullable=False),
            sa.Column("service_date", sa.DateTime, nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("deleted_at", sa.DateTime, nullable=True),
        )
        op.create_index("idx_revenues_tenant", "revenues", ["tenant_id"])
        op.create_index("idx_revenues_service_date", "revenues", ["service_date"])

    if "expenses" not in existing:
        op.create_table(
            "expenses",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
            sa.Column("period_id", UUID(as_uuid=True), sa.ForeignKey("financial_periods.id"), nullable=False),
            sa.Column("branch_id", UUID(as_uuid=True), sa.ForeignKey("branches.id"), nullable=False),
            sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=False),
            sa.Column("category", sa.String(100), nullable=False),
            sa.Column("amount", sa.Float, nullable=False),
            sa.Column("description", sa.Text),
            sa.Column("expense_date", sa.DateTime, nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("deleted_at", sa.DateTime, nullable=True),
        )
        op.create_index("idx_expenses_tenant", "expenses", ["tenant_id"])
        op.create_index("idx_expenses_expense_date", "expenses", ["expense_date"])

    if "claims" not in existing:
        op.create_table(
            "claims",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
            sa.Column("claim_number", sa.String(100), unique=True, nullable=False),
            sa.Column("patient_id", sa.String(100), nullable=False),
            sa.Column("branch_id", UUID(as_uuid=True), sa.ForeignKey("branches.id"), nullable=False),
            sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=False),
            sa.Column("payer_id", UUID(as_uuid=True), sa.ForeignKey("payers.id"), nullable=False),
            sa.Column("doctor_id", UUID(as_uuid=True), sa.ForeignKey("doctors.id"), nullable=True),
            sa.Column("total_amount", sa.Float, nullable=False),
            sa.Column("approved_amount", sa.Float),
            sa.Column("status", sa.String(50), nullable=False),
            sa.Column("submitted_date", sa.DateTime, nullable=False),
            sa.Column("resolved_date", sa.DateTime),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("deleted_at", sa.DateTime, nullable=True),
        )
        op.create_index("idx_claims_tenant", "claims", ["tenant_id"])
        op.create_index("idx_claims_status", "claims", ["status"])

    if "occupancy" not in existing:
        op.create_table(
            "occupancy",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
            sa.Column("branch_id", UUID(as_uuid=True), sa.ForeignKey("branches.id"), nullable=False),
            sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=False),
            sa.Column("date", sa.DateTime, nullable=False),
            sa.Column("total_beds", sa.Integer, nullable=False),
            sa.Column("occupied_beds", sa.Integer, nullable=False),
            sa.Column("occupancy_rate", sa.Float, nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("deleted_at", sa.DateTime, nullable=True),
        )
        op.create_index("idx_occupancy_tenant", "occupancy", ["tenant_id"])
        op.create_index("idx_occupancy_date", "occupancy", ["date"])

    if "kpis" not in existing:
        op.create_table(
            "kpis",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("code", sa.String(50), nullable=False),
            sa.Column("category", sa.String(100), nullable=False),
            sa.Column("formula", sa.Text, nullable=False),
            sa.Column("unit", sa.String(50)),
            sa.Column("target_value", sa.Float),
            sa.Column("is_active", sa.Boolean, server_default="true"),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        )

    if "kpi_values" not in existing:
        op.create_table(
            "kpi_values",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
            sa.Column("kpi_id", UUID(as_uuid=True), sa.ForeignKey("kpis.id"), nullable=False),
            sa.Column("period_id", UUID(as_uuid=True), sa.ForeignKey("financial_periods.id"), nullable=False),
            sa.Column("branch_id", UUID(as_uuid=True), sa.ForeignKey("branches.id"), nullable=True),
            sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=True),
            sa.Column("value", sa.Float, nullable=False),
            sa.Column("target_value", sa.Float),
            sa.Column("previous_value", sa.Float),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    if "alerts" not in existing:
        op.create_table(
            "alerts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("message", sa.Text, nullable=False),
            sa.Column("severity", sa.String(50), nullable=False),
            sa.Column("category", sa.String(100), nullable=False),
            sa.Column("entity_type", sa.String(50)),
            sa.Column("entity_id", UUID(as_uuid=True)),
            sa.Column("is_read", sa.Boolean, server_default="false"),
            sa.Column("is_resolved", sa.Boolean, server_default="false"),
            sa.Column("recommendation", sa.Text),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        )

    if "forecasts" not in existing:
        op.create_table(
            "forecasts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("metric_type", sa.String(100), nullable=False),
            sa.Column("branch_id", UUID(as_uuid=True), sa.ForeignKey("branches.id"), nullable=True),
            sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=True),
            sa.Column("forecast_date", sa.DateTime, nullable=False),
            sa.Column("period_type", sa.String(50), nullable=False),
            sa.Column("predicted_value", sa.Float, nullable=False),
            sa.Column("confidence_lower", sa.Float),
            sa.Column("confidence_upper", sa.Float),
            sa.Column("confidence_score", sa.Float),
            sa.Column("methodology", sa.String(100)),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        )

    if "scenarios" not in existing:
        op.create_table(
            "scenarios",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text),
            sa.Column("created_by", UUID(as_uuid=True), nullable=False),
            sa.Column("parameters", JSONB, nullable=False),
            sa.Column("results", JSONB),
            sa.Column("status", sa.String(50), server_default="pending"),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        )


def downgrade() -> None:
    op.drop_table("scenarios")
    op.drop_table("forecasts")
    op.drop_table("alerts")
    op.drop_table("kpi_values")
    op.drop_table("kpis")
    op.drop_table("occupancy")
    op.drop_table("claims")
    op.drop_table("expenses")
    op.drop_table("revenues")
