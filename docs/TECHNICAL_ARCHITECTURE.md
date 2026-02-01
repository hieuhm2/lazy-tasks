# TECHNICAL ARCHITECTURE

## 1. Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Language | Python 3.11+ | Core runtime |
| Web Framework | FastAPI | REST API, Webhook receiver |
| Agent Orchestration | LangGraph | Stateful agent workflow |
| LLM Utilities | LangChain | Prompt templates, output parsers |
| LLM Provider | OpenAI API (GPT-4o) | Primary LLM for reasoning |
| Embedding Model | OpenAI `text-embedding-3-small` (1536 dims) | Vector embeddings for RAG |
| Interface | `python-telegram-bot` v20+ | Webhook mode |

> **Note:** While Gemini could be used for summarization to reduce costs, the primary LLM is OpenAI for consistency. This can be revisited post-MVP.

---

## 2. Infrastructure (Dockerized)

All services run via `docker-compose.yml`:

```yaml
services:
  app:           # FastAPI + LangGraph
  postgres:      # PostgreSQL v15
  elasticsearch: # Elasticsearch v8 (single node)
  qdrant:        # Vector DB
  kibana:        # Log visualization (optional)
```

### 2.1 Environment Variables & Secrets

**Strategy:** Use a `.env` file for local development, Docker Secrets for production.

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | LLM API Key | `sk-...` |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `123456:ABC...` |
| `TELEGRAM_WEBHOOK_SECRET` | Secret token for webhook validation | `random-string-32-chars` |
| `POSTGRES_URL` | Database connection string | `postgresql://user:pass@host:5432/lazy_tasks` |
| `QDRANT_URL` | Qdrant endpoint | `http://qdrant:6333` |
| `ELASTICSEARCH_URL` | ES endpoint | `http://elasticsearch:9200` |
| `LANGSMITH_API_KEY` | (Optional) For tracing | `ls-...` |

**Security Rules:**
- `.env` file MUST be in `.gitignore`
- Production uses Docker Secrets mounted at `/run/secrets/`
- Never log API keys or tokens

---

## 3. Database Schema (PostgreSQL)

### 3.1 Core Tables

> **Note:** All tables use incremental BIGINT IDs starting from 1,000,000 for easy counting and human-readability.

```sql
-- Create sequences starting from 1000000
CREATE SEQUENCE tasks_id_seq START WITH 1000000;
CREATE SEQUENCE projects_id_seq START WITH 1000000;
CREATE SEQUENCE reminders_id_seq START WITH 1000000;
CREATE SEQUENCE calendar_events_id_seq START WITH 1000000;
CREATE SEQUENCE chat_logs_id_seq START WITH 1000000;
CREATE SEQUENCE documents_id_seq START WITH 1000000;

-- Tasks with full metadata
CREATE TABLE tasks (
    id BIGINT PRIMARY KEY DEFAULT nextval('tasks_id_seq'),
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'todo', -- todo, in_progress, done, cancelled
    priority INTEGER DEFAULT 3,        -- 1 (P1) to 5 (P5)
    complexity VARCHAR(10),            -- low, medium, high
    deadline TIMESTAMPTZ,
    tags TEXT[],                       -- Array of tags
    project_id BIGINT REFERENCES projects(id),
    parent_task_id BIGINT REFERENCES tasks(id), -- For subtasks
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projects for grouping tasks
CREATE TABLE projects (
    id BIGINT PRIMARY KEY DEFAULT nextval('projects_id_seq'),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active', -- active, paused, archived
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reminders linked to tasks
CREATE TABLE reminders (
    id BIGINT PRIMARY KEY DEFAULT nextval('reminders_id_seq'),
    task_id BIGINT REFERENCES tasks(id) ON DELETE CASCADE,
    remind_at TIMESTAMPTZ NOT NULL,
    message TEXT,
    is_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Calendar events (synced or manual)
CREATE TABLE calendar_events (
    id BIGINT PRIMARY KEY DEFAULT nextval('calendar_events_id_seq'),
    title VARCHAR(255) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    location TEXT,
    source VARCHAR(50) DEFAULT 'manual', -- manual, google_calendar, etc.
    external_id VARCHAR(255),            -- For sync reference
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat logs for RAG and analysis
CREATE TABLE chat_logs (
    id BIGINT PRIMARY KEY DEFAULT nextval('chat_logs_id_seq'),
    session_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,          -- user, assistant, system
    content TEXT NOT NULL,
    intent VARCHAR(50),                 -- Detected intent (create_task, query, chat, review)
    sentiment FLOAT,                    -- -1.0 to 1.0 (for reflection worker)
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- User state (key-value store)
CREATE TABLE user_state (
    key VARCHAR(100) PRIMARY KEY,       -- current_focus, status, energy_level, etc.
    value JSONB NOT NULL,               -- Flexible value storage
    confidence FLOAT DEFAULT 1.0,       -- Confidence of inferred state
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents for RAG ingestion
CREATE TABLE documents (
    id BIGINT PRIMARY KEY DEFAULT nextval('documents_id_seq'),
    title VARCHAR(255),
    content TEXT NOT NULL,
    source VARCHAR(100),                -- telegram, file_upload, note
    file_path VARCHAR(500),
    embedding_id VARCHAR(100),          -- Reference to Qdrant point ID
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- LangGraph checkpoints
CREATE TABLE langgraph_checkpoints (
    thread_id VARCHAR(100) PRIMARY KEY,
    checkpoint BYTEA NOT NULL,          -- Serialized graph state
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.2 Indexes

```sql
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_deadline ON tasks(deadline);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_chat_logs_session ON chat_logs(session_id);
CREATE INDEX idx_chat_logs_timestamp ON chat_logs(timestamp);
CREATE INDEX idx_reminders_remind_at ON reminders(remind_at) WHERE is_sent = FALSE;
CREATE INDEX idx_calendar_events_time ON calendar_events(start_time);
```

---

## 4. Telegram Webhook Security

### 4.1 Validation Strategy

```python
# In FastAPI route
@app.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    # 1. Validate secret token (set via setWebhook)
    if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret token")

    # 2. Parse and process update
    update = await request.json()
    # ... process
