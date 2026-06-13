from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Intent(Enum):
    PERFORMANCE_ANALYSIS = "performance_analysis"
    ROOT_CAUSE = "root_cause"
    FORECAST_EXPLAIN = "forecast_explain"
    VARIANCE_ANALYSIS = "variance_analysis"
    SCENARIO_PLANNING = "scenario_planning"
    RECOMMENDATION = "recommendation"
    BRIEFING = "briefing"
    WHAT_IF = "what_if"
    RISK_ASSESSMENT = "risk_assessment"
    BENCHMARKING = "benchmarking"
    TREND_ANALYSIS = "trend_analysis"
    ANOMALY_EXPLAIN = "anomaly_explain"


class BriefingMode(Enum):
    ON_DEMAND = "on_demand"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"


class BriefingStatus(Enum):
    GENERATED = "generated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    DISSEMINATED = "disseminated"
    ARCHIVED = "archived"


class Urgency(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RecommendationPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CFOProfile:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    name: str = ""
    role: str = ""
    preferences: Dict[str, Any] = field(default_factory=lambda: {
        "preferred_language": "en",
        "briefing_frequency": "daily",
        "risk_tolerance": "medium",
        "focus_areas": [],
        "report_format": "pdf",
    })
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True


@dataclass
class Question:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    user_query: str = ""
    intent: Intent = Intent.PERFORMANCE_ANALYSIS
    context: Dict[str, Any] = field(default_factory=lambda: {
        "entities": [],
        "time_range": None,
        "filters": {},
    })
    routing: Dict[str, Any] = field(default_factory=dict)
    reasoning_trace: List[str] = field(default_factory=list)
    answer: Dict[str, Any] = field(default_factory=dict)
    evidence_chain: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    processing_time_ms: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Briefing:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    mode: BriefingMode = BriefingMode.ON_DEMAND
    status: BriefingStatus = BriefingStatus.GENERATED
    period: str = ""
    generated_at: datetime = field(default_factory=datetime.utcnow)
    sections: List[Dict[str, Any]] = field(default_factory=list)
    score: int = 0
    executive_summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    narrative: str = ""


@dataclass
class Workspace:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    owner_id: UUID = field(default_factory=uuid4)
    members: List[Dict[str, Any]] = field(default_factory=list)
    widgets: List[Dict[str, Any]] = field(default_factory=list)
    layout: Dict[str, Any] = field(default_factory=dict)
    shared: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AlertConfig:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    metric_id: UUID = field(default_factory=uuid4)
    metric_name: str = ""
    user_id: UUID = field(default_factory=uuid4)
    condition: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, Any] = field(default_factory=lambda: {
        "warning": None,
        "critical": None,
    })
    channels: List[str] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Alert:
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    config_id: UUID = field(default_factory=uuid4)
    metric_id: UUID = field(default_factory=uuid4)
    metric_name: str = ""
    message: str = ""
    severity: RiskSeverity = RiskSeverity.INFO
    value: Decimal = Decimal("0")
    threshold: Decimal = Decimal("0")
    is_read: bool = False
    is_dismissed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Intent routing map
# ---------------------------------------------------------------------------

_INTENT_KEYWORDS: Dict[str, List[str]] = {
    Intent.ROOT_CAUSE: ["why"],
    Intent.FORECAST_EXPLAIN: ["will", "forecast"],
    Intent.WHAT_IF: ["what if", "what-if"],
    Intent.RISK_ASSESSMENT: ["risk"],
    Intent.BENCHMARKING: ["compare", "benchmark"],
    Intent.TREND_ANALYSIS: ["trend"],
    Intent.ANOMALY_EXPLAIN: ["anomaly"],
    Intent.VARIANCE_ANALYSIS: ["variance", "budget"],
    Intent.SCENARIO_PLANNING: ["scenario", "plan"],
    Intent.RECOMMENDATION: ["recommend"],
    Intent.BRIEFING: ["briefing", "summary"],
}


def _classify_intent(query: str) -> Intent:
    lowered = query.lower()
    for intent, keywords in _INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                return intent
    return Intent.PERFORMANCE_ANALYSIS


def _build_routing(intent: Intent, query: str) -> Dict[str, Any]:
    return {
        "intent": intent.value,
        "query_length": len(query),
        "timestamp": datetime.utcnow().isoformat(),
    }


