"""
KPI Engine v2 - The authoritative engine for all metric computations.
All dashboards, APIs, and AI features consume from this engine only.
"""
import uuid
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from app.domain.entities.metric import (
    MetricDefinition,
    MetricComputedValue,
    MetricStatus,
    PeriodType,
    TrendDirection,
    MetricUnit
)
from app.domain.entities.base import TenantAwareEntity


class ComputationError(Exception):
    """Raised when computation fails."""
    pass


class MetricNotPublishedError(ComputationError):
    """Raised when trying to compute an unpublished metric."""
    pass


class MissingDependencyError(ComputationError):
    """Raised when a required dependency is missing."""
    pass


@dataclass
class ComputationScope:
    """Scope for metric computation."""
    tenant_id: uuid.UUID
    hospital_id: Optional[uuid.UUID] = None
    branch_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None


@dataclass
class TimePeriod:
    """Time period for metric computation."""
    start: datetime
    end: datetime
    period_type: PeriodType = PeriodType.MONTHLY


@dataclass
class ComputationOptions:
    """Options for metric computation."""
    force_recompute: bool = False
    skip_validation: bool = False
    skip_event_publish: bool = False
    priority: str = "normal"  # low, normal, high, critical


@dataclass
class ComputationResult:
    """Result of metric computation."""
    success: bool
    computed_value: Optional[MetricComputedValue] = None
    
    # Timing and performance
    computation_time_ms: int = 0
    cache_hit: bool = False
    query_hash: str = ""
    
    # Quality
    quality_score: float = 0.0
    validation_passed: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    # Provenance
    sql_executed: str = ""
    records_scanned: int = 0
    
    # Error handling
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class DependencyResolution:
    """Result of dependency resolution."""
    execution_order: List[MetricDefinition]
    dependency_graph: Dict[uuid.UUID, List[uuid.UUID]]
    parallel_batches: List[List[uuid.UUID]]
    max_depth: int
    cycles: List[List[uuid.UUID]]


