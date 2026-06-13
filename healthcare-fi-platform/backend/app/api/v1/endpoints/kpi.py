from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.core.dev_auth import DevUser, dep_dev_admin
from app.services.kpi.engine import KPIEngine

router = APIRouter()


@router.get("/executive-summary")
async def get_executive_summary(
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    kpi_engine = KPIEngine(db)
    kpis = await kpi_engine.get_all_kpis(branch_id, department_id, start_date, end_date)
    
    return {
        "kpis": {
            code: {
                "name": kpi.name,
                "value": kpi.value,
                "target": kpi.target,
                "previous_value": kpi.previous_value,
                "change_percent": kpi.change_percent,
                "trend": kpi.trend,
                "category": kpi.category,
                "unit": kpi.unit
            }
            for code, kpi in kpis.items()
        }
    }


@router.get("/revenue")
async def get_revenue_kpis(
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    kpi_engine = KPIEngine(db)
    kpis = await kpi_engine.calculate_revenue_kpis(branch_id, department_id, start_date, end_date)
    
    return {
        code: {
            "name": kpi.name,
            "value": kpi.value,
            "target": kpi.target,
            "previous_value": kpi.previous_value,
            "change_percent": kpi.change_percent,
            "trend": kpi.trend,
            "unit": kpi.unit
        }
        for code, kpi in kpis.items()
    }


@router.get("/profitability")
async def get_profitability_kpis(
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    kpi_engine = KPIEngine(db)
    kpis = await kpi_engine.calculate_profitability_kpis(branch_id, department_id, start_date, end_date)
    
    return {
        code: {
            "name": kpi.name,
            "value": kpi.value,
            "target": kpi.target,
            "previous_value": kpi.previous_value,
            "change_percent": kpi.change_percent,
            "trend": kpi.trend,
            "unit": kpi.unit
        }
        for code, kpi in kpis.items()
    }


@router.get("/occupancy")
async def get_occupancy_kpis(
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    kpi_engine = KPIEngine(db)
    kpis = await kpi_engine.calculate_occupancy_kpis(branch_id, department_id)
    
    return {
        code: {
            "name": kpi.name,
            "value": kpi.value,
            "target": kpi.target,
            "trend": kpi.trend,
            "unit": kpi.unit
        }
        for code, kpi in kpis.items()
    }


@router.get("/claims")
async def get_claim_kpis(
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    kpi_engine = KPIEngine(db)
    kpis = await kpi_engine.calculate_claim_kpis(branch_id, department_id, start_date, end_date)
    
    return {
        code: {
            "name": kpi.name,
            "value": kpi.value,
            "target": kpi.target,
            "trend": kpi.trend,
            "unit": kpi.unit
        }
        for code, kpi in kpis.items()
    }


@router.get("/trend/{kpi_code}")
async def get_kpi_trend(
    kpi_code: str,
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    periods: int = Query(12),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    kpi_engine = KPIEngine(db)
    trend = await kpi_engine.get_kpi_trend(kpi_code, branch_id, department_id, periods)
    
    return {"kpi_code": kpi_code, "trend": trend}


@router.get("/revenue/by-department")
async def get_revenue_by_department(
    branch_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    kpi_engine = KPIEngine(db)
    departments = await kpi_engine.get_revenue_by_department(branch_id, start_date, end_date)
    
    return {"departments": departments}


@router.get("/revenue/by-payer")
async def get_revenue_by_payer(
    branch_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    kpi_engine = KPIEngine(db)
    payers = await kpi_engine.get_revenue_by_payer(branch_id, start_date, end_date)
    
    return {"payers": payers}
