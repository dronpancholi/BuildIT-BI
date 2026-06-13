"""
Decision Service Implementation.
Core business logic for Decision Management.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

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
    TriggerType,
    PriorityLabel,
    UrgencyLabel,
    ScopeType,
    EvidenceType,
    SourceType,
    ReviewType,
    ReviewStatus,
    ReviewDecision,
    TimelineEventType,
    OutcomeStatus,
)
from app.domain.decision.repositories import (
    IDecisionRepository,
    IDecisionEvidenceRepository,
    IDecisionOutcomeRepository,
    IDecisionReviewRepository,
    IDecisionTimelineRepository,
    Pagination,
    DecisionFilter,
)
from app.domain.decision.services import (
    IDecisionService,
    ProposeDecisionCommand,
    ApproveCommand,
    EvidenceInput,
    DecisionContext,
    DecisionSummary,
    DecisionValueSummary,
)


class DecisionService(IDecisionService):
    """Concrete implementation of the Decision Management service."""

    def __init__(
        self,
        decision_repo: IDecisionRepository,
        evidence_repo: IDecisionEvidenceRepository,
        outcome_repo: IDecisionOutcomeRepository,
        review_repo: IDecisionReviewRepository,
        timeline_repo: IDecisionTimelineRepository,
    ):
        self._decisions = decision_repo
        self._evidence = evidence_repo
        self._outcomes = outcome_repo
        self._reviews = review_repo
        self._timeline = timeline_repo

    async def propose_decision(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID,
        command: ProposeDecisionCommand
    ) -> Decision:
        decision = Decision(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            title=command.title,
            description=command.description,
            decision_type=command.decision_type,
            status=DecisionStatus.PROPOSED,
            priority=command.priority,
            urgency=command.urgency,
            trigger_type=command.trigger_type,
            trigger_id=command.trigger_id,
            trigger_summary=command.trigger_summary,
            category=command.category,
            department_ids=command.department_ids or [],
            scope_type=command.scope_type,
            scope_id=command.scope_id,
            estimated_value=command.estimated_value,
            estimated_cost=command.estimated_cost,
            review_deadline=command.review_deadline,
            approval_deadline=command.approval_deadline,
            implementation_target_date=(
                command.implementation_target_date.date()
                if command.implementation_target_date else None
            ),
            tags=command.tags or [],
            metadata=command.metadata or {},
            proposed_by=user_id,
            proposed_at=datetime.utcnow(),
            created_by=user_id,
        )
        decision = await self._decisions.create(decision)

        await self._add_timeline(
            decision, TimelineEventType.CREATED,
            actor_id=user_id,
        )
        return decision

    async def submit_for_review(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Decision:
        decision = await self._get_and_validate(decision_id, tenant_id)
        from_status = decision.status
        decision.submit_for_review(user_id)
        decision = await self._decisions.update(decision)

        await self._add_timeline(
            decision, TimelineEventType.SUBMITTED_FOR_REVIEW,
            from_status=from_status, actor_id=user_id,
        )

        review = DecisionReview(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision_id,
            review_type=ReviewType.INITIAL_REVIEW,
            status=ReviewStatus.PENDING,
        )
        await self._reviews.create(review)
        return decision

    async def approve(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        reviewer_id: uuid.UUID, command: ApproveCommand
    ) -> Decision:
        decision = await self._get_and_validate(decision_id, tenant_id)
        from_status = decision.status
        decision.approve(reviewer_id)
        decision = await self._decisions.update(decision)

        await self._add_timeline(
            decision, TimelineEventType.APPROVED,
            from_status=from_status, actor_id=reviewer_id,
        )

        reviews = await self._reviews.get_by_decision(decision_id)
        pending = [r for r in reviews if r.status == ReviewStatus.PENDING]
        if pending:
            pending[0].status = ReviewStatus.APPROVED
            pending[0].review_decision = ReviewDecision.APPROVE
            pending[0].reviewer_id = reviewer_id
            pending[0].decided_at = datetime.utcnow()
            pending[0].version += 1
            await self._reviews.update(pending[0])

        return decision

    async def reject(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        reviewer_id: uuid.UUID, reason: str
    ) -> Decision:
        decision = await self._get_and_validate(decision_id, tenant_id)
        from_status = decision.status
        decision.reject(reviewer_id, reason)
        decision = await self._decisions.update(decision)

        await self._add_timeline(
            decision, TimelineEventType.REJECTED,
            from_status=from_status, actor_id=reviewer_id,
            metadata={"reason": reason},
        )

        reviews = await self._reviews.get_by_decision(decision_id)
        pending = [r for r in reviews if r.status == ReviewStatus.PENDING]
        if pending:
            pending[0].status = ReviewStatus.REJECTED
            pending[0].review_decision = ReviewDecision.REJECT
            pending[0].reviewer_id = reviewer_id
            pending[0].decided_at = datetime.utcnow()
            pending[0].version += 1
            await self._reviews.update(pending[0])

        return decision

    async def start_implementation(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Decision:
        decision = await self._get_and_validate(decision_id, tenant_id)
        from_status = decision.status
        decision.start_implementation(user_id)
        decision = await self._decisions.update(decision)

        await self._add_timeline(
            decision, TimelineEventType.IMPLEMENTATION_STARTED,
            from_status=from_status, actor_id=user_id,
        )
        return decision

    async def complete_implementation(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Decision:
        decision = await self._get_and_validate(decision_id, tenant_id)
        from_status = decision.status
        decision.complete_implementation(user_id)
        decision = await self._decisions.update(decision)

        await self._add_timeline(
            decision, TimelineEventType.IMPLEMENTATION_COMPLETED,
            from_status=from_status, actor_id=user_id,
        )
        return decision

    async def archive_decision(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Decision:
        decision = await self._get_and_validate(decision_id, tenant_id)
        from_status = decision.status
        decision.archive(user_id)
        decision = await self._decisions.update(decision)

        await self._add_timeline(
            decision, TimelineEventType.ARCHIVED,
            from_status=from_status, actor_id=user_id,
        )
        return decision

    async def attach_evidence(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID,
        user_id: uuid.UUID, evidence: EvidenceInput
    ) -> DecisionEvidence:
        await self._get_and_validate(decision_id, tenant_id)

        record = DecisionEvidence(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision_id,
            evidence_type=evidence.evidence_type,
            title=evidence.title,
            description=evidence.description,
            weight=evidence.weight,
            source_type=evidence.source_type,
            source_id=evidence.source_id,
            source_metric_code=evidence.source_metric_code,
            data_payload=evidence.data_payload or {},
            created_by=user_id,
        )
        record = await self._evidence.create(record)

        await self._add_timeline(
            await self._decisions.get_by_id(decision_id),
            TimelineEventType.EVIDENCE_ADDED,
            actor_id=user_id,
            metadata={"evidence_id": str(record.id), "evidence_title": evidence.title},
        )
        return record

    async def get_decision_with_context(
        self, decision_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> DecisionContext:
        decision = await self._get_and_validate(decision_id, tenant_id)
        evidence = await self._evidence.get_by_decision(decision_id)
        timeline = await self._timeline.get_by_decision(decision_id)
        outcome = await self._outcomes.get_by_decision(decision_id)
        reviews = await self._reviews.get_by_decision(decision_id)

        return DecisionContext(
            decision=decision,
            evidence=evidence,
            timeline=[t.to_dict() for t in timeline],
            outcome=outcome,
            reviews=reviews,
        )

    async def get_decisions_requiring_review(
        self, tenant_id: uuid.UUID
    ) -> List[DecisionSummary]:
        decisions = await self._decisions.get_by_status(
            tenant_id, DecisionStatus.REVIEWING,
            Pagination(offset=0, limit=100)
        )
        summaries = []
        for d in decisions:
            evidence = await self._evidence.get_by_decision(d.id)
            summaries.append(DecisionSummary(
                id=d.id,
                title=d.title,
                decision_type=d.decision_type,
                status=d.status,
                priority=d.priority,
                category=d.category,
                estimated_value=d.estimated_value,
                proposed_by=d.proposed_by,
                created_at=d.created_at,
                evidence_count=len(evidence),
            ))
        return summaries

    async def calculate_decision_value(
        self, decision_id: uuid.UUID
    ) -> DecisionValueSummary:
        decision = await self._decisions.get_by_id(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")

        outcome = await self._outcomes.get_by_decision(decision_id)
        realized = outcome.realized_value if outcome else None
        roi_actual = outcome.roi_actual if outcome else None

        roi_expected = None
        if decision.estimated_value and decision.estimated_cost and decision.estimated_cost > 0:
            roi_expected = ((decision.estimated_value - decision.estimated_cost) / decision.estimated_cost) * 100

        variance = None
        if realized is not None and decision.estimated_value is not None:
            variance = realized - decision.estimated_value

        return DecisionValueSummary(
            decision_id=decision_id,
            estimated_value=decision.estimated_value,
            estimated_cost=decision.estimated_cost,
            realized_value=realized,
            roi_expected=roi_expected,
            roi_actual=roi_actual,
            variance=variance,
        )

    async def _get_and_validate(self, decision_id: uuid.UUID, tenant_id: uuid.UUID) -> Decision:
        decision = await self._decisions.get_by_id_with_tenant(decision_id, tenant_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found for tenant {tenant_id}")
        return decision

    async def _add_timeline(
        self,
        decision: Decision,
        event_type: TimelineEventType,
        actor_id: Optional[uuid.UUID] = None,
        from_status: Optional[DecisionStatus] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DecisionTimeline:
        entry = DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=decision.tenant_id,
            decision_id=decision.id,
            event_type=event_type,
            from_status=from_status,
            to_status=decision.status,
            actor_id=actor_id,
            metadata=metadata or {},
        )
        return await self._timeline.create(entry)
