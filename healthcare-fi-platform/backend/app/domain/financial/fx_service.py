"""
FX Service — Exchange rate fetching, caching, and conversion.
"""
import uuid
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, Dict, List, Protocol

import httpx

from app.core.config import settings
from app.domain.financial import (
    CurrencyCode,
    ExchangeRate,
    Money,
)

logger = logging.getLogger(__name__)


class FXService(Protocol):
    """Protocol for exchange rate services."""

    def get_rate(
        self,
        base: CurrencyCode,
        target: CurrencyCode,
        effective_date: date,
    ) -> ExchangeRate: ...

    def get_historical_rates(
        self,
        base: CurrencyCode,
        target: CurrencyCode,
        start_date: date,
        end_date: date,
    ) -> List[ExchangeRate]: ...

    def convert(
        self,
        money: Money,
        target: CurrencyCode,
        effective_date: date,
    ) -> Money: ...


# ============================================================
# MANUAL FX SERVICE (for development)
# ============================================================

class ManualFXService:
    """Hardcoded FX rates for development. Replace with live provider in production."""

    RATES = {
        (CurrencyCode.INR, CurrencyCode.USD): Decimal("0.000012"),
        (CurrencyCode.USD, CurrencyCode.INR): Decimal("83500"),
        (CurrencyCode.INR, CurrencyCode.EUR): Decimal("0.000011"),
        (CurrencyCode.INR, CurrencyCode.GBP): Decimal("0.0000095"),
        (CurrencyCode.USD, CurrencyCode.EUR): Decimal("0.92"),
        (CurrencyCode.USD, CurrencyCode.GBP): Decimal("0.79"),
        (CurrencyCode.USD, CurrencyCode.AED): Decimal("3.67"),
        (CurrencyCode.USD, CurrencyCode.SGD): Decimal("1.34"),
    }

    def get_rate(
        self,
        base: CurrencyCode,
        target: CurrencyCode,
        effective_date: date,
    ) -> ExchangeRate:
        if base == target:
            return ExchangeRate(
                id=uuid.uuid4(),
                base_currency=base,
                target_currency=target,
                rate=Decimal("1"),
                inverse_rate=Decimal("1"),
                effective_date=effective_date,
                source="identity",
                is_estimated=False,
                is_confirmed=True,
            )

        key = (base, target)
        rate = self.RATES.get(key)
        if rate is None:
            raise ValueError(f"No exchange rate available for {base.code} → {target.code}")

        inverse_key = (target, base)
        inverse_rate = self.RATES.get(inverse_key, Decimal("1") / rate)

        return ExchangeRate(
            id=uuid.uuid4(),
            base_currency=base,
            target_currency=target,
            rate=rate,
            inverse_rate=inverse_rate,
            effective_date=effective_date,
            source="manual_development",
            is_estimated=False,
            is_confirmed=True,
        )

    def get_historical_rates(
        self,
        base: CurrencyCode,
        target: CurrencyCode,
        start_date: date,
        end_date: date,
    ) -> List[ExchangeRate]:
        rates = []
        current = start_date
        while current <= end_date:
            try:
                rate = self.get_rate(base, target, current)
                rates.append(rate)
            except ValueError:
                pass
            current += timedelta(days=1)
        return rates

    def convert(
        self,
        money: Money,
        target: CurrencyCode,
        effective_date: date,
    ) -> Money:
        rate = self.get_rate(money.currency, target, effective_date)
        converted_value = rate.convert(money.amount)
        return Money(amount=converted_value, currency=target)


# ============================================================
# CACHED FX SERVICE (wraps any FXService with in-memory cache)
# ============================================================

class CachedFXService:
    """Decorator that caches FX rates with configurable TTL."""

    def __init__(self, inner: FXService, ttl_seconds: int = 3600):
        self._inner = inner
        self._ttl = ttl_seconds
        self._cache: Dict[str, tuple] = {}

    def _cache_key(self, base: CurrencyCode, target: CurrencyCode, effective_date: date) -> str:
        return f"{base.code}:{target.code}:{effective_date.isoformat()}"

    def _is_fresh(self, cached_at: datetime) -> bool:
        return (datetime.utcnow() - cached_at).total_seconds() < self._ttl

    def get_rate(
        self,
        base: CurrencyCode,
        target: CurrencyCode,
        effective_date: date,
    ) -> ExchangeRate:
        key = self._cache_key(base, target, effective_date)
        if key in self._cache:
            rate, cached_at = self._cache[key]
            if self._is_fresh(cached_at):
                return rate

        rate = self._inner.get_rate(base, target, effective_date)
        self._cache[key] = (rate, datetime.utcnow())
        return rate

    def get_historical_rates(
        self,
        base: CurrencyCode,
        target: CurrencyCode,
        start_date: date,
        end_date: date,
    ) -> List[ExchangeRate]:
        return self._inner.get_historical_rates(base, target, start_date, end_date)

    def convert(
        self,
        money: Money,
        target: CurrencyCode,
        effective_date: date,
    ) -> Money:
        rate = self.get_rate(money.currency, target, effective_date)
        converted_value = rate.convert(money.amount)
        return Money(amount=converted_value, currency=target)


# ============================================================
# NIM FX SERVICE (live rates via NVIDIA NIM API — placeholder)
# ============================================================

class NIMFXService:
    """
    Live FX rates from external APIs.
    Uses NIM for rate prediction/forecasting, with fallback to manual rates.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.NVIDIA_NIM_API_KEY
        self._fallback = ManualFXService()

    def get_rate(
        self,
        base: CurrencyCode,
        target: CurrencyCode,
        effective_date: date,
    ) -> ExchangeRate:
        try:
            return self._fetch_live_rate(base, target, effective_date)
        except Exception as e:
            logger.warning(f"Live FX rate fetch failed, using fallback: {e}")
            rate = self._fallback.get_rate(base, target, effective_date)
            return ExchangeRate(
                id=rate.id,
                base_currency=rate.base_currency,
                target_currency=rate.target_currency,
                rate=rate.rate,
                inverse_rate=rate.inverse_rate,
                effective_date=rate.effective_date,
                source="fallback_manual",
                is_estimated=True,
                is_confirmed=False,
            )

    def _fetch_live_rate(
        self,
        base: CurrencyCode,
        target: CurrencyCode,
        effective_date: date,
    ) -> ExchangeRate:
        # Placeholder for live FX API integration
        raise NotImplementedError("Live FX API integration pending")

    def get_historical_rates(
        self,
        base: CurrencyCode,
        target: CurrencyCode,
        start_date: date,
        end_date: date,
    ) -> List[ExchangeRate]:
        return self._fallback.get_historical_rates(base, target, start_date, end_date)

    def convert(
        self,
        money: Money,
        target: CurrencyCode,
        effective_date: date,
    ) -> Money:
        rate = self.get_rate(money.currency, target, effective_date)
        converted_value = rate.convert(money.amount)
        return Money(amount=converted_value, currency=target)
