"""
Query Engine Domain - Query execution pipeline for healthcare financial analytics.

Provides semantic query planning, SQL generation, and execution capabilities.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Query Plan
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class QueryPlan:
    """Structured representation of a query to be executed against the analytics store."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    metrics: list[str] = field(default_factory=list)
    dimensions: list[str] = field(default_factory=list)
    filters: list[dict[str, Any]] = field(default_factory=list)
    time_range: dict[str, Any] = field(default_factory=dict)
    comparison: Optional[dict[str, Any]] = None
    join_order: list[str] = field(default_factory=list)
    group_by: list[str] = field(default_factory=list)
    order_by: list[dict[str, Any]] = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    dialect: str = "postgresql"


# ---------------------------------------------------------------------------
# Query Result
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class QueryResult:
    """Result of an executed query."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    plan_id: uuid.UUID = field(default_factory=uuid.uuid4)
    columns: list[dict[str, Any]] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    data_freshness: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Query Context
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class QueryContext:
    """Tenant and user context applied to every query."""

    tenant_id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    default_currency: str = "USD"
    user_preferences: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Saved Query
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class SavedQuery:
    """A persisted semantic query that can be reused or shared."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    description: str = ""
    semantic_query_json: dict[str, Any] = field(default_factory=dict)
    created_by: uuid.UUID = field(default_factory=uuid.uuid4)
    access_level: str = "private"
    is_shared: bool = False
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Query Template
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class QueryParameter:
    """A single parameter within a query template."""

    name: str = ""
    type: str = "string"
    default: Optional[Any] = None
    required: bool = True
    description: str = ""


