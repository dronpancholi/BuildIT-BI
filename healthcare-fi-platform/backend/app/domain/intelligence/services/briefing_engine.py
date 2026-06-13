"""
Executive Briefing Engine.
Generates comprehensive executive briefings from intelligence artifacts.
"""
import uuid
import time
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List

from ..entities import (
    Briefing,
    BriefingSection,
    BriefingSummary,
    BriefingHighlight,
    Insight,
    RootCause,
    Anomaly,
    Opportunity,
    Recommendation,
    IntelligenceScores,
)
from app.domain.intelligence.value_objects import (
    BriefingType,
    BriefingStatus,
    HighlightType,
    SentimentLabel,
    ArtifactStatus,
    ArtifactType,
    GenerationSource,
    PeriodType,
    ScopeType,
    InsightType,
    AnomalySeverity,
    OpportunityStatus,
)


@dataclass
class BriefingOptions:
    include_narrative: bool = True
    include_visualizations: bool = True
    max_highlights: int = 5
    max_recommendations: int = 10
    tone: str = "executive"


@dataclass
class BriefingGenerationContext:
    tenant_id: uuid.UUID
    briefing_type: BriefingType
    period_start: datetime
    period_end: datetime
    comparison_period_start: Optional[datetime] = None
    comparison_period_end: Optional[datetime] = None
    recipient_ids: List[uuid.UUID] = field(default_factory=list)
    scope: Optional[Dict[str, Any]] = None


