"""
Static / Benchmark Ingestion Providers.

Provides deterministic, offline-capable historical series for:
1. Daily Exchange Prices (WTI, Brent, Natural Gas, Gold, Corn) with prompt and term curves.
2. Weekly EIA Energy Fundamentals (Commercial Crude Stocks, Cushing, Natural Gas Storage).
3. Weekly CFTC Commitment of Traders (COT) Disaggregated positioning.

Enables instant zero-dependency testing, developer sandboxing, and benchmark replication.
"""

import math
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Optional

from .base import (
    BaseMarketDataProvider,
    BaseFundamentalProvider,
    BaseCOTProvider,
    RawPriceObservation,
    RawFundamentalObservation,
    RawCOTObservation,
)

COMMODITY_ALIASES = {
    "BZ": "BRENT",
    "GC": "GOLD",
    "ZC": "CORN",
}

VARIABLE_ALIASES = {
    "EIA_CRUDE_STOCKS_WEEKLY": "CRUDE_US_TOTAL_COMMERCIAL_STOCKS",
    "CUSHING_INVENTORIES": "CRUDE_CUSHING_STOCKS",
    "EIA_NG_STORAGE_WEEKLY": "NATGAS_LOWER_48_WORKING_STORAGE",
    "EIA_US_CRUDE_PROD": "CRUDE_US_TOTAL_COMMERCIAL_STOCKS",
}


class StaticMarketDataProvider(BaseMarketDataProvider):
    """
    Simulates high-fidelity exchange settlements and OHLCV bars.
    Excludes weekend sessions (Saturday & Sunday).
    """

    @property
    def name(self) -> str:
        return "Static Exchange Settlement Simulator"

    def fetch_price_observations(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs,
    ) -> list[RawPriceObservation]:
        raw_symbol = symbol.upper()
        canonical_symbol = COMMODITY_ALIASES.get(raw_symbol, raw_symbol)

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=90)

        configs = {
            "CL": {"base": 76.50, "amp": 4.50, "vol": 320000, "oi": 1820000},
            "BRENT": {"base": 80.20, "amp": 4.20, "vol": 260000, "oi": 1250000},
            "NG": {"base": 2.45, "amp": 0.40, "vol": 150000, "oi": 1410000},
            "GOLD": {"base": 2580.00, "amp": 60.00, "vol": 210000, "oi": 520000},
            "CORN": {"base": 420.00, "amp": 25.00, "vol": 140000, "oi": 1480000},
        }
        cfg = configs.get(canonical_symbol, {"base": 50.00, "amp": 5.00, "vol": 100000, "oi": 500000})

        observations: list[RawPriceObservation] = []
        cur_date = start_date
        day_idx = 0

        while cur_date <= end_date:
            if cur_date.weekday() < 5:
                drift = cfg["amp"] * math.sin(day_idx * 0.12) + (day_idx * 0.03)
                settle = round(Decimal(str(cfg["base"] + drift)), 2)
                opn = round(settle - Decimal("0.35"), 2)
                high = round(settle + Decimal("0.85"), 2)
                low = round(settle - Decimal("0.95"), 2)
                cls = round(settle + Decimal("0.10"), 2)
                vol = int(cfg["vol"] * (0.85 + 0.3 * math.cos(day_idx * 0.15)))
                oi = int(cfg["oi"] + (day_idx * 450))

                pub_time = datetime.combine(
                    cur_date, time(20, 30, tzinfo=timezone.utc)
                )

                # Prompt contract
                observations.append(
                    RawPriceObservation(
                        symbol=canonical_symbol,
                        observation_date=cur_date,
                        contract_month="2026-11" if canonical_symbol in ["CL", "BRENT"] else "PROMPT",
                        is_prompt=True,
                        open_price=opn,
                        high_price=high,
                        low_price=low,
                        close_price=cls,
                        settlement_price=settle,
                        volume=vol,
                        open_interest=oi,
                        publication_time=pub_time,
                        source_endpoint_code="CME_SETTLE_FEED" if canonical_symbol in ["CL", "NG", "GOLD", "CORN"] else "ICE_SETTLE_FEED",
                    )
                )

                # For CL, generate 2 forward curve contracts to model forward curve term structure
                if canonical_symbol == "CL":
                    m2_settle = round(settle - Decimal("0.40"), 2)
                    observations.append(
                        RawPriceObservation(
                            symbol=canonical_symbol,
                            observation_date=cur_date,
                            contract_month="2026-12",
                            is_prompt=False,
                            open_price=round(m2_settle - Decimal("0.20"), 2),
                            high_price=round(m2_settle + Decimal("0.50"), 2),
                            low_price=round(m2_settle - Decimal("0.60"), 2),
                            close_price=m2_settle,
                            settlement_price=m2_settle,
                            volume=int(vol * 0.45),
                            open_interest=int(oi * 0.65),
                            publication_time=pub_time,
                            source_endpoint_code="CME_SETTLE_FEED",
                        )
                    )
                    m3_settle = round(settle - Decimal("0.75"), 2)
                    observations.append(
                        RawPriceObservation(
                            symbol=canonical_symbol,
                            observation_date=cur_date,
                            contract_month="2027-01",
                            is_prompt=False,
                            open_price=round(m3_settle - Decimal("0.15"), 2),
                            high_price=round(m3_settle + Decimal("0.40"), 2),
                            low_price=round(m3_settle - Decimal("0.45"), 2),
                            close_price=m3_settle,
                            settlement_price=m3_settle,
                            volume=int(vol * 0.25),
                            open_interest=int(oi * 0.40),
                            publication_time=pub_time,
                            source_endpoint_code="CME_SETTLE_FEED",
                        )
                    )

            cur_date += timedelta(days=1)
            day_idx += 1

        return observations


