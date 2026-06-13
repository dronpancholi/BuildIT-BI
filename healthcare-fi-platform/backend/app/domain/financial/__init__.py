"""
Domain 1: Financial Architecture — Currency, FX, Money.
The canonical financial foundation for the entire platform.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple


# ============================================================
# CURRENCY CODE (ISO 4217)
# ============================================================

class CurrencyCode(Enum):
    """ISO 4217 currency codes with numeric codes."""
    INR = ("INR", 356)
    USD = ("USD", 840)
    EUR = ("EUR", 978)
    GBP = ("GBP", 826)
    JPY = ("JPY", 392)
    AED = ("AED", 784)
    SAR = ("SAR", 682)
    SGD = ("SGD", 702)
    AUD = ("AUD", 36)
    CAD = ("CAD", 124)
    CHF = ("CHF", 756)
    CNY = ("CNY", 156)
    BHD = ("BHD", 48)
    KWD = ("KWD", 414)
    OMR = ("OMR", 512)
    QAR = ("QAR", 634)

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def numeric_code(self) -> int:
        return self.value[1]


# ============================================================
# CURRENCY (canonical)
# ============================================================

@dataclass(frozen=True)
class Currency:
    """Complete currency definition with formatting rules."""
    code: CurrencyCode
    name: str
    symbol: str
    decimal_places: int
    sub_unit: str
    country_codes: tuple  # ISO 3166
    is_active: bool = True
    effective_from: date = field(default_factory=date.today)
    effective_to: Optional[date] = None

    def format_amount(self, amount: Decimal) -> str:
        """Format amount with currency-specific rules."""
        rounded = self.round_amount(amount)
        if self.decimal_places == 0:
            formatted = f"{int(rounded):,}"
        else:
            formatted = f"{rounded:,.{self.decimal_places}f}"
        return f"{self.symbol}{formatted}"

    def round_amount(self, amount: Decimal) -> Decimal:
        """Round amount to currency-specific decimal places."""
        quantize_str = "1" if self.decimal_places == 0 else f"0.{'0' * self.decimal_places}"
        return amount.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)


# ============================================================
# PRE-DEFINED CURRENCIES
# ============================================================

CURRENCIES = {
    CurrencyCode.INR: Currency(
        code=CurrencyCode.INR, name="Indian Rupee", symbol="₹",
        decimal_places=2, sub_unit="Paise",
        country_codes=("IN",),
    ),
    CurrencyCode.USD: Currency(
        code=CurrencyCode.USD, name="United States Dollar", symbol="$",
        decimal_places=2, sub_unit="Cents",
        country_codes=("US",),
    ),
    CurrencyCode.EUR: Currency(
        code=CurrencyCode.EUR, name="Euro", symbol="€",
        decimal_places=2, sub_unit="Cents",
        country_codes=("DE", "FR", "IT", "ES", "NL", "BE", "AT", "IE", "PT", "FI", "GR"),
    ),
    CurrencyCode.GBP: Currency(
        code=CurrencyCode.GBP, name="British Pound", symbol="£",
        decimal_places=2, sub_unit="Pence",
        country_codes=("GB",),
    ),
    CurrencyCode.JPY: Currency(
        code=CurrencyCode.JPY, name="Japanese Yen", symbol="¥",
        decimal_places=0, sub_unit="Sen",
        country_codes=("JP",),
    ),
    CurrencyCode.AED: Currency(
        code=CurrencyCode.AED, name="UAE Dirham", symbol="AED",
        decimal_places=2, sub_unit="Fils",
        country_codes=("AE",),
    ),
    CurrencyCode.BHD: Currency(
        code=CurrencyCode.BHD, name="Bahraini Dinar", symbol="BD",
        decimal_places=3, sub_unit="Fils",
        country_codes=("BH",),
    ),
    CurrencyCode.SAR: Currency(
        code=CurrencyCode.SAR, name="Saudi Riyal", symbol="﷼",
        decimal_places=2, sub_unit="Halalas",
        country_codes=("SA",),
    ),
    CurrencyCode.SGD: Currency(
        code=CurrencyCode.SGD, name="Singapore Dollar", symbol="S$",
        decimal_places=2, sub_unit="Cents",
        country_codes=("SG",),
    ),
    CurrencyCode.AUD: Currency(
        code=CurrencyCode.AUD, name="Australian Dollar", symbol="A$",
        decimal_places=2, sub_unit="Cents",
        country_codes=("AU",),
    ),
    CurrencyCode.CAD: Currency(
        code=CurrencyCode.CAD, name="Canadian Dollar", symbol="C$",
        decimal_places=2, sub_unit="Cents",
        country_codes=("CA",),
    ),
    CurrencyCode.CHF: Currency(
        code=CurrencyCode.CHF, name="Swiss Franc", symbol="CHF",
        decimal_places=2, sub_unit="Rappen",
        country_codes=("CH",),
    ),
    CurrencyCode.CNY: Currency(
        code=CurrencyCode.CNY, name="Chinese Yuan", symbol="¥",
        decimal_places=2, sub_unit="Fen",
        country_codes=("CN",),
    ),
    CurrencyCode.KWD: Currency(
        code=CurrencyCode.KWD, name="Kuwaiti Dinar", symbol="KD",
        decimal_places=3, sub_unit="Fils",
        country_codes=("KW",),
    ),
    CurrencyCode.OMR: Currency(
        code=CurrencyCode.OMR, name="Omani Rial", symbol="﷼",
        decimal_places=3, sub_unit="Baisa",
        country_codes=("OM",),
    ),
    CurrencyCode.QAR: Currency(
        code=CurrencyCode.QAR, name="Qatari Riyal", symbol="QR",
        decimal_places=2, sub_unit="Dirhams",
        country_codes=("QA",),
    ),
}


# ============================================================
# EXCHANGE RATE
# ============================================================

@dataclass(frozen=True)
class ExchangeRate:
    """Immutable exchange rate record."""
    id: uuid.UUID
    base_currency: CurrencyCode
    target_currency: CurrencyCode
    rate: Decimal
    inverse_rate: Decimal
    effective_date: date
    source: str
    source_url: Optional[str] = None
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    is_estimated: bool = False
    is_confirmed: bool = False

    def convert(self, amount: Decimal) -> Decimal:
        """Convert amount from base to target currency."""
        return (amount * self.rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


# ============================================================
# MONEY VALUE OBJECT
# ============================================================

@dataclass(frozen=True, slots=True)
class Money:
    """
    Canonical money representation. Every monetary amount in the system
    has exactly one representation: Money(amount, currency).

    Invariants:
    - amount is Decimal (never float)
    - currency is CurrencyCode
    - All arithmetic is currency-aware
    - Formatting respects locale conventions
    """
    amount: Decimal
    currency: CurrencyCode

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise TypeError(
                f"Cannot add Money with different currencies: "
                f"{self.currency.code} + {other.currency.code}. "
                f"Convert to same currency first."
            )
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise TypeError(
                f"Cannot subtract Money with different currencies: "
                f"{self.currency.code} - {other.currency.code}. "
                f"Convert to same currency first."
            )
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, scalar) -> "Money":
        if isinstance(scalar, (int, float, Decimal)):
            return Money(amount=self.amount * Decimal(str(scalar)), currency=self.currency)
        raise TypeError(f"Cannot multiply Money by {type(scalar)}")

    def __rmul__(self, scalar) -> "Money":
        return self.__mul__(scalar)

    def __truediv__(self, other: "Money") -> Decimal:
        if self.currency != other.currency:
            raise TypeError(
                f"Cannot divide Money with different currencies: "
                f"{self.currency.code} / {other.currency.code}"
            )
        if other.amount == 0:
            raise ZeroDivisionError("Cannot divide Money by zero")
        return self.amount / other.amount

    def __neg__(self) -> "Money":
        return Money(amount=-self.amount, currency=self.currency)

    def __abs__(self) -> "Money":
        return Money(amount=abs(self.amount), currency=self.currency)

    def __gt__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            raise TypeError(f"Cannot compare Money with different currencies")
        return self.amount > other.amount

    def __lt__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            raise TypeError(f"Cannot compare Money with different currencies")
        return self.amount < other.amount

    def __ge__(self, other: "Money") -> bool:
        return self == other or self > other

    def __le__(self, other: "Money") -> bool:
        return self == other or self < other

    def is_zero(self) -> bool:
        return self.amount == 0

    def is_positive(self) -> bool:
        return self.amount > 0

    def is_negative(self) -> bool:
        return self.amount < 0

    def round(self) -> "Money":
        """Round to currency-specific decimal places."""
        currency_def = CURRENCIES.get(self.currency)
        if currency_def:
            return Money(amount=currency_def.round_amount(self.amount), currency=self.currency)
        return self

    def format(self, locale: str = "en_IN") -> str:
        """Format with locale-specific conventions."""
        currency_def = CURRENCIES.get(self.currency)
        if currency_def:
            return currency_def.format_amount(self.amount)
        return f"{self.currency.code} {self.amount}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount": str(self.amount),
            "currency": self.currency.code,
            "formatted": self.format(),
        }

    @classmethod
    def zero(cls, currency: CurrencyCode) -> "Money":
        return cls(amount=Decimal("0"), currency=currency)

    @classmethod
    def from_float(cls, amount: float, currency: CurrencyCode) -> "Money":
        return cls(amount=Decimal(str(amount)), currency=currency)


# ============================================================
# TENANT CURRENCY CONFIGURATION
# ============================================================

@dataclass
class TenantCurrencyConfig:
    """Per-tenant currency configuration."""
    tenant_id: uuid.UUID
    transaction_currencies: List[CurrencyCode] = field(default_factory=lambda: [CurrencyCode.INR])
    default_transaction_currency: CurrencyCode = CurrencyCode.INR
    reporting_currency: CurrencyCode = CurrencyCode.USD
    fx_source: str = "manual"
    fx_update_frequency: str = "daily"


# ============================================================
# REPORTING CURRENCY ENGINE
# ============================================================

@dataclass(frozen=True)
class ConvertedAmount:
    """Result of a currency conversion with full audit trail."""
    original: Money
    converted: Money
    rate: ExchangeRate
    conversion_timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_amount": str(self.original.amount),
            "original_currency": self.original.currency.code,
            "converted_amount": str(self.converted.amount),
            "converted_currency": self.converted.currency.code,
            "rate": str(self.rate.rate),
            "rate_date": self.rate.effective_date.isoformat(),
            "rate_source": self.rate.source,
            "is_estimated": self.rate.is_estimated,
        }


class ReportingCurrencyEngine:
    """
    Converts transaction currencies to reporting currency.
    Every conversion is auditable — original amount + rate used are preserved.

    Design invariant:
    - Transaction currency amount is IMMUTABLE
    - Reporting currency is DERIVED (re-computable from FX table + original)
    - Every report states its currency and FX source
    - FX rates used are stored with the report snapshot
    """

    def __init__(self, fx_service: "FXService"):
        self._fx = fx_service

    def convert_transaction(
        self,
        amount: Money,
        reporting_currency: CurrencyCode,
        transaction_date: date,
    ) -> ConvertedAmount:
        """Convert a single transaction amount to reporting currency."""
        if amount.currency == reporting_currency:
            rate = ExchangeRate(
                id=uuid.uuid4(),
                base_currency=amount.currency,
                target_currency=reporting_currency,
                rate=Decimal("1"),
                inverse_rate=Decimal("1"),
                effective_date=transaction_date,
                source="identity",
                is_estimated=False,
                is_confirmed=True,
            )
            return ConvertedAmount(
                original=amount,
                converted=amount,
                rate=rate,
            )

        rate = self._fx.get_rate(amount.currency, reporting_currency, transaction_date)
        converted_value = rate.convert(amount.amount)
        converted = Money(amount=converted_value, currency=reporting_currency)

        return ConvertedAmount(
            original=amount,
            converted=converted,
            rate=rate,
        )

    def convert_batch(
        self,
        transactions: List[Tuple[Money, date]],
        reporting_currency: CurrencyCode,
    ) -> List[ConvertedAmount]:
        """Convert a batch of transactions. Returns list of ConvertedAmount."""
        return [
            self.convert_transaction(amount, reporting_currency, txn_date)
            for amount, txn_date in transactions
        ]

    def sum_converted(
        self,
        transactions: List[Tuple[Money, date]],
        reporting_currency: CurrencyCode,
    ) -> Money:
        """Convert and sum a batch of transactions into a single reporting amount."""
        converted = self.convert_batch(transactions, reporting_currency)
        total = Money.zero(reporting_currency)
        for c in converted:
            total = total + c.converted
        return total
