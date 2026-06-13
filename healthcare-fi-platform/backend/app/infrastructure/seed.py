"""
WAVE-2 Comprehensive Data Seeder
Populates ALL tables needed for the platform to display real data.
Covers: V1 tables (revenues, expenses, claims, occupancy, branches, departments,
payers, doctors, financial_periods) + V2 metric computed values + intelligence artifacts.
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# =============================================
# SEED CONFIGURATION
# =============================================
SEED_MONTHS = 24
BASE_DATE = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

BRANCHES = [
    {"id": 1, "name": "Main Hospital", "code": "MAIN"},
    {"id": 2, "name": "North Campus", "code": "NORTH"},
    {"id": 3, "name": "South Clinic", "code": "SOUTH"},
]

DEPARTMENTS = [
    {"id": 1, "name": "Emergency Department", "code": "ED", "branch_id": 1, "beds": 30},
    {"id": 2, "name": "Cardiology", "code": "CARD", "branch_id": 1, "beds": 40},
    {"id": 3, "name": "Surgical Suite", "code": "SURG", "branch_id": 1, "beds": 50},
    {"id": 4, "name": "ICU", "code": "ICU", "branch_id": 1, "beds": 20},
    {"id": 5, "name": "Pediatrics", "code": "PED", "branch_id": 2, "beds": 35},
    {"id": 6, "name": "Oncology", "code": "ONC", "branch_id": 2, "beds": 45},
    {"id": 7, "name": "Obstetrics & Gynecology", "code": "OBG", "branch_id": 3, "beds": 30},
    {"id": 8, "name": "Orthopedics", "code": "ORTH", "branch_id": 3, "beds": 40},
]

PAYERS = [
    {"id": 1, "name": "Blue Cross Blue Shield", "code": "BCBS", "payer_type": "insurance"},
    {"id": 2, "name": "Aetna", "code": "AETNA", "payer_type": "insurance"},
    {"id": 3, "name": "Medicare", "code": "MCR", "payer_type": "government"},
    {"id": 4, "name": "Medicaid", "code": "MCD", "payer_type": "government"},
    {"id": 5, "name": "United Healthcare", "code": "UHC", "payer_type": "insurance"},
    {"id": 6, "name": "Self Pay", "code": "SELF", "payer_type": "self-pay"},
    {"id": 7, "name": "Cigna", "code": "CIGNA", "payer_type": "insurance"},
]

DOCTORS = [
    {"id": 1, "name": "Dr. Sarah Mitchell", "specialization": "Emergency Medicine", "department_id": 1},
    {"id": 2, "name": "Dr. James Chen", "specialization": "Cardiology", "department_id": 2},
    {"id": 3, "name": "Dr. Priya Sharma", "specialization": "Cardiothoracic Surgery", "department_id": 3},
    {"id": 4, "name": "Dr. Michael Torres", "specialization": "Critical Care", "department_id": 4},
    {"id": 5, "name": "Dr. Emma Johnson", "specialization": "Pediatrics", "department_id": 5},
    {"id": 6, "name": "Dr. Robert Kim", "specialization": "Oncology", "department_id": 6},
    {"id": 7, "name": "Dr. Aisha Patel", "specialization": "Obstetrics", "department_id": 7},
    {"id": 8, "name": "Dr. David Walsh", "specialization": "Orthopedics", "department_id": 8},
]

# Revenue baselines per department per month (net amounts in AED/USD)
DEPT_REVENUE_BASELINE = {
    1: 850_000,   # ED
    2: 1_200_000, # Cardiology
    3: 1_800_000, # Surgery
    4: 950_000,   # ICU
    5: 650_000,   # Pediatrics
    6: 1_100_000, # Oncology
    7: 720_000,   # OBG
    8: 980_000,   # Orthopedics
}

DEPT_EXPENSE_BASELINE = {
    1: 620_000,   # ED
    2: 880_000,   # Cardiology
    3: 1_350_000, # Surgery
    4: 720_000,   # ICU
    5: 480_000,   # Pediatrics
    6: 820_000,   # Oncology
    7: 530_000,   # OBG
    8: 720_000,   # Orthopedics
}

PREDEFINED_METRICS = [
    {"code": "GROSS_REVENUE", "name": "Gross Revenue", "description": "Total revenue before deductions", "category": "revenue", "metric_type": "financial", "formula": "SUM(revenue.amount)", "formula_language": "sql", "trust_level": "gold", "is_system": True, "refresh_frequency": "daily", "dependencies": "[]", "output_schema": '{"type": "number", "format": "currency"}'},
    {"code": "NET_REVENUE", "name": "Net Revenue", "description": "Revenue after adjustments", "category": "revenue", "metric_type": "financial", "formula": "SUM(revenue.net_amount)", "formula_language": "sql", "trust_level": "gold", "is_system": True, "refresh_frequency": "daily", "dependencies": '["GROSS_REVENUE"]', "output_schema": '{"type": "number", "format": "currency"}'},
    {"code": "TOTAL_EXPENSES", "name": "Total Expenses", "description": "Total operating expenses", "category": "expense", "metric_type": "financial", "formula": "SUM(expense.amount)", "formula_language": "sql", "trust_level": "gold", "is_system": True, "refresh_frequency": "daily", "dependencies": "[]", "output_schema": '{"type": "number", "format": "currency"}'},
    {"code": "NET_MARGIN", "name": "Net Profit Margin", "description": "Net income as percentage of revenue", "category": "profitability", "metric_type": "ratio", "formula": "(NET_REVENUE - TOTAL_EXPENSES) / NET_REVENUE * 100", "formula_language": "sql", "trust_level": "gold", "is_system": True, "refresh_frequency": "daily", "dependencies": '["NET_REVENUE", "TOTAL_EXPENSES"]', "output_schema": '{"type": "number", "format": "percentage"}'},
    {"code": "OCCUPANCY_RATE", "name": "Bed Occupancy Rate", "description": "Percentage of beds occupied", "category": "operations", "metric_type": "ratio", "formula": "occupied_beds / total_beds * 100", "formula_language": "sql", "trust_level": "silver", "is_system": True, "refresh_frequency": "daily", "dependencies": "[]", "output_schema": '{"type": "number", "format": "percentage"}'},
    {"code": "CLAIM_APPROVAL_RATE", "name": "Claim Approval Rate", "description": "Percentage of claims approved", "category": "revenue_cycle", "metric_type": "ratio", "formula": "approved_claims / total_claims * 100", "formula_language": "sql", "trust_level": "silver", "is_system": True, "refresh_frequency": "weekly", "dependencies": "[]", "output_schema": '{"type": "number", "format": "percentage"}'},
    {"code": "EBITDA", "name": "EBITDA", "description": "Earnings before interest, taxes, depreciation, amortization", "category": "profitability", "metric_type": "financial", "formula": "NET_REVENUE - TOTAL_EXPENSES + DEPRECIATION", "formula_language": "sql", "trust_level": "gold", "is_system": True, "refresh_frequency": "monthly", "dependencies": '["NET_REVENUE", "TOTAL_EXPENSES"]', "output_schema": '{"type": "number", "format": "currency"}'},
    {"code": "DENIAL_RATE", "name": "Claim Denial Rate", "description": "Percentage of claims denied", "category": "revenue_cycle", "metric_type": "ratio", "formula": "denied_claims / total_claims * 100", "formula_language": "sql", "trust_level": "silver", "is_system": True, "refresh_frequency": "weekly", "dependencies": "[]", "output_schema": '{"type": "number", "format": "percentage"}'},
    {"code": "REVENUE_PER_PATIENT", "name": "Revenue Per Patient", "description": "Average revenue per patient visit", "category": "efficiency", "metric_type": "ratio", "formula": "NET_REVENUE / patient_count", "formula_language": "sql", "trust_level": "silver", "is_system": True, "refresh_frequency": "monthly", "dependencies": '["NET_REVENUE"]', "output_schema": '{"type": "number", "format": "currency"}'},
    {"code": "COST_PER_PATIENT", "name": "Cost Per Patient", "description": "Average cost per patient visit", "category": "efficiency", "metric_type": "ratio", "formula": "TOTAL_EXPENSES / patient_count", "formula_language": "sql", "trust_level": "silver", "is_system": True, "refresh_frequency": "monthly", "dependencies": '["TOTAL_EXPENSES"]', "output_schema": '{"type": "number", "format": "currency"}'},
    {"code": "HOSPITAL_SCORE", "name": "Hospital Performance Score", "description": "Composite operational health score (0-100)", "category": "composite", "metric_type": "index", "formula": "WEIGHTED(OCCUPANCY_RATE, CLAIM_APPROVAL_RATE, NET_MARGIN, EBITDA_MARGIN)", "formula_language": "bfl", "trust_level": "gold", "is_system": True, "refresh_frequency": "daily", "dependencies": '["OCCUPANCY_RATE", "CLAIM_APPROVAL_RATE", "NET_MARGIN"]', "output_schema": '{"type": "number", "format": "score"}'},
    {"code": "AVG_LENGTH_OF_STAY", "name": "Average Length of Stay", "description": "Average patient stay in days", "category": "operations", "metric_type": "metric", "formula": "SUM(stay_days) / COUNT(discharges)", "formula_language": "sql", "trust_level": "silver", "is_system": True, "refresh_frequency": "daily", "dependencies": "[]", "output_schema": '{"type": "number", "format": "days"}'},
]


def month_offset(months_back: int) -> datetime:
    """Return datetime for N months ago."""
    d = BASE_DATE - timedelta(days=30 * months_back)
    return d.replace(day=1)


def random_variance(base: float, variance_pct: float = 0.15) -> float:
    """Add random variance ±variance_pct to base value."""
    return base * (1 + random.uniform(-variance_pct, variance_pct))


def growth_factor(month_idx: int, annual_growth: float = 0.12) -> float:
    """Monthly growth factor for realistic time-series data."""
    monthly_rate = (1 + annual_growth) ** (1/12) - 1
    return (1 + monthly_rate) ** month_idx


class ComprehensiveSeeder:
    """Seeds ALL platform tables with realistic 24-month financial data."""

    def __init__(self, db: AsyncSession):
        self.db = db
        random.seed(42)  # Reproducible data

    async def check_already_seeded(self) -> bool:
        """Check if data already exists to avoid duplicate seeding."""
        result = await self.db.execute(text("SELECT COUNT(*) FROM branches"))
        count = result.scalar() or 0
        return count > 0

    # =============================================
    # V1 TABLE SEEDING (Used by dashboard, revenue, KPI pages)
    # =============================================

    async def seed_branches(self):
        for b in BRANCHES:
            await self.db.execute(text("""
                INSERT INTO branches (id, name, code, is_active, created_at)
                VALUES (:id, :name, :code, true, NOW())
                ON CONFLICT (id) DO NOTHING
            """), b)
        print(f"  ✓ Seeded {len(BRANCHES)} branches")

    async def seed_departments(self):
        for d in DEPARTMENTS:
            await self.db.execute(text("""
                INSERT INTO departments (id, name, code, branch_id, is_active, created_at)
                VALUES (:id, :name, :code, :branch_id, true, NOW())
                ON CONFLICT (id) DO NOTHING
            """), d)
        print(f"  ✓ Seeded {len(DEPARTMENTS)} departments")

    async def seed_payers(self):
        for p in PAYERS:
            await self.db.execute(text("""
                INSERT INTO payers (id, name, code, payer_type, is_active, created_at)
                VALUES (:id, :name, :code, :payer_type, true, NOW())
                ON CONFLICT (id) DO NOTHING
            """), p)
        print(f"  ✓ Seeded {len(PAYERS)} payers")

    async def seed_doctors(self):
        for d in DOCTORS:
            await self.db.execute(text("""
                INSERT INTO doctors (id, name, specialization, department_id, is_active, created_at)
                VALUES (:id, :name, :specialization, :department_id, true, NOW())
                ON CONFLICT (id) DO NOTHING
            """), d)
        print(f"  ✓ Seeded {len(DOCTORS)} doctors")

    async def seed_financial_periods(self) -> List[Dict]:
        periods = []
        for i in range(SEED_MONTHS):
            period_start = month_offset(SEED_MONTHS - 1 - i)
            period_end = period_start + timedelta(days=30)
            period_id = i + 1
            period_name = period_start.strftime("%B %Y")

            await self.db.execute(text("""
                INSERT INTO financial_periods (id, name, start_date, end_date, is_closed, created_at)
                VALUES (:id, :name, :start_date, :end_date, :is_closed, NOW())
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": period_id,
                "name": period_name,
                "start_date": period_start,
                "end_date": period_end,
                "is_closed": i < SEED_MONTHS - 2,
            })
            periods.append({"id": period_id, "start": period_start, "end": period_end})

        print(f"  ✓ Seeded {len(periods)} financial periods")
        return periods

    async def seed_revenues(self, periods: List[Dict]):
        count = 0
        for period in periods:
            month_idx = periods.index(period)
            gf = growth_factor(month_idx)

            for dept in DEPARTMENTS:
                baseline = DEPT_REVENUE_BASELINE[dept["id"]]
                dept_revenue = random_variance(baseline * gf)

                # Split across 3-5 payer transactions
                payer_weights = [0.25, 0.18, 0.22, 0.12, 0.13, 0.05, 0.05]
                for payer_idx, payer in enumerate(PAYERS):
                    amount = dept_revenue * payer_weights[payer_idx]
                    net_amount = amount * random.uniform(0.88, 0.96)  # 88-96% collection rate

                    # Generate 5-15 transactions per payer per dept per month
                    n_transactions = random.randint(5, 15)
                    for _ in range(n_transactions):
                        tx_amount = amount / n_transactions * random_variance(1.0, 0.3)
                        tx_net = tx_amount * random.uniform(0.88, 0.96)
                        service_date = period["start"] + timedelta(days=random.randint(0, 28))

                        doctor_id = next(
                            (d["id"] for d in DOCTORS if d["department_id"] == dept["id"]),
                            None
                        )

                        await self.db.execute(text("""
                            INSERT INTO revenues (period_id, branch_id, department_id, payer_id,
                                                  doctor_id, amount, net_amount, service_date, created_at)
                            VALUES (:period_id, :branch_id, :department_id, :payer_id,
                                    :doctor_id, :amount, :net_amount, :service_date, NOW())
                        """), {
                            "period_id": period["id"],
                            "branch_id": dept["branch_id"],
                            "department_id": dept["id"],
                            "payer_id": payer["id"],
                            "doctor_id": doctor_id,
                            "amount": round(tx_amount, 2),
                            "net_amount": round(tx_net, 2),
                            "service_date": service_date,
                        })
                        count += 1

        print(f"  ✓ Seeded {count:,} revenue transactions")

    async def seed_expenses(self, periods: List[Dict]):
        expense_categories = [
            ("salary", 0.55),
            ("supplies", 0.15),
            ("equipment", 0.10),
            ("utilities", 0.05),
            ("maintenance", 0.05),
            ("administrative", 0.05),
            ("other", 0.05),
        ]

        count = 0
        for period in periods:
            month_idx = periods.index(period)
            gf = growth_factor(month_idx, annual_growth=0.08)  # Expenses grow slower

            for dept in DEPARTMENTS:
                baseline = DEPT_EXPENSE_BASELINE[dept["id"]]
                dept_expenses = random_variance(baseline * gf)

                for cat, pct in expense_categories:
                    cat_amount = dept_expenses * pct * random_variance(1.0, 0.1)
                    expense_date = period["start"] + timedelta(days=random.randint(1, 27))

                    await self.db.execute(text("""
                        INSERT INTO expenses (period_id, branch_id, department_id, category,
                                             amount, description, expense_date, created_at)
                        VALUES (:period_id, :branch_id, :department_id, :category,
                                :amount, :description, :expense_date, NOW())
                    """), {
                        "period_id": period["id"],
                        "branch_id": dept["branch_id"],
                        "department_id": dept["id"],
                        "category": cat,
                        "amount": round(cat_amount, 2),
                        "description": f"{cat.title()} expenses - {dept['name']}",
                        "expense_date": expense_date,
                    })
                    count += 1

        print(f"  ✓ Seeded {count:,} expense records")

    async def seed_claims(self, periods: List[Dict]):
        statuses = ["approved", "denied", "pending", "submitted"]
        status_weights = [0.72, 0.10, 0.10, 0.08]

        count = 0
        claim_num = 1000
        for period in periods:
            for dept in DEPARTMENTS:
                n_claims = random.randint(80, 200)

                for _ in range(n_claims):
                    claim_num += 1
                    status = random.choices(statuses, status_weights)[0]
                    total_amount = random.uniform(1_500, 45_000)
                    approved_amount = (
                        total_amount * random.uniform(0.85, 0.98)
                        if status == "approved"
                        else (total_amount * random.uniform(0.0, 0.3) if status == "denied" else None)
                    )
                    submitted_date = period["start"] + timedelta(days=random.randint(0, 27))
                    resolved_date = (
                        submitted_date + timedelta(days=random.randint(5, 45))
                        if status in ["approved", "denied"]
                        else None
                    )

                    doctor_id = next(
                        (d["id"] for d in DOCTORS if d["department_id"] == dept["id"]),
                        None
                    )
                    payer_id = random.choice(PAYERS[:-1])["id"]  # Exclude self-pay mostly

                    await self.db.execute(text("""
                        INSERT INTO claims (claim_number, patient_id, branch_id, department_id,
                                           payer_id, doctor_id, total_amount, approved_amount,
                                           status, submitted_date, resolved_date, created_at)
                        VALUES (:claim_number, :patient_id, :branch_id, :department_id,
                                :payer_id, :doctor_id, :total_amount, :approved_amount,
                                :status, :submitted_date, :resolved_date, NOW())
                    """), {
                        "claim_number": f"CLM-{claim_num:06d}",
                        "patient_id": f"PAT-{random.randint(10000, 99999)}",
                        "branch_id": dept["branch_id"],
                        "department_id": dept["id"],
                        "payer_id": payer_id,
                        "doctor_id": doctor_id,
                        "total_amount": round(total_amount, 2),
                        "approved_amount": round(approved_amount, 2) if approved_amount else None,
                        "status": status,
                        "submitted_date": submitted_date,
                        "resolved_date": resolved_date,
                    })
                    count += 1

        print(f"  ✓ Seeded {count:,} claims")

    async def seed_occupancy(self, periods: List[Dict]):
        count = 0
        for period in periods:
            month_idx = periods.index(period)

            for dept in DEPARTMENTS:
                # Generate daily occupancy for the month
                for day in range(28):
                    record_date = period["start"] + timedelta(days=day)
                    total_beds = dept["beds"]
                    base_rate = 0.75 + (month_idx * 0.003)  # Slowly improving
                    occ_rate = min(0.98, random_variance(base_rate, 0.08))
                    occupied = int(total_beds * occ_rate)

                    await self.db.execute(text("""
                        INSERT INTO occupancy (branch_id, department_id, date,
                                              total_beds, occupied_beds, occupancy_rate, created_at)
                        VALUES (:branch_id, :department_id, :date,
                                :total_beds, :occupied_beds, :occupancy_rate, NOW())
                    """), {
                        "branch_id": dept["branch_id"],
                        "department_id": dept["id"],
                        "date": record_date,
                        "total_beds": total_beds,
                        "occupied_beds": occupied,
                        "occupancy_rate": round(occ_rate * 100, 2),
                    })
                    count += 1

        print(f"  ✓ Seeded {count:,} occupancy records")

    async def seed_alerts(self):
        alerts = [
            {"title": "High Denial Rate — Cardiology", "message": "Cardiology claim denial rate exceeded 15% this month, up from 9% last month. BCBS rejections increased by 67%.", "severity": "critical", "category": "revenue_cycle", "recommendation": "Review Cardiology coding practices. Schedule meeting with BCBS coordinator."},
            {"title": "Revenue Target Gap — Q4", "message": "Current revenue run-rate projects a 4.2% shortfall against Q4 target. Surgical suite utilization is the primary driver.", "severity": "warning", "category": "revenue", "recommendation": "Increase surgical suite scheduling efficiency. Consider extended operating hours on Saturdays."},
            {"title": "ICU Occupancy Critical", "message": "ICU bed occupancy reached 97% for the past 5 days. Patient boarding risk is elevated.", "severity": "critical", "category": "operations", "recommendation": "Activate overflow protocols. Accelerate discharge reviews for step-down eligible patients."},
            {"title": "Positive: ED Revenue Up 12%", "message": "Emergency Department revenue increased 12.3% month-over-month, driven by higher acuity cases and improved capture rates.", "severity": "info", "category": "revenue", "recommendation": "Maintain current ED staffing levels. Replicate triage optimization in other departments."},
            {"title": "Outstanding Claims >90 Days", "message": "43 claims exceeding AED 2.5M have been outstanding for more than 90 days. Primary payers: Medicaid (28), self-pay (15).", "severity": "warning", "category": "revenue_cycle", "recommendation": "Escalate Medicaid claims to state liaison. Initiate payment plan outreach for self-pay patients."},
            {"title": "Expense Variance — Supplies", "message": "Medical supplies expense exceeded budget by 18% in Month 3. Surgical Suite and ICU are primary contributors.", "severity": "warning", "category": "expense", "recommendation": "Conduct supplies audit. Evaluate bulk purchasing agreements with primary vendors."},
            {"title": "Net Margin Recovery", "message": "Net profit margin improved to 14.2% this month, up from 11.8% last month — highest in 6 months.", "severity": "info", "category": "profitability", "recommendation": "Continue current cost optimization initiatives. Present margin recovery story in board meeting."},
        ]

        for a in alerts:
            await self.db.execute(text("""
                INSERT INTO alerts (title, message, severity, category, is_read, is_resolved,
                                   recommendation, created_at, updated_at)
                VALUES (:title, :message, :severity, :category, false, false,
                        :recommendation, NOW(), NOW())
            """), a)

        print(f"  ✓ Seeded {len(alerts)} alerts")

    # =============================================
    # V2 TABLE SEEDING (Used by executive center, intelligence, metric studio)
    # =============================================

    async def seed_v2_tenant_hierarchy(self) -> Dict[str, Any]:
        """Seed V2 tenant/hospital hierarchy for metric_computed_values etc."""
        # Check if already exists
        result = await self.db.execute(text("SELECT id FROM tenants LIMIT 1"))
        row = result.mappings().first()
        if row:
            tenant_id = row["id"]
            result2 = await self.db.execute(text("SELECT id FROM hospitals LIMIT 1"))
            row2 = result2.mappings().first()
            hospital_id = row2["id"] if row2 else None
            return {"tenant_id": tenant_id, "hospital_id": hospital_id}

        tenant_id = uuid.uuid4()
        await self.db.execute(text("""
            INSERT INTO tenants (id, name, slug, plan, settings, is_active, created_at, updated_at)
            VALUES (:id, :name, :slug, :plan, '{}', true, NOW(), NOW())
        """), {"id": tenant_id, "name": "BuildIT Health System", "slug": "buildit-health", "plan": "enterprise"})

        group_id = uuid.uuid4()
        await self.db.execute(text("""
            INSERT INTO hospital_groups (id, tenant_id, name, legal_name, settings, is_active, created_at, updated_at)
            VALUES (:id, :tenant_id, :name, :legal_name, '{}', true, NOW(), NOW())
        """), {"id": group_id, "tenant_id": tenant_id, "name": "BuildIT Health Group", "legal_name": "BuildIT Healthcare LLC"})

        hospital_id = uuid.uuid4()
        await self.db.execute(text("""
            INSERT INTO hospitals (id, tenant_id, hospital_group_id, name, code, hospital_type,
                                   bed_count, settings, is_active, created_at, updated_at)
            VALUES (:id, :tenant_id, :hospital_group_id, :name, :code, :hospital_type,
                    :bed_count, '{}', true, NOW(), NOW())
        """), {
            "id": hospital_id, "tenant_id": tenant_id, "hospital_group_id": group_id,
            "name": "BuildIT General Hospital", "code": "BGH", "hospital_type": "acute_care", "bed_count": 290
        })

        print(f"  ✓ Seeded V2 tenant hierarchy")
        return {"tenant_id": tenant_id, "hospital_id": hospital_id}

    async def seed_metric_definitions(self, tenant_id: uuid.UUID) -> Dict[str, uuid.UUID]:
        metric_ids: Dict[str, uuid.UUID] = {}

        # Check existing
        result = await self.db.execute(
            text("SELECT code, id FROM metric_definitions WHERE tenant_id = :tid"),
            {"tid": tenant_id}
        )
        existing = {row["code"]: row["id"] for row in result.mappings()}
        if existing:
            return existing

        for m in PREDEFINED_METRICS:
            mid = uuid.uuid4()
            metric_ids[m["code"]] = mid
            await self.db.execute(text("""
                INSERT INTO metric_definitions (id, tenant_id, code, name, description, category,
                    metric_type, formula, formula_language, trust_level, is_system,
                    refresh_frequency, dependencies, output_schema, created_at, updated_at)
                VALUES (:id, :tenant_id, :code, :name, :description, :category,
                    :metric_type, :formula, :formula_language, :trust_level, :is_system,
                    :refresh_frequency, :dependencies, :output_schema, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """), {
                "id": mid, "tenant_id": tenant_id,
                "code": m["code"], "name": m["name"], "description": m["description"],
                "category": m["category"], "metric_type": m["metric_type"],
                "formula": m["formula"], "formula_language": m["formula_language"],
                "trust_level": m["trust_level"], "is_system": m["is_system"],
                "refresh_frequency": m["refresh_frequency"],
                "dependencies": m["dependencies"], "output_schema": m["output_schema"],
            })

        print(f"  ✓ Seeded {len(metric_ids)} metric definitions")
        return metric_ids

    async def seed_metric_computed_values(
        self, tenant_id: uuid.UUID, hospital_id: uuid.UUID, metric_ids: Dict[str, uuid.UUID], periods: List[Dict]
    ):
        count = 0
        for period in periods:
            month_idx = periods.index(period)
            gf = growth_factor(month_idx)

            # Compute aggregate values across all departments
            total_revenue_net = sum(DEPT_REVENUE_BASELINE[d["id"]] * gf * 0.92 for d in DEPARTMENTS)
            total_expenses = sum(DEPT_EXPENSE_BASELINE[d["id"]] * growth_factor(month_idx, 0.08) for d in DEPARTMENTS)
            ebitda = (total_revenue_net - total_expenses) * 1.12  # Add back D&A
            net_margin = ((total_revenue_net - total_expenses) / total_revenue_net * 100) if total_revenue_net > 0 else 0
            occupancy = 75 + (month_idx * 0.3) + random.uniform(-2, 2)
            denial_rate = max(4, 12 - (month_idx * 0.25) + random.uniform(-1, 1))
            hospital_score = min(95, 60 + (occupancy / 100 * 20) + (net_margin / 20 * 15) + ((100 - denial_rate) / 100 * 5))

            values = {
                "GROSS_REVENUE": total_revenue_net / 0.92,
                "NET_REVENUE": total_revenue_net,
                "TOTAL_EXPENSES": total_expenses,
                "NET_MARGIN": net_margin,
                "OCCUPANCY_RATE": min(98, occupancy),
                "CLAIM_APPROVAL_RATE": min(99, 100 - denial_rate),
                "EBITDA": ebitda,
                "DENIAL_RATE": denial_rate,
                "REVENUE_PER_PATIENT": total_revenue_net / random.randint(2800, 3200),
                "COST_PER_PATIENT": total_expenses / random.randint(2800, 3200),
                "HOSPITAL_SCORE": hospital_score,
                "AVG_LENGTH_OF_STAY": max(2.5, 5.2 - (month_idx * 0.04) + random.uniform(-0.3, 0.3)),
            }

            for code, value in values.items():
                if code in metric_ids:
                    await self.db.execute(text("""
                        INSERT INTO metric_computed_values
                        (id, tenant_id, metric_id, value, period_start, period_end, period_type,
                         scope_hospital_id, computation_time_ms, is_valid, created_at, updated_at)
                        VALUES (:id, :tenant_id, :metric_id, :value, :period_start, :period_end,
                                :period_type, :scope_hospital_id, :computation_time_ms, true, NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uuid.uuid4(), "tenant_id": tenant_id,
                        "metric_id": metric_ids[code],
                        "value": round(value, 4),
                        "period_start": period["start"],
                        "period_end": period["end"],
                        "period_type": "monthly",
                        "scope_hospital_id": hospital_id,
                        "computation_time_ms": random.randint(50, 300),
                    })
                    count += 1

        print(f"  ✓ Seeded {count} metric computed values")

    async def seed_intelligence_insights(self, tenant_id: uuid.UUID, periods: List[Dict]):
        insights = [
            {
                "insight_type": "trend",
                "title": "Revenue Growing 12% Annually",
                "summary": "Total net revenue has grown at a 12% annualized rate over the past 24 months, driven primarily by Cardiology and Surgical departments. Growth is outpacing the regional benchmark of 8%.",
                "scores": '{"confidence": 0.92, "impact": 0.85, "novelty": 0.70}',
                "period_start": periods[0]["start"],
                "period_end": periods[-1]["end"],
            },
            {
                "insight_type": "anomaly",
                "title": "Cardiology Denial Rate Spike",
                "summary": "Cardiology claim denial rate increased 6.3 percentage points in the last 2 months, from 8.2% to 14.5%. Root cause: coding changes for cardiovascular procedure bundles.",
                "scores": '{"confidence": 0.96, "impact": 0.90, "novelty": 0.80}',
                "period_start": periods[-3]["start"],
                "period_end": periods[-1]["end"],
            },
            {
                "insight_type": "opportunity",
                "title": "Orthopedics Revenue Expansion",
                "summary": "Orthopedics operates at 88% capacity during peak hours but 41% on Fridays. Adding Friday surgical slots could generate AED 2.8M incremental annual revenue.",
                "scores": '{"confidence": 0.85, "impact": 0.92, "novelty": 0.75}',
                "period_start": periods[-6]["start"],
                "period_end": periods[-1]["end"],
            },
            {
                "insight_type": "trend",
                "title": "ICU Efficiency Improving",
                "summary": "Average ICU length of stay decreased from 5.8 to 4.1 days over 12 months, improving bed turnover by 29% without adverse outcomes.",
                "scores": '{"confidence": 0.89, "impact": 0.78, "novelty": 0.65}',
                "period_start": periods[-12]["start"],
                "period_end": periods[-1]["end"],
            },
            {
                "insight_type": "correlation",
                "title": "Payer Mix Shift Impacting Margins",
                "summary": "Medicaid volume increased from 18% to 26% of total payer mix over 18 months. Medicaid reimburses at 74% of commercial rates, creating a 2.1% net margin compression.",
                "scores": '{"confidence": 0.94, "impact": 0.88, "novelty": 0.82}',
                "period_start": periods[-18]["start"],
                "period_end": periods[-1]["end"],
            },
        ]

        for ins in insights:
            await self.db.execute(text("""
                INSERT INTO intelligence_insights
                (id, tenant_id, insight_type, title, summary, scores, status,
                 scope_type, period_start, period_end, created_at, updated_at)
                VALUES (:id, :tenant_id, :insight_type, :title, :summary, :scores::jsonb,
                        'active', 'hospital', :period_start, :period_end, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """), {"id": uuid.uuid4(), "tenant_id": tenant_id, **ins})

        print(f"  ✓ Seeded {len(insights)} intelligence insights")

    async def seed_intelligence_anomalies(self, tenant_id: uuid.UUID):
        anomalies = [
            {
                "anomaly_type": "statistical",
                "severity": "high",
                "title": "Cardiology Billing Anomaly",
                "description": "Cardiology billing codes CPT-93458 and CPT-93460 show a 340% increase in volume without corresponding procedure count increase. Possible miscoding.",
                "observed_value": 3.4,
                "expected_value": 1.0,
                "deviation_percent": 240.0,
                "anomaly_status": "detected",
            },
            {
                "anomaly_type": "trend",
                "severity": "medium",
                "title": "Supply Cost Drift — ICU",
                "description": "ICU supply costs have exceeded budget for 4 consecutive months. Cumulative variance: AED 847K above plan.",
                "observed_value": 847000,
                "expected_value": 0,
                "deviation_percent": 18.5,
                "anomaly_status": "investigating",
            },
            {
                "anomaly_type": "outlier",
                "severity": "high",
                "title": "Unusual Payment Pattern — Self Pay",
                "description": "Self-pay collection rate jumped to 68% this month (baseline: 31%). 3 large accounts settled. Not a systemic improvement.",
                "observed_value": 68.0,
                "expected_value": 31.0,
                "deviation_percent": 119.4,
                "anomaly_status": "resolved",
            },
            {
                "anomaly_type": "statistical",
                "severity": "low",
                "title": "Pediatrics Weekend Occupancy Drop",
                "description": "Pediatrics weekend occupancy is 22 points below weekday levels, unusual given regional patient demand patterns.",
                "observed_value": 51.0,
                "expected_value": 73.0,
                "deviation_percent": -30.1,
                "anomaly_status": "detected",
            },
        ]

        for a in anomalies:
            await self.db.execute(text("""
                INSERT INTO intelligence_anomalies
                (id, tenant_id, anomaly_type, severity, title, description,
                 observed_value, expected_value, deviation_percent, anomaly_status,
                 scope_type, period_start, period_end, created_at, updated_at)
                VALUES (:id, :tenant_id, :anomaly_type, :severity, :title, :description,
                        :observed_value, :expected_value, :deviation_percent, :anomaly_status,
                        'hospital', NOW() - INTERVAL '7 days', NOW(), NOW(), NOW())
                ON CONFLICT DO NOTHING
            """), {"id": uuid.uuid4(), "tenant_id": tenant_id, **a})

        print(f"  ✓ Seeded {len(anomalies)} intelligence anomalies")

    async def seed_intelligence_recommendations(self, tenant_id: uuid.UUID):
        recommendations = [
            {
                "recommendation_type": "revenue_optimization",
                "title": "Renegotiate BCBS Contract Terms",
                "description": "Current BCBS reimbursement rates are 8% below market benchmark for Cardiology procedures. Renegotiation opportunity identified based on volume growth.",
                "expected_impact": 1_850_000.0,
                "effort_level": "medium",
                "status": "pending_review",
                "priority_score": 92.0,
            },
            {
                "recommendation_type": "cost_reduction",
                "title": "Consolidate Supply Chain Vendors",
                "description": "Surgical suite uses 7 supply vendors for equivalent products. Consolidating to 3 preferred vendors could yield 12-18% cost savings.",
                "expected_impact": 680_000.0,
                "effort_level": "low",
                "status": "approved",
                "priority_score": 85.0,
            },
            {
                "recommendation_type": "operational_efficiency",
                "title": "Implement Predictive Bed Management",
                "description": "ED patients wait avg 4.2 hours for inpatient bed. ML-based demand forecasting could reduce wait time by 65% and improve 3.2 beds/day utilization.",
                "expected_impact": 2_100_000.0,
                "effort_level": "high",
                "status": "pending_review",
                "priority_score": 88.0,
            },
            {
                "recommendation_type": "revenue_cycle",
                "title": "Automate Prior Authorization — Cardiology",
                "description": "72% of Cardiology denial claims cite authorization failures. Automated prior auth workflow could reduce denials by 60% and recover AED 1.1M annually.",
                "expected_impact": 1_100_000.0,
                "effort_level": "medium",
                "status": "implementing",
                "priority_score": 91.0,
            },
        ]

        for r in recommendations:
            await self.db.execute(text("""
                INSERT INTO intelligence_recommendations
                (id, tenant_id, recommendation_type, title, description,
                 expected_impact, effort_level, status, priority_score,
                 scope_type, created_at, updated_at)
                VALUES (:id, :tenant_id, :recommendation_type, :title, :description,
                        :expected_impact, :effort_level, :status, :priority_score,
                        'hospital', NOW(), NOW())
                ON CONFLICT DO NOTHING
            """), {"id": uuid.uuid4(), "tenant_id": tenant_id, **r})

        print(f"  ✓ Seeded {len(recommendations)} recommendations")

    async def seed_intelligence_briefing(self, tenant_id: uuid.UUID):
        briefing_content = {
            "headline": "Hospital performing at 82/100 — Revenue growing, ICU at capacity, 4 action items require attention",
            "sections": [
                {
                    "title": "Financial Performance",
                    "content": "Net revenue reached AED 87.3M this month, up 8.4% vs prior month and 12.2% year-over-year. EBITDA margin at 16.8%, highest in 8 months. Net profit margin: 14.2%. All revenue targets on track for Q4.",
                    "kpis": ["net_revenue", "ebitda", "net_margin"]
                },
                {
                    "title": "Operational Health",
                    "content": "Bed occupancy at 84.3%, approaching target of 85%. ICU utilization critical at 96.8% — bed management protocol activated. Average length of stay improved to 4.1 days (-0.3 vs target).",
                    "kpis": ["occupancy_rate", "avg_length_of_stay"]
                },
                {
                    "title": "Revenue Cycle",
                    "content": "Overall claim approval rate: 91.2%. Cardiology denial rate elevated at 14.5% — root cause identified as CPT coding change. 43 claims >AED 2.5M outstanding >90 days require escalation.",
                    "kpis": ["claim_approval_rate", "denial_rate"]
                },
                {
                    "title": "Action Items",
                    "items": [
                        "Escalate 43 outstanding claims to payer liaisons",
                        "Review Cardiology CPT coding — BCBS denials",
                        "Activate ICU overflow protocols",
                        "Schedule BCBS contract renegotiation meeting"
                    ]
                }
            ],
            "hospital_score": 82,
            "score_change": "+3 vs last month",
            "generated_at": datetime.now().isoformat()
        }

        import json
        await self.db.execute(text("""
            INSERT INTO intelligence_briefings
            (id, tenant_id, briefing_type, title, content, status, scope_type,
             period_start, period_end, created_at, updated_at)
            VALUES (:id, :tenant_id, 'daily', :title, :content::jsonb, 'published', 'hospital',
                    NOW() - INTERVAL '1 day', NOW(), NOW(), NOW())
            ON CONFLICT DO NOTHING
        """), {
            "id": uuid.uuid4(),
            "tenant_id": tenant_id,
            "title": f"Daily Briefing — {datetime.now().strftime('%B %d, %Y')}",
            "content": json.dumps(briefing_content),
        })

        print(f"  ✓ Seeded 1 intelligence briefing")


async def run_seeding():
    """Main seeding orchestrator. Safe to run multiple times (idempotent)."""
    from app.db.session import AsyncSessionLocal

    print("\n🌱 WAVE-2 COMPREHENSIVE DATA SEED STARTING...")
    print("=" * 55)

    async with AsyncSessionLocal() as session:
        seeder = ComprehensiveSeeder(session)

        # Check if already seeded
        if await seeder.check_already_seeded():
            print("  ⚡ Data already seeded — skipping V1 tables")
        else:
            print("\n📊 Phase A: Core Reference Data")
            await seeder.seed_branches()
            await seeder.seed_departments()
            await seeder.seed_payers()
            await seeder.seed_doctors()

            print("\n📅 Phase B: Financial Periods")
            periods = await seeder.seed_financial_periods()

            print("\n💰 Phase C: Financial Transactions (24 months)")
            await seeder.seed_revenues(periods)
            await seeder.seed_expenses(periods)
            await seeder.seed_claims(periods)
            await seeder.seed_occupancy(periods)
            await seeder.seed_alerts()
        else:
            # Still need periods for V2
            periods = [
                {"id": i+1, "start": month_offset(SEED_MONTHS - 1 - i), "end": month_offset(SEED_MONTHS - 1 - i) + timedelta(days=30)}
                for i in range(SEED_MONTHS)
            ]

        print("\n🏥 Phase D: V2 Tenant Hierarchy")
        ids = await seeder.seed_v2_tenant_hierarchy()
        tenant_id = ids["tenant_id"]
        hospital_id = ids["hospital_id"]

        if hospital_id:
            print("\n📈 Phase E: Metric Definitions + Computed Values")
            metric_ids = await seeder.seed_metric_definitions(tenant_id)
            await seeder.seed_metric_computed_values(tenant_id, hospital_id, metric_ids, periods)

        print("\n🧠 Phase F: Intelligence Layer")
        await seeder.seed_intelligence_insights(tenant_id, periods)
        await seeder.seed_intelligence_anomalies(tenant_id)
        await seeder.seed_intelligence_recommendations(tenant_id)
        await seeder.seed_intelligence_briefing(tenant_id)

        await session.commit()

    print("\n✅ WAVE-2 SEED COMPLETE")
    print("=" * 55)
    print("  The platform now has 24 months of financial data.")
    print("  All KPIs will show real values.")
    print("  Intelligence engine has data to work with.")
    print()


if __name__ == "__main__":
    asyncio.run(run_seeding())
