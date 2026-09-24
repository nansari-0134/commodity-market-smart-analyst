"""
Management command to ingest market data, fundamentals, and COT observations.

Loads point-in-time time-series data using configured pluggable providers.
Fully idempotent: safe to run repeatedly via update_or_create.
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.commodities.models import CommodityMaster
from apps.contracts.models import ContractSpecification
from apps.endpoints.models import EndpointMaster
from apps.metadata.models import UnitMaster
from apps.variables.models import VariableMaster
from apps.market_data.models import (
    MarketPriceObservation,
    FundamentalObservation,
    CommitmentOfTradersObservation,
)
from apps.market_data.providers.factory import (
    get_market_data_provider,
    get_fundamental_provider,
    get_cot_provider,
)


COMMODITY_ALIASES = {
    "BZ": "BRENT",
    "GC": "GOLD",
    "ZC": "CORN",
}


class Command(BaseCommand):
    help = "Ingest point-in-time market prices, fundamental balances, and COT positioning."

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            choices=["all", "prices", "fundamentals", "cot"],
            default="all",
            help="Observation domain to ingest (default: all)",
        )
        parser.add_argument(
            "--commodity",
            type=str,
            default="",
            help="Comma-separated list of commodity codes (e.g. 'CL,BRENT,NG'). Ingests all defaults if empty.",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Number of historical days to ingest (default: 90)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing observations for the target domains before ingestion",
        )

    def handle(self, *args, **options):
        ingest_type = options["type"]
        commodity_filter = options["commodity"]
        days = options["days"]
        clear = options["clear"]

        start_date = date.today() - timedelta(days=days)
        end_date = date.today()

        if clear:
            self.stdout.write(self.style.WARNING("Clearing existing observations..."))
            if ingest_type in ["all", "prices"]:
                MarketPriceObservation.objects.all().delete()
            if ingest_type in ["all", "fundamentals"]:
                FundamentalObservation.objects.all().delete()
            if ingest_type in ["all", "cot"]:
                CommitmentOfTradersObservation.objects.all().delete()

        raw_symbols = [s.strip().upper() for s in commodity_filter.split(",") if s.strip()]
        if not raw_symbols:
            symbols = ["CL", "BRENT", "NG", "GOLD", "CORN"]
        else:
            symbols = [COMMODITY_ALIASES.get(s, s) for s in raw_symbols]

        if ingest_type in ["all", "prices"]:
            self._ingest_prices(symbols, start_date, end_date)

        if ingest_type in ["all", "fundamentals"]:
            self._ingest_fundamentals(start_date, end_date)

        if ingest_type in ["all", "cot"]:
            self._ingest_cot(symbols, start_date, end_date)

        self.stdout.write(self.style.SUCCESS("Market data ingestion completed successfully."))

    def _ingest_prices(self, symbols: list[str], start_date: date, end_date: date) -> None:
        self.stdout.write(self.style.NOTICE(f"Ingesting market prices for {symbols}..."))
        provider = get_market_data_provider()
        total_created = 0
        total_updated = 0

        endpoints = {e.code: e for e in EndpointMaster.objects.all()}

        for symbol in symbols:
            commodity = CommodityMaster.objects.filter(code=symbol).first()
            if not commodity:
                self.stdout.write(self.style.WARNING(f"Commodity '{symbol}' not found in database. Skipping."))
                continue

            contract = ContractSpecification.objects.filter(commodity=commodity).first()
            raw_obs = provider.fetch_price_observations(symbol, start_date, end_date)

            with transaction.atomic():
                for raw in raw_obs:
                    endpoint = endpoints.get(raw.source_endpoint_code) if raw.source_endpoint_code else None
                    obj, created = MarketPriceObservation.objects.update_or_create(
                        commodity=commodity,
                        delivery_month=raw.contract_month,
                        observation_date=raw.observation_date,
                        revision_number=0,
                        defaults={
                            "contract": contract,
                            "is_prompt": raw.is_prompt,
                            "open_price": raw.open_price,
                            "high_price": raw.high_price,
                            "low_price": raw.low_price,
                            "close_price": raw.close_price,
                            "settlement_price": raw.settlement_price,
                            "volume": raw.volume,
                            "open_interest": raw.open_interest,
                            "publication_time": raw.publication_time,
                            "source_endpoint": endpoint,
                            "is_preliminary": raw.is_preliminary,
                        },
                    )
                    if created:
                        total_created += 1
                    else:
                        total_updated += 1

        self.stdout.write(
            f"  -> Prices: {total_created} created, {total_updated} updated. "
            f"Total stored: {MarketPriceObservation.objects.count()}"
        )

    def _ingest_fundamentals(self, start_date: date, end_date: date) -> None:
        self.stdout.write(self.style.NOTICE("Ingesting fundamental supply-demand observations..."))
        provider = get_fundamental_provider()
        variables_to_ingest = [
            "CRUDE_US_TOTAL_COMMERCIAL_STOCKS",
            "CRUDE_CUSHING_STOCKS",
            "NATGAS_LOWER_48_WORKING_STORAGE",
            "NATGAS_WEEKLY_NET_CHANGE",
        ]

        units = {u.code: u for u in UnitMaster.objects.all()}
        endpoints = {e.code: e for e in EndpointMaster.objects.all()}
        total_created = 0
        total_updated = 0

        for var_code in variables_to_ingest:
            variable = VariableMaster.objects.filter(code=var_code).first()
            if not variable:
                self.stdout.write(self.style.WARNING(f"Variable '{var_code}' not found in database. Skipping."))
                continue

            raw_obs = provider.fetch_fundamental_observations(var_code, start_date, end_date)

            with transaction.atomic():
                for raw in raw_obs:
                    unit = units.get(raw.unit_code) if raw.unit_code else variable.default_unit
                    endpoint = endpoints.get(raw.source_endpoint_code) if raw.source_endpoint_code else None

                    obj, created = FundamentalObservation.objects.update_or_create(
                        variable=variable,
                        observation_date=raw.observation_date,
                        revision_number=raw.revision_number,
                        defaults={
                            "value": raw.value,
                            "unit": unit,
                            "period_start": raw.period_start,
                            "period_end": raw.period_end,
                            "publication_time": raw.publication_time,
                            "source_endpoint": endpoint,
                            "is_preliminary": raw.is_preliminary,
                        },
                    )
                    if created:
                        total_created += 1
                    else:
                        total_updated += 1

        self.stdout.write(
            f"  -> Fundamentals: {total_created} created, {total_updated} updated. "
            f"Total stored: {FundamentalObservation.objects.count()}"
        )

    def _ingest_cot(self, symbols: list[str], start_date: date, end_date: date) -> None:
        self.stdout.write(self.style.NOTICE(f"Ingesting CFTC Commitment of Traders for {symbols}..."))
        provider = get_cot_provider()
        endpoints = {e.code: e for e in EndpointMaster.objects.all()}
        total_created = 0
        total_updated = 0

        for symbol in symbols:
            commodity = CommodityMaster.objects.filter(code=symbol).first()
            if not commodity:
                continue

            raw_obs = provider.fetch_cot_observations(symbol, start_date, end_date)

            with transaction.atomic():
                for raw in raw_obs:
                    endpoint = endpoints.get(raw.source_endpoint_code) if raw.source_endpoint_code else None

                    obj, created = CommitmentOfTradersObservation.objects.update_or_create(
                        commodity=commodity,
                        observation_date=raw.observation_date,
                        report_type=raw.report_type,
                        defaults={
                            "open_interest": raw.open_interest,
                            "prod_merc_long": raw.prod_merc_long,
                            "prod_merc_short": raw.prod_merc_short,
                            "swap_long": raw.swap_long,
                            "swap_short": raw.swap_short,
                            "swap_spread": raw.swap_spread,
                            "money_manager_long": raw.money_manager_long,
                            "money_manager_short": raw.money_manager_short,
                            "money_manager_spread": raw.money_manager_spread,
                            "other_rept_long": raw.other_rept_long,
                            "other_rept_short": raw.other_rept_short,
                            "non_rept_long": raw.non_rept_long,
                            "non_rept_short": raw.non_rept_short,
                            "publication_time": raw.publication_time,
                            "source_endpoint": endpoint,
                        },
                    )
                    if created:
                        total_created += 1
                    else:
                        total_updated += 1

        self.stdout.write(
            f"  -> COT: {total_created} created, {total_updated} updated. "
            f"Total stored: {CommitmentOfTradersObservation.objects.count()}"
        )
