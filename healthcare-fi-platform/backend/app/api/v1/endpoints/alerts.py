from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.session import get_db
from app.core.dev_auth import DevUser, dep_dev_admin
from app.models.models import User, Alert
from app.schemas.schemas import AlertCreate, AlertResponse

router = APIRouter()


@router.get("/list", response_model=list[AlertResponse])
async def list_alerts(
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    query = select(Alert)
    
    if severity:
        query = query.where(Alert.severity == severity)
    if category:
        query = query.where(Alert.category == category)
    if is_read is not None:
        query = query.where(Alert.is_read == is_read)
    
    query = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return alert


@router.put("/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_read = True
    await db.flush()
    
    return {"status": "marked as read"}


@router.put("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_resolved = True
    alert.is_read = True
    await db.flush()
    
    return {"status": "resolved"}


@router.post("/create", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    if current_user.role not in ["ceo", "cfo", "finance_manager"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    alert = Alert(
        title=alert_data.title,
        message=alert_data.message,
        severity=alert_data.severity,
        category=alert_data.category,
        entity_type=alert_data.entity_type,
        entity_id=alert_data.entity_id,
        recommendation=alert_data.recommendation
    )
    
    db.add(alert)
    await db.flush()
    
    return alert


@router.get("/stats/summary")
async def get_alert_stats(
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    from sqlalchemy import func
    
    total_query = select(func.count(Alert.id))
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0
    
    unread_query = select(func.count(Alert.id)).where(Alert.is_read == False)
    unread_result = await db.execute(unread_query)
    unread = unread_result.scalar() or 0
    
    critical_query = select(func.count(Alert.id)).where(
        (Alert.severity == "critical") & (Alert.is_resolved == False)
    )
    critical_result = await db.execute(critical_query)
    critical = critical_result.scalar() or 0
    
    return {
        "total": total,
        "unread": unread,
        "critical": critical
    }
