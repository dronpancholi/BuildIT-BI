"""Seed intelligence tables with proper JSONB data via SQL strings."""
import asyncio
import uuid
import json
from datetime import datetime, timedelta
import asyncpg

DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/healthcare_fi"
TENANT_ID = "51267a17-735c-479a-979c-cd4c5f04cabb"
NOW = datetime.now()
WEEK_AGO = NOW - timedelta(days=7)
MONTH_AGO = NOW - timedelta(days=30)


def js(obj):
    """Serialize to JSON string for JSONB columns."""
    return json.dumps(obj)


async def seed_briefings(conn):
    briefings = [
        {
            "briefing_type": "daily",
            "title": "Daily Operations Briefing - Revenue Performance",
            "period_start": WEEK_AGO,
            "period_end": NOW,
            "period_type": "daily",
            "recipient_ids": js(["board", "cfo", "vp-operations"]),
            "recipient_emails": js(["board@healthcare.org", "cfo@healthcare.org"]),
            "recipient_roles": js(["board_member", "cfo", "vp_operations"]),
            "sections": js([
                {"title": "Revenue Summary", "content": "Total revenue up 3.2% week over week", "order": 1},
                {"title": "Claims Status", "content": "12 new claims pending review", "order": 2},
                {"title": "Occupancy", "content": "Current occupancy rate at 78.3%", "order": 3}
            ]),
            "executive_summary": js({"revenue_change": 3.2, "claims_pending": 12, "occupancy": 78.3}),
            "key_highlights": js(["Revenue exceeded target by $45K", "Claims approval rate improved to 87%"]),
            "metrics_snapshot": js([
                {"name": "total_revenue", "value": 1250000, "unit": "USD"},
                {"name": "claim_approval_rate", "value": 87.1, "unit": "percent"},
                {"name": "occupancy_rate", "value": 78.3, "unit": "percent"}
            ]),
            "narrative": "Revenue performance continues to exceed expectations. Claims processing efficiency has improved significantly following the recent workflow optimization.",
            "attachment_urls": js(["/reports/daily-revenue-001.pdf"]),
            "briefing_status": "published",
            "distribution_channels": js(["email", "dashboard"]),
            "is_update": False,
            "generation_method": "automated",
            "generation_duration_ms": 1200,
            "generation_prompts": js([{"type": "daily_summary", "model": "gpt-4"}]),
            "scores": js({"revenue_health": 0.85, "operational_efficiency": 0.92, "risk_level": "low"}),
            "scope_type": "organization",
            "scope_name": "Organization-wide",
            "status": "discovered",
            "version": 1,
        },
        {
            "briefing_type": "weekly",
            "title": "Weekly Executive Summary - Q2 Performance",
            "period_start": WEEK_AGO,
            "period_end": NOW,
            "period_type": "weekly",
            "recipient_ids": js(["board", "cfo", "ceo"]),
            "recipient_emails": js(["board@healthcare.org", "cfo@healthcare.org", "ceo@healthcare.org"]),
            "recipient_roles": js(["board_member", "cfo", "ceo"]),
            "sections": js([
                {"title": "Financial Performance", "content": "Q2 revenue tracking 5% above forecast", "order": 1},
                {"title": "Strategic Initiatives", "content": "AI pilot program showing promising results", "order": 2}
            ]),
            "executive_summary": js({"revenue_vs_forecast": 1.05, "strategic_initiatives_on_track": 3, "total_initiatives": 4}),
            "key_highlights": js(["Q2 revenue $2.1M vs $2.0M forecast", "AI pilot reduced claim processing time by 35%"]),
            "metrics_snapshot": js([
                {"name": "q2_revenue", "value": 2100000, "unit": "USD"},
                {"name": "forecast_variance", "value": 5.0, "unit": "percent"}
            ]),
            "narrative": "Q2 performance is exceeding expectations across all major metrics.",
            "attachment_urls": js(["/reports/weekly-exec-002.pdf"]),
            "briefing_status": "published",
            "distribution_channels": js(["email", "dashboard", "slack"]),
            "is_update": False,
            "generation_method": "automated",
            "generation_duration_ms": 2800,
            "generation_prompts": js([{"type": "weekly_summary", "model": "gpt-4"}]),
            "scores": js({"revenue_health": 0.91, "operational_efficiency": 0.88, "risk_level": "low"}),
            "scope_type": "organization",
            "scope_name": "Organization-wide",
            "status": "discovered",
            "version": 1,
        },
        {
            "briefing_type": "monthly",
            "title": "Monthly Board Briefing - Financial Overview",
            "period_start": MONTH_AGO,
            "period_end": NOW,
            "period_type": "monthly",
            "recipient_ids": js(["board"]),
            "recipient_emails": js(["board@healthcare.org"]),
            "recipient_roles": js(["board_member"]),
            "sections": js([
                {"title": "P&L Summary", "content": "Net income $340K, margin 27.2%", "order": 1},
                {"title": "Balance Sheet", "content": "Cash position strong at $1.8M", "order": 2}
            ]),
            "executive_summary": js({"net_income": 340000, "margin": 27.2, "cash_position": 1800000}),
            "key_highlights": js(["Net income $340K exceeds budget by $40K", "Cash position remains strong"]),
            "metrics_snapshot": js([
                {"name": "net_income", "value": 340000, "unit": "USD"},
                {"name": "operating_margin", "value": 27.2, "unit": "percent"}
            ]),
            "narrative": "Monthly financial performance remains strong with net income exceeding budget.",
            "attachment_urls": js(["/reports/monthly-board-003.pdf"]),
            "briefing_status": "published",
            "distribution_channels": js(["email"]),
            "is_update": False,
            "generation_method": "automated",
            "generation_duration_ms": 4500,
            "generation_prompts": js([{"type": "monthly_board", "model": "gpt-4"}]),
            "scores": js({"revenue_health": 0.82, "operational_efficiency": 0.85, "risk_level": "medium"}),
            "scope_type": "organization",
            "scope_name": "Organization-wide",
            "status": "discovered",
            "version": 1,
        }
    ]

    existing = await conn.fetchval("SELECT count(*) FROM intelligence_briefings")
    print(f"  Briefings: {existing} existing")
    inserted = 0
    for b in briefings:
        try:
            await conn.execute("""
                INSERT INTO intelligence_briefings (
                    tenant_id, briefing_type, title, period_start, period_end, period_type,
                    recipient_ids, recipient_emails, recipient_roles, sections,
                    executive_summary, key_highlights, metrics_snapshot, narrative,
                    attachment_urls, briefing_status, distribution_channels, is_update,
                    generation_method, generation_duration_ms, generation_prompts, scores,
                    scope_type, scope_name, status, version, created_at
                ) VALUES (
                    $1,$2,$3,$4,$5,$6,
                    $7::jsonb,$8::jsonb,$9::jsonb,$10::jsonb,
                    $11::jsonb,$12::jsonb,$13::jsonb,$14,
                    $15::jsonb,$16,$17::jsonb,$18,
                    $19,$20,$21::jsonb,$22::jsonb,
                    $23,$24,$25,$26,$27
                )
            """,
                uuid.UUID(TENANT_ID), b["briefing_type"], b["title"],
                b["period_start"], b["period_end"], b["period_type"],
                b["recipient_ids"], b["recipient_emails"], b["recipient_roles"], b["sections"],
                b["executive_summary"], b["key_highlights"], b["metrics_snapshot"], b["narrative"],
                b["attachment_urls"], b["briefing_status"], b["distribution_channels"], b["is_update"],
                b["generation_method"], b["generation_duration_ms"], b["generation_prompts"], b["scores"],
                b["scope_type"], b["scope_name"], b["status"], b["version"], NOW
            )
            inserted += 1
        except Exception as e:
            print(f"  Briefing insert error: {e}")
    print(f"  Inserted {inserted} briefings")


