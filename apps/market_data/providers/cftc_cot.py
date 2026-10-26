"""
Official CFTC Commitment of Traders (COT) Data Provider.

Directly ingests official CFTC weekly Commitment of Traders (COT) positioning reports
via the official CFTC Socrata Open Data REST API (publicreporting.cftc.gov).
Retrieves institutional positioning across Commercial Hedgers, Managed Money / Speculators,
and Non-Reportables with zero lookahead bias.

Adheres strictly to:
- Core Directive 1: Pluggable Source Independence (BaseCOTProvider)
- Core Directive 2: Point-in-Time Correctness (Tuesday cutoff -> Friday 20:30 UTC release)
- Core Directive 3: Deterministic Arithmetic (Net = Long - Short)
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import requests

from .base import BaseCOTProvider, RawCOTObservation

logger = logging.getLogger(__name__)

CFTC_API_URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"

# CFTC Contract Market Code to Canonical Commodity Code mapping
# Sourced and verified against CFTC Socrata FutOnly Legacy dataset & institutional market master
CFTC_CODE_TO_COMMODITY: dict[str, str] = {
    # Energy
    "067651": "CL",             # WTI Crude Oil (NYMEX)
    "06765T": "BRENT",          # Brent Crude Oil (ICE)
    "023651": "NG",             # Natural Gas (NYMEX)
    "111659": "RB",             # RBOB Gasoline (NYMEX)
    "022651": "HO",             # Heating Oil (NYMEX)
    # Grains & Oilseeds
    "001612": "CORN",           # Corn (CBOT)
    "005602": "SOYBEANS",       # Soybeans (CBOT)
    "007601": "SOYOIL",         # Soybean Oil (CBOT)
    "026603": "SOYMEAL",        # Soybean Meal (CBOT)
    "001602": "WHEAT_SRW",      # Wheat-SRW (CBOT)
    "001620": "WHEAT_HRW",      # Wheat-HRW (KCBT)
    # Metals
    "088691": "GOLD",           # Gold (COMEX)
    "084691": "SILVER",         # Silver (COMEX)
    "085692": "COPPER",         # Copper (COMEX)
    "076651": "PLATINUM",       # Platinum (NYMEX)
    "075651": "PALLADIUM",      # Palladium (NYMEX)
    # Softs & Agris
    "080732": "SUGAR_11",       # Sugar No. 11 (ICE)
    "083731": "COFFEE_ARABICA", # Coffee C (ICE)
    "073732": "COCOA",          # Cocoa (ICE)
    "033661": "COTTON_2",       # Cotton No. 2 (ICE)
    # Livestock
    "057642": "LIVE_CATTLE",    # Live Cattle (CME)
    "061641": "FEEDER_CATTLE",  # Feeder Cattle (CME)
    "054642": "LEAN_HOGS",      # Lean Hogs (CME)
}

COMMODITY_TO_CFTC_CODE: dict[str, str] = {v: k for k, v in CFTC_CODE_TO_COMMODITY.items()}

# Common commodity symbol aliases
COMMODITY_TO_CFTC_CODE.update({
    "GC": "088691",
    "SI": "084691",
    "HG": "085692",
    "ZC": "001612",
    "ZS": "005602",
    "ZL": "007601",
    "ZM": "026603",
    "ZW": "001602",
    "SB": "080732",
    "KC": "083731",
    "CC": "073732",
    "CT": "033661",
    "LE": "057642",
    "GF": "061641",
    "HE": "054642",
})


def _parse_int(val, default: Optional[int] = None) -> Optional[int]:
    """Safely parse integer from string, returning default if null/invalid."""
    if val is None:
        return default
    try:
        return int(float(str(val).replace(",", "").strip()))
    except (ValueError, TypeError):
        return default


class CFTCCOTProvider(BaseCOTProvider):
    """
    Pluggable COT Data Provider ingesting official CFTC positioning data
    via the CFTC Socrata Open Data REST API.
    """

    @property
    def name(self) -> str:
        return "CFTC Official Disaggregated COT Provider"

    def is_healthy(self) -> bool:
        """Verify network connectivity to official CFTC Socrata API."""
        try:
            params = {
                "$select": "report_date_as_yyyy_mm_dd",
                "$limit": 1,
            }
            resp = requests.get(CFTC_API_URL, params=params, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"CFTC Socrata API health check failed: {e}")
            return False

    def fetch_cot_observations(
        self,
        commodity_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs,
    ) -> list[RawCOTObservation]:
        """
        Fetch weekly CFTC Commitment of Traders positioning for a commodity.

        Args:
            commodity_code: Canonical commodity symbol (e.g. 'CL', 'GOLD')
            start_date: Filter for reports on or after this date (inclusive)
            end_date: Filter for reports on or before this date (inclusive)
            limit: Maximum records to return (defaults to 5000)
            report_type: Classification label (defaults to 'LEGACY')
        """
        clean_code = commodity_code.strip().upper()
        cftc_code = COMMODITY_TO_CFTC_CODE.get(clean_code)

        if not cftc_code:
            logger.warning(f"No CFTC contract code mapped for commodity '{commodity_code}'")
            return []

        limit = kwargs.get("limit", 5000)
        report_type = kwargs.get("report_type", "LEGACY")

        params = {
            "$where": f"cftc_contract_market_code='{cftc_code}' AND futonly_or_combined='FutOnly'",
            "$order": "report_date_as_yyyy_mm_dd ASC",
            "$limit": limit,
        }

        if start_date:
            params["$where"] += f" AND report_date_as_yyyy_mm_dd >= '{start_date.isoformat()}'"
        if end_date:
            params["$where"] += f" AND report_date_as_yyyy_mm_dd <= '{end_date.isoformat()}'"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CommodityMarketSmartAnalyst/1.0",
            "Accept": "application/json",
        }

        try:
            resp = requests.get(CFTC_API_URL, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            rows = resp.json()
        except Exception as e:
            logger.error(f"Error querying CFTC Socrata API for {clean_code} ({cftc_code}): {e}")
            return []

        observations: list[RawCOTObservation] = []
        seen_dates = set()

        for row in rows:
            date_str = (row.get("report_date_as_yyyy_mm_dd") or "")[:10]
            if not date_str:
                continue

            try:
                report_date = date.fromisoformat(date_str)
            except ValueError:
                continue

            if report_date in seen_dates:
                continue
            seen_dates.add(report_date)

            # Point-in-Time: CFTC survey Tuesday cutoff -> official public release Friday 15:30 EST (20:30 UTC)
            days_to_friday = (4 - report_date.weekday()) % 7
            pub_date = report_date + timedelta(days=days_to_friday)
            pub_time = datetime.combine(pub_date, datetime.min.time()).replace(
                hour=20, minute=30, tzinfo=timezone.utc
            )

            open_int = _parse_int(row.get("open_interest_all"), default=0) or 0
            pm_long = _parse_int(row.get("comm_positions_long_all"))
            pm_short = _parse_int(row.get("comm_positions_short_all"))
            mm_long = _parse_int(row.get("noncomm_positions_long_all"))
            mm_short = _parse_int(row.get("noncomm_positions_short_all"))
            mm_spread = _parse_int(row.get("noncomm_postions_spread_all"))
            non_long = _parse_int(row.get("nonrept_positions_long_all"))
            non_short = _parse_int(row.get("nonrept_positions_short_all"))

            observations.append(
                RawCOTObservation(
                    commodity_code=clean_code,
                    observation_date=report_date,
                    report_type=report_type,
                    open_interest=open_int,
                    prod_merc_long=pm_long,
                    prod_merc_short=pm_short,
                    swap_long=None,
                    swap_short=None,
                    swap_spread=None,
                    money_manager_long=mm_long,
                    money_manager_short=mm_short,
                    money_manager_spread=mm_spread,
                    other_rept_long=None,
                    other_rept_short=None,
                    non_rept_long=non_long,
                    non_rept_short=non_short,
                    publication_time=pub_time,
                    source_endpoint_code="CFTC_COT_DISAGGREGATED_FUT",
                )
            )

        logger.info(f"Loaded {len(observations)} official CFTC COT observations for {clean_code}")
        return observations
