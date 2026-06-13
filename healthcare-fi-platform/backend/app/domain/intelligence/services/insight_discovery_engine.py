"""
Insight Discovery Engine.
Continuously scans metrics for non-trivial, significant patterns.
"""
import uuid
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from ..entities import (
    Insight,
    IntelligenceScores,
)
from .root_cause_engine import TimePeriod
from app.domain.intelligence.value_objects import (
    InsightType,
    PatternType,
    DiscoveryMethod,
    ArtifactStatus,
    ArtifactType,
    GenerationSource,
    PeriodType,
    ScopeType,
    StatisticalTest,
    PatternDescription,
    EvidenceType,
    Evidence,
)
from .scoring import IntelligenceScoreCalculator, ScoringContext


@dataclass
class DiscoveryOptions:
    run_all_methods: bool = True
    methods_to_run: Optional[List[str]] = None
    min_confidence: float = 0.70
    min_effect_size: float = 0.10
    max_insights_per_run: int = 50
    apply_bh_correction: bool = True
    alpha: float = 0.05


@dataclass
class TrendDetectionResult:
    trend_direction: str  # "up", "down", "stable", "reversal"
    slope: float
    slope_std_error: float
    r_squared: float
    is_sustained: bool
    reversal_detected: bool
    reversal_confidence: Optional[float]
    acceleration_detected: bool
    acceleration_magnitude: Optional[float]


@dataclass
class CorrelationDiscoveryResult:
    metric_a_id: uuid.UUID
    metric_b_id: uuid.UUID
    correlation_coefficient: float
    correlation_type: str
    p_value: float
    is_significant: bool
    strength: str
    direction: str
    is_new_correlation: bool
    correlation_change: Optional[float]


@dataclass
class SegmentPerformanceResult:
    segment_name: str
    segment_id: Optional[uuid.UUID]
    metric_value: float
    expected_value: float
    deviation_percent: float
    is_outperforming: bool
    confidence: float


@dataclass
class MetricTimeSeries:
    metric_id: uuid.UUID
    metric_code: str
    values: List[float]
    timestamps: List[datetime]
    scope_id: Optional[uuid.UUID] = None