def _build_evidence_chain(
    intent: Intent,
    context: Dict[str, Any],
) -> List[Dict[str, Any]]:
    evidence: List[Dict[str, Any]] = []
    entities = context.get("entities", [])
    for entity in entities:
        evidence.append({
            "source": "context",
            "entity": entity,
            "relevance": 1.0,
            "timestamp": datetime.utcnow().isoformat(),
        })
    if not evidence:
        evidence.append({
            "source": "default",
            "entity": "system",
            "relevance": 0.5,
            "timestamp": datetime.utcnow().isoformat(),
        })
    return evidence


def _generate_answer(
    intent: Intent,
    query: str,
    context: Dict[str, Any],
    evidence_chain: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "intent": intent.value,
        "query": query,
        "entities": context.get("entities", []),
        "time_range": context.get("time_range"),
        "evidence_count": len(evidence_chain),
        "summary": f"Analysis for '{query}' under intent {intent.value}.",
    }


def _score_briefing(sections: List[Dict[str, Any]]) -> int:
    if not sections:
        return 0
    total = 0
    for section in sections:
        total += section.get("score", 0)
    return total // len(sections)


def _generate_executive_summary(
    sections: List[Dict[str, Any]],
    period: str,
) -> str:
    if not sections:
        return f"No data available for period {period}."
    highlights = [s.get("title", "Untitled") for s in sections[:3]]
    return (
        f"Briefing for {period}: covering "
        + ", ".join(highlights)
        + "."
    )


def _generate_key_findings(sections: List[Dict[str, Any]]) -> List[str]:
    findings: List[str] = []
    for section in sections:
        title = section.get("title", "Section")
        value = section.get("value", "N/A")
        findings.append(f"{title}: {value}")
    return findings


def _generate_actions(sections: List[Dict[str, Any]]) -> List[str]:
    actions: List[str] = []
    for section in sections:
        action = section.get("action")
        if action:
            actions.append(action)
    if not actions:
        actions.append("Review detailed report for further insights.")
    return actions


