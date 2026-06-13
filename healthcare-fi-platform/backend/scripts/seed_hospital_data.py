#!/usr/bin/env python3
"""
Seed script for Healthcare FI Platform.
Creates tables and seeds 3 hospitals with 36 months of data,
knowledge graph nodes/edges, memory records, decisions, and forecasts.
"""

import asyncio
import random
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.infrastructure.persistence.models import (
    Base,
    KnowledgeNodeModel,
    KnowledgeEdgeModel,
    MemoryRecordModel,
    ExecutiveDecisionModel,
    ForecastModelModel,
    ForecastResultModel,
)

TENANT_ID = "00000000-0000-0000-0000-000000000001"
BASE_DATE = date(2024, 1, 1)

HOSPITALS = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "name": "Metropolitan Multi-Specialty Medical Center",
        "short_name": "Metropolitan",
        "beds": 450,
        "departments": [
            ("Emergency Medicine", "EMRG", "emergency"),
            ("Cardiology", "CARD", "specialty"),
            ("Orthopedics", "ORTH", "specialty"),
            ("Neurology", "NEUR", "specialty"),
            ("Pediatrics", "PEDS", "pediatric"),
            ("Oncology", "ONCL", "specialty"),
        ],
        "base_revenue": 8_500_000.0,
        "growth_rate": 0.008,
        "volatility": 0.04,
        "base_denial_rate": 0.082,
        "base_ar_days": 38,
        "base_occupancy": 0.84,
        "anomalies": {
            18: {"metric": "revenue", "factor": 0.88},
            24: {"metric": "denial_rate", "factor": 2.24},
            30: {"metric": "ar_days", "factor": 1.53},
        },
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "name": "Riverside Cardiac Center",
        "short_name": "Riverside",
        "beds": 180,
        "departments": [
            ("Cardiac Surgery", "CSUR", "surgical"),
            ("Interventional Cardiology", "ICAR", "specialty"),
            ("Cardiac Imaging", "CIMG", "diagnostic"),
            ("Heart Failure Clinic", "HFLC", "specialty"),
            ("Cardiac Rehabilitation", "CREH", "rehabilitation"),
        ],
        "base_revenue": 4_200_000.0,
        "growth_rate": 0.012,
        "volatility": 0.06,
        "base_denial_rate": 0.061,
        "base_ar_days": 44,
        "base_occupancy": 0.91,
        "anomalies": {
            15: {"metric": "occupancy", "factor": 0.78},
            16: {"metric": "occupancy", "factor": 0.78},
            17: {"metric": "occupancy", "factor": 0.78},
        },
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000003"),
        "name": "University Teaching Hospital",
        "short_name": "University",
        "beds": 620,
        "departments": [
            ("General Surgery", "GSUR", "surgical"),
            ("Internal Medicine", "IMED", "general"),
            ("Obstetrics & Gynecology", "OBGN", "specialty"),
            ("Psychiatry", "PSYC", "specialty"),
            ("Radiology", "RADL", "diagnostic"),
            ("Pathology", "PATH", "diagnostic"),
        ],
        "base_revenue": 14_800_000.0,
        "growth_rate": 0.005,
        "volatility": 0.05,
        "base_denial_rate": 0.094,
        "base_ar_days": 52,
        "base_occupancy": 0.89,
        "anomalies": {},
    },
]


