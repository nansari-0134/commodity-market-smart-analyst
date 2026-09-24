"""
Endpoint & API Metadata models and enumerations.

Represents specific vendor API routes, path templates, HTTP methods,
request parameter schemas, response formats, and target dataset bindings.
"""

from urllib.parse import urljoin
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, UUIDModel


class ProtocolType(models.TextChoices):
    """Network protocol used to communicate with the endpoint."""

    REST_HTTP = "REST_HTTP", _("REST / HTTP API")
    FTP_SFTP = "FTP_SFTP", _("FTP / SFTP Batch File Server")
    WEBSOCKET = "WEBSOCKET", _("WebSocket Live Streaming")


class HttpMethod(models.TextChoices):
    """HTTP method for web endpoints."""

    GET = "GET", _("HTTP GET")
    POST = "POST", _("HTTP POST")


class ResponseFormat(models.TextChoices):
    """Payload serialization format returned by the endpoint."""

    JSON = "JSON", _("JSON Object/Array")
    CSV = "CSV", _("Comma-Separated Values (CSV)")
    TSV = "TSV", _("Tab-Separated Values (TSV)")
    XML = "XML", _("XML Document")
    ZIP = "ZIP", _("Compressed ZIP Archive")
    PARQUET = "PARQUET", _("Apache Parquet Columnar")
    EXCEL_XLSX = "EXCEL_XLSX", _("Microsoft Excel (.xlsx)")


class EndpointMaster(UUIDModel, TimeStampedModel):
    """
    Canonical registry for vendor API routes, endpoints, and data contracts.
    Bridges WHO provides data (ProviderMaster) with WHAT is ingested (DatasetMaster).
    """

    code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Canonical unique identifier (e.g. EIA_PETROLEUM_SPOT_DAILY, CFTC_COT_DISAGGREGATED_FUT).",
    )
    name = models.CharField(
        max_length=150,
        help_text="Human-readable title describing the endpoint feed.",
    )
    description = models.TextField(
        blank=True,
        help_text="Operational description of endpoint data, update schedule, and query scope.",
    )
    provider = models.ForeignKey(
        "providers.ProviderMaster",
        on_delete=models.CASCADE,
        related_name="endpoints",
        help_text="Data vendor providing this API endpoint.",
    )
    dataset = models.ForeignKey(
        "datasets.DatasetMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="endpoints",
        help_text="Target canonical dataset populated by this endpoint.",
    )
    protocol = models.CharField(
        max_length=20,
        choices=ProtocolType.choices,
        default=ProtocolType.REST_HTTP,
        db_index=True,
        help_text="Underlying transport protocol.",
    )
    http_method = models.CharField(
        max_length=10,
        choices=HttpMethod.choices,
        default=HttpMethod.GET,
        help_text="HTTP request method.",
    )
    path_template = models.CharField(
        max_length=500,
        help_text="Relative route or path template appended to provider base_url (e.g. 'petroleum/pri/spt/data/').",
    )
    response_format = models.CharField(
        max_length=20,
        choices=ResponseFormat.choices,
        default=ResponseFormat.JSON,
        db_index=True,
        help_text="Data serialization format returned by this endpoint.",
    )
    data_envelope_path = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Dot-separated path or JSON key to records array (e.g. 'response.data', 'observations', or blank for root array).",
    )
    default_params = models.JSONField(
        default=dict,
        blank=True,
        help_text="Default query parameters and pagination keys (e.g. {'frequency': 'weekly', 'length': 5000}).",
    )
    custom_headers = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom HTTP request headers (e.g. {'Accept': 'application/json'}).",
    )
    cache_ttl_seconds = models.PositiveIntegerField(
        default=3600,
        help_text="Ingestion cache lifetime in seconds (default 3600 = 1 hour).",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Flag indicating whether endpoint is active for automated ingestion runs.",
    )
    is_deprecated = models.BooleanField(
        default=False,
        help_text="Flag indicating whether the vendor has deprecated this endpoint version.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes, migration history, or vendor quirks.",
    )

    class Meta:
        verbose_name = _("Endpoint Master")
        verbose_name_plural = _("Endpoint Masters")
        ordering = ["provider__code", "code"]
        indexes = [
            models.Index(fields=["provider", "is_active"]),
            models.Index(fields=["dataset", "is_active"]),
            models.Index(fields=["response_format"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} [{self.http_method} {self.path_template}] ({self.provider.code})"

    def get_full_url(self, **path_kwargs) -> str:
        """
        Resolves the full URL by combining the parent provider's base_url with the path_template.
        Accepts optional path interpolation kwargs (e.g. symbol='CL', series_id='PET.RWTC.D').
        """
        base = self.provider.base_url.rstrip("/") + "/"
        path = self.path_template.lstrip("/")
        if path_kwargs:
            path = path.format(**path_kwargs)
        return urljoin(base, path)

    def build_request_params(self, runtime_params: dict | None = None) -> dict:
        """
        Merges stored default query parameters with runtime overrides.
        """
        params = dict(self.default_params)
        if runtime_params:
            params.update(runtime_params)
        return params
