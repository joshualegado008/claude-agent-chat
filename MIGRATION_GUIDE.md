# Migration Guide: Anthropic API Direct Integration

## Overview

Your multi-agent conversation system has been refactored to use the **Anthropic API directly** instead of subprocess calls to the Claude Code CLI. This creates truly independent agent instances.

## What Changed

### Before (Subprocess Approach)
- Used `subprocess` to spawn Claude Code CLI processes
- One Claude instance talking to itself via CLI
- Complex stdin/stdout parsing
- Risk of recursion loops
- No true agent independence

### After (API Approach)
- Direct Anthropic Python SDK integration
- **Two truly independent Claude instances**
- Clean API calls with proper message history
- Each agent has its own system prompt and context
- Much more reliable and maintainable

## Why This Is Better

1. **True Independence**: Each agent is a separate Claude instance with its own personality
2. **Cleaner Architecture**: No subprocess complexity
3. **Better Error Handling**: Direct API error messages
4. **Token Tracking**: Built-in usage monitoring
5. **More Control**: Fine-tune model, temperature, max_tokens per agent
6. **Scalable**: Easy to add more agents or features

## Migration Steps

### Step 1: Get Your API Key

1. Visit [https://console.anthropic.com/](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to **API Keys** in the left sidebar
4. Click **Create Key**
5. Copy your API key (starts with `sk-ant-api03-`)

**Important**: Keep this key secret! Never commit it to version control.

### Step 2: Set Environment Variable

Choose one of these methods:

#### Option A: For Current Session (Temporary)
```bash
export ANTHROPIC_API_KEY='sk-ant-api03-your-key-here'
```

#### Option B: Add to Shell Profile (Persistent)
```bash
# Add to ~/.zshrc or ~/.bashrc
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

#### Option C: Use .env File (Recommended for Projects)
```bash
# Create .env file
echo "ANTHROPIC_API_KEY=sk-ant-api03-your-key-here" > .env

# Add .env to .gitignore
echo ".env" >> .gitignore

# Install python-dotenv
pip install python-dotenv

# Add to top of coordinator.py:
from dotenv import load_dotenv
load_dotenv()
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `anthropic>=0.39.0` - Anthropic Python SDK
- `pyyaml>=6.0.1` - YAML config parsing (already had)
- `colorama>=0.4.6` - Terminal colors (already had)

### Step 4: Validate Setup

Run the test script to ensure everything is configured correctly:

```bash
python3 test_setup.py
```

This will check:
- ✅ All required packages are installed
- ✅ API key is set correctly
- ✅ Agent files exist
- ✅ config.yaml is valid
- ✅ API connection works

### Step 5: Run Your Coordinator

Your existing `coordinator.py` should work **without any changes**!

```bash
# Use default prompt from config.yaml
python3 coordinator.py

# Or specify a custom prompt
python3 coordinator.py --prompt "What is the nature of consciousness?"

# Or with custom max turns
python3 coordinator.py --prompt "Discuss AI ethics" --max-turns 10
```

## What Works Automatically

The refactored `agent_runner.py` maintains **100% backward compatibility** with your existing code:

- ✅ Same `AgentRunner` class interface
- ✅ Same `send_message_to_agent()` method signature
- ✅ Same `test_agent_availability()` method
- ✅ Works with your existing `coordinator.py` (no changes needed)
- ✅ Works with your existing `conversation_manager.py`
- ✅ Works with your existing `display_formatter.py`
- ✅ Loads agent personalities from `.claude/agents/agent_a.md` and `agent_b.md`

## Cost Information

### Pricing (as of 2025)
- **Claude Sonnet 4.5**: $3 per million input tokens, $15 per million output tokens
- Typical conversation turn: ~500-2000 tokens
- 20-turn conversation: ~$0.30-$0.60 total

### Cost Estimation for Your Setup
- **Test run** (3-5 turns): ~$0.05-$0.10
- **Full conversation** (20 turns): ~$0.30-$0.60
- **Daily testing** (10 conversations): ~$3-$6

**Bottom line**: Very affordable for development and testing!

## Configuration Options

You can customize each agent in `config.yaml`:

```yaml
agents:
  agent_a:
    name: "Nova"
    model: "claude-sonnet-4-5-20250929"  # Default
    max_tokens: 2048                      # Max response length
    temperature: 1.0                      # Creativity (0-1)

  agent_b:
    name: "Atlas"
    model: "claude-sonnet-4-5-20250929"
    max_tokens: 2048
    temperature: 0.7                      # More focused
```

## Troubleshooting

### Error: "ANTHROPIC_API_KEY environment variable not set"

**Solution**: Set your API key
```bash
export ANTHROPIC_API_KEY='sk-ant-api03-your-key-here'
```

Verify it's set:
```bash
echo $ANTHROPIC_API_KEY
```

### Error: "No module named 'anthropic'"

**Solution**: Install the package
```bash
pip install anthropic
```

### Error: "Agent file not found: .claude/agents/agent_a.md"

**Solution**: Your agent files already exist, but verify:
```bash
ls -la .claude/agents/
```

Should show:
- `agent_a.md` (Nova)
- `agent_b.md` (Atlas)

### API Errors (Rate Limits, etc.)

The Anthropic API has rate limits:
- **Requests per minute**: Varies by tier
- **Tokens per minute**: Varies by tier

If you hit limits, the error message will tell you when to retry.

## Advanced: Using Multiple Models

You can use different Claude models for different agents:

```yaml
agents:
  agent_a:
    name: "Nova"
    model: "claude-sonnet-4-5-20250929"  # Latest Sonnet

  agent_b:
    name: "Atlas"
    model: "claude-sonnet-4-5-20250929"  # Same for consistency

  # Or mix models:
  agent_c:
    name: "Opus"
    model: "claude-opus-4-20250514"       # More powerful (more expensive)
```

Available models:
- `claude-sonnet-4-5-20250929` - Best balance (recommended)
- `claude-opus-4-20250514` - Most capable (pricier)
- `claude-haiku-3-5-20241022` - Fastest/cheapest (good for testing)

## Debugging Tips

### Enable Debug Logging

In `config.yaml`:
```yaml
logging:
  debug: true
```

This will show token usage for each agent turn:
```
[DEBUG] Agent agent_a tokens: in=245 out=123
```

### Inspect Agent Responses

The refactored code logs all API errors with helpful messages.

### Test Individual Agents

You can test agents in isolation:

```python
from agent_runner import AgentRunner
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

runner = AgentRunner(config)

# Test agent availability
if runner.test_agent_availability('agent_a'):
    print("Agent A is working!")

    # Send a test message
    response = runner.send_message_to_agent(
        'agent_a',
        [],  # No context
        "Say hello!"
    )
    print(f"Response: {response}")
```

## What's Next?

Now that you have true multi-agent conversations:

1. **Experiment with personalities**: Edit `.claude/agents/*.md` files
2. **Try different models**: Update `config.yaml`
3. **Add more agents**: Create new agent files and config entries
4. **Build new features**: The API gives you full control

## Rollback Instructions

If you need to go back to the subprocess approach:

```bash
# The old agent_runner.py was overwritten, but you can recreate it from git history:
git checkout HEAD~1 agent_runner.py

# Or restore from backup if you made one
```

However, the API approach is **strongly recommended** - it's more reliable, maintainable, and gives you true multi-agent conversations.

## Questions?

- **API Documentation**: https://docs.anthropic.com/
- **Python SDK**: https://github.com/anthropics/anthropic-sdk-python
- **Pricing**: https://www.anthropic.com/pricing

---

**You're all set! Run `python3 test_setup.py` to validate, then start your multi-agent conversations with `python3 coordinator.py`**
