# Features Guide: Thinking Display & TRUE Real-Time Streaming

Your multi-agent system now supports **authentic real-time streaming** - no fake delays!

## 🧠 Feature 1: Extended Thinking

See what Claude is "thinking" before it responds - the internal reasoning process that leads to its answer.

### What It Looks Like

```
💭 Nova is thinking...
────────────────────────────────────────────────────────────
Let me consider this carefully. The user is asking about...
I should address both the technical and philosophical aspects...
The key tension here is between autonomy and reliability...
────────────────────────────────────────────────────────────

💬 Nova responds:
────────────────────────────────────────────────────────────
I think we're on the cusp of something truly transformative...
```

### How It Works

- Claude's thinking is displayed in **yellow/dim text**
- Thinking appears **instantly as generated**
- After thinking, the actual response streams in real-time
- Thinking tokens are included in the token budget

### Configuration

In your `config.yaml`:

```yaml
conversation:
  show_thinking: true  # Set to false to hide thinking
  thinking_budget: 5000  # Control thinking depth (1000-10000)
```

Or when calling directly in `coordinator.py`:

```python
coordinator.show_thinking = True  # Toggle here
coordinator.thinking_budget = 5000  # Adjust thinking depth
```

### When to Use

- **Enable thinking** for:
  - Debugging agent reasoning
  - Understanding decision-making process
  - Educational/demonstration purposes
  - Catching logic errors early

- **Disable thinking** for:
  - Production deployments
  - Faster conversations
  - Cleaner output
  - Lower token costs

---

## ⚡ Feature 2: TRUE Real-Time Streaming

Responses appear at the **actual speed Claude generates them** - no artificial delays or fake typing effects!

### How It Works

```python
# Traditional approach (FAKE - waits then simulates typing)
response = get_full_response()  # Wait for everything
for char in response:
    print(char)
    time.sleep(0.01)  # ❌ Artificial delay

# Our approach (REAL - shows tokens as generated)
for chunk in stream_response():
    print(chunk)  # ✅ Appears instantly as model generates it
```

### What You'll Experience

- **Text appears in chunks** as Claude generates tokens
- **No waiting** for the full response before seeing anything
- **Variable speed** - complex thoughts may pause, simple words flow quickly
- **Authentic generation** - you see exactly what the model is doing

### Benefits

✅ **Lower perceived latency** - see first words immediately
✅ **More engaging** - watch the response unfold naturally
✅ **No artificial delays** - respect the user's time
✅ **True transparency** - see actual model generation speed

---

## 🎛️ Complete Configuration Example

```yaml
# config.yaml
conversation:
  max_turns: 20
  initial_prompt: "Your conversation starter..."
  turn_delay: 1.0

  # FEATURE TOGGLES
  show_thinking: true  # Show internal reasoning
  thinking_budget: 5000  # Control thinking depth
  # Streaming is ALWAYS real-time - no speed config needed!
```

---

## 📊 Token Usage with Thinking

Extended thinking uses additional tokens. Here's the breakdown:

### Without Thinking
- Input: 1,000 tokens
- Output: 300 tokens
- **Total: 1,300 tokens**
- **Cost: ~$0.008**

### With Thinking
- Input: 1,000 tokens
- Thinking: 500 tokens (included in output)
- Output: 300 tokens
- **Total: 1,800 tokens**
- **Cost: ~$0.012**

💡 Thinking adds ~25-50% more tokens, but provides valuable insight into reasoning.

---

## 🎨 Customizing Display Colors

Edit `display_formatter.py` to change colors:

```python
AGENT_COLORS = {
    'Nova': Fore.CYAN,      # Change to Fore.BLUE, Fore.GREEN, etc.
    'Atlas': Fore.MAGENTA,  # Customize per agent
}
```

Edit `config.yaml` to set agent colors:

```yaml
agents:
  agent_a:
    name: "Nova"
    color: "cyan"  # Available: cyan, yellow, green, red, blue, magenta, white
  agent_b:
    name: "Atlas"
    color: "yellow"
```

