-- Migration 003: Increase conversation title length limit
-- Date: 2025-10-14
-- Purpose: Allow longer conversation titles (especially those with URLs)
--
-- Previously: title VARCHAR(255)
-- Now: title TEXT (unlimited length)
--
-- This is a safe operation that preserves all existing data

BEGIN;

-- Step 1: Drop the view that depends on the title column
DROP VIEW IF EXISTS conversation_summaries;

-- Step 2: Alter the title column to support unlimited length
ALTER TABLE conversations
ALTER COLUMN title TYPE TEXT;

-- Step 3: Recreate the view with the updated column type
CREATE OR REPLACE VIEW conversation_summaries AS
SELECT
    c.id,
    c.title,
    c.initial_prompt,
    c.agent_a_name,
    c.agent_b_name,
    c.created_at,
    c.updated_at,
    c.total_turns,
    c.total_tokens,
    c.status,
    c.tags,
    COUNT(e.id) as exchange_count,
    MAX(e.created_at) as last_exchange_at
FROM conversations c
LEFT JOIN exchanges e ON c.id = e.conversation_id
GROUP BY c.id
ORDER BY c.updated_at DESC;

-- Step 4: Verify the change was successful
DO $$
DECLARE
    column_type TEXT;
BEGIN
    SELECT data_type INTO column_type
    FROM information_schema.columns
    WHERE table_name = 'conversations'
    AND column_name = 'title';

    IF column_type = 'text' THEN
        RAISE NOTICE '✓ Migration successful: title column is now TEXT';
    ELSE
        RAISE EXCEPTION 'Migration failed: title column is still %', column_type;
    END IF;
END $$;

COMMIT;
