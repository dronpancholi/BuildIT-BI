"""
End-to-end test for the complete Decision Lifecycle.
Tests the full flow: Propose → Submit → Review → Approve → Implement → Complete → Measure
"""
import uuid
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock

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
    Currency,
    EvidenceType,
    SourceType,
    ReviewType,
    ReviewStatus,
    ReviewDecision,
    TimelineEventType,
    OutcomeStatus,
)
from app.domain.decision.services import (
    ProposeDecisionCommand,
    ApproveCommand,
    EvidenceInput,
    DecisionContext,
    DecisionSummary,
    DecisionValueSummary,
)


class TestDecisionLifecycleE2E:
    def test_full_decision_lifecycle(self):
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        reviewer_id = uuid.uuid4()
        implementer_id = uuid.uuid4()

        # 1. PROPOSE
        decision = Decision(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            title="Implement New Revenue Cycle Management System",
            description="Replace legacy RCM system with AI-powered solution to improve claim processing efficiency",
            decision_type=DecisionType.STRATEGIC,
            status=DecisionStatus.PROPOSED,
            priority=PriorityLabel.P0,
            urgency=UrgencyLabel.IMMEDIATE,
            category=DecisionCategory.REVENUE,
            estimated_value=500000.0,
            estimated_cost=150000.0,
            currency=Currency.INR,
            trigger_type=TriggerType.ANOMALY,
            trigger_summary="High claim denial rate detected",
            proposed_by=user_id,
            created_by=user_id,
        )
        assert decision.status == DecisionStatus.PROPOSED
        assert decision.version == 1

        # 2. ATTACH EVIDENCE
        evidence1 = DecisionEvidence(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            evidence_type=EvidenceType.HISTORICAL_TREND,
            title="Claim Denial Rate Trend",
            description="Claim denial rate increased from 8% to 15% over last 3 months",
            weight=0.9,
            source_type=SourceType.USER_INPUT,
            created_by=user_id,
        )
        evidence2 = DecisionEvidence(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            evidence_type=EvidenceType.BENCHMARK,
            title="Industry Benchmark",
            description="Industry average denial rate is 5%, we are 3x above",
            weight=0.75,
            source_type=SourceType.EXTERNAL_API,
            created_by=user_id,
        )
        assert evidence1.weight == 0.9
        assert evidence2.evidence_type == EvidenceType.BENCHMARK

        # 3. CREATE TIMELINE EVENTS
        timeline_events = []
        timeline_events.append(DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            event_type=TimelineEventType.CREATED,
            from_status=None,
            to_status=DecisionStatus.PROPOSED,
            actor_id=user_id,
            metadata={"notes": "Decision proposed"},
        ))

        # 4. SUBMIT FOR REVIEW
        decision.submit_for_review(user_id)
        assert decision.status == DecisionStatus.REVIEWING
        assert decision.version == 2
        timeline_events.append(DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            event_type=TimelineEventType.SUBMITTED_FOR_REVIEW,
            from_status=DecisionStatus.PROPOSED,
            to_status=DecisionStatus.REVIEWING,
            actor_id=user_id,
            metadata={"notes": "Submitted for review"},
        ))

        # 5. REVIEW
        review = DecisionReview(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            review_type=ReviewType.INITIAL_REVIEW,
            review_round=1,
            status=ReviewStatus.APPROVED,
            reviewer_id=reviewer_id,
            reviewer_role="ceo",
            review_decision=ReviewDecision.APPROVE,
        )
        assert review.status == ReviewStatus.APPROVED
        assert review.reviewer_role == "ceo"

        # 6. APPROVE
        decision.approve(reviewer_id)
        assert decision.status == DecisionStatus.APPROVED
        assert reviewer_id in decision.approved_by
        assert decision.version == 3
        timeline_events.append(DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            event_type=TimelineEventType.APPROVED,
            from_status=DecisionStatus.REVIEWING,
            to_status=DecisionStatus.APPROVED,
            actor_id=reviewer_id,
            metadata={"notes": "Approved by CEO"},
        ))

        # 7. START IMPLEMENTATION
        decision.start_implementation(implementer_id)
        assert decision.status == DecisionStatus.IN_PROGRESS
        assert decision.implemented_by == implementer_id
        assert decision.version == 4
        timeline_events.append(DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            event_type=TimelineEventType.IMPLEMENTATION_STARTED,
            from_status=DecisionStatus.APPROVED,
            to_status=DecisionStatus.IN_PROGRESS,
            actor_id=implementer_id,
            metadata={"notes": "Implementation started"},
        ))

        # 8. COMPLETE IMPLEMENTATION
        decision.complete_implementation(implementer_id)
        assert decision.status == DecisionStatus.COMPLETED
        assert decision.completion_date is not None
        assert decision.version == 5
        timeline_events.append(DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            event_type=TimelineEventType.IMPLEMENTATION_COMPLETED,
            from_status=DecisionStatus.IN_PROGRESS,
            to_status=DecisionStatus.COMPLETED,
            actor_id=implementer_id,
            metadata={"notes": "Implementation completed"},
        ))

        # 9. MEASURE OUTCOME
        outcome = DecisionOutcome(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            measurement_start=datetime.utcnow() - timedelta(days=90),
            measurement_end=datetime.utcnow(),
            accuracy_score=0.88,
            variance_absolute=44000.0,
            variance_percent=8.8,
            outcome_status=OutcomeStatus.AHEAD,
            realized_value=456000.0,
            roi_actual=3.04,
            measured_by=user_id,
            measured_at=datetime.utcnow(),
        )
        assert outcome.accuracy_score == 0.88
        assert outcome.realized_value == 456000.0
        assert outcome.roi_actual == 3.04

        decision.measure(user_id)
        assert decision.status == DecisionStatus.MEASURED
        assert decision.version == 6
        timeline_events.append(DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            event_type=TimelineEventType.OUTCOME_MEASURED,
            from_status=DecisionStatus.COMPLETED,
            to_status=DecisionStatus.MEASURED,
            actor_id=user_id,
            metadata={"notes": "Outcome measured: 8.8% variance, ROI 3.04x"},
        ))

        # 10. ARCHIVE
        decision.archive(user_id)
        assert decision.status == DecisionStatus.ARCHIVED
        assert decision.version == 7
        timeline_events.append(DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            event_type=TimelineEventType.ARCHIVED,
            from_status=DecisionStatus.MEASURED,
            to_status=DecisionStatus.ARCHIVED,
            actor_id=user_id,
            metadata={"notes": "Decision archived"},
        ))

        # VERIFICATION
        assert decision.status == DecisionStatus.ARCHIVED
        assert decision.version == 7
        assert len(timeline_events) == 7
        assert len(decision.approved_by) == 1

        # Value summary
        value_summary = DecisionValueSummary(
            decision_id=decision.id,
            estimated_value=500000.0,
            estimated_cost=150000.0,
            realized_value=456000.0,
            roi_expected=3.33,
            roi_actual=3.04,
            variance=-44000.0,
        )
        assert value_summary.estimated_value == 500000.0
        assert value_summary.realized_value == 456000.0
        assert value_summary.roi_actual == 3.04

    def test_decision_rejection_flow(self):
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        reviewer_id = uuid.uuid4()

        decision = Decision(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            title="Test Rejection",
            description="Should be rejected",
            decision_type=DecisionType.PROCESS_CHANGE,
            proposed_by=user_id,
        )

        decision.submit_for_review(user_id)
        decision.reject(reviewer_id, "Not aligned with Q3 strategy")
        assert decision.status == DecisionStatus.REJECTED
        assert decision.rejection_reason == "Not aligned with Q3 strategy"

        with pytest.raises(ValueError):
            decision.approve(reviewer_id)

    def test_decision_with_multiple_evidence(self):
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        decision = Decision(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            title="Evidence-Rich Decision",
            description="Decision with many evidence items",
            decision_type=DecisionType.STRATEGIC,
            proposed_by=user_id,
        )

        evidence_items = []
        for i in range(5):
            evidence_items.append(DecisionEvidence(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                decision_id=decision.id,
                evidence_type=EvidenceType.HISTORICAL_TREND,
                title=f"Evidence {i+1}",
                description=f"Supporting evidence item {i+1}",
                weight=0.5 + (i * 0.1),
            ))

        assert len(evidence_items) == 5
        total_weight = sum(e.weight for e in evidence_items)
        assert total_weight == 3.5

    def test_decision_timeline_integrity(self):
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        decision = Decision(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            title="Timeline Test",
            description="Testing timeline integrity",
            decision_type=DecisionType.EXPANSION,
            proposed_by=user_id,
        )

        events = []
        now = datetime.utcnow()

        events.append(DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            event_type=TimelineEventType.CREATED,
            from_status=None,
            to_status=DecisionStatus.PROPOSED,
            created_at=now,
        ))

        decision.submit_for_review(user_id)
        events.append(DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            event_type=TimelineEventType.SUBMITTED_FOR_REVIEW,
            from_status=DecisionStatus.PROPOSED,
            to_status=DecisionStatus.REVIEWING,
            created_at=now + timedelta(minutes=1),
        ))

        decision.approve(user_id)
        events.append(DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision.id,
            event_type=TimelineEventType.APPROVED,
            from_status=DecisionStatus.REVIEWING,
            to_status=DecisionStatus.APPROVED,
            created_at=now + timedelta(minutes=2),
        ))

        for i in range(1, len(events)):
            assert events[i].created_at >= events[i-1].created_at

    def test_decision_with_domain_context(self):
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        decision = Decision(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            title="Context Test",
            description="Testing decision context",
            decision_type=DecisionType.STRATEGIC,
            category=DecisionCategory.QUALITY,
            priority=PriorityLabel.P0,
            urgency=UrgencyLabel.IMMEDIATE,
            estimated_value=250000.0,
            estimated_cost=75000.0,
            proposed_by=user_id,
        )

        context = DecisionContext(
            decision=decision,
            evidence=[],
            timeline=[],
            outcome=None,
            reviews=[],
        )

        assert context.decision.id == decision.id
        assert context.decision.estimated_value == 250000.0

    def test_decision_soft_delete_preserves_data(self):
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        decision = Decision(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            title="Soft Delete Test",
            description="Should be soft deleted",
            decision_type=DecisionType.RESOURCE_ALLOCATION,
            estimated_value=10000.0,
            proposed_by=user_id,
            created_by=user_id,
        )

        original_data = decision.to_dict()
        decision.soft_delete(user_id)

        assert decision.title == original_data["title"]
        assert decision.estimated_value == original_data["estimated_value"]
        assert decision.deleted_at is not None
        assert decision.deleted_by == user_id
