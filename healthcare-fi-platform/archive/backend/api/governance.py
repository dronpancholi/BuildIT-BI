from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dev_auth import DevUser, dep_dev_admin
from app.db.session import get_db
from app.infrastructure.persistence.repositories import DashboardRepository

router = APIRouter(tags=["Analytics Governance"])


# ---------------------------------------------------------------------------
# Dashboard Versions
# ---------------------------------------------------------------------------

@router.get("/dashboards/{dashboard_id}/versions")
async def list_dashboard_versions(
    dashboard_id: UUID,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """List versions of a dashboard."""
    repo = DashboardRepository(db)
    dashboard = await repo.get(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    versions = await repo.list(
        str(current_user.tenant_id),
        parent_dashboard_id=str(dashboard_id),
    )
    return {
        "status": "success",
        "data": {"dashboard_id": str(dashboard_id), "versions": versions},
        "meta": {"request_id": str(uuid4())},
    }


@router.post("/dashboards/{dashboard_id}/versions")
async def create_dashboard_version(
    dashboard_id: UUID,
    label: str = Query(..., min_length=1, max_length=255),
    notes: str = Query(default=""),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a dashboard version snapshot."""
    repo = DashboardRepository(db)
    existing = await repo.get(dashboard_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    version = await repo.create(
        tenant_id=str(current_user.tenant_id),
        parent_dashboard_id=str(dashboard_id),
        name=label,
        description=notes,
        owner_id=str(current_user.id),
        version_label=label,
        snapshot_status="completed",
    )
    return {"status": "success", "data": version, "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# Report Versions
# ---------------------------------------------------------------------------

@router.get("/reports/{report_id}/versions")
async def list_report_versions(
    report_id: UUID,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """List versions of a report."""
    repo = DashboardRepository(db)
    versions = await repo.list(
        str(current_user.tenant_id),
        parent_dashboard_id=str(report_id),
    )
    return {
        "status": "success",
        "data": {"report_id": str(report_id), "versions": versions},
        "meta": {"request_id": str(uuid4())},
    }


@router.post("/reports/{report_id}/versions")
async def create_report_version(
    report_id: UUID,
    label: str = Query(..., min_length=1, max_length=255),
    notes: str = Query(default=""),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a report version snapshot."""
    repo = DashboardRepository(db)
    version = await repo.create(
        tenant_id=str(current_user.tenant_id),
        parent_dashboard_id=str(report_id),
        name=label,
        description=notes,
        owner_id=str(current_user.id),
        version_label=label,
        snapshot_status="completed",
    )
    return {"status": "success", "data": version, "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# Certified Metrics (static governance config)
# ---------------------------------------------------------------------------

@router.get("/certifications/metrics")
async def list_certified_metrics(
    status: Optional[str] = Query(None, description="pending, certified, deprecated"),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """List certified metrics."""
    metrics = [
        {
            "name": "Net Collection Rate",
            "definition": "Total payments received divided by total allowed amount, expressed as a percentage",
            "formula": "(payments_received / allowed_amount) * 100",
            "category": "Revenue Cycle",
            "status": "certified",
            "version": 3,
            "data_sources": ["claims", "remittances"],
            "refresh_frequency": "daily",
        },
        {
            "name": "Days in Accounts Receivable",
            "definition": "Average number of days to collect payment after a service is rendered",
            "formula": "(total_ar / net_patient_revenue) * days_in_period",
            "category": "Revenue Cycle",
            "status": "certified",
            "version": 2,
            "data_sources": ["ar_aging", "revenue"],
            "refresh_frequency": "daily",
        },
        {
            "name": "Claims Denial Rate",
            "definition": "Percentage of claims denied by payers",
            "formula": "(denied_claims / total_claims_submitted) * 100",
            "category": "Claims",
            "status": "pending",
            "version": 1,
            "data_sources": ["claims"],
            "refresh_frequency": "daily",
        },
    ]
    if status:
        metrics = [m for m in metrics if m["status"] == status]
    return {"status": "success", "data": metrics, "meta": {"request_id": str(uuid4())}}


@router.post("/certifications/metrics")
async def submit_metric_for_certification(
    name: str = Query(..., min_length=1, max_length=255),
    definition: str = Query(..., min_length=1),
    formula: str = Query(..., min_length=1),
    category: str = Query(...),
    data_sources: list[str] = Query(...),
    refresh_frequency: str = Query(default="daily"),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Submit a metric for certification."""
    submission = {
        "name": name,
        "definition": definition,
        "formula": formula,
        "category": category,
        "owner_id": str(current_user.id),
        "status": "pending",
        "submitted_at": datetime.utcnow().isoformat(),
        "version": 1,
        "data_sources": data_sources,
        "refresh_frequency": refresh_frequency,
    }
    return {"status": "success", "data": submission, "meta": {"request_id": str(uuid4())}}


@router.put("/certifications/metrics/{metric_id}/certify")
async def certify_metric(
    metric_id: UUID,
    approval_notes: str = Query(default=""),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Certify a metric after review."""
    result = {
        "id": str(metric_id),
        "status": "certified",
        "certified_at": datetime.utcnow().isoformat(),
        "certified_by": str(current_user.id),
        "approval_notes": approval_notes,
        "valid_until": (datetime.utcnow() + timedelta(days=365)).isoformat(),
    }
    return {"status": "success", "data": result, "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# Certified Reports (static governance config)
# ---------------------------------------------------------------------------

@router.get("/certifications/reports")
async def list_certified_reports(
    status: Optional[str] = Query(None),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """List certified reports."""
    reports = [
        {
            "name": "Monthly Revenue Cycle Summary",
            "description": "Comprehensive monthly summary of revenue cycle performance metrics",
            "category": "Financial",
            "status": "certified",
            "version": 4,
            "metrics_included": ["Net Collection Rate", "Days in A/R", "Clean Claim Rate"],
            "refresh_frequency": "monthly",
        },
        {
            "name": "Payer Mix Analysis Report",
            "description": "Breakdown of patient volume and revenue by payer category",
            "category": "Financial",
            "status": "certified",
            "version": 3,
            "metrics_included": ["Payer Mix Percentage", "Revenue by Payer", "Volume by Payer"],
            "refresh_frequency": "monthly",
        },
        {
            "name": "Claims Denial Root Cause Report",
            "description": "Analysis of denial reasons with actionable recommendations",
            "category": "Claims",
            "status": "pending",
            "version": 1,
            "metrics_included": ["Claims Denial Rate", "Top Denial Reasons", "Appeal Success Rate"],
            "refresh_frequency": "weekly",
        },
    ]
    if status:
        reports = [r for r in reports if r["status"] == status]
    return {"status": "success", "data": reports, "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# Approval Workflows (static governance config)
# ---------------------------------------------------------------------------

@router.post("/approvals")
async def create_approval_workflow(
    entity_type: str = Query(..., description="metric, report, dashboard, config_change"),
    entity_id: UUID = Query(...),
    title: str = Query(..., min_length=1, max_length=255),
    description: str = Query(default=""),
    required_approvers: int = Query(default=1, ge=1, le=10),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Create a new approval workflow."""
    workflow = {
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "title": title,
        "description": description,
        "status": "pending",
        "created_by": str(current_user.id),
        "created_at": datetime.utcnow().isoformat(),
        "required_approvers": required_approvers,
        "current_approvals": 0,
        "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat(),
    }
    return {"status": "success", "data": workflow, "meta": {"request_id": str(uuid4())}}


@router.put("/approvals/{workflow_id}/approve")
async def approve_workflow(
    workflow_id: UUID,
    comments: str = Query(default=""),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Approve an approval workflow."""
    result = {
        "id": str(workflow_id),
        "status": "approved",
        "approved_by": str(current_user.id),
        "approved_at": datetime.utcnow().isoformat(),
        "comments": comments,
    }
    return {"status": "success", "data": result, "meta": {"request_id": str(uuid4())}}


@router.put("/approvals/{workflow_id}/reject")
async def reject_workflow(
    workflow_id: UUID,
    reason: str = Query(..., min_length=1, max_length=2000),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Reject an approval workflow."""
    result = {
        "id": str(workflow_id),
        "status": "rejected",
        "rejected_by": str(current_user.id),
        "rejected_at": datetime.utcnow().isoformat(),
        "reason": reason,
    }
    return {"status": "success", "data": result, "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# Usage Metrics (static governance config)
# ---------------------------------------------------------------------------

@router.get("/usage")
async def list_usage_metrics(
    staleness_filter: Optional[str] = Query(None, description="fresh, stale, all"),
    metric_name: Optional[str] = Query(None),
    limit: int = Query(default=25, ge=1, le=100),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """List usage metrics with staleness filter."""
    usage_metrics = [
        {
            "metric_name": "Net Collection Rate",
            "last_refreshed": datetime.utcnow().isoformat(),
            "staleness": "fresh",
            "staleness_hours": 2,
            "data_freshness_threshold_hours": 24,
            "usage_count_30d": 342,
        },
        {
            "metric_name": "Days in Accounts Receivable",
            "last_refreshed": datetime.utcnow().isoformat(),
            "staleness": "fresh",
            "staleness_hours": 2,
            "data_freshness_threshold_hours": 24,
            "usage_count_30d": 287,
        },
        {
            "metric_name": "Claims Denial Rate",
            "last_refreshed": (datetime.utcnow() - timedelta(hours=48)).isoformat(),
            "staleness": "stale",
            "staleness_hours": 48,
            "data_freshness_threshold_hours": 24,
            "usage_count_30d": 198,
        },
        {
            "metric_name": "Operating Margin",
            "last_refreshed": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "staleness": "stale",
            "staleness_hours": 168,
            "data_freshness_threshold_hours": 72,
            "usage_count_30d": 156,
        },
    ]
    if staleness_filter and staleness_filter != "all":
        usage_metrics = [m for m in usage_metrics if m["staleness"] == staleness_filter]
    if metric_name:
        usage_metrics = [m for m in usage_metrics if metric_name.lower() in m["metric_name"].lower()]
    usage_metrics = usage_metrics[:limit]
    return {"status": "success", "data": usage_metrics, "meta": {"request_id": str(uuid4())}}
