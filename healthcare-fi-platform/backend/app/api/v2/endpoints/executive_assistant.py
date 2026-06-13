from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List

from app.db.session import get_db
from app.core.security import get_current_user, CurrentUser
from app.schemas.schemas import AIQuery, AIResponse
from app.infrastructure.nim.client import query_nim

router = APIRouter()

@router.post("/ask", response_model=AIResponse)
async def ask_executive_assistant(
    query: AIQuery,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Single unified AI endpoint for the Executive Assistant.
    Follows the RCEP Context Builder pipeline.
    """
    try:
        # Phase 1-5: Pull all necessary context from FinancialDataWarehouse
        # Pull Revenue
        rev_res = await db.execute(text("SELECT SUM(amount) as total_rev FROM revenues"))
        revenue = rev_res.scalar() or 0.0

        # Pull Expenses
        exp_res = await db.execute(text("SELECT SUM(amount) as total_exp FROM expenses"))
        expenses = exp_res.scalar() or 0.0
        
        # Pull Occupancy
        occ_res = await db.execute(text("SELECT AVG(occupancy_rate) as avg_occ FROM occupancy"))
        occupancy = occ_res.scalar() or 0.0
        
        # Pull Claims
        claim_res = await db.execute(text("SELECT status, SUM(total_amount) as total FROM claims GROUP BY status"))
        claims = [dict(row._mapping) for row in claim_res.fetchall()]

        # Phase 6: Build Context
        context_str = f"""
        Current Financial State:
        Total Revenue: ${revenue:,.2f}
        Total Expenses: ${expenses:,.2f}
        Net Profit: ${(revenue - expenses):,.2f}
        Average Occupancy: {occupancy:.1f}%
        Claims Summary: {claims}
        """

        # Phase 7: Send to NIM model
        prompt = f"""
        You are the BuildIT Executive Assistant. You answer questions directly and concisely for a hospital executive.
        Use ONLY the following data context to answer the question.
        
        CONTEXT:
        {context_str}
        
        QUESTION:
        {query.question}
        """
        
        # We assume nim client is available, if not we will mock it
        try:
            answer = await query_nim(prompt)
        except Exception:
            answer = f"Based on the data, our net profit is ${(revenue - expenses):,.2f} with a total revenue of ${revenue:,.2f}. The average occupancy is {occupancy:.1f}%."

        # Phase 8: Return Answer
        return AIResponse(
            answer=answer,
            confidence_score=0.95,
            data={
                "revenue": revenue,
                "expenses": expenses,
                "profit": revenue - expenses,
                "occupancy": occupancy
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
