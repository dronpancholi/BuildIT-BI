"""Self-Service Analytics Layer domain models for healthcare financial platform."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MetricCategory(str, Enum):
    """Categories for semantic metrics."""

    REVENUE = "REVENUE"
    COST = "COST"
    QUALITY = "QUALITY"
    OPERATIONS = "OPERATIONS"
    PATIENT = "PATIENT"
    FINANCIAL = "FINANCIAL"
    COMPLIANCE = "COMPLIANCE"


class AggregationType(str, Enum):
    """Supported aggregation functions for metrics."""

    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    MIN = "MIN"
    MAX = "MAX"


class Operator(str, Enum):
    """Arithmetic operators used in metric formulas."""

    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    PERCENTAGE = "PERCENTAGE"


class FormulaComponentType(str, Enum):
    """Types of components that can appear in a metric formula."""

    METRIC = "metric"
    CONSTANT = "constant"
    OPERATOR = "operator"


class Cardinality(str, Enum):
    """Cardinality of a dimension."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class FilterOperator(str, Enum):
    """Operators supported in filter specifications."""

    EQ = "EQ"
    NEQ = "NEQ"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    IN = "IN"
    NOT_IN = "NOT_IN"
    LIKE = "LIKE"
    BETWEEN = "BETWEEN"


class TimeRangeRelative(str, Enum):
    """Pre-defined relative time ranges."""

    TODAY = "TODAY"
    THIS_WEEK = "THIS_WEEK"
    THIS_MONTH = "THIS_MONTH"
    THIS_QUARTER = "THIS_QUARTER"
    THIS_YEAR = "THIS_YEAR"
    LAST_7_DAYS = "LAST_7_DAYS"
    LAST_30_DAYS = "LAST_30_DAYS"
    LAST_90_DAYS = "LAST_90_DAYS"
    LAST_12_MONTHS = "LAST_12_MONTHS"
    CUSTOM = "CUSTOM"


class ComparisonType(str, Enum):
    """Types of period comparisons for queries."""

    NONE = "NONE"
    PERIOD_OVER_PERIOD = "PERIOD_OVER_PERIOD"
    YEAR_OVER_YEAR = "YEAR_OVER_YEAR"
    CUSTOM = "CUSTOM"


class AccessLevel(str, Enum):
    """Access control levels for saved reports."""

    PRIVATE = "PRIVATE"
    TEAM = "TEAM"
    ORGANIZATION = "ORGANIZATION"
    PUBLIC = "PUBLIC"


class ParameterType(str, Enum):
    """Types of query parameters that can be exposed to end-users."""

    TEXT = "TEXT"
    SELECT = "SELECT"
    DATE_RANGE = "DATE_RANGE"
    NUMBER = "NUMBER"


# ---------------------------------------------------------------------------
# Formula Components
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class FormulaComponent:
    """A single component inside a metric formula.

    When *type* is ``METRIC`` the *value* references another metric slug.
    When *type* is ``CONSTANT`` the *value* is a numeric literal.
    When *type* is ``OPERATOR`` the *value* is an :class:`Operator` member name.
    """

    type: FormulaComponentType
    value: str
    aggregation: Optional[AggregationType] = None


