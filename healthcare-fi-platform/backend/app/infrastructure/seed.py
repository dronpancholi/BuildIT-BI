"""
Data seeding module for the Healthcare Financial Intelligence Platform.
Uses SQLAlchemy text() with named parameters for raw SQL inserts.
"""
import asyncio
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


PREDEFINED_METRICS = [
    {"code": "GROSS_REVENUE", "name": "Gross Revenue", "description": "Total revenue before deductions", "category": "revenue", "metric_type": "financial", "formula": "SUM(revenue.amount)", "formula_language": "sql", "trust_level": "gold", "is_system": True, "refresh_frequency": "daily", "dependencies": "[]", "output_schema": '{"type": "number", "format": "currency"}'},
    {"code": "NET_REVENUE", "name": "Net Revenue", "description": "Revenue after adjustments", "category": "revenue", "metric_type": "financial", "formula": "SUM(revenue.net_amount)", "formula_language": "sql", "trust_level": "gold", "is_system": True, "refresh_frequency": "daily", "dependencies": '["GROSS_REVENUE"]', "output_schema": '{"type": "number", "format": "currency"}'},
    {"code": "TOTAL_EXPENSES", "name": "Total Expenses", "description": "Total operating expenses", "category": "expense", "metric_type": "financial", "formula": "SUM(expense.amount)", "formula_language": "sql", "trust_level": "gold", "is_system": True, "refresh_frequency": "daily", "dependencies": "[]", "output_schema": '{"type": "number", "format": "currency"}'},
    {"code": "NET_MARGIN", "name": "Net Profit Margin", "description": "Net income as percentage of revenue", "category": "profitability", "metric_type": "ratio", "formula": "(NET_REVENUE - TOTAL_EXPENSES) / NET_REVENUE * 100", "formula_language": "sql", "trust_level": "gold", "is_system": True, "refresh_frequency": "daily", "dependencies": '["NET_REVENUE", "TOTAL_EXPENSES"]', "output_schema": '{"type": "number", "format": "percentage"}'},
    {"code": "OCCUPANCY_RATE", "name": "Bed Occupancy Rate", "description": "Percentage of beds occupied", "category": "operations", "metric_type": "ratio", "formula": "occupied_beds / total_beds * 100", "formula_language": "sql", "trust_level": "silver", "is_system": True, "refresh_frequency": "daily", "dependencies": "[]", "output_schema": '{"type": "number", "format": "percentage"}'},
    {"code": "CLAIM_APPROVAL_RATE", "name": "Claim Approval Rate", "description": "Percentage of claims approved", "category": "revenue_cycle", "metric_type": "ratio", "formula": "approved_claims / total_claims * 100", "formula_language": "sql", "trust_level": "silver", "is_system": True, "refresh_frequency": "weekly", "dependencies": "[]", "output_schema": '{"type": "number", "format": "percentage"}'},
    {"code": "AVG_LENGTH_OF_STAY", "name": "Average Length of Stay", "description": "Average patient stay in days", "category": "operations", "metric_type": "metric", "formula": "SUM(stay_days) / COUNT(discharges)", "formula_language": "sql", "trust_level": "silver", "is_system": True, "refresh_frequency": "daily", "dependencies": "[]", "output_schema": '{"type": "number", "format": "days"}'},
    {"code": "CASE_MIX_INDEX", "name": "Case Mix Index", "description": "Average DRG weight", "category": "operations", "metric_type": "metric", "formula": "AVG(drg_weight)", "formula_language": "sql", "trust_level": "silver", "is_system": True, "refresh_frequency": "monthly", "dependencies": "[]", "output_schema": '{"type": "number"}'},
    {"code": "EBITDA", "name": "EBITDA", "description": "Earnings before interest, taxes, depreciation, amortization", "category": "profitability", "metric_type": "financial", "formula": "NET_REVENUE - TOTAL_EXPENSES + DEPRECIATION + AMORTIZATION", "formula_language": "sql", "trust_level": "gold", "is_system": True, "refresh_frequency": "monthly", "dependencies": '["NET_REVENUE", "TOTAL_EXPENSES"]', "output_schema": '{"type": "number", "format": "currency"}'},
    {"code": "WORKING_CAPITAL_RATIO", "name": "Working Capital Ratio", "description": "Current assets / current liabilities", "category": "financial_health", "metric_type": "ratio", "formula": "current_assets / current_liabilities", "formula_language": "sql", "trust_level": "gold", "is_system": True, "refresh_frequency": "monthly", "dependencies": "[]", "output_schema": '{"type": "number"}'},
    {"code": "DEBT_SERVICE_COVERAGE", "name": "Debt Service Coverage Ratio", "description": "Operating income / debt service", "category": "financial_health", "metric_type": "ratio", "formula": "operating_income / debt_service", "formula_language": "sql", "trust_level": "gold", "is_system": True, "refresh_frequency": "quarterly", "dependencies": "[]", "output_schema": '{"type": "number"}'},
    {"code": "REVENUE_PER_AVAILABLE_BED", "name": "Revenue Per Available Bed", "description": "Revenue per available bed", "category": "efficiency", "metric_type": "ratio", "formula": "NET_REVENUE / available_beds", "formula_language": "sql", "trust_level": "silver", "is_system": True, "refresh_frequency": "monthly", "dependencies": '["NET_REVENUE"]', "output_schema": '{"type": "number", "format": "currency"}'},
]

