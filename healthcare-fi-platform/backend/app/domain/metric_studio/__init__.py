from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

class MetricCategory(Enum):
    REVENUE = "revenue"
    COST = "cost"
    OPERATIONS = "operations"
    QUALITY = "quality"
    PATIENT = "patient"
    FINANCIAL = "financial"
    WORKFORCE = "workforce"
    SUPPLY_CHAIN = "supply_chain"

class MetricStatus(Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    CERTIFIED = "certified"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class ChangeType(Enum):
    CREATED = "created"
    FORMULA_CHANGED = "formula_changed"
    METADATA_CHANGED = "metadata_changed"
    CERTIFIED = "certified"
    DEPRECATED = "deprecated"
    RESTORED = "restored"

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class StepStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"

@dataclass
class Metric:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    category: MetricCategory = MetricCategory.FINANCIAL
    description: str = ""
    formula_id: Optional[UUID] = None
    unit: str = ""
    format_pattern: str = "#,##0"
    decimal_places: int = 2
    aggregation_default: str = "sum"
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    status: MetricStatus = MetricStatus.DRAFT
    is_certified: bool = False
    certified_by: Optional[UUID] = None
    certified_at: Optional[datetime] = None
    certification_expires_at: Optional[date] = None
    review_frequency: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    owner_id: UUID = field(default_factory=uuid4)
    steward_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    default_time_range: str = "current_month"
    default_filters: list[dict] = field(default_factory=list)
    default_dimensions: list[str] = field(default_factory=list)
    deprecated_at: Optional[datetime] = None

    def publish(self):
        if self.status != MetricStatus.DRAFT and self.status != MetricStatus.PENDING_REVIEW:
            raise ValueError(f"Cannot publish from {self.status.value}")
        self.status = MetricStatus.PUBLISHED

    def request_certification(self):
        if self.status != MetricStatus.PUBLISHED:
            raise ValueError("Must be published before certification")
        self.status = MetricStatus.PENDING_REVIEW

    def certify(self, certifier_id: UUID, expires_at: Optional[date] = None):
        if self.status != MetricStatus.PENDING_REVIEW:
            raise ValueError("Must be pending review to certify")
        self.status = MetricStatus.CERTIFIED
        self.is_certified = True
        self.certified_by = certifier_id
        self.certified_at = datetime.utcnow()
        self.certification_expires_at = expires_at

    def deprecate(self):
        if self.status in (MetricStatus.ARCHIVED, MetricStatus.DEPRECATED):
            raise ValueError(f"Cannot deprecate from {self.status.value}")
        self.status = MetricStatus.DEPRECATED
        self.deprecated_at = datetime.utcnow()

    def is_expired(self) -> bool:
        if self.certification_expires_at is None:
            return False
        return date.today() > self.certification_expires_at

@dataclass
class MetricVersion:
    id: UUID = field(default_factory=uuid4)
    metric_id: UUID = field(default_factory=uuid4)
    version: int = 1
    snapshot: Optional[Metric] = None
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    change_type: ChangeType = ChangeType.CREATED
    change_summary: str = ""
    is_current: bool = True

@dataclass
class ApprovalStep:
    step_order: int = 1
    approver_role: str = ""
    approver_id: Optional[UUID] = None
    status: StepStatus = StepStatus.PENDING
    decided_by: Optional[UUID] = None
    decided_at: Optional[datetime] = None
    note: Optional[str] = None

@dataclass
class MetricApprovalWorkflow:
    id: UUID = field(default_factory=uuid4)
    metric_id: UUID = field(default_factory=uuid4)
    status: ApprovalStatus = ApprovalStatus.PENDING
    steps: list[ApprovalStep] = field(default_factory=list)
    current_step: int = 0
    requested_by: UUID = field(default_factory=uuid4)
    requested_at: datetime = field(default_factory=datetime.utcnow)

    def approve_step(self, step_index: int, approver_id: UUID, note: Optional[str] = None):
        if step_index >= len(self.steps):
            raise IndexError("Step index out of range")
        step = self.steps[step_index]
        if step.status != StepStatus.PENDING:
            raise ValueError(f"Step {step_index} already {step.status.value}")
        step.status = StepStatus.APPROVED
        step.decided_by = approver_id
        step.decided_at = datetime.utcnow()
        step.note = note
        if step_index == len(self.steps) - 1:
            self.status = ApprovalStatus.APPROVED

    def reject_step(self, step_index: int, approver_id: UUID, note: Optional[str] = None):
        if step_index >= len(self.steps):
            raise IndexError("Step index out of range")
        step = self.steps[step_index]
        step.status = StepStatus.REJECTED
        step.decided_by = approver_id
        step.decided_at = datetime.utcnow()
        step.note = note
        self.status = ApprovalStatus.REJECTED

@dataclass
class MetricDependencyGraph:
    nodes: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)
    cycles: list[list[UUID]] = field(default_factory=list)

    def add_node(self, metric_id: UUID, name: str, formula_id: Optional[UUID] = None):
        self.nodes.append({"id": metric_id, "name": name, "formula_id": formula_id})

    def add_edge(self, source_id: UUID, target_id: UUID, relationship: str = "depends_on"):
        self.edges.append({"source": source_id, "target": target_id, "relationship": relationship})

    def detect_cycles(self) -> list[list[UUID]]:
        visited = set()
        path = []
        cycles = []

        def dfs(node):
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            for edge in self.edges:
                if edge["source"] == node:
                    dfs(edge["target"])
            path.pop()

        for node in self.nodes:
            dfs(node["id"])
        self.cycles = cycles
        return cycles

    def get_upstream(self, metric_id: UUID) -> list[UUID]:
        upstream = []
        for edge in self.edges:
            if edge["target"] == metric_id:
                upstream.append(edge["source"])
        return upstream

    def get_downstream(self, metric_id: UUID) -> list[UUID]:
        downstream = []
        for edge in self.edges:
            if edge["source"] == metric_id:
                downstream.append(edge["target"])
        return downstream

    def get_root_metrics(self) -> list[UUID]:
        targets = {e["target"] for e in self.edges}
        return [n["id"] for n in self.nodes if n["id"] not in targets]

