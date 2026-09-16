-- Native PostgreSQL, additive upgrade of the existing populated schema.
ALTER TABLE source_policies ADD COLUMN IF NOT EXISTS region TEXT;
ALTER TABLE source_policies ADD COLUMN IF NOT EXISTS market_relevance TEXT;
ALTER TABLE evidence_records ADD COLUMN IF NOT EXISTS content_hash TEXT;
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS before_json JSONB;
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS correlation_id TEXT;
CREATE TABLE IF NOT EXISTS documents (
 document_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, source_url TEXT, pdf_url TEXT,
 title TEXT, author TEXT, publication_date TEXT, retrieved_at TEXT NOT NULL,
 content_hash TEXT NOT NULL UNIQUE, extraction_method TEXT, raw_text TEXT, storage_path TEXT,
 summary TEXT, market_topics TEXT, countries TEXT, sectors TEXT, companies TEXT,
 commodities TEXT, currencies TEXT, instruments TEXT, macro_factors TEXT, sentiment TEXT,
 time_horizon TEXT, confidence DOUBLE PRECISION, analysis_model TEXT, analysis_timestamp TEXT, metadata TEXT);
CREATE TABLE IF NOT EXISTS market_narratives (
 narrative_id TEXT PRIMARY KEY, generated_at TEXT NOT NULL, model TEXT, provider TEXT,
 schema_version TEXT, enabled_sources TEXT, summary TEXT, themes TEXT, candidates TEXT,
 selected_tickers TEXT, top_opportunities TEXT, prompt_version TEXT, metadata TEXT);
CREATE TABLE IF NOT EXISTS ticker_selections (
 selection_id BIGSERIAL PRIMARY KEY, instrument_id TEXT NOT NULL, display_symbol TEXT NOT NULL,
 pinned INTEGER NOT NULL DEFAULT 0, reason TEXT, theme TEXT, confidence DOUBLE PRECISION,
 source_evidence_ids TEXT, selected_at TEXT NOT NULL, review_at TEXT,
 status TEXT NOT NULL DEFAULT 'active', replaced_by BIGINT);
CREATE TABLE IF NOT EXISTS watchlists (
 watchlist_id TEXT PRIMARY KEY, name TEXT, pinned_instruments TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS documents_v2 (
 document_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, title TEXT NOT NULL, author TEXT,
 publication_date TEXT, canonical_url TEXT, pdf_url TEXT, retrieved_at TEXT NOT NULL,
 content_hash TEXT NOT NULL, mime_type TEXT, byte_size INTEGER, extraction_method TEXT,
 extraction_status TEXT NOT NULL, text_hash TEXT, processing_status TEXT NOT NULL,
 metadata TEXT NOT NULL DEFAULT '{}', UNIQUE(source_id,content_hash));
CREATE TABLE IF NOT EXISTS document_analyses (
 analysis_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, provider TEXT NOT NULL,
 model TEXT NOT NULL, schema_version TEXT NOT NULL, prompt_version TEXT NOT NULL,
 content_hash TEXT NOT NULL, analysed_at TEXT NOT NULL, facts TEXT NOT NULL,
 themes TEXT NOT NULL, candidates TEXT NOT NULL, uncertainties TEXT NOT NULL,
 contradictions TEXT NOT NULL, usage TEXT NOT NULL DEFAULT '{}',
 UNIQUE(document_id,content_hash,provider,model,schema_version,prompt_version));
CREATE TABLE IF NOT EXISTS provenance_edges (
 provenance_id TEXT PRIMARY KEY, snapshot_id TEXT, from_type TEXT NOT NULL,
 from_id TEXT NOT NULL, relationship_type TEXT NOT NULL, to_type TEXT NOT NULL,
 to_id TEXT NOT NULL, confidence DOUBLE PRECISION, reason TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS intelligence_snapshots (
 snapshot_id TEXT PRIMARY KEY, generated_at TEXT NOT NULL, schema_version TEXT NOT NULL,
 enabled_sources TEXT NOT NULL, document_hashes TEXT NOT NULL, themes TEXT NOT NULL,
 candidates TEXT NOT NULL, selections TEXT NOT NULL, provider_metadata TEXT NOT NULL,
 metadata TEXT NOT NULL DEFAULT '{}');
CREATE INDEX IF NOT EXISTS idx_worker_due ON worker_jobs(status,target_time);
CREATE INDEX IF NOT EXISTS idx_worker_expired ON worker_jobs(status,last_updated);
CREATE INDEX IF NOT EXISTS idx_document_analysis_content ON document_analyses(content_hash,provider,model,schema_version,prompt_version);
CREATE INDEX IF NOT EXISTS idx_provenance_from ON provenance_edges(from_type,from_id);
CREATE INDEX IF NOT EXISTS idx_provenance_to ON provenance_edges(to_type,to_id);
