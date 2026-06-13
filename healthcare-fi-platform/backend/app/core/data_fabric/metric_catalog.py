"""
BuildIT Canonical Metric Catalog — Single Source of Truth.
Every page, dashboard, AI, and report MUST use these definitions.
No page may define KPIs independently.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable
from enum import Enum


class MetricCategory(str, Enum):
    REVENUE = "revenue"
    PROFITABILITY = "profitability"
    OPERATIONS = "operations"
    REVENUE_CYCLE = "revenue_cycle"
    FINANCIAL_HEALTH = "financial_health"
    EFFICIENCY = "efficiency"
    WORKFORCE = "workforce"
    QUALITY = "quality"


class MetricUnit(str, Enum):
    CURRENCY = "currency"          # $, ₹
    PERCENT = "percent"            # %
    RATIO = "ratio"                # decimal ratio
    DAYS = "days"                  # days
    COUNT = "count"                # integer count
    CURRENCY_PER_UNIT = "currency_per_unit"  # $/bed, $/doctor
    HOURS = "hours"
    RATIO_PERCENT = "ratio_percent"  # displayed as %


@dataclass(frozen=True)
class MetricDefinition:
    """Immutable metric definition. The single source of truth."""
    code: str
    name: str
    description: str
    category: MetricCategory
    unit: MetricUnit
    formula: str
    owner: str  # department that owns this metric
    dimensions: list  # valid drill-down dimensions
    aggregation: str = "sum"  # sum, avg, last, max, min
    target: Optional[float] = None
    benchmark: Optional[float] = None
    benchmark_source: str = ""
    is_financial: bool = False
    lower_is_better: bool = False  # e.g., denial rate, ALOS


# ============================================================
# CANONICAL KPI CATALOG — Uncle's KPIs + Extended
# ============================================================

METRIC_CATALOG: Dict[str, MetricDefinition] = {}


def _register(m: MetricDefinition):
    METRIC_CATALOG[m.code] = m
    return m


# --- REVENUE ---

_register(MetricDefinition(
    code="GROSS_REVENUE",
    name="Gross Revenue",
    description="Total revenue before deductions",
    category=MetricCategory.REVENUE,
    unit=MetricUnit.CURRENCY,
    formula="SUM(revenues.amount)",
    owner="finance",
    dimensions=["department", "payer", "service_line", "month", "quarter"],
    aggregation="sum",
    is_financial=True,
))

_register(MetricDefinition(
    code="NET_REVENUE",
    name="Net Revenue",
    description="Revenue after contractual adjustments and bad debt",
    category=MetricCategory.REVENUE,
    unit=MetricUnit.CURRENCY,
    formula="SUM(revenues.net_amount)",
    owner="finance",
    dimensions=["department", "payer", "service_line", "month", "quarter"],
    aggregation="sum",
    is_financial=True,
))

_register(MetricDefinition(
    code="REVENUE_PER_DOCTOR",
    name="Revenue per Doctor",
    description="Average revenue generated per doctor",
    category=MetricCategory.EFFICIENCY,
    unit=MetricUnit.CURRENCY_PER_UNIT,
    formula="NET_REVENUE / COUNT(DISTINCT doctors.id)",
    owner="finance",
    dimensions=["department", "month", "quarter"],
    aggregation="avg",
))

# --- EXPENSE ---

_register(MetricDefinition(
    code="TOTAL_EXPENSES",
    name="Total Expenses",
    description="Total operating expenses",
    category=MetricCategory.PROFITABILITY,
    unit=MetricUnit.CURRENCY,
    formula="SUM(expenses.amount)",
    owner="finance",
    dimensions=["department", "category", "month", "quarter"],
    aggregation="sum",
    is_financial=True,
))

_register(MetricDefinition(
    code="LABOUR_COST_RATIO",
    name="Labour Cost Ratio",
    description="Staff costs as percentage of total revenue",
    category=MetricCategory.WORKFORCE,
    unit=MetricUnit.PERCENT,
    formula="LABOUR_COSTS / NET_REVENUE * 100",
    owner="hr",
    dimensions=["department", "month", "quarter"],
    aggregation="avg",
    lower_is_better=True,
    target=45.0,
    benchmark=42.0,
    benchmark_source="HFMA",
))

# --- PROFITABILITY ---

_register(MetricDefinition(
    code="EBITDA",
    name="EBITDA",
    description="Earnings Before Interest, Taxes, Depreciation, Amortization",
    category=MetricCategory.PROFITABILITY,
    unit=MetricUnit.CURRENCY,
    formula="NET_REVENUE - TOTAL_EXPENSES + DEPRECIATION + AMORTIZATION",
    owner="finance",
    dimensions=["department", "month", "quarter"],
    aggregation="sum",
    is_financial=True,
))

_register(MetricDefinition(
    code="EBITDA_MARGIN",
    name="EBITDA Margin",
    description="EBITDA as percentage of net revenue",
    category=MetricCategory.PROFITABILITY,
    unit=MetricUnit.PERCENT,
    formula="EBITDA / NET_REVENUE * 100",
    owner="finance",
    dimensions=["department", "month", "quarter"],
    aggregation="avg",
    is_financial=True,
    target=15.0,
    benchmark=12.0,
    benchmark_source="HFMA",
))

_register(MetricDefinition(
    code="NET_MARGIN",
    name="Net Profit Margin",
    description="Net income as percentage of revenue",
    category=MetricCategory.PROFITABILITY,
    unit=MetricUnit.PERCENT,
    formula="(NET_REVENUE - TOTAL_EXPENSES) / NET_REVENUE * 100",
    owner="finance",
    dimensions=["department", "month", "quarter"],
    aggregation="avg",
    is_financial=True,
))

# --- OPERATIONS ---

_register(MetricDefinition(
    code="OCCUPANCY_RATE",
    name="Bed Occupancy Rate",
    description="Percentage of beds occupied",
    category=MetricCategory.OPERATIONS,
    unit=MetricUnit.PERCENT,
    formula="occupied_beds / total_beds * 100",
    owner="operations",
    dimensions=["department", "month", "quarter"],
    aggregation="avg",
    target=85.0,
    benchmark=80.0,
    benchmark_source="AHA",
))

_register(MetricDefinition(
    code="ALOS",
    name="Average Length of Stay",
    description="Average number of days per patient stay",
    category=MetricCategory.OPERATIONS,
    unit=MetricUnit.DAYS,
    formula="SUM(stay_days) / COUNT(discharges)",
    owner="operations",
    dimensions=["department", "payer", "month", "quarter"],
    aggregation="avg",
    lower_is_better=True,
    target=4.5,
    benchmark=5.0,
    benchmark_source="CMS",
))

_register(MetricDefinition(
    code="CMI",
    name="Case Mix Index",
    description="Average DRG weight indicating patient complexity",
    category=MetricCategory.OPERATIONS,
    unit=MetricUnit.RATIO,
    formula="AVG(drg_weight)",
    owner="clinical",
    dimensions=["department", "month", "quarter"],
    aggregation="avg",
    benchmark=1.35,
    benchmark_source="CMS",
))

# --- REVENUE CYCLE ---

_register(MetricDefinition(
    code="CLAIM_DENIAL_RATE",
    name="Claim Denial Rate",
    description="Percentage of claims denied by payers",
    category=MetricCategory.REVENUE_CYCLE,
    unit=MetricUnit.PERCENT,
    formula="denied_claims / total_claims * 100",
    owner="revenue_cycle",
    dimensions=["payer", "department", "month", "quarter"],
    aggregation="avg",
    lower_is_better=True,
    target=5.0,
    benchmark=5.0,
    benchmark_source="HFMA",
))

_register(MetricDefinition(
    code="CLAIM_APPROVAL_RATE",
    name="Claim Approval Rate",
    description="Percentage of claims approved on first submission",
    category=MetricCategory.REVENUE_CYCLE,
    unit=MetricUnit.PERCENT,
    formula="approved_claims / total_claims * 100",
    owner="revenue_cycle",
    dimensions=["payer", "department", "month", "quarter"],
    aggregation="avg",
    target=95.0,
    benchmark=90.0,
    benchmark_source="HFMA",
))

_register(MetricDefinition(
    code="DAYS_IN_AR",
    name="Days in Accounts Receivable",
    description="Average number of days to collect payment",
    category=MetricCategory.REVENUE_CYCLE,
    unit=MetricUnit.DAYS,
    formula="AR_BALANCE / (NET_REVENUE / 365)",
    owner="revenue_cycle",
    dimensions=["payer", "department", "month", "quarter"],
    aggregation="avg",
    lower_is_better=True,
    target=40.0,
    benchmark=45.0,
    benchmark_source="HFMA",
))

_register(MetricDefinition(
    code="COLLECTION_EFFICIENCY",
    name="Collection Efficiency",
    description="Percentage of billed amount actually collected",
    category=MetricCategory.REVENUE_CYCLE,
    unit=MetricUnit.PERCENT,
    formula="COLLECTED_AMOUNT / BILLED_AMOUNT * 100",
    owner="revenue_cycle",
    dimensions=["payer", "department", "month", "quarter"],
    aggregation="avg",
    target=98.0,
    benchmark=95.0,
    benchmark_source="HFMA",
))

# --- FINANCIAL HEALTH ---

_register(MetricDefinition(
    code="OPERATING_CASH_FLOW",
    name="Operating Cash Flow",
    description="Cash generated from operations",
    category=MetricCategory.FINANCIAL_HEALTH,
    unit=MetricUnit.CURRENCY,
    formula="OPERATING_INCOME + DEPRECIATION - CHANGES_IN_WC",
    owner="finance",
    dimensions=["month", "quarter"],
    aggregation="sum",
    is_financial=True,
))

_register(MetricDefinition(
    code="WORKING_CAPITAL_RATIO",
    name="Working Capital Ratio",
    description="Current assets divided by current liabilities",
    category=MetricCategory.FINANCIAL_HEALTH,
    unit=MetricUnit.RATIO,
    formula="current_assets / current_liabilities",
    owner="finance",
    dimensions=["month", "quarter"],
    aggregation="last",
    target=1.5,
))

_register(MetricDefinition(
    code="ARPOB",
    name="Average Revenue Per Occupied Bed",
    description="Revenue per occupied bed per day",
    category=MetricCategory.EFFICIENCY,
    unit=MetricUnit.CURRENCY_PER_UNIT,
    formula="NET_REVENUE / (OCCUPIED_BEDS * DAYS_IN_PERIOD)",
    owner="finance",
    dimensions=["department", "month", "quarter"],
    aggregation="avg",
    benchmark=800.0,
    benchmark_source="Industry",
))


# ============================================================
# PUBLIC API
# ============================================================

def get_metric(code: str) -> Optional[MetricDefinition]:
    """Get a metric definition by code."""
    return METRIC_CATALOG.get(code)


def get_all_metrics() -> Dict[str, MetricDefinition]:
    """Get the entire metric catalog."""
    return dict(METRIC_CATALOG)


def get_metrics_by_category(category: MetricCategory) -> list[MetricDefinition]:
    """Get all metrics in a category."""
    return [m for m in METRIC_CATALOG.values() if m.category == category]


def get_executive_kpis() -> list[MetricDefinition]:
    """Get the core KPIs for the Executive Center."""
    executive_codes = [
        "GROSS_REVENUE", "NET_REVENUE", "EBITDA", "EBITDA_MARGIN",
        "OCCUPANCY_RATE", "CLAIM_DENIAL_RATE", "DAYS_IN_AR",
        "ALOS", "LABOUR_COST_RATIO", "OPERATING_CASH_FLOW",
        "ARPOB", "COLLECTION_EFFICIENCY",
    ]
    return [METRIC_CATALOG[c] for c in executive_codes if c in METRIC_CATALOG]


def metric_to_dict(m: MetricDefinition) -> Dict[str, Any]:
    """Serialize a metric definition for API responses."""
    return {
        "code": m.code,
        "name": m.name,
        "description": m.description,
        "category": m.category.value,
        "unit": m.unit.value,
        "formula": m.formula,
        "owner": m.owner,
        "dimensions": m.dimensions,
        "aggregation": m.aggregation,
        "target": m.target,
        "benchmark": m.benchmark,
        "benchmark_source": m.benchmark_source,
        "is_financial": m.is_financial,
        "lower_is_better": m.lower_is_better,
    }
