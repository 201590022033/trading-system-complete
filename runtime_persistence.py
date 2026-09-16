"""Canonical runtime persistence composition for web and worker processes."""
from persistence.repository import get_storage_repository

def runtime_repository(*, database_url=None, sqlite_path="market_intelligence.db"):
    """Select the shared backend; PostgreSQL never falls back to local SQLite."""
    return get_storage_repository(database_url=database_url, sqlite_path=sqlite_path)
