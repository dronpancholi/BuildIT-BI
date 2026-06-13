"""
Comprehensive test suite for Domain 1: Financial Architecture.
Tests Currency, Money, FX, Reporting Currency Engine.
"""
import uuid
import pytest
from decimal import Decimal
from datetime import date, datetime

from app.domain.financial import (
    CurrencyCode,
    Currency,
    CURRENCIES,
    ExchangeRate,
    Money,
    TenantCurrencyConfig,
    ReportingCurrencyEngine,
    ConvertedAmount,
)
from app.domain.financial.fx_service import ManualFXService, CachedFXService


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def fx_service():
    return ManualFXService()


@pytest.fixture
def cached_fx_service(fx_service):
    return CachedFXService(fx_service, ttl_seconds=3600)


@pytest.fixture
def reporting_engine(fx_service):
    return ReportingCurrencyEngine(fx_service)


# ============================================================
# CURRENCY CODE TESTS
# ============================================================

class TestCurrencyCode:
    def test_currency_code_values(self):
        assert CurrencyCode.INR.code == "INR"
        assert CurrencyCode.INR.numeric_code == 356
        assert CurrencyCode.USD.code == "USD"
        assert CurrencyCode.USD.numeric_code == 840

    def test_all_currencies_have_definitions(self):
        for code in CurrencyCode:
            assert code in CURRENCIES, f"Missing currency definition for {code.code}"


# ============================================================
# CURRENCY ENTITY TESTS
# ============================================================

class TestCurrency:
    def test_inr_formatting(self):
        inr = CURRENCIES[CurrencyCode.INR]
        # Python default comma formatting: 250,000.00
        # Indian convention (lakhs/crores) would be 2,50,000.00 — requires custom implementation
        formatted = inr.format_amount(Decimal("250000"))
        assert "₹" in formatted
        assert "250,000.00" in formatted
        assert inr.decimal_places == 2

    def test_usd_formatting(self):
        usd = CURRENCIES[CurrencyCode.USD]
        assert usd.format_amount(Decimal("1234567.89")) == "$1,234,567.89"

    def test_jpy_no_decimals(self):
        jpy = CURRENCIES[CurrencyCode.JPY]
        assert jpy.decimal_places == 0
        formatted = jpy.format_amount(Decimal("1234567"))
        assert "¥" in formatted

    def test_bhd_three_decimals(self):
        bhd = CURRENCIES[CurrencyCode.BHD]
        assert bhd.decimal_places == 3
        assert bhd.sub_unit == "Fils"

    def test_round_amount(self):
        usd = CURRENCIES[CurrencyCode.USD]
        assert usd.round_amount(Decimal("1234.567")) == Decimal("1234.57")
        assert usd.round_amount(Decimal("1234.562")) == Decimal("1234.56")


# ============================================================
# MONEY VALUE OBJECT TESTS
# ============================================================

