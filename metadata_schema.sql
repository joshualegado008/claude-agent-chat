-- Add metadata storage to existing schema

-- Conversation metadata table (stores rich AI-generated metadata)
CREATE TABLE IF NOT EXISTS conversation_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    snapshot_at_turn INTEGER NOT NULL,

    -- Core metadata
    current_vibe TEXT,
    content_type VARCHAR(50),
    technical_level VARCHAR(50),
    sentiment VARCHAR(50),
    conversation_stage VARCHAR(50),
    complexity_level INTEGER CHECK (complexity_level BETWEEN 1 AND 10),
    engagement_quality VARCHAR(50),

    -- Topics and concepts (arrays)
    main_topics TEXT[] DEFAULT '{}',
    key_concepts TEXT[] DEFAULT '{}',
    emerging_themes TEXT[] DEFAULT '{}',

    -- Named entities (JSONB for flexible structure)
    named_entities JSONB DEFAULT '{"people": [], "organizations": [], "locations": [], "technologies": []}',

    -- Turn insights (JSONB array of turn-level data)
    recent_turn_insights JSONB DEFAULT '[]',

    -- Timestamps
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Prevent duplicate snapshots
    UNIQUE(conversation_id, snapshot_at_turn)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conv_metadata_conversation_id
    ON conversation_metadata(conversation_id);

CREATE INDEX IF NOT EXISTS idx_conv_metadata_turn
    ON conversation_metadata(snapshot_at_turn);

CREATE INDEX IF NOT EXISTS idx_conv_metadata_stage
    ON conversation_metadata(conversation_stage);

CREATE INDEX IF NOT EXISTS idx_conv_metadata_topics
    ON conversation_metadata USING GIN(main_topics);

CREATE INDEX IF NOT EXISTS idx_conv_metadata_entities
    ON conversation_metadata USING GIN(named_entities);

-- View for latest metadata per conversation
CREATE OR REPLACE VIEW conversation_latest_metadata AS
SELECT DISTINCT ON (conversation_id)
    conversation_id,
    snapshot_at_turn,
    current_vibe,
    content_type,
    technical_level,
    sentiment,
    conversation_stage,
    complexity_level,
    engagement_quality,
    main_topics,
    key_concepts,
    emerging_themes,
    named_entities,
    analyzed_at
FROM conversation_metadata
ORDER BY conversation_id, snapshot_at_turn DESC;

-- View for topic frequency across all conversations
CREATE OR REPLACE VIEW topic_frequency AS
SELECT
    unnest(main_topics) as topic,
    COUNT(*) as frequency,
    array_agg(DISTINCT conversation_id) as conversation_ids
FROM conversation_metadata
GROUP BY topic
ORDER BY frequency DESC;

-- View for entity analytics
CREATE OR REPLACE VIEW entity_analytics AS
SELECT
    'people' as entity_type,
    jsonb_array_elements_text(named_entities->'people') as entity_name,
    COUNT(*) as mention_count,
    array_agg(DISTINCT conversation_id) as mentioned_in
FROM conversation_metadata
WHERE jsonb_array_length(named_entities->'people') > 0
GROUP BY entity_name

UNION ALL

SELECT
    'organizations' as entity_type,
    jsonb_array_elements_text(named_entities->'organizations') as entity_name,
    COUNT(*) as mention_count,
    array_agg(DISTINCT conversation_id) as mentioned_in
FROM conversation_metadata
WHERE jsonb_array_length(named_entities->'organizations') > 0
GROUP BY entity_name

UNION ALL

SELECT
    'locations' as entity_type,
    jsonb_array_elements_text(named_entities->'locations') as entity_name,
    COUNT(*) as mention_count,
    array_agg(DISTINCT conversation_id) as mentioned_in
FROM conversation_metadata
WHERE jsonb_array_length(named_entities->'locations') > 0
GROUP BY entity_name

UNION ALL

SELECT
    'technologies' as entity_type,
    jsonb_array_elements_text(named_entities->'technologies') as entity_name,
    COUNT(*) as mention_count,
    array_agg(DISTINCT conversation_id) as mentioned_in
FROM conversation_metadata
WHERE jsonb_array_length(named_entities->'technologies') > 0
GROUP BY entity_name

ORDER BY mention_count DESC;

-- Function to get conversation evolution
CREATE OR REPLACE FUNCTION get_conversation_evolution(conv_id UUID)
RETURNS TABLE (
    turn_number INTEGER,
    stage VARCHAR(50),
    complexity INTEGER,
    main_topic TEXT,
    analyzed_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        snapshot_at_turn,
        conversation_stage,
        complexity_level,
        main_topics[1] as main_topic,
        cm.analyzed_at
    FROM conversation_metadata cm
    WHERE conversation_id = conv_id
    ORDER BY snapshot_at_turn;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON conversation_metadata TO agent_user;
GRANT SELECT ON conversation_latest_metadata TO agent_user;
GRANT SELECT ON topic_frequency TO agent_user;
GRANT SELECT ON entity_analytics TO agent_user;