class BriefingEngine:
    """
    Generates comprehensive executive briefings.
    """

    def __init__(self):
        pass

    async def generate_briefing(
        self,
        context: BriefingGenerationContext,
        insights: List[Insight],
        anomalies: List[Anomaly],
        opportunities: List[Opportunity],
        recommendations: List[Recommendation],
        root_causes: List[RootCause],
        metrics_snapshot: Dict[str, Any],
        options: BriefingOptions = BriefingOptions(),
    ) -> Briefing:
        """
        Generate a complete executive briefing.
        """
        start_time = time.time()

        # Generate sections
        sections = []

        # Wins section
        wins_section = self._generate_wins_section(insights, metrics_snapshot)
        sections.append(wins_section)

        # Risks section
        risks_section = self._generate_risks_section(anomalies, root_causes)
        sections.append(risks_section)

        # Opportunities section
        opportunities_section = self._generate_opportunities_section(opportunities)
        sections.append(opportunities_section)

        # Recommendations section
        recommendations_section = self._generate_recommendations_section(recommendations)
        sections.append(recommendations_section)

        # Generate key highlights
        key_highlights = self._generate_highlights(
            insights, anomalies, opportunities, options.max_highlights
        )

        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            insights, anomalies, opportunities, recommendations, metrics_snapshot
        )

        # Generate narrative
        narrative = ""
        if options.include_narrative:
            narrative = self._generate_narrative(
                executive_summary, sections, key_highlights
            )

        # Create briefing
        briefing = Briefing(
            id=uuid.uuid4(),
            tenant_id=context.tenant_id,
            artifact_type=ArtifactType.BRIEFING,
            briefing_type=context.briefing_type,
            title=self._generate_title(context.briefing_type, context.period_start, context.period_end),
            period_start=context.period_start,
            period_end=context.period_end,
            period_type=PeriodType.MONTHLY,
            comparison_period_start=context.comparison_period_start,
            comparison_period_end=context.comparison_period_end,
            recipient_ids=context.recipient_ids,
            sections=sections,
            executive_summary=executive_summary,
            key_highlights=key_highlights,
            metrics_snapshot=[metrics_snapshot],
            narrative=narrative,
            briefing_status=BriefingStatus.DRAFT,
            generation_method="template_generation",
            generation_duration_ms=int((time.time() - start_time) * 1000),
            scope_type=ScopeType.TENANT,
            scope_id=context.scope.get("scope_id") if context.scope else None,
            status=ArtifactStatus.DISCOVERED,
            version=1,
        )

        return briefing

    async def generate_daily_briefing(
        self,
        briefing_date: date,
        tenant_id: uuid.UUID,
        recipient_ids: List[uuid.UUID],
        intelligence_data: Dict[str, Any],
    ) -> Briefing:
        """
        Generate daily briefing.
        """
        context = BriefingGenerationContext(
            tenant_id=tenant_id,
            briefing_type=BriefingType.DAILY,
            period_start=datetime.combine(briefing_date, datetime.min.time()),
            period_end=datetime.combine(briefing_date, datetime.max.time()),
            comparison_period_start=datetime.combine(briefing_date - timedelta(days=1), datetime.min.time()),
            comparison_period_end=datetime.combine(briefing_date - timedelta(days=1), datetime.max.time()),
            recipient_ids=recipient_ids,
        )

        return await self.generate_briefing(
            context=context,
            insights=intelligence_data.get("insights", []),
            anomalies=intelligence_data.get("anomalies", []),
            opportunities=intelligence_data.get("opportunities", []),
            recommendations=intelligence_data.get("recommendations", []),
            root_causes=intelligence_data.get("root_causes", []),
            metrics_snapshot=intelligence_data.get("metrics_snapshot", {}),
        )

    async def generate_weekly_briefing(
        self,
        week_start: date,
        tenant_id: uuid.UUID,
        recipient_ids: List[uuid.UUID],
        intelligence_data: Dict[str, Any],
    ) -> Briefing:
        """
        Generate weekly briefing.
        """
        week_end = week_start + timedelta(days=6)

        context = BriefingGenerationContext(
            tenant_id=tenant_id,
            briefing_type=BriefingType.WEEKLY,
            period_start=datetime.combine(week_start, datetime.min.time()),
            period_end=datetime.combine(week_end, datetime.max.time()),
            comparison_period_start=datetime.combine(week_start - timedelta(days=7), datetime.min.time()),
            comparison_period_end=datetime.combine(week_end - timedelta(days=7), datetime.max.time()),
            recipient_ids=recipient_ids,
        )

        return await self.generate_briefing(
            context=context,
            insights=intelligence_data.get("insights", []),
            anomalies=intelligence_data.get("anomalies", []),
            opportunities=intelligence_data.get("opportunities", []),
            recommendations=intelligence_data.get("recommendations", []),
            root_causes=intelligence_data.get("root_causes", []),
            metrics_snapshot=intelligence_data.get("metrics_snapshot", {}),
        )

    async def generate_monthly_briefing(
        self,
        month: date,
        tenant_id: uuid.UUID,
        recipient_ids: List[uuid.UUID],
        intelligence_data: Dict[str, Any],
    ) -> Briefing:
        """
        Generate monthly briefing.
        """
        # Calculate month start and end
        month_start = month.replace(day=1)
        if month.month == 12:
            month_end = month.replace(year=month.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month.replace(month=month.month + 1, day=1) - timedelta(days=1)

        # Previous month for comparison
        prev_month_end = month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        context = BriefingGenerationContext(
            tenant_id=tenant_id,
            briefing_type=BriefingType.MONTHLY,
            period_start=datetime.combine(month_start, datetime.min.time()),
            period_end=datetime.combine(month_end, datetime.max.time()),
            comparison_period_start=datetime.combine(prev_month_start, datetime.min.time()),
            comparison_period_end=datetime.combine(prev_month_end, datetime.max.time()),
            recipient_ids=recipient_ids,
        )

        return await self.generate_briefing(
            context=context,
            insights=intelligence_data.get("insights", []),
            anomalies=intelligence_data.get("anomalies", []),
            opportunities=intelligence_data.get("opportunities", []),
            recommendations=intelligence_data.get("recommendations", []),
            root_causes=intelligence_data.get("root_causes", []),
            metrics_snapshot=intelligence_data.get("metrics_snapshot", {}),
        )

    def _generate_wins_section(
        self,
        insights: List[Insight],
        metrics_snapshot: Dict[str, Any]
    ) -> BriefingSection:
        """
        Generate wins section from positive insights.
        """
        positive_insights = [
            i for i in insights
            if i.insight_type in [
                InsightType.REVENUE_GROWTH,
                InsightType.MARGIN_IMPROVEMENT,
                InsightType.COST_REDUCTION,
                InsightType.SEGMENT_OUTPERFORMANCE,
            ]
        ]

        content_parts = []
        for insight in positive_insights[:5]:
            content_parts.append(f"- {insight.title}: {insight.summary}")

        return BriefingSection(
            section_id="wins",
            section_type="wins",
            title="Key Wins",
            order=1,
            content="\n".join(content_parts) if content_parts else "No significant wins this period.",
            data={"insight_count": len(positive_insights)},
            confidence=0.8,
            sources=[str(i.id) for i in positive_insights],
        )

    def _generate_risks_section(
        self,
        anomalies: List[Anomaly],
        root_causes: List[RootCause]
    ) -> BriefingSection:
        """
        Generate risks section from anomalies and root causes.
        """
        critical_anomalies = [
            a for a in anomalies
            if a.severity in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH]
        ]

        content_parts = []
        for anomaly in critical_anomalies[:5]:
            content_parts.append(
                f"- {anomaly.title} ({anomaly.severity.value}): "
                f"Observed {anomaly.observed_value:,.0f}, "
                f"Expected {anomaly.expected_value:,.0f} "
                f"({anomaly.deviation_percent:+.1f}%)"
            )

        return BriefingSection(
            section_id="risks",
            section_type="risks",
            title="Key Risks & Alerts",
            order=2,
            content="\n".join(content_parts) if content_parts else "No significant risks detected.",
            data={"anomaly_count": len(critical_anomalies)},
            confidence=0.85,
            sources=[str(a.id) for a in critical_anomalies],
        )

    def _generate_opportunities_section(
        self,
        opportunities: List[Opportunity]
    ) -> BriefingSection:
        """
        Generate opportunities section.
        """
        active_opportunities = [
            o for o in opportunities
            if o.estimated_value > 0
        ]

        total_value = sum(o.estimated_value for o in active_opportunities)

        content_parts = []
        for opp in active_opportunities[:5]:
            content_parts.append(
                f"- {opp.title}: ${opp.estimated_value:,.0f} "
                f"({opp.effort_level.value} effort, {opp.risk_level.value} risk)"
            )

        return BriefingSection(
            section_id="opportunities",
            section_type="opportunities",
            title=f"Opportunities (${total_value:,.0f} Total Value)",
            order=3,
            content="\n".join(content_parts) if content_parts else "No opportunities identified.",
            data={
                "opportunity_count": len(active_opportunities),
                "total_value": total_value,
            },
            confidence=0.75,
            sources=[str(o.id) for o in active_opportunities],
        )

    def _generate_recommendations_section(
        self,
        recommendations: List[Recommendation]
    ) -> BriefingSection:
        """
        Generate recommendations section.
        """
        top_recommendations = sorted(
            recommendations,
            key=lambda r: r.scores.priority if r.scores else 0,
            reverse=True
        )[:5]

        content_parts = []
        for rec in top_recommendations:
            content_parts.append(
                f"- {rec.title}: Expected impact ${rec.expected_impact_value:,.0f}"
            )

        return BriefingSection(
            section_id="recommendations",
            section_type="recommendations",
            title="Top Recommendations",
            order=4,
            content="\n".join(content_parts) if content_parts else "No recommendations.",
            data={"recommendation_count": len(top_recommendations)},
            confidence=0.8,
            sources=[str(r.id) for r in top_recommendations],
        )

    def _generate_highlights(
        self,
        insights: List[Insight],
        anomalies: List[Anomaly],
        opportunities: List[Opportunity],
        max_highlights: int
    ) -> List[BriefingHighlight]:
        """
        Generate key highlights from all intelligence.
        """
        highlights = []

        # Add critical anomalies as highlights
        for anomaly in anomalies:
            if anomaly.severity == AnomalySeverity.CRITICAL:
                highlights.append(BriefingHighlight(
                    highlight_type=HighlightType.RISK,
                    priority="P0",
                    title=anomaly.title,
                    description=anomaly.description,
                    metric_value=f"Observed: {anomaly.observed_value:,.0f}, Expected: {anomaly.expected_value:,.0f}",
                    action_required="Investigate immediately",
                ))

        # Add high-value opportunities
        for opp in opportunities:
            if opp.estimated_value > 100000:
                highlights.append(BriefingHighlight(
                    highlight_type=HighlightType.OPPORTUNITY,
                    priority="P1",
                    title=opp.title,
                    description=opp.summary,
                    metric_value=f"Value: ${opp.estimated_value:,.0f}",
                ))

        # Add significant insights
        for insight in insights:
            if insight.scores and insight.scores.priority >= 0.7:
                highlights.append(BriefingHighlight(
                    highlight_type=HighlightType.TREND,
                    priority="P2",
                    title=insight.title,
                    description=insight.summary,
                ))

        # Sort by priority and limit
        highlights = highlights[:max_highlights]

        return highlights

    def _generate_executive_summary(
        self,
        insights: List[Insight],
        anomalies: List[Anomaly],
        opportunities: List[Opportunity],
        recommendations: List[Recommendation],
        metrics_snapshot: Dict[str, Any]
    ) -> BriefingSummary:
        """
        Generate executive summary.
        """
        # Determine overall sentiment
        critical_anomalies = [
            a for a in anomalies if a.severity == AnomalySeverity.CRITICAL
        ]
        positive_insights = [
            i for i in insights
            if i.insight_type in [InsightType.REVENUE_GROWTH, InsightType.MARGIN_IMPROVEMENT]
        ]

        if len(critical_anomalies) > 2:
            sentiment = SentimentLabel.CRITICAL
        elif len(critical_anomalies) > 0:
            sentiment = SentimentLabel.CONCERNED
        elif len(positive_insights) > 2:
            sentiment = SentimentLabel.POSITIVE
        else:
            sentiment = SentimentLabel.NEUTRAL

        # Generate narrative
        narrative_parts = []
        if positive_insights:
            narrative_parts.append(
                f"{len(positive_insights)} positive insights detected"
            )
        if critical_anomalies:
            narrative_parts.append(
                f"{len(critical_anomalies)} critical anomalies require attention"
            )
        if opportunities:
            total_value = sum(o.estimated_value for o in opportunities)
            narrative_parts.append(
                f"{len(opportunities)} opportunities identified (${total_value:,.0f} total value)"
            )

        narrative = ". ".join(narrative_parts) + "." if narrative_parts else "No significant activity."

        return BriefingSummary(
            narrative=narrative,
            primary_wins=[i.title for i in positive_insights[:3]],
            primary_risks=[a.title for a in critical_anomalies[:3]],
            primary_actions=[r.title for r in recommendations[:3]],
            overall_sentiment=sentiment,
            confidence=0.8,
        )

    def _generate_narrative(
        self,
        summary: BriefingSummary,
        sections: List[BriefingSection],
        highlights: List[BriefingHighlight]
    ) -> str:
        """
        Generate full briefing narrative.
        """
        narrative_parts = []

        # Executive summary
        narrative_parts.append(f"**Executive Summary**\n{summary.narrative}\n")

        # Key highlights
        if highlights:
            narrative_parts.append("**Key Highlights**")
            for highlight in highlights:
                narrative_parts.append(
                    f"- [{highlight.priority}] {highlight.title}: {highlight.description}"
                )
            narrative_parts.append("")

        # Section narratives
        for section in sections:
            if section.content:
                narrative_parts.append(f"**{section.title}**\n{section.content}\n")

        return "\n".join(narrative_parts)

    def _generate_title(
        self,
        briefing_type: BriefingType,
        period_start: datetime,
        period_end: datetime
    ) -> str:
        """
        Generate briefing title.
        """
        if briefing_type == BriefingType.DAILY:
            return f"Daily Briefing - {period_start.strftime('%B %d, %Y')}"
        elif briefing_type == BriefingType.WEEKLY:
            return f"Weekly Briefing - {period_start.strftime('%B %d')} to {period_end.strftime('%B %d, %Y')}"
        elif briefing_type == BriefingType.MONTHLY:
            return f"Monthly Briefing - {period_start.strftime('%B %Y')}"
        elif briefing_type == BriefingType.QUARTERLY:
            quarter = (period_start.month - 1) // 3 + 1
            return f"Q{quarter} {period_start.year} Briefing"
        elif briefing_type == BriefingType.ANNUAL:
            return f"Annual Briefing - {period_start.year}"
        else:
            return f"Briefing - {period_start.strftime('%B %d, %Y')}"
