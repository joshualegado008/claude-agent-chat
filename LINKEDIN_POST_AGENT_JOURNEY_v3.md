# Building a Self-Curating Agent System (V3)

## Two Versions: LinkedIn Feed + Full Article

---

# VERSION 1: LinkedIn Feed Post (250-300 words)

**I realized I'd been using "agents" all along—then built a system that creates its own experts.**

After a year with Claude Code, ChatGPT, and Copilot, the lightbulb was simple: these tools aren't just chats—they're *agentic assistants*: an LLM guided by a role/policy and orchestration logic. In the stricter sense, agents also add tools, memory, and control loops. I decided to build toward that.

**What I built**

* A tiny *agent factory* that generates specialized expert profiles on demand (e.g., "Cybersecurity: vulnerability assessment for cloud-native apps").
* A coordinator that assembles a panel (AI/ML + Security + Ethics), has them collaborate, and tracks outcomes.
* A lifecycle: rate agents on helpfulness/accuracy/relevance, reuse high performers, retire weak ones (self-curating roster).

**What worked**

* **Infinite specialization:** Ask about "LLM jailbreaking and context poisoning" → the system proposes an AI/ML expert, a Security specialist, and an Ethics lead. Preview them, approve, then they collaborate.
* **Cost control:** Profile creation costs pennies at typical token counts; reusing profiles has no creation cost (conversation tokens still apply).
* **UX fix:** Preview candidate experts first, then synthesize full profiles only after approval (avoids token burn on wrong selections).

**What I learned**

* Definitions matter: I use "agent" broadly; stricter definitions require autonomy + tools + memory + planning.
* Classification is sneaky: rule order causes mislabels—test with real scenarios early.
* Ratings drive quality: simple weighted scoring makes the roster better over time.

**Conceptually similar to AutoGen, LangGraph, CrewAI—this version emphasizes on-demand expert synthesis + lifecycle scoring.**

**Code:** [GitHub repo link] - Start with `agent_factory.py` and `agent_coordinator.py`.

If you're curious about agentic systems, you don't need a PhD—just a policy, a loop, and willingness to debug edge cases. What would *your* expert panel look like?

#ai #agents #machinelearning #softwareengineering #buildinpublic

---

# VERSION 2: Full Article (LinkedIn Article Mode)

## The Day I Realized I'd Been Using Agents All Along

### (And How I Built a Self-Curating AI System That Creates Its Own Experts)

After a year of "vibe coding" with Claude Code, ChatGPT, and Copilot, I had an embarrassingly simple revelation that changed how I think about AI tools entirely.

**I'd been using agents all along. I just didn't know to call them that.**

Let me explain.

## The Epiphany

I was deep in a coding session with Claude Code, working on yet another feature, when it hit me: Claude Code isn't just an AI assistant. It's an **agent**—in the broad sense I use here.

What I mean: An LLM wrapped in a system prompt that defines its personality, capabilities, and behavior, plus orchestration logic that manages the interaction. That's the basic formula.

Then the dominoes started falling:
- **Claude Web?** Agentic assistant. (LLM + "You are a helpful AI assistant..." + web interface)
- **ChatGPT?** Agentic assistant. (LLM + system prompt + chat UI)
- **GitHub Copilot?** Agentic assistant. (LLM + "You are a code completion expert..." + IDE integration)

Now, in industry and research, the term **"agent"** typically implies something stricter: *goal-directed autonomy + tool use + memory + a control loop* (planning/acting/observing). Think AutoGen, LangGraph, CrewAI.

What I realized was: the tools I'd been using were the building blocks for that stricter definition. They weren't magical black boxes—they were orchestrated policies over LLMs. And if *they* could work this way... **I could build toward the full agentic stack.**

## The Experiment That Started It All

My first thought was: "What if two Claude agents talked to *each other*?"

Not a revolutionary idea, but it was *my* idea, and I wanted to build it. So I started with something simple:

**Two agents, two personalities:**
- **Nova** - The optimistic visionary who explores possibilities
- **Atlas** - The pragmatic analyst who questions assumptions

