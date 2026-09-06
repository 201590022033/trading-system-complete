"""Policy-aware catalogue for specialist and community evidence sources."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional

from data_pipeline import NewsItem
from evidence import EvidenceRecord, normalize_news_item
from reliability_store import SourceDefinition, SourceRegistry


CATALOG_VERSION = "specialist-sources-v1"


@dataclass(frozen=True)
class SourcePolicy:
    source_id: str
    source_name: str
    source_class: str
    authority_tier: int
    access_mode: str
    status: str
    url: str
    enabled: bool = False
    minimum_poll_seconds: int = 300
    notes: str = ""


DEFAULT_SOURCE_POLICIES = (
    SourcePolicy("jse_market_data", "JSE Market Data", "market_data", 1,
                 "licensed_feed", "requires_license", "https://www.jse.co.za/market-data/data-agreements-policies",
                 notes="Use a licensed JSE product or registered distributor."),
    SourcePolicy("moneyweb_sens", "JSE SENS via Moneyweb", "authoritative_event", 1,
                 "public_html", "live_existing", "https://www.moneyweb.co.za/tools-and-data/moneyweb-sens/", True),
    SourcePolicy("moneyweb_rss", "Moneyweb", "financial_media", 3,
                 "public_rss", "live_existing", "https://www.moneyweb.co.za/feed/", True),
    SourcePolicy("businesslive", "Business Day / BusinessLIVE", "financial_media", 3,
                 "licensed_or_manual", "requires_permission", "https://www.businesslive.co.za/bd/markets/"),
    SourcePolicy("reuters_za", "Reuters South Africa", "financial_media", 3,
                 "licensed_api_or_manual", "requires_license", "https://www.reuters.com/world/africa/"),
    SourcePolicy("ig_za_analysis", "IG South Africa analysis", "financial_media", 3,
                 "public_manual", "no_stable_api_verified", "https://www.ig.com/za/news-and-trade-ideas"),
    SourcePolicy("standard_bank_commentary", "Standard Bank public commentary", "financial_media", 3,
                 "public_manual", "no_stable_feed_verified", "https://www.standardbank.co.za/"),
    SourcePolicy("efficient_group_commentary", "Efficient Group economic commentary", "financial_media", 3,
                 "public_manual", "no_stable_feed_verified",
                 "https://www.efgroup.co.za/news-and-media/economic-updates/",
                 notes="Public dated commentary verified 2026-09-06; automated ingestion permission/feed not verified."),
    SourcePolicy("tradingview_ideas", "TradingView JSE ideas", "community", 4,
                 "none", "excluded_non_display_terms", "https://www.tradingview.com/policies/"),
    SourcePolicy("mybroadband_forum", "MyBroadband finance forums", "community", 4,
                 "public_manual", "requires_permission", "https://mybroadband.co.za/forum/forums/business-finance-and-start-ups.225/"),
    SourcePolicy("reddit_personalfinanceza", "Reddit r/PersonalFinanceZA", "community", 4,
                 "oauth_api", "requires_approved_api", "https://redditinc.com/policies/data-api-terms"),
    SourcePolicy("reddit_jse", "Reddit r/JSE", "community", 4,
                 "oauth_api", "activity_not_verified", "https://redditinc.com/policies/data-api-terms"),
    SourcePolicy("x_jse", "X JSE sources", "community", 4,
                 "official_api", "requires_paid_or_approved_api", "https://developer.x.com/"),
    SourcePolicy("telegram_blackstone", "BlackStone Futures public Telegram", "community", 4,
                 "public_manual", "public_channel_verified_no_connector", "https://t.me/s/BSF_Official"),
    SourcePolicy("telegram_other", "Other public Telegram channels", "community", 4,
                 "official_api_with_permission", "not_configured", "https://core.telegram.org/api"),
    SourcePolicy("discord_public", "Permitted Discord communities", "community", 4,
                 "approved_bot_api", "requires_server_permission", "https://docs.discord.com/developers/events/gateway"),
)


class SpecialistSourceCatalog:
    """Independent source switches, poll intervals and provenance adaptation."""

    def __init__(self, policies: Iterable[SourcePolicy] = DEFAULT_SOURCE_POLICIES) -> None:
        self._policies: Dict[str, SourcePolicy] = {item.source_id: item for item in policies}
        self._last_polled: Dict[str, datetime] = {}

    def get(self, source_id: str) -> SourcePolicy:
        return self._policies[source_id]

    def configured(self):
        return tuple(self._policies.values())

    def with_enabled(self, source_id: str, enabled: bool) -> "SpecialistSourceCatalog":
        policies = [
            replace(item, enabled=enabled) if item.source_id == source_id else item
            for item in self._policies.values()
        ]
        if source_id not in self._policies:
            raise KeyError(source_id)
        return SpecialistSourceCatalog(policies)

    def poll_allowed(self, source_id: str, now: Optional[datetime] = None) -> bool:
        policy = self.get(source_id)
        if not policy.enabled:
            return False
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        previous = self._last_polled.get(source_id)
        return previous is None or (current - previous).total_seconds() >= policy.minimum_poll_seconds

    def mark_polled(self, source_id: str, now: Optional[datetime] = None) -> None:
        if not self.get(source_id).enabled:
            raise ValueError("Cannot poll a disabled source")
        value = now or datetime.now(timezone.utc)
        self._last_polled[source_id] = value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    def normalize(self, source_id: str, item: NewsItem, **mappings) -> EvidenceRecord:
        policy = self.get(source_id)
        return normalize_news_item(
            item,
            source_id=policy.source_id,
            source_class=policy.source_class,
            authority_tier=policy.authority_tier,
            parser_version=CATALOG_VERSION,
            metadata={
                "access_mode": policy.access_mode,
                "source_status": policy.status,
                "catalog_version": CATALOG_VERSION,
            },
            **mappings,
        )

    def reliability_registry(self) -> SourceRegistry:
        return SourceRegistry(SourceDefinition(
            item.source_id, item.source_name, item.source_class,
            item.authority_tier, item.enabled,
        ) for item in self._policies.values())


DEFAULT_SPECIALIST_SOURCES = SpecialistSourceCatalog()
