"""
Domain 7: Executive Workspace — Personalized executive dashboards, briefings, and notifications.
Provides each executive with a tailored view of the metrics, decisions, and insights that matter most.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any


# ============================================================
# SECTION TYPE
# ============================================================

class SectionType(Enum):
    """Types of sections available in the executive workspace."""
    MY_DASHBOARD = "my_dashboard"
    MY_DECISIONS = "my_decisions"
    MY_RECOMMENDATIONS = "my_recommendations"
    MY_WATCHLISTS = "my_watchlists"
    MY_REPORTS = "my_reports"
    MY_BRIEFINGS = "my_briefings"
    MY_ANOMALIES = "my_anomalies"
    MY_ASSIGNMENTS = "my_assignments"


# ============================================================
# WORKSPACE SECTION
# ============================================================

@dataclass(kw_only=True)
class WorkspaceSection:
    """A single configurable section within the executive workspace."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    section_type: SectionType
    position: int
    config: Dict[str, Any] = field(default_factory=dict)
    is_collapsed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "section_type": self.section_type.value,
            "position": self.position,
            "config": self.config,
            "is_collapsed": self.is_collapsed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ============================================================
# EXECUTIVE WORKSPACE
# ============================================================

@dataclass(kw_only=True)
class ExecutiveWorkspace:
    """The full personalized workspace configuration for an executive user."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    sections: List[WorkspaceSection] = field(default_factory=list)
    layout: Dict[str, Any] = field(default_factory=dict)
    notification_preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_section(self, section: WorkspaceSection) -> None:
        """Add a section to the workspace."""
        self.sections.append(section)
        self._reorder_positions()
        self.updated_at = datetime.utcnow()

    def remove_section(self, section_id: uuid.UUID) -> bool:
        """Remove a section by ID. Returns True if found and removed."""
        original_length = len(self.sections)
        self.sections = [s for s in self.sections if s.id != section_id]
        if len(self.sections) < original_length:
            self._reorder_positions()
            self.updated_at = datetime.utcnow()
            return True
        return False

    def get_section(self, section_id: uuid.UUID) -> Optional[WorkspaceSection]:
        """Get a section by ID."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def reorder_sections(self, ordered_ids: List[uuid.UUID]) -> None:
        """Reorder sections based on provided ID list."""
        section_map = {s.id: s for s in self.sections}
        reordered: List[WorkspaceSection] = []
        for sid in ordered_ids:
            if sid in section_map:
                reordered.append(section_map[sid])
        for s in self.sections:
            if s.id not in ordered_ids:
                reordered.append(s)
        self.sections = reordered
        self._reorder_positions()
        self.updated_at = datetime.utcnow()

    def get_section_by_type(self, section_type: SectionType) -> Optional[WorkspaceSection]:
        """Get the first section matching the given type."""
        for section in self.sections:
            if section.section_type == section_type:
                return section
        return None

    def collapse_section(self, section_id: uuid.UUID) -> bool:
        """Collapse a section. Returns True if found."""
        section = self.get_section(section_id)
        if section:
            section.is_collapsed = True
            section.updated_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False

    def expand_section(self, section_id: uuid.UUID) -> bool:
        """Expand a section. Returns True if found."""
        section = self.get_section(section_id)
        if section:
            section.is_collapsed = False
            section.updated_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False

    def update_layout(self, layout: Dict[str, Any]) -> None:
        """Update the workspace layout."""
        self.layout = layout
        self.updated_at = datetime.utcnow()

    def update_notification_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update notification preferences."""
        self.notification_preferences = preferences
        self.updated_at = datetime.utcnow()

    def _reorder_positions(self) -> None:
        """Recalculate position indices after mutation."""
        for idx, section in enumerate(self.sections):
            section.position = idx

    def active_section_count(self) -> int:
        """Return the count of non-collapsed sections."""
        return sum(1 for s in self.sections if not s.is_collapsed)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "sections": [s.to_dict() for s in self.sections],
            "layout": self.layout,
            "notification_preferences": self.notification_preferences,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ============================================================
# BRIEFING SECTION
# ============================================================

@dataclass(kw_only=True)
class BriefingSection:
    """A single section within an executive briefing."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    title: str
    content: str
    metric_values: List[Dict[str, Any]] = field(default_factory=list)
    highlights: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_metric_value(self, metric_name: str, value: Any, unit: Optional[str] = None, trend: Optional[str] = None) -> None:
        """Add a metric value to this briefing section."""
        entry: Dict[str, Any] = {"metric_name": metric_name, "value": value}
        if unit is not None:
            entry["unit"] = unit
        if trend is not None:
            entry["trend"] = trend
        self.metric_values.append(entry)

    def add_highlight(self, highlight: str) -> None:
        """Add a highlight to this briefing section."""
        self.highlights.append(highlight)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "title": self.title,
            "content": self.content,
            "metric_values": self.metric_values,
            "highlights": self.highlights,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================