@dataclass(kw_only=True)
class MetricFormula:
    """An ordered list of :class:`FormulaComponent` instances that define how a
    derived metric is calculated."""

    components: list[FormulaComponent] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def to_json(self) -> dict[str, Any]:
        """Serialise the formula to a JSON-safe dictionary."""
        return {
            "components": [
                {
                    "type": c.type.value,
                    "value": c.value,
                    **(({"aggregation": c.aggregation.value}) if c.aggregation else {}),
                }
                for c in self.components
            ]
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> MetricFormula:
        """Deserialise a formula from a dictionary (e.g. from JSON)."""
        components = []
        for item in data.get("components", []):
            agg = AggregationType(item["aggregation"]) if "aggregation" in item else None
            components.append(
                FormulaComponent(
                    type=FormulaComponentType(item["type"]),
                    value=item["value"],
                    aggregation=agg,
                )
            )
        return cls(components=components)


# ---------------------------------------------------------------------------
# Semantic Metric
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class SemanticMetric:
    """A governed, well-defined metric that can be used across the analytics
    layer."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    description: str = ""
    formula_json: dict[str, Any] = field(default_factory=dict)
    unit: str = ""
    aggregation: AggregationType = AggregationType.SUM
    format_pattern: str = ""
    category: MetricCategory = MetricCategory.FINANCIAL
    tags: list[str] = field(default_factory=list)
    created_by: str = ""
    version: int = 1
    is_certified: bool = False
    certified_by: Optional[str] = None
    is_deprecated: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def formula(self) -> MetricFormula:
        """Return the formula as a typed :class:`MetricFormula` object."""
        return MetricFormula.from_json(self.formula_json)

    @formula.setter
    def formula(self, value: MetricFormula) -> None:
        self.formula_json = value.to_json()


# ---------------------------------------------------------------------------
# Dimension & Hierarchy
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class DimensionHierarchy:
    """Describes a parent-child hierarchy within a dimension (e.g. Region >
    State > City)."""

    levels: list[str] = field(default_factory=list)
    member_table: str = ""
    parent_column: str = ""
    child_column: str = ""


@dataclass(kw_only=True)
class Dimension:
    """A categorical axis along which metrics can be sliced and diced."""

    id: UUID = field(default_factory=uuid4)
    slug: str = ""
    name: str = ""
    table_name: str = ""
    column_name: str = ""
    hierarchy_json: Optional[dict[str, Any]] = None
    cardinality: Cardinality = Cardinality.MEDIUM
    values: list[str] = field(default_factory=list)
    description: str = ""

    @property
    def hierarchy(self) -> Optional[DimensionHierarchy]:
        """Return the hierarchy as a typed object, if present."""
        if self.hierarchy_json is None:
            return None
        data = self.hierarchy_json
        return DimensionHierarchy(
            levels=data.get("levels", []),
            member_table=data.get("member_table", ""),
            parent_column=data.get("parent_column", ""),
            child_column=data.get("child_column", ""),
        )

    @hierarchy.setter
    def hierarchy(self, value: Optional[DimensionHierarchy]) -> None:
        if value is None:
            self.hierarchy_json = None
        else:
            self.hierarchy_json = {
                "levels": value.levels,
                "member_table": value.member_table,
                "parent_column": value.parent_column,
                "child_column": value.child_column,
            }


# ---------------------------------------------------------------------------
# Filter & Time Range
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class FilterSpec:
    """A single filter condition applied to a dimension."""

    dimension_slug: str = ""
    operator: FilterOperator = FilterOperator.EQ
    values: list[Any] = field(default_factory=list)


@dataclass(kw_only=True)
class TimeRange:
    """Defines the time window for a query, either explicit dates or a
    relative preset."""

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    relative: TimeRangeRelative = TimeRangeRelative.THIS_MONTH
    custom_days: Optional[int] = None


# ---------------------------------------------------------------------------
# Semantic Query
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class SemanticQuery:
    """A high-level, intent-driven query submitted through the self-service
    analytics API."""

    metric_ids: list[UUID] = field(default_factory=list)
    dimension_ids: list[UUID] = field(default_factory=list)
    filters: list[FilterSpec] = field(default_factory=list)
    time_range: TimeRange = field(default_factory=TimeRange)
    comparison: ComparisonType = ComparisonType.NONE


# ---------------------------------------------------------------------------
# Saved Report
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class SavedReport:
    """A persisted analytics report that can be shared, scheduled, and
    versioned."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    metric_ids: list[UUID] = field(default_factory=list)
    dimension_ids: list[UUID] = field(default_factory=list)
    filters: list[FilterSpec] = field(default_factory=list)
    time_range: TimeRange = field(default_factory=TimeRange)
    visualization_configs: list[dict[str, Any]] = field(default_factory=list)
    is_template: bool = False
    template_category: Optional[str] = None
    owner_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    access_level: AccessLevel = AccessLevel.PRIVATE
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_accessed_at: Optional[datetime] = None
    access_count: int = 0


# ---------------------------------------------------------------------------
# Query Parameters & Templates
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class QueryParameter:
    """A parameter that can be bound to a query template, allowing end-users to
    customise report inputs."""

    name: str = ""
    type: ParameterType = ParameterType.TEXT
    required: bool = True
    default: Optional[Any] = None
    options: list[Any] = field(default_factory=list)


@dataclass(kw_only=True)
class QueryTemplate:
    """A reusable query skeleton with parameterised placeholders."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    partial_query_json: dict[str, Any] = field(default_factory=dict)
    parameters: list[QueryParameter] = field(default_factory=list)
