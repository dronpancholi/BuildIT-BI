from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel, Field

from app.core.dev_auth import DevUser, dep_dev_admin
from app.db.session import get_db
from app.infrastructure.persistence.repositories import (
    CFOWorkspaceRepository,
    CFOBriefingRepository,
)

class NotificationUpdateRequest(BaseModel):
    channel: Optional[str] = None
    channel_enabled: Optional[bool] = None
    preference_key: Optional[str] = None
    preference_enabled: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None

router = APIRouter(tags=["Executive Workspace"])


@router.get("")
async def get_workspace_layout(
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get the user's workspace layout configuration."""
    repo = CFOWorkspaceRepository(db)
    workspaces = await repo.list(str(current_user.tenant_id), user_id=str(current_user.id))
    if workspaces:
        workspace = workspaces[0]
    else:
        workspace = {
            "user_id": str(current_user.id),
            "layout": {
                "columns": 3,
                "gap": 16,
                "sections": [],
            },
        }
    return {"status": "success", "data": workspace, "meta": {"request_id": str(uuid4())}}


@router.put("")
async def update_workspace_layout(
    columns: int = Query(default=3, ge=1, le=6),
    gap: int = Query(default=16, ge=4, le=48),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update the user's workspace layout."""
    repo = CFOWorkspaceRepository(db)
    workspaces = await repo.list(str(current_user.tenant_id), user_id=str(current_user.id))
    if workspaces:
        workspace = await repo.update(
            workspaces[0]["id"],
            columns=columns,
            gap=gap,
        )
    else:
        workspace = await repo.create(
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.id),
            layout={"columns": columns, "gap": gap},
        )
    return {"status": "success", "data": workspace, "meta": {"request_id": str(uuid4())}}


@router.put("/sections/{section_type}")
async def update_section_config(
    section_type: str,
    title: str = Query(default=None),
    visible: bool = Query(default=True),
    config_json: str = Query(default="{}", alias="config"),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a specific workspace section's configuration."""
    repo = CFOWorkspaceRepository(db)
    workspaces = await repo.list(str(current_user.tenant_id), user_id=str(current_user.id))
    if workspaces:
        ws = workspaces[0]
        layout = ws.get("layout", {})
        sections = layout.get("sections", [])
        updated = False
        for section in sections:
            if section.get("type") == section_type:
                if title is not None:
                    section["title"] = title
                section["visible"] = visible
                section["config"] = config_json
                updated = True
                break
        if updated:
            await repo.update(ws["id"], layout=layout)
    return {
        "status": "success",
        "data": {
            "section_type": section_type,
            "title": title or section_type.replace("_", " ").title(),
            "visible": visible,
            "config": config_json,
        },
        "meta": {"request_id": str(uuid4())},
    }


# ---------------------------------------------------------------------------
# Briefings
# ---------------------------------------------------------------------------

@router.get("/briefings")
async def list_briefings(
    unread_only: bool = Query(default=False),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """List executive briefings for the user."""
    repo = CFOBriefingRepository(db)
    filters = {}
    if unread_only:
        filters["is_read"] = False
    briefings = await repo.list(str(current_user.tenant_id), **filters)
    return {"status": "success", "data": briefings, "meta": {"request_id": str(uuid4())}}


@router.get("/briefings/{briefing_id}")
async def get_briefing_detail(
    briefing_id: UUID,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed briefing with full content."""
    repo = CFOBriefingRepository(db)
    briefing = await repo.get(briefing_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")
    return {"status": "success", "data": briefing, "meta": {"request_id": str(uuid4())}}


@router.post("/briefings/generate")
async def generate_briefing(
    briefing_type: str = Query(..., description="daily_revenue, weekly_payer_mix, monthly_close, alert"),
    time_range: str = Query(default="1d", description="Time range for data aggregation"),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new executive briefing."""
    repo = CFOBriefingRepository(db)
    briefing = await repo.create(
        tenant_id=str(current_user.tenant_id),
        title=f"{briefing_type.replace('_', ' ').title()} — Generated",
        briefing_type=briefing_type,
        time_range=time_range,
        generated_by=str(current_user.id),
        status="generating",
    )
    return {"status": "success", "data": briefing, "meta": {"request_id": str(uuid4())}}


@router.put("/briefings/{briefing_id}/read")
async def mark_briefing_read(
    briefing_id: UUID,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Mark a briefing as read."""
    repo = CFOBriefingRepository(db)
    existing = await repo.get(briefing_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Briefing not found")
    result = await repo.update(
        briefing_id,
        is_read=True,
        read_at=datetime.utcnow(),
    )
    return {"status": "success", "data": result, "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# Notification Config (static config)
# ---------------------------------------------------------------------------

@router.get("/notifications/config")
async def get_notification_config(
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Get user notification preferences."""
    config = {
        "user_id": str(current_user.id),
        "channels": {
            "email": {"enabled": True, "address": current_user.email},
            "in_app": {"enabled": True, "sound": True},
            "slack": {"enabled": False, "webhook_url": None},
            "sms": {"enabled": False, "phone": None},
        },
        "preferences": {
            "briefing_notifications": {"enabled": True, "frequency": "daily"},
            "alert_notifications": {"enabled": True, "frequency": "immediate"},
            "assignment_notifications": {"enabled": True, "frequency": "immediate"},
            "comment_mentions": {"enabled": True, "frequency": "immediate"},
            "certification_updates": {"enabled": True, "frequency": "weekly"},
            "usage_reports": {"enabled": False, "frequency": "monthly"},
        },
        "quiet_hours": {"enabled": True, "start": "22:00", "end": "07:00", "timezone": "America/New_York"},
        "updated_at": datetime.utcnow().isoformat(),
    }
    return {"status": "success", "data": config, "meta": {"request_id": str(uuid4())}}


@router.put("/notifications/config")
async def update_notification_config(
    req: NotificationUpdateRequest,
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Update notification preferences."""
    result = {
        "user_id": str(current_user.id),
        "updated_at": datetime.utcnow().isoformat(),
        "changes": [],
    }
    if req.channel:
        result["changes"].append({"type": "channel", "channel": req.channel, "enabled": req.channel_enabled})
    if req.preference_key:
        result["changes"].append({"type": "preference", "key": req.preference_key, "enabled": req.preference_enabled})
    if req.quiet_hours_enabled is not None:
        result["changes"].append({
            "type": "quiet_hours",
            "enabled": req.quiet_hours_enabled,
            "start": req.quiet_hours_start,
            "end": req.quiet_hours_end,
        })
    return {"status": "success", "data": result, "meta": {"request_id": str(uuid4())}}
