from fastapi import APIRouter
from app.api.v1.endpoints import auth, kpi, insights, forecasts, scenarios, alerts

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(kpi.router, prefix="/kpis", tags=["KPIs"])
api_router.include_router(insights.router, prefix="/insights", tags=["AI Insights"])
api_router.include_router(forecasts.router, prefix="/forecasts", tags=["Forecasts"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Scenarios"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
