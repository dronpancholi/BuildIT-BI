from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import numpy as np
from dataclasses import dataclass
import structlog

from app.models.models import Revenue, Expense, KPIValue, Forecast

logger = structlog.get_logger()


@dataclass
class ForecastResult:
    metric_type: str
    predicted_value: float
    confidence_lower: float
    confidence_upper: float
    confidence_score: float
    methodology: str
    historical_data: List[Dict[str, Any]]


class ForecastingEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_historical_data(
        self,
        metric_type: str,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None,
        periods: int = 24
    ) -> List[Dict[str, Any]]:
        if metric_type == "revenue":
            query = select(
                Revenue.service_date,
                func.sum(Revenue.net_amount)
            ).group_by(Revenue.service_date)
            
            if branch_id:
                query = query.where(Revenue.branch_id == branch_id)
            if department_id:
                query = query.where(Revenue.department_id == department_id)
            
            query = query.order_by(Revenue.service_date.desc()).limit(periods)
            
            result = await self.db.execute(query)
            data = result.all()
            
            return [
                {"date": r[0].isoformat(), "value": r[1]}
                for r in reversed(data)
            ]
        
        elif metric_type == "expenses":
            query = select(
                Expense.expense_date,
                func.sum(Expense.amount)
            ).group_by(Expense.expense_date)
            
            if branch_id:
                query = query.where(Expense.branch_id == branch_id)
            if department_id:
                query = query.where(Expense.department_id == department_id)
            
            query = query.order_by(Expense.expense_date.desc()).limit(periods)
            
            result = await self.db.execute(query)
            data = result.all()
            
            return [
                {"date": r[0].isoformat(), "value": r[1]}
                for r in reversed(data)
            ]
        
        return []

    async def forecast_linear_regression(
        self,
        historical_data: List[Dict[str, Any]],
        periods_ahead: int = 12
    ) -> ForecastResult:
        if len(historical_data) < 2:
            return ForecastResult(
                metric_type="unknown",
                predicted_value=0,
                confidence_lower=0,
                confidence_upper=0,
                confidence_score=0,
                methodology="insufficient_data",
                historical_data=historical_data
            )
        
        values = [d["value"] for d in historical_data]
        x = np.arange(len(values))
        y = np.array(values)
        
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs
        
        predictions = []
        for i in range(periods_ahead):
            pred_x = len(values) + i
            pred_y = slope * pred_x + intercept
            predictions.append(pred_y)
        
        residuals = y - (slope * x + intercept)
        std_error = np.std(residuals)
        
        predicted_value = predictions[-1]
        confidence_interval = 1.96 * std_error
        
        confidence_score = max(0, min(1, 1 - (std_error / np.mean(y)))) if np.mean(y) > 0 else 0
        
        return ForecastResult(
            metric_type="linear_regression",
            predicted_value=predicted_value,
            confidence_lower=predicted_value - confidence_interval,
            confidence_upper=predicted_value + confidence_interval,
            confidence_score=confidence_score,
            methodology="linear_regression",
            historical_data=historical_data
        )

    async def forecast_moving_average(
        self,
        historical_data: List[Dict[str, Any]],
        periods_ahead: int = 12,
        window_size: int = 3
    ) -> ForecastResult:
        if len(historical_data) < window_size:
            return await self.forecast_linear_regression(historical_data, periods_ahead)
        
        values = [d["value"] for d in historical_data]
        
        moving_averages = []
        for i in range(window_size, len(values) + 1):
            window = values[i - window_size:i]
            moving_averages.append(np.mean(window))
        
        predictions = []
        last_ma = moving_averages[-1]
        for i in range(periods_ahead):
            predictions.append(last_ma)
        
        ma_std = np.std(moving_averages)
        predicted_value = predictions[-1]
        confidence_interval = 1.96 * ma_std
        
        confidence_score = max(0, min(1, 1 - (ma_std / np.mean(values)))) if np.mean(values) > 0 else 0
        
        return ForecastResult(
            metric_type="moving_average",
            predicted_value=predicted_value,
            confidence_lower=predicted_value - confidence_interval,
            confidence_upper=predicted_value + confidence_interval,
            confidence_score=confidence_score,
            methodology="moving_average",
            historical_data=historical_data
        )

    async def create_forecast(
        self,
        metric_type: str,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None,
        periods_ahead: int = 12,
        methodology: str = "auto"
    ) -> ForecastResult:
        historical_data = await self.get_historical_data(
            metric_type, branch_id, department_id
        )
        
        if methodology == "auto":
            if len(historical_data) >= 12:
                result = await self.forecast_linear_regression(historical_data, periods_ahead)
            else:
                result = await self.forecast_moving_average(historical_data, periods_ahead)
        elif methodology == "linear_regression":
            result = await self.forecast_linear_regression(historical_data, periods_ahead)
        elif methodology == "moving_average":
            result = await self.forecast_moving_average(historical_data, periods_ahead)
        else:
            result = await self.forecast_linear_regression(historical_data, periods_ahead)
        
        forecast = Forecast(
            name=f"{metric_type}_forecast",
            metric_type=metric_type,
            branch_id=branch_id,
            department_id=department_id,
            forecast_date=datetime.utcnow(),
            period_type="monthly",
            predicted_value=result.predicted_value,
            confidence_lower=result.confidence_lower,
            confidence_upper=result.confidence_upper,
            confidence_score=result.confidence_score,
            methodology=result.methodology
        )
        
        self.db.add(forecast)
        await self.db.flush()
        
        return result

    async def decompose_forecast(
        self,
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if len(historical_data) < 3:
            return {
                "trend": "insufficient_data",
                "seasonality": "insufficient_data",
                "noise": "insufficient_data"
            }
        
        values = [d["value"] for d in historical_data]
        
        trend = np.polyfit(range(len(values)), values, 1)
        
        detrended = values - np.polyval(trend, range(len(values)))
        
        seasonal_pattern = np.mean(detrended) if len(detrended) > 0 else 0
        
        noise = np.std(detrended) if len(detrended) > 0 else 0
        
        return {
            "trend": {
                "slope": trend[0],
                "intercept": trend[1],
                "direction": "increasing" if trend[0] > 0 else "decreasing"
            },
            "seasonality": {
                "pattern": seasonal_pattern,
                "strength": abs(seasonal_pattern) / np.mean(values) if np.mean(values) > 0 else 0
            },
            "noise": {
                "magnitude": noise,
                "signal_to_noise": np.mean(values) / noise if noise > 0 else 0
            }
        }

    async def validate_forecast(
        self,
        forecast_value: float,
        actual_value: float
    ) -> Dict[str, Any]:
        error = actual_value - forecast_value
        absolute_error = abs(error)
        percentage_error = (absolute_error / actual_value * 100) if actual_value > 0 else 0
        
        accuracy_score = max(0, 100 - percentage_error)
        
        return {
            "forecast_value": forecast_value,
            "actual_value": actual_value,
            "error": error,
            "absolute_error": absolute_error,
            "percentage_error": percentage_error,
            "accuracy_score": accuracy_score,
            "is_accurate": percentage_error < 10
        }
