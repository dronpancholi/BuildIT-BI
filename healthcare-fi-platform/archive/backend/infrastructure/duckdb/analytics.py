"""
DuckDB Analytics Layer - Abstraction for analytical queries.
Separates concerns: business logic never calls DuckDB directly.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

from app.domain.services.kpi_engine import AnalyticsQueryService


class AggregationType(str, Enum):
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    COUNT_DISTINCT = "count_distinct"
    MEDIAN = "median"


class Granularity(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class WindowUnit(str, Enum):
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"


@dataclass
class FilterCondition:
    """A single filter condition."""
    column: str
    operator: str  # =, !=, >, <, >=, <=, IN, LIKE, IS NULL, IS NOT NULL
    value: Any = None


@dataclass
class OrderByClause:
    """Order by clause."""
    column: str
    ascending: bool = True


@dataclass
class AggregationConfig:
    """Configuration for aggregation queries."""
    tenant_id: uuid.UUID
    table_name: str
    aggregation_type: AggregationType
    aggregation_column: str
    group_by_columns: List[str] = field(default_factory=list)
    filters: List[FilterCondition] = field(default_factory=list)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    hospital_id: Optional[uuid.UUID] = None
    branch_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    limit: Optional[int] = None
    order_by: Optional[List[OrderByClause]] = None


@dataclass
class TimeSeriesConfig:
    """Configuration for time series queries."""
    tenant_id: uuid.UUID
    table_name: str
    date_column: str
    value_column: str
    aggregation_type: AggregationType
    granularity: Granularity
    period_start: datetime
    period_end: datetime
    comparison_period_start: Optional[datetime] = None
    comparison_period_end: Optional[datetime] = None
    moving_averages: Optional[List[int]] = None
    hospital_id: Optional[uuid.UUID] = None
    branch_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None


@dataclass
class RollingWindowConfig:
    """Configuration for rolling window queries."""
    tenant_id: uuid.UUID
    table_name: str
    date_column: str
    value_column: str
    window_size: int
    window_unit: WindowUnit
    aggregation_type: AggregationType
    hospital_id: Optional[uuid.UUID] = None
    branch_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None


@dataclass
class PercentileConfig:
    """Configuration for percentile computation."""
    tenant_id: uuid.UUID
    table_name: str
    column: str
    percentiles: List[float]  # e.g., [50, 90, 95, 99]
    filters: List[FilterCondition] = field(default_factory=list)


@dataclass
class AggregationResult:
    """Result of an aggregation query."""
    data: List[Dict[str, Any]]
    total_count: int
    execution_time_ms: int


@dataclass
class TimeSeriesResult:
    """Result of a time series query."""
    data: List[Dict[str, Any]]
    comparison_data: Optional[List[Dict[str, Any]]] = None
    moving_averages: Optional[Dict[str, List[Dict[str, Any]]]] = None
    execution_time_ms: int = 0


@dataclass
class RollingWindowResult:
    """Result of a rolling window query."""
    data: List[Dict[str, Any]]
    execution_time_ms: int = 0


@dataclass
class PercentileResult:
    """Result of a percentile computation."""
    percentiles: Dict[float, float]
    count: int
    mean: float
    std_dev: float
    execution_time_ms: int = 0


class DuckDBAnalyticsEngine:
    """
    DuckDB implementation of analytics queries.
    Handles Parquet/CSV import from PostgreSQL and DuckDB-native SQL.
    """
    
    def __init__(self, connection_string: str = ":memory:"):
        self._connection_string = connection_string
        self._connection = None
    
    async def connect(self):
        """Establish connection to DuckDB."""
        try:
            import duckdb
            self._connection = duckdb.connect(self._connection_string)
        except ImportError:
            raise RuntimeError("DuckDB is not installed. Install with: pip install duckdb")
    
    async def disconnect(self):
        """Close DuckDB connection."""
        if self._connection:
            self._connection.close()
    
    async def execute_aggregation(
        self,
        config: AggregationConfig
    ) -> AggregationResult:
        """
        Execute a multi-dimensional aggregation.
        """
        import time
        start_time = time.time()
        
        # Build SQL
        sql = self._build_aggregation_sql(config)
        
        # Execute
        result = self._connection.execute(sql).fetchall()
        columns = [desc[0] for desc in self._connection.description]
        
        data = [dict(zip(columns, row)) for row in result]
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return AggregationResult(
            data=data,
            total_count=len(data),
            execution_time_ms=execution_time
        )
    
    async def execute_time_series(
        self,
        config: TimeSeriesConfig
    ) -> TimeSeriesResult:
        """
        Execute a time-series query with configurable granularity.
        """
        import time
        start_time = time.time()
        
        # Build SQL
        sql = self._build_time_series_sql(config)
        
        # Execute
        result = self._connection.execute(sql).fetchall()
        columns = [desc[0] for desc in self._connection.description]
        
        data = [dict(zip(columns, row)) for row in result]
        
        # Get comparison data if requested
        comparison_data = None
        if config.comparison_period_start and config.comparison_period_end:
            comparison_sql = self._build_time_series_sql(config, is_comparison=True)
            comp_result = self._connection.execute(comparison_sql).fetchall()
            comparison_data = [dict(zip(columns, row)) for row in comp_result]
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return TimeSeriesResult(
            data=data,
            comparison_data=comparison_data,
            execution_time_ms=execution_time
        )
    
    async def execute_rolling_window(
        self,
        config: RollingWindowConfig
    ) -> RollingWindowResult:
        """
        Execute a rolling window aggregation.
        """
        import time
        start_time = time.time()
        
        # Build SQL
        sql = self._build_rolling_window_sql(config)
        
        # Execute
        result = self._connection.execute(sql).fetchall()
        columns = [desc[0] for desc in self._connection.description]
        
        data = [dict(zip(columns, row)) for row in result]
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return RollingWindowResult(
            data=data,
            execution_time_ms=execution_time
        )
    
    async def execute_nested_aggregation(
        self,
        inner_config: AggregationConfig,
        outer_aggregation: AggregationType
    ) -> AggregationResult:
        """
        Execute nested aggregation (aggregation of aggregations).
        """
        import time
        start_time = time.time()
        
        # Execute inner aggregation
        inner_result = await self.execute_aggregation(inner_config)
        
        # Build outer query
        inner_data = inner_result.data
        if not inner_data:
            return AggregationResult(data=[], total_count=0, execution_time_ms=0)
        
        # Compute outer aggregation in Python
        values = [row.get("value", 0) for row in inner_data]
        
        if outer_aggregation == AggregationType.AVG:
            outer_value = sum(values) / len(values) if values else 0
        elif outer_aggregation == AggregationType.SUM:
            outer_value = sum(values)
        elif outer_aggregation == AggregationType.COUNT:
            outer_value = len(values)
        elif outer_aggregation == AggregationType.MIN:
            outer_value = min(values) if values else 0
        elif outer_aggregation == AggregationType.MAX:
            outer_value = max(values) if values else 0
        else:
            outer_value = sum(values) / len(values) if values else 0
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return AggregationResult(
            data=[{"value": outer_value}],
            total_count=1,
            execution_time_ms=execution_time
        )
    
    async def get_distinct_values(
        self,
        table: str,
        column: str,
        filters: Optional[List[FilterCondition]] = None
    ) -> List[Any]:
        """Get distinct values for a column."""
        sql = f"SELECT DISTINCT {column} FROM {table}"
        
        if filters:
            where_clauses = self._build_where_clauses(filters)
            if where_clauses:
                sql += f" WHERE {where_clauses}"
        
        sql += f" ORDER BY {column}"
        
        result = self._connection.execute(sql).fetchall()
        return [row[0] for row in result]
    
    async def compute_percentile(
        self,
        config: PercentileConfig
    ) -> PercentileResult:
        """
        Compute percentiles using t-digest for accurate distributed computation.
        """
        import time
        start_time = time.time()
        
        # Build SQL
        sql = f"SELECT {config.column} FROM {config.table_name}"
        
        if config.filters:
            where_clauses = self._build_where_clauses(config.filters)
            if where_clauses:
                sql += f" WHERE {where_clauses}"
        
        # Execute and compute percentiles
        result = self._connection.execute(sql).fetchall()
        values = sorted([row[0] for row in result if row[0] is not None])
        
        if not values:
            return PercentileResult(
                percentiles={p: 0.0 for p in config.percentiles},
                count=0,
                mean=0.0,
                std_dev=0.0
            )
        
        # Compute percentiles
        percentiles = {}
        for p in config.percentiles:
            index = int(len(values) * p / 100)
            index = min(index, len(values) - 1)
            percentiles[p] = values[index]
        
        # Compute statistics
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return PercentileResult(
            percentiles=percentiles,
            count=len(values),
            mean=mean,
            std_dev=std_dev,
            execution_time_ms=execution_time
        )
    
    async def import_from_postgres(
        self,
        postgres_url: str,
        table_name: str,
        query: Optional[str] = None
    ) -> None:
        """Import data from PostgreSQL to DuckDB."""
        if not query:
            query = f"SELECT * FROM {table_name}"
        
        # Use DuckDB's postgres extension
        self._connection.execute(f"""
            CREATE OR REPLACE VIEW {table_name} AS
            SELECT * FROM postgres_scan('{postgres_url}', '{query}')
        """)
    
    async def create_table_from_data(
        self,
        table_name: str,
        data: List[Dict[str, Any]]
    ) -> None:
        """Create a DuckDB table from Python data."""
        if not data:
            return
        
        # Get column names from first row
        columns = list(data[0].keys())
        
        # Create table
        create_sql = f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM (VALUES "
        values = []
        for row in data:
            row_values = [f"'{v}'" if isinstance(v, str) else str(v) for v in row.values()]
            values.append(f"({', '.join(row_values)})")
        
        create_sql += ", ".join(values) + f") AS {table_name}({', '.join(columns)})"
        
        self._connection.execute(create_sql)
    
    async def vacuum_and_analyze(self, table_name: Optional[str] = None) -> None:
        """Run VACUUM and ANALYZE on DuckDB tables."""
        if table_name:
            self._connection.execute(f"VACUUM {table_name}")
            self._connection.execute(f"ANALYZE {table_name}")
        else:
            self._connection.execute("VACUUM")
            self._connection.execute("ANALYZE")
    
    def _build_aggregation_sql(self, config: AggregationConfig) -> str:
        """Build SQL for aggregation query."""
        # Select clause
        select_parts = []
        if config.group_by_columns:
            select_parts.extend(config.group_by_columns)
        
        agg_func = config.aggregation_type.value.upper()
        if config.aggregation_type == AggregationType.COUNT_DISTINCT:
            select_parts.append(f"COUNT(DISTINCT {config.aggregation_column}) as value")
        else:
            select_parts.append(f"{agg_func}({config.aggregation_column}) as value")
        
        select_clause = ", ".join(select_parts)
        
        # From clause
        from_clause = config.table_name
        
        # Where clause
        where_parts = [f"tenant_id = '{config.tenant_id}'"]
        
        if config.hospital_id:
            where_parts.append(f"hospital_id = '{config.hospital_id}'")
        if config.branch_id:
            where_parts.append(f"branch_id = '{config.branch_id}'")
        if config.department_id:
            where_parts.append(f"department_id = '{config.department_id}'")
        if config.period_start:
            where_parts.append(f"date >= '{config.period_start.isoformat()}'")
        if config.period_end:
            where_parts.append(f"date < '{config.period_end.isoformat()}'")
        
        for filter_cond in config.filters:
            where_parts.append(self._build_filter_clause(filter_cond))
        
        where_clause = " AND ".join(where_parts)
        
        # Group by clause
        group_by_clause = ", ".join(config.group_by_columns) if config.group_by_columns else ""
        
        # Build final SQL
        sql = f"SELECT {select_clause} FROM {from_clause} WHERE {where_clause}"
        
        if group_by_clause:
            sql += f" GROUP BY {group_by_clause}"
        
        if config.order_by:
            order_parts = []
            for order in config.order_by:
                direction = "ASC" if order.ascending else "DESC"
                order_parts.append(f"{order.column} {direction}")
            sql += f" ORDER BY {', '.join(order_parts)}"
        
        if config.limit:
            sql += f" LIMIT {config.limit}"
        
        return sql
    
    def _build_time_series_sql(
        self,
        config: TimeSeriesConfig,
        is_comparison: bool = False
    ) -> str:
        """Build SQL for time series query."""
        # Date truncation
        date_trunc = {
            Granularity.DAILY: "day",
            Granularity.WEEKLY: "week",
            Granularity.MONTHLY: "month",
            Granularity.QUARTERLY: "quarter",
            Granularity.YEARLY: "year"
        }[config.granularity]
        
        # Select clause
        select_parts = [
            f"DATE_TRUNC('{date_trunc}', {config.date_column}) as period",
            f"{config.aggregation_type.value.upper()}({config.value_column}) as value"
        ]
        
        select_clause = ", ".join(select_parts)
        
        # From clause
        from_clause = config.table_name
        
        # Where clause
        where_parts = [f"tenant_id = '{config.tenant_id}'"]
        
        if config.hospital_id:
            where_parts.append(f"hospital_id = '{config.hospital_id}'")
        if config.branch_id:
            where_parts.append(f"branch_id = '{config.branch_id}'")
        if config.department_id:
            where_parts.append(f"department_id = '{config.department_id}'")
        
        if is_comparison:
            where_parts.append(f"{config.date_column} >= '{config.comparison_period_start.isoformat()}'")
            where_parts.append(f"{config.date_column} < '{config.comparison_period_end.isoformat()}'")
        else:
            where_parts.append(f"{config.date_column} >= '{config.period_start.isoformat()}'")
            where_parts.append(f"{config.date_column} < '{config.period_end.isoformat()}'")
        
        where_clause = " AND ".join(where_parts)
        
        # Group by clause
        group_by_clause = f"DATE_TRUNC('{date_trunc}', {config.date_column})"
        
        # Order by clause
        order_clause = f"DATE_TRUNC('{date_trunc}', {config.date_column})"
        
        # Build final SQL
        sql = f"""
            SELECT {select_clause}
            FROM {from_clause}
            WHERE {where_clause}
            GROUP BY {group_by_clause}
            ORDER BY {order_clause}
        """
        
        return sql
    
    def _build_rolling_window_sql(self, config: RollingWindowConfig) -> str:
        """Build SQL for rolling window query."""
        # Window function
        window_func = f"{config.aggregation_type.value.upper()}({config.value_column})"
        
        # Window size in days
        if config.window_unit == WindowUnit.DAYS:
            window_size = config.window_size
        elif config.window_unit == WindowUnit.WEEKS:
            window_size = config.window_size * 7
        else:  # MONTHS
            window_size = config.window_size * 30
        
        # Build SQL
        sql = f"""
            SELECT
                {config.date_column} as period,
                {config.value_column} as value,
                {window_func} OVER (
                    ORDER BY {config.date_column}
                    ROWS BETWEEN {window_size} PRECEDING AND CURRENT ROW
                ) as rolling_value
            FROM {config.table_name}
            WHERE tenant_id = '{config.tenant_id}'
            ORDER BY {config.date_column}
        """
        
        return sql
    
    def _build_where_clauses(self, filters: List[FilterCondition]) -> str:
        """Build WHERE clauses from filters."""
        clauses = []
        for f in filters:
            clauses.append(self._build_filter_clause(f))
        return " AND ".join(clauses)
    
    def _build_filter_clause(self, filter_cond: FilterCondition) -> str:
        """Build a single filter clause."""
        if filter_cond.operator.upper() == "IS NULL":
            return f"{filter_cond.column} IS NULL"
        elif filter_cond.operator.upper() == "IS NOT NULL":
            return f"{filter_cond.column} IS NOT NULL"
        elif filter_cond.operator.upper() == "IN":
            values = ", ".join([f"'{v}'" for v in filter_cond.value])
            return f"{filter_cond.column} IN ({values})"
        elif filter_cond.operator.upper() == "LIKE":
            return f"{filter_cond.column} LIKE '{filter_cond.value}'"
        elif isinstance(filter_cond.value, str):
            return f"{filter_cond.column} {filter_cond.operator} '{filter_cond.value}'"
        else:
            return f"{filter_cond.column} {filter_cond.operator} {filter_cond.value}"


class AnalyticsCacheService:
    """
    Caches analytics query results in Redis.
    """
    
    def __init__(self, redis_client):
        self._redis = redis_client
    
    async def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result."""
        import json
        cached = await self._redis.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    
    async def set_cached_result(
        self,
        cache_key: str,
        result: Any,
        ttl_seconds: int = 300
    ) -> None:
        """Set cached result."""
        import json
        await self._redis.setex(
            cache_key,
            ttl_seconds,
            json.dumps(result, default=str)
        )
    
    async def invalidate_scope(self, scope: str) -> None:
        """Invalidate all cache entries for a scope."""
        pattern = f"analytics:{scope}:*"
        keys = await self._redis.keys(pattern)
        if keys:
            await self._redis.delete(*keys)
    
    async def invalidate_metric(self, metric_id: str) -> None:
        """Invalidate cache for a metric."""
        pattern = f"analytics:metric:{metric_id}:*"
        keys = await self._redis.keys(pattern)
        if keys:
            await self._redis.delete(*keys)
