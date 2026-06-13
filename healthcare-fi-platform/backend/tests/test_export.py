"""
Comprehensive test suite for Domain 5: Export Engine.
Tests export jobs, scheduling, subscriptions, and templates.
"""
import uuid
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from app.domain.export import (
    ExportFormat,
    JobStatus,
    ScheduleFrequency,
    SubscriptionTrigger,
    ExportParameters,
    ExportJob,
    ScheduleConfig,
    ReportSubscription,
    ExportTemplate,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def report_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def recipient_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_params() -> Dict[str, Any]:
    return {
        "date_range": {"start": "2026-01-01", "end": "2026-03-31"},
        "department": "cardiology",
    }


@pytest.fixture
def sample_export_params() -> ExportParameters:
    return ExportParameters(
        include_raw_data=False,
        include_charts=True,
        include_metadata=True,
        page_orientation="portrait",
        paper_size="letter",
    )


@pytest.fixture
def sample_recipients() -> list:
    return [
        {"email": "admin@hospital.org", "name": "Admin"},
        {"email": "finance@hospital.org", "name": "Finance"},
    ]


# ============================================================
# ENUM TESTS
# ============================================================

class TestExportFormat:
    def test_all_values(self):
        values = [ef.value for ef in ExportFormat]
        assert "PDF" in values
        assert "EXCEL" in values
        assert "CSV" in values
        assert "PNG" in values

    def test_count(self):
        assert len(ExportFormat) == 4


class TestJobStatus:
    def test_all_values(self):
        values = [js.value for js in JobStatus]
        assert "PENDING" in values
        assert "PROCESSING" in values
        assert "COMPLETED" in values
        assert "FAILED" in values
        assert "EXPIRED" in values

    def test_count(self):
        assert len(JobStatus) == 5


class TestScheduleFrequency:
    def test_all_values(self):
        values = [sf.value for sf in ScheduleFrequency]
        assert "DAILY" in values
        assert "WEEKLY" in values
        assert "MONTHLY" in values
        assert "QUARTERLY" in values
        assert "CUSTOM" in values

    def test_count(self):
        assert len(ScheduleFrequency) == 5


class TestSubscriptionTrigger:
    def test_all_values(self):
        values = [st.value for st in SubscriptionTrigger]
        assert "ON_NEW_DATA" in values
        assert "ON_THRESHOLD_BREACH" in values
        assert "ON_SCHEDULE" in values

    def test_count(self):
        assert len(SubscriptionTrigger) == 3


# ============================================================
# EXPORT PARAMETERS TESTS
# ============================================================

class TestExportParameters:
    def test_defaults(self):
        params = ExportParameters()
        assert params.include_raw_data is True
        assert params.include_charts is True
        assert params.include_metadata is True
        assert params.page_orientation == "landscape"
        assert params.paper_size == "A4"

    def test_custom_values(self, sample_export_params):
        assert sample_export_params.include_raw_data is False
        assert sample_export_params.include_charts is True
        assert sample_export_params.include_metadata is True
        assert sample_export_params.page_orientation == "portrait"
        assert sample_export_params.paper_size == "letter"

    def test_frozen(self):
        params = ExportParameters()
        with pytest.raises(AttributeError):
            params.page_orientation = "portrait"


# ============================================================
# EXPORT JOB TESTS
# ============================================================

class TestExportJob:
    def test_create_job(self, report_id, user_id, sample_params):
        job = ExportJob(
            report_id=report_id,
            format=ExportFormat.PDF,
            parameters=sample_params,
            created_by=user_id,
        )
        assert job.report_id == report_id
        assert job.format == ExportFormat.PDF
        assert job.parameters == sample_params
        assert job.status == JobStatus.PENDING
        assert job.created_by == user_id
        assert job.started_at is None
        assert job.completed_at is None
        assert job.file_url is None
        assert job.expires_at is None
        assert job.error_message is None

    def test_default_id(self, report_id, user_id):
        j1 = ExportJob(report_id=report_id, format=ExportFormat.CSV, created_by=user_id)
        j2 = ExportJob(report_id=report_id, format=ExportFormat.CSV, created_by=user_id)
        assert j1.id != j2.id

    def test_default_created_at(self, report_id, user_id):
        before = datetime.utcnow()
        job = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        after = datetime.utcnow()
        assert before <= job.created_at <= after

    def test_start(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        job.start()
        assert job.status == JobStatus.PROCESSING
        assert job.started_at is not None

    def test_start_wrong_status_raises(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        job.start()
        with pytest.raises(ValueError, match="Cannot start job in PROCESSING status"):
            job.start()

    def test_complete(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.EXCEL, created_by=user_id)
        job.start()
        job.complete(file_url="https://storage.example.com/report.xlsx")
        assert job.status == JobStatus.COMPLETED
        assert job.file_url == "https://storage.example.com/report.xlsx"
        assert job.completed_at is not None

    def test_complete_with_expiry(self, report_id, user_id):
        expires = datetime.utcnow() + timedelta(hours=24)
        job = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        job.start()
        job.complete(file_url="https://storage.example.com/report.pdf", expires_at=expires)
        assert job.expires_at == expires

    def test_complete_wrong_status_raises(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        with pytest.raises(ValueError, match="Cannot complete job in PENDING status"):
            job.complete(file_url="https://storage.example.com/report.pdf")

    def test_fail_from_pending(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.PNG, created_by=user_id)
        job.fail("Timeout exceeded")
        assert job.status == JobStatus.FAILED
        assert job.error_message == "Timeout exceeded"
        assert job.completed_at is not None

    def test_fail_from_processing(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        job.start()
        job.fail("Rendering error")
        assert job.status == JobStatus.FAILED
        assert job.error_message == "Rendering error"

    def test_fail_wrong_status_raises(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        job.start()
        job.complete(file_url="https://storage.example.com/report.pdf")
        with pytest.raises(ValueError, match="Cannot fail job in COMPLETED status"):
            job.fail("Cannot fail after success")

    def test_expire_pending(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.CSV, created_by=user_id)
        job.expire()
        assert job.status == JobStatus.EXPIRED
        assert job.completed_at is not None

    def test_expire_processing_no_op(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        job.start()
        job.expire()
        assert job.status == JobStatus.PROCESSING

    def test_is_terminal(self, report_id, user_id):
        pending = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        assert not pending.is_terminal()

        completed = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        completed.start()
        completed.complete(file_url="https://example.com/report.pdf")
        assert completed.is_terminal()

        failed = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        failed.fail("Error")
        assert failed.is_terminal()

        expired = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        expired.expire()
        assert expired.is_terminal()

    def test_duration_seconds(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        assert job.duration_seconds() is None
        job.start()
        duration = job.duration_seconds()
        assert duration is not None
        assert duration >= 0

    def test_duration_seconds_completed(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        job.start()
        job.complete(file_url="https://example.com/report.pdf")
        assert job.duration_seconds() is not None
        assert job.duration_seconds() >= 0

    def test_is_expired_no_expiry(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.PDF, created_by=user_id)
        assert not job.is_expired()

    def test_is_expired_with_future_expiry(self, report_id, user_id):
        future = datetime.utcnow() + timedelta(hours=24)
        job = ExportJob(
            report_id=report_id,
            format=ExportFormat.PDF,
            created_by=user_id,
            expires_at=future,
        )
        assert not job.is_expired()

    def test_is_expired_with_past_expiry(self, report_id, user_id):
        past = datetime(2020, 1, 1)
        job = ExportJob(
            report_id=report_id,
            format=ExportFormat.PDF,
            created_by=user_id,
            expires_at=past,
        )
        assert job.is_expired()

    def test_full_lifecycle_success(self, report_id, user_id, sample_params):
        job = ExportJob(
            report_id=report_id,
            format=ExportFormat.PDF,
            parameters=sample_params,
            created_by=user_id,
        )
        assert job.status == JobStatus.PENDING

        job.start()
        assert job.status == JobStatus.PROCESSING

        expires = datetime.utcnow() + timedelta(days=7)
        job.complete(file_url="https://storage.example.com/final.pdf", expires_at=expires)
        assert job.status == JobStatus.COMPLETED
        assert job.file_url == "https://storage.example.com/final.pdf"
        assert job.is_terminal()
        assert not job.is_expired()

    def test_full_lifecycle_failure(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.PNG, created_by=user_id)
        job.start()
        job.fail("GPU out of memory")
        assert job.status == JobStatus.FAILED
        assert job.error_message == "GPU out of memory"
        assert job.is_terminal()

    def test_default_parameters(self, report_id, user_id):
        job = ExportJob(report_id=report_id, format=ExportFormat.CSV, created_by=user_id)
        assert job.parameters == {}


# ============================================================
# EXPORT PARAMETERS FROZEN TEST
# ============================================================

class TestExportParametersImmutable:
    def test_cannot_modify_include_raw_data(self):
        params = ExportParameters()
        with pytest.raises(AttributeError):
            params.include_raw_data = False

    def test_cannot_modify_orientation(self):
        params = ExportParameters()
        with pytest.raises(AttributeError):
            params.page_orientation = "portrait"

    def test_cannot_modify_paper_size(self):
        params = ExportParameters()
        with pytest.raises(AttributeError):
            params.paper_size = "letter"


# ============================================================
# SCHEDULE CONFIG TESTS
# ============================================================

class TestScheduleConfig:
    def test_create_schedule(self, report_id, sample_recipients):
        config = ScheduleConfig(
            report_id=report_id,
            frequency=ScheduleFrequency.WEEKLY,
            timezone="America/New_York",
            recipients=sample_recipients,
            subject_template="Weekly Report: {{report_name}}",
            body_template="<p>Please find the weekly report attached.</p>",
        )
        assert config.report_id == report_id
        assert config.frequency == ScheduleFrequency.WEEKLY
        assert config.timezone == "America/New_York"
        assert len(config.recipients) == 2
        assert config.is_active is True
        assert config.failure_count == 0
        assert config.include_attachment is True
        assert config.attachment_format == ExportFormat.PDF

    def test_default_values(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.DAILY)
        assert config.params == {}
        assert config.timezone == "UTC"
        assert config.recipients == []
        assert config.subject_template == ""
        assert config.body_template == ""
        assert config.is_active is True
        assert config.last_run_at is None
        assert config.failure_count == 0
        assert config.failure_alert_recipients == []

    def test_record_success(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.DAILY)
        config.record_success()
        assert config.last_run_at is not None
        assert config.failure_count == 0
        assert config.next_run_at > datetime.utcnow()

    def test_record_failure(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.DAILY)
        config.record_failure()
        assert config.failure_count == 1
        assert config.next_run_at > datetime.utcnow()

    def test_multiple_failures(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.WEEKLY)
        config.record_failure()
        config.record_failure()
        config.record_failure()
        assert config.failure_count == 3

    def test_success_resets_failure_count(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.DAILY)
        config.record_failure()
        config.record_failure()
        config.record_success()
        assert config.failure_count == 0

    def test_deactivate(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.DAILY)
        config.deactivate()
        assert config.is_active is False

    def test_activate(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.DAILY)
        config.deactivate()
        config.activate()
        assert config.is_active is True

    def test_should_alert_threshold(self, report_id):
        config = ScheduleConfig(
            report_id=report_id,
            frequency=ScheduleFrequency.DAILY,
            failure_alert_recipients=[{"email": "ops@hospital.org"}],
        )
        config.record_failure()
        config.record_failure()
        assert not config.should_alert()
        config.record_failure()
        assert config.should_alert()

    def test_should_alert_no_recipients(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.DAILY)
        for _ in range(5):
            config.record_failure()
        assert not config.should_alert()

    def test_next_run_daily(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.DAILY)
        before = datetime.utcnow() + timedelta(hours=23)
        config.record_success()
        after = datetime.utcnow() + timedelta(hours=25)
        assert before < config.next_run_at < after

    def test_next_run_weekly(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.WEEKLY)
        config.record_success()
        assert config.next_run_at > datetime.utcnow() + timedelta(days=6)

    def test_next_run_monthly(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.MONTHLY)
        config.record_success()
        assert config.next_run_at > datetime.utcnow() + timedelta(days=29)

    def test_next_run_quarterly(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.QUARTERLY)
        config.record_success()
        assert config.next_run_at > datetime.utcnow() + timedelta(days=90)

    def test_next_run_custom(self, report_id):
        config = ScheduleConfig(report_id=report_id, frequency=ScheduleFrequency.CUSTOM)
        config.record_success()
        assert config.next_run_at > datetime.utcnow()

    def test_excel_attachment_format(self, report_id):
        config = ScheduleConfig(
            report_id=report_id,
            frequency=ScheduleFrequency.MONTHLY,
            attachment_format=ExportFormat.EXCEL,
        )
        assert config.attachment_format == ExportFormat.EXCEL

    def test_failure_alert_recipients(self, report_id):
        alerts = [{"email": "admin@hospital.org"}, {"email": "cto@hospital.org"}]
        config = ScheduleConfig(
            report_id=report_id,
            frequency=ScheduleFrequency.DAILY,
            failure_alert_recipients=alerts,
        )
        assert len(config.failure_alert_recipients) == 2

    def test_all_frequencies(self, report_id):
        for freq in ScheduleFrequency:
            config = ScheduleConfig(report_id=report_id, frequency=freq)
            assert config.frequency == freq


# ============================================================
# REPORT SUBSCRIPTION TESTS
# ============================================================

class TestReportSubscription:
    def test_create_subscription(self, report_id, user_id, recipient_id):
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_NEW_DATA,
            include_context=True,
        )
        assert sub.report_id == report_id
        assert sub.recipient_id == recipient_id
        assert sub.trigger_type == SubscriptionTrigger.ON_NEW_DATA
        assert sub.include_context is True
        assert sub.is_active is True
        assert sub.threshold_config is None

    def test_default_values(self, report_id, recipient_id):
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_SCHEDULE,
        )
        assert sub.threshold_config is None
        assert sub.include_context is True
        assert sub.is_active is True

    def test_deactivate(self, report_id, recipient_id):
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_NEW_DATA,
        )
        sub.deactivate()
        assert sub.is_active is False

    def test_activate(self, report_id, recipient_id):
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_NEW_DATA,
        )
        sub.deactivate()
        sub.activate()
        assert sub.is_active is True

    def test_is_threshold_based(self, report_id, recipient_id):
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_THRESHOLD_BREACH,
        )
        assert sub.is_threshold_based()

    def test_is_not_threshold_based(self, report_id, recipient_id):
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_NEW_DATA,
        )
        assert not sub.is_threshold_based()

    def test_validate_threshold_config_valid(self, report_id, recipient_id):
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_THRESHOLD_BREACH,
            threshold_config={"metric": "revenue", "operator": "gt", "value": 1000000},
        )
        assert sub.validate_threshold_config() is True

    def test_validate_threshold_config_missing_keys(self, report_id, recipient_id):
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_THRESHOLD_BREACH,
            threshold_config={"metric": "revenue"},
        )
        assert sub.validate_threshold_config() is False

    def test_validate_threshold_config_none(self, report_id, recipient_id):
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_THRESHOLD_BREACH,
            threshold_config=None,
        )
        assert sub.validate_threshold_config() is False

    def test_validate_threshold_config_not_threshold_trigger(self, report_id, recipient_id):
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_NEW_DATA,
        )
        assert sub.validate_threshold_config() is True

    def test_all_trigger_types(self, report_id, recipient_id):
        for trigger in SubscriptionTrigger:
            sub = ReportSubscription(
                report_id=report_id,
                recipient_id=recipient_id,
                trigger_type=trigger,
            )
            assert sub.trigger_type == trigger

    def test_default_created_at(self, report_id, recipient_id):
        before = datetime.utcnow()
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_SCHEDULE,
        )
        after = datetime.utcnow()
        assert before <= sub.created_at <= after


