import os
import subprocess
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from ai_config import project_environment
from shadow_learning import ObservationRecord

class ShadowHardening(unittest.TestCase):
    def test_process_dotenv_disable_cannot_be_bypassed_by_explicit_mapping(self):
        with patch.dict(os.environ,{'PYTHON_DOTENV_DISABLED':'1'}),patch('ai_config.dotenv_values') as loader:
            self.assertEqual(project_environment({'SAFE':'value'}),{'SAFE':'value'})
            loader.assert_not_called()

    def test_nested_observation_context_is_immutable(self):
        record=ObservationRecord('o','NPN','2026-01-01T00:00:00Z','1',{'nested':{'close':100}})
        with self.assertRaises(TypeError): record.market_data['nested']['close']=0

    def test_nonfinite_string_prices_are_rejected(self):
        for value in ('NaN','inf','-inf','0','-1'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                ObservationRecord('o','NPN','2026-01-01T00:00:00Z','1',{'close':value})

    def test_secret_runtime_and_browser_paths_are_ignored_without_opening_them(self):
        paths=['.env','.env.production','reliability.db','nested/state.sqlite3',
               '.ost-browser-profile/Cookies','.viewpoint-discovery/profile.json',
               'runtime/learned.json','downloaded-report.pdf']
        result=subprocess.run(['git','check-ignore','--no-index','--stdin'],input=('\n'.join(paths)+'\n').encode(),capture_output=True,check=False)
        self.assertEqual(set(result.stdout.decode().splitlines()),set(paths))

    def test_docker_excludes_secrets_and_runtime_artifacts(self):
        path=Path(__file__).parent/'.dockerignore'
        self.assertTrue(path.is_file())
        rules=set(path.read_text().splitlines())
        self.assertTrue({'.env','.env.*','**/*.db','**/*.sqlite*','.git','.venv','runtime','**/__pycache__'}.issubset(rules))

    def test_partial_legacy_reliability_schema_is_repaired_without_reset(self):
        from persistence.sqlite_repository import SQLiteRepository
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'old.db'; repo=SQLiteRepository(path)
            repo.save_observation(ObservationRecord('keep','NPN','2026-01-01T00:00:00Z','1',{}))
            # Isolated synthetic v4 predecessor, never the user's runtime DB.
            repo.store._connection.execute('DROP TABLE reliability_outcomes')
            repo.store._connection.execute('DELETE FROM schema_version WHERE version>=8')
            repo.store._connection.commit(); repo.close()
            repo=SQLiteRepository(path)
            try:
                self.assertEqual(repo.readiness()['state'],'AVAILABLE')
                self.assertIsNotNone(repo.get_observation('keep'))
            finally: repo.close()

    def test_shadow_decisions_do_not_accumulate_web_run_cache(self):
        from operational_intelligence import OperationalIntelligence
        from shadow_learning_pipeline import production_shadow_decision
        from test_shadow_acceptance import causal_observation
        service=OperationalIntelligence(); observation=causal_observation()
        production_shadow_decision(service,'NPN',horizon='1',decided_at=observation.observed_at,observation=observation)
        self.assertEqual(service.runs,{})
