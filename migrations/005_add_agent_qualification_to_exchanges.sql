-- Migration 005: Add agent_qualification to exchanges table
--
-- Purpose: Store agent qualifications (e.g., "Physics", "Child Development")
--          so agents can see each other's credentials in conversation context
--
-- Date: 2025-01-XX
-- Author: System

-- Step 1: Add agent_qualification column to exchanges table
ALTER TABLE exchanges
ADD COLUMN IF NOT EXISTS agent_qualification VARCHAR(200);

-- Step 2: Create index for faster queries by agent_qualification
CREATE INDEX IF NOT EXISTS idx_exchanges_agent_qualification
ON exchanges(agent_qualification);

-- Step 3: Add comment for documentation
COMMENT ON COLUMN exchanges.agent_qualification IS
'Agent classification/expertise (e.g., Physics, Child Development, Educational Technology). Displayed in conversation context so agents know each others credentials.';

-- Migration complete
COMMENT ON TABLE exchanges IS
'Stores individual agent messages with turn number, content, tokens, and agent qualification. Updated in migration 005 to add agent_qualification column.';