def generate_monthly_metrics(hospital: dict, rng: random.Random):
    """Generate 36 months of financial metrics for a hospital."""
    months = []
    for m in range(36):
        month_date = BASE_DATE + timedelta(days=32 * m)
        month_date = month_date.replace(day=1)
        month_label = month_date.strftime("%Y-%m")

        growth_factor = (1 + hospital["growth_rate"]) ** m
        seasonal = 1.0 + 0.03 * (1 if month_date.month in (1, 6, 9, 12) else -1 if month_date.month in (2, 7) else 0)
        noise = 1.0 + rng.gauss(0, hospital["volatility"])

        revenue = hospital["base_revenue"] * growth_factor * seasonal * noise
        denial_rate = hospital["base_denial_rate"] * (1 + rng.gauss(0, 0.1))
        denial_rate = max(0.01, min(0.25, denial_rate))
        ar_days = hospital["base_ar_days"] * (1 + rng.gauss(0, 0.08))
        ar_days = max(15, min(90, ar_days))
        occupancy = hospital["base_occupancy"] * (1 + rng.gauss(0, 0.05))
        occupancy = max(0.40, min(0.99, occupancy))

        anomalies = hospital.get("anomalies", {})
        month_num = m + 1
        if month_num in anomalies:
            a = anomalies[month_num]
            if a["metric"] == "revenue":
                revenue *= a["factor"]
            elif a["metric"] == "denial_rate":
                denial_rate = hospital["base_denial_rate"] * a["factor"]
            elif a["metric"] == "ar_days":
                ar_days = hospital["base_ar_days"] * a["factor"]
            elif a["metric"] == "occupancy":
                occupancy = hospital["base_occupancy"] * a["factor"]

        expense_ratio = 0.72 + rng.gauss(0, 0.03)
        expenses = revenue * expense_ratio
        net_income = revenue - expenses
        collections = revenue * (1 - denial_rate)
        claim_volume = int(rng.uniform(800, 1500) * (hospital["beds"] / 200))

        months.append({
            "month": month_num,
            "month_date": month_date,
            "month_label": month_label,
            "revenue": round(revenue, 2),
            "expenses": round(expenses, 2),
            "net_income": round(net_income, 2),
            "denial_rate": round(denial_rate, 4),
            "ar_days": round(ar_days, 1),
            "occupancy": round(occupancy, 4),
            "collections": round(collections, 2),
            "claim_volume": claim_volume,
        })
    return months


def build_knowledge_nodes(hospital: dict, metrics: list):
    """Create knowledge graph nodes: 1 hospital node + 1 per department."""
    nodes = []

    hospital_node_id = uuid.uuid4()
    avg_revenue = sum(m["revenue"] for m in metrics) / len(metrics)
    nodes.append({
        "id": hospital_node_id,
        "tenant_id": TENANT_ID,
        "node_type": "hospital",
        "name": hospital["name"],
        "description": f"{hospital['beds']}-bed hospital with {len(hospital['departments'])} departments",
        "properties": {
            "total_beds": hospital["beds"],
            "department_count": len(hospital["departments"]),
            "avg_monthly_revenue": round(avg_revenue, 2),
        },
        "importance_score": 1.0,
    })

    dept_node_ids = []
    for i, (dept_name, dept_code, dept_type) in enumerate(hospital["departments"]):
        dept_node_id = uuid.uuid4()
        dept_node_ids.append(dept_node_id)
        dept_revenue_share = 1.0 / len(hospital["departments"])
        dept_avg_rev = avg_revenue * dept_revenue_share
        nodes.append({
            "id": dept_node_id,
            "tenant_id": TENANT_ID,
            "node_type": "department",
            "name": dept_name,
            "description": f"{dept_type} department (code: {dept_code})",
            "properties": {
                "code": dept_code,
                "department_type": dept_type,
                "estimated_monthly_revenue": round(dept_avg_rev, 2),
                "hospital_id": str(hospital["id"]),
            },
            "importance_score": round(0.5 + random.random() * 0.3, 2),
        })

    return hospital_node_id, dept_node_ids, nodes


def build_knowledge_edges(hospital_node_id, dept_node_ids, hospital: dict):
    """Create edges: departments -> hospital, departments -> revenue metric nodes."""
    edges = []
    for dept_id in dept_node_ids:
        edges.append({
            "id": uuid.uuid4(),
            "tenant_id": TENANT_ID,
            "source_id": dept_id,
            "target_id": hospital_node_id,
            "relation_type": "belongs_to",
            "weight": 1.0,
            "confidence": 1.0,
            "evidence": [],
            "properties": {"relationship": "organizational"},
        })

    for i, dept_id in enumerate(dept_node_ids):
        for j, other_dept_id in enumerate(dept_node_ids):
            if i < j:
                edges.append({
                    "id": uuid.uuid4(),
                    "tenant_id": TENANT_ID,
                    "source_id": dept_id,
                    "target_id": other_dept_id,
                    "relation_type": "shares_resource",
                    "weight": round(0.3 + random.random() * 0.4, 2),
                    "confidence": round(0.6 + random.random() * 0.3, 2),
                    "evidence": [],
                    "properties": {"resource_type": "staff_or_equipment"},
                })
    return edges


