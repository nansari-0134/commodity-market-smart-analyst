"""
Exchange Master, Trading Sessions, and Holiday Calendars.

Implements architectural specifications from:
- Section 10 (Major Metadata Entities: exchange_master)
- Section 11 (Commodity Hierarchy: Exchange -> Commodity -> Product -> Instrument -> Contract)
- Section 13 (Market Data & Exchange Reference Standards)
"""
from datetime import date as dt_date
import zoneinfo
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import UUIDModel, TimeStampedModel


class ExchangeTier(models.TextChoices):
    """Classification tier of trading venue."""
    GLOBAL_BENCHMARK = "GLOBAL_BENCHMARK", "Global Benchmark Venue"
    REGIONAL_PRIMARY = "REGIONAL_PRIMARY", "Regional Primary Exchange"
    DOMESTIC = "DOMESTIC", "Domestic / Local Venue"


class ExchangeMaster(UUIDModel, TimeStampedModel):
    """
    Master entity representing a clearinghouse, futures exchange, or physical trading venue.
    Forms the root of the financial instrument hierarchy (Section 11).
    """
    code = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="Canonical internal symbol (e.g. 'CME', 'NYMEX', 'ICE_EU', 'IFAD', 'B3', 'BMD')",
    )
    name = models.CharField(
        max_length=128,
        help_text="Full legal/operating name of the exchange",
    )
    mic = models.CharField(
        max_length=4,
        unique=True,
        db_index=True,
        help_text="ISO 10383 Market Identifier Code (e.g. 'XNYM', 'XCME', 'IFEU', 'IFAD', 'BVMF', 'XKLS')",
    )
    operating_mic = models.CharField(
        max_length=4,
        blank=True,
        default="",
        help_text="Parent Operating MIC if different from venue MIC (e.g. 'XCME' for NYMEX/COMEX)",
    )
    country = models.CharField(
        max_length=2,
        db_index=True,
        help_text="ISO 3166-1 alpha-2 country code (e.g. 'US', 'GB', 'BR', 'MY', 'AE', 'IN', 'CN')",
    )
    city = models.CharField(
        max_length=64,
        help_text="Primary financial center / headquarters city",
    )
    timezone = models.CharField(
        max_length=64,
        help_text="IANA standard timezone (e.g. 'America/Chicago', 'America/Sao_Paulo', 'Asia/Kuala_Lumpur', 'Asia/Dubai')",
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Primary quote/settlement currency ISO code (e.g. 'USD', 'BRL', 'MYR', 'EUR')",
    )
    tier = models.CharField(
        max_length=32,
        choices=ExchangeTier.choices,
        default=ExchangeTier.GLOBAL_BENCHMARK,
        db_index=True,
        help_text="Venue hierarchy classification tier",
    )
    website_url = models.URLField(
        blank=True,
        default="",
        help_text="Official exchange portal or trading calendar URL",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Flag indicating if venue is active for data ingestion and trading",
    )

    class Meta:
        verbose_name = "Exchange Master"
        verbose_name_plural = "Exchange Masters"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["country", "tier"]),
            models.Index(fields=["is_active", "code"]),
        ]

    def __str__(self):
        return f"{self.code} [{self.mic}] - {self.name}"

    def clean(self):
        """Validates that the provided timezone string is a valid IANA timezone."""
        super().clean()
        if self.timezone:
            try:
                zoneinfo.ZoneInfo(self.timezone)
            except Exception as e:
                raise ValidationError({"timezone": f"Invalid IANA timezone '{self.timezone}': {str(e)}"})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def tz_info(self) -> zoneinfo.ZoneInfo:
        """Returns the zoneinfo.ZoneInfo object for this exchange."""
        return zoneinfo.ZoneInfo(self.timezone)

    def is_trading_day(self, check_date: dt_date, product_group: str | None = None) -> bool:
        """
        Determines whether a given calendar date is an active trading day on this exchange.
        Returns False on weekends (Saturday=5, Sunday=6) and full exchange closure holidays.
        Takes into account partial sessions (e.g. electronic trading open without settlement)
        and product-group-specific closures.
        """
        if check_date.weekday() >= 5:
            return False

        holiday = self.holidays.filter(date=check_date, is_active=True).first()
        if not holiday:
            return True

        # Check if this holiday is restricted to a specific product group
        if product_group and holiday.affected_product_groups and holiday.affected_product_groups != "ALL":
            affected_groups = [g.strip().upper() for g in holiday.affected_product_groups.split(",")]
            if product_group.strip().upper() not in affected_groups:
                # This product group is not affected by this holiday closure
                return True

        # If it has trading explicitly (e.g. holiday electronic session), it's a trading day
        if holiday.has_trading:
            return True

        # Full day closure without trading
        if holiday.is_full_day_closure:
            return False

        # Early close partial day has trading
        return True

    def is_settlement_day(self, check_date: dt_date, product_group: str | None = None) -> bool:
        """
        Determines whether official daily settlement prices are established for this calendar date.
        Returns False on weekends, full closures, and holiday trading sessions where settlement rolls
        forward to the next business day (e.g. CME Memorial Day electronic trading).
        """
        if check_date.weekday() >= 5:
            return False

        holiday = self.holidays.filter(date=check_date, is_active=True).first()
        if not holiday:
            return True

        if product_group and holiday.affected_product_groups and holiday.affected_product_groups != "ALL":
            affected_groups = [g.strip().upper() for g in holiday.affected_product_groups.split(",")]
            if product_group.strip().upper() not in affected_groups:
                return True

        return holiday.has_settlement

    def get_market_status(self, check_date: dt_date, product_group: str | None = None) -> dict:
        """
        Returns rich diagnostic market status for an exchange on a given date.
        """
        is_weekend = check_date.weekday() >= 5
        if is_weekend:
            return {
                "date": check_date.isoformat(),
                "is_weekend": True,
                "is_trading_day": False,
                "is_settlement_day": False,
                "status": "WEEKEND",
                "holiday_name": None,
                "has_trading": False,
                "has_settlement": False,
                "settlement_rolled": False,
                "early_close_time": None,
                "affected_product_groups": None,
            }

        holiday = self.holidays.filter(date=check_date, is_active=True).first()
        if not holiday:
            return {
                "date": check_date.isoformat(),
                "is_weekend": False,
                "is_trading_day": True,
                "is_settlement_day": True,
                "status": "REGULAR_TRADING",
                "holiday_name": None,
                "has_trading": True,
                "has_settlement": True,
                "settlement_rolled": False,
                "early_close_time": None,
                "affected_product_groups": "ALL",
            }

        # Check product group filtering
        is_affected = True
        if product_group and holiday.affected_product_groups and holiday.affected_product_groups != "ALL":
            affected_groups = [g.strip().upper() for g in holiday.affected_product_groups.split(",")]
            is_affected = product_group.strip().upper() in affected_groups

        if not is_affected:
            return {
                "date": check_date.isoformat(),
                "is_weekend": False,
                "is_trading_day": True,
                "is_settlement_day": True,
                "status": "REGULAR_TRADING",
                "holiday_name": holiday.name,
                "has_trading": True,
                "has_settlement": True,
                "settlement_rolled": False,
                "early_close_time": None,
                "affected_product_groups": holiday.affected_product_groups,
            }

        # Determine state
        if holiday.is_full_day_closure and not holiday.has_trading:
            status_str = "FULL_DAY_CLOSURE"
        elif holiday.has_trading and not holiday.has_settlement:
            status_str = "TRADING_WITHOUT_SETTLEMENT"
        elif holiday.has_trading and holiday.has_settlement and holiday.early_close_time_local:
            status_str = "EARLY_CLOSE_WITH_SETTLEMENT"
        elif holiday.has_trading and holiday.has_settlement:
            status_str = "TRADING_WITH_SETTLEMENT"
        else:
            status_str = "PARTIAL_CLOSURE"

        return {
            "date": check_date.isoformat(),
            "is_weekend": False,
            "is_trading_day": self.is_trading_day(check_date, product_group=product_group),
            "is_settlement_day": holiday.has_settlement,
            "status": status_str,
            "holiday_name": holiday.name,
            "has_trading": holiday.has_trading,
            "has_settlement": holiday.has_settlement,
            "settlement_rolled": holiday.settlement_rolled_to_next_day,
            "early_close_time": holiday.early_close_time_local.strftime("%H:%M:%S") if holiday.early_close_time_local else None,
            "affected_product_groups": holiday.affected_product_groups,
        }



