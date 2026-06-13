import pytest
from datetime import datetime, date
from uuid import uuid4
from app.domain.metric_studio import (
    Metric, MetricVersion, MetricStudioService, MetricCategory, MetricStatus,
    ChangeType, ApprovalStep, StepStatus, MetricApprovalWorkflow, ApprovalStatus,
    MetricDependencyGraph, MetricImpactAnalysis
)

class TestMetric:
    def test_create_metric(self):
        m = Metric(name="Revenue", slug="revenue", category=MetricCategory.REVENUE)
        assert m.status == MetricStatus.DRAFT
        assert m.version == 1

    def test_publish(self):
        m = Metric(name="Revenue")
        m.publish()
        assert m.status == MetricStatus.PUBLISHED

    def test_publish_requires_draft(self):
        m = Metric(name="Revenue", status=MetricStatus.CERTIFIED)
        with pytest.raises(ValueError, match="Cannot publish"):
            m.publish()

    def test_request_certification(self):
        m = Metric(name="Revenue", status=MetricStatus.PUBLISHED)
        m.request_certification()
        assert m.status == MetricStatus.PENDING_REVIEW

    def test_certify(self):
        m = Metric(name="Revenue", status=MetricStatus.PENDING_REVIEW)
        m.certify(certifier_id=uuid4(), expires_at=date(2026, 12, 31))
        assert m.status == MetricStatus.CERTIFIED
        assert m.is_certified is True

    def test_certify_requires_pending(self):
        m = Metric(name="Revenue", status=MetricStatus.DRAFT)
        with pytest.raises(ValueError, match="Must be pending"):
            m.certify(uuid4())

    def test_deprecate(self):
        m = Metric(name="Old", status=MetricStatus.PUBLISHED)
        m.deprecate()
        assert m.status == MetricStatus.DEPRECATED

    def test_deprecate_archived_fails(self):
        m = Metric(name="Archived", status=MetricStatus.ARCHIVED)
        with pytest.raises(ValueError):
            m.deprecate()

    def test_is_expired_false(self):
        m = Metric(certification_expires_at=date(2099, 12, 31))
        assert m.is_expired() is False

    def test_is_expired_true(self):
        m = Metric(certification_expires_at=date(2020, 1, 1))
        assert m.is_expired() is True

    def test_is_expired_no_date(self):
        m = Metric(certification_expires_at=None)
        assert m.is_expired() is False

class TestApprovalWorkflow:
    def test_approve_single_step(self):
        wf = MetricApprovalWorkflow(steps=[ApprovalStep(step_order=0, approver_role="cfo")])
        wf.approve_step(0, uuid4())
        assert wf.status == ApprovalStatus.APPROVED

    def test_approve_multi_step(self):
        wf = MetricApprovalWorkflow(steps=[
            ApprovalStep(step_order=0, approver_role="steward"),
            ApprovalStep(step_order=1, approver_role="cfo"),
        ])
        wf.approve_step(0, uuid4())
        assert wf.status == ApprovalStatus.PENDING
        wf.approve_step(1, uuid4())
        assert wf.status == ApprovalStatus.APPROVED

    def test_reject_step(self):
        wf = MetricApprovalWorkflow(steps=[ApprovalStep(step_order=0)])
        wf.reject_step(0, uuid4(), note="Not ready")
        assert wf.status == ApprovalStatus.REJECTED

    def test_approve_out_of_range(self):
        wf = MetricApprovalWorkflow(steps=[ApprovalStep(step_order=0)])
        with pytest.raises(IndexError):
            wf.approve_step(5, uuid4())

    def test_approve_already_decided(self):
        wf = MetricApprovalWorkflow(steps=[ApprovalStep(step_order=0)])
        wf.approve_step(0, uuid4())
        with pytest.raises(ValueError, match="already"):
            wf.approve_step(0, uuid4())

