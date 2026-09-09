"""M7 write/verify validation for the configured Railway PostgreSQL store."""

from datetime import datetime, timezone
import os
import sys

from domain.intelligence.clustering import ClusteredEvent
from domain.registry.source import default_canonical_policies
from evidence import EvidenceRecord
from persistence.postgres_repository import PostgresRepository

PREFIX = "M7_VALIDATION_"
IDS = {"source": PREFIX + "SOURCE_POLICY", "evidence": PREFIX + "EVIDENCE",
       "event": PREFIX + "CLUSTERED_EVENT", "audit": PREFIX + "AUDIT"}


def repository() -> PostgresRepository:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is required")
    result = PostgresRepository(url)
    result.initialize()
    return result


def records():
    stamp = datetime.now(timezone.utc).isoformat()
    source = next(item for item in default_canonical_policies() if item.source_id == "moneyweb_rss")
    source = source.__class__(IDS["source"], "M7 validation source", source.source_type, source.source_class,
                              source.endpoint, source.access_mode, True, source.governance_state, source.authority_tier,
                              source.manual_weight, None, source.minimum_poll_seconds, None, stamp, 0, "M7_VALIDATION", (), True, None, "M7 only")
    evidence = EvidenceRecord(IDS["evidence"], IDS["source"], source.display_name, source.source_class, source.authority_tier,
                              "M7 validation evidence", "M7 validation record", None, stamp, stamp, stamp,
                              ["M7"], [], [], "neutral", 0.0, 0.0, None, metadata={"validation": True})
    event = ClusteredEvent(IDS["event"], "M7_VALIDATION", "v1", stamp, stamp, evidence.headline,
                           (evidence.evidence_id,), (evidence.source_id,), ("M7",), (), 0, 0.0, 0)
    return source, evidence, event, stamp


def write() -> None:
    repo = repository(); source, evidence, event, stamp = records()
    repo.save_source_policy(source)
    repo.save_evidence(evidence); repo.save_clustered_event(event)
    repo.append_audit_event("M7_VALIDATION_AUDIT", "m7_validation", IDS["audit"], {"validation": True})
    assert repo.get_source_policy(source.source_id) is not None
    assert repo.evidence_exists(evidence.evidence_id) and repo.clustered_event_exists(event.event_id)
    assert repo.audit_exists("M7_VALIDATION_AUDIT", IDS["audit"])
    assert repo.evidence_ingested_at(evidence.evidence_id) == stamp
    try:
        with repo.transaction():
            with repo._require_connection().cursor() as cursor:
                cursor.execute("INSERT INTO audit_log (action, entity_id) VALUES (%s,%s)", ("M7_ROLLBACK", "M7_ROLLBACK"))
            raise RuntimeError("M7 rollback probe")
    except RuntimeError:
        pass
    assert not repo.audit_exists("M7_ROLLBACK", "M7_ROLLBACK")
    print("PASS WRITE", " ".join(f"{key}={value}" for key, value in IDS.items()), "timestamp=" + stamp)
    repo.close()


def verify() -> None:
    repo = repository()
    assert repo.get_source_policy(IDS["source"]) is not None
    assert repo.evidence_exists(IDS["evidence"]) and repo.clustered_event_exists(IDS["event"])
    assert repo.audit_exists("M7_VALIDATION_AUDIT", IDS["audit"])
    assert repo.evidence_ingested_at(IDS["evidence"]) is not None
    print("PASS VERIFY", " ".join(f"{key}={value}" for key, value in IDS.items()))
    repo.close()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"write", "verify"}:
        raise SystemExit("usage: validate_railway_postgres.py write|verify")
    try:
        write() if sys.argv[1] == "write" else verify()
    except Exception as exc:
        print(f"FAIL {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
