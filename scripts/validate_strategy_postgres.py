"""Explicit localhost-only native acceptance in a newly created disposable DB.

Reads DATABASE_URL privately from --local-config; never prints credentials.
No application/Railway database is migrated. Cleanup targets only the random
database created by this invocation, never the configured database.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
import re
import subprocess
import sys
from urllib.parse import urlparse, urlunparse
from uuid import uuid4
from unittest.mock import patch

import psycopg
from psycopg import sql
from domain.strategy import DEFAULT_STRATEGY_REGISTRY
from domain.strategy.attribution import freeze_profile, reference
from application.opportunities.paper_config import PaperLoopConfig
from application.opportunities.paper_loop import PaperLoop, paper_feature_outcomes
from persistence.postgres_repository import PostgresRepository
from test_paper_closed_loop import T
from test_strategy_attribution import attributed_frozen


def validate(url):
    profile = DEFAULT_STRATEGY_REGISTRY.resolve("jse_swing_3_5d", "1.0.1")
    config = replace(PaperLoopConfig.load("config/paper.example.json"), universe=("TFMJ",), holding_sessions=1)
    repo = PostgresRepository(url)
    try:
        repo.initialize()
        repo.save_strategy_definition(freeze_profile(profile))
        loop = PaperLoop(repo, config)
        loop.initialize()
        loop.cycle("j0", attributed_frozen(0))
        def competing(_):
            worker = PostgresRepository(url)
            try:
                return PaperLoop(worker, config).cycle("j1", attributed_frozen(1))
            finally:
                worker.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            a, b = list(pool.map(competing, range(2)))
        assert a == b and a["opened"]
        before = repo.paper_account(config.account_id)
        save = repo.save_paper_record
        def fail(rid, account, kind, at, payload):
            if kind == "ranking":
                raise RuntimeError("native rollback injection")
            return save(rid, account, kind, at, payload)
        with patch.object(repo, "save_paper_record", side_effect=fail):
            try:
                loop.cycle("j2", attributed_frozen(2))
            except RuntimeError:
                pass
            else:
                raise AssertionError("rollback injection missing")
        assert before == repo.paper_account(config.account_id)
        assert loop.cycle("j2", attributed_frozen(2))["closed"]
        assert len(paper_feature_outcomes(repo, config.account_id, T+timedelta(days=3),
                                         strategy_profile=profile.reference)) == 1
        assert paper_feature_outcomes(repo, config.account_id, T+timedelta(days=3)) == ()
        from application.opportunities.swing_technical import snapshot, record_and_label, OUTCOME_KIND
        from test_swing_technical import chart, clock
        first = chart(80)
        record_and_label(repo, config.account_id,
            {"TFMJ": snapshot(first, evaluated_at=clock(first), benchmark_chart=first)},
            {"TFMJ": first}, evaluated_at=clock(first))
        final = chart(86)
        summary = record_and_label(repo, config.account_id, {}, {"TFMJ": final}, evaluated_at=clock(final))
        assert all(summary["horizons"][str(h)]["sample_count"] == 1 for h in (3, 4, 5))
        assert len(repo.paper_records(config.account_id, OUTCOME_KIND, as_of=clock(final).isoformat())) == 3
        repo.initialize()
        assert repo._job_sql("SELECT COUNT(*) FROM strategy_record_refs", rows=True)[0][0] > 10
        # A new process gets its URL through stdin, never command-line output.
        child = """import sys
from persistence.postgres_repository import PostgresRepository
from domain.strategy.attribution import reference
repo=PostgresRepository(sys.stdin.read())
try:
 state=repo.paper_account('paper-example-zar')
 if state is None:
  row=repo._job_sql('SELECT account_id FROM paper_accounts',rows=True)[0]
  state=repo.paper_account(row[0])
 assert len(state['broker']['fills'])==2
 assert all(reference(row).strategy_profile_version=='1.0.1' for row in state['broker']['fills'])
finally: repo.close()
"""
        result = subprocess.run([sys.executable, "-c", child], input=url, text=True,
                                capture_output=True, timeout=15)
        if result.returncode:
            raise RuntimeError("separate-process recovery failed (output withheld)")
        print("PASS native PostgreSQL: migrations, exact lineage, concurrent exactly-once fill, rollback, recovery and distinct Swing 3/4/5-session labels")
    finally:
        repo.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-config", required=True)
    args = parser.parse_args()
    from dotenv import dotenv_values
    url = dotenv_values(args.local_config).get("DATABASE_URL", "")
    parsed = urlparse(url)
    if parsed.scheme not in {"postgresql", "postgres"} or parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError("explicit localhost PostgreSQL config required")
    name = "strategy_attribution_validator_" + uuid4().hex
    target_url = urlunparse(parsed._replace(path="/"+name))
    admin = psycopg.connect(url, autocommit=True, connect_timeout=3)
    created = False
    try:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        created = True
        validate(target_url)
    finally:
        if created:
            if not re.fullmatch(r"strategy_attribution_validator_[0-9a-f]{32}", name) or name == parsed.path.lstrip("/"):
                raise RuntimeError("unsafe disposable database cleanup target")
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
            print("Removed only this run's disposable validation database; application data unchanged.")
        admin.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Native validation failed:", type(exc).__name__, "(details withheld to protect connection configuration)")
        raise SystemExit(1)
