"""
005: Financial Architecture — Currency, Exchange Rates, Tenant Currency Config.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "005_financial_architecture"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Currencies table
    op.create_table(
        "currencies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("code", sa.String(3), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("decimal_places", sa.Integer, nullable=False, server_default="2"),
        sa.Column("sub_unit", sa.String(50), nullable=False),
        sa.Column("country_codes", JSONB, nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_tenant_currency"),
    )

    # Exchange rates table
    op.create_table(
        "exchange_rates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column("target_currency", sa.String(3), nullable=False),
        sa.Column("rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("inverse_rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("effective_date", sa.Date, nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("fetched_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("is_estimated", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_confirmed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Index("ix_fx_rate_lookup", "tenant_id", "base_currency", "target_currency", "effective_date"),
    )

    # Tenant currency configuration
    op.create_table(
        "tenant_currency_config",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("transaction_currencies", JSONB, nullable=False, server_default='["INR"]'),
        sa.Column("default_transaction_currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("reporting_currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("fx_source", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("fx_update_frequency", sa.String(20), nullable=False, server_default="daily"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Monetary amounts table (immutable transaction amounts)
    op.create_table(
        "monetary_amounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount_type", sa.String(20), nullable=False, server_default="transaction"),
        sa.Column("fx_rate_id", UUID(as_uuid=True), nullable=True),
        sa.Column("converted_amount", sa.Numeric(18, 4), nullable=True),
        sa.Column("converted_currency", sa.String(3), nullable=True),
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Index("ix_monetary_entity", "entity_type", "entity_id"),
    )


def downgrade() -> None:
    op.drop_table("monetary_amounts")
    op.drop_table("tenant_currency_config")
    op.drop_table("exchange_rates")
    op.drop_table("currencies")
