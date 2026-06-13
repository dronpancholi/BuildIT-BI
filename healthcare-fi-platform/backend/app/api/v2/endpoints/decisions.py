"""
V2 Decision Intelligence API Endpoints.
REST API for Decision Management domain.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dev_auth import dep_dev_admin
from app.domain.decision.value_objects import (
    DecisionStatus,
    DecisionType,
    DecisionCategory,
    TriggerType,
    PriorityLabel,
    UrgencyLabel,
    ScopeType,
    EvidenceType,
    SourceType,
    ReviewDecision,
)
from app.domain.decision.services import (
    ProposeDecisionCommand,
    ApproveCommand,
    EvidenceInput,
)
from app.domain.decision.services.decision_service import DecisionService
from app.infrastructure.database.repositories.decision_repository import (
    DecisionRepository,
    DecisionEvidenceRepository,
    DecisionOutcomeRepository,
    DecisionReviewRepository,
    DecisionTimelineRepository,
)
from app.domain.decision.repositories import Pagination, DecisionFilter

router = APIRouter()


# ============================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================

class ProposeDecisionRequest(BaseModel):
    title: str
    description: str = ""
    decision_type: DecisionType
    category: DecisionCategory = DecisionCategory.OPERATIONAL
    priority: PriorityLabel = PriorityLabel.P2
    urgency: UrgencyLabel = UrgencyLabel.SCHEDULED
    trigger_type: TriggerType = TriggerType.MANUAL
    trigger_id: Optional[uuid.UUID] = None
    trigger_summary: str = ""
    department_ids: Optional[List[uuid.UUID]] = None
    scope_type: ScopeType = ScopeType.TENANT
    scope_id: Optional[uuid.UUID] = None
    estimated_value: Optional[float] = None
    estimated_cost: Optional[float] = None
    review_deadline: Optional[datetime] = None
    approval_deadline: Optional[datetime] = None
    implementation_target_date: Optional[datetime] = None
    tags: Optional[List[str]] = None


class ApproveRequest(BaseModel):
    review_decision: ReviewDecision = ReviewDecision.APPROVE
    comments: Optional[str] = None
    conditions: Optional[List[str]] = None


class RejectRequest(BaseModel):
    reason: str = ""


class AttachEvidenceRequest(BaseModel):
    evidence_type: EvidenceType
    title: str
    description: str = ""
    weight: float = 1.0
    source_type: SourceType = SourceType.USER_INPUT
    source_id: Optional[uuid.UUID] = None
    source_metric_code: Optional[str] = None
    data_payload: Optional[dict] = None


class DecisionResponse(BaseModel):
    id: str
    tenant_id: str
    title: str
    description: str
    decision_type: str
    status: str
    priority: str
    urgency: str
    trigger_type: str
    trigger_id: Optional[str] = None
    trigger_summary: str
    category: str
    department_ids: List[str]
    scope_type: str
    scope_id: Optional[str] = None
    estimated_value: Optional[float] = None
    estimated_cost: Optional[float] = None
    currency: str
    review_deadline: Optional[str] = None
    approval_deadline: Optional[str] = None
    implementation_target_date: Optional[str] = None
    completion_date: Optional[str] = None
    proposed_by: Optional[str] = None
    proposed_at: str
    reviewed_by: List[str]
    approved_by: List[str]
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    implemented_by: Optional[str] = None
    outcome_id: Optional[str] = None
    tags: List[str]
    version: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DecisionSummaryResponse(BaseModel):
    id: str
    title: str
    decision_type: str
    status: str
    priority: str
    category: str
    estimated_value: Optional[float] = None
    proposed_by: Optional[str] = None
    created_at: str
    evidence_count: int


class DecisionContextResponse(BaseModel):
    decision: DecisionResponse
    evidence: List[dict]
    timeline: List[dict]
    outcome: Optional[dict] = None
    reviews: List[dict]


class DecisionValueResponse(BaseModel):
    decision_id: str
    estimated_value: Optional[float] = None
    estimated_cost: Optional[float] = None
    realized_value: Optional[float] = None
    roi_expected: Optional[float] = None
    roi_actual: Optional[float] = None
    variance: Optional[float] = None


# ============================================================
# HELPERS
# ============================================================

def _get_service(db: AsyncSession) -> DecisionService:
    return DecisionService(
        decision_repo=DecisionRepository(db),
        evidence_repo=DecisionEvidenceRepository(db),
        outcome_repo=DecisionOutcomeRepository(db),
        review_repo=DecisionReviewRepository(db),
        timeline_repo=DecisionTimelineRepository(db),
    )


def _decision_to_response(d) -> DecisionResponse:
    return DecisionResponse(
        id=str(d.id),
        tenant_id=str(d.tenant_id),
        title=d.title,
        description=d.description,
        decision_type=d.decision_type.value,
        status=d.status.value,
        priority=d.priority.value,
        urgency=d.urgency.value,
        trigger_type=d.trigger_type.value,
        trigger_id=str(d.trigger_id) if d.trigger_id else None,
        trigger_summary=d.trigger_summary,
        category=d.category.value,
        department_ids=[str(dept) for dept in d.department_ids],
        scope_type=d.scope_type.value,
        scope_id=str(d.scope_id) if d.scope_id else None,
        estimated_value=d.estimated_value,
        estimated_cost=d.estimated_cost,
        currency=d.currency.value,
        review_deadline=d.review_deadline.isoformat() if d.review_deadline else None,
        approval_deadline=d.approval_deadline.isoformat() if d.approval_deadline else None,
        implementation_target_date=d.implementation_target_date.isoformat() if d.implementation_target_date else None,
        completion_date=d.completion_date.isoformat() if d.completion_date else None,
        proposed_by=str(d.proposed_by) if d.proposed_by else None,
        proposed_at=d.proposed_at.isoformat(),
        reviewed_by=[str(r) for r in d.reviewed_by],
        approved_by=[str(a) for a in d.approved_by],
        rejected_by=str(d.rejected_by) if d.rejected_by else None,
        rejection_reason=d.rejection_reason,
        implemented_by=str(d.implemented_by) if d.implemented_by else None,
        outcome_id=str(d.outcome_id) if d.outcome_id else None,
        tags=d.tags,
        version=d.version,
        created_at=d.created_at.isoformat(),
        updated_at=d.updated_at.isoformat(),
    )


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
async def propose_decision(
    request: ProposeDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_service(db)
    command = ProposeDecisionCommand(
        title=request.title,
        description=request.description,
        decision_type=request.decision_type,
        category=request.category,
        priority=request.priority,
        urgency=request.urgency,
        trigger_type=request.trigger_type,
        trigger_id=request.trigger_id,
        trigger_summary=request.trigger_summary,
        department_ids=request.department_ids,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        estimated_value=request.estimated_value,
        estimated_cost=request.estimated_cost,
        review_deadline=request.review_deadline,
        approval_deadline=request.approval_deadline,
        implementation_target_date=request.implementation_target_date,
        tags=request.tags,
    )
    tenant_id = uuid.UUID(str(current_user.tenant_id)) if hasattr(current_user, 'tenant_id') else uuid.uuid4()
    user_id = uuid.UUID(str(current_user.id))
    decision = await service.propose_decision(tenant_id, user_id, command)
    return _decision_to_response(decision)


@router.get("", response_model=List[DecisionResponse])
async def list_decisions(
    status_filter: Optional[DecisionStatus] = Query(None, alias="status"),
    decision_type: Optional[DecisionType] = None,
    category: Optional[DecisionCategory] = None,
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_service(db)
    tenant_id = uuid.UUID(str(current_user.tenant_id)) if hasattr(current_user, 'tenant_id') else uuid.uuid4()
    filters = DecisionFilter(
        status=status_filter,
        decision_type=decision_type,
        category=category,
        search_query=search,
    )
    decisions = await service._decisions.list(tenant_id, filters, Pagination(offset=offset, limit=limit))
    return [_decision_to_response(d) for d in decisions]


@router.get("/pending-review", response_model=List[DecisionSummaryResponse])
async def get_pending_review(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_service(db)
    tenant_id = uuid.UUID(str(current_user.tenant_id)) if hasattr(current_user, 'tenant_id') else uuid.uuid4()
    summaries = await service.get_decisions_requiring_review(tenant_id)
    return [DecisionSummaryResponse(
        id=str(s.id),
        title=s.title,
        decision_type=s.decision_type.value,
        status=s.status.value,
        priority=s.priority.value,
        category=s.category.value,
        estimated_value=s.estimated_value,
        proposed_by=str(s.proposed_by) if s.proposed_by else None,
        created_at=s.created_at.isoformat(),
        evidence_count=s.evidence_count,
    ) for s in summaries]


@router.get("/{decision_id}", response_model=DecisionContextResponse)
async def get_decision(
    decision_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_service(db)
    tenant_id = uuid.UUID(str(current_user.tenant_id)) if hasattr(current_user, 'tenant_id') else uuid.uuid4()
    try:
        ctx = await service.get_decision_with_context(decision_id, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return DecisionContextResponse(
        decision=_decision_to_response(ctx.decision),
        evidence=[e.to_dict() for e in ctx.evidence],
        timeline=ctx.timeline,
        outcome=ctx.outcome.to_dict() if ctx.outcome else None,
        reviews=[r.to_dict() for r in ctx.reviews],
    )


@router.post("/{decision_id}/submit", response_model=DecisionResponse)
async def submit_for_review(
    decision_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_service(db)
    tenant_id = uuid.UUID(str(current_user.tenant_id)) if hasattr(current_user, 'tenant_id') else uuid.uuid4()
    user_id = uuid.UUID(str(current_user.id))
    try:
        decision = await service.submit_for_review(decision_id, tenant_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _decision_to_response(decision)


@router.post("/{decision_id}/approve", response_model=DecisionResponse)
async def approve_decision(
    decision_id: uuid.UUID,
    request: ApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_service(db)
    tenant_id = uuid.UUID(str(current_user.tenant_id)) if hasattr(current_user, 'tenant_id') else uuid.uuid4()
    reviewer_id = uuid.UUID(str(current_user.id))
    command = ApproveCommand(
        review_decision=request.review_decision,
        comments=request.comments,
        conditions=request.conditions,
    )
    try:
        decision = await service.approve(decision_id, tenant_id, reviewer_id, command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _decision_to_response(decision)


@router.post("/{decision_id}/reject", response_model=DecisionResponse)
async def reject_decision(
    decision_id: uuid.UUID,
    request: RejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_service(db)
    tenant_id = uuid.UUID(str(current_user.tenant_id)) if hasattr(current_user, 'tenant_id') else uuid.uuid4()
    reviewer_id = uuid.UUID(str(current_user.id))
    try:
        decision = await service.reject(decision_id, tenant_id, reviewer_id, request.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _decision_to_response(decision)


@router.post("/{decision_id}/start-implementation", response_model=DecisionResponse)
async def start_implementation(
    decision_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_service(db)
    tenant_id = uuid.UUID(str(current_user.tenant_id)) if hasattr(current_user, 'tenant_id') else uuid.uuid4()
    user_id = uuid.UUID(str(current_user.id))
    try:
        decision = await service.start_implementation(decision_id, tenant_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _decision_to_response(decision)


@router.post("/{decision_id}/complete", response_model=DecisionResponse)
async def complete_implementation(
    decision_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_service(db)
    tenant_id = uuid.UUID(str(current_user.tenant_id)) if hasattr(current_user, 'tenant_id') else uuid.uuid4()
    user_id = uuid.UUID(str(current_user.id))
    try:
        decision = await service.complete_implementation(decision_id, tenant_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _decision_to_response(decision)


@router.post("/{decision_id}/evidence", status_code=status.HTTP_201_CREATED)
async def attach_evidence(
    decision_id: uuid.UUID,
    request: AttachEvidenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_service(db)
    tenant_id = uuid.UUID(str(current_user.tenant_id)) if hasattr(current_user, 'tenant_id') else uuid.uuid4()
    user_id = uuid.UUID(str(current_user.id))
    evidence_input = EvidenceInput(
        evidence_type=request.evidence_type,
        title=request.title,
        description=request.description,
        weight=request.weight,
        source_type=request.source_type,
        source_id=request.source_id,
        source_metric_code=request.source_metric_code,
        data_payload=request.data_payload,
    )
    try:
        evidence = await service.attach_evidence(decision_id, tenant_id, user_id, evidence_input)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return evidence.to_dict()


@router.get("/{decision_id}/timeline")
async def get_timeline(
    decision_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_service(db)
    tenant_id = uuid.UUID(str(current_user.tenant_id)) if hasattr(current_user, 'tenant_id') else uuid.uuid4()
    await service._get_and_validate(decision_id, tenant_id)
    timeline = await service._timeline.get_by_decision(decision_id)
    return [t.to_dict() for t in timeline]


@router.get("/{decision_id}/value", response_model=DecisionValueResponse)
async def get_decision_value(
    decision_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(dep_dev_admin),
):
    service = _get_service(db)
    try:
        value = await service.calculate_decision_value(decision_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return DecisionValueResponse(
        decision_id=str(value.decision_id),
        estimated_value=value.estimated_value,
        estimated_cost=value.estimated_cost,
        realized_value=value.realized_value,
        roi_expected=value.roi_expected,
        roi_actual=value.roi_actual,
        variance=value.variance,
    )
