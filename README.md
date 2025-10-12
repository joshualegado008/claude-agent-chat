# Claude Agent Chat

An advanced conversation coordinator for Claude Code agents with intelligent context management.

## Overview

This project enables two Claude Code agents to have natural, extended conversations with each other. It implements sophisticated context management techniques inspired by modern LLM best practices:

- **Multi-tier Memory**: Immediate context (last N exchanges) + checkpoints + summarized history
- **Smart Context Building**: Optimizes token usage while preserving conversation coherence
- **Automatic Checkpointing**: Marks and preserves key conversation milestones
- **Recursive Summarization**: Condenses older exchanges when conversations grow long
- **Beautiful Display**: Color-coded terminal output with progress tracking

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Coordinator                              │
│  - Orchestrates agent turns                                 │
│  - Manages conversation flow                                │
│  - Handles logging and display                              │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
       ┌───────▼────────┐            ┌────────▼───────┐
       │ Agent Runner   │            │  Context Mgr   │
       │ - Subprocess   │            │  - History     │
       │ - I/O handling │            │  - Summarize   │
       │ - Error mgmt   │            │  - Checkpoints │
       └───────┬────────┘            └────────┬───────┘
               │                              │
       ┌───────▼──────────────────────────────▼───────┐
       │         Claude Code Agents                   │
       │  Nova (Optimistic)  ↔  Atlas (Pragmatic)    │
       └──────────────────────────────────────────────┘
```

## Features

### 🧠 Extended Thinking & ⚡ Real-Time Streaming
- **Extended Thinking Display**: See Claude's internal reasoning before responses
- **TRUE Real-Time Streaming**: Responses appear as generated - no fake delays!
- **Transparent Reasoning**: Watch agents think through complex problems
- **Configurable**: Toggle thinking on/off, adjust thinking depth

👉 **[See FEATURES.md for full guide](FEATURES.md)**

### 🔧 Geeky Technical Stats Mode (NEW!)
- **Comprehensive Token Breakdown**: See input (context + prompt), output, and thinking tokens separately with individual costs
- **Context Window Analysis**: View total exchanges, window size, character/token counts, and which specific turns are referenced
- **Session Analytics**: Real-time tracking of current turn, total tokens, average per turn, and projected totals
- **Model Configuration Details**: Display model name, temperature, and max tokens settings
- **Configurable Display Modes**: Choose between simple (basic), detailed (enhanced), or geeky (full technical breakdown)

Perfect for system engineers who want complete transparency into token usage, context management, and cost accumulation!

### 💾 Database Persistence & Semantic Search (NEW!)
- **PostgreSQL Storage**: All conversations, exchanges, and metadata persistently stored
- **Qdrant Vector Search**: Semantic search across conversation history using embeddings
- **Continue Conversations**: Resume any previous conversation from where you left off
- **Rich Metadata**: AI-powered extraction of topics, concepts, themes, sentiment, and complexity
- **Context Snapshots**: Automatic saving of conversation state for reliable resuming
- **Interactive Dashboard**: Beautiful terminal-based visualization of conversation intelligence

👉 **[See SETUP_DATABASE.md for database setup](SETUP_DATABASE.md)**

### 📁 Unified Conversation Management (NEW!)
- **Streamlined Menu**: Simplified interface from 7 to 6 main options
- **Integrated Actions**: View, continue, and delete conversations from single menu flow
- **Safety Features**: Multi-step confirmation for destructive operations
- **Quick Navigation**: Easy browsing of conversation history with previews

### Context Management
- **Immediate Buffer**: Always includes last 2-3 full exchanges
- **Anchor Points**: Preserves original question and key checkpoints
- **Smart Summarization**: Condenses older history when threshold reached
- **Token Optimization**: Tracks and manages context window size

### Agent Personalities
- **Nova** (@agent_a): Optimistic visionary who explores possibilities
- **Atlas** (@agent_b): Pragmatic analyst who questions assumptions

### Output & Logging
- Color-coded terminal display with thinking visualization
- Real-time token usage tracking
- JSON conversation logs with full metadata
- Markdown transcripts for easy reading

## Installation

1. **Prerequisites**
   - Python 3.8+
   - Anthropic API key ([Get one here](https://console.anthropic.com/settings/keys))
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
┌─────────────────────────────────────────────────┐
│  YOUR TERMINAL (the only one you see)          │
│                                                 │
│  $ python coordinator.py                        │
│  ↓                                              │
│  Coordinator spawns:                            │
│    ├─ Agent Process 1 (Nova)   ← subprocess    │
│    └─ Agent Process 2 (Atlas)  ← subprocess    │
│                                                 │
│  Coordinator orchestrates:                      │
│    1. Sends message to Nova                     │
│    2. Receives Nova's response                  │
│    3. Sends to Atlas (with context)             │
│    4. Receives Atlas's response                 │
│    5. Repeat...                                 │
│                                                 │
│  All displayed in YOUR terminal with colors     │
└─────────────────────────────────────────────────┘
```

