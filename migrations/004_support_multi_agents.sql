-- Migration 004: Support multiple agents in conversations
-- Date: 2025-10-14
-- Purpose: Enable conversations with 3+ agents instead of just 2
--
-- Strategy: Add new agents JSONB column while keeping agent_a/agent_b for backward compatibility
--
-- New schema:
--   agents JSONB: Array of {id, name, qualification}
--   Example: [
--     {"id": "dynamic-abc123", "name": "Dr. Smith", "qualification": "Neuroscience"},
--     {"id": "dynamic-def456", "name": "Prof. Johnson", "qualification": "Philosophy"},
--     {"id": "dynamic-ghi789", "name": "Sarah Chen", "qualification": "Ethics"}
--   ]
--
-- Backward compatibility:
--   - Keep agent_a_id, agent_a_name, agent_b_id, agent_b_name columns
--   - New conversations populate both formats
--   - Old conversations continue to work

BEGIN;

-- Step 1: Add agents JSONB column
ALTER TABLE conversations
ADD COLUMN agents JSONB DEFAULT NULL;

-- Step 2: Add index for agents JSONB column (for querying)
CREATE INDEX IF NOT EXISTS idx_conversations_agents ON conversations USING GIN(agents);

-- Step 3: Migrate existing 2-agent conversations to new format
-- Populate agents column from agent_a/agent_b for existing conversations
UPDATE conversations
SET agents = jsonb_build_array(
    jsonb_build_object(
        'id', agent_a_id,
        'name', agent_a_name,
        'qualification', NULL
    ),
    jsonb_build_object(
        'id', agent_b_id,
        'name', agent_b_name,
        'qualification', NULL
    )
)
WHERE agents IS NULL;

-- Step 4: Drop and recreate the conversation_summaries view
DROP VIEW IF EXISTS conversation_summaries;

CREATE OR REPLACE VIEW conversation_summaries AS
SELECT
    c.id,
    c.title,
    c.initial_prompt,
    c.agent_a_name,
    c.agent_b_name,
    c.agents,  -- New column
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

-- Step 5: Create helper function to extract agent names for display
CREATE OR REPLACE FUNCTION get_agent_names(conversation_row conversations)
RETURNS TEXT AS $$
DECLARE
    agent_names TEXT;
    agent_count INT;
BEGIN
    -- If agents JSONB exists and has data, use it
    IF conversation_row.agents IS NOT NULL THEN
        SELECT string_agg(agent->>'name', ' ↔ ' ORDER BY ordinality)
        INTO agent_names
        FROM jsonb_array_elements(conversation_row.agents) WITH ORDINALITY AS agent;

        RETURN agent_names;
    ELSE
        -- Fallback to agent_a/agent_b for backward compatibility
        RETURN conversation_row.agent_a_name || ' ↔ ' || conversation_row.agent_b_name;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Step 6: Verify the migration
DO $$
DECLARE
    new_column_exists BOOLEAN;
    migrated_count INTEGER;
    total_count INTEGER;
BEGIN
    -- Check if agents column was added
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'conversations'
        AND column_name = 'agents'
    ) INTO new_column_exists;

    IF NOT new_column_exists THEN
        RAISE EXCEPTION 'Migration failed: agents column was not added';
    END IF;

    -- Count total conversations
    SELECT COUNT(*) INTO total_count FROM conversations;

    -- Count conversations with agents data
    SELECT COUNT(*) INTO migrated_count FROM conversations WHERE agents IS NOT NULL;

    IF total_count = migrated_count THEN
        RAISE NOTICE '✓ Migration successful: agents column added and % existing conversations migrated', total_count;
    ELSE
        RAISE WARNING 'Migration partial: % of % conversations migrated', migrated_count, total_count;
    END IF;
END $$;

COMMIT;
