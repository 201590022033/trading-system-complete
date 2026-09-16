"""Reuse MI domain serialization with a narrow PostgreSQL SQL/row adapter.

Only the store's internal parameterized SQL is accepted. No user SQL enters
this adapter. Schema creation remains native, versioned PostgreSQL SQL.
"""
import json
import re
from datetime import datetime
from market_intelligence.store import MarketIntelligenceStore


class StoreRow(dict):
    def __getitem__(self, key):
        return list(self.values())[key] if isinstance(key,int) else super().__getitem__(key)

class StoreResult:
    def __init__(self,rows,rowcount): self.rows,self.rowcount=rows,rowcount
    def fetchall(self): return self.rows
    def fetchone(self): return self.rows[0] if self.rows else None

class StoreConnection:
    def __init__(self,repository): self.repository=repository
    def execute(self,sql,parameters=()):
        sql=sql.strip().replace("datetime('now')","CURRENT_TIMESTAMP")
        if 'INSERT OR IGNORE INTO' in sql:
            sql=sql.replace('INSERT OR IGNORE INTO','INSERT INTO')+' ON CONFLICT DO NOTHING'
        if 'INSERT OR REPLACE INTO' in sql:
            match=re.search(r'INSERT OR REPLACE INTO (\w+)\s*\(([^)]+)\)',sql)
            if not match or match[1]!='evidence_records': raise ValueError('unsupported store upsert')
            columns=[part.strip() for part in match[2].split(',')]
            sql=sql.replace('INSERT OR REPLACE INTO','INSERT INTO')+' ON CONFLICT(evidence_id) DO UPDATE SET '+','.join(f'{name}=excluded.{name}' for name in columns if name!='evidence_id')
        parameters=list(parameters)
        if 'INSERT INTO source_policies' in sql:
            names=re.search(r'INSERT INTO source_policies\s*\(([^)]+)\)',sql)[1].split(',')
            if 'enabled' in [n.strip() for n in names]:
                index=[n.strip() for n in names].index('enabled'); parameters[index]=bool(parameters[index])
        with self.repository._require_connection().cursor() as cursor:
            cursor.execute(sql.replace('?', '%s'),parameters)
            result=[]
            if cursor.description:
                names=[column[0] for column in cursor.description]
                for row in cursor.fetchall():
                    values=[json.dumps(v) if isinstance(v,(dict,list)) else v.isoformat() if isinstance(v,datetime) else v for v in row]
                    result.append(StoreRow(zip(names,values)))
            return StoreResult(result,cursor.rowcount)
    def commit(self): self.repository._require_connection().commit()
    def transaction(self): return self.repository.transaction()
    def close(self): pass  # repository, not the MI view, owns the connection

def market_store(repository):
    store=MarketIntelligenceStore.__new__(MarketIntelligenceStore)
    store.path='postgresql'
    store._connection=StoreConnection(repository)
    return store