Available colors: `BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE`

---

## 🔧 Advanced: Fine-Tuning Thinking Budget

Control how much thinking Claude does by adjusting `thinking_budget` in `config.yaml`:

**Budget Guidelines:**
- `1000-3000`: Quick thoughts
- `3000-5000`: Balanced (default)
- `5000-10000`: Deep reasoning
- `10000+`: Very thorough analysis

⚠️ Higher budgets = more tokens = higher cost

---

## 🚀 Why TRUE Streaming Matters

### The Problem with Fake Typing

Many chatbots use "fake typing" - they wait for the ENTIRE response, then simulate typing with `time.sleep()`. This:
- ❌ Wastes user time
- ❌ Hides when the model is actually done
- ❌ Feels dishonest

### Our Real-Time Approach

We show text **exactly as the model generates it**:
- ✅ First tokens appear in ~1-2 seconds
- ✅ You see progress immediately
- ✅ Complex reasoning shows natural pauses
- ✅ Simple responses flow quickly

**Result**: Feels more authentic and responsive!

---

## 🐛 Troubleshooting

### Thinking doesn't appear
- Check `show_thinking: true` in `config.yaml`
- Ensure you're using Claude Sonnet 4.5 model
- Verify the model name contains "sonnet-4" (e.g., `claude-sonnet-4-5-20250929`)

### Text appears in chunks (not smooth)
- **This is normal!** The model generates in chunks, not characters
- Chunk size depends on the model's internal generation
- This is the TRUE generation speed - not a bug

### Colors not showing
- Install colorama: `pip install colorama`
- Check `use_colors: true` in `config.yaml` under `display` section
- Windows users: Ensure ANSI support is enabled

### "Thinking" shows garbled text
- Terminal encoding issue
- Try: `export PYTHONIOENCODING=utf-8`

### Streaming errors
- Check your ANTHROPIC_API_KEY is set correctly
- Verify you have the latest `anthropic` Python package: `pip install --upgrade anthropic`
- Enable debug mode in `config.yaml`: `debug: true` under `logging`

---

## 💡 Pro Tips

1. **For demos**: Enable thinking to show reasoning process
2. **For development**: Enable thinking to debug logic
3. **For production**: Disable thinking for cleaner output
4. **For testing**: Disable thinking for faster execution
5. **Watch generation patterns**: Notice how complex reasoning has longer pauses
6. **Adjust thinking budget**: Start with 3000, increase if you want deeper reasoning

---

## 🎯 What Makes This Special

Unlike ChatGPT's interface which can fake typing effects, your system shows:
- **Authentic generation speed** - see model performance in real-time
- **Transparent thinking** - understand reasoning before responses
- **True streaming** - no artificial delays or tricks

This is as close as you can get to watching Claude "think" in real-time! 🧠⚡

---

## 🎯 Next Steps

Now that you have TRUE real-time streaming:

1. Watch how different prompts affect generation speed
2. Notice pauses during complex reasoning
3. See simpler responses flow quickly
4. Appreciate the authenticity of real-time AI
5. Experiment with different thinking budgets
6. Compare thinking vs. no-thinking mode

Enjoy watching your agents generate responses in **actual real-time**! 🚀

---

## 📝 Technical Implementation

### Architecture

The streaming system uses a generator pattern:

1. **agent_runner.py** - `send_message_streaming()` method yields chunks as they arrive
2. **display_formatter.py** - Methods to display thinking and responses in real-time
3. **coordinator.py** - Orchestrates the streaming display loop

### Stream Event Types

- `thinking_start` - Thinking block begins
- `thinking` - Thinking content chunk
- `text` - Response content chunk
- `complete` - Stream finished (includes token info)
- `error` - Error occurred

### Token Tracking

Both thinking and response tokens are tracked separately and displayed after each turn:

```
Tokens: +800 (Total: 5200)
```

This shows tokens used in the current turn and cumulative total across the conversation.
