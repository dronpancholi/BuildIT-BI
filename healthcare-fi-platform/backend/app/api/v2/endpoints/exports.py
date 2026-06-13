from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any
from pydantic import BaseModel

from app.db.session import get_db
from app.core.security import get_current_user, CurrentUser
from app.models.models import Report

router = APIRouter()

class ExportJobCreate(BaseModel):
    name: str
    format: str # excel, pdf, ppt

@router.post("")
async def create_export_job(
    job: ExportJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Creates a new Board Pack export.
    For this MVP, it creates a mock file reference.
    """
    try:
        report = Report(
            name=job.name,
            format=job.format,
            created_by=current_user.id,
            s3_key=f"exports/{job.name}.{job.format}"
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        return {
            "status": "success",
            "message": "Export job queued",
            "report_id": str(report.id)
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def list_exports(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Lists recent Board Pack exports.
    """
    res = await db.execute(
        text("SELECT id, name, format, s3_key, created_at FROM reports ORDER BY created_at DESC LIMIT 20")
    )
    reports = [dict(row._mapping) for row in res.fetchall()]
    return {
        "status": "success",
        "reports": reports
    }