I wrote two markdown files in `.claude/agents/`, gave them distinct personalities and conversation styles, and built a coordinator to orchestrate their turns. The result was fascinating - they had genuine back-and-forth discussions, building on each other's ideas, challenging assumptions, and exploring topics from multiple angles.

But there was a problem.

## The Limitation of Static Agents

Nova and Atlas were great for general discussions, but they were... generic. When I wanted to discuss the biomechanics of Olympic gymnastic routines, I got two generalists having a surface-level conversation. When I asked about LLM security vulnerabilities, they did their best, but neither was a true expert in cybersecurity or AI safety.

I needed **specialized agents**. Experts. Profiles that could be created on-demand based on the topic.

And that's when the real journey began.

## Building Blocks: The Five-Phase Evolution

### Phase 1A: The Foundation (The "Oh No, What Have I Started" Phase)

First, I needed data structures. How do you represent an agent profile? What metadata matters?

```python
@dataclass
class AgentProfile:
    agent_id: str
    name: str
    domain: AgentDomain  # SCIENCE, MEDICINE, HUMANITIES, TECHNOLOGY...
    primary_class: str   # "Cybersecurity", "AI & ML", "Philosophy"
    unique_expertise: str  # What makes this agent special?
    core_skills: List[str]
    system_prompt: str  # The personality + role definition
    created_at: datetime
    last_used: datetime
```

This was the lightbulb moment. An agent profile is just structured data. I don't need to train models or build infrastructure. I just need to define WHO they are and WHAT they know. The LLM provides the intelligence, the profile provides the identity.

**Key Insight:** In my broad sense, an "agent" is metadata + a system prompt + orchestration. The system manages their lifecycle.

### Phase 1B: Taxonomy & Classification (The "Organizing the Chaos" Phase)

If I'm going to create agent profiles on-demand, I need to organize them. I built a taxonomy system:
- **7 domains**: Science, Medicine, Humanities, Technology, Business, Law, Arts
- **23 classes**: Cardiology, Cybersecurity, Ancient Near East, AI/ML, Philosophy...
- **Classification system**: Analyze expertise descriptions and auto-classify using keyword matching

Here's where I hit my first real bug. I asked for a discussion on "LLM jailbreaking and context poisoning" and the system created:
- **Dr. Aria Chen** - AI & Machine Learning ✅
- **Dr. Tobias Hartmann** - History (Humanities) ❌ WHAT?
- **Prof. Elena Kowalski** - Philosophy (AI Ethics) ✅

The cybersecurity expert got classified as a *historian*?

I dove into the code and found the culprit: my classification logic checked AI/ML keywords, then Software Engineering keywords, then... **skipped Cybersecurity entirely** and jumped to Linguistics, which fell through to History.

```python
# THE BUG - No cybersecurity check!
if any(word in desc for word in ['machine learning', 'ai', 'neural']):
    return TECHNOLOGY, 'AI and Machine Learning'
if any(word in desc for word in ['software', 'code', 'programming']):
    return TECHNOLOGY, 'Software Engineering'
# ❌ MISSING: Cybersecurity priority check
if any(word in desc for word in ['linguistics', 'language']):
    return HUMANITIES, 'Linguistics'
# Falls through to History scoring...
```

**The Fix:** Added priority checking for cybersecurity keywords before other classifications.

**The Lesson:** Even simple rule-based systems have edge cases. Rule order matters. Test with real scenarios early.

### Phase 1C: The Agent Factory (The "Holy Shit, It's Working" Phase)

Now for the interesting part: creating agent profiles on-demand.

When a user starts a conversation, the system:
1. **Analyzes the topic** using a small LLM (e.g., GPT-4o-mini for cost efficiency)
2. **Determines required expertise** (e.g., "AI/ML" + "Cybersecurity" + "AI Ethics")
3. **Checks for existing profiles** with similar expertise (deduplication using similarity detection ~85-95% threshold)
4. **Generates lightweight candidate previews** (names, expertise summaries)
5. **Shows candidates to user for approval**
6. **Only then synthesizes full system prompts** for approved candidates

