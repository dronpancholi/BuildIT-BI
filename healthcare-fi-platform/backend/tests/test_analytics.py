"""Tests for the Self-Service Analytics Layer domain models."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.domain.analytics import (
    AccessLevel,
    AggregationType,
    Cardinality,
    ComparisonType,
    Dimension,
    DimensionHierarchy,
    FilterOperator,
    FilterSpec,
    FormulaComponent,
    FormulaComponentType,
    MetricCategory,
    MetricFormula,
    Operator,
    ParameterType,
    QueryParameter,
    QueryTemplate,
    SemanticMetric,
    SemanticQuery,
    TimeRange,
    TimeRangeRelative,
)


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------

class TestEnums:
    def test_metric_category_values(self):
        expected = {"REVENUE", "COST", "QUALITY", "OPERATIONS", "PATIENT", "FINANCIAL", "COMPLIANCE"}
        assert {m.value for m in MetricCategory} == expected

    def test_aggregation_type_values(self):
        expected = {"SUM", "AVG", "COUNT", "COUNT_DISTINCT", "MIN", "MAX"}
        assert {a.value for a in AggregationType} == expected

    def test_operator_values(self):
        expected = {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "PERCENTAGE"}
        assert {o.value for o in Operator} == expected

    def test_formula_component_type_values(self):
        expected = {"metric", "constant", "operator"}
        assert {f.value for f in FormulaComponentType} == expected

    def test_cardinality_values(self):
        expected = {"HIGH", "MEDIUM", "LOW"}
        assert {c.value for c in Cardinality} == expected

    def test_filter_operator_values(self):
        expected = {"EQ", "NEQ", "GT", "GTE", "LT", "LTE", "IN", "NOT_IN", "LIKE", "BETWEEN"}
        assert {f.value for f in FilterOperator} == expected

    def test_time_range_relative_values(self):
        expected = {
            "TODAY", "THIS_WEEK", "THIS_MONTH", "THIS_QUARTER", "THIS_YEAR",
            "LAST_7_DAYS", "LAST_30_DAYS", "LAST_90_DAYS", "LAST_12_MONTHS", "CUSTOM",
        }
        assert {t.value for t in TimeRangeRelative} == expected

    def test_comparison_type_values(self):
        expected = {"NONE", "PERIOD_OVER_PERIOD", "YEAR_OVER_YEAR", "CUSTOM"}
        assert {c.value for c in ComparisonType} == expected

    def test_access_level_values(self):
        expected = {"PRIVATE", "TEAM", "ORGANIZATION", "PUBLIC"}
        assert {a.value for a in AccessLevel} == expected

    def test_parameter_type_values(self):
        expected = {"TEXT", "SELECT", "DATE_RANGE", "NUMBER"}
        assert {p.value for p in ParameterType} == expected

    def test_enum_string_representation(self):
        assert str(MetricCategory.REVENUE) == "MetricCategory.REVENUE"
        assert MetricCategory("REVENUE") is MetricCategory.REVENUE

    def test_enum_is_hashable(self):
        s = {MetricCategory.REVENUE, MetricCategory.COST}
        assert MetricCategory.REVENUE in s
        assert MetricCategory.QUALITY not in s

    def test_enum_comparison(self):
        assert MetricCategory.REVENUE == MetricCategory.REVENUE
        assert MetricCategory.REVENUE != MetricCategory.COST


# ---------------------------------------------------------------------------
# FormulaComponent tests
# ---------------------------------------------------------------------------

class TestFormulaComponent:
    def test_metric_component(self):
        comp = FormulaComponent(type=FormulaComponentType.METRIC, value="total_revenue")
        assert comp.type == FormulaComponentType.METRIC
        assert comp.value == "total_revenue"
        assert comp.aggregation is None

    def test_constant_component(self):
        comp = FormulaComponent(type=FormulaComponentType.CONSTANT, value="100")
        assert comp.type == FormulaComponentType.CONSTANT
        assert comp.value == "100"

    def test_operator_component(self):
        comp = FormulaComponent(type=FormulaComponentType.OPERATOR, value="ADD")
        assert comp.type == FormulaComponentType.OPERATOR
        assert comp.value == "ADD"

    def test_component_with_aggregation(self):
        comp = FormulaComponent(
            type=FormulaComponentType.METRIC,
            value="claim_amount",
            aggregation=AggregationType.SUM,
        )
        assert comp.aggregation == AggregationType.SUM

    def test_component_defaults(self):
        comp = FormulaComponent(type=FormulaComponentType.CONSTANT, value="0")
        assert comp.aggregation is None


# ---------------------------------------------------------------------------
# MetricFormula tests
# ---------------------------------------------------------------------------

class TestMetricFormula:
    def test_empty_formula(self):
        formula = MetricFormula()
        assert formula.components == []

    def test_simple_addition_formula(self):
        formula = MetricFormula(
            components=[
                FormulaComponent(type=FormulaComponentType.METRIC, value="revenue"),
                FormulaComponent(type=FormulaComponentType.OPERATOR, value="ADD"),
                FormulaComponent(type=FormulaComponentType.METRIC, value="cost"),
            ]
        )
        assert len(formula.components) == 3
        assert formula.components[0].type == FormulaComponentType.METRIC
        assert formula.components[1].type == FormulaComponentType.OPERATOR
        assert formula.components[2].type == FormulaComponentType.METRIC

    def test_to_json(self):
        formula = MetricFormula(
            components=[
                FormulaComponent(type=FormulaComponentType.METRIC, value="claims", aggregation=AggregationType.COUNT),
                FormulaComponent(type=FormulaComponentType.OPERATOR, value="DIVIDE"),
                FormulaComponent(type=FormulaComponentType.CONSTANT, value="1"),
            ]
        )
        result = formula.to_json()
        assert result == {
            "components": [
                {"type": "metric", "value": "claims", "aggregation": "COUNT"},
                {"type": "operator", "value": "DIVIDE"},
                {"type": "constant", "value": "1"},
            ]
        }

    def test_to_json_without_aggregation(self):
        formula = MetricFormula(
            components=[
                FormulaComponent(type=FormulaComponentType.CONSTANT, value="100"),
            ]
        )
        result = formula.to_json()
        assert result == {"components": [{"type": "constant", "value": "100"}]}

    def test_from_json(self):
        data = {
            "components": [
                {"type": "metric", "value": "total_billed"},
                {"type": "operator", "value": "SUBTRACT"},
                {"type": "metric", "value": "total_collected"},
            ]
        }
        formula = MetricFormula.from_json(data)
        assert len(formula.components) == 3
        assert formula.components[0].type == FormulaComponentType.METRIC
        assert formula.components[0].value == "total_billed"
        assert formula.components[1].type == FormulaComponentType.OPERATOR
        assert formula.components[1].value == "SUBTRACT"
        assert formula.components[2].type == FormulaComponentType.METRIC
        assert formula.components[2].aggregation is None

    def test_from_json_with_aggregation(self):
        data = {
            "components": [
                {"type": "metric", "value": "patient_id", "aggregation": "COUNT_DISTINCT"},
            ]
        }
        formula = MetricFormula.from_json(data)
        assert formula.components[0].aggregation == AggregationType.COUNT_DISTINCT

    def test_roundtrip_serialization(self):
        original = MetricFormula(
            components=[
                FormulaComponent(type=FormulaComponentType.METRIC, value="revenue", aggregation=AggregationType.SUM),
                FormulaComponent(type=FormulaComponentType.OPERATOR, value="MULTIPLY"),
                FormulaComponent(type=FormulaComponentType.CONSTANT, value="0.1"),
            ]
        )
        serialised = original.to_json()
        restored = MetricFormula.from_json(serialised)
        assert len(restored.components) == len(original.components)
        for orig, rest in zip(original.components, restored.components):
            assert orig.type == rest.type
            assert orig.value == rest.value
            assert orig.aggregation == rest.aggregation

    def test_complex_percentage_formula(self):
        formula = MetricFormula(
            components=[
                FormulaComponent(type=FormulaComponentType.METRIC, value="denied_claims", aggregation=AggregationType.COUNT),
                FormulaComponent(type=FormulaComponentType.OPERATOR, value="DIVIDE"),
                FormulaComponent(type=FormulaComponentType.METRIC, value="total_claims", aggregation=AggregationType.COUNT),
                FormulaComponent(type=FormulaComponentType.OPERATOR, value="MULTIPLY"),
                FormulaComponent(type=FormulaComponentType.CONSTANT, value="100"),
            ]
        )
        assert len(formula.components) == 5
        result = formula.to_json()
        assert result["components"][0]["aggregation"] == "COUNT"
        assert result["components"][2]["aggregation"] == "COUNT"


# ---------------------------------------------------------------------------
# SemanticMetric tests
# ---------------------------------------------------------------------------

class TestSemanticMetric:
    def test_default_values(self):
        metric = SemanticMetric()
        assert isinstance(metric.id, UUID)
        assert metric.name == ""
        assert metric.slug == ""
        assert metric.description == ""
        assert metric.formula_json == {}
        assert metric.unit == ""
        assert metric.aggregation == AggregationType.SUM
        assert metric.format_pattern == ""
        assert metric.category == MetricCategory.FINANCIAL
        assert metric.tags == []
        assert metric.created_by == ""
        assert metric.version == 1
        assert metric.is_certified is False
        assert metric.certified_by is None
        assert metric.is_deprecated is False
        assert isinstance(metric.created_at, datetime)

    def test_custom_values(self):
        metric_id = uuid4()
        metric = SemanticMetric(
            id=metric_id,
            name="Net Collection Rate",
            slug="net-collection-rate",
            description="Percentage of collected amounts vs. billed amounts",
            formula_json={
                "components": [
                    {"type": "metric", "value": "total_collected", "aggregation": "SUM"},
                    {"type": "operator", "value": "DIVIDE"},
                    {"type": "metric", "value": "total_billed", "aggregation": "SUM"},
                ]
            },
            unit="%",
            aggregation=AggregationType.AVG,
            format_pattern="0.00%",
            category=MetricCategory.REVENUE,
            tags=["collection", "denial", "KPI"],
            created_by="admin@example.com",
            version=2,
            is_certified=True,
            certified_by="finance-director@example.com",
        )
        assert metric.id == metric_id
        assert metric.name == "Net Collection Rate"
        assert metric.slug == "net-collection-rate"
        assert metric.formula_json["components"][0]["value"] == "total_collected"
        assert metric.unit == "%"
        assert metric.aggregation == AggregationType.AVG
        assert metric.format_pattern == "0.00%"
        assert metric.category == MetricCategory.REVENUE
        assert metric.tags == ["collection", "denial", "KPI"]
        assert metric.created_by == "admin@example.com"
        assert metric.version == 2
        assert metric.is_certified is True
        assert metric.certified_by == "finance-director@example.com"

    def test_formula_property_getter(self):
        metric = SemanticMetric(
            formula_json={
                "components": [
                    {"type": "metric", "value": "a", "aggregation": "SUM"},
                    {"type": "operator", "value": "ADD"},
                    {"type": "metric", "value": "b"},
                ]
            }
        )
        formula = metric.formula
        assert isinstance(formula, MetricFormula)
        assert len(formula.components) == 3
        assert formula.components[0].aggregation == AggregationType.SUM

    def test_formula_property_setter(self):
        metric = SemanticMetric()
        new_formula = MetricFormula(
            components=[
                FormulaComponent(type=FormulaComponentType.METRIC, value="x", aggregation=AggregationType.AVG),
            ]
        )
        metric.formula = new_formula
        assert metric.formula_json == {
            "components": [{"type": "metric", "value": "x", "aggregation": "AVG"}]
        }
        assert metric.formula.components[0].value == "x"

    def test_formula_property_none_components(self):
        metric = SemanticMetric(formula_json={"components": []})
        formula = metric.formula
        assert formula.components == []

    def test_deprecated_metric(self):
        metric = SemanticMetric(name="Old Metric", is_deprecated=True)
        assert metric.is_deprecated is True

    def test_certified_metric(self):
        metric = SemanticMetric(
            name="Certified Metric",
            is_certified=True,
            certified_by="qa@example.com",
        )
        assert metric.is_certified is True
        assert metric.certified_by == "qa@example.com"


# ---------------------------------------------------------------------------
# DimensionHierarchy tests
# ---------------------------------------------------------------------------

class TestDimensionHierarchy:
    def test_hierarchy_defaults(self):
        h = DimensionHierarchy()
        assert h.levels == []
        assert h.member_table == ""
        assert h.parent_column == ""
        assert h.child_column == ""

    def test_hierarchy_custom(self):
        h = DimensionHierarchy(
            levels=["Region", "State", "City"],
            member_table="dim_geography",
            parent_column="parent_id",
            child_column="child_id",
        )
        assert h.levels == ["Region", "State", "City"]
        assert h.member_table == "dim_geography"
        assert h.parent_column == "parent_id"
        assert h.child_column == "child_id"


# ---------------------------------------------------------------------------
# Dimension tests
# ---------------------------------------------------------------------------

class TestDimension:
    def test_default_values(self):
        dim = Dimension()
        assert isinstance(dim.id, UUID)
        assert dim.slug == ""
        assert dim.name == ""
        assert dim.table_name == ""
        assert dim.column_name == ""
        assert dim.hierarchy_json is None
        assert dim.cardinality == Cardinality.MEDIUM
        assert dim.values == []
        assert dim.description == ""

    def test_custom_values(self):
        dim = Dimension(
            slug="payer",
            name="Insurance Payer",
            table_name="dim_payer",
            column_name="payer_id",
            cardinality=Cardinality.LOW,
            values=["Medicare", "Medicaid", "BCBS", "UHC"],
            description="Primary insurance payer",
        )
        assert dim.slug == "payer"
        assert dim.name == "Insurance Payer"
        assert dim.table_name == "dim_payer"
        assert dim.column_name == "payer_id"
        assert dim.cardinality == Cardinality.LOW
        assert dim.values == ["Medicare", "Medicaid", "BCBS", "UHC"]
        assert dim.description == "Primary insurance payer"

    def test_hierarchy_property_getter(self):
        dim = Dimension(
            hierarchy_json={
                "levels": ["Facility", "Department", "Unit"],
                "member_table": "dim_org",
                "parent_column": "parent_id",
                "child_column": "child_id",
            }
        )
        h = dim.hierarchy
        assert isinstance(h, DimensionHierarchy)
        assert h.levels == ["Facility", "Department", "Unit"]
        assert h.member_table == "dim_org"

    def test_hierarchy_property_getter_none(self):
        dim = Dimension()
        assert dim.hierarchy is None

    def test_hierarchy_property_setter(self):
        dim = Dimension()
        dim.hierarchy = DimensionHierarchy(
            levels=["A", "B"],
            member_table="tbl",
            parent_column="p",
            child_column="c",
        )
        assert dim.hierarchy_json is not None
        assert dim.hierarchy_json["levels"] == ["A", "B"]
        assert dim.hierarchy_json["member_table"] == "tbl"

    def test_hierarchy_property_setter_none(self):
        dim = Dimension(hierarchy_json={"levels": ["X"]})
        dim.hierarchy = None
        assert dim.hierarchy_json is None

    def test_high_cardinality(self):
        dim = Dimension(slug="patient", cardinality=Cardinality.HIGH)
        assert dim.cardinality == Cardinality.HIGH


# ---------------------------------------------------------------------------
# FilterSpec tests
# ---------------------------------------------------------------------------

class TestFilterSpec:
    def test_default_values(self):
        f = FilterSpec()
        assert f.dimension_slug == ""
        assert f.operator == FilterOperator.EQ
        assert f.values == []

    def test_eq_filter(self):
        f = FilterSpec(dimension_slug="payer", operator=FilterOperator.EQ, values=["Medicare"])
        assert f.dimension_slug == "payer"
        assert f.operator == FilterOperator.EQ
        assert f.values == ["Medicare"]

    def test_in_filter(self):
        f = FilterSpec(
            dimension_slug="status",
            operator=FilterOperator.IN,
            values=["ACTIVE", "PENDING", "APPROVED"],
        )
        assert f.operator == FilterOperator.IN
        assert len(f.values) == 3

    def test_between_filter(self):
        f = FilterSpec(
            dimension_slug="charge_amount",
            operator=FilterOperator.BETWEEN,
            values=[100, 5000],
        )
        assert f.operator == FilterOperator.BETWEEN
        assert f.values == [100, 5000]

    def test_like_filter(self):
        f = FilterSpec(
            dimension_slug="patient_name",
            operator=FilterOperator.LIKE,
            values=["%Smith%"],
        )
        assert f.operator == FilterOperator.LIKE

    def test_not_in_filter(self):
        f = FilterSpec(
            dimension_slug="claim_type",
            operator=FilterOperator.NOT_IN,
            values=["TEST", "SAMPLE"],
        )
        assert f.operator == FilterOperator.NOT_IN

    def test_numeric_comparisons(self):
        for op in [FilterOperator.GT, FilterOperator.GTE, FilterOperator.LT, FilterOperator.LTE]:
            f = FilterSpec(dimension_slug="amount", operator=op, values=[1000])
            assert f.operator == op

    def test_neq_filter(self):
        f = FilterSpec(dimension_slug="status", operator=FilterOperator.NEQ, values=["DENIED"])
        assert f.operator == FilterOperator.NEQ


# ---------------------------------------------------------------------------
# TimeRange tests
# ---------------------------------------------------------------------------

class TestTimeRange:
    def test_default_values(self):
        tr = TimeRange()
        assert tr.start_date is None
        assert tr.end_date is None
        assert tr.relative == TimeRangeRelative.THIS_MONTH
        assert tr.custom_days is None

    def test_explicit_date_range(self):
        tr = TimeRange(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            relative=TimeRangeRelative.CUSTOM,
        )
        assert tr.start_date == date(2025, 1, 1)
        assert tr.end_date == date(2025, 12, 31)
        assert tr.relative == TimeRangeRelative.CUSTOM

    def test_relative_presets(self):
        for preset in TimeRangeRelative:
            tr = TimeRange(relative=preset)
            assert tr.relative == preset

    def test_custom_days(self):
        tr = TimeRange(relative=TimeRangeRelative.CUSTOM, custom_days=45)
        assert tr.custom_days == 45

    def test_today(self):
        tr = TimeRange(relative=TimeRangeRelative.TODAY)
        assert tr.relative == TimeRangeRelative.TODAY

    def test_last_12_months(self):
        tr = TimeRange(relative=TimeRangeRelative.LAST_12_MONTHS)
        assert tr.relative == TimeRangeRelative.LAST_12_MONTHS


# ---------------------------------------------------------------------------
# SemanticQuery tests
# ---------------------------------------------------------------------------

class TestSemanticQuery:
    def test_default_values(self):
        q = SemanticQuery()
        assert q.metric_ids == []
        assert q.dimension_ids == []
        assert q.filters == []
        assert isinstance(q.time_range, TimeRange)
        assert q.comparison == ComparisonType.NONE

    def test_simple_query(self):
        m1, m2 = uuid4(), uuid4()
        d1 = uuid4()
        q = SemanticQuery(
            metric_ids=[m1, m2],
            dimension_ids=[d1],
        )
        assert len(q.metric_ids) == 2
        assert len(q.dimension_ids) == 1
        assert m1 in q.metric_ids

    def test_query_with_filters(self):
        m1 = uuid4()
        q = SemanticQuery(
            metric_ids=[m1],
            filters=[
                FilterSpec(dimension_slug="payer", operator=FilterOperator.EQ, values=["Medicare"]),
                FilterSpec(dimension_slug="status", operator=FilterOperator.IN, values=["PAID", "PENDING"]),
            ],
        )
        assert len(q.filters) == 2
        assert q.filters[0].dimension_slug == "payer"
        assert q.filters[1].operator == FilterOperator.IN

    def test_query_with_time_range(self):
        q = SemanticQuery(
            time_range=TimeRange(
                start_date=date(2025, 1, 1),
                end_date=date(2025, 6, 30),
                relative=TimeRangeRelative.CUSTOM,
            )
        )
        assert q.time_range.start_date == date(2025, 1, 1)
        assert q.time_range.end_date == date(2025, 6, 30)

    def test_query_with_comparison(self):
        q = SemanticQuery(
            metric_ids=[uuid4()],
            comparison=ComparisonType.YEAR_OVER_YEAR,
        )
        assert q.comparison == ComparisonType.YEAR_OVER_YEAR

    def test_query_with_all_comparison_types(self):
        for ct in ComparisonType:
            q = SemanticQuery(comparison=ct)
            assert q.comparison == ct

    def test_complex_query(self):
        q = SemanticQuery(
            metric_ids=[uuid4(), uuid4(), uuid4()],
            dimension_ids=[uuid4(), uuid4()],
            filters=[
                FilterSpec(dimension_slug="facility", operator=FilterOperator.EQ, values=["Main Campus"]),
                FilterSpec(dimension_slug="date", operator=FilterOperator.BETWEEN, values=["2025-01-01", "2025-12-31"]),
            ],
            time_range=TimeRange(relative=TimeRangeRelative.THIS_YEAR),
            comparison=ComparisonType.PERIOD_OVER_PERIOD,
        )
        assert len(q.metric_ids) == 3
        assert len(q.dimension_ids) == 2
        assert len(q.filters) == 2
        assert q.time_range.relative == TimeRangeRelative.THIS_YEAR
        assert q.comparison == ComparisonType.PERIOD_OVER_PERIOD


# ---------------------------------------------------------------------------
# SavedReport tests
# ---------------------------------------------------------------------------

class TestSavedReport:
    def test_default_values(self):
        from app.domain.analytics import SavedReport

        r = SavedReport()
        assert isinstance(r.id, UUID)
        assert r.name == ""
        assert r.description == ""
        assert r.metric_ids == []
        assert r.dimension_ids == []
        assert r.filters == []
        assert isinstance(r.time_range, TimeRange)
        assert r.visualization_configs == []
        assert r.is_template is False
        assert r.template_category is None
        assert isinstance(r.owner_id, UUID)
        assert isinstance(r.tenant_id, UUID)
        assert r.access_level == AccessLevel.PRIVATE
        assert r.version == 1
        assert isinstance(r.created_at, datetime)
        assert isinstance(r.updated_at, datetime)
        assert r.last_accessed_at is None
        assert r.access_count == 0

    def test_custom_values(self):
        from app.domain.analytics import SavedReport

        report_id = uuid4()
        owner_id = uuid4()
        tenant_id = uuid4()
        r = SavedReport(
            id=report_id,
            name="Monthly Revenue by Payer",
            description="Revenue breakdown by insurance payer",
            metric_ids=[uuid4(), uuid4()],
            dimension_ids=[uuid4()],
            filters=[FilterSpec(dimension_slug="status", operator=FilterOperator.EQ, values=["PAID"])],
            time_range=TimeRange(relative=TimeRangeRelative.THIS_MONTH),
            visualization_configs=[
                {"type": "bar", "x_axis": "payer", "y_axis": "revenue"},
                {"type": "table", "columns": ["payer", "revenue", "claims"]},
            ],
            is_template=True,
            template_category="financial",
            owner_id=owner_id,
            tenant_id=tenant_id,
            access_level=AccessLevel.ORGANIZATION,
            version=3,
            access_count=42,
        )
        assert r.id == report_id
        assert r.name == "Monthly Revenue by Payer"
        assert r.description == "Revenue breakdown by insurance payer"
        assert len(r.metric_ids) == 2
        assert len(r.dimension_ids) == 1
        assert len(r.filters) == 1
        assert r.time_range.relative == TimeRangeRelative.THIS_MONTH
        assert len(r.visualization_configs) == 2
        assert r.is_template is True
        assert r.template_category == "financial"
        assert r.owner_id == owner_id
        assert r.tenant_id == tenant_id
        assert r.access_level == AccessLevel.ORGANIZATION
        assert r.version == 3
        assert r.access_count == 42

    def test_access_level_values(self):
        from app.domain.analytics import SavedReport

        for level in AccessLevel:
            r = SavedReport(access_level=level)
            assert r.access_level == level

    def test_team_access(self):
        from app.domain.analytics import SavedReport

        r = SavedReport(name="Team Report", access_level=AccessLevel.TEAM)
        assert r.access_level == AccessLevel.TEAM

    def test_public_access(self):
        from app.domain.analytics import SavedReport

        r = SavedReport(name="Public Report", access_level=AccessLevel.PUBLIC)
        assert r.access_level == AccessLevel.PUBLIC

    def test_report_with_last_accessed(self):
        from app.domain.analytics import SavedReport

        accessed = datetime(2025, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        r = SavedReport(last_accessed_at=accessed)
        assert r.last_accessed_at == accessed


# ---------------------------------------------------------------------------
# QueryParameter tests
# ---------------------------------------------------------------------------

class TestQueryParameter:
    def test_default_values(self):
        p = QueryParameter()
        assert p.name == ""
        assert p.type == ParameterType.TEXT
        assert p.required is True
        assert p.default is None
        assert p.options == []

    def test_text_parameter(self):
        p = QueryParameter(name="patient_name", type=ParameterType.TEXT, required=False, default="")
        assert p.name == "patient_name"
        assert p.type == ParameterType.TEXT
        assert p.required is False
        assert p.default == ""

    def test_select_parameter(self):
        p = QueryParameter(
            name="payer",
            type=ParameterType.SELECT,
            required=True,
            default="Medicare",
            options=["Medicare", "Medicaid", "BCBS", "UHC"],
        )
        assert p.type == ParameterType.SELECT
        assert len(p.options) == 4
        assert p.default == "Medicare"

    def test_date_range_parameter(self):
        p = QueryParameter(name="report_period", type=ParameterType.DATE_RANGE, required=True)
        assert p.type == ParameterType.DATE_RANGE

    def test_number_parameter(self):
        p = QueryParameter(
            name="min_amount",
            type=ParameterType.NUMBER,
            required=False,
            default=0,
        )
        assert p.type == ParameterType.NUMBER
        assert p.default == 0


# ---------------------------------------------------------------------------
# QueryTemplate tests
# ---------------------------------------------------------------------------

class TestQueryTemplate:
    def test_default_values(self):
        t = QueryTemplate()
        assert isinstance(t.id, UUID)
        assert t.name == ""
        assert t.description == ""
        assert t.partial_query_json == {}
        assert t.parameters == []

    def test_custom_template(self):
        param1 = QueryParameter(name="payer", type=ParameterType.SELECT, options=["Medicare", "BCBS"])
        param2 = QueryParameter(name="start_date", type=ParameterType.DATE_RANGE, required=True)
        t = QueryTemplate(
            name="Revenue by Payer",
            description="Shows revenue broken down by insurance payer for a given date range",
            partial_query_json={
                "metric_ids": ["revenue-metric-id"],
                "dimension_ids": ["payer-dimension-id"],
                "filters": [{"dimension_slug": "payer", "operator": "EQ", "values": ["{{payer}}"]}],
                "time_range": {"relative": "CUSTOM"},
            },
            parameters=[param1, param2],
        )
        assert t.name == "Revenue by Payer"
        assert t.description == "Shows revenue broken down by insurance payer for a given date range"
        assert "metric_ids" in t.partial_query_json
        assert len(t.parameters) == 2
        assert t.parameters[0].name == "payer"
        assert t.parameters[1].type == ParameterType.DATE_RANGE

    def test_template_with_empty_partial_query(self):
        t = QueryTemplate(name="Empty Template")
        assert t.partial_query_json == {}
        assert t.parameters == []


# ---------------------------------------------------------------------------
# Integration / composition tests
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_metric_with_complex_formula(self):
        """Metric wrapping a realistic claim-denial-rate formula."""
        metric = SemanticMetric(
            name="Claim Denial Rate",
            slug="claim-denial-rate",
            description="Percentage of claims denied by payers",
            formula_json={
                "components": [
                    {"type": "metric", "value": "denied_claims", "aggregation": "COUNT"},
                    {"type": "operator", "value": "DIVIDE"},
                    {"type": "metric", "value": "total_submitted_claims", "aggregation": "COUNT"},
                    {"type": "operator", "value": "MULTIPLY"},
                    {"type": "constant", "value": "100"},
                ]
            },
            unit="%",
            aggregation=AggregationType.AVG,
            format_pattern="0.00%",
            category=MetricCategory.QUALITY,
            tags=["denial", "claims", "KPI"],
            created_by="analytics-team",
        )
        assert metric.formula.components[0].aggregation == AggregationType.COUNT
        assert metric.formula_json["components"][1]["value"] == "DIVIDE"

    def test_query_from_saved_report(self):
        """Build a SemanticQuery from a SavedReport."""
        from app.domain.analytics import SavedReport

        payer_dim = uuid4()
        status_dim = uuid4()
        revenue_metric = uuid4()
        claims_metric = uuid4()

        report = SavedReport(
            name="Payer Performance Dashboard",
            metric_ids=[revenue_metric, claims_metric],
            dimension_ids=[payer_dim, status_dim],
            filters=[
                FilterSpec(dimension_slug="payer", operator=FilterOperator.NOT_IN, values=["TEST"]),
                FilterSpec(dimension_slug="status", operator=FilterOperator.IN, values=["PAID", "PENDING"]),
            ],
            time_range=TimeRange(relative=TimeRangeRelative.LAST_90_DAYS),
            visualization_configs=[
                {"type": "line", "x_axis": "date", "y_axis": "revenue"},
                {"type": "pie", "dimension": "payer", "metric": "claims"},
            ],
            access_level=AccessLevel.TEAM,
        )

        query = SemanticQuery(
            metric_ids=report.metric_ids,
            dimension_ids=report.dimension_ids,
            filters=report.filters,
            time_range=report.time_range,
            comparison=ComparisonType.PERIOD_OVER_PERIOD,
        )

        assert len(query.metric_ids) == 2
        assert len(query.dimension_ids) == 2
        assert len(query.filters) == 2
        assert query.time_range.relative == TimeRangeRelative.LAST_90_DAYS
        assert query.comparison == ComparisonType.PERIOD_OVER_PERIOD

    def test_dimension_with_hierarchy_roundtrip(self):
        """Ensure hierarchy serialisation works through the Dimension property."""
        original = DimensionHierarchy(
            levels=["Facility", "Department", "Unit"],
            member_table="dim_org_hierarchy",
            parent_column="parent_org_id",
            child_column="child_org_id",
        )
        dim = Dimension(slug="org", name="Organization")
        dim.hierarchy = original
        restored = dim.hierarchy
        assert restored is not None
        assert restored.levels == original.levels
        assert restored.member_table == original.member_table
        assert restored.parent_column == original.parent_column
        assert restored.child_column == original.child_column

    def test_metric_formula_roundtrip(self):
        """Serialize then deserialize a formula and verify equality."""
        formula = MetricFormula(
            components=[
                FormulaComponent(type=FormulaComponentType.METRIC, value="collected", aggregation=AggregationType.SUM),
                FormulaComponent(type=FormulaComponentType.OPERATOR, value="DIVIDE"),
                FormulaComponent(type=FormulaComponentType.METRIC, value="billed", aggregation=AggregationType.SUM),
                FormulaComponent(type=FormulaComponentType.OPERATOR, value="MULTIPLY"),
                FormulaComponent(type=FormulaComponentType.CONSTANT, value="100"),
            ]
        )
        json_data = formula.to_json()
        restored = MetricFormula.from_json(json_data)
        assert len(restored.components) == 5
        assert restored.components[0].value == "collected"
        assert restored.components[0].aggregation == AggregationType.SUM
        assert restored.components[2].aggregation == AggregationType.SUM
        assert restored.components[4].value == "100"

    def test_full_report_lifecycle(self):
        """Simulate creating, parameterising, and querying a report."""
        from app.domain.analytics import SavedReport

        # 1. Create a report
        report = SavedReport(
            name="Charge Lag Analysis",
            description="Analyses time between charge posting and payment posting",
            metric_ids=[uuid4(), uuid4()],
            dimension_ids=[uuid4()],
            filters=[],
            time_range=TimeRange(relative=TimeRangeRelative.LAST_30_DAYS),
            is_template=True,
            template_category="operations",
            access_level=AccessLevel.ORGANIZATION,
        )

        # 2. Create a template from the report
        template = QueryTemplate(
            name=report.name,
            description=report.description,
            partial_query_json={
                "metric_ids": [str(m) for m in report.metric_ids],
                "dimension_ids": [str(d) for d in report.dimension_ids],
                "time_range": {"relative": report.time_range.relative.value},
            },
            parameters=[
                QueryParameter(name="facility", type=ParameterType.SELECT, required=False, options=["All", "Main", "Satellite"]),
                QueryParameter(name="min_lag_days", type=ParameterType.NUMBER, required=False, default=0),
            ],
        )
        assert template.name == "Charge Lag Analysis"
        assert len(template.parameters) == 2

        # 3. Build a query from the template
        query = SemanticQuery(
            metric_ids=[UUID(m) for m in template.partial_query_json["metric_ids"]],
            dimension_ids=[UUID(d) for d in template.partial_query_json["dimension_ids"]],
            filters=[
                FilterSpec(dimension_slug="lag_days", operator=FilterOperator.GTE, values=[0]),
            ],
            time_range=TimeRange(relative=TimeRangeRelative.LAST_30_DAYS),
        )
        assert len(query.metric_ids) == 2

    def test_all_filter_operators(self):
        """Create a FilterSpec for every FilterOperator value."""
        for op in FilterOperator:
            f = FilterSpec(dimension_slug="test", operator=op, values=[1])
            assert f.operator == op

    def test_all_parameter_types(self):
        """Create a QueryParameter for every ParameterType value."""
        for pt in ParameterType:
            p = QueryParameter(name="param", type=pt)
            assert p.type == pt

    def test_all_metric_categories(self):
        """Create a SemanticMetric for every MetricCategory value."""
        for cat in MetricCategory:
            m = SemanticMetric(name=cat.value, category=cat)
            assert m.category == cat

    def test_all_aggregation_types(self):
        """Create a SemanticMetric for every AggregationType value."""
        for agg in AggregationType:
            m = SemanticMetric(name=agg.value, aggregation=agg)
            assert m.aggregation == agg

    def test_all_comparison_types(self):
        """Create a SemanticQuery for every ComparisonType value."""
        for ct in ComparisonType:
            q = SemanticQuery(comparison=ct)
            assert q.comparison == ct

    def test_all_time_range_relatives(self):
        """Create a TimeRange for every TimeRangeRelative value."""
        for rel in TimeRangeRelative:
            tr = TimeRange(relative=rel)
            assert tr.relative == rel
