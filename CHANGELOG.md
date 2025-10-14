# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
