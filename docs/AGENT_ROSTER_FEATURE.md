# Agent Roster & Management Feature Specification

**Status**: Not Implemented
**Priority**: Medium
**Target Version**: 0.5.0
**Created**: 2025-10-14

## Overview

Add a comprehensive agent viewing and management interface to the Settings menu, allowing users to browse, inspect, and manage their dynamic agent roster. Currently, agent information is only visible during conversations or after completion, but users have no way to browse all available agents.

## Current State

### What Exists (Backend)

**Data Storage**:
- `.claude/agents/dynamic/*.md` - Agent prompts/personalities (41 files after v0.4.2 cleanup)
- `data/agents/*.json` - Agent metadata (classification, skills, keywords, embeddings)
- `data/performance/*.json` - Performance profiles (ratings, usage history, ranks)

**Backend Methods Available**:

From `src/persistence.py` (DataStore):
```python
def load_all_agents(self) -> Dict[str, AgentProfile]
def get_all_agent_ids(self) -> List[str]
def get_agent_count(self) -> int
def load_all_performance_profiles(self) -> Dict
```

From `src/agent_coordinator.py` (AgentCoordinator):
```python
def get_leaderboard(self, top_n: int = 10) -> List
def get_statistics(self) -> Dict
```

**Where Agent Info IS Currently Shown**:
- **After conversation completion** (`coordinator_with_memory.py:764-806`):
  ```
  📊 PERFORMANCE EVALUATION
  [Interactive rating for each agent]

  🏆 Top Performing Agents
  [Leaderboard with top 10]

  📈 System Statistics:
    • Total Agents: 41
    • Total Conversations: X
    • Average Rating: 4.5/5.00
    • Total System Cost: $X.XX

  📊 Agents by Rank:
    NOVICE: 5
    COMPETENT: 10
    EXPERT: 15
    ...
  ```

### What's Missing

**Current Settings Menu** (`menu.py:268-305`):
```
⚙️  Settings
  1. 🔑 Configure API Keys
  2. 🤖 Select Models for Agents
  3. 🎨 Customize Display Colors
  4. 👁️  View Current Configuration
  5. 🧪 Test API Connections
  6. 🔧 Run Setup Wizard
  7. ◀️  Back to Main Menu
```

**No way to**:
- View all available agents
- Inspect individual agent details
- Search agents by expertise/domain
- See agent performance history
- Manage agent lifecycle (retire, export, etc.)

## Feature Requirements

### 1. Agent List View

**Menu Option**: `8. 👥 View Agent Roster`

**Display**:
```
================================================================================
👥 AGENT ROSTER (41 Agents)
================================================================================

Filter: [All Domains ▼] | Sort: [By Rating ▼] | Search: [___________]

#  Name                      Domain        Rank        Rating  Uses  Last Used
────────────────────────────────────────────────────────────────────────────────
1  Prof. Rebecca Hartfield   Law           COMPETENT   4.2/5   3     2025-10-14
2  Dr. Mei-Ling Chen          Humanities    EXPERT      4.8/5   8     2025-10-14
3  Dr. Michael Thompson       Medicine      MASTER      4.9/5   12    2025-10-13
4  Alex Chen                  Technology    NOVICE      3.5/5   1     2025-10-12
...

[Enter #] View Details | [f] Filter | [s] Search | [b] Back
```

**Features**:
- Pagination (show 20 per page)
- Filter by domain (Medicine, Law, Humanities, Technology, etc.)
- Sort by: Rating, Uses, Last Used, Name, Rank
- Search by name or expertise keywords
- Color-coded ranks (📗 NOVICE, 📘 COMPETENT, 📙 EXPERT, 📕 MASTER, 🔮 LEGENDARY, ⭐ GOD_TIER)

### 2. Agent Detail View

