from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any

from app.db.session import get_db
from app.core.dev_auth import DevUser, dep_dev_admin
from app.services.scenarios.simulator import ScenarioSimulator
from app.schemas.schemas import ScenarioCreate

router = APIRouter()


@router.post("/simulate")
async def run_simulation(
    scenario_type: str,
    parameters: Dict[str, Any],
    periods: int = Query(12),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    simulator = ScenarioSimulator(db)
    result = await simulator.run_simulation(scenario_type, parameters, periods)
    
    return result


@router.post("/pricing-change")
async def simulate_pricing_change(
    current_revenue: float,
    price_change_percent: float,
    volume_impact_percent: float = 0,
    periods: int = Query(12),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    simulator = ScenarioSimulator(db)
    result = await simulator.simulate_pricing_change(
        current_revenue, price_change_percent, volume_impact_percent, periods
    )
    
    return result


@router.post("/department-expansion")
async def simulate_department_expansion(
    current_revenue: float,
    current_expenses: float,
    investment: float,
    monthly_revenue: float,
    monthly_expenses: float,
    periods: int = Query(12),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    simulator = ScenarioSimulator(db)
    result = await simulator.simulate_department_expansion(
        current_revenue, current_expenses, investment,
        monthly_revenue, monthly_expenses, periods
    )
    
    return result


@router.post("/staffing-change")
async def simulate_staffing_change(
    current_monthly_salary_cost: float,
    new_hires: int,
    average_salary: float,
    productivity_improvement_percent: float = 0,
    periods: int = Query(12),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    simulator = ScenarioSimulator(db)
    result = await simulator.simulate_staffing_change(
        current_monthly_salary_cost, new_hires, average_salary,
        productivity_improvement_percent, periods
    )
    
    return result


@router.post("/insurance-mix")
async def simulate_insurance_mix(
    current_revenue: float,
    current_payer_mix: Dict[str, float],
    new_payer_mix: Dict[str, float],
    payer_revenue_impact: Dict[str, float],
    periods: int = Query(12),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    simulator = ScenarioSimulator(db)
    result = await simulator.simulate_insurance_mix_change(
        current_revenue, current_payer_mix, new_payer_mix,
        payer_revenue_impact, periods
    )
    
    return result


@router.post("/capacity-expansion")
async def simulate_capacity_expansion(
    current_beds: int,
    current_occupancy_rate: float,
    additional_beds: int,
    bed_cost: float,
    daily_revenue_per_bed: float,
    daily_cost_per_bed: float,
    periods: int = Query(12),
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    simulator = ScenarioSimulator(db)
    result = await simulator.simulate_capacity_expansion(
        current_beds, current_occupancy_rate, additional_beds,
        bed_cost, daily_revenue_per_bed, daily_cost_per_bed, periods
    )
    
    return result


@router.post("/save")
async def save_scenario(
    scenario_data: ScenarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    simulator = ScenarioSimulator(db)
    
    result = await simulator.run_simulation(
        "custom",
        scenario_data.parameters,
        12
    )
    
    scenario = await simulator.save_scenario(
        name=scenario_data.name,
        description=scenario_data.description,
        created_by=current_user.id,
        parameters=scenario_data.parameters,
        results=result
    )
    
    return {"id": scenario.id, "name": scenario.name, "status": scenario.status}


@router.get("/list")
async def list_scenarios(
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(dep_dev_admin)
):
    from sqlalchemy import select
    from app.models.models import Scenario
    
    query = select(Scenario).where(Scenario.created_by == current_user.id)
    result = await db.execute(query)
    scenarios = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "status": s.status,
            "created_at": s.created_at
        }
        for s in scenarios
    ]
