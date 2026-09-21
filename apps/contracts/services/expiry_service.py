"""
Institutional Contract Expiry Calculation Service.

Provides deterministic date arithmetic for commodity futures and derivatives.
Calculates exact last trading days, notice days, physical delivery windows,
and settlement dates while accounting for exchange holiday closures and weekend shifts.
"""

from calendar import monthrange
from datetime import date as dt_date, timedelta
import logging
from typing import Dict, Any

from apps.contracts.models import (
    ContractSpecification,
    ExpiryRuleType,
    MonthCode,
    MONTH_NUMBER_TO_CODE,
    CODE_TO_MONTH_NUMBER,
    SettlementMethod,
)
from apps.exchanges.models import ExchangeMaster, ExchangeHoliday

logger = logging.getLogger("apps.contracts")


def month_to_code(month: int) -> str:
    """Convert integer month (1-12) to standard commodity futures code (F-Z)."""
    if month not in MONTH_NUMBER_TO_CODE:
        raise ValueError(f"Invalid month number: {month}. Must be 1-12.")
    return MONTH_NUMBER_TO_CODE[month].value


def code_to_month(code: str) -> int:
    """Convert standard commodity futures code (F-Z) to integer month (1-12)."""
    clean_code = code.strip().upper()
    if clean_code not in CODE_TO_MONTH_NUMBER:
        raise ValueError(f"Invalid month code: '{code}'. Valid codes: {list(CODE_TO_MONTH_NUMBER.keys())}")
    return CODE_TO_MONTH_NUMBER[clean_code]


def generate_contract_symbol(symbol_root: str, year: int, month: int) -> str:
    """
    Generate standard institutional futures ticker symbol.
    Example: CL, 2026, 12 -> CLZ26
    """
    m_code = month_to_code(month)
    y_short = str(year)[-2:]
    return f"{symbol_root}{m_code}{y_short}"


