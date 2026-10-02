CREATE TABLE IF NOT EXISTS paper_record_archives (
 record_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, kind TEXT NOT NULL,
 available_at TEXT NOT NULL, payload_gzip_base64 TEXT NOT NULL, sha256 TEXT NOT NULL,
 FOREIGN KEY(account_id) REFERENCES paper_accounts(account_id)
);
