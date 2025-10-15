# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [0.7.0] - 2025-10-15

### Added

#### 📊 Post-Conversation Intelligence Report (AI-Generated Summaries)

- **Automatic summary generation**: Comprehensive conversation summaries automatically generated when conversations complete using GPT-4o-mini
- **TL;DR section**: Ultra-brief 1-2 sentence summary prominently displayed at the top
- **Executive Summary**: One-paragraph comprehensive overview of main topics and conclusions
- **Key Insights & Emergent Ideas**: Novel concepts and breakthrough ideas that arose organically during discussion (not in initial prompt)
- **Technical Glossary**: Scientific, medical, and technical terms with definitions, pronunciation guides, and difficulty levels (beginner/intermediate/advanced)
- **Vocabulary Highlights**: Interesting words for vocabulary enrichment with etymology, usage examples, and educational value
- **Agent Contribution Analysis**: Per-agent breakdown showing:
  - Key concepts introduced by each agent
  - Technical terms used
  - Novel insights generated
  - Turn count and engagement level (high/medium/low)
  - Communication style analysis
- **Collaboration Dynamics**: Interaction pattern analysis including:
  - Overall quality and interaction pattern (agreement/debate/synthesis/exploration)
  - Most collaborative agent identification
  - Points of convergence and divergence
  - Collaborative highlights with turn ranges
- **Named Entities & References**: Extraction of people, organizations, locations, publications, and URLs mentioned
- **Learning Outcomes**: What readers can learn from the conversation
- **Generation Metadata**: Complete transparency showing:
  - Model used (GPT-4o-mini)
  - Tokens used (input/output breakdown)
  - Generation cost in USD
  - Processing time
  - Combined cost (conversation + summary)
- **Beautiful React UI**: Collapsible sections with icons for easy navigation through all summary components
- **API endpoint**: `GET /api/conversations/{id}/summary` for retrieving generated summaries
- **Summary indicators**: Conversations with summaries show visual indicators on the main page
- **Cost-efficient**: Uses GPT-4o-mini (~$0.0001-$0.001 per summary) instead of expensive models

**Files Added**:
- `conversation_summarizer.py`: Core ConversationSummarizer class using GPT-4o-mini
- `migrations/005_add_conversation_summaries.sql`: Database migration for conversation_summaries table
- `run_migration_005.py`: Migration runner script with verification
- `web/frontend/components/ConversationSummary.tsx`: Comprehensive React component with collapsible sections

**Files Modified (Backend)**:
- `db_manager.py`: Added `save_conversation_summary()`, `get_conversation_summary()`, and `conversation_has_summary()` methods
- `web/backend/bridge.py`: Integrated ConversationSummarizer with OpenAI key validation
- `web/backend/websocket_handler.py`: Added `_generate_summary()` method called automatically on conversation completion
- `web/backend/api.py`:
  - Added `GET /api/conversations/{id}/summary` endpoint
  - Updated `GET /api/conversations` to include `has_summary` indicator

**Files Modified (Frontend)**:
- `web/frontend/types/index.ts`: Added comprehensive summary type definitions (KeyInsight, TechnicalTerm, VocabularyHighlight, AgentContribution, CollaborationDynamics, etc.)
- Updated WebSocket message types to include summary-related events (summary_generation_start, summary_generated, summary_error, summary_unavailable)
- Added `has_summary` field to Conversation interface

**Database Schema**:
```sql
CREATE TABLE conversation_summaries (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    summary_data JSONB NOT NULL,
    generation_model VARCHAR(50) NOT NULL DEFAULT 'gpt-4o-mini',
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    generation_cost NUMERIC(10, 6) NOT NULL,
    generation_time_ms INTEGER NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(conversation_id)
);
```

**Summary Structure (JSON)**:
```json
{
  "tldr": "Brief 1-2 sentence summary",
  "executive_summary": "Comprehensive paragraph",
  "key_insights": [{
    "insight": "Novel concept",
    "significance": "Why important",
    "emerged_at_turn": 5
  }],
  "technical_glossary": [{
    "term": "Scientific term",
    "definition": "Clear definition",
    "pronunciation": "phonetic guide",
    "context": "How it was used",
    "difficulty": "intermediate"
  }],
  "vocabulary_highlights": [{
    "word": "Interesting word",
    "definition": "Definition",
    "pronunciation": "guide",
    "usage_example": "Example from conversation",
    "why_interesting": "Etymology or rarity"
  }],
  "agent_contributions": [...],
  "collaboration_dynamics": {...},
  "named_entities": {...},
  "learning_outcomes": [...],
  "generation_metadata": {...}
}
```

