"""
Comprehensive test suite for Decision Domain.
Tests all decision entities, value objects, services, and lifecycle.
"""
import uuid
import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, AsyncMock, patch, MagicMock

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


@pytest.fixture
def tenant_id():
    return uuid.uuid4()

@pytest.fixture
def user_id():
    return uuid.uuid4()

@pytest.fixture
def decision_id():
    return uuid.uuid4()

@pytest.fixture
def sample_decision(tenant_id, user_id, decision_id):
    return Decision(
        id=decision_id,
        tenant_id=tenant_id,
        title="Test Decision",
        description="A test decision for unit testing",
        decision_type=DecisionType.STRATEGIC,
        status=DecisionStatus.PROPOSED,
        priority=PriorityLabel.P1,
        urgency=UrgencyLabel.IMMEDIATE,
        category=DecisionCategory.REVENUE,
        estimated_value=50000.0,
        proposed_by=user_id,
        created_by=user_id,
    )


class TestDecisionEntity:
    def test_create_decision(self, sample_decision, tenant_id, user_id):
        assert sample_decision.id is not None
        assert sample_decision.tenant_id == tenant_id
        assert sample_decision.title == "Test Decision"
        assert sample_decision.decision_type == DecisionType.STRATEGIC
        assert sample_decision.status == DecisionStatus.PROPOSED
        assert sample_decision.priority == PriorityLabel.P1
        assert sample_decision.estimated_value == 50000.0
        assert sample_decision.proposed_by == user_id
        assert sample_decision.version == 1

    def test_decision_submit_for_review(self, sample_decision, user_id):
        sample_decision.submit_for_review(user_id)
        assert sample_decision.status == DecisionStatus.REVIEWING
        assert sample_decision.version == 2
        assert sample_decision.updated_by == user_id

    def test_decision_submit_for_review_wrong_status(self, sample_decision, user_id):
        sample_decision.status = DecisionStatus.APPROVED
        with pytest.raises(ValueError, match="Cannot submit decision in approved status"):
            sample_decision.submit_for_review(user_id)

    def test_decision_approve(self, sample_decision, user_id):
        reviewer = uuid.uuid4()
        sample_decision.submit_for_review(user_id)
        sample_decision.approve(reviewer)
        assert sample_decision.status == DecisionStatus.APPROVED
        assert reviewer in sample_decision.approved_by
        assert sample_decision.version == 3

    def test_decision_approve_wrong_status(self, sample_decision, user_id):
        with pytest.raises(ValueError, match="Cannot approve decision in proposed status"):
            sample_decision.approve(user_id)

    def test_decision_reject(self, sample_decision, user_id):
        reviewer = uuid.uuid4()
        sample_decision.submit_for_review(user_id)
        sample_decision.reject(reviewer, "Not aligned with strategy")
        assert sample_decision.status == DecisionStatus.REJECTED
        assert sample_decision.rejected_by == reviewer
        assert sample_decision.rejection_reason == "Not aligned with strategy"

    def test_decision_reject_wrong_status(self, sample_decision, user_id):
        with pytest.raises(ValueError, match="Cannot reject decision in proposed status"):
            sample_decision.reject(user_id, "reason")

    def test_decision_start_implementation(self, sample_decision, user_id):
        sample_decision.submit_for_review(user_id)
        sample_decision.approve(user_id)
        sample_decision.start_implementation(user_id)
        assert sample_decision.status == DecisionStatus.IN_PROGRESS
        assert sample_decision.implemented_by == user_id

    def test_decision_start_implementation_wrong_status(self, sample_decision, user_id):
        with pytest.raises(ValueError, match="Cannot start implementation in proposed status"):
            sample_decision.start_implementation(user_id)

    def test_decision_complete_implementation(self, sample_decision, user_id):
        sample_decision.submit_for_review(user_id)
        sample_decision.approve(user_id)
        sample_decision.start_implementation(user_id)
        sample_decision.complete_implementation(user_id)
        assert sample_decision.status == DecisionStatus.COMPLETED
        assert sample_decision.completion_date is not None

    def test_decision_complete_implementation_wrong_status(self, sample_decision, user_id):
        with pytest.raises(ValueError, match="Cannot complete implementation in proposed status"):
            sample_decision.complete_implementation(user_id)

    def test_decision_measure(self, sample_decision, user_id):
        sample_decision.submit_for_review(user_id)
        sample_decision.approve(user_id)
        sample_decision.start_implementation(user_id)
        sample_decision.complete_implementation(user_id)
        sample_decision.measure(user_id)
        assert sample_decision.status == DecisionStatus.MEASURED

    def test_decision_measure_wrong_status(self, sample_decision, user_id):
        with pytest.raises(ValueError, match="Cannot measure decision in proposed status"):
            sample_decision.measure(user_id)

    def test_decision_archive(self, sample_decision, user_id):
        sample_decision.archive(user_id)
        assert sample_decision.status == DecisionStatus.ARCHIVED

    def test_decision_soft_delete(self, sample_decision, user_id):
        sample_decision.soft_delete(user_id)
        assert sample_decision.deleted_at is not None
        assert sample_decision.deleted_by == user_id

    def test_decision_to_dict(self, sample_decision):
        d = sample_decision.to_dict()
        assert d["title"] == "Test Decision"
        assert d["decision_type"] == "strategic"
        assert d["status"] == "proposed"
        assert d["priority"] == "P1"
        assert d["estimated_value"] == 50000.0

    def test_decision_full_lifecycle(self, sample_decision, user_id):
        reviewer = uuid.uuid4()
        sample_decision.submit_for_review(user_id)
        sample_decision.approve(reviewer)
        sample_decision.start_implementation(user_id)
        sample_decision.complete_implementation(user_id)
        sample_decision.measure(user_id)
        sample_decision.archive(user_id)
        assert sample_decision.status == DecisionStatus.ARCHIVED
        assert sample_decision.version == 7