class ContractExpiryService:
    """
    Calculates deterministic last trading dates, notice dates, and settlement schedules
    for commodity derivatives across global venues.
    """

    @classmethod
    def is_exchange_trading_day(cls, exchange: ExchangeMaster, target_date: dt_date) -> bool:
        """
        Determines whether the exchange is open for trading on target_date.
        Checks for weekend closures (Mon-Fri default) and registered full-day exchange holidays.
        """
        # Weekends (Saturday = 5, Sunday = 6)
        if target_date.weekday() >= 5:
            return False

        # Check full day exchange holiday
        is_holiday = ExchangeHoliday.objects.filter(
            exchange=exchange,
            date=target_date,
            is_full_day_closure=True,
            is_active=True,
        ).exists()

        return not is_holiday

    @classmethod
    def get_previous_trading_day(cls, exchange: ExchangeMaster, start_date: dt_date) -> dt_date:
        """Find the most recent trading day strictly prior to start_date."""
        candidate = start_date - timedelta(days=1)
        while not cls.is_exchange_trading_day(exchange, candidate):
            candidate -= timedelta(days=1)
        return candidate

    @classmethod
    def get_next_trading_day(cls, exchange: ExchangeMaster, start_date: dt_date) -> dt_date:
        """Find the nearest trading day strictly following start_date."""
        candidate = start_date + timedelta(days=1)
        while not cls.is_exchange_trading_day(exchange, candidate):
            candidate += timedelta(days=1)
        return candidate

    @classmethod
    def subtract_trading_days(cls, exchange: ExchangeMaster, start_date: dt_date, n_days: int) -> dt_date:
        """Count backward exactly n trading days from start_date."""
        current = start_date
        count = 0
        while count < n_days:
            current = cls.get_previous_trading_day(exchange, current)
            count += 1
        return current

    @classmethod
    def calculate_last_trading_day(
        cls,
        spec: ContractSpecification,
        year: int,
        month: int,
    ) -> dt_date:
        """
        Determines the exact last trading day according to the specification's expiry rule.
        """
        exchange = spec.exchange
        rule = spec.expiry_rule
        param = spec.expiry_rule_parameter or 3

        if rule == ExpiryRuleType.DAYS_BEFORE_MONTH_START:
            # First day of the delivery month
            first_of_month = dt_date(year, month, 1)
            # Count back param trading days
            return cls.subtract_trading_days(exchange, first_of_month, param)

        elif rule == ExpiryRuleType.DAY_OF_PRIOR_MONTH_WITH_BUS_OFFSET:
            # e.g., NYMEX WTI rule: 25th calendar day of prior month.
            # If 25th is not a business day, trading terminates on the 3rd business day prior to the 25th.
            prior_year = year if month > 1 else year - 1
            prior_month = month - 1 if month > 1 else 12
            _, max_day = monthrange(prior_year, prior_month)
            day_target = min(param, max_day)
            calendar_target = dt_date(prior_year, prior_month, day_target)

            if cls.is_exchange_trading_day(exchange, calendar_target):
                return calendar_target
            else:
                # 3rd business day prior to the 25th
                offset = 3
                candidate = calendar_target
                count = 0
                while count < offset:
                    candidate = cls.get_previous_trading_day(exchange, candidate)
                    count += 1
                return candidate

        elif rule == ExpiryRuleType.BUSINESS_DAY_BEFORE_DAY_OF_MONTH:
            # e.g., CBOT Grains: business day preceding the 15th calendar day of the contract month
            day_target = min(param, 28)
            ref_date = dt_date(year, month, day_target)
            return cls.get_previous_trading_day(exchange, ref_date)

        elif rule == ExpiryRuleType.LAST_BUSINESS_DAY_OF_PRIOR_MONTH:
            prior_year = year if month > 1 else year - 1
            prior_month = month - 1 if month > 1 else 12
            _, max_day = monthrange(prior_year, prior_month)
            end_of_prior_month = dt_date(prior_year, prior_month, max_day)
            if cls.is_exchange_trading_day(exchange, end_of_prior_month):
                return end_of_prior_month
            return cls.get_previous_trading_day(exchange, end_of_prior_month)

        elif rule == ExpiryRuleType.LAST_BUSINESS_DAY_OF_TWO_MONTHS_PRIOR:
            # e.g., ICE Brent: ceases on the last business day of the second month preceding the delivery month
            m2 = month - 2
            y2 = year
            if m2 <= 0:
                m2 += 12
                y2 -= 1
            _, max_day = monthrange(y2, m2)
            end_of_m2 = dt_date(y2, m2, max_day)
            if cls.is_exchange_trading_day(exchange, end_of_m2):
                return end_of_m2
            return cls.get_previous_trading_day(exchange, end_of_m2)

        elif rule == ExpiryRuleType.THIRD_WEDNESDAY_OF_MONTH:
            # e.g., LME Prompt Date: Third Wednesday of the delivery month
            first_day = dt_date(year, month, 1)
            # Days to first Wednesday (Wednesday is weekday 2)
            days_to_first_wed = (2 - first_day.weekday()) % 7
            first_wed = first_day + timedelta(days=days_to_first_wed)
            third_wed = first_wed + timedelta(weeks=2)
            if cls.is_exchange_trading_day(exchange, third_wed):
                return third_wed
            return cls.get_previous_trading_day(exchange, third_wed)

        elif rule == ExpiryRuleType.FIFTH_BUSINESS_DAY_BEFORE_MONTH_END:
            _, max_day = monthrange(year, month)
            month_end = dt_date(year, month, max_day)
            return cls.subtract_trading_days(exchange, month_end, param)

        else:
            # Default fallback: 3 business days before month start
            first_of_month = dt_date(year, month, 1)
            return cls.subtract_trading_days(exchange, first_of_month, 3)

    @classmethod
    def calculate_contract_schedule(
        cls,
        spec: ContractSpecification,
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """
        Computes the complete delivery schedule for a contract month:
        - Contract symbol
        - Last trading day
        - First notice day (if physical)
        - Last delivery day (if physical)
        - Final settlement date
        """
        symbol = generate_contract_symbol(spec.symbol_root, year, month)
        m_code = month_to_code(month)
        last_trading = cls.calculate_last_trading_day(spec, year, month)

        first_notice = None
        last_delivery = None

        if spec.settlement_method == SettlementMethod.PHYSICAL:
            # First notice day is typically the last business day of the month preceding delivery month
            prior_year = year if month > 1 else year - 1
            prior_month = month - 1 if month > 1 else 12
            _, max_day = monthrange(prior_year, prior_month)
            end_prior = dt_date(prior_year, prior_month, max_day)
            first_notice = end_prior if cls.is_exchange_trading_day(spec.exchange, end_prior) else cls.get_previous_trading_day(spec.exchange, end_prior)

            # Last delivery day is typically the last business day of the delivery month
            _, max_del_day = monthrange(year, month)
            end_delivery_month = dt_date(year, month, max_del_day)
            last_delivery = end_delivery_month if cls.is_exchange_trading_day(spec.exchange, end_delivery_month) else cls.get_previous_trading_day(spec.exchange, end_delivery_month)

        # Final settlement is either last trading day or next business day
        final_settlement = cls.get_next_trading_day(spec.exchange, last_trading)

        return {
            "contract_symbol": symbol,
            "contract_year": year,
            "contract_month": month,
            "contract_month_code": m_code,
            "last_trading_day": last_trading,
            "first_notice_day": first_notice,
            "last_delivery_day": last_delivery,
            "final_settlement_date": final_settlement,
        }
