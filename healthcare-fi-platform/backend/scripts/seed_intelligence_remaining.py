"""Seed intelligence tables with correct column schemas."""
import asyncio
import uuid
import json
from datetime import datetime, timedelta
import asyncpg

DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/healthcare_fi"
TENANT_ID = "51267a17-735c-479a-979c-cd4c5f04cabb"
NOW = datetime.now()
MONTH_AGO = NOW - timedelta(days=30)
WEEK_AGO = NOW - timedelta(days=7)


async def seed_insights(conn):
    existing = await conn.fetchval("SELECT count(*) FROM intelligence_insights")
    print(f"  insights: {existing} existing")
    if existing > 0:
        return

    insights = [
        ("revenue_growth", "Revenue Growth Trend", "Recurring revenue growing 12% QoQ", "high", 0.89),
        ("claims_pattern", "Claims Denial Pattern", "Systematic denials for modifier -25", "critical", 0.95),
        ("occupancy_trend", "Weekend Occupancy Gap", "Weekend occupancy 15% below weekday", "medium", 0.82),
        ("payer_mix", "Payer Mix Shift", "Commercial mix declining 3 points", "high", 0.87),
        ("cost_trend", "Cost Per Case Rising", "Average cost per case up 8%", "medium", 0.78),
        ("labor_cost", "Overtime Spike", "Overtime hours up 40% in March", "high", 0.91),
        ("supply_chain", "Supply Chain Savings", "GPO renegotiation opportunity", "low", 0.75),
        ("telehealth", "Telehealth Adoption", "Telehealth doubled but reimbursement lagging", "medium", 0.83),
        ("ar_aging", "AR Days Increasing", "Days in AR from 38 to 45", "high", 0.88),
        ("patient_experience", "HCAHPS Dip", "Scores dropped 4 points in Q2", "medium", 0.80),
    ]

    for insight_type, title, summary, priority, confidence in insights:
        await conn.execute("""
            INSERT INTO intelligence_insights (
                id, tenant_id, insight_type, title, summary, status,
                scores, period_start, period_end, period_type, created_at
            ) VALUES ($1,$2,$3,$4,$5,'discovered',$6::jsonb,$7,$8,$9,$10)
        """, uuid.uuid4(), uuid.UUID(TENANT_ID), insight_type, title, summary,
             json.dumps({"priority": {"high": 3, "critical": 4, "medium": 2, "low": 1}[priority], "confidence": confidence}),
             MONTH_AGO, NOW, "monthly", NOW)
    print(f"  Inserted {len(insights)} insights")


async def seed_recommendations(conn):
    existing = await conn.fetchval("SELECT count(*) FROM intelligence_recommendations")
    print(f"  recommendations: {existing} existing")
    if existing > 0:
        return

    recs = [
        ("actionable", "billing_optimization", "Renegotiate Medicare modifier -25 billing", 125000, "high"),
        ("actionable", "occupancy_improvement", "Implement weekend occupancy incentive", 85000, "medium"),
        ("actionable", "revenue_growth", "Accelerate VBC contract enrollment", 340000, "high"),
        ("actionable", "cost_reduction", "Audit overtime approval workflow", 67000, "high"),
        ("actionable", "cost_reduction", "Negotiate GPO volume commitments", 52000, "medium"),
        ("actionable", "ar_optimization", "Deploy AR aging task force", 180000, "high"),
        ("actionable", "operational", "Expand telehealth reimbursement tracking", 45000, "medium"),
        ("actionable", "patient_experience", "Review patient experience touchpoints", 30000, "medium"),
    ]

    for rec_type, category, title, value, priority in recs:
        priority_scores = {"high": 0.9, "medium": 0.6, "low": 0.3}
        await conn.execute("""
            INSERT INTO intelligence_recommendations (
                id, tenant_id, recommendation_type, category, title,
                expected_impact_value, priority_score, recommendation_status,
                scores, period_start, period_end, period_type, status, created_at
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,'proposed',$8::jsonb,$9,$10,$11,'discovered',$12)
        """, uuid.uuid4(), uuid.UUID(TENANT_ID), rec_type, category, title,
             value, priority_scores[priority],
             json.dumps({"priority": priority, "impact_value": value}),
             MONTH_AGO, NOW, "monthly", NOW)
    print(f"  Inserted {len(recs)} recommendations")


