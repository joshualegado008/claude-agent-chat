-- Fix conversation status for conversations that exceeded max_turns
-- This script updates conversations that are marked as 'active' but have
-- reached or exceeded the 20-turn limit

-- Show conversations that will be updated
SELECT
    id,
    title,
    total_turns,
    status,
    updated_at
FROM conversations
WHERE total_turns >= 20 AND status = 'active';

-- Update status to 'completed' for conversations at or past max_turns
UPDATE conversations
SET
    status = 'completed',
    updated_at = CURRENT_TIMESTAMP
WHERE
    total_turns >= 20
    AND status = 'active';

-- Show updated conversations
SELECT
    id,
    title,
    total_turns,
    status,
    updated_at
FROM conversations
WHERE total_turns >= 20;

-- Summary
SELECT
    status,
    COUNT(*) as count,
    MIN(total_turns) as min_turns,
    MAX(total_turns) as max_turns,
    AVG(total_turns) as avg_turns
FROM conversations
GROUP BY status
ORDER BY status;