async def seed_scenarios(conn):
    scenarios = [
        {
            "name": "Aggressive Growth Strategy",
            "description": "Scenario modeling 15% revenue growth through service line expansion",
            "type": "revenue_growth",
            "status": "active",
            "assumptions": js([
                {"name": "revenue_growth_rate", "value": 0.15, "unit": "percent"},
                {"name": "new_patients_monthly", "value": 120, "unit": "count"}
            ]),
            "driver_values": js({"growth_rate": 0.15, "marketing_spend": 50000}),
            "results": js({"projected_revenue": 3450000, "projected_cost": 2760000, "projected_profit": 690000, "roi": 1.25}),
            "created_by": "financial_planning",
        },
        {
            "name": "Cost Optimization Program",
            "description": "Scenario modeling 12% cost reduction through operational efficiency",
            "type": "cost_optimization",
            "status": "active",
            "assumptions": js([
                {"name": "labor_cost_reduction", "value": 0.08, "unit": "percent"},
                {"name": "supply_chain_savings", "value": 0.15, "unit": "percent"}
            ]),
            "driver_values": js({"labor_reduction": 0.08, "supply_reduction": 0.15}),
            "results": js({"projected_savings": 312000, "implementation_cost": 180000, "net_savings": 132000, "roi": 1.73}),
            "created_by": "financial_planning",
        },
        {
            "name": "Market Expansion - Telehealth",
            "description": "Scenario modeling telehealth service launch with 200 virtual visits per month",
            "type": "market_expansion",
            "status": "draft",
            "assumptions": js([
                {"name": "virtual_visits_monthly", "value": 200, "unit": "count"},
                {"name": "avg_virtual_visit_revenue", "value": 150, "unit": "USD"}
            ]),
            "driver_values": js({"patient_adoption_rate": 0.25, "physician_availability": 0.60}),
            "results": js({"projected_monthly_revenue": 30000, "projected_monthly_cost": 18000, "roi": 1.67}),
            "created_by": "strategic_planning",
        }
    ]

    existing = await conn.fetchval("SELECT count(*) FROM strategic_scenarios")
    print(f"  Scenarios: {existing} existing")
    inserted = 0
    for s in scenarios:
        try:
            await conn.execute("""
                INSERT INTO strategic_scenarios (
                    tenant_id, name, description, type, status,
                    assumptions, driver_values, results, created_by, created_at
                ) VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8::jsonb,$9,$10)
            """,
                uuid.UUID(TENANT_ID), s["name"], s["description"],
                s["type"], s["status"],
                s["assumptions"], s["driver_values"], s["results"],
                s["created_by"], NOW
            )
            inserted += 1
        except Exception as e:
            print(f"  Scenario insert error: {e}")
    print(f"  Inserted {inserted} scenarios")