class TestMoney:
    def test_create_money(self):
        m = Money(amount=Decimal("1000"), currency=CurrencyCode.INR)
        assert m.amount == Decimal("1000")
        assert m.currency == CurrencyCode.INR

    def test_create_from_float(self):
        m = Money.from_float(1000.50, CurrencyCode.USD)
        assert m.amount == Decimal("1000.50")

    def test_add_same_currency(self):
        a = Money(amount=Decimal("100"), currency=CurrencyCode.INR)
        b = Money(amount=Decimal("200"), currency=CurrencyCode.INR)
        result = a + b
        assert result.amount == Decimal("300")
        assert result.currency == CurrencyCode.INR

    def test_add_different_currency_raises(self):
        a = Money(amount=Decimal("100"), currency=CurrencyCode.INR)
        b = Money(amount=Decimal("200"), currency=CurrencyCode.USD)
        with pytest.raises(TypeError, match="different currencies"):
            a + b

    def test_subtract_same_currency(self):
        a = Money(amount=Decimal("500"), currency=CurrencyCode.INR)
        b = Money(amount=Decimal("200"), currency=CurrencyCode.INR)
        result = a - b
        assert result.amount == Decimal("300")

    def test_subtract_different_currency_raises(self):
        a = Money(amount=Decimal("500"), currency=CurrencyCode.INR)
        b = Money(amount=Decimal("200"), currency=CurrencyCode.USD)
        with pytest.raises(TypeError, match="different currencies"):
            a - b

    def test_multiply(self):
        m = Money(amount=Decimal("100"), currency=CurrencyCode.INR)
        result = m * 3
        assert result.amount == Decimal("300")
        assert result.currency == CurrencyCode.INR

    def test_rmultiply(self):
        m = Money(amount=Decimal("100"), currency=CurrencyCode.INR)
        result = 3 * m
        assert result.amount == Decimal("300")

    def test_divide_same_currency(self):
        a = Money(amount=Decimal("1000"), currency=CurrencyCode.INR)
        b = Money(amount=Decimal("100"), currency=CurrencyCode.INR)
        result = a / b
        assert result == Decimal("10")

    def test_divide_different_currency_raises(self):
        a = Money(amount=Decimal("1000"), currency=CurrencyCode.INR)
        b = Money(amount=Decimal("100"), currency=CurrencyCode.USD)
        with pytest.raises(TypeError, match="different currencies"):
            a / b

    def test_divide_by_zero_raises(self):
        a = Money(amount=Decimal("1000"), currency=CurrencyCode.INR)
        b = Money(amount=Decimal("0"), currency=CurrencyCode.INR)
        with pytest.raises(ZeroDivisionError):
            a / b

    def test_negate(self):
        m = Money(amount=Decimal("100"), currency=CurrencyCode.INR)
        assert (-m).amount == Decimal("-100")

    def test_abs(self):
        m = Money(amount=Decimal("-100"), currency=CurrencyCode.INR)
        assert abs(m).amount == Decimal("100")

    def test_compare(self):
        a = Money(amount=Decimal("100"), currency=CurrencyCode.INR)
        b = Money(amount=Decimal("200"), currency=CurrencyCode.INR)
        assert a < b
        assert b > a
        assert a <= b
        assert b >= a

    def test_compare_different_currency_raises(self):
        a = Money(amount=Decimal("100"), currency=CurrencyCode.INR)
        b = Money(amount=Decimal("200"), currency=CurrencyCode.USD)
        with pytest.raises(TypeError, match="different currencies"):
            a < b

    def test_is_zero(self):
        m = Money.zero(CurrencyCode.INR)
        assert m.is_zero()

    def test_is_positive(self):
        m = Money(amount=Decimal("100"), currency=CurrencyCode.INR)
        assert m.is_positive()

    def test_is_negative(self):
        m = Money(amount=Decimal("-100"), currency=CurrencyCode.INR)
        assert m.is_negative()

    def test_to_dict(self):
        m = Money(amount=Decimal("1000"), currency=CurrencyCode.INR)
        d = m.to_dict()
        assert d["amount"] == "1000"
        assert d["currency"] == "INR"
        assert "₹" in d["formatted"]

    def test_format(self):
        m = Money(amount=Decimal("1234567.89"), currency=CurrencyCode.USD)
        formatted = m.format()
        assert "$" in formatted
        assert "1,234,567.89" in formatted


# ============================================================
# EXCHANGE RATE TESTS
# ============================================================

class TestExchangeRate:
    def test_create_rate(self):
        rate = ExchangeRate(
            id=uuid.uuid4(),
            base_currency=CurrencyCode.INR,
            target_currency=CurrencyCode.USD,
            rate=Decimal("0.000012"),
            inverse_rate=Decimal("83333.33"),
            effective_date=date(2026, 1, 15),
            source="rbi.gov.in",
        )
        assert rate.base_currency == CurrencyCode.INR
        assert rate.target_currency == CurrencyCode.USD
        assert rate.is_estimated is False

    def test_convert_amount(self):
        rate = ExchangeRate(
            id=uuid.uuid4(),
            base_currency=CurrencyCode.INR,
            target_currency=CurrencyCode.USD,
            rate=Decimal("0.000012"),
            inverse_rate=Decimal("83333.33"),
            effective_date=date(2026, 1, 15),
            source="manual",
        )
        converted = rate.convert(Decimal("250000"))
        assert converted == Decimal("3.000000")


# ============================================================
# FX SERVICE TESTS
# ============================================================

