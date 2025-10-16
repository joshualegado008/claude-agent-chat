-- Migration 007: Add sources column to exchanges table
-- This enables tracking of citations/sources for each agent response

-- Add sources column as JSONB array
-- Each source: {source_id, title, url, publisher, accessed_date, excerpt}
ALTER TABLE exchanges
ADD COLUMN sources JSONB DEFAULT '[]'::jsonb;

-- Create GIN index for efficient JSON queries on sources
CREATE INDEX IF NOT EXISTS idx_exchanges_sources
ON exchanges USING GIN(sources);

-- Add comment for documentation
COMMENT ON COLUMN exchanges.sources IS 'Array of sources/citations used in this exchange (from web searches or URL fetches)';