def _generate_narrative(
    intent: Intent,
    query: str,
    context: Dict[str, Any],
) -> str:
    return (
        f"Narrative for intent '{intent.value}': "
        f"the query '{query}' was processed with "
        f"{len(context.get('entities', []))} contextual entity(ies)."
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class CFOCoreService:
    """Central service for the AI CFO Platform core domain."""

    def __init__(self) -> None:
        self._profiles: Dict[UUID, CFOProfile] = {}
        self._questions: Dict[UUID, Question] = {}
        self._briefings: Dict[UUID, Briefing] = {}
        self._workspaces: Dict[UUID, Workspace] = {}
        self._alert_configs: Dict[UUID, AlertConfig] = {}
        self._alerts: Dict[UUID, Alert] = {}

    # ---- Profile CRUD -----------------------------------------------------

    def create_profile(
        self,
        tenant_id: UUID,
        name: str,
        role: str,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> CFOProfile:
        profile = CFOProfile(
            tenant_id=tenant_id,
            name=name,
            role=role,
            preferences=preferences or CFOProfile().preferences,
        )
        self._profiles[profile.id] = profile
        return profile

    def get_profile(
        self,
        tenant_id: UUID,
        profile_id: UUID,
    ) -> Optional[CFOProfile]:
        profile = self._profiles.get(profile_id)
        if profile is None or profile.tenant_id != tenant_id:
            return None
        return profile

    def update_profile(
        self,
        tenant_id: UUID,
        profile_id: UUID,
        updates: Dict[str, Any],
    ) -> CFOProfile:
        profile = self.get_profile(tenant_id, profile_id)
        if profile is None:
            raise KeyError(f"Profile {profile_id} not found in tenant {tenant_id}")
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.updated_at = datetime.utcnow()
        return profile

    # ---- Question handling ------------------------------------------------

    def ask_question(
        self,
        tenant_id: UUID,
        user_id: UUID,
        user_query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Question:
        ctx = context or {"entities": [], "time_range": None, "filters": {}}
        intent = _classify_intent(user_query)
        routing = _build_routing(intent, user_query)
        evidence_chain = _build_evidence_chain(intent, ctx)
        answer = _generate_answer(intent, user_query, ctx, evidence_chain)
        confidence = min(1.0, 0.6 + 0.1 * len(evidence_chain))

        question = Question(
            tenant_id=tenant_id,
            user_id=user_id,
            user_query=user_query,
            intent=intent,
            context=ctx,
            routing=routing,
            reasoning_trace=[
                f"Classified intent as {intent.value}",
                f"Built evidence chain with {len(evidence_chain)} item(s)",
                f"Generated answer with confidence {confidence:.2f}",
            ],
            answer=answer,
            evidence_chain=evidence_chain,
            confidence=confidence,
            processing_time_ms=0,
        )
        self._questions[question.id] = question
        return question

    # ---- Briefing ---------------------------------------------------------

    def get_briefing(
        self,
        tenant_id: UUID,
        briefing_id: UUID,
    ) -> Optional[Briefing]:
        briefing = self._briefings.get(briefing_id)
        if briefing is None or briefing.tenant_id != tenant_id:
            return None
        return briefing

    def generate_briefing(
        self,
        tenant_id: UUID,
        mode: BriefingMode,
        period: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Briefing:
        ctx = context or {}
        sections = ctx.get("sections", [])
        score = _score_briefing(sections)
        executive_summary = _generate_executive_summary(sections, period)
        key_findings = _generate_key_findings(sections)
        actions = _generate_actions(sections)

        briefing = Briefing(
            tenant_id=tenant_id,
            mode=mode,
            status=BriefingStatus.GENERATED,
            period=period,
            sections=sections,
            score=score,
            executive_summary=executive_summary,
            key_findings=key_findings,
            actions=actions,
            narrative="",
        )
        self._briefings[briefing.id] = briefing
        return briefing

    # ---- Workspace --------------------------------------------------------

    def create_workspace(
        self,
        tenant_id: UUID,
        name: str,
        description: str,
        owner_id: UUID,
        members: Optional[List[Dict[str, Any]]] = None,
    ) -> Workspace:
        ws = Workspace(
            tenant_id=tenant_id,
            name=name,
            description=description,
            owner_id=owner_id,
            members=members or [],
        )
        self._workspaces[ws.id] = ws
        return ws

    def get_workspace(
        self,
        tenant_id: UUID,
        workspace_id: UUID,
    ) -> Optional[Workspace]:
        ws = self._workspaces.get(workspace_id)
        if ws is None or ws.tenant_id != tenant_id:
            return None
        return ws

    def add_widget(
        self,
        tenant_id: UUID,
        workspace_id: UUID,
        widget_type: str,
        config: Dict[str, Any],
    ) -> Workspace:
        ws = self.get_workspace(tenant_id, workspace_id)
        if ws is None:
            raise KeyError(f"Workspace {workspace_id} not found in tenant {tenant_id}")
        ws.widgets.append({
            "widget_id": str(uuid4()),
            "type": widget_type,
            "config": config,
        })
        ws.updated_at = datetime.utcnow()
        return ws

    def delete_workspace(
        self,
        tenant_id: UUID,
        workspace_id: UUID,
    ) -> bool:
        ws = self.get_workspace(tenant_id, workspace_id)
        if ws is None:
            return False
        del self._workspaces[workspace_id]
        return True

    # ---- Alerts -----------------------------------------------------------

    def create_alert_config(
        self,
        tenant_id: UUID,
        metric_id: UUID,
        metric_name: str,
        user_id: UUID,
        condition: Dict[str, Any],
        thresholds: Dict[str, Any],
        channels: List[str],
    ) -> AlertConfig:
        cfg = AlertConfig(
            tenant_id=tenant_id,
            metric_id=metric_id,
            metric_name=metric_name,
            user_id=user_id,
            condition=condition,
            thresholds=thresholds,
            channels=channels,
        )
        self._alert_configs[cfg.id] = cfg
        return cfg

    def get_alerts(
        self,
        tenant_id: UUID,
        user_id: UUID,
        unread_only: bool = False,
    ) -> List[Alert]:
        result: List[Alert] = []
        for alert in self._alerts.values():
            if alert.tenant_id != tenant_id:
                continue
            cfg = self._alert_configs.get(alert.config_id)
            if cfg is not None and cfg.user_id != user_id:
                continue
            if unread_only and alert.is_read:
                continue
            result.append(alert)
        return result

    def dismiss_alert(
        self,
        tenant_id: UUID,
        alert_id: UUID,
    ) -> Alert:
        alert = self._alerts.get(alert_id)
        if alert is None or alert.tenant_id != tenant_id:
            raise KeyError(f"Alert {alert_id} not found in tenant {tenant_id}")
        alert.is_dismissed = True
        alert.is_read = True
        alert.read_at = datetime.utcnow()
        return alert
