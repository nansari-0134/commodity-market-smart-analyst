"""
Contract and Derivative Models.

Provides canonical futures contract specifications, standardized month codes (F-Z),
contract delivery cycles, institutional expiry calculation parameters,
and benchmark index roll conventions.
"""

from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import UUIDModel, TimeStampedModel


class InstrumentType(models.TextChoices):
    FUTURES = "FUTURES", _("Physical/Cash Futures")
    OPTIONS_AMERICAN = "OPTIONS_AMERICAN", _("American Vanilla Options")
    OPTIONS_EUROPEAN = "OPTIONS_EUROPEAN", _("European Vanilla Options")
    CALENDAR_SPREAD = "CALENDAR_SPREAD", _("Calendar Spread")
    BASIS_SWAP = "BASIS_SWAP", _("Basis Swap")


class ExpiryRuleType(models.TextChoices):
    DAYS_BEFORE_MONTH_START = (
        "DAYS_BEFORE_MONTH_START",
        _("N Business Days Before Delivery Month Start"),
    )
    DAY_OF_PRIOR_MONTH_WITH_BUS_OFFSET = (
        "DAY_OF_PRIOR_MONTH_WITH_BUS_OFFSET",
        _("Specific Calendar Day of Prior Month (Rolled to Prior Business Day)"),
    )
    BUSINESS_DAY_BEFORE_DAY_OF_MONTH = (
        "BUSINESS_DAY_BEFORE_DAY_OF_MONTH",
        _("Business Day Preceding Specific Day of Delivery Month"),
    )
    LAST_BUSINESS_DAY_OF_PRIOR_MONTH = (
        "LAST_BUSINESS_DAY_OF_PRIOR_MONTH",
        _("Last Business Day of Month Preceding Delivery Month"),
    )
    LAST_BUSINESS_DAY_OF_TWO_MONTHS_PRIOR = (
        "LAST_BUSINESS_DAY_OF_TWO_MONTHS_PRIOR",
        _("Last Business Day of Second Month Preceding Delivery Month"),
    )
    THIRD_WEDNESDAY_OF_MONTH = (
        "THIRD_WEDNESDAY_OF_MONTH",
        _("Third Wednesday of Delivery Month"),
    )
    FIFTH_BUSINESS_DAY_BEFORE_MONTH_END = (
        "FIFTH_BUSINESS_DAY_BEFORE_MONTH_END",
        _("Nth Business Day Preceding Contract Month End"),
    )


class MonthCode(models.TextChoices):
    F = "F", _("January (F)")
    G = "G", _("February (G)")
    H = "H", _("March (H)")
    J = "J", _("April (J)")
    K = "K", _("May (K)")
    M = "M", _("June (M)")
    N = "N", _("July (N)")
    Q = "Q", _("August (Q)")
    U = "U", _("September (U)")
    V = "V", _("October (V)")
    X = "X", _("November (X)")
    Z = "Z", _("December (Z)")


MONTH_NUMBER_TO_CODE = {
    1: MonthCode.F,
    2: MonthCode.G,
    3: MonthCode.H,
    4: MonthCode.J,
    5: MonthCode.K,
    6: MonthCode.M,
    7: MonthCode.N,
    8: MonthCode.Q,
    9: MonthCode.U,
    10: MonthCode.V,
    11: MonthCode.X,
    12: MonthCode.Z,
}

CODE_TO_MONTH_NUMBER = {v.value: k for k, v in MONTH_NUMBER_TO_CODE.items()}


class SettlementMethod(models.TextChoices):
    PHYSICAL = "PHYSICAL", _("Physical Delivery")
    CASH = "CASH", _("Cash Settled")


