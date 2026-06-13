"""
Decision Repository Implementations.
SQLAlchemy async implementations of all Decision domain repository interfaces.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.decision.repositories import (
    IDecisionRepository,
    IDecisionEvidenceRepository,
    IDecisionOutcomeRepository,
    IDecisionReviewRepository,
    IDecisionTimelineRepository,
    Pagination,
    DecisionFilter,
)
from app.domain.decision.entities import (
    Decision,
    DecisionEvidence,
    DecisionOutcome,
    DecisionReview,
    DecisionTimeline,
)
from app.domain.decision.value_objects import (
    DecisionStatus,
    DecisionType,
    DecisionCategory,
    ScopeType,
    TriggerType,
    PriorityLabel,
    UrgencyLabel,
    Currency,
    EvidenceType,
    SourceType,
    ReviewType,
    ReviewStatus,
    ReviewDecision,
    TimelineEventType,
    OutcomeStatus,
)
from app.infrastructure.persistence.models import (
    DecisionModel,
    DecisionEvidenceModel,
    DecisionOutcomeModel,
    DecisionReviewModel,
    DecisionTimelineModel,
)


# ============================================================
# MAPPING FUNCTIONS
# ============================================================

def _model_to_decision(m: DecisionModel) -> Decision:
    """Map DecisionModel to Decision domain entity."""
    return Decision(
        id=m.id,
        tenant_id=m.tenant_id,
        title=m.title,
        description=m.description or "",
        decision_type=DecisionType(m.decision_type),
        status=DecisionStatus(m.status),
        priority=PriorityLabel(m.priority),
        urgency=UrgencyLabel(m.urgency),
        trigger_type=TriggerType(m.trigger_type) if m.trigger_type else TriggerType.MANUAL,
        trigger_id=m.trigger_id,
        trigger_summary=m.trigger_summary or "",
        category=DecisionCategory(m.category),
        department_ids=[uuid.UUID(d) if isinstance(d, str) else d for d in (m.department_ids or [])],
        scope_type=ScopeType(m.scope_type),
        scope_id=m.scope_id,
        estimated_value=m.estimated_value,
        estimated_cost=m.estimated_cost,
        currency=Currency(m.currency),
        review_deadline=m.review_deadline,
        approval_deadline=m.approval_deadline,
        implementation_target_date=m.implementation_target_date.date() if m.implementation_target_date else None,
        completion_date=m.completion_date,
        proposed_by=m.proposed_by,
        proposed_at=m.proposed_at,
        reviewed_by=[uuid.UUID(r) if isinstance(r, str) else r for r in (m.reviewed_by or [])],
        approved_by=[uuid.UUID(a) if isinstance(a, str) else a for a in (m.approved_by or [])],
        rejected_by=m.rejected_by,
        rejection_reason=m.rejection_reason,
        implemented_by=m.implemented_by,
        outcome_id=m.outcome_id,
        tags=m.tags or [],
        metadata=m.metadata_ or {},
        version=m.version,
        created_at=m.created_at,
        created_by=m.created_by,
        updated_at=m.updated_at,
        updated_by=m.updated_by,
        deleted_at=m.deleted_at,
        deleted_by=m.deleted_by,
    )


def _decision_to_model(d: Decision) -> Dict[str, Any]:
    """Map Decision domain entity to model kwargs."""
    impl_target = None
    if d.implementation_target_date:
        impl_target = datetime.combine(d.implementation_target_date, datetime.min.time())
    return {
        "id": d.id,
        "tenant_id": d.tenant_id,
        "title": d.title,
        "description": d.description,
        "decision_type": d.decision_type.value,
        "status": d.status.value,
        "priority": d.priority.value,
        "urgency": d.urgency.value,
        "trigger_type": d.trigger_type.value,
        "trigger_id": d.trigger_id,
        "trigger_summary": d.trigger_summary,
        "category": d.category.value,
        "department_ids": d.department_ids,
        "scope_type": d.scope_type.value,
        "scope_id": d.scope_id,
        "estimated_value": d.estimated_value,
        "estimated_cost": d.estimated_cost,
        "currency": d.currency.value,
        "review_deadline": d.review_deadline,
        "approval_deadline": d.approval_deadline,
        "implementation_target_date": impl_target,
        "completion_date": d.completion_date,
        "proposed_by": d.proposed_by,
        "proposed_at": d.proposed_at,
        "reviewed_by": [str(r) for r in d.reviewed_by],
        "approved_by": [str(a) for a in d.approved_by],
        "rejected_by": d.rejected_by,
        "rejection_reason": d.rejection_reason,
        "implemented_by": d.implemented_by,
        "outcome_id": d.outcome_id,
        "tags": d.tags,
        "metadata_": d.metadata,
        "version": d.version,
        "created_at": d.created_at,
        "created_by": d.created_by,
        "updated_at": d.updated_at,
        "updated_by": d.updated_by,
        "deleted_at": d.deleted_at,
        "deleted_by": d.deleted_by,
    }


def _model_to_evidence(m: DecisionEvidenceModel) -> DecisionEvidence:
    return DecisionEvidence(
        id=m.id,
        tenant_id=m.tenant_id,
        decision_id=m.decision_id,
        evidence_type=EvidenceType(m.evidence_type),
        title=m.title,
        description=m.description or "",
        weight=m.weight,
        source_type=SourceType(m.source_type) if m.source_type else SourceType.USER_INPUT,
        source_id=m.source_id,
        source_metric_code=m.source_metric_code,
        data_payload=m.data_payload or {},
        created_at=m.created_at,
        created_by=m.created_by,
    )


def _model_to_outcome(m: DecisionOutcomeModel) -> DecisionOutcome:
    return DecisionOutcome(
        id=m.id,
        tenant_id=m.tenant_id,
        decision_id=m.decision_id,
        measurement_start=m.measurement_start,
        measurement_end=m.measurement_end,
        expected_metrics=[],
        actual_metrics=[],
        accuracy_score=m.accuracy_score,
        variance_absolute=m.variance_absolute,
        variance_percent=m.variance_percent,
        outcome_status=OutcomeStatus(m.outcome_status),
        realized_value=m.realized_value,
        roi_actual=m.roi_actual,
        measured_by=m.measured_by,
        measured_at=m.measured_at,
        version=m.version,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _model_to_review(m: DecisionReviewModel) -> DecisionReview:
    return DecisionReview(
        id=m.id,
        tenant_id=m.tenant_id,
        decision_id=m.decision_id,
        review_type=ReviewType(m.review_type),
        review_round=m.review_round,
        status=ReviewStatus(m.status),
        reviewer_id=m.reviewer_id,
        reviewer_role=m.reviewer_role or "",
        review_decision=ReviewDecision(m.review_decision) if m.review_decision else None,
        comments=[],
        conditions=m.conditions,
        escalation_required=m.escalation_required,
        escalation_to=m.escalation_to,
        decided_at=m.decided_at,
        version=m.version,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _model_to_timeline(m: DecisionTimelineModel) -> DecisionTimeline:
    return DecisionTimeline(
        id=m.id,
        tenant_id=m.tenant_id,
        decision_id=m.decision_id,
        event_type=TimelineEventType(m.event_type),
        from_status=DecisionStatus(m.from_status) if m.from_status else None,
        to_status=DecisionStatus(m.to_status),
        actor_id=m.actor_id,
        actor_role=m.actor_role or "",
        metadata=m.metadata_ or {},
        ip_address=m.ip_address,
        created_at=m.created_at,
    )


# ============================================================
# REPOSITORY IMPLEMENTATIONS
# ============================================================

class DecisionRepository(IDecisionRepository):
    """SQLAlchemy implementation of IDecisionRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, decision_id: uuid.UUID) -> Optional[Decision]:
        query = select(DecisionModel).where(
            DecisionModel.id == decision_id,
            DecisionModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return _model_to_decision(model) if model else None

    async def get_by_id_with_tenant(self, decision_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Decision]:
        query = select(DecisionModel).where(
            DecisionModel.id == decision_id,
            DecisionModel.tenant_id == tenant_id,
            DecisionModel.deleted_at.is_(None)
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return _model_to_decision(model) if model else None

    async def list(self, tenant_id: uuid.UUID, filters: DecisionFilter, pagination: Pagination) -> List[Decision]:
        query = select(DecisionModel).where(
            DecisionModel.tenant_id == tenant_id,
            DecisionModel.deleted_at.is_(None)
        )
        if filters.status:
            query = query.where(DecisionModel.status == filters.status.value)
        if filters.decision_type:
            query = query.where(DecisionModel.decision_type == filters.decision_type.value)
        if filters.category:
            query = query.where(DecisionModel.category == filters.category.value)
        if filters.scope_type:
            query = query.where(DecisionModel.scope_type == filters.scope_type.value)
        if filters.scope_id:
            query = query.where(DecisionModel.scope_id == filters.scope_id)
        if filters.department_id:
            query = query.where(DecisionModel.department_ids.op("@>")(f'["{filters.department_id}"]'))
        if filters.proposed_by:
            query = query.where(DecisionModel.proposed_by == filters.proposed_by)
        if filters.search_query:
            search = f"%{filters.search_query}%"
            query = query.where(or_(
                DecisionModel.title.ilike(search),
                DecisionModel.description.ilike(search)
            ))
        query = query.order_by(DecisionModel.created_at.desc())
        query = query.offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(query)
        return [_model_to_decision(m) for m in result.scalars().all()]

    async def count(self, tenant_id: uuid.UUID, filters: DecisionFilter) -> int:
        query = select(func.count()).select_from(DecisionModel).where(
            DecisionModel.tenant_id == tenant_id,
            DecisionModel.deleted_at.is_(None)
        )
        if filters.status:
            query = query.where(DecisionModel.status == filters.status.value)
        if filters.decision_type:
            query = query.where(DecisionModel.decision_type == filters.decision_type.value)
        if filters.category:
            query = query.where(DecisionModel.category == filters.category.value)
        result = await self._session.execute(query)
        return result.scalar() or 0

    async def create(self, decision: Decision) -> Decision:
        model = DecisionModel(**_decision_to_model(decision))
        self._session.add(model)
        await self._session.flush()
        return _model_to_decision(model)

    async def update(self, decision: Decision) -> Decision:
        query = select(DecisionModel).where(DecisionModel.id == decision.id)
        result = await self._session.execute(query)
        model = result.scalar_one()
        data = _decision_to_model(decision)
        data.pop("id", None)
        for key, value in data.items():
            setattr(model, key, value)
        await self._session.flush()
        return _model_to_decision(model)

    async def soft_delete(self, decision_id: uuid.UUID, deleted_by: uuid.UUID) -> bool:
        query = select(DecisionModel).where(DecisionModel.id == decision_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        if not model:
            return False
        model.deleted_at = datetime.utcnow()
        model.deleted_by = deleted_by
        model.updated_at = datetime.utcnow()
        model.updated_by = deleted_by
        await self._session.flush()
        return True

    async def get_by_status(self, tenant_id: uuid.UUID, status: DecisionStatus, pagination: Pagination) -> List[Decision]:
        query = select(DecisionModel).where(
            DecisionModel.tenant_id == tenant_id,
            DecisionModel.status == status.value,
            DecisionModel.deleted_at.is_(None)
        ).order_by(DecisionModel.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(query)
        return [_model_to_decision(m) for m in result.scalars().all()]

    async def get_by_trigger(self, tenant_id: uuid.UUID, trigger_id: uuid.UUID) -> List[Decision]:
        query = select(DecisionModel).where(
            DecisionModel.tenant_id == tenant_id,
            DecisionModel.trigger_id == trigger_id,
            DecisionModel.deleted_at.is_(None)
        ).order_by(DecisionModel.created_at.desc())
        result = await self._session.execute(query)
        return [_model_to_decision(m) for m in result.scalars().all()]

    async def search(self, tenant_id: uuid.UUID, query_str: str, filters: DecisionFilter, pagination: Pagination) -> List[Decision]:
        filters = DecisionFilter(**{**filters.__dict__, "search_query": query_str})
        return await self.list(tenant_id, filters, pagination)


class DecisionEvidenceRepository(IDecisionEvidenceRepository):
    """SQLAlchemy implementation of IDecisionEvidenceRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, evidence_id: uuid.UUID) -> Optional[DecisionEvidence]:
        query = select(DecisionEvidenceModel).where(DecisionEvidenceModel.id == evidence_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return _model_to_evidence(model) if model else None

    async def get_by_decision(self, decision_id: uuid.UUID) -> List[DecisionEvidence]:
        query = select(DecisionEvidenceModel).where(
            DecisionEvidenceModel.decision_id == decision_id
        ).order_by(DecisionEvidenceModel.created_at.desc())
        result = await self._session.execute(query)
        return [_model_to_evidence(m) for m in result.scalars().all()]

    async def create(self, evidence: DecisionEvidence) -> DecisionEvidence:
        model = DecisionEvidenceModel(
            id=evidence.id,
            tenant_id=evidence.tenant_id,
            decision_id=evidence.decision_id,
            evidence_type=evidence.evidence_type.value,
            title=evidence.title,
            description=evidence.description,
            weight=evidence.weight,
            source_type=evidence.source_type.value,
            source_id=evidence.source_id,
            source_metric_code=evidence.source_metric_code,
            data_payload=evidence.data_payload,
            created_at=evidence.created_at,
            created_by=evidence.created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return _model_to_evidence(model)

    async def delete(self, evidence_id: uuid.UUID) -> bool:
        query = select(DecisionEvidenceModel).where(DecisionEvidenceModel.id == evidence_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True


class DecisionOutcomeRepository(IDecisionOutcomeRepository):
    """SQLAlchemy implementation of IDecisionOutcomeRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, outcome_id: uuid.UUID) -> Optional[DecisionOutcome]:
        query = select(DecisionOutcomeModel).where(DecisionOutcomeModel.id == outcome_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return _model_to_outcome(model) if model else None

    async def get_by_decision(self, decision_id: uuid.UUID) -> Optional[DecisionOutcome]:
        query = select(DecisionOutcomeModel).where(DecisionOutcomeModel.decision_id == decision_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return _model_to_outcome(model) if model else None

    async def create(self, outcome: DecisionOutcome) -> DecisionOutcome:
        model = DecisionOutcomeModel(
            id=outcome.id,
            tenant_id=outcome.tenant_id,
            decision_id=outcome.decision_id,
            measurement_start=outcome.measurement_start,
            measurement_end=outcome.measurement_end,
            expected_metrics=[],
            actual_metrics=[],
            accuracy_score=outcome.accuracy_score,
            variance_absolute=outcome.variance_absolute,
            variance_percent=outcome.variance_percent,
            outcome_status=outcome.outcome_status.value,
            realized_value=outcome.realized_value,
            roi_actual=outcome.roi_actual,
            measured_by=outcome.measured_by,
            measured_at=outcome.measured_at,
            version=outcome.version,
            created_at=outcome.created_at,
            updated_at=outcome.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _model_to_outcome(model)

    async def update(self, outcome: DecisionOutcome) -> DecisionOutcome:
        query = select(DecisionOutcomeModel).where(DecisionOutcomeModel.id == outcome.id)
        result = await self._session.execute(query)
        model = result.scalar_one()
        model.accuracy_score = outcome.accuracy_score
        model.variance_absolute = outcome.variance_absolute
        model.variance_percent = outcome.variance_percent
        model.outcome_status = outcome.outcome_status.value
        model.realized_value = outcome.realized_value
        model.roi_actual = outcome.roi_actual
        model.measured_by = outcome.measured_by
        model.measured_at = outcome.measured_at
        model.version = outcome.version
        model.updated_at = datetime.utcnow()
        await self._session.flush()
        return _model_to_outcome(model)


class DecisionReviewRepository(IDecisionReviewRepository):
    """SQLAlchemy implementation of IDecisionReviewRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, review_id: uuid.UUID) -> Optional[DecisionReview]:
        query = select(DecisionReviewModel).where(DecisionReviewModel.id == review_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return _model_to_review(model) if model else None

    async def get_by_decision(self, decision_id: uuid.UUID) -> List[DecisionReview]:
        query = select(DecisionReviewModel).where(
            DecisionReviewModel.decision_id == decision_id
        ).order_by(DecisionReviewModel.created_at.desc())
        result = await self._session.execute(query)
        return [_model_to_review(m) for m in result.scalars().all()]

    async def create(self, review: DecisionReview) -> DecisionReview:
        model = DecisionReviewModel(
            id=review.id,
            tenant_id=review.tenant_id,
            decision_id=review.decision_id,
            review_type=review.review_type.value,
            review_round=review.review_round,
            status=review.status.value,
            reviewer_id=review.reviewer_id,
            reviewer_role=review.reviewer_role,
            review_decision=review.review_decision.value if review.review_decision else None,
            conditions=review.conditions,
            escalation_required=review.escalation_required,
            escalation_to=review.escalation_to,
            decided_at=review.decided_at,
            version=review.version,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _model_to_review(model)

    async def update(self, review: DecisionReview) -> DecisionReview:
        query = select(DecisionReviewModel).where(DecisionReviewModel.id == review.id)
        result = await self._session.execute(query)
        model = result.scalar_one()
        model.status = review.status.value
        model.review_decision = review.review_decision.value if review.review_decision else None
        model.decided_at = review.decided_at
        model.version = review.version
        model.updated_at = datetime.utcnow()
        await self._session.flush()
        return _model_to_review(model)


class DecisionTimelineRepository(IDecisionTimelineRepository):
    """SQLAlchemy implementation of IDecisionTimelineRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_decision(self, decision_id: uuid.UUID) -> List[DecisionTimeline]:
        query = select(DecisionTimelineModel).where(
            DecisionTimelineModel.decision_id == decision_id
        ).order_by(DecisionTimelineModel.created_at.desc())
        result = await self._session.execute(query)
        return [_model_to_timeline(m) for m in result.scalars().all()]

    async def create(self, entry: DecisionTimeline) -> DecisionTimeline:
        model = DecisionTimelineModel(
            id=entry.id,
            tenant_id=entry.tenant_id,
            decision_id=entry.decision_id,
            event_type=entry.event_type.value,
            from_status=entry.from_status.value if entry.from_status else None,
            to_status=entry.to_status.value,
            actor_id=entry.actor_id,
            actor_role=entry.actor_role,
            metadata_=entry.metadata,
            ip_address=entry.ip_address,
            created_at=entry.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _model_to_timeline(model)
