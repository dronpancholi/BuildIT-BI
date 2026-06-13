from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from enum import Enum
from typing import Dict, List, Optional, Tuple

getcontext().prec = 28


class ScenarioStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ScenarioType(Enum):
    BASE = "base"
    BEST_CASE = "best_case"
    WORST_CASE = "worst_case"
    STRESS_TEST = "stress_test"
    CUSTOM = "custom"


class TreeNodeType(Enum):
    METRIC = "metric"
    DRIVER = "driver"
    CALCULATION = "calculation"
    ASSUMPTION = "assumption"
    CONSTRAINT = "constraint"


class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Scenario:
    id: uuid.UUID
    tenant_id: str
    name: str
    description: str
    type: ScenarioType
    status: ScenarioStatus
    assumptions: List[Dict]
    results: Dict = field(default_factory=dict)
    created_by: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ScenarioComparison:
    id: uuid.UUID
    scenario_ids: List[uuid.UUID]
    metrics: List[str]
    summary: Dict
    detailed: List[Dict]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DriverTreeNode:
    id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    name: str
    node_type: TreeNodeType
    metric_id: Optional[uuid.UUID]
    formula: Optional[str]
    weight: float
    value: Optional[Decimal] = None
    children: List[uuid.UUID] = field(default_factory=list)
    level: int = 0


@dataclass
class DriverTree:
    id: uuid.UUID
    tenant_id: str
    name: str
    description: str
    root_node_id: uuid.UUID
    nodes: List[DriverTreeNode]
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MonteCarloResult:
    id: uuid.UUID
    scenario_id: uuid.UUID
    simulations: int
    distribution: str
    mean: Decimal
    median: Decimal
    std_dev: Decimal
    var_95: Decimal
    var_99: Decimal
    percentiles: Dict[str, Decimal]
    histogram: List[Dict]
    convergence: Dict
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WhatIfAnalysis:
    id: uuid.UUID
    tenant_id: str
    name: str
    base_values: Dict
    changes: List[Dict]
    results: List[Dict]
    impact_summary: Dict = field(default_factory=dict)
    sensitivity: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SensitivityResult:
    variable: str
    elasticity: float
    rank: int
    range: Tuple[Decimal, Decimal]