PREDEFINED_QUALITY_RULES = [
    {"name": "Revenue Range Check", "description": "Revenue must be within reasonable bounds", "rule_type": "range_check", "rule_category": "financial", "severity": "critical", "entity_type": "revenue", "configuration": '{"min": 0, "max": 100000000}'},
    {"name": "Occupancy Null Check", "description": "Occupancy rate cannot be null", "rule_type": "null_check", "rule_category": "operations", "severity": "warning", "entity_type": "occupancy", "configuration": '{"field": "occupancy_rate"}'},
    {"name": "Claim Duplicate Detection", "description": "Detect duplicate claims", "rule_type": "duplicate_check", "rule_category": "revenue_cycle", "severity": "critical", "entity_type": "claim", "configuration": '{"fields": ["claim_number", "patient_id", "service_date"]}'},
    {"name": "Data Freshness Check", "description": "Data must be less than 7 days old", "rule_type": "freshness", "rule_category": "data_quality", "severity": "warning", "entity_type": "all", "configuration": '{"max_age_days": 7}'},
    {"name": "Revenue Expense Balance", "description": "Total revenue should exceed total expenses", "rule_type": "balance_check", "rule_category": "financial", "severity": "critical", "entity_type": "financial", "configuration": '{"revenue_field": "total_revenue", "expense_field": "total_expenses", "min_ratio": 1.0}'},
    {"name": "Length of Stay Reasonableness", "description": "Average length of stay should be between 1-30 days", "rule_type": "reasonableness", "rule_category": "operations", "severity": "warning", "entity_type": "operations", "configuration": '{"min": 1, "max": 30}'},
    {"name": "Bed Count Bounds", "description": "Bed count should be positive and reasonable", "rule_type": "bounds", "rule_category": "operations", "severity": "warning", "entity_type": "facility", "configuration": '{"min": 1, "max": 5000}'},
    {"name": "Date Sequence Check", "description": "Service date should not be in the future", "rule_type": "date_sequence", "rule_category": "temporal", "severity": "critical", "entity_type": "all", "configuration": '{"allow_future": false}'},
]


