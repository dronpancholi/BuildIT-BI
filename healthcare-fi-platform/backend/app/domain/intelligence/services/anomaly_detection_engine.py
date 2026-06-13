"""
Anomaly Detection Engine.
Implements multiple statistical anomaly detection algorithms.
"""
import uuid
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from ..entities import (
    Anomaly,
    IntelligenceScores,
)
from app.domain.intelligence.value_objects import (
    AnomalyType,
    AnomalySeverity,
    AnomalyCategory,
    AnomalyStatus,
    DetectionMethod,
    BaselineType,
    ArtifactStatus,
    ArtifactType,
    GenerationSource,
    PeriodType,
    ScopeType,
)
from .scoring import IntelligenceScoreCalculator, ScoringContext


@dataclass
class AnomalyDetectionOptions:
    methods_to_run: List[DetectionMethod] = field(default_factory=lambda: [
        DetectionMethod.Z_SCORE,
        DetectionMethod.IQR,
        DetectionMethod.EWMA,
    ])
    z_score_threshold: float = 3.0
    iqr_multiplier: float = 1.5
    ewma_lambda: float = 0.3
    ewma_control_limit: float = 3.0
    min_confidence: float = 0.70
    max_anomalies_per_run: int = 50


@dataclass
class AnomalyPoint:
    """A single detected anomaly point."""
    index: int
    timestamp: Optional[datetime]
    value: float
    expected_value: float
    deviation: float
    z_score: Optional[float]
    method: str
    confidence: float = 0.0
    severity: AnomalySeverity = AnomalySeverity.MEDIUM


@dataclass
class TimeSeriesData:
    """Time series data for anomaly detection."""
    timestamps: List[datetime]
    values: List[float]
    metric_id: uuid.UUID
    metric_code: str
    scope_id: Optional[uuid.UUID] = None