class TestDecisionEvidence:
    def test_create_evidence(self, tenant_id, decision_id, user_id):
        evidence = DecisionEvidence(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision_id,
            evidence_type=EvidenceType.HISTORICAL_TREND,
            title="Revenue Trend",
            description="Revenue increased 15% over last quarter",
            weight=0.85,
            source_type=SourceType.USER_INPUT,
            created_by=user_id,
        )
        assert evidence.evidence_type == EvidenceType.HISTORICAL_TREND
        assert evidence.weight == 0.85
        assert evidence.source_type == SourceType.USER_INPUT

    def test_evidence_to_dict(self, tenant_id, decision_id):
        evidence = DecisionEvidence(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision_id,
            evidence_type=EvidenceType.BENCHMARK,
            title="Market Report",
            description="Q4 market analysis",
            weight=0.7,
        )
        d = evidence.to_dict()
        assert d["evidence_type"] == "benchmark"
        assert d["weight"] == 0.7


class TestDecisionOutcome:
    def test_create_outcome(self, tenant_id, decision_id):
        outcome = DecisionOutcome(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision_id,
            accuracy_score=0.85,
            variance_absolute=2500.0,
            variance_percent=5.0,
            outcome_status=OutcomeStatus.AHEAD,
            realized_value=47500.0,
            roi_actual=0.95,
        )
        assert outcome.accuracy_score == 0.85
        assert outcome.outcome_status == OutcomeStatus.AHEAD
        assert outcome.realized_value == 47500.0
        assert outcome.roi_actual == 0.95

    def test_outcome_to_dict(self, tenant_id, decision_id):
        outcome = DecisionOutcome(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision_id,
            accuracy_score=0.9,
            realized_value=50000.0,
        )
        d = outcome.to_dict()
        assert d["accuracy_score"] == 0.9
        assert d["realized_value"] == 50000.0


class TestDecisionReview:
    def test_create_review(self, tenant_id, decision_id, user_id):
        review = DecisionReview(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision_id,
            review_type=ReviewType.INITIAL_REVIEW,
            review_round=1,
            status=ReviewStatus.PENDING,
            reviewer_id=user_id,
            reviewer_role="ceo",
        )
        assert review.review_type == ReviewType.INITIAL_REVIEW
        assert review.status == ReviewStatus.PENDING
        assert review.reviewer_role == "ceo"

    def test_review_to_dict(self, tenant_id, decision_id):
        review = DecisionReview(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision_id,
            status=ReviewStatus.APPROVED,
        )
        d = review.to_dict()
        assert d["status"] == "approved"


class TestDecisionTimeline:
    def test_create_timeline_event(self, tenant_id, decision_id, user_id):
        event = DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision_id,
            event_type=TimelineEventType.SUBMITTED_FOR_REVIEW,
            from_status=DecisionStatus.PROPOSED,
            to_status=DecisionStatus.REVIEWING,
            actor_id=user_id,
            metadata={"notes": "Submitted for review"},
        )
        assert event.event_type == TimelineEventType.SUBMITTED_FOR_REVIEW
        assert event.from_status == DecisionStatus.PROPOSED
        assert event.to_status == DecisionStatus.REVIEWING

    def test_timeline_to_dict(self, tenant_id, decision_id):
        event = DecisionTimeline(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            decision_id=decision_id,
            event_type=TimelineEventType.EVIDENCE_ADDED,
            to_status=DecisionStatus.PROPOSED,
        )
        d = event.to_dict()
        assert d["event_type"] == "evidence_added"


