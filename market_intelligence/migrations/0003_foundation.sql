-- Additive Market Intelligence Foundation metadata and explicit provenance.
CREATE TABLE IF NOT EXISTS documents_v2 (
    document_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    publication_date TEXT,
    canonical_url TEXT,
    pdf_url TEXT,
    retrieved_at TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    mime_type TEXT,
    byte_size INTEGER,
    extraction_method TEXT,
    extraction_status TEXT NOT NULL,
    text_hash TEXT,
    processing_status TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    UNIQUE(source_id, content_hash)
);
CREATE INDEX IF NOT EXISTS idx_documents_v2_source ON documents_v2(source_id, publication_date);
CREATE INDEX IF NOT EXISTS idx_documents_v2_hash ON documents_v2(content_hash);

CREATE TABLE IF NOT EXISTS document_analyses (
    analysis_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    analysed_at TEXT NOT NULL,
    facts TEXT NOT NULL,
    themes TEXT NOT NULL,
    candidates TEXT NOT NULL,
    uncertainties TEXT NOT NULL,
    contradictions TEXT NOT NULL,
    usage TEXT NOT NULL DEFAULT '{}',
    UNIQUE(document_id, content_hash, provider, model, schema_version, prompt_version)
);

CREATE TABLE IF NOT EXISTS provenance_edges (
    provenance_id TEXT PRIMARY KEY,
    snapshot_id TEXT,
    from_type TEXT NOT NULL,
    from_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    to_type TEXT NOT NULL,
    to_id TEXT NOT NULL,
    confidence REAL,
    reason TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_provenance_from ON provenance_edges(from_type, from_id);
CREATE INDEX IF NOT EXISTS idx_provenance_to ON provenance_edges(to_type, to_id);

CREATE TABLE IF NOT EXISTS intelligence_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    generated_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    enabled_sources TEXT NOT NULL,
    document_hashes TEXT NOT NULL,
    themes TEXT NOT NULL,
    candidates TEXT NOT NULL,
    selections TEXT NOT NULL,
    provider_metadata TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}'
);