async def seed_anomalies(conn):
    existing = await conn.fetchval("SELECT count(*) FROM intelligence_anomalies")
    print(f"  anomalies: {existing} existing")
    if existing > 0:
        return

    anomalies = [
        ("statistical", "claims", "critical", "Claims Spike", "Claims volume up 45% in single day", 200, 290, -0.31),
        ("statistical", "revenue", "critical", "Revenue Drop - Cardiology", "Cardiology revenue down 22%", 450000, 351000, 0.22),
        ("statistical", "occupancy", "medium", "East Wing Drop", "East wing occupancy dropped to 52%", 78, 52, 0.33),
        ("threshold", "financial", "high", "AR Days Breach", "Days in AR exceeded 45-day threshold", 45, 52, -0.16),
        ("statistical", "operational", "high", "Staff Cost Surge", "Staff costs 18% above budget", 280000, 330400, -0.18),
        ("statistical", "claims", "critical", "BCBS Denial Spike", "BCBS denial rate from 5% to 14%", 0.05, 0.14, -1.8),
    ]

    for anomaly_type, category, severity, title, description, expected, observed, dev_pct in anomalies:
        await conn.execute("""
            INSERT INTO intelligence_anomalies (
                id, tenant_id, anomaly_type, category, severity, title, description,
                expected_value, observed_value, deviation_percent, anomaly_status,
                scores, period_start, period_end, period_type, status, created_at
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'detected',$11::jsonb,$12,$13,$14,'discovered',$15)
        """, uuid.uuid4(), uuid.UUID(TENANT_ID), anomaly_type, category, severity, title, description,
             expected, observed, dev_pct,
             json.dumps({"severity": severity, "deviation_pct": abs(dev_pct)}),
             MONTH_AGO, NOW, "monthly", NOW)
    print(f"  Inserted {len(anomalies)} anomalies")


async def seed_opportunities(conn):
    existing = await conn.fetchval("SELECT count(*) FROM intelligence_opportunities")
    print(f"  opportunities: {existing} existing")
    if existing > 0:
        return

    opps = [
        ("strategic", "revenue", "VBC Expansion", 340000, "high", "Three high-volume payers ready for VBC"),
        ("revenue_recovery", "revenue", "Telehealth Revenue Recovery", 180000, "medium", "Telehealth visits not captured in billing"),
        ("cost_optimization", "financial", "Supply Chain Optimization", 125000, "medium", "GPO renegotiation opportunity"),
        ("process_improvement", "financial", "Revenue Cycle Automation", 280000, "high", "AI-assisted claims processing"),
        ("market_expansion", "revenue", "Orthopedic Expansion", 450000, "high", "Referral leakage at 22%"),
    ]

    for opp_type, category, title, value, risk, description in opps:
        await conn.execute("""
            INSERT INTO intelligence_opportunities (
                id, tenant_id, opportunity_type, category, title, summary,
                estimated_value, risk_level, opportunity_status,
                scores, period_start, period_end, period_type, status, created_at
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'identified',$9::jsonb,$10,$11,$12,'discovered',$13)
        """, uuid.uuid4(), uuid.UUID(TENANT_ID), opp_type, category, title, description,
             value, risk,
             json.dumps({"risk_level": risk, "estimated_value": value}),
             MONTH_AGO, NOW, "monthly", NOW)
    print(f"  Inserted {len(opps)} opportunities")


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        print("Seeding intelligence tables...")
        await seed_insights(conn)
        await seed_recommendations(conn)
        await seed_anomalies(conn)
        await seed_opportunities(conn)
        for tbl in ["intelligence_insights", "intelligence_recommendations", "intelligence_anomalies", "intelligence_opportunities"]:
            count = await conn.fetchval(f"SELECT count(*) FROM {tbl}")
            print(f"  TOTAL {tbl}: {count} rows")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
