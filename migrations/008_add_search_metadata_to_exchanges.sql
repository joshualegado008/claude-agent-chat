-- Migration 008: Add search metadata to exchanges table
-- Enables tracking which exchanges triggered autonomous searches

-- Add search_query column (the query that was searched)
ALTER TABLE exchanges
ADD COLUMN search_query TEXT;

-- Add search_trigger_type column (why the search was triggered: fact_check, curiosity, etc.)
ALTER TABLE exchanges
ADD COLUMN search_trigger_type TEXT;

-- Add comments for documentation
COMMENT ON COLUMN exchanges.search_query IS 'The search query used if autonomous search was triggered during this exchange';
COMMENT ON COLUMN exchanges.search_trigger_type IS 'Type of search trigger (e.g., fact_check, curiosity, verification)';
