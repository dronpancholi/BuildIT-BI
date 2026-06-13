"""
Temporal Workflow Definitions for the Healthcare Financial Intelligence Platform.
All long-running processes are Temporal workflows.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class WorkflowSchedule:
    """Schedule configuration for recurring workflows."""
    cron: str
    timezone: str = "UTC"
    enabled: bool = True


@dataclass
class RetryPolicy:
    """Retry policy for workflows and activities."""
    max_attempts: int = 3
    initial_interval: timedelta = timedelta(minutes=1)
    backoff_coefficient: float = 2.0
    maximum_interval: timedelta = timedelta(hours=1)
    non_retryable_error_types: List[str] = field(default_factory=list)


@dataclass
class ComputationScope:
    """Scope for metric computation."""
    tenant_id: uuid.UUID
    hospital_id: Optional[uuid.UUID] = None
    branch_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None


@dataclass
class TimePeriod:
    """Time period for computation."""
    start: datetime
    end: datetime
    period_type: str = "monthly"


# ============================
# METRIC COMPUTATION WORKFLOW
# ============================

@dataclass
class MetricComputationInput:
    """Input for metric computation workflow."""
    metric_id: uuid.UUID
    scope: ComputationScope
    period: TimePeriod
    force_recompute: bool = False
    skip_validation: bool = False
    skip_event_publish: bool = False


@dataclass
class MetricComputationOutput:
    """Output from metric computation workflow."""
    success: bool
    computed_value_id: Optional[uuid.UUID] = None
    value: Optional[float] = None
    computation_time_ms: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class MetricComputationWorkflow:
    """
    Computes a single metric for a given scope and time period.
    Handles dependency resolution, execution, caching, and alerting.
    
    Workflow:
    1. Validate metric is PUBLISHED
    2. Resolve dependencies (DAG)
    3. Check cache
    4. Execute dependencies (in topological order)
    5. Execute target metric
    6. Store result
    7. Validate result against rules
    8. Update quality scores
    9. Publish MetricComputed event
    10. Alert if thresholds breached
    """
    
    def __init__(self):
        self.retry_policy = RetryPolicy(
            max_attempts=3,
            initial_interval=timedelta(minutes=1),
            backoff_coefficient=2.0
        )
        self.timeout = timedelta(hours=1)
    
    async def execute(self, input: MetricComputationInput) -> MetricComputationOutput:
        """Execute the workflow."""
        # This would be implemented with Temporal SDK
        # For now, return placeholder
        return MetricComputationOutput(
            success=True,
            computation_time_ms=0
        )


# ============================
# DATA QUALITY WORKFLOW
# ============================

@dataclass
class DataQualityInput:
    """Input for data quality workflow."""
    scope: ComputationScope
    rule_ids: Optional[List[uuid.UUID]] = None
    period: Optional[TimePeriod] = None


@dataclass
class DataQualityOutput:
    """Output from data quality workflow."""
    run_id: uuid.UUID
    rules_evaluated: int
    rules_passed: int
    rules_failed: int
    issues_created: int
    issues_resolved: int
    quality_score: float
    duration_ms: int


class DataQualityWorkflow:
    """
    Runs quality validation for a scope.
    Processes rules, creates issues, sends alerts.
    
    Workflow:
    1. Fetch applicable rules for scope
    2. Execute rules in parallel (fan-out)
    3. Collect results
    4. De-duplicate with previous issues
    5. Create/update QualityIssue records
    6. Update DataQualityScore
    7. Send alerts for new critical/high issues
    8. Publish QualityIssueDetected events
    """
    
    def __init__(self):
        self.retry_policy = RetryPolicy(
            max_attempts=2,
            initial_interval=timedelta(minutes=15)
        )
        self.timeout = timedelta(hours=2)
    
    async def execute(self, input: DataQualityInput) -> DataQualityOutput:
        """Execute the workflow."""
        return DataQualityOutput(
            run_id=uuid.uuid4(),
            rules_evaluated=0,
            rules_passed=0,
            rules_failed=0,
            issues_created=0,
            issues_resolved=0,
            quality_score=0.0,
            duration_ms=0
        )


# ============================
# DATA IMPORT WORKFLOW
# ============================

@dataclass
class DataImportInput:
    """Input for data import workflow."""
    import_id: uuid.UUID
    template_id: uuid.UUID
    file_path: str
    initiated_by: uuid.UUID


@dataclass
class DataImportOutput:
    """Output from data import workflow."""
    import_id: uuid.UUID
    records_processed: int
    records_succeeded: int
    records_failed: int
    duration_ms: int
    quality_score: float
    errors: List[Dict[str, Any]]


class DataImportWorkflow:
    """
    Orchestrates the full import pipeline.
    Implements the outbox pattern for reliability.
    
    Workflow:
    1. Parse file
    2. Auto-map columns (or use saved mapping)
    3. Validate all records (batch)
    4. Write to staging table
    5. Run post-import validations
    6. Swap staging -> production (atomic)
    7. Update MetricComputedValues
    8. Send notifications
    9. Publish DataImportCompleted event
    """
    
    def __init__(self):
        self.retry_policy = RetryPolicy(
            max_attempts=3,
            initial_interval=timedelta(minutes=5)
        )
        self.timeout = timedelta(hours=4)
    
    async def execute(self, input: DataImportInput) -> DataImportOutput:
        """Execute the workflow."""
        return DataImportOutput(
            import_id=input.import_id,
            records_processed=0,
            records_succeeded=0,
            records_failed=0,
            duration_ms=0,
            quality_score=0.0,
            errors=[]
        )
    
    async def resume(self, import_id: uuid.UUID, checkpoint_id: uuid.UUID) -> DataImportOutput:
        """Resume a failed import from last checkpoint."""
        return DataImportOutput(
            import_id=import_id,
            records_processed=0,
            records_succeeded=0,
            records_failed=0,
            duration_ms=0,
            quality_score=0.0,
            errors=[]
        )


# ============================
# NIGHTLY PROCESSING WORKFLOW
# ============================

@dataclass
class NightlyProcessingInput:
    """Input for nightly processing workflow."""
    date: datetime
    tenant_id: uuid.UUID


@dataclass
class NightlyProcessingOutput:
    """Output from nightly processing workflow."""
    date: datetime
    sync_completed: bool
    metrics_computed: int
    quality_issues_detected: int
    alerts_generated: int
    duration_ms: int


class NightlyProcessingWorkflow:
    """
    Orchestrates all nightly batch jobs.
    Runs in sequence with dependency management.
    
    Sequence:
    1. Sync PostgreSQL -> DuckDB
    2. Compute all daily metrics
    3. Run data quality checks
    4. Generate alerts
    5. Update dashboards
    6. Send nightly summary notifications
    """
    
    def __init__(self):
        self.retry_policy = RetryPolicy(
            max_attempts=3,
            initial_interval=timedelta(minutes=5)
        )
        self.timeout = timedelta(hours=4)
        self.schedule = WorkflowSchedule(cron="0 2 * * *")  # 2:00 AM daily
    
    async def execute(self, input: NightlyProcessingInput) -> NightlyProcessingOutput:
        """Execute the workflow."""
        return NightlyProcessingOutput(
            date=input.date,
            sync_completed=False,
            metrics_computed=0,
            quality_issues_detected=0,
            alerts_generated=0,
            duration_ms=0
        )


# ============================
# METRIC REFRESH WORKFLOW
# ============================

@dataclass
class MetricRefreshInput:
    """Input for metric refresh workflow."""
    tenant_id: uuid.UUID
    metric_codes: Optional[List[str]] = None
    scope: Optional[ComputationScope] = None


@dataclass
class MetricRefreshOutput:
    """Output from metric refresh workflow."""
    metrics_refreshed: int
    metrics_failed: int
    duration_ms: int


class MetricRefreshWorkflow:
    """
    Refreshes metrics on a schedule.
    Supports 15-minute and hourly refresh.
    """
    
    def __init__(self, interval_minutes: int = 15):
        self.interval_minutes = interval_minutes
        self.retry_policy = RetryPolicy(
            max_attempts=3,
            initial_interval=timedelta(minutes=1)
        )
        self.timeout = timedelta(minutes=10)
        self.schedule = WorkflowSchedule(cron=f"*/{interval_minutes} * * * *")
    
    async def execute(self, input: MetricRefreshInput) -> MetricRefreshOutput:
        """Execute the workflow."""
        return MetricRefreshOutput(
            metrics_refreshed=0,
            metrics_failed=0,
            duration_ms=0
        )


# ============================
# EXECUTIVE BRIEFING WORKFLOW
# ============================

@dataclass
class ExecutiveBriefingInput:
    """Input for executive briefing workflow."""
    period_start: datetime
    period_end: datetime
    recipients: List[uuid.UUID]
    tenant_id: uuid.UUID


@dataclass
class ExecutiveBriefingOutput:
    """Output from executive briefing workflow."""
    briefing_id: uuid.UUID
    report_generated: bool
    email_sent: bool
    dashboard_updated: bool
    duration_ms: int


class ExecutiveBriefingWorkflow:
    """
    Generates the monthly executive briefing.
    Triggers on first of each month.
    
    Workflow:
    1. Fetch all metrics for period
    2. Generate AI CFO narrative
    3. Compile insights and alerts
    4. Generate PDF report
    5. Send email to recipients
    6. Publish to dashboard
    """
    
    def __init__(self):
        self.retry_policy = RetryPolicy(
            max_attempts=3,
            initial_interval=timedelta(hours=1)
        )
        self.timeout = timedelta(hours=1)
        self.schedule = WorkflowSchedule(cron="0 8 1 * *")  # 8:00 AM on 1st of month
    
    async def execute(self, input: ExecutiveBriefingInput) -> ExecutiveBriefingOutput:
        """Execute the workflow."""
        return ExecutiveBriefingOutput(
            briefing_id=uuid.uuid4(),
            report_generated=False,
            email_sent=False,
            dashboard_updated=False,
            duration_ms=0
        )


# ============================
# WORKFLOW SCHEDULE CONFIGURATION
# ============================

WORKFLOW_SCHEDULES = {
    "nightly_processing": {
        "workflow": NightlyProcessingWorkflow,
        "schedule": WorkflowSchedule(cron="0 2 * * *"),
        "retry_policy": RetryPolicy(max_attempts=3, initial_interval=timedelta(minutes=5)),
        "timeout": timedelta(hours=4),
    },
    "metric_refresh_15m": {
        "workflow": MetricRefreshWorkflow,
        "schedule": WorkflowSchedule(cron="*/15 * * * *"),
        "retry_policy": RetryPolicy(max_attempts=3, initial_interval=timedelta(minutes=1)),
        "timeout": timedelta(minutes=10),
    },
    "metric_refresh_hourly": {
        "workflow": MetricRefreshWorkflow,
        "schedule": WorkflowSchedule(cron="0 * * * *"),
        "retry_policy": RetryPolicy(max_attempts=3),
        "timeout": timedelta(minutes=30),
    },
    "quality_check_6h": {
        "workflow": DataQualityWorkflow,
        "schedule": WorkflowSchedule(cron="0 */6 * * *"),
        "retry_policy": RetryPolicy(max_attempts=2, initial_interval=timedelta(minutes=15)),
        "timeout": timedelta(hours=2),
    },
    "executive_briefing_monthly": {
        "workflow": ExecutiveBriefingWorkflow,
        "schedule": WorkflowSchedule(cron="0 8 1 * *"),
        "retry_policy": RetryPolicy(max_attempts=3, initial_interval=timedelta(hours=1)),
        "timeout": timedelta(hours=1),
    },
}


# ============================
# ACTIVITY DEFINITIONS
# ============================

@dataclass
class ComputeMetricInput:
    """Input for compute metric activity."""
    metric_id: uuid.UUID
    tenant_id: uuid.UUID
    hospital_id: Optional[uuid.UUID] = None
    branch_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    period_type: str = "monthly"


@dataclass
class ComputeMetricOutput:
    """Output from compute metric activity."""
    success: bool
    computed_value_id: Optional[uuid.UUID] = None
    value: Optional[float] = None
    duration_ms: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class MetricActivities:
    """
    Activity methods for metric computation.
    Each is independently retryable with typed inputs/outputs.
    """
    
    async def compute_metric_value(self, input: ComputeMetricInput) -> ComputeMetricOutput:
        """Executes the SQL/Python for a single metric."""
        return ComputeMetricOutput(success=True)
    
    async def store_computed_value(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Persists computed value to PostgreSQL."""
        return {"success": True}
    
    async def validate_metric_result(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validates computed value against quality rules."""
        return {"passed": True}


@dataclass
class ParseFileInput:
    """Input for parse file activity."""
    file_path: str
    file_type: str  # csv, excel, json
    encoding: str = "UTF-8"
    delimiter: Optional[str] = None
    sheet_name: Optional[str] = None
    header_row: int = 1
    skip_rows: int = 0


@dataclass
class ParseFileOutput:
    """Output from parse file activity."""
    success: bool
    record_count: int
    headers: List[str]
    sample_records: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class ImportActivities:
    """
    Activity methods for data import.
    """
    
    async def parse_source_file(self, input: ParseFileInput) -> ParseFileOutput:
        """Parses CSV/Excel into typed records."""
        return ParseFileOutput(
            success=True,
            record_count=0,
            headers=[],
            sample_records=[],
            errors=[]
        )
    
    async def transform_record(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Applies transformation rules to a single record."""
        return {"success": True, "record": input}
    
    async def bulk_insert_records(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Batch inserts records into staging table."""
        return {"success": True, "inserted_count": 0}


@dataclass
class QualityCheckInput:
    """Input for quality check activity."""
    rule_id: uuid.UUID
    tenant_id: uuid.UUID
    entity_type: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


@dataclass
class QualityCheckOutput:
    """Output from quality check activity."""
    rule_id: uuid.UUID
    passed: bool
    issues_found: int
    details: Dict[str, Any]


class QualityActivities:
    """
    Activity methods for data quality checks.
    """
    
    async def execute_quality_rule(self, input: QualityCheckInput) -> QualityCheckOutput:
        """Execute a single quality rule."""
        return QualityCheckOutput(
            rule_id=input.rule_id,
            passed=True,
            issues_found=0,
            details={}
        )
    
    async def create_quality_issue(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Create a quality issue record."""
        return {"success": True, "issue_id": str(uuid.uuid4())}
    
    async def update_quality_score(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Update data quality score for a scope."""
        return {"success": True, "score": 0.0}
