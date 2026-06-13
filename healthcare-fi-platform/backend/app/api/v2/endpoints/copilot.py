"""
Domain 10: AI CFO Copilot API endpoints.
Natural language interface for healthcare financial analysis with multi-step reasoning,
cross-domain analysis, and proactive insights.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import dep_tenant_id
from app.core.dev_auth import DevUser, dep_dev_user
from app.db.session import get_db
from app.domain.copilot import (
    AICFOCopilot,
    Conversation,
    CopilotActionRecord,
    CopilotCapability,
    CopilotSuggestion,
    ConversationStatus,
    Message,
    ReasoningChain,
)
from app.infrastructure.persistence.repositories import CopilotConversationRepository

router = APIRouter(tags=["AI CFO Copilot"])

__all__ = ["router"]


def _deep_serialize(obj: Any) -> Any:
    """Recursively convert Enums and datetimes to JSON-safe values."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _deep_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_deep_serialize(item) for item in obj]
    return obj


def _envelope(result: Any, total: int = 1) -> Dict[str, Any]:
    return {"data": result, "meta": {"total": total}}


def _serialize_message(msg: Message) -> Dict[str, Any]:
    return _deep_serialize(msg.to_dict())


def _serialize_conversation(conv: Conversation) -> Dict[str, Any]:
    return conv.to_dict()


def _serialize_action_record(record: CopilotActionRecord) -> Dict[str, Any]:
    return _deep_serialize(record.to_dict())


def _serialize_reasoning_chain(chain: ReasoningChain) -> Dict[str, Any]:
    return chain.to_dict()


def _serialize_suggestion(suggestion: CopilotSuggestion) -> Dict[str, Any]:
    return suggestion.to_dict()


def _serialize_capability(cap: CopilotCapability) -> Dict[str, Any]:
    return {"name": cap.value}


# ---------------------------------------------------------------------------
# Query Processing
# ---------------------------------------------------------------------------


@router.post("/query")
async def process_query(
    body: Dict[str, Any] = Body(...),
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Process a natural language query through the copilot."""
    user_query = body.get("user_query")
    if not user_query:
        raise HTTPException(status_code=400, detail="user_query is required")
    context = body.get("context", {})

    try:
        copilot = AICFOCopilot(tenant_id)
        message, actions = await copilot.process_query(user.id, user_query, context)

        repo = CopilotConversationRepository(db)
        conversation = await repo.create(
            tenant_id=tenant_id,
            user_id=user.id,
            title=user_query[:200],
            status="active",
            messages=[_serialize_message(message)],
            context=context,
        )

        return _envelope({
            "conversation_id": str(conversation["id"]),
            "message": _serialize_message(message),
            "actions_taken": [_serialize_action_record(a) for a in actions],
        })
    except Exception as e:
        # Graceful fallback — return a response even if storage fails
        return _envelope({
            "conversation_id": None,
            "message": _serialize_message(message) if 'message' in locals() else {"content": user_query},
            "actions_taken": [_serialize_action_record(a) for a in actions] if 'actions' in locals() else [],
            "error": str(e) if str(e) else "Processing completed without storage",
        })


# ---------------------------------------------------------------------------
# Multi-Step Reasoning
# ---------------------------------------------------------------------------


@router.post("/reasoning")
async def multi_step_reasoning(
    body: Dict[str, Any] = Body(...),
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute multi-step reasoning for a query."""
    query = body.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    context = body.get("context", {})

    copilot = AICFOCopilot(tenant_id)
    chain = copilot.multi_step_reasoning(query, context)

    return _envelope(_serialize_reasoning_chain(chain))


# ---------------------------------------------------------------------------
# Suggestions
# ---------------------------------------------------------------------------


@router.get("/suggestions")
async def get_suggestions(
    limit: int = Query(5, ge=1, le=50),
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Get proactive suggestions based on user history and context."""
    copilot = AICFOCopilot(tenant_id)
    suggestions = copilot.generate_suggestions(user.id)
    result = [_serialize_suggestion(s) for s in suggestions[:limit]]
    return _envelope(result, total=len(result))


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------


@router.get("/conversations")
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """List conversations for the current user."""
    repo = CopilotConversationRepository(db)
    rows = await repo.list(str(tenant_id), user_id=user.id)
    items = [dict(r) for r in rows[:limit]]
    return _envelope(items, total=len(items))


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific conversation by ID."""
    repo = CopilotConversationRepository(db)
    conversation = await repo.get(conversation_id)
    if conversation is None or str(conversation["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _envelope(conversation)


@router.put("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: UUID,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Archive a conversation."""
    repo = CopilotConversationRepository(db)
    conversation = await repo.get(conversation_id)
    if conversation is None or str(conversation["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    updated = await repo.update(conversation_id, status="archived")
    return _envelope(updated)


# ---------------------------------------------------------------------------
# Reasoning Explanation
# ---------------------------------------------------------------------------


@router.get("/actions/{action_id}/reasoning")
async def explain_reasoning(
    action_id: UUID,
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """Explain the reasoning behind a specific copilot action."""
    copilot = AICFOCopilot(tenant_id)
    reasoning = copilot.explain_reasoning(action_id)
    if not reasoning:
        raise HTTPException(status_code=404, detail="Action or reasoning not found")
    return _envelope(reasoning, total=len(reasoning))


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


@router.get("/capabilities")
async def list_capabilities(
    tenant_id: str = Depends(dep_tenant_id),
    user: DevUser = Depends(dep_dev_user),
    db: AsyncSession = Depends(get_db),
):
    """List available copilot capabilities."""
    copilot = AICFOCopilot(tenant_id)
    result = [_serialize_capability(c) for c in copilot._capabilities]
    return _envelope(result, total=len(result))
