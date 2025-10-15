-- Migration 005: Add conversation summaries table
--
-- This migration adds support for AI-generated conversation summaries
-- (Post-Conversation Intelligence Reports) using GPT-4o-mini.
--
-- Features:
-- - Comprehensive summary storage (TL;DR, executive summary, insights, etc.)
-- - Cost and token tracking for summary generation
-- - Performance metrics (generation time)
-- - Only for completed conversations

-- Create ai_summaries table (renamed from conversation_summaries to avoid conflict with existing view)
CREATE TABLE IF NOT EXISTS ai_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Summary data (full JSON structure from ConversationSummarizer)
    summary_data JSONB NOT NULL,

    -- Generation metadata
    generation_model VARCHAR(50) NOT NULL DEFAULT 'gpt-4o-mini',
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    generation_cost NUMERIC(10, 6) NOT NULL DEFAULT 0.0,
    generation_time_ms INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Ensure one summary per conversation
    UNIQUE(conversation_id)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_ai_summaries_conversation_id ON ai_summaries(conversation_id);
CREATE INDEX IF NOT EXISTS idx_ai_summaries_generated_at ON ai_summaries(generated_at DESC);

-- GIN index for JSONB searching (allows querying within summary data)
CREATE INDEX IF NOT EXISTS idx_ai_summaries_data ON ai_summaries USING GIN(summary_data);

-- Grant permissions
GRANT ALL PRIVILEGES ON ai_summaries TO agent_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agent_user;

-- Comment on table
COMMENT ON TABLE ai_summaries IS 'AI-generated comprehensive summaries for completed conversations using GPT-4o-mini';
COMMENT ON COLUMN ai_summaries.summary_data IS 'Full JSON structure: tldr, executive_summary, key_insights, technical_glossary, vocabulary_highlights, agent_contributions, collaboration_dynamics, named_entities, learning_outcomes';
COMMENT ON COLUMN ai_summaries.generation_cost IS 'Cost in USD to generate the summary using GPT-4o-mini';