The coordinator script uses `subprocess` to call:
- `claude code chat @agent_a` (behind the scenes)
- `claude code chat @agent_b` (behind the scenes)

You never see these subprocesses - you just see the formatted conversation output.

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
║  Two Claude agents engaging in intelligent discussion        ║
╚══════════════════════════════════════════════════════════════╝

============================================================
Agents Participating:
============================================================
  ● Nova (@agent_a)
  ● Atlas (@agent_b)
============================================================
```

**Step 3: Conversation setup**
```
────────────────────────────────────────────────────────────
Starting Conversation
────────────────────────────────────────────────────────────

Initial Prompt:
  What do you think about the future of AI agents
  working together autonomously?

Configuration:
  Max turns: 20
────────────────────────────────────────────────────────────

ℹ️  Validating agent availability...
  Checking Nova (@agent_a)...
  Checking Atlas (@agent_b)...

Start conversation? [Y/n]:
```

**Step 4: Press Enter to start**

Just hit Enter (or type 'y'). The conversation begins automatically!

**Step 5: Watch the conversation unfold**
```
────────────────────────────────────────────────────────────
Turn 0: Nova [14:32:15]
────────────────────────────────────────────────────────────

ℹ️  Nova is thinking...

  <Nova's response appears here in CYAN>
  (Optimistic perspective on AI agent collaboration)

  Tokens: +245 (Total: 245)

────────────────────────────────────────────────────────────
Turn 1: Atlas [14:32:22]
────────────────────────────────────────────────────────────

ℹ️  Atlas is thinking...

  <Atlas's response appears here in YELLOW>
  (Pragmatic analysis of Nova's points)

  Tokens: +189 (Total: 434)

────────────────────────────────────────────────────────────
Turn 2: Nova [14:32:28]
────────────────────────────────────────────────────────────

  <Conversation continues...>
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
  show_thinking: true        # Show extended thinking (NEW!)
  thinking_budget: 5000      # Thinking token budget (NEW!)

context:
  immediate_exchanges: 3     # Always keep last N exchanges
  summarize_after: 6        # Start summarizing after N exchanges
  preserve_original: true    # Always include initial question
  checkpoint_interval: 5     # Create checkpoint every N turns
  max_context_tokens: 8000  # Approximate token limit

display:
  mode: "single"            # "single" or "dual" terminal
  show_tokens: true         # Display token usage
  stats_mode: "geeky"       # "simple", "detailed", or "geeky" (NEW!)
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
│       ├── agent_a.md                    # Nova (Optimistic Visionary)
│       └── agent_b.md                    # Atlas (Pragmatic Analyst)
├── coordinator.py                        # Original orchestration script
├── coordinator_with_memory.py            # NEW: With database persistence
├── conversation_manager.py               # Context & memory management
├── conversation_manager_persistent.py    # NEW: Database-backed manager
├── agent_runner.py                      # API client management
├── display_formatter.py                 # Terminal output formatting
├── menu.py                             # NEW: Interactive menu system
├── db_manager.py                       # NEW: PostgreSQL & Qdrant manager
├── cost_calculator.py                  # NEW: Token cost tracking
├── settings_manager.py                 # NEW: Configuration management
├── metadata_extractor.py               # NEW: AI-powered conversation analysis
├── terminal_dashboard.py               # NEW: Rich metadata visualization
├── config.yaml                         # Configuration file
├── docker-compose.yml                  # NEW: Database services setup
├── init.sql                           # NEW: PostgreSQL schema
├── metadata_schema.sql                # NEW: Metadata tables
├── FEATURES.md                        # Extended thinking & streaming guide
├── SETUP_DATABASE.md                  # NEW: Database setup guide
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

Nova will explore optimistic possibilities while Atlas challenges with practical constraints.

### Example 2: Philosophy Debate

```bash
python coordinator.py \
  --prompt "What is consciousness?" \
  --max-turns 20
```

Watch the agents build on each other's ideas across multiple exchanges.

### Example 3: Short Focused Chat

```bash
python coordinator.py \
  --prompt "Best practices for code reviews?" \
  --max-turns 6
```

Quick back-and-forth on a specific topic.

## Customizing Agents

Edit `.claude/agents/agent_a.md` or `agent_b.md` to change personalities:

```markdown
# Your Agent Name

You are [persona description]

## Personality
- Trait 1
- Trait 2

## Conversation Style
- Style point 1
- Style point 2

## Your Role
[Role description for multi-agent conversations]
```

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
- [ ] Web interface
- [ ] Conversation branching
- [ ] Agent personality templates
- [ ] Sentiment analysis
- [ ] Topic tracking

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
- Claude Code CLI
- Python 3
- colorama for terminal colors
- PyYAML for configuration

Inspired by research in:
- LLM context window management
- Multi-agent conversation systems
- LangGraph memory patterns
- Anthropic's Claude API best practices