async def seed_decisions(conn):
    decisions = [
        {
            "title": "Approve Q3 Capital Expenditure - MRI Equipment",
            "description": "Purchase of new MRI machine to expand diagnostic imaging capacity",
            "category": "financial",
            "priority": "high",
            "status": "pending",
            "impact_estimate": js({"financial_impact": 850000, "timeline_months": 12, "risk_level": "medium"}),
            "deadline": NOW + timedelta(days=30),
            "context": js({"department": "Radiology", "requested_by": "Dr. Smith", "budget_approved": True}),
        },
        {
            "title": "Payer Contract Renegotiation - BlueCross",
            "description": "Renegotiate reimbursement rates with BlueCross BlueShield",
            "category": "strategic",
            "priority": "high",
            "status": "in_review",
            "impact_estimate": js({"financial_impact": 320000, "timeline_months": 6, "rate_increase_percent": 8}),
            "deadline": NOW + timedelta(days=60),
            "context": js({"payer": "BCBS", "current_rate_index": 0.92, "market_rate_index": 1.0}),
        },
        {
            "title": "Hire 5 Additional RNs for Night Shift",
            "description": "Address nursing shortage on night shift to maintain patient-to-nurse ratios",
            "category": "operational",
            "priority": "medium",
            "status": "approved",
            "impact_estimate": js({"financial_impact": 420000, "timeline_months": 3, "overtime_reduction_percent": 40}),
            "deadline": NOW + timedelta(days=45),
            "context": js({"department": "Nursing", "current_vacancies": 5, "overtime_cost_monthly": 35000}),
        },
        {
            "title": "Implement AI-Assisted Claims Processing",
            "description": "Deploy AI tool to automate initial claims review, reducing manual processing time by 35%",
            "category": "technology",
            "priority": "high",
            "status": "pending",
            "impact_estimate": js({"financial_impact": 180000, "timeline_months": 6, "efficiency_gain_percent": 35}),
            "deadline": NOW + timedelta(days=90),
            "context": js({"department": "Revenue Cycle", "current_processing_time_hours": 48}),
        },
        {
            "title": "Expand Outpatient Services - Orthopedics",
            "description": "Launch orthopedic outpatient clinic to capture growing demand",
            "category": "strategic",
            "priority": "medium",
            "status": "in_review",
            "impact_estimate": js({"financial_impact": 560000, "timeline_months": 9, "patient_volume_increase": 180}),
            "deadline": NOW + timedelta(days=120),
            "context": js({"department": "Orthopedics", "referral_leakage_percent": 22}),
        }
    ]

    existing = await conn.fetchval("SELECT count(*) FROM executive_decisions")
    print(f"  Decisions: {existing} existing")
    inserted = 0
    for d in decisions:
        try:
            await conn.execute("""
                INSERT INTO executive_decisions (
                    tenant_id, title, description, category, priority, status,
                    impact_estimate, deadline, context, created_at
                ) VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8,$9::jsonb,$10)
            """,
                d["tenant_id"] if "tenant_id" in d else uuid.UUID(TENANT_ID),
                d["title"], d["description"],
                d["category"], d["priority"], d["status"],
                d["impact_estimate"], d["deadline"],
                d["context"], NOW
            )
            inserted += 1
        except Exception as e:
            print(f"  Decision insert error: {e}")
    print(f"  Inserted {inserted} decisions")


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        print("Seeding intelligence tables with JSONB data...")
        await seed_briefings(conn)
        await seed_scenarios(conn)
        await seed_decisions(conn)
        for tbl in ["intelligence_briefings", "strategic_scenarios", "executive_decisions"]:
            count = await conn.fetchval(f"SELECT count(*) FROM {tbl}")
            print(f"  TOTAL {tbl}: {count} rows")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
