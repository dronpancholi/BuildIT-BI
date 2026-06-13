"""
Comprehensive test suite for Domain 10: Analytics Governance.
Tests versioning, certification, approval workflows, and usage metrics.
"""
import uuid
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from app.domain.governance import (
    ChangeType,
    CertificationStatus,
    ApprovalStatus,
    ApprovalTarget,
    ApprovalPolicy,
    AuditEntry,
    DashboardVersion,
    ReportVersion,
    CertifiedMetric,
    CertifiedReport,
    ApprovalWorkflow,
    AnalyticsUsageMetrics,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def dashboard_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def report_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def metric_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_snapshot() -> Dict[str, Any]:
    return {
        "title": "Revenue Dashboard",
        "widgets": ["kpi_card", "line_chart", "table"],
        "filters": {"date_range": "2026-Q1"},
    }


@pytest.fixture
def approver_ids() -> list:
    return [uuid.uuid4() for _ in range(3)]


# ============================================================
# ENUM TESTS
# ============================================================

class TestChangeType:
    def test_all_values(self):
        values = [ct.value for ct in ChangeType]
        assert "LAYOUT" in values
        assert "WIDGET_ADDED" in values
        assert "WIDGET_REMOVED" in values
        assert "WIDGET_CHANGED" in values
        assert "FILTER_CHANGED" in values
        assert "METRIC_ADDED" in values
        assert "METRIC_REMOVED" in values
        assert "METRIC_CHANGED" in values

    def test_count(self):
        assert len(ChangeType) == 8


class TestCertificationStatus:
    def test_all_values(self):
        values = [cs.value for cs in CertificationStatus]
        assert "DRAFT" in values
        assert "IN_REVIEW" in values
        assert "CERTIFIED" in values
        assert "EXPIRED" in values

    def test_count(self):
        assert len(CertificationStatus) == 4


class TestApprovalStatus:
    def test_all_values(self):
        values = [a.value for a in ApprovalStatus]
        assert "PENDING" in values
        assert "APPROVED" in values
        assert "REJECTED" in values
        assert "EXPIRED" in values

    def test_count(self):
        assert len(ApprovalStatus) == 4


class TestApprovalTarget:
    def test_all_values(self):
        values = [at.value for at in ApprovalTarget]
        assert "DASHBOARD" in values
        assert "REPORT" in values
        assert "METRIC" in values

    def test_count(self):
        assert len(ApprovalTarget) == 3


class TestApprovalPolicy:
    def test_all_values(self):
        values = [ap.value for ap in ApprovalPolicy]
        assert "ANY_ONE" in values
        assert "ALL" in values
        assert "MAJORITY" in values

    def test_count(self):
        assert len(ApprovalPolicy) == 3


# ============================================================
# AUDIT ENTRY TESTS
# ============================================================

class TestAuditEntry:
    def test_create_audit_entry(self, user_id):
        entry = AuditEntry(
            action="CERTIFIED",
            performed_by=user_id,
            performed_at=datetime(2026, 6, 1, 10, 0, 0),
            details="Initial certification",
        )
        assert entry.action == "CERTIFIED"
        assert entry.performed_by == user_id
        assert entry.details == "Initial certification"

    def test_frozen(self, user_id):
        entry = AuditEntry(
            action="CERTIFIED",
            performed_by=user_id,
            performed_at=datetime.utcnow(),
        )
        with pytest.raises(AttributeError):
            entry.action = "REJECTED"


# ============================================================
# DASHBOARD VERSION TESTS
# ============================================================

class TestDashboardVersion:
    def test_create_version(self, dashboard_id, user_id, sample_snapshot):
        version = DashboardVersion(
            dashboard_id=dashboard_id,
            version=1,
            snapshot=sample_snapshot,
            changed_by=user_id,
            change_type=ChangeType.LAYOUT,
            change_summary="Reorganized dashboard layout",
        )
        assert version.dashboard_id == dashboard_id
        assert version.version == 1
        assert version.snapshot == sample_snapshot
        assert version.changed_by == user_id
        assert version.change_type == ChangeType.LAYOUT
        assert version.change_summary == "Reorganized dashboard layout"

    def test_immutable(self, dashboard_id, user_id, sample_snapshot):
        version = DashboardVersion(
            dashboard_id=dashboard_id,
            version=1,
            snapshot=sample_snapshot,
            changed_by=user_id,
            change_type=ChangeType.WIDGET_ADDED,
            change_summary="Added KPI card",
        )
        with pytest.raises(AttributeError):
            version.version = 2

    def test_default_id(self, dashboard_id, user_id, sample_snapshot):
        v1 = DashboardVersion(
            dashboard_id=dashboard_id,
            version=1,
            snapshot=sample_snapshot,
            changed_by=user_id,
            change_type=ChangeType.FILTER_CHANGED,
            change_summary="Updated filters",
        )
        v2 = DashboardVersion(
            dashboard_id=dashboard_id,
            version=2,
            snapshot=sample_snapshot,
            changed_by=user_id,
            change_type=ChangeType.FILTER_CHANGED,
            change_summary="Updated filters again",
        )
        assert v1.id != v2.id

    def test_default_changed_at(self, dashboard_id, user_id, sample_snapshot):
        before = datetime.utcnow()
        version = DashboardVersion(
            dashboard_id=dashboard_id,
            version=1,
            snapshot=sample_snapshot,
            changed_by=user_id,
            change_type=ChangeType.WIDGET_REMOVED,
            change_summary="Removed table widget",
        )
        after = datetime.utcnow()
        assert before <= version.changed_at <= after


# ============================================================
# REPORT VERSION TESTS
# ============================================================

class TestReportVersion:
    def test_create_version(self, report_id, user_id, sample_snapshot):
        version = ReportVersion(
            report_id=report_id,
            version=3,
            snapshot=sample_snapshot,
            changed_by=user_id,
            change_type=ChangeType.METRIC_CHANGED,
            change_summary="Updated revenue metric formula",
        )
        assert version.report_id == report_id
        assert version.version == 3
        assert version.change_type == ChangeType.METRIC_CHANGED

    def test_immutable(self, report_id, user_id, sample_snapshot):
        version = ReportVersion(
            report_id=report_id,
            version=1,
            snapshot=sample_snapshot,
            changed_by=user_id,
            change_type=ChangeType.METRIC_ADDED,
            change_summary="Added EBITDA metric",
        )
        with pytest.raises(AttributeError):
            version.change_summary = "Tampered"

    def test_independent_from_dashboard_version(self, report_id, dashboard_id, user_id, sample_snapshot):
        rv = ReportVersion(
            report_id=report_id,
            version=1,
            snapshot=sample_snapshot,
            changed_by=user_id,
            change_type=ChangeType.WIDGET_CHANGED,
            change_summary="Changed chart type",
        )
        dv = DashboardVersion(
            dashboard_id=dashboard_id,
            version=1,
            snapshot=sample_snapshot,
            changed_by=user_id,
            change_type=ChangeType.WIDGET_CHANGED,
            change_summary="Changed chart type",
        )
        assert rv.id != dv.id
        assert rv.report_id != dv.dashboard_id


# ============================================================
# CERTIFIED METRIC TESTS
# ============================================================

class TestCertifiedMetric:
    def test_create_metric(self, metric_id):
        metric = CertifiedMetric(
            metric_id=metric_id,
            certification_criteria=["accuracy > 99%", "source verified"],
        )
        assert metric.metric_id == metric_id
        assert metric.certification_status == CertificationStatus.DRAFT
        assert metric.certified_by is None
        assert metric.certified_at is None
        assert metric.review_frequency_days == 90

    def test_submit_for_review(self, metric_id):
        metric = CertifiedMetric(metric_id=metric_id)
        metric.submit_for_review()
        assert metric.certification_status == CertificationStatus.IN_REVIEW

    def test_certify(self, metric_id, user_id):
        metric = CertifiedMetric(metric_id=metric_id)
        metric.certify(certified_by=user_id)
        assert metric.certification_status == CertificationStatus.CERTIFIED
        assert metric.certified_by == user_id
        assert metric.certified_at is not None

    def test_certify_with_expiry(self, metric_id, user_id):
        expires = datetime(2027, 1, 1)
        metric = CertifiedMetric(metric_id=metric_id)
        metric.certify(certified_by=user_id, expires_at=expires)
        assert metric.expires_at == expires
        assert not metric.is_expired()

    def test_is_certified(self, metric_id, user_id):
        metric = CertifiedMetric(metric_id=metric_id)
        assert not metric.is_certified()
        metric.certify(certified_by=user_id)
        assert metric.is_certified()

    def test_is_expired(self, metric_id, user_id):
        past = datetime(2020, 1, 1)
        metric = CertifiedMetric(metric_id=metric_id)
        metric.certify(certified_by=user_id, expires_at=past)
        assert metric.is_expired()

    def test_is_expired_no_expiry(self, metric_id):
        metric = CertifiedMetric(metric_id=metric_id)
        assert not metric.is_expired()

    def test_expire(self, metric_id, user_id):
        metric = CertifiedMetric(metric_id=metric_id)
        metric.certify(certified_by=user_id)
        metric.expire()
        assert metric.certification_status == CertificationStatus.EXPIRED

    def test_reset_to_draft(self, metric_id, user_id):
        metric = CertifiedMetric(metric_id=metric_id)
        metric.certify(certified_by=user_id)
        metric.reset_to_draft()
        assert metric.certification_status == CertificationStatus.DRAFT
        assert metric.certified_by is None
        assert metric.certified_at is None

    def test_full_lifecycle(self, metric_id, user_id):
        metric = CertifiedMetric(
            metric_id=metric_id,
            certification_criteria=["data quality > 95%"],
        )
        assert metric.certification_status == CertificationStatus.DRAFT

        metric.submit_for_review()
        assert metric.certification_status == CertificationStatus.IN_REVIEW

        expires = datetime.utcnow() + timedelta(days=365)
        metric.certify(certified_by=user_id, expires_at=expires)
        assert metric.certification_status == CertificationStatus.CERTIFIED
        assert metric.is_certified()

        metric.expire()
        assert metric.certification_status == CertificationStatus.EXPIRED

    def test_custom_review_frequency(self, metric_id):
        metric = CertifiedMetric(metric_id=metric_id, review_frequency_days=30)
        assert metric.review_frequency_days == 30


# ============================================================
# CERTIFIED REPORT TESTS
# ============================================================

class TestCertifiedReport:
    def test_create_report(self, report_id):
        report = CertifiedReport(report_id=report_id)
        assert report.report_id == report_id
        assert report.certification_status == CertificationStatus.DRAFT
        assert report.audit_trail == []

    def test_submit_for_review(self, report_id):
        report = CertifiedReport(report_id=report_id)
        report.submit_for_review()
        assert report.certification_status == CertificationStatus.IN_REVIEW

    def test_certify_adds_audit_entry(self, report_id, user_id):
        report = CertifiedReport(report_id=report_id)
        report.certify(certified_by=user_id)
        assert report.certification_status == CertificationStatus.CERTIFIED
        assert len(report.audit_trail) == 1
        assert report.audit_trail[0].action == "CERTIFIED"
        assert report.audit_trail[0].performed_by == user_id

    def test_add_manual_audit_entry(self, report_id, user_id):
        report = CertifiedReport(report_id=report_id)
        report.add_audit_entry("REVIEWED", user_id, "Looks good")
        assert len(report.audit_trail) == 1
        assert report.audit_trail[0].action == "REVIEWED"
        assert report.audit_trail[0].details == "Looks good"

    def test_is_certified(self, report_id, user_id):
        report = CertifiedReport(report_id=report_id)
        assert not report.is_certified()
        report.certify(certified_by=user_id)
        assert report.is_certified()

    def test_expire(self, report_id, user_id):
        report = CertifiedReport(report_id=report_id)
        report.certify(certified_by=user_id)
        report.expire()
        assert report.certification_status == CertificationStatus.EXPIRED

    def test_reset_to_draft(self, report_id, user_id):
        report = CertifiedReport(report_id=report_id)
        report.certify(certified_by=user_id)
        report.reset_to_draft()
        assert report.certification_status == CertificationStatus.DRAFT
        assert report.certified_by is None
        assert report.certified_at is None

    def test_audit_trail_grows(self, report_id, user_id):
        report = CertifiedReport(report_id=report_id)
        report.certify(certified_by=user_id)
        report.add_audit_entry("REVIEWED", user_id, "First review")
        report.add_audit_entry("UPDATED", user_id, "Changed formula")
        assert len(report.audit_trail) == 3
        actions = [e.action for e in report.audit_trail]
        assert actions == ["CERTIFIED", "REVIEWED", "UPDATED"]


# ============================================================
# APPROVAL WORKFLOW TESTS
# ============================================================

class TestApprovalWorkflow:
    def test_create_workflow(self, dashboard_id, user_id, approver_ids):
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
            approver_ids=approver_ids,
            approval_policy=ApprovalPolicy.ALL,
        )
        assert workflow.target_type == ApprovalTarget.DASHBOARD
        assert workflow.target_id == dashboard_id
        assert workflow.status == ApprovalStatus.PENDING
        assert workflow.approval_policy == ApprovalPolicy.ALL
        assert len(workflow.approver_ids) == 3

    def test_approve(self, dashboard_id, user_id, approver_ids):
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
            approver_ids=approver_ids,
        )
        workflow.approve(reviewer=approver_ids[0], note="LGTM")
        assert workflow.status == ApprovalStatus.APPROVED
        assert workflow.reviewed_by == approver_ids[0]
        assert workflow.reviewed_at is not None
        assert workflow.review_note == "LGTM"

    def test_reject(self, dashboard_id, user_id, approver_ids):
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
            approver_ids=approver_ids,
        )
        workflow.reject(reviewer=approver_ids[1], note="Needs changes")
        assert workflow.status == ApprovalStatus.REJECTED
        assert workflow.reviewed_by == approver_ids[1]
        assert workflow.review_note == "Needs changes"

    def test_approve_non_approver_raises(self, dashboard_id, user_id, approver_ids):
        outsider = uuid.uuid4()
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
            approver_ids=approver_ids,
        )
        with pytest.raises(PermissionError, match="not an authorized approver"):
            workflow.approve(reviewer=outsider)

    def test_reject_non_approver_raises(self, dashboard_id, user_id, approver_ids):
        outsider = uuid.uuid4()
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
            approver_ids=approver_ids,
        )
        with pytest.raises(PermissionError, match="not an authorized approver"):
            workflow.reject(reviewer=outsider)

    def test_approve_already_approved_raises(self, dashboard_id, user_id, approver_ids):
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
            approver_ids=approver_ids,
        )
        workflow.approve(reviewer=approver_ids[0])
        with pytest.raises(ValueError, match="Cannot approve workflow in APPROVED status"):
            workflow.approve(reviewer=approver_ids[1])

    def test_reject_already_approved_raises(self, dashboard_id, user_id, approver_ids):
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
            approver_ids=approver_ids,
        )
        workflow.approve(reviewer=approver_ids[0])
        with pytest.raises(ValueError, match="Cannot reject workflow in APPROVED status"):
            workflow.reject(reviewer=approver_ids[1])

    def test_approve_already_rejected_raises(self, dashboard_id, user_id, approver_ids):
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
            approver_ids=approver_ids,
        )
        workflow.reject(reviewer=approver_ids[0])
        with pytest.raises(ValueError, match="Cannot approve workflow in REJECTED status"):
            workflow.approve(reviewer=approver_ids[1])

    def test_expire_pending(self, dashboard_id, user_id, approver_ids):
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
            approver_ids=approver_ids,
        )
        workflow.expire()
        assert workflow.status == ApprovalStatus.EXPIRED

    def test_expire_approved_no_op(self, dashboard_id, user_id, approver_ids):
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
            approver_ids=approver_ids,
        )
        workflow.approve(reviewer=approver_ids[0])
        workflow.expire()
        assert workflow.status == ApprovalStatus.APPROVED

    def test_status_predicates(self, dashboard_id, user_id, approver_ids):
        pending = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
            approver_ids=approver_ids,
        )
        assert pending.is_pending()
        assert not pending.is_approved()
        assert not pending.is_rejected()
        assert not pending.is_expired()

        approved = ApprovalWorkflow(
            target_type=ApprovalTarget.REPORT,
            target_id=uuid.uuid4(),
            requested_by=user_id,
            approver_ids=approver_ids,
        )
        approved.approve(reviewer=approver_ids[0])
        assert not approved.is_pending()
        assert approved.is_approved()

    def test_report_target_type(self, report_id, user_id, approver_ids):
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.REPORT,
            target_id=report_id,
            requested_by=user_id,
            approver_ids=approver_ids,
            approval_policy=ApprovalPolicy.MAJORITY,
        )
        assert workflow.target_type == ApprovalTarget.REPORT
        assert workflow.approval_policy == ApprovalPolicy.MAJORITY

    def test_metric_target_type(self, metric_id, user_id, approver_ids):
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.METRIC,
            target_id=metric_id,
            requested_by=user_id,
            approver_ids=approver_ids,
            approval_policy=ApprovalPolicy.ANY_ONE,
        )
        assert workflow.target_type == ApprovalTarget.METRIC
        assert workflow.approval_policy == ApprovalPolicy.ANY_ONE

    def test_default_values(self, dashboard_id, user_id):
        workflow = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
        )
        assert workflow.id is not None
        assert workflow.approver_ids == []
        assert workflow.reviewed_by is None
        assert workflow.reviewed_at is None
        assert workflow.review_note is None


