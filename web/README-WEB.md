# Claude Agent Chat - Web Interface 🌐

Modern web interface for watching AI agents discuss topics in real-time.

**⚠️ Important:** This web interface **coexists** with the terminal interface. Both use the same databases and conversations. You can use whichever you prefer!

## ✨ Features

### Priority Features (Implemented)

#### 1. 🚀 Streamlined Conversation Starter
- Title input with validation
- **AI-powered prompt generation** (click one button!)
- Auto-generated tags (editable)
- Beautiful, intuitive UI
- One-click start

#### 2. 💬 Live Conversation Stream
- **Real-time agent messages** with WebSocket streaming
- Animated thinking bubbles
- Typing indicators
- Agent avatars (Nova & Atlas)
- Pause/Resume controls
- Turn counter and progress tracking

#### 3. 📊 Interrupt Dashboard
- Pause button triggers beautiful modal
- **Rich metadata visualization:**
  - Current vibe (sentiment with emoji)
  - Topics as colorful badges
  - Entities with icons and mention counts
  - Complexity progress bar
  - Sentiment gauge
  - Key points and emerging themes
- Resume or Stop actions

### Additional Features

- **Dashboard:** View all conversations, stats, and quick access
- **Search:** Semantic search across conversation history (coming soon)
- **Geeky Stats:** Technical token breakdown, costs, context window analysis
- **Responsive Design:** Works on desktop, tablet, and mobile
- **Dark Mode Ready:** Full dark theme support (toggle coming soon)

## 🏗️ Architecture

```
web/
├── backend/                    # FastAPI server
│   ├── api.py                  # REST + WebSocket endpoints
│   ├── websocket_handler.py    # Real-time streaming
│   ├── bridge.py               # Imports existing Python code
│   └── requirements-web.txt    # Dependencies
│
└── frontend/                   # Next.js 14 app
    ├── app/                    # Pages (App Router)
    │   ├── page.tsx            # Dashboard
    │   ├── new/page.tsx        # New conversation
    │   └── conversation/[id]/  # Live viewer
    ├── components/             # React components
    ├── hooks/                  # Custom hooks
    ├── lib/                    # Utilities
    └── types/                  # TypeScript types
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (for databases)
- Anthropic API key
- OpenAI API key (optional, for AI-powered features)

### 1. Start Databases

```bash
# From project root
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Qdrant (port 6333)

### 2. Start Backend API

```bash
# Install dependencies
cd web/backend
pip install -r requirements-web.txt

# Also install main project dependencies (if not already)
cd ../..
pip install -r requirements.txt

# Start FastAPI server
cd web/backend
python api.py

# Or with uvicorn directly:
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### 3. Start Frontend

```bash
# Install dependencies
cd web/frontend
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

### 4. Open in Browser

Navigate to http://localhost:3000 and enjoy! 🎉

## 📋 Environment Variables

### Backend

Set these in your shell or `.env` file:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (enables AI-powered features)
OPENAI_API_KEY=sk-...

# Database (defaults shown)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agent_conversations
POSTGRES_USER=agent_user
POSTGRES_PASSWORD=agent_pass_local
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### Frontend

Create `web/frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 🔧 Development

### Backend Development

```bash
cd web/backend

# Run with auto-reload
uvicorn api:app --reload

# View API docs
open http://localhost:8000/docs
```

### Frontend Development

```bash
cd web/frontend

