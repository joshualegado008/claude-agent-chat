# 🧠 Contextual Intelligence System - Complete Guide

## Overview

Your multi-agent conversation system now features **AI-powered contextual intelligence** that automatically extracts rich metadata, tracks conversation evolution, and provides real-time insights through an interactive terminal dashboard.

Inspired by [Anthropic's Contextual Retrieval research](https://www.anthropic.com/engineering/contextual-retrieval), this system understands your conversations deeply and makes them searchable, analyzable, and insightful.

---

## ✨ New Features

### 🎯 **Streamlined Conversation Start**
- Just enter a title → AI generates the perfect initial prompt
- Auto-extracts relevant tags using GPT-4o-mini
- No more manual prompt writing!

### 📊 **Rich Metadata Extraction**
Automatically tracks:
- **Current Vibe** - The atmosphere and direction of discussion
- **Content Type** - Debate, exploration, analysis, etc.
- **Technical Level** - Beginner to expert
- **Sentiment** - Positive, negative, neutral, mixed
- **Main Topics** - What agents are discussing
- **Key Concepts** - Important ideas emerging
- **Named Entities** - People, organizations, locations, technologies
- **Conversation Stage** - Opening, exploration, deep dive, synthesis
- **Complexity Level** - 1-10 scale
- **Engagement Quality** - How dynamic the conversation is
- **Emerging Themes** - New ideas coming to life

### ⚡ **Interactive Dashboard**
- Press **CTRL-C** during any conversation to pause
- View real-time stats and rich metadata
- Resume seamlessly
- Non-intrusive, always available

---

## 🚀 Quick Start

### 1. Setup (One Time)

```bash
# Install new dependencies
pip3 install openai

# Set OpenAI API key (for metadata extraction)
export OPENAI_API_KEY='sk-...'

# Update database schema
cat metadata_schema.sql | docker exec -i agent-chat-postgres psql -U agent_user agent_conversations

# Run the system
python3 contextual_coordinator.py
```

### 2. Start a Conversation

```bash
$ python3 contextual_coordinator.py

> Choose: 1 (Start new conversation)

> Conversation title: What does it mean when something is meta?

✨ AI generates prompt automatically!
🏷️  Auto-generated tags: meta, philosophy, self-reference, recursion

> Ready to start? Y
```

### 3. Watch the Magic

- Agents start conversing
- Metadata extracts every 3 turns
- Press **CTRL-C** anytime to pause

### 4. View the Dashboard

When you press CTRL-C:
```
⏸️  CONVERSATION PAUSED

What would you like to do?

  1. 📊 View Stats & Context
  2. 💬 Say Something (Coming Soon)
  3. 💾 Save Snapshot
  4. ⏹️  Stop Conversation
  5. ▶️  Resume
```

Choose **1** to see the full intelligence dashboard!

---

## 📊 Dashboard Features

### **Conversation Overview**
- Title, turns, tokens
- Current stage

### **Current Vibe**
- Real-time description of discussion atmosphere
- Updates as conversation evolves

### **Classification**
- Content type, technical level, sentiment
- Visual complexity bar (█████░░░░░)
- Engagement indicator (🔥🔥🔥)

### **Topics & Concepts**
- Main topics being discussed
- Key concepts emerging
- New themes developing
- Shows "+X more" for overflow

### **Named Entities**
- 👥 People mentioned
- 🏢 Organizations
- 📍 Locations
- 💻 Technologies

All organized, color-coded, and beautiful in your terminal!

---

## 🎮 How It Works

### **Streamlined Input Flow**

```
You enter: "What does it mean when something is meta?"
           ↓
     GPT-4o-mini analyzes
           ↓
   ┌──────────────────┬──────────────────┐
   ↓                  ↓                  ↓
Generated Prompt   Auto Tags      Ready to Start
"Let's explore..."  meta,          Agents begin!
                    philosophy,
                    recursion
```

### **Continuous Metadata Extraction**

```
Turn 0-2: Agents converse
    ↓
Turn 3: 📊 Metadata extraction
    ↓  (GPT-4o-mini analyzes last 5 exchanges)
    ↓
Turn 4-5: More conversation
    ↓
Turn 6: 📊 Another extraction
    ↓
... continues ...
```

### **Interrupt System**

```
Conversation running...
    ↓
User presses CTRL-C
    ↓
Conversation pauses gracefully
    ↓
Menu appears
    ↓
User selects "View Stats"
    ↓
Dashboard displays
    ↓
User presses any key
    ↓
Back to conversation!
```

---

## 🗄️ Database Schema

### **New Table: `conversation_metadata`**

Stores rich metadata snapshots:
- Analyzed every N turns (default: 3)
- Full metadata including topics, entities, sentiment
- Queryable for analytics

### **Useful Views**

**`conversation_latest_metadata`**
```sql
SELECT * FROM conversation_latest_metadata
WHERE conversation_id = 'your-id';
```

**`topic_frequency`**
```sql
SELECT * FROM topic_frequency
ORDER BY frequency DESC
LIMIT 10;
```

**`entity_analytics`**
```sql
SELECT * FROM entity_analytics
WHERE entity_type = 'technologies';
```

---

## 💡 Use Cases

### **Research & Analysis**
- Track how topics evolve over conversation
- Identify emerging themes
- Analyze sentiment shifts

### **Content Discovery**
- Find conversations by vibe or stage
- Search by named entities
- Discover related discussions

### **Quality Monitoring**
- Track engagement quality
- Monitor complexity levels
- Ensure conversations stay on track

### **Meta-Analysis**
- What topics do your agents discuss most?
- Which entities appear frequently?
- How do conversations typically evolve?

---

## 🎨 Customization

### **Adjust Metadata Extraction Frequency**

In `interactive_coordinator.py`:
```python
metadata_interval = 3  # Change to 1 for every turn, 5 for less frequent
```

### **Change Dashboard Colors**

In `terminal_dashboard.py`, modify colors:
```python
Fore.CYAN   # Main highlights
Fore.GREEN  # Positive/success
Fore.YELLOW # Warnings/neutral
Fore.RED    # Negative/critical
```

### **Add Custom Metadata Fields**

1. Update `metadata_extractor.py` analysis prompt
2. Add fields to database schema
3. Update dashboard display

---

## 📈 Analytics Queries

### **Most Discussed Topics**
```sql
SELECT
    topic,
    COUNT(*) as mentions,
    array_length(conversation_ids, 1) as num_conversations
FROM topic_frequency
WHERE frequency > 5
ORDER BY frequency DESC;
```

### **Conversation Evolution**
```sql
SELECT * FROM get_conversation_evolution('your-conversation-id');
```

### **Entity Co-occurrence**
```sql
SELECT
    jsonb_object_keys(named_entities) as entity_type,
    COUNT(*) as count
FROM conversation_metadata
GROUP BY entity_type;
```

### **Complexity Trends**
```sql
SELECT
    conversation_stage,
    AVG(complexity_level) as avg_complexity,
    COUNT(*) as stage_count
FROM conversation_metadata
GROUP BY conversation_stage
ORDER BY avg_complexity DESC;
```

---

## 🐛 Troubleshooting

### **"OPENAI_API_KEY not set"**
```bash
export OPENAI_API_KEY='sk-proj-...'
# Add to ~/.bashrc for persistence
```

### **Metadata extraction fails**
- Check OpenAI API key is valid
- Check API quota/billing
- System falls back to simple metadata

### **Dashboard doesn't show**
- Make sure terminal supports ANSI colors
- Try: `export TERM=xterm-256color`

### **CTRL-C doesn't pause conversation**
- Signal handling is automatic
- Should work during streaming responses
- Check that Python signal module is available

---

## 🔮 Future Enhancements

### **Coming Soon**
- [ ] User can inject messages during conversation
- [ ] Export metadata as reports
- [ ] Visual timeline of conversation evolution
- [ ] Automatic conversation summarization
- [ ] Theme clustering across conversations

### **Planned**
- [ ] Web dashboard for metadata
- [ ] Real-time metadata streaming
- [ ] Conversation recommendations
- [ ] Topic-based search
- [ ] Entity relationship graphs

---

## 📊 Cost Estimates

### **OpenAI API Usage**

**Per Conversation (20 turns):**
- Initial prompt generation: ~150 tokens × $0.000150/1K = $0.000023
- Tags extraction: ~100 tokens × $0.000150/1K = $0.000015
- Metadata extraction (6-7 times): ~500 tokens × $0.000150/1K × 7 = $0.000525

**Total per conversation: ~$0.0006** (less than a penny!)

**Monthly estimate (100 conversations): ~$0.06**

💡 Incredibly cheap for the value you get!

---

## 🎯 Best Practices

### **1. Choose Descriptive Titles**
Good: "The ethics of AI in healthcare decision-making"
Bad: "AI stuff"

Better titles = better prompts + better tags

### **2. Use Interrupts Strategically**
- Check metadata every 5-10 turns
- Use when conversation seems to shift topics
- Great for understanding complex discussions

### **3. Review Metadata Regularly**
- See what themes are emerging
- Identify valuable conversations
- Understand agent behavior patterns

### **4. Tag Conversations Consistently**
- Use similar tags for related topics
- Makes searching more effective
- Builds useful topic clusters

---

## 🌟 Example Session

```
$ python3 contextual_coordinator.py

> Title: What is consciousness?

✨ Generated Prompt:
   "Is consciousness simply an emergent property of complex
   information processing, or does it require something
   fundamentally different?"

🏷️ Tags: consciousness, philosophy, cognitive science, emergence

> Ready? Y

[Agents start conversing...]

Turn 0: Nova
💭 Nova is thinking...
Let me consider multiple perspectives on consciousness...

💬 Nova responds:
This is a fascinating question that sits at the intersection...

[Press CTRL-C]

⏸️ CONVERSATION PAUSED

> Choose: 1 (View Stats)

╔════════════════════════════════════════════════╗
║   📊 CONVERSATION INTELLIGENCE DASHBOARD      ║
╚════════════════════════════════════════════════╝

🎯 Conversation Overview
─────────────────────────────────────────────────
  Title: What is consciousness?
  Turns: 8
  Tokens: 4,521
  Stage: Deep Dive

💭 Current Vibe
┌────────────────────────────────────────────┐
│ Agents are engaging in philosophical      │
│ exploration of consciousness theories,     │
│ comparing materialist and dualist views    │
└────────────────────────────────────────────┘

🏷️ Classification
───────────────────────────────────────
  Content Type: Philosophical
  Technical Level: Advanced
  Sentiment: Neutral
  Complexity: ████████░░ (8/10)
  Engagement: 🔥🔥🔥 High

🎓 Main Topics
───────────────────────────────────────
  consciousness • philosophy • emergence •
  qualia • materialism • dualism •
  information processing • +2 more

💡 Key Concepts
───────────────────────────────────────
  hard problem • philosophical zombies •
  integrated information theory

🌟 Emerging Themes
───────────────────────────────────────
  free will • subjective experience •
  AI consciousness

🔍 Named Entities
───────────────────────────────────────
  👥 People: David Chalmers, Daniel Dennett
  🏢 Organizations: None identified
  📍 Locations: None identified
  💻 Technologies: neural networks, AI systems

─────────────────────────────────────────
Press any key to return to conversation...

[Press any key → back to conversation!]
```

---

## 🎓 Learning More

### **Anthropic's Contextual Retrieval**
Read the research: https://www.anthropic.com/engineering/contextual-retrieval

Key principles we implement:
- Rich context preservation
- Semantic understanding
- Continuous analysis
- Queryable insights

### **OpenAI GPT-4o-mini**
- Fast and cheap
- Great for structured extraction
- JSON mode for reliable parsing

---

## ✅ Quick Checklist

Before using:
- [ ] OPENAI_API_KEY set
- [ ] ANTHROPIC_API_KEY set
- [ ] Database schema updated
- [ ] Dependencies installed

To use:
- [ ] Enter descriptive title
- [ ] Let AI generate prompt
- [ ] Watch conversation
- [ ] Press CTRL-C to view dashboard
- [ ] Explore rich metadata

---

## 🎉 You're Ready!

You now have a **sophisticated contextual intelligence system** that makes your agent conversations:
- ✅ Easier to start
- ✅ Richer in metadata
- ✅ More discoverable
- ✅ Deeply analyzable
- ✅ Forward-compatible with web UI

Start a conversation and watch the intelligence unfold! 🧠✨

---

**Questions? Issues?**
- Check terminal output for helpful messages
- Review database views for analytics
- Experiment with different titles and topics

**Happy conversing!** 🚀
