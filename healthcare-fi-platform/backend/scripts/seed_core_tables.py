"""
Seed core financial tables with realistic healthcare data.
Run: python -m scripts.seed_core_tables
"""
import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/healthcare_fi"


async def seed():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get tenant_id
        result = await db.execute(text("SELECT id FROM tenants LIMIT 1"))
        tenant_row = result.first()
        if not tenant_row:
            print("No tenant found. Creating default tenant...")
            tenant_id = uuid4()
            await db.execute(
                text("INSERT INTO tenants (id, name, slug, is_active) VALUES (:id, :name, :slug, true)"),
                {"id": tenant_id, "name": "Default Hospital", "slug": "default"},
            )
        else:
            tenant_id = tenant_row[0]

        # Get existing branches, departments, payers
        result = await db.execute(text("SELECT id, name FROM branches WHERE tenant_id = :tid"), {"tid": tenant_id})
        branch_rows = result.all()
        if not branch_rows:
            print("No branches found. Create branches first.")
            return
        branch_ids = [r[0] for r in branch_rows]

        result = await db.execute(text("SELECT id, name FROM departments WHERE tenant_id = :tid"), {"tid": tenant_id})
        dept_rows = result.all()
        if not dept_rows:
            print("No departments found. Create departments first.")
            return
        dept_ids = [r[0] for r in dept_rows]

        result = await db.execute(text("SELECT id, name FROM payers WHERE tenant_id = :tid"), {"tid": tenant_id})
        payer_rows = result.all()
        if not payer_rows:
            print("No payers found. Creating default payers...")
            payer_data = [
                ("Blue Cross Blue Shield", "BCBS", "insurance"),
                ("Aetna Health", "AETNA", "insurance"),
                ("Medicare", "MCR", "government"),
                ("Medicaid", "MCD", "government"),
                ("United Healthcare", "UHC", "insurance"),
            ]
            payer_ids = []
            for name, code, ptype in payer_data:
                pid = uuid4()
                await db.execute(
                    text("INSERT INTO payers (id, tenant_id, name, code, payer_type) VALUES (:id, :tid, :name, :code, :ptype)"),
                    {"id": pid, "tid": tenant_id, "name": name, "code": code, "ptype": ptype},
                )
                payer_ids.append(pid)
        else:
            payer_ids = [r[0] for r in payer_rows]

        # Check if data already exists
        result = await db.execute(text("SELECT COUNT(*) FROM revenues WHERE tenant_id = :tid"), {"tid": tenant_id})
        count = result.scalar()
        if count and count > 0:
            print(f"Revenue data already exists ({count} records). Skipping seed.")
            return

        print(f"Seeding with tenant={tenant_id}, branches={len(branch_ids)}, depts={len(dept_ids)}, payers={len(payer_ids)}...")

        now = datetime.utcnow()

        # ── Financial Periods ─────────────────────────────────────────────
        period_ids = []
        for i in range(12):
            start = now - timedelta(days=30 * (12 - i))
            end = start + timedelta(days=29)
            pid = uuid4()
            await db.execute(
                text("INSERT INTO financial_periods (id, tenant_id, name, start_date, end_date) VALUES (:id, :tid, :name, :start, :end)"),
                {"id": pid, "tid": tenant_id, "name": f"Period {i+1}", "start": start, "end": end},
            )
            period_ids.append(pid)

        # ── Revenues (12 months x branches x depts) ──────────────────────
        revenue_count = 0
        for pi, period_id in enumerate(period_ids):
            period_start = now - timedelta(days=30 * (12 - pi))
            for branch_id in branch_ids:
                for dept_id in random.sample(dept_ids, min(4, len(dept_ids))):
                    for _ in range(random.randint(3, 6)):
                        amount = round(random.uniform(50000, 500000), 2)
                        net = round(amount * random.uniform(0.75, 0.95), 2)
                        service_date = period_start + timedelta(days=random.randint(0, 29))
                        await db.execute(
                            text("""INSERT INTO revenues (id, tenant_id, period_id, branch_id, department_id, payer_id,
                                    amount, net_amount, service_date)
                                   VALUES (:id, :tid, :pid, :bid, :did, :payid, :amt, :net, :sd)"""),
                            {
                                "id": uuid4(), "tid": tenant_id, "pid": period_id,
                                "bid": branch_id, "did": dept_id,
                                "payid": random.choice(payer_ids),
                                "amt": amount, "net": net, "sd": service_date,
                            },
                        )
                        revenue_count += 1

        # ── Expenses ──────────────────────────────────────────────────────
        expense_categories = ["salaries", "supplies", "equipment", "utilities", "maintenance", "pharmaceuticals"]
        expense_count = 0
        for pi, period_id in enumerate(period_ids):
            period_start = now - timedelta(days=30 * (12 - pi))
            for branch_id in branch_ids:
                for cat in random.sample(expense_categories, 4):
                    amount = round(random.uniform(20000, 200000), 2)
                    expense_date = period_start + timedelta(days=random.randint(0, 29))
                    await db.execute(
                        text("""INSERT INTO expenses (id, tenant_id, period_id, branch_id, department_id, category, amount, expense_date)
                               VALUES (:id, :tid, :pid, :bid, :did, :cat, :amt, :ed)"""),
                        {
                            "id": uuid4(), "tid": tenant_id, "pid": period_id,
                            "bid": branch_id, "did": random.choice(dept_ids),
                            "cat": cat, "amt": amount, "ed": expense_date,
                        },
                    )
                    expense_count += 1

        # ── Claims ────────────────────────────────────────────────────────
        claim_statuses = ["submitted", "approved", "denied", "pending"]
        claim_count = 0
        for pi, period_id in enumerate(period_ids):
            period_start = now - timedelta(days=30 * (12 - pi))
            for branch_id in branch_ids:
                for _ in range(random.randint(5, 15)):
                    total = round(random.uniform(1000, 50000), 2)
                    status = random.choice(claim_statuses)
                    approved = round(total * random.uniform(0.6, 1.0), 2) if status == "approved" else None
                    submitted = period_start + timedelta(days=random.randint(0, 29))
                    resolved = submitted + timedelta(days=random.randint(5, 30)) if status in ("approved", "denied") else None
                    await db.execute(
                        text("""INSERT INTO claims (id, tenant_id, claim_number, patient_id, branch_id, department_id, payer_id,
                                total_amount, approved_amount, status, submitted_date, resolved_date)
                               VALUES (:id, :tid, :cn, :pid, :bid, :did, :payid, :ta, :aa, :st, :sd, :rd)"""),
                        {
                            "id": uuid4(), "tid": tenant_id,
                            "cn": f"CLM-{str(uuid4())[:8]}",
                            "pid": f"PAT-{random.randint(1000, 9999)}",
                            "bid": branch_id, "did": random.choice(dept_ids),
                            "payid": random.choice(payer_ids),
                            "ta": total, "aa": approved, "st": status,
                            "sd": submitted, "rd": resolved,
                        },
                    )
                    claim_count += 1

        # ── Occupancy ─────────────────────────────────────────────────────
        occ_count = 0
        for pi in range(12):
            day = now - timedelta(days=30 * (12 - pi))
            for branch_id in branch_ids:
                for dept_id in random.sample(dept_ids, min(4, len(dept_ids))):
                    total_beds = random.randint(20, 100)
                    occupied = random.randint(int(total_beds * 0.5), total_beds)
                    rate = round(occupied / total_beds, 3)
                    await db.execute(
                        text("""INSERT INTO occupancy (id, tenant_id, branch_id, department_id, date, total_beds, occupied_beds, occupancy_rate)
                               VALUES (:id, :tid, :bid, :did, :dt, :tb, :ob, :or)"""),
                        {"id": uuid4(), "tid": tenant_id, "bid": branch_id, "did": dept_id,
                         "dt": day, "tb": total_beds, "ob": occupied, "or": rate},
                    )
                    occ_count += 1

        # ── KPIs ──────────────────────────────────────────────────────────
        kpi_data = [
            ("Total Revenue", "TOTAL_REV", "revenue", "SUM(revenues.net_amount)", "USD", 10000000),
            ("Net Profit", "NET_PROFIT", "profitability", "SUM(revenues.net_amount) - SUM(expenses.amount)", "USD", 2000000),
            ("Profit Margin", "PROFIT_MARGIN", "profitability", "(revenue - expenses) / revenue * 100", "%", 20.0),
            ("Occupancy Rate", "OCC_RATE", "occupancy", "AVG(occupancy.occupancy_rate) * 100", "%", 85.0),
            ("Claim Approval Rate", "CLAIM_RATE", "claims", "approved / total * 100", "%", 90.0),
        ]
        kpi_ids = []
        for name, code, cat, formula, unit, target in kpi_data:
            kid = uuid4()
            await db.execute(
                text("""INSERT INTO kpis (id, tenant_id, name, code, category, formula, unit, target_value)
                       VALUES (:id, :tid, :name, :code, :cat, :formula, :unit, :target)"""),
                {"id": kid, "tid": tenant_id, "name": name, "code": code, "cat": cat,
                 "formula": formula, "unit": unit, "target": target},
            )
            kpi_ids.append(kid)

        # ── KPI Values ────────────────────────────────────────────────────
        for kpi_id in kpi_ids:
            for pi, period_id in enumerate(period_ids):
                base = random.uniform(50000, 500000)
                value = base * (1 + pi * 0.02)
                await db.execute(
                    text("""INSERT INTO kpi_values (id, tenant_id, kpi_id, period_id, value, target_value, previous_value)
                           VALUES (:id, :tid, :kpi, :pid, :val, :tv, :pv)"""),
                    {"id": uuid4(), "tid": tenant_id, "kpi": kpi_id, "pid": period_id,
                     "val": round(value, 2), "tv": round(value * 1.1, 2), "pv": round(value * 0.95, 2)},
                )

        # ── Alerts ────────────────────────────────────────────────────────
        alert_data = [
            ("Revenue Drop Detected", "Monthly revenue fell below threshold", "critical", "financial"),
            ("High Claim Denial Rate", "Claim denial rate exceeds 15%", "warning", "claims"),
            ("Occupancy Below Target", "ICU occupancy dropped below 60%", "warning", "operational"),
            ("Expense Spike", "Supplies expense increased 25% MoM", "critical", "financial"),
            ("New Payer Contract", "United Healthcare contract renewal due", "info", "strategic"),
            ("Staff Overtime Alert", "Overtime costs exceeded budget by 20%", "warning", "operational"),
            ("Revenue Target Met", "Q4 revenue target achieved ahead of schedule", "info", "financial"),
            ("Bed Utilization Peak", "Bed occupancy reached 98% this week", "critical", "operational"),
        ]
        for title, msg, sev, cat in alert_data:
            await db.execute(
                text("""INSERT INTO alerts (id, tenant_id, title, message, severity, category, is_read, is_resolved)
                       VALUES (:id, :tid, :title, :msg, :sev, :cat, :read, :resolved)"""),
                {"id": uuid4(), "tid": tenant_id, "title": title, "msg": msg, "sev": sev, "cat": cat,
                 "read": random.choice([True, False]), "resolved": random.choice([True, False])},
            )

        # ── Forecasts ─────────────────────────────────────────────────────
        for branch_id in branch_ids:
            for i in range(6):
                future_date = now + timedelta(days=30 * (i + 1))
                predicted = round(random.uniform(800000, 1200000), 2)
                await db.execute(
                    text("""INSERT INTO forecasts (id, tenant_id, name, metric_type, branch_id, forecast_date, period_type,
                            predicted_value, confidence_lower, confidence_upper, confidence_score, methodology)
                           VALUES (:id, :tid, :name, :mt, :bid, :fd, :pt, :pv, :cl, :cu, :cs, :meth)"""),
                    {
                        "id": uuid4(), "tid": tenant_id,
                        "name": f"Revenue Forecast M+{i+1}",
                        "mt": "revenue", "bid": branch_id, "fd": future_date,
                        "pt": "monthly", "pv": predicted,
                        "cl": round(predicted * 0.85, 2),
                        "cu": round(predicted * 1.15, 2),
                        "cs": round(random.uniform(0.75, 0.95), 2),
                        "meth": "linear_trend",
                    },
                )

        await db.commit()
        print(f"Seeded: {len(period_ids)} periods, {revenue_count} revenues, {expense_count} expenses, "
              f"{claim_count} claims, {occ_count} occupancy records, {len(kpi_ids)} KPIs, "
              f"{len(alert_data)} alerts, {len(branch_ids)*6} forecasts")


if __name__ == "__main__":
    asyncio.run(seed())