# ============================================================
# EXPORT TEMPLATE TESTS
# ============================================================

class TestExportTemplate:
    def test_create_template(self):
        template = ExportTemplate(
            name="Executive Summary Template",
            format=ExportFormat.PDF,
            template_config={
                "page_size": "A4",
                "margins": {"top": 20, "bottom": 20, "left": 15, "right": 15},
                "font_family": "Helvetica",
            },
        )
        assert template.name == "Executive Summary Template"
        assert template.format == ExportFormat.PDF
        assert template.template_config["page_size"] == "A4"
        assert template.header_html is None
        assert template.footer_html is None
        assert template.css_override is None

    def test_with_branding(self):
        template = ExportTemplate(
            name="Branded Report",
            format=ExportFormat.PDF,
            template_config={"page_size": "A4"},
            header_html="<div class='header'><img src='logo.png'/></div>",
            footer_html="<div class='footer'>Confidential</div>",
        )
        assert template.has_branding() is True
        assert template.header_html is not None
        assert template.footer_html is not None

    def test_without_branding(self):
        template = ExportTemplate(
            name="Plain Report",
            format=ExportFormat.CSV,
            template_config={},
        )
        assert template.has_branding() is False

    def test_has_custom_styles(self):
        template = ExportTemplate(
            name="Styled Report",
            format=ExportFormat.PDF,
            template_config={},
            css_override="body { font-size: 12pt; } .chart { margin: 10px; }",
        )
        assert template.has_custom_styles() is True

    def test_no_custom_styles(self):
        template = ExportTemplate(
            name="Default Styles",
            format=ExportFormat.PDF,
            template_config={},
        )
        assert template.has_custom_styles() is False

    def test_merge_config(self):
        template = ExportTemplate(
            name="Merge Test",
            format=ExportFormat.EXCEL,
            template_config={"page_size": "A4", "orientation": "landscape"},
        )
        merged = template.merge_config({"orientation": "portrait", "font_size": 14})
        assert merged["page_size"] == "A4"
        assert merged["orientation"] == "portrait"
        assert merged["font_size"] == 14

    def test_merge_config_does_not_mutate_original(self):
        template = ExportTemplate(
            name="No Mutate",
            format=ExportFormat.PDF,
            template_config={"key": "original"},
        )
        merged = template.merge_config({"key": "override"})
        assert template.template_config["key"] == "original"
        assert merged["key"] == "override"

    def test_all_formats(self):
        for fmt in ExportFormat:
            template = ExportTemplate(name=f"Template for {fmt.value}", format=fmt)
            assert template.format == fmt

    def test_default_id(self):
        t1 = ExportTemplate(name="T1", format=ExportFormat.PDF)
        t2 = ExportTemplate(name="T2", format=ExportFormat.PDF)
        assert t1.id != t2.id

    def test_empty_template_config(self):
        template = ExportTemplate(name="Minimal", format=ExportFormat.CSV)
        assert template.template_config == {}