@dataclass
class MetricImpactAnalysis:
    metric_id: UUID = field(default_factory=uuid4)
    affected_metrics: list[dict] = field(default_factory=list)
    affected_dashboards: list[dict] = field(default_factory=list)
    affected_reports: list[dict] = field(default_factory=list)
    total_impact_score: int = 0

    def calculate_score(self):
        self.total_impact_score = (
            len(self.affected_metrics) * 3 +
            len(self.affected_dashboards) * 2 +
            len(self.affected_reports) * 1
        )

class MetricStudioService:
    def __init__(self):
        self.metrics: dict[UUID, Metric] = {}
        self.versions: dict[UUID, list[MetricVersion]] = {}
        self.workflows: dict[UUID, MetricApprovalWorkflow] = {}
        self.graph = MetricDependencyGraph()

    def create_metric(self, **kwargs) -> Metric:
        metric = Metric(**kwargs)
        self.metrics[metric.id] = metric
        version = MetricVersion(metric_id=metric.id, version=1, snapshot=metric, change_type=ChangeType.CREATED)
        self.versions.setdefault(metric.id, []).append(version)
        self.graph.add_node(metric.id, metric.name, metric.formula_id)
        return metric

    def get_metric(self, metric_id: UUID) -> Optional[Metric]:
        return self.metrics.get(metric_id)

    def update_metric(self, metric_id: UUID, **kwargs) -> Metric:
        metric = self.metrics.get(metric_id)
        if not metric:
            raise KeyError(f"Metric {metric_id} not found")
        for k, v in kwargs.items():
            if hasattr(metric, k):
                setattr(metric, k, v)
        metric.version += 1
        version = MetricVersion(
            metric_id=metric_id, version=metric.version, snapshot=metric,
            change_type=ChangeType.METADATA_CHANGED, change_summary=f"Updated {list(kwargs.keys())}"
        )
        self.versions.setdefault(metric_id, []).append(version)
        return metric

    def publish_metric(self, metric_id: UUID) -> Metric:
        metric = self.metrics[metric_id]
        metric.publish()
        return metric

    def request_certification(self, metric_id: UUID, requested_by: UUID, steps: list[ApprovalStep]) -> MetricApprovalWorkflow:
        metric = self.metrics[metric_id]
        metric.request_certification()
        workflow = MetricApprovalWorkflow(metric_id=metric_id, requested_by=requested_by, steps=steps)
        self.workflows[workflow.id] = workflow
        return workflow

    def certify_metric(self, metric_id: UUID, certifier_id: UUID) -> Metric:
        metric = self.metrics[metric_id]
        metric.certify(certifier_id)
        version = MetricVersion(
            metric_id=metric_id, version=metric.version, snapshot=metric,
            change_type=ChangeType.CERTIFIED, change_summary=f"Certified by {certifier_id}"
        )
        self.versions.setdefault(metric_id, []).append(version)
        return metric

    def deprecate_metric(self, metric_id: UUID) -> Metric:
        metric = self.metrics[metric_id]
        metric.deprecate()
        return metric

    def rollback_metric(self, metric_id: UUID, target_version: int) -> Metric:
        versions = self.versions.get(metric_id, [])
        target = next((v for v in versions if v.version == target_version), None)
        if not target or not target.snapshot:
            raise ValueError(f"Version {target_version} not found")
        metric = self.metrics[metric_id]
        metric.status = target.snapshot.status
        metric.version += 1
        rollback_version = MetricVersion(
            metric_id=metric_id, version=metric.version, snapshot=metric,
            change_type=ChangeType.RESTORED, change_summary=f"Rolled back to v{target_version}"
        )
        self.versions.setdefault(metric_id, []).append(rollback_version)
        return metric

    def get_version_history(self, metric_id: UUID) -> list[MetricVersion]:
        return self.versions.get(metric_id, [])

    def analyze_impact(self, metric_id: UUID, affected_dashboards: list[dict] = None, affected_reports: list[dict] = None) -> MetricImpactAnalysis:
        downstream = self.graph.get_downstream(metric_id)
        analysis = MetricImpactAnalysis(
            metric_id=metric_id,
            affected_metrics=[{"id": mid, "name": self.metrics[mid].name} for mid in downstream if mid in self.metrics],
            affected_dashboards=affected_dashboards or [],
            affected_reports=affected_reports or [],
        )
        analysis.calculate_score()
        return analysis

    def list_metrics(self, category: Optional[MetricCategory] = None, status: Optional[MetricStatus] = None) -> list[Metric]:
        results = list(self.metrics.values())
        if category:
            results = [m for m in results if m.category == category]
        if status:
            results = [m for m in results if m.status == status]
        return results
