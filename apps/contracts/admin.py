"""
Django Admin Configuration for Contract Master and Derivatives.
"""

from django.contrib import admin
from apps.contracts.models import ContractSpecification, ContractExpiry


class ContractExpiryInline(admin.TabularInline):
    model = ContractExpiry
    extra = 0
    fields = [
        "contract_symbol",
        "contract_year",
        "contract_month",
        "contract_month_code",
        "last_trading_day",
        "first_notice_day",
        "final_settlement_date",
        "is_expired",
        "is_active",
    ]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["contract_year", "contract_month"]
    show_change_link = True


@admin.register(ContractSpecification)
class ContractSpecificationAdmin(admin.ModelAdmin):
    list_display = [
        "symbol_root",
        "name",
        "exchange",
        "commodity",
        "instrument_type",
        "contract_size",
        "contract_unit",
        "trading_currency",
        "settlement_method",
        "trading_months",
        "expiry_rule",
        "is_active",
    ]
    list_filter = [
        "exchange",
        "instrument_type",
        "settlement_method",
        "trading_currency",
        "is_active",
    ]
    search_fields = [
        "symbol_root",
        "name",
        "commodity__code",
        "commodity__name",
        "exchange__code",
        "exchange__mic",
    ]
    inlines = [ContractExpiryInline]
    ordering = ["display_order", "exchange", "symbol_root"]


@admin.register(ContractExpiry)
class ContractExpiryAdmin(admin.ModelAdmin):
    list_display = [
        "contract_symbol",
        "specification",
        "contract_year",
        "contract_month_code",
        "last_trading_day",
        "first_notice_day",
        "last_delivery_day",
        "final_settlement_date",
        "is_expired",
        "is_active",
    ]
    list_filter = [
        "contract_year",
        "contract_month_code",
        "is_expired",
        "is_active",
        "specification__exchange",
    ]
    search_fields = [
        "contract_symbol",
        "specification__symbol_root",
        "specification__name",
    ]
    ordering = ["specification__symbol_root", "contract_year", "contract_month"]