**Benefits**:
- **Educational value**: Vocabulary highlights and learning outcomes enhance knowledge retention
- **Quick review**: TL;DR and executive summary enable rapid understanding
- **Research utility**: Technical glossary and named entities aid in reference and citation
- **Agent performance**: Contribution analysis shows which agents provided the most value
- **Cost transparency**: Full breakdown of token usage and costs for both conversation and summary
- **Accessible**: Pronunciation guides make complex terms approachable
- **Exportable**: JSON format enables future export to PDF, Markdown, or other formats

**Example Use Cases**:
- **Academic research**: Quickly extract key concepts, technical terms, and references from multi-agent discussions
- **Learning & Education**: Vocabulary highlights and learning outcomes enhance educational value
- **Professional insights**: Executive summaries for sharing conversation outcomes with colleagues
- **Performance tracking**: Agent contribution analysis for understanding which agents excel at what
- **Knowledge management**: Named entities and references for building knowledge graphs

**Performance**:
- Generation time: 5-15 seconds depending on conversation length
- Cost: $0.0001-$0.001 per summary (GPT-4o-mini pricing)
- Token usage: Typically 1000-3000 tokens for input + 800-2000 tokens for output

**Future Enhancements** (not in this release):
- Frontend integration: "View Summary" button on conversation pages
- Main page indicators: Visual badges for conversations with summaries
- PDF export of summaries
- Bulk summary generation for past conversations
- Summary search/filter on main page

---

## [0.6.0] - 2025-10-15

### Added

#### 🔄 Multi-Agent Conversations (3+ Agents)

- **N-agent support**: Conversations now support 3+ agents instead of being limited to 2
- **Round-robin turn-taking**: Agents rotate through all N participants in order (e.g., Agent1 → Agent2 → Agent3 → Agent1...)
- **Database migration**: Added `agents` JSONB column to store array of participating agents
- **Backward compatibility**: Legacy 2-agent conversations still fully supported via `agent_a/agent_b` columns
- **Dynamic agent selection**: Frontend UI now accepts and displays all selected agents (no 2-agent limit)
- **Multi-agent display**: Conversation headers show all agents with qualifications (e.g., "Agent1 - Title ↔ Agent2 - Title ↔ Agent3 - Title")
- **WebSocket round-robin**: Updated turn logic from `turn % 2` to `turn % len(agents)` for N-agent rotation
- **Agent metadata storage**: Each agent stored with `{id, name, qualification}` in JSONB array

**Files Added**:
- `migrations/004_support_multi_agents.sql`: Database migration adding agents JSONB column
- `run_migration_004.py`: Migration script with verification
- `run_migration_004_simple.py`: Simplified migration runner

**Files Modified (Backend)**:
- `db_manager.py`: Updated `create_conversation()` to accept optional `agents: List[Dict]` parameter
- `conversation_manager_persistent.py`: Updated `start_new_conversation()` and `load_conversation()` for multi-agent format
- `web/backend/api.py`:
  - POST `/api/conversations`: Now accepts all agents from `request.agent_ids` (not just first 2)
  - GET `/api/conversations/{id}`: Returns `agents` array alongside legacy `agent_a/agent_b` fields
- `web/backend/websocket_handler.py`:
  - Loads all agents from conversation metadata
  - Round-robin turn-taking: `current_agent_idx = (current_agent_idx + 1) % len(self.agents)`

**Files Modified (Frontend)**:
- `web/frontend/components/AgentSelector.tsx`: Removed 2-agent validation, approve button works for N agents
- `web/frontend/app/conversation/[id]/page.tsx`: Dynamic agent display supporting N agents
- `web/frontend/types/index.ts`: Added `AgentInfo` interface, updated `Conversation` type with optional `agents` array

**Migration Strategy**:
- **Non-breaking**: Adds `agents` JSONB column while preserving `agent_a_id`, `agent_a_name`, `agent_b_id`, `agent_b_name`
- **Data migration**: Existing 2-agent conversations automatically migrated to new format
- **Dual format support**: New conversations use `agents` array, old conversations use legacy columns
- **Zero downtime**: Migration runs while conversations continue

**Benefits**:
- Richer multi-perspective discussions with 3+ expert agents
- More comprehensive coverage of complex topics requiring diverse expertise
- Natural extension of dynamic agent selection (which already creates 3+ agents)
- Flexible conversation structures (2-way, 3-way, 4-way, etc.)
- Round-robin ensures all agents participate equally

