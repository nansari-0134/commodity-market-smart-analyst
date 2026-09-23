"""
Provider Master models and enumerations.

Represents data vendors, government statistical agencies, exchange data feeds,
12-factor credential environment references, rate limit policies, and fallback failovers.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, UUIDModel


class ProviderType(models.TextChoices):
    """Broad institutional categorization of data vendors and sources."""

    GOVERNMENT_PUBLIC = "GOVERNMENT_PUBLIC", _("Government / Public Statistical Agency")
    EXCHANGE_DIRECT = "EXCHANGE_DIRECT", _("Exchange Direct Market Data")
    PRICE_REPORTING_AGENCY = "PRICE_REPORTING_AGENCY", _("Price Reporting Agency (PRA)")
    COMMERCIAL_AGGREGATOR = "COMMERCIAL_AGGREGATOR", _("Commercial Market Data Aggregator")
    ALTERNATIVE_DATA = "ALTERNATIVE_DATA", _("Alternative Data & Physical Flows")
    INTERNAL_ENGINE = "INTERNAL_ENGINE", _("Internal Quant Calculation Engine")


class AuthType(models.TextChoices):
    """Protocol used to authenticate with the vendor API."""

    NONE_PUBLIC = "NONE_PUBLIC", _("No Authentication (Public Open Data)")
    API_KEY_QUERY_PARAM = "API_KEY_QUERY_PARAM", _("API Key (URL Query Parameter)")
    API_KEY_HEADER = "API_KEY_HEADER", _("API Key (HTTP Header)")
    BEARER_TOKEN = "BEARER_TOKEN", _("Bearer Token (Authorization Header)")
    BASIC_AUTH = "BASIC_AUTH", _("Basic Auth (Username/Password)")
    OAUTH2_CLIENT_CREDENTIALS = "OAUTH2_CLIENT_CREDENTIALS", _("OAuth 2.0 (Client Credentials Grant)")


class ProviderMaster(UUIDModel, TimeStampedModel):
    """
    Canonical registry for all external data sources, PRAs, exchange data feeds,
    and internal calculation services.
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Canonical unique identifier (e.g. EIA_GOV, CME_DATAMINE, ARGUS_MEDIA).",
    )
    name = models.CharField(
        max_length=120,
        help_text="Full institutional organization or vendor title.",
    )
    description = models.TextField(
        blank=True,
        help_text="Provider coverage, data methodology, and licensing scope.",
    )
    provider_type = models.CharField(
        max_length=32,
        choices=ProviderType.choices,
        default=ProviderType.GOVERNMENT_PUBLIC,
        db_index=True,
        help_text="Institutional classification of the data provider.",
    )
    base_url = models.URLField(
        max_length=255,
        help_text="Root endpoint or service URL (e.g. https://api.eia.gov/v2/).",
    )
    documentation_url = models.URLField(
        max_length=255,
        blank=True,
        help_text="Official developer API documentation URL.",
    )
    support_contact = models.CharField(
        max_length=150,
        blank=True,
        help_text="Vendor technical support email or contact portal.",
    )

    # 12-Factor Security & Authentication
    auth_type = models.CharField(
        max_length=32,
        choices=AuthType.choices,
        default=AuthType.NONE_PUBLIC,
        db_index=True,
        help_text="Authentication protocol expected by the vendor.",
    )
    env_var_name = models.CharField(
        max_length=80,
        blank=True,
        help_text="Environment variable name containing the secret (e.g. EIA_API_KEY). Never stores plaintext secrets.",
    )
    auth_param_name = models.CharField(
        max_length=60,
        blank=True,
        help_text="Query parameter or header name (e.g. 'api_key', 'X-API-KEY').",
    )

    # Rate Limiting & Backoff Policies
    rate_limit_requests = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum request budget permitted per time window (null = unmetered).",
    )
    rate_limit_window_seconds = models.PositiveIntegerField(
        default=60,
        help_text="Rate limit time window in seconds (default 60s).",
    )
    backoff_seconds = models.PositiveIntegerField(
        default=60,
        help_text="Retry backoff interval in seconds upon encountering HTTP 429.",
    )

    # SLA & Redundancy / Failover
    target_sla_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=99.50,
        help_text="Target service level availability percentage.",
    )
    fallback_provider = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fallback_for",
        help_text="Secondary failover vendor if this primary provider is unavailable.",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this provider is actively used in ingestion workflows.",
    )
    display_order = models.PositiveIntegerField(
        default=100,
        help_text="Display and sort priority.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Operational notes or special handling instructions.",
    )

    class Meta:
        db_table = "providers_master"
        ordering = ["display_order", "code"]
        verbose_name = _("Provider Master")
        verbose_name_plural = _("Provider Master Catalog")

    def __str__(self) -> str:
        return f"{self.code}: {self.name} ({self.get_provider_type_display()})"

    @property
    def has_rate_limit(self) -> bool:
        """Return True if an explicit rate limit budget is configured."""
        return self.rate_limit_requests is not None

    @property
    def requires_auth(self) -> bool:
        """Return True if provider requires an API key or credentials."""
        return self.auth_type != AuthType.NONE_PUBLIC
