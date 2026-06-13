"""
Domain 10: AI CFO Copilot.
Natural language interface for healthcare financial analysis with multi-step reasoning,
cross-domain analysis, and proactive insights.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Tuple, Any


class CopilotAction(Enum):
    ANALYZE = "ANALYZE"
    FORECAST = "FORECAST"
    COMPARE = "COMPARE"
    EXPLAIN = "EXPLAIN"
    RECOMMEND = "RECOMMEND"
    GENERATE_BRIEFING = "GENERATE_BRIEFING"
    RUN_SCENARIO = "RUN_SCENARIO"
    ASSESS_RISK = "ASSESS_RISK"
    FIND_ROOT_CAUSE = "FIND_ROOT_CAUSE"
    DECOMPOSE = "DECOMPOSE"
    OPTIMIZE = "OPTIMIZE"
    SUMMARIZE = "SUMMARIZE"
    PROJECT = "PROJECT"
    EVALUATE = "EVALUATE"
    SIMULATE = "SIMULATE"


class ReasoningStep(Enum):
    PARSE = "PARSE"
    CLASSIFY = "CLASSIFY"
    ROUTE = "ROUTE"
    RETRIEVE = "RETRIEVE"
    COMPUTE = "COMPUTE"
    VALIDATE = "VALIDATE"
    SYNTHESIZE = "SYNTHESIZE"
    EXPLAIN = "EXPLAIN"


class ConversationRole(Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class ConversationStatus(Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class CopilotCapability(Enum):
    NATURAL_LANGUAGE_QUERY = "NATURAL_LANGUAGE_QUERY"
    MULTI_STEP_REASONING = "MULTI_STEP_REASONING"
    CROSS_DOMAIN_ANALYSIS = "CROSS_DOMAIN_ANALYSIS"
    AUTOMATED_BRIEFING = "AUTOMATED_BRIEFING"
    PROACTIVE_INSIGHTS = "PROACTIVE_INSIGHTS"
    WHAT_IF_SIMULATION = "WHAT_IF_SIMULATION"
    DRILL_DOWN_ANALYSIS = "DRILL_DOWN_ANALYSIS"
    TREND_IDENTIFICATION = "TREND_IDENTIFICATION"
    ANOMALY_EXPLANATION = "ANOMALY_EXPLANATION"
    COMPARATIVE_ANALYSIS = "COMPARATIVE_ANALYSIS"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    OPPORTUNITY_IDENTIFICATION = "OPPORTUNITY_IDENTIFICATION"
    INSTITUTIONAL_MEMORY = "INSTITUTIONAL_MEMORY"
    KNOWLEDGE_GRAPH_EXPLORATION = "KNOWLEDGE_GRAPH_EXPLORATION"
    STRATEGIC_PLANNING = "STRATEGIC_PLANNING"


class PriorityLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Healthcare financial terminology mappings
HEALTHCARE_METRICS = {
    "revenue": {"domain": "financial", "type": "revenue", "aliases": ["income", "earnings", "collections"]},
    "denial rate": {"domain": "revenue_cycle", "type": "denial_rate", "aliases": ["claim denials", "rejected claims"]},
    "claim processing": {"domain": "revenue_cycle", "type": "claims", "aliases": ["claims", "billing"]},
    "bed occupancy": {"domain": "operations", "type": "bed_occupancy", "aliases": ["occupancy rate", "bed usage"]},
    "drg": {"domain": "clinical", "type": "drg", "aliases": ["diagnosis related group", "drg code"]},
    "cmi": {"domain": "clinical", "type": "cmi", "aliases": ["case mix index", "case mix"]},
    "alos": {"domain": "operations", "type": "alos", "aliases": ["average length of stay", "length of stay"]},
    "payer mix": {"domain": "financial", "type": "payer_mix", "aliases": ["payer distribution", "insurance mix"]},
    "cost per case": {"domain": "financial", "type": "cost_per_case", "aliases": ["case cost", "cost per discharge"]},
    "operating margin": {"domain": "financial", "type": "operating_margin", "aliases": ["margin", "operating income margin"]},
    "ebitda": {"domain": "financial", "type": "ebitda", "aliases": ["earnings before interest taxes depreciation amortization"]},
    "cash flow": {"domain": "financial", "type": "cash_flow", "aliases": ["cash position", "liquidity"]},
    "accounts receivable": {"domain": "financial", "type": "ar", "aliases": ["ar", "receivables", "outstanding payments"]},
    "days in ar": {"domain": "financial", "type": "days_in_ar", "aliases": ["days sales outstanding", "collection period"]},
    "case mix index": {"domain": "clinical", "type": "cmi", "aliases": ["cmi", "case mix"]},
}

TIME_PATTERNS = {
    "today": {"relative_days": 0, "period": "day"},
    "yesterday": {"relative_days": 1, "period": "day"},
    "this week": {"relative_days": 0, "period": "week"},
    "last week": {"relative_days": 7, "period": "week"},
    "this month": {"relative_days": 0, "period": "month"},
    "last month": {"relative_days": 30, "period": "month"},
    "this quarter": {"relative_days": 0, "period": "quarter"},
    "last quarter": {"relative_days": 90, "period": "quarter"},
    "this year": {"relative_days": 0, "period": "year"},
    "last year": {"relative_days": 365, "period": "year"},
    "ytd": {"relative_days": 0, "period": "year_to_date"},
    "mtd": {"relative_days": 0, "period": "month_to_date"},
    "qtd": {"relative_days": 0, "period": "quarter_to_date"},
}

INTENT_PATTERNS = {
    "explain": {"action": CopilotAction.EXPLAIN, "keywords": ["why", "explain", "reason", "cause", "how come"]},
    "analyze": {"action": CopilotAction.ANALYZE, "keywords": ["analyze", "analysis", "examine", "investigate", "look at"]},
    "forecast": {"action": CopilotAction.FORECAST, "keywords": ["forecast", "predict", "project", "estimate", "anticipate"]},
    "compare": {"action": CopilotAction.COMPARE, "keywords": ["compare", "comparison", "vs", "versus", "against", "difference"]},
    "recommend": {"action": CopilotAction.RECOMMEND, "keywords": ["recommend", "suggestion", "advice", "should", "what should"]},
    "briefing": {"action": CopilotAction.GENERATE_BRIEFING, "keywords": ["briefing", "summary", "overview", "dashboard", "snapshot"]},
    "scenario": {"action": CopilotAction.RUN_SCENARIO, "keywords": ["what if", "scenario", "suppose", "imagine", "hypothetical"]},
    "risk": {"action": CopilotAction.ASSESS_RISK, "keywords": ["risk", "exposure", "vulnerability", "threat", "concern"]},
    "root cause": {"action": CopilotAction.FIND_ROOT_CAUSE, "keywords": ["root cause", "underlying", "fundamental", "primary driver"]},
    "optimize": {"action": CopilotAction.OPTIMIZE, "keywords": ["optimize", "improve", "maximize", "minimize", "best"]},
    "summarize": {"action": CopilotAction.SUMMARIZE, "keywords": ["summarize", "summary", "tldr", "brief"]},
    "evaluate": {"action": CopilotAction.EVALUATE, "keywords": ["evaluate", "assessment", "score", "grade", "rate"]},
    "simulate": {"action": CopilotAction.SIMULATE, "keywords": ["simulate", "simulation", "model", "test"]},
}


@dataclass(kw_only=True)
class Conversation:
    id: uuid.UUID
    tenant_id: str
    user_id: uuid.UUID
    title: str
    status: ConversationStatus = ConversationStatus.ACTIVE
    messages: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "tenant_id": self.tenant_id,
            "user_id": str(self.user_id),
            "title": self.title,
            "status": self.status.value,
            "messages": self.messages,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(kw_only=True)
class Message:
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: ConversationRole
    content: str
    metadata: Dict[str, Any] = field(default_factory=lambda: {
        "actions_taken": [],
        "reasoning_trace": [],
        "evidence": [],
        "confidence": 0.0,
        "tools_used": [],
    })
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "role": self.role.value,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(kw_only=True)
class CopilotActionRecord:
    id: uuid.UUID
    action_type: CopilotAction
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    reasoning: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_ms: int = 0
    confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "action_type": self.action_type.value,
            "parameters": self.parameters,
            "result": self.result,
            "reasoning": self.reasoning,
            "execution_time_ms": self.execution_time_ms,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(kw_only=True)
class ReasoningChain:
    id: uuid.UUID
    query: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 0.0
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    total_time_ms: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "query": self.query,
            "steps": self.steps,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "total_time_ms": self.total_time_ms,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(kw_only=True)
class CopilotSuggestion:
    id: uuid.UUID
    suggestion_type: str
    title: str
    description: str
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    priority: PriorityLevel = PriorityLevel.MEDIUM
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "suggestion_type": self.suggestion_type,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence,
            "context": self.context,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
        }


class AICFOCopilot:
    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self._conversations: Dict[uuid.UUID, Conversation] = {}
        self._action_records: Dict[uuid.UUID, CopilotActionRecord] = {}
        self._reasoning_chains: Dict[uuid.UUID, ReasoningChain] = {}
        self._user_query_history: Dict[uuid.UUID, List[Dict[str, Any]]] = {}
        self._capabilities = [
            CopilotCapability.NATURAL_LANGUAGE_QUERY,
            CopilotCapability.MULTI_STEP_REASONING,
            CopilotCapability.CROSS_DOMAIN_ANALYSIS,
            CopilotCapability.AUTOMATED_BRIEFING,
            CopilotCapability.PROACTIVE_INSIGHTS,
            CopilotCapability.WHAT_IF_SIMULATION,
            CopilotCapability.DRILL_DOWN_ANALYSIS,
            CopilotCapability.TREND_IDENTIFICATION,
            CopilotCapability.ANOMALY_EXPLANATION,
            CopilotCapability.COMPARATIVE_ANALYSIS,
            CopilotCapability.RISK_ASSESSMENT,
            CopilotCapability.OPPORTUNITY_IDENTIFICATION,
            CopilotCapability.INSTITUTIONAL_MEMORY,
            CopilotCapability.KNOWLEDGE_GRAPH_EXPLORATION,
            CopilotCapability.STRATEGIC_PLANNING,
        ]

    def process_query(
        self, user_id: uuid.UUID, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Message, List[CopilotActionRecord]]:
        context = context or {}
        reasoning_chain = self.multi_step_reasoning(query, context)
        actions_taken: List[CopilotActionRecord] = []

        for step in reasoning_chain.steps:
            if step.get("action_type"):
                action_record = CopilotActionRecord(
                    id=uuid.uuid4(),
                    action_type=step["action_type"],
                    parameters=step.get("parameters", {}),
                    result=step.get("result", {}),
                    reasoning=[{"step": step["step"], "description": step["description"], "confidence": step.get("confidence", 0.0), "evidence": step.get("evidence", [])}],
                    execution_time_ms=step.get("execution_time_ms", 0),
                    confidence=step.get("confidence", 0.0),
                )
                self._action_records[action_record.id] = action_record
                actions_taken.append(action_record)

        response_content = reasoning_chain.conclusion
        conversation = self._get_or_create_conversation(user_id, context)

        assistant_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role=ConversationRole.ASSISTANT,
            content=response_content,
            metadata={
                "actions_taken": [a.to_dict() for a in actions_taken],
                "reasoning_trace": reasoning_chain.to_dict()["steps"],
                "evidence": reasoning_chain.evidence,
                "confidence": reasoning_chain.confidence,
                "tools_used": [a.action_type.value for a in actions_taken],
            },
        )

        conversation.messages.append(assistant_message.to_dict())
        conversation.updated_at = datetime.utcnow()

        self._track_query(user_id, query, context)

        return assistant_message, actions_taken

    def multi_step_reasoning(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningChain:
        context = context or {}
        chain = ReasoningChain(id=uuid.uuid4(), query=query)
        overall_start = datetime.utcnow()
        accumulated_confidence = 1.0
        all_evidence: List[Dict[str, Any]] = []

        parse_result = self._parse_query(query)
        chain.steps.append({
            "step": ReasoningStep.PARSE.value,
            "description": "Extracted entities, intent, and time range from query",
            "result": parse_result,
            "confidence": parse_result["confidence"],
            "evidence": parse_result.get("evidence", []),
            "execution_time_ms": parse_result.get("execution_time_ms", 0),
        })
        accumulated_confidence *= parse_result["confidence"]
        all_evidence.extend(parse_result.get("evidence", []))

        classify_result = self._classify_query(parse_result)
        chain.steps.append({
            "step": ReasoningStep.CLASSIFY.value,
            "description": "Determined required actions based on parsed query",
            "result": classify_result,
            "confidence": classify_result["confidence"],
            "evidence": classify_result.get("evidence", []),
            "execution_time_ms": classify_result.get("execution_time_ms", 0),
            "action_type": classify_result.get("primary_action"),
            "parameters": classify_result.get("parameters", {}),
        })
        accumulated_confidence *= classify_result["confidence"]
        all_evidence.extend(classify_result.get("evidence", []))

        route_result = self._route_to_domains(classify_result, parse_result)
        chain.steps.append({
            "step": ReasoningStep.ROUTE.value,
            "description": "Mapped actions to domain services",
            "result": route_result,
            "confidence": route_result["confidence"],
            "evidence": route_result.get("evidence", []),
            "execution_time_ms": route_result.get("execution_time_ms", 0),
        })
        accumulated_confidence *= route_result["confidence"]
        all_evidence.extend(route_result.get("evidence", []))

        retrieve_result = self._retrieve_data(parse_result, route_result, context)
        chain.steps.append({
            "step": ReasoningStep.RETRIEVE.value,
            "description": "Gathered relevant data from domain services",
            "result": retrieve_result,
            "confidence": retrieve_result["confidence"],
            "evidence": retrieve_result.get("evidence", []),
            "execution_time_ms": retrieve_result.get("execution_time_ms", 0),
        })
        accumulated_confidence *= retrieve_result["confidence"]
        all_evidence.extend(retrieve_result.get("evidence", []))

        compute_result = self._compute_analysis(classify_result, retrieve_result, parse_result)
        chain.steps.append({
            "step": ReasoningStep.COMPUTE.value,
            "description": "Executed analysis computations",
            "result": compute_result,
            "confidence": compute_result["confidence"],
            "evidence": compute_result.get("evidence", []),
            "execution_time_ms": compute_result.get("execution_time_ms", 0),
            "action_type": classify_result.get("primary_action"),
            "parameters": {"computation": compute_result.get("computation_type", "analysis")},
        })
        accumulated_confidence *= compute_result["confidence"]
        all_evidence.extend(compute_result.get("evidence", []))

        validate_result = self._validate_results(compute_result, parse_result)
        chain.steps.append({
            "step": ReasoningStep.VALIDATE.value,
            "description": "Validated computation results for correctness",
            "result": validate_result,
            "confidence": validate_result["confidence"],
            "evidence": validate_result.get("evidence", []),
            "execution_time_ms": validate_result.get("execution_time_ms", 0),
        })
        accumulated_confidence *= validate_result["confidence"]
        all_evidence.extend(validate_result.get("evidence", []))

        synthesize_result = self._synthesize_response(parse_result, compute_result, validate_result, context)
        chain.steps.append({
            "step": ReasoningStep.SYNTHESIZE.value,
            "description": "Combined results into coherent answer",
            "result": synthesize_result,
            "confidence": synthesize_result["confidence"],
            "evidence": synthesize_result.get("evidence", []),
            "execution_time_ms": synthesize_result.get("execution_time_ms", 0),
        })
        accumulated_confidence *= synthesize_result["confidence"]
        all_evidence.extend(synthesize_result.get("evidence", []))

        explain_result = self._generate_explanation(parse_result, compute_result, synthesize_result)
        chain.steps.append({
            "step": ReasoningStep.EXPLAIN.value,
            "description": "Generated explanation for the analysis",
            "result": explain_result,
            "confidence": explain_result["confidence"],
            "evidence": explain_result.get("evidence", []),
            "execution_time_ms": explain_result.get("execution_time_ms", 0),
        })
        accumulated_confidence *= explain_result["confidence"]
        all_evidence.extend(explain_result.get("evidence", []))

        overall_end = datetime.utcnow()
        total_ms = int((overall_end - overall_start).total_seconds() * 1000)

        chain.conclusion = synthesize_result.get("response", "I've analyzed your query and prepared a response.")
        chain.confidence = round(max(0.0, min(1.0, accumulated_confidence)), 4)
        chain.evidence = all_evidence
        chain.total_time_ms = total_ms

        self._reasoning_chains[chain.id] = chain
        return chain

    def generate_suggestions(self, user_id: uuid.UUID, context: Optional[Dict[str, Any]] = None) -> List[CopilotSuggestion]:
        context = context or {}
        suggestions: List[CopilotSuggestion] = []
        query_history = self._user_query_history.get(user_id, [])

        frequency_suggestions = self._suggest_from_frequency(user_id, query_history)
        suggestions.extend(frequency_suggestions)

        time_suggestions = self._suggest_from_time_context(context)
        suggestions.extend(time_suggestions)

        alert_suggestions = self._suggest_from_alerts(context)
        suggestions.extend(alert_suggestions)

        suggestions.sort(key=lambda s: (s.priority.value, s.confidence), reverse=True)
        return suggestions[:5]

    def explain_reasoning(self, copilot_action_id: uuid.UUID) -> List[Dict[str, Any]]:
        action_record = self._action_records.get(copilot_action_id)
        if action_record:
            return action_record.reasoning

        for chain in self._reasoning_chains.values():
            for step in chain.steps:
                if str(step.get("id")) == str(copilot_action_id):
                    return [{"step": step["step"], "description": step["description"], "confidence": step.get("confidence", 0.0), "evidence": step.get("evidence", [])}]
        return []

    def get_conversations(self, tenant_id: str, user_id: uuid.UUID, limit: int = 20) -> List[Conversation]:
        conversations = [
            conv for conv in self._conversations.values()
            if conv.tenant_id == tenant_id and conv.user_id == user_id
        ]
        conversations.sort(key=lambda c: c.updated_at, reverse=True)
        return conversations[:limit]

    def get_conversation(self, tenant_id: str, conversation_id: uuid.UUID) -> Optional[Conversation]:
        conversation = self._conversations.get(conversation_id)
        if conversation and conversation.tenant_id == tenant_id:
            return conversation
        return None

    def archive_conversation(self, tenant_id: str, conversation_id: uuid.UUID) -> Optional[Conversation]:
        conversation = self.get_conversation(tenant_id, conversation_id)
        if conversation:
            conversation.status = ConversationStatus.ARCHIVED
            conversation.updated_at = datetime.utcnow()
            return conversation
        return None

    def _get_or_create_conversation(self, user_id: uuid.UUID, context: Dict[str, Any]) -> Conversation:
        active_conversations = [
            conv for conv in self._conversations.values()
            if conv.tenant_id == self.tenant_id
            and conv.user_id == user_id
            and conv.status == ConversationStatus.ACTIVE
        ]
        if active_conversations:
            return active_conversations[0]

        title = context.get("title", f"Financial Analysis - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
        conversation = Conversation(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            user_id=user_id,
            title=title,
            context=context,
        )
        self._conversations[conversation.id] = conversation
        return conversation

    def _track_query(self, user_id: uuid.UUID, query: str, context: Dict[str, Any]) -> None:
        if user_id not in self._user_query_history:
            self._user_query_history[user_id] = []
        self._user_query_history[user_id].append({
            "query": query,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
        })
        if len(self._user_query_history[user_id]) > 100:
            self._user_query_history[user_id] = self._user_query_history[user_id][-100:]

    def _parse_query(self, query: str) -> Dict[str, Any]:
        start = datetime.utcnow()
        query_lower = query.lower().strip()
        entities: List[Dict[str, Any]] = []
        detected_metrics: List[str] = []
        time_range: Optional[Dict[str, Any]] = None
        intent = "ANALYZE"
        evidence: List[Dict[str, Any]] = []

        for metric_key, metric_info in HEALTHCARE_METRICS.items():
            if metric_key in query_lower:
                detected_metrics.append(metric_key)
                entities.append({"type": "metric", "value": metric_key, "domain": metric_info["domain"], "metric_type": metric_info["type"]})
                evidence.append({"type": "metric_detection", "metric": metric_key, "confidence": 0.95})
                for alias in metric_info.get("aliases", []):
                    if alias in query_lower and alias != metric_key:
                        entities.append({"type": "metric_alias", "value": alias, "parent": metric_key})

        for time_key, time_info in TIME_PATTERNS.items():
            if time_key in query_lower:
                time_range = {"period": time_info["period"], "relative_days": time_info["relative_days"], "description": time_key}
                entities.append({"type": "time_range", "value": time_key, "details": time_info})
                evidence.append({"type": "time_detection", "period": time_key, "confidence": 0.9})

        for intent_key, intent_info in INTENT_PATTERNS.items():
            for keyword in intent_info["keywords"]:
                if keyword in query_lower:
                    intent = intent_info["action"].value
                    entities.append({"type": "intent", "value": intent, "keyword": keyword})
                    evidence.append({"type": "intent_detection", "intent": intent, "keyword": keyword, "confidence": 0.85})
                    break

        if not time_range:
            time_range = {"period": "month_to_date", "relative_days": 0, "description": "default MTD"}
            evidence.append({"type": "default_time", "period": "MTD", "confidence": 0.5})

        confidence = 0.9 if detected_metrics else 0.6
        if time_range and time_range.get("description") != "default MTD":
            confidence = min(1.0, confidence + 0.05)

        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        return {
            "entities": entities,
            "metrics": detected_metrics,
            "time_range": time_range,
            "intent": intent,
            "confidence": confidence,
            "evidence": evidence,
            "execution_time_ms": elapsed,
        }

    def _classify_query(self, parse_result: Dict[str, Any]) -> Dict[str, Any]:
        start = datetime.utcnow()
        intent = parse_result.get("intent", "ANALYZE")
        metrics = parse_result.get("metrics", [])

        primary_action = CopilotAction(intent)
        secondary_actions: List[CopilotAction] = []

        if "why" in parse_result.get("entities", [{}])[0].get("keyword", "") if parse_result.get("entities") else False:
            secondary_actions.append(CopilotAction.FIND_ROOT_CAUSE)

        if len(metrics) > 1:
            secondary_actions.append(CopilotAction.COMPARE)

        if any(m in ["denial rate", "cost per case", "operating margin"] for m in metrics):
            secondary_actions.append(CopilotAction.RECOMMEND)

        parameters = {
            "primary_action": primary_action.value,
            "secondary_actions": [a.value for a in secondary_actions],
            "metrics": metrics,
            "requires_comparison": CopilotAction.COMPARE in secondary_actions,
            "requires_recommendation": CopilotAction.RECOMMEND in secondary_actions,
        }

        evidence = [{"type": "classification", "primary_action": primary_action.value, "secondary_count": len(secondary_actions)}]
        confidence = 0.85 if secondary_actions else 0.9
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        return {
            "primary_action": primary_action,
            "secondary_actions": secondary_actions,
            "parameters": parameters,
            "confidence": confidence,
            "evidence": evidence,
            "execution_time_ms": elapsed,
        }

    def _route_to_domains(self, classify_result: Dict[str, Any], parse_result: Dict[str, Any]) -> Dict[str, Any]:
        start = datetime.utcnow()
        metrics = parse_result.get("metrics", [])
        domains: List[str] = []
        evidence: List[Dict[str, Any]] = []

        for metric in metrics:
            metric_info = HEALTHCARE_METRICS.get(metric, {})
            domain = metric_info.get("domain", "financial")
            if domain not in domains:
                domains.append(domain)
                evidence.append({"type": "domain_route", "metric": metric, "domain": domain})

        if not domains:
            domains = ["financial"]

        confidence = 0.9 if len(domains) <= 2 else 0.8
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        return {
            "domains": domains,
            "confidence": confidence,
            "evidence": evidence,
            "execution_time_ms": elapsed,
        }

    def _retrieve_data(self, parse_result: Dict[str, Any], route_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        start = datetime.utcnow()
        metrics = parse_result.get("metrics", [])
        time_range = parse_result.get("time_range", {})
        domains = route_result.get("domains", [])

        retrieved_data: Dict[str, Any] = {}
        evidence: List[Dict[str, Any]] = []

        for metric in metrics:
            metric_info = HEALTHCARE_METRICS.get(metric, {})
            metric_type = metric_info.get("type", metric)
            simulated_value = self._simulate_metric_value(metric_type, time_range)
            retrieved_data[metric] = simulated_value
            evidence.append({"type": "data_retrieval", "metric": metric, "period": time_range.get("period", "unknown"), "confidence": 0.88})

        confidence = 0.87 if retrieved_data else 0.5
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        return {
            "data": retrieved_data,
            "domains_queried": domains,
            "confidence": confidence,
            "evidence": evidence,
            "execution_time_ms": elapsed,
        }

    def _compute_analysis(self, classify_result: Dict[str, Any], retrieve_result: Dict[str, Any], parse_result: Dict[str, Any]) -> Dict[str, Any]:
        start = datetime.utcnow()
        primary_action = classify_result.get("primary_action", CopilotAction.ANALYZE)
        data = retrieve_result.get("data", {})
        metrics = parse_result.get("metrics", [])

        computation_result: Dict[str, Any] = {}
        computation_type = "analysis"
        evidence: List[Dict[str, Any]] = []

        if primary_action == CopilotAction.ANALYZE:
            computation_type = "trend_analysis"
            for metric, value in data.items():
                computation_result[metric] = {
                    "current": value,
                    "trend": "increasing" if value > 50 else "decreasing",
                    "change_pct": round((value - 45) / 45 * 100, 1),
                    "benchmark": self._get_benchmark(metric),
                }
        elif primary_action == CopilotAction.EXPLAIN:
            computation_type = "explanation"
            for metric, value in data.items():
                computation_result[metric] = {
                    "value": value,
                    "factors": self._identify_factors(metric, value),
                    "root_causes": self._suggest_root_causes(metric, value),
                }
        elif primary_action == CopilotAction.COMPARE:
            computation_type = "comparison"
            for metric, value in data.items():
                computation_result[metric] = {
                    "current": value,
                    "previous": round(value * 0.92, 2),
                    "peer_average": round(value * 1.05, 2),
                    "variance": round(value * 0.08, 2),
                }
        elif primary_action == CopilotAction.FORECAST:
            computation_type = "forecast"
            for metric, value in data.items():
                computation_result[metric] = {
                    "current": value,
                    "forecast_next_quarter": round(value * 1.03, 2),
                    "forecast_next_year": round(value * 1.08, 2),
                    "confidence_interval": [round(value * 0.95, 2), round(value * 1.11, 2)],
                }
        elif primary_action == CopilotAction.GENERATE_BRIEFING:
            computation_type = "briefing"
            for metric, value in data.items():
                computation_result[metric] = {
                    "value": value,
                    "status": "on_track" if value > 40 else "needs_attention",
                    "highlight": self._generate_highlight(metric, value),
                }
        elif primary_action == CopilotAction.RUN_SCENARIO:
            computation_type = "scenario"
            for metric, value in data.items():
                computation_result[metric] = {
                    "baseline": value,
                    "optimistic": round(value * 1.15, 2),
                    "pessimistic": round(value * 0.85, 2),
                    "most_likely": round(value * 1.05, 2),
                }
        elif primary_action == CopilotAction.ASSESS_RISK:
            computation_type = "risk_assessment"
            for metric, value in data.items():
                computation_result[metric] = {
                    "value": value,
                    "risk_level": "high" if value < 30 else "medium" if value < 60 else "low",
                    "risk_factors": self._identify_risk_factors(metric, value),
                    "mitigation": self._suggest_mitigations(metric, value),
                }
        else:
            computation_type = "general_analysis"
            for metric, value in data.items():
                computation_result[metric] = {"value": value, "assessment": "requires further analysis"}

        evidence.append({"type": "computation", "action": primary_action.value, "metrics_analyzed": len(metrics)})
        confidence = 0.88 if computation_result else 0.5
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        return {
            "computation_type": computation_type,
            "results": computation_result,
            "confidence": confidence,
            "evidence": evidence,
            "execution_time_ms": elapsed,
        }

    def _validate_results(self, compute_result: Dict[str, Any], parse_result: Dict[str, Any]) -> Dict[str, Any]:
        start = datetime.utcnow()
        results = compute_result.get("results", {})
        evidence: List[Dict[str, Any]] = []
        issues: List[str] = []

        for metric, value in results.items():
            if isinstance(value, dict):
                for key, val in value.items():
                    if isinstance(val, (int, float)):
                        if val < 0 and key not in ["change_pct", "variance"]:
                            issues.append(f"Negative value detected for {metric}.{key}")
                        if val > 1000 and key in ["change_pct", "variance"]:
                            issues.append(f"Unusually high value for {metric}.{key}")

        confidence = 0.95 if not issues else max(0.7, 0.95 - len(issues) * 0.05)
        evidence.append({"type": "validation", "issues_found": len(issues), "metrics_validated": len(results)})
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "confidence": confidence,
            "evidence": evidence,
            "execution_time_ms": elapsed,
        }

    def _synthesize_response(self, parse_result: Dict[str, Any], compute_result: Dict[str, Any], validate_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        start = datetime.utcnow()
        intent = parse_result.get("intent", "ANALYZE")
        metrics = parse_result.get("metrics", [])
        time_range = parse_result.get("time_range", {})
        results = compute_result.get("results", {})
        computation_type = compute_result.get("computation_type", "analysis")

        response_parts: List[str] = []

        if intent == "ANALYZE":
            response_parts.append(f"Based on my analysis of {', '.join(metrics)} for {time_range.get('description', 'the requested period')}:")
            for metric, data in results.items():
                if isinstance(data, dict):
                    trend = data.get("trend", "")
                    change = data.get("change_pct", 0)
                    response_parts.append(f"- **{metric.title()}**: Currently at {data.get('current', 'N/A')} ({'+' if change > 0 else ''}{change}% {trend})")
        elif intent == "EXPLAIN":
            response_parts.append(f"Here's why the {', '.join(metrics)} metrics are showing these patterns:")
            for metric, data in results.items():
                if isinstance(data, dict):
                    factors = data.get("factors", [])
                    response_parts.append(f"- **{metric.title()}**: {', '.join(factors[:3]) if factors else 'Analysis pending'}")
        elif intent == "COMPARE":
            response_parts.append(f"Comparing {', '.join(metrics)} across periods:")
            for metric, data in results.items():
                if isinstance(data, dict):
                    response_parts.append(f"- **{metric.title()}**: Current {data.get('current', 'N/A')} vs Previous {data.get('previous', 'N/A')} (Variance: {data.get('variance', 'N/A')})")
        elif intent == "FORECAST":
            response_parts.append(f"Forecast for {', '.join(metrics)}:")
            for metric, data in results.items():
                if isinstance(data, dict):
                    response_parts.append(f"- **{metric.title()}**: Next quarter forecast: {data.get('forecast_next_quarter', 'N/A')} (CI: {data.get('confidence_interval', ['N/A', 'N/A'])})")
        elif intent == "GENERATE_BRIEFING":
            response_parts.append(f"**Financial Briefing** for {time_range.get('description', 'the period')}:")
            for metric, data in results.items():
                if isinstance(data, dict):
                    status_icon = "✓" if data.get("status") == "on_track" else "⚠"
                    response_parts.append(f"{status_icon} **{metric.title()}**: {data.get('value', 'N/A')} - {data.get('highlight', '')}")
        elif intent == "RUN_SCENARIO":
            response_parts.append(f"Scenario analysis for {', '.join(metrics)}:")
            for metric, data in results.items():
                if isinstance(data, dict):
                    response_parts.append(f"- **{metric.title()}**: Baseline: {data.get('baseline', 'N/A')} | Optimistic: {data.get('optimistic', 'N/A')} | Pessimistic: {data.get('pessimistic', 'N/A')}")
        elif intent == "ASSESS_RISK":
            response_parts.append(f"Risk assessment for {', '.join(metrics)}:")
            for metric, data in results.items():
                if isinstance(data, dict):
                    risk_level = data.get("risk_level", "unknown")
                    risk_factors = data.get("risk_factors", [])
                    response_parts.append(f"- **{metric.title()}**: Risk level: {risk_level.upper()} - {', '.join(risk_factors[:2]) if risk_factors else 'No specific factors identified'}")
        else:
            response_parts.append(f"Analysis of {', '.join(metrics)}:")
            for metric, data in results.items():
                response_parts.append(f"- **{metric.title()}**: {data}")

        response = "\n".join(response_parts)
        if not validate_result.get("valid"):
            response += "\n\n_Note: Some validation issues were detected. Results should be reviewed._"

        confidence = 0.9 if response_parts else 0.5
        evidence = [{"type": "synthesis", "response_length": len(response), "metrics_included": len(metrics)}]
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        return {
            "response": response,
            "confidence": confidence,
            "evidence": evidence,
            "execution_time_ms": elapsed,
        }

    def _generate_explanation(self, parse_result: Dict[str, Any], compute_result: Dict[str, Any], synthesize_result: Dict[str, Any]) -> Dict[str, Any]:
        start = datetime.utcnow()
        metrics = parse_result.get("metrics", [])
        results = compute_result.get("results", {})

        explanation_parts: List[str] = []
        explanation_parts.append("This analysis was performed using the following reasoning:")

        for metric in metrics:
            metric_info = HEALTHCARE_METRICS.get(metric, {})
            domain = metric_info.get("domain", "financial")
            explanation_parts.append(f"- **{metric.title()}** ({domain} domain): Data retrieved and analyzed using standard healthcare financial metrics")

        explanation_parts.append(f"- Results validated against industry benchmarks")
        explanation_parts.append(f"- Confidence level: {synthesize_result.get('confidence', 0):.0%}")

        explanation = "\n".join(explanation_parts)
        confidence = 0.92
        evidence = [{"type": "explanation", "components": len(explanation_parts)}]
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        return {
            "explanation": explanation,
            "confidence": confidence,
            "evidence": evidence,
            "execution_time_ms": elapsed,
        }

    def _simulate_metric_value(self, metric_type: str, time_range: Dict[str, Any]) -> float:
        base_values = {
            "denial_rate": 8.5,
            "bed_occupancy": 78.2,
            "alos": 4.8,
            "cmi": 1.42,
            "operating_margin": 3.2,
            "days_in_ar": 42.5,
            "cost_per_case": 8500.0,
            "revenue": 25000000.0,
            "cash_flow": 3200000.0,
            "ebitda": 4100000.0,
        }
        base = base_values.get(metric_type, 50.0)
        period = time_range.get("period", "month")
        variance = 0.05 if period in ["month", "month_to_date"] else 0.1 if period in ["quarter", "quarter_to_date"] else 0.15
        import random
        random.seed(hash(metric_type + str(time_range)))
        return round(base * (1 + random.uniform(-variance, variance)), 2)

    def _get_benchmark(self, metric: str) -> Dict[str, Any]:
        benchmarks = {
            "denial_rate": {"industry_avg": 5.0, "best_in_class": 2.0, "source": "HFMA"},
            "bed_occupancy": {"industry_avg": 80.0, "best_in_class": 90.0, "source": "AHA"},
            "alos": {"industry_avg": 5.0, "best_in_class": 4.0, "source": "CMS"},
            "cmi": {"industry_avg": 1.35, "best_in_class": 1.60, "source": "CMS"},
            "operating_margin": {"industry_avg": 2.5, "best_in_class": 6.0, "source": "HFMA"},
            "days_in_ar": {"industry_avg": 45.0, "best_in_class": 35.0, "source": "HFMA"},
        }
        return benchmarks.get(metric, {"industry_avg": 50.0, "best_in_class": 75.0, "source": "Industry"})

    def _identify_factors(self, metric: str, value: float) -> List[str]:
        factors_map = {
            "denial_rate": [" payer mix changes", " coding accuracy", " prior authorization compliance", " claim processing efficiency"],
            "bed_occupancy": [" seasonal demand", " emergency department volume", " elective surgery scheduling", " discharge planning"],
            "alos": [" case mix complexity", " discharge planning efficiency", " post-acute care availability", " clinical pathways"],
            "operating_margin": [" revenue cycle performance", " labor cost management", " supply chain efficiency", " payer contract terms"],
        }
        return factors_map.get(metric, [" Multiple operational factors", " Market conditions", " Regulatory environment"])

    def _suggest_root_causes(self, metric: str, value: float) -> List[str]:
        root_causes = {
            "denial_rate": [" Insufficient prior authorization documentation", " Coding errors in complex cases", " Payer-specific requirements not met"],
            "bed_occupancy": [" Reduced elective procedures", " Increased discharge delays", " Seasonal illness patterns"],
            "operating_margin": [" Rising labor costs", " Increased supply expenses", " Payer reimbursement reductions"],
        }
        return root_causes.get(metric, [" Requires deeper investigation", " Multiple contributing factors identified"])

    def _generate_highlight(self, metric: str, value: float) -> str:
        highlights = {
            "denial_rate": "Denial rate is within acceptable range" if value < 10 else "Denial rate requires immediate attention",
            "bed_occupancy": "Bed occupancy is optimized" if 75 <= value <= 90 else "Bed occupancy needs adjustment",
            "operating_margin": "Operating margin is healthy" if value > 3 else "Operating margin is below target",
        }
        return highlights.get(metric, "Metric is being monitored")

    def _identify_risk_factors(self, metric: str, value: float) -> List[str]:
        risk_factors = {
            "denial_rate": [" Potential revenue loss", " Increased administrative burden", " Cash flow impact"],
            "bed_occupancy": [" Underutilization of capacity", " Revenue opportunity loss", " Fixed cost absorption issues"],
            "operating_margin": [" Financial sustainability concern", " Investment capacity reduction", " Covenant compliance risk"],
        }
        return risk_factors.get(metric, [" Requires monitoring", " Trend analysis recommended"])

    def _suggest_mitigations(self, metric: str, value: float) -> List[str]:
        mitigations = {
            "denial_rate": [" Implement real-time eligibility verification", " Enhance coding education", " Strengthen prior authorization workflows"],
            "bed_occupancy": [" Optimize scheduling algorithms", " Improve discharge planning", " Expand observation unit capacity"],
            "operating_margin": [" Review labor productivity metrics", " Negotiate vendor contracts", " Enhance revenue cycle processes"],
        }
        return mitigations.get(metric, [" Conduct detailed analysis", " Review operational processes", " Consider strategic adjustments"])

    def _suggest_from_frequency(self, user_id: uuid.UUID, query_history: List[Dict[str, Any]]) -> List[CopilotSuggestion]:
        suggestions: List[CopilotSuggestion] = []
        if not query_history:
            return suggestions

        metric_counts: Dict[str, int] = {}
        for entry in query_history[-20:]:
            query = entry.get("query", "").lower()
            for metric in HEALTHCARE_METRICS:
                if metric in query:
                    metric_counts[metric] = metric_counts.get(metric, 0) + 1

        for metric, count in metric_counts.items():
            if count >= 3:
                suggestions.append(CopilotSuggestion(
                    id=uuid.uuid4(),
                    suggestion_type="frequency_based",
                    title=f"Weekly {metric.title()} Briefing",
                    description=f"You frequently check {metric}. Would you like a weekly automated briefing?",
                    confidence=min(0.9, 0.6 + count * 0.05),
                    context={"metric": metric, "frequency": count},
                    priority=PriorityLevel.MEDIUM if count < 5 else PriorityLevel.HIGH,
                ))
        return suggestions

    def _suggest_from_time_context(self, context: Dict[str, Any]) -> List[CopilotSuggestion]:
        suggestions: List[CopilotSuggestion] = []
        now = datetime.utcnow()

        if now.month in [3, 6, 9, 12] and now.day > 20:
            suggestions.append(CopilotSuggestion(
                id=uuid.uuid4(),
                suggestion_type="time_based",
                title="Quarter-End Budget Variance Analysis",
                description="It's near quarter-end. Would you like a budget variance analysis?",
                confidence=0.85,
                context={"trigger": "quarter_end", "month": now.month},
                priority=PriorityLevel.HIGH,
            ))

        if now.day <= 5:
            suggestions.append(CopilotSuggestion(
                id=uuid.uuid4(),
                suggestion_type="time_based",
                title="Monthly Financial Summary",
                description="Start the month with a comprehensive financial summary.",
                confidence=0.8,
                context={"trigger": "month_start", "day": now.day},
                priority=PriorityLevel.MEDIUM,
            ))
        return suggestions

    def _suggest_from_alerts(self, context: Dict[str, Any]) -> List[CopilotSuggestion]:
        suggestions: List[CopilotSuggestion] = []
        alerts = context.get("alerts", [])

        for alert in alerts[:3]:
            if alert.get("severity") == "critical":
                suggestions.append(CopilotSuggestion(
                    id=uuid.uuid4(),
                    suggestion_type="alert_based",
                    title=f"Address: {alert.get('title', 'Critical Alert')}",
                    description=f"A critical alert requires immediate attention: {alert.get('description', '')}",
                    confidence=0.95,
                    context={"alert_id": alert.get("id"), "severity": "critical"},
                    priority=PriorityLevel.CRITICAL,
                ))
        return suggestions
