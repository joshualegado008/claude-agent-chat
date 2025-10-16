# Database Setup Guide: Persistent Conversation Memory

This guide will help you set up PostgreSQL and Qdrant for persistent conversation storage with semantic search.

## 📋 Prerequisites

- Docker and Docker Compose installed
- Python 3.9+
- Anthropic API key configured

## 🚀 Quick Start (5 minutes)

### Step 1: Start Database Services

```bash
# Start PostgreSQL and Qdrant
docker-compose up -d

# Verify services are running
docker-compose ps
```

You should see:
```
NAME                    STATUS
agent-chat-postgres     Up (healthy)
agent-chat-qdrant       Up (healthy)
```

### Step 2: Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### Step 3: Run the Coordinator with Memory

```bash
python3 coordinator_with_memory.py
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────┐
│   Agent Conversation Coordinator    │
│   ├─ Start new conversation         │
│   ├─ Continue previous conversation │
│   └─ Search conversations           │
└─────────────────────────────────────┘
          │                  │
          ↓                  ↓
   ┌─────────────┐    ┌─────────────┐
   │ PostgreSQL  │    │   Qdrant    │
   │  Port 5432  │    │  Port 6333  │
   │             │    │             │
   │ - Metadata  │    │ - Vectors   │
   │ - Exchanges │    │ - Semantic  │
   │ - Context   │    │   Search    │
   └─────────────┘    └─────────────┘
```

---

## 📊 Database Schema

### PostgreSQL Tables

**conversations**
- Stores conversation metadata
- Title, initial prompt, agents, timestamps
- Status: active, completed, archived

**exchanges**
- Individual agent messages
- Thinking content (optional)
- Response content
- Token counts

**context_snapshots**
- Periodic conversation state saves
- Used for resuming conversations

**conversation_metadata** (Optional - Rich AI Features)
- AI-generated conversation insights
- Topics, concepts, themes, named entities
- Sentiment, complexity, engagement metrics
- Conversation stage tracking
- Required for the rich contextual intelligence dashboard

> **Note:** This table is automatically created during initialization. For existing installations without this table, see the [Migration Guide](#migrating-existing-databases) below.

---

## 🔍 Semantic Search with Qdrant

Qdrant stores vector embeddings of all exchanges, enabling:
- **Semantic search**: Find conversations by meaning, not just keywords
- **Similar conversations**: Discover related discussions
- **Topic clustering**: Group conversations by themes

### Current Implementation Note

The initial implementation uses a placeholder embedding function (hash-based). For production, you should use a real embedding model:

**Option 1: OpenAI (Recommended for production)**
```python
import openai

def generate_embedding(text: str) -> List[float]:
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding
```

**Option 2: Local Model (Free, runs locally)**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str) -> List[float]:
    return model.encode(text).tolist()
```

**Option 3: Cohere**
```python
import cohere

co = cohere.Client('your-api-key')

def generate_embedding(text: str) -> List[float]:
    response = co.embed(texts=[text], model='embed-english-v3.0')
    return response.embeddings[0]
```

To use a real embedding model, edit `db_manager.py` and replace the `_generate_embedding()` method.

---

## 🔄 Migrating Existing Databases

If you have an existing installation without the `conversation_metadata` table, you can apply the schema upgrade:

### Option 1: Apply to Running Database (Recommended)
```bash
# Apply metadata schema to existing database
cat metadata_schema.sql | docker exec -i agent-chat-postgres psql -U agent_user -d agent_conversations

# Verify table was created
docker exec agent-chat-postgres psql -U agent_user -d agent_conversations -c "\dt conversation_metadata"
```

### Option 2: Recreate Database (⚠️ Loses existing data)
```bash
# Stop services and remove volumes
docker-compose down -v

# Start fresh with complete schema
docker-compose up -d
```

> **Note:** After applying the migration, the rich contextual intelligence features (metadata dashboard, AI-powered insights) will be fully functional.

---

## 🎮 Usage Examples

### Starting a New Conversation

1. Run the coordinator
2. Select "Start a new conversation"
3. Enter title and initial prompt
4. Agents converse and everything is automatically saved

### Continuing a Previous Conversation

1. Select "Continue a previous conversation"
2. Choose from the list of recent conversations
3. Option A: Continue with original topic
4. Option B: Steer in a new direction with a new prompt

### Searching Past Conversations

1. Select "Search past conversations"
2. Enter search query (e.g., "AI ethics discussion")
3. Results ranked by semantic similarity
4. Open conversation to view or continue

---

## 🛠️ Management Commands

### View Database Logs
```bash
# PostgreSQL logs
docker-compose logs postgres

