import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4

from app.domain.metric_studio import (
    Metric,
    MetricCategory,
    MetricStatus,
    MetricVersion,
    ChangeType,
    ApprovalStep,
    StepStatus,
    MetricApprovalWorkflow,
    ApprovalStatus,
    MetricDependencyGraph,
    MetricImpactAnalysis,
    MetricStudioService,
)


class TestMetricLifecycle:
    def test_create_metric_defaults(self):
        metric = Metric(name="Revenue", slug="revenue")
        assert metric.name == "Revenue"
        assert metric.slug == "revenue"
        assert metric.status == MetricStatus.DRAFT
        assert metric.version == 1
        assert metric.is_certified is False
        assert metric.category == MetricCategory.FINANCIAL

    def test_publish_from_draft(self):
        metric = Metric(name="Test")
        metric.publish()
        assert metric.status == MetricStatus.PUBLISHED

    def test_publish_from_pending_review(self):
        metric = Metric(name="Test")
        metric.status = MetricStatus.PENDING_REVIEW
        metric.publish()
        assert metric.status == MetricStatus.PUBLISHED

    def test_publish_from_certified_raises(self):
        metric = Metric(name="Test", status=MetricStatus.CERTIFIED)
        with pytest.raises(ValueError, match="Cannot publish from certified"):
            metric.publish()

    def test_request_certification(self):
        metric = Metric(name="Test", status=MetricStatus.PUBLISHED)
        metric.request_certification()
        assert metric.status == MetricStatus.PENDING_REVIEW

    def test_request_certification_not_published_raises(self):
        metric = Metric(name="Test", status=MetricStatus.DRAFT)
        with pytest.raises(ValueError, match="Must be published before certification"):
            metric.request_certification()

    def test_certify(self):
        certifier_id = uuid4()
        metric = Metric(name="Test", status=MetricStatus.PENDING_REVIEW)
        expires = date.today() + timedelta(days=365)
        metric.certify(certifier_id, expires_at=expires)
        assert metric.status == MetricStatus.CERTIFIED
        assert metric.is_certified is True
        assert metric.certified_by == certifier_id
        assert metric.certified_at is not None
        assert metric.certification_expires_at == expires

    def test_certify_not_pending_raises(self):
        metric = Metric(name="Test", status=MetricStatus.DRAFT)
        with pytest.raises(ValueError, match="Must be pending review to certify"):
            metric.certify(uuid4())

    def test_deprecate(self):
        metric = Metric(name="Test", status=MetricStatus.PUBLISHED)
        metric.deprecate()
        assert metric.status == MetricStatus.DEPRECATED
        assert metric.deprecated_at is not None

    def test_deprecate_already_deprecated_raises(self):
        metric = Metric(name="Test", status=MetricStatus.DEPRECATED)
        with pytest.raises(ValueError, match="Cannot deprecate from deprecated"):
            metric.deprecate()

    def test_deprecate_archived_raises(self):
        metric = Metric(name="Test", status=MetricStatus.ARCHIVED)
        with pytest.raises(ValueError, match="Cannot deprecate from archived"):
            metric.deprecate()

    def test_is_expired_no_expiry(self):
        metric = Metric(name="Test")
        assert metric.is_expired() is False

    def test_is_expired_future_date(self):
        metric = Metric(name="Test", certification_expires_at=date.today() + timedelta(days=10))
        assert metric.is_expired() is False

    def test_is_expired_past_date(self):
        metric = Metric(name="Test", certification_expires_at=date.today() - timedelta(days=1))
        assert metric.is_expired() is True


class TestMetricVersion:
    def test_version_snapshot(self):
        metric = Metric(name="Rev", version=2)
        version = MetricVersion(
            metric_id=metric.id,
            version=2,
            snapshot=metric,
            change_type=ChangeType.CREATED,
        )
        assert version.snapshot.name == "Rev"
        assert version.version == 2
        assert version.change_type == ChangeType.CREATED

    def test_change_types(self):
        for ct in ChangeType:
            v = MetricVersion(change_type=ct)
            assert v.change_type == ct


