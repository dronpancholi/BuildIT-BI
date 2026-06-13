from uuid import uuid4, UUID
from datetime import datetime, date, time
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Body, HTTPException
from pydantic import BaseModel, Field
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dev_auth import DevUser, dep_dev_admin
from app.db.session import get_db
from app.infrastructure.persistence.repositories import ExportJobRepository

router = APIRouter()


# ============================================================
# Request Models
# ============================================================

class ExportFormat(str, Enum):
    csv = "csv"
    xlsx = "xlsx"
    pdf = "pdf"
    json = "json"
    parquet = "parquet"


class ExportJobCreate(BaseModel):
    query_id: Optional[str] = None
    query_plan: Optional[dict] = None
    format: ExportFormat
    filename: Optional[str] = None
    delivery_email: Optional[str] = None
    compression: bool = False
    options: Optional[dict] = None


class ScheduledExportCreate(BaseModel):
    name: str
    query_id: Optional[str] = None
    query_plan: Optional[dict] = None
    format: ExportFormat
    schedule_cron: str
    delivery_email: Optional[str] = None
    delivery_s3_bucket: Optional[str] = None
    delivery_s3_prefix: Optional[str] = None
    is_active: bool = True
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ReportSubscriptionCreate(BaseModel):
    report_id: str
    frequency: str = "weekly"
    delivery_email: Optional[str] = None
    delivery_format: ExportFormat = ExportFormat.pdf
    include_data: bool = True
    include_charts: bool = True


# ============================================================
# Static Export Format Config (reference data, not mock)
# ============================================================

EXPORT_FORMATS = [
    {
        "id": "csv",
        "name": "CSV",
        "mime_type": "text/csv",
        "file_extension": ".csv",
        "max_rows": 1000000,
        "supports_charts": False,
        "supports_formatting": False,
        "description": "Comma-separated values, universal compatibility",
    },
    {
        "id": "xlsx",
        "name": "Excel Workbook",
        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "file_extension": ".xlsx",
        "max_rows": 1048576,
        "supports_charts": True,
        "supports_formatting": True,
        "description": "Excel with formatting, charts, and multiple sheets",
    },
    {
        "id": "pdf",
        "name": "PDF Report",
        "mime_type": "application/pdf",
        "file_extension": ".pdf",
        "max_rows": 50000,
        "supports_charts": True,
        "supports_formatting": True,
        "description": "Formatted PDF with embedded charts and branding",
    },
    {
        "id": "json",
        "name": "JSON",
        "mime_type": "application/json",
        "file_extension": ".json",
        "max_rows": 5000000,
        "supports_charts": False,
        "supports_formatting": False,
        "description": "JSON format for API integrations",
    },
    {
        "id": "parquet",
        "name": "Apache Parquet",
        "mime_type": "application/octet-stream",
        "file_extension": ".parquet",
        "max_rows": 10000000,
        "supports_charts": False,
        "supports_formatting": False,
        "description": "Columnar format optimized for analytics workloads",
    },
]


# ============================================================
# Export Job Endpoints
# ============================================================

