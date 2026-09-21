"""
Management command to seed canonical commodities and their multi-exchange listings.
Follows the Pluggable Provider Architecture via get_commodity_provider().
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.commodities.providers.factory import get_commodity_provider
from apps.commodities.models import CommodityMaster, CommodityExchangeListing
from apps.exchanges.models import ExchangeMaster
from apps.metadata.models import UnitMaster


class Command(BaseCommand):
    help = "Seeds canonical physical commodities, deliverable grade chemistry, and multi-exchange listings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing commodities and listings before seeding.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding canonical commodity catalog & multi-exchange listings..."))

        provider = get_commodity_provider()
        specs = provider.get_commodities()

        with transaction.atomic():
            if options.get("clear"):
                self.stdout.write(self.style.WARNING("Clearing existing commodities and exchange listings..."))
                CommodityExchangeListing.objects.all().delete()
                CommodityMaster.objects.all().delete()

            # Pre-cache exchanges and units for fast lookup
            exchanges = {e.code.upper(): e for e in ExchangeMaster.objects.all()}
            units = {u.code.upper(): u for u in UnitMaster.objects.all()}

            commodities_seeded = 0
            listings_seeded = 0

            for spec in specs:
                primary_exchange = exchanges.get(spec.primary_exchange_code.upper())
                if not primary_exchange:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Primary exchange '{spec.primary_exchange_code}' not found for {spec.code}. Skipping."
                        )
                    )
                    continue

                base_unit = units.get(spec.base_unit_code.upper())
                pricing_unit = units.get(spec.pricing_unit_code.upper())
                lot_unit = units.get(spec.standard_lot_unit_code.upper())

                if not base_unit or not pricing_unit or not lot_unit:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Units not found for {spec.code} (Base: {spec.base_unit_code}, Pricing: {spec.pricing_unit_code}, Lot: {spec.standard_lot_unit_code}). Skipping."
                        )
                    )
                    continue

                commodity, created = CommodityMaster.objects.update_or_create(
                    code=spec.code,
                    defaults={
                        "name": spec.name,
                        "sector": spec.sector,
                        "group": spec.group,
                        "primary_exchange": primary_exchange,
                        "base_unit": base_unit,
                        "pricing_unit": pricing_unit,
                        "standard_lot_size": spec.standard_lot_size,
                        "standard_lot_unit": lot_unit,
                        "minimum_tick_size": spec.minimum_tick_size,
                        "tick_value": spec.tick_value,
                        "tick_currency": spec.tick_currency,
                        "settlement_method": spec.settlement_method,
                        "hs_code": spec.hs_code,
                        "deliverable_grade_standard": spec.deliverable_grade_standard,
                        "quality_specifications": spec.quality_specifications,
                        "primary_delivery_hub": spec.primary_delivery_hub,
                        "delivery_hub_details": spec.delivery_hub_details,
                        "crop_year_start_month": spec.crop_year_start_month,
                        "peak_production_months": spec.peak_production_months,
                        "peak_demand_months": spec.peak_demand_months,
                        "seasonality_notes": spec.seasonality_notes,
                        "description": spec.description,
                        "display_order": spec.display_order,
                        "is_active": spec.is_active,
                        "metadata": spec.metadata,
                    },
                )
                commodities_seeded += 1

                # Seed liquid exchange listings
                for listing_spec in spec.listings:
                    listing_exchange = exchanges.get(listing_spec.exchange_code.upper())
                    if not listing_exchange:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Listing exchange '{listing_spec.exchange_code}' not found for {commodity.code}. Skipping listing."
                            )
                        )
                        continue

                    listing_unit = units.get(listing_spec.contract_unit_code.upper())
                    if not listing_unit:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Listing unit '{listing_spec.contract_unit_code}' not found. Skipping listing."
                            )
                        )
                        continue

                    CommodityExchangeListing.objects.update_or_create(
                        commodity=commodity,
                        exchange=listing_exchange,
                        defaults={
                            "ticker_symbol": listing_spec.ticker_symbol,
                            "contract_size": listing_spec.contract_size,
                            "contract_unit": listing_unit,
                            "settlement_method": listing_spec.settlement_method,
                            "is_primary_benchmark": listing_spec.is_primary_benchmark,
                            "liquidity_tier": listing_spec.liquidity_tier,
                            "typical_daily_volume": listing_spec.typical_daily_volume,
                            "typical_open_interest": listing_spec.typical_open_interest,
                            "trading_currency": listing_spec.trading_currency,
                            "is_active": listing_spec.is_active,
                        },
                    )
                    listings_seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded {commodities_seeded} benchmark commodities and {listings_seeded} active exchange listings."
            )
        )