class DataSeeder:
    """Handles data seeding for the platform."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def seed_tenant(
        self,
        name: str,
        code: str,
        created_by: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Create a tenant and return its ID."""
        tenant_id = uuid.uuid4()

        await self.db_session.execute(
            text("""
                INSERT INTO tenants (id, tenant_id, name, code, created_by, updated_by)
                VALUES (:id, :tenant_id, :name, :code, :created_by, :updated_by)
            """),
            {"id": tenant_id, "tenant_id": tenant_id, "name": name, "code": code,
             "created_by": created_by, "updated_by": created_by},
        )

        hospital_group_id = uuid.uuid4()
        await self.db_session.execute(
            text("""
                INSERT INTO hospital_groups (id, tenant_id, name, code, created_by, updated_by)
                VALUES (:id, :tenant_id, :name, :code, :created_by, :updated_by)
            """),
            {"id": hospital_group_id, "tenant_id": tenant_id,
             "name": f"{name} Health System", "code": f"{code}_HS",
             "created_by": created_by, "updated_by": created_by},
        )

        hospital_id = uuid.uuid4()
        await self.db_session.execute(
            text("""
                INSERT INTO hospitals (id, tenant_id, hospital_group_id, name, code,
                                       hospital_type, bed_count, created_by, updated_by)
                VALUES (:id, :tenant_id, :hospital_group_id, :name, :code,
                        :hospital_type, :bed_count, :created_by, :updated_by)
            """),
            {"id": hospital_id, "tenant_id": tenant_id,
             "hospital_group_id": hospital_group_id,
             "name": f"{name} Main Hospital", "code": f"{code}_MAIN",
             "hospital_type": "acute_care", "bed_count": 200,
             "created_by": created_by, "updated_by": created_by},
        )

        branch_id = uuid.uuid4()
        await self.db_session.execute(
            text("""
                INSERT INTO branches (id, tenant_id, hospital_id, name, code,
                                      branch_type, capacity, created_by, updated_by)
                VALUES (:id, :tenant_id, :hospital_id, :name, :code,
                        :branch_type, :capacity, :created_by, :updated_by)
            """),
            {"id": branch_id, "tenant_id": tenant_id, "hospital_id": hospital_id,
             "name": f"{name} Main Branch", "code": f"{code}_MAIN_BR",
             "branch_type": "main", "capacity": 200,
             "created_by": created_by, "updated_by": created_by},
        )

        departments = [
            ("Emergency", "ED", "emergency", 30),
            ("Medical", "MED", "medical", 50),
            ("Surgical", "SUR", "surgical", 40),
            ("ICU", "ICU", "intensive_care", 20),
            ("Pediatrics", "PED", "pediatric", 30),
            ("Obstetrics", "OBS", "obstetric", 30),
        ]

        for dept_name, dept_code, dept_type, bed_count in departments:
            await self.db_session.execute(
                text("""
                    INSERT INTO departments (id, tenant_id, branch_id, name, code,
                                             department_type, created_by, updated_by)
                    VALUES (:id, :tenant_id, :branch_id, :name, :code,
                            :department_type, :created_by, :updated_by)
                """),
                {"id": uuid.uuid4(), "tenant_id": tenant_id, "branch_id": branch_id,
                 "name": dept_name, "code": dept_code, "department_type": dept_type,
                 "created_by": created_by, "updated_by": created_by},
            )

        return tenant_id

    async def seed_metric_definitions(
        self, tenant_id: uuid.UUID, created_by: Optional[uuid.UUID]
    ) -> Dict[str, uuid.UUID]:
        """Create predefined metric definitions for a tenant."""
        metric_ids: Dict[str, uuid.UUID] = {}

        for metric_def in PREDEFINED_METRICS:
            metric_id = uuid.uuid4()
            metric_ids[metric_def["code"]] = metric_id

            await self.db_session.execute(
                text("""
                    INSERT INTO metric_definitions
                    (id, tenant_id, code, name, description, category, metric_type,
                     formula, formula_language, trust_level, is_system, refresh_frequency,
                     dependencies, output_schema, created_by, updated_by)
                    VALUES (:id, :tenant_id, :code, :name, :description, :category, :metric_type,
                            :formula, :formula_language, :trust_level, :is_system, :refresh_frequency,
                            :dependencies, :output_schema, :created_by, :updated_by)
                """),
                {"id": metric_id, "tenant_id": tenant_id,
                 "code": metric_def["code"], "name": metric_def["name"],
                 "description": metric_def["description"],
                 "category": metric_def["category"],
                 "metric_type": metric_def["metric_type"],
                 "formula": metric_def["formula"],
                 "formula_language": metric_def["formula_language"],
                 "trust_level": metric_def["trust_level"],
                 "is_system": metric_def["is_system"],
                 "refresh_frequency": metric_def["refresh_frequency"],
                 "dependencies": metric_def["dependencies"],
                 "output_schema": metric_def["output_schema"],
                 "created_by": created_by, "updated_by": created_by},
            )

        return metric_ids

    async def seed_quality_rules(
        self, tenant_id: uuid.UUID, created_by: Optional[uuid.UUID]
    ) -> List[uuid.UUID]:
        """Create predefined quality rules for a tenant."""
        rule_ids: List[uuid.UUID] = []

        for rule_def in PREDEFINED_QUALITY_RULES:
            rule_id = uuid.uuid4()
            rule_ids.append(rule_id)

            await self.db_session.execute(
                text("""
                    INSERT INTO quality_rules
                    (id, tenant_id, name, description, rule_type, rule_category,
                     severity, entity_type, configuration, created_by, updated_by)
                    VALUES (:id, :tenant_id, :name, :description, :rule_type, :rule_category,
                            :severity, :entity_type, :configuration, :created_by, :updated_by)
                """),
                {"id": rule_id, "tenant_id": tenant_id,
                 "name": rule_def["name"], "description": rule_def["description"],
                 "rule_type": rule_def["rule_type"],
                 "rule_category": rule_def["rule_category"],
                 "severity": rule_def["severity"],
                 "entity_type": rule_def["entity_type"],
                 "configuration": rule_def["configuration"],
                 "created_by": created_by, "updated_by": created_by},
            )

        return rule_ids

    async def seed_sample_data(
        self,
        tenant_id: uuid.UUID,
        hospital_id: uuid.UUID,
        metric_ids: Dict[str, uuid.UUID],
        months: int = 12,
    ):
        """Generate sample metric data for testing."""
        base_date = date.today()

        for i in range(months):
            period_start = base_date - timedelta(days=30 * (i + 1))
            period_end = base_date - timedelta(days=30 * i)

            sample_values = {
                "GROSS_REVENUE": Decimal("5000000") + Decimal(str(i * 100000)),
                "NET_REVENUE": Decimal("4500000") + Decimal(str(i * 90000)),
                "TOTAL_EXPENSES": Decimal("4000000") + Decimal(str(i * 80000)),
                "NET_MARGIN": Decimal("10.0") + Decimal(str(i * 0.5)),
                "OCCUPANCY_RATE": Decimal("75.0") + Decimal(str(i * 0.5)),
                "CLAIM_APPROVAL_RATE": Decimal("85.0") + Decimal(str(i * 0.3)),
                "AVG_LENGTH_OF_STAY": Decimal("4.5") - Decimal(str(i * 0.1)),
                "CASE_MIX_INDEX": Decimal("1.2") + Decimal(str(i * 0.02)),
                "EBITDA": Decimal("800000") + Decimal(str(i * 15000)),
                "WORKING_CAPITAL_RATIO": Decimal("1.5") + Decimal(str(i * 0.05)),
                "DEBT_SERVICE_COVERAGE": Decimal("1.8") + Decimal(str(i * 0.03)),
                "REVENUE_PER_AVAILABLE_BED": Decimal("25000") + Decimal(str(i * 500)),
            }

            for metric_code, value in sample_values.items():
                if metric_code in metric_ids:
                    await self.db_session.execute(
                        text("""
                            INSERT INTO metric_computed_values
                            (id, tenant_id, metric_id, value, period_start, period_end,
                             period_type, scope_hospital_id, computation_time_ms,
                             is_valid, created_by, updated_by)
                            VALUES (:id, :tenant_id, :metric_id, :value, :period_start,
                                    :period_end, :period_type, :scope_hospital_id,
                                    :computation_time_ms, :is_valid, :created_by, :updated_by)
                        """),
                        {"id": uuid.uuid4(), "tenant_id": tenant_id,
                         "metric_id": metric_ids[metric_code],
                         "value": float(value),
                         "period_start": period_start,
                         "period_end": period_end,
                         "period_type": "monthly",
                         "scope_hospital_id": hospital_id,
                         "computation_time_ms": 150,
                         "is_valid": True,
                         "created_by": None, "updated_by": None},
                    )


async def run_seeding():
    """Main seeding function."""
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        seeder = DataSeeder(session)

        tenant_id = await seeder.seed_tenant(
            name="Default Healthcare System",
            code="DH",
        )
        print(f"Created tenant: {tenant_id}")

        metric_ids = await seeder.seed_metric_definitions(tenant_id, None)
        print(f"Created {len(metric_ids)} metric definitions")

        rule_ids = await seeder.seed_quality_rules(tenant_id, None)
        print(f"Created {len(rule_ids)} quality rules")

        result = await session.execute(
            text("SELECT id FROM hospitals WHERE tenant_id = :tid LIMIT 1"),
            {"tid": tenant_id},
        )
        row = result.mappings().first()
        hospital_id = row["id"]

        await seeder.seed_sample_data(tenant_id, hospital_id, metric_ids)
        print("Created sample metric data")

        await session.commit()

        return {
            "tenant_id": str(tenant_id),
            "metric_count": len(metric_ids),
            "rule_count": len(rule_ids),
            "status": "success",
        }


if __name__ == "__main__":
    asyncio.run(run_seeding())