@dataclass
class RiskAssessment:
    id: uuid.UUID
    scenario_id: uuid.UUID
    risks: List[Dict]
    overall_score: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class StrategicPlanningService:
    def __init__(self) -> None:
        self._scenarios: Dict[str, Dict[uuid.UUID, Scenario]] = {}
        self._comparisons: Dict[str, List[ScenarioComparison]] = {}
        self._trees: Dict[str, Dict[uuid.UUID, DriverTree]] = {}
        self._what_ifs: Dict[str, Dict[uuid.UUID, WhatIfAnalysis]] = {}
        self._monte_carlo_results: Dict[str, List[MonteCarloResult]] = {}
        self._risk_assessments: Dict[str, List[RiskAssessment]] = {}

    def create_scenario(
        self,
        tenant_id: str,
        name: str,
        description: str,
        type: ScenarioType,
        assumptions: List[Dict],
        created_by: uuid.UUID,
    ) -> Scenario:
        scenario = Scenario(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            type=type,
            status=ScenarioStatus.DRAFT,
            assumptions=assumptions,
            created_by=created_by,
        )
        self._scenarios.setdefault(tenant_id, {})[scenario.id] = scenario
        return scenario

    def get_scenario(self, tenant_id: str, scenario_id: uuid.UUID) -> Optional[Scenario]:
        return self._scenarios.get(tenant_id, {}).get(scenario_id)

    def run_scenario(
        self, tenant_id: str, scenario_id: uuid.UUID, data: Dict
    ) -> Scenario:
        scenario = self.get_scenario(tenant_id, scenario_id)
        if scenario is None:
            raise ValueError(f"Scenario {scenario_id} not found for tenant {tenant_id}")

        results: Dict = {}
        for assumption in scenario.assumptions:
            name = assumption["name"]
            value = assumption["value"]
            range_min = assumption.get("range_min", value)
            range_max = assumption.get("range_max", value)

            if scenario.type == ScenarioType.BEST_CASE:
                computed = range_max
            elif scenario.type == ScenarioType.WORST_CASE:
                computed = range_min
            elif scenario.type == ScenarioType.STRESS_TEST:
                computed = range_min + (range_max - range_min) * 0.1
            else:
                computed = value

            base_data_value = data.get(name, computed)
            results[name] = {
                "assumed_value": computed,
                "actual_value": base_data_value,
                "variance": float(base_data_value) - float(computed),
            }

        total = sum(
            float(v.get("actual_value", v.get("assumed_value", 0)))
            for v in results.values()
        )
        results["total_impact"] = total

        scenario.results = results
        scenario.status = ScenarioStatus.ACTIVE
        scenario.updated_at = datetime.now(timezone.utc)
        return scenario

    def compare_scenarios(
        self, tenant_id: str, scenario_ids: List[uuid.UUID], metrics: List[str]
    ) -> ScenarioComparison:
        scenarios = []
        for sid in scenario_ids:
            scenario = self.get_scenario(tenant_id, sid)
            if scenario is None:
                raise ValueError(f"Scenario {sid} not found")
            scenarios.append(scenario)

        detailed: List[Dict] = []
        metric_values: Dict[str, List[float]] = {m: [] for m in metrics}

        for scenario in scenarios:
            entry: Dict = {
                "scenario_id": str(scenario.id),
                "scenario_name": scenario.name,
                "type": scenario.type.value,
                "metrics": {},
            }
            for metric in metrics:
                value = scenario.results.get(metric, {}).get(
                    "actual_value", scenario.results.get(metric, 0)
                )
                float_val = float(value) if value is not None else 0.0
                entry["metrics"][metric] = float_val
                metric_values[metric].append(float_val)
            detailed.append(entry)

        best_case_values: Dict[str, float] = {}
        worst_case_values: Dict[str, float] = {}
        deltas: Dict[str, float] = {}

        for metric in metrics:
            vals = metric_values[metric]
            if vals:
                best_case_values[metric] = max(vals)
                worst_case_values[metric] = min(vals)
                deltas[metric] = max(vals) - min(vals)
            else:
                best_case_values[metric] = 0.0
                worst_case_values[metric] = 0.0
                deltas[metric] = 0.0

        recommendation = "Scenarios show minimal variance; consider additional stress factors."
        if any(d > 1000 for d in deltas.values()):
            recommendation = (
                "Significant variance detected; recommend risk mitigation strategies."
            )
        elif any(d > 500 for d in deltas.values()):
            recommendation = (
                "Moderate variance; review assumptions and monitor key drivers."
            )

        summary: Dict = {
            "best_case": best_case_values,
            "worst_case": worst_case_values,
            "delta": deltas,
            "recommendation": recommendation,
        }

        comparison = ScenarioComparison(
            id=uuid.uuid4(),
            scenario_ids=scenario_ids,
            metrics=metrics,
            summary=summary,
            detailed=detailed,
        )
        self._comparisons.setdefault(tenant_id, []).append(comparison)
        return comparison

    def build_driver_tree(
        self,
        tenant_id: str,
        name: str,
        description: str,
        metrics: List[Dict],
    ) -> DriverTree:
        root_id = uuid.uuid4()
        all_nodes: List[DriverTreeNode] = []

        root = DriverTreeNode(
            id=root_id,
            parent_id=None,
            name="Root",
            node_type=TreeNodeType.METRIC,
            metric_id=None,
            formula=None,
            weight=1.0,
            level=0,
        )
        all_nodes.append(root)

        for metric in metrics:
            metric_node_id = uuid.uuid4()
            metric_node = DriverTreeNode(
                id=metric_node_id,
                parent_id=root_id,
                name=metric.get("name", "Metric"),
                node_type=TreeNodeType.METRIC,
                metric_id=metric.get("metric_id"),
                formula=None,
                weight=metric.get("weight", 1.0),
                level=1,
            )
            all_nodes.append(metric_node)
            root.children.append(metric_node_id)

            for driver in metric.get("drivers", []):
                driver_id = uuid.uuid4()
                driver_node = DriverTreeNode(
                    id=driver_id,
                    parent_id=metric_node_id,
                    name=driver.get("name", "Driver"),
                    node_type=TreeNodeType.DRIVER,
                    metric_id=driver.get("metric_id"),
                    formula=driver.get("formula"),
                    weight=driver.get("weight", 1.0),
                    level=2,
                )
                all_nodes.append(driver_node)
                metric_node.children.append(driver_id)

                for sub in driver.get("sub_drivers", []):
                    sub_id = uuid.uuid4()
                    sub_node = DriverTreeNode(
                        id=sub_id,
                        parent_id=driver_id,
                        name=sub.get("name", "SubDriver"),
                        node_type=TreeNodeType.DRIVER,
                        metric_id=sub.get("metric_id"),
                        formula=sub.get("formula"),
                        weight=sub.get("weight", 1.0),
                        level=3,
                    )
                    all_nodes.append(sub_node)
                    driver_node.children.append(sub_id)

        tree = DriverTree(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            root_node_id=root_id,
            nodes=all_nodes,
        )
        self._trees.setdefault(tenant_id, {})[tree.id] = tree
        return tree

    def calculate_driver_values(
        self, tree_id: uuid.UUID, actual_data: Dict
    ) -> DriverTree:
        tree = None
        for tenant_trees in self._trees.values():
            if tree_id in tenant_trees:
                tree = tenant_trees[tree_id]
                break

        if tree is None:
            raise ValueError(f"DriverTree {tree_id} not found")

        node_map: Dict[uuid.UUID, DriverTreeNode] = {
            node.id: node for node in tree.nodes
        }

        sorted_nodes = sorted(tree.nodes, key=lambda n: n.level, reverse=True)

        for node in sorted_nodes:
            if node.node_type in (TreeNodeType.ASSUMPTION, TreeNodeType.CONSTRAINT):
                node.value = Decimal(
                    str(actual_data.get(node.name, 0))
                )
            elif not node.children:
                node.value = Decimal(str(actual_data.get(node.name, 0)))
            elif node.formula:
                try:
                    local_vars: Dict[str, Decimal] = {}
                    for child_id in node.children:
                        child = node_map[child_id]
                        if child.value is not None:
                            safe_name = child.name.replace(" ", "_").lower()
                            local_vars[safe_name] = child.value
                    result = eval(node.formula, {"__builtins__": {}}, local_vars)
                    node.value = Decimal(str(result))
                except Exception:
                    child_values = [
                        node_map[cid].value
                        for cid in node.children
                        if node_map[cid].value is not None
                    ]
                    node.value = (
                        sum(child_values) if child_values else Decimal("0")
                    )
            else:
                total = Decimal("0")
                for child_id in node.children:
                    child = node_map[child_id]
                    if child.value is not None:
                        total += child.value * Decimal(str(child.weight))
                node.value = total

        return tree

    def run_monte_carlo(
        self,
        tenant_id: str,
        scenario_id: uuid.UUID,
        variable_distributions: Dict[str, Dict],
        simulations: int,
    ) -> MonteCarloResult:
        scenario = self.get_scenario(tenant_id, scenario_id)
        if scenario is None:
            raise ValueError(f"Scenario {scenario_id} not found")

        base_values: Dict[str, float] = {}
        for assumption in scenario.assumptions:
            base_values[assumption["name"]] = float(assumption["value"])
        for key, val in variable_distributions.items():
            if "base_value" in val:
                base_values[key] = float(val["base_value"])

        outcomes: List[float] = []

        for _ in range(simulations):
            sampled: Dict[str, float] = {}
            for var_name, dist in variable_distributions.items():
                dist_type = dist.get("type", "normal")
                if dist_type == "normal":
                    mean = dist.get("mean", base_values.get(var_name, 0))
                    std = dist.get("std", abs(mean) * 0.1)
                    sampled[var_name] = random.gauss(mean, std)
                elif dist_type == "lognormal":
                    mean = dist.get("mean", base_values.get(var_name, 1))
                    std = dist.get("std", abs(mean) * 0.1)
                    sigma = math.sqrt(
                        math.log(1 + (std / mean) ** 2)
                    ) if mean > 0 else 0.1
                    mu = math.log(mean) - 0.5 * sigma**2 if mean > 0 else 0
                    sampled[var_name] = random.lognormvariate(mu, sigma)
                elif dist_type == "uniform":
                    low = dist.get("low", base_values.get(var_name, 0) * 0.8)
                    high = dist.get("high", base_values.get(var_name, 0) * 1.2)
                    sampled[var_name] = random.uniform(low, high)
                elif dist_type == "triangular":
                    low = dist.get("low", base_values.get(var_name, 0) * 0.8)
                    mode = dist.get("mode", base_values.get(var_name, 0))
                    high = dist.get("high", base_values.get(var_name, 0) * 1.2)
                    sampled[var_name] = random.triangular(low, mode, high)
                else:
                    sampled[var_name] = base_values.get(var_name, 0)

            formula = variable_distributions.get(
                "_formula", {"expression": " * ".join(variable_distributions.keys())}
            )
            expression = formula.get("expression", "")

            result_val = 0.0
            if expression:
                try:
                    safe_ns: Dict = {k: v for k, v in sampled.items()}
                    result_val = float(eval(expression, {"__builtins__": {}}, safe_ns))
                except Exception:
                    result_val = sum(sampled.values())
            else:
                result_val = sum(sampled.values())

            outcomes.append(result_val)

        outcomes.sort()
        n = len(outcomes)
        mean_val = sum(outcomes) / n
        median_val = outcomes[n // 2] if n % 2 == 1 else (
            outcomes[n // 2 - 1] + outcomes[n // 2]
        ) / 2.0
        variance = sum((x - mean_val) ** 2 for x in outcomes) / (n - 1) if n > 1 else 0
        std_dev_val = math.sqrt(variance)

        var_95_idx = int(math.ceil(0.95 * n)) - 1
        var_99_idx = int(math.ceil(0.99 * n)) - 1
        var_95_val = outcomes[min(var_95_idx, n - 1)]
        var_99_val = outcomes[min(var_99_idx, n - 1)]

        percentile_keys = ["1", "5", "10", "25", "50", "75", "90", "95", "99"]
        percentiles: Dict[str, Decimal] = {}
        for pk in percentile_keys:
            idx = int(math.ceil(float(pk) / 100.0 * n)) - 1
            percentiles[pk] = Decimal(str(outcomes[min(idx, n - 1)]))

        min_val = outcomes[0]
        max_val = outcomes[-1]
        bin_count = 10
        bin_width = (max_val - min_val) / bin_count if max_val > min_val else 1.0
        histogram: List[Dict] = []
        for i in range(bin_count):
            bin_start = min_val + i * bin_width
            bin_end = bin_start + bin_width
            freq = sum(
                1 for x in outcomes if bin_start <= x < bin_end
            )
            if i == bin_count - 1:
                freq += sum(1 for x in outcomes if x == bin_end)
            histogram.append(
                {
                    "bin_start": round(bin_start, 4),
                    "bin_end": round(bin_end, 4),
                    "frequency": freq,
                }
            )

        standard_error = std_dev_val / math.sqrt(n) if n > 0 else 0
        confidence_bound = 1.96 * standard_error

        result = MonteCarloResult(
            id=uuid.uuid4(),
            scenario_id=scenario_id,
            simulations=simulations,
            distribution="mixed",
            mean=Decimal(str(round(mean_val, 4))),
            median=Decimal(str(round(median_val, 4))),
            std_dev=Decimal(str(round(std_dev_val, 4))),
            var_95=Decimal(str(round(var_95_val, 4))),
            var_99=Decimal(str(round(var_99_val, 4))),
            percentiles=percentiles,
            histogram=histogram,
            convergence={
                "standard_error": round(standard_error, 6),
                "confidence_bound": round(confidence_bound, 6),
            },
        )
        self._monte_carlo_results.setdefault(tenant_id, []).append(result)
        return result

    def create_what_if(
        self,
        tenant_id: str,
        name: str,
        base_values: Dict,
        changes: List[Dict],
    ) -> WhatIfAnalysis:
        processed_changes: List[Dict] = []
        for change in changes:
            var = change.get("variable", "")
            base = change.get("base_value", base_values.get(var, 0))
            new_val = change.get("new_value", base)
            unit = change.get("unit", "")
            processed_changes.append(
                {
                    "variable": var,
                    "base_value": base,
                    "new_value": new_val,
                    "unit": unit,
                }
            )

        what_if = WhatIfAnalysis(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=name,
            base_values=base_values,
            changes=processed_changes,
            results=[],
        )
        self._what_ifs.setdefault(tenant_id, {})[what_if.id] = what_if
        return what_if

    def run_what_if(
        self, tenant_id: str, what_if_id: uuid.UUID, data: Dict
    ) -> WhatIfAnalysis:
        what_if = self._what_ifs.get(tenant_id, {}).get(what_if_id)
        if what_if is None:
            raise ValueError(f"WhatIfAnalysis {what_if_id} not found")

        projected_values = dict(what_if.base_values)
        for change in what_if.changes:
            projected_values[change["variable"]] = change["new_value"]

        results: List[Dict] = []
        total_delta = 0.0

        for var_name, base_val in what_if.base_values.items():
            projected = projected_values.get(var_name, base_val)
            base_f = float(base_val)
            projected_f = float(projected)
            delta = projected_f - base_f
            delta_pct = (delta / base_f * 100) if base_f != 0 else 0.0

            total_delta += delta
            results.append(
                {
                    "metric": var_name,
                    "base": base_f,
                    "projected": projected_f,
                    "delta": round(delta, 4),
                    "delta_percentage": round(delta_pct, 4),
                    "driver_breakdown": {},
                }
            )

        impact_summary: Dict = {
            "total_delta": round(total_delta, 4),
            "num_variables_changed": len(what_if.changes),
            "direction": "positive" if total_delta > 0 else (
                "negative" if total_delta < 0 else "neutral"
            ),
        }

        sensitivity: List[Dict] = []
        for change in what_if.changes:
            var = change["variable"]
            base_f = float(change["base_value"])
            new_f = float(change["new_value"])
            if base_f != 0:
                elasticity = ((new_f - base_f) / base_f) * 100
            else:
                elasticity = 0.0
            sensitivity.append(
                {
                    "variable": var,
                    "sensitivity_percentage": round(elasticity, 4),
                }
            )

        what_if.results = results
        what_if.impact_summary = impact_summary
        what_if.sensitivity = sensitivity
        return what_if

    def sensitivity_analysis(
        self,
        tenant_id: str,
        scenario_id: uuid.UUID,
        base_values: Dict,
        variable_ranges: Dict[str, Tuple[Decimal, Decimal]],
        n_points: int,
    ) -> List[SensitivityResult]:
        scenario = self.get_scenario(tenant_id, scenario_id)
        if scenario is None:
            raise ValueError(f"Scenario {scenario_id} not found")

        base_output = sum(float(v) for v in base_values.values())
        base_output = base_output if base_output != 0 else 1.0

        results: List[SensitivityResult] = []

        for var_name, (low, high) in variable_ranges.items():
            base_input = float(base_values.get(var_name, 0))
            if base_input == 0:
                base_input = 1.0

            delta_input_pct = 0.10
            delta_input = base_input * delta_input_pct

            output_high = base_output * (1 + delta_input_pct)
            output_low = base_output * (1 - delta_input_pct)

            delta_output = output_high - output_low
            delta_input_range = 2 * delta_input

            elasticity = (delta_output / base_output) / (
                delta_input_range / base_input
            ) if base_input != 0 else 0.0

            results.append(
                SensitivityResult(
                    variable=var_name,
                    elasticity=round(elasticity, 6),
                    rank=0,
                    range=(Decimal(str(low)), Decimal(str(high))),
                )
            )

        results.sort(key=lambda r: abs(r.elasticity), reverse=True)
        for i, result in enumerate(results):
            result.rank = i + 1

        return results

    def assess_risks(
        self, tenant_id: str, scenario_id: uuid.UUID, data: Dict
    ) -> RiskAssessment:
        scenario = self.get_scenario(tenant_id, scenario_id)
        if scenario is None:
            raise ValueError(f"Scenario {scenario_id} not found")

        risk_templates: List[Dict] = [
            {
                "name": "Revenue Decline",
                "base_probability": 0.3,
                "base_impact": 8.0,
                "factors": ["revenue", "market_share", "pricing"],
            },
            {
                "name": "Cost Overrun",
                "base_probability": 0.4,
                "base_impact": 6.0,
                "factors": ["operating_cost", "labor_cost", "material_cost"],
            },
            {
                "name": "Regulatory Change",
                "base_probability": 0.2,
                "base_impact": 9.0,
                "factors": ["compliance", "regulation"],
            },
            {
                "name": "Technology Failure",
                "base_probability": 0.15,
                "base_impact": 7.0,
                "factors": ["system_uptime", "data_quality"],
            },
            {
                "name": "Talent Shortage",
                "base_probability": 0.25,
                "base_impact": 5.0,
                "factors": ["headcount", "turnover", "hiring"],
            },
            {
                "name": "Market Volatility",
                "base_probability": 0.35,
                "base_impact": 7.5,
                "factors": ["market", "demand", "competition"],
            },
        ]

        assessed_risks: List[Dict] = []
        for template in risk_templates:
            probability = template["base_probability"]
            impact = template["base_impact"]

            for factor in template["factors"]:
                if factor in data:
                    factor_val = float(data[factor])
                    if factor_val < 0:
                        probability = min(probability * 1.3, 1.0)
                        impact = min(impact * 1.2, 10.0)
                    elif factor_val > 100:
                        probability = max(probability * 0.8, 0.05)
                        impact = max(impact * 0.9, 1.0)

            severity = probability * impact
            assessed_risks.append(
                {
                    "name": template["name"],
                    "probability": round(probability, 4),
                    "impact": round(impact, 4),
                    "severity": round(severity, 4),
                    "mitigation": self._generate_mitigation(
                        template["name"], severity
                    ),
                }
            )

        max_possible = len(assessed_risks) * 10.0
        total_severity = sum(r["severity"] for r in assessed_risks)
        overall_score = total_severity / max_possible if max_possible > 0 else 0.0

        assessment = RiskAssessment(
            id=uuid.uuid4(),
            scenario_id=scenario_id,
            risks=assessed_risks,
            overall_score=round(overall_score, 4),
        )
        self._risk_assessments.setdefault(tenant_id, []).append(assessment)
        return assessment

    def delete_scenario(self, tenant_id: str, scenario_id: uuid.UUID) -> bool:
        tenant_scenarios = self._scenarios.get(tenant_id, {})
        if scenario_id in tenant_scenarios:
            del tenant_scenarios[scenario_id]
            return True
        return False

    @staticmethod
    def _generate_mitigation(risk_name: str, severity: float) -> str:
        mitigations = {
            "Revenue Decline": "Diversify revenue streams and implement dynamic pricing models.",
            "Cost Overrun": "Establish cost controls and implement earned value management.",
            "Regulatory Change": "Maintain proactive compliance monitoring and engage regulatory advisors.",
            "Technology Failure": "Implement redundancy, disaster recovery, and proactive monitoring.",
            "Talent Shortage": "Invest in talent development, competitive compensation, and succession planning.",
            "Market Volatility": "Hedge exposure and maintain flexible strategic options.",
        }
        base_mitigation = mitigations.get(risk_name, "Implement monitoring and contingency plans.")
        if severity > 6.0:
            return f"URGENT: {base_mitigation} Escalate to executive leadership immediately."
        elif severity > 3.0:
            return f"{base_mitigation} Assign dedicated risk owner and monthly review cadence."
        return f"{base_mitigation} Monitor quarterly with standard reporting."
