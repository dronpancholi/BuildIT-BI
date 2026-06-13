"""
API v2 endpoints package.
Simplified: Only core Executive Edition modules.
"""
from fastapi import APIRouter
from app.api.v2.endpoints.api import router as api_router
from app.api.v2.endpoints.financial import router as financial_router
from app.api.v2.endpoints.analytics import router as analytics_router
from app.api.v2.endpoints.exports import router as exports_router
from app.api.v2.endpoints.forecasting import router as forecasting_router
from app.api.v2.endpoints.executive_center import router as executive_router

v2_router = APIRouter()
v2_router.include_router(api_router)
v2_router.include_router(financial_router, prefix="/financial", tags=["Financial Data Warehouse"])
v2_router.include_router(analytics_router, prefix="/analytics", tags=["Executive Analytics"])
v2_router.include_router(exports_router, prefix="/exports", tags=["Board Pack Export"])
v2_router.include_router(forecasting_router, prefix="/forecasting", tags=["Executive Forecasting"])
v2_router.include_router(executive_router, prefix="/executive", tags=["Executive Command Center"])

__all__ = ["v2_router"]
