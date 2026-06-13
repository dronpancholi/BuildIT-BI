from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.core.dev_auth import DevUser, dep_dev_admin
from app.services.insights.engine import InsightsEngine

router = APIRouter()


@router.get("/comprehensive")
async def get_comprehensive_insights(
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    insights_engine = InsightsEngine(db)
    insights = await insights_engine.get_comprehensive_insights(
        branch_id, department_id, start_date, end_date
    )
    
    return insights


@router.get("/anomalies")
async def get_anomalies(
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    insights_engine = InsightsEngine(db)
    anomalies = await insights_engine.detect_anomalies(
        branch_id, department_id, start_date, end_date
    )
    
    return {"anomalies": anomalies}


@router.get("/trends")
async def get_trends(
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    insights_engine = InsightsEngine(db)
    trends = await insights_engine.analyze_trends(branch_id, department_id)
    
    return {"trends": trends}


@router.get("/opportunities")
async def get_opportunities(
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    insights_engine = InsightsEngine(db)
    opportunities = await insights_engine.identify_opportunities(branch_id, department_id)
    
    return {"opportunities": opportunities}


@router.get("/narrative")
async def get_narrative(
    branch_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    insights_engine = InsightsEngine(db)
    narrative = await insights_engine.generate_narrative(
        branch_id, department_id, start_date, end_date
    )
    
    return {"narrative": narrative}
