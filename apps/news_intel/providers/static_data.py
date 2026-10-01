"""
Deterministic static seed dataset and StaticNewsProvider for news headlines and macroeconomic catalysts.
Enables 100% offline, reproducible testing and point-in-time backfilling.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from .base import (
    BaseNewsProvider,
    RawCatalystEventDTO,
    RawNewsArticleDTO,
    RawNewsCommodityTagDTO,
)


STATIC_CATALYST_EVENTS: List[RawCatalystEventDTO] = [
    RawCatalystEventDTO(
        name="OPEC+ Joint Ministerial Monitoring Committee (JMMC) Meeting",
        event_type="POLICY_OPEC",
        impact_level="HIGH",
        scheduled_datetime_utc=datetime(2026, 10, 2, 11, 0, tzinfo=timezone.utc),
        source_agency="OPEC Secretariat",
        status="SCHEDULED",
        period_covered="Q4 2026 Production Strategy",
        primary_commodity_code="CL",
        affected_commodity_codes=["CL", "BRENT", "RB", "HO", "GO"],
        consensus_expectation=Decimal("0.0000"),
        actual_value=None,
        prior_value=Decimal("-2.2000"),
        unit_symbol="MMBBL",
        notes="High-profile policy review assessing adherence to voluntary 2.2M bpd quota cuts and Asian demand recovery.",
    ),
    RawCatalystEventDTO(
        name="USDA WASDE - World Agricultural Supply and Demand Estimates",
        event_type="GOVERNMENT_WASDE",
        impact_level="HIGH",
        scheduled_datetime_utc=datetime(2026, 10, 10, 16, 0, tzinfo=timezone.utc),
        source_agency="USDA World Agricultural Outlook Board",
        status="SCHEDULED",
        period_covered="October 2026 Crop Balance Sheet",
        primary_commodity_code="CORN",
        affected_commodity_codes=["CORN", "SOYBEANS", "WHEAT_SRW", "SOYOIL"],
        consensus_expectation=Decimal("181.5000"),
        actual_value=None,
        prior_value=Decimal("183.1000"),
        unit_symbol="BU",
        notes="Benchmark global grain balance sheets, US domestic corn & soybean yields, and ending stocks projections.",
    ),
    RawCatalystEventDTO(
        name="Federal Reserve FOMC Interest Rate Decision & Monetary Statement",
        event_type="MACRO_CENTRAL_BANK",
        impact_level="HIGH",
        scheduled_datetime_utc=datetime(2026, 10, 28, 18, 0, tzinfo=timezone.utc),
        source_agency="Federal Reserve System",
        status="SCHEDULED",
        period_covered="October 2026 Policy Meeting",
        primary_commodity_code="GOLD",
        affected_commodity_codes=["GOLD", "SILVER", "COPPER", "CL"],
        consensus_expectation=Decimal("4.5000"),
        actual_value=None,
        prior_value=Decimal("4.7500"),
        unit_symbol="PERCENT",
        notes="Federal Open Market Committee policy announcement and updated dot plot projections directly driving real yields and USD.",
    ),
    RawCatalystEventDTO(
        name="EIA Weekly Petroleum Status Report (Crude Oil Inventories)",
        event_type="INVENTORY_EIA",
        impact_level="HIGH",
        scheduled_datetime_utc=datetime(2026, 9, 30, 14, 30, tzinfo=timezone.utc),
        source_agency="Energy Information Administration (EIA)",
        status="OCCURRED",
        period_covered="Week Ended Sep 25, 2026",
        primary_commodity_code="CL",
        affected_commodity_codes=["CL", "BRENT", "RB", "HO"],
        consensus_expectation=Decimal("-1.2000"),
        actual_value=Decimal("-4.5000"),
        prior_value=Decimal("-1.6000"),
        unit_symbol="MMBBL",
        surprise_magnitude=Decimal("-3.3000"),
        surprise_direction="BULLISH_SURPRISE",
        notes="Massive 4.5M barrel draw in US commercial crude oil stockpiles exceeding consensus expectations.",
    ),
    RawCatalystEventDTO(
        name="EIA Weekly Natural Gas Underground Storage Report",
        event_type="INVENTORY_EIA",
        impact_level="HIGH",
        scheduled_datetime_utc=datetime(2026, 9, 29, 14, 30, tzinfo=timezone.utc),
        source_agency="Energy Information Administration (EIA)",
        status="OCCURRED",
        period_covered="Week Ended Sep 24, 2026",
        primary_commodity_code="NG",
        affected_commodity_codes=["NG", "HO"],
        consensus_expectation=Decimal("62.0000"),
        actual_value=Decimal("78.0000"),
        prior_value=Decimal("58.0000"),
        unit_symbol="BCF",
        surprise_magnitude=Decimal("16.0000"),
        surprise_direction="BEARISH_SURPRISE",
        notes="Net injection of 78 Bcf exceeded survey consensus of 62 Bcf, dampening early autumn spot Henry Hub cash basis.",
    ),
    RawCatalystEventDTO(
        name="CFTC Commitments of Traders (COT) Weekly Speculative Positions",
        event_type="REGULATORY_CFTC",
        impact_level="MEDIUM",
        scheduled_datetime_utc=datetime(2026, 10, 2, 19, 30, tzinfo=timezone.utc),
        source_agency="Commodity Futures Trading Commission (CFTC)",
        status="SCHEDULED",
        period_covered="As of Sep 29, 2026",
        primary_commodity_code="CL",
        affected_commodity_codes=["CL", "GOLD", "CORN", "SOYBEANS"],
        consensus_expectation=None,
        actual_value=None,
        prior_value=None,
        unit_symbol=None,
        notes="Weekly disaggregated trader positioning showing money manager net longs and commercial producer short hedges.",
    ),
    RawCatalystEventDTO(
        name="Brazil UNICA Center-South Bi-Weekly Sugarcane Crush & Ethanol Ratio",
        event_type="WEATHER_ANOMALY",
        impact_level="MEDIUM",
        scheduled_datetime_utc=datetime(2026, 10, 12, 13, 0, tzinfo=timezone.utc),
        source_agency="UNICA Brazilian Sugarcane Industry Association",
        status="SCHEDULED",
        period_covered="Second Half September 2026",
        primary_commodity_code="SUGAR_11",
        affected_commodity_codes=["SUGAR_11", "CL"],
        consensus_expectation=Decimal("41.5000"),
        actual_value=None,
        prior_value=Decimal("43.2000"),
        unit_symbol="MT",
        notes="Bi-weekly cane crushing pace, sugar-to-ethanol diversion mix, and hydrous ethanol pricing relative to gasoline.",
    ),
    RawCatalystEventDTO(
        name="USDA NASS Weekly Crop Progress and Condition Ratings",
        event_type="WEATHER_ANOMALY",
        impact_level="MEDIUM",
        scheduled_datetime_utc=datetime(2026, 10, 5, 20, 0, tzinfo=timezone.utc),
        source_agency="USDA National Agricultural Statistics Service",
        status="SCHEDULED",
        period_covered="Week Ended Oct 4, 2026",
        primary_commodity_code="SOYBEANS",
        affected_commodity_codes=["SOYBEANS", "CORN", "WHEAT_SRW"],
        consensus_expectation=Decimal("65.0000"),
        actual_value=None,
        prior_value=Decimal("64.0000"),
        unit_symbol="PERCENT",
        notes="US Corn and Soybean Belt harvest pace and Good-to-Excellent condition percentages across top 18 agricultural states.",
    ),
]


STATIC_NEWS_ARTICLES: List[RawNewsArticleDTO] = [
    RawNewsArticleDTO(
        title="OPEC+ Extends Voluntary Output Cuts of 2.2M Barrels per Day Through Q4 to Defend Crude Prices",
        summary="OPEC+ energy ministers confirmed the extension of voluntary production curbs into fourth quarter, tightening physical Atlantic Basin supplies.",
        published_at_utc=datetime(2026, 9, 30, 8, 30, tzinfo=timezone.utc),
        source_name="Reuters Energy Wire",
        source_url="https://www.reuters.com/business/energy/opec-output-cuts-extended-2026-09-30/",
        author="Amena Bakr & Alex Lawler",
        overall_sentiment_score=Decimal("0.780"),
        overall_sentiment_label="STRONG_BULLISH",
        confidence_score=Decimal("0.920"),
        is_breaking=True,
        primary_commodity_code="CL",
        tags=[
            RawNewsCommodityTagDTO(
                commodity_code="CL",
                relevance_score=Decimal("1.000"),
                is_primary=True,
                commodity_sentiment="STRONG_BULLISH",
                commodity_sentiment_score=Decimal("0.820"),
                matched_keywords=["opec", "crude", "output cuts", "production curbs"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="BRENT",
                relevance_score=Decimal("0.950"),
                is_primary=False,
                commodity_sentiment="STRONG_BULLISH",
                commodity_sentiment_score=Decimal("0.800"),
                matched_keywords=["opec", "crude", "atlantic basin", "brent"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="HO",
                relevance_score=Decimal("0.700"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.450"),
                matched_keywords=["distillates", "feedstock costs", "heating oil"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="RB",
                relevance_score=Decimal("0.650"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.420"),
                matched_keywords=["gasoline", "crack spread", "refinery margins"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="SUGAR_11",
                relevance_score=Decimal("0.400"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.300"),
                matched_keywords=["ethanol parity", "biofuel substitution"],
            ),
        ],
        catalyst_event_name="OPEC+ Joint Ministerial Monitoring Committee (JMMC) Meeting",
    ),
    RawNewsArticleDTO(
        title="USDA WASDE Slashes US Corn Yield Estimate Amid Late-Summer Heat; Soybeans and Wheat Rally",
        summary="The Department of Agriculture trimmed domestic corn yields and ending stocks projections, providing strong bullish tailwinds across Chicago agricultural futures.",
        published_at_utc=datetime(2026, 9, 29, 16, 15, tzinfo=timezone.utc),
        source_name="Bloomberg Agriculture",
        source_url="https://www.bloomberg.com/news/articles/2026-09-29/usda-wasde-cuts-corn-yield",
        author="Michael Hirtzer",
        overall_sentiment_score=Decimal("0.740"),
        overall_sentiment_label="STRONG_BULLISH",
        confidence_score=Decimal("0.890"),
        is_breaking=False,
        primary_commodity_code="CORN",
        tags=[
            RawNewsCommodityTagDTO(
                commodity_code="CORN",
                relevance_score=Decimal("1.000"),
                is_primary=True,
                commodity_sentiment="STRONG_BULLISH",
                commodity_sentiment_score=Decimal("0.860"),
                matched_keywords=["usda", "wasde", "corn", "yield", "ending stocks"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="SOYBEANS",
                relevance_score=Decimal("0.750"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.550"),
                matched_keywords=["soybeans", "midwest heat", "chicago futures"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="WHEAT_SRW",
                relevance_score=Decimal("0.450"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.320"),
                matched_keywords=["wheat", "feed substitution", "grain complex"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="SOYOIL",
                relevance_score=Decimal("0.400"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.300"),
                matched_keywords=["vegetable oil", "crush margin"],
            ),
        ],
        catalyst_event_name="USDA WASDE - World Agricultural Supply and Demand Estimates",
    ),
    RawNewsArticleDTO(
        title="Federal Reserve Delivers 25 Bps Rate Cut as Core Inflation Cools; Bullion and Base Metals Advance",
        summary="Lower real Treasury yields and dollar weakness prompted broad-based institutional buying across physical gold, silver, and copper contracts.",
        published_at_utc=datetime(2026, 9, 28, 18, 45, tzinfo=timezone.utc),
        source_name="Financial Times Markets",
        source_url="https://www.ft.com/content/fed-rate-cut-gold-metals-2026-09-28",
        author="Colby Smith",
        overall_sentiment_score=Decimal("0.720"),
        overall_sentiment_label="STRONG_BULLISH",
        confidence_score=Decimal("0.910"),
        is_breaking=True,
        primary_commodity_code="GOLD",
        tags=[
            RawNewsCommodityTagDTO(
                commodity_code="GOLD",
                relevance_score=Decimal("1.000"),
                is_primary=True,
                commodity_sentiment="STRONG_BULLISH",
                commodity_sentiment_score=Decimal("0.840"),
                matched_keywords=["federal reserve", "rate cut", "bullion", "real yields", "gold"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="SILVER",
                relevance_score=Decimal("0.900"),
                is_primary=False,
                commodity_sentiment="STRONG_BULLISH",
                commodity_sentiment_score=Decimal("0.760"),
                matched_keywords=["silver", "dollar weakness", "precious metals"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="COPPER",
                relevance_score=Decimal("0.600"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.420"),
                matched_keywords=["base metals", "copper", "monetary easing"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="CL",
                relevance_score=Decimal("0.500"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.350"),
                matched_keywords=["crude oil", "dollar depreciation"],
            ),
        ],
        catalyst_event_name="Federal Reserve FOMC Interest Rate Decision & Monetary Statement",
    ),
    RawNewsArticleDTO(
        title="EIA Data Confirms Heavy 4.5M Barrel Drawdown in US Commercial Crude Inventories",
        summary="Strong refinery runs at 93.5% capacity and robust export loadings drove commercial crude stockpiles down more than triple consensus expectations.",
        published_at_utc=datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc),
        source_name="Argus Media Petroleum",
        source_url="https://www.argusmedia.com/en/news/eia-crude-stocks-draw-sept-2026",
        author="Amanda Hilow",
        overall_sentiment_score=Decimal("0.650"),
        overall_sentiment_label="STRONG_BULLISH",
        confidence_score=Decimal("0.940"),
        is_breaking=False,
        primary_commodity_code="CL",
        tags=[
            RawNewsCommodityTagDTO(
                commodity_code="CL",
                relevance_score=Decimal("1.000"),
                is_primary=True,
                commodity_sentiment="STRONG_BULLISH",
                commodity_sentiment_score=Decimal("0.750"),
                matched_keywords=["eia", "crude draw", "inventories", "commercial stockpiles"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="BRENT",
                relevance_score=Decimal("0.800"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.600"),
                matched_keywords=["global balance", "export arbitrage", "brent"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="HO",
                relevance_score=Decimal("0.600"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.450"),
                matched_keywords=["refinery utilization", "distillates"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="RB",
                relevance_score=Decimal("0.550"),
                is_primary=False,
                commodity_sentiment="NEUTRAL",
                commodity_sentiment_score=Decimal("-0.050"),
                matched_keywords=["gasoline stocks", "finished motor gasoline build"],
            ),
        ],
        catalyst_event_name="EIA Weekly Petroleum Status Report (Crude Oil Inventories)",
    ),
    RawNewsArticleDTO(
        title="European Underground Gas Storage Crosses 94% Full; Autumn Warmth Dampens Heating Demand",
        summary="Abundant LNG tanker arrivals and mild October forecasts pushed European storage near capacity limits, weighing on prompt month gas and spark spreads.",
        published_at_utc=datetime(2026, 9, 29, 11, 20, tzinfo=timezone.utc),
        source_name="ICIS Heren European Energy",
        source_url="https://www.icis.com/explore/resources/news/european-gas-storage-94-percent/",
        author="Muriel Boselli",
        overall_sentiment_score=Decimal("-0.450"),
        overall_sentiment_label="MODERATE_BEARISH",
        confidence_score=Decimal("0.880"),
        is_breaking=False,
        primary_commodity_code="NG",
        tags=[
            RawNewsCommodityTagDTO(
                commodity_code="NG",
                relevance_score=Decimal("1.000"),
                is_primary=True,
                commodity_sentiment="MODERATE_BEARISH",
                commodity_sentiment_score=Decimal("-0.520"),
                matched_keywords=["gas storage", "natural gas", "lng arrivals", "mild weather"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="HO",
                relevance_score=Decimal("0.550"),
                is_primary=False,
                commodity_sentiment="MODERATE_BEARISH",
                commodity_sentiment_score=Decimal("-0.280"),
                matched_keywords=["heating oil", "fuel switching", "heating degree days"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="EUA_CARBON",
                relevance_score=Decimal("0.500"),
                is_primary=False,
                commodity_sentiment="MODERATE_BEARISH",
                commodity_sentiment_score=Decimal("-0.300"),
                matched_keywords=["power generation", "carbon emissions", "coal switching"],
            ),
        ],
    ),
    RawNewsArticleDTO(
        title="Brazil UNICA Reports Heavy Sugar Allocation by Center-South Mills as Hydrous Ethanol Discounts Linger",
        summary="Cane processors maximized crystallization ratios to 51.2% in response to attractive sugar futures, dampening domestic biofuel yields while swelling world sugar supplies.",
        published_at_utc=datetime(2026, 9, 27, 14, 0, tzinfo=timezone.utc),
        source_name="S&P Global Commodity Insights",
        source_url="https://www.spglobal.com/commodityinsights/en/market-insights/latest-news/agriculture/brazil-unica-sugar-mix",
        author="Beatriz Pupo",
        overall_sentiment_score=Decimal("-0.680"),
        overall_sentiment_label="STRONG_BEARISH",
        confidence_score=Decimal("0.870"),
        is_breaking=False,
        primary_commodity_code="SUGAR_11",
        tags=[
            RawNewsCommodityTagDTO(
                commodity_code="SUGAR_11",
                relevance_score=Decimal("1.000"),
                is_primary=True,
                commodity_sentiment="STRONG_BEARISH",
                commodity_sentiment_score=Decimal("-0.740"),
                matched_keywords=["unica", "brazil sugar", "cane crush", "sugar mix"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="CL",
                relevance_score=Decimal("0.350"),
                is_primary=False,
                commodity_sentiment="NEUTRAL",
                commodity_sentiment_score=Decimal("0.020"),
                matched_keywords=["ethanol parity", "gasoline blend"],
            ),
        ],
        catalyst_event_name="Brazil UNICA Center-South Bi-Weekly Sugarcane Crush & Ethanol Ratio",
    ),
    RawNewsArticleDTO(
        title="Red Sea Shipping Disruptions Force Tanker Rerouting Around Cape of Good Hope, Spiking Distillate Freight",
        summary="Maritime security tensions have driven maritime insurance rates up 40%, boosting landed arbitrage prices for Middle East and Asian middle distillates into Europe.",
        published_at_utc=datetime(2026, 9, 30, 7, 0, tzinfo=timezone.utc),
        source_name="Lloyd's List Maritime Intelligence",
        source_url="https://www.lloydslist.com/markets/tankers/red-sea-freight-surge-2026",
        author="Michelle Wiese Bockmann",
        overall_sentiment_score=Decimal("0.620"),
        overall_sentiment_label="STRONG_BULLISH",
        confidence_score=Decimal("0.900"),
        is_breaking=True,
        primary_commodity_code="BRENT",
        tags=[
            RawNewsCommodityTagDTO(
                commodity_code="BRENT",
                relevance_score=Decimal("1.000"),
                is_primary=True,
                commodity_sentiment="STRONG_BULLISH",
                commodity_sentiment_score=Decimal("0.720"),
                matched_keywords=["red sea", "tanker rerouting", "freight rates", "crude supply risk"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="HO",
                relevance_score=Decimal("0.850"),
                is_primary=False,
                commodity_sentiment="STRONG_BULLISH",
                commodity_sentiment_score=Decimal("0.680"),
                matched_keywords=["heating oil", "diesel", "middle distillates", "transit time"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="CL",
                relevance_score=Decimal("0.700"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.500"),
                matched_keywords=["tanker freight", "crude arbitrage"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="NG",
                relevance_score=Decimal("0.550"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.400"),
                matched_keywords=["qatar lng", "cape rerouting", "lng freight"],
            ),
        ],
    ),
    RawNewsArticleDTO(
        title="China Announces Target Infrastructure and Industrial Stimulus; Base Metals and Iron Ore Futures Rally",
        summary="The National Development and Reform Commission introduced targeted credit lines for state grid upgrades and clean energy manufacturing, sparking heavy buying in metals.",
        published_at_utc=datetime(2026, 9, 29, 6, 30, tzinfo=timezone.utc),
        source_name="Caixin Global Commodities",
        source_url="https://www.caixinglobal.com/2026-09-29/china-infrastructure-stimulus-metals",
        author="Wang Xiaomeng",
        overall_sentiment_score=Decimal("0.760"),
        overall_sentiment_label="STRONG_BULLISH",
        confidence_score=Decimal("0.910"),
        is_breaking=False,
        primary_commodity_code="COPPER",
        tags=[
            RawNewsCommodityTagDTO(
                commodity_code="COPPER",
                relevance_score=Decimal("1.000"),
                is_primary=True,
                commodity_sentiment="STRONG_BULLISH",
                commodity_sentiment_score=Decimal("0.840"),
                matched_keywords=["china stimulus", "state grid", "copper demand", "industrial metal"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="IRON_ORE",
                relevance_score=Decimal("0.900"),
                is_primary=False,
                commodity_sentiment="STRONG_BULLISH",
                commodity_sentiment_score=Decimal("0.800"),
                matched_keywords=["steel mills", "iron ore", "infrastructure"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="ALUMINUM",
                relevance_score=Decimal("0.800"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.620"),
                matched_keywords=["aluminum", "clean energy manufacturing"],
            ),
            RawNewsCommodityTagDTO(
                commodity_code="CL",
                relevance_score=Decimal("0.450"),
                is_primary=False,
                commodity_sentiment="MODERATE_BULLISH",
                commodity_sentiment_score=Decimal("0.350"),
                matched_keywords=["industrial growth", "energy consumption"],
            ),
        ],
    ),
]


class StaticNewsProvider(BaseNewsProvider):
    """
    Deterministic news and macroeconomic catalyst provider using static benchmark data.
    Ensures zero external network dependencies and 100% test reproducibility.
    """

    def __init__(self, catalyst_events: Optional[List[RawCatalystEventDTO]] = None, articles: Optional[List[RawNewsArticleDTO]] = None):
        self._catalyst_events = catalyst_events or STATIC_CATALYST_EVENTS
        self._articles = articles or STATIC_NEWS_ARTICLES

    def get_catalyst_events(
        self,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        commodity_code: Optional[str] = None,
    ) -> List[RawCatalystEventDTO]:
        events = self._catalyst_events
        if start_datetime:
            events = [e for e in events if e.scheduled_datetime_utc >= start_datetime]
        if end_datetime:
            events = [e for e in events if e.scheduled_datetime_utc <= end_datetime]
        if commodity_code:
            code_upper = commodity_code.upper()
            events = [
                e for e in events
                if (e.primary_commodity_code and e.primary_commodity_code.upper() == code_upper)
                or any(c.upper() == code_upper for c in e.affected_commodity_codes)
            ]
        return sorted(events, key=lambda e: e.scheduled_datetime_utc, reverse=True)

    def get_news_articles(
        self,
        limit: int = 50,
        commodity_code: Optional[str] = None,
    ) -> List[RawNewsArticleDTO]:
        articles = self._articles
        if commodity_code:
            code_upper = commodity_code.upper()
            filtered = []
            for art in articles:
                if (art.primary_commodity_code and art.primary_commodity_code.upper() == code_upper) or any(
                    t.commodity_code.upper() == code_upper for t in art.tags
                ):
                    filtered.append(art)
            articles = filtered
        articles = sorted(articles, key=lambda a: a.published_at_utc, reverse=True)
        return articles[:limit]
