"""
Domain 1: Financial Architecture — API Endpoints.
Currency management, FX rates, money conversion.
FX rates backed by FXRateSnapshotRepository for persistence.
"""
import uuid
from typing import Optional, List
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dev_auth import DevUser, dep_dev_admin
from app.db.session import get_db
from app.domain.financial import (
    CurrencyCode,
    CURRENCIES,
    Money,
    ExchangeRate,
    ConvertedAmount,
    ReportingCurrencyEngine,
    TenantCurrencyConfig,
)
from app.domain.financial.fx_service import ManualFXService, CachedFXService
from app.infrastructure.persistence.repositories import FXRateSnapshotRepository

router = APIRouter()

_fx_service = CachedFXService(ManualFXService(), ttl_seconds=3600)
_engine = ReportingCurrencyEngine(_fx_service)


class ConvertRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str
    transaction_date: str


class BatchConvertRequest(BaseModel):
    transactions: List[dict]
    to_currency: str


class MoneyResponse(BaseModel):
    amount: str
    currency: str
    formatted: str


class ExchangeRateResponse(BaseModel):
    base_currency: str
    target_currency: str
    rate: str
    inverse_rate: str
    effective_date: str
    source: str
    is_estimated: bool


class ConvertedAmountResponse(BaseModel):
    original_amount: str
    original_currency: str
    converted_amount: str
    converted_currency: str
    rate: str
    rate_date: str
    rate_source: str
    is_estimated: bool


# ============================================================
# CURRENCY ENDPOINTS (static reference data)
# ============================================================

@router.get("/currencies")
async def list_currencies():
    """List all supported currencies."""
    return {
        "currencies": [
            {
                "code": c.code.code,
                "name": c.name,
                "symbol": c.symbol,
                "decimal_places": c.decimal_places,
                "sub_unit": c.sub_unit,
                "country_codes": list(c.country_codes),
            }
            for c in CURRENCIES.values()
        ]
    }


@router.get("/currencies/{currency_code}")
async def get_currency(currency_code: str):
    """Get details for a specific currency."""
    try:
        code = CurrencyCode(currency_code.upper())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Currency {currency_code} not found")

    currency = CURRENCIES.get(code)
    if not currency:
        raise HTTPException(status_code=404, detail=f"Currency {currency_code} not configured")

    return {
        "code": currency.code.code,
        "name": currency.name,
        "symbol": currency.symbol,
        "decimal_places": currency.decimal_places,
        "sub_unit": currency.sub_unit,
        "country_codes": list(currency.country_codes),
    }


# ============================================================
# FX RATE ENDPOINTS (DB-backed via FXRateSnapshotRepository)
# ============================================================

@router.get("/fx-rates")
async def get_fx_rate(
    base: str,
    target: str,
    effective_date: Optional[str] = None,
    _user: DevUser = Depends(dep_dev_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get exchange rate between two currencies."""
    try:
        base_code = CurrencyCode(base.upper())
        target_code = CurrencyCode(target.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid currency code")

    rate_date = date.fromisoformat(effective_date) if effective_date else date.today()

    repo = FXRateSnapshotRepository(db)
    snapshot = await repo.get_latest_rate(
        tenant_id=str(_user.tenant_id),
        base_currency=base_code.value,
        target_currency=target_code.value,
    )
    if snapshot:
        return {
            "base_currency": snapshot["base_currency"],
            "target_currency": snapshot["target_currency"],
            "rate": str(snapshot["rate"]),
            "inverse_rate": str(1 / Decimal(str(snapshot["rate"]))),
            "effective_date": str(snapshot.get("rate_date", rate_date)),
            "source": "database",
            "is_estimated": False,
        }

    try:
        rate = _fx_service.get_rate(base_code, target_code, rate_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "base_currency": rate.base_currency.code,
        "target_currency": rate.target_currency.code,
        "rate": str(rate.rate),
        "inverse_rate": str(rate.inverse_rate),
        "effective_date": rate.effective_date.isoformat(),
        "source": rate.source,
        "is_estimated": rate.is_estimated,
    }


@router.post("/convert")
async def convert_money(request: ConvertRequest):
    """Convert an amount from one currency to another."""
    try:
        from_code = CurrencyCode(request.from_currency.upper())
        to_code = CurrencyCode(request.to_currency.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid currency code")

    amount = Money(amount=Decimal(str(request.amount)), currency=from_code)
    txn_date = date.fromisoformat(request.transaction_date)

    try:
        result = _engine.convert_transaction(amount, to_code, txn_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "original": result.original.to_dict(),
        "converted": result.converted.to_dict(),
        "rate_used": {
            "rate": str(result.rate.rate),
            "date": result.rate.effective_date.isoformat(),
            "source": result.rate.source,
            "is_estimated": result.rate.is_estimated,
        },
        "audit": result.to_dict(),
    }


@router.post("/convert/batch")
async def convert_batch(request: BatchConvertRequest):
    """Convert a batch of transactions to a single reporting currency."""
    try:
        to_code = CurrencyCode(request.to_currency.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid target currency")

    transactions = []
    for txn in request.transactions:
        try:
            from_code = CurrencyCode(txn["currency"].upper())
            amount = Money(amount=Decimal(str(txn["amount"])), currency=from_code)
            txn_date = date.fromisoformat(txn["date"])
            transactions.append((amount, txn_date))
        except (KeyError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid transaction: {e}")

    results = _engine.convert_batch(transactions, to_code)
    total = _engine.sum_converted(transactions, to_code)

    return {
        "conversions": [r.to_dict() for r in results],
        "total": total.to_dict(),
        "transaction_count": len(results),
    }


# ============================================================
# MONEY UTILITY ENDPOINTS
# ============================================================

@router.post("/money/format")
async def format_money(amount: float, currency: str, locale: str = "en_IN"):
    """Format a monetary amount with locale-specific formatting."""
    try:
        code = CurrencyCode(currency.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid currency code")

    money = Money(amount=Decimal(str(amount)), currency=code)
    return {
        "amount": str(money.amount),
        "currency": money.currency.code,
        "formatted": money.format(locale=locale),
    }
