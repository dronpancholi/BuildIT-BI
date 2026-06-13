"""
Collaboration Domain — Healthcare Financial Intelligence Platform.
Entities for comments, assignments, and watchlists.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================
# ENUMS
# ============================================================

class CommentTarget(Enum):
    INSIGHT = "INSIGHT"
    RECOMMENDATION = "RECOMMENDATION"
    ANOMALY = "ANOMALY"
    DECISION = "DECISION"
    REPORT = "REPORT"
    DASHBOARD = "DASHBOARD"


class AssignmentStatus(Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DISMISSED = "DISMISSED"


class AssignmentPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WatchlistItemType(Enum):
    METRIC = "METRIC"
    INSIGHT = "INSIGHT"
    DEPARTMENT = "DEPARTMENT"
    HOSPITAL = "HOSPITAL"
    REPORT = "REPORT"


# ============================================================
# COMMENT
# ============================================================

@dataclass(kw_only=True)
class Comment:
    """A comment on an analytics entity with optional threading."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    target_type: CommentTarget
    target_id: uuid.UUID
    content: str
    mentions: List[Dict[str, Any]] = field(default_factory=list)
    parent_id: Optional[uuid.UUID] = None
    thread_id: Optional[uuid.UUID] = None
    created_by: uuid.UUID
    created_at: datetime = field(default_factory=datetime.utcnow)
    edited_at: Optional[datetime] = None
    is_resolved: bool = False
    resolved_by: Optional[uuid.UUID] = None
    resolved_at: Optional[datetime] = None

    def edit(self, new_content: str) -> None:
        self.content = new_content
        self.edited_at = datetime.utcnow()

    def resolve(self, resolver: uuid.UUID) -> None:
        self.is_resolved = True
        self.resolved_by = resolver
        self.resolved_at = datetime.utcnow()

    def unresolve(self) -> None:
        self.is_resolved = False
        self.resolved_by = None
        self.resolved_at = None

    def is_reply(self) -> bool:
        return self.parent_id is not None

    def is_thread_root(self) -> bool:
        return self.parent_id is None and self.thread_id is None

    def add_mention(self, user_id: uuid.UUID, display_name: str) -> None:
        self.mentions.append({"user_id": str(user_id), "display_name": display_name})

    def mentioned_user_ids(self) -> List[uuid.UUID]:
        return [uuid.UUID(m["user_id"]) for m in self.mentions]


# ============================================================
# COMMENT THREAD
# ============================================================

@dataclass(kw_only=True)
class CommentThread:
    """A thread grouping comments on the same target."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    target_type: CommentTarget
    target_id: uuid.UUID
    title: Optional[str] = None
    is_open: bool = True
    participant_ids: List[uuid.UUID] = field(default_factory=list)
    last_activity_at: datetime = field(default_factory=datetime.utcnow)
    comment_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_participant(self, user_id: uuid.UUID) -> None:
        if user_id not in self.participant_ids:
            self.participant_ids.append(user_id)
        self.last_activity_at = datetime.utcnow()

    def record_comment(self, commenter_id: uuid.UUID) -> None:
        self.comment_count += 1
        self.add_participant(commenter_id)

    def close(self) -> None:
        self.is_open = False

    def reopen(self) -> None:
        self.is_open = True

    def is_participant(self, user_id: uuid.UUID) -> bool:
        return user_id in self.participant_ids

    def participant_count(self) -> int:
        return len(self.participant_ids)


# ============================================================
# ASSIGNMENT
# ============================================================

@dataclass(kw_only=True)
class Assignment:
    """A task assignment for follow-up on insights, anomalies, or decisions."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    title: str
    description: str
    target_type: str
    target_id: uuid.UUID
    assignee_id: uuid.UUID
    assigned_by: uuid.UUID
    priority: AssignmentPriority
    due_date: Optional[date] = None
    status: AssignmentStatus = AssignmentStatus.OPEN
    completed_at: Optional[datetime] = None
    completion_note: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def start_progress(self) -> None:
        if self.status != AssignmentStatus.OPEN:
            raise ValueError(f"Cannot start progress on assignment in {self.status.value} status")
        self.status = AssignmentStatus.IN_PROGRESS

    def complete(self, note: Optional[str] = None) -> None:
        if self.status not in (AssignmentStatus.OPEN, AssignmentStatus.IN_PROGRESS):
            raise ValueError(f"Cannot complete assignment in {self.status.value} status")
        self.status = AssignmentStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.completion_note = note

    def dismiss(self) -> None:
        if self.status == AssignmentStatus.COMPLETED:
            raise ValueError("Cannot dismiss a completed assignment")
        self.status = AssignmentStatus.DISMISSED

    def reopen(self) -> None:
        if self.status != AssignmentStatus.DISMISSED:
            raise ValueError("Can only reopen dismissed assignments")
        self.status = AssignmentStatus.OPEN
        self.completed_at = None
        self.completion_note = None

    def is_overdue(self, reference_date: Optional[date] = None) -> bool:
        if self.due_date is None:
            return False
        if self.status in (AssignmentStatus.COMPLETED, AssignmentStatus.DISMISSED):
            return False
        ref = reference_date or date.today()
        return ref > self.due_date

    def is_terminal(self) -> bool:
        return self.status in (AssignmentStatus.COMPLETED, AssignmentStatus.DISMISSED)

    def reassign(self, new_assignee: uuid.UUID) -> None:
        self.assignee_id = new_assignee

    def change_priority(self, new_priority: AssignmentPriority) -> None:
        self.priority = new_priority


# ============================================================
# WATCHLIST
# ============================================================

@dataclass(kw_only=True)
class Watchlist:
    """A user's curated watchlist of metrics, insights, and entities."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    name: str
    items: List[Dict[str, Any]] = field(default_factory=list)
    notification_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_item(self, item_type: WatchlistItemType, item_id: uuid.UUID, label: str = "") -> None:
        item = {"type": item_type.value, "id": str(item_id), "label": label}
        if not self._item_exists(item_type, item_id):
            self.items.append(item)

    def remove_item(self, item_type: WatchlistItemType, item_id: uuid.UUID) -> bool:
        before = len(self.items)
        self.items = [
            i for i in self.items
            if not (i["type"] == item_type.value and i["id"] == str(item_id))
        ]
        return len(self.items) < before

    def has_item(self, item_type: WatchlistItemType, item_id: uuid.UUID) -> bool:
        return self._item_exists(item_type, item_id)

    def item_count(self) -> int:
        return len(self.items)

    def items_by_type(self, item_type: WatchlistItemType) -> List[Dict[str, Any]]:
        return [i for i in self.items if i["type"] == item_type.value]

    def clear(self) -> None:
        self.items.clear()

    def update_notification_config(self, config: Dict[str, Any]) -> None:
        self.notification_config.update(config)

    def _item_exists(self, item_type: WatchlistItemType, item_id: uuid.UUID) -> bool:
        return any(
            i["type"] == item_type.value and i["id"] == str(item_id)
            for i in self.items
        )