def build_memory_records(hospital: dict, metrics: list, rng: random.Random):
    """Create 12 memory records per hospital."""
    memory_templates = [
        {
            "memory_type": "past_decision",
            "content": "Implemented {year} budget reallocation shifting 8% from admin to clinical operations, resulting in 12% improvement in patient throughput.",
            "source": "budget_meeting",
            "confidence": 0.95,
        },
        {
            "memory_type": "known_pattern",
            "content": "Revenue consistently dips 3-5% in February due to post-holiday patient deferral pattern observed since 2022.",
            "source": "trend_analysis",
            "confidence": 0.88,
        },
        {
            "memory_type": "past_decision",
            "content": "Denied prior authorization for new MRI equipment in Q3 due to ROI threshold not met (projected 18-month payback vs 12-month target).",
            "source": "capital_review",
            "confidence": 0.92,
        },
        {
            "memory_type": "known_pattern",
            "content": "Denial rates spike 2-3x when new CPT code sets are introduced; requires 60-day grace period for staff training.",
            "source": "claims_analysis",
            "confidence": 0.85,
        },
        {
            "memory_type": "past_decision",
            "content": "Contracted with {payer} for 5% rate increase effective January after 3-month negotiation, impacting ~{rev}M annual revenue.",
            "source": "contract_negotiation",
            "confidence": 0.90,
        },
        {
            "memory_type": "known_pattern",
            "content": "Occupancy drops to ~75% during summer months (June-August) as elective procedures decline; staff scheduling adjusted accordingly.",
            "source": "occupancy_analysis",
            "confidence": 0.82,
        },
        {
            "memory_type": "past_decision",
            "content": "Invested $2.1M in revenue cycle management platform upgrade in {year}, reducing A/R days from 52 to 38 over 12 months.",
            "source": "it_investment",
            "confidence": 0.93,
        },
        {
            "memory_type": "known_pattern",
            "content": "Emergency department overcrowding correlates with 15% revenue leakage from diverted patients; threshold at 95% occupancy triggers overflow protocol.",
            "source": "operational_data",
            "confidence": 0.87,
        },
        {
            "memory_type": "past_decision",
            "content": "Approved telehealth expansion for {dept} department, increasing patient volume by 22% with minimal marginal cost.",
            "source": "strategic_planning",
            "confidence": 0.89,
        },
        {
            "memory_type": "known_pattern",
            "content": "Claims submitted within 7 days of service have 94% first-pass acceptance vs 78% for claims submitted after 30 days.",
            "source": "claims_analysis",
            "confidence": 0.91,
        },
        {
            "memory_type": "past_decision",
            "content": "Implemented dynamic pricing model for self-pay patients, increasing collection rate from 34% to 61% over {year}.",
            "source": "pricing_strategy",
            "confidence": 0.86,
        },
        {
            "memory_type": "known_pattern",
            "content": "Insurance verification at scheduling reduces denials by 40%; compliance rate currently at 72% across all intake points.",
            "source": "process_analysis",
            "confidence": 0.84,
        },
    ]

    records = []
    payers = ["Blue Cross", "Aetna", "UnitedHealth", "Cigna", "Medicare"]
    depts = [d[0] for d in hospital["departments"]]
    for i, template in enumerate(memory_templates):
        year = 2022 + (i % 3)
        month_offset = rng.randint(0, 11)
        created = datetime(2023, 1, 1) + timedelta(days=30 * month_offset + i * 15)

        content = template["content"].format(
            year=year,
            payer=rng.choice(payers),
            rev=round(hospital["base_revenue"] / 1_000_000 * rng.uniform(0.02, 0.08), 2),
            dept=rng.choice(depts),
        )

        records.append({
            "id": uuid.uuid4(),
            "tenant_id": TENANT_ID,
            "memory_type": template["memory_type"],
            "content": content,
            "embedding": None,
            "metadata_": {"hospital_id": str(hospital["id"]), "tags": [template["memory_type"], hospital["short_name"]]},
            "source": template["source"],
            "confidence": template["confidence"],
            "access_count": rng.randint(1, 15),
            "status": "active",
            "created_at": created,
            "last_accessed": created + timedelta(days=rng.randint(1, 90)),
            "expires_at": None,
        })
    return records