# Development server
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build
npm start
```

## 🎯 Usage

### Starting a New Conversation

1. Click "New Conversation" button
2. Enter a title (e.g., "The Future of AI in Healthcare")
3. Click "Generate Prompt & Tags with AI"
4. Review and edit the generated prompt
5. Add/remove tags as needed
6. Click "Start Conversation"

### Watching the Conversation

- Agents will discuss in real-time
- Thinking bubbles show internal reasoning
- Progress stats update after each turn
- Use controls to pause, resume, or stop

### Viewing Insights (Interrupt Dashboard)

1. Click "Pause" during conversation
2. Click "View Insights" button
3. Explore rich metadata:
   - Vibe and sentiment
   - Topics and entities
   - Complexity analysis
   - Key points and themes
4. Resume or stop the conversation

## 🔌 API Endpoints

### REST API

- `GET /api/conversations` - List recent conversations
- `GET /api/conversations/{id}` - Get specific conversation
- `POST /api/conversations` - Create new conversation
- `DELETE /api/conversations/{id}` - Delete conversation
- `POST /api/search` - Semantic search
- `POST /api/generate-prompt` - AI-generate prompt from title
- `GET /api/health` - Health check

### WebSocket

- `WS /ws/conversation/{id}` - Live conversation streaming

**Message Types:**
- `conversation_loaded` - Conversation initialized
- `ready` - Agents ready to start
- `turn_start` - New turn beginning
- `thinking_start/chunk` - Agent thinking
- `response_chunk` - Agent response streaming
- `turn_complete` - Turn finished with stats
- `conversation_complete` - Conversation finished

**Commands (send to WebSocket):**
- `{"command": "pause"}` - Pause conversation
- `{"command": "resume"}` - Resume conversation
- `{"command": "stop"}` - Stop and save
- `{"command": "get_metadata"}` - Request rich metadata

## 🤝 Coexistence with Terminal Interface

Both interfaces work together harmoniously:

### Shared Resources

✅ **Same PostgreSQL database** - All conversations stored centrally
✅ **Same Qdrant vectors** - Semantic search works across both
✅ **Same agent definitions** - Uses `.claude/agents/*.md` files
✅ **Same configuration** - Reads from `config.yaml`

### What You Can Do

- Start conversation in **web**, continue in **terminal**
- Start conversation in **terminal**, view in **web**
- Search conversations from either interface
- Both can run simultaneously without conflicts

### Terminal Interface (Unchanged)

```bash
# Still works exactly as before
python3 coordinator_with_memory.py
```

All existing functionality preserved:
- Interactive menu
- Conversation management
- Geeky stats mode
- Ctrl+C interrupts

## 📊 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **WebSockets** - Real-time streaming
- **Bridge Pattern** - Imports existing Python modules (no code duplication!)

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **TailwindCSS** - Utility-first styling
- **React Query** - Server state management
- **Lucide Icons** - Beautiful icons

### Shared
- **PostgreSQL** - Conversation storage
- **Qdrant** - Vector database for semantic search
- **Anthropic API** - Claude agent responses
- **OpenAI API** - Embeddings and metadata extraction (optional)

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check if databases are running
docker ps

# Check Python dependencies
pip install -r requirements-web.txt
pip install -r ../../requirements.txt

# Check API key
echo $ANTHROPIC_API_KEY
```

### Frontend won't connect to backend

```bash
# Check backend is running
curl http://localhost:8000/api/health

# Check .env.local file exists
cat web/frontend/.env.local

# Restart frontend
npm run dev
```

### WebSocket disconnects

- Check if backend is running
- Check browser console for errors
- WebSocket auto-reconnects after 3 seconds
- Refresh page if connection fails repeatedly

### No metadata/insights

- Requires OpenAI API key for AI-powered metadata extraction
- Configure in Settings menu or set `OPENAI_API_KEY` environment variable
- Basic stats still work without OpenAI

## 📝 Future Enhancements

- [ ] **Search Page** - Dedicated semantic search UI
- [ ] **Settings Page** - Configure API keys, models, preferences
- [ ] **Dark Mode Toggle** - Manual theme switching
- [ ] **Export Options** - Download conversations as PDF, Markdown, JSON
- [ ] **Shareable URLs** - Share conversations with others
- [ ] **Conversation Branching** - Fork conversations at specific turns
- [ ] **Multi-Agent Support** - More than 2 agents
- [ ] **Web Notifications** - Browser notifications when conversation completes
- [ ] **Mobile App** - Native iOS/Android apps

## 🤝 Contributing

Both terminal and web interfaces use the same backend code:
- Modifications to `db_manager.py`, `agent_runner.py`, etc. affect both
- Web-specific code is isolated in `/web/` directory
- Terminal-specific code is in project root

## 📄 License

Same as main project.

---

**Built with ❤️ to coexist with the terminal interface**

No terminal functionality was harmed in the making of this web interface. 🎭
