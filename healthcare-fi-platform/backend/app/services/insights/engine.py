from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import structlog

from app.models.models import (
    Revenue, Expense, Claim, Occupancy, KPI, KPIValue,
    Branch, Department, Alert, AlertSeverity
)
from app.services.kpi.engine import KPIEngine

logger = structlog.get_logger()


class InsightsEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.kpi_engine = KPIEngine(db)

    async def detect_anomalies(
        self,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        anomalies = []
        
        query = select(
            Revenue.service_date,
            func.sum(Revenue.net_amount)
        ).group_by(Revenue.service_date)
        
        if branch_id:
            query = query.where(Revenue.branch_id == branch_id)
        if department_id:
            query = query.where(Revenue.department_id == department_id)
        if start_date:
            query = query.where(Revenue.service_date >= start_date)
        if end_date:
            query = query.where(Revenue.service_date <= end_date)
        
        query = query.order_by(Revenue.service_date)
        
        result = await self.db.execute(query)
        daily_revenue = result.all()
        
        if len(daily_revenue) < 7:
            return anomalies
        
        amounts = [r[1] for r in daily_revenue]
        mean_amount = sum(amounts) / len(amounts)
        std_amount = (sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)) ** 0.5
        
        for date, amount in daily_revenue:
            z_score = (amount - mean_amount) / std_amount if std_amount > 0 else 0
            
            if abs(z_score) > 2:
                anomaly_type = "spike" if z_score > 0 else "drop"
                severity = AlertSeverity.WARNING if abs(z_score) > 3 else AlertSeverity.INFO
                
                anomalies.append({
                    "date": date.isoformat(),
                    "amount": amount,
                    "expected_amount": mean_amount,
                    "z_score": z_score,
                    "anomaly_type": anomaly_type,
                    "severity": severity.value,
                    "description": f"Revenue {anomaly_type} detected: {amount:,.2f} vs expected {mean_amount:,.2f}"
                })
        
        return anomalies

    async def analyze_trends(
        self,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        insights = []
        
        kpis = await self.kpi_engine.get_all_kpis(branch_id, department_id)
        
        for kpi_code, kpi in kpis.items():
            if kpi.change_percent is not None:
                if abs(kpi.change_percent) > 10:
                    trend_direction = "significant_increase" if kpi.change_percent > 0 else "significant_decrease"
                    insights.append({
                        "type": "trend",
                        "kpi_code": kpi_code,
                        "kpi_name": kpi.name,
                        "current_value": kpi.value,
                        "change_percent": kpi.change_percent,
                        "trend_direction": trend_direction,
                        "description": f"{kpi.name} has {'increased' if kpi.change_percent > 0 else 'decreased'} by {abs(kpi.change_percent):.1f}%",
                        "severity": "warning" if kpi.change_percent < -10 else "info"
                    })
        
        return insights

    async def identify_opportunities(
        self,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        opportunities = []
        
        occupancy_kpis = await self.kpi_engine.calculate_occupancy_kpis(branch_id, department_id)
        occupancy_rate = occupancy_kpis["occupancy_rate"].value
        
        if occupancy_rate < 85:
            opportunities.append({
                "type": "occupancy_optimization",
                "current_rate": occupancy_rate,
                "target_rate": 85,
                "potential_improvement": 85 - occupancy_rate,
                "description": f"Occupancy rate is {occupancy_rate:.1f}%, below target of 85%. Opportunity to increase utilization.",
                "recommendation": "Consider marketing initiatives or partnerships to increase patient volume."
            })
        
        claim_kpis = await self.kpi_engine.calculate_claim_kpis(branch_id, department_id)
        approval_rate = claim_kpis["claim_approval_rate"].value
        
        if approval_rate < 90:
            opportunities.append({
                "type": "claims_optimization",
                "current_rate": approval_rate,
                "target_rate": 90,
                "potential_improvement": 90 - approval_rate,
                "description": f"Claim approval rate is {approval_rate:.1f}%, below target of 90%. Opportunity to improve revenue cycle.",
                "recommendation": "Review claim submission processes and improve documentation quality."
            })
        
        return opportunities

    async def generate_narrative(
        self,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        kpis = await self.kpi_engine.get_all_kpis(branch_id, department_id, start_date, end_date)
        
        revenue = kpis.get("total_revenue")
        expenses = kpis.get("total_expenses")
        profit = kpis.get("net_profit")
        margin = kpis.get("profit_margin")
        occupancy = kpis.get("occupancy_rate")
        claims = kpis.get("claim_approval_rate")
        
        narrative_parts = []
        
        if revenue:
            narrative_parts.append(
                f"Total revenue stands at ${revenue.value:,.2f}"
                f"{'down' if revenue.trend == 'down' else 'up'} "
                f"{abs(revenue.change_percent or 0):.1f}% from the previous period."
            )
        
        if profit:
            narrative_parts.append(
                f"Net profit is ${profit.value:,.2f} with a margin of {margin.value:.1f}%"
                f"{'below' if margin.value < 20 else 'above'} the target of 20%."
            )
        
        if occupancy:
            narrative_parts.append(
                f"Occupancy rate is {occupancy.value:.1f}%"
                f"{'below' if occupancy.value < 85 else 'above'} the target of 85%."
            )
        
        if claims:
            narrative_parts.append(
                f"Claim approval rate is {claims.value:.1f}%"
                f"{'below' if claims.value < 90 else 'above'} the target of 90%."
            )
        
        return " ".join(narrative_parts) if narrative_parts else "No data available for analysis."

    async def get_comprehensive_insights(
        self,
        branch_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        anomalies = await self.detect_anomalies(branch_id, department_id, start_date, end_date)
        trends = await self.analyze_trends(branch_id, department_id)
        opportunities = await self.identify_opportunities(branch_id, department_id)
        narrative = await self.generate_narrative(branch_id, department_id, start_date, end_date)
        
        return {
            "anomalies": anomalies,
            "trends": trends,
            "opportunities": opportunities,
            "narrative": narrative,
            "summary": {
                "anomaly_count": len(anomalies),
                "trend_count": len(trends),
                "opportunity_count": len(opportunities)
            }
        }

    async def create_alerts_from_insights(
        self,
        insights: Dict[str, Any]
    ) -> List[Alert]:
        alerts = []
        
        for anomaly in insights.get("anomalies", []):
            alert = Alert(
                title=f"Revenue Anomaly: {anomaly['anomaly_type'].title()}",
                message=anomaly["description"],
                severity=anomaly["severity"],
                category="revenue_anomaly",
                recommendation="Review recent transactions and investigate the cause."
            )
            self.db.add(alert)
            alerts.append(alert)
        
        for trend in insights.get("trends", []):
            if trend["severity"] == "warning":
                alert = Alert(
                    title=f"Significant Trend: {trend['kpi_name']}",
                    message=trend["description"],
                    severity="warning",
                    category="trend_alert",
                    recommendation="Analyze the root cause and take corrective action if needed."
                )
                self.db.add(alert)
                alerts.append(alert)
        
        await self.db.flush()
        
        return alerts
