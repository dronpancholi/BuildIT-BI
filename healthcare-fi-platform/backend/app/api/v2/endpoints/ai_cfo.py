"""
Domain 1: AI CFO Core API endpoints.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import dep_tenant_id
from app.core.dev_auth import DevUser, dep_dev_user
from app.db.session import get_db
from app.domain.ai_cfo import (
    BriefingMode,
    CFOCoreService,
)
from app.infrastructure.persistence.repositories import (
    CFOProfileRepository,
    CFOQuestionRepository,
    CFOBriefingRepository,
    CFOWorkspaceRepository,
    CFOAlertRepository,
)

router = APIRouter(tags=["AI CFO"])

__all__ = ["router"]


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class ProfileCreate(BaseModel):
    name: str
    role: str
    preferences: dict = {}


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    preferences: Optional[dict] = None


class QuestionRequest(BaseModel):
    user_query: str
    context: Optional[dict] = None


class BriefingRequest(BaseModel):
    mode: str
    period: str
    context: Optional[dict] = None


class WorkspaceCreate(BaseModel):
    name: str
    description: str = ""
    members: list = []


class WidgetCreate(BaseModel):
    widget_type: str
    config: dict = {}


class AlertConfigCreate(BaseModel):
    metric_id: str
    metric_name: str
    condition: dict
    thresholds: dict
    channels: list = []


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------


def _envelope(result: Any, total: int = 1) -> Dict[str, Any]:
    return {"data": result, "meta": {"total": total}}


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------


@router.get("/profiles")
async def list_profiles(
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """List CFO profiles for the tenant."""
    repo = CFOProfileRepository(db)
    profiles = await repo.list(str(tenant_id))
    return _envelope(profiles, total=len(profiles))


@router.post("/profiles")
async def create_profile(
    body: ProfileCreate,
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new CFO profile."""
    repo = CFOProfileRepository(db)
    profile = await repo.create(
        tenant_id=str(tenant_id),
        name=body.name,
        role=body.role,
        preferences=body.preferences or {},
    )
    return _envelope(profile)