```

### 4.2 Webhook Setup

```bash
# Set webhook with secret token
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/webhook/telegram",
    "secret_token": "your-secret-token-32-chars"
  }'
```

---

## 5. Background Task Scheduling

### 5.1 Scheduler Choice: APScheduler

Using `APScheduler` with AsyncIO for background jobs (lighter than Celery for single-node deployment).

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Daily briefing at 8:00 AM
scheduler.add_job(send_daily_briefing, 'cron', hour=8, minute=0)

# Reflection worker at 10:00 PM
scheduler.add_job(run_reflection_worker, 'cron', hour=22, minute=0)

# Reminder checker every 5 minutes
scheduler.add_job(check_reminders, 'interval', minutes=5)

scheduler.start()
```

### 5.2 Startup Detection

For "laptop opens" trigger, use a systemd user service or a simple cron `@reboot`:

```bash
# ~/.config/systemd/user/lazy-tasks-startup.service
[Unit]
Description=Lazy Tasks Startup Trigger

[Service]
ExecStart=/usr/bin/curl -X POST http://localhost:8000/api/trigger/startup
Type=oneshot

[Install]
WantedBy=default.target
```

---

## 6. Error Handling & Retry Logic

### 6.1 LLM API Calls

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_llm(prompt: str) -> str:
    response = await openai_client.chat.completions.create(...)
    return response.choices[0].message.content
```

### 6.2 Rate Limiting

- **Telegram:** Max 30 messages/second to a user, 20 messages/minute to a group
- **OpenAI:** Implement token bucket or use `tenacity` with retry-after header

---

## 7. Monitoring Strategy

| Tool | Purpose |
|------|---------|
| **LangSmith** | Agent step tracing, token usage, latency |
| **Elasticsearch + Kibana** | Raw chat log analytics, search debugging |
| **Prometheus + Grafana** (Optional) | System metrics (CPU, memory, API latency) |

### 7.1 LangSmith Integration

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "lazy-tasks-production"
```

---

## 8. Qdrant Configuration

### 8.1 Collection Setup

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(url=settings.QDRANT_URL)

# Create collection for chat/document embeddings
client.create_collection(
    collection_name="lazy_tasks_memory",
    vectors_config=VectorParams(
        size=1536,  # text-embedding-3-small
        distance=Distance.COSINE
    )
)
```

### 8.2 Payload Schema

```json
{
  "source": "chat_log | document | task",
  "source_id": "uuid",
  "content_preview": "First 200 chars...",
  "timestamp": "2024-01-15T10:30:00Z",
  "tags": ["project_a", "finance"]
}
```

---

## 9. Directory Structure (Reference)

```text
lazy-tasks/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── telegram.py      # Webhook handler
│   │   │   ├── tasks.py         # Task CRUD endpoints
│   │   │   └── health.py
│   │   └── deps.py              # Dependency injection
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   └── security.py          # Auth utilities
│   ├── services/
│   │   ├── llm_service.py       # LLM wrapper
│   │   ├── retrieval_service.py # RAG (Qdrant + ES)
│   │   └── task_service.py      # Business logic
│   ├── agents/
│   │   ├── graph.py             # LangGraph definition
│   │   ├── nodes/
│   │   │   ├── receiver.py
│   │   │   ├── retriever.py
│   │   │   ├── analyzer.py
│   │   │   ├── refiner.py
│   │   │   └── executor.py
│   │   └── state.py             # AgentState TypedDict
│   ├── prompts/                 # See CODING_CONVENTION.md
│   ├── models/                  # SQLAlchemy models
│   ├── workers/
│   │   ├── reflection.py
│   │   └── scheduler.py
│   └── main.py
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── pyproject.toml
```