@dataclass(kw_only=True)
class QueryTemplate:
    """A reusable query skeleton with pluggable parameters."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    description: str = ""
    partial_query_json: dict[str, Any] = field(default_factory=dict)
    parameters: list[QueryParameter] = field(default_factory=list)


# ---------------------------------------------------------------------------
# SQL Generator
# ---------------------------------------------------------------------------

# Operators that map semantic filter operators to SQL operators
_FILTER_OP_MAP: dict[str, str] = {
    "eq": "=",
    "neq": "!=",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "in": "IN",
    "not_in": "NOT IN",
    "like": "LIKE",
    "not_like": "NOT LIKE",
    "is_null": "IS NULL",
    "is_not_null": "IS NOT NULL",
    "between": "BETWEEN",
}


class SQLGenerator:
    """Generates ANSI-compliant SQL from a QueryPlan.

    Supports ``postgresql`` (default) and ``trino`` dialects.
    """

    def generate_sql(self, plan: QueryPlan) -> str:
        """Return the full SQL statement for *plan*."""
        parts: list[str] = []
        parts.append(self._build_select(plan))
        parts.append(self._build_from(plan))

        where = self._build_where(plan)
        if where:
            parts.append(where)

        group_by = self._build_group_by(plan)
        if group_by:
            parts.append(group_by)

        order_by = self._build_order_by(plan)
        if order_by:
            parts.append(order_by)

        if plan.limit is not None:
            parts.append(f"LIMIT {plan.limit}")
        if plan.offset is not None:
            parts.append(f"OFFSET {plan.offset}")

        return "\n".join(parts)

    # -- SELECT ---------------------------------------------------------------

    def _build_select(self, plan: QueryPlan) -> str:
        """Build the SELECT clause from metrics and dimensions."""
        columns: list[str] = []

        for dim in plan.dimensions:
            columns.append(dim)

        for metric in plan.metrics:
            columns.append(metric)

        if not columns:
            columns.append("*")

        select_clause = ",\n       ".join(columns)
        return f"SELECT\n       {select_clause}"

    # -- FROM -----------------------------------------------------------------

    def _build_from(self, plan: QueryPlan) -> str:
        """Build the FROM clause using the join order."""
        if not plan.join_order:
            return "FROM analytics"
        if len(plan.join_order) == 1:
            return f"FROM {plan.join_order[0]}"

        # Sequential LEFT JOINs
        base = plan.join_order[0]
        joins: list[str] = [f"FROM {base}"]
        for table in plan.join_order[1:]:
            joins.append(f"LEFT JOIN {table} ON {base}.id = {table}.{base}_id")
        return "\n".join(joins)

    # -- WHERE ----------------------------------------------------------------

    def _build_where(self, plan: QueryPlan) -> str:
        """Build the WHERE clause from filters and time range."""
        conditions: list[str] = []

        for flt in plan.filters:
            cond = self._render_filter(flt)
            if cond:
                conditions.append(cond)

        # Apply time range
        time_conditions = self._apply_time_range(plan)
        if time_conditions:
            conditions.append(time_conditions)

        if not conditions:
            return ""

        where_block = "\n  AND ".join(conditions)
        return f"WHERE\n  {where_block}"

    # -- GROUP BY -------------------------------------------------------------

    def _build_group_by(self, plan: QueryPlan) -> str:
        """Build the GROUP BY clause."""
        if not plan.group_by:
            return ""
        return f"GROUP BY {', '.join(plan.group_by)}"

    # -- ORDER BY -------------------------------------------------------------

    def _build_order_by(self, plan: QueryPlan) -> str:
        """Build the ORDER BY clause."""
        if not plan.order_by:
            return ""

        clauses: list[str] = []
        for item in plan.order_by:
            column = item.get("column", "")
            direction = item.get("direction", "ASC").upper()
            clauses.append(f"{column} {direction}")
        return f"ORDER BY {', '.join(clauses)}"

    # -- Time Range -----------------------------------------------------------

    def _apply_time_range(self, plan: QueryPlan) -> str:
        """Return a SQL condition string for the plan's time_range, or '' if empty."""
        if not plan.time_range:
            return ""

        date_column = plan.time_range.get("date_column", "report_date")

        # Explicit start/end take precedence over preset ranges
        start = plan.time_range.get("start")
        end = plan.time_range.get("end")
        if start and end:
            return f"{date_column} BETWEEN '{start}' AND '{end}'"
        if start:
            return f"{date_column} >= '{start}'"
        if end:
            return f"{date_column} <= '{end}'"

        range_type = plan.time_range.get("range", "last_30_days")

        range_map: dict[str, str] = {
            "today": f"{date_column} = CURRENT_DATE",
            "yesterday": f"{date_column} = CURRENT_DATE - INTERVAL '1 day'",
            "last_7_days": f"{date_column} >= CURRENT_DATE - INTERVAL '7 days'",
            "last_30_days": f"{date_column} >= CURRENT_DATE - INTERVAL '30 days'",
            "last_90_days": f"{date_column} >= CURRENT_DATE - INTERVAL '90 days'",
            "this_month": f"{date_column} >= date_trunc('month', CURRENT_DATE)",
            "last_month": f"{date_column} >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month') "
                          f"AND {date_column} < date_trunc('month', CURRENT_DATE)",
            "this_quarter": f"{date_column} >= date_trunc('quarter', CURRENT_DATE)",
            "this_year": f"{date_column} >= date_trunc('year', CURRENT_DATE)",
            "last_year": f"{date_column} >= date_trunc('year', CURRENT_DATE - INTERVAL '1 year') "
                         f"AND {date_column} < date_trunc('year', CURRENT_DATE)",
        }

        if range_type in range_map:
            return range_map[range_type]

        return ""

    # -- Comparison -----------------------------------------------------------

    def _apply_comparison(self, plan: QueryPlan) -> str:
        """Return a SQL fragment for period-over-period comparison.

        The comparison dict is expected to contain:
            - ``type``: "yoy", "mom", "qoq", or "custom"
            - ``metric``: the metric alias to compare
            - ``offset``: optional custom interval expression
        """
        if not plan.comparison:
            return ""

        comp_type = plan.comparison.get("type", "")
        metric = plan.comparison.get("metric", "")
        alias = plan.comparison.get("alias", f"{metric}_prev")

        offset_map: dict[str, str] = {
            "yoy": "INTERVAL '1 year'",
            "mom": "INTERVAL '1 month'",
            "qoq": "INTERVAL '1 quarter'",
        }

        offset = plan.comparison.get("offset") or offset_map.get(comp_type, "INTERVAL '1 year'")

        return (
            f"LAG({metric}) OVER (ORDER BY report_date) AS {alias}, "
            f"{metric} - LAG({metric}) OVER (ORDER BY report_date) AS {alias}_delta"
        )

    # -- Helpers ---------------------------------------------------------------

    def _render_filter(self, flt: dict[str, Any]) -> str:
        """Render a single filter dict into a SQL condition fragment."""
        column = flt.get("column", "")
        op = flt.get("operator", "eq")
        value = flt.get("value")

        sql_op = _FILTER_OP_MAP.get(op, "=")

        if op in ("is_null", "is_not_null"):
            return f"{column} {sql_op}"

        if op in ("in", "not_in") and isinstance(value, list):
            elements = ", ".join(
                f"'{v}'" if isinstance(v, str) else str(v) for v in value
            )
            return f"{column} {sql_op} ({elements})"

        if op == "between" and isinstance(value, (list, tuple)) and len(value) == 2:
            return f"{column} BETWEEN '{value[0]}' AND '{value[1]}'"

        if isinstance(value, str):
            return f"{column} {sql_op} '{value}'"

        return f"{column} {sql_op} {value}"


# ---------------------------------------------------------------------------
# Query Executor (stub — real implementation would use a DB connection pool)
# ---------------------------------------------------------------------------

class QueryExecutor:
    """Executes SQL and QueryPlans, returning QueryResult objects.

    In production this class wraps an async database connection pool.  The
    current implementation is a synchronous stub that returns empty results
    so that the domain layer is testable without infrastructure.
    """

    def __init__(self, *, context: Optional[QueryContext] = None) -> None:
        self.context = context or QueryContext()
        self._generator = SQLGenerator()

    # -- Public API -----------------------------------------------------------

    def execute(self, query: str) -> dict[str, Any]:
        """Execute raw SQL and return a result dict.

        Returns a dict with keys: ``columns``, ``rows``, ``row_count``,
        ``execution_time_ms``.
        """
        # Placeholder — would execute against a real database.
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time_ms": 0.0,
        }

    def execute_with_plan(self, plan: QueryPlan) -> QueryResult:
        """Generate SQL from *plan*, execute it, and return a ``QueryResult``."""
        sql = self._generator.generate_sql(plan)
        raw = self.execute(sql)

        return QueryResult(
            plan_id=plan.id,
            columns=raw.get("columns", []),
            rows=raw.get("rows", []),
            row_count=raw.get("row_count", 0),
            execution_time_ms=raw.get("execution_time_ms", 0.0),
            data_freshness=datetime.now(timezone.utc),
            metadata={"sql": sql, "dialect": plan.dialect},
        )