# ============================================================
# ANALYTICS USAGE METRICS TESTS
# ============================================================

class TestAnalyticsUsageMetrics:
    def test_create_metrics(self, dashboard_id):
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
        )
        assert metrics.dashboard_id == dashboard_id
        assert metrics.total_views == 0
        assert metrics.unique_viewers == 0
        assert metrics.staleness_score == 0.0
        assert metrics.export_counts == {}
        assert metrics.shared_count == 0

    def test_populated_metrics(self, dashboard_id):
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            total_views=1500,
            unique_viewers=450,
            avg_session_duration_seconds=120.5,
            export_counts={"pdf": 30, "csv": 15, "xlsx": 5},
            shared_count=25,
            last_viewed_at=datetime(2026, 6, 10),
            staleness_score=0.1,
        )
        assert metrics.total_views == 1500
        assert metrics.unique_viewers == 450
        assert metrics.export_counts["pdf"] == 30
        assert metrics.shared_count == 25

    def test_total_exports(self, dashboard_id):
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            export_counts={"pdf": 30, "csv": 15, "xlsx": 5},
        )
        assert metrics.total_exports() == 50

    def test_total_exports_empty(self, dashboard_id):
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
        )
        assert metrics.total_exports() == 0

    def test_viewer_ratio(self, dashboard_id):
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            total_views=200,
            unique_viewers=50,
        )
        assert metrics.viewer_ratio() == 0.25

    def test_viewer_ratio_zero_views(self, dashboard_id):
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            total_views=0,
        )
        assert metrics.viewer_ratio() == 0.0

    def test_compute_staleness_no_view(self, dashboard_id):
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            last_viewed_at=None,
        )
        assert metrics.compute_staleness() == 1.0

    def test_compute_staleness_fresh(self, dashboard_id):
        now = datetime.utcnow()
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            last_viewed_at=now,
        )
        assert metrics.compute_staleness(reference_date=now) == 0.0

    def test_compute_staleness_one_day(self, dashboard_id):
        now = datetime.utcnow()
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            last_viewed_at=now - timedelta(days=1),
        )
        assert metrics.compute_staleness(reference_date=now) == 0.0

    def test_compute_staleness_mid_range(self, dashboard_id):
        now = datetime.utcnow()
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            last_viewed_at=now - timedelta(days=45),
        )
        score = metrics.compute_staleness(reference_date=now)
        assert 0.0 < score < 1.0
        assert abs(score - 45 / 90) < 0.01

    def test_compute_staleness_very_stale(self, dashboard_id):
        now = datetime.utcnow()
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            last_viewed_at=now - timedelta(days=90),
        )
        assert metrics.compute_staleness(reference_date=now) == 1.0

    def test_compute_staleness_beyond_90(self, dashboard_id):
        now = datetime.utcnow()
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            last_viewed_at=now - timedelta(days=120),
        )
        assert metrics.compute_staleness(reference_date=now) == 1.0

    def test_is_stale_default_threshold(self, dashboard_id):
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            staleness_score=0.8,
        )
        assert metrics.is_stale()

    def test_is_not_stale(self, dashboard_id):
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            staleness_score=0.3,
        )
        assert not metrics.is_stale()

    def test_is_stale_custom_threshold(self, dashboard_id):
        metrics = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            staleness_score=0.4,
        )
        assert not metrics.is_stale(threshold=0.5)
        assert metrics.is_stale(threshold=0.3)


