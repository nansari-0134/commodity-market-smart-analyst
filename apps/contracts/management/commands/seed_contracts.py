"""
Management command to seed canonical contract specifications and active prompt expiries.
Follows the Pluggable Provider Architecture via get_contract_provider().
"""

from datetime import date as dt_date
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.commodities.models import CommodityMaster
from apps.contracts.models import (
    ContractSpecification,
    ContractExpiry,
    SettlementMethod,
    InstrumentType,
    ExpiryRuleType,
    MONTH_NUMBER_TO_CODE,
)
from apps.contracts.providers.factory import get_contract_provider
from apps.contracts.services.expiry_service import ContractExpiryService, month_to_code
from apps.exchanges.models import ExchangeMaster
from apps.metadata.models import UnitMaster


class Command(BaseCommand):
    help = "Seeds canonical futures contract specifications and computes active prompt delivery expiries."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing contract specifications and expiries before seeding.",
        )
        parser.add_argument(
            "--start-year",
            type=int,
            default=2026,
            help="Base starting year for delivery contract generation (default: 2026).",
        )
        parser.add_argument(
            "--start-month",
            type=int,
            default=10,
            help="Base starting month for delivery contract generation (default: 10 - October).",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding canonical contract specifications and prompt delivery cycles..."))

        provider = get_contract_provider()
        specs = provider.get_specifications()

        start_year = options["start_year"]
        start_month = options["start_month"]
        today = timezone.now().date()

        with transaction.atomic():
            if options.get("clear"):
                self.stdout.write(self.style.WARNING("Clearing existing contract specifications and expiries..."))
                ContractExpiry.objects.all().delete()
                ContractSpecification.objects.all().delete()

            # Pre-cache lookups
            commodities = {c.code.upper(): c for c in CommodityMaster.objects.all()}
            exchanges = {e.mic.upper(): e for e in ExchangeMaster.objects.all()}
            units = {u.code.upper(): u for u in UnitMaster.objects.all()}

            specs_created_or_updated = 0
            expiries_seeded = 0

            for raw in specs:
                commodity = commodities.get(raw.commodity_code.upper())
                if not commodity:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Commodity '{raw.commodity_code}' not found in database. Skipping spec {raw.symbol_root}."
                        )
                    )
                    continue

                exchange = exchanges.get(raw.exchange_mic.upper())
                if not exchange:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Exchange with MIC '{raw.exchange_mic}' not found. Skipping spec {raw.symbol_root}."
                        )
                    )
                    continue

                contract_unit = units.get(raw.contract_unit_code.upper())
                price_unit = units.get(raw.price_quote_unit_code.upper())

                if not contract_unit or not price_unit:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Units not found for spec {raw.symbol_root} (Contract: {raw.contract_unit_code}, Price: {raw.price_quote_unit_code}). Skipping."
                        )
                    )
                    continue

                spec_obj, _ = ContractSpecification.objects.update_or_create(
                    exchange=exchange,
                    symbol_root=raw.symbol_root,
                    defaults={
                        "commodity": commodity,
                        "name": raw.name,
                        "instrument_type": getattr(InstrumentType, raw.instrument_type, InstrumentType.FUTURES),
                        "contract_size": raw.contract_size,
                        "contract_unit": contract_unit,
                        "price_quote_unit": price_unit,
                        "minimum_tick_size": raw.minimum_tick_size,
                        "tick_value": raw.tick_value,
                        "trading_currency": raw.trading_currency,
                        "settlement_method": getattr(SettlementMethod, raw.settlement_method, SettlementMethod.PHYSICAL),
                        "trading_months": raw.trading_months,
                        "expiry_rule": getattr(ExpiryRuleType, raw.expiry_rule, ExpiryRuleType.DAY_OF_PRIOR_MONTH_WITH_BUS_OFFSET),
                        "expiry_rule_parameter": raw.expiry_rule_parameter,
                        "notice_rule": raw.notice_rule,
                        "default_roll_rule": raw.default_roll_rule,
                        "display_order": raw.display_order,
                        "is_active": True,
                    },
                )
                specs_created_or_updated += 1

                # Generate forward prompt delivery contract expiries
                valid_month_codes = spec_obj.trading_month_codes
                cycles_generated = 0
                step = 0

                while cycles_generated < raw.prompt_cycles_to_seed and step < 60:
                    current_step_month = start_month + step
                    y = start_year + (current_step_month - 1) // 12
                    m = ((current_step_month - 1) % 12) + 1
                    step += 1

                    m_code = month_to_code(m)
                    if m_code not in valid_month_codes:
                        continue

                    schedule = ContractExpiryService.calculate_contract_schedule(spec_obj, y, m)
                    is_expired = schedule["last_trading_day"] < today

                    ContractExpiry.objects.update_or_create(
                        specification=spec_obj,
                        contract_year=y,
                        contract_month=m,
                        defaults={
                            "contract_symbol": schedule["contract_symbol"],
                            "contract_month_code": schedule["contract_month_code"],
                            "last_trading_day": schedule["last_trading_day"],
                            "first_notice_day": schedule["first_notice_day"],
                            "last_delivery_day": schedule["last_delivery_day"],
                            "final_settlement_date": schedule["final_settlement_date"],
                            "is_expired": is_expired,
                            "is_active": True,
                        },
                    )
                    expiries_seeded += 1
                    cycles_generated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded {specs_created_or_updated} contract specifications and {expiries_seeded} delivery expiries."
            )
        )
