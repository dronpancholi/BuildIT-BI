"""
Phase 5: AI Everywhere — Universal 'Ask AI About This' endpoint.
Every page can embed an AskAIButton that calls this endpoint.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import dep_tenant_id
from app.core.dev_auth import DevUser, dep_dev_user
from app.db.session import get_db
from app.core.data_fabric.query_engine import QueryEngine
from app.core.data_fabric.metric_catalog import get_metric, get_all_metrics, metric_to_dict

router = APIRouter(tags=["AI Everywhere"])

__all__ = ["router"]


# ============================================================
# Request / Response Models
# ============================================================

class AskAIRequest(BaseModel):
    question: str
    page_context: Dict[str, Any] = {}
    # page_context can include:
    #   page: str           — current page name (e.g., "executive-center")
    #   metrics: list[str]  — metrics currently displayed
    #   filters: dict       — active filters
    #   date_range: list    — [start, end]
    #   selected_entity: dict — currently selected item (department, payer, etc.)


class AskAIResponse(BaseModel):
    answer: str
    metrics_used: List[Dict[str, Any]] = []
    insights: List[str] = []
    actions: List[str] = []
    confidence: float = 0.85


# ============================================================
# Page Context Definitions — what each page knows
# ============================================================

PAGE_CONTEXTS = {
    "executive-center": {
        "description": "Executive Command Center — high-level KPIs, alerts, decisions, forecasts",
        "available_metrics": ["GROSS_REVENUE", "NET_REVENUE", "EBITDA", "EBITDA_MARGIN",
                              "OCCUPANCY_RATE", "CLAIM_DENIAL_RATE", "DAYS_IN_AR", "ALOS",
                              "LABOUR_COST_RATIO", "OPERATING_CASH_FLOW", "ARPOB", "COLLECTION_EFFICIENCY"],
        "capabilities": ["View KPIs", "Generate briefings", "Track decisions", "View alerts", "Revenue/cost forecasts"],
    },
    "revenue": {
        "description": "Revenue Analytics — revenue by department, payer, service line",
        "available_metrics": ["GROSS_REVENUE", "NET_REVENUE", "REVENUE_PER_DOCTOR"],
        "capabilities": ["Revenue breakdown by department", "Payer mix analysis", "Revenue trends"],
    },
    "analytics": {
        "description": "Power BI Replacement — pivot tables, drill down, time intelligence",
        "available_metrics": ["GROSS_REVENUE", "NET_REVENUE", "TOTAL_EXPENSES", "OCCUPANCY_RATE",
                              "CLAIM_DENIAL_RATE", "CLAIM_APPROVAL_RATE"],
        "capabilities": ["Semantic query engine", "Pivot tables", "Drill down", "Saved reports"],
    },
    "forecasting": {
        "description": "Enterprise Forecasting — revenue and cost predictions",
        "available_metrics": ["GROSS_REVENUE", "NET_REVENUE", "TOTAL_EXPENSES"],
        "capabilities": ["Revenue forecasting", "Cost forecasting", "Confidence intervals"],
    },
    "intelligence": {
        "description": "Intelligence Engine — insights, anomalies, recommendations",
        "available_metrics": ["GROSS_REVENUE", "NET_REVENUE", "OCCUPANCY_RATE", "CLAIM_DENIAL_RATE"],
        "capabilities": ["AI-generated insights", "Anomaly detection", "Recommendation engine"],
    },
    "ai-cfo": {
        "description": "AI CFO — financial advisor, briefings, questions",
        "available_metrics": ["GROSS_REVENUE", "NET_REVENUE", "EBITDA", "EBITDA_MARGIN",
                              "TOTAL_EXPENSES", "NET_MARGIN"],
        "capabilities": ["Ask financial questions", "Generate briefings", "Financial analysis"],
    },
    "copilot": {
        "description": "AI Copilot — natural language interface for data exploration",
        "available_metrics": ["ALL"],
        "capabilities": ["Natural language queries", "Multi-step reasoning", "Cross-domain analysis"],
    },
    "alerts": {
        "description": "Alert Management — monitor and respond to alerts",
        "available_metrics": [],
        "capabilities": ["View alerts", "Mark read", "Dismiss alerts"],
    },
    "decisions": {
        "description": "Decision Intelligence — track and manage decisions",
        "available_metrics": [],
        "capabilities": ["Create decisions", "Track status", "Decision timeline"],
    },
    "scenarios": {
        "description": "Strategic Scenarios — what-if analysis and Monte Carlo",
        "available_metrics": ["GROSS_REVENUE", "NET_REVENUE", "TOTAL_EXPENSES", "EBITDA"],
        "capabilities": ["Create scenarios", "What-if analysis", "Monte Carlo simulation"],
    },
    "settings": {
        "description": "Platform Settings — configuration and administration",
        "available_metrics": [],
        "capabilities": ["System configuration", "User management"],
    },
    "dashboard": {
        "description": "Dashboard Builder — create and customize dashboards",
        "available_metrics": ["ALL"],
        "capabilities": ["Create dashboards", "Add widgets", "Customize layouts"],
    },
}


# ============================================================
# Core AI Logic
# ============================================================

async def _gather_page_data(
    db: AsyncSession,
    tenant_id: UUID,
    page_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Gather relevant data from the page context."""
    engine = QueryEngine(db, tenant_id)
    page = page_context.get("page", "executive-center")
    ctx = PAGE_CONTEXTS.get(page, PAGE_CONTEXTS["executive-center"])
    
    result = {
        "page": page,
        "page_description": ctx["description"],
        "metrics": {},
        "kpis": [],
        "alerts_count": 0,
        "insights_count": 0,
    }
    
    # Get KPI summary
    try:
        kpi_summary = await engine.get_kpi_summary()
        result["kpis"] = kpi_summary["kpis"]
        result["overall_health"] = kpi_summary["overall_health"]
    except Exception:
        pass
    
    # Get specific metrics if requested
    requested_metrics = page_context.get("metrics", [])
    for metric_code in requested_metrics[:5]:  # limit to 5
        metric_def = get_metric(metric_code)
        if metric_def:
            try:
                value_data = await engine._compute_metric(metric_def, [], {}, None)
                result["metrics"][metric_code] = {
                    "name": metric_def.name,
                    "value": value_data["total"],
                    "unit": metric_def.unit.value,
                    "target": metric_def.target,
                    "benchmark": metric_def.benchmark,
                }
            except Exception:
                pass
    
    # Get alert count
    try:
        from sqlalchemy import text
        r = await db.execute(text("SELECT COUNT(*) FROM alerts WHERE is_read = false"))
        result["alerts_count"] = r.scalar() or 0
    except Exception:
        pass
    
    return result


