"""
Comprehensive Automated Tests for Phase 13: AI Market Narratives & Hybrid Context.
"""
from decimal import Decimal
import pytest
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.commodities.models import CommodityMaster
from apps.narratives.models import (
    MarketNarrative,
    NarrativeType,
    NarrativeStatus,
    REGULATORY_COMPLIANCE_DISCLAIMER,
)
from apps.narratives.providers.base import BaseLLMProvider, LLMResponse
from apps.narratives.providers.static_catalog import StaticLLMProvider
from apps.narratives.providers.gemini_provider import GeminiLLMProvider
from apps.narratives.providers.claude_provider import ClaudeLLMProvider
from apps.narratives.providers.openai_provider import OpenAILLMProvider
from apps.narratives.providers.ollama_provider import OllamaLLMProvider
from apps.narratives.providers.factory import get_llm_provider
from apps.narratives.services.context_builder import build_narrative_context
from apps.narratives.services.generator import generate_market_narrative


@pytest.fixture(scope="module")
def django_db_setup(django_db_setup, django_db_blocker):
    """Seed prerequisite metadata, exchanges, commodities, contracts, and market data."""
    with django_db_blocker.unblock():
        call_command("seed_metadata")
        call_command("seed_exchanges", skip_api_holidays=True)
        call_command("seed_commodities")
        call_command("seed_contracts")
        call_command("seed_datasets")
        call_command("seed_variables")
        call_command("seed_providers")
        call_command("seed_endpoints")
        call_command("ingest_market_data")
        call_command("seed_narratives", clear=True)


@pytest.mark.django_db
class TestMarketNarrativeModels:
    """Test model constraints, compliance stamping, and point-in-time preservation."""

    def test_narrative_creation_and_disclaimer(self):
        commodity = CommodityMaster.objects.filter(code="CL").first()
        narrative = MarketNarrative.objects.create(
            commodity=commodity,
            narrative_type=NarrativeType.MORNING_BRIEF,
            headline="WTI Crude Oil Test Morning Briefing",
            executive_summary="Executive summary test content.",
            market_context_body="Detailed market context body.",
            key_bullet_points=["Bullet 1", "Bullet 2"],
            risk_factors=["Risk 1", "Risk 2"],
            evidence_snapshot={"price": 90.0, "spread": 0.5},
            llm_provider="static",
            llm_model="test-model",
        )

        assert narrative.id is not None
        assert narrative.headline == "WTI Crude Oil Test Morning Briefing"
        assert narrative.compliance_disclaimer == REGULATORY_COMPLIANCE_DISCLAIMER
        assert narrative.status == NarrativeStatus.PUBLISHED
        assert narrative.availability_time is not None
        assert narrative.evidence_snapshot["price"] == 90.0
        assert str(narrative).startswith("[CL] Morning Executive Briefing")


@pytest.mark.django_db
class TestPluggableLLMProviders:
    """Test provider contracts, offline determinism, and graceful fallbacks."""

    def test_static_llm_provider_generation(self):
        provider = StaticLLMProvider()
        context = {
            "commodity_code": "CL",
            "commodity_name": "Light Sweet Crude Oil",
            "last_price": 91.50,
            "return_1d": 0.012,
            "regime": "BULLISH",
            "trend": "bullish_trend",
            "curve_state": "BACKWARDATION",
            "spread_f1_f2": 0.55,
            "adx": 28.5,
            "rsi": 62.0,
            "rvol": 1.35,
            "composite_score": 0.45,
            "divergences": ["Price vs OI: Mild Bearish Divergence"],
        }
        res = provider.generate_narrative(
            prompt="Test prompt",
            system_instruction="Test system instruction",
            context_dict=context,
            narrative_type="MORNING_BRIEF",
        )

        assert isinstance(res, LLMResponse)
        assert "Light Sweet Crude Oil" in res.headline
        assert "BACKWARDATION" in res.headline
        assert "$91.50" in res.executive_summary
        assert len(res.key_bullet_points) >= 3
        assert len(res.risk_factors) >= 2
        assert res.provider_name == "static"

    def test_provider_factory_resolution(self):
        assert isinstance(get_llm_provider("static"), StaticLLMProvider)
        assert isinstance(get_llm_provider("gemini"), GeminiLLMProvider)
        assert isinstance(get_llm_provider("claude"), ClaudeLLMProvider)
        assert isinstance(get_llm_provider("openai"), OpenAILLMProvider)
        assert isinstance(get_llm_provider("ollama"), OllamaLLMProvider)
        # Unknown provider falls back to static
        assert isinstance(get_llm_provider("unknown_vendor"), StaticLLMProvider)

    def test_remote_providers_graceful_fallback_without_keys(self):
        context = {"commodity_code": "CL", "last_price": 90.0}
        
        gemini = GeminiLLMProvider(api_key="")
        res_gemini = gemini.generate_narrative("test", "test", context)
        assert res_gemini.provider_name == "static"

        claude = ClaudeLLMProvider(api_key="")
        res_claude = claude.generate_narrative("test", "test", context)
        assert res_claude.provider_name == "static"

        openai = OpenAILLMProvider(api_key="")
        res_openai = openai.generate_narrative("test", "test", context)
        assert res_openai.provider_name == "static"

        ollama = OllamaLLMProvider(base_url="http://invalid-host:9999")
        res_ollama = ollama.generate_narrative("test", "test", context)
        assert res_ollama.provider_name == "static"


