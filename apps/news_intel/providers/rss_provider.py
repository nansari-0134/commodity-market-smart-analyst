"""
RSS / Atom Feed News Provider for live governmental and agency market news ingestion.
Includes graceful fallback to StaticNewsProvider when offline or during air-gapped test runs.
"""

import logging
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from .base import (
    BaseNewsProvider,
    RawCatalystEventDTO,
    RawNewsArticleDTO,
    RawNewsCommodityTagDTO,
)
from .static_data import StaticNewsProvider

logger = logging.getLogger(__name__)

DEFAULT_RSS_FEEDS = [
    {
        "name": "EIA Petroleum Highlights",
        "url": "https://www.eia.gov/petroleum/supply/weekly/rss/petroleum.xml",
        "primary_commodity": "CL",
    },
    {
        "name": "USDA News Releases",
        "url": "https://www.usda.gov/rss/latest-releases.xml",
        "primary_commodity": "CORN",
    },
]


class RSSNewsProvider(BaseNewsProvider):
    """
    Live RSS / XML provider capable of streaming macroeconomic releases from government agencies.
    Gracefully falls back to static benchmark seeds if network is unavailable or times out.
    """

    def __init__(self, feeds: Optional[List[dict]] = None, timeout_seconds: int = 4):
        self._feeds = feeds or DEFAULT_RSS_FEEDS
        self._timeout_seconds = timeout_seconds
        self._fallback_provider = StaticNewsProvider()

    def get_catalyst_events(
        self,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        commodity_code: Optional[str] = None,
    ) -> List[RawCatalystEventDTO]:
        """Catalyst events are benchmarked against official schedules provided by StaticNewsProvider."""
        return self._fallback_provider.get_catalyst_events(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            commodity_code=commodity_code,
        )

    def get_news_articles(
        self,
        limit: int = 50,
        commodity_code: Optional[str] = None,
    ) -> List[RawNewsArticleDTO]:
        """Fetch RSS feeds and parse XML items into RawNewsArticleDTO instances."""
        parsed_articles: List[RawNewsArticleDTO] = []

        for feed_config in self._feeds:
            feed_url = feed_config.get("url")
            source_name = feed_config.get("name", "RSS Feed")
            default_commodity = feed_config.get("primary_commodity", "CL")

            try:
                req = urllib.request.Request(
                    feed_url,
                    headers={"User-Agent": "CommoditySmartAnalyst/1.0 (+https://github.com/nansari-0134/commodity-market-smart-analyst)"},
                )
                with urllib.request.urlopen(req, timeout=self._timeout_seconds) as response:
                    content = response.read()
                    root = ET.fromstring(content)

                    # Support both standard RSS 2.0 and Atom feeds
                    channel = root.find("channel")
                    items = channel.findall("item") if channel is not None else root.findall("{http://www.w3.org/2005/Atom}entry")

                    for item in items[:15]:
                        title = item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "Untitled"
                        summary = item.findtext("description") or item.findtext("{http://www.w3.org/2005/Atom}summary") or title
                        link = item.findtext("link") or ""

                        article_dto = RawNewsArticleDTO(
                            title=title.strip(),
                            summary=summary.strip()[:600],
                            published_at_utc=datetime.now(timezone.utc),
                            source_name=source_name,
                            source_url=link.strip(),
                            primary_commodity_code=default_commodity,
                            tags=[
                                RawNewsCommodityTagDTO(
                                    commodity_code=default_commodity,
                                    relevance_score=Decimal("1.000"),
                                    is_primary=True,
                                    commodity_sentiment="NEUTRAL",
                                    commodity_sentiment_score=Decimal("0.000"),
                                    matched_keywords=[default_commodity.lower()],
                                )
                            ],
                        )
                        parsed_articles.append(article_dto)
            except Exception as exc:
                logger.info("RSS feed fetch failed for %s (%s): %s. Falling back to static data.", feed_url, source_name, exc)

        if not parsed_articles:
            # Fallback to static seeds for offline reliability
            return self._fallback_provider.get_news_articles(limit=limit, commodity_code=commodity_code)

        if commodity_code:
            code_upper = commodity_code.upper()
            parsed_articles = [
                a for a in parsed_articles
                if (a.primary_commodity_code and a.primary_commodity_code.upper() == code_upper)
                or any(t.commodity_code.upper() == code_upper for t in a.tags)
            ]

        return parsed_articles[:limit]
