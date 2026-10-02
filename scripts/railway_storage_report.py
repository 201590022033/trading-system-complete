"""Read-only, secret-free storage capacity report. No account or chart payload output."""
import argparse
import gzip
import json
from math import ceil


def retention_capacity(*, volume_used_bytes, compact_session_bytes, archived_session_bytes,
                       recent_session_bytes, volume_limit_bytes=500_000_000, reserve_bytes=100_000_000):
    # 90 calendar days ~65 sessions; 252 annual sessions is a planning assumption.
    recent_reserve = 65 * recent_session_bytes
    annual_growth = 252 * (compact_session_bytes + archived_session_bytes) * 2
    # 2x margin for indexes, row overhead and a growing paper execution ledger.
    headroom = max(0, volume_limit_bytes-reserve_bytes-volume_used_bytes-recent_reserve)
    return {"raw_snapshot_days":90, "compact_evidence_expiry":None,
            "automatic_evidence_deletion":False,
            "headroom_after_reserves_bytes":headroom, "annual_growth_budget_bytes":ceil(annual_growth),
            "projected_years_to_storage_review": headroom/annual_growth if annual_growth else None,
            "assumptions":"252 sessions/year; 2x row/index margin; 100MB free reserve; forecast not a guarantee",
            "online_evidence_query_max_rows":5000}


def report(repository, *, volume_used_bytes):
    rows = repository._job_sql("SELECT kind,COUNT(*),SUM(LENGTH(payload)) FROM paper_records GROUP BY kind ORDER BY kind",rows=True)
    state_rows = repository._job_sql("SELECT account_id,payload FROM paper_accounts",rows=True)
    config_rows = [(aid,json.loads(raw)) for aid,raw in state_rows]
    active = next(((aid,state) for aid,state in config_rows if aid == "railway-paper-zar-v3"), None)
    latest_sizes = {}
    archive_bytes = 0
    signal_clocks = []
    if active:
        aid,state = active
        for kind in ("input","ranking"):
            latest = repository.paper_records(aid,kind,as_of="2099-01-01T00:00:00Z",limit=1)
            if latest:
                raw = json.dumps(latest[0],separators=(",",":"),sort_keys=True).encode()
                latest_sizes[kind] = len(raw)
                archive_bytes += ceil(len(gzip.compress(raw,mtime=0))*4/3)
        decisions = repository.paper_records(aid,"candidate-decision",as_of="2099-01-01T00:00:00Z",limit=30)
        signal_clocks = sorted({row["signal_bar_at"] for row in decisions})
    # All 17 shares + 4 mandatory ETFs: decision and outcome, plus 4 market benchmarks.
    compact_bytes = 21*2000 + 4*1000
    capacity = retention_capacity(volume_used_bytes=volume_used_bytes,
        compact_session_bytes=compact_bytes,archived_session_bytes=archive_bytes,
        recent_session_bytes=sum(latest_sizes.values()))
    return {"record_sizes":[{"kind":kind,"count":count,"payload_bytes":size} for kind,count,size in rows],
            "latest_snapshot_bytes":latest_sizes,"forecast_compressed_snapshot_bytes":archive_bytes,
            "candidate_signal_availability_clocks":signal_clocks,"retention":capacity}


if __name__ == "__main__":
    from runtime_persistence import runtime_repository
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--volume-used-bytes",type=int,required=True)
    args=parser.parse_args()
    repository=runtime_repository()
    try:print(json.dumps(report(repository,volume_used_bytes=args.volume_used_bytes),sort_keys=True))
    finally:repository.close()