class TestApprovalWorkflow:
    def _make_workflow(self, num_steps=2):
        steps = [
            ApprovalStep(step_order=i + 1, approver_role=f"approver_{i + 1}")
            for i in range(num_steps)
        ]
        return MetricApprovalWorkflow(
            metric_id=uuid4(),
            requested_by=uuid4(),
            steps=steps,
        )

    def test_approve_all_steps(self):
        workflow = self._make_workflow(3)
        approver = uuid4()
        workflow.approve_step(0, approver, note="OK")
        assert workflow.steps[0].status == StepStatus.APPROVED
        assert workflow.steps[0].decided_by == approver
        assert workflow.status == ApprovalStatus.PENDING

        workflow.approve_step(1, approver)
        assert workflow.steps[1].status == StepStatus.APPROVED
        assert workflow.status == ApprovalStatus.PENDING

        workflow.approve_step(2, approver, note="Final")
        assert workflow.steps[2].status == StepStatus.APPROVED
        assert workflow.status == ApprovalStatus.APPROVED

    def test_reject_step(self):
        workflow = self._make_workflow(2)
        approver = uuid4()
        workflow.approve_step(0, approver)
        workflow.reject_step(1, approver, note="Nope")
        assert workflow.steps[1].status == StepStatus.REJECTED
        assert workflow.status == ApprovalStatus.REJECTED

    def test_approve_out_of_range_raises(self):
        workflow = self._make_workflow(2)
        with pytest.raises(IndexError, match="Step index out of range"):
            workflow.approve_step(5, uuid4())

    def test_reject_out_of_range_raises(self):
        workflow = self._make_workflow(2)
        with pytest.raises(IndexError, match="Step index out of range"):
            workflow.reject_step(10, uuid4())

    def test_approve_already_approved_raises(self):
        workflow = self._make_workflow(2)
        approver = uuid4()
        workflow.approve_step(0, approver)
        with pytest.raises(ValueError, match="Step 0 already approved"):
            workflow.approve_step(0, approver)


class TestDependencyGraph:
    def _build_graph(self):
        g = MetricDependencyGraph()
        a = uuid4()
        b = uuid4()
        c = uuid4()
        g.add_node(a, "A")
        g.add_node(b, "B")
        g.add_node(c, "C")
        g.add_edge(a, b)
        g.add_edge(b, c)
        return g, a, b, c

    def test_upstream_downstream(self):
        g, a, b, c = self._build_graph()
        assert g.get_upstream(b) == [a]
        assert g.get_downstream(a) == [b]
        assert g.get_downstream(b) == [c]
        assert g.get_downstream(c) == []
        assert g.get_upstream(a) == []

    def test_root_metrics(self):
        g, a, b, c = self._build_graph()
        roots = g.get_root_metrics()
        assert a in roots
        assert b not in roots
        assert c not in roots

    def test_detect_cycle(self):
        g = MetricDependencyGraph()
        a = uuid4()
        b = uuid4()
        g.add_node(a, "A")
        g.add_node(b, "B")
        g.add_edge(a, b)
        g.add_edge(b, a)
        cycles = g.detect_cycles()
        assert len(cycles) >= 1

    def test_no_cycle(self):
        g, a, b, c = self._build_graph()
        cycles = g.detect_cycles()
        assert cycles == []


class TestImpactAnalysis:
    def test_score_calculation(self):
        analysis = MetricImpactAnalysis(
            affected_metrics=[{"id": uuid4(), "name": "M1"}, {"id": uuid4(), "name": "M2"}],
            affected_dashboards=[{"id": uuid4(), "name": "D1"}],
            affected_reports=[{"id": uuid4(), "name": "R1"}, {"id": uuid4(), "name": "R2"}, {"id": uuid4(), "name": "R3"}],
        )
        analysis.calculate_score()
        assert analysis.total_impact_score == 2 * 3 + 1 * 2 + 3 * 1

    def test_zero_score(self):
        analysis = MetricImpactAnalysis()
        analysis.calculate_score()
        assert analysis.total_impact_score == 0


