"""Native PAPER acceptance against an explicitly supplied disposable localhost DB."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from uuid import uuid4
from urllib.parse import urlparse
from unittest.mock import patch
import subprocess
import sys
from application.opportunities.paper_config import PaperLoopConfig
from application.opportunities.paper_loop import PaperLoop
from persistence.postgres_repository import PostgresRepository
from test_paper_closed_loop import frozen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--account")
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.username != "paper_validator":
        raise ValueError("use only a disposable local paper_validator database")
    account_id = args.account or "native-paper-"+uuid4().hex
    config = replace(PaperLoopConfig.load("config/paper.example.json"),
                     account_id=account_id, universe=("TFMJ",))
    repo = PostgresRepository(args.url)
    try:
        if args.verify:
            state = repo.paper_account(config.account_id)
            assert len(state["broker"]["fills"]) == 2
            assert state["broker"]["positions"] == []
            print("PASS separate-process paper recovery")
            return
        repo.initialize()
        loop = PaperLoop(repo, config)
        loop.initialize()
        loop.cycle("j0", frozen(0))
        def competing():
            connection = PostgresRepository(args.url)
            try:
                return PaperLoop(connection, config).cycle("j1", frozen(1))
            finally:
                connection.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            a, b = list(pool.map(lambda _: competing(), range(2)))
        assert a == b and len(a["opened"]) == 1
        before = repo.paper_account(config.account_id)
        save = repo.save_paper_record
        def fail(rid, account, kind, at, payload):
            if kind == "ranking":
                raise RuntimeError("rollback injection")
            return save(rid, account, kind, at, payload)
        with patch.object(repo, "save_paper_record", side_effect=fail):
            try:
                loop.cycle("j2", frozen(2))
            except RuntimeError:
                pass
            else:
                raise AssertionError("injection did not fire")
        assert before == repo.paper_account(config.account_id)
        result = loop.cycle("j2", frozen(2))
        assert result["outcome_count"] == 1 and len(result["closed"]) == 1
        repo.initialize()
        assert len(repo.paper_account(config.account_id)["broker"]["fills"]) == 2
        print("PASS native migrations, concurrent exactly-once fill, rollback, outcome and remigration")
    finally:
        repo.close()
    subprocess.run([sys.executable, "-m", "scripts.validate_paper_postgres", "--url", args.url,
                    "--verify", "--account", account_id], check=True)


if __name__ == "__main__":
    main()
