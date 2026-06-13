"""Seed the decisions table (what DecisionModel actually maps to)."""
import asyncio
import uuid
import json
from datetime import datetime, timedelta
import asyncpg

DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/healthcare_fi"
TENANT_ID = "51267a17-735c-479a-979c-cd4c5f04cabb"
NOW = datetime.now()


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        existing = await conn.fetchval("SELECT count(*) FROM decisions")
        print(f"  decisions: {existing} existing")
        if existing > 0:
            return

        decisions = [
            ("MRI Equipment Purchase", "Q3 CapEx for new MRI machine", "investment", "proposed", "P1", "urgent",
             "financial", 850000, 850000, NOW + timedelta(days=30)),
            ("BCBS Contract Renegotiation", "Renegotiate reimbursement rates", "contract", "in_review", "P1", "scheduled",
             "strategic", 320000, None, NOW + timedelta(days=60)),
            ("Night Shift RN Hiring", "Hire 5 RNs for night shift", "staffing", "approved", "P2", "scheduled",
             "operational", 420000, 420000, NOW + timedelta(days=45)),
            ("AI Claims Processing", "Deploy AI for claims review", "technology", "proposed", "P1", "scheduled",
             "technology", 180000, 180000, NOW + timedelta(days=90)),
            ("Orthopedic Expansion", "Launch outpatient orthopedic clinic", "expansion", "in_review", "P2", "scheduled",
             "strategic", 560000, None, NOW + timedelta(days=120)),
        ]

        for title, desc, dtype, status, priority, urgency, category, est_val, est_cost, deadline in decisions:
            await conn.execute("""
                INSERT INTO decisions (
                    id, tenant_id, title, description, decision_type, status, priority, urgency,
                    category, estimated_value, estimated_cost, review_deadline, proposed_at
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
            """, uuid.uuid4(), uuid.UUID(TENANT_ID), title, desc, dtype, status, priority, urgency,
                 category, est_val, est_cost, deadline, NOW)

        count = await conn.fetchval("SELECT count(*) FROM decisions")
        print(f"  Inserted {count} decisions total")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
