-- Initial market-intelligence schema.
-- evidence_records, documents, market_narratives, ticker_selections and audit_log
-- are append-only. source_policies is mutable configuration.

CREATE TABLE IF NOT EXISTS source_policies (
    source_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_class TEXT NOT NULL,
    authority_tier INTEGER NOT NULL,
    access_mode TEXT NOT NULL,
    status TEXT NOT NULL,
    region TEXT,
    market_relevance TEXT,
    url TEXT,
    enabled INTEGER NOT NULL DEFAULT 0,
    weight REAL DEFAULT 1.0,
    minimum_poll_seconds INTEGER DEFAULT 300,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_records (
    evidence_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_class TEXT NOT NULL,
    authority_tier INTEGER NOT NULL,
    headline TEXT,
    text TEXT,
    url TEXT,
    observed_at TEXT,
    published_at TEXT,
    ingested_at TEXT NOT NULL,
    tickers TEXT,
    assets TEXT,
    sectors TEXT,
    sentiment TEXT,
    score REAL,
    confidence REAL,
    horizon TEXT,
    parser_version TEXT,
    metadata TEXT,
    content_hash TEXT
);
CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence_records(source_id, ingested_at);
CREATE INDEX IF NOT EXISTS idx_evidence_published ON evidence_records(published_at);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    source_url TEXT,
    pdf_url TEXT,
    title TEXT,
    author TEXT,
    publication_date TEXT,
    retrieved_at TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    extraction_method TEXT,
    raw_text TEXT,
    storage_path TEXT,
    summary TEXT,
    market_topics TEXT,
    countries TEXT,
    sectors TEXT,
    companies TEXT,
    commodities TEXT,
    currencies TEXT,
    instruments TEXT,
    macro_factors TEXT,
    sentiment TEXT,
    time_horizon TEXT,
    confidence REAL,
    analysis_model TEXT,
    analysis_timestamp TEXT,
    metadata TEXT
);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_id, publication_date);
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(content_hash);

CREATE TABLE IF NOT EXISTS market_narratives (
    narrative_id TEXT PRIMARY KEY,
    generated_at TEXT NOT NULL,
    model TEXT,
    provider TEXT,
    schema_version TEXT,
    enabled_sources TEXT,
    summary TEXT,
    themes TEXT,
    candidates TEXT,
    selected_tickers TEXT,
    top_opportunities TEXT,
    prompt_version TEXT,
    metadata TEXT
);
CREATE INDEX IF NOT EXISTS idx_narratives_time ON market_narratives(generated_at DESC);

CREATE TABLE IF NOT EXISTS ticker_selections (
    selection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id TEXT NOT NULL,
    display_symbol TEXT NOT NULL,
    pinned INTEGER NOT NULL DEFAULT 0,
    reason TEXT,
    theme TEXT,
    confidence REAL,
    source_evidence_ids TEXT,
    selected_at TEXT NOT NULL,
    review_at TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    replaced_by INTEGER
);
CREATE INDEX IF NOT EXISTS idx_ticker_status ON ticker_selections(status, selected_at DESC);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL,
    actor TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    before_json TEXT,
    after_json TEXT,
    correlation_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id, occurred_at DESC);

CREATE TABLE IF NOT EXISTS watchlists (
    watchlist_id TEXT PRIMARY KEY,
    name TEXT,
    pinned_instruments TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
