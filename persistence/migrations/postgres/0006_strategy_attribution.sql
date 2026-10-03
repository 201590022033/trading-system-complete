CREATE TABLE IF NOT EXISTS strategy_definitions (
 strategy_profile_id TEXT NOT NULL, strategy_profile_version TEXT NOT NULL,
 payload TEXT NOT NULL, sha256 TEXT NOT NULL,
 PRIMARY KEY(strategy_profile_id, strategy_profile_version)
);
CREATE TABLE IF NOT EXISTS strategy_record_refs (
 record_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, kind TEXT NOT NULL,
 strategy_profile_id TEXT NOT NULL, strategy_profile_version TEXT NOT NULL,
 FOREIGN KEY(account_id) REFERENCES paper_accounts(account_id),
 FOREIGN KEY(strategy_profile_id, strategy_profile_version)
 REFERENCES strategy_definitions(strategy_profile_id, strategy_profile_version)
);
CREATE INDEX IF NOT EXISTS strategy_record_scope ON strategy_record_refs
 (account_id,kind,strategy_profile_id,strategy_profile_version);
