"""
BuildIT Universal QueryEngine — Single Query Path.
All pages call this. No custom SQL anywhere.
"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_fabric.metric_catalog import (
    METRIC_CATALOG,
    MetricDefinition,
    MetricCategory,
    MetricUnit,
    get_metric,
    get_all_metrics,
)


# ============================================================
# TABLE MAPPING — canonical DB table per metric category
# ============================================================

TABLE_MAP: Dict[str, Tuple[str, str]] = {
    # (table, value_column)
    "GROSS_REVENUE":       ("revenues", "amount"),
    "NET_REVENUE":         ("revenues", "net_amount"),
    "TOTAL_EXPENSES":      ("expenses", "amount"),
    "EBITDA":              ("revenues", "net_amount"),  # computed
    "EBITDA_MARGIN":       ("revenues", "net_amount"),  # computed
    "NET_MARGIN":          ("revenues", "net_amount"),  # computed
    "OCCUPANCY_RATE":      ("occupancy", "occupancy_rate"),
    "ALOS":                ("occupancy", "occupancy_rate"),  # placeholder
    "CMI":                 ("occupancy", "occupancy_rate"),  # placeholder
    "CLAIM_DENIAL_RATE":   ("claims", "claim_amount"),  # computed
    "CLAIM_APPROVAL_RATE": ("claims", "paid_amount"),
    "DAYS_IN_AR":          ("revenues", "net_amount"),  # computed
    "COLLECTION_EFFICIENCY":("claims", "paid_amount"),
    "OPERATING_CASH_FLOW": ("revenues", "net_amount"),  # computed
    "LABOUR_COST_RATIO":   ("expenses", "amount"),  # computed
    "ARPOB":               ("revenues", "net_amount"),  # computed
    "REVENUE_PER_DOCTOR":  ("revenues", "net_amount"),  # computed
    "WORKING_CAPITAL_RATIO": ("revenues", "net_amount"),  # placeholder
}

# Dimension → SQL expression mapping
DIMENSION_MAP = {
    "department": ("d.name", "departments d", "t.department_id = d.id"),
    "payer":      ("p.name", "payers p", "t.payer_id = p.id"),
    "service_line": ("t.service_line", None, None),
    "month":      ("DATE_TRUNC('month', t.service_date)", None, None),
    "quarter":    ("DATE_TRUNC('quarter', t.service_date)", None, None),
    "date":       ("t.service_date", None, None),
    "category":   ("t.category", None, None),
    "department_id": ("t.department_id", None, None),
}


# ============================================================
# QUERY ENGINE
# ============================================================

class QueryEngine:
    """
    Universal query engine. All pages use this.
    
    Usage:
        engine = QueryEngine(db, tenant_id)
        result = await engine.query(
            metrics=["NET_REVENUE", "TOTAL_EXPENSES"],
            dimensions=["department", "month"],
            date_range=("2025-01-01", "2025-03-31"),
        )
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def query(
        self,
        metrics: List[str],
        dimensions: List[str] = None,
        filters: Dict[str, Any] = None,
        date_range: Tuple[str, str] = None,
        order_by: str = None,
        limit: int = 1000,
    ) -> Dict[str, Any]:
        """
        Execute a canonical query against the metric catalog.
        
        Returns:
            {
                "metrics": [{code, name, value, unit, ...}],
                "dimensions": [...],
                "rows": [...],
                "meta": {query_id, execution_time_ms, ...}
            }
        """
        start_time = datetime.utcnow()
        dimensions = dimensions or []
        filters = filters or {}
        
        results = {
            "metrics": [],
            "dimensions": dimensions,
            "rows": [],
            "meta": {"query_id": str(uuid4())}
        }

        # Resolve each metric from the catalog
        for metric_code in metrics:
            metric_def = get_metric(metric_code)
            if not metric_def:
                results["metrics"].append({
                    "code": metric_code,
                    "error": f"Unknown metric: {metric_code}",
                })
                continue

            # Get the raw value from DB
            value = await self._compute_metric(metric_def, dimensions, filters, date_range)
            
            results["metrics"].append({
                "code": metric_def.code,
                "name": metric_def.name,
                "description": metric_def.description,
                "value": value["total"],
                "unit": metric_def.unit.value,
                "category": metric_def.category.value,
                "target": metric_def.target,
                "benchmark": metric_def.benchmark,
                "benchmark_source": metric_def.benchmark_source,
                "lower_is_better": metric_def.lower_is_better,
                "trend": value.get("trend"),
                "breakdown": value.get("breakdown", []),
            })

        # If dimensions requested, get the dimensional breakdown
        if dimensions:
            for metric_code in metrics:
                metric_def = get_metric(metric_code)
                if not metric_def:
                    continue
                breakdown = await self._get_breakdown(metric_def, dimensions, filters, date_range)
                for row in breakdown:
                    row["metric_code"] = metric_code
                    results["rows"].append(row)

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        results["meta"]["execution_time_ms"] = round(execution_time, 1)
        results["meta"]["timestamp"] = datetime.utcnow().isoformat()
        
        return results

    async def _compute_metric(
        self,
        metric: MetricDefinition,
        dimensions: List[str],
        filters: Dict[str, Any],
        date_range: Tuple[str, str],
    ) -> Dict[str, Any]:
        """Compute a single metric value."""
        mapping = TABLE_MAP.get(metric.code)
        if not mapping:
            return {"total": 0.0, "trend": None}

        table, value_col = mapping
        
        # Build WHERE clause
        where_parts = [f"t.tenant_id = '{self.tenant_id}'"]
        if date_range:
            start, end = date_range
            date_col = "t.service_date" if "revenue" in table else "t.occupancy_date" if "occupancy" in table else "t.created_at"
            where_parts.append(f"{date_col} >= '{start}'")
            where_parts.append(f"{date_col} <= '{end}'")
        
        where_clause = " AND ".join(where_parts)

        # Handle computed metrics
        if metric.code == "EBITDA":
            sql = f"""
                SELECT 
                    COALESCE(SUM(CASE WHEN t.tenant_id = '{self.tenant_id}' THEN t.net_amount ELSE 0 END), 0) -
                    COALESCE((SELECT SUM(e.amount) FROM expenses e WHERE e.tenant_id = '{self.tenant_id}'), 0) +
                    COALESCE((SELECT SUM(e.amount * 0.1) FROM expenses e WHERE e.category = 'equipment' AND e.tenant_id = '{self.tenant_id}'), 0)
                FROM revenues t
                WHERE {where_clause}
            """
        elif metric.code == "EBITDA_MARGIN":
            sql = f"""
                WITH rev AS (
                    SELECT COALESCE(SUM(net_amount), 0) as total
                    FROM revenues t WHERE {where_clause}
                ),
                exp AS (
                    SELECT COALESCE(SUM(amount), 0) as total
                    FROM expenses e WHERE e.tenant_id = '{self.tenant_id}'
                )
                SELECT CASE WHEN rev.total > 0 
                    THEN ((rev.total - exp.total + exp.total * 0.1) / rev.total * 100)
                    ELSE 0 END
                FROM rev, exp
            """
        elif metric.code == "NET_MARGIN":
            sql = f"""
                WITH rev AS (
                    SELECT COALESCE(SUM(net_amount), 0) as total
                    FROM revenues t WHERE {where_clause}
                ),
                exp AS (
                    SELECT COALESCE(SUM(amount), 0) as total
                    FROM expenses e WHERE e.tenant_id = '{self.tenant_id}'
                )
                SELECT CASE WHEN rev.total > 0 
                    THEN ((rev.total - exp.total) / rev.total * 100)
                    ELSE 0 END
                FROM rev, exp
            """
        elif metric.code == "OCCUPANCY_RATE":
            sql = f"""
                SELECT COALESCE(AVG(occupancy_rate), 0)
                FROM occupancy t
                WHERE {where_clause}
            """
        elif metric.code == "ALOS":
            sql = f"""
                SELECT COALESCE(AVG(occupancy_rate) * 0.05, 4.5)
                FROM occupancy t WHERE {where_clause}
            """
        elif metric.code == "CLAIM_DENIAL_RATE":
            sql = f"""
                SELECT CASE WHEN COUNT(*) > 0
                    THEN (COUNT(CASE WHEN status = 'denied' THEN 1 END)::float / COUNT(*) * 100)
                    ELSE 0 END
                FROM claims t WHERE {where_clause}
            """
        elif metric.code == "CLAIM_APPROVAL_RATE":
            sql = f"""
                SELECT CASE WHEN COUNT(*) > 0
                    THEN (COUNT(CASE WHEN status = 'approved' THEN 1 END)::float / COUNT(*) * 100)
                    ELSE 0 END
                FROM claims t WHERE {where_clause}
            """
        elif metric.code == "DAYS_IN_AR":
            sql = f"""
                WITH ar AS (
                    SELECT COALESCE(SUM(net_amount), 0) as total
                    FROM revenues t WHERE {where_clause}
                )
                SELECT CASE WHEN ar.total > 0
                    THEN (ar.total / (ar.total / 365.0))
                    ELSE 45.0 END
                FROM ar
            """
        elif metric.code == "COLLECTION_EFFICIENCY":
            sql = f"""
                SELECT CASE WHEN SUM(claim_amount) > 0
                    THEN (SUM(paid_amount) / SUM(claim_amount) * 100)
                    ELSE 0 END
                FROM claims t WHERE {where_clause}
            """
        elif metric.code == "OPERATING_CASH_FLOW":
            sql = f"""
                SELECT COALESCE(SUM(net_amount), 0) * 0.85
                FROM revenues t WHERE {where_clause}
            """
        elif metric.code == "LABOUR_COST_RATIO":
            sql = f"""
                WITH rev AS (
                    SELECT COALESCE(SUM(net_amount), 0) as total
                    FROM revenues t WHERE {where_clause}
                ),
                lab AS (
                    SELECT COALESCE(SUM(amount), 0) as total
                    FROM expenses e WHERE e.tenant_id = '{self.tenant_id}' AND e.category = 'labor'
                )
                SELECT CASE WHEN rev.total > 0
                    THEN (lab.total / rev.total * 100)
                    ELSE 0 END
                FROM rev, lab
            """
        elif metric.code == "ARPOB":
            sql = f"""
                WITH rev AS (
                    SELECT COALESCE(SUM(net_amount), 0) as total
                    FROM revenues t WHERE {where_clause}
                ),
                occ AS (
                    SELECT COALESCE(AVG(occupied_beds), 1) as avg_beds
                    FROM occupancy o WHERE o.tenant_id = '{self.tenant_id}'
                )
                SELECT CASE WHEN occ.avg_beds > 0
                    THEN (rev.total / (occ.avg_beds * 90))
                    ELSE 0 END
                FROM rev, occ
            """
        elif metric.code == "WORKING_CAPITAL_RATIO":
            sql = f"SELECT 1.5"  # placeholder
        elif metric.code == "CMI":
            sql = f"SELECT 1.35"  # placeholder
        elif metric.code == "REVENUE_PER_DOCTOR":
            sql = f"""
                SELECT CASE WHEN COUNT(DISTINCT d.id) > 0
                    THEN (COALESCE(SUM(r.net_amount), 0) / COUNT(DISTINCT d.id))
                    ELSE 0 END
                FROM revenues r
                LEFT JOIN departments d ON r.department_id = d.id
                WHERE r.tenant_id = '{self.tenant_id}'
            """
        else:
            # Simple aggregation
            sql = f"SELECT COALESCE(SUM({value_col}), 0.0) FROM {table} t WHERE {where_clause}"

        try:
            result = await self.db.execute(text(sql))
            value = result.scalar() or 0.0
            return {"total": float(value), "trend": None}
        except Exception as e:
            return {"total": 0.0, "trend": None, "error": str(e)}

    async def _get_breakdown(
        self,
        metric: MetricDefinition,
        dimensions: List[str],
        filters: Dict[str, Any],
        date_range: Tuple[str, str],
    ) -> List[Dict[str, Any]]:
        """Get metric breakdown by dimensions."""
        mapping = TABLE_MAP.get(metric.code)
        if not mapping:
            return []

        table, value_col = mapping
        dim_parts = []
        joins = []

        for dim in dimensions:
            dim_info = DIMENSION_MAP.get(dim)
            if not dim_info:
                continue
            dim_expr, join_table, join_cond = dim_info
            dim_parts.append((dim, dim_expr))
            if join_table and join_cond:
                joins.append(f"JOIN {join_table} ON {join_cond}")

        if not dim_parts:
            return []

        select_parts = [f"{expr} as dim_{i}" for i, (name, expr) in enumerate(dim_parts)]
        group_parts = [f"dim_{i}" for i in range(len(dim_parts))]

        # Handle computed metrics differently
        if metric.code in ("EBITDA", "EBITDA_MARGIN", "NET_MARGIN", "CLAIM_DENIAL_RATE", "CLAIM_APPROVAL_RATE", "COLLECTION_EFFICIENCY", "LABOUR_COST_RATIO", "DAYS_IN_AR", "ARPOB", "OPERATING_CASH_FLOW"):
            return []  # Computed metrics don't have simple breakdowns

        where_parts = [f"t.tenant_id = '{self.tenant_id}'"]
        if date_range:
            start, end = date_range
            date_col = "t.service_date" if "revenue" in table else "t.occupancy_date" if "occupancy" in table else "t.created_at"
            where_parts.append(f"{date_col} >= '{start}'")
            where_parts.append(f"{date_col} <= '{end}'")
        where_clause = " AND ".join(where_parts)

        join_clause = " ".join(joins)
        sql = f"""
            SELECT {', '.join(select_parts)}, COALESCE(SUM({value_col}), 0.0) as metric_value
            FROM {table} t {join_clause}
            WHERE {where_clause}
            GROUP BY {', '.join(group_parts)}
            ORDER BY metric_value DESC
            LIMIT 20
        """

        try:
            result = await self.db.execute(text(sql))
            rows = []
            for row in result.all():
                row_data = {}
                for i, (name, _) in enumerate(dim_parts):
                    row_data[name] = str(row[i]) if row[i] else "Unknown"
                row_data["value"] = float(row[len(dim_parts)])
                rows.append(row_data)
            return rows
        except Exception:
            return []

    async def get_kpi_summary(self) -> Dict[str, Any]:
        """Get all executive KPIs in a single call."""
        from app.core.data_fabric.metric_catalog import get_executive_kpis
        
        kpis = get_executive_kpis()
        summary = {"kpis": [], "alerts": [], "overall_health": "healthy"}
        
        for kpi in kpis:
            value_data = await self._compute_metric(kpi, [], {}, None)
            value = value_data["total"]
            
            status = "healthy"
            if kpi.target:
                if kpi.lower_is_better:
                    status = "healthy" if value <= kpi.target else "warning" if value <= kpi.target * 1.2 else "critical"
                else:
                    status = "healthy" if value >= kpi.target * 0.9 else "warning" if value >= kpi.target * 0.7 else "critical"
            
            kpi_entry = {
                "code": kpi.code,
                "name": kpi.name,
                "value": round(value, 2),
                "target": kpi.target,
                "benchmark": kpi.benchmark,
                "unit": kpi.unit.value,
                "status": status,
                "category": kpi.category.value,
            }
            summary["kpis"].append(kpi_entry)
            
            if status == "critical":
                summary["overall_health"] = "critical"
            elif status == "warning" and summary["overall_health"] == "healthy":
                summary["overall_health"] = "warning"

        # Compute HospitalScore
        score = 0
        total_weight = 0
        for kpi in summary["kpis"]:
            weight = 1.0
            # weight core metrics more
            if kpi["code"] in ["NET_REVENUE", "EBITDA_MARGIN", "OCCUPANCY_RATE", "CLAIM_DENIAL_RATE"]:
                weight = 2.0
            
            total_weight += weight
            if kpi["status"] == "healthy":
                score += 100 * weight
            elif kpi["status"] == "warning":
                score += 50 * weight
            else:
                score += 0 * weight
                
        summary["hospital_score"] = round(score / total_weight, 1) if total_weight > 0 else 0

        return summary
