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
    RawOptionsObservation,
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

BENCHMARK_CONFIGS = {
    "CL": {"base": 76.50, "amp": 4.50, "vol": 320000, "oi": 1820000},
    "BRENT": {"base": 80.20, "amp": 4.20, "vol": 260000, "oi": 1250000},
    "NG": {"base": 2.45, "amp": 0.40, "vol": 150000, "oi": 1410000},
    "GOLD": {"base": 2580.00, "amp": 60.00, "vol": 210000, "oi": 520000},
    "CORN": {"base": 420.00, "amp": 25.00, "vol": 140000, "oi": 1480000},
    "SILVER": {"base": 31.50, "amp": 1.50, "vol": 120000, "oi": 420000},
    "COPPER": {"base": 4.30, "amp": 0.20, "vol": 95000, "oi": 310000},
    "RB": {"base": 2.15, "amp": 0.15, "vol": 110000, "oi": 390000},
    "HO": {"base": 2.30, "amp": 0.18, "vol": 105000, "oi": 380000},
    "SOYBEANS": {"base": 1020.00, "amp": 40.00, "vol": 160000, "oi": 850000},
    "SOYOIL": {"base": 43.50, "amp": 2.50, "vol": 85000, "oi": 460000},
    "WHEAT_SRW": {"base": 580.00, "amp": 30.00, "vol": 115000, "oi": 520000},
    "SUGAR_11": {"base": 22.50, "amp": 1.20, "vol": 130000, "oi": 720000},
    "COFFEE_ARABICA": {"base": 255.00, "amp": 15.00, "vol": 65000, "oi": 320000},
    "LIVE_CATTLE": {"base": 185.00, "amp": 8.00, "vol": 55000, "oi": 310000},
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

        cfg = BENCHMARK_CONFIGS.get(canonical_symbol, {"base": 50.00, "amp": 5.00, "vol": 100000, "oi": 500000})

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

    def fetch_forward_curve(
        self,
        symbol: str,
        as_of_date: Optional[date] = None,
        num_months: int = 24,
        **kwargs,
    ) -> list[RawPriceObservation]:
        ref_date = as_of_date or date.today()
        canonical_symbol = COMMODITY_ALIASES.get(symbol.upper(), symbol.upper())
        cfg = BENCHMARK_CONFIGS.get(canonical_symbol, {"base": 75.0, "amp": 2.5, "vol": 100000, "oi": 500000})
        base = cfg["base"]

        nodes = []
        for i in range(num_months):
            month_idx = i + 1
            m_label = f"M{month_idx}"
            decay = math.exp(-0.04 * i)
            p = round(Decimal(str(base * (0.82 + 0.18 * decay))), 2)
            vol = int(cfg["vol"] * math.exp(-0.15 * i))
            oi = int(cfg["oi"] * math.exp(-0.12 * i))

            nodes.append(
                RawPriceObservation(
                    symbol=canonical_symbol,
                    observation_date=ref_date,
                    contract_month=m_label,
                    is_prompt=False,
                    open_price=p,
                    high_price=p,
                    low_price=p,
                    close_price=p,
                    settlement_price=p,
                    volume=vol if vol > 0 else None,
                    open_interest=oi if oi > 0 else None,
                    publication_time=datetime.combine(ref_date, time(20, 30, tzinfo=timezone.utc)),
                    is_preliminary=False,
                    source_endpoint_code="STATIC_BENCHMARK_CURVE",
                )
            )
        return nodes

    def fetch_options_chain(
        self,
        symbol: str,
        as_of_date: Optional[date] = None,
        num_months: int = 24,
        **kwargs,
    ) -> list[RawOptionsObservation]:
        ref_date = as_of_date or date.today()
        canonical_symbol = COMMODITY_ALIASES.get(symbol.upper(), symbol.upper())
        base_iv = Decimal("28.50")
        rv_30d = Decimal("26.80")

        obs = []
        for i in range(num_months):
            month_idx = i + 1
            m_label = f"M{month_idx}"
            decay = Decimal(str(round(math.exp(-0.10 * i), 4)))
            node_iv = Decimal("22.00") + (base_iv - Decimal("22.00")) * decay
            node_rv = Decimal("21.00") + (rv_30d - Decimal("21.00")) * decay
            slope = (base_iv - node_iv) if i > 0 else Decimal("0.00")

            obs.append(
                RawOptionsObservation(
                    symbol=canonical_symbol,
                    observation_date=ref_date,
                    delivery_month=m_label,
                    atm_implied_volatility=round(node_iv, 4),
                    realized_volatility_30d=round(node_rv, 4),
                    iv_rv_spread=round(node_iv - node_rv, 4),
                    skew_25d=round(Decimal("2.20") * decay, 4),
                    term_structure_slope=round(slope, 4),
                    put_call_volume_ratio=Decimal("0.85"),
                    put_call_oi_ratio=Decimal("0.88"),
                    total_options_volume=int(250000 * math.exp(-0.18 * i)),
                    total_options_oi=int(1800000 * math.exp(-0.15 * i)),
                    source_endpoint_code="STATIC_OPTIONS_BENCHMARK",
                )
            )
        return obs


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