**Example Use Cases**:
- Religious topic: Theologian + Historian + Ethicist (3 agents)
- Healthcare topic: Doctor + Researcher + Policy Expert (3 agents)
- Technology topic: Engineer + Designer + Product Manager + Ethicist (4 agents)

---

## [0.5.0] - 2025-10-14

### Added

#### 👥 Agent Roster & Management

- **Agent roster browsing**: New "View Agent Roster" option (Settings menu #7) for browsing all 41 dynamic agents
- **Paginated agent list**: Display 20 agents per page with comprehensive information (name, domain, rank, rating, uses, last used)
- **Agent filtering**: Filter agents by domain (Medicine, Law, Humanities, Technology, Business, Science, Arts)
- **Multiple sort options**: Sort by Rating, Uses, Last Used, Name, or Rank
- **Search functionality**: Search agents by name or expertise keywords
- **Detailed agent profiles**: View complete agent information including:
  - Basic info (name, ID, domain, classification, specialization)
  - Performance statistics (total uses, average/best/worst ratings, costs)
  - Core skills and keywords
  - Recent rating history with detailed scores
  - System prompt preview (200 chars) with option to view full prompt
- **Statistics dashboard**: New "Agent Statistics" option (Settings menu #8) showing:
  - System overview (total agents, active count, conversations, avg rating, total cost)
  - Top performers by rating (top 5)
  - Most used agents (top 5)
  - Agents by rank distribution (NOVICE through GOD_TIER)
  - Agents by domain distribution
  - Activity metrics (created today, used today, inactive counts with tier indicators)
- **Interactive navigation**: Full keyboard-driven interface with commands for filtering, searching, sorting, and viewing details
- **Agent tier indicators**: Visual status indicators (🟢 HOT, 🟡 WARM, 🔵 COLD) based on last usage
- **Color-coded ranks**: Emoji icons for easy rank identification (📗 NOVICE, 📘 COMPETENT, 📙 EXPERT, 📕 MASTER, 🔮 LEGENDARY, ⭐ GOD_TIER)

**Files Added**:
- `agent_roster.py`: Complete AgentRoster class with list view, detail view, and statistics dashboard

**Files Modified**:
- `menu.py`: Added options 7 & 8 to Settings menu, added `_handle_agent_roster()`, `_choose_domain_filter()`, `_choose_sort_option()`, and `_view_full_prompt()` methods
- `docs/AGENT_ROSTER_FEATURE.md`: Updated status to "✅ Implemented"

**Benefits**:
- Users can now browse and inspect all agents without starting conversations
- Easy discovery of specialized agents for specific topics
- Performance tracking visibility encourages agent quality
- Helps identify underutilized or high-performing agents
- Complete transparency into the dynamic multi-agent system

---

## [0.4.2] - 2025-10-14

### Fixed

- **Duplicate agent file cleanup**: Removed 67 duplicate agent files (`.md`) and 8 duplicate metadata files (`.json`) that were created before the name uniqueness fix in v0.4.1
- **Misleading startup message**: Fixed agent loading message to accurately show unique agent count vs total files, preventing confusion when duplicates exist

### Changed

- **Agent loading message**: Updated `agent_factory.py:_load_existing_names()` to display:
  - `📝 Loaded {N} existing agents` when all files are unique
  - `📝 Loaded {N} unique agents ({total} files, {duplicates} duplicates detected)` when duplicates exist

### Added

- **Cleanup script**: Added `cleanup_duplicate_agents.py` with dry-run mode for safe duplicate removal
- **Backup system**: Created timestamped backups in `backup/agents-YYYYMMDD-HHMMSS/` before cleanup operations
- **Cleanup report**: Detailed report showing which duplicates will be deleted, grouped by agent name

### Performance

- **Faster startup**: Reduced agent file count from 108 to 41 files (62% reduction)
- **Disk space**: Freed up storage by removing 67 redundant `.md` files and 8 redundant `.json` files
- **Cleaner data**: All remaining 41 agents now have unique names with no duplicates

---

## [0.4.1] - 2025-10-13

### Fixed

#### 🐛 Bug #1: Classification Fallback to Cardiology
- **Root cause**: Non-medical topics were incorrectly defaulting to "Cardiology" due to poor keyword ordering and fallback logic
- **Symptoms**: Mandarin language teaching classified as Cardiology instead of Linguistics, cultural topics misclassified
- **Fixes applied**:
  - Expanded taxonomy from 20 to 22 classes (added Psychology and Education to HUMANITIES domain)
  - Reordered keyword matching to check specific terms before generic ones (e.g., "machine learning" before "learning", "language teaching" before "teaching")
  - Added comprehensive debug logging showing classification decisions with emoji indicators
  - Added API-based classification fallback using Claude for ambiguous cases
  - Added context-aware checks to distinguish between similar keywords (e.g., language teaching vs general teaching)
  - Medicine classification now requires explicit medical keywords, not just domain proximity
- **Test results**: ✅ 14/14 classification tests passed
- **Impact**: Mandarin/Chinese topics now correctly classify as Linguistics, cultural topics as Cultural Studies, no more Cardiology false positives

#### 🐛 Bug #2: Name Race Condition (Duplicate Agent Names)
- **Root cause**: Async race condition during concurrent agent creation - multiple agents checked `used_names` before any registered their names
- **Symptoms**: Duplicate names like "Dr. Mei-Ling Chen" appearing for different agents during concurrent creation
- **Fixes applied**:
  - Added `asyncio.Lock` (`_name_lock`) to protect `used_names` set during name checking and registration
  - Added `used_names: Set[str]` attribute to track all agent names in memory
  - Added `_load_existing_names()` method to scan disk and load existing agent names at factory initialization
  - Added retry logic (up to 3 attempts) with updated prompts listing recently-used names to avoid
  - Added fallback numbering if all retries fail (e.g., "Dr. Smith 2", "Dr. Smith 3")
  - Wrapped name uniqueness check in `async with self._name_lock:` to ensure atomic check-and-register
- **Test results**: ✅ All tests passed - 5 agents created concurrently with 0 duplicates, retry logic successfully regenerated 2 duplicate names
- **Impact**: Guarantees unique agent names even during high-concurrency scenarios

### Changed

- **Agent taxonomy**: Now 22 classes instead of 20 (added Psychology and Education to HUMANITIES)
- **Classification logging**: Added comprehensive debug output showing keyword matches, confidence scores, and decision paths
- **Classification priority**: Reordered checks so specific terms (machine learning, bilingual, language teaching) match before generic terms (learning, teaching)
- **Agent factory imports**: Added `asyncio` import for async lock support

### Added

- **Test suites**: Added `test_classification_fix.py` (14 test cases) and `test_name_uniqueness_fix.py` (concurrent creation testing)
- **Classification fallback**: API-based classification using Claude for ambiguous cases when keyword confidence < 0.3
- **Name loading**: Factory now loads existing agent names from disk at initialization to prevent duplicates across sessions

---

## [0.4.0] - 2025-10-13

### Added

#### 🤖 Dynamic Multi-Agent System (Phase 1E)
- **On-demand agent creation**: System analyzes conversation topic and creates specialized expert agents dynamically
- **Agent deduplication**: Prevents creation of duplicate agents with similar expertise (85-95% similarity threshold)
- **Topic analysis**: GPT-4o-mini integration for intelligent topic extraction and refinement
- **Agent taxonomy**: Hierarchical classification system (domain → classification → skills)
- **5-dimension rating system**: Rate agents on helpfulness (30%), accuracy (25%), relevance (20%), clarity (15%), collaboration (10%)
- **6-rank promotion system**:
  - 📗 NOVICE (0-9 points)
  - 📘 COMPETENT (10-24 points)
  - 📙 EXPERT (25-49 points)
  - 📕 MASTER (50-99 points)
  - 🔮 LEGENDARY (100-199 points)
  - ⭐ GOD_TIER (200+ points) - Never retired!
- **Lifecycle management**: HOT (active) → WARM (7 days) → COLD (90 days) → ARCHIVED (180 days) → RETIRED states
- **Leaderboard system**: Track top-performing agents across all conversations
- **Agent persistence**: JSON-based storage for agents, ratings, performance history, and leaderboard
- **Agent prompt generation**: Dynamic creation of system prompts with personality, expertise, and conversation style
- **Cost tracking**: Monitor API costs for agent creation ($0.013-$0.015 per agent)
- **AgentCoordinator class**: Central orchestration for dynamic agent lifecycle (`src/agent_coordinator.py`)
- **AgentFactory**: Template-based agent generation with Claude API (`src/agent_factory.py`)
- **DynamicAgentRegistry**: Agent storage and retrieval system (`src/dynamic_agent_registry.py`)
- **PerformanceTracker**: Rating history and analytics (`src/performance_tracker.py`)
- **AgentLifecycleManager**: Tier management and retirement logic (`src/agent_lifecycle.py`)
- **AgentDeduplicator**: Similarity detection and duplicate prevention (`src/agent_deduplicator.py`)

#### 📊 Post-Conversation Rating Flow
- **Interactive rating prompt**: Rate each agent after conversation completes
- **Promotion notifications**: Celebrate when agents level up ranks
- **Performance dashboard**: Display agent statistics, ranks, and scores
- **Rating persistence**: Store all ratings with timestamps and conversation context
- **Weighted scoring**: Configurable weights for different rating dimensions

#### 🎯 Integration with coordinator_with_memory.py
- **Seamless integration**: Drop-in replacement for static Nova/Atlas agents
- **Fallback mode**: Automatically reverts to static agents if dynamic system fails
- **Database compatibility**: Works with PostgreSQL and Qdrant persistence
- **All features preserved**: User injection, tool visibility, state management, metadata extraction
- **Enhanced topic analysis**: Uses OpenAI for better agent selection

### Fixed

#### 🔑 OpenAI API Key Three-Way Sync
- **Root cause**: Settings menu only updated `settings.json`, not `.env` file
- **Fix**: Added `_update_env_file()` method to `settings_manager.py`
- **Three-way updates**: Now syncs `settings.json`, `.env` file, AND process environment
- **Methods updated**: `set_openai_api_key()` and `set_anthropic_api_key()`
- **Impact**: API key updates now take effect immediately after restart

#### 🤖 Agent Prompt Lazy-Loading
- **Root cause**: AgentRunner only loaded prompts for agents in `config.yaml` at initialization
- **Fix**: Added lazy-loading logic in `send_message_streaming()` and `send_message_to_agent()`
- **Behavior**: Dynamic agents now load prompts on-demand from disk and cache them
- **Impact**: Dynamic agents can now run without pre-configuration

#### ⚙️ Extended Thinking Token Limits
- **Root cause**: Default `max_tokens=2048` was less than `thinking_budget=5000`
- **Error**: "max_tokens must be greater than thinking.budget_tokens"
- **Fix**: Changed default from 2048 to 8000 in both `send_message_to_agent()` and `send_message_streaming()`
- **Impact**: Extended thinking now works correctly for dynamic agents

### Changed

- **Agent file structure**: Dynamic agents stored in `.claude/agents/dynamic/` subdirectory
- **Agent ID format**: Dynamic agents use `dynamic/<hash>` pattern (e.g., `dynamic/dynamic-a551f2bec1c4`)
- **Path extraction**: Fixed agent ID extraction to preserve subdirectory structure
- **Settings validation**: Enhanced API key validation with test calls
- **Configuration**: Added Phase 1E settings to `config.yaml` (openai, agent_factory, agent_lifecycle, rating, taxonomy)

### Documentation

- **INTEGRATION_COMPLETE.md**: Comprehensive Phase 1E integration guide with usage examples, data storage, and testing recommendations
- **Test suites**: Added `test_phase_1a.py`, `test_phase_1b.py`, `test_phase_1c.py` for Phase 1 validation
- **Examples**: Added example configurations in `examples/` directory
- **README updates**: Phase 1E feature documentation (below)

---

## [0.3.0] - 2025-10-13

### Added

#### 💬 User Content Injection
- **Mid-conversation injection**: Pause conversations and inject custom user content (terminal and web)
- **Interactive prompt**: Multi-line text input with URL detection
- **WebSocket integration**: Real-time injection in web interface via `InjectContentModal.tsx`
- **Database persistence**: User injections stored as special USER exchanges
- **Context highlighting**: Injected content prominently displayed in conversation context

#### 🔧 Tool Use Visibility
- **Web browsing display**: Show when agents use fetch_url tool to browse websites
- **Tool use events**: Backend forwards tool_use events to frontend for real-time display
- **Expandable UI**: `ToolUseMessage.tsx` component with collapsible details
- **URL highlighting**: Automatically detect and display fetched URLs

#### 📊 Conversation State Management
- **Four-state system**: Active, Paused, Completed, Archived status tracking
- **Pause vs Stop**: Clear distinction between temporary pause (resumable) and permanent completion
- **Database migration**: Added 'paused' status to conversation schema (`migrations/002_add_paused_status.sql`)
- **Smart cleanup logic**: WebSocket disconnect handling with priority-based status determination
- **State documentation**: Comprehensive `CONVERSATION_STATES.md` with lifecycle diagrams and testing scenarios

#### 🌐 Enhanced Web Interface
- **Inject button**: Available when conversation is paused
- **Tool use cards**: Purple bordered cards showing agent web browsing activity
- **State badges**: Color-coded status badges (green/blue/yellow) on homepage
- **Resume messaging**: "This conversation is paused" with resume button
- **Clean UI**: Removed emojis from status badges for professional appearance

#### 🔧 Geeky Technical Stats Mode
- **Comprehensive token breakdown display** showing input (context + prompt), output, and thinking tokens separately
- **Context window analysis** displaying total exchanges, window size, character/token counts, and which turns are referenced
- **Session analytics** with current turn, total tokens, average per turn, and projected totals
- **Model configuration details** including model name, temperature, and max tokens settings
- **Configurable display modes** via `config.yaml`:
  - `simple`: Basic token count and cost (default)
  - `detailed`: Adds model info and session stats (future)
  - `geeky`: Full technical breakdown with all internals visible
- **Real-time cost tracking** with per-component cost breakdowns

#### 📁 Unified Conversation Management
- **Consolidated menu option** for viewing, continuing, and deleting conversations
- **Enhanced UX flow**: Select conversation → View preview → Choose action (view full/continue/delete)
- **Simplified main menu** from 7 options to 6 options
- **Interactive submenu** with clear action choices

#### 💾 Database & Persistence Improvements
- **PostgreSQL + Qdrant integration** for conversation storage and semantic search
- **Metadata extraction** with AI-powered conversation analysis
- **Context snapshots** for resuming conversations
- **Rich contextual intelligence** with optional OpenAI integration
- **Database migration support** for existing installations
- **Docker Compose setup** for easy database deployment

### Fixed

- **Qdrant deletion errors**: Fixed vector database cleanup by using proper `PointIdsList` instead of plain dict
- **Missing metadata table handling**: Added graceful fallback when `conversation_metadata` table doesn't exist
- **Database initialization**: Metadata schema now automatically included in docker-compose setup
- **Import reliability**: Enhanced agent_runner to return complete model metadata including thinking tokens
- **Database connection issues**: Fixed stale connections after docker-compose restart
- **API 500 errors**: Resolved by restarting web server after database restart

### Changed

- **Enhanced token_info structure**: Now includes `thinking_tokens`, `model_name`, `temperature`, and `max_tokens`
- **Context analysis**: Coordinator now calculates and tracks context window statistics in real-time
- **Configuration loading**: Main coordinator loads full config.yaml for access to all settings
- **Stats display logic**: Conditionally shows simple vs geeky stats based on config setting
- **WebSocket handler**: Added pause/resume/stop/inject command support
- **Conversation page**: Enhanced with injection support and tool use display
- **ConversationControls**: Added inject button for paused conversations
- **Homepage badges**: Simplified to show status without emojis

### Documentation

- **CONVERSATION_STATES.md**: Comprehensive state lifecycle documentation with diagrams, UI specs, and testing scenarios
- **SETUP_DATABASE.md**: Added comprehensive migration guide for existing databases
- **CHANGELOG.md**: Created to track version history
- **README.md**: Updated with new features (injection, tool visibility, state management) and file structure
- **Code comments**: Enhanced inline documentation for technical stats methods

---

## [0.2.0] - 2024-10-12

### Added
- Extended thinking display feature
- Real-time streaming responses
- Token usage tracking with costs
- Cost calculator module
- Settings management system
- Interactive menu system

### Changed
- Migrated from subprocess to direct Anthropic API usage
- Enhanced display formatter with streaming support
- Improved agent runner architecture

---

## [0.1.0] - 2024-10-11

### Added
- Initial release
- Basic two-agent conversation system
- Context management with checkpoints
- Agent personality system (Nova & Atlas)
- Configuration via YAML
- JSON and Markdown logging
- Color-coded terminal display

---

## Notes

### Version Numbering
- **Major (X.0.0)**: Breaking changes or major feature additions
- **Minor (0.X.0)**: New features, backward compatible
- **Patch (0.0.X)**: Bug fixes and minor improvements

### Contributing
When adding entries:
- Place new changes under `[Unreleased]`
- Use categories: Added, Changed, Deprecated, Removed, Fixed, Security
- Include clear descriptions of what changed and why
- Link to relevant issue numbers or PRs when available
