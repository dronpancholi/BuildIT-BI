from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4


class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


class PriorityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DecisionCategory(Enum):
    INVESTMENT = "investment"
    COST_REDUCTION = "cost_reduction"
    REVENUE_GROWTH = "revenue_growth"
    RISK = "risk"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"


@dataclass
class KPIStatus:
    name: str
    value: Decimal
    target: Decimal
    unit: str
    status: HealthStatus
    trend: str
    trend_percentage: float
    last_updated: datetime
    data_points: int
    is_real_time: bool


@dataclass
class AlertItem:
    id: UUID
    severity: PriorityLevel
    category: DecisionCategory
    title: str
    summary: str
    metric_id: Optional[UUID]
    metric_name: Optional[str]
    value: Optional[Decimal]
    threshold: Optional[Decimal]
    timestamp: datetime
    is_read: bool
    recommended_actions: List[str]


@dataclass
class DecisionNeed:
    id: UUID
    title: str
    description: str
    category: DecisionCategory
    priority: PriorityLevel
    status: str
    impact_estimate: Dict
    deadline: Optional[datetime]
    context: Dict
    created_at: datetime


@dataclass
class PerformanceSummary:
    score: float
    components: Dict
    trend: str
    historical_scores: List[Dict]
    data_quality: float
    completeness: float


@dataclass
class RevenueForecast:
    id: UUID
    period: str
    forecasted_revenue: Decimal
    confidence_interval: Tuple[Decimal, Decimal]
    model_used: str
    data_points: int
    accuracy: float
    assumptions: List[str]
    created_at: datetime


@dataclass
class CostForecast:
    id: UUID
    period: str
    forecasted_cost: Decimal
    cost_breakdown: Dict
    cost_drivers: List[Dict]
    confidence: float
    recommendations: List[str]
    created_at: datetime


@dataclass
class RiskSummary:
    id: UUID
    overall_risk_score: float
    risk_level: HealthStatus
    risks: List[Dict]
    risk_categories: Dict
    mitigation_suggestions: List[str]
    created_at: datetime


@dataclass
class ExecutiveBriefing:
    id: UUID
    period: str
    period_type: str
    generated_at: datetime
    sections: List[Dict]
    overall_health: HealthStatus
    financial_score: float
    operational_score: float
    strategic_score: float
    narrative: str
    executive_summary: str
    key_actions: List[str]
    risks: List[str]