class ContractSpecification(UUIDModel, TimeStampedModel):
    """
    Standardized trading specification for a commodity derivative contract on a specific exchange venue.
    """

    commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.CASCADE,
        related_name="contract_specifications",
        help_text="Canonical physical commodity underpinning this derivative contract.",
    )
    exchange = models.ForeignKey(
        "exchanges.ExchangeMaster",
        on_delete=models.CASCADE,
        related_name="contract_specifications",
        help_text="Operating exchange venue listing this contract.",
    )
    symbol_root = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Exchange ticker root (e.g. CL, B, NG, ZC, ZS, GC, HG, CA, FCPO, CRUDEOIL).",
    )
    name = models.CharField(
        max_length=150,
        help_text="Full commercial name of contract (e.g. Light Sweet Crude Oil Futures).",
    )
    instrument_type = models.CharField(
        max_length=30,
        choices=InstrumentType.choices,
        default=InstrumentType.FUTURES,
        help_text="Instrument classification.",
    )
    contract_size = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        help_text="Contract multiplier quantity (e.g. 1000 for CL = 1,000 barrels).",
    )
    contract_unit = models.ForeignKey(
        "metadata.UnitMaster",
        on_delete=models.PROTECT,
        related_name="contract_size_specs",
        help_text="Unit of measure for the contract size (e.g. BBL, BU, MT, TOZ).",
    )
    price_quote_unit = models.ForeignKey(
        "metadata.UnitMaster",
        on_delete=models.PROTECT,
        related_name="price_quote_specs",
        help_text="Quotation unit of measure (e.g. USD/bbl, USC/bu, USD/t, INR/bbl).",
    )
    minimum_tick_size = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal("0.01"),
        help_text="Minimum allowable price fluctuation.",
    )
    tick_value = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=Decimal("10.00"),
        help_text="Monetary value of a minimum tick move per contract.",
    )
    trading_currency = models.CharField(
        max_length=5,
        default="USD",
        help_text="ISO currency in which the contract prices and settles.",
    )
    settlement_method = models.CharField(
        max_length=20,
        choices=SettlementMethod.choices,
        default=SettlementMethod.PHYSICAL,
        help_text="Binary settlement mechanism: Physical delivery vs Cash settlement.",
    )
    trading_months = models.CharField(
        max_length=100,
        default="ALL_12",
        help_text="Comma-separated month codes (e.g. 'F,G,H,J,K,M,N,Q,U,V,X,Z' or 'F,H,K,N,U,X,Z').",
    )
    expiry_rule = models.CharField(
        max_length=50,
        choices=ExpiryRuleType.choices,
        default=ExpiryRuleType.DAY_OF_PRIOR_MONTH_WITH_BUS_OFFSET,
        help_text="Algorithmic rule used to determine the last trading day.",
    )
    expiry_rule_parameter = models.IntegerField(
        default=25,
        help_text="Rule parameter (e.g. 25 for 25th day of month, 3 for 3 business days offset).",
    )
    notice_rule = models.CharField(
        max_length=200,
        blank=True,
        default="First business day prior to first delivery day",
        help_text="Contract first notice day rule description.",
    )
    default_roll_rule = models.CharField(
        max_length=100,
        default="GSCI_5_TO_9_BUS_DAY",
        help_text="Benchmark roll schedule (e.g. GSCI 5-9 business days, BCOM 6-10 business days).",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this specification is actively traded.",
    )
    display_order = models.PositiveIntegerField(
        default=100,
        help_text="Sorting order in dashboards and analytical tables.",
    )

    class Meta:
        db_table = "contracts_specification"
        ordering = ["display_order", "exchange", "symbol_root"]
        unique_together = [("exchange", "symbol_root")]
        verbose_name = _("Contract Specification")
        verbose_name_plural = _("Contract Specifications")

    def __str__(self) -> str:
        return f"{self.exchange.mic}:{self.symbol_root} ({self.name})"

    @property
    def trading_month_codes(self) -> list[str]:
        """Return list of valid month code strings."""
        if self.trading_months == "ALL_12":
            return [m.value for m in MonthCode]
        return [code.strip().upper() for code in self.trading_months.split(",") if code.strip()]


class ContractExpiry(UUIDModel, TimeStampedModel):
    """
    A specific tradable contract delivery month for an underlying specification.
    Tracks exact calculated termination dates, notice dates, and settlement schedules.
    """

    specification = models.ForeignKey(
        ContractSpecification,
        on_delete=models.CASCADE,
        related_name="expiries",
        help_text="Parent contract specification.",
    )
    contract_symbol = models.CharField(
        max_length=30,
        db_index=True,
        help_text="Full standardized ticker symbol (e.g. CLZ26, BRENTF27, ZCH27).",
    )
    contract_year = models.PositiveSmallIntegerField(
        db_index=True,
        help_text="4-digit contract delivery year (e.g. 2026).",
    )
    contract_month = models.PositiveSmallIntegerField(
        db_index=True,
        help_text="Contract delivery month (1-12).",
    )
    contract_month_code = models.CharField(
        max_length=2,
        choices=MonthCode.choices,
        help_text="Standard futures month letter (F-Z).",
    )
    last_trading_day = models.DateField(
        db_index=True,
        help_text="Exact calculated last trading / expiration date.",
    )
    first_notice_day = models.DateField(
        null=True,
        blank=True,
        help_text="First date exchange issues delivery notices (physical contracts only).",
    )
    last_delivery_day = models.DateField(
        null=True,
        blank=True,
        help_text="Final physical transfer date (physical contracts only).",
    )
    final_settlement_date = models.DateField(
        help_text="Date on which cash settlement or physical invoice is finalized.",
    )
    is_expired = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this delivery contract has completed trading and settled.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether contract is actively monitored.",
    )

    class Meta:
        db_table = "contracts_expiry"
        ordering = ["specification", "contract_year", "contract_month"]
        unique_together = [("specification", "contract_year", "contract_month")]
        verbose_name = _("Contract Expiry")
        verbose_name_plural = _("Contract Expiries")

    def __str__(self) -> str:
        return f"{self.contract_symbol} (Exp: {self.last_trading_day})"
