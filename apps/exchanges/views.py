"""
REST API Views for Exchange Master, Sessions, and Trading Calendars.
"""
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
from .models import ExchangeMaster, ExchangeHoliday, ExchangeTradingSession
from .serializers import (
    ExchangeMasterListSerializer,
    ExchangeMasterDetailSerializer,
    ExchangeHolidaySerializer,
)


from django.db.models import Q


def get_exchange_by_identifier(identifier: str) -> ExchangeMaster:
    """Looks up exchange by canonical code or ISO 10383 MIC."""
    return get_object_or_404(
        ExchangeMaster,
        Q(code__iexact=identifier) | Q(mic__iexact=identifier),
    )


class ExchangeListAPIView(ListAPIView):
    """Lists supported exchanges with optional filtering (?country=US, ?tier=GLOBAL_BENCHMARK)."""
    serializer_class = ExchangeMasterListSerializer

    def get_queryset(self):
        qs = ExchangeMaster.objects.filter(is_active=True)
        country = self.request.query_params.get("country")
        tier = self.request.query_params.get("tier")
        currency = self.request.query_params.get("currency")

        if country:
            qs = qs.filter(country=country.upper())
        if tier:
            qs = qs.filter(tier=tier.upper())
        if currency:
            qs = qs.filter(currency=currency.upper())

        return qs.order_by("code")


class ExchangeDetailAPIView(APIView):
    """Retrieves full profile for an exchange by code or MIC (e.g. /api/exchanges/NYMEX/ or /api/exchanges/XNYM/)."""

    def get(self, request, identifier):
        exchange = ExchangeMaster.objects.filter(code__iexact=identifier).first() or \
                   ExchangeMaster.objects.filter(mic__iexact=identifier).first()
        if not exchange:
            return Response({"detail": f"Exchange '{identifier}' not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ExchangeMasterDetailSerializer(exchange)
        return Response(serializer.data)


class ExchangeTradingDayAPIView(APIView):
    """
    Evaluates whether a given date is an active trading day and/or settlement day on this exchange.
    Usage:
      /api/exchanges/CME/is-trading-day/?date=2026-12-25
      /api/exchanges/NYMEX/is-trading-day/?date=2025-05-26&require_settlement=true
      /api/exchanges/CBOT/is-trading-day/?date=2025-05-26&product_group=AGRICULTURE
    """

    def get(self, request, identifier):
        exchange = ExchangeMaster.objects.filter(code__iexact=identifier).first() or \
                   ExchangeMaster.objects.filter(mic__iexact=identifier).first()
        if not exchange:
            return Response({"detail": f"Exchange '{identifier}' not found."}, status=status.HTTP_404_NOT_FOUND)

        date_param = request.query_params.get("date")
        if not date_param:
            target_date = timezone.now().date()
        else:
            try:
                target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD (e.g. 2026-12-25)"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        product_group = request.query_params.get("product_group")
        require_settlement_str = request.query_params.get("require_settlement", "false").lower()
        require_settlement = require_settlement_str in ("true", "1", "yes")

        market_status = exchange.get_market_status(target_date, product_group=product_group)
        is_trading = exchange.is_trading_day(target_date, product_group=product_group)
        is_settlement = exchange.is_settlement_day(target_date, product_group=product_group)

        effective_status = is_settlement if require_settlement else is_trading

        data = {
            "exchange": exchange.code,
            "mic": exchange.mic,
            "date": target_date.isoformat(),
            "weekday": target_date.strftime("%A"),
            "is_weekend": target_date.weekday() >= 5,
            "is_trading_day": is_trading,
            "is_settlement_day": is_settlement,
            "require_settlement": require_settlement,
            "product_group": product_group,
            "result": effective_status,
            "market_status": market_status["status"],
            "settlement_rolled_to_next_day": market_status["settlement_rolled"],
            "early_close_time": market_status["early_close_time"],
            "holiday": {
                "name": market_status["holiday_name"],
                "has_trading": market_status["has_trading"],
                "has_settlement": market_status["has_settlement"],
                "affected_product_groups": market_status["affected_product_groups"],
            } if market_status["holiday_name"] else None,
        }
        return Response(data, status=status.HTTP_200_OK)


class ExchangeHolidayListAPIView(ListAPIView):
    """Lists calendar holidays for a specific exchange, filterable by ?year=2026."""
    serializer_class = ExchangeHolidaySerializer

    def get_queryset(self):
        identifier = self.kwargs["identifier"]
        exchange = ExchangeMaster.objects.filter(code__iexact=identifier).first() or \
                   ExchangeMaster.objects.filter(mic__iexact=identifier).first()
        if not exchange:
            return ExchangeHoliday.objects.none()

        qs = exchange.holidays.filter(is_active=True)
        year = self.request.query_params.get("year")
        if year:
            try:
                qs = qs.filter(date__year=int(year))
            except ValueError:
                pass
        return qs.order_by("date")


class ExchangeSummaryAPIView(APIView):
    """High-level summary of active venues, tiers, and holiday coverage."""

    def get(self, request):
        data = {
            "phase": "Phase 3: Exchange Master",
            "exchanges": {
                "total": ExchangeMaster.objects.count(),
                "active": ExchangeMaster.objects.filter(is_active=True).count(),
                "global_benchmarks": ExchangeMaster.objects.filter(tier="GLOBAL_BENCHMARK").count(),
            },
            "trading_sessions": ExchangeTradingSession.objects.filter(is_active=True).count(),
            "holidays_tracked": ExchangeHoliday.objects.filter(is_active=True).count(),
        }
        return Response(data, status=status.HTTP_200_OK)
