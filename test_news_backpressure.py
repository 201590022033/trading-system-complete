"""Offline SENS burst, retention and slow-consumer regression checks."""
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from data_pipeline import NewsItem, SentimentLabel
from jse_adapter import SENSFeedFetcher
from sentiment_analyzer import MacroSentimentScanner
from test_dashboard_feeds import ManualPool
from dashboard_feeds import DashboardFeeds


class NewsBackpressureTests(unittest.TestCase):
    def scanner(self, retain=True):
        providers = Mock()
        providers.begin_scan.return_value = False
        scanner = MacroSentimentScanner(retain_items=retain, providers=providers)
        scanner.adapter.get_moneyweb_news = Mock(return_value=[])
        scanner._fetch_global_newsapi = Mock(return_value=[])
        return scanner

    @staticmethod
    def item(index):
        return NewsItem('JSE', f'SENS company announcement {index}', 'JSE SENS',
                        datetime.now(timezone.utc), SentimentLabel.NEUTRAL, 0)

    def test_sens_bursts_and_outage_keep_retention_bounded(self):
        scanner = self.scanner()
        for batch in range(15):
            # Deliberately misbehaving provider ignores its requested limit.
            scanner.adapter.get_sens_news = Mock(return_value=[
                self.item(batch * 1000 + i) for i in range(1000)])
            previews = []
            report = scanner.scan(sens_limit=15, on_progress=previews.append)
            self.assertLessEqual(len(report.items), 100)
            self.assertLessEqual(len(previews[0].items), 100)
            self.assertLessEqual(len(scanner._seen_headlines), 15)
        self.assertEqual(len(scanner._analyzed_cache), 100)
        before = scanner.scan(sens_limit=15).to_dict()['items']
        scanner.adapter.get_sens_news.return_value = []
        self.assertEqual(scanner.scan().to_dict()['items'], before)
        scanner.providers.analyze.assert_not_called()

    def test_non_retaining_seen_history_is_bounded_and_recent_duplicates_skipped(self):
        scanner = self.scanner(retain=False)
        for batch in range(12):
            scanner.adapter.get_sens_news = Mock(return_value=[
                self.item(batch * 100 + i) for i in range(100)])
            scanner.scan(sens_limit=100)
        self.assertEqual(len(scanner._seen_headlines), scanner.MAX_SEEN_HEADLINES)
        self.assertEqual(scanner.scan(sens_limit=100).items, [])

    def test_thousand_polls_queue_one_slow_news_refresh(self):
        feed = DashboardFeeds()
        feed._pool.shutdown()
        feed._pool = ManualPool()
        for _ in range(1000):
            self.assertTrue(feed.news()['refreshing'])
        self.assertEqual(len(feed._pool.jobs), 1)
        self.assertEqual(len(feed._entries), 1)

    def test_oversized_stream_is_stopped_and_response_closed(self):
        fetcher = SENSFeedFetcher()
        fetcher.MAX_RESPONSE_BYTES = 32
        response = Mock(status_code=200, encoding='utf-8')
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        consumed = []
        def chunks(**kwargs):
            for index in range(100):
                consumed.append(index)
                yield b'x' * 16
        response.iter_content.side_effect = chunks
        fetcher.session.get = Mock(return_value=response)
        self.assertEqual(fetcher.fetch_recent(), [])
        self.assertEqual(fetcher.last_status, 'RESPONSE_TOO_LARGE')
        self.assertEqual(len(consumed), 3)
        response.__exit__.assert_called_once()
        self.assertTrue(fetcher.session.get.call_args.kwargs['stream'])

    def test_sens_parser_limits_large_listing_and_zero_request(self):
        text = '<strong>COMPANY</strong>&nbsp;&#8211;&nbsp;Trading statement' * 10000
        self.assertEqual(len(SENSFeedFetcher._parse_moneyweb_sens(text, 15)), 15)
        self.assertEqual(len(SENSFeedFetcher._parse_moneyweb_sens(text, 10000)), 100)
        self.assertEqual(SENSFeedFetcher._parse_moneyweb_sens(text, 0), [])


if __name__ == '__main__':
    unittest.main()
