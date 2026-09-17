"""Persisted UTC-window read model shared by both database backends."""
import json
from datetime import datetime, timezone, timedelta
from shadow_learning import timestamp

def learning_status(repository, now=None):
    current=timestamp(now) if now else datetime.now(timezone.utc)
    pg=repository.backend=='postgresql'
    temporal=lambda column: f'CAST({column} AS TIMESTAMPTZ)' if pg else f'julianday({column})'
    parameter='CAST(? AS TIMESTAMPTZ)' if pg else 'julianday(?)'
    result={'pending_outcomes':0,'latest_timestamps':{},'database_backend':repository.backend,
            'database_state':'AVAILABLE','worker_status':{'status':'UNKNOWN'}}
    evaluated="o.payload->>'evaluated_at'" if pg else "json_extract(o.payload,'$.evaluated_at')"
    metrics=(('observations','observations','observed_at','1=1'),
        ('shadow_decisions','shadow_decisions','decided_at','1=1'),
        ('labelled_outcomes','outcome_labels o JOIN shadow_decisions d ON d.decision_id=o.decision_id',evaluated,"d.outcome_status='LABELLED'"),
        ('unavailable_outcomes','outcome_labels o JOIN shadow_decisions d ON d.decision_id=o.decision_id',evaluated,"d.outcome_status='OUTCOME_DATA_UNAVAILABLE'"),
        ('adaptive_updates','adaptive_evidence_contributions','contributed_at','1=1'))
    with repository.transaction():
        for name,table,column,extra in metrics:
            clock=temporal(column); result[name]={}
            for window,days in (('24h',1),('3d',3),('7d',7)):
                rows=repository._job_sql(f'SELECT COUNT(*) FROM {table} WHERE {extra} AND {clock}>={parameter} AND {clock}<={parameter}',
                    ((current-timedelta(days=days)).isoformat(),current.isoformat()),rows=True)
                result[name][window]=rows[0][0]
            rows=repository._job_sql(f'SELECT {column} FROM {table} WHERE {extra} AND {clock}<={parameter} ORDER BY {clock} DESC LIMIT 1',
                (current.isoformat(),),rows=True)
            value=rows[0][0] if rows else None
            result['latest_timestamps'][name]=(timestamp(value.isoformat() if isinstance(value,datetime) else value).isoformat() if value else None)
        result['pending_outcomes']=repository._job_sql(f"SELECT COUNT(*) FROM shadow_decisions WHERE outcome_status='PENDING_OUTCOME' AND {temporal('decided_at')}<={parameter}",(current.isoformat(),),rows=True)[0][0]
        rows=repository._job_sql(f'SELECT payload FROM worker_status WHERE {temporal("last_updated")}<={parameter} ORDER BY last_updated DESC LIMIT 1',
            (current.isoformat(),),rows=True)
        if rows:
            state=json.loads(rows[0][0]) if isinstance(rows[0][0],str) else rows[0][0]
            # Explicit safe projection; checkpoints and arbitrary payloads never leak.
            result['worker_status']={key:state[key] for key in ('status','last_heartbeat_at','started_at','processed') if key in state}
            if timestamp(state['last_heartbeat_at'])<current-timedelta(seconds=300):
                result['worker_status']['status']='STALE'
    return result
