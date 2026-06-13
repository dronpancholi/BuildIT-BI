from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.core.dev_auth import DevUser, dep_dev_admin
from app.services.forecasting.engine import ForecastingEngine
from app.schemas.schemas import ForecastRequest

router = APIRouter()


@router.post("/create")
async def create_forecast(
    request: ForecastRequest,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    forecasting_engine = ForecastingEngine(db)
    
    result = await forecasting_engine.create_forecast(
        metric_type=request.metric_type,
        branch_id=request.branch_id,
        department_id=request.department_id,
        periods_ahead=request.periods_ahead
    )
    
    return {
        "metric_type": result.metric_type,
        "predicted_value": result.predicted_value,
        "confidence_lower": result.confidence_lower,
        "confidence_upper": result.confidence_upper,
        "confidence_score": result.confidence_score,
        "methodology": result.methodology,
        "historical_data": result.historical_data
    }


@router.get("/historical/{metric_type}")
async def get_historical_data(
    metric_type: str,
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    periods: int = Query(24),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    forecasting_engine = ForecastingEngine(db)
    data = await forecasting_engine.get_historical_data(
        metric_type, branch_id, department_id, periods
    )
    
    return {"metric_type": metric_type, "data": data}


@router.post("/decompose")
async def decompose_forecast(
    metric_type: str,
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    periods: int = Query(24),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    forecasting_engine = ForecastingEngine(db)
    historical_data = await forecasting_engine.get_historical_data(
        metric_type, branch_id, department_id, periods
    )
    
    decomposition = await forecasting_engine.decompose_forecast(historical_data)
    
    return {"metric_type": metric_type, "decomposition": decomposition}


@router.post("/validate")
async def validate_forecast(
    forecast_value: float,
    actual_value: float,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    forecasting_engine = ForecastingEngine(db)
    validation = await forecasting_engine.validate_forecast(forecast_value, actual_value)
    
    return validation
