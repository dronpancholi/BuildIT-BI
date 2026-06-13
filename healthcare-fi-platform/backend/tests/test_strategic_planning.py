import pytest
from uuid import uuid4
from decimal import Decimal
from app.domain.strategic_planning import (
    StrategicPlanningService, Scenario, ScenarioComparison, DriverTree,
    MonteCarloResult, WhatIfAnalysis, SensitivityResult, RiskAssessment,
    ScenarioStatus, ScenarioType, TreeNodeType, RiskLevel,
)


class TestStrategicPlanningService:
    def setup_method(self):
        self.service = StrategicPlanningService()
        self.tenant_id = str(uuid4())
        self.user_id = str(uuid4())

    def test_create_scenario(self):
        assumptions = [{"name": "growth_rate", "value": 0.05, "unit": "%"}]
        scenario = self.service.create_scenario(
            self.tenant_id, "Base Case", "Revenue forecast", ScenarioType.BASE, assumptions, self.user_id
        )
        assert isinstance(scenario, Scenario)
        assert scenario.name == "Base Case"
        assert scenario.type == ScenarioType.BASE
        assert scenario.status == ScenarioStatus.DRAFT

    def test_get_scenario(self):
        s = self.service.create_scenario(self.tenant_id, "S", "D", ScenarioType.BASE, [], self.user_id)
        result = self.service.get_scenario(self.tenant_id, s.id)
        assert result is not None
        assert result.id == s.id

    def test_get_scenario_returns_none(self):
        result = self.service.get_scenario(self.tenant_id, uuid4())
        assert result is None

    def test_run_scenario(self):
        s = self.service.create_scenario(
            self.tenant_id, "S", "D", ScenarioType.BASE,
            [{"name": "price", "value": 100}], self.user_id
        )
        data = {"units": 1000, "price": 100}
        result = self.service.run_scenario(self.tenant_id, s.id, data)
        assert result.results is not None

    def test_compare_scenarios(self):
        s1 = self.service.create_scenario(self.tenant_id, "Base", "", ScenarioType.BASE, [], self.user_id)
        s2 = self.service.create_scenario(self.tenant_id, "Best", "", ScenarioType.BEST_CASE, [], self.user_id)
        comparison = self.service.compare_scenarios(self.tenant_id, [s1.id, s2.id], ["revenue"])
        assert isinstance(comparison, ScenarioComparison)
        assert len(comparison.scenario_ids) == 2

    def test_build_driver_tree(self):
        metrics = [
            {"name": "Revenue", "type": "metric", "weight": 1.0},
            {"name": "Units", "type": "driver", "weight": 0.6},
            {"name": "Price", "type": "driver", "weight": 0.4},
        ]
        tree = self.service.build_driver_tree(self.tenant_id, "Revenue Tree", "Breakdown", metrics)
        assert isinstance(tree, DriverTree)
        assert len(tree.nodes) == 4

    def test_calculate_driver_values(self):
        metrics = [
            {"name": "Revenue", "type": "metric", "weight": 1.0},
            {"name": "Units", "type": "driver", "weight": 0.6},
            {"name": "Price", "type": "driver", "weight": 0.4},
        ]
        tree = self.service.build_driver_tree(self.tenant_id, "T", "D", metrics)
        actual_data = {"Units": 100, "Price": 50}
        result = self.service.calculate_driver_values(tree.id, actual_data)
        assert result is not None

    def test_run_monte_carlo(self):
        s = self.service.create_scenario(
            self.tenant_id, "MC", "", ScenarioType.BASE,
            [{"name": "revenue", "value": 1000000}], self.user_id
        )
        distributions = {"revenue": {"type": "normal", "mean": 1000000, "std": 100000}}
        result = self.service.run_monte_carlo(self.tenant_id, s.id, distributions, 100)
        assert isinstance(result, MonteCarloResult)
        assert result.simulations == 100
        assert isinstance(result.mean, Decimal)
        assert isinstance(result.var_95, Decimal)
        assert len(result.histogram) == 10

    def test_create_what_if(self):
        changes = [{"variable": "price", "base_value": 100, "new_value": 90}]
        wi = self.service.create_what_if(
            self.tenant_id, "Price Cut", {"revenue": 1000000}, changes
        )
        assert isinstance(wi, WhatIfAnalysis)
        assert wi.name == "Price Cut"

    def test_run_what_if(self):
        wi = self.service.create_what_if(
            self.tenant_id, "Test", {"revenue": 1000}, [{"variable": "x", "base_value": 10, "new_value": 15}]
        )
        result = self.service.run_what_if(self.tenant_id, wi.id, {})
        assert result.results is not None or result.impact_summary is not None

    def test_sensitivity_analysis(self):
        s = self.service.create_scenario(
            self.tenant_id, "SA", "", ScenarioType.BASE,
            [{"name": "price", "value": 100}], self.user_id
        )
        ranges = {"price": (Decimal("80"), Decimal("120"))}
        results = self.service.sensitivity_analysis(self.tenant_id, s.id, {"revenue": Decimal("1000")}, ranges, 10)
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, SensitivityResult)

    def test_assess_risks(self):
        s = self.service.create_scenario(self.tenant_id, "R", "", ScenarioType.BASE, [], self.user_id)
        assessment = self.service.assess_risks(self.tenant_id, s.id, {})
        assert isinstance(assessment, RiskAssessment)
        assert 0 <= assessment.overall_score <= 1

    def test_delete_scenario(self):
        s = self.service.create_scenario(self.tenant_id, "Del", "", ScenarioType.BASE, [], self.user_id)
        result = self.service.delete_scenario(self.tenant_id, s.id)
        assert result is True
        assert self.service.get_scenario(self.tenant_id, s.id) is None

    def test_scenario_type_enum(self):
        assert len(ScenarioType) == 5
        assert ScenarioType.BASE.value == "base"