Here's the key insight: **Use an LLM to create agent profiles for other LLMs.**

The factory prompt is elegant in its simplicity:

```
You are an expert agent profile creator. Generate a specialized AI agent for:

Expertise: "Vulnerability assessment and mitigation for cloud-native applications"
Domain: Technology
Class: Cybersecurity

Provide:
1. Professional name (e.g., "Dr. Sarah Thompson")
2. Unique expertise (1 sentence - what makes them special)
3. 5-7 core skills
4. Complete system prompt defining their personality and expertise

Be specific. Be professional. Make them feel real.
```

The LLM returns a fully-formed agent profile. Complete with personality, speaking style, and domain expertise. In ~2 seconds.

**Example Output:**

```json
{
  "name": "Dr. Marcus Wei",
  "unique_expertise": "Specialized in penetration testing and secure architecture design for cloud-native applications with focus on container security and zero-trust models",
  "core_skills": [
    "vulnerability assessment",
    "penetration testing",
    "threat modeling",
    "security architecture",
    "OWASP Top 10",
    "cloud security (AWS/Azure/GCP)",
    "incident response"
  ],
  "system_prompt": "You are Dr. Marcus Wei, a cybersecurity expert..."
}
```

That profile is now **saved**, added to the registry, and becomes available for future conversations.

