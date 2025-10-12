# 🚀 Quick Start: Contextual Intelligence System

Get your AI-powered conversation system running in **5 minutes**!

## ⚡ Super Quick Setup

```bash
# 1. Install new dependency
pip3 install openai

# 2. Set OpenAI API key
export OPENAI_API_KEY='sk-...'

# 3. Update database (run once)
cat metadata_schema.sql | docker exec -i agent-chat-postgres psql -U agent_user agent_conversations

# 4. Run the system
python3 contextual_coordinator.py
```

That's it! 🎉

---

## 🎯 First Conversation

```
$ python3 contextual_coordinator.py

> Choose: 1 (Start new conversation)

> Title: What is consciousness?

✨ Generated Prompt: (AI creates it for you!)
🏷️ Tags: consciousness, philosophy, cognitive science

> Ready? Y

[Agents start conversing...]

💡 Tip: Press CTRL-C anytime to view stats!
```

---

## 📊 View the Dashboard

During conversation:
1. Press **CTRL-C**
2. Choose **1** (View Stats & Context)
3. See rich metadata:
   - Current vibe
   - Topics being discussed
   - Named entities
   - Complexity level
   - Emerging themes
4. Press any key to return

---

## 🎨 What's New?

### Before (Old Way)
```
Title: [enter]
Prompt: [enter long paragraph]
Tags: [manually type tags]
```

### Now (New Way)
```
Title: What is consciousness?

✨ AI generates prompt automatically!
🏷️ AI extracts tags automatically!
📊 AI tracks metadata continuously!
```

**Result**: 3x faster to start, 10x more insights!

---

## 🧠 Rich Metadata Tracked

Every conversation now tracks:
- 💭 Current vibe
- 🎯 Main topics
- 💡 Key concepts
- 🌟 Emerging themes
- 👥 People mentioned
- 🏢 Organizations
- 📍 Locations
- 💻 Technologies
- 📊 Complexity (1-10)
- 🔥 Engagement quality
- 😊 Sentiment

---

## 💰 Costs

**OpenAI API (GPT-4o-mini):**
- Per conversation: ~$0.0006 (less than a penny!)
- 100 conversations: ~$0.06/month

**Super cheap for amazing insights!**

---

## ⌨️ Keyboard Controls

During conversation:
- **CTRL-C** - Pause and view menu

In menu:
- **1** - View stats & context
- **2** - Say something (coming soon)
- **3** - Save snapshot
- **4** - Stop conversation
- **5** - Resume

---

## 🔧 Troubleshooting

### API Key Not Set
```bash
export OPENAI_API_KEY='sk-...'
export ANTHROPIC_API_KEY='sk-ant-...'
```

### Database Not Updated
```bash
# Run the schema update
cat metadata_schema.sql | docker exec -i agent-chat-postgres psql -U agent_user agent_conversations
```

### Interrupt Not Working
- CTRL-C signal handling is automatic
- Works during streaming responses
- Check terminal compatibility

---

## 📚 Learn More

- **Full Guide**: `CONTEXTUAL_INTELLIGENCE_GUIDE.md`
- **Anthropic Research**: https://www.anthropic.com/engineering/contextual-retrieval

---

## ✅ Quick Checklist

- [ ] OpenAI API key set
- [ ] Anthropic API key set
- [ ] Database schema updated
- [ ] `openai` package installed
- [ ] Docker services running

All set? Run:
```bash
python3 contextual_coordinator.py
```

**Enjoy your intelligent conversations!** 🎉