class StatisticalAnomalyDetector:
    """
    Implements statistical anomaly detection methods.
    """

    def __init__(self, score_calculator: IntelligenceScoreCalculator):
        self.score_calculator = score_calculator

    async def detect_z_score_anomalies(
        self,
        data: TimeSeriesData,
        threshold: float = 3.0
    ) -> List[AnomalyPoint]:
        """
        Simple z-score detection.
        z = (x - mean) / std_dev
        """
        if len(data.values) < 3:
            return []

        mean = statistics.mean(data.values)
        std_dev = statistics.stdev(data.values) if len(data.values) > 1 else 0.0

        if std_dev == 0:
            return []

        anomalies = []
        for i, value in enumerate(data.values):
            z_score = (value - mean) / std_dev
            if abs(z_score) > threshold:
                anomaly = AnomalyPoint(
                    index=i,
                    timestamp=data.timestamps[i] if i < len(data.timestamps) else None,
                    value=value,
                    expected_value=mean,
                    deviation=value - mean,
                    z_score=z_score,
                    method="z_score",
                    confidence=self._z_score_to_confidence(z_score),
                    severity=self._calculate_severity(abs(z_score), threshold),
                )
                anomalies.append(anomaly)

        return anomalies

    async def detect_iqr_anomalies(
        self,
        data: TimeSeriesData,
        k: float = 1.5
    ) -> List[AnomalyPoint]:
        """
        Interquartile range method.
        Anomaly if value < Q1 - k×IQR or value > Q3 + k×IQR
        """
        if len(data.values) < 4:
            return []

        sorted_values = sorted(data.values)
        n = len(sorted_values)

        q1 = sorted_values[n // 4]
        q3 = sorted_values[3 * n // 4]
        iqr = q3 - q1

        lower_bound = q1 - k * iqr
        upper_bound = q3 + k * iqr

        mean = statistics.mean(data.values)
        anomalies = []

        for i, value in enumerate(data.values):
            if value < lower_bound or value > upper_bound:
                z_score = (value - mean) / (iqr / 1.35) if iqr > 0 else 0
                anomaly = AnomalyPoint(
                    index=i,
                    timestamp=data.timestamps[i] if i < len(data.timestamps) else None,
                    value=value,
                    expected_value=mean,
                    deviation=value - mean,
                    z_score=z_score,
                    method="iqr",
                    confidence=self._iqr_to_confidence(value, q1, q3, iqr),
                    severity=self._calculate_severity_from_bounds(value, lower_bound, upper_bound),
                )
                anomalies.append(anomaly)

        return anomalies

    async def detect_ewma_anomalies(
        self,
        data: TimeSeriesData,
        lambda_: float = 0.3,
        k: float = 3.0
    ) -> List[AnomalyPoint]:
        """
        Exponentially Weighted Moving Average.
        Detects sustained shifts, not just point anomalies.

        EWM_t = lambda × x_t + (1-lambda) × EWM_{t-1}
        Control limit = EWM_mean ± k × sigma_EWM
        """
        if len(data.values) < 3:
            return []

        # Calculate EWMA
        ewma = [data.values[0]]
        for i in range(1, len(data.values)):
            ewma_t = lambda_ * data.values[i] + (1 - lambda_) * ewma[-1]
            ewma.append(ewma_t)

        # Calculate sigma (using exponentially weighted variance)
        ewma_mean = statistics.mean(ewma)
        ewma_var = sum((x - ewma_mean) ** 2 for x in ewma) / len(ewma)
        sigma_ewma = math.sqrt(ewma_var)

        # Control limits
        ucl = ewma_mean + k * sigma_ewma
        lcl = ewma_mean - k * sigma_ewma

        anomalies = []
        for i, value in enumerate(data.values):
            if value > ucl or value < lcl:
                deviation = value - ewma[i]
                z_score = deviation / sigma_ewma if sigma_ewma > 0 else 0

                anomaly = AnomalyPoint(
                    index=i,
                    timestamp=data.timestamps[i] if i < len(data.timestamps) else None,
                    value=value,
                    expected_value=ewma[i],
                    deviation=deviation,
                    z_score=z_score,
                    method="ewma",
                    confidence=self._ewma_to_confidence(deviation, sigma_ewma),
                    severity=self._calculate_severity_from_bounds(value, lcl, ucl),
                )
                anomalies.append(anomaly)

        return anomalies

    async def detect_cusum_anomalies(
        self,
        data: TimeSeriesData,
        target: Optional[float] = None,
        k: float = 0.5,
        h: float = 5.0
    ) -> List[AnomalyPoint]:
        """
        Cumulative Sum (CUSUM) detection.
        Detects sustained upward or downward shifts.

        S_t = max(0, S_{t-1} + (x_t - target - k))
        CUSUM alarm when S_t > h
        """
        if len(data.values) < 3:
            return []

        if target is None:
            target = statistics.mean(data.values)

        # Initialize CUSUM
        s_pos = [0.0]  # Positive shift
        s_neg = [0.0]  # Negative shift

        anomalies = []
        for i, value in enumerate(data.values):
            # Update CUSUM
            s_pos_new = max(0, s_pos[-1] + (value - target - k))
            s_neg_new = max(0, s_neg[-1] + (target - value - k))

            s_pos.append(s_pos_new)
            s_neg.append(s_neg_new)

            # Check for alarm
            if s_pos_new > h or s_neg_new > h:
                deviation = value - target
                z_score = deviation / (statistics.stdev(data.values) if len(data.values) > 1 else 1)

                anomaly = AnomalyPoint(
                    index=i,
                    timestamp=data.timestamps[i] if i < len(data.timestamps) else None,
                    value=value,
                    expected_value=target,
                    deviation=deviation,
                    z_score=z_score,
                    method="cusum",
                    confidence=self._cusum_to_confidence(s_pos_new, s_neg_new, h),
                    severity=self._calculate_severity_from_cusum(s_pos_new, s_neg_new, h),
                )
                anomalies.append(anomaly)

        return anomalies

    def _z_score_to_confidence(self, z_score: float) -> float:
        """Convert z-score to confidence level."""
        abs_z = abs(z_score)
        if abs_z >= 4.0:
            return 0.99
        elif abs_z >= 3.0:
            return 0.95
        elif abs_z >= 2.5:
            return 0.90
        elif abs_z >= 2.0:
            return 0.80
        else:
            return 0.50

    def _iqr_to_confidence(self, value: float, q1: float, q3: float, iqr: float) -> float:
        """Convert IQR position to confidence."""
        if iqr == 0:
            return 0.5

        distance_from_bounds = min(
            abs(value - q1),
            abs(value - q3)
        )
        normalized_distance = distance_from_bounds / iqr

        if normalized_distance >= 2.0:
            return 0.95
        elif normalized_distance >= 1.5:
            return 0.85
        elif normalized_distance >= 1.0:
            return 0.75
        else:
            return 0.50

    def _ewma_to_confidence(self, deviation: float, sigma: float) -> float:
        """Convert EWMA deviation to confidence."""
        if sigma == 0:
            return 0.5

        abs_deviation = abs(deviation)
        normalized = abs_deviation / sigma

        if normalized >= 4.0:
            return 0.99
        elif normalized >= 3.0:
            return 0.95
        elif normalized >= 2.0:
            return 0.85
        else:
            return 0.50

    def _cusum_to_confidence(self, s_pos: float, s_neg: float, h: float) -> float:
        """Convert CUSUM statistic to confidence."""
        max_s = max(s_pos, s_neg)
        ratio = max_s / h if h > 0 else 0

        if ratio >= 2.0:
            return 0.99
        elif ratio >= 1.5:
            return 0.95
        elif ratio >= 1.0:
            return 0.90
        else:
            return 0.50

    def _calculate_severity(self, abs_z_score: float, threshold: float) -> AnomalySeverity:
        """Calculate severity from z-score."""
        ratio = abs_z_score / threshold
        if ratio >= 2.0:
            return AnomalySeverity.CRITICAL
        elif ratio >= 1.5:
            return AnomalySeverity.HIGH
        elif ratio >= 1.0:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

    def _calculate_severity_from_bounds(self, value: float, lower: float, upper: float) -> AnomalySeverity:
        """Calculate severity from position relative to bounds."""
        if value < lower:
            distance = lower - value
        else:
            distance = value - upper

        range_size = upper - lower
        if range_size == 0:
            return AnomalySeverity.MEDIUM

        normalized_distance = distance / range_size

        if normalized_distance >= 2.0:
            return AnomalySeverity.CRITICAL
        elif normalized_distance >= 1.0:
            return AnomalySeverity.HIGH
        elif normalized_distance >= 0.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

    def _calculate_severity_from_cusum(self, s_pos: float, s_neg: float, h: float) -> AnomalySeverity:
        """Calculate severity from CUSUM statistic."""
        max_s = max(s_pos, s_neg)
        ratio = max_s / h if h > 0 else 0

        if ratio >= 2.0:
            return AnomalySeverity.CRITICAL
        elif ratio >= 1.5:
            return AnomalySeverity.HIGH
        elif ratio >= 1.0:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW


class ForecastDeviationDetector:
    """
    Compares actual values against forecasts.
    """

    async def detect_forecast_deviations(
        self,
        data: TimeSeriesData,
        forecast_values: List[float],
        tolerance_percent: float = 10.0
    ) -> List[AnomalyPoint]:
        """
        Compare actual values against forecasts.
        Flag deviations beyond tolerance.
        """
        if len(data.values) != len(forecast_values):
            return []

        anomalies = []
        for i, (actual, forecast) in enumerate(zip(data.values, forecast_values)):
            if forecast == 0:
                continue

            deviation_percent = ((actual - forecast) / forecast) * 100

            if abs(deviation_percent) > tolerance_percent:
                z_score = deviation_percent / tolerance_percent  # Normalized deviation
                anomaly = AnomalyPoint(
                    index=i,
                    timestamp=data.timestamps[i] if i < len(data.timestamps) else None,
                    value=actual,
                    expected_value=forecast,
                    deviation=actual - forecast,
                    z_score=z_score,
                    method="forecast_deviation",
                    confidence=min(0.95, 0.7 + abs(deviation_percent) / 100),
                    severity=self._calculate_severity_from_deviation(deviation_percent),
                )
                anomalies.append(anomaly)

        return anomalies

    def _calculate_severity_from_deviation(self, deviation_percent: float) -> AnomalySeverity:
        """Calculate severity from deviation percentage."""
        abs_dev = abs(deviation_percent)
        if abs_dev >= 50:
            return AnomalySeverity.CRITICAL
        elif abs_dev >= 30:
            return AnomalySeverity.HIGH
        elif abs_dev >= 20:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW


class AnomalyDetectionEngine:
    """
    Enterprise-grade anomaly detection with multiple algorithms.
    """

    def __init__(self):
        self.score_calculator = IntelligenceScoreCalculator()
        self.statistical_detector = StatisticalAnomalyDetector(self.score_calculator)
        self.forecast_detector = ForecastDeviationDetector()

    async def detect_anomalies(
        self,
        data: TimeSeriesData,
        scope_id: Optional[uuid.UUID] = None,
        options: AnomalyDetectionOptions = AnomalyDetectionOptions()
    ) -> List[Anomaly]:
        """
        Run all configured detection methods.
        Returns deduplicated anomalies with merged evidence.
        """
        all_anomalies = []

        # Run each configured method
        for method in options.methods_to_run:
            if method == DetectionMethod.Z_SCORE:
                z_anomalies = await self.statistical_detector.detect_z_score_anomalies(
                    data, options.z_score_threshold
                )
                all_anomalies.extend(z_anomalies)

            elif method == DetectionMethod.IQR:
                iqr_anomalies = await self.statistical_detector.detect_iqr_anomalies(
                    data, options.iqr_multiplier
                )
                all_anomalies.extend(iqr_anomalies)

            elif method == DetectionMethod.EWMA:
                ewma_anomalies = await self.statistical_detector.detect_ewma_anomalies(
                    data, options.ewma_lambda, options.ewma_control_limit
                )
                all_anomalies.extend(ewma_anomalies)

            elif method == DetectionMethod.CUSUM:
                cusum_anomalies = await self.statistical_detector.detect_cusum_anomalies(data)
                all_anomalies.extend(cusum_anomalies)

        # Deduplicate anomalies (same timestamp)
        deduplicated = self._deduplicate_anomalies(all_anomalies)

        # Convert to Anomaly entities
        anomaly_entities = []
        for point in deduplicated:
            if point.confidence >= options.min_confidence:
                anomaly = await self._create_anomaly_entity(
                    data=data,
                    point=point,
                    scope_id=scope_id
                )
                anomaly_entities.append(anomaly)

        # Limit number of anomalies
        anomaly_entities = anomaly_entities[:options.max_anomalies_per_run]

        return anomaly_entities

    async def detect_statistical_anomalies(
        self,
        data: TimeSeriesData,
        scope_id: Optional[uuid.UUID] = None,
        options: AnomalyDetectionOptions = AnomalyDetectionOptions()
    ) -> List[Anomaly]:
        """
        Statistical anomaly detection using multiple methods.
        Methods: Z-score, IQR, EWMA, CUSUM
        """
        return await self.detect_anomalies(
            data=data,
            scope_id=scope_id,
            options=AnomalyDetectionOptions(
                methods_to_run=[
                    DetectionMethod.Z_SCORE,
                    DetectionMethod.IQR,
                    DetectionMethod.EWMA,
                    DetectionMethod.CUSUM,
                ],
                z_score_threshold=options.z_score_threshold,
                iqr_multiplier=options.iqr_multiplier,
                ewma_lambda=options.ewma_lambda,
                ewma_control_limit=options.ewma_control_limit,
                min_confidence=options.min_confidence,
            )
        )

    async def detect_forecast_deviation_anomalies(
        self,
        data: TimeSeriesData,
        forecast_values: List[float],
        scope_id: Optional[uuid.UUID] = None,
        tolerance_percent: float = 10.0
    ) -> List[Anomaly]:
        """
        Compare actual values against forecasts.
        Flag deviations beyond tolerance.
        """
        points = await self.forecast_detector.detect_forecast_deviations(
            data=data,
            forecast_values=forecast_values,
            tolerance_percent=tolerance_percent
        )

        anomalies = []
        for point in points:
            anomaly = await self._create_anomaly_entity(
                data=data,
                point=point,
                scope_id=scope_id
            )
            anomalies.append(anomaly)

        return anomalies

    def _deduplicate_anomalies(self, anomalies: List[AnomalyPoint]) -> List[AnomalyPoint]:
        """
        Deduplicate anomalies at the same timestamp.
        Keep the one with highest confidence.
        """
        if not anomalies:
            return []

        # Group by timestamp
        timestamp_map: Dict[int, AnomalyPoint] = {}
        for anomaly in anomalies:
            key = anomaly.index
            if key not in timestamp_map or anomaly.confidence > timestamp_map[key].confidence:
                timestamp_map[key] = anomaly

        # Sort by index
        deduplicated = sorted(timestamp_map.values(), key=lambda a: a.index)
        return deduplicated

    async def _create_anomaly_entity(
        self,
        data: TimeSeriesData,
        point: AnomalyPoint,
        scope_id: Optional[uuid.UUID] = None
    ) -> Anomaly:
        """
        Create an Anomaly entity from an AnomalyPoint.
        """
        # Determine anomaly type based on direction
        if point.value > point.expected_value:
            anomaly_type = AnomalyType.SPIKE
        elif point.value < point.expected_value:
            anomaly_type = AnomalyType.DROP
        else:
            anomaly_type = AnomalyType.FLATLINE

        # Calculate deviation percent
        deviation_percent = (
            ((point.value - point.expected_value) / point.expected_value * 100)
            if point.expected_value != 0 else 0
        )

        # Create anomaly
        anomaly = Anomaly(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # Will be set by caller
            artifact_type=ArtifactType.ANOMALY,
            anomaly_type=anomaly_type,
            category=AnomalyCategory.REVENUE,  # Default, should be determined by context
            severity=point.severity,
            detection_method=DetectionMethod(point.method) if point.method in [m.value for m in DetectionMethod] else DetectionMethod.Z_SCORE,
            detection_algorithm=point.method,
            title=f"Anomaly detected: {data.metric_code}",
            description=self._generate_anomaly_description(data, point),
            detailed_explanation=self._generate_detailed_explanation(data, point),
            metric_id=data.metric_id,
            metric_code=data.metric_code,
            observed_value=point.value,
            expected_value=point.expected_value,
            deviation_absolute=point.deviation,
            deviation_percent=deviation_percent,
            z_score=point.z_score,
            p_value=self._z_score_to_p_value(point.z_score) if point.z_score else None,
            baseline_value=point.expected_value,
            baseline_type=BaselineType.HISTORICAL_MEAN,
            anomaly_status=AnomalyStatus.DETECTED,
            scope_type=ScopeType.TENANT,
            scope_id=scope_id,
            status=ArtifactStatus.DISCOVERED,
            version=1,
        )

        # Calculate scores
        scoring_context = ScoringContext(
            tenant_id=anomaly.tenant_id,
            artifact_type=ArtifactType.ANOMALY,
            artifact_data={
                "severity": point.severity.value,
                "confidence": point.confidence,
                "p_value": anomaly.p_value,
                "dollar_impact": abs(point.deviation),
                "is_persistent": False,
                "duration_periods": 1,
            }
        )
        scores = await self.score_calculator.calculate_scores(
            ArtifactType.ANOMALY,
            scoring_context.artifact_data,
            scoring_context
        )
        anomaly.scores = scores

        return anomaly

    def _generate_anomaly_description(self, data: TimeSeriesData, point: AnomalyPoint) -> str:
        """Generate a description for the anomaly."""
        direction = "above" if point.value > point.expected_value else "below"
        return (
            f"The value {point.value:,.2f} for {data.metric_code} was {direction} "
            f"the expected range, with a deviation of {abs(point.deviation):,.2f} "
            f"({point.method} method, z-score: {point.z_score:.2f})"
        )

    def _generate_detailed_explanation(self, data: TimeSeriesData, point: AnomalyPoint) -> str:
        """Generate a detailed technical explanation."""
        return (
            f"Statistical anomaly detected using {point.method} algorithm.\n"
            f"Observed value: {point.value:,.2f}\n"
            f"Expected value: {point.expected_value:,.2f}\n"
            f"Deviation: {point.deviation:,.2f} ({point.deviation / point.expected_value * 100 if point.expected_value else 0:.1f}%)\n"
            f"Z-score: {point.z_score:.2f}\n"
            f"Confidence: {point.confidence:.1%}\n"
            f"Severity: {point.severity.value}"
        )

    def _z_score_to_p_value(self, z_score: float) -> float:
        """Convert z-score to approximate p-value."""
        if z_score is None:
            return 1.0

        abs_z = abs(z_score)
        # Approximate p-value using normal distribution
        if abs_z >= 3.5:
            return 0.0002
        elif abs_z >= 3.0:
            return 0.0013
        elif abs_z >= 2.5:
            return 0.0124
        elif abs_z >= 2.0:
            return 0.0455
        elif abs_z >= 1.5:
            return 0.1336
        else:
            return 0.5