@pytest.mark.django_db
class TestContextBuilderAndGenerator:
    """Test multi-source fusion and generation pipeline."""

    def test_build_narrative_context_fuses_sources(self):
        prompt_md, context = build_narrative_context("CL")
        assert "GROUND-TRUTH MARKET EVIDENCE" in prompt_md
        assert context["commodity_code"] == "CL"
        assert "last_price" in context
        assert "curve_state" in context
        assert "rvol" in context
        assert "upcoming_catalysts" in context

    def test_generate_market_narrative_persists_record(self):
        narrative = generate_market_narrative(
            commodity_code="CL",
            narrative_type=NarrativeType.RISK_ALERT,
            provider_name="static",
        )
        assert narrative.id is not None
        assert narrative.narrative_type == NarrativeType.RISK_ALERT
        assert narrative.commodity.code == "CL"
        assert narrative.llm_provider == "static"
        assert narrative.compliance_disclaimer == REGULATORY_COMPLIANCE_DISCLAIMER
        assert narrative.evidence_snapshot["commodity_code"] == "CL"


@pytest.mark.django_db
class TestLangChainNarrativeChains:
    """Test LangChain LCEL chains, ChatModel instances, and schema parsers."""

    def test_langchain_model_instances(self):
        from langchain_core.language_models.chat_models import BaseChatModel
        for prov_name in ["static", "gemini", "claude", "openai", "ollama"]:
            prov = get_llm_provider(prov_name)
            model = prov.get_langchain_model()
            assert isinstance(model, BaseChatModel)

    def test_langchain_lcel_execution(self):
        from apps.narratives.chains.narrative_chain import execute_narrative_chain
        prompt_md, context = build_narrative_context("CL")
        res = execute_narrative_chain(
            prompt_markdown=prompt_md,
            context_dict=context,
            provider_name="static",
            narrative_type="MORNING_BRIEF",
        )
        assert isinstance(res, LLMResponse)
        assert res.headline is not None
        assert len(res.key_bullet_points) >= 1
        assert res.raw_response.get("framework") == "langchain_lcel"


@pytest.mark.django_db
class TestNarrativesAPI:
    """Test REST API views for narratives."""

    def setup_method(self):
        self.client = APIClient()

    def test_list_narratives(self):
        url = reverse("narratives:narrative-list")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_narratives_by_commodity_and_type(self):
        url = reverse("narratives:narrative-list")
        response = self.client.get(url, {"commodity": "CL", "type": "MORNING_BRIEF"})
        assert response.status_code == status.HTTP_200_OK
        for item in response.data:
            assert item["commodity_code"] == "CL"
            assert item["narrative_type"] == "MORNING_BRIEF"

    def test_retrieve_narrative_by_id(self):
        item = MarketNarrative.objects.first()
        url = reverse("narratives:narrative-detail", kwargs={"id": str(item.id)})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(item.id)
        assert response.data["headline"] == item.headline

    def test_latest_narrative_endpoint(self):
        url = reverse("narratives:narrative-latest")
        response = self.client.get(url, {"commodity": "CL"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["commodity_code"] == "CL"

    def test_generate_narrative_endpoint(self):
        url = reverse("narratives:narrative-generate")
        payload = {
            "commodity": "NG",
            "narrative_type": "EXECUTIVE_FLASH",
            "provider": "static",
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["commodity_code"] == "NG"
        assert response.data["narrative_type"] == "EXECUTIVE_FLASH"

    def test_summary_telemetry_endpoint(self):
        url = reverse("narratives:narrative-summary")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "total_narratives" in response.data
        assert "by_type" in response.data
        assert "by_provider" in response.data
        assert response.data["total_narratives"] >= 1
