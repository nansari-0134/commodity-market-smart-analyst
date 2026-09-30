"""
Management command to ingest market data, fundamentals, and COT observations.

Loads point-in-time time-series data using configured pluggable providers
(Yahoo Finance live futures, CFTC official COT, or offline static benchmark series).
Supports 20+ years of continuous history, incremental daily updates, and the
full 24-month forward curve contract strip (M1 through M24).
Fully idempotent with high-speed bulk ingestion.
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max

from apps.commodities.models import CommodityMaster
from apps.contracts.models import ContractSpecification
from apps.endpoints.models import EndpointMaster
from apps.metadata.models import UnitMaster
from apps.variables.models import VariableMaster
from apps.market_data.models import (
    MarketPriceObservation,
    FundamentalObservation,
    CommitmentOfTradersObservation,
    OptionsObservation,
)
from apps.market_data.providers.factory import (
    get_market_data_provider,
    get_fundamental_provider,
    get_cot_provider,
)


COMMODITY_ALIASES = {
    "BZ": "BRENT",
    "GC": "GOLD",
    "SI": "SILVER",
    "HG": "COPPER",
    "ZC": "CORN",
    "ZS": "SOYBEANS",
    "ZL": "SOYOIL",
    "ZW": "WHEAT_SRW",
    "SB": "SUGAR_11",
    "KC": "COFFEE_ARABICA",
    "LE": "LIVE_CATTLE",
    "HE": "LEAN_HOGS",
}

DEFAULT_COMMODITIES = [
    "CL", "BRENT", "NG", "RB", "HO",
    "GOLD", "SILVER", "COPPER",
    "CORN", "SOYBEANS", "SOYOIL", "WHEAT_SRW",
    "SUGAR_11", "COFFEE_ARABICA", "LIVE_CATTLE",
]


class Command(BaseCommand):
    help = "Ingest point-in-time market prices, forward curves (M1-M24), fundamental balances, and COT positioning."

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            choices=["all", "prices", "fundamentals", "cot", "curve", "options"],
            default="all",
            help="Observation domain to ingest (default: all)",
        )
        parser.add_argument(
            "--provider",
            choices=["static", "auto", "yahoo", "cftc"],
            default="static",
            help="Data provider to use: 'static' (offline test benchmarks), 'auto' (live Yahoo/CFTC), 'yahoo', or 'cftc' (default: static)",
        )
        parser.add_argument(
            "--commodity",
            type=str,
            default="",
            help="Comma-separated list of commodity codes (e.g. 'CL,BRENT,NG'). Ingests all defaults if empty.",
        )
        parser.add_argument(
            "--years",
            type=int,
            default=20,
            help="Number of historical years to ingest (default: 20 for full historical depth)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=0,
            help="Number of historical days to ingest (overrides --years if > 0)",
        )
        parser.add_argument(
            "--incremental",
            action="store_true",
            help="Incremental update: only fetch missing dates since latest record in DB",
        )
        parser.add_argument(
            "--include-curve",
            action="store_true",
            default=True,
            help="Ingest full 24-month forward curve contract strip (M1-M24) for each commodity (default: True)",
        )
        parser.add_argument(
            "--no-curve",
            action="store_false",
            dest="include_curve",
            help="Skip forward curve contract strip ingestion",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing observations for the target domains before ingestion",
        )

    def handle(self, *args, **options):
        ingest_type = options["type"]
        provider_mode = options["provider"]
        commodity_filter = options["commodity"]
        years = options["years"]
        days = options["days"]
        incremental = options["incremental"]
        include_curve = options["include_curve"]
        clear = options["clear"]

        if days > 0:
            start_date = date.today() - timedelta(days=days)
        else:
            start_date = date.today() - timedelta(days=years * 365)
        end_date = date.today()

        if clear:
            self.stdout.write(self.style.WARNING("Clearing existing observations..."))
            if ingest_type in ["all", "prices", "curve"]:
                MarketPriceObservation.objects.all().delete()
            if ingest_type in ["all", "options", "curve"]:
                OptionsObservation.objects.all().delete()
            if ingest_type in ["all", "fundamentals"]:
                FundamentalObservation.objects.all().delete()
            if ingest_type in ["all", "cot"]:
                CommitmentOfTradersObservation.objects.all().delete()

        raw_symbols = [s.strip().upper() for s in commodity_filter.split(",") if s.strip()]
        if not raw_symbols:
            symbols = DEFAULT_COMMODITIES
        else:
            symbols = [COMMODITY_ALIASES.get(s, s) for s in raw_symbols]

        # Resolve providers based on mode
        price_provider_name = "yahoo" if provider_mode in ["auto", "yahoo"] else "static"
        cot_provider_name = "cftc" if provider_mode in ["auto", "cftc"] else "static"

        if ingest_type in ["all", "prices"]:
            self._ingest_prices(symbols, start_date, end_date, price_provider_name, years, incremental, include_curve)

        elif ingest_type == "curve":
            self._ingest_forward_curves_only(symbols, end_date, price_provider_name)

        if ingest_type in ["all", "options"]:
            self._ingest_options(symbols, end_date, price_provider_name)

        if ingest_type in ["all", "fundamentals"]:
            self._ingest_fundamentals(start_date, end_date)

        if ingest_type in ["all", "cot"]:
            self._ingest_cot(symbols, start_date, end_date, cot_provider_name, years, incremental)

        self.stdout.write(self.style.SUCCESS("Market data ingestion completed successfully."))

    def _ingest_prices(
        self,
        symbols: list[str],
        start_date: date,
        end_date: date,
        provider_name: str,
        years: int,
        incremental: bool,
        include_curve: bool,
    ) -> None:
        self.stdout.write(self.style.NOTICE(f"Ingesting market prices for {symbols} via '{provider_name}' ({years}Y history, curve={include_curve})..."))
        try:
            provider = get_market_data_provider(provider_name)
        except Exception:
            self.stdout.write(self.style.WARNING(f"Provider '{provider_name}' unavailable, falling back to 'static'"))
            provider = get_market_data_provider("static")

        total_created = 0
        total_updated = 0
        endpoints = {e.code: e for e in EndpointMaster.objects.all()}

        for symbol in symbols:
            commodity = CommodityMaster.objects.filter(code=symbol).first()
            if not commodity:
                self.stdout.write(self.style.WARNING(f"Commodity '{symbol}' not found in database. Skipping."))
                continue

            contract = ContractSpecification.objects.filter(commodity=commodity).first()

            # Smart incremental check
            eff_start = start_date
            if incremental:
                latest_obs_date = MarketPriceObservation.objects.filter(
                    commodity=commodity, is_prompt=True
                ).aggregate(Max("observation_date"))["observation_date__max"]
                if latest_obs_date:
                    eff_start = latest_obs_date - timedelta(days=2)
                    self.stdout.write(f"  -> {symbol}: Incremental update from {eff_start}")

            # 1. Fetch continuous prompt daily price series (20+ years)
            raw_obs = provider.fetch_price_observations(symbol, eff_start, end_date, years=years)

            # 2. Fetch forward curve strip M1 through M24 if requested
            if include_curve:
                try:
                    curve_obs = provider.fetch_forward_curve(symbol, as_of_date=end_date, num_months=24)
                    raw_obs.extend(curve_obs)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Could not fetch forward curve for {symbol}: {e}"))

            if not raw_obs:
                self.stdout.write(self.style.WARNING(f"  -> {symbol}: 0 observations returned."))
                continue

            filter_kwargs = {"commodity": commodity}
            if incremental:
                filter_kwargs["observation_date__gte"] = eff_start
            existing_map = {
                (obs.observation_date, obs.delivery_month): obs
                for obs in MarketPriceObservation.objects.filter(**filter_kwargs)
            }

            to_create = []
            to_update = []

            for raw in raw_obs:
                endpoint = endpoints.get(raw.source_endpoint_code) if raw.source_endpoint_code else None
                key = (raw.observation_date, raw.contract_month)
                if key in existing_map:
                    obj = existing_map[key]
                    obj.open_price = raw.open_price
                    obj.high_price = raw.high_price
                    obj.low_price = raw.low_price
                    obj.close_price = raw.close_price
                    obj.settlement_price = raw.settlement_price
                    obj.volume = raw.volume
                    obj.is_prompt = raw.is_prompt
                    obj.is_preliminary = raw.is_preliminary
                    to_update.append(obj)
                else:
                    to_create.append(
                        MarketPriceObservation(
                            commodity=commodity,
                            contract=contract,
                            delivery_month=raw.contract_month,
                            observation_date=raw.observation_date,
                            revision_number=0,
                            is_prompt=raw.is_prompt,
                            open_price=raw.open_price,
                            high_price=raw.high_price,
                            low_price=raw.low_price,
                            close_price=raw.close_price,
                            settlement_price=raw.settlement_price,
                            volume=raw.volume,
                            open_interest=raw.open_interest,
                            publication_time=raw.publication_time,
                            source_endpoint=endpoint,
                            is_preliminary=raw.is_preliminary,
                        )
                    )

            with transaction.atomic():
                if to_create:
                    MarketPriceObservation.objects.bulk_create(to_create, batch_size=1000)
                    total_created += len(to_create)
                if to_update:
                    MarketPriceObservation.objects.bulk_update(
                        to_update,
                        fields=["open_price", "high_price", "low_price", "close_price", "settlement_price", "volume", "is_prompt", "is_preliminary"],
                        batch_size=1000,
                    )
                    total_updated += len(to_update)

            self.stdout.write(f"  -> {symbol}: {len(to_create)} created, {len(to_update)} updated ({len(raw_obs)} total parsed).")

        self.stdout.write(
            f"  -> Prices Summary: {total_created} created, {total_updated} updated. "
            f"Total stored in DB: {MarketPriceObservation.objects.count()}"
        )

    def _ingest_forward_curves_only(self, symbols: list[str], end_date: date, provider_name: str) -> None:
        """Ingest only the forward curve strip M1 through M24 for target commodities."""
        self.stdout.write(self.style.NOTICE(f"Ingesting 24-month forward curves (M1-M24) for {symbols}..."))
        provider = get_market_data_provider(provider_name)
        total_nodes = 0

        for symbol in symbols:
            commodity = CommodityMaster.objects.filter(code=symbol).first()
            if not commodity:
                continue

            contract = ContractSpecification.objects.filter(commodity=commodity).first()
            curve_obs = provider.fetch_forward_curve(symbol, as_of_date=end_date, num_months=24)

            existing_map = {
                (obs.observation_date, obs.delivery_month): obs
                for obs in MarketPriceObservation.objects.filter(commodity=commodity)
            }

            to_create = []
            to_update = []

            for raw in curve_obs:
                key = (raw.observation_date, raw.contract_month)
                if key in existing_map:
                    obj = existing_map[key]
                    obj.settlement_price = raw.settlement_price
                    obj.close_price = raw.close_price
                    to_update.append(obj)
                else:
                    to_create.append(
                        MarketPriceObservation(
                            commodity=commodity,
                            contract=contract,
                            delivery_month=raw.contract_month,
                            observation_date=raw.observation_date,
                            is_prompt=raw.is_prompt,
                            settlement_price=raw.settlement_price,
                            close_price=raw.close_price,
                            publication_time=raw.publication_time,
                        )
                    )

            with transaction.atomic():
                if to_create:
                    MarketPriceObservation.objects.bulk_create(to_create, batch_size=1000)
                if to_update:
                    MarketPriceObservation.objects.bulk_update(to_update, fields=["settlement_price", "close_price"], batch_size=1000)

            total_nodes += len(curve_obs)
            self.stdout.write(f"  -> {symbol}: 24 forward curve nodes stored (M1-M24)")

        self.stdout.write(f"Forward curves completed: {total_nodes} nodes updated.")

    def _ingest_options(self, symbols: list[str], end_date: date, provider_name: str) -> None:
        """Ingest 24-contract options implied volatility surface (M1-M24) for target commodities."""
        self.stdout.write(self.style.NOTICE(f"Ingesting 24-contract options surfaces (M1-M24) for {symbols}..."))
        provider = get_market_data_provider(provider_name)
        endpoints = {e.code: e for e in EndpointMaster.objects.all()}
        total_created = 0
        total_updated = 0

        for symbol in symbols:
            commodity = CommodityMaster.objects.filter(code=symbol).first()
            if not commodity:
                continue

            contract = ContractSpecification.objects.filter(commodity=commodity).first()
            raw_options = provider.fetch_options_chain(symbol, as_of_date=end_date, num_months=24)
            if not raw_options:
                continue

            existing_map = {
                (obs.observation_date, obs.delivery_month): obs
                for obs in OptionsObservation.objects.filter(commodity=commodity, observation_date=end_date)
            }

            to_create = []
            to_update = []

            for raw in raw_options:
                endpoint = endpoints.get(raw.source_endpoint_code) if raw.source_endpoint_code else None
                key = (raw.observation_date, raw.delivery_month)
                if key in existing_map:
                    obj = existing_map[key]
                    obj.atm_implied_volatility = raw.atm_implied_volatility
                    obj.realized_volatility_30d = raw.realized_volatility_30d
                    obj.iv_rv_spread = raw.iv_rv_spread
                    obj.skew_25d = raw.skew_25d
                    obj.term_structure_slope = raw.term_structure_slope
                    obj.put_call_volume_ratio = raw.put_call_volume_ratio
                    obj.put_call_oi_ratio = raw.put_call_oi_ratio
                    obj.total_options_volume = raw.total_options_volume
                    obj.total_options_oi = raw.total_options_oi
                    to_update.append(obj)
                else:
                    to_create.append(
                        OptionsObservation(
                            commodity=commodity,
                            contract=contract,
                            delivery_month=raw.delivery_month,
                            observation_date=raw.observation_date,
                            atm_implied_volatility=raw.atm_implied_volatility,
                            realized_volatility_30d=raw.realized_volatility_30d,
                            iv_rv_spread=raw.iv_rv_spread,
                            skew_25d=raw.skew_25d,
                            term_structure_slope=raw.term_structure_slope,
                            put_call_volume_ratio=raw.put_call_volume_ratio,
                            put_call_oi_ratio=raw.put_call_oi_ratio,
                            total_options_volume=raw.total_options_volume,
                            total_options_oi=raw.total_options_oi,
                            source_endpoint=endpoint,
                        )
                    )

            with transaction.atomic():
                if to_create:
                    OptionsObservation.objects.bulk_create(to_create, batch_size=1000)
                    total_created += len(to_create)
                if to_update:
                    OptionsObservation.objects.bulk_update(
                        to_update,
                        fields=[
                            "atm_implied_volatility", "realized_volatility_30d", "iv_rv_spread",
                            "skew_25d", "term_structure_slope", "put_call_volume_ratio",
                            "put_call_oi_ratio", "total_options_volume", "total_options_oi",
                        ],
                        batch_size=1000,
                    )
                    total_updated += len(to_update)

            self.stdout.write(f"  -> Options {symbol}: 24 contracts (M1-M24) stored.")

        self.stdout.write(
            f"  -> Options Summary: {total_created} created, {total_updated} updated. "
            f"Total stored in DB: {OptionsObservation.objects.count()}"
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

    def _ingest_cot(
        self,
        symbols: list[str],
        start_date: date,
        end_date: date,
        provider_name: str,
        years: int,
        incremental: bool,
    ) -> None:
        self.stdout.write(self.style.NOTICE(f"Ingesting CFTC Commitment of Traders for {symbols} via '{provider_name}' provider..."))
        try:
            provider = get_cot_provider(provider_name)
        except Exception:
            self.stdout.write(self.style.WARNING(f"Provider '{provider_name}' unavailable, falling back to 'static'"))
            provider = get_cot_provider("static")

        endpoints = {e.code: e for e in EndpointMaster.objects.all()}
        total_created = 0
        total_updated = 0

        for symbol in symbols:
            commodity = CommodityMaster.objects.filter(code=symbol).first()
            if not commodity:
                continue

            eff_start = start_date
            if incremental:
                latest_cot_date = CommitmentOfTradersObservation.objects.filter(
                    commodity=commodity
                ).aggregate(Max("observation_date"))["observation_date__max"]
                if latest_cot_date:
                    eff_start = latest_cot_date - timedelta(days=7)

            raw_obs = provider.fetch_cot_observations(symbol, eff_start, end_date, years=years, include_history=True)
            if not raw_obs:
                continue

            existing_map = {
                (obs.observation_date, obs.report_type): obs
                for obs in CommitmentOfTradersObservation.objects.filter(commodity=commodity)
            }

            to_create = []
            to_update = []

            for raw in raw_obs:
                endpoint = endpoints.get(raw.source_endpoint_code) if raw.source_endpoint_code else None
                key = (raw.observation_date, raw.report_type)
                if key in existing_map:
                    obj = existing_map[key]
                    obj.open_interest = raw.open_interest
                    obj.prod_merc_long = raw.prod_merc_long
                    obj.prod_merc_short = raw.prod_merc_short
                    obj.swap_long = raw.swap_long
                    obj.swap_short = raw.swap_short
                    obj.swap_spread = raw.swap_spread
                    obj.money_manager_long = raw.money_manager_long
                    obj.money_manager_short = raw.money_manager_short
                    obj.money_manager_spread = raw.money_manager_spread
                    obj.other_rept_long = raw.other_rept_long
                    obj.other_rept_short = raw.other_rept_short
                    obj.non_rept_long = raw.non_rept_long
                    obj.non_rept_short = raw.non_rept_short
                    to_update.append(obj)
                else:
                    to_create.append(
                        CommitmentOfTradersObservation(
                            commodity=commodity,
                            observation_date=raw.observation_date,
                            report_type=raw.report_type,
                            open_interest=raw.open_interest,
                            prod_merc_long=raw.prod_merc_long,
                            prod_merc_short=raw.prod_merc_short,
                            swap_long=raw.swap_long,
                            swap_short=raw.swap_short,
                            swap_spread=raw.swap_spread,
                            money_manager_long=raw.money_manager_long,
                            money_manager_short=raw.money_manager_short,
                            money_manager_spread=raw.money_manager_spread,
                            other_rept_long=raw.other_rept_long,
                            other_rept_short=raw.other_rept_short,
                            non_rept_long=raw.non_rept_long,
                            non_rept_short=raw.non_rept_short,
                            publication_time=raw.publication_time,
                            source_endpoint=endpoint,
                        )
                    )

            with transaction.atomic():
                if to_create:
                    CommitmentOfTradersObservation.objects.bulk_create(to_create, batch_size=1000)
                    total_created += len(to_create)
                if to_update:
                    CommitmentOfTradersObservation.objects.bulk_update(
                        to_update,
                        fields=[
                            "open_interest", "prod_merc_long", "prod_merc_short",
                            "swap_long", "swap_short", "swap_spread",
                            "money_manager_long", "money_manager_short", "money_manager_spread",
                            "other_rept_long", "other_rept_short", "non_rept_long", "non_rept_short",
                        ],
                        batch_size=1000,
                    )
                    total_updated += len(to_update)

            self.stdout.write(f"  -> COT {symbol}: {len(to_create)} created, {len(to_update)} updated.")

        self.stdout.write(
            f"  -> COT Summary: {total_created} created, {total_updated} updated. "
            f"Total stored in DB: {CommitmentOfTradersObservation.objects.count()}"
        )
