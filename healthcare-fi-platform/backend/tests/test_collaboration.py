"""
Comprehensive test suite for Domain 6: Collaboration.
Tests comments, threading, assignments, and watchlists.
"""
import uuid
import pytest
from datetime import date, datetime, timedelta
from typing import Dict, Any

from app.domain.collaboration import (
    CommentTarget,
    AssignmentStatus,
    AssignmentPriority,
    WatchlistItemType,
    Comment,
    CommentThread,
    Assignment,
    Watchlist,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def target_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def another_user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def thread_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def parent_comment_id() -> uuid.UUID:
    return uuid.uuid4()


# ============================================================
# ENUM TESTS
# ============================================================

class TestCommentTarget:
    def test_all_values(self):
        values = [ct.value for ct in CommentTarget]
        assert "INSIGHT" in values
        assert "RECOMMENDATION" in values
        assert "ANOMALY" in values
        assert "DECISION" in values
        assert "REPORT" in values
        assert "DASHBOARD" in values

    def test_count(self):
        assert len(CommentTarget) == 6


class TestAssignmentStatus:
    def test_all_values(self):
        values = [as_.value for as_ in AssignmentStatus]
        assert "OPEN" in values
        assert "IN_PROGRESS" in values
        assert "COMPLETED" in values
        assert "DISMISSED" in values

    def test_count(self):
        assert len(AssignmentStatus) == 4


class TestAssignmentPriority:
    def test_all_values(self):
        values = [ap.value for ap in AssignmentPriority]
        assert "LOW" in values
        assert "MEDIUM" in values
        assert "HIGH" in values
        assert "CRITICAL" in values

    def test_count(self):
        assert len(AssignmentPriority) == 4


class TestWatchlistItemType:
    def test_all_values(self):
        values = [w.value for w in WatchlistItemType]
        assert "METRIC" in values
        assert "INSIGHT" in values
        assert "DEPARTMENT" in values
        assert "HOSPITAL" in values
        assert "REPORT" in values

    def test_count(self):
        assert len(WatchlistItemType) == 5


# ============================================================
# COMMENT TESTS
# ============================================================

class TestComment:
    def test_create_comment(self, user_id, target_id):
        comment = Comment(
            target_type=CommentTarget.INSIGHT,
            target_id=target_id,
            content="Revenue is trending upward in Q2.",
            created_by=user_id,
        )
        assert comment.target_type == CommentTarget.INSIGHT
        assert comment.target_id == target_id
        assert comment.content == "Revenue is trending upward in Q2."
        assert comment.created_by == user_id
        assert comment.parent_id is None
        assert comment.thread_id is None
        assert comment.is_resolved is False
        assert comment.resolved_by is None
        assert comment.resolved_at is None
        assert comment.mentions == []

    def test_default_id(self, user_id, target_id):
        c1 = Comment(
            target_type=CommentTarget.REPORT,
            target_id=target_id,
            content="First",
            created_by=user_id,
        )
        c2 = Comment(
            target_type=CommentTarget.REPORT,
            target_id=target_id,
            content="Second",
            created_by=user_id,
        )
        assert c1.id != c2.id

    def test_default_created_at(self, user_id, target_id):
        before = datetime.utcnow()
        comment = Comment(
            target_type=CommentTarget.DASHBOARD,
            target_id=target_id,
            content="Test",
            created_by=user_id,
        )
        after = datetime.utcnow()
        assert before <= comment.created_at <= after

    def test_edit(self, user_id, target_id):
        comment = Comment(
            target_type=CommentTarget.INSIGHT,
            target_id=target_id,
            content="Original content",
            created_by=user_id,
        )
        comment.edit("Updated content")
        assert comment.content == "Updated content"
        assert comment.edited_at is not None

    def test_resolve(self, user_id, another_user_id, target_id):
        comment = Comment(
            target_type=CommentTarget.ANOMALY,
            target_id=target_id,
            content="This anomaly has been investigated.",
            created_by=user_id,
        )
        comment.resolve(resolver=another_user_id)
        assert comment.is_resolved is True
        assert comment.resolved_by == another_user_id
        assert comment.resolved_at is not None

    def test_unresolve(self, user_id, another_user_id, target_id):
        comment = Comment(
            target_type=CommentTarget.ANOMALY,
            target_id=target_id,
            content="Needs further review.",
            created_by=user_id,
        )
        comment.resolve(resolver=another_user_id)
        comment.unresolve()
        assert comment.is_resolved is False
        assert comment.resolved_by is None
        assert comment.resolved_at is None

    def test_is_reply(self, user_id, target_id, parent_comment_id):
        comment = Comment(
            target_type=CommentTarget.INSIGHT,
            target_id=target_id,
            content="I agree.",
            created_by=user_id,
            parent_id=parent_comment_id,
        )
        assert comment.is_reply() is True

    def test_is_not_reply(self, user_id, target_id):
        comment = Comment(
            target_type=CommentTarget.INSIGHT,
            target_id=target_id,
            content="Root comment.",
            created_by=user_id,
        )
        assert comment.is_reply() is False

    def test_is_thread_root(self, user_id, target_id):
        comment = Comment(
            target_type=CommentTarget.REPORT,
            target_id=target_id,
            content="Starting a discussion.",
            created_by=user_id,
        )
        assert comment.is_thread_root() is True

    def test_not_thread_root_with_parent(self, user_id, target_id, parent_comment_id):
        comment = Comment(
            target_type=CommentTarget.REPORT,
            target_id=target_id,
            content="Reply.",
            created_by=user_id,
            parent_id=parent_comment_id,
        )
        assert comment.is_thread_root() is False

    def test_not_thread_root_with_thread_id(self, user_id, target_id, thread_id):
        comment = Comment(
            target_type=CommentTarget.REPORT,
            target_id=target_id,
            content="In thread.",
            created_by=user_id,
            thread_id=thread_id,
        )
        assert comment.is_thread_root() is False

    def test_add_mention(self, user_id, another_user_id, target_id):
        comment = Comment(
            target_type=CommentTarget.DECISION,
            target_id=target_id,
            content="@admin please review.",
            created_by=user_id,
        )
        comment.add_mention(another_user_id, "Admin User")
        assert len(comment.mentions) == 1
        assert comment.mentions[0]["user_id"] == str(another_user_id)
        assert comment.mentions[0]["display_name"] == "Admin User"

    def test_mentioned_user_ids(self, user_id, another_user_id, target_id):
        third_user = uuid.uuid4()
        comment = Comment(
            target_type=CommentTarget.DECISION,
            target_id=target_id,
            content="@admin @finance please review.",
            created_by=user_id,
        )
        comment.add_mention(another_user_id, "Admin")
        comment.add_mention(third_user, "Finance")
        ids = comment.mentioned_user_ids()
        assert another_user_id in ids
        assert third_user in ids

    def test_multiple_mentions(self, user_id, target_id):
        comment = Comment(
            target_type=CommentTarget.RECOMMENDATION,
            target_id=target_id,
            content="Team review needed.",
            created_by=user_id,
        )
        for i in range(5):
            comment.add_mention(uuid.uuid4(), f"User {i}")
        assert len(comment.mentions) == 5

    def test_all_target_types(self, user_id, target_id):
        for target in CommentTarget:
            comment = Comment(
                target_type=target,
                target_id=target_id,
                content=f"Comment on {target.value}",
                created_by=user_id,
            )
            assert comment.target_type == target


# ============================================================
# COMMENT THREAD TESTS
# ============================================================

class TestCommentThread:
    def test_create_thread(self, user_id, target_id):
        thread = CommentThread(
            target_type=CommentTarget.INSIGHT,
            target_id=target_id,
            title="Revenue Anomaly Discussion",
        )
        assert thread.target_type == CommentTarget.INSIGHT
        assert thread.target_id == target_id
        assert thread.title == "Revenue Anomaly Discussion"
        assert thread.is_open is True
        assert thread.participant_ids == []
        assert thread.comment_count == 0

    def test_default_values(self, user_id, target_id):
        thread = CommentThread(
            target_type=CommentTarget.REPORT,
            target_id=target_id,
        )
        assert thread.title is None
        assert thread.is_open is True
        assert thread.participant_ids == []
        assert thread.comment_count == 0

    def test_add_participant(self, user_id, target_id):
        thread = CommentThread(
            target_type=CommentTarget.ANOMALY,
            target_id=target_id,
        )
        thread.add_participant(user_id)
        assert user_id in thread.participant_ids
        assert thread.last_activity_at is not None

    def test_add_duplicate_participant(self, user_id, target_id):
        thread = CommentThread(
            target_type=CommentTarget.ANOMALY,
            target_id=target_id,
        )
        thread.add_participant(user_id)
        thread.add_participant(user_id)
        assert thread.participant_ids.count(user_id) == 1

    def test_record_comment(self, user_id, target_id):
        thread = CommentThread(
            target_type=CommentTarget.DECISION,
            target_id=target_id,
        )
        thread.record_comment(user_id)
        assert thread.comment_count == 1
        assert user_id in thread.participant_ids

    def test_record_multiple_comments(self, user_id, another_user_id, target_id):
        thread = CommentThread(
            target_type=CommentTarget.DECISION,
            target_id=target_id,
        )
        thread.record_comment(user_id)
        thread.record_comment(another_user_id)
        thread.record_comment(user_id)
        assert thread.comment_count == 3
        assert len(thread.participant_ids) == 2

    def test_close(self, user_id, target_id):
        thread = CommentThread(
            target_type=CommentTarget.INSIGHT,
            target_id=target_id,
        )
        thread.close()
        assert thread.is_open is False

    def test_reopen(self, user_id, target_id):
        thread = CommentThread(
            target_type=CommentTarget.INSIGHT,
            target_id=target_id,
        )
        thread.close()
        thread.reopen()
        assert thread.is_open is True

    def test_is_participant(self, user_id, another_user_id, target_id):
        thread = CommentThread(
            target_type=CommentTarget.REPORT,
            target_id=target_id,
        )
        thread.add_participant(user_id)
        assert thread.is_participant(user_id) is True
        assert thread.is_participant(another_user_id) is False

    def test_participant_count(self, user_id, another_user_id, target_id):
        thread = CommentThread(
            target_type=CommentTarget.REPORT,
            target_id=target_id,
        )
        assert thread.participant_count() == 0
        thread.add_participant(user_id)
        assert thread.participant_count() == 1
        thread.add_participant(another_user_id)
        assert thread.participant_count() == 2

    def test_default_id(self, target_id):
        t1 = CommentThread(target_type=CommentTarget.INSIGHT, target_id=target_id)
        t2 = CommentThread(target_type=CommentTarget.INSIGHT, target_id=target_id)
        assert t1.id != t2.id

    def test_all_target_types(self, target_id):
        for target in CommentTarget:
            thread = CommentThread(target_type=target, target_id=target_id)
            assert thread.target_type == target

    def test_last_activity_updates_on_comment(self, user_id, target_id):
        thread = CommentThread(
            target_type=CommentTarget.DASHBOARD,
            target_id=target_id,
        )
        initial_activity = thread.last_activity_at
        thread.record_comment(user_id)
        assert thread.last_activity_at >= initial_activity


# ============================================================
# ASSIGNMENT TESTS
# ============================================================

class TestAssignment:
    def test_create_assignment(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Investigate revenue drop",
            description="Revenue dropped 15% in cardiology department.",
            target_type="anomaly",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.HIGH,
            due_date=date(2026, 6, 30),
        )
        assert assignment.title == "Investigate revenue drop"
        assert assignment.description == "Revenue dropped 15% in cardiology department."
        assert assignment.target_type == "anomaly"
        assert assignment.target_id == target_id
        assert assignment.assignee_id == user_id
        assert assignment.assigned_by == another_user_id
        assert assignment.priority == AssignmentPriority.HIGH
        assert assignment.due_date == date(2026, 6, 30)
        assert assignment.status == AssignmentStatus.OPEN
        assert assignment.completed_at is None
        assert assignment.completion_note is None

    def test_default_values(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Review insight",
            description="Review the new insight.",
            target_type="insight",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.MEDIUM,
        )
        assert assignment.due_date is None
        assert assignment.status == AssignmentStatus.OPEN
        assert assignment.completed_at is None
        assert assignment.completion_note is None

    def test_start_progress(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Task",
            description="Desc",
            target_type="report",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.LOW,
        )
        assignment.start_progress()
        assert assignment.status == AssignmentStatus.IN_PROGRESS

    def test_start_progress_wrong_status_raises(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Task",
            description="Desc",
            target_type="report",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.LOW,
        )
        assignment.start_progress()
        with pytest.raises(ValueError, match="Cannot start progress on assignment in IN_PROGRESS status"):
            assignment.start_progress()

    def test_complete_from_open(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Task",
            description="Desc",
            target_type="insight",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.MEDIUM,
        )
        assignment.complete(note="Resolved the issue.")
        assert assignment.status == AssignmentStatus.COMPLETED
        assert assignment.completed_at is not None
        assert assignment.completion_note == "Resolved the issue."

    def test_complete_from_in_progress(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Task",
            description="Desc",
            target_type="anomaly",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.HIGH,
        )
        assignment.start_progress()
        assignment.complete()
        assert assignment.status == AssignmentStatus.COMPLETED
        assert assignment.completed_at is not None

    def test_complete_wrong_status_raises(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Task",
            description="Desc",
            target_type="decision",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.CRITICAL,
        )
        assignment.dismiss()
        with pytest.raises(ValueError, match="Cannot complete assignment in DISMISSED status"):
            assignment.complete()

    def test_complete_already_completed_raises(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Task",
            description="Desc",
            target_type="report",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.LOW,
        )
        assignment.complete()
        with pytest.raises(ValueError, match="Cannot complete assignment in COMPLETED status"):
            assignment.complete()

    def test_dismiss(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Task",
            description="Desc",
            target_type="insight",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.LOW,
        )
        assignment.dismiss()
        assert assignment.status == AssignmentStatus.DISMISSED

    def test_dismiss_completed_raises(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Task",
            description="Desc",
            target_type="report",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.MEDIUM,
        )
        assignment.complete()
        with pytest.raises(ValueError, match="Cannot dismiss a completed assignment"):
            assignment.dismiss()

    def test_reopen(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Task",
            description="Desc",
            target_type="anomaly",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.HIGH,
        )
        assignment.dismiss()
        assignment.reopen()
        assert assignment.status == AssignmentStatus.OPEN
        assert assignment.completed_at is None
        assert assignment.completion_note is None

    def test_reopen_wrong_status_raises(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Task",
            description="Desc",
            target_type="insight",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.MEDIUM,
        )
        with pytest.raises(ValueError, match="Can only reopen dismissed assignments"):
            assignment.reopen()

    def test_is_overdue(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Overdue Task",
            description="Should be overdue.",
            target_type="anomaly",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.HIGH,
            due_date=date(2026, 1, 1),
        )
        assert assignment.is_overdue(reference_date=date(2026, 6, 12)) is True

    def test_is_not_overdue_future(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Future Task",
            description="Not overdue.",
            target_type="report",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.LOW,
            due_date=date(2026, 12, 31),
        )
        assert assignment.is_overdue(reference_date=date(2026, 6, 12)) is False

    def test_is_not_overdue_no_due_date(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="No Due Date",
            description="No deadline.",
            target_type="decision",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.LOW,
        )
        assert assignment.is_overdue() is False

    def test_is_not_overdue_completed(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Completed Task",
            description="Done.",
            target_type="insight",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.MEDIUM,
            due_date=date(2026, 1, 1),
        )
        assignment.complete()
        assert assignment.is_overdue(reference_date=date(2026, 6, 12)) is False

    def test_is_not_overdue_dismissed(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Dismissed Task",
            description="Dismissed.",
            target_type="anomaly",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.LOW,
            due_date=date(2026, 1, 1),
        )
        assignment.dismiss()
        assert assignment.is_overdue(reference_date=date(2026, 6, 12)) is False

    def test_is_terminal(self, user_id, another_user_id, target_id):
        open_assignment = Assignment(
            title="Open",
            description="Desc",
            target_type="report",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.LOW,
        )
        assert open_assignment.is_terminal() is False

        completed = Assignment(
            title="Completed",
            description="Desc",
            target_type="report",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.LOW,
        )
        completed.complete()
        assert completed.is_terminal() is True

        dismissed = Assignment(
            title="Dismissed",
            description="Desc",
            target_type="report",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.LOW,
        )
        dismissed.dismiss()
        assert dismissed.is_terminal() is True

    def test_reassign(self, user_id, another_user_id, target_id):
        new_assignee = uuid.uuid4()
        assignment = Assignment(
            title="Task",
            description="Desc",
            target_type="insight",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.MEDIUM,
        )
        assignment.reassign(new_assignee)
        assert assignment.assignee_id == new_assignee

    def test_change_priority(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Task",
            description="Desc",
            target_type="anomaly",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.LOW,
        )
        assignment.change_priority(AssignmentPriority.CRITICAL)
        assert assignment.priority == AssignmentPriority.CRITICAL

    def test_default_id(self, user_id, another_user_id, target_id):
        a1 = Assignment(
            title="T1", description="D1", target_type="report",
            target_id=target_id, assignee_id=user_id,
            assigned_by=another_user_id, priority=AssignmentPriority.LOW,
        )
        a2 = Assignment(
            title="T2", description="D2", target_type="report",
            target_id=target_id, assignee_id=user_id,
            assigned_by=another_user_id, priority=AssignmentPriority.LOW,
        )
        assert a1.id != a2.id

    def test_default_created_at(self, user_id, another_user_id, target_id):
        before = datetime.utcnow()
        assignment = Assignment(
            title="Task", description="Desc", target_type="insight",
            target_id=target_id, assignee_id=user_id,
            assigned_by=another_user_id, priority=AssignmentPriority.MEDIUM,
        )
        after = datetime.utcnow()
        assert before <= assignment.created_at <= after

    def test_full_lifecycle(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Investigate billing anomaly",
            description="Billing codes show unexpected pattern.",
            target_type="anomaly",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.HIGH,
            due_date=date(2026, 7, 1),
        )
        assert assignment.status == AssignmentStatus.OPEN
        assert not assignment.is_terminal()

        assignment.start_progress()
        assert assignment.status == AssignmentStatus.IN_PROGRESS

        assignment.complete(note="Root cause identified: duplicate codes.")
        assert assignment.status == AssignmentStatus.COMPLETED
        assert assignment.is_terminal()
        assert assignment.completion_note == "Root cause identified: duplicate codes."


# ============================================================
# WATCHLIST TESTS
# ============================================================

class TestWatchlist:
    def test_create_watchlist(self, user_id):
        watchlist = Watchlist(
            user_id=user_id,
            name="Cardiology Metrics",
            notification_config={"email": True, "frequency": "daily"},
        )
        assert watchlist.user_id == user_id
        assert watchlist.name == "Cardiology Metrics"
        assert watchlist.items == []
        assert watchlist.notification_config == {"email": True, "frequency": "daily"}

    def test_default_values(self, user_id):
        watchlist = Watchlist(user_id=user_id, name="My Watchlist")
        assert watchlist.items == []
        assert watchlist.notification_config == {}

    def test_add_item(self, user_id):
        watchlist = Watchlist(user_id=user_id, name="Revenue Watch")
        item_id = uuid.uuid4()
        watchlist.add_item(WatchlistItemType.METRIC, item_id, "Revenue per Patient")
        assert watchlist.item_count() == 1
        assert watchlist.items[0]["type"] == "METRIC"
        assert watchlist.items[0]["id"] == str(item_id)
        assert watchlist.items[0]["label"] == "Revenue per Patient"

    def test_add_duplicate_item(self, user_id):
        watchlist = Watchlist(user_id=user_id, name="Duplicate Test")
        item_id = uuid.uuid4()
        watchlist.add_item(WatchlistItemType.METRIC, item_id, "Revenue")
        watchlist.add_item(WatchlistItemType.METRIC, item_id, "Revenue Again")
        assert watchlist.item_count() == 1

    def test_add_different_type_same_id(self, user_id):
        watchlist = Watchlist(user_id=user_id, name="Multi Type")
        item_id = uuid.uuid4()
        watchlist.add_item(WatchlistItemType.METRIC, item_id, "Revenue Metric")
        watchlist.add_item(WatchlistItemType.INSIGHT, item_id, "Revenue Insight")
        assert watchlist.item_count() == 2

    def test_remove_item(self, user_id):
        watchlist = Watchlist(user_id=user_id, name="Remove Test")
        item_id = uuid.uuid4()
        watchlist.add_item(WatchlistItemType.DEPARTMENT, item_id, "Cardiology")
        assert watchlist.item_count() == 1
        removed = watchlist.remove_item(WatchlistItemType.DEPARTMENT, item_id)
        assert removed is True
        assert watchlist.item_count() == 0

    def test_remove_nonexistent_item(self, user_id):
        watchlist = Watchlist(user_id=user_id, name="Empty")
        removed = watchlist.remove_item(WatchlistItemType.METRIC, uuid.uuid4())
        assert removed is False

    def test_has_item(self, user_id):
        watchlist = Watchlist(user_id=user_id, name="Check")
        item_id = uuid.uuid4()
        watchlist.add_item(WatchlistItemType.REPORT, item_id, "Q2 Report")
        assert watchlist.has_item(WatchlistItemType.REPORT, item_id) is True
        assert watchlist.has_item(WatchlistItemType.METRIC, item_id) is False

    def test_items_by_type(self, user_id):
        watchlist = Watchlist(user_id=user_id, name="Filter Test")
        metric_id = uuid.uuid4()
        insight_id = uuid.uuid4()
        dept_id = uuid.uuid4()
        watchlist.add_item(WatchlistItemType.METRIC, metric_id, "Revenue")
        watchlist.add_item(WatchlistItemType.INSIGHT, insight_id, "Cost Trend")
        watchlist.add_item(WatchlistItemType.DEPARTMENT, dept_id, "Cardiology")
        metrics = watchlist.items_by_type(WatchlistItemType.METRIC)
        assert len(metrics) == 1
        assert metrics[0]["type"] == "METRIC"
        insights = watchlist.items_by_type(WatchlistItemType.INSIGHT)
        assert len(insights) == 1

    def test_clear(self, user_id):
        watchlist = Watchlist(user_id=user_id, name="Clear Test")
        for i in range(5):
            watchlist.add_item(WatchlistItemType.METRIC, uuid.uuid4(), f"Metric {i}")
        assert watchlist.item_count() == 5
        watchlist.clear()
        assert watchlist.item_count() == 0

    def test_update_notification_config(self, user_id):
        watchlist = Watchlist(
            user_id=user_id,
            name="Notif Test",
            notification_config={"email": True},
        )
        watchlist.update_notification_config({"slack": True, "frequency": "weekly"})
        assert watchlist.notification_config["email"] is True
        assert watchlist.notification_config["slack"] is True
        assert watchlist.notification_config["frequency"] == "weekly"

    def test_default_id(self, user_id):
        w1 = Watchlist(user_id=user_id, name="W1")
        w2 = Watchlist(user_id=user_id, name="W2")
        assert w1.id != w2.id

    def test_default_created_at(self, user_id):
        before = datetime.utcnow()
        watchlist = Watchlist(user_id=user_id, name="Timestamp Test")
        after = datetime.utcnow()
        assert before <= watchlist.created_at <= after

    def test_add_multiple_items(self, user_id):
        watchlist = Watchlist(user_id=user_id, name="Multi Item")
        ids = [uuid.uuid4() for _ in range(3)]
        watchlist.add_item(WatchlistItemType.METRIC, ids[0], "M1")
        watchlist.add_item(WatchlistItemType.METRIC, ids[1], "M2")
        watchlist.add_item(WatchlistItemType.METRIC, ids[2], "M3")
        assert watchlist.item_count() == 3
        metrics = watchlist.items_by_type(WatchlistItemType.METRIC)
        assert len(metrics) == 3

    def test_all_item_types(self, user_id):
        watchlist = Watchlist(user_id=user_id, name="All Types")
        for item_type in WatchlistItemType:
            watchlist.add_item(item_type, uuid.uuid4(), item_type.value)
        assert watchlist.item_count() == len(WatchlistItemType)

    def test_remove_item_returns_false_for_wrong_type(self, user_id):
        watchlist = Watchlist(user_id=user_id, name="Wrong Type")
        item_id = uuid.uuid4()
        watchlist.add_item(WatchlistItemType.METRIC, item_id, "Revenue")
        removed = watchlist.remove_item(WatchlistItemType.INSIGHT, item_id)
        assert removed is False
        assert watchlist.item_count() == 1


# ============================================================
# INTEGRATION-STYLE TESTS
# ============================================================

class TestCollaborationIntegration:
    def test_comment_thread_lifecycle(self, user_id, another_user_id, target_id):
        thread = CommentThread(
            target_type=CommentTarget.ANOMALY,
            target_id=target_id,
            title="Anomaly Investigation",
        )

        root = Comment(
            target_type=CommentTarget.ANOMALY,
            target_id=target_id,
            content="I noticed unusual billing patterns.",
            created_by=user_id,
            thread_id=thread.id,
        )
        thread.record_comment(user_id)

        reply = Comment(
            target_type=CommentTarget.ANOMALY,
            target_id=target_id,
            content="@admin can you verify the data source?",
            created_by=another_user_id,
            parent_id=root.id,
            thread_id=thread.id,
        )
        reply.add_mention(uuid.uuid4(), "Admin")
        thread.record_comment(another_user_id)

        assert thread.comment_count == 2
        assert thread.participant_count() == 2
        assert thread.is_participant(user_id)
        assert thread.is_participant(another_user_id)

        root.resolve(resolver=another_user_id)
        assert root.is_resolved
        thread.close()
        assert not thread.is_open

    def test_assignment_with_watchlist(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Review metric accuracy",
            description="Verify Q2 revenue metric calculations.",
            target_type="metric",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.HIGH,
            due_date=date(2026, 6, 30),
        )

        watchlist = Watchlist(
            user_id=user_id,
            name="Assigned Tasks",
            notification_config={"email": True, "frequency": "daily"},
        )
        watchlist.add_item(WatchlistItemType.METRIC, target_id, "Q2 Revenue")

        assignment.start_progress()
        assert assignment.status == AssignmentStatus.IN_PROGRESS
        assert watchlist.has_item(WatchlistItemType.METRIC, target_id)

        assignment.complete(note="Verified against source data.")
        assert assignment.is_terminal()
        assert not assignment.is_overdue(reference_date=date(2026, 6, 12))

    def test_comment_on_assignment(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="Investigate cost spike",
            description="Pharmacy costs increased 20%.",
            target_type="anomaly",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.CRITICAL,
        )

        comment = Comment(
            target_type=CommentTarget.ANOMALY,
            target_id=target_id,
            content="Started investigating. Will update by EOD.",
            created_by=user_id,
        )
        comment.add_mention(another_user_id, "Assigned By")
        assert len(comment.mentions) == 1

        assignment.start_progress()
        comment.edit("Progress update: Identified potential data quality issue.")
        assert comment.edited_at is not None

        assignment.complete(note="Root cause: incorrect supplier codes.")
        comment.resolve(resolver=another_user_id)
        assert comment.is_resolved
        assert assignment.is_terminal()

    def test_multi_watchlist_scenario(self, user_id):
        revenue_watchlist = Watchlist(
            user_id=user_id,
            name="Revenue Metrics",
            notification_config={"email": True},
        )
        cost_watchlist = Watchlist(
            user_id=user_id,
            name="Cost Metrics",
            notification_config={"slack": True},
        )

        metric_ids = [uuid.uuid4() for _ in range(4)]
        revenue_watchlist.add_item(WatchlistItemType.METRIC, metric_ids[0], "Revenue per Patient")
        revenue_watchlist.add_item(WatchlistItemType.METRIC, metric_ids[1], "Total Revenue")
        cost_watchlist.add_item(WatchlistItemType.METRIC, metric_ids[2], "Pharmacy Cost")
        cost_watchlist.add_item(WatchlistItemType.METRIC, metric_ids[3], "Staff Cost")

        assert revenue_watchlist.item_count() == 2
        assert cost_watchlist.item_count() == 2

        revenue_watchlist.remove_item(WatchlistItemType.METRIC, metric_ids[1])
        assert revenue_watchlist.item_count() == 1
        assert cost_watchlist.item_count() == 2

    def test_assignment_dismiss_and_reopen(self, user_id, another_user_id, target_id):
        assignment = Assignment(
            title="False positive alert",
            description="This anomaly was a false positive.",
            target_type="anomaly",
            target_id=target_id,
            assignee_id=user_id,
            assigned_by=another_user_id,
            priority=AssignmentPriority.LOW,
        )
        assignment.dismiss()
        assert assignment.status == AssignmentStatus.DISMISSED
        assert assignment.is_terminal()

        assignment.reopen()
        assert assignment.status == AssignmentStatus.OPEN
        assert not assignment.is_terminal()
        assert assignment.completed_at is None

        assignment.complete(note="Confirmed as false positive.")
        assert assignment.is_terminal()
