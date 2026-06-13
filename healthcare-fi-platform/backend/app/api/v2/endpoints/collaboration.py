from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dev_auth import DevUser, dep_dev_admin
from app.db.session import get_db
from app.infrastructure.persistence.repositories import CollaborationCommentRepository

router = APIRouter(tags=["Collaboration"])


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

@router.get("/comments")
async def list_comments(
    target_type: str = Query(..., description="Target type: dashboard, report, metric"),
    target_id: str = Query(..., description="Target entity ID"),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """List comments for a specific target entity."""
    repo = CollaborationCommentRepository(db)
    comments = await repo.get_thread(
        tenant_id=str(current_user.tenant_id),
        resource_type=target_type,
        resource_id=target_id,
    )
    return {"status": "success", "data": comments, "meta": {"request_id": str(uuid4())}}


@router.post("/comments")
async def create_comment(
    target_type: str = Query(...),
    target_id: str = Query(...),
    content: str = Query(..., min_length=1, max_length=5000),
    mentions: list[str] = Query(default_factory=list),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new comment on a target entity."""
    repo = CollaborationCommentRepository(db)
    comment = await repo.create(
        tenant_id=str(current_user.tenant_id),
        resource_type=target_type,
        resource_id=str(target_id),
        author_id=str(current_user.id),
        content=content,
        mentions=mentions,
        is_resolved=False,
    )
    return {"status": "success", "data": comment, "meta": {"request_id": str(uuid4())}}


@router.put("/comments/{comment_id}")
async def edit_comment(
    comment_id: UUID,
    content: str = Query(..., min_length=1, max_length=5000),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Edit an existing comment."""
    repo = CollaborationCommentRepository(db)
    existing = await repo.get(comment_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment = await repo.update(comment_id, content=content)
    return {"status": "success", "data": comment, "meta": {"request_id": str(uuid4())}}


@router.post("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: UUID,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Mark a comment as resolved."""
    repo = CollaborationCommentRepository(db)
    existing = await repo.get(comment_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Comment not found")
    result = await repo.update(
        comment_id,
        is_resolved=True,
        resolved_by=str(current_user.id),
        resolved_at=datetime.utcnow(),
    )
    return {"status": "success", "data": result, "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# Threads
# ---------------------------------------------------------------------------

@router.get("/threads")
async def list_threads(
    target_type: str = Query(...),
    target_id: str = Query(...),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """List discussion threads for a target entity."""
    repo = CollaborationCommentRepository(db)
    threads = await repo.get_thread(
        tenant_id=str(current_user.tenant_id),
        resource_type=target_type,
        resource_id=target_id,
    )
    return {"status": "success", "data": threads, "meta": {"request_id": str(uuid4())}}


@router.post("/threads")
async def create_thread(
    target_type: str = Query(...),
    target_id: str = Query(...),
    title: str = Query(..., min_length=1, max_length=255),
    initial_message: str = Query(..., min_length=1, max_length=5000),
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new discussion thread."""
    repo = CollaborationCommentRepository(db)
    thread = await repo.create(
        tenant_id=str(current_user.tenant_id),
        resource_type=target_type,
        resource_id=target_id,
        author_id=str(current_user.id),
        content=initial_message,
        title=title,
        is_resolved=False,
    )
    return {"status": "success", "data": thread, "meta": {"request_id": str(uuid4())}}


@router.post("/threads/{thread_id}/close")
async def close_thread(
    thread_id: UUID,
    current_user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Close a discussion thread."""
    repo = CollaborationCommentRepository(db)
    existing = await repo.get(thread_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Thread not found")
    result = await repo.update(
        thread_id,
        is_resolved=True,
        resolved_by=str(current_user.id),
        resolved_at=datetime.utcnow(),
    )
    return {"status": "success", "data": result, "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# Assignments (no dedicated repo — structured responses)
# ---------------------------------------------------------------------------

@router.get("/assignments")
async def list_assignments(
    status: Optional[str] = Query(None, description="Filter: pending, in_progress, completed"),
    assignee_id: Optional[str] = Query(None),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """List assignments with optional status filter."""
    return {"status": "success", "data": [], "meta": {"request_id": str(uuid4())}}


@router.post("/assignments")
async def create_assignment(
    title: str = Query(..., min_length=1, max_length=255),
    description: str = Query(default=""),
    assignee_id: str = Query(...),
    priority: str = Query(default="medium", description="low, medium, high, critical"),
    due_date: str = Query(..., description="ISO 8601 date"),
    target_type: str = Query(default="dashboard"),
    target_id: str = Query(default=None),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Create a new assignment."""
    assignment = {
        "title": title,
        "description": description,
        "assignee_id": str(assignee_id),
        "assigned_by": str(current_user.id),
        "status": "pending",
        "priority": priority,
        "due_date": due_date,
        "target_type": target_type,
        "target_id": str(target_id) if target_id else None,
    }
    return {"status": "success", "data": assignment, "meta": {"request_id": str(uuid4())}}


@router.put("/assignments/{assignment_id}")
async def update_assignment(
    assignment_id: UUID,
    status: str = Query(..., description="pending, in_progress, completed"),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Update assignment status."""
    result = {
        "id": str(assignment_id),
        "status": status,
        "updated_at": datetime.utcnow().isoformat(),
        "updated_by": str(current_user.id),
    }
    return {"status": "success", "data": result, "meta": {"request_id": str(uuid4())}}


@router.post("/assignments/{assignment_id}/complete")
async def complete_assignment(
    assignment_id: UUID,
    completion_notes: str = Query(default=""),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Mark an assignment as completed."""
    result = {
        "id": str(assignment_id),
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
        "completed_by": str(current_user.id),
        "completion_notes": completion_notes,
    }
    return {"status": "success", "data": result, "meta": {"request_id": str(uuid4())}}


# ---------------------------------------------------------------------------
# Watchlists (no dedicated repo — structured responses)
# ---------------------------------------------------------------------------

@router.get("/watchlists")
async def list_watchlists(
    current_user: DevUser = Depends(dep_dev_admin),
):
    """List user watchlists."""
    return {"status": "success", "data": [], "meta": {"request_id": str(uuid4())}}


@router.post("/watchlists")
async def create_watchlist(
    name: str = Query(..., min_length=1, max_length=100),
    description: str = Query(default=""),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Create a new watchlist."""
    watchlist = {
        "name": name,
        "description": description,
        "created_by": str(current_user.id),
        "created_at": datetime.utcnow().isoformat(),
        "item_count": 0,
        "items": [],
    }
    return {"status": "success", "data": watchlist, "meta": {"request_id": str(uuid4())}}


@router.put("/watchlists/{watchlist_id}")
async def update_watchlist(
    watchlist_id: UUID,
    name: str = Query(default=None),
    description: str = Query(default=None),
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Update a watchlist's metadata."""
    result = {
        "id": str(watchlist_id),
        "name": name,
        "description": description,
        "updated_at": datetime.utcnow().isoformat(),
        "updated_by": str(current_user.id),
    }
    return {"status": "success", "data": result, "meta": {"request_id": str(uuid4())}}


@router.delete("/watchlists/{watchlist_id}/items/{item_id}")
async def remove_watchlist_item(
    watchlist_id: UUID,
    item_id: UUID,
    current_user: DevUser = Depends(dep_dev_admin),
):
    """Remove an item from a watchlist."""
    result = {
        "watchlist_id": str(watchlist_id),
        "removed_item_id": str(item_id),
        "removed_at": datetime.utcnow().isoformat(),
        "removed_by": str(current_user.id),
    }
    return {"status": "success", "data": result, "meta": {"request_id": str(uuid4())}}