# Qdrant logs
docker-compose logs qdrant
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### Reset Database (⚠️ Deletes all data)
```bash
docker-compose down -v
docker-compose up -d
```

### Backup Conversations
```bash
# Backup PostgreSQL
docker exec agent-chat-postgres pg_dump -U agent_user agent_conversations > backup.sql

# Restore
cat backup.sql | docker exec -i agent-chat-postgres psql -U agent_user agent_conversations
```

---

## 📊 Database Access

### PostgreSQL Connection
```bash
# CLI access
docker exec -it agent-chat-postgres psql -U agent_user -d agent_conversations

# From Python
import psycopg2
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="agent_conversations",
    user="agent_user",
    password="agent_pass_local"
)
```

### Qdrant Web UI
Open in browser: http://localhost:6333/dashboard

### Useful SQL Queries

```sql
-- List all conversations
SELECT * FROM conversation_summaries;

-- Get conversation details
SELECT * FROM conversations WHERE id = 'your-uuid-here';

-- Find conversations by agent (dynamic agents have varied names)
SELECT * FROM conversations
WHERE agent_a_name LIKE 'Dr.%' OR agent_a_name LIKE 'Prof.%';

-- Find conversations by domain/topic
SELECT * FROM conversations WHERE title ILIKE '%physics%';

-- Count total exchanges
SELECT COUNT(*) FROM exchanges;

-- Get most active conversations
SELECT conversation_id, COUNT(*) as exchange_count
FROM exchanges
GROUP BY conversation_id
ORDER BY exchange_count DESC
LIMIT 10;

-- View dynamic agent names used
SELECT DISTINCT agent_name FROM exchanges ORDER BY agent_name;
```

---

## 🐛 Troubleshooting

### "Connection refused" errors

**Problem**: Can't connect to PostgreSQL or Qdrant

**Solution**:
```bash
# Check if containers are running
docker-compose ps

# Check if ports are available
lsof -i :5432  # PostgreSQL
lsof -i :6333  # Qdrant

# Restart services
docker-compose restart
```

### "Database does not exist"

**Problem**: PostgreSQL database not initialized

**Solution**:
```bash
# Recreate containers
docker-compose down -v
docker-compose up -d

# Wait 10 seconds for initialization
sleep 10

# Verify
docker exec agent-chat-postgres psql -U agent_user -d agent_conversations -c "SELECT 1;"
```

### "Collection not found" in Qdrant

**Problem**: Qdrant collection not created

**Solution**: The collection is auto-created on first use. If issues persist:
```bash
docker-compose restart qdrant
```

### Port conflicts

**Problem**: Ports 5432 or 6333 already in use

**Solution**: Edit `docker-compose.yml` to use different ports:
```yaml
ports:
  - "5433:5432"  # Changed from 5432:5432
```

Then update connection strings in your code.

---

## 🔒 Security Notes

### For Local Development
The default credentials are fine for local development:
- Username: `agent_user`
- Password: `agent_pass_local`

### For Production
**⚠️ IMPORTANT**: Change these settings in `docker-compose.yml`:

```yaml
environment:
  POSTGRES_USER: ${POSTGRES_USER}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

And use environment variables or secrets management.

---

## 📈 Performance Tips

### PostgreSQL
- Increase `shared_buffers` for larger datasets
- Add indexes on frequently queried columns
- Regular VACUUM operations

### Qdrant
- Adjust `collection_size` based on memory
- Use quantization for large datasets
- Consider clustering for high-volume production

---

## 🎯 Next Steps

1. ✅ Start services with `docker-compose up -d`
2. ✅ Run your first conversation
3. ✅ Try searching past conversations
4. ✅ Continue a previous conversation
5. 🔧 Replace placeholder embeddings with real model
6. 🚀 Build custom search features
7. 📊 Add analytics and insights

---

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Docker Compose Guide](https://docs.docker.com/compose/)
- [Anthropic API Docs](https://docs.anthropic.com/)

---

## 💡 Feature Ideas

Now that you have persistent memory, you can build:

- **Conversation Analytics**: Track topics, agent styles over time
- **Auto-tagging**: Classify conversations automatically
- **Topic Clustering**: Group related discussions
- **Conversation Summaries**: Generate summaries of long conversations
- **Export Features**: Export to PDF, Markdown, JSON
- **Web Interface**: Build a web UI for browsing conversations
- **Agent Performance**: Track which agents excel at which topics

Enjoy your enhanced multi-agent system with persistent memory! 🎉