class SessionType(models.TextChoices):
    """Trading session category."""
    ELECTRONIC = "ELECTRONIC", "Electronic Trading (Globex/Web)"
    OPEN_OUTCRY = "OPEN_OUTCRY", "Open Outcry / Floor Pit"
    SETTLEMENT_WINDOW = "SETTLEMENT_WINDOW", "Official Daily Settlement Window"
    MAINTENANCE_PAUSE = "MAINTENANCE_PAUSE", "Daily Maintenance / System Pause"


class ExchangeTradingSession(UUIDModel, TimeStampedModel):
    """
    Operating hours and settlement windows for an exchange in local exchange time.
    """
    exchange = models.ForeignKey(
        ExchangeMaster,
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="Associated exchange venue",
    )
    session_type = models.CharField(
        max_length=32,
        choices=SessionType.choices,
        default=SessionType.ELECTRONIC,
        db_index=True,
    )
    name = models.CharField(
        max_length=128,
        help_text="Description (e.g. 'Globex Electronic Continuous Trading')",
    )
    start_time_local = models.TimeField(
        help_text="Opening time in exchange local time",
    )
    end_time_local = models.TimeField(
        help_text="Closing time in exchange local time",
    )
    days_of_week = models.CharField(
        max_length=32,
        default="MON,TUE,WED,THU,FRI",
        help_text="Comma-separated active days of week",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Flag indicating if this session definition is currently active",
    )

    class Meta:
        verbose_name = "Trading Session"
        verbose_name_plural = "Trading Sessions"
        ordering = ["exchange", "start_time_local"]

    def __str__(self):
        return f"{self.exchange.code} - {self.name} ({self.start_time_local} to {self.end_time_local})"