class TestManualFXService:
    def test_get_rate_inr_to_usd(self, fx_service):
        rate = fx_service.get_rate(CurrencyCode.INR, CurrencyCode.USD, date.today())
        assert rate.base_currency == CurrencyCode.INR
        assert rate.target_currency == CurrencyCode.USD
        assert rate.rate > 0

    def test_get_rate_same_currency(self, fx_service):
        rate = fx_service.get_rate(CurrencyCode.INR, CurrencyCode.INR, date.today())
        assert rate.rate == Decimal("1")

    def test_get_rate_unknown_pair_raises(self, fx_service):
        with pytest.raises(ValueError, match="No exchange rate"):
            fx_service.get_rate(CurrencyCode.BHD, CurrencyCode.KWD, date.today())

    def test_convert(self, fx_service):
        money = Money(amount=Decimal("83500"), currency=CurrencyCode.INR)
        result = fx_service.convert(money, CurrencyCode.USD, date.today())
        assert result.currency == CurrencyCode.USD
        assert result.amount > 0


class TestCachedFXService:
    def test_cache_hit(self, cached_fx_service):
        rate1 = cached_fx_service.get_rate(CurrencyCode.INR, CurrencyCode.USD, date.today())
        rate2 = cached_fx_service.get_rate(CurrencyCode.INR, CurrencyCode.USD, date.today())
        assert rate1.id == rate2.id


# ============================================================
# REPORTING CURRENCY ENGINE TESTS
# ============================================================

class TestReportingCurrencyEngine:
    def test_convert_same_currency(self, reporting_engine):
        amount = Money(amount=Decimal("1000"), currency=CurrencyCode.USD)
        result = reporting_engine.convert_transaction(
            amount, CurrencyCode.USD, date.today()
        )
        assert result.original == amount
        assert result.converted == amount
        assert result.rate.source == "identity"

    def test_convert_inr_to_usd(self, reporting_engine):
        amount = Money(amount=Decimal("83500"), currency=CurrencyCode.INR)
        result = reporting_engine.convert_transaction(
            amount, CurrencyCode.USD, date.today()
        )
        assert result.converted.currency == CurrencyCode.USD
        assert result.converted.amount > 0

    def test_convert_batch(self, reporting_engine):
        transactions = [
            (Money(amount=Decimal("83500"), currency=CurrencyCode.INR), date(2026, 1, 1)),
            (Money(amount=Decimal("167000"), currency=CurrencyCode.INR), date(2026, 2, 1)),
        ]
        results = reporting_engine.convert_batch(transactions, CurrencyCode.USD)
        assert len(results) == 2
        assert all(r.converted.currency == CurrencyCode.USD for r in results)

    def test_sum_converted(self, reporting_engine):
        transactions = [
            (Money(amount=Decimal("83500"), currency=CurrencyCode.INR), date(2026, 1, 1)),
            (Money(amount=Decimal("83500"), currency=CurrencyCode.INR), date(2026, 1, 1)),
        ]
        total = reporting_engine.sum_converted(transactions, CurrencyCode.USD)
        assert total.currency == CurrencyCode.USD
        assert total.amount > 0

    def test_audit_trail(self, reporting_engine):
        amount = Money(amount=Decimal("83500"), currency=CurrencyCode.INR)
        result = reporting_engine.convert_transaction(
            amount, CurrencyCode.USD, date.today()
        )
        audit = result.to_dict()
        assert audit["original_currency"] == "INR"
        assert audit["converted_currency"] == "USD"
        assert "rate" in audit
        assert "rate_source" in audit


# ============================================================
# TENANT CURRENCY CONFIG TESTS
# ============================================================

class TestTenantCurrencyConfig:
    def test_default_config(self):
        config = TenantCurrencyConfig(tenant_id=uuid.uuid4())
        assert config.default_transaction_currency == CurrencyCode.INR
        assert config.reporting_currency == CurrencyCode.USD
        assert config.fx_source == "manual"

    def test_custom_config(self):
        config = TenantCurrencyConfig(
            tenant_id=uuid.uuid4(),
            transaction_currencies=[CurrencyCode.USD, CurrencyCode.EUR],
            default_transaction_currency=CurrencyCode.USD,
            reporting_currency=CurrencyCode.USD,
            fx_source="ecb",
        )
        assert config.reporting_currency == CurrencyCode.USD