def build_executive_decisions(hospital: dict, metrics: list, rng: random.Random):
    """Create 6 historical executive decisions per hospital."""
    decision_templates = [
        {
            "title": "Revenue Cycle Optimization Initiative",
            "description": "Approved $1.8M investment in RCM platform modernization to reduce denial rates and accelerate cash collections.",
            "category": "financial",
            "priority": "P1",
            "status": "completed",
            "impact_estimate": {"expected_revenue_increase": 2400000, "payback_months": 14},
        },
        {
            "title": "Bed Capacity Expansion Phase 2",
            "description": "Authorized 40-bed expansion to meet growing demand, with construction scheduled for Q2-Q4.",
            "category": "operational",
            "priority": "P1",
            "status": "completed",
            "impact_estimate": {"additional_beds": 40, "estimated_annual_revenue": 6000000},
        },
        {
            "title": "Payer Contract Renegotiation",
            "description": "Negotiated rate increases across top 5 payers with focus on cardiac and surgical services.",
            "category": "financial",
            "priority": "P2",
            "status": "completed",
            "impact_estimate": {"rate_increase_percent": 4.5, "annual_impact": 3200000},
        },
        {
            "title": "Clinical Staffing Model Redesign",
            "description": "Implemented predictive staffing model to reduce overtime costs while maintaining patient satisfaction scores.",
            "category": "operational",
            "priority": "P2",
            "status": "completed",
            "impact_estimate": {"annual_savings": 850000, "overtime_reduction_percent": 22},
        },
        {
            "title": "Digital Health Platform Deployment",
            "description": "Rolled out telehealth and remote patient monitoring for chronic disease management across 3 departments.",
            "category": "strategic",
            "priority": "P1",
            "status": "completed",
            "impact_estimate": {"new_patient_volume_increase": 18, "cost_per_visit_reduction": 35},
        },
        {
            "title": "Denial Management Task Force",
            "description": "Established cross-functional team to address rising denial rates, targeting 30% reduction in 6 months.",
            "category": "financial",
            "priority": "P1",
            "status": "completed",
            "impact_estimate": {"denial_rate_target": 0.055, "recovered_revenue": 1800000},
        },
    ]

    decisions = []
    for i, template in enumerate(decision_templates):
        month_offset = 6 + i * 5
        proposed_at = datetime(2023, 1, 1) + timedelta(days=30 * month_offset)
        completed_at = proposed_at + timedelta(days=rng.randint(30, 120))

        decisions.append({
            "id": uuid.uuid4(),
            "tenant_id": TENANT_ID,
            "title": f"{template['title']} - {hospital['short_name']}",
            "description": template["description"],
            "category": template["category"],
            "priority": template["priority"],
            "status": template["status"],
            "impact_estimate": template["impact_estimate"],
            "deadline": completed_at + timedelta(days=30),
            "context": {
                "hospital_id": str(hospital["id"]),
                "hospital_name": hospital["name"],
                "trigger": "quarterly_review",
            },
            "created_at": proposed_at,
            "updated_at": completed_at,
        })
    return decisions


def build_forecast_model(hospital: dict, metrics: list):
    """Create 1 pre-trained forecast model per hospital."""
    model_id = uuid.uuid4()
    last_month = metrics[-1]
    avg_revenue = sum(m["revenue"] for m in metrics) / len(metrics)
    std_revenue = (sum((m["revenue"] - avg_revenue) ** 2 for m in metrics) / len(metrics)) ** 0.5

    return {
        "id": model_id,
        "tenant_id": TENANT_ID,
        "name": f"Revenue Forecast - {hospital['name']}",
        "model_type": "prophet",
        "parameters": {
            "changepoint_prior_scale": 0.05,
            "seasonality_mode": "multiplicative",
            "yearly_seasonality": True,
            "weekly_seasonality": False,
            "growth": "linear",
        },
        "hyperparameters": {
            "training_months": 36,
            "validation_months": 6,
            "mape": round(std_revenue / avg_revenue * 100, 2),
            "rmse": round(std_revenue, 2),
            "r_squared": round(0.85 + random.random() * 0.1, 3),
        },
        "status": "trained",
        "training_metadata": {
            "trained_at": datetime.now().isoformat(),
            "data_start": metrics[0]["month_label"],
            "data_end": last_month["month_label"],
            "total_observations": len(metrics),
            "features_used": [
                "historical_revenue",
                "seasonality",
                "bed_utilization",
                "claim_volume",
                "denial_rate",
                "occupancy",
            ],
        },
        "model_artifact": None,
    }


