"""Guarded local preflight for the one-web/one-worker Railway deployment.

This command is intentionally local-only.  It does not invoke Railway, run
migrations, print connection strings, or contact a broker/provider.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass


REQUIRED = ("DATABASE_URL", "APP_MODE", "PORT", "COMMIT_SHA", "WORKER_ID")


@dataclass(frozen=True)
class PreflightResult:
    checks: tuple[str, ...]


def _git_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and not result.stdout.strip()


def validate_environment(environ: dict[str, str] | None = None) -> PreflightResult:
    env = os.environ if environ is None else environ
    missing = [name for name in REQUIRED if not env.get(name, "").strip()]
    if missing:
        raise RuntimeError("missing required deployment variables: " + ", ".join(missing))
    mode = env["APP_MODE"].strip().upper()
    if mode == "LIVE":
        raise RuntimeError("LIVE mode is refused by the shadow-learning preflight")
    database_url = env["DATABASE_URL"].strip().lower()
    if not database_url.startswith(("postgresql://", "postgres://")):
        raise RuntimeError("DATABASE_URL must be a PostgreSQL URL")
    try:
        port = int(env["PORT"])
    except ValueError as exc:
        raise RuntimeError("PORT must be numeric") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError("PORT is outside the valid range")
    return PreflightResult(("configuration", "shadow-only mode", "postgresql", "port"))


def check_database() -> None:
    """Check native PostgreSQL readiness without running migrations."""
    from persistence.repository import get_storage_repository

    repository = get_storage_repository(database_url=os.environ["DATABASE_URL"])
    try:
        connection = repository._require_connection()  # narrow preflight probe
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone()[0] != 1:
                raise RuntimeError("PostgreSQL readiness query failed")
    finally:
        repository.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-database", action="store_true",
                        help="perform a read-only native PostgreSQL readiness query")
    args = parser.parse_args(argv)
    try:
        result = validate_environment()
        if not _git_clean():
            raise RuntimeError("working tree must be clean before deployment")
        if args.check_database:
            check_database()
        print("PREFLIGHT PASS checks=" + ",".join(result.checks))
        if args.check_database:
            print("PREFLIGHT PASS database=reachable")
        return 0
    except Exception as exc:
        print("PREFLIGHT FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
