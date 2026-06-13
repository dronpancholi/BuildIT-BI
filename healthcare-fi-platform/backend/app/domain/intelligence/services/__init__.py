"""
Intelligence Domain Services.
"""
from .scoring import IntelligenceScoreCalculator, ScoringContext, score_calculator
from .root_cause_engine import (
    RootCauseEngine,
    VarianceDecompositionAnalyzer,
    RootCauseOptions,
    RootCauseAnalysisMethod,
    ComputationScope,
    TimePeriod,
    MetricData,
    SegmentData,
)
from .anomaly_detection_engine import (
    AnomalyDetectionEngine,
    StatisticalAnomalyDetector,
    ForecastDeviationDetector,
    AnomalyDetectionOptions,
    AnomalyPoint,
    TimeSeriesData,
)
from .insight_discovery_engine import (
    InsightDiscoveryEngine,
    TrendAnalyzer,
    CorrelationAnalyzer,
    SegmentAnalyzer,
    DiscoveryOptions,
    TrendDetectionResult,
    CorrelationDiscoveryResult,
    SegmentPerformanceResult,
    MetricTimeSeries,
)
from .opportunity_engine import (
    OpportunityDiscoveryEngine,
    OpportunityDiscoveryOptions,
    OpportunityData,
)
from .recommendation_engine import (
    RecommendationEngine,
    RecommendationGenerationOptions,
)

__all__ = [
    # Scoring
    "IntelligenceScoreCalculator",
    "ScoringContext",
    "score_calculator",
    # Root Cause Analysis
    "RootCauseEngine",
    "VarianceDecompositionAnalyzer",
    "RootCauseOptions",
    "RootCauseAnalysisMethod",
    "ComputationScope",
    "TimePeriod",
    "MetricData",
    "SegmentData",
    # Anomaly Detection
    "AnomalyDetectionEngine",
    "StatisticalAnomalyDetector",
    "ForecastDeviationDetector",
    "AnomalyDetectionOptions",
    "AnomalyPoint",
    "TimeSeriesData",
    # Insight Discovery
    "InsightDiscoveryEngine",
    "TrendAnalyzer",
    "CorrelationAnalyzer",
    "SegmentAnalyzer",
    "DiscoveryOptions",
    "TrendDetectionResult",
    "CorrelationDiscoveryResult",
    "SegmentPerformanceResult",
    "MetricTimeSeries",
    # Opportunity Discovery
    "OpportunityDiscoveryEngine",
    "OpportunityDiscoveryOptions",
    "OpportunityData",
    # Recommendation
    "RecommendationEngine",
    "RecommendationGenerationOptions",
]
