from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any
import pandas as pd
import io

from app.db.session import get_db
from app.core.security import get_current_user, CurrentUser
from app.models.models import DataImport

router = APIRouter()

@router.post("/upload")
async def upload_financial_data(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Upload financial data (CSV or Excel) and import into the FinancialDataWarehouse.
    Supports Revenues and Expenses.
    """
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported.")

    try:
        content = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Clean columns
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        
        # Required columns mapping (Basic matching)
        required = {'branch_id', 'department_id', 'amount', 'date', 'type'}
        
        if not required.issubset(set(df.columns)):
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns. Found: {list(df.columns)}. Required: {required}"
            )
            
        # Create DataImport record
        db_import = DataImport(
            filename=file.filename,
            status="imported",
            imported_by=current_user.id,
            records_processed=len(df)
        )
        db.add(db_import)
        
        # Process records
        for _, row in df.iterrows():
            if row['type'] == 'revenue':
                await db.execute(
                    text("""
                        INSERT INTO revenues (branch_id, department_id, amount, net_amount, service_date, created_at)
                        VALUES (:branch_id, :department_id, :amount, :amount, :date, NOW())
                    """),
                    {
                        "branch_id": int(row['branch_id']),
                        "department_id": int(row['department_id']),
                        "amount": float(row['amount']),
                        "date": pd.to_datetime(row['date'])
                    }
                )
            elif row['type'] == 'expense':
                await db.execute(
                    text("""
                        INSERT INTO expenses (branch_id, department_id, category, amount, expense_date, created_at)
                        VALUES (:branch_id, :department_id, :category, :amount, :date, NOW())
                    """),
                    {
                        "branch_id": int(row['branch_id']),
                        "department_id": int(row['department_id']),
                        "category": str(row.get('category', 'general')),
                        "amount": float(row['amount']),
                        "date": pd.to_datetime(row['date'])
                    }
                )
                
        await db.commit()
        
        return {
            "status": "success", 
            "message": f"Successfully imported {len(df)} records.",
            "import_id": str(db_import.id)
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
