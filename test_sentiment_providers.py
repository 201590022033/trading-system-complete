"""Offline OI3 routing contracts; responses here are synthetic, never live evidence."""
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import requests

from data_pipeline import NewsItem, SentimentLabel
from sentiment_analyzer import MacroSentimentScanner
from sentiment_providers import SentimentProviders, validated_result


RESULT = {'summary': 'Synthetic Sasol earnings impact', 'sentiment': 'bullish',
          'score': 0.6, 'assets': [{'name': 'SOL', 'direction': 1, 'strength': 0.6}]}


def response(data):
    return Mock(json=Mock(return_value=data))


class RoutingTests(unittest.TestCase):
    def router(self, env=None, local=True):
        transport = Mock()
        transport.get.return_value = response({'models': [{'name': 'llama3.2:3b'}] if local else []})
        return SentimentProviders(environ=env or {}, transport=transport)

    def test_local_structured_output_has_real_router_provenance(self):
        router = self.router()
        router.transport.post.return_value = response({'done': True, 'response': json.dumps(RESULT)})
        self.assertTrue(router.begin_scan(1))
        result = router.analyze('synthetic test prompt')
        self.assertEqual(result['_provider'], 'ollama_local')
        self.assertEqual(result['_model'], 'llama3.2:3b')
        args, kwargs = router.transport.post.call_args
        self.assertEqual(args[0], 'http://127.0.0.1:11434/api/generate')
        self.assertEqual(kwargs['headers'], {})
        self.assertEqual(kwargs['json']['format'], 'json')
        self.assertFalse(kwargs['allow_redirects'])
        self.assertIsNotNone(router.statuses()[0]['last_success'])

    def test_cloud_and_kimi_rotate_with_isolated_credentials(self):
        router = self.router({'OLLAMA_API_KEY': 'synthetic-cloud-secret',
                             'MOONSHOT_API_KEY': 'synthetic-kimi-secret'}, local=False)
        router.transport.post.side_effect = [
            response({'done': True, 'response': json.dumps(RESULT)}),
            response({'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(RESULT)}}]})]
        router.begin_scan(2)
        self.assertEqual(router.analyze('synthetic prompt')['_provider'], 'ollama_cloud')
        self.assertEqual(router.analyze('synthetic prompt')['_provider'], 'kimi')
        first, second = router.transport.post.call_args_list
        self.assertEqual(first.args[0], 'https://ollama.com/api/generate')
        self.assertEqual(second.args[0], 'https://api.moonshot.ai/v1/chat/completions')
        self.assertEqual(first.kwargs['headers']['Authorization'], 'Bearer synthetic-cloud-secret')
        self.assertEqual(second.kwargs['headers']['Authorization'], 'Bearer synthetic-kimi-secret')
        self.assertEqual(second.kwargs['json']['response_format'], {'type': 'json_object'})
        self.assertEqual(second.kwargs['json']['reasoning_effort'], 'low')
        for call in (first, second):
            self.assertFalse(call.kwargs['allow_redirects'])
            self.assertEqual(call.kwargs['timeout'], (5, 45))
        self.assertNotIn('synthetic-', repr(router.providers) + json.dumps(router.statuses()))

    def test_moonshot_precedence_and_kimi_aliases(self):
        preferred = self.router({'MOONSHOT_API_KEY': 'primary', 'KIMI_API_KEY': 'alias',
                                 'MOONSHOT_MODEL': 'primary-model', 'KIMI_MODEL': 'alias-model'})
        alias = self.router({'KIMI_API_KEY': 'alias', 'KIMI_MODEL': 'alias-model'})
        self.assertEqual((preferred.providers[2].key, preferred.providers[2].model), ('primary', 'primary-model'))
        self.assertEqual((alias.providers[2].key, alias.providers[2].model), ('alias', 'alias-model'))

    def test_missing_credentials_and_model_never_generate(self):
        router = self.router(local=False)
        self.assertFalse(router.begin_scan(8))
        self.assertIsNone(router.analyze('synthetic prompt'))
        router.transport.post.assert_not_called()
        self.assertEqual([p['state'] for p in router.statuses()],
                         ['MODEL_NOT_INSTALLED', 'NOT_CONFIGURED', 'NOT_CONFIGURED'])

    def test_auth_failure_falls_through_and_backs_off_without_secret_leak(self):
        router = self.router({'OLLAMA_API_KEY': 'synthetic-secret', 'KIMI_API_KEY': 'synthetic-other'}, local=False)
        error = requests.HTTPError('private response synthetic-secret', response=Mock(status_code=401))
        router.transport.post.side_effect = [error, response({'choices': [
            {'finish_reason': 'stop', 'message': {'content': json.dumps(RESULT)}}]})]
        with patch('sentiment_providers.monotonic', return_value=100):
            router.begin_scan(2)
            self.assertEqual(router.analyze('synthetic prompt')['_provider'], 'kimi')
            self.assertFalse(router._eligible(router.providers[1]))
        self.assertEqual(router.statuses()[1]['state'], 'HTTP_401')
        self.assertNotIn('synthetic-secret', json.dumps(router.statuses()))

    def test_invalid_and_truncated_output_cannot_claim_ai_success(self):
        invalid = [dict(RESULT, score=float('nan')), dict(RESULT, score=True),
                   dict(RESULT, assets=[{'name': 'SOL', 'direction': 2, 'strength': 1}])]
        for data in invalid:
            with self.assertRaises(ValueError): validated_result(json.dumps(data))
        for data in [{'done': False, 'response': json.dumps(RESULT)},
                     {'done': True, 'done_reason': 'length', 'response': json.dumps(RESULT)},
                     {'done': True, 'response': 'not JSON'}]:
            router = self.router()
            router.transport.post.return_value = response(data)
            router.begin_scan(1)
            self.assertIsNone(router.analyze('synthetic prompt'))
            self.assertEqual(router.statuses()[0]['state'], 'INVALID_RESPONSE')
            self.assertIsNone(router.statuses()[0]['last_success'])

    def test_budget_caps_network_attempts_and_local_probe_is_throttled(self):
        router = self.router()
        router.transport.post.return_value = response({'done': True, 'response': json.dumps(RESULT)})
        with patch('sentiment_providers.monotonic', return_value=100):
            router.begin_scan(999)
            for _ in range(10): router.analyze('synthetic prompt')
            self.assertEqual(router.transport.post.call_count, 8)
            router.begin_scan(0)
            router.transport.get.assert_called_once()
            self.assertIsNone(router.analyze('synthetic prompt'))

    def test_unreachable_service_keeps_scanner_keyword_provenance(self):
        router = self.router()
        router.transport.get.side_effect = requests.ConnectionError('synthetic-private-error')
        scanner = MacroSentimentScanner(providers=router, retain_items=True)
        item = NewsItem('SASOL', 'Synthetic Sasol profits rise', 'test fixture',
                        datetime(2026, 9, 6, tzinfo=timezone.utc), SentimentLabel.NEUTRAL, 0)
        scanner._fetch = Mock(return_value=[item])
        report = scanner.scan().to_dict()
        self.assertEqual(router.statuses()[0]['state'], 'UNREACHABLE')
        self.assertFalse(report['items'][0]['llm_used'])
        self.assertEqual(report['items'][0]['analysis_provider'], 'keywords')
        self.assertIn('SASOL', report['tickers'])
        router.transport.post.assert_not_called()
