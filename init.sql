-- Database initialization script for agent conversations

-- Conversations table: stores metadata about each conversation
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    initial_prompt TEXT NOT NULL,
    agent_a_id VARCHAR(50) NOT NULL,
    agent_a_name VARCHAR(100) NOT NULL,
    agent_b_id VARCHAR(50) NOT NULL,
    agent_b_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_turns INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active', -- active, completed, archived
    tags TEXT[] DEFAULT '{}',

    -- Indexes for common queries
    CONSTRAINT valid_status CHECK (status IN ('active', 'completed', 'archived'))
);

-- Exchanges table: stores individual agent messages
CREATE TABLE IF NOT EXISTS exchanges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    thinking_content TEXT,  -- Extended thinking (if enabled)
    response_content TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Composite index for efficient conversation retrieval
    UNIQUE(conversation_id, turn_number)
);

-- Conversation context snapshots (for resuming conversations)
CREATE TABLE IF NOT EXISTS context_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    snapshot_at_turn INTEGER NOT NULL,
    context_data JSONB NOT NULL,  -- Stores full context object
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(conversation_id, snapshot_at_turn)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_tags ON conversations USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_exchanges_conversation_id ON exchanges(conversation_id);
CREATE INDEX IF NOT EXISTS idx_exchanges_turn_number ON exchanges(turn_number);
CREATE INDEX IF NOT EXISTS idx_context_snapshots_conversation_id ON context_snapshots(conversation_id);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on conversations
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for conversation summaries
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

-- Sample data for testing (optional - comment out for production)
-- INSERT INTO conversations (title, initial_prompt, agent_a_id, agent_a_name, agent_b_id, agent_b_name, total_turns, total_tokens, status)
-- VALUES
--     ('Test Conversation', 'What do you think about AI?', 'agent_a', 'Nova', 'agent_b', 'Atlas', 5, 1250, 'completed');

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agent_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agent_user;
