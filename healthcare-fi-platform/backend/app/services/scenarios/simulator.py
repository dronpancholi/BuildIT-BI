from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.models import Scenario

logger = structlog.get_logger()


class ScenarioSimulator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def simulate_pricing_change(
        self,
        current_revenue: float,
        price_change_percent: float,
        volume_impact_percent: float = 0,
        periods: int = 12
    ) -> Dict[str, Any]:
        monthly_revenue = current_revenue / 12
        
        simulations = []
        cumulative_impact = 0
        
        for period in range(1, periods + 1):
            new_price_factor = 1 + (price_change_percent / 100)
            volume_factor = 1 + (volume_impact_percent / 100)
            
            simulated_revenue = monthly_revenue * new_price_factor * volume_factor
            period_impact = simulated_revenue - monthly_revenue
            cumulative_impact += period_impact
            
            simulations.append({
                "period": period,
                "simulated_revenue": simulated_revenue,
                "period_impact": period_impact,
                "cumulative_impact": cumulative_impact
            })
        
        total_impact = cumulative_impact
        roi = (total_impact / current_revenue * 100) if current_revenue > 0 else 0
        
        return {
            "simulation_type": "pricing_change",
            "parameters": {
                "price_change_percent": price_change_percent,
                "volume_impact_percent": volume_impact_percent,
                "periods": periods
            },
            "results": {
                "monthly_simulations": simulations,
                "total_impact": total_impact,
                "roi_percent": roi,
                "breakeven_period": self._calculate_breakeven(
                    monthly_revenue, price_change_percent, volume_impact_percent
                )
            }
        }

    async def simulate_department_expansion(
        self,
        current_revenue: float,
        current_expenses: float,
        new_dept_investment: float,
        new_dept_monthly_revenue: float,
        new_dept_monthly_expenses: float,
        periods: int = 12
    ) -> Dict[str, Any]:
        simulations = []
        cumulative_roi = -new_dept_investment
        
        for period in range(1, periods + 1):
            period_revenue = new_dept_monthly_revenue
            period_expenses = new_dept_monthly_expenses
            period_profit = period_revenue - period_expenses
            cumulative_roi += period_profit
            
            simulations.append({
                "period": period,
                "revenue": period_revenue,
                "expenses": period_expenses,
                "profit": period_profit,
                "cumulative_roi": cumulative_roi
            })
        
        total_revenue = current_revenue + (new_dept_monthly_revenue * periods)
        total_expenses = current_expenses + (new_dept_monthly_expenses * periods) + new_dept_investment
        total_profit = total_revenue - total_expenses
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            "simulation_type": "department_expansion",
            "parameters": {
                "investment": new_dept_investment,
                "monthly_revenue": new_dept_monthly_revenue,
                "monthly_expenses": new_dept_monthly_expenses,
                "periods": periods
            },
            "results": {
                "monthly_simulations": simulations,
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "total_profit": total_profit,
                "profit_margin": profit_margin,
                "payback_period": self._calculate_payback_period(
                    new_dept_investment, new_dept_monthly_revenue, new_dept_monthly_expenses
                ),
                "roi_percent": (total_profit / new_dept_investment * 100) if new_dept_investment > 0 else 0
            }
        }

    async def simulate_staffing_change(
        self,
        current_monthly_salary_cost: float,
        new_hires: int,
        average_salary: float,
        productivity_improvement_percent: float = 0,
        periods: int = 12
    ) -> Dict[str, Any]:
        additional_monthly_cost = new_hires * (average_salary / 12)
        new_total_salary_cost = current_monthly_salary_cost + additional_monthly_cost
        
        simulations = []
        cumulative_benefit = 0
        cumulative_cost = 0
        
        for period in range(1, periods + 1):
            period_cost = additional_monthly_cost
            period_benefit = (current_monthly_salary_cost * productivity_improvement_percent / 100)
            net_impact = period_benefit - period_cost
            
            cumulative_cost += period_cost
            cumulative_benefit += period_benefit
            
            simulations.append({
                "period": period,
                "additional_cost": period_cost,
                "productivity_benefit": period_benefit,
                "net_impact": net_impact,
                "cumulative_cost": cumulative_cost,
                "cumulative_benefit": cumulative_benefit
            })
        
        total_cost = cumulative_cost
        total_benefit = cumulative_benefit
        net_roi = total_benefit - total_cost
        
        return {
            "simulation_type": "staffing_change",
            "parameters": {
                "new_hires": new_hires,
                "average_salary": average_salary,
                "productivity_improvement_percent": productivity_improvement_percent,
                "periods": periods
            },
            "results": {
                "monthly_simulations": simulations,
                "total_additional_cost": total_cost,
                "total_productivity_benefit": total_benefit,
                "net_roi": net_roi,
                "roi_percent": (net_roi / total_cost * 100) if total_cost > 0 else 0,
                "payback_period": self._calculate_staffing_payback(
                    additional_monthly_cost,
                    current_monthly_salary_cost,
                    productivity_improvement_percent
                )
            }
        }

    async def simulate_insurance_mix_change(
        self,
        current_revenue: float,
        current_payer_mix: Dict[str, float],
        new_payer_mix: Dict[str, float],
        payer_revenue_impact: Dict[str, float],
        periods: int = 12
    ) -> Dict[str, Any]:
        current_weighted_revenue = sum(
            current_payer_mix.get(payer, 0) * payer_revenue_impact.get(payer, 1)
            for payer in current_payer_mix
        )
        
        new_weighted_revenue = sum(
            new_payer_mix.get(payer, 0) * payer_revenue_impact.get(payer, 1)
            for payer in new_payer_mix
        )
        
        monthly_revenue = current_revenue / 12
        change_factor = new_weighted_revenue / current_weighted_revenue if current_weighted_revenue > 0 else 1
        
        simulations = []
        cumulative_impact = 0
        
        for period in range(1, periods + 1):
            simulated_revenue = monthly_revenue * change_factor
            period_impact = simulated_revenue - monthly_revenue
            cumulative_impact += period_impact
            
            simulations.append({
                "period": period,
                "simulated_revenue": simulated_revenue,
                "period_impact": period_impact,
                "cumulative_impact": cumulative_impact
            })
        
        return {
            "simulation_type": "insurance_mix_change",
            "parameters": {
                "current_payer_mix": current_payer_mix,
                "new_payer_mix": new_payer_mix,
                "periods": periods
            },
            "results": {
                "monthly_simulations": simulations,
                "total_impact": cumulative_impact,
                "revenue_change_percent": (change_factor - 1) * 100
            }
        }

    async def simulate_capacity_expansion(
        self,
        current_beds: int,
        current_occupancy_rate: float,
        additional_beds: int,
        bed_cost: float,
        daily_revenue_per_bed: float,
        daily_cost_per_bed: float,
        periods: int = 12
    ) -> Dict[str, Any]:
        current_daily_revenue = current_beds * current_occupancy_rate / 100 * daily_revenue_per_bed
        new_total_beds = current_beds + additional_beds
        
        target_occupancy = 80
        expected_occupancy = min(target_occupancy, current_occupancy_rate + 5)
        
        simulations = []
        cumulative_roi = -bed_cost * additional_beds
        
        for period in range(1, periods + 1):
            period_days = 30
            period_revenue = new_total_beds * expected_occupancy / 100 * daily_revenue_per_bed * period_days
            period_cost = new_total_beds * daily_cost_per_bed * period_days
            period_profit = period_revenue - period_cost
            cumulative_roi += period_profit
            
            simulations.append({
                "period": period,
                "revenue": period_revenue,
                "expenses": period_cost,
                "profit": period_profit,
                "cumulative_roi": cumulative_roi
            })
        
        total_investment = bed_cost * additional_beds
        annual_revenue = sum(s["revenue"] for s in simulations[:12])
        annual_profit = sum(s["profit"] for s in simulations[:12])
        
        return {
            "simulation_type": "capacity_expansion",
            "parameters": {
                "current_beds": current_beds,
                "additional_beds": additional_beds,
                "bed_cost": bed_cost,
                "daily_revenue_per_bed": daily_revenue_per_bed,
                "daily_cost_per_bed": daily_cost_per_bed,
                "periods": periods
            },
            "results": {
                "monthly_simulations": simulations,
                "total_investment": total_investment,
                "annual_revenue": annual_revenue,
                "annual_profit": annual_profit,
                "payback_period": self._calculate_capacity_payback(
                    total_investment, annual_profit
                ),
                "roi_percent": (annual_profit / total_investment * 100) if total_investment > 0 else 0
            }
        }

    def _calculate_breakeven(
        self,
        monthly_revenue: float,
        price_change_percent: float,
        volume_impact_percent: float
    ) -> int:
        new_monthly = monthly_revenue * (1 + price_change_percent / 100) * (1 + volume_impact_percent / 100)
        if new_monthly > monthly_revenue:
            return 1
        return -1

    def _calculate_payback_period(
        self,
        investment: float,
        monthly_revenue: float,
        monthly_expenses: float
    ) -> int:
        monthly_profit = monthly_revenue - monthly_expenses
        if monthly_profit <= 0:
            return -1
        return int(investment / monthly_profit) + 1

    def _calculate_staffing_payback(
        self,
        additional_monthly_cost: float,
        current_salary_cost: float,
        productivity_improvement_percent: float
    ) -> int:
        monthly_benefit = current_salary_cost * productivity_improvement_percent / 100
        if monthly_benefit <= additional_monthly_cost:
            return -1
        return 1

    def _calculate_capacity_payback(
        self,
        investment: float,
        annual_profit: float
    ) -> int:
        if annual_profit <= 0:
            return -1
        return int(investment / annual_profit * 12) + 1

    async def run_simulation(
        self,
        scenario_type: str,
        parameters: Dict[str, Any],
        periods: int = 12
    ) -> Dict[str, Any]:
        if scenario_type == "pricing_change":
            return await self.simulate_pricing_change(
                current_revenue=parameters.get("current_revenue", 0),
                price_change_percent=parameters.get("price_change_percent", 0),
                volume_impact_percent=parameters.get("volume_impact_percent", 0),
                periods=periods
            )
        elif scenario_type == "department_expansion":
            return await self.simulate_department_expansion(
                current_revenue=parameters.get("current_revenue", 0),
                current_expenses=parameters.get("current_expenses", 0),
                new_dept_investment=parameters.get("investment", 0),
                new_dept_monthly_revenue=parameters.get("monthly_revenue", 0),
                new_dept_monthly_expenses=parameters.get("monthly_expenses", 0),
                periods=periods
            )
        elif scenario_type == "staffing_change":
            return await self.simulate_staffing_change(
                current_monthly_salary_cost=parameters.get("current_monthly_salary_cost", 0),
                new_hires=parameters.get("new_hires", 0),
                average_salary=parameters.get("average_salary", 0),
                productivity_improvement_percent=parameters.get("productivity_improvement_percent", 0),
                periods=periods
            )
        elif scenario_type == "insurance_mix_change":
            return await self.simulate_insurance_mix_change(
                current_revenue=parameters.get("current_revenue", 0),
                current_payer_mix=parameters.get("current_payer_mix", {}),
                new_payer_mix=parameters.get("new_payer_mix", {}),
                payer_revenue_impact=parameters.get("payer_revenue_impact", {}),
                periods=periods
            )
        elif scenario_type == "capacity_expansion":
            return await self.simulate_capacity_expansion(
                current_beds=parameters.get("current_beds", 0),
                current_occupancy_rate=parameters.get("current_occupancy_rate", 0),
                additional_beds=parameters.get("additional_beds", 0),
                bed_cost=parameters.get("bed_cost", 0),
                daily_revenue_per_bed=parameters.get("daily_revenue_per_bed", 0),
                daily_cost_per_bed=parameters.get("daily_cost_per_bed", 0),
                periods=periods
            )
        else:
            return {"error": f"Unknown scenario type: {scenario_type}"}

    async def save_scenario(
        self,
        name: str,
        description: str,
        created_by: int,
        parameters: Dict[str, Any],
        results: Dict[str, Any],
        status: str = "completed"
    ) -> Scenario:
        scenario = Scenario(
            name=name,
            description=description,
            created_by=created_by,
            parameters=parameters,
            results=results,
            status=status
        )
        
        self.db.add(scenario)
        await self.db.flush()
        
        return scenario