# EXECUTIVE BRIEFING
# ============================================================

@dataclass(kw_only=True)
class ExecutiveBriefing:
    """A generated briefing document for an executive covering a specific period."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    generated_at: datetime = field(default_factory=datetime.utcnow)
    period_start: date
    period_end: date
    sections: List[BriefingSection] = field(default_factory=list)
    ai_generated_summary: Optional[str] = None
    is_read: bool = False
    read_at: Optional[datetime] = None

    def mark_as_read(self) -> None:
        """Mark the briefing as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()

    def add_section(self, section: BriefingSection) -> None:
        """Add a section to the briefing."""
        self.sections.append(section)

    def get_section_by_title(self, title: str) -> Optional[BriefingSection]:
        """Find a section by its title."""
        for section in self.sections:
            if section.title == title:
                return section
        return None

    def total_highlights(self) -> int:
        """Count total highlights across all sections."""
        return sum(len(s.highlights) for s in self.sections)

    def total_metric_values(self) -> int:
        """Count total metric values across all sections."""
        return sum(len(s.metric_values) for s in self.sections)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "generated_at": self.generated_at.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "sections": [s.to_dict() for s in self.sections],
            "ai_generated_summary": self.ai_generated_summary,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }


# ============================================================
# NOTIFICATION CONFIG
# ============================================================

@dataclass(kw_only=True)
class NotificationConfig:
    """Configuration for how an executive receives notifications."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    email_enabled: bool = True
    push_enabled: bool = True
    frequency: str = "real_time"
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def set_quiet_hours(self, start: str, end: str) -> None:
        """Set quiet hours during which notifications are suppressed."""
        self.quiet_hours_start = start
        self.quiet_hours_end = end
        self.updated_at = datetime.utcnow()

    def clear_quiet_hours(self) -> None:
        """Remove quiet hours configuration."""
        self.quiet_hours_start = None
        self.quiet_hours_end = None
        self.updated_at = datetime.utcnow()

    def is_any_channel_enabled(self) -> bool:
        """Check if at least one notification channel is enabled."""
        return self.email_enabled or self.push_enabled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "email_enabled": self.email_enabled,
            "push_enabled": self.push_enabled,
            "frequency": self.frequency,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ============================================================
# WORKSPACE LAYOUT
# ============================================================

@dataclass(kw_only=True)
class WorkspaceLayout:
    """Controls the visual layout and theme of the executive workspace."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    columns: int = 2
    theme: str = "light"
    compact_mode: bool = False
    show_sidebar: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def set_theme(self, theme: str) -> None:
        """Set the workspace theme."""
        self.theme = theme
        self.updated_at = datetime.utcnow()

    def toggle_compact_mode(self) -> None:
        """Toggle compact mode on/off."""
        self.compact_mode = not self.compact_mode
        self.updated_at = datetime.utcnow()

    def toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        self.show_sidebar = not self.show_sidebar
        self.updated_at = datetime.utcnow()

    def set_columns(self, columns: int) -> None:
        """Set the number of layout columns."""
        if columns < 1 or columns > 4:
            raise ValueError("Columns must be between 1 and 4")
        self.columns = columns
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "columns": self.columns,
            "theme": self.theme,
            "compact_mode": self.compact_mode,
            "show_sidebar": self.show_sidebar,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
