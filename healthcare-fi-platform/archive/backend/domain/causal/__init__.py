"""
Causal Impact Engine Domain.
Multiple causal inference methods for decision outcome analysis.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from app.domain.decision.value_objects import CausalMethod, ConfoundingFactor


@dataclass(kw_only=True)
class BeforeAfterResult:
    treatment_entity_id: uuid.UUID
    control_entity_id: Optional[uuid.UUID] = None
    intervention_date: date = field(default_factory=date.today)
    pre_period_mean: float = 0.0
    post_period_mean: float = 0.0
    effect_size: float = 0.0
    confidence_interval: tuple = (0.0, 0.0)
    p_value: float = 1.0
    is_significant: bool = False


@dataclass(kw_only=True)
class ITSResult:
    entity_id: uuid.UUID
    intervention_date: date = field(default_factory=date.today)
    level_change: float = 0.0
    slope_change: float = 0.0
    trend_pre: float = 0.0
    trend_post: float = 0.0
    p_value: float = 1.0
    is_significant: bool = False


@dataclass(kw_only=True)
class DiffInDiffResult:
    treatment_entity_id: uuid.UUID
    control_entity_id: uuid.UUID
    intervention_date: date = field(default_factory=date.today)
    did_estimate: float = 0.0
    se: float = 0.0
    p_value: float = 1.0
    confidence_interval: tuple = (0.0, 0.0)
    is_significant: bool = False


@dataclass(kw_only=True)
class CounterfactualEstimate:
    entity_id: uuid.UUID
    metric_codes: List[str] = field(default_factory=list)
    counterfactual_values: Dict[str, float] = field(default_factory=dict)
    actual_values: Dict[str, float] = field(default_factory=dict)
    estimated_effect: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0


class ICausalImpactEngine:
    async def analyze(self, outcome_id, tenant_id, preferred_method=None):
        pass
    async def before_after_analysis(self, treatment_entity_id, control_entity_id,
                                     intervention_date, metric_codes,
                                     pre_period_days, post_period_days):
        pass
    async def interrupted_time_series(self, entity_id, metric_codes,
                                       intervention_date, control_entity_id=None):
        pass
    async def diff_in_diff(self, treatment_entity_id, control_entity_id,
                            intervention_date, metric_codes):
        pass
    async def get_confounding_factors(self, entity_id, outcome_metric, intervention_date):
        pass
    async def estimate_counterfactual(self, entity_id, metric_codes, intervention_date):
        pass
