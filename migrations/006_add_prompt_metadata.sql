-- Migration 006: Add prompt metadata to conversations
-- Date: 2025-10-16
-- Purpose: Store the complete prompt evolution chain (original input → AI enhancements)
--
-- This allows users to see:
--   1. What they originally typed
--   2. How GPT-4o-mini enhanced it
--   3. How Sonnet refined it for agent selection (if dynamic agents)
--
-- Schema:
--   prompt_metadata JSONB: {
--     "original_user_input": "user's raw input",
--     "generated_title": "concise title created by AI",
--     "generated_prompt": "enhanced prompt created by AI",
--     "refined_topic": "refined topic for agent selection (optional)",
--     "expertise_analysis": {
--       "refined_topic": "...",
--       "expertise_needed": [...],
--       "suggested_domains": [...]
--     },
--     "timestamps": {
--       "title_generated_at": "...",
--       "prompt_generated_at": "...",
--       "topic_refined_at": "..."
--     }
--   }

BEGIN;

-- Step 1: Add prompt_metadata JSONB column
ALTER TABLE conversations
ADD COLUMN prompt_metadata JSONB DEFAULT NULL;

-- Step 2: Add index for prompt_metadata (for querying)
CREATE INDEX IF NOT EXISTS idx_conversations_prompt_metadata ON conversations USING GIN(prompt_metadata);

-- Step 3: Add comment for documentation
COMMENT ON COLUMN conversations.prompt_metadata IS 'Stores the complete prompt evolution chain from original user input through AI enhancements';

-- Step 4: Verify the migration
DO $$
DECLARE
    new_column_exists BOOLEAN;
BEGIN
    -- Check if prompt_metadata column was added
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'conversations'
        AND column_name = 'prompt_metadata'
    ) INTO new_column_exists;

    IF NOT new_column_exists THEN
        RAISE EXCEPTION 'Migration failed: prompt_metadata column was not added';
    END IF;

    RAISE NOTICE '✓ Migration successful: prompt_metadata column added to conversations table';
END $$;

COMMIT;
