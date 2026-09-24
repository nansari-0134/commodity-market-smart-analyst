"""
Static Canonical Endpoint Catalog Reference Provider.

Supplies institutional benchmark API endpoint specifications across global commodity data providers
(EIA, CFTC, FRED, USDA, NOAA, CME, ICE, LME, EEX, MCX, INE, Argus, Platts, Fastmarkets, Bloomberg, Refinitiv, Kpler).
Guarantees 100% offline capability, zero vendor API dependencies, and deterministic testing fixtures.
"""

from typing import List, Optional

from .base import BaseEndpointCatalogProvider, RawEndpointSpec


class StaticEndpointCatalogProvider(BaseEndpointCatalogProvider):
    """
    Default deterministic static provider supplying canonical endpoint metadata.
    """

    def get_endpoints(self) -> List[RawEndpointSpec]:
        return self._catalog()

    def get_endpoint(self, code: str) -> Optional[RawEndpointSpec]:
        for spec in self._catalog():
            if spec.code.upper() == code.upper():
                return spec
        return None

    def _catalog(self) -> List[RawEndpointSpec]:
        return [
            # =========================================================================
            # 1. US ENERGY INFORMATION ADMINISTRATION (EIA)
            # =========================================================================
            RawEndpointSpec(
                code="EIA_PETROLEUM_SPOT_PRICES",
                name="EIA v2 Petroleum Spot Prices API",
                description="Daily spot prices for WTI crude at Cushing, Brent crude, heating oil, and gasoline.",
                provider_code="EIA_GOV",
                dataset_code="EIA_WPSR_PETROLEUM_STOCKS",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="petroleum/pri/spt/data/",
                response_format="JSON",
                data_envelope_path="response.data",
                default_params={"frequency": "daily", "data[]": "value", "length": 5000},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=3600,
                notes="Requires api_key query param. Frequency choices: daily, weekly, monthly.",
            ),
            RawEndpointSpec(
                code="EIA_CRUDE_STOCKS_WEEKLY",
                name="EIA v2 Weekly Petroleum Stocks API",
                description="Weekly commercial crude oil, Strategic Petroleum Reserve (SPR), and product inventories.",
                provider_code="EIA_GOV",
                dataset_code="EIA_WPSR_PETROLEUM_STOCKS",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="petroleum/stoc/wstk/data/",
                response_format="JSON",
                data_envelope_path="response.data",
                default_params={"frequency": "weekly", "data[]": "value", "length": 5000},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=86400,
                notes="Published Wednesdays at 10:30 AM EST (14:30 UTC).",
            ),
            RawEndpointSpec(
                code="EIA_NATGAS_STORAGE_WEEKLY",
                name="EIA v2 Weekly Natural Gas Underground Storage API",
                description="Weekly working gas in underground storage for the Lower 48 and five EIA regions.",
                provider_code="EIA_GOV",
                dataset_code="EIA_WEEKLY_NATURAL_GAS_STORAGE",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="natural-gas/stor/wkly/data/",
                response_format="JSON",
                data_envelope_path="response.data",
                default_params={"frequency": "weekly", "data[]": "value", "length": 5000},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=86400,
                notes="Published Thursdays at 10:30 AM EST (14:30 UTC).",
            ),

            # =========================================================================
            # 2. COMMODITY FUTURES TRADING COMMISSION (CFTC)
            # =========================================================================
            RawEndpointSpec(
                code="CFTC_COT_DISAGGREGATED_FUT",
                name="CFTC Disaggregated Commitments of Traders Socrata API",
                description="Weekly breakdown of trader positioning across Producer/Merchant, Swap Dealer, Managed Money, and Other Reportables.",
                provider_code="CFTC_GOV",
                dataset_code="CFTC_COT_DISAGGREGATED_FUT_OPT",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="resource/jun7-fc8e.json",
                response_format="JSON",
                data_envelope_path="",
                default_params={"$limit": 5000, "$order": "report_date_as_yyyy_mm_dd DESC"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=86400,
                notes="Socrata open data REST API. Root array of JSON records.",
            ),
            RawEndpointSpec(
                code="CFTC_COT_FINANCIAL_FUT",
                name="CFTC Traders in Financial Futures (TFF) Socrata API",
                description="Weekly financial futures commitments of traders for currencies, rates, and equity indices.",
                provider_code="CFTC_GOV",
                dataset_code=None,
                protocol="REST_HTTP",
                http_method="GET",
                path_template="resource/72hh-3qpy.json",
                response_format="JSON",
                data_envelope_path="",
                default_params={"$limit": 5000, "$order": "report_date_as_yyyy_mm_dd DESC"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=86400,
                notes="Published Fridays at 15:30 EST (20:30 UTC).",
            ),

            # =========================================================================
            # 3. FEDERAL RESERVE ECONOMIC DATA (FRED)
            # =========================================================================
            RawEndpointSpec(
                code="FRED_SERIES_OBSERVATIONS",
                name="FRED Series Economic Observations API",
                description="Macroeconomic series observations (CPI, PPI, Interest Rates, US Dollar Index).",
                provider_code="FRED_FED",
                dataset_code=None,
                protocol="REST_HTTP",
                http_method="GET",
                path_template="series/observations",
                response_format="JSON",
                data_envelope_path="observations",
                default_params={"file_type": "json", "sort_order": "desc"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=86400,
                notes="Requires series_id parameter (e.g. series_id=DCOILWTICO).",
            ),
            RawEndpointSpec(
                code="FRED_SERIES_METADATA",
                name="FRED Series Metadata & Release Information",
                description="Metadata, units, frequency, and seasonal adjustment descriptors for economic series.",
                provider_code="FRED_FED",
                dataset_code=None,
                protocol="REST_HTTP",
                http_method="GET",
                path_template="series",
                response_format="JSON",
                data_envelope_path="seriess",
                default_params={"file_type": "json"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=604800,
                notes="Weekly or monthly metadata synchronization.",
            ),

            # =========================================================================
            # 4. USDA FOREIGN AGRICULTURAL SERVICE (FAS)
            # =========================================================================
            RawEndpointSpec(
                code="USDA_EXPORT_SALES_COMMODITIES",
                name="USDA FAS Export Sales Reporting Commodity Data",
                description="Weekly US physical export sales, outstanding commitments, and accumulated exports.",
                provider_code="USDA_FAS",
                dataset_code="USDA_EXPORT_SALES_WEEKLY",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="api/esr/exportsales/commodityData/",
                response_format="JSON",
                data_envelope_path="",
                default_params={},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=86400,
                notes="Published Thursdays at 08:30 EST (13:30 UTC).",
            ),
            RawEndpointSpec(
                code="USDA_EXPORT_SALES_COUNTRIES",
                name="USDA FAS Country Destinations API",
                description="Directory of trading partner destination countries for US export flow tracking.",
                provider_code="USDA_FAS",
                dataset_code="USDA_EXPORT_SALES_WEEKLY",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="api/esr/countries/",
                response_format="JSON",
                data_envelope_path="",
                default_params={},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=604800,
                notes="Reference lookup for trade flow origin-destination mapping.",
            ),

            # =========================================================================
            # 5. USDA NATIONAL AGRICULTURAL STATISTICS SERVICE (NASS)
            # =========================================================================
            RawEndpointSpec(
                code="USDA_QUICKSTATS_DATA",
                name="USDA NASS QuickStats Agricultural Data API",
                description="Crop acreage, planting progress, harvesting progress, yield, and condition ratings.",
                provider_code="USDA_NASS",
                dataset_code="USDA_CROP_PROGRESS_WEEKLY",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="api_get_data/",
                response_format="JSON",
                data_envelope_path="data",
                default_params={"format": "JSON"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=86400,
                notes="Requires api_key query param. Query filters: commodity_desc, year, state_alpha.",
            ),

            # =========================================================================
            # 6. NATIONAL OCEANIC AND ATMOSPHERIC ADMINISTRATION (NOAA)
            # =========================================================================
            RawEndpointSpec(
                code="NOAA_WEATHER_GRIDPOINTS",
                name="NOAA National Weather Service Grid Forecast API",
                description="Weather forecasts, temperature anomalies, and precipitation for key agricultural & energy gridpoints.",
                provider_code="NOAA_NWS",
                dataset_code="NOAA_CPC_ENSO_OUTLOOK",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="gridpoints/{wfo}/{x},{y}/forecast",
                response_format="JSON",
                data_envelope_path="properties.periods",
                default_params={},
                custom_headers={"Accept": "application/geo+json", "User-Agent": "CommoditySmartAnalyst/1.0"},
                cache_ttl_seconds=21600,
                notes="Public open data. Strict User-Agent header required by weather.gov.",
            ),

            # =========================================================================
            # 7. CME DATAMINE (CHICAGO MERCANTILE EXCHANGE)
            # =========================================================================
            RawEndpointSpec(
                code="CME_DATAMINE_EOD_SETTLE",
                name="CME Datamine EOD Futures Settlements API",
                description="Official closing settlement prices, trade volume, and open interest for NYMEX, COMEX, and CBOT contracts.",
                provider_code="CME_DATAMINE",
                dataset_code="CME_FUTURES_EOD",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="v1/settlements/eod",
                response_format="JSON",
                data_envelope_path="results",
                default_params={"pageSize": 1000},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=1800,
                notes="Commercial OAuth2 credentials required. Rate-limited to 60 req/min.",
            ),
            RawEndpointSpec(
                code="CME_DATAMINE_BLOCK_TRADES",
                name="CME Datamine Block Trades & EFRP Feed",
                description="Off-exchange negotiated block trades, Exchange for Physical (EFP), and Exchange for Risk (EFR).",
                provider_code="CME_DATAMINE",
                dataset_code="CME_FUTURES_EOD",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="v1/trades/blocks",
                response_format="JSON",
                data_envelope_path="trades",
                default_params={"limit": 500},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=1800,
                notes="Institutional block trade surveillance.",
            ),

            # =========================================================================
            # 8. ICE DATA SERVICES (INTERCONTINENTAL EXCHANGE)
            # =========================================================================
            RawEndpointSpec(
                code="ICE_DATA_COMMODITIES_EOD",
                name="ICE Data Services Global Commodities EOD API",
                description="Daily official settlements and forward curve marks for Brent, Gasoil, WTI, and Sugar.",
                provider_code="ICE_DATA_SERVICES",
                dataset_code="ICE_BRENT_DAILY_SETTLEMENTS",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="v2/markets/commodities/eod",
                response_format="JSON",
                data_envelope_path="data.settlements",
                default_params={"format": "json"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=1800,
                notes="Requires Bearer Token authentication.",
            ),

            # =========================================================================
            # 9. LONDON METAL EXCHANGE (LME)
            # =========================================================================
            RawEndpointSpec(
                code="LME_NONFERROUS_OFFICIAL",
                name="LME Official Cash & 3-Month Settlement Prices",
                description="Daily official and unofficial settlement prices for Copper, Aluminum, Zinc, Nickel, Lead, and Tin.",
                provider_code="LME_DATA",
                dataset_code="LME_DAILY_OFFICIAL_PRICES",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="v1/pricing/nonferrous/official",
                response_format="JSON",
                data_envelope_path="prices",
                default_params={"currency": "USD"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=3600,
                notes="Morning Ring official cash/3M prices.",
            ),

            # =========================================================================
            # 10. EUROPEAN ENERGY EXCHANGE (EEX)
            # =========================================================================
            RawEndpointSpec(
                code="EEX_POWER_BENCHMARKS",
                name="EEX European Power & Carbon Allowances EOD",
                description="End-of-day futures settlement prices for German Power (Phelix) and EU ETS Carbon Allowances.",
                provider_code="EEX_DATA",
                dataset_code="EEX_EUA_CARBON_AUCTION_RESULTS",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="v1/markets/power/eod",
                response_format="JSON",
                data_envelope_path="items",
                default_params={"market": "EEX_GERMANY"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=3600,
                notes="European gas, power, and environmental markets.",
            ),

            # =========================================================================
            # 11. MULTI COMMODITY EXCHANGE OF INDIA (MCX)
            # =========================================================================
            RawEndpointSpec(
                code="MCX_INDIA_BHAVCOPY",
                name="MCX India Daily Bhavcopy End-of-Day Report",
                description="Daily trading summary for Crude Oil, Natural Gas, Gold, and Cotton on MCX.",
                provider_code="MCX_INDIA",
                dataset_code="MCX_DAILY_COMMODITY_SETTLEMENTS",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="v1/market-data/bhavcopy",
                response_format="CSV",
                data_envelope_path="",
                default_params={"format": "csv"},
                custom_headers={"Accept": "text/csv"},
                cache_ttl_seconds=3600,
                notes="Downloadable CSV Bhavcopy report for Indian physical and derivative markets.",
            ),

            # =========================================================================
            # 12. SHANGHAI INTERNATIONAL ENERGY EXCHANGE (INE)
            # =========================================================================
            RawEndpointSpec(
                code="INE_CRUDE_DAILY_REPORT",
                name="Shanghai INE Medium Sour Crude Oil Daily Report",
                description="Daily settlement prices, trade volume, and warehouse warrants for INE RMB-denominated Crude Oil.",
                provider_code="SHFE_INE",
                dataset_code="SHFE_DAILY_METALS_SETTLEMENTS",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="v1/reports/daily",
                response_format="JSON",
                data_envelope_path="report.data",
                default_params={"symbol": "sc"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=3600,
                notes="Asia-Pacific medium sour benchmark pricing.",
            ),

            # =========================================================================
            # 13. ARGUS MEDIA
            # =========================================================================
            RawEndpointSpec(
                code="ARGUS_DIRECT_CRUDE_PRICES",
                name="Argus Direct Physical Crude Assessments API",
                description="Physical spot assessments for WTI Midland, Mars, North Sea Dated, and ESPO crude.",
                provider_code="ARGUS_MEDIA",
                dataset_code="ARGUS_US_GULF_CRUDE_ASSESSMENTS",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="v1/prices/crude",
                response_format="JSON",
                data_envelope_path="assessments",
                default_params={"currency": "USD", "unit": "bbl"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=3600,
                notes="PRA physical methodology assessments.",
            ),

            # =========================================================================
            # 14. S&P GLOBAL PLATTS
            # =========================================================================
            RawEndpointSpec(
                code="PLATTS_COMMODITY_ASSESSMENTS",
                name="Platts Market Data Assessments API",
                description="Physical benchmark assessments for Dated Brent, Dubai/Oman, JKM LNG, and FOB Singapore Gasoil.",
                provider_code="SP_GLOBAL_PLATTS",
                dataset_code="PLATTS_NORTH_SEA_BRENT_ASSESSMENTS",
                protocol="REST_HTTP",
                http_method="GET",
                path_template="market-data/v2/assessments",
                response_format="JSON",
                data_envelope_path="results",
                default_params={"pageSize": 500},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=3600,
                notes="Primary global benchmark price reporting agency.",
            ),

            # =========================================================================
            # 15. FASTMARKETS
            # =========================================================================
            RawEndpointSpec(
                code="FASTMARKETS_BATTERY_METALS",
                name="Fastmarkets Battery Raw Materials & Minor Metals API",
                description="Spot price assessments for Lithium Hydroxide, Cobalt, and Nickel briquettes.",
                provider_code="FASTMARKETS",
                dataset_code=None,
                protocol="REST_HTTP",
                http_method="GET",
                path_template="v1/prices/metals",
                response_format="JSON",
                data_envelope_path="data",
                default_params={"sector": "battery_raw_materials"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=3600,
                notes="Energy transition metals pricing.",
            ),

            # =========================================================================
            # 16. OIL PRICE INFORMATION SERVICE (OPIS)
            # =========================================================================
            RawEndpointSpec(
                code="OPIS_REFINED_SPOT_PRICES",
                name="OPIS US Wholesale Rack & Spot Refined Products API",
                description="Wholesale rack prices and pipeline spot assessments for gasoline, diesel, and jet fuel across US PADDs.",
                provider_code="OPIS_ENERGY",
                dataset_code=None,
                protocol="REST_HTTP",
                http_method="GET",
                path_template="v1/spot/refined",
                response_format="JSON",
                data_envelope_path="spot_prices",
                default_params={"padd": "all"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=3600,
                notes="Downstream refined product distribution benchmarks.",
            ),

            # =========================================================================
            # 17. BLOOMBERG (B-PIPE / DATA LICENSE)
            # =========================================================================
            RawEndpointSpec(
                code="BLOOMBERG_BPIPE_REFERENCE",
                name="Bloomberg B-PIPE Market Data & Reference Service",
                description="Enterprise market data snapshot feed for global commodities, forward curves, and FX crosses.",
                provider_code="BLOOMBERG",
                dataset_code=None,
                protocol="REST_HTTP",
                http_method="POST",
                path_template="v1/bpipe/securities",
                response_format="JSON",
                data_envelope_path="response.securityData",
                default_params={},
                custom_headers={"Content-Type": "application/json"},
                cache_ttl_seconds=1800,
                notes="POST request with JSON array of Bloomberg tickers in request body.",
            ),

            # =========================================================================
            # 18. LSEG REFINITIV (DATASCOPE SELECT)
            # =========================================================================
            RawEndpointSpec(
                code="REFINITIV_DATASCOPE_RAW",
                name="LSEG Refinitiv DataScope Select Extraction API",
                description="Scheduled tick and end-of-day history extractions across global physical and derivative instruments.",
                provider_code="LSEG_REFINITIV",
                dataset_code=None,
                protocol="REST_HTTP",
                http_method="POST",
                path_template="RestApi/v1/Extractions/ExtractRaw",
                response_format="CSV",
                data_envelope_path="",
                default_params={},
                custom_headers={"Content-Type": "application/json", "Prefer": "respond-async"},
                cache_ttl_seconds=3600,
                notes="Asynchronous raw extraction with RIC identifier mapping.",
            ),

            # =========================================================================
            # 19. KPLER (AIS TANKER & SEABORNE CARGO)
            # =========================================================================
            RawEndpointSpec(
                code="KPLER_SEABORNE_FLOWS",
                name="Kpler Seaborne Crude & Clean Tanker Flows API",
                description="Vessel tracking, real-time seaborne trade flows, floating storage, and destination tracking.",
                provider_code="KPLER",
                dataset_code=None,
                protocol="REST_HTTP",
                http_method="GET",
                path_template="v1/flows/crude",
                response_format="JSON",
                data_envelope_path="flows",
                default_params={"granularity": "daily"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=7200,
                notes="Physical commodity satellite AIS analytics.",
            ),

            # =========================================================================
            # 20. INTERNAL QUANTITATIVE ENGINE
            # =========================================================================
            RawEndpointSpec(
                code="INTERNAL_FORWARD_CURVE_CALC",
                name="Internal Forward Curve & Crack Spread Engine",
                description="Deterministic synthetic curve interpolation, crack spread calculation, and carrying charge evaluation.",
                provider_code="INTERNAL_QUANT",
                dataset_code=None,
                protocol="REST_HTTP",
                http_method="GET",
                path_template="api/internal/curves/forward",
                response_format="JSON",
                data_envelope_path="data.curves",
                default_params={"model": "cubic_spline"},
                custom_headers={"Accept": "application/json"},
                cache_ttl_seconds=300,
                notes="Internal quant service generating canonical forward curves from prompt futures contracts.",
            ),
        ]