class TrendAnalyzer:
    """
    Analyzes trend patterns in time series data.
    """

    async def detect_trend(
        self,
        data: MetricTimeSeries,
        min_periods: int = 3
    ) -> Optional[TrendDetectionResult]:
        """
        Detect trend patterns using linear regression.
        """
        if len(data.values) < min_periods:
            return None

        # Calculate linear regression
        n = len(data.values)
        x = list(range(n))
        y = data.values

        # Mean of x and y
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)

        # Calculate slope and intercept
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return None

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Calculate R-squared
        y_pred = [slope * xi + intercept for xi in x]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Calculate standard error of slope
        residual_std = math.sqrt(ss_res / (n - 2)) if n > 2 else 0
        slope_std_error = residual_std / math.sqrt(denominator) if denominator > 0 else 0

        # Determine trend direction
        if abs(slope) < 0.001:  # Threshold for "stable"
            direction = "stable"
        elif slope > 0:
            direction = "up"
        else:
            direction = "down"

        # Check for sustained trend (at least 3 consecutive periods)
        is_sustained = self._check_sustained_trend(data.values, min_periods=3)

        # Check for reversal
        reversal_detected = False
        reversal_confidence = None
        if len(data.values) >= 5:
            # Check if trend changed direction in last 2 periods
            recent_trend = data.values[-1] - data.values[-3]
            prior_trend = data.values[-3] - data.values[0]
            if recent_trend * prior_trend < 0:  # Opposite signs
                reversal_detected = True
                reversal_confidence = 0.7  # Simplified

        # Check for acceleration
        acceleration_detected = False
        acceleration_magnitude = None
        if len(data.values) >= 6:
            first_half_slope = (data.values[len(data.values)//2] - data.values[0]) / (len(data.values)//2)
            second_half_slope = (data.values[-1] - data.values[len(data.values)//2]) / (len(data.values)//2)
            if abs(second_half_slope) > abs(first_half_slope) * 1.5:
                acceleration_detected = True
                acceleration_magnitude = second_half_slope - first_half_slope

        return TrendDetectionResult(
            trend_direction=direction,
            slope=slope,
            slope_std_error=slope_std_error,
            r_squared=r_squared,
            is_sustained=is_sustained,
            reversal_detected=reversal_detected,
            reversal_confidence=reversal_confidence,
            acceleration_detected=acceleration_detected,
            acceleration_magnitude=acceleration_magnitude,
        )

    def _check_sustained_trend(self, values: List[float], min_periods: int = 3) -> bool:
        """Check if trend is sustained over multiple periods."""
        if len(values) < min_periods:
            return False

        # Check if all changes have the same sign
        changes = [values[i+1] - values[i] for i in range(len(values) - 1)]
        if not changes:
            return False

        # Count consecutive same-sign changes from the end
        consecutive = 0
        for change in reversed(changes):
            if change * changes[-1] > 0:  # Same sign as last change
                consecutive += 1
            else:
                break

        return consecutive >= min_periods - 1


class CorrelationAnalyzer:
    """
    Analyzes correlation patterns between metrics.
    """

    async def calculate_correlation(
        self,
        x: List[float],
        y: List[float],
        method: str = "pearson"
    ) -> Optional[CorrelationDiscoveryResult]:
        """
        Calculate correlation between two metrics.
        """
        if len(x) != len(y) or len(x) < 3:
            return None

        if method == "pearson":
            correlation = self._pearson_correlation(x, y)
        else:
            correlation = self._spearman_correlation(x, y)

        # Calculate p-value (simplified)
        n = len(x)
        if n < 3:
            p_value = 1.0
        else:
            # t-statistic for correlation
            t_stat = correlation * math.sqrt((n - 2) / (1 - correlation**2)) if abs(correlation) < 1 else 0
            # Approximate p-value
            p_value = self._t_to_p_value(t_stat, n - 2)

        is_significant = p_value < 0.05

        # Determine strength and direction
        strength = self._correlation_strength(correlation)
        direction = "positive" if correlation > 0 else "negative"

        return CorrelationDiscoveryResult(
            metric_a_id=uuid.uuid4(),  # Placeholder
            metric_b_id=uuid.uuid4(),  # Placeholder
            correlation_coefficient=correlation,
            correlation_type=method,
            p_value=p_value,
            is_significant=is_significant,
            strength=strength,
            direction=direction,
            is_new_correlation=False,  # Would need historical data
            correlation_change=None,  # Would need historical data
        )

    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        n = len(x)
        if n < 2:
            return 0.0

        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator_x = math.sqrt(sum((xi - x_mean) ** 2 for xi in x))
        denominator_y = math.sqrt(sum((yi - y_mean) ** 2 for yi in y))
        denominator = denominator_x * denominator_y

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _spearman_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Spearman rank correlation."""
        n = len(x)
        if n < 2:
            return 0.0

        # Rank the data
        x_ranks = self._rank_data(x)
        y_ranks = self._rank_data(y)

        # Calculate Pearson correlation on ranks
        return self._pearson_correlation(x_ranks, y_ranks)

    def _rank_data(self, data: List[float]) -> List[float]:
        """Rank data values."""
        sorted_indices = sorted(range(len(data)), key=lambda i: data[i])
        ranks = [0.0] * len(data)
        for rank, idx in enumerate(sorted_indices):
            ranks[idx] = float(rank + 1)
        return ranks

    def _correlation_strength(self, correlation: float) -> str:
        """Determine correlation strength."""
        abs_corr = abs(correlation)
        if abs_corr >= 0.8:
            return "strong"
        elif abs_corr >= 0.5:
            return "moderate"
        elif abs_corr >= 0.3:
            return "weak"
        else:
            return "negligible"

    def _t_to_p_value(self, t_stat: float, df: int) -> float:
        """Convert t-statistic to approximate p-value."""
        if df <= 0:
            return 1.0

        abs_t = abs(t_stat)
        # Approximate p-value for two-tailed test
        if abs_t >= 3.5:
            return 0.001
        elif abs_t >= 2.5:
            return 0.01
        elif abs_t >= 2.0:
            return 0.05
        elif abs_t >= 1.5:
            return 0.10
        else:
            return 0.5


class SegmentAnalyzer:
    """
    Analyzes segment performance insights.
    """

    async def analyze_segment_performance(
        self,
        segments: List[Dict[str, Any]],
        total_change: float
    ) -> List[SegmentPerformanceResult]:
        """
        Analyze which segments are over/under-performing.
        """
        results = []

        for segment in segments:
            current = segment.get("current_value", 0)
            previous = segment.get("previous_value", 0)
            expected = segment.get("expected_value", previous)

            if expected == 0:
                continue

            deviation_percent = ((current - expected) / expected) * 100
            is_outperforming = deviation_percent > 0

            # Simple confidence calculation
            confidence = min(0.95, 0.7 + abs(deviation_percent) / 100)

            results.append(SegmentPerformanceResult(
                segment_name=segment.get("name", "Unknown"),
                segment_id=segment.get("id"),
                metric_value=current,
                expected_value=expected,
                deviation_percent=deviation_percent,
                is_outperforming=is_outperforming,
                confidence=confidence,
            ))

        return results


class InsightDiscoveryEngine:
    """
    Continuously scans metrics for non-trivial, significant patterns.
    """

    def __init__(self):
        self.score_calculator = IntelligenceScoreCalculator()
        self.trend_analyzer = TrendAnalyzer()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.segment_analyzer = SegmentAnalyzer()

    async def discover_insights_for_scope(
        self,
        tenant_id: uuid.UUID,
        metrics: List[MetricTimeSeries],
        period: TimePeriod,
        options: DiscoveryOptions = DiscoveryOptions()
    ) -> List[Insight]:
        """
        Runs all discovery algorithms for a given scope and period.
        Returns ranked list of discovered insights.
        """
        all_insights = []

        # Discover trend insights
        trend_insights = await self.discover_trend_insights(
            tenant_id=tenant_id,
            metrics=metrics,
            period=period
        )
        all_insights.extend(trend_insights)

        # Discover correlation insights
        correlation_insights = await self.discover_correlation_insights(
            tenant_id=tenant_id,
            metrics=metrics,
            period=period
        )
        all_insights.extend(correlation_insights)

        # Apply Benjamini-Hochberg correction if enabled
        if options.apply_bh_correction:
            all_insights = self._apply_bh_correction(all_insights, options.alpha)

        # Filter by minimum confidence
        all_insights = [
            i for i in all_insights
            if i.scores and i.scores.confidence >= options.min_confidence
        ]

        # Rank insights
        all_insights = await self.rank_insights(all_insights)

        # Limit number of insights
        all_insights = all_insights[:options.max_insights_per_run]

        return all_insights

    async def discover_trend_insights(
        self,
        tenant_id: uuid.UUID,
        metrics: List[MetricTimeSeries],
        period: TimePeriod
    ) -> List[Insight]:
        """
        Detects trend patterns:
        - Sustained directional movement
        - Trend reversals
        - Acceleration/deceleration
        """
        insights = []

        for metric in metrics:
            if len(metric.values) < 3:
                continue

            trend_result = await self.trend_analyzer.detect_trend(
                MetricTimeSeries(
                    metric_id=metric.metric_id,
                    metric_code=metric.metric_code,
                    values=metric.values,
                    timestamps=metric.timestamps,
                )
            )

            if trend_result is None:
                continue

            # Create insight based on trend
            insight = await self._create_trend_insight(
                tenant_id=tenant_id,
                metric=metric,
                trend=trend_result,
                period=period
            )
            if insight:
                insights.append(insight)

        return insights

    async def discover_correlation_insights(
        self,
        tenant_id: uuid.UUID,
        metrics: List[MetricTimeSeries],
        period: TimePeriod
    ) -> List[Insight]:
        """
        Detects correlation patterns between metrics.
        """
        insights = []

        # Need at least 2 metrics with enough data
        valid_metrics = [m for m in metrics if len(m.values) >= 3]
        if len(valid_metrics) < 2:
            return insights

        # Check all pairs
        for i in range(len(valid_metrics)):
            for j in range(i + 1, len(valid_metrics)):
                m1 = valid_metrics[i]
                m2 = valid_metrics[j]

                # Ensure same length
                min_len = min(len(m1.values), len(m2.values))
                if min_len < 3:
                    continue

                x = m1.values[:min_len]
                y = m2.values[:min_len]

                corr_result = await self.correlation_analyzer.calculate_correlation(x, y)
                if corr_result and corr_result.is_significant:
                    insight = await self._create_correlation_insight(
                        tenant_id=tenant_id,
                        metric_a=m1,
                        metric_b=m2,
                        correlation=corr_result,
                        period=period
                    )
                    if insight:
                        insights.append(insight)

        return insights

    async def _create_trend_insight(
        self,
        tenant_id: uuid.UUID,
        metric: MetricTimeSeries,
        trend: TrendDetectionResult,
        period: TimePeriod
    ) -> Optional[Insight]:
        """
        Create an insight from trend analysis.
        """
        if trend.trend_direction == "stable":
            return None

        # Determine insight type
        if trend.trend_direction == "up":
            insight_type = InsightType.REVENUE_GROWTH
            title = f"Sustained upward trend in {metric.metric_code}"
        elif trend.trend_direction == "down":
            insight_type = InsightType.REVENUE_DECLINE
            title = f"Sustained downward trend in {metric.metric_code}"
        elif trend.reversal_detected:
            insight_type = InsightType.TREND_REVERSAL
            title = f"Trend reversal detected in {metric.metric_code}"
        else:
            return None

        # Calculate magnitude
        magnitude = abs(trend.slope) * len(metric.values)
        relative_magnitude = abs(trend.slope) / statistics.mean(metric.values) if statistics.mean(metric.values) != 0 else 0

        # Create insight
        insight = Insight(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            artifact_type=ArtifactType.INSIGHT,
            insight_type=insight_type,
            title=title,
            summary=f"{metric.metric_code} shows a {trend.trend_direction} trend over {len(metric.values)} periods",
            detailed_analysis=self._generate_trend_analysis(metric, trend),
            pattern_detected=PatternDescription(
                pattern_type=PatternType.TREND,
                description=f"{'Positive' if trend.trend_direction == 'up' else 'Negative'} trend with R²={trend.r_squared:.3f}",
                confidence=trend.r_squared,
                direction=trend.trend_direction,
                is_sustained=trend.is_sustained,
            ),
            pattern_type=PatternType.TREND,
            statistical_properties={
                "slope": trend.slope,
                "r_squared": trend.r_squared,
                "is_sustained": trend.is_sustained,
            },
            statistical_test=StatisticalTest(
                test_name="linear_regression",
                test_statistic=trend.slope / trend.slope_std_error if trend.slope_std_error > 0 else 0,
                p_value=self._r_squared_to_p_value(trend.r_squared, len(metric.values)),
                confidence_level=0.95,
                effect_size=relative_magnitude,
            ),
            test_statistic=trend.slope / trend.slope_std_error if trend.slope_std_error > 0 else None,
            p_value=self._r_squared_to_p_value(trend.r_squared, len(metric.values)),
            is_significant=trend.r_squared > 0.5,
            confidence_level=trend.r_squared,
            effect_size=relative_magnitude,
            magnitude=magnitude,
            magnitude_unit="absolute",
            relative_magnitude=relative_magnitude,
            metric_id=metric.metric_id,
            metric_code=metric.metric_code,
            period_start=period.start,
            period_end=period.end,
            period_type=period.period_type,
            scope_type=ScopeType.TENANT,
            discovery_method=DiscoveryMethod.SCHEDULED,
            status=ArtifactStatus.DISCOVERED,
            version=1,
        )

        # Calculate scores
        scoring_context = ScoringContext(
            tenant_id=tenant_id,
            artifact_type=ArtifactType.INSIGHT,
            artifact_data={
                "p_value": insight.p_value,
                "dollar_impact": magnitude,
                "severity": "high" if trend.r_squared > 0.8 else "medium",
                "sample_size": len(metric.values),
                "historical_consistency": trend.r_squared,
            }
        )
        scores = await self.score_calculator.calculate_scores(
            ArtifactType.INSIGHT,
            scoring_context.artifact_data,
            scoring_context
        )
        insight.scores = scores

        return insight

    async def _create_correlation_insight(
        self,
        tenant_id: uuid.UUID,
        metric_a: MetricTimeSeries,
        metric_b: MetricTimeSeries,
        correlation: CorrelationDiscoveryResult,
        period: TimePeriod
    ) -> Optional[Insight]:
        """
        Create an insight from correlation analysis.
        """
        if abs(correlation.correlation_coefficient) < 0.5:
            return None

        # Determine insight type
        if correlation.direction == "positive":
            insight_type = InsightType.CORRELATION_DISCOVERED
            title = f"Strong positive correlation between {metric_a.metric_code} and {metric_b.metric_code}"
        else:
            insight_type = InsightType.CORRELATION_DISCOVERED
            title = f"Strong negative correlation between {metric_a.metric_code} and {metric_b.metric_code}"

        # Create insight
        insight = Insight(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            artifact_type=ArtifactType.INSIGHT,
            insight_type=insight_type,
            title=title,
            summary=f"{metric_a.metric_code} and {metric_b.metric_code} show {correlation.strength} {correlation.direction} correlation (r={correlation.correlation_coefficient:.3f})",
            detailed_analysis=(
                f"Analysis of {len(metric_a.values)} periods reveals a {correlation.strength} "
                f"{correlation.direction} correlation (r={correlation.correlation_coefficient:.3f}, "
                f"p={correlation.p_value:.4f}) between {metric_a.metric_code} and {metric_b.metric_code}. "
                f"This {'statistically significant' if correlation.is_significant else 'not statistically significant'} "
                f"correlation suggests {'a potential causal relationship' if abs(correlation.correlation_coefficient) > 0.7 else 'an association between these metrics'}."
            ),
            pattern_detected=PatternDescription(
                pattern_type=PatternType.CORRELATION,
                description=f"{correlation.strength} {correlation.direction} correlation (r={correlation.correlation_coefficient:.3f})",
                confidence=1 - correlation.p_value,
                metadata={
                    "metric_a_code": metric_a.metric_code,
                    "metric_b_code": metric_b.metric_code,
                    "correlation_type": correlation.correlation_type,
                },
            ),
            pattern_type=PatternType.CORRELATION,
            statistical_properties={
                "correlation_coefficient": correlation.correlation_coefficient,
                "p_value": correlation.p_value,
                "strength": correlation.strength,
                "direction": correlation.direction,
            },
            statistical_test=StatisticalTest(
                test_name=correlation.correlation_type,
                test_statistic=correlation.correlation_coefficient,
                p_value=correlation.p_value,
                confidence_level=0.95,
                effect_size=abs(correlation.correlation_coefficient),
                sample_size=len(metric_a.values),
            ),
            p_value=correlation.p_value,
            is_significant=correlation.is_significant,
            confidence_level=1 - correlation.p_value,
            effect_size=abs(correlation.correlation_coefficient),
            magnitude=abs(correlation.correlation_coefficient),
            magnitude_unit="correlation",
            relative_magnitude=abs(correlation.correlation_coefficient),
            related_metric_ids=[metric_a.metric_id, metric_b.metric_id],
            metric_id=metric_a.metric_id,
            metric_code=metric_a.metric_code,
            period_start=period.start,
            period_end=period.end,
            period_type=period.period_type,
            scope_type=ScopeType.TENANT,
            discovery_method=DiscoveryMethod.SCHEDULED,
            status=ArtifactStatus.DISCOVERED,
            version=1,
        )

        # Calculate scores
        scoring_context = ScoringContext(
            tenant_id=tenant_id,
            artifact_type=ArtifactType.INSIGHT,
            artifact_data={
                "p_value": correlation.p_value,
                "dollar_impact": 0,  # Correlations don't have direct dollar impact
                "severity": "medium",
                "sample_size": len(metric_a.values),
                "historical_consistency": 1 - correlation.p_value,
            }
        )
        scores = await self.score_calculator.calculate_scores(
            ArtifactType.INSIGHT,
            scoring_context.artifact_data,
            scoring_context
        )
        insight.scores = scores

        return insight

    def _generate_trend_analysis(self, metric: MetricTimeSeries, trend: TrendDetectionResult) -> str:
        """Generate detailed analysis for trend insight."""
        analysis = f"Analysis of {metric.metric_code} over {len(metric.values)} periods:\n\n"
        analysis += f"Trend Direction: {trend.trend_direction}\n"
        analysis += f"Slope: {trend.slope:.4f} per period\n"
        analysis += f"R-squared: {trend.r_squared:.3f}\n"
        analysis += f"Sustained: {'Yes' if trend.is_sustained else 'No'}\n"

        if trend.reversal_detected:
            analysis += f"Trend Reversal Detected: Yes (confidence: {trend.reversal_confidence:.1%})\n"

        if trend.acceleration_detected:
            analysis += f"Acceleration Detected: Yes (magnitude: {trend.acceleration_magnitude:.4f})\n"

        # Add values
        analysis += f"\nValues: {[f'{v:,.2f}' for v in metric.values]}\n"

        return analysis

    def _r_squared_to_p_value(self, r_squared: float, n: int) -> float:
        """Convert R-squared to approximate p-value."""
        if n < 3:
            return 1.0

        # F-statistic for regression
        f_stat = (r_squared / (1 - r_squared)) * (n - 2) if r_squared < 1 else float('inf')

        # Approximate p-value
        if f_stat >= 10:
            return 0.001
        elif f_stat >= 5:
            return 0.01
        elif f_stat >= 3:
            return 0.05
        elif f_stat >= 2:
            return 0.10
        else:
            return 0.5

    def _apply_bh_correction(self, insights: List[Insight], alpha: float) -> List[Insight]:
        """
        Apply Benjamini-Hochberg correction for multiple comparisons.
        """
        if not insights:
            return insights

        # Sort by p-value
        sorted_insights = sorted(insights, key=lambda i: i.p_value or 1.0)

        # Apply correction
        m = len(sorted_insights)
        for i, insight in enumerate(sorted_insights):
            if insight.p_value is not None:
                corrected_p = insight.p_value * m / (i + 1)
                corrected_p = min(1.0, corrected_p)
                insight.p_value_corrected = corrected_p

        # Filter by corrected p-value
        significant_insights = [
            i for i in sorted_insights
            if i.p_value_corrected is not None and i.p_value_corrected < alpha
        ]

        return significant_insights

    async def rank_insights(
        self,
        insights: List[Insight]
    ) -> List[Insight]:
        """
        Ranks insights using the Intelligence Scoring Framework.
        """
        # Insights are already scored, just sort by priority
        ranked = sorted(
            insights,
            key=lambda i: i.scores.priority if i.scores else 0,
            reverse=True
        )
        return ranked
