# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