**Cost Reality Check:** Profile creation costs pennies at typical token counts (varies by LLM pricing tiers and token usage - check your provider's $/M-token rates). Reusing an existing profile has **no creation cost** (though conversation tokens still apply).

### Phase 1D: Ratings & Lifecycle (The "Natural Selection for AI" Phase)

Creating profiles is one thing. Managing them over time is another.

I implemented a **5-dimension rating system**:
- Helpfulness (30% weight)
- Accuracy (25% weight)
- Relevance (20% weight)
- Clarity (15% weight)
- Collaboration (10% weight)

After each conversation, users rate the agents. Points accumulate. Agents level up:

**NOVICE** (0-9 pts) → **COMPETENT** (10-24 pts) → **EXPERT** (25-49 pts) → **MASTER** (50-99 pts) → **LEGENDARY** (100-199 pts) → **ELITE** (200+ pts, never retired)

Good agents stick around. Weak agents fade away. The system self-curates.

The lifecycle tiers add another dimension:
- **HOT**: Currently in conversation
- **WARM**: Used within 7 days (instant retrieval)
- **COLD**: Used 7-90 days ago
- **ARCHIVED**: 90+ days unused
- **RETIRED**: Deleted, but patterns saved for learning

Over time, you build a roster of proven experts.

### Phase 1E: Integration & Self-Curation (The "It's Alive!" Phase)

This is where everything came together.

**The Flow:**
```
User: "Let's discuss LLM jailbreaking and context poisoning"
   ↓
System analyzes topic → Identifies expertise needs:
   • AI & Machine Learning
   • Cybersecurity
   • AI Ethics/Safety
   ↓
Checks existing agents:
   • Finds Dr. Aria Chen (AI/ML, rated 4.5/5, reuse)
   • No cybersecurity expert → generate candidate preview
   • Finds Prof. Elena Kowalski (AI Ethics, Elite tier, reuse)
   ↓
Shows preview panel:
   🤖 Candidate Agents for This Conversation

   1. Dr. Aria Chen - AI and Machine Learning
      Expertise: Large language models and ML systems
      Status: ⭐ Proven (4.5/5 avg, 12 conversations)

   2. Dr. Marcus Wei - Cybersecurity (NEW - Preview)
      Expertise: Vulnerability assessment for cloud-native apps
      Status: 🆕 Candidate (will be created if approved)

   3. Prof. Elena Kowalski - Philosophy (AI Ethics)
      Expertise: AI ethics and technology policy
      Status: 🏆 Elite tier (4.8/5 avg, 45 conversations)

   Approve these agents? [Y/n/r]:
   ↓
User approves → Dr. Marcus Wei profile fully synthesized
   ↓
Conversation begins → Agents collaborate
   ↓
User rates agents → System learns → Roster improves
```

**Here's a short transcript snippet showing them in action:**

```
Dr. Aria Chen (AI/ML): The core vulnerability in prompt injection
attacks stems from the lack of clear boundaries between instruction
and data in LLM context windows...

Dr. Marcus Wei (Cybersecurity): From a security architecture
perspective, we need defense-in-depth. Input validation alone isn't
sufficient—we should treat user input as untrusted by default and
implement sandboxing at the model layer...

Prof. Elena Kowalski (Ethics): But we must also consider the
incentive structures. If we make LLMs too restrictive to prevent
jailbreaking, we risk limiting legitimate research into model
behavior...
```

Next time someone asks about AI security, the system already has Dr. Marcus Wei. He's proven. Rated. Ready.

## The Bugs That Taught Me Everything

Building this wasn't smooth sailing. Here are the three bugs that taught me the most:

### Bug 1: The Multi-Line Title Disaster
Users pasted conversation titles with URLs across multiple lines. Python's `input()` only reads ONE line. Result? Lost URLs, confused system.

**Fix:** Multi-line input handler. Press Enter twice to submit.

**Lesson:** Never assume user input patterns. Test with real copy-paste scenarios.

### Bug 2: The Classification Nightmare
Covered earlier - cybersecurity classified as history due to missing priority check.

**Lesson:** Priority ordering matters in rule-based systems. Edge cases *will* find you. Test classification with diverse real-world examples.

### Bug 3: The Token-Burning Approval Problem (The Important One)
Initial implementation: System *created full agent profiles*, **then** asked for approval. If wrong agents were selected, you'd already burned API tokens for nothing.

**First attempted fix (still wrong):** "Create agents first, show them, then get approval before starting conversation."
- Problem: Still burns tokens creating full profiles before user confirms.

**Actual fix:**
1. Generate **lightweight candidate previews** (name + 1-sentence expertise) - cheap, fast
2. Show preview panel to user
3. Get approval
4. **Only then** synthesize full system prompts for approved candidates

**Lesson:** In systems with costs (API calls, tokens, time), fail fast and fail cheap. Get user confirmation before expensive operations. Preview before synthesis.

## What This Actually Unlocks

This isn't just a cool experiment. The implications are tangible:

### 1. **Infinite Specialization**
Need to explore how jazz improvisation relates to mathematical patterns? System creates:
- Music theory expert (jazz specialization)
- Mathematician (pattern recognition, chaos theory)
- Cognitive scientist (creativity and spontaneity)

Need to optimize React component re-renders in a massive application? System creates:
- Frontend architecture specialist
- React performance expert
- State management guru

**The specialization is bounded only by the LLM's knowledge**. Which is substantial.

### 2. **Collaborative Intelligence**
Agents aren't just responding to you. They're responding to **each other**. They build on ideas, challenge assumptions, and explore tangents you wouldn't have thought of.

It's like assembling an expert panel for every question.

### 3. **Self-Improving Systems**
The rating system means the **agent roster gets better over time**. Good agents get reused. Weak agents retire. The system learns which expertise profiles work best for which topics.

You're not just building agents. You're building an **ecosystem that curates itself**.

### 4. **Cost-Effective Expertise**
- Profile creation: Pennies per agent (varies by token usage and provider rates)
- Reusing existing profile: No creation cost (conversation tokens still apply)
- Conversation with 3 agents (10 turns): Typical costs scale with tokens used

Compare that to hiring human experts for a consultation. The economics are compelling.

## Framework Context

**This approach is conceptually similar to established agentic orchestration frameworks** (AutoGen, LangGraph, CrewAI). The differentiator here is:
- **On-demand expert synthesis**: Rather than pre-defined agent pools
- **Lifecycle scoring**: Performance-based curation and retirement
- **Self-curating roster**: System learns which agents work over time

## The Bigger Picture: Building an Agentic Stack

Here's what keeps me up at night (in a good way):

I built this system **using Claude Code**—which is itself an agentic assistant. I used that agent to create a system that creates other agent profiles. Those agents collaborate to answer questions. Users rate those agents. The ratings inform which profiles get created in the future.

**It's an agentic stack all the way down.**

And the barrier to entry? You need:
1. Claude Code (or any LLM with a good API)
2. Python basics
3. Curiosity
4. Willingness to debug weird edge cases

That's it. No PhD. No ML training. No fancy infrastructure.

## The Future Is Weirder Than You Think

Right now, my system creates agent profiles for conversations. But there's no technical reason it couldn't:
- Create agents to write code
- Create agents to review PRs
- Create agents to analyze data
- Create agents to... **create better agent profiles**

We're not far from systems where:
- Agents specialize in agent creation
- Agents review other agents' performance
- Agents decide when to create new agents
- Agents deprecate obsolete agents

**The system manages itself.**

And the wildest part? This isn't science fiction. This isn't AGI. This is just:
- Good data structures
- Thoughtful prompts
- A bit of orchestration code
- LLMs that already exist

## Limitations & Risks (Let's Be Real)

No technology is without risks. Here are the key ones:

1. **Prompt injection**: Malicious users could try to manipulate agent system prompts
2. **Evaluation drift**: Rating systems can be gamed or biased over time
3. **Privacy**: Conversation content should be handled with care
4. **Cost management**: Uncontrolled agent creation could rack up API costs
5. **Quality control**: LLM-generated profiles need validation

**Mitigations I've implemented:**
- Preview + approval gates
- Cost tracking and limits
- User ratings for quality control
- Deduplication to prevent redundant agents

But this is an evolving system. Caution warranted.

## Your Turn

If you've made it this far, you're probably thinking one of two things:

1. "That's cool, but I could never build something like that."
2. "Wait, I could totally build something like that."

If you're in camp 1: **You're wrong**. A year ago, I didn't know what a system prompt was. I just started playing with Claude Code, got curious, and followed the breadcrumbs.

If you're in camp 2: **You're right**. Do it. Build something weird. Break things. Fix the bugs. Share what you learn.

The tools are already in your hands. Claude Code, ChatGPT, Gemini - they're not black boxes. They're **building blocks** for agentic systems.

## The Code

The entire system is open source:

**Repository:** [Insert your actual GitHub repo URL here]

**Key files to explore:**
- `src/agent_factory.py` - Where the profile generation happens
- `src/agent_taxonomy.py` - Classification system
- `src/agent_coordinator.py` - Orchestration logic
- `coordinator_with_memory.py` - Main entry point
- `README.md` - Setup and usage guide

Clone it. Break it. Make it better. Tell me what you build.

## Final Thoughts

A year ago, I was just trying to make two AI assistants talk to each other for fun. Today, I have a system that creates specialized expert profiles on-demand, rates their performance, and self-curates over time.

And the most important lesson?

**The tools we've been using - Claude Code, ChatGPT, Copilot - aren't endpoints. They're starting points.**

Every agentic assistant you use is a template for agents you could build. Every system prompt is a blueprint. Every API call is a building block.

We're not just *using* AI anymore. We're **composing** it. Orchestrating it. Building systems that build systems.

And honestly? I think that's way cooler than any single AI tool could ever be.

---

**What's your "aha moment" with AI tools? What are you building?**

Drop a comment or DM me. I'd love to hear about your experiments, your weird projects, and the bugs that taught you the most.

*P.S. - If you try to discuss "designing sustainable life support systems for Mars colonies" with the system and it assembles an aerospace engineer, an ecologist, and a systems architect in ~5 seconds... you'll understand why I'm excited. The system creates exactly the experts you need. Every time.*

---

**Tags:** #ai #agents #machinelearning #softwareengineering #automation #buildinpublic #innovation #claudecode #openai

---

**About the Author:**
A developer who asks "what if?" a little too often and actually tries to build the answer. Currently exploring agentic systems, emergent behavior, and the question of whether agents creating agents counts as proper recursion.

*Built with curiosity, caffeine, and Claude Code.*