def _build_system_prompt(page_data: Dict[str, Any], question: str) -> str:
    """Build the system prompt for the LLM."""
    page = page_data.get("page", "unknown")
    page_desc = page_data.get("page_description", "")
    
    kpis_text = ""
    for kpi in page_data.get("kpis", [])[:8]:
        status_emoji = {"healthy": "✓", "warning": "⚠", "critical": "✗"}.get(kpi.get("status", ""), "")
        kpis_text += f"  - {kpi['name']}: {kpi['value']:.1f} {kpi.get('unit', '')} {status_emoji} [{kpi.get('status', 'unknown')}]\n"
    
    metrics_text = ""
    for code, data in page_data.get("metrics", {}).items():
        metrics_text += f"  - {data['name']}: {data['value']:.1f} {data['unit']}\n"
    
    return f"""You are Dr. Darshan Shukla's AI financial advisor for BuildIT BI Healthcare Platform.

Current Page: {page} — {page_desc}

Available KPIs:
{kpis_text or '  (none loaded)'}

Specific Metrics:
{metrics_text or '  (none loaded)'}

Alerts: {page_data.get('alerts_count', 0)} unread
Overall Health: {page_data.get('overall_health', 'unknown')}

INSTRUCTIONS:
- Answer as a senior healthcare financial advisor
- Reference specific numbers from the data
- Provide actionable insights
- Be concise (2-4 sentences max)
- If the question is about a metric, explain its significance
- If asked to compare, calculate the variance
- Always end with a specific recommended action"""


