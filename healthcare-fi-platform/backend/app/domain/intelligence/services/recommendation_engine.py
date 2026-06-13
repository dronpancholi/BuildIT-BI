"""
Recommendation Engine.
Generates actionable, evidence-backed recommendations from intelligence artifacts.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..entities import (
    Recommendation,
    ActionStep,
    EvidenceItem,
    IntelligenceScores,
)
from app.domain.intelligence.value_objects import (
    RecommendationType,
    RecommendationStatus,
    ImpactDirection,
    ArtifactStatus,
    ArtifactType,
    GenerationSource,
    PeriodType,
    ScopeType,
)
from .scoring import IntelligenceScoreCalculator, ScoringContext


@dataclass
class RecommendationGenerationOptions:
    max_recommendations: int = 20
    min_confidence: float = 0.60
    include_evidence_chain: bool = True


class RecommendationEngine:
    """
    Generates actionable recommendations from intelligence artifacts.
    """

    def __init__(self):
        self.score_calculator = IntelligenceScoreCalculator()

    async def generate_recommendations_from_insight(
        self,
        tenant_id: uuid.UUID,
        insight_data: Dict[str, Any],
        scope: Optional[Dict[str, Any]] = None,
        options: RecommendationGenerationOptions = RecommendationGenerationOptions()
    ) -> List[Recommendation]:
        """
        Given an insight, generate actionable recommendations.
        """
        recommendations = []

        insight_type = insight_data.get("insight_type", "")
        change_percent = insight_data.get("change_percent", 0)
        metric_code = insight_data.get("metric_code", "")
        metric_id = insight_data.get("metric_id")

        # Map insight types to recommendation types
        recommendation_templates = {
            "revenue_decline": [
                {
                    "type": RecommendationType.REVENUE_OPTIMIZATION,
                    "title": f"Investigate and address {metric_code} decline",
                    "actions": [
                        "Analyze root cause of revenue decline",
                        "Review department-level contribution",
                        "Assess payer mix changes",
                        "Evaluate pricing and contract impacts",
                    ],
                },
            ],
            "margin_decline": [
                {
                    "type": RecommendationType.COST_REDUCTION,
                    "title": f"Address margin pressure in {metric_code}",
                    "actions": [
                        "Identify cost reduction opportunities",
                        "Review operational efficiency",
                        "Analyze labor and supply costs",
                        "Evaluate process improvements",
                    ],
                },
            ],
            "claims_approval_decline": [
                {
                    "type": RecommendationType.CLAIMS_OPTIMIZATION,
                    "title": "Improve claim approval rate",
                    "actions": [
                        "Review top denial reasons",
                        "Update charge capture processes",
                        "Enhance documentation",
                        "Engage payer relations team",
                    ],
                },
            ],
            "segment_underperformance": [
                {
                    "type": RecommendationType.REVENUE_OPTIMIZATION,
                    "title": f"Address underperformance in {metric_code}",
                    "actions": [
                        "Analyze segment-specific drivers",
                        "Identify improvement opportunities",
                        "Develop targeted action plan",
                        "Monitor segment performance",
                    ],
                },
            ],
        }

        # Get templates for this insight type
        templates = recommendation_templates.get(insight_type, [])

        for template in templates:
            # Calculate expected impact
            expected_impact = abs(change_percent) / 100 * insight_data.get("current_value", 0)

            # Create recommendation
            recommendation = Recommendation(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                artifact_type=ArtifactType.RECOMMENDATION,
                recommendation_type=template["type"],
                category="FINANCIAL",
                title=template["title"],
                summary=f"Based on insight: {insight_data.get('title', '')}",
                detailed_recommendation=(
                    f"Analysis reveals {change_percent:+.1f}% change in {metric_code}. "
                    f"The following actions are recommended to address this finding."
                ),
                expected_impact_value=expected_impact,
                expected_impact_unit="annual",
                impact_direction=ImpactDirection.INCREASE_REVENUE if change_percent < 0 else ImpactDirection.REDUCE_COST,
                confidence_in_impact=0.7,
                impact_calculation=f"Based on {abs(change_percent):.1f}% recovery of current value",
                recommended_actions=[
                    ActionStep(
                        step_number=i + 1,
                        action_description=action,
                        estimated_effort_hours=8,
                        success_criteria="Completed",
                    )
                    for i, action in enumerate(template["actions"])
                ],
                estimated_effort_hours=32,
                time_to_implement_months=3,
                success_metrics=[
                    f"{metric_code} returns to previous level",
                    "Root cause is addressed",
                ],
                failure_risks=[
                    "Root cause may be complex",
                    "External factors may limit improvement",
                ],
                generation_method="rule_based",
                supporting_insight_ids=[insight_data.get("id")],
                scope_type=ScopeType.TENANT,
                scope_id=scope.get("scope_id") if scope else None,
                status=ArtifactStatus.DISCOVERED,
                version=1,
            )

            # Calculate scores
            scoring_context = ScoringContext(
                tenant_id=tenant_id,
                artifact_type=ArtifactType.RECOMMENDATION,
                artifact_data={
                    "dollar_impact": expected_impact,
                    "severity": "high" if abs(change_percent) > 10 else "medium",
                    "confidence": 0.7,
                    "time_to_impact_days": 90,
                    "sample_size": 1,
                }
            )
            scores = await self.score_calculator.calculate_scores(
                ArtifactType.RECOMMENDATION,
                scoring_context.artifact_data,
                scoring_context
            )
            recommendation.scores = scores

            recommendations.append(recommendation)

        return recommendations

    async def generate_recommendations_from_anomaly(
        self,
        tenant_id: uuid.UUID,
        anomaly_data: Dict[str, Any],
        scope: Optional[Dict[str, Any]] = None
    ) -> List[Recommendation]:
        """
        Given an anomaly, generate actionable recommendations.
        """
        recommendations = []

        anomaly_type = anomaly_data.get("anomaly_type", "")
        severity = anomaly_data.get("severity", "medium")
        metric_code = anomaly_data.get("metric_code", "")
        deviation_percent = anomaly_data.get("deviation_percent", 0)

        # Generate recommendation based on anomaly type
        if anomaly_type in ["drop", "spike"] and severity in ["critical", "high"]:
            expected_impact = abs(deviation_percent) / 100 * anomaly_data.get("current_value", 0)

            recommendation = Recommendation(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                artifact_type=ArtifactType.RECOMMENDATION,
                recommendation_type=RecommendationType.REVENUE_OPTIMIZATION,
                category="OPERATIONAL",
                title=f"Investigate {anomaly_type} in {metric_code}",
                summary=f"Anomaly detected: {deviation_percent:+.1f}% deviation",
                detailed_recommendation=(
                    f"A {severity} anomaly was detected in {metric_code} with a "
                    f"{deviation_percent:+.1f}% deviation from expected. "
                    f"Investigation is recommended to identify root cause and implement corrective actions."
                ),
                expected_impact_value=expected_impact,
                expected_impact_unit="one_time",
                impact_direction=ImpactDirection.REDUCE_RISK,
                confidence_in_impact=0.6,
                recommended_actions=[
                    ActionStep(
                        step_number=1,
                        action_description="Investigate anomaly root cause",
                        estimated_effort_hours=4,
                        success_criteria="Root cause identified",
                    ),
                    ActionStep(
                        step_number=2,
                        action_description="Implement corrective actions",
                        estimated_effort_hours=8,
                        success_criteria="Actions implemented",
                    ),
                ],
                estimated_effort_hours=12,
                time_to_implement_months=1,
                generation_method="rule_based",
                supporting_anomaly_ids=[anomaly_data.get("id")],
                scope_type=ScopeType.TENANT,
                scope_id=scope.get("scope_id") if scope else None,
                status=ArtifactStatus.DISCOVERED,
                version=1,
            )

            # Calculate scores
            scoring_context = ScoringContext(
                tenant_id=tenant_id,
                artifact_type=ArtifactType.RECOMMENDATION,
                artifact_data={
                    "dollar_impact": expected_impact,
                    "severity": severity,
                    "confidence": 0.6,
                    "time_to_impact_days": 30,
                }
            )
            scores = await self.score_calculator.calculate_scores(
                ArtifactType.RECOMMENDATION,
                scoring_context.artifact_data,
                scoring_context
            )
            recommendation.scores = scores

            recommendations.append(recommendation)

        return recommendations

    async def generate_recommendations_from_opportunity(
        self,
        tenant_id: uuid.UUID,
        opportunity_data: Dict[str, Any],
        scope: Optional[Dict[str, Any]] = None
    ) -> List[Recommendation]:
        """
        Given an opportunity, generate actionable recommendations.
        """
        recommendations = []

        opportunity_type = opportunity_data.get("opportunity_type", "")
        estimated_value = opportunity_data.get("estimated_value", 0)
        title = opportunity_data.get("title", "")
        metric_code = opportunity_data.get("metric_code", "")

        # Generate recommendation based on opportunity type
        recommendation = Recommendation(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            artifact_type=ArtifactType.RECOMMENDATION,
            recommendation_type=RecommendationType.REVENUE_OPTIMIZATION,
            category="FINANCIAL",
            title=f"Realize opportunity: {title}",
            summary=f"Estimated value: ${estimated_value:,.0f}",
            detailed_recommendation=(
                f"An opportunity has been identified with an estimated value of "
                f"${estimated_value:,.0f}. The following actions are recommended to "
                f"realize this value."
            ),
            expected_impact_value=estimated_value,
            expected_impact_unit="annual",
            impact_direction=ImpactDirection.INCREASE_REVENUE,
            confidence_in_impact=opportunity_data.get("value_confidence", 0.6),
            recommended_actions=[
                ActionStep(
                    step_number=1,
                    action_description="Validate opportunity assumptions",
                    estimated_effort_hours=4,
                    success_criteria="Assumptions validated",
                ),
                ActionStep(
                    step_number=2,
                    action_description="Develop implementation plan",
                    estimated_effort_hours=8,
                    success_criteria="Plan approved",
                ),
                ActionStep(
                    step_number=3,
                    action_description="Execute implementation",
                    estimated_effort_hours=40,
                    success_criteria="Implementation complete",
                ),
            ],
            estimated_effort_hours=52,
            time_to_implement_months=6,
            generation_method="rule_based",
            supporting_opportunity_ids=[opportunity_data.get("id")],
            scope_type=ScopeType.TENANT,
            scope_id=scope.get("scope_id") if scope else None,
            status=ArtifactStatus.DISCOVERED,
            version=1,
        )

        # Calculate scores
        scoring_context = ScoringContext(
            tenant_id=tenant_id,
            artifact_type=ArtifactType.RECOMMENDATION,
            artifact_data={
                "dollar_impact": estimated_value,
                "severity": "high" if estimated_value > 100000 else "medium",
                "confidence": opportunity_data.get("value_confidence", 0.6),
                "time_to_impact_days": 180,
            }
        )
        scores = await self.score_calculator.calculate_scores(
            ArtifactType.RECOMMENDATION,
            scoring_context.artifact_data,
            scoring_context
        )
        recommendation.scores = scores

        recommendations.append(recommendation)

        return recommendations

    async def rank_recommendations(
        self,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """
        Rank recommendations by priority score.
        """
        ranked = sorted(
            recommendations,
            key=lambda r: r.scores.priority if r.scores else 0,
            reverse=True
        )
        return ranked
