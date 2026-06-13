"""
MetricRegistry service for managing metric definitions.
Central authority for all metric definitions with version management.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from app.domain.entities.metric import (
    MetricDefinition,
    MetricCategory,
    MetricStatus,
    TrustLevel
)
from app.domain.repositories.interfaces import MetricDefinitionRepository


class CyclicDependencyError(Exception):
    """Raised when metric dependencies form a cycle."""
    pass


class MetricNotFoundError(Exception):
    """Raised when a metric is not found."""
    pass


class MetricPublishError(Exception):
    """Raised when a metric cannot be published."""
    pass


@dataclass
class ValidationResult:
    """Result of formula validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class MetricRegistry:
    """
    The MetricRegistry is the central authority for all metric definitions.
    Provides CRUD, version management, dependency resolution, and governance.
    """
    
    def __init__(self, repository: MetricDefinitionRepository):
        self._repository = repository
    
    async def register(
        self,
        metric: MetricDefinition,
        created_by: uuid.UUID
    ) -> MetricDefinition:
        """
        Register a new metric definition.
        Validates uniqueness and dependency graph.
        """
        # Check slug uniqueness
        existing = await self._repository.get_by_slug(metric.slug, metric.tenant_id)
        if existing and existing.entity_id != metric.entity_id:
            raise ValueError(f"Metric with slug '{metric.slug}' already exists")
        
        # Check code uniqueness
        existing = await self._repository.get_by_code(metric.code, metric.tenant_id)
        if existing and existing.entity_id != metric.entity_id:
            raise ValueError(f"Metric with code '{metric.code}' already exists")
        
        # Validate dependencies exist
        if metric.depends_on:
            await self._validate_dependencies(metric.depends_on, metric.tenant_id)
            
            # Check for cycles
            if await self._has_circular_dependency(metric.entity_id, metric.depends_on, metric.tenant_id):
                raise CyclicDependencyError(f"Metric '{metric.slug}' has circular dependencies")
        
        metric.created_by = created_by
        metric.updated_by = created_by
        
        return await self._repository.create(metric)
    
    async def publish(
        self,
        metric_id: uuid.UUID,
        published_by: uuid.UUID
    ) -> MetricDefinition:
        """
        Publish a metric definition.
        All dependencies must be published first.
        """
        metric = await self._repository.get_by_id(metric_id)
        if not metric:
            raise MetricNotFoundError(f"Metric {metric_id} not found")
        
        # Validate all dependencies are published
        if metric.depends_on:
            for dep_id in metric.depends_on:
                dep = await self._repository.get_by_id(dep_id)
                if not dep or dep.status != MetricStatus.PUBLISHED:
                    raise MetricPublishError(
                        f"Dependency {dep_id} is not published"
                    )
        
        metric.publish(published_by)
        return await self._repository.update(metric)
    
    async def deprecate(
        self,
        metric_id: uuid.UUID,
        reason: str,
        deprecated_by: uuid.UUID
    ) -> MetricDefinition:
        """
        Deprecate a metric definition.
        """
        metric = await self._repository.get_by_id(metric_id)
        if not metric:
            raise MetricNotFoundError(f"Metric {metric_id} not found")
        
        # Check if any active metrics depend on this one
        dependents = await self._get_dependents(metric_id, metric.tenant_id)
        active_dependents = [d for d in dependents if d.status == MetricStatus.PUBLISHED]
        
        if active_dependents:
            dependent_names = [d.name for d in active_dependents[:5]]
            raise MetricPublishError(
                f"Cannot deprecate: {len(active_dependents)} active metrics depend on this one. "
                f"First deprecate: {', '.join(dependent_names)}"
            )
        
        metric.deprecate(reason, deprecated_by)
        return await self._repository.update(metric)
    
    async def certify(
        self,
        metric_id: uuid.UUID,
        certified_by: uuid.UUID
    ) -> MetricDefinition:
        """
        Certify a metric for audit readiness.
        """
        metric = await self._repository.get_by_id(metric_id)
        if not metric:
            raise MetricNotFoundError(f"Metric {metric_id} not found")
        
        metric.certify(certified_by)
        return await self._repository.update(metric)
    
    async def get_version(
        self,
        metric_id: uuid.UUID,
        version: int
    ) -> Optional[MetricDefinition]:
        """
        Get a specific version of a metric definition.
        Note: Current implementation returns latest version.
        Version history would require separate version table.
        """
        return await self._repository.get_by_id(metric_id)
    
    async def list_active(
        self,
        tenant_id: uuid.UUID,
        category: Optional[MetricCategory] = None
    ) -> List[MetricDefinition]:
        """
        List all active (published) metrics.
        """
        filters = {"status": MetricStatus.PUBLISHED}
        if category:
            filters["category"] = category.value
        
        return await self._repository.list(tenant_id, filters)
    
    async def resolve_dependencies(
        self,
        metric_id: uuid.UUID
    ) -> List[MetricDefinition]:
        """
        Resolve dependencies and return topological sort order.
        """
        metric = await self._repository.get_by_id(metric_id)
        if not metric:
            raise MetricNotFoundError(f"Metric {metric_id} not found")
        
        visited = set()
        order = []
        
        async def dfs(mid: uuid.UUID):
            if mid in visited:
                return
            visited.add(mid)
            
            m = await self._repository.get_by_id(mid)
            if m and m.depends_on:
                for dep_id in m.depends_on:
                    await dfs(dep_id)
            
            if m:
                order.append(m)
        
        await dfs(metric_id)
        return order
    
    async def validate_formula(
        self,
        sql: str,
        python: str
    ) -> ValidationResult:
        """
        Validate metric formula syntax.
        """
        errors = []
        warnings = []
        
        # Basic SQL validation
        if sql and not sql.strip():
            errors.append("SQL expression is empty")
        
        # Basic Python validation
        if python and not python.strip():
            warnings.append("Python expression is empty")
        
        # Check for dangerous SQL operations
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE"]
        sql_upper = sql.upper() if sql else ""
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                errors.append(f"SQL contains dangerous operation: {keyword}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def _validate_dependencies(
        self,
        dependency_ids: List[uuid.UUID],
        tenant_id: uuid.UUID
    ) -> None:
        """Validate that all dependencies exist."""
        for dep_id in dependency_ids:
            dep = await self._repository.get_by_id(dep_id)
            if not dep:
                raise ValueError(f"Dependency metric {dep_id} not found")
            if dep.tenant_id != tenant_id:
                raise ValueError(f"Dependency metric {dep_id} belongs to different tenant")
    
    async def _has_circular_dependency(
        self,
        metric_id: uuid.UUID,
        depends_on: List[uuid.UUID],
        tenant_id: uuid.UUID
    ) -> bool:
        """Check if adding dependencies would create a cycle."""
        visited = set()
        
        async def dfs(mid: uuid.UUID) -> bool:
            if mid == metric_id:
                return True  # Cycle detected
            if mid in visited:
                return False
            visited.add(mid)
            
            m = await self._repository.get_by_id(mid)
            if m and m.depends_on:
                for dep_id in m.depends_on:
                    if await dfs(dep_id):
                        return True
            return False
        
        for dep_id in depends_on:
            if await dfs(dep_id):
                return True
        return False
    
    async def _get_dependents(
        self,
        metric_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> List[MetricDefinition]:
        """Get all metrics that depend on the given metric."""
        all_metrics = await self._repository.list(tenant_id)
        return [m for m in all_metrics if metric_id in (m.depends_on or [])]


# Pre-defined metric registry
PREDEFINED_METRICS = [
    {
        "name": "Gross Revenue",
        "slug": "gross_revenue",
        "code": "GROSS_REV",
        "category": "revenue",
        "formula": "SUM(revenue.amount)",
        "sql_expression": "SELECT SUM(amount) FROM revenues WHERE {filters}",
        "unit": "currency",
        "aggregation": "sum",
        "direction": 1,
        "description": "Total gross revenue before deductions"
    },
    {
        "name": "Net Revenue",
        "slug": "net_revenue",
        "code": "NET_REV",
        "category": "revenue",
        "formula": "SUM(revenue.net_amount)",
        "sql_expression": "SELECT SUM(net_amount) FROM revenues WHERE {filters}",
        "unit": "currency",
        "aggregation": "sum",
        "direction": 1,
        "description": "Total net revenue after deductions"
    },
    {
        "name": "Total Expenses",
        "slug": "total_expenses",
        "code": "TOTAL_EXP",
        "category": "expense",
        "formula": "SUM(expense.amount)",
        "sql_expression": "SELECT SUM(amount) FROM expenses WHERE {filters}",
        "unit": "currency",
        "aggregation": "sum",
        "direction": -1,
        "description": "Total operating expenses"
    },
    {
        "name": "Net Margin",
        "slug": "net_margin",
        "code": "NET_MARGIN",
        "category": "profitability",
        "formula": "(Net Revenue - Total Expenses) / Net Revenue * 100",
        "depends_on": ["net_revenue", "total_expenses"],
        "unit": "percentage",
        "aggregation": "avg",
        "direction": 1,
        "description": "Net profit margin percentage"
    },
    {
        "name": "Occupancy Rate",
        "slug": "occupancy_rate",
        "code": "OCC_RATE",
        "category": "occupancy",
        "formula": "SUM(occupied_beds) / SUM(total_beds) * 100",
        "sql_expression": "SELECT SUM(occupied_beds)::float / NULLIF(SUM(total_beds), 0) * 100 FROM occupancy WHERE {filters}",
        "unit": "percentage",
        "aggregation": "avg",
        "direction": 1,
        "description": "Bed occupancy rate percentage"
    },
    {
        "name": "Claim Approval Rate",
        "slug": "claim_approval_rate",
        "code": "CLAIM_APP_RATE",
        "category": "claims",
        "formula": "COUNT(approved claims) / COUNT(submitted claims) * 100",
        "sql_expression": "SELECT COUNT(CASE WHEN status = 'approved' THEN 1 END)::float / NULLIF(COUNT(*), 0) * 100 FROM claims WHERE {filters}",
        "unit": "percentage",
        "aggregation": "avg",
        "direction": 1,
        "description": "Percentage of claims approved"
    }
]
