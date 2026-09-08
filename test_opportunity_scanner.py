"""Synthetic OI3 discovery checks; no external prices or model calls."""
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from data_pipeline import NewsItem, SentimentLabel
from opportunity_scanner import discover, DISCOVERY_UNIVERSE
from sentiment_analyzer import MacroSentimentScanner
from sentiment_providers import SentimentProviders
from test_sentiment_providers import RESULT, response
import json


class DiscoveryTests(unittest.TestCase):
    def test_ai_ticker_alias_reaches_existing_discovery_universe(self):
        transport = Mock()
        transport.get.return_value = response({'models': [{'name': 'llama3.2:3b'}]})
        transport.post.return_value = response({'done': True, 'response': json.dumps(RESULT)})
        providers = SentimentProviders(environ={'OLLAMA_LOCAL_MODEL': 'llama3.2:3b'}, transport=transport)
        scanner = MacroSentimentScanner(providers=providers, max_llm_items=1)
        scanner._fetch = Mock(return_value=[NewsItem(
            'SASOL', 'Synthetic earnings fixture', 'test fixture', datetime(2026, 9, 6, tzinfo=timezone.utc),
            SentimentLabel.NEUTRAL, 0)])
        news = scanner.scan().to_dict()
        self.assertTrue(news['items'][0]['llm_used'])
        self.assertEqual(news['items'][0]['analysis_provider'], 'ollama_local')
        self.assertIn('SASOL', news['tickers'])
        fetcher = Mock()
        fetcher.get_chart.return_value = {'bars': [{'close': 100 + i} for i in range(21)],
                                          'source_timestamp': '2026-09-04'}
        result = discover(news, {'SASOL': DISCOVERY_UNIVERSE['SASOL']}, fetcher)
        row = result['opportunities'][0]
        self.assertEqual(row['state'], 'NEWS_AND_TECHNICAL')
        self.assertEqual(row['news_mentions'], 1)
        self.assertGreater(row['news_score'], 0)
        self.assertFalse(result['execution_enabled'])

    def test_no_news_does_not_invent_ai_evidence_or_expand_universe(self):
        fetcher = Mock()
        fetcher.get_chart.return_value = {'bars': [{'close': 100 + i} for i in range(21)]}
        result = discover({'tickers': {'INVENTED': {'score': 1, 'mentions': 5}}},
                          {'BTI': DISCOVERY_UNIVERSE['BTI']}, fetcher)
        self.assertEqual(result['scanned'], 1)
        row = result['opportunities'][0]
        self.assertEqual(row['symbol'], 'BTI')
        self.assertEqual(row['state'], 'TECHNICAL_ONLY')
        self.assertEqual(row['news_mentions'], 0)
        self.assertFalse(result['execution_enabled'])

    def test_missing_or_short_history_never_produces_an_opportunity(self):
        for value in [RuntimeError('synthetic-secret'), {'bars': [{'close': 100}]}]:
            fetcher = Mock()
            if isinstance(value, Exception): fetcher.get_chart.side_effect = value
            else: fetcher.get_chart.return_value = value
            result = discover({}, {'SASOL': DISCOVERY_UNIVERSE['SASOL']}, fetcher)
            self.assertEqual(result['opportunities'], [])
            self.assertEqual(len(result['unavailable']), 1)
            self.assertNotIn('synthetic-secret', json.dumps(result))
            self.assertFalse(result['execution_enabled'])
