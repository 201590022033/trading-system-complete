"""Canonical experiment repository boundary.

Durable SQLite/PostgreSQL adapters require a later additive schema migration.
M17 exposes the protocol and safe local append-only implementation without
creating a disconnected database.
"""
from domain.evaluation.experiment import ExperimentRepository, InMemoryExperimentRepository

__all__ = ["ExperimentRepository", "InMemoryExperimentRepository"]
