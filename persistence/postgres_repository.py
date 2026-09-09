"""PostgreSQL-compatible adapter boundary.

No PostgreSQL driver is required for local M6 work. A DB-API connection or
connection factory may be injected for integration tests; otherwise the adapter
fails explicitly when used rather than pretending a live connection exists.
"""

from contextlib import contextmanager
from typing import Any, Callable, Iterator


POSTGRES_SCHEMA = """CREATE TABLE IF NOT EXISTS clustered_events (
event_id TEXT PRIMARY KEY, policy_id TEXT NOT NULL, policy_version TEXT NOT NULL,
first_observed_at TEXT NOT NULL, latest_observed_at TEXT NOT NULL, primary_headline TEXT NOT NULL,
evidence_ids TEXT NOT NULL, source_ids TEXT NOT NULL, entity_references TEXT NOT NULL,
macro_references TEXT NOT NULL, consensus_direction INTEGER NOT NULL,
aggregate_strength DOUBLE PRECISION NOT NULL, duplicate_count INTEGER NOT NULL
)"""


class PostgresRepository:
    backend = "postgresql"

    def __init__(self, database_url: str, connection: Any = None,
                 connection_factory: Callable[[str], Any] | None = None) -> None:
        if not database_url.lower().startswith(("postgresql://", "postgres://")):
            raise ValueError("PostgresRepository requires a PostgreSQL DATABASE_URL")
        self.database_url = database_url
        self._connection = connection
        self._connection_factory = connection_factory

    @property
    def connected(self) -> bool:
        return self._connection is not None

    def _require_connection(self) -> Any:
        if self._connection is None and self._connection_factory is not None:
            self._connection = self._connection_factory(self.database_url)
        if self._connection is None:
            raise RuntimeError("PostgreSQL integration is not configured; inject a DB-API connection")
        return self._connection

    def initialize_sql(self) -> str:
        return POSTGRES_SCHEMA

    @contextmanager
    def transaction(self) -> Iterator[Any]:
        connection = self._require_connection()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
