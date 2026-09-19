CREATE TABLE IF NOT EXISTS paper_accounts (
 account_id TEXT PRIMARY KEY, revision INTEGER NOT NULL, payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS paper_records (
 record_id TEXT PRIMARY KEY, account_id TEXT NOT NULL,
 kind TEXT NOT NULL, available_at TEXT NOT NULL, payload TEXT NOT NULL,
 FOREIGN KEY(account_id) REFERENCES paper_accounts(account_id)
);
CREATE INDEX IF NOT EXISTS paper_records_lookup ON paper_records(account_id,kind,available_at,record_id);
