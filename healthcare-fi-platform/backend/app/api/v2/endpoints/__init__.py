"""
API v2 endpoints package.
Simplified: Only core Power BI replacement modules.
"""
from fastapi import APIRouter
from app.api.v2.endpoints.api import router as api_router
from app.api.v2.endpoints.decisions import router as decisions_router
from app.api.v2.endpoints.outcomes import router as outcomes_router
from app.api.v2.endpoints.learning import router as learning_router
from app.api.v2.endpoints.financial import router as financial_router
from app.api.v2.endpoints.analytics import router as analytics_router
from app.api.v2.endpoints.dashboards import router as dashboards_router
from app.api.v2.endpoints.query_engine import router as query_engine_router
from app.api.v2.endpoints.exports import router as exports_router
from app.api.v2.endpoints.collaboration import router as collaboration_router
from app.api.v2.endpoints.workspace import router as workspace_router
from app.api.v2.endpoints.visualization import router as visualization_router
from app.api.v2.endpoints.governance import router as governance_router
from app.api.v2.endpoints.bfl import router as bfl_router
from app.api.v2.endpoints.metric_studio import router as metric_studio_router
from app.api.v2.endpoints.semantic_layer import router as semantic_layer_router
from app.api.v2.endpoints.ai_cfo import router as ai_cfo_router
from app.api.v2.endpoints.strategic_planning import router as strategic_router
from app.api.v2.endpoints.forecasting import router as forecasting_router
from app.api.v2.endpoints.executive_center import router as executive_router
from app.api.v2.endpoints.copilot import router as copilot_router
from app.api.v2.endpoints.intelligence import router as intelligence_router
from app.api.v2.endpoints.ai_everywhere import router as ai_everywhere_router

v2_router = APIRouter()
v2_router.include_router(api_router)
v2_router.include_router(decisions_router, prefix="/decisions", tags=["Decision Intelligence"])
v2_router.include_router(outcomes_router, prefix="", tags=["Outcome Measurement, Feature Store, Model Registry"])
v2_router.include_router(learning_router, prefix="", tags=["Learning Engine, Causal Impact, Knowledge Graph, Memory"])
v2_router.include_router(financial_router, prefix="/financial", tags=["Financial Architecture"])
v2_router.include_router(analytics_router, prefix="/analytics", tags=["Semantic Metrics & Dimensions"])
v2_router.include_router(dashboards_router, prefix="/dashboards", tags=["Dashboard Builder & Widget Framework"])
v2_router.include_router(query_engine_router, prefix="/query", tags=["Query Engine — Semantic to SQL"])
v2_router.include_router(exports_router, prefix="/exports", tags=["Export Engine — PDF, Excel, CSV, Scheduled Reports"])
v2_router.include_router(collaboration_router, prefix="/collaboration", tags=["Collaboration — Comments, Assignments"])
v2_router.include_router(workspace_router, prefix="/workspace", tags=["Executive Workspace & Briefings"])
v2_router.include_router(visualization_router, prefix="/visualization", tags=["Visualization Library — 19 Chart Types"])
v2_router.include_router(governance_router, prefix="/governance", tags=["Analytics Governance — Versioning, Certifications"])
v2_router.include_router(bfl_router, prefix="/bfl", tags=["BuildIT Formula Language"])
v2_router.include_router(metric_studio_router, prefix="/metric-studio", tags=["Metric Studio — Lifecycle, Certification, Dependencies"])
v2_router.include_router(semantic_layer_router, prefix="/semantic", tags=["Semantic Layer 2.0 — SCD2, Hierarchies, Relationships"])
v2_router.include_router(ai_cfo_router, prefix="/ai-cfo", tags=["AI CFO Core — Briefings, Questions, Workspaces"])
v2_router.include_router(strategic_router, prefix="/strategic", tags=["Strategic Planning — Scenarios, Monte Carlo, What-If"])
v2_router.include_router(forecasting_router, prefix="/forecasting", tags=["Enterprise Forecasting — Models, Monitoring, Drift"])
v2_router.include_router(executive_router, prefix="/executive", tags=["Executive Command Center — KPIs, Briefings, Forecasts"])
v2_router.include_router(copilot_router, prefix="/copilot", tags=["AI CFO Copilot — Natural Language Interface"])
v2_router.include_router(intelligence_router, prefix="/intelligence", tags=["Intelligence Engine — Insights, Anomalies, Recommendations"])
v2_router.include_router(ai_everywhere_router, prefix="/ai", tags=["AI Everywhere — Ask AI About This"])

__all__ = ["v2_router"]