# ============================================================
# API Endpoint
# ============================================================

@router.post("/ask")
async def ask_ai_about_this(
    req: AskAIRequest,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Universal 'Ask AI About This' endpoint.
    Every page can call this with its context to get AI-powered insights.
    """
    tid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
    
    # Gather page data
    page_data = await _gather_page_data(db, tid, req.page_context)
    
    # Build context for LLM
    system_prompt = _build_system_prompt(page_data, req.question)
    
    # Try to get LLM response
    answer = ""
    try:
        from app.infrastructure.nim.llm_client import get_llm_client
        llm = get_llm_client()
        answer = await llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.question},
            ],
            temperature=0.3,
            max_tokens=512,
        )
    except Exception as e:
        # Fallback to rule-based response
        answer = _fallback_response(req.question, page_data)
    
    # Build insights from KPIs
    insights = []
    for kpi in page_data.get("kpis", []):
        if kpi.get("status") == "critical":
            insights.append(f"CRITICAL: {kpi['name']} is {kpi['value']:.1f} (target: {kpi.get('target', 'N/A')})")
        elif kpi.get("status") == "warning":
            insights.append(f"WARNING: {kpi['name']} at {kpi['value']:.1f} needs attention")
    
    # Build actions
    actions = []
    if page_data.get("alerts_count", 0) > 0:
        actions.append(f"Review {page_data['alerts_count']} unread alerts")
    if page_data.get("overall_health") == "critical":
        actions.append("Address critical KPIs immediately")
    
    # Metrics used
    metrics_used = []
    for kpi in page_data.get("kpis", [])[:5]:
        metrics_used.append({
            "code": kpi.get("code", ""),
            "name": kpi["name"],
            "value": kpi["value"],
            "status": kpi.get("status", "unknown"),
        })
    
    return {
        "answer": answer,
        "metrics_used": metrics_used,
        "insights": insights[:5],
        "actions": actions[:3],
        "confidence": 0.85 if answer else 0.0,
    }


def _fallback_response(question: str, page_data: Dict[str, Any]) -> str:
    """Rule-based fallback when LLM is unavailable."""
    question_lower = question.lower()
    kpis = {k["name"].lower(): k for k in page_data.get("kpis", [])}
    
    if "revenue" in question_lower:
        rev = kpis.get("net revenue", kpis.get("gross revenue", {}))
        if rev:
            return f"Current revenue is ${rev['value']:,.0f}. " + \
                   (f"This is {'above' if rev.get('status') == 'healthy' else 'below'} target. " if rev.get('target') else "") + \
                   "Review revenue trends in the Revenue Analytics page for detailed breakdown."
    
    if "occupancy" in question_lower:
        occ = kpis.get("bed occupancy rate", {})
        if occ:
            return f"Bed occupancy is at {occ['value']:.1f}%. " + \
                   (f"Target is {occ.get('target', 'N/A')}%. " if occ.get('target') else "") + \
                   "Consider optimizing bed management to improve utilization."
    
    if "denial" in question_lower or "claim" in question_lower:
        denial = kpis.get("claim denial rate", {})
        if denial:
            return f"Claim denial rate is {denial['value']:.1f}%. " + \
                   (f"Target is {denial.get('target', 'N/A')}%. " if denial.get('target') else "") + \
                   "Focus on reducing denials to improve cash flow."
    
    if "margin" in question_lower or "profit" in question_lower:
        margin = kpis.get("net profit margin", kpis.get("ebitda margin", {}))
        if margin:
            return f"Current margin is {margin['value']:.1f}%. " + \
                   (f"Target is {margin.get('target', 'N/A')}%. " if margin.get('target') else "") + \
                   "Review expense categories for optimization opportunities."
    
    # Generic response
    health = page_data.get("overall_health", "unknown")
    return f"System health is {health}. " + \
           f"Currently monitoring {len(page_data.get('kpis', []))} KPIs. " + \
           "Ask specific questions about revenue, occupancy, claims, or margins for detailed insights."