# ============================================================
# INTEGRATION-STYLE TESTS
# ============================================================

class TestExportIntegration:
    def test_job_full_lifecycle_with_schedule(self, report_id, user_id, sample_params):
        job = ExportJob(
            report_id=report_id,
            format=ExportFormat.PDF,
            parameters=sample_params,
            created_by=user_id,
        )
        job.start()
        expires = datetime.utcnow() + timedelta(days=7)
        job.complete(file_url="https://storage.example.com/quarterly.pdf", expires_at=expires)
        assert job.is_terminal()
        assert job.duration_seconds() is not None

        config = ScheduleConfig(
            report_id=report_id,
            frequency=ScheduleFrequency.QUARTERLY,
            recipients=[{"email": "cfo@hospital.org"}],
            attachment_format=ExportFormat.PDF,
        )
        config.record_success()
        assert config.failure_count == 0
        assert config.last_run_at is not None

    def test_subscription_to_export_pipeline(self, report_id, user_id, recipient_id):
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_THRESHOLD_BREACH,
            threshold_config={"metric": "total_cost", "operator": "gt", "value": 500000},
        )
        assert sub.validate_threshold_config()
        assert sub.is_threshold_based()

        job = ExportJob(
            report_id=report_id,
            format=ExportFormat.PDF,
            parameters={"threshold_alert": True},
            created_by=user_id,
        )
        job.start()
        job.complete(file_url="https://storage.example.com/alert.pdf")
        assert job.status == JobStatus.COMPLETED

    def test_template_driven_export(self, report_id, user_id):
        template = ExportTemplate(
            name="Monthly Financial Summary",
            format=ExportFormat.EXCEL,
            template_config={"include_charts": True, "sheet_name": "Financial Summary"},
            header_html="<h1>Hospital Financial Report</h1>",
            footer_html="<p>Generated by BuildIT BI</p>",
        )

        job = ExportJob(
            report_id=report_id,
            format=template.format,
            parameters=template.template_config,
            created_by=user_id,
        )
        job.start()
        job.complete(file_url="https://storage.example.com/financial.xlsx")
        assert job.status == JobStatus.COMPLETED
        assert job.format == ExportFormat.EXCEL

    def test_failed_export_alerts(self, report_id):
        config = ScheduleConfig(
            report_id=report_id,
            frequency=ScheduleFrequency.DAILY,
            failure_alert_recipients=[{"email": "ops@hospital.org"}],
        )
        for _ in range(3):
            config.record_failure()
        assert config.should_alert()
        assert config.failure_count == 3

    def test_subscription_deactivation(self, report_id, recipient_id):
        sub = ReportSubscription(
            report_id=report_id,
            recipient_id=recipient_id,
            trigger_type=SubscriptionTrigger.ON_NEW_DATA,
        )
        assert sub.is_active
        sub.deactivate()
        assert not sub.is_active
        sub.activate()
        assert sub.is_active

    def test_job_expiry_workflow(self, report_id, user_id):
        job = ExportJob(
            report_id=report_id,
            format=ExportFormat.PNG,
            created_by=user_id,
        )
        job.expire()
        assert job.status == JobStatus.EXPIRED
        assert job.is_terminal()

    def test_schedule_lifecycle_across_frequencies(self, report_id):
        for freq in ScheduleFrequency:
            config = ScheduleConfig(report_id=report_id, frequency=freq)
            config.record_success()
            assert config.next_run_at > datetime.utcnow()
            config.record_failure()
            assert config.failure_count == 1
            config.record_success()
            assert config.failure_count == 0
