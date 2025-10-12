# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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

### Changed

- **Enhanced token_info structure**: Now includes `thinking_tokens`, `model_name`, `temperature`, and `max_tokens`
- **Context analysis**: Coordinator now calculates and tracks context window statistics in real-time
- **Configuration loading**: Main coordinator loads full config.yaml for access to all settings
- **Stats display logic**: Conditionally shows simple vs geeky stats based on config setting

### Documentation

- **SETUP_DATABASE.md**: Added comprehensive migration guide for existing databases
- **CHANGELOG.md**: Created to track version history
- **README.md**: Updated with new features and configuration options
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