@router.post("/jobs")
async def create_export_job(
    job: ExportJobCreate,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = ExportJobRepository(db)
    new_job = await repo.create(
        tenant_id=str(current_user.tenant_id),
        query_id=job.query_id,
        format=job.format.value,
        filename=job.filename,
        delivery_email=job.delivery_email,
        compression=job.compression,
        options=job.options or {},
        status="queued",
    )
    return {
        "status": "success",
        "data": new_job,
        "meta": {"request_id": str(uuid4())},
    }


@router.get("/jobs")
async def list_export_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    format: Optional[str] = Query(None, description="Filter by export format"),
    created_after: Optional[datetime] = Query(None, description="Jobs created after"),
    created_before: Optional[datetime] = Query(None, description="Jobs created before"),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = ExportJobRepository(db)
    filters = {}
    if status:
        filters["status"] = status
    if format:
        filters["format"] = format
    jobs = await repo.list(str(current_user.tenant_id), **filters)
    return {
        "status": "success",
        "data": {"jobs": jobs, "total": len(jobs)},
        "meta": {"request_id": str(uuid4())},
    }


@router.get("/jobs/{id}")
async def get_export_job(
    id: UUID,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = ExportJobRepository(db)
    job = await repo.get(id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return {
        "status": "success",
        "data": job,
        "meta": {"request_id": str(uuid4())},
    }


@router.delete("/jobs/{id}")
async def cancel_export_job(
    id: UUID,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = ExportJobRepository(db)
    existing = await repo.get(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Export job not found")
    await repo.update(id, status="cancelled")
    return {
        "status": "success",
        "data": {
            "id": str(id),
            "cancelled": True,
            "cancelled_at": datetime.utcnow().isoformat(),
            "cancelled_by": current_user.email,
        },
        "meta": {"request_id": str(uuid4())},
    }


@router.get("/formats")
async def list_export_formats(
    current_user: DevUser = Depends(dep_dev_admin),
):
    return {
        "status": "success",
        "data": {"formats": EXPORT_FORMATS, "total": len(EXPORT_FORMATS)},
        "meta": {"request_id": str(uuid4())},
    }


# ============================================================
# Scheduled Exports
# ============================================================

@router.post("/schedule")
async def create_scheduled_export(
    schedule: ScheduledExportCreate,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = ExportJobRepository(db)
    new_schedule = await repo.create(
        tenant_id=str(current_user.tenant_id),
        query_id=schedule.query_id,
        format=schedule.format.value,
        schedule_cron=schedule.schedule_cron,
        delivery_email=schedule.delivery_email,
        delivery_s3_bucket=schedule.delivery_s3_bucket,
        delivery_s3_prefix=schedule.delivery_s3_prefix,
        is_active=schedule.is_active,
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        job_type="scheduled",
        created_by=current_user.email,
    )
    return {
        "status": "success",
        "data": new_schedule,
        "meta": {"request_id": str(uuid4())},
    }


@router.get("/schedule")
async def list_scheduled_exports(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    format: Optional[str] = Query(None, description="Filter by format"),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = ExportJobRepository(db)
    filters = {"job_type": "scheduled"}
    if is_active is not None:
        filters["is_active"] = is_active
    if format:
        filters["format"] = format
    schedules = await repo.list(str(current_user.tenant_id), **filters)
    return {
        "status": "success",
        "data": {"schedules": schedules, "total": len(schedules)},
        "meta": {"request_id": str(uuid4())},
    }


@router.delete("/schedule/{id}")
async def cancel_scheduled_export(
    id: UUID,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = ExportJobRepository(db)
    existing = await repo.get(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Scheduled export not found")
    await repo.update(id, is_active=False)
    return {
        "status": "success",
        "data": {
            "id": str(id),
            "is_active": False,
            "cancelled_at": datetime.utcnow().isoformat(),
            "cancelled_by": current_user.email,
        },
        "meta": {"request_id": str(uuid4())},
    }


# ============================================================
# Subscriptions
# ============================================================

@router.post("/subscribe")
async def subscribe_to_report(
    subscription: ReportSubscriptionCreate,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = ExportJobRepository(db)
    new_subscription = await repo.create(
        tenant_id=str(current_user.tenant_id),
        report_id=subscription.report_id,
        frequency=subscription.frequency,
        delivery_email=subscription.delivery_email or current_user.email,
        delivery_format=subscription.delivery_format.value,
        include_data=subscription.include_data,
        include_charts=subscription.include_charts,
        job_type="subscription",
        created_by=current_user.email,
    )
    return {
        "status": "success",
        "data": new_subscription,
        "meta": {"request_id": str(uuid4())},
    }


@router.get("/subscriptions")
async def list_subscriptions(
    frequency: Optional[str] = Query(None, description="Filter by frequency"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = ExportJobRepository(db)
    filters = {"job_type": "subscription"}
    if frequency:
        filters["frequency"] = frequency
    if is_active is not None:
        filters["is_active"] = is_active
    subscriptions = await repo.list(str(current_user.tenant_id), **filters)
    return {
        "status": "success",
        "data": {"subscriptions": subscriptions, "total": len(subscriptions)},
        "meta": {"request_id": str(uuid4())},
    }
