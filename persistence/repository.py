"""Domain-oriented storage interface and backend factory."""

from contextlib import contextmanager
import os
from typing import Iterator, Protocol

from domain.intelligence.clustering import ClusteredEvent
from domain.registry.source import CanonicalSourcePolicy
from evidence import EvidenceRecord


class StorageRepository(Protocol):
    def list_source_policies(self) -> list[CanonicalSourcePolicy]: ...
    def get_source_policy(self, source_id: str) -> CanonicalSourcePolicy | None: ...
    def save_source_policy(self, policy: CanonicalSourcePolicy) -> CanonicalSourcePolicy: ...
    def save_evidence(self, record: EvidenceRecord) -> None: ...
    def get_evidence(self, evidence_id: str) -> EvidenceRecord | None: ...
    def save_clustered_event(self, event: ClusteredEvent) -> None: ...
    def list_clustered_events(self) -> list[ClusteredEvent]: ...
    def append_audit_event(self, action: str, entity_type: str | None = None,
                           entity_id: str | None = None, after: dict | None = None) -> None: ...
    @contextmanager
    def transaction(self) -> Iterator[None]: ...


def get_storage_repository(*, database_url: str | None = None, sqlite_path: str = "market_intelligence.db") -> StorageRepository:
    url = database_url if database_url is not None else os.environ.get("DATABASE_URL")
    if url and url.lower().startswith(("postgresql://", "postgres://")):
        from .postgres_repository import PostgresRepository
        return PostgresRepository(url)
    from .sqlite_repository import SQLiteRepository
    return SQLiteRepository(sqlite_path)
