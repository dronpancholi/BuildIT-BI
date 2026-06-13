"""
Narrative Generation Engine.
Transforms structured data into executive-quality prose.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from string import Template

from ..entities import (
    Insight,
    RootCause,
    Anomaly,
    Opportunity,
    Recommendation,
    IntelligenceScores,
)
from app.domain.intelligence.value_objects import (
    InsightType,
    AnomalySeverity,
    ArtifactType,
    NarrativeTone,
    SentimentLabel,
)


@dataclass
class NarrativeContext:
    metric_name: str
    metric_code: str
    current_value: float
    previous_value: Optional[float] = None
    target_value: Optional[float] = None
    unit: str = "USD"
    period_description: str = ""
    comparison_change_percent: Optional[float] = None
    root_cause_description: Optional[str] = None
    scope_name: Optional[str] = None


class NarrativeEngine:
    """
    Transforms structured data into executive-quality prose.
    """

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Template]:
        """
        Load narrative templates.
        """
        return {
            "revenue_increase": Template(
                """$subject $verb $change to $value, $context.
                $contribution_statement.
                $outlook_statement"""
            ),
            "revenue_decrease": Template(
                """$subject $verb $change to $value, $context.
                $contribution_statement.
                $outlook_statement"""
            ),
            "anomaly_detected": Template(
                """An anomaly was detected in $metric_name: $observed_value was significantly $direction
                $expected_direction the expected range of $expected_range.
                The $deviation_percent deviation from expected has a $confidence% confidence level.
                $root_cause_statement.
                $business_impact_statement.
                $recommended_action_statement"""
            ),
            "briefing_executive_summary": Template(
                """$period_label performance showed $overall_sentiment results.
                $win_summary.
                $risk_summary.
                $action_summary"""
            ),
        }

    async def generate_metric_narrative(
        self,
        context: NarrativeContext,
        change_percent: Optional[float] = None,
        target_variance: Optional[float] = None,
    ) -> str:
        """
        Generate narrative for a single metric.
        """
        if change_percent is None and context.previous_value:
            change_percent = (
                (context.current_value - context.previous_value) /
                context.previous_value * 100
            )

        # Determine verb and direction
        if change_percent is not None:
            if change_percent > 0:
                verb = "increased"
                direction = "up"
            elif change_percent < 0:
                verb = "decreased"
                direction = "down"
            else:
                verb = "remained stable"
                direction = "unchanged"
        else:
            verb = "is"
            direction = "at"

        # Format change
        if change_percent is not None:
            change_str = f"{abs(change_percent):.1f}%"
        else:
            change_str = ""

        # Format value
        value_str = self._format_value(context.current_value, context.unit)

        # Context statement
        context_stmt = "compared to the prior period"
        if context.previous_value:
            prev_str = self._format_value(context.previous_value, context.unit)
            context_stmt = f"from {prev_str}"

        # Target comparison
        target_stmt = ""
        if target_variance is not None:
            if target_variance > 0:
                target_stmt = f"outperforming the target by {abs(target_variance):.1f}%"
            elif target_variance < 0:
                target_stmt = f"{abs(target_variance):.1f}% below target"

        # Build narrative
        narrative = f"{context.metric_name} {verb} {change_str} {direction} to {value_str}, {context_stmt}."
        if target_stmt:
            narrative += f" {target_stmt}."

        return narrative

    async def generate_insight_narrative(
        self,
        insight: Insight,
        context: Optional[NarrativeContext] = None,
    ) -> str:
        """
        Generate narrative explaining a discovered insight.
        """
        if context is None:
            context = NarrativeContext(
                metric_name=insight.metric_code or "Metric",
                metric_code=insight.metric_code or "",
                current_value=insight.magnitude,
            )

        # Generate based on insight type
        if insight.insight_type == InsightType.REVENUE_GROWTH:
            return await self._generate_growth_narrative(insight, context)
        elif insight.insight_type == InsightType.REVENUE_DECLINE:
            return await self._generate_decline_narrative(insight, context)
        elif insight.insight_type == InsightType.SUSTAINED_TREND:
            return await self._generate_trend_narrative(insight, context)
        elif insight.insight_type == InsightType.TREND_REVERSAL:
            return await self._generate_reversal_narrative(insight, context)
        elif insight.insight_type == InsightType.SEGMENT_OUTPERFORMANCE:
            return await self._generate_segment_narrative(insight, context)
        else:
            return await self._generate_generic_insight_narrative(insight, context)

    async def generate_anomaly_narrative(
        self,
        anomaly: Anomaly,
        context: Optional[NarrativeContext] = None,
    ) -> str:
        """
        Generate narrative explaining an anomaly.
        """
        if context is None:
            context = NarrativeContext(
                metric_name=anomaly.metric_code or "Metric",
                metric_code=anomaly.metric_code or "",
                current_value=anomaly.observed_value,
            )

        direction = "above" if anomaly.observed_value > anomaly.expected_value else "below"
        expected_range = f"${anomaly.expected_value:,.0f}"

        narrative = (
            f"An anomaly was detected in {context.metric_name}: "
            f"the observed value of ${anomaly.observed_value:,.0f} was significantly {direction} "
            f"the expected range of {expected_range}. "
            f"The {abs(anomaly.deviation_percent):.1f}% deviation from expected has a "
            f"{anomaly.confidence if anomaly.scores else 0:.0%} confidence level."
        )

        if anomaly.root_cause_description:
            narrative += f" Root cause analysis identified: {anomaly.root_cause_description}."

        if anomaly.business_impact:
            narrative += (
                f" This represents approximately ${abs(anomaly.business_impact.impact_amount or 0):,.0f} "
                f"in {anomaly.business_impact.impact_type}."
            )

        return narrative

    async def generate_comparison_narrative(
        self,
        current: float,
        previous: float,
        target: Optional[float],
        metric_name: str,
        unit: str = "USD",
    ) -> str:
        """
        Generate a comparison statement.
        """
        change_percent = ((current - previous) / previous * 100) if previous else 0

        current_str = self._format_value(current, unit)
        previous_str = self._format_value(previous, unit)

        if change_percent > 0:
            verb = "increased"
        elif change_percent < 0:
            verb = "decreased"
        else:
            verb = "remained stable"

        narrative = (
            f"{metric_name} {verb} from {previous_str} to {current_str} "
            f"({change_percent:+.1f}%)."
        )

        if target:
            target_str = self._format_value(target, unit)
            variance = ((current - target) / target * 100) if target else 0
            if variance > 0:
                narrative += f" This is {abs(variance):.1f}% above the target of {target_str}."
            elif variance < 0:
                narrative += f" This is {abs(variance):.1f}% below the target of {target_str}."

        return narrative

    async def synthesize_briefing_narrative(
        self,
        sections: List[Dict[str, Any]],
        tone: NarrativeTone = NarrativeTone.EXECUTIVE,
    ) -> str:
        """
        Synthesize briefing sections into coherent narrative.
        """
        narrative_parts = []

        for section in sections:
            if section.get("content"):
                narrative_parts.append(f"**{section.get('title', '')}**\n{section['content']}")

        return "\n\n".join(narrative_parts)

    async def _generate_growth_narrative(
        self,
        insight: Insight,
        context: NarrativeContext,
    ) -> str:
        """
        Generate narrative for growth insight.
        """
        change_str = f"{abs(insight.relative_magnitude * 100):.1f}%"
        value_str = self._format_value(insight.magnitude, context.unit)

        narrative = (
            f"{context.metric_name} showed strong growth of {change_str}, "
            f"contributing {value_str} to overall performance. "
            f"This represents a {insight.pattern_detected.direction if insight.pattern_detected else 'positive'} "
            f"trend that {'is sustained' if insight.pattern_detected and insight.pattern_detected.is_sustained else 'requires monitoring'}."
        )

        if insight.scores:
            narrative += f" Confidence: {insight.scores.confidence_label.value}."

        return narrative

    async def _generate_decline_narrative(
        self,
        insight: Insight,
        context: NarrativeContext,
    ) -> str:
        """
        Generate narrative for decline insight.
        """
        change_str = f"{abs(insight.relative_magnitude * 100):.1f}%"
        value_str = self._format_value(abs(insight.magnitude), context.unit)

        narrative = (
            f"{context.metric_name} declined by {change_str}, "
            f"representing a reduction of {value_str}. "
            f"This {'sustained' if insight.pattern_detected and insight.pattern_detected.is_sustained else 'emerging'} "
            f"decline requires investigation."
        )

        if insight.scores:
            narrative += f" Priority: {insight.scores.priority_label.value}."

        return narrative

    async def _generate_trend_narrative(
        self,
        insight: Insight,
        context: NarrativeContext,
    ) -> str:
        """
        Generate narrative for sustained trend insight.
        """
        direction = insight.pattern_detected.direction if insight.pattern_detected else "unknown"

        narrative = (
            f"A {direction} trend has been detected in {context.metric_name} "
            f"over the analysis period. "
            f"The trend shows {insight.pattern_detected.description if insight.pattern_detected else 'consistent directional movement'}."
        )

        if insight.pattern_detected and insight.pattern_detected.is_sustained:
            narrative += " This trend is sustained and likely to continue without intervention."

        return narrative

    async def _generate_reversal_narrative(
        self,
        insight: Insight,
        context: NarrativeContext,
    ) -> str:
        """
        Generate narrative for trend reversal insight.
        """
        narrative = (
            f"A trend reversal has been detected in {context.metric_name}. "
            f"The previous trend has reversed direction, indicating a significant shift in performance. "
            f"This reversal has {insight.confidence_level:.0%} confidence."
        )

        return narrative

    async def _generate_segment_narrative(
        self,
        insight: Insight,
        context: NarrativeContext,
    ) -> str:
        """
        Generate narrative for segment insight.
        """
        is_outperformance = insight.insight_type == InsightType.SEGMENT_OUTPERFORMANCE
        verb = "outperformed" if is_outperformance else "underperformed"

        narrative = (
            f"A segment has {verb} the overall {context.metric_name} performance. "
            f"The segment contributed {abs(insight.relative_magnitude * 100):.1f}% "
            f"{'above' if is_outperformance else 'below'} the average."
        )

        return narrative

    async def _generate_generic_insight_narrative(
        self,
        insight: Insight,
        context: NarrativeContext,
    ) -> str:
        """
        Generate generic insight narrative.
        """
        narrative = (
            f"An insight has been detected in {context.metric_name}: {insight.title}. "
            f"{insight.summary}"
        )

        return narrative

    def _format_value(self, value: float, unit: str) -> str:
        """
        Format a value based on unit.
        """
        if unit == "USD" or unit == "$":
            if abs(value) >= 1_000_000:
                return f"${value / 1_000_000:,.2f}M"
            elif abs(value) >= 1_000:
                return f"${value / 1_000:,.1f}K"
            else:
                return f"${value:,.2f}"
        elif unit == "%":
            return f"{value:.1f}%"
        else:
            return f"{value:,.2f} {unit}"


# Singleton instance
narrative_engine = NarrativeEngine()