**Display** (when user selects an agent):
```
================================================================================
👤 AGENT PROFILE
================================================================================

Name:          Prof. Rebecca Hartfield
Agent ID:      dynamic-f7d8de1192f8
Domain:        ⚖️  Law
Classification: Constitutional Law
Specialization: Constitutional Law (First Amendment rights)
Rank:          📘 COMPETENT (18 points)
Status:        🟢 HOT (Active)

Core Skills:
  • First Amendment jurisprudence analysis
  • Establishment Clause interpretation
  • Religious freedom litigation strategy
  • Constitutional doctrine application
  • Separation of church and state advocacy

Keywords:
  public education, establishment clause, free exercise, constitutional rights,
  viewpoint neutrality, religious liberty, secular purpose, lemon test

📊 Performance Statistics:
  Total Uses:        3 conversations
  Average Rating:    4.2/5.0
  Best Rating:       5.0/5.0
  Creation Cost:     $0.0128
  Total Cost:        $0.0456
  Created:           2025-10-14 07:30
  Last Used:         2025-10-14 08:15

📈 Rating History:
  Conv #1 (2025-10-14): ⭐⭐⭐⭐⭐ 5.0 (Helpfulness: 5, Accuracy: 5, ...)
  Conv #2 (2025-10-14): ⭐⭐⭐⭐   4.0 (Helpfulness: 4, Accuracy: 4, ...)
  Conv #3 (2025-10-14): ⭐⭐⭐⭐   3.5 (Helpfulness: 3, Accuracy: 4, ...)

🔍 Conversations:
  #1: "Religious texts in public school classrooms" (5 turns, completed)
  #2: "First Amendment rights in education" (8 turns, completed)
  #3: "Church-state separation policy" (3 turns, paused)

📝 System Prompt Preview:
  You are Professor Rebecca Hartfield, a distinguished constitutional law
  expert specializing in First Amendment jurisprudence. With decades of
  experience analyzing landmark Supreme Court cases...
  [Full prompt: 387 words]

Actions:
  [v] View Full Prompt | [h] Rating History | [c] Conversations | [b] Back
================================================================================
```

### 3. Statistics Dashboard

**Additional option**: `9. 📊 Agent Statistics`

```
================================================================================
📊 AGENT SYSTEM STATISTICS
================================================================================

📈 Overview:
  Total Agents:           41
  Active Agents:          12 (🟢 HOT)
  Total Conversations:    145
  Average Rating:         4.3/5.0
  Total System Cost:      $2.34

🏆 Top Performers (by rating):
  1. Dr. Marcus Thompson    Medicine      4.9/5   (15 uses)
  2. Prof. Sarah Kim        Humanities    4.8/5   (12 uses)
  3. Dr. Mei-Ling Chen      Humanities    4.8/5   (8 uses)

💪 Most Used Agents:
  1. Dr. Marcus Thompson    Medicine      15 uses
  2. Prof. Sarah Kim        Humanities    12 uses
  3. Dr. James Wilson       Law           10 uses

📊 Agents by Rank:
  ⭐ GOD_TIER (200+):        0 agents
  🔮 LEGENDARY (100-199):    0 agents
  📕 MASTER (50-99):         2 agents
  📙 EXPERT (25-49):         8 agents
  📘 COMPETENT (10-24):     15 agents
  📗 NOVICE (0-9):          16 agents

🌍 Agents by Domain:
  ⚕️  Medicine:             8 agents
  ⚖️  Law:                  7 agents
  📚 Humanities:           12 agents
  💻 Technology:            6 agents
  💼 Business:              4 agents
  🔬 Science:               3 agents
  🎨 Arts:                  1 agent

📅 Activity:
  Created today:            7 agents
  Used today:              12 agents
  Inactive (>7 days):       5 agents (🟡 WARM)
  Inactive (>90 days):      2 agents (🔵 COLD)

[Press Enter to return]
================================================================================
```

## Implementation Plan

### Phase 1: Core Viewing (MVP)

**New file**: `agent_roster.py`

```python
"""
Agent Roster Management - View and manage dynamic agents
"""

from typing import List, Dict, Optional
from src.persistence import DataStore
from src.data_models import AgentProfile
from display_formatter import DisplayFormatter


class AgentRoster:
    """Manages agent roster viewing and inspection."""

    def __init__(self, data_store: DataStore):
        self.data_store = data_store

    def show_agent_list(
        self,
        filter_domain: Optional[str] = None,
        sort_by: str = 'rating',
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ):
        """Display paginated agent list with filtering and sorting."""
        # Load all agents
        all_agents = self.data_store.load_all_agents()
        all_profiles = self.data_store.load_all_performance_profiles()

        # Apply filters
        agents = self._filter_agents(all_agents, all_profiles, filter_domain, search)

        # Sort
        agents = self._sort_agents(agents, all_profiles, sort_by)

        # Paginate
        total_pages = (len(agents) + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        page_agents = agents[start:end]

        # Display
        self._render_agent_list(page_agents, all_profiles, page, total_pages)

    def show_agent_details(self, agent_id: str):
        """Display detailed view of a specific agent."""
        agent = self.data_store.load_agent(agent_id)
        if not agent:
            print(f"❌ Agent not found: {agent_id}")
            return

        profile = self.data_store.load_performance_profile(agent_id)
        ratings = self.data_store.load_agent_ratings(agent_id)

        self._render_agent_details(agent, profile, ratings)

    def show_statistics_dashboard(self):
        """Display overall agent system statistics."""
        all_agents = self.data_store.load_all_agents()
        all_profiles = self.data_store.load_all_performance_profiles()

        stats = self._calculate_statistics(all_agents, all_profiles)
        self._render_statistics(stats)

    # Private helper methods...
    def _filter_agents(self, agents, profiles, domain, search):
        """Apply domain and search filters."""
        # Implementation...
        pass

    def _sort_agents(self, agents, profiles, sort_by):
        """Sort agents by specified criterion."""
        # Implementation...
        pass

    def _render_agent_list(self, agents, profiles, page, total_pages):
        """Render the agent list view."""
        # Implementation...
        pass

    def _render_agent_details(self, agent, profile, ratings):
        """Render detailed agent view."""
        # Implementation...
        pass

    def _render_statistics(self, stats):
        """Render statistics dashboard."""
        # Implementation...
        pass
```

**Modifications to `menu.py`**:

Add to `_handle_settings()` method (around line 305):

```python
def _handle_settings(self):
    """Handle settings configuration."""
    settings = get_settings()

    # Initialize agent roster manager (lazy load)
    agent_roster = None

    while True:
        print("\n" + "="*60)
        print("⚙️  Settings")
        print("="*60)

        print("\nWhat would you like to configure?\n")
        print("  1. 🔑 Configure API Keys")
        print("  2. 🤖 Select Models for Agents")
        print("  3. 🎨 Customize Display Colors")
        print("  4. 👁️  View Current Configuration")
        print("  5. 🧪 Test API Connections")
        print("  6. 🔧 Run Setup Wizard")
        print("  7. 👥 View Agent Roster")           # NEW
        print("  8. 📊 Agent Statistics")             # NEW
        print("  9. ◀️  Back to Main Menu")

        choice = input("\nEnter your choice (1-9): ").strip()

        if choice == '1':
            self._configure_api_keys(settings)
        # ... existing choices ...
        elif choice == '7':
            if not agent_roster:
                from agent_roster import AgentRoster
                from src.persistence import DataStore
                agent_roster = AgentRoster(DataStore())
            self._handle_agent_roster(agent_roster)
        elif choice == '8':
            if not agent_roster:
                from agent_roster import AgentRoster
                from src.persistence import DataStore
                agent_roster = AgentRoster(DataStore())
            agent_roster.show_statistics_dashboard()
            input("\nPress Enter to continue...")
        elif choice == '9':
            break
        else:
            print("\n❌ Invalid choice. Please enter 1-9.")

def _handle_agent_roster(self, roster: 'AgentRoster'):
    """Handle agent roster browsing interface."""
    current_page = 1
    filter_domain = None
    sort_by = 'rating'
    search = None

    while True:
        roster.show_agent_list(
            filter_domain=filter_domain,
            sort_by=sort_by,
            search=search,
            page=current_page
        )

        choice = input("\nChoice: ").strip().lower()

        if choice.isdigit():
            # View agent details
            agent_num = int(choice)
            # Get agent_id from displayed list...
            roster.show_agent_details(agent_id)
            input("\nPress Enter to continue...")
        elif choice == 'f':
            # Filter menu
            filter_domain = self._choose_domain_filter()
        elif choice == 's':
            # Search
            search = input("Search: ").strip()
        elif choice == 'b':
            break
        # ... pagination controls ...
```