class ExchangeHoliday(UUIDModel, TimeStampedModel):
    """
    Calendar closures and early closes for an exchange.
    Essential for calculating contract expiration dates (Section 11) and avoiding bad tick alerts.
    """
    exchange = models.ForeignKey(
        ExchangeMaster,
        on_delete=models.CASCADE,
        related_name="holidays",
        help_text="Associated exchange venue",
    )
    date = models.DateField(
        db_index=True,
        help_text="Calendar date of closure",
    )
    name = models.CharField(
        max_length=128,
        help_text="Official holiday title (e.g. 'Good Friday', 'Thanksgiving', 'Carnaval')",
    )
    is_full_day_closure = models.BooleanField(
        default=True,
        help_text="True if exchange is completely closed; False if partial-day early close",
    )
    has_trading = models.BooleanField(
        default=False,
        help_text="True if electronic matching engines operate for trading on this date",
    )
    has_settlement = models.BooleanField(
        default=False,
        help_text="True if official daily settlement prices are established for this trade date",
    )
    settlement_rolled_to_next_day = models.BooleanField(
        default=False,
        help_text="True if trades executed on this date clear and settle under the next business day (e.g. CME holiday roll)",
    )
    affected_product_groups = models.CharField(
        max_length=255,
        default="ALL",
        blank=True,
        help_text="Commodity sectors affected (e.g. 'ALL', 'ENERGY,METALS', 'AGRICULTURE', 'EVENING_SESSION_OPEN')",
    )
    early_close_time_local = models.TimeField(
        null=True,
        blank=True,
        help_text="Early session close time in local exchange timezone (if partial-day)",
    )
    source_api = models.CharField(
        max_length=64,
        blank=True,
        default="OFFICIAL_CALENDAR",
        help_text="Provenance of holiday record (e.g. 'NAGER_DATE_API', 'EXCHANGE_CALENDAR', 'MANUAL')",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    class Meta:
        verbose_name = "Exchange Holiday"
        verbose_name_plural = "Exchange Holidays"
        unique_together = ("exchange", "date")
        ordering = ["date"]
        indexes = [
            models.Index(fields=["exchange", "date", "is_full_day_closure"]),
        ]

    def __str__(self):
        closure_desc = "Closed" if self.is_full_day_closure else f"Early close @ {self.early_close_time_local}"
        return f"{self.exchange.code} Holiday: {self.name} ({self.date}) - {closure_desc}"
