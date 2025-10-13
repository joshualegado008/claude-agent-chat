-- Migration: Add 'paused' status to conversations
-- Date: 2025-10-13
-- Description: Adds 'paused' as a valid status for conversations to distinguish
--              between actively running, paused (can resume), and completed conversations.

-- Drop the existing constraint
ALTER TABLE conversations DROP CONSTRAINT IF EXISTS valid_status;

-- Add the new constraint with 'paused' included
ALTER TABLE conversations ADD CONSTRAINT valid_status
    CHECK (status IN ('active', 'paused', 'completed', 'archived'));

-- Note: No data migration needed. Existing 'active' conversations remain 'active'
-- and will be automatically updated to 'paused' when users pause them.