# ============================================================
# INTEGRATION-STYLE TESTS
# ============================================================

class TestGovernanceIntegration:
    def test_dashboard_lifecycle(self, dashboard_id, user_id, approver_ids, sample_snapshot):
        version = DashboardVersion(
            dashboard_id=dashboard_id,
            version=1,
            snapshot=sample_snapshot,
            changed_by=user_id,
            change_type=ChangeType.WIDGET_ADDED,
            change_summary="Initial dashboard creation",
        )

        approval = ApprovalWorkflow(
            target_type=ApprovalTarget.DASHBOARD,
            target_id=dashboard_id,
            requested_by=user_id,
            approver_ids=approver_ids,
            approval_policy=ApprovalPolicy.ALL,
        )
        approval.approve(reviewer=approver_ids[0])
        assert approval.is_approved()

        usage = AnalyticsUsageMetrics(
            dashboard_id=dashboard_id,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            total_views=500,
            unique_viewers=100,
            last_viewed_at=datetime.utcnow(),
        )
        assert usage.compute_staleness() == 0.0

    def test_report_certification_lifecycle(self, report_id, user_id):
        cert_report = CertifiedReport(report_id=report_id)
        cert_report.submit_for_review()
        cert_report.certify(certified_by=user_id)
        cert_report.add_audit_entry("REVIEWED", user_id, "Passed QA")
        assert cert_report.is_certified()
        assert len(cert_report.audit_trail) == 2

        cert_report.expire()
        assert not cert_report.is_certified()

    def test_metric_certification_with_approval(self, metric_id, user_id, approver_ids):
        cert_metric = CertifiedMetric(
            metric_id=metric_id,
            certification_criteria=["data lineage verified"],
        )
        cert_metric.submit_for_review()
        assert cert_metric.is_certified() is False

        approval = ApprovalWorkflow(
            target_type=ApprovalTarget.METRIC,
            target_id=metric_id,
            requested_by=user_id,
            approver_ids=approver_ids,
            approval_policy=ApprovalPolicy.ANY_ONE,
        )
        approval.approve(reviewer=approver_ids[2])
        cert_metric.certify(
            certified_by=approver_ids[2],
            expires_at=datetime.utcnow() + timedelta(days=365),
        )
        assert cert_metric.is_certified()
        assert not cert_metric.is_expired()
