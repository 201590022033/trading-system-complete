CREATE INDEX IF NOT EXISTS idx_worker_due ON worker_jobs(status,target_time);
CREATE INDEX IF NOT EXISTS idx_worker_expired ON worker_jobs(status,last_updated);
CREATE INDEX IF NOT EXISTS idx_document_analysis_content ON document_analyses(content_hash,provider,model,schema_version,prompt_version);