@router.get("/profiles/{profile_id}")
async def get_profile(
    profile_id: UUID,
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a CFO profile by ID."""
    repo = CFOProfileRepository(db)
    profile = await repo.get(profile_id)
    if profile is None or str(profile["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Profile not found")
    return _envelope(profile)


@router.put("/profiles/{profile_id}")
async def update_profile(
    profile_id: UUID,
    body: ProfileUpdate,
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a CFO profile."""
    repo = CFOProfileRepository(db)
    existing = await repo.get(profile_id)
    if existing is None or str(existing["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Profile not found")
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    updated = await repo.update(profile_id, **updates)
    return _envelope(updated)


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------


@router.post("/questions")
async def ask_question(
    body: QuestionRequest,
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Ask a question to the AI CFO."""
    service = CFOCoreService()
    question = await service.ask_question(tenant_id, user.id, body.user_query, body.context or {})

    repo = CFOQuestionRepository(db)
    saved = await repo.create(
        tenant_id=str(tenant_id),
        user_id=str(user.id),
        user_query=question.user_query,
        intent=question.intent.value,
        answer=question.answer,
        evidence_chain=question.evidence_chain,
        confidence=question.confidence,
        processing_time_ms=question.processing_time_ms,
    )
    return _envelope(saved)


@router.get("/questions")
async def list_questions(
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """List questions for the tenant."""
    repo = CFOQuestionRepository(db)
    questions = await repo.list(str(tenant_id))
    return _envelope(questions, total=len(questions))


@router.get("/questions/{question_id}")
async def get_question(
    question_id: UUID,
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a question by ID."""
    repo = CFOQuestionRepository(db)
    question = await repo.get(question_id)
    if question is None or str(question["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Question not found")
    return _envelope(question)


# ---------------------------------------------------------------------------
# Briefings
# ---------------------------------------------------------------------------


@router.post("/briefings")
async def generate_briefing(
    body: BriefingRequest,
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an executive briefing."""
    try:
        mode = BriefingMode(body.mode)
    except ValueError:
        valid = [m.value for m in BriefingMode]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{body.mode}'. Must be one of: {valid}",
        )

    service = CFOCoreService()
    briefing = service.generate_briefing(tenant_id, mode, body.period, body.context)

    repo = CFOBriefingRepository(db)
    saved = await repo.create(
        tenant_id=str(tenant_id),
        mode=briefing.mode.value,
        status=briefing.status.value,
        period=briefing.period,
        generated_at=briefing.generated_at,
        sections=briefing.sections,
        score=briefing.score,
        executive_summary=briefing.executive_summary,
        key_findings=briefing.key_findings,
        actions=briefing.actions,
        narrative=briefing.narrative,
    )
    return _envelope(saved)


@router.get("/briefings")
async def list_briefings(
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """List briefings for the tenant."""
    repo = CFOBriefingRepository(db)
    briefings = await repo.list(str(tenant_id))
    return _envelope(briefings, total=len(briefings))


@router.get("/briefings/{briefing_id}")
async def get_briefing(
    briefing_id: UUID,
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a briefing by ID."""
    repo = CFOBriefingRepository(db)
    briefing = await repo.get(briefing_id)
    if briefing is None or str(briefing["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Briefing not found")
    return _envelope(briefing)


# ---------------------------------------------------------------------------
# Workspaces
# ---------------------------------------------------------------------------


@router.post("/workspaces")
async def create_workspace(
    body: WorkspaceCreate,
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a collaborative workspace."""
    repo = CFOWorkspaceRepository(db)
    ws = await repo.create(
        tenant_id=str(tenant_id),
        name=body.name,
        description=body.description,
        owner_id=str(user.id),
        widgets=[],
        layout={},
        shared=False,
    )
    return _envelope(ws)


@router.get("/workspaces")
async def list_workspaces(
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """List workspaces for the tenant."""
    repo = CFOWorkspaceRepository(db)
    workspaces = await repo.list(str(tenant_id))
    return _envelope(workspaces, total=len(workspaces))


@router.put("/workspaces/{workspace_id}/widgets")
async def add_widget(
    workspace_id: UUID,
    body: WidgetCreate,
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a widget to a workspace."""
    repo = CFOWorkspaceRepository(db)
    ws = await repo.get(workspace_id)
    if ws is None or str(ws["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Workspace not found")

    widgets = ws.get("widgets") or []
    widgets.append({
        "widget_id": str(uuid4()),
        "type": body.widget_type,
        "config": body.config,
    })
    updated = await repo.update(workspace_id, widgets=widgets)
    return _envelope(updated)


@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(
    workspace_id: UUID,
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a workspace."""
    repo = CFOWorkspaceRepository(db)
    ws = await repo.get(workspace_id)
    if ws is None or str(ws["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Workspace not found")
    await repo.delete(workspace_id)
    return _envelope({"deleted": True})


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


@router.post("/alerts/configs")
async def create_alert_config(
    body: AlertConfigCreate,
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an alert configuration."""
    try:
        metric_id = UUID(body.metric_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="metric_id must be a valid UUID")

    repo = CFOAlertRepository(db)
    cfg = await repo.create_config(
        tenant_id=str(tenant_id),
        metric_id=str(metric_id),
        metric_name=body.metric_name,
        user_id=str(user.id),
        condition=body.condition,
        thresholds=body.thresholds,
        channels=body.channels,
        is_active=True,
    )
    return _envelope(cfg)


@router.get("/alerts")
async def get_alerts(
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
    unread_only: bool = Query(False),
):
    """Get alerts for the current user."""
    repo = CFOAlertRepository(db)
    alerts = await repo.list(str(tenant_id), user_id=str(user.id))
    if unread_only:
        alerts = [a for a in alerts if not a.get("is_read")]
    return _envelope(alerts, total=len(alerts))


@router.put("/alerts/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: UUID,
    tenant_id: UUID = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss an alert."""
    repo = CFOAlertRepository(db)
    alert = await repo.get(alert_id)
    if alert is None or str(alert["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    updated = await repo.update(
        alert_id,
        is_dismissed=True,
        is_read=True,
        read_at=datetime.utcnow(),
    )
    return _envelope(updated)
