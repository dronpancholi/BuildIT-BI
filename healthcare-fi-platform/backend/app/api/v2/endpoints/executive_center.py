from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any

from app.db.session import get_db
from app.core.security import get_current_user, CurrentUser

router = APIRouter()

@router.get("/kpis")
async def get_executive_kpis(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    try:
        # Real-time queries for the Executive Dashboard
        rev_res = await db.execute(text("SELECT COALESCE(SUM(amount), 0) FROM revenues"))
        revenue = rev_res.scalar()
        
        exp_res = await db.execute(text("SELECT COALESCE(SUM(amount), 0) FROM expenses"))
        expenses = exp_res.scalar()
        
        occ_res = await db.execute(text("SELECT COALESCE(AVG(occupancy_rate), 0) FROM occupancy"))
        occupancy = occ_res.scalar()

        claim_res = await db.execute(text("""
            SELECT 
                COUNT(*) as total_claims,
                SUM(CASE WHEN status = 'denied' THEN 1 ELSE 0 END) as denied_claims
            FROM claims
        """))
        claim_data = claim_res.fetchone()
        denial_rate = (claim_data[1] / claim_data[0] * 100) if claim_data[0] > 0 else 0
        
        return {
            "status": "success",
            "financials": {
                "revenue": revenue,
                "expenses": expenses,
                "profit": revenue - expenses,
                "cash": (revenue - expenses) * 0.8 # Rough cash estimate
            },
            "operations": {
                "occupancy": occupancy,
                "patients": 0, # Should query patients table
                "claims_denial_rate": denial_rate
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_executive_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    # Mock alerts since we removed the alerts module
    return {
        "status": "success",
        "alerts": [
            { "id": 1, "title": "Cash flow dip projected for next week", "severity": "warning" },
            { "id": 2, "title": "Unusual Supply Cost Spike", "severity": "critical" }
        ]
    }
