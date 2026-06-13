"""Tests for the Query Engine domain."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.domain.query_engine import (
    QueryContext,
    QueryExecutor,
    QueryParameter,
    QueryPlan,
    QueryResult,
    QueryTemplate,
    SQLGenerator,
    SavedQuery,
)


# ---------------------------------------------------------------------------
# QueryPlan
# ---------------------------------------------------------------------------

class TestQueryPlan:
    def test_default_construction(self) -> None:
        plan = QueryPlan()
        assert isinstance(plan.id, uuid.UUID)
        assert plan.metrics == []
        assert plan.dimensions == []
        assert plan.filters == []
        assert plan.time_range == {}
        assert plan.comparison is None
        assert plan.join_order == []
        assert plan.group_by == []
        assert plan.order_by == []
        assert plan.limit is None
        assert plan.offset is None
        assert plan.dialect == "postgresql"

    def test_construction_with_values(self) -> None:
        plan = QueryPlan(
            metrics=["SUM(charge_amount)", "COUNT(*)"],
            dimensions=["payer_name", "service_line"],
            filters=[
                {"column": "status", "operator": "eq", "value": "posted"},
            ],
            time_range={"date_column": "service_date", "range": "this_month"},
            join_order=["claims", "payers"],
            group_by=["payer_name", "service_line"],
            order_by=[{"column": "SUM(charge_amount)", "direction": "DESC"}],
            limit=100,
            offset=20,
            dialect="trino",
        )
        assert len(plan.metrics) == 2
        assert len(plan.dimensions) == 2
        assert len(plan.filters) == 1
        assert plan.time_range["range"] == "this_month"
        assert plan.join_order == ["claims", "payers"]
        assert plan.group_by == ["payer_name", "service_line"]
        assert len(plan.order_by) == 1
        assert plan.limit == 100
        assert plan.offset == 20
        assert plan.dialect == "trino"

    def test_comparison_set(self) -> None:
        comp = {"type": "yoy", "metric": "net_revenue"}
        plan = QueryPlan(comparison=comp)
        assert plan.comparison is not None
        assert plan.comparison["type"] == "yoy"

    def test_unique_ids(self) -> None:
        p1 = QueryPlan()
        p2 = QueryPlan()
        assert p1.id != p2.id


# ---------------------------------------------------------------------------
# QueryResult
# ---------------------------------------------------------------------------

class TestQueryResult:
    def test_default_construction(self) -> None:
        result = QueryResult()
        assert isinstance(result.id, uuid.UUID)
        assert isinstance(result.plan_id, uuid.UUID)
        assert result.columns == []
        assert result.rows == []
        assert result.row_count == 0
        assert result.execution_time_ms == 0.0
        assert isinstance(result.data_freshness, datetime)
        assert result.metadata == {}

    def test_construction_with_values(self) -> None:
        result = QueryResult(
            plan_id=uuid.uuid4(),
            columns=[
                {"name": "payer_name", "type": "varchar"},
                {"name": "total", "type": "numeric"},
            ],
            rows=[["Medicare", 123456.78], ["Medicaid", 98765.43]],
            row_count=2,
            execution_time_ms=42.5,
            metadata={"sql": "SELECT ...", "rows_affected": 2},
        )
        assert result.row_count == 2
        assert result.execution_time_ms == 42.5
        assert len(result.columns) == 2
        assert result.rows[0][0] == "Medicare"

    def test_unique_ids(self) -> None:
        r1 = QueryResult()
        r2 = QueryResult()
        assert r1.id != r2.id


# ---------------------------------------------------------------------------
# QueryContext
# ---------------------------------------------------------------------------

class TestQueryContext:
    def test_default_construction(self) -> None:
        ctx = QueryContext()
        assert isinstance(ctx.tenant_id, uuid.UUID)
        assert isinstance(ctx.user_id, uuid.UUID)
        assert ctx.default_currency == "USD"
        assert ctx.user_preferences == {}

    def test_construction_with_values(self) -> None:
        ctx = QueryContext(
            tenant_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            user_id=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            default_currency="EUR",
            user_preferences={"theme": "dark", "locale": "de-DE"},
        )
        assert ctx.tenant_id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert ctx.default_currency == "EUR"
        assert ctx.user_preferences["theme"] == "dark"


# ---------------------------------------------------------------------------
# SavedQuery
# ---------------------------------------------------------------------------

class TestSavedQuery:
    def test_default_construction(self) -> None:
        sq = SavedQuery()
        assert isinstance(sq.id, uuid.UUID)
        assert sq.name == ""
        assert sq.description == ""
        assert sq.semantic_query_json == {}
        assert isinstance(sq.created_by, uuid.UUID)
        assert sq.access_level == "private"
        assert sq.is_shared is False
        assert sq.tags == []
        assert isinstance(sq.created_at, datetime)
        assert isinstance(sq.updated_at, datetime)

    def test_construction_with_values(self) -> None:
        sq = SavedQuery(
            name="Monthly Denials by Payer",
            description="Tracks denial amounts grouped by payer for the current month.",
            semantic_query_json={
                "metrics": ["denial_amount"],
                "dimensions": ["payer_name"],
                "filters": [{"column": "status", "operator": "eq", "value": "denied"}],
            },
            created_by=uuid.uuid4(),
            access_level="shared",
            is_shared=True,
            tags=["denials", "monthly", "payer"],
        )
        assert sq.name == "Monthly Denials by Payer"
        assert sq.is_shared is True
        assert len(sq.tags) == 3

    def test_unique_ids(self) -> None:
        s1 = SavedQuery()
        s2 = SavedQuery()
        assert s1.id != s2.id


# ---------------------------------------------------------------------------
# QueryTemplate & QueryParameter
# ---------------------------------------------------------------------------

class TestQueryTemplate:
    def test_default_construction(self) -> None:
        qt = QueryTemplate()
        assert isinstance(qt.id, uuid.UUID)
        assert qt.name == ""
        assert qt.partial_query_json == {}
        assert qt.parameters == []

    def test_construction_with_parameters(self) -> None:
        qt = QueryTemplate(
            name="Denial Trend",
            description="Denial trend over a configurable date range.",
            partial_query_json={
                "metrics": ["total_denials"],
                "time_range": {"date_column": "{{date_column}}", "range": "{{range}}"},
            },
            parameters=[
                QueryParameter(
                    name="date_column",
                    type="string",
                    default="report_date",
                    required=True,
                    description="Column to use for date filtering.",
                ),
                QueryParameter(
                    name="range",
                    type="string",
                    default="last_30_days",
                    required=False,
                    description="Preset time range.",
                ),
            ],
        )
        assert qt.name == "Denial Trend"
        assert len(qt.parameters) == 2
        assert qt.parameters[0].name == "date_column"
        assert qt.parameters[0].required is True
        assert qt.parameters[1].default == "last_30_days"

    def test_unique_ids(self) -> None:
        t1 = QueryTemplate()
        t2 = QueryTemplate()
        assert t1.id != t2.id


# ---------------------------------------------------------------------------
# SQLGenerator
# ---------------------------------------------------------------------------

class TestSQLGenerator:
    def setup_method(self) -> None:
        self.gen = SQLGenerator()

    def test_simple_select_star(self) -> None:
        plan = QueryPlan()
        sql = self.gen.generate_sql(plan)
        assert "SELECT" in sql
        assert "*" in sql
        assert "FROM analytics" in sql

    def test_select_with_metrics_and_dimensions(self) -> None:
        plan = QueryPlan(
            metrics=["SUM(charge_amount) AS total_charges"],
            dimensions=["payer_name"],
        )
        sql = self.gen.generate_sql(plan)
        assert "payer_name" in sql
        assert "SUM(charge_amount) AS total_charges" in sql
        assert sql.startswith("SELECT")

    def test_group_by(self) -> None:
        plan = QueryPlan(
            metrics=["SUM(charge_amount)"],
            dimensions=["payer_name"],
            group_by=["payer_name"],
        )
        sql = self.gen.generate_sql(plan)
        assert "GROUP BY payer_name" in sql

    def test_order_by(self) -> None:
        plan = QueryPlan(
            metrics=["SUM(charge_amount)"],
            order_by=[{"column": "total", "direction": "DESC"}],
        )
        sql = self.gen.generate_sql(plan)
        assert "ORDER BY total DESC" in sql

    def test_limit_offset(self) -> None:
        plan = QueryPlan(limit=50, offset=10)
        sql = self.gen.generate_sql(plan)
        assert "LIMIT 50" in sql
        assert "OFFSET 10" in sql

    def test_single_table_join(self) -> None:
        plan = QueryPlan(join_order=["claims"])
        sql = self.gen.generate_sql(plan)
        assert "FROM claims" in sql
        assert "LEFT JOIN" not in sql

    def test_multi_table_join(self) -> None:
        plan = QueryPlan(join_order=["claims", "payers", "providers"])
        sql = self.gen.generate_sql(plan)
        assert "LEFT JOIN payers ON claims.id = payers.claims_id" in sql
        assert "LEFT JOIN providers ON claims.id = providers.claims_id" in sql

    def test_filter_eq(self) -> None:
        plan = QueryPlan(
            filters=[{"column": "status", "operator": "eq", "value": "posted"}],
        )
        sql = self.gen.generate_sql(plan)
        assert "WHERE" in sql
        assert "status = 'posted'" in sql

    def test_filter_in(self) -> None:
        plan = QueryPlan(
            filters=[{"column": "payer_id", "operator": "in", "value": [1, 2, 3]}],
        )
        sql = self.gen.generate_sql(plan)
        assert "payer_id IN (1, 2, 3)" in sql

    def test_filter_between(self) -> None:
        plan = QueryPlan(
            filters=[{"column": "amount", "operator": "between", "value": [100, 500]}],
        )
        sql = self.gen.generate_sql(plan)
        assert "amount BETWEEN '100' AND '500'" in sql

    def test_filter_is_null(self) -> None:
        plan = QueryPlan(
            filters=[{"column": "denial_reason", "operator": "is_null", "value": None}],
        )
        sql = self.gen.generate_sql(plan)
        assert "denial_reason IS NULL" in sql

    def test_filter_is_not_null(self) -> None:
        plan = QueryPlan(
            filters=[{"column": "denial_reason", "operator": "is_not_null", "value": None}],
        )
        sql = self.gen.generate_sql(plan)
        assert "denial_reason IS NOT NULL" in sql

    def test_filter_gt(self) -> None:
        plan = QueryPlan(
            filters=[{"column": "amount", "operator": "gt", "value": 1000}],
        )
        sql = self.gen.generate_sql(plan)
        assert "amount > 1000" in sql

    def test_filter_neq(self) -> None:
        plan = QueryPlan(
            filters=[{"column": "status", "operator": "neq", "value": "void"}],
        )
        sql = self.gen.generate_sql(plan)
        assert "status != 'void'" in sql

    def test_time_range_last_30_days(self) -> None:
        plan = QueryPlan(time_range={"date_column": "service_date", "range": "last_30_days"})
        sql = self.gen.generate_sql(plan)
        assert "service_date >= CURRENT_DATE - INTERVAL '30 days'" in sql

    def test_time_range_this_month(self) -> None:
        plan = QueryPlan(time_range={"date_column": "report_date", "range": "this_month"})
        sql = self.gen.generate_sql(plan)
        assert "date_trunc('month', CURRENT_DATE)" in sql

    def test_time_range_last_month(self) -> None:
        plan = QueryPlan(time_range={"date_column": "report_date", "range": "last_month"})
        sql = self.gen.generate_sql(plan)
        assert "date_trunc('month', CURRENT_DATE - INTERVAL '1 month')" in sql
        assert "date_trunc('month', CURRENT_DATE)" in sql

    def test_time_range_explicit_start_end(self) -> None:
        plan = QueryPlan(
            time_range={"date_column": "report_date", "start": "2025-01-01", "end": "2025-01-31"}
        )
        sql = self.gen.generate_sql(plan)
        assert "report_date BETWEEN '2025-01-01' AND '2025-01-31'" in sql

    def test_time_range_start_only(self) -> None:
        plan = QueryPlan(time_range={"date_column": "report_date", "start": "2025-06-01"})
        sql = self.gen.generate_sql(plan)
        assert "report_date >= '2025-06-01'" in sql

    def test_time_range_end_only(self) -> None:
        plan = QueryPlan(time_range={"date_column": "report_date", "end": "2025-06-30"})
        sql = self.gen.generate_sql(plan)
        assert "report_date <= '2025-06-30'" in sql

    def test_time_range_unknown_preset(self) -> None:
        plan = QueryPlan(time_range={"date_column": "report_date", "range": "next_century"})
        sql = self.gen.generate_sql(plan)
        # Unknown range without start/end yields no time condition
        assert "WHERE" not in sql

    def test_comparison_yoy(self) -> None:
        plan = QueryPlan(comparison={"type": "yoy", "metric": "net_revenue"})
        fragment = self.gen._apply_comparison(plan)
        assert "LAG(net_revenue)" in fragment
        assert "net_revenue_prev" in fragment
        assert "net_revenue_prev_delta" in fragment

    def test_comparison_mom(self) -> None:
        plan = QueryPlan(comparison={"type": "mom", "metric": "total_charges"})
        fragment = self.gen._apply_comparison(plan)
        assert "LAG(total_charges)" in fragment

    def test_comparison_none(self) -> None:
        plan = QueryPlan(comparison=None)
        fragment = self.gen._apply_comparison(plan)
        assert fragment == ""

    def test_full_query_combined(self) -> None:
        """End-to-end test: metrics, dimensions, filters, time range, group, order, limit."""
        plan = QueryPlan(
            metrics=["SUM(charge_amount) AS total_charges", "COUNT(*) AS claim_count"],
            dimensions=["payer_name", "service_line"],
            filters=[
                {"column": "status", "operator": "neq", "value": "void"},
                {"column": "amount", "operator": "gt", "value": 0},
            ],
            time_range={"date_column": "service_date", "range": "this_quarter"},
            join_order=["claims", "payers"],
            group_by=["payer_name", "service_line"],
            order_by=[{"column": "total_charges", "direction": "DESC"}],
            limit=50,
        )
        sql = self.gen.generate_sql(plan)
        assert "SELECT" in sql
        assert "payer_name" in sql
        assert "service_line" in sql
        assert "SUM(charge_amount) AS total_charges" in sql
        assert "LEFT JOIN payers" in sql
        assert "WHERE" in sql
        assert "status != 'void'" in sql
        assert "amount > 0" in sql
        assert "service_date >= date_trunc('quarter', CURRENT_DATE)" in sql
        assert "GROUP BY payer_name, service_line" in sql
        assert "ORDER BY total_charges DESC" in sql
        assert "LIMIT 50" in sql

    def test_filter_like(self) -> None:
        plan = QueryPlan(
            filters=[{"column": "name", "operator": "like", "value": "%Smith%"}],
        )
        sql = self.gen.generate_sql(plan)
        assert "name LIKE '%Smith%'" in sql

    def test_filter_not_in(self) -> None:
        plan = QueryPlan(
            filters=[{"column": "status", "operator": "not_in", "value": ["void", "deleted"]}],
        )
        sql = self.gen.generate_sql(plan)
        assert "status NOT IN ('void', 'deleted')" in sql

    def test_time_range_this_year(self) -> None:
        plan = QueryPlan(time_range={"date_column": "report_date", "range": "this_year"})
        sql = self.gen.generate_sql(plan)
        assert "date_trunc('year', CURRENT_DATE)" in sql

    def test_time_range_last_year(self) -> None:
        plan = QueryPlan(time_range={"date_column": "report_date", "range": "last_year"})
        sql = self.gen.generate_sql(plan)
        assert "date_trunc('year', CURRENT_DATE - INTERVAL '1 year')" in sql

    def test_time_range_today(self) -> None:
        plan = QueryPlan(time_range={"date_column": "report_date", "range": "today"})
        sql = self.gen.generate_sql(plan)
        assert "report_date = CURRENT_DATE" in sql

    def test_time_range_yesterday(self) -> None:
        plan = QueryPlan(time_range={"date_column": "report_date", "range": "yesterday"})
        sql = self.gen.generate_sql(plan)
        assert "report_date = CURRENT_DATE - INTERVAL '1 day'" in sql

    def test_time_range_last_7_days(self) -> None:
        plan = QueryPlan(time_range={"date_column": "report_date", "range": "last_7_days"})
        sql = self.gen.generate_sql(plan)
        assert "report_date >= CURRENT_DATE - INTERVAL '7 days'" in sql

    def test_time_range_last_90_days(self) -> None:
        plan = QueryPlan(time_range={"date_column": "report_date", "range": "last_90_days"})
        sql = self.gen.generate_sql(plan)
        assert "report_date >= CURRENT_DATE - INTERVAL '90 days'" in sql

    def test_comparison_custom_offset(self) -> None:
        plan = QueryPlan(
            comparison={"type": "custom", "metric": "charges", "offset": "INTERVAL '2 months'"}
        )
        fragment = self.gen._apply_comparison(plan)
        assert "LAG(charges)" in fragment

    def test_comparison_with_alias(self) -> None:
        plan = QueryPlan(
            comparison={"type": "qoq", "metric": "revenue", "alias": "prev_quarter_revenue"}
        )
        fragment = self.gen._apply_comparison(plan)
        assert "prev_quarter_revenue" in fragment


# ---------------------------------------------------------------------------
# QueryExecutor
# ---------------------------------------------------------------------------

class TestQueryExecutor:
    def test_execute_returns_empty(self) -> None:
        executor = QueryExecutor()
        result = executor.execute("SELECT 1")
        assert result["row_count"] == 0
        assert result["columns"] == []
        assert result["rows"] == []

    def test_execute_with_plan_returns_query_result(self) -> None:
        executor = QueryExecutor(
            context=QueryContext(
                tenant_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
            )
        )
        plan = QueryPlan(
            metrics=["COUNT(*)"],
            dimensions=["payer_name"],
            group_by=["payer_name"],
        )
        qr = executor.execute_with_plan(plan)
        assert isinstance(qr, QueryResult)
        assert qr.plan_id == plan.id
        assert qr.row_count == 0
        assert "sql" in qr.metadata

    def test_executor_uses_context(self) -> None:
        ctx = QueryContext(default_currency="EUR")
        executor = QueryExecutor(context=ctx)
        assert executor.context.default_currency == "EUR"