class AnalyticsQueryService(ABC):
    """Abstract interface for analytics queries."""
    
    @abstractmethod
    async def execute_query(
        self,
        sql: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        pass
    
    @abstractmethod
    async def get_table_count(
        self,
        table_name: str,
        filters: Dict[str, Any]
    ) -> int:
        """Get count of records in a table."""
        pass


class CacheService(ABC):
    """Abstract interface for caching."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def invalidate(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern."""
        pass


class DependencyResolver:
    """
    Resolves metric dependencies and determines execution order.
    """
    
    def __init__(self, metric_repository):
        self._repository = metric_repository
    
    async def resolve(self, metric_id: uuid.UUID) -> DependencyResolution:
        """
        Resolve dependencies for a metric.
        Returns topological sort order and dependency graph.
        """
        metric = await self._repository.get_by_id(metric_id)
        if not metric:
            raise ValueError(f"Metric {metric_id} not found")
        
        visited: Set[uuid.UUID] = set()
        visiting: Set[uuid.UUID] = set()
        order: List[MetricDefinition] = []
        graph: Dict[uuid.UUID, List[uuid.UUID]] = {}
        cycles: List[List[uuid.UUID]] = []
        
        async def dfs(mid: uuid.UUID, path: List[uuid.UUID]) -> bool:
            if mid in visiting:
                # Cycle detected
                cycle_start = path.index(mid)
                cycles.append(path[cycle_start:] + [mid])
                return True
            
            if mid in visited:
                return False
            
            visiting.add(mid)
            visited.add(mid)
            
            m = await self._repository.get_by_id(mid)
            if m:
                graph[mid] = m.depends_on or []
                for dep_id in (m.depends_on or []):
                    if await dfs(dep_id, path + [mid]):
                        return True
            
            visiting.remove(mid)
            order.append(m)
            return False
        
        if await dfs(metric_id, []):
            raise ValueError(f"Circular dependency detected for metric {metric_id}")
        
        # Group into parallel batches
        batches = self._group_into_batches(order, graph)
        
        return DependencyResolution(
            execution_order=order,
            dependency_graph=graph,
            parallel_batches=batches,
            max_depth=self._calculate_depth(graph, metric_id),
            cycles=cycles
        )
    
    async def get_affected_metrics(self, source_table: str) -> List[uuid.UUID]:
        """Get all metrics affected by changes to a source table."""
        # This would query metrics where source_tables contains the table
        all_metrics = await self._repository.list(uuid.UUID())  # Would need tenant_id
        affected = []
        
        for metric in all_metrics:
            if source_table in (metric.source_tables or []):
                affected.append(metric.entity_id)
        
        return affected
    
    def _group_into_batches(
        self,
        order: List[MetricDefinition],
        graph: Dict[uuid.UUID, List[uuid.UUID]]
    ) -> List[List[uuid.UUID]]:
        """Group metrics into parallel execution batches."""
        if not order:
            return []
        
        batches = []
        processed: Set[uuid.UUID] = set()
        
        for metric in order:
            deps = set(graph.get(metric.entity_id, []))
            if deps.issubset(processed):
                # All dependencies processed, can run in parallel
                if batches and not deps.intersection(set(batches[-1])):
                    batches[-1].append(metric.entity_id)
                else:
                    batches.append([metric.entity_id])
            else:
                batches.append([metric.entity_id])
            
            processed.add(metric.entity_id)
        
        return batches
    
    def _calculate_depth(
        self,
        graph: Dict[uuid.UUID, List[uuid.UUID]],
        metric_id: uuid.UUID
    ) -> int:
        """Calculate maximum depth of dependency tree."""
        visited: Set[uuid.UUID] = set()
        
        def dfs(mid: uuid.UUID) -> int:
            if mid in visited:
                return 0
            visited.add(mid)
            
            deps = graph.get(mid, [])
            if not deps:
                return 0
            
            max_child_depth = 0
            for dep_id in deps:
                child_depth = dfs(dep_id)
                max_child_depth = max(max_child_depth, child_depth)
            
            return max_child_depth + 1
        
        return dfs(metric_id)


class KPIComputationEngine:
    """
    The authoritative engine for all metric computations.
    All dashboards, APIs, and AI features consume from this engine only.
    """
    
    def __init__(
        self,
        metric_repository,
        computed_value_repository,
        analytics_service: AnalyticsQueryService,
        cache_service: Optional[CacheService] = None,
        event_publisher=None
    ):
        self._metric_repo = metric_repository
        self._computed_value_repo = computed_value_repository
        self._analytics = analytics_service
        self._cache = cache_service
        self._event_publisher = event_publisher
        self._dependency_resolver = DependencyResolver(metric_repository)
    
    async def compute_metric(
        self,
        metric_id: uuid.UUID,
        scope: ComputationScope,
        period: TimePeriod,
        options: ComputationOptions = ComputationOptions()
    ) -> ComputationResult:
        """
        Compute a single metric.
        Handles caching, dependency resolution, and error recovery.
        """
        start_time = datetime.utcnow()
        
        try:
            # Gate 1: METRIC_PUBLISHED
            metric = await self._metric_repo.get_by_id(metric_id)
            if not metric:
                return ComputationResult(
                    success=False,
                    error_code="METRIC_NOT_FOUND",
                    error_message=f"Metric {metric_id} not found"
                )
            
            if metric.status != MetricStatus.PUBLISHED and not options.force_recompute:
                return ComputationResult(
                    success=False,
                    error_code="METRIC_NOT_PUBLISHED",
                    error_message=f"Metric is in {metric.status} status"
                )
            
            # Gate 2: DEPENDENCIES_RESOLVED
            if metric.depends_on:
                for dep_id in metric.depends_on:
                    dep = await self._metric_repo.get_by_id(dep_id)
                    if not dep or dep.status != MetricStatus.PUBLISHED:
                        return ComputationResult(
                            success=False,
                            error_code="MISSING_DEPENDENCY",
                            error_message=f"Dependency {dep_id} is not published"
                        )
            
            # Check cache
            cache_key = self._build_cache_key(metric_id, scope, period)
            if not options.force_recompute and self._cache:
                cached = await self._cache.get(cache_key)
                if cached:
                    return ComputationResult(
                        success=True,
                        computed_value=cached,
                        cache_hit=True
                    )
            
            # Compute dependencies first
            dependency_values = {}
            if metric.depends_on:
                for dep_id in metric.depends_on:
                    result = await self.compute_metric(dep_id, scope, period, options)
                    if not result.success:
                        return result
                    dependency_values[dep_id] = result.computed_value
            
            # Gate 5: SOURCE_DATA_EXISTS
            # Execute SQL
            sql = self._build_sql(metric, scope, period)
            query_hash = hashlib.sha256(sql.encode()).hexdigest()
            
            results = await self._analytics.execute_query(sql, {})
            
            if not results:
                # No data - return zero value
                computed_value = MetricComputedValue(
                    tenant_id=scope.tenant_id,
                    metric_id=metric_id,
                    metric_version=metric.version,
                    value=0.0,
                    unit=MetricUnit(metric.unit),
                    confidence_score=0.0,
                    quality_score=0.0,
                    period_start=period.start,
                    period_end=period.end,
                    period_type=period.period_type,
                    source_query_hash=query_hash
                )
                return ComputationResult(
                    success=True,
                    computed_value=computed_value,
                    query_hash=query_hash
                )
            
            # Extract value from results
            value = results[0].get("value", 0.0) if results else 0.0
            
            # Gate 7: VALUE_REASONABLENESS
            validation_errors = []
            if not options.skip_validation:
                if metric.min_value is not None and value < metric.min_value:
                    validation_errors.append(f"Value {value} below minimum {metric.min_value}")
                if metric.max_value is not None and value > metric.max_value:
                    validation_errors.append(f"Value {value} above maximum {metric.max_value}")
            
            # Get previous value for comparison
            previous_value = await self._get_previous_value(
                metric_id, scope, period
            )
            
            # Create computed value
            computation_duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            computed_value = MetricComputedValue(
                tenant_id=scope.tenant_id,
                metric_id=metric_id,
                metric_version=metric.version,
                value=value,
                unit=MetricUnit(metric.unit),
                confidence_score=self._calculate_confidence(results),
                quality_score=metric.quality_score,
                period_start=period.start,
                period_end=period.end,
                period_type=period.period_type,
                previous_value=previous_value,
                computation_duration_ms=computation_duration,
                source_query_hash=query_hash,
                sample_size=len(results)
            )
            computed_value.compute_change()
            
            # Store result
            await self._computed_value_repo.create(computed_value)
            
            # Update cache
            if self._cache:
                await self._cache.set(cache_key, computed_value, ttl_seconds=300)
            
            # Publish event
            if not options.skip_event_publish and self._event_publisher:
                await self._event_publisher.publish_metric_computed(computed_value)
            
            return ComputationResult(
                success=True,
                computed_value=computed_value,
                computation_time_ms=computation_duration,
                query_hash=query_hash,
                validation_passed=len(validation_errors) == 0,
                validation_errors=validation_errors,
                sql_executed=sql,
                records_scanned=len(results)
            )
            
        except Exception as e:
            return ComputationResult(
                success=False,
                error_code="COMPUTATION_ERROR",
                error_message=str(e),
                computation_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
            )
    
    async def compute_metrics_batch(
        self,
        metric_ids: List[uuid.UUID],
        scope: ComputationScope,
        period: TimePeriod,
        options: ComputationOptions = ComputationOptions()
    ) -> List[ComputationResult]:
        """
        Compute multiple metrics efficiently.
        Groups by dependency DAG level for optimal execution order.
        """
        results = []
        
        # Resolve all dependencies
        all_metrics = set()
        for metric_id in metric_ids:
            try:
                resolution = await self._dependency_resolver.resolve(metric_id)
                for m in resolution.execution_order:
                    all_metrics.add(m.entity_id)
            except ValueError:
                results.append(ComputationResult(
                    success=False,
                    error_code="DEPENDENCY_ERROR",
                    error_message=f"Failed to resolve dependencies for {metric_id}"
                ))
        
        # Compute in dependency order
        computed = set()
        for metric_id in all_metrics:
            if metric_id not in computed:
                result = await self.compute_metric(metric_id, scope, period, options)
                results.append(result)
                if result.success:
                    computed.add(metric_id)
        
        return results
    
    async def compute_all_metrics_for_period(
        self,
        scope: ComputationScope,
        period: TimePeriod
    ) -> Dict[str, Any]:
        """
        Full refresh of all published metrics for a period.
        Used by nightly batch processing.
        """
        start_time = datetime.utcnow()
        
        # Get all published metrics
        all_metrics = await self._metric_repo.list(
            scope.tenant_id,
            {"status": MetricStatus.PUBLISHED}
        )
        
        results = []
        success_count = 0
        failure_count = 0
        
        for metric in all_metrics:
            result = await self.compute_metric(
                metric.entity_id,
                scope,
                period,
                ComputationOptions(skip_event_publish=True)
            )
            results.append(result)
            if result.success:
                success_count += 1
            else:
                failure_count += 1
        
        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return {
            "total_metrics": len(all_metrics),
            "success_count": success_count,
            "failure_count": failure_count,
            "duration_ms": duration,
            "results": results
        }
    
    async def get_cached_value(
        self,
        metric_id: uuid.UUID,
        scope: ComputationScope,
        period: TimePeriod
    ) -> Optional[MetricComputedValue]:
        """Get cached computed value if available."""
        cache_key = self._build_cache_key(metric_id, scope, period)
        
        if self._cache:
            cached = await self._cache.get(cache_key)
            if cached:
                return cached
        
        # Fall back to database
        return await self._computed_value_repo.get_by_period(
            metric_id, scope.tenant_id, period.start, period.end
        )
    
    async def invalidate_cache(
        self,
        metric_id: Optional[uuid.UUID] = None,
        scope: Optional[ComputationScope] = None
    ) -> None:
        """Invalidate cache for a metric or scope."""
        if self._cache:
            pattern = f"metric:*"
            if metric_id:
                pattern = f"metric:{metric_id}:*"
            await self._cache.invalidate(pattern)
    
    def _build_cache_key(
        self,
        metric_id: uuid.UUID,
        scope: ComputationScope,
        period: TimePeriod
    ) -> str:
        """Build cache key for a computation."""
        parts = [
            "metric",
            str(metric_id),
            str(scope.tenant_id),
            str(scope.hospital_id or "all"),
            str(scope.branch_id or "all"),
            str(scope.department_id or "all"),
            period.start.isoformat(),
            period.end.isoformat()
        ]
        return ":".join(parts)
    
    def _build_sql(
        self,
        metric: MetricDefinition,
        scope: ComputationScope,
        period: TimePeriod
    ) -> str:
        """Build SQL for metric computation."""
        if metric.sql_expression:
            sql = metric.sql_expression
            
            # Add scope filters
            filters = []
            if scope.hospital_id:
                filters.append(f"hospital_id = '{scope.hospital_id}'")
            if scope.branch_id:
                filters.append(f"branch_id = '{scope.branch_id}'")
            if scope.department_id:
                filters.append(f"department_id = '{scope.department_id}'")
            
            filters.append(f"service_date >= '{period.start.isoformat()}'")
            filters.append(f"service_date < '{period.end.isoformat()}'")
            
            where_clause = " AND ".join(filters)
            sql = sql.replace("{filters}", where_clause)
            
            return sql
        
        # Default query
        return f"""
            SELECT 0 as value
            WHERE 1=0
        """
    
    def _calculate_confidence(self, results: List[Dict]) -> float:
        """Calculate confidence score based on data quality."""
        if not results:
            return 0.0
        
        # Simple heuristic: more data = higher confidence
        record_count = len(results)
        if record_count >= 100:
            return 0.95
        elif record_count >= 50:
            return 0.85
        elif record_count >= 10:
            return 0.70
        else:
            return 0.50
    
    async def _get_previous_value(
        self,
        metric_id: uuid.UUID,
        scope: ComputationScope,
        period: TimePeriod
    ) -> Optional[float]:
        """Get value from previous period."""
        # Calculate previous period
        from datetime import timedelta
        
        duration = period.end - period.start
        previous_end = period.start
        previous_start = previous_end - duration
        
        previous_period = TimePeriod(
            start=previous_start,
            end=previous_end,
            period_type=period.period_type
        )
        
        cached = await self.get_cached_value(metric_id, scope, previous_period)
        return cached.value if cached else None
