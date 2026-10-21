"""
REST API Serializers for Market Narratives.
"""
from rest_framework import serializers
from .models import MarketNarrative


class MarketNarrativeSerializer(serializers.ModelSerializer):
    commodity_code = serializers.CharField(source="commodity.code", read_only=True)
    commodity_name = serializers.CharField(source="commodity.name", read_only=True)
    narrative_type_display = serializers.CharField(source="get_narrative_type_display", read_only=True)

    class Meta:
        model = MarketNarrative
        fields = [
            "id",
            "commodity",
            "commodity_code",
            "commodity_name",
            "narrative_type",
            "narrative_type_display",
            "headline",
            "executive_summary",
            "market_context_body",
            "key_bullet_points",
            "risk_factors",
            "evidence_snapshot",
            "llm_provider",
            "llm_model",
            "prompt_tokens",
            "completion_tokens",
            "status",
            "compliance_disclaimer",
            "availability_time",
            "ingestion_time",
        ]
        read_only_fields = fields


class GenerateNarrativeRequestSerializer(serializers.Serializer):
    commodity = serializers.CharField(required=False, default="CL", max_length=16)
    narrative_type = serializers.ChoiceField(
        choices=[
            "MORNING_BRIEF",
            "EXECUTIVE_FLASH",
            "SUPPLY_DEMAND",
            "RISK_ALERT",
            "OUTLIER_DIVERGENCE",
        ],
        default="MORNING_BRIEF",
    )
    provider = serializers.CharField(required=False, allow_blank=True, default=None)