class ExecutiveCenterService:
    def __init__(self) -> None:
        self._kpi_data: Dict[UUID, List[KPIStatus]] = {}
        self._alerts: Dict[UUID, List[AlertItem]] = {}
        self._decisions: Dict[UUID, List[DecisionNeed]] = {}
        self._briefings: Dict[UUID, List[ExecutiveBriefing]] = {}
        self._seed_data: bool = True

    def _ensure_seed_data(self, tenant_id: UUID) -> None:
        if tenant_id not in self._kpi_data or not self._kpi_data[tenant_id]:
            self._seed_kpi_data(tenant_id)
            self._seed_alert_data(tenant_id)
            self._seed_decision_data(tenant_id)

    def _seed_kpi_data(self, tenant_id: UUID) -> None:
        now = datetime.utcnow()
        kpis = [
            KPIStatus(
                name="Monthly Recurring Revenue",
                value=Decimal("2450000.00"),
                target=Decimal("2500000.00"),
                unit="USD",
                status=HealthStatus.WARNING,
                trend="up",
                trend_percentage=3.2,
                last_updated=now - timedelta(minutes=5),
                data_points=365,
                is_real_time=True,
            ),
            KPIStatus(
                name="Gross Margin",
                value=Decimal("68.5"),
                target=Decimal("70.0"),
                unit="%",
                status=HealthStatus.WARNING,
                trend="down",
                trend_percentage=-0.5,
                last_updated=now - timedelta(minutes=12),
                data_points=365,
                is_real_time=True,
            ),
            KPIStatus(
                name="Customer Acquisition Cost",
                value=Decimal("1850.00"),
                target=Decimal("2000.00"),
                unit="USD",
                status=HealthStatus.HEALTHY,
                trend="down",
                trend_percentage=-5.8,
                last_updated=now - timedelta(hours=1),
                data_points=180,
                is_real_time=False,
            ),
            KPIStatus(
                name="Net Revenue Retention",
                value=Decimal("112.0"),
                target=Decimal("110.0"),
                unit="%",
                status=HealthStatus.HEALTHY,
                trend="up",
                trend_percentage=1.5,
                last_updated=now - timedelta(hours=2),
                data_points=365,
                is_real_time=False,
            ),
            KPIStatus(
                name="Days Sales Outstanding",
                value=Decimal("42.0"),
                target=Decimal("35.0"),
                unit="days",
                status=HealthStatus.CRITICAL,
                trend="up",
                trend_percentage=8.0,
                last_updated=now - timedelta(minutes=30),
                data_points=365,
                is_real_time=False,
            ),
            KPIStatus(
                name="Operating Cash Flow",
                value=Decimal("890000.00"),
                target=Decimal("900000.00"),
                unit="USD",
                status=HealthStatus.WARNING,
                trend="up",
                trend_percentage=2.1,
                last_updated=now - timedelta(hours=6),
                data_points=365,
                is_real_time=False,
            ),
            KPIStatus(
                name="Revenue per Employee",
                value=Decimal("185000.00"),
                target=Decimal("175000.00"),
                unit="USD",
                status=HealthStatus.HEALTHY,
                trend="up",
                trend_percentage=4.2,
                last_updated=now - timedelta(days=1),
                data_points=365,
                is_real_time=False,
            ),
            KPIStatus(
                name="Employee Utilization",
                value=Decimal("82.0"),
                target=Decimal("85.0"),
                unit="%",
                status=HealthStatus.WARNING,
                trend="down",
                trend_percentage=-1.2,
                last_updated=now - timedelta(hours=3),
                data_points=90,
                is_real_time=True,
            ),
        ]
        self._kpi_data[tenant_id] = kpis

    def _seed_alert_data(self, tenant_id: UUID) -> None:
        now = datetime.utcnow()
        alerts = [
            AlertItem(
                id=uuid4(),
                severity=PriorityLevel.CRITICAL,
                category=DecisionCategory.OPERATIONAL,
                title="DSO Exceeding Threshold",
                summary="Days Sales Outstanding has risen to 42 days, exceeding the 35-day target. Cash flow impact estimated at $120K monthly.",
                metric_id=uuid4(),
                metric_name="Days Sales Outstanding",
                value=Decimal("42.0"),
                threshold=Decimal("35.0"),
                timestamp=now - timedelta(hours=1),
                is_read=False,
                recommended_actions=[
                    "Review outstanding invoices over 30 days",
                    "Implement automated payment reminders",
                    "Consider early payment discounts for large accounts",
                ],
            ),
            AlertItem(
                id=uuid4(),
                severity=PriorityLevel.HIGH,
                category=DecisionCategory.COST_REDUCTION,
                title="Cloud Infrastructure Costs Rising",
                summary="AWS/cloud spending up 18% month-over-month without corresponding revenue growth. Projected overspend of $45K this quarter.",
                metric_id=uuid4(),
                metric_name="Cloud Infrastructure Spend",
                value=Decimal("128000.00"),
                threshold=Decimal("108000.00"),
                timestamp=now - timedelta(hours=3),
                is_read=False,
                recommended_actions=[
                    "Audit unused resources and reserved instances",
                    "Implement auto-scaling policies",
                    "Review vendor contracts for optimization opportunities",
                ],
            ),
            AlertItem(
                id=uuid4(),
                severity=PriorityLevel.HIGH,
                category=DecisionCategory.REVENUE_GROWTH,
                title="MRR Growth Slowing",
                summary="Monthly Recurring Revenue growth has slowed to 3.2%, below the 5% quarterly target. Pipeline conversion rates declining.",
                metric_id=uuid4(),
                metric_name="MRR Growth Rate",
                value=Decimal("3.2"),
                threshold=Decimal("5.0"),
                timestamp=now - timedelta(hours=6),
                is_read=True,
                recommended_actions=[
                    "Review sales pipeline and conversion metrics",
                    "Assess competitive pricing and positioning",
                    "Consider promotional campaigns for new customer acquisition",
                ],
            ),
            AlertItem(
                id=uuid4(),
                severity=PriorityLevel.MEDIUM,
                category=DecisionCategory.OPERATIONAL,
                title="Employee Utilization Below Target",
                summary="Current team utilization at 82%, below the 85% target. Indicates potential bench time or inefficient resource allocation.",
                metric_id=uuid4(),
                metric_name="Employee Utilization",
                value=Decimal("82.0"),
                threshold=Decimal("85.0"),
                timestamp=now - timedelta(hours=8),
                is_read=False,
                recommended_actions=[
                    "Review project assignments and workload distribution",
                    "Identify training or upskilling opportunities",
                    "Consider cross-team resource sharing",
                ],
            ),
            AlertItem(
                id=uuid4(),
                severity=PriorityLevel.MEDIUM,
                category=DecisionCategory.RISK,
                title="Key Client Concentration Risk",
                summary="Top 3 clients represent 42% of total revenue. Industry best practice suggests keeping any single client below 15%.",
                metric_id=uuid4(),
                metric_name="Client Revenue Concentration",
                value=Decimal("42.0"),
                threshold=Decimal("30.0"),
                timestamp=now - timedelta(days=1),
                is_read=True,
                recommended_actions=[
                    "Accelerate diversification of client base",
                    "Develop retention strategies for key accounts",
                    "Monitor renewal dates and satisfaction scores",
                ],
            ),
            AlertItem(
                id=uuid4(),
                severity=PriorityLevel.LOW,
                category=DecisionCategory.OPERATIONAL,
                title="Gross Margin Slight Decline",
                summary="Gross margin at 68.5%, down 0.5% from previous quarter. Primarily driven by increased delivery costs.",
                metric_id=uuid4(),
                metric_name="Gross Margin",
                value=Decimal("68.5"),
                threshold=Decimal("70.0"),
                timestamp=now - timedelta(days=2),
                is_read=True,
                recommended_actions=[
                    "Review project profitability by engagement type",
                    "Assess subcontractor costs and renegotiate where possible",
                ],
            ),
        ]
        self._alerts[tenant_id] = alerts

    def _seed_decision_data(self, tenant_id: UUID) -> None:
        now = datetime.utcnow()
        decisions = [
            DecisionNeed(
                id=uuid4(),
                title="Q3 Technology Investment Plan",
                description="Evaluate and approve $500K investment in AI/ML platform capabilities to enhance product offerings and maintain competitive edge.",
                category=DecisionCategory.INVESTMENT,
                priority=PriorityLevel.CRITICAL,
                status="pending",
                impact_estimate={
                    "revenue_impact": 2000000,
                    "cost_impact": 500000,
                    "timeline_months": 9,
                    "roi_projected": 4.0,
                },
                deadline=now + timedelta(days=14),
                context={
                    "business_case": "Market analysis shows 35% demand growth for AI features",
                    "alternatives": ["Build in-house", "Acquire startup", "Partner with vendor"],
                    "risk_level": "medium",
                },
                created_at=now - timedelta(days=5),
            ),
            DecisionNeed(
                id=uuid4(),
                title="Vendor Consolidation Initiative",
                description="Consolidate SaaS tools from 47 to under 30 to reduce licensing costs and improve security posture.",
                category=DecisionCategory.COST_REDUCTION,
                priority=PriorityLevel.HIGH,
                status="in_review",
                impact_estimate={
                    "annual_savings": 180000,
                    "implementation_cost": 45000,
                    "timeline_months": 6,
                    "efficiency_gain": 0.15,
                },
                deadline=now + timedelta(days=30),
                context={
                    "current_tools": 47,
                    "target_tools": 30,
                    " departments_affected": ["engineering", "marketing", "finance", "hr"],
                },
                created_at=now - timedelta(days=10),
            ),
            DecisionNeed(
                id=uuid4(),
                title="Regional Expansion Strategy",
                description="Assess market entry for EMEA region with focus on DACH countries. Requires evaluation of regulatory, staffing, and go-to-market considerations.",
                category=DecisionCategory.STRATEGIC,
                priority=PriorityLevel.HIGH,
                status="pending",
                impact_estimate={
                    "projected_revenue_y1": 3000000,
                    "initial_investment": 1200000,
                    "breakeven_months": 18,
                    "market_size": 50000000,
                },
                deadline=now + timedelta(days=60),
                context={
                    "market_research": "Completed",
                    "regulatory_analysis": "In progress",
                    "competitor_landscape": "3 major players identified",
                },
                created_at=now - timedelta(days=15),
            ),
            DecisionNeed(
                id=uuid4(),
                title="Pricing Model Restructure",
                description="Evaluate transition from per-seat to usage-based pricing for enterprise tier. Impact on existing contracts and revenue recognition.",
                category=DecisionCategory.REVENUE_GROWTH,
                priority=PriorityLevel.MEDIUM,
                status="pending",
                impact_estimate={
                    "revenue_increase_projected": 800000,
                    "churn_risk": 0.08,
                    "transition_period_months": 6,
                    "customer_satisfaction_impact": "neutral_to_positive",
                },
                deadline=now + timedelta(days=45),
                context={
                    "customer_feedback": "68% prefer usage-based",
                    "competitive_analysis": "Industry moving toward hybrid models",
                },
                created_at=now - timedelta(days=7),
            ),
            DecisionNeed(
                id=uuid4(),
                title="Compliance Framework Update",
                description="Update SOC 2 and ISO 27001 compliance frameworks to meet new enterprise client requirements and regulatory standards.",
                category=DecisionCategory.RISK,
                priority=PriorityLevel.MEDIUM,
                status="in_progress",
                impact_estimate={
                    "compliance_cost": 85000,
                    "revenue_protection": 5000000,
                    "timeline_months": 4,
                    "audit_readiness": 0.75,
                },
                deadline=now + timedelta(days=90),
                context={
                    "current_certifications": ["SOC 2 Type I", "ISO 27001"],
                    "target_certifications": ["SOC 2 Type II", "ISO 27001:2022"],
                    "audit_firm": "Deloitte",
                },
                created_at=now - timedelta(days=20),
            ),
        ]
        self._decisions[tenant_id] = decisions

    def get_kpi_dashboard(self, tenant_id: UUID, time_range: str = "30d") -> List[KPIStatus]:
        self._ensure_seed_data(tenant_id)
        kpis = self._kpi_data.get(tenant_id, [])
        if time_range == "7d":
            return [k for k in kpis if k.is_real_time]
        return kpis

    def get_kpis(self, tenant_id: str, time_range: str = "30d") -> List[KPIStatus]:
        """Get KPI dashboard data. Delegates to get_kpi_dashboard for compatibility."""
        try:
            tid = UUID(tenant_id)
        except ValueError:
            return []
        return self.get_kpi_dashboard(tid, time_range)

    def get_active_alerts(
        self, tenant_id: UUID, severity_filter: Optional[PriorityLevel] = None, limit: int = 20
    ) -> List[AlertItem]:
        self._ensure_seed_data(tenant_id)
        alerts = self._alerts.get(tenant_id, [])
        if severity_filter:
            alerts = [a for a in alerts if a.severity == severity_filter]
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)[:limit]

    def get_alerts(
        self, tenant_id: str, severity: Optional[str] = None, limit: int = 20
    ) -> List[AlertItem]:
        """Get alerts. Converts severity string to PriorityLevel for compatibility."""
        try:
            tid = UUID(tenant_id)
        except ValueError:
            return []
        severity_filter = None
        if severity:
            try:
                severity_filter = PriorityLevel(severity.lower())
            except ValueError:
                pass
        return self.get_active_alerts(tid, severity_filter, limit)

    def mark_alert_read(self, tenant_id: UUID, alert_id: UUID) -> AlertItem:
        self._ensure_seed_data(tenant_id)
        for alert in self._alerts.get(tenant_id, []):
            if alert.id == alert_id:
                alert.is_read = True
                return alert
        raise ValueError(f"Alert {alert_id} not found for tenant {tenant_id}")

    def dismiss_alert(self, tenant_id: UUID, alert_id: UUID) -> AlertItem:
        self._ensure_seed_data(tenant_id)
        for i, alert in enumerate(self._alerts.get(tenant_id, [])):
            if alert.id == alert_id:
                self._alerts[tenant_id].pop(i)
                return alert
        raise ValueError(f"Alert {alert_id} not found for tenant {tenant_id}")

    def get_decision_needs(
        self, tenant_id: UUID, status_filter: Optional[str] = None
    ) -> List[DecisionNeed]:
        self._ensure_seed_data(tenant_id)
        decisions = self._decisions.get(tenant_id, [])
        if status_filter:
            decisions = [d for d in decisions if d.status == status_filter]
        return sorted(decisions, key=lambda d: (d.priority.value, d.deadline or datetime.max))

    def create_decision_need(
        self,
        tenant_id: UUID,
        title: str,
        description: str,
        category: DecisionCategory,
        priority: PriorityLevel,
        impact_estimate: Dict,
        deadline: Optional[datetime] = None,
        context: Optional[Dict] = None,
    ) -> DecisionNeed:
        self._ensure_seed_data(tenant_id)
        decision = DecisionNeed(
            id=uuid4(),
            title=title,
            description=description,
            category=category,
            priority=priority,
            status="pending",
            impact_estimate=impact_estimate,
            deadline=deadline,
            context=context or {},
            created_at=datetime.utcnow(),
        )
        self._decisions.setdefault(tenant_id, []).append(decision)
        return decision

    def update_decision_status(self, tenant_id: UUID, decision_id: UUID, status: str) -> DecisionNeed:
        self._ensure_seed_data(tenant_id)
        for decision in self._decisions.get(tenant_id, []):
            if decision.id == decision_id:
                decision.status = status
                return decision
        raise ValueError(f"Decision {decision_id} not found for tenant {tenant_id}")

    def get_performance_summary(self, tenant_id: UUID, time_range: str = "30d") -> PerformanceSummary:
        self._ensure_seed_data(tenant_id)
        kpis = self._kpi_data.get(tenant_id, [])

        healthy_count = sum(1 for k in kpis if k.status == HealthStatus.HEALTHY)
        total_count = len(kpis) if kpis else 1
        score = (healthy_count / total_count) * 100

        components = {}
        for kpi in kpis:
            components[kpi.name] = {
                "status": kpi.status.value,
                "value": float(kpi.value),
                "target": float(kpi.target),
                "compliance": float(kpi.value) / float(kpi.target) if float(kpi.target) > 0 else 0,
            }

        trend = "up" if score > 50 else "down"
        historical_scores = [
            {"date": (datetime.utcnow() - timedelta(days=i * 7)).isoformat(), "score": score + random.uniform(-5, 5)}
            for i in range(4, -1, -1)
        ]

        return PerformanceSummary(
            score=round(score, 1),
            components=components,
            trend=trend,
            historical_scores=historical_scores,
            data_quality=round(random.uniform(0.88, 0.96), 2),
            completeness=round(random.uniform(0.91, 0.98), 2),
        )

    def _calculate_revenue_forecast(
        self, base_revenue: Decimal, periods_ahead: int
    ) -> List[RevenueForecast]:
        alpha = 0.3
        forecasts = []
        current_value = float(base_revenue)
        historical_values = [current_value * (1 + random.uniform(-0.02, 0.04)) for _ in range(12)]

        smoothed = historical_values[0]
        for val in historical_values:
            smoothed = alpha * val + (1 - alpha) * smoothed

        std_dev = (sum((v - smoothed) ** 2 for v in historical_values) / len(historical_values)) ** 0.5

        now = datetime.utcnow()
        for i in range(1, periods_ahead + 1):
            period_date = now + timedelta(days=30 * i)
            period_str = period_date.strftime("%Y-%m")
            forecast_value = smoothed * ((1 + 0.03) ** i)
            margin = 1.96 * std_dev * math.sqrt(i)
            lower = Decimal(str(round(forecast_value - margin, 2)))
            upper = Decimal(str(round(forecast_value + margin, 2)))
            forecasted = Decimal(str(round(forecast_value, 2)))
            accuracy = round(1 - (std_dev / smoothed) * random.uniform(0.5, 1.5), 2)

            forecasts.append(
                RevenueForecast(
                    id=uuid4(),
                    period=period_str,
                    forecasted_revenue=forecasted,
                    confidence_interval=(lower, upper),
                    model_used="exponential_smoothing_alpha_0.3",
                    data_points=len(historical_values),
                    accuracy=min(accuracy, 0.99),
                    assumptions=[
                        "Historical growth trend continues",
                        "No major market disruptions",
                        "Current client retention rates maintained",
                        "Seasonal patterns consistent with prior years",
                    ],
                    created_at=now,
                )
            )
        return forecasts

    def _calculate_cost_forecast(
        self, base_cost: Decimal, periods_ahead: int
    ) -> List[CostForecast]:
        forecasts = []
        now = datetime.utcnow()
        categories = {
            "labor": 0.55,
            "supplies": 0.12,
            "overhead": 0.15,
            "equipment": 0.08,
            "it": 0.07,
            "other": 0.03,
        }

        for i in range(1, periods_ahead + 1):
            period_date = now + timedelta(days=30 * i)
            period_str = period_date.strftime("%Y-%m")
            growth_factor = 1 + (0.02 * i * 0.1)
            forecasted = base_cost * Decimal(str(growth_factor))

            breakdown = {cat: float(forecasted) * pct for cat, pct in categories.items()}

            drivers = [
                {"driver": "volume", "impact": round(random.uniform(-0.01, 0.03), 3), "description": "Client volume changes"},
                {"driver": "inflation", "impact": round(random.uniform(0.01, 0.03), 3), "description": "General inflation adjustment"},
                {"driver": "efficiency", "impact": round(random.uniform(-0.03, 0.01), 3), "description": "Operational efficiency gains"},
                {"driver": "utilization", "impact": round(random.uniform(-0.02, 0.02), 3), "description": "Resource utilization changes"},
            ]

            recommendations = []
            if breakdown["labor"] > float(forecasted) * 0.57:
                recommendations.append("Review staffing levels and consider automation for routine tasks")
            if breakdown["it"] > float(forecasted) * 0.08:
                recommendations.append("Evaluate cloud infrastructure costs and implement optimization")
            if breakdown["supplies"] > float(forecasted) * 0.13:
                recommendations.append("Negotiate volume discounts with key suppliers")
            if not recommendations:
                recommendations.append("Costs are within projected ranges; continue monitoring")

            confidence = round(random.uniform(0.75, 0.92), 2)

            forecasts.append(
                CostForecast(
                    id=uuid4(),
                    period=period_str,
                    forecasted_cost=round(forecasted, 2),
                    cost_breakdown=breakdown,
                    cost_drivers=drivers,
                    confidence=confidence,
                    recommendations=recommendations,
                    created_at=now,
                )
            )
        return forecasts

    def _calculate_risk_summary(self, tenant_id: UUID) -> RiskSummary:
        self._ensure_seed_data(tenant_id)
        alerts = self._alerts.get(tenant_id, [])
        decisions = self._decisions.get(tenant_id, [])

        risk_score = 0.0
        risks = []
        risk_categories = {
            "financial": 0.0,
            "operational": 0.0,
            "strategic": 0.0,
            "compliance": 0.0,
            "reputational": 0.0,
        }

        for alert in alerts:
            severity_weight = {
                PriorityLevel.CRITICAL: 1.0,
                PriorityLevel.HIGH: 0.7,
                PriorityLevel.MEDIUM: 0.4,
                PriorityLevel.LOW: 0.2,
            }
            weight = severity_weight.get(alert.severity, 0.3)
            risk_score += weight

            risk_entry = {
                "source": "alert",
                "title": alert.title,
                "severity": alert.severity.value,
                "category": alert.category.value,
                "score": weight,
            }
            risks.append(risk_entry)

            if alert.category == DecisionCategory.COST_REDUCTION:
                risk_categories["financial"] += weight
            elif alert.category == DecisionCategory.OPERATIONAL:
                risk_categories["operational"] += weight
            elif alert.category in (DecisionCategory.STRATEGIC, DecisionCategory.REVENUE_GROWTH):
                risk_categories["strategic"] += weight
            elif alert.category == DecisionCategory.RISK:
                risk_categories["compliance"] += weight

        for decision in decisions:
            if decision.status in ("pending", "in_review"):
                weight = {
                    PriorityLevel.CRITICAL: 0.8,
                    PriorityLevel.HIGH: 0.5,
                    PriorityLevel.MEDIUM: 0.3,
                    PriorityLevel.LOW: 0.1,
                }.get(decision.priority, 0.3)
                risk_score += weight * 0.5
                risks.append({
                    "source": "decision",
                    "title": decision.title,
                    "severity": decision.priority.value,
                    "category": decision.category.value,
                    "score": weight * 0.5,
                })

        max_category = max(risk_categories.values()) if risk_categories.values() else 0
        if risk_categories.values():
            risk_categories = {k: round(v, 2) for k, v in risk_categories.items()}

        normalized_score = min(risk_score / 5.0, 10.0)
        if normalized_score >= 7.0:
            risk_level = HealthStatus.CRITICAL
        elif normalized_score >= 4.0:
            risk_level = HealthStatus.WARNING
        else:
            risk_level = HealthStatus.HEALTHY

        mitigation_suggestions = []
        if risk_categories.get("financial", 0) > 1.0:
            mitigation_suggestions.append("Implement enhanced financial monitoring and early warning systems")
        if risk_categories.get("operational", 0) > 1.0:
            mitigation_suggestions.append("Review operational processes and implement automation where feasible")
        if risk_categories.get("strategic", 0) > 1.0:
            mitigation_suggestions.append("Conduct strategic review and adjust market positioning")
        if risk_categories.get("compliance", 0) > 0.5:
            mitigation_suggestions.append("Accelerate compliance certification timelines")
        mitigation_suggestions.append("Schedule weekly risk review meetings with leadership team")
        mitigation_suggestions.append("Update business continuity plan with current risk scenarios")

        return RiskSummary(
            id=uuid4(),
            overall_risk_score=round(normalized_score, 2),
            risk_level=risk_level,
            risks=sorted(risks, key=lambda r: r["score"], reverse=True)[:10],
            risk_categories=risk_categories,
            mitigation_suggestions=mitigation_suggestions[:5],
            created_at=datetime.utcnow(),
        )

    def get_revenue_forecast(self, tenant_id: UUID, periods_ahead: int = 6) -> List[RevenueForecast]:
        self._ensure_seed_data(tenant_id)
        kpis = self._kpi_data.get(tenant_id, [])
        mrr_kpi = next((k for k in kpis if k.name == "Monthly Recurring Revenue"), None)
        base_revenue = mrr_kpi.value if mrr_kpi else Decimal("2450000.00")
        return self._calculate_revenue_forecast(base_revenue, periods_ahead)

    def get_cost_forecast(self, tenant_id: UUID, periods_ahead: int = 6) -> List[CostForecast]:
        self._ensure_seed_data(tenant_id)
        base_cost = Decimal("1680000.00")
        return self._calculate_cost_forecast(base_cost, periods_ahead)

    def get_risk_summary(self, tenant_id: UUID) -> RiskSummary:
        return self._calculate_risk_summary(tenant_id)

    def generate_executive_briefing(
        self, tenant_id: UUID, period: str, period_type: str = "monthly"
    ) -> ExecutiveBriefing:
        self._ensure_seed_data(tenant_id)
        now = datetime.utcnow()

        kpis = self.get_kpi_dashboard(tenant_id, "30d")
        alerts = self.get_active_alerts(tenant_id, limit=20)
        decisions = self.get_decision_needs(tenant_id)
        revenue_forecasts = self.get_revenue_forecast(tenant_id, 3)
        cost_forecasts = self.get_cost_forecast(tenant_id, 3)
        risk_summary = self.get_risk_summary(tenant_id)

        sections = []

        kpi_rows = []
        for kpi in kpis:
            trend_arrow = "^" if kpi.trend == "up" else "v" if kpi.trend == "down" else "-"
            compliance = float(kpi.value) / float(kpi.target) if float(kpi.target) > 0 else 0
            kpi_rows.append({
                "name": kpi.name,
                "value": float(kpi.value),
                "target": float(kpi.target),
                "unit": kpi.unit,
                "status": kpi.status.value,
                "trend": f"{trend_arrow} {kpi.trend_percentage:+.1f}%",
                "compliance": round(compliance * 100, 1),
            })
        sections.append({
            "title": "KPI Overview",
            "content": "Current status of key performance indicators across financial, operational, and growth metrics.",
            "priority": "high",
            "kpis": kpi_rows,
            "alerts": [],
        })

        critical_high_alerts = [a for a in alerts if a.severity in (PriorityLevel.CRITICAL, PriorityLevel.HIGH)]
        alert_items = [
            {
                "title": a.title,
                "severity": a.severity.value,
                "summary": a.summary,
                "timestamp": a.timestamp.isoformat(),
                "recommended_actions": a.recommended_actions,
            }
            for a in critical_high_alerts
        ]
        sections.append({
            "title": "Active Alerts",
            "content": f"{len(critical_high_alerts)} critical/high severity items requiring attention.",
            "priority": "critical" if any(a.severity == PriorityLevel.CRITICAL for a in critical_high_alerts) else "high",
            "kpis": [],
            "alerts": alert_items,
        })

        pending_decisions = [d for d in decisions if d.status in ("pending", "in_review")]
        decision_items = [
            {
                "title": d.title,
                "category": d.category.value,
                "priority": d.priority.value,
                "status": d.status,
                "deadline": d.deadline.isoformat() if d.deadline else None,
                "impact_estimate": d.impact_estimate,
            }
            for d in pending_decisions
        ]
        sections.append({
            "title": "Decision Needs",
            "content": f"{len(pending_decisions)} items requiring executive attention.",
            "priority": "high" if any(d.priority == PriorityLevel.CRITICAL for d in pending_decisions) else "medium",
            "kpis": [],
            "alerts": decision_items,
        })

        financial_items = []
        if revenue_forecasts:
            rf = revenue_forecasts[0]
            financial_items.append({
                "metric": "Revenue Forecast",
                "value": float(rf.forecasted_revenue),
                "period": rf.period,
                "confidence": rf.accuracy,
                "range": [float(rf.confidence_interval[0]), float(rf.confidence_interval[1])],
            })
        if cost_forecasts:
            cf = cost_forecasts[0]
            financial_items.append({
                "metric": "Cost Forecast",
                "value": float(cf.forecasted_cost),
                "period": cf.period,
                "confidence": cf.confidence,
                "breakdown": cf.cost_breakdown,
            })
        sections.append({
            "title": "Financial Forecast",
            "content": "Revenue and cost projections for upcoming periods.",
            "priority": "medium",
            "kpis": financial_items,
            "alerts": [],
        })

        risk_items = [
            {
                "title": r["title"],
                "severity": r["severity"],
                "score": r["score"],
            }
            for r in risk_summary.risks[:5]
        ]
        sections.append({
            "title": "Risk Assessment",
            "content": f"Overall risk score: {risk_summary.overall_risk_score}/10. {len(risk_summary.risks)} risks identified.",
            "priority": risk_summary.risk_level.value,
            "kpis": [],
            "alerts": risk_items,
        })

        kpi_compliance_scores = []
        for kpi in kpis:
            compliance = float(kpi.value) / float(kpi.target) if float(kpi.target) > 0 else 1.0
            kpi_compliance_scores.append(min(compliance, 1.2))
        financial_score = (sum(kpi_compliance_scores) / len(kpi_compliance_scores) * 100) if kpi_compliance_scores else 75.0

        total_alerts = len(alerts)
        unread_critical = sum(1 for a in alerts if a.severity in (PriorityLevel.CRITICAL, PriorityLevel.HIGH) and not a.is_read)
        operational_score = max(0, 100 - (total_alerts * 5) - (unread_critical * 10))

        completed_decisions = sum(1 for d in decisions if d.status in ("completed", "approved"))
        total_decisions = len(decisions) if decisions else 1
        strategic_score = (completed_decisions / total_decisions) * 100

        critical_alerts = [a for a in alerts if a.severity == PriorityLevel.CRITICAL]
        warning_alerts = [a for a in alerts if a.severity == PriorityLevel.HIGH]
        if critical_alerts:
            overall_health = HealthStatus.CRITICAL
        elif warning_alerts:
            overall_health = HealthStatus.WARNING
        else:
            overall_health = HealthStatus.HEALTHY

        mrr_kpi = next((k for k in kpis if k.name == "Monthly Recurring Revenue"), None)
        dso_kpi = next((k for k in kpis if k.name == "Days Sales Outstanding"), None)
        narrative_parts = []
        if mrr_kpi:
            narrative_parts.append(
                f"Revenue stands at ${float(mrr_kpi.value):,.0f} against a target of ${float(mrr_kpi.target):,.0f}, "
                f"showing a {mrr_kpi.trend_percentage:+.1f}% {mrr_kpi.trend} trend."
            )
        if dso_kpi:
            narrative_parts.append(
                f"Accounts receivable processing requires attention with DSO at {float(dso_kpi.value):.0f} days "
                f"versus the {float(dso_kpi.target):.0f}-day target."
            )
        narrative_parts.append(
            f"The organization maintains {len([k for k in kpis if k.status == HealthStatus.HEALTHY])} of {len(kpis)} "
            f"KPIs within target ranges."
        )
        narrative = " ".join(narrative_parts)

        executive_summary = (
            f"Executive Summary for {period}: Overall organizational health is {overall_health.value}. "
            f"Financial performance score is {financial_score:.1f}%, operational score is {operational_score:.1f}%, "
            f"and strategic score is {strategic_score:.1f}%. "
            f"{len(critical_alerts)} critical and {len(warning_alerts)} high-priority alerts require immediate attention."
        )

        key_actions = []
        for alert in critical_high_alerts[:3]:
            if alert.recommended_actions:
                key_actions.append(alert.recommended_actions[0])
        urgent_decisions = sorted(
            [d for d in pending_decisions if d.deadline],
            key=lambda d: d.deadline,
        )
        for decision in urgent_decisions[:2]:
            key_actions.append(f"Review and decide on: {decision.title}")
        while len(key_actions) < 5:
            key_actions.append("Schedule leadership review meeting for outstanding items")
        key_actions = key_actions[:5]

        risks_list = [r["title"] for r in risk_summary.risks[:5]]

        return ExecutiveBriefing(
            id=uuid4(),
            period=period,
            period_type=period_type,
            generated_at=now,
            sections=sections,
            overall_health=overall_health,
            financial_score=round(financial_score, 1),
            operational_score=round(operational_score, 1),
            strategic_score=round(strategic_score, 1),
            narrative=narrative,
            executive_summary=executive_summary,
            key_actions=key_actions,
            risks=risks_list,
        )