class TestDependencyGraph:
    def test_add_node(self):
        g = MetricDependencyGraph()
        g.add_node(uuid4(), "Revenue")
        assert len(g.nodes) == 1

    def test_add_edge(self):
        g = MetricDependencyGraph()
        a, b = uuid4(), uuid4()
        g.add_node(a, "A")
        g.add_node(b, "B")
        g.add_edge(a, b)
        assert len(g.edges) == 1

    def test_detect_cycle(self):
        g = MetricDependencyGraph()
        a, b = uuid4(), uuid4()
        g.add_node(a, "A")
        g.add_node(b, "B")
        g.add_edge(a, b)
        g.add_edge(b, a)
        cycles = g.detect_cycles()
        assert len(cycles) > 0

    def test_no_cycle(self):
        g = MetricDependencyGraph()
        a, b, c = uuid4(), uuid4(), uuid4()
        g.add_node(a, "A")
        g.add_node(b, "B")
        g.add_node(c, "C")
        g.add_edge(a, b)
        g.add_edge(b, c)
        cycles = g.detect_cycles()
        assert len(cycles) == 0

    def test_get_upstream(self):
        g = MetricDependencyGraph()
        a, b = uuid4(), uuid4()
        g.add_node(a, "A")
        g.add_node(b, "B")
        g.add_edge(a, b)
        assert g.get_upstream(b) == [a]

    def test_get_downstream(self):
        g = MetricDependencyGraph()
        a, b = uuid4(), uuid4()
        g.add_node(a, "A")
        g.add_node(b, "B")
        g.add_edge(a, b)
        assert g.get_downstream(a) == [b]

    def test_get_root_metrics(self):
        g = MetricDependencyGraph()
        a, b = uuid4(), uuid4()
        g.add_node(a, "A")
        g.add_node(b, "B")
        g.add_edge(a, b)
        roots = g.get_root_metrics()
        assert a in roots
        assert b not in roots

class TestImpactAnalysis:
    def test_calculate_score(self):
        analysis = MetricImpactAnalysis(
            affected_metrics=[{"id": uuid4()}],
            affected_dashboards=[{"id": uuid4()}, {"id": uuid4()}],
            affected_reports=[{"id": uuid4()}],
        )
        analysis.calculate_score()
        assert analysis.total_impact_score == 3*1 + 2*2 + 1*1

class TestMetricStudioService:
    def test_create_and_get(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Revenue", category=MetricCategory.REVENUE)
        assert svc.get_metric(m.id) is not None

    def test_publish_metric(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Revenue")
        svc.publish_metric(m.id)
        assert m.status == MetricStatus.PUBLISHED

    def test_certify_metric(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Revenue")
        svc.publish_metric(m.id)
        m.request_certification()
        svc.certify_metric(m.id, uuid4())
        assert m.status == MetricStatus.CERTIFIED

    def test_request_certification(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Revenue")
        svc.publish_metric(m.id)
        wf = svc.request_certification(m.id, uuid4(), [ApprovalStep(step_order=0)])
        assert wf.metric_id == m.id
        assert m.status == MetricStatus.PENDING_REVIEW

    def test_version_history(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Revenue")
        svc.publish_metric(m.id)
        svc.update_metric(m.id, name="Revenue v2")
        versions = svc.get_version_history(m.id)
        assert len(versions) == 2

    def test_rollback(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Revenue")
        svc.publish_metric(m.id)
        svc.update_metric(m.id, name="Revenue v2")
        svc.rollback_metric(m.id, 1)
        versions = svc.get_version_history(m.id)
        assert len(versions) == 3

    def test_deprecate_metric(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Revenue")
        svc.publish_metric(m.id)
        svc.deprecate_metric(m.id)
        assert m.status == MetricStatus.DEPRECATED

    def test_analyze_impact(self):
        svc = MetricStudioService()
        a = svc.create_metric(name="A")
        b = svc.create_metric(name="B")
        svc.graph.add_edge(a.id, b.id)
        analysis = svc.analyze_impact(a.id, affected_dashboards=[{"id": uuid4()}])
        assert analysis.total_impact_score > 0

    def test_list_metrics_filter(self):
        svc = MetricStudioService()
        svc.create_metric(name="Rev", category=MetricCategory.REVENUE)
        svc.create_metric(name="Cost", category=MetricCategory.COST)
        revs = svc.list_metrics(category=MetricCategory.REVENUE)
        assert len(revs) == 1