class StaticFundamentalProvider(BaseFundamentalProvider):
    """
    Simulates official weekly government fundamental releases (EIA, USDA).
    """

    @property
    def name(self) -> str:
        return "Static Government Fundamentals Simulator"

    def fetch_fundamental_observations(
        self,
        variable_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs,
    ) -> list[RawFundamentalObservation]:
        raw_code = variable_code.upper()
        canonical_code = VARIABLE_ALIASES.get(raw_code, raw_code)

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=120)

        configs = {
            "CRUDE_US_TOTAL_COMMERCIAL_STOCKS": {
                "base": 425000.0,
                "unit": "MBBL",
                "drift_step": 650.0,
                "pub_hour": 14,
                "pub_min": 30,
            },
            "CRUDE_CUSHING_STOCKS": {
                "base": 24500.0,
                "unit": "MBBL",
                "drift_step": 320.0,
                "pub_hour": 14,
                "pub_min": 30,
            },
            "NATGAS_LOWER_48_WORKING_STORAGE": {
                "base": 3250.0,
                "unit": "BCF",
                "drift_step": 45.0,
                "pub_hour": 14,
                "pub_min": 30,
            },
            "NATGAS_WEEKLY_NET_CHANGE": {
                "base": -35.0,
                "unit": "BCF",
                "drift_step": 15.0,
                "pub_hour": 14,
                "pub_min": 30,
            },
        }

        cfg = configs.get(
            canonical_code,
            {"base": 1000.0, "unit": "MBBL", "drift_step": 10.0, "pub_hour": 14, "pub_min": 30},
        )

        observations: list[RawFundamentalObservation] = []
        cur_date = start_date
        week_idx = 0

        while cur_date <= end_date:
            if cur_date.weekday() == 4:  # Friday
                period_start = cur_date - timedelta(days=6)
                period_end = cur_date
                pub_date = cur_date + timedelta(days=5)
                pub_time = datetime.combine(
                    pub_date, time(cfg["pub_hour"], cfg["pub_min"], tzinfo=timezone.utc)
                )

                if week_idx == 7:
                    val = None
                else:
                    cycle = cfg["drift_step"] * math.sin(week_idx * 0.45)
                    val = Decimal(str(round(cfg["base"] + cycle, 2)))

                observations.append(
                    RawFundamentalObservation(
                        variable_code=canonical_code,
                        observation_date=cur_date,
                        value=val,
                        unit_code=cfg["unit"],
                        period_start=period_start,
                        period_end=period_end,
                        publication_time=pub_time,
                        source_endpoint_code="EIA_V2_PETROLEUM",
                    )
                )
                week_idx += 1

            cur_date += timedelta(days=1)

        return observations


class StaticCOTProvider(BaseCOTProvider):
    """
    Simulates CFTC Commitment of Traders (COT) Disaggregated reports.
    Survey date is Tuesday; official publication is Friday afternoon (20:30 UTC).
    """

    @property
    def name(self) -> str:
        return "Static CFTC COT Simulator"

    def fetch_cot_observations(
        self,
        commodity_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs,
    ) -> list[RawCOTObservation]:
        raw_code = commodity_code.upper()
        canonical_code = COMMODITY_ALIASES.get(raw_code, raw_code)

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=120)

        configs = {
            "CL": {"oi": 1850000, "mm_long": 240000, "mm_short": 85000, "prod_long": 380000, "prod_short": 540000},
            "BRENT": {"oi": 1280000, "mm_long": 195000, "mm_short": 72000, "prod_long": 290000, "prod_short": 410000},
            "GOLD": {"oi": 520000, "mm_long": 210000, "mm_short": 42000, "prod_long": 75000, "prod_short": 220000},
            "CORN": {"oi": 1450000, "mm_long": 120000, "mm_short": 250000, "prod_long": 620000, "prod_short": 490000},
            "NG": {"oi": 1420000, "mm_long": 160000, "mm_short": 190000, "prod_long": 450000, "prod_short": 410000},
        }
        cfg = configs.get(
            canonical_code,
            {"oi": 500000, "mm_long": 80000, "mm_short": 50000, "prod_long": 150000, "prod_short": 180000},
        )

        observations: list[RawCOTObservation] = []
        cur_date = start_date
        week_idx = 0

        while cur_date <= end_date:
            if cur_date.weekday() == 1:  # Tuesday
                pub_date = cur_date + timedelta(days=3)
                pub_time = datetime.combine(pub_date, time(20, 30, tzinfo=timezone.utc))

                swing = int(12000 * math.sin(week_idx * 0.4))
                oi = cfg["oi"] + int(swing * 1.5)
                mm_long = cfg["mm_long"] + swing
                mm_short = cfg["mm_short"] - int(swing * 0.5)
                prod_long = cfg["prod_long"] - int(swing * 0.7)
                prod_short = cfg["prod_short"] + int(swing * 0.8)

                observations.append(
                    RawCOTObservation(
                        commodity_code=canonical_code,
                        observation_date=cur_date,
                        report_type="DISAGGREGATED",
                        open_interest=oi,
                        prod_merc_long=prod_long,
                        prod_merc_short=prod_short,
                        swap_long=180000,
                        swap_short=215000,
                        swap_spread=42000,
                        money_manager_long=mm_long,
                        money_manager_short=mm_short,
                        money_manager_spread=48000,
                        other_rept_long=88000,
                        other_rept_short=52000,
                        non_rept_long=68000,
                        non_rept_short=44000,
                        publication_time=pub_time,
                        source_endpoint_code="CFTC_SODA_FEED",
                    )
                )
                week_idx += 1

            cur_date += timedelta(days=1)

        return observations
