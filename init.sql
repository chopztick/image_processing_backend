-- Initialize pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify the extension was created
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';