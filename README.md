# Claude Agent Chat

A production-ready multi-agent conversation system featuring dynamic agent creation, autonomous web research, and intelligent context management.

## Overview

Create specialized AI experts on-demand for any topic and watch them engage in evidence-based discussions. The system dynamically generates domain experts, conducts autonomous web research, and manages sophisticated multi-agent conversations with full database persistence.

- **Multi-tier Memory**: Immediate context (last N exchanges) + checkpoints + summarized history
- **Smart Context Building**: Optimizes token usage while preserving conversation coherence
- **Automatic Checkpointing**: Marks and preserves key conversation milestones
- **Recursive Summarization**: Condenses older exchanges when conversations grow long
- **Beautiful Display**: Color-coded terminal output with progress tracking

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User Interfaces                              │
│                                                                     │
│  ┌──────────────────────┐         ┌─────────────────────────┐    │
│  │   Web Interface      │         │   Terminal CLI          │    │
│  │   React + Next.js    │         │   coordinator.py        │    │
│  │   localhost:3000     │         │   menu.py               │    │
│  └──────────┬───────────┘         └───────────┬─────────────┘    │
└─────────────┼──────────────────────────────────┼──────────────────┘
              │                                  │
              │ HTTP/WebSocket                   │ Direct Python API
              ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend Services                               │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  FastAPI Backend (api.py + websocket_handler.py)            │ │
│  │  • REST API endpoints                                        │ │
│  │  • WebSocket streaming                                       │ │
│  │  • Real-time agent coordination                              │ │
│  └────────────────────────┬─────────────────────────────────────┘ │
│                           │                                        │
│  ┌────────────────────────┴─────────────────────────────────────┐ │
│  │               Bridge Layer (bridge.py)                       │ │
│  │  • Conversation Manager  • Metadata Extractor               │ │
│  │  • Agent Coordinator     • Search Coordinator               │ │
│  │  • Database Manager      • Citation Manager                 │ │
│  └────────────────────────┬─────────────────────────────────────┘ │
└───────────────────────────┼───────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Agent System    │  │  Search System   │  │  Data Layer      │
│                  │  │                  │  │                  │
│ • Agent Runner   │  │ • SearXNG API    │  │ • PostgreSQL     │
│ • Agent Factory  │  │ • Content Ext.   │  │ • Qdrant         │
│ • Dynamic Agents │  │ • Citation Mgr   │  │ • Embeddings     │
│ • Anthropic API  │  │ • Query Cache    │  │ • Snapshots      │
└──────────────────┘  └──────────────────┘  └──────────────────┘

                    ┌────────────────────┐
                    │  Dynamic Agents    │
                    │  (N agents, any    │
                    │   domain expertise)│
                    └────────────────────┘
```

**Modern Multi-Agent Architecture:**
- **Dual Interfaces**: Web UI and Terminal CLI both access the same backend
- **FastAPI Backend**: RESTful API + WebSocket for real-time streaming
- **Bridge Layer**: Orchestrates conversation management, agent coordination, search, and database operations
- **Agent System**: Dynamic agent creation with Anthropic API, supporting N agents with any domain expertise
- **Autonomous Search**: Real-time web research via SearXNG with content extraction and citation tracking
- **Data Persistence**: PostgreSQL for conversations/exchanges, Qdrant for semantic search with embeddings

## Features

### 🧠 Extended Thinking & ⚡ Real-Time Streaming
- **Extended Thinking Display**: See Claude's internal reasoning before responses
- **TRUE Real-Time Streaming**: Responses appear as generated - no fake delays!
- **Transparent Reasoning**: Watch agents think through complex problems
- **Configurable**: Toggle thinking on/off, adjust thinking depth

👉 **[See FEATURES.md for full guide](FEATURES.md)**

### 🔧 Geeky Technical Stats Mode
- **Comprehensive Token Breakdown**: See input (context + prompt), output, and thinking tokens separately with individual costs
- **Context Window Analysis**: View total exchanges, window size, character/token counts, and which specific turns are referenced
- **Session Analytics**: Real-time tracking of current turn, total tokens, average per turn, and projected totals
- **Model Configuration Details**: Display model name, temperature, and max tokens settings
- **Configurable Display Modes**: Choose between simple (basic), detailed (enhanced), or geeky (full technical breakdown)

Perfect for system engineers who want complete transparency into token usage, context management, and cost accumulation!

### 🤖 Dynamic Multi-Agent System
- **On-Demand Agent Creation**: System analyzes conversation topic and creates specialized expert agents automatically
- **Multi-Agent Conversations (3+ Agents)**: Conversations now support any number of agents in round-robin rotation, not just 2
- **Round-Robin Turn-Taking**: Agents rotate seamlessly (Agent1 → Agent2 → Agent3 → Agent1...) for multi-perspective discussions
- **Agent Deduplication**: Prevents duplicate agents with similar expertise (85-95% similarity detection)
- **5-Dimension Rating System**: Rate agents on helpfulness, accuracy, relevance, clarity, and collaboration after each conversation
- **6-Rank Promotion System**: Agents level up from NOVICE → COMPETENT → EXPERT → MASTER → LEGENDARY → GOD_TIER based on performance
- **Lifecycle Management**: HOT (active) → WARM (7 days) → COLD (90 days) → ARCHIVED → RETIRED states
- **Leaderboard**: Track top-performing agents across all conversations with detailed analytics
- **Cost Tracking**: Monitor API costs for agent creation (~$0.013-$0.015 per agent)

👉 **[See INTEGRATION_COMPLETE.md for Phase 1E guide](INTEGRATION_COMPLETE.md)**

Example flow:
```
Topic: "Ancient Mesopotamian agriculture"
↓
System creates 2 dynamic agents:
  • Dr. Ashurbanipal Chen (Ancient Near East expert)
  • Irrigation Systems Specialist (Agricultural science)
↓
Conversation proceeds with specialized experts
↓
Rate agents after completion → Agents gain rank points
```

### 🔍 Autonomous Search & Research
**Transform theoretical debates into evidence-based discussions with real-time web research**

- **Truly Autonomous**: Agents don't need explicit tool commands - search triggers naturally from their thinking
- **Intelligent Trigger Detection**:
  - **Uncertainty Markers**: "I believe...", "likely...", "might be..." → automatic verification
  - **Fact-Checking**: Claims with statistics, percentages, or research citations → auto-verify
  - **Explicit Requests**: "Let me search for...", "current data on..." → immediate search
- **SearXNG Integration**: Privacy-focused metasearch aggregating Google, DuckDuckGo, Wikipedia
- **Smart Budget Management**:
  - 3 searches per turn max
  - 15 searches per conversation max
  - Rate limiting (10/minute)
  - Cooldown periods between searches
- **Query Deduplication**: 15-minute cache prevents redundant searches
- **Content Extraction**: Automatic cleaning and summarization of top 3 results
- **Citation Tracking**: Full provenance with publisher, date, URL
- **Context Injection**: Search results inserted seamlessly into agent context
- **WebSocket Streaming**: Real-time search progress visible in web UI

**Why This Is Transformative:**
- **Evidence-Based Debates**: Specialized agents can fact-check each other's claims in real-time
- **Ground Abstract Discussions**: Replace "I think..." with "According to [source]..."
- **Research Loops**: One agent proposes → Another searches counter-evidence → First refines based on findings
- **Beyond Training Cutoff**: Discuss current events, breaking news, emerging technologies
- **Emergent Behavior**: Agents learn and adapt during conversations

**Example Trigger Flow:**
```
Agent thinking: "I believe antibiotic resistance affects 2.8M people annually -
                 let me verify this statistic"
↓
System: Detects uncertainty + fact claim
↓
Search: "antibiotic resistance statistics annual cases"
↓
SearXNG: Returns top 8 results from multiple engines
↓
Extract: Pull clean content from top 3 sources
↓
Citations: Create [1], [2], [3] references
↓
Inject: Add to next agent's context with full sourcing
↓
Agent response: "Actually, according to CDC data [1], the figure is 2.8 million..."
```

**Configuration** (`config.yaml`):
```yaml
search:
  searxng_url: "https://s.llam.ai"  # Or self-hosted
  engines: [google, duckduckgo, wikipedia]
  limits:
    max_per_turn: 3
    max_per_conversation: 15
  cache:
    enabled: true
    ttl_minutes: 15
```

This makes the system **genuinely useful**, not just entertaining - agents conducting real research during conversations!

👉 **[See search_coordinator.py for implementation](search_coordinator.py)**

### 👤 Agent Qualification Display
- **Visible Credentials**: Agents see each other's qualifications in conversation context
- **UI Display**: Agent names show qualifications in header (e.g., "Oscar Solis - Biology ↔ Dr. Michael Leach - Public Policy")
- **Context Awareness**: Agents know who they're speaking to - no more guessing
- **Database Persistence**: Qualifications stored in `agent_qualification` column
- **Metadata Fallback**: Old conversations retroactively show qualifications from stored metadata
- **Format**: "Agent Name (Qualification)" in context, "Agent Name - Qualification" in UI

### 💾 Database Persistence & Semantic Search
- **PostgreSQL Storage**: All conversations, exchanges, and metadata persistently stored
- **Qdrant Vector Search**: Semantic search across conversation history using embeddings
- **Continue Conversations**: Resume any previous conversation from where you left off
- **Rich Metadata**: AI-powered extraction of topics, concepts, themes, sentiment, and complexity
- **Context Snapshots**: Automatic saving of conversation state for reliable resuming
- **Interactive Dashboard**: Beautiful terminal-based visualization of conversation intelligence

👉 **[See SETUP_DATABASE.md for database setup](SETUP_DATABASE.md)**

### 🌐 Modern Web Interface
- **React + Next.js Frontend**: Beautiful dark-mode UI with real-time streaming
- **FastAPI Backend**: RESTful API + WebSocket support for live conversations
- **Dual Interface System**: Terminal and web work simultaneously, sharing the same database
- **Real-Time Streaming**: Watch agent responses appear as they're generated
- **User Content Injection**: Pause conversations and inject custom user content mid-conversation (like terminal Ctrl-C)
- **Tool Use Visibility**: See when agents use web browsing tools (fetch_url) with expandable details
- **Conversation State Management**: Clear distinction between paused (resumable), active, and completed states
- **Continue Conversations**: Resume any active or paused conversation (< 20 turns) from the web UI
- **Browse History**: View all completed conversations with full exchanges and thinking content
- **Permanent Statistics Display**: Token usage and cost tracking for ALL conversations (live and completed)
  - Header stats always visible during viewing
  - Detailed breakdown panel with per-agent analytics
  - Historical cost calculation using current model pricing
- **Responsive Design**: Works on desktop and mobile with Tailwind CSS

👉 **[See CONVERSATION_STATES.md for state management details](CONVERSATION_STATES.md)**

**Quick Start Web Interface:**
```bash
# Start databases (if not already running)
docker-compose up -d

# Start web services (backend + frontend)
./web/start-web.sh

# Open browser
open http://localhost:3000
```

**Architecture:**
```
┌──────────────────┐  ┌──────────────────┐
│  Terminal CLI    │  │  Web Interface   │
│  (Python)        │  │  (React/Next.js) │
│  coordinator.py  │  │  localhost:3000  │
└─────────┬────────┘  └─────────┬────────┘
          │                     │
          │   Shared Storage    │
          └──────────┬──────────┘
                     ▼
          ┌────────────────────┐
          │  Docker Services   │
          │  • PostgreSQL      │
          │  • Qdrant          │
          └────────────────────┘
```

Both interfaces can run at the same time - conversations created in the terminal appear in the web UI and vice versa!

### 📁 Unified Conversation Management
- **Streamlined Menu**: Simplified interface from 7 to 6 main options
- **Integrated Actions**: View, continue, and delete conversations from single menu flow
- **Safety Features**: Multi-step confirmation for destructive operations
- **Quick Navigation**: Easy browsing of conversation history with previews

### Context Management
- **Immediate Buffer**: Always includes last 2-3 full exchanges
- **Anchor Points**: Preserves original question and key checkpoints
- **Smart Summarization**: Condenses older history when threshold reached
- **Token Optimization**: Tracks and manages context window size

### Dynamic Agent Creation

Agents are created on-demand based on conversation topics. The system:
- Analyzes the topic to identify required expertise
- Creates 2-3 specialized agents with relevant qualifications
- Assigns domain classifications (STEM, Humanities, Social Sciences, etc.)
- Rates agent performance and promotes them through 6 ranks (NOVICE → GOD_TIER)

**Example agents created:**
- **Dr. Ashurbanipal Chen** - Ancient Near East expert for Mesopotamian agriculture discussions
- **Dr. Marcus Ashford** - Cardiology specialist for medical debates
- **Oscar Solis** - Biology researcher for antibiotic resistance analysis
- **Prof. Sarah Martinez** - Climate scientist for environmental policy discussions

### Output & Logging
- Color-coded terminal display with thinking visualization
- Real-time token usage tracking
- JSON conversation logs with full metadata
- Markdown transcripts for easy reading

## Installation

1. **Prerequisites**
   - Python 3.8+
   - Anthropic API key ([Get one here](https://console.anthropic.com/settings/keys))
   - Docker & Docker Compose (for databases)
   - Node.js 18+ (for web interface - optional)
   - Terminal with color support (recommended)

2. **Setup API Key**

   This project requires ONE Anthropic API key (not two - the same key is used for both agents).

   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit .env and add your API key
   # ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
   ```

   Or set it directly in your shell:
   ```bash
   export ANTHROPIC_API_KEY='sk-ant-api03-your-key-here'
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Setup**
   ```bash
   # Check that API key is set
   echo $ANTHROPIC_API_KEY

   # Check that agents are available
   ls .claude/agents/

   # Run the test script
   python test_setup.py
   ```

## Getting Started - Step by Step

### How Many Terminal Windows Do I Need?

**Just ONE!** This is a common point of confusion.

You do **NOT** need to:
- Open separate terminals for each agent
- Manually copy/paste between windows
- Directly interact with the agents yourself

You **ONLY** need to:
- Run `python coordinator.py` in a single terminal
- Watch the automated conversation unfold
- Let the coordinator handle everything

### What Happens Behind the Scenes

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR TERMINAL (the only one you see)                       │
│                                                              │
│  $ python coordinator.py                                     │
│  ↓                                                           │
│  System analyzes your topic and creates specialized agents: │
│    ├─ Agent 1: Domain Expert    ← dynamically created       │
│    ├─ Agent 2: Related Specialist ← dynamically created     │
│    └─ Agent 3: Complementary Expert ← (if needed)           │
│                                                              │
│  Coordinator orchestrates:                                   │
│    1. Sends message to Agent 1                               │
│    2. Receives Agent 1's response                            │
│    3. Sends to Agent 2 (with context + qualification)        │
│    4. Receives Agent 2's response                            │
│    5. Repeat in round-robin...                               │
│                                                              │
│  All displayed in YOUR terminal with colors                  │
└─────────────────────────────────────────────────────────────┘
```

The system dynamically creates agents based on your conversation topic, determining the required expertise and creating specialized agents on-demand.

You never see the agent creation process - you just see the formatted conversation output with qualified experts discussing the topic.

### Your First Run - What You'll See

Here's exactly what happens when you run the coordinator:

**Step 1: Start the script**
```bash
$ python coordinator.py
```

**Step 2: Welcome banner appears**
```
╔══════════════════════════════════════════════════════════════╗
║         🤖 Agent-to-Agent Conversation Coordinator 🤖        ║
║                                                              ║
║  Specialized AI experts engaging in intelligent discussion   ║
╚══════════════════════════════════════════════════════════════╝

============================================================
Agents Participating:
============================================================
  ● Dr. Sarah Martinez - Climate Science
  ● Prof. Michael Chen - Economics
  ● Dr. Alexandra Torres - Public Policy
============================================================
```

**Step 3: Conversation setup**
```
────────────────────────────────────────────────────────────
Starting Conversation
────────────────────────────────────────────────────────────

Initial Prompt:
  Climate change policy trade-offs between economic
  growth and environmental protection

Configuration:
  Max turns: 20
────────────────────────────────────────────────────────────

ℹ️  Creating specialized agents for this topic...
  ✓ Created Dr. Sarah Martinez (Climate Science)
  ✓ Created Prof. Michael Chen (Economics)
  ✓ Created Dr. Alexandra Torres (Public Policy)

Start conversation? [Y/n]:
```

**Step 4: Press Enter to start**

Just hit Enter (or type 'y'). The conversation begins automatically!

**Step 5: Watch the conversation unfold**
```
────────────────────────────────────────────────────────────
Turn 0: Dr. Sarah Martinez (Climate Science) [14:32:15]
────────────────────────────────────────────────────────────

ℹ️  Dr. Sarah Martinez is thinking...

  <Response appears here in CYAN>
  (Climate scientist perspective on environmental impacts)

  Tokens: +245 (Total: 245)

────────────────────────────────────────────────────────────
Turn 1: Prof. Michael Chen (Economics) [14:32:22]
────────────────────────────────────────────────────────────

ℹ️  Prof. Michael Chen is thinking...

  <Response appears here in YELLOW>
  (Economic analysis of policy trade-offs)

  Tokens: +189 (Total: 434)

────────────────────────────────────────────────────────────
Turn 2: Dr. Alexandra Torres (Public Policy) [14:32:28]
────────────────────────────────────────────────────────────

  <Conversation continues with third agent perspective...>
```

**Step 6: Conversation completes**

After reaching max_turns (or you press Ctrl+C), you'll see:

```
============================================================
Conversation Complete
============================================================

Total turns: 20
Total tokens: ~4,523

============================================================

ℹ️  Saving conversation log to: conversation_log.json
ℹ️  Saving transcript to: conversation_transcript.md
```

### Your Role as the User

You are essentially a **spectator** watching an automated discussion:

1. **Start**: Run the script and confirm the prompt
2. **Watch**: Agents automatically take turns responding
3. **Stop**: Press `Ctrl+C` anytime to end early (optional)
4. **Review**: Check the saved logs afterward

The agents never wait for your input during the conversation - they respond to each other automatically based on the context management system.

### Automated vs Manual Modes

This project supports two approaches:

| **Automated (Recommended)** | **Manual (Educational)** |
|----------------------------|--------------------------|
| **1 terminal window** | **2-3 terminal windows** |
| Run `coordinator.py` | Open separate terminals for each agent |
| Agents respond automatically | You manually copy/paste between agents |
| Context managed intelligently | Context only includes what you paste |
| Full logging and formatting | No automatic logging |
| **Use this for actual conversations** | **Use this to understand agent behavior** |

