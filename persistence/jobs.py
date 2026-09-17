"""Bounded durable queries and compare-and-swap claims, no extra service."""
import json
from dataclasses import replace
from datetime import timedelta
from shadow_learning import JobCheckpoint, timestamp


class DurableJobs:
    def readiness(self):
        try:
            tables=('observations','shadow_decisions','outcome_labels','adaptive_evidence_contributions',
                    'worker_jobs','worker_status','document_analyses','intelligence_snapshots','reliability_sources')
            for table in tables:
                self._job_sql(f'SELECT 1 FROM {table} LIMIT 0',rows=True)
            return {'backend':self.backend,'state':'AVAILABLE'}
        except Exception:
            return {'backend':self.backend,'state':'UNAVAILABLE'}

    def counts(self):
        result={}
        for name,table,where in (
            ('observations','observations','1=1'),('shadow_decisions','shadow_decisions','1=1'),
            ('labelled_outcomes','shadow_decisions',"outcome_status='LABELLED'"),
            ('pending_outcomes','shadow_decisions',"outcome_status='PENDING_OUTCOME'"),
            ('adaptive_updates','adaptive_evidence_contributions','1=1')):
            result[name]=self._job_sql(f'SELECT COUNT(*) FROM {table} WHERE {where}',rows=True)[0][0]
        return result
    def _job_sql(self, sql, parameters=(), *, rows=False):
        connection=self.store._connection if self.backend=='sqlite' else self._require_connection()
        cursor=connection.cursor()
        try:
            cursor.execute(sql if self.backend=='sqlite' else sql.replace('?', '%s'),parameters)
            return cursor.fetchall() if rows else cursor.rowcount
        finally: cursor.close()

    def ensure_job(self, job):
        with self.transaction():
            self._job_sql('INSERT INTO worker_jobs VALUES (?,?,?,?,?,?) ON CONFLICT(job_key) DO NOTHING',
                (job.job_key,job.job_type,job.target_time,job.status,json.dumps(job.to_dict()),job.last_updated or job.target_time))
            stored=self.get_job(job.job_key)
            if (stored['job_type'],stored['target_time']) != (job.job_type,job.target_time):
                raise ValueError('job identity conflict')

    def due_jobs(self, now, limit=1):
        if not 1 <= limit <= 100: raise ValueError('bounded job limit required')
        retry=("json_extract(payload,'$.retryable') = 1" if self.backend=='sqlite'
               else "CAST(payload->>'retryable' AS BOOLEAN) = TRUE")
        attempts=("json_extract(payload,'$.attempt_count')" if self.backend=='sqlite'
                  else "CAST(payload->>'attempt_count' AS INTEGER)")
        rows=self._job_sql(f"SELECT payload FROM worker_jobs WHERE target_time<=? AND (status='PENDING' OR (status='FAILED' AND {retry})) AND {attempts}<5 ORDER BY target_time,job_key LIMIT ?",
            (timestamp(now).isoformat(),limit),rows=True)
        return [JobCheckpoint(**(json.loads(row[0]) if isinstance(row[0],str) else row[0])) for row in rows]

    def claim_job(self, job_key, worker_id, now):
        with self.transaction():
            data=self.get_job(job_key)
            if not data: return None
            job=JobCheckpoint(**data)
            if (timestamp(job.target_time)>timestamp(now) or job.status not in {'PENDING','FAILED'}
                    or (job.status=='FAILED' and not job.retryable) or job.attempt_count>=5):
                return None
            claimed=replace(job,status='RUNNING',worker_id=worker_id,attempt_count=job.attempt_count+1,last_updated=now)
            changed=self._job_sql('UPDATE worker_jobs SET status=?,payload=?,last_updated=? WHERE job_key=? AND status=? AND last_updated=?',
                ('RUNNING',json.dumps(claimed.to_dict()),claimed.last_updated,job_key,job.status,job.last_updated or job.target_time))
            return claimed if changed==1 else None

    def finish_job(self, running, done):
        with self.transaction():
            # last_updated + attempt owner are checked from persisted state in
            # the transaction; the SQL compare-and-swap prevents stale writers.
            current=self.get_job(running.job_key)
            if current != running.to_dict(): return False
            return self._job_sql("UPDATE worker_jobs SET status=?,payload=?,last_updated=? WHERE job_key=? AND status='RUNNING' AND last_updated=?",
                (done.status,json.dumps(done.to_dict()),done.last_updated,running.job_key,running.last_updated))==1

    def recover_jobs(self, now, *, limit=1, lease_seconds=300, keys=None):
        cutoff=(timestamp(now)-timedelta(seconds=lease_seconds)).isoformat()
        retry=("json_extract(payload,'$.retryable') = 1" if self.backend=='sqlite'
               else "CAST(payload->>'retryable' AS BOOLEAN) = TRUE")
        with self.transaction():
            rows=self._job_sql(f"SELECT payload FROM worker_jobs WHERE status='RUNNING' AND last_updated<=? AND {retry} ORDER BY last_updated,job_key LIMIT ?",(cutoff,limit),rows=True)
            recovered=[]
            for row in rows:
                job=JobCheckpoint(**(json.loads(row[0]) if isinstance(row[0],str) else row[0]))
                if keys is not None and job.job_key not in keys: continue
                pending=replace(job,status='PENDING',worker_id=None,error_category='WORKER_RESTART',last_updated=now)
                if self._job_sql("UPDATE worker_jobs SET status=?,payload=?,last_updated=? WHERE job_key=? AND status='RUNNING' AND last_updated=?",
                    ('PENDING',json.dumps(pending.to_dict()),pending.last_updated,job.job_key,job.last_updated or job.target_time))==1:
                    recovered.append(pending)
            return recovered

    def save_worker_status(self, status):
        with self.transaction():
            self._job_sql('INSERT INTO worker_status VALUES (?,?,?,?) ON CONFLICT(worker_id) DO UPDATE SET status=excluded.status,payload=excluded.payload,last_updated=excluded.last_updated',
                (status['worker_id'],status['status'],json.dumps(status),status['last_heartbeat_at']))

    def save_reliability_source(self, source):
        with self.transaction():
            self._job_sql('INSERT INTO reliability_sources VALUES (?,?) ON CONFLICT(source_id) DO UPDATE SET payload=excluded.payload',
                (source['source_id'],json.dumps(source)))

    def get_reliability_source(self, source_id):
        rows=self._job_sql('SELECT payload FROM reliability_sources WHERE source_id=?',(source_id,),rows=True)
        return (json.loads(rows[0][0]) if isinstance(rows[0][0],str) else rows[0][0]) if rows else None

    def find_reliability_outcome(self,evidence_id,scope_key,horizon):
        from shadow_learning import stable_id
        rows=self._job_sql('SELECT payload FROM reliability_outcomes WHERE reliability_id IN (?,?)',
            (stable_id('reliability',evidence_id,scope_key,horizon),'|'.join((evidence_id,scope_key,horizon))),rows=True)
        for row in rows:
            data=json.loads(row[0]) if isinstance(row[0],str) else row[0]
            if (data['evidence_id'],data['scope_key'],data['horizon'])==(evidence_id,scope_key,horizon): return data
        return None

    def reliability_statistics(self,source_id,scope_key,horizon):
        outcome="payload->>'outcome'" if self.backend=='postgresql' else "json_extract(payload,'$.outcome')"
        aligned="CAST(payload->>'aligned_return' AS DOUBLE PRECISION)" if self.backend=='postgresql' else "json_extract(payload,'$.aligned_return')"
        return self._job_sql(f"SELECT COUNT(*),SUM(CASE WHEN {outcome}='win' THEN 1 ELSE 0 END),SUM(CASE WHEN {outcome}='loss' THEN 1 ELSE 0 END),SUM(CASE WHEN {outcome}='flat' THEN 1 ELSE 0 END),AVG({aligned}) FROM reliability_outcomes WHERE source_id=? AND scope_key=? AND horizon=?",(source_id,scope_key,horizon),rows=True)[0]
