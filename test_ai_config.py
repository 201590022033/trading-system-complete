import unittest
from unittest.mock import patch
from ai_config import project_environment
from sentiment_providers import SentimentProviders

class AIConfigTests(unittest.TestCase):
    def test_explicit_environment_overrides_file(self):
        with patch('ai_config.dotenv_values', return_value={'KIMI_API_KEY':'file-secret'}):
            self.assertEqual(project_environment({'KIMI_API_KEY':'explicit-secret'})['KIMI_API_KEY'], 'explicit-secret')

    def test_missing_credentials_are_not_configured(self):
        p = SentimentProviders(environ={'KIMI_API_KEY':'', 'MOONSHOT_API_KEY':'', 'OLLAMA_HOST':'http://127.0.0.1:1'})
        self.assertEqual(p.providers[2].state, 'NOT_CONFIGURED')

if __name__ == '__main__': unittest.main()