def build_forecast_results(model_id, hospital: dict, metrics: list):
    """Create 12-month forward projections per hospital."""
    results = []
    last_metrics = metrics[-1]
    rng = random.Random(42)

    for m in range(1, 13):
        future_date = BASE_DATE + timedelta(days=32 * (35 + m))
        future_date = future_date.replace(day=1)
        period_label = future_date.strftime("%Y-%m")

        growth_factor = (1 + hospital["growth_rate"]) ** (36 + m)
        seasonal = 1.0 + 0.03 * (1 if future_date.month in (1, 6, 9, 12) else -1 if future_date.month in (2, 7) else 0)
        noise = 1.0 + rng.gauss(0, hospital["volatility"] * 0.5)

        projected_revenue = hospital["base_revenue"] * growth_factor * seasonal * noise
        confidence = max(0.6, 0.95 - m * 0.02)

        lower_bound = projected_revenue * (1 - 0.05 * m)
        upper_bound = projected_revenue * (1 + 0.05 * m)

        projected_denial = hospital["base_denial_rate"] * (1 + rng.gauss(0, 0.05))
        projected_ar = hospital["base_ar_days"] * (1 + rng.gauss(0, 0.05))
        projected_occupancy = hospital["base_occupancy"] * (1 + rng.gauss(0, 0.03))

        results.append({
            "id": uuid.uuid4(),
            "model_id": model_id,
            "tenant_id": TENANT_ID,
            "metric_id": f"revenue_{hospital['short_name'].lower()}",
            "metric_name": f"Monthly Revenue - {hospital['short_name']}",
            "period": period_label,
            "values": [
                {"metric": "revenue", "value": round(projected_revenue, 2), "lower": round(lower_bound, 2), "upper": round(upper_bound, 2)},
                {"metric": "denial_rate", "value": round(projected_denial, 4)},
                {"metric": "ar_days", "value": round(projected_ar, 1)},
                {"metric": "occupancy", "value": round(projected_occupancy, 4)},
            ],
            "metrics": {
                "mape": round(abs(projected_revenue - hospital["base_revenue"] * growth_factor) / (hospital["base_revenue"] * growth_factor) * 100, 2),
                "confidence_interval_width": round((upper_bound - lower_bound) / projected_revenue * 100, 2),
            },
            "confidence_level": confidence,
            "model_name": f"Revenue Forecast - {hospital['name']}",
            "model_type": "prophet",
        })
    return results


async def seed():
    random.seed(42)

    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        all_nodes = []
        all_edges = []
        all_memories = []
        all_decisions = []
        all_forecast_models = []
        all_forecast_results = []

        for hospital in HOSPITALS:
            metrics = generate_monthly_metrics(hospital, random.Random(42))

            hospital_node_id, dept_node_ids, nodes = build_knowledge_nodes(hospital, metrics)
            all_nodes.extend(nodes)

            edges = build_knowledge_edges(hospital_node_id, dept_node_ids, hospital)
            all_edges.extend(edges)

            memories = build_memory_records(hospital, metrics, random.Random(42 + hash(hospital["name"]) % 1000))
            all_memories.extend(memories)

            decisions = build_executive_decisions(hospital, metrics, random.Random(84 + hash(hospital["name"]) % 1000))
            all_decisions.extend(decisions)

            forecast_model = build_forecast_model(hospital, metrics)
            all_forecast_models.append(forecast_model)

            forecast_results = build_forecast_results(forecast_model["id"], hospital, metrics)
            all_forecast_results.extend(forecast_results)

        for node in all_nodes:
            session.add(KnowledgeNodeModel(**node))
        print(f"  Inserted {len(all_nodes)} knowledge nodes")
        await session.flush()

        for edge in all_edges:
            session.add(KnowledgeEdgeModel(**edge))
        print(f"  Inserted {len(all_edges)} knowledge edges")

        for mem in all_memories:
            if "metadata" in mem:
                mem["metadata_"] = mem.pop("metadata")
            session.add(MemoryRecordModel(**mem))
        print(f"  Inserted {len(all_memories)} memory records")

        for decision in all_decisions:
            session.add(ExecutiveDecisionModel(**decision))
        print(f"  Inserted {len(all_decisions)} executive decisions")

        for fm in all_forecast_models:
            session.add(ForecastModelModel(**fm))
        print(f"  Inserted {len(all_forecast_models)} forecast models")

        for fr in all_forecast_results:
            session.add(ForecastResultModel(**fr))
        print(f"  Inserted {len(all_forecast_results)} forecast results")

        await session.commit()

    await engine.dispose()
    print("\nSeed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