The automated mode (what we've built) is the recommended approach. The manual mode (mentioned earlier) was just to help you understand how the agents work individually.

### Quick Start Checklist

- [ ] Open **one** terminal window
- [ ] Navigate to project directory: `cd /path/to/claude-agent-chat`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run coordinator: `python coordinator.py`
- [ ] Press Enter when prompted
- [ ] Watch the conversation happen automatically
- [ ] Press `Ctrl+C` to stop anytime (optional)
- [ ] Check output files: `conversation_log.json` and `conversation_transcript.md`

That's it! No multiple terminals, no copy/paste, no manual orchestration.

## Usage

### Basic Usage

Run with default settings:
```bash
python coordinator.py
```

### Custom Prompt

Start a conversation with a specific question:
```bash
python coordinator.py --prompt "What makes a good programming language?"
```

### Limit Conversation Length

Control the number of turns:
```bash
python coordinator.py --max-turns 10
```

### Custom Configuration

Use a different config file:
```bash
python coordinator.py --config my_config.yaml
```

### All Options

```bash
python coordinator.py \
  --config config.yaml \
  --prompt "Your question here" \
  --max-turns 15 \
  --debug
```

## Configuration

Edit `config.yaml` to customize behavior:

### Key Settings

```yaml
conversation:
  max_turns: 20              # Maximum exchanges
  initial_prompt: "..."      # Default starting question
  turn_delay: 1.0           # Seconds between turns
  show_thinking: true        # Show extended thinking
  thinking_budget: 5000      # Thinking token budget

context:
  immediate_exchanges: 3     # Always keep last N exchanges
  summarize_after: 6        # Start summarizing after N exchanges
  preserve_original: true    # Always include initial question
  checkpoint_interval: 5     # Create checkpoint every N turns
  max_context_tokens: 8000  # Approximate token limit

display:
  mode: "single"            # "single" or "dual" terminal
  show_tokens: true         # Display token usage
  stats_mode: "geeky"       # "simple", "detailed", or "geeky"
  use_colors: true          # Color-coded output
  clear_screen: false       # Clear between turns

logging:
  save_full_history: true   # Save JSON log
  save_transcript: true     # Save Markdown transcript
```

## Project Structure

```
claude-agent-chat/
├── .claude/
│   └── agents/
│       ├── agent_a.md                    # Legacy static agent (optional)
│       ├── agent_b.md                    # Legacy static agent (optional)
│       └── dynamic/                      # Dynamically created agents
│           ├── dynamic-a551f2bec1c4.md   # Example: Dr. Marcus Ashford (Cardiology)
│           ├── dynamic-7b3fdfca864f.md   # Example: Oscar Solis (Biology)
│           └── ...                       # More dynamic agents
├── web/                                  # NEW: Web Interface
│   ├── frontend/                         # Next.js React app
│   │   ├── app/                          # App Router pages
│   │   │   ├── page.tsx                  # Home page (conversation list)
│   │   │   ├── new/page.tsx              # Create new conversation
│   │   │   └── conversation/[id]/page.tsx # Conversation viewer
│   │   ├── components/                   # React components
│   │   │   ├── AgentMessage.tsx          # Message display with thinking
│   │   │   ├── ConversationControls.tsx  # Pause/Resume/Stop/Inject controls
│   │   │   ├── InjectContentModal.tsx    # NEW: User content injection modal
│   │   │   ├── ToolUseMessage.tsx        # NEW: Tool use display
│   │   │   └── InterruptDashboard.tsx    # Metadata dashboard
│   │   ├── hooks/                        # Custom React hooks
│   │   │   ├── useWebSocket.ts           # WebSocket management (with inject)
│   │   │   └── useConversations.ts       # Data fetching
│   │   └── lib/                          # Utilities
│   │   │   └── costCalculator.ts         # NEW: Token cost calculation
│   ├── backend/                          # FastAPI backend
│   │   ├── api.py                        # REST + WebSocket endpoints
│   │   ├── bridge.py                     # Python module bridge
│   │   └── websocket_handler.py          # WebSocket streaming + state logic
│   └── start-web.sh                      # Service launcher
├── coordinator.py                        # Original orchestration script
├── coordinator_with_memory.py            # NEW: With database persistence + Phase 1E
├── enhanced_coordinator.py              # NEW: Standalone Phase 1E coordinator
├── conversation_manager.py               # Context & memory management
├── conversation_manager_persistent.py    # NEW: Database-backed manager
├── agent_runner.py                      # API client management (with lazy-loading)
├── display_formatter.py                 # Terminal output formatting
├── menu.py                             # NEW: Interactive menu system
├── db_manager.py                       # NEW: PostgreSQL & Qdrant manager
├── cost_calculator.py                  # NEW: Token cost tracking
├── settings_manager.py                 # NEW: Configuration management (API key sync)
├── metadata_extractor.py               # NEW: AI-powered conversation analysis
├── terminal_dashboard.py               # NEW: Rich metadata visualization
├── config.yaml                         # Configuration file (with Phase 1E settings)
├── web_tools.py                        # NEW: Web browsing tools for agents
├── src/                                # NEW: Phase 1E Dynamic Agent System
│   ├── __init__.py
│   ├── agent_coordinator.py            # Central orchestration
│   ├── agent_factory.py                # Agent creation with Claude API
│   ├── dynamic_agent_registry.py       # Agent storage and retrieval
│   ├── performance_tracker.py          # Rating history and analytics
│   ├── agent_lifecycle.py              # Lifecycle management (HOT/WARM/COLD)
│   ├── agent_deduplicator.py           # Similarity detection
│   ├── leaderboard.py                  # Agent ranking system
│   ├── data_models.py                  # Data structures
│   └── utils.py                        # Utility functions
├── tests/                              # NEW: Phase 1 test suites
│   ├── test_phase_1a.py                # Agent creation tests
│   ├── test_phase_1b.py                # Registry and deduplication tests
│   └── test_phase_1c.py                # End-to-end integration tests
├── examples/                           # NEW: Example configurations
├── data/                               # NEW: Phase 1E persistent data
│   ├── agents/                         # Agent profiles (JSON)
│   ├── performance/                    # Performance history
│   ├── ratings/                        # Rating records
│   ├── leaderboard/                    # Leaderboard cache
│   └── conversations/                  # Conversation metadata
├── docker-compose.yml                  # NEW: Database services setup
├── init.sql                           # NEW: PostgreSQL schema
├── metadata_schema.sql                # NEW: Metadata tables
├── migrations/                        # NEW: Database migrations
│   └── 002_add_paused_status.sql      # Add 'paused' status
├── fix_conversation_status.sql        # NEW: Database maintenance
├── FEATURES.md                        # Extended thinking & streaming guide
├── SETUP_DATABASE.md                  # NEW: Database setup guide
├── CONVERSATION_STATES.md             # NEW: Conversation state lifecycle guide
├── INTEGRATION_COMPLETE.md            # NEW: Phase 1E dynamic agent system guide
├── CHANGELOG.md                       # NEW: Version history
├── .env.example                       # Environment variable template
├── .env                              # Your API key (create from .env.example)
├── requirements.txt                   # Python dependencies
└── README.md                         # This file
```

## How It Works

### Memory Management

The system uses a three-tier memory strategy:

1. **Immediate Context** (Always included)
   - Last 2-3 exchanges in full
   - Ensures conversation continuity

2. **Checkpoints** (Preserved milestones)
   - Created every N turns (configurable)
   - Marks key moments in conversation
   - Original question always preserved

3. **Summarized History** (Compressed older content)
   - Activates after threshold (default: 6 exchanges)
   - Uses recursive summarization
   - Condenses information while preserving key points

### Conversation Flow

```
1. Initial Prompt → Agent A
2. Agent A responds → Context built for Agent B
3. Agent B responds → Context built for Agent A
4. Repeat until max_turns reached
5. Save logs and display summary
```

### Context Building Process

For each agent's turn:
1. Include original question (anchor point)
2. Add relevant checkpoints
3. Add summarized older history (if needed)
4. Always include last N exchanges in full
5. Check total token count
6. Send optimized context to agent

## Examples

### Example 1: Technology Discussion

```bash
python coordinator.py \
  --prompt "Should we prioritize AI safety or AI capabilities?" \
  --max-turns 15
```

System creates domain experts to explore different perspectives on the question.

### Example 2: Philosophy Debate

```bash
python coordinator.py \
  --prompt "What is consciousness?" \
  --max-turns 20
```

System creates philosophers and neuroscientists to explore this deep question from multiple angles.

### Example 3: Short Focused Chat

```bash
python coordinator.py \
  --prompt "Best practices for code reviews?" \
  --max-turns 6
```

System creates software engineering experts for a focused technical discussion.

## Customizing Agents

The system dynamically creates agents based on conversation topics, but you can optionally create static agents by editing `.claude/agents/agent_a.md` or `agent_b.md`:

```markdown
# Your Agent Name

You are [persona description]

## Expertise
- Domain 1
- Domain 2

## Conversation Style
- Style point 1
- Style point 2

## Your Role
[Role description for multi-agent conversations]
```

**Note**: Dynamic agent creation is the default and recommended approach. Static agents are primarily for backwards compatibility.

## Output Files

### conversation_log.json
Complete conversation history with metadata:
- All exchanges with timestamps
- Token estimates
- Context provided to each agent
- Checkpoints created

### conversation_transcript.md
Human-readable transcript:
- Formatted conversation flow
- Turn numbers and timestamps
- Easy to share and read

## Troubleshooting

### API Key Issues
- **"ANTHROPIC_API_KEY environment variable not set"**
  - Create a `.env` file: `cp .env.example .env`
  - Add your API key to `.env`
  - Or set it in your shell: `export ANTHROPIC_API_KEY='your-key-here'`
- **API authentication errors**
  - Verify your key is valid at [console.anthropic.com](https://console.anthropic.com/)
  - Ensure the key starts with `sk-ant-api03-`

### Agents not responding
- Check that agent files exist: `ls .claude/agents/`
- Verify both agent_a.md and agent_b.md are present
- Run the test script: `python test_setup.py`

### Import errors
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

### Colors not working
- Terminal may not support colors
- Disable in config: `display.use_colors: false`
- Install colorama: `pip install colorama`

### Context too long
- Reduce `context.max_context_tokens` in config
- Lower `context.immediate_exchanges`
- Decrease `conversation.max_turns`

## Advanced Features

### Debug Mode

Enable detailed logging:
```bash
python coordinator.py --debug
```

### Custom Summarization Strategy

Edit `config.yaml`:
```yaml
context:
  summarization_strategy: "recursive"  # or "simple"
```

### Checkpoint Frequency

Adjust checkpoint creation:
```yaml
context:
  checkpoint_interval: 3  # Create every 3 turns
```

## Research Background

This implementation is based on modern LLM context management research:

- **Sliding Window Approach**: Maintains recent history while summarizing older content
- **Checkpoint Systems**: Preserves key moments (LangGraph-inspired)
- **Recursive Summarization**: Condenses information progressively
- **Context Engineering**: Optimizes what information to include
- **Token Optimization**: Manages context window efficiently

## Future Enhancements

Potential improvements:
- [ ] True recursive summarization using LLM
- [ ] Multi-agent support (3+ agents)
- [ ] Real-time context editing
- [x] Web interface (✅ Complete!)
- [ ] Conversation branching
- [ ] Agent personality templates
- [x] Sentiment analysis (✅ In metadata extraction)
- [x] Topic tracking (✅ In metadata extraction)
- [ ] Mobile app
- [ ] Conversation export/import
- [ ] Custom agent creation UI
- [ ] Advanced search filters

## Contributing

This is an experimental project. Feel free to:
- Create new agent personalities
- Implement better summarization
- Add visualization features
- Improve context management

## License

MIT License - feel free to use and modify

## Credits

Built with:
- **Backend**: Claude Code CLI, Python 3, FastAPI, PostgreSQL, Qdrant
- **Frontend**: React, Next.js 14, Tailwind CSS, TypeScript
- **Libraries**: colorama, PyYAML, psycopg2, openai (embeddings), tanstack/react-query
- **Infrastructure**: Docker, Docker Compose

Inspired by research in:
- LLM context window management
- Multi-agent conversation systems
- LangGraph memory patterns
- Anthropic's Claude API best practices
- Real-time WebSocket streaming
- Modern React patterns (Server Components, Suspense)