class TestMetricStudioService:
    def test_create_and_get(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="LOS", slug="los", category=MetricCategory.OPERATIONS)
        assert m.name == "LOS"
        assert svc.get_metric(m.id) is m

    def test_create_stores_version(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Readmit")
        versions = svc.get_version_history(m.id)
        assert len(versions) == 1
        assert versions[0].change_type == ChangeType.CREATED

    def test_update_metric(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Old")
        updated = svc.update_metric(m.id, name="New", description="Updated")
        assert updated.name == "New"
        assert updated.description == "Updated"
        assert updated.version == 2
        versions = svc.get_version_history(m.id)
        assert len(versions) == 2
        assert versions[1].change_type == ChangeType.METADATA_CHANGED

    def test_update_nonexistent_raises(self):
        svc = MetricStudioService()
        with pytest.raises(KeyError, match="not found"):
            svc.update_metric(uuid4(), name="X")

    def test_publish_metric(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Test")
        result = svc.publish_metric(m.id)
        assert result.status == MetricStatus.PUBLISHED

    def test_certify_metric_creates_version(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Test")
        svc.publish_metric(m.id)
        svc.request_certification(m.id, uuid4(), [ApprovalStep(step_order=1, approver_role="reviewer")])
        certifier = uuid4()
        result = svc.certify_metric(m.id, certifier)
        assert result.status == MetricStatus.CERTIFIED
        versions = svc.get_version_history(m.id)
        assert any(v.change_type == ChangeType.CERTIFIED for v in versions)

    def test_deprecate_metric(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Test")
        svc.publish_metric(m.id)
        result = svc.deprecate_metric(m.id)
        assert result.status == MetricStatus.DEPRECATED

    def test_rollback_metric(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="v1")
        svc.update_metric(m.id, name="v2")
        rolled = svc.rollback_metric(m.id, target_version=1)
        assert rolled.version == 3

    def test_rollback_nonexistent_version_raises(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Test")
        with pytest.raises(ValueError, match="Version 99 not found"):
            svc.rollback_metric(m.id, target_version=99)

    def test_list_metrics_by_category(self):
        svc = MetricStudioService()
        svc.create_metric(name="R1", category=MetricCategory.REVENUE)
        svc.create_metric(name="R2", category=MetricCategory.REVENUE)
        svc.create_metric(name="C1", category=MetricCategory.COST)
        revenue = svc.list_metrics(category=MetricCategory.REVENUE)
        assert len(revenue) == 2

    def test_list_metrics_by_status(self):
        svc = MetricStudioService()
        m1 = svc.create_metric(name="A")
        m2 = svc.create_metric(name="B")
        svc.publish_metric(m1.id)
        published = svc.list_metrics(status=MetricStatus.PUBLISHED)
        assert len(published) == 1
        assert published[0].name == "A"

    def test_analyze_impact(self):
        svc = MetricStudioService()
        a = svc.create_metric(name="A")
        b = svc.create_metric(name="B")
        c = svc.create_metric(name="C")
        svc.graph.add_edge(a.id, b.id)
        svc.graph.add_edge(b.id, c.id)
        dashboards = [{"id": uuid4(), "name": "D1"}]
        reports = [{"id": uuid4(), "name": "R1"}]
        analysis = svc.analyze_impact(a.id, affected_dashboards=dashboards, affected_reports=reports)
        assert analysis.total_impact_score > 0

    def test_full_lifecycle(self):
        svc = MetricStudioService()
        m = svc.create_metric(name="Full")
        assert m.status == MetricStatus.DRAFT

        svc.publish_metric(m.id)
        assert svc.get_metric(m.id).status == MetricStatus.PUBLISHED

        step = ApprovalStep(step_order=1, approver_role="director")
        workflow = svc.request_certification(m.id, uuid4(), [step])
        assert workflow.status == ApprovalStatus.PENDING

        workflow.approve_step(0, uuid4())
        assert workflow.status == ApprovalStatus.APPROVED

        svc.certify_metric(m.id, uuid4())
        assert svc.get_metric(m.id).status == MetricStatus.CERTIFIED

        svc.deprecate_metric(m.id)
        assert svc.get_metric(m.id).status == MetricStatus.DEPRECATED
