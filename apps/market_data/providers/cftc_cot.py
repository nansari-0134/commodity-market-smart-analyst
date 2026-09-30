"""
Live CFTC Commitment of Traders (COT) Data Provider.

Fetches official CFTC Disaggregated Futures & Options positioning reports
directly from the US Commodity Futures Trading Commission (cftc.gov).
Supports both latest weekly releases and historical multi-year annual archives.
Enforces Core Directive 1: Pluggable Source Independence.
"""

import certifi
import csv
import io
import logging
import ssl
import urllib.request
import zipfile
from datetime import date, datetime, timezone
from typing import Optional

from .base import BaseCOTProvider, RawCOTObservation

logger = logging.getLogger(__name__)

# CFTC Contract Market Code to Canonical Commodity Code mapping
CFTC_CODE_TO_COMMODITY: dict[str, str] = {
    # Energy
    "067651": "CL",
    "023651": "NG",
    "111659": "RB",
    "022651": "HO",
    # Grains & Oilseeds
    "002602": "CORN",
    "005602": "SOYBEANS",
    "007601": "SOYOIL",
    "026603": "SOYMEAL",
    "001602": "WHEAT_SRW",
    # Metals
    "088691": "GOLD",
    "084691": "SILVER",
    "085692": "COPPER",
    "076651": "PLATINUM",
    # Softs & Agris
    "080732": "SUGAR_11",
    "083731": "COFFEE_ARABICA",
    "073732": "COCOA",
    "033661": "COTTON_2",
    # Livestock
    "057642": "LIVE_CATTLE",
    "054642": "LEAN_HOGS",
}

COMMODITY_TO_CFTC_CODE: dict[str, str] = {v: k for k, v in CFTC_CODE_TO_COMMODITY.items()}
# Add aliases
COMMODITY_TO_CFTC_CODE.update({
    "GC": "088691",
    "SI": "084691",
    "HG": "085692",
    "ZC": "002602",
    "ZS": "005602",
    "ZL": "007601",
    "ZM": "026603",
    "ZW": "001602",
    "SB": "080732",
    "KC": "083731",
    "CC": "073732",
    "CT": "033661",
    "LE": "057642",
    "HE": "054642",
})


class CFTCCOTProvider(BaseCOTProvider):
    """
    Pluggable COT Data Provider ingesting official CFTC Disaggregated reports.
    """

    @property
    def name(self) -> str:
        return "CFTC Official Disaggregated COT Provider"

    def fetch_cot_observations(
        self,
        commodity_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs,
    ) -> list[RawCOTObservation]:
        """
        Fetch weekly CFTC Commitment of Traders positioning for a commodity.
        If start_date is more than a year ago or include_history=True, fetches annual archives.
        """
        clean_code = commodity_code.strip().upper()
        cftc_code = COMMODITY_TO_CFTC_CODE.get(clean_code)

        if not cftc_code:
            logger.warning(f"No CFTC contract code mapped for commodity '{commodity_code}'")
            return []

        ctx = ssl.create_default_context(cafile=certifi.where())
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

        include_history = kwargs.get("include_history", False)
        years_back = kwargs.get("years", 1)

        # Decide which years to fetch
        current_year = date.today().year
        years_to_fetch = []
        if include_history or years_back > 1 or (start_date and start_date.year < current_year):
            start_yr = max(current_year - years_back + 1, (start_date.year if start_date else current_year - 3))
            years_to_fetch = list(range(start_yr, current_year))

        observations: list[RawCOTObservation] = []
        seen_dates = set()

        # 1. Fetch current year active report
        latest_url = "https://www.cftc.gov/dea/newcot/f_disagg.txt"
        try:
            req = urllib.request.Request(latest_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
                obs_list = self._parse_cftc_csv(text, cftc_code, clean_code, start_date, end_date)
                for o in obs_list:
                    if o.observation_date not in seen_dates:
                        observations.append(o)
                        seen_dates.add(o.observation_date)
        except Exception as e:
            logger.error(f"Error fetching current CFTC report: {e}")

        # 2. Fetch historical annual ZIP archives if multi-year requested
        for yr in years_to_fetch:
            archive_url = f"https://www.cftc.gov/files/dea/history/fut_disagg_txt_{yr}.zip"
            try:
                logger.info(f"Fetching CFTC historical archive for {yr} from {archive_url}")
                req = urllib.request.Request(archive_url, headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
                    z = zipfile.ZipFile(io.BytesIO(resp.read()))
                    for name in z.namelist():
                        text = z.read(name).decode("utf-8", errors="ignore")
                        obs_list = self._parse_cftc_csv(text, cftc_code, clean_code, start_date, end_date)
                        for o in obs_list:
                            if o.observation_date not in seen_dates:
                                observations.append(o)
                                seen_dates.add(o.observation_date)
            except Exception as e:
                logger.warning(f"Could not load CFTC archive for year {yr}: {e}")

        # Sort chronologically
        observations.sort(key=lambda x: x.observation_date)
        logger.info(f"Loaded {len(observations)} COT observations for {commodity_code}")
        return observations

    def _parse_cftc_csv(
        self,
        csv_text: str,
        target_cftc_code: str,
        commodity_code: str,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> list[RawCOTObservation]:
        """Parse raw CFTC disaggregated CSV text and filter for target commodity."""
        reader = csv.reader(io.StringIO(csv_text))
        results = []

        def to_int(val: str) -> Optional[int]:
            v = val.strip().replace(",", "")
            return int(v) if v and v.lstrip("-").isdigit() else None

        for row in reader:
            if len(row) < 21:
                continue

            contract_code = row[3].strip()
            if contract_code != target_cftc_code:
                continue

            try:
                report_date = date.fromisoformat(row[2].strip())
            except Exception:
                continue

            if start_date and report_date < start_date:
                continue
            if end_date and report_date > end_date:
                continue

            open_int = to_int(row[7]) or 0
            pm_long = to_int(row[8])
            pm_short = to_int(row[9])
            sw_long = to_int(row[10])
            sw_short = to_int(row[11])
            sw_spread = to_int(row[12])
            mm_long = to_int(row[13])
            mm_short = to_int(row[14])
            mm_spread = to_int(row[15])
            oth_long = to_int(row[16])
            oth_short = to_int(row[17])
            non_long = to_int(row[19])
            non_short = to_int(row[20])

            # CFTC reports are released on Fridays at 15:30 EST (20:30 UTC) for Tuesday positions
            pub_time = datetime.combine(report_date, datetime.min.time()).replace(
                hour=20, minute=30, tzinfo=timezone.utc
            )

            results.append(
                RawCOTObservation(
                    commodity_code=commodity_code,
                    observation_date=report_date,
                    report_type="DISAGGREGATED",
                    open_interest=open_int,
                    prod_merc_long=pm_long,
                    prod_merc_short=pm_short,
                    swap_long=sw_long,
                    swap_short=sw_short,
                    swap_spread=sw_spread,
                    money_manager_long=mm_long,
                    money_manager_short=mm_short,
                    money_manager_spread=mm_spread,
                    other_rept_long=oth_long,
                    other_rept_short=oth_short,
                    non_rept_long=non_long,
                    non_rept_short=non_short,
                    publication_time=pub_time,
                    source_endpoint_code="CFTC_DISAGG_WEB",
                )
            )

        return results