### Phase 2: Advanced Features (Future)

**To be implemented later**:
- Agent editing (modify prompts/skills)
- Manual retirement
- Export agent data (JSON, CSV)
- Import agents from other systems
- Agent comparison (side-by-side view)
- Custom agent creation wizard
- Bulk operations (retire multiple, export selected)

## User Experience Flow

```
Main Menu
  └─ 5. ⚙️  Settings
      └─ 7. 👥 View Agent Roster
          ├─ Agent List View (paginated, filtered)
          │   └─ [Select #] → Agent Detail View
          │       ├─ [v] View Full Prompt
          │       ├─ [h] Rating History
          │       └─ [c] Conversations
          └─ [f] Filter by Domain
              ├─ All Domains
              ├─ Medicine
              ├─ Law
              ├─ Humanities
              ├─ Technology
              └─ ... (more domains)

      └─ 8. 📊 Agent Statistics
          └─ Statistics Dashboard (read-only)
```

## Data Access Patterns

**Agent Loading**:
```python
# Load all agents (expensive)
all_agents = data_store.load_all_agents()  # Dict[str, AgentProfile]

# Load specific agent (cheap)
agent = data_store.load_agent('dynamic-abc123')  # AgentProfile

# Get IDs only (very cheap)
agent_ids = data_store.get_all_agent_ids()  # List[str]
```

**Performance Considerations**:
- Cache loaded agents in memory during browsing session
- Lazy-load performance profiles (only load when viewing details)
- Use IDs-only for list view, load full data on detail view
- Consider adding index for common queries (domain, rank, rating)

## File Structure

```
claude-agent-chat/
├── agent_roster.py                 # NEW - Agent roster management
├── menu.py                          # MODIFIED - Add roster options
├── display_formatter.py             # MODIFIED - Add roster display methods
├── src/
│   ├── persistence.py              # EXISTING - Data access layer
│   └── agent_coordinator.py        # EXISTING - Agent coordination
└── docs/
    └── AGENT_ROSTER_FEATURE.md     # THIS FILE
```

## Testing Checklist

Before marking this feature complete:

- [ ] Agent list displays correctly with all 41 agents
- [ ] Filtering by domain works for all domains
- [ ] Sorting by rating/uses/date works correctly
- [ ] Pagination works (prev/next page)
- [ ] Search finds agents by name and keywords
- [ ] Agent detail view shows complete information
- [ ] Rating history displays correctly
- [ ] Conversation links are accurate
- [ ] Statistics dashboard calculations are correct
- [ ] Performance is acceptable (<1s for list view)
- [ ] Memory usage is reasonable
- [ ] Error handling for missing/corrupted agent data
- [ ] Back navigation works from all screens
- [ ] Terminal colors/formatting look good

## Open Questions

1. **Agent Editing**: Should users be able to edit agent prompts through the UI, or keep that file-based?
2. **Retirement**: Should there be a "Retire Agent" action in the detail view?
3. **Export Format**: What format would be most useful for exporting agents? JSON? YAML? CSV?
4. **Search Scope**: Should search include full prompt text, or just name/keywords?
5. **Real-time Updates**: If an agent is used during browsing, should the list auto-refresh?

## Future Enhancements

- **Agent Creation Wizard**: Interactive wizard for creating custom agents
- **Agent Templates**: Pre-built agent templates for common use cases
- **Agent Comparison**: Side-by-side comparison of 2-3 agents
- **Performance Graphs**: Visual charts for rating trends over time
- **Export/Import**: Backup and restore agent collections
- **Agent Tagging**: Custom tags for organizing agents
- **Favorites**: Mark frequently-used agents
- **Agent Recommendations**: Suggest agents based on conversation topics

## Related Issues

- #TODO: Consider adding REST API endpoints for web interface
- #TODO: Web UI agent roster page (future)
- #TODO: Agent versioning (track prompt changes over time)

## References

- Phase 1E Implementation: `docs/INTEGRATION_COMPLETE.md`
- Agent Data Models: `src/data_models.py`
- Performance Tracking: `src/rating_system.py`
- Agent Lifecycle: `src/lifecycle_manager.py`
