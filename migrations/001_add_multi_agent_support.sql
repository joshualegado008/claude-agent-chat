-- Migration: Add multi-agent support and prompt metadata to conversations table
-- Description: Adds agents JSONB column for storing multiple agent profiles
--              and prompt_metadata JSONB column for tracking prompt evolution
-- Date: 2025-10-17

-- Add agents column (JSONB array of agent objects)
-- Stores: [{id, name, qualification}, ...]
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS agents JSONB DEFAULT NULL;

-- Add prompt_metadata column (JSONB object)
-- Stores: {original_user_input, generated_title, generated_prompt, generated_tags, refined_topic, expertise_requirements, timestamps: {...}}
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS prompt_metadata JSONB DEFAULT NULL;

-- Create index on agents column for efficient queries
CREATE INDEX IF NOT EXISTS idx_conversations_agents ON conversations USING GIN(agents);

-- Create index on prompt_metadata column for efficient queries
CREATE INDEX IF NOT EXISTS idx_conversations_prompt_metadata ON conversations USING GIN(prompt_metadata);

-- Migrate legacy conversations: populate agents array from agent_a/agent_b columns
-- This ensures backward compatibility for existing conversations
UPDATE conversations
SET agents = jsonb_build_array(
    jsonb_build_object('id', agent_a_id, 'name', agent_a_name, 'qualification', NULL),
    jsonb_build_object('id', agent_b_id, 'name', agent_b_name, 'qualification', NULL)
)
WHERE agents IS NULL;

COMMENT ON COLUMN conversations.agents IS 'JSONB array of agent profiles: [{id, name, qualification}, ...]';
COMMENT ON COLUMN conversations.prompt_metadata IS 'JSONB object tracking prompt evolution and agent selection metadata';
