"""
REST API Views for AI Market Narratives.
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count

from .models import MarketNarrative, NarrativeStatus
from .serializers import (
    MarketNarrativeSerializer,
    GenerateNarrativeRequestSerializer,
)
from .services.generator import generate_market_narrative


class MarketNarrativeListView(generics.ListAPIView):
    """
    List historical AI Market Narratives with multi-factor filtering.
    
    Query Parameters:
        - `commodity`: Canonical commodity code (e.g., 'CL', 'BRENT', 'GOLD')
        - `type`: Narrative type (MORNING_BRIEF, EXECUTIVE_FLASH, SUPPLY_DEMAND, RISK_ALERT, OUTLIER_DIVERGENCE)
        - `provider`: Filter by LLM provider (static, gemini, claude, openai, ollama)
        - `status`: Filter by status (PUBLISHED, DRAFT, ARCHIVED)
        - `search`: Keyword search across headline and executive summary
    """
    serializer_class = MarketNarrativeSerializer

    def get_queryset(self):
        qs = MarketNarrative.objects.select_related("commodity").all()
        
        commodity = self.request.query_params.get("commodity")
        if commodity:
            qs = qs.filter(commodity__code__iexact=commodity)

        n_type = self.request.query_params.get("type")
        if n_type:
            qs = qs.filter(narrative_type__iexact=n_type)

        provider = self.request.query_params.get("provider")
        if provider:
            qs = qs.filter(llm_provider__iexact=provider)

        narrative_status = self.request.query_params.get("status")
        if narrative_status:
            qs = qs.filter(status__iexact=narrative_status)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(headline__icontains=search) | qs.filter(executive_summary__icontains=search)

        return qs.order_by("-availability_time")


class MarketNarrativeDetailView(generics.RetrieveAPIView):
    """Retrieve full details of a specific Market Narrative by UUID."""
    queryset = MarketNarrative.objects.select_related("commodity").all()
    serializer_class = MarketNarrativeSerializer
    lookup_field = "id"


class LatestMarketNarrativeView(APIView):
    """
    Retrieve the most recent published narrative for a given commodity and type.
    """
    def get(self, request):
        commodity = request.query_params.get("commodity", "CL").upper()
        n_type = request.query_params.get("type")

        qs = MarketNarrative.objects.filter(
            commodity__code=commodity,
            status=NarrativeStatus.PUBLISHED,
        )
        if n_type:
            qs = qs.filter(narrative_type=n_type)

        latest = qs.order_by("-availability_time").first()
        if not latest:
            # If none exists yet, generate one on-the-fly
            try:
                latest = generate_market_narrative(
                    commodity_code=commodity,
                    narrative_type=n_type or "MORNING_BRIEF",
                )
            except Exception as exc:
                return Response(
                    {"error": f"No narrative found and on-demand generation failed: {exc}"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        serializer = MarketNarrativeSerializer(latest)
        return Response(serializer.data)


class GenerateMarketNarrativeView(APIView):
    """
    On-demand API endpoint to trigger AI narrative generation.
    """
    def post(self, request):
        serializer = GenerateNarrativeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            narrative = generate_market_narrative(
                commodity_code=data.get("commodity", "CL"),
                narrative_type=data.get("narrative_type", "MORNING_BRIEF"),
                provider_name=data.get("provider") or None,
            )
            return Response(
                MarketNarrativeSerializer(narrative).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return Response(
                {"error": f"Failed to generate narrative: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class NarrativesSummaryView(APIView):
    """
    Telemetry and aggregate metrics across market narratives.
    """
    def get(self, request):
        total = MarketNarrative.objects.count()
        by_type = dict(
            MarketNarrative.objects.values("narrative_type")
            .annotate(count=Count("id"))
            .values_list("narrative_type", "count")
        )
        by_provider = dict(
            MarketNarrative.objects.values("llm_provider")
            .annotate(count=Count("id"))
            .values_list("llm_provider", "count")
        )
        latest_item = MarketNarrative.objects.order_by("-availability_time").first()

        return Response({
            "total_narratives": total,
            "by_type": by_type,
            "by_provider": by_provider,
            "latest_publication": latest_item.availability_time if latest_item else None,
        })
