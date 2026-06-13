"""
Opportunity Discovery Engine.
Systematically discovers actionable opportunities with quantified value.
"""
import uuid
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from ..entities import (
    Opportunity,
    IntelligenceScores,
)
from app.domain.intelligence.value_objects import (
    OpportunityType,
    OpportunityCategory,
    OpportunityStatus,
    EffortLevel,
    RiskLevel,
    ValueBreakdown,
    ArtifactStatus,
    ArtifactType,
    GenerationSource,
    PeriodType,
    ScopeType,
)
from .scoring import IntelligenceScoreCalculator, ScoringContext


@dataclass
class OpportunityDiscoveryOptions:
    min_confidence: float = 0.70
    min_value: float = 1000
    max_opportunities: int = 50
    include_estimates: bool = True


@dataclass
class OpportunityData:
    metric_id: uuid.UUID
    metric_code: str
    current_value: float
    target_value: float
    benchmark_value: Optional[float] = None
    peer_average: Optional[float] = None
    historical_average: Optional[float] = None
    volume: float = 0
    category: str = "revenue"


class OpportunityDiscoveryEngine:
    """
    Systematically discovers actionable opportunities.
    """

    def __init__(self):
        self.score_calculator = IntelligenceScoreCalculator()

    async def discover_opportunities(
        self,
        tenant_id: uuid.UUID,
        opportunities_data: List[OpportunityData],
        scope: Optional[Dict[str, Any]] = None,
        options: OpportunityDiscoveryOptions = OpportunityDiscoveryOptions()
    ) -> List[Opportunity]:
        """
        Runs all opportunity discovery methods.
        Returns opportunities with quantified value estimates.
        """
        all_opportunities = []

        for data in opportunities_data:
            # Discover from benchmarking
            if data.benchmark_value is not None:
                opp = await self._discover_from_benchmarking(
                    tenant_id=tenant_id,
                    data=data,
                    scope=scope
                )
                if opp:
                    all_opportunities.append(opp)

            # Discover from target gap
            if data.target_value > data.current_value:
                opp = await self._discover_from_target_gap(
                    tenant_id=tenant_id,
                    data=data,
                    scope=scope
                )
                if opp:
                    all_opportunities.append(opp)

            # Discover from peer comparison
            if data.peer_average is not None:
                opp = await self._discover_from_peer_comparison(
                    tenant_id=tenant_id,
                    data=data,
                    scope=scope
                )
                if opp:
                    all_opportunities.append(opp)

        # Rank opportunities
        ranked_opportunities = await self.rank_opportunities(all_opportunities)

        # Filter by minimum value
        filtered = [
            o for o in ranked_opportunities
            if o.estimated_value >= options.min_value
        ]

        # Limit number
        filtered = filtered[:options.max_opportunities]

        return filtered

    async def discover_from_root_causes(
        self,
        tenant_id: uuid.UUID,
        root_cause_id: uuid.UUID,
        root_cause_data: Dict[str, Any],
        scope: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        """
        Given a root cause, generate actionable opportunities.
        """
        opportunities = []

        # Extract data from root cause
        metric_code = root_cause_data.get("metric_code", "")
        change_percent = root_cause_data.get("change_percent", 0)
        attribution_absolute = root_cause_data.get("attribution_absolute", 0)
        cause_category = root_cause_data.get("cause_category", "")

        # Generate opportunity based on cause type
        if change_percent < -5:  # Significant decline
            # Recovery opportunity
            recovery_value = abs(attribution_absolute)
            opportunity = Opportunity(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                artifact_type=ArtifactType.OPPORTUNITY,
                opportunity_type=OpportunityType.REVENUE_GROWTH,
                category=OpportunityCategory.REVENUE,
                title=f"Recover {metric_code} decline of ${abs(attribution_absolute):,.0f}",
                summary=f"Address the root cause of {metric_code} decline to recover lost value",
                detailed_description=(
                    f"Root cause analysis identified a decline in {metric_code} of "
                    f"{abs(change_percent):.1f}%. The primary cause contributed "
                    f"${abs(attribution_absolute):,.0f} to this decline. "
                    f"By addressing this root cause, we can potentially recover this value."
                ),
                estimated_value=recovery_value,
                value_unit="annual",
                value_confidence=0.7,
                baseline_value=root_cause_data.get("previous_value", 0),
                target_value=root_cause_data.get("current_value", 0) + abs(attribution_absolute),
                improvement_potential=abs(attribution_absolute),
                effort_level=EffortLevel.MEDIUM,
                risk_level=RiskLevel.MEDIUM,
                time_to_realize_months=6,
                roi=abs(attribution_absolute) / 10000 if 10000 > 0 else 0,  # Simplified
                recommended_actions=[
                    "Investigate root cause in detail",
                    "Develop remediation plan",
                    "Implement corrective actions",
                    "Monitor recovery metrics",
                ],
                success_criteria=[
                    f"{metric_code} returns to previous level",
                    "Root cause is addressed",
                ],
                failure_risks=[
                    "Root cause may be complex",
                    "External factors may limit recovery",
                ],
                discovery_method="root_cause_analysis",
                source_opportunity_id=root_cause_id,
                related_metric_ids=[root_cause_data.get("metric_id")],
                scope_type=ScopeType.TENANT,
                scope_id=scope.get("scope_id") if scope else None,
                status=ArtifactStatus.DISCOVERED,
                version=1,
            )

            # Calculate scores
            scoring_context = ScoringContext(
                tenant_id=tenant_id,
                artifact_type=ArtifactType.OPPORTUNITY,
                artifact_data={
                    "dollar_impact": recovery_value,
                    "severity": "high" if abs(change_percent) > 10 else "medium",
                    "confidence": 0.7,
                    "time_to_impact_days": 180,
                    "sample_size": 1,
                }
            )
            scores = await self.score_calculator.calculate_scores(
                ArtifactType.OPPORTUNITY,
                scoring_context.artifact_data,
                scoring_context
            )
            opportunity.scores = scores

            opportunities.append(opportunity)

        return opportunities

    async def discover_from_benchmarking(
        self,
        tenant_id: uuid.UUID,
        metrics_data: List[Dict[str, Any]],
        scope: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        """
        Compare metrics against internal/external benchmarks.
        Generate opportunities to close the gap.
        """
        opportunities = []

        for data in metrics_data:
            current = data.get("current_value", 0)
            benchmark = data.get("benchmark_value")

            if benchmark is None or benchmark <= 0:
                continue

            # Calculate gap
            gap = benchmark - current
            if gap <= 0:
                continue  # Already meeting/exceeding benchmark

            # Calculate value of closing gap
            volume = data.get("volume", 1)
            value_per_unit = data.get("value_per_unit", 1)
            estimated_value = gap * volume * value_per_unit

            opportunity = Opportunity(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                artifact_type=ArtifactType.OPPORTUNITY,
                opportunity_type=OpportunityType.REVENUE_GROWTH,
                category=OpportunityCategory.REVENUE,
                title=f"Improve {data.get('metric_code', 'metric')} to benchmark level",
                summary=f"Current value is {current:,.2f}, benchmark is {benchmark:,.2f}",
                detailed_description=(
                    f"The metric {data.get('metric_code', 'metric')} is currently "
                    f"performing below benchmark. Current: {current:,.2f}, "
                    f"Benchmark: {benchmark:,.2f}. Closing this gap represents an "
                    f"opportunity to improve by {gap:,.2f}."
                ),
                estimated_value=estimated_value,
                value_unit="annual",
                value_confidence=0.6,
                baseline_value=current,
                target_value=benchmark,
                improvement_potential=gap,
                effort_level=EffortLevel.MEDIUM,
                risk_level=RiskLevel.MEDIUM,
                time_to_realize_months=12,
                recommended_actions=[
                    "Analyze gap drivers",
                    "Develop improvement plan",
                    "Implement changes",
                    "Monitor progress",
                ],
                discovery_method="benchmarking",
                related_metric_ids=[data.get("metric_id")],
                scope_type=ScopeType.TENANT,
                scope_id=scope.get("scope_id") if scope else None,
                status=ArtifactStatus.DISCOVERED,
                version=1,
            )

            # Calculate scores
            scoring_context = ScoringContext(
                tenant_id=tenant_id,
                artifact_type=ArtifactType.OPPORTUNITY,
                artifact_data={
                    "dollar_impact": estimated_value,
                    "severity": "medium",
                    "confidence": 0.6,
                    "time_to_impact_days": 365,
                }
            )
            scores = await self.score_calculator.calculate_scores(
                ArtifactType.OPPORTUNITY,
                scoring_context.artifact_data,
                scoring_context
            )
            opportunity.scores = scores

            opportunities.append(opportunity)

        return opportunities

    async def _discover_from_benchmarking(
        self,
        tenant_id: uuid.UUID,
        data: OpportunityData,
        scope: Optional[Dict[str, Any]] = None
    ) -> Optional[Opportunity]:
        """
        Discover opportunity from benchmark comparison.
        """
        if data.benchmark_value is None or data.benchmark_value <= 0:
            return None

        gap = data.benchmark_value - data.current_value
        if gap <= 0:
            return None

        estimated_value = gap * data.volume

        opportunity = Opportunity(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            artifact_type=ArtifactType.OPPORTUNITY,
            opportunity_type=OpportunityType.REVENUE_GROWTH,
            category=OpportunityCategory.REVENUE,
            title=f"Improve {data.metric_code} to benchmark level",
            summary=f"Current: {data.current_value:,.2f}, Benchmark: {data.benchmark_value:,.2f}",
            detailed_description=(
                f"Gap to benchmark: {gap:,.2f}. Estimated value: ${estimated_value:,.0f}"
            ),
            estimated_value=estimated_value,
            value_unit="annual",
            value_confidence=0.6,
            baseline_value=data.current_value,
            target_value=data.benchmark_value,
            improvement_potential=gap,
            effort_level=EffortLevel.MEDIUM,
            risk_level=RiskLevel.MEDIUM,
            time_to_realize_months=12,
            recommended_actions=[
                "Analyze gap drivers",
                "Develop improvement plan",
                "Implement changes",
            ],
            discovery_method="benchmarking",
            related_metric_ids=[data.metric_id],
            scope_type=ScopeType.TENANT,
            scope_id=scope.get("scope_id") if scope else None,
            status=ArtifactStatus.DISCOVERED,
            version=1,
        )

        # Calculate scores
        scoring_context = ScoringContext(
            tenant_id=tenant_id,
            artifact_type=ArtifactType.OPPORTUNITY,
            artifact_data={
                "dollar_impact": estimated_value,
                "severity": "medium",
                "confidence": 0.6,
                "time_to_impact_days": 365,
            }
        )
        scores = await self.score_calculator.calculate_scores(
            ArtifactType.OPPORTUNITY,
            scoring_context.artifact_data,
            scoring_context
        )
        opportunity.scores = scores

        return opportunity

    async def _discover_from_target_gap(
        self,
        tenant_id: uuid.UUID,
        data: OpportunityData,
        scope: Optional[Dict[str, Any]] = None
    ) -> Optional[Opportunity]:
        """
        Discover opportunity from target gap.
        """
        gap = data.target_value - data.current_value
        if gap <= 0:
            return None

        estimated_value = gap * data.volume

        opportunity = Opportunity(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            artifact_type=ArtifactType.OPPORTUNITY,
            opportunity_type=OpportunityType.REVENUE_GROWTH,
            category=OpportunityCategory.REVENUE,
            title=f"Achieve target for {data.metric_code}",
            summary=f"Gap to target: {gap:,.2f}",
            detailed_description=(
                f"Current: {data.current_value:,.2f}, Target: {data.target_value:,.2f}. "
                f"Achieving the target represents an improvement of {gap:,.2f}."
            ),
            estimated_value=estimated_value,
            value_unit="annual",
            value_confidence=0.7,
            baseline_value=data.current_value,
            target_value=data.target_value,
            improvement_potential=gap,
            effort_level=EffortLevel.MEDIUM,
            risk_level=RiskLevel.LOW,
            time_to_realize_months=6,
            recommended_actions=[
                "Review current performance drivers",
                "Identify improvement levers",
                "Implement targeted actions",
            ],
            discovery_method="target_comparison",
            related_metric_ids=[data.metric_id],
            scope_type=ScopeType.TENANT,
            scope_id=scope.get("scope_id") if scope else None,
            status=ArtifactStatus.DISCOVERED,
            version=1,
        )

        # Calculate scores
        scoring_context = ScoringContext(
            tenant_id=tenant_id,
            artifact_type=ArtifactType.OPPORTUNITY,
            artifact_data={
                "dollar_impact": estimated_value,
                "severity": "medium",
                "confidence": 0.7,
                "time_to_impact_days": 180,
            }
        )
        scores = await self.score_calculator.calculate_scores(
            ArtifactType.OPPORTUNITY,
            scoring_context.artifact_data,
            scoring_context
        )
        opportunity.scores = scores

        return opportunity

    async def _discover_from_peer_comparison(
        self,
        tenant_id: uuid.UUID,
        data: OpportunityData,
        scope: Optional[Dict[str, Any]] = None
    ) -> Optional[Opportunity]:
        """
        Discover opportunity from peer comparison.
        """
        if data.peer_average is None or data.peer_average <= 0:
            return None

        gap = data.peer_average - data.current_value
        if gap <= 0:
            return None

        estimated_value = gap * data.volume * 0.5  # Conservative estimate

        opportunity = Opportunity(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            artifact_type=ArtifactType.OPPORTUNITY,
            opportunity_type=OpportunityType.REVENUE_GROWTH,
            category=OpportunityCategory.REVENUE,
            title=f"Improve {data.metric_code} to peer average",
            summary=f"Current: {data.current_value:,.2f}, Peer Average: {data.peer_average:,.2f}",
            detailed_description=(
                f"Gap to peer average: {gap:,.2f}. Estimated value: ${estimated_value:,.0f}"
            ),
            estimated_value=estimated_value,
            value_unit="annual",
            value_confidence=0.5,
            baseline_value=data.current_value,
            target_value=data.peer_average,
            improvement_potential=gap,
            effort_level=EffortLevel.MEDIUM,
            risk_level=RiskLevel.MEDIUM,
            time_to_realize_months=12,
            recommended_actions=[
                "Analyze peer best practices",
                "Adapt successful strategies",
                "Monitor improvement",
            ],
            discovery_method="peer_comparison",
            related_metric_ids=[data.metric_id],
            scope_type=ScopeType.TENANT,
            scope_id=scope.get("scope_id") if scope else None,
            status=ArtifactStatus.DISCOVERED,
            version=1,
        )

        # Calculate scores
        scoring_context = ScoringContext(
            tenant_id=tenant_id,
            artifact_type=ArtifactType.OPPORTUNITY,
            artifact_data={
                "dollar_impact": estimated_value,
                "severity": "low",
                "confidence": 0.5,
                "time_to_impact_days": 365,
            }
        )
        scores = await self.score_calculator.calculate_scores(
            ArtifactType.OPPORTUNITY,
            scoring_context.artifact_data,
            scoring_context
        )
        opportunity.scores = scores

        return opportunity

    async def rank_opportunities(
        self,
        opportunities: List[Opportunity]
    ) -> List[Opportunity]:
        """
        Rank opportunities by composite score.
        Score = f(value, roi, confidence, urgency, feasibility)
        """
        def ranking_score(opp: Opportunity) -> float:
            if not opp.scores:
                return 0
            # Weighted combination
            return (
                opp.scores.priority * 0.4 +
                opp.scores.impact * 0.3 +
                opp.scores.confidence * 0.2 +
                opp.scores.urgency * 0.1
            )

        ranked = sorted(opportunities, key=ranking_score, reverse=True)
        return ranked