class TestDecisionValueObjects:
    def test_decision_status_values(self):
        statuses = list(DecisionStatus)
        assert DecisionStatus.PROPOSED in statuses
        assert DecisionStatus.REVIEWING in statuses
        assert DecisionStatus.APPROVED in statuses
        assert DecisionStatus.REJECTED in statuses
        assert DecisionStatus.IN_PROGRESS in statuses
        assert DecisionStatus.COMPLETED in statuses
        assert DecisionStatus.MEASURED in statuses
        assert DecisionStatus.ARCHIVED in statuses

    def test_decision_type_values(self):
        types = list(DecisionType)
        assert DecisionType.STRATEGIC in types
        assert DecisionType.EXPANSION in types
        assert DecisionType.COST_REDUCTION in types
        assert DecisionType.PROCESS_CHANGE in types

    def test_priority_label_values(self):
        priorities = list(PriorityLabel)
        assert PriorityLabel.P0 in priorities
        assert PriorityLabel.P1 in priorities
        assert PriorityLabel.P2 in priorities
        assert PriorityLabel.P3 in priorities

    def test_urgency_label_values(self):
        urgencies = list(UrgencyLabel)
        assert UrgencyLabel.IMMEDIATE in urgencies
        assert UrgencyLabel.SOON in urgencies
        assert UrgencyLabel.SCHEDULED in urgencies
        assert UrgencyLabel.BACKLOG in urgencies

    def test_timeline_event_type_values(self):
        event_types = list(TimelineEventType)
        assert TimelineEventType.SUBMITTED_FOR_REVIEW in event_types
        assert TimelineEventType.EVIDENCE_ADDED in event_types
        assert TimelineEventType.OUTCOME_MEASURED in event_types
        assert TimelineEventType.ARCHIVED in event_types

    def test_evidence_type_values(self):
        evidence_types = list(EvidenceType)
        assert EvidenceType.HISTORICAL_TREND in evidence_types
        assert EvidenceType.BENCHMARK in evidence_types
        assert EvidenceType.REGULATORY in evidence_types

    def test_outcome_status_values(self):
        statuses = list(OutcomeStatus)
        assert OutcomeStatus.ON_TRACK in statuses
        assert OutcomeStatus.AHEAD in statuses
        assert OutcomeStatus.BEHIND in statuses
        assert OutcomeStatus.FAILED in statuses


class TestDecisionCommands:
    def test_propose_command(self):
        cmd = ProposeDecisionCommand(
            title="Test Decision",
            description="Test description",
            decision_type=DecisionType.STRATEGIC,
            category=DecisionCategory.REVENUE,
            priority=PriorityLabel.P1,
            urgency=UrgencyLabel.IMMEDIATE,
            estimated_value=100000.0,
        )
        assert cmd.title == "Test Decision"
        assert cmd.decision_type == DecisionType.STRATEGIC
        assert cmd.estimated_value == 100000.0

    def test_approve_command(self):
        cmd = ApproveCommand(
            review_decision=ReviewDecision.APPROVE,
            comments="Looks good",
        )
        assert cmd.review_decision == ReviewDecision.APPROVE
        assert cmd.comments == "Looks good"

    def test_evidence_input(self):
        inp = EvidenceInput(
            evidence_type=EvidenceType.HISTORICAL_TREND,
            title="Revenue Analysis",
            description="15% increase",
            weight=0.8,
        )
        assert inp.evidence_type == EvidenceType.HISTORICAL_TREND
        assert inp.weight == 0.8

    def test_decision_context(self, tenant_id, user_id):
        decision = Decision(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            title="Context Test",
            description="Test",
            decision_type=DecisionType.STRATEGIC,
            created_by=user_id,
        )
        ctx = DecisionContext(
            decision=decision,
            evidence=[],
            timeline=[],
            outcome=None,
            reviews=[],
        )
        assert ctx.decision.id is not None

    def test_decision_summary(self):
        summary = DecisionSummary(
            id=uuid.uuid4(),
            title="Test",
            decision_type=DecisionType.STRATEGIC,
            status=DecisionStatus.PROPOSED,
            priority=PriorityLabel.P1,
            category=DecisionCategory.REVENUE,
            estimated_value=10000.0,
            proposed_by=uuid.uuid4(),
            created_at=datetime.utcnow(),
        )
        assert summary.title == "Test"
        assert summary.estimated_value == 10000.0

    def test_decision_value_summary(self):
        vs = DecisionValueSummary(
            decision_id=uuid.uuid4(),
            estimated_value=100000.0,
            estimated_cost=50000.0,
            realized_value=None,
            roi_expected=2.0,
            roi_actual=None,
            variance=None,
        )
        assert vs.estimated_value == 100000.0
        assert vs.roi_expected == 2.0
