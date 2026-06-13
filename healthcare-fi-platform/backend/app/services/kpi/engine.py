from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from dataclasses import dataclass
import structlog

from app.models.models import (
    Revenue, Expense, Claim, Occupancy, KPI, KPIValue,
    Branch, Department, Payer, Doctor, FinancialPeriod
)

logger = structlog.get_logger()


@dataclass
class KPIMetric:
    name: str
    code: str
    value: float
    target: Optional[float]
    previous_value: Optional[float]
    change_percent: Optional[float]
    trend: str
    category: str
    unit: Optional[str]


class KPIEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_revenue_kpis(
        self,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, KPIMetric]:
        query = select(func.sum(Revenue.net_amount))
        
        if branch_id:
            query = query.where(Revenue.branch_id == branch_id)
        if department_id:
            query = query.where(Revenue.department_id == department_id)
        if start_date:
            query = query.where(Revenue.service_date >= start_date)
        if end_date:
            query = query.where(Revenue.service_date <= end_date)
        
        result = await self.db.execute(query)
        total_revenue = result.scalar() or 0

        previous_start = start_date - timedelta(days=30) if start_date else None
        previous_end = start_date if start_date else None
        
        previous_query = select(func.sum(Revenue.net_amount))
        if previous_start:
            previous_query = previous_query.where(Revenue.service_date >= previous_start)
        if previous_end:
            previous_query = previous_query.where(Revenue.service_date < previous_end)
        if branch_id:
            previous_query = previous_query.where(Revenue.branch_id == branch_id)
        if department_id:
            previous_query = previous_query.where(Revenue.department_id == department_id)
        
        previous_result = await self.db.execute(previous_query)
        previous_revenue = previous_result.scalar() or 0

        change_percent = (
            ((total_revenue - previous_revenue) / previous_revenue * 100)
            if previous_revenue > 0
            else 0
        )

        return {
            "total_revenue": KPIMetric(
                name="Total Revenue",
                code="total_revenue",
                value=total_revenue,
                target=None,
                previous_value=previous_revenue,
                change_percent=change_percent,
                trend="up" if change_percent > 0 else "down" if change_percent < 0 else "stable",
                category="revenue",
                unit="currency"
            )
        }

    async def calculate_expense_kpis(
        self,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, KPIMetric]:
        query = select(func.sum(Expense.amount))
        
        if branch_id:
            query = query.where(Expense.branch_id == branch_id)
        if department_id:
            query = query.where(Expense.department_id == department_id)
        if start_date:
            query = query.where(Expense.expense_date >= start_date)
        if end_date:
            query = query.where(Expense.expense_date <= end_date)
        
        result = await self.db.execute(query)
        total_expenses = result.scalar() or 0

        return {
            "total_expenses": KPIMetric(
                name="Total Expenses",
                code="total_expenses",
                value=total_expenses,
                target=None,
                previous_value=None,
                change_percent=None,
                trend="stable",
                category="expense",
                unit="currency"
            )
        }

    async def calculate_profitability_kpis(
        self,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, KPIMetric]:
        revenue_kpis = await self.calculate_revenue_kpis(branch_id, department_id, start_date, end_date)
        expense_kpis = await self.calculate_expense_kpis(branch_id, department_id, start_date, end_date)
        
        total_revenue = revenue_kpis["total_revenue"].value
        total_expenses = expense_kpis["total_expenses"].value
        net_profit = total_revenue - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        return {
            "net_profit": KPIMetric(
                name="Net Profit",
                code="net_profit",
                value=net_profit,
                target=None,
                previous_value=None,
                change_percent=None,
                trend="up" if net_profit > 0 else "down",
                category="profitability",
                unit="currency"
            ),
            "profit_margin": KPIMetric(
                name="Profit Margin",
                code="profit_margin",
                value=profit_margin,
                target=20.0,
                previous_value=None,
                change_percent=None,
                trend="up" if profit_margin >= 20 else "down",
                category="profitability",
                unit="percentage"
            )
        }

    async def calculate_occupancy_kpis(
        self,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, KPIMetric]:
        query = select(
            func.sum(Occupancy.total_beds),
            func.sum(Occupancy.occupied_beds)
        )
        
        if branch_id:
            query = query.where(Occupancy.branch_id == branch_id)
        if department_id:
            query = query.where(Occupancy.department_id == department_id)
        
        result = await self.db.execute(query)
        row = result.first()
        total_beds = row[0] or 0
        occupied_beds = row[1] or 0
        occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0

        return {
            "occupancy_rate": KPIMetric(
                name="Occupancy Rate",
                code="occupancy_rate",
                value=occupancy_rate,
                target=85.0,
                previous_value=None,
                change_percent=None,
                trend="up" if occupancy_rate >= 85 else "down",
                category="occupancy",
                unit="percentage"
            )
        }

    async def calculate_claim_kpis(
        self,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, KPIMetric]:
        query = select(
            func.count(Claim.id),
            func.sum(Claim.total_amount),
            func.sum(Claim.approved_amount)
        )
        
        if branch_id:
            query = query.where(Claim.branch_id == branch_id)
        if department_id:
            query = query.where(Claim.department_id == department_id)
        if start_date:
            query = query.where(Claim.submitted_date >= start_date)
        if end_date:
            query = query.where(Claim.submitted_date <= end_date)
        
        result = await self.db.execute(query)
        row = result.first()
        total_claims = row[0] or 0
        total_claim_amount = row[1] or 0
        total_approved_amount = row[2] or 0
        
        approval_rate = (
            (total_approved_amount / total_claim_amount * 100)
            if total_claim_amount > 0
            else 0
        )

        return {
            "claim_approval_rate": KPIMetric(
                name="Claim Approval Rate",
                code="claim_approval_rate",
                value=approval_rate,
                target=90.0,
                previous_value=None,
                change_percent=None,
                trend="up" if approval_rate >= 90 else "down",
                category="claims",
                unit="percentage"
            ),
            "total_claims": KPIMetric(
                name="Total Claims",
                code="total_claims",
                value=total_claims,
                target=None,
                previous_value=None,
                change_percent=None,
                trend="stable",
                category="claims",
                unit="count"
            )
        }

    async def get_all_kpis(
        self,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, KPIMetric]:
        kpis = {}
        
        revenue_kpis = await self.calculate_revenue_kpis(branch_id, department_id, start_date, end_date)
        kpis.update(revenue_kpis)
        
        expense_kpis = await self.calculate_expense_kpis(branch_id, department_id, start_date, end_date)
        kpis.update(expense_kpis)
        
        profitability_kpis = await self.calculate_profitability_kpis(branch_id, department_id, start_date, end_date)
        kpis.update(profitability_kpis)
        
        occupancy_kpis = await self.calculate_occupancy_kpis(branch_id, department_id)
        kpis.update(occupancy_kpis)
        
        claim_kpis = await self.calculate_claim_kpis(branch_id, department_id, start_date, end_date)
        kpis.update(claim_kpis)
        
        return kpis

    async def get_kpi_trend(
        self,
        kpi_code: str,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None,
        periods: int = 12
    ) -> List[Dict[str, Any]]:
        query = select(KPIValue).where(KPIValue.kpi.has(code=kpi_code))
        
        if branch_id:
            query = query.where(KPIValue.branch_id == branch_id)
        if department_id:
            query = query.where(KPIValue.department_id == department_id)
        
        query = query.order_by(KPIValue.period_id.desc()).limit(periods)
        
        result = await self.db.execute(query)
        values = result.scalars().all()
        
        return [
            {
                "period_id": v.period_id,
                "value": v.value,
                "target_value": v.target_value,
                "previous_value": v.previous_value,
                "created_at": v.created_at.isoformat()
            }
            for v in reversed(values)
        ]

    async def get_revenue_by_department(
        self,
        branch_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        query = select(
            Department.name,
            func.sum(Revenue.net_amount).label("revenue"),
            func.count(Revenue.id).label("transaction_count")
        ).join(Department, Revenue.department_id == Department.id)
        
        if branch_id:
            query = query.where(Revenue.branch_id == branch_id)
        if start_date:
            query = query.where(Revenue.service_date >= start_date)
        if end_date:
            query = query.where(Revenue.service_date <= end_date)
        
        query = query.group_by(Department.id, Department.name).order_by(func.sum(Revenue.net_amount).desc())
        
        result = await self.db.execute(query)
        rows = result.all()
        
        departments = []
        for row in rows:
            departments.append({
                "name": row.name,
                "revenue": float(row.revenue or 0),
                "transaction_count": int(row.transaction_count or 0)
            })
        
        return departments

    async def get_revenue_by_payer(
        self,
        branch_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        query = select(
            Payer.name,
            Payer.payer_type,
            func.sum(Revenue.net_amount).label("revenue"),
            func.count(Revenue.id).label("transaction_count")
        ).join(Payer, Revenue.payer_id == Payer.id)
        
        if branch_id:
            query = query.where(Revenue.branch_id == branch_id)
        if start_date:
            query = query.where(Revenue.service_date >= start_date)
        if end_date:
            query = query.where(Revenue.service_date <= end_date)
        
        query = query.group_by(Payer.id, Payer.name, Payer.payer_type).order_by(func.sum(Revenue.net_amount).desc())
        
        result = await self.db.execute(query)
        rows = result.all()
        
        total_revenue = sum(float(row.revenue or 0) for row in rows)
        
        payers = []
        for row in rows:
            revenue = float(row.revenue or 0)
            payers.append({
                "name": row.name,
                "payer_type": row.payer_type,
                "revenue": revenue,
                "percentage": round((revenue / total_revenue * 100) if total_revenue > 0 else 0, 1),
                "transaction_count": int(row.transaction_count or 0)
            })
        
        return payers
