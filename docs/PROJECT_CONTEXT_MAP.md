# PROJECT CONTEXT MAP

> **Purpose:** This document acts as a "Knowledge Graph" for the PAEA project, linking features to technical components. Use this as a quick reference to understand system relationships and maintain context across long development sessions.

---

## 1. PROJECT IDENTITY

```
┌──────────────────────────────────────────────────────────────────┐
│  PAEA - Personal AI Executive Assistant                          │
├──────────────────────────────────────────────────────────────────┤
│  Type:     Local-first Agentic AI Assistant                      │
│  User:     Vietnamese Software Engineer (AI/DL Researcher)       │
│  Interface: Telegram Bot (Webhook)                               │
│  Core Tech: LangGraph + FastAPI + PostgreSQL + Qdrant            │
│  Style:    VietTech (Vietnamese + English tech terms)            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. FEATURE → COMPONENT MAPPING

### F1: Intelligent Task Capture (Refiner Agent)

```
┌─────────────────────────────────────────────────────────────────┐
│ FEATURE: Smart Task Clarification                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Input                                                     │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │  Analyzer   │────▶│   Refiner   │────▶│  Executor   │       │
│  │   Node      │     │    Node     │     │    Node     │       │
│  └─────────────┘     └──────┬──────┘     └──────┬──────┘       │
│                             │                    │              │
│                   (if incomplete)         (if complete)        │
│                             │                    │              │
│                             ▼                    ▼              │
│                      ┌───────────┐       ┌────────────┐        │
│                      │ Telegram  │       │ PostgreSQL │        │
│                      │  Reply    │       │   tasks    │        │
│                      └───────────┘       └────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

COMPONENTS INVOLVED:
├── Agents:       analyzer.yaml, refiner.yaml
├── Templates:    task_clarification.jinja2, task_confirmation.jinja2
├── DB Tables:    tasks, projects, reminders
├── Services:     task_service.py, llm_service.py
└── API:          POST /webhook/telegram
```

---

### F2: Contextual Memory (RAG Scanner)

```
┌─────────────────────────────────────────────────────────────────┐
│ FEATURE: Hybrid Search & Memory Retrieval                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Query: "Tháng trước có note gì về budget?"                │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────┐                                                │
│  │   Scanner   │                                                │
│  │    Node     │                                                │
│  └──────┬──────┘                                                │
│         │                                                       │
│    ┌────┴────┐                                                  │
│    ▼         ▼                                                  │
│ ┌───────┐ ┌───────┐                                             │
│ │Qdrant │ │  ES   │  ◀── Hybrid Search                          │
│ │Vector │ │Keyword│                                             │
│ └───┬───┘ └───┬───┘                                             │
│     │         │                                                 │
│     └────┬────┘                                                 │
│          ▼                                                      │
│    ┌───────────┐                                                │
│    │  Reranker │  ◀── Combine & Score Results                   │
│    └─────┬─────┘                                                │
│          ▼                                                      │
│    ┌───────────┐                                                │
│    │ Synthesize│  ◀── LLM Summarization                         │
│    └─────┬─────┘                                                │
│          ▼                                                      │
│    Telegram Reply                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

COMPONENTS INVOLVED:
├── Agents:       scanner.yaml
├── DB Tables:    chat_logs, documents
├── Vector DB:    Qdrant (paea_memory collection)
├── Search:       Elasticsearch (chat logs index)
├── Services:     retrieval_service.py, llm_service.py
└── Embedding:    OpenAI text-embedding-3-small (1536 dims)
```

---

### F3: Proactive Planning (Manager Worker)

```
┌─────────────────────────────────────────────────────────────────┐
│ FEATURE: Daily Briefing & Reflection                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   SCHEDULER (APScheduler)               │   │
│  │                                                         │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │   │ 8:00 AM     │  │ 10:00 PM    │  │ Every 5 min │    │   │
│  │   │ Briefing    │  │ Reflection  │  │ Reminders   │    │   │
│  │   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │   │
│  │          │                │                │           │   │
│  └──────────┼────────────────┼────────────────┼───────────┘   │
│             │                │                │               │
│             ▼                ▼                ▼               │
│       ┌───────────┐   ┌───────────┐   ┌───────────┐          │
│       │  Manager  │   │  Manager  │   │  Reminder │          │
│       │  Agent    │   │  Agent    │   │  Checker  │          │
│       └─────┬─────┘   └─────┬─────┘   └─────┬─────┘          │
│             │               │               │                 │
│             ▼               ▼               ▼                 │
│       ┌───────────┐   ┌───────────┐   ┌───────────┐          │
│       │ Telegram  │   │user_state │   │ Telegram  │          │
│       │ Message   │   │  UPDATE   │   │ Message   │          │
│       └───────────┘   └───────────┘   └───────────┘          │
│                                                               │
└───────────────────────────────────────────────────────────────┘

COMPONENTS INVOLVED:
├── Agents:       manager.yaml
├── Templates:    daily_briefing.jinja2
├── DB Tables:    tasks, user_state, calendar_events, reminders
├── Services:     reflection.py, scheduler.py
├── Triggers:     APScheduler (cron jobs)
└── External:     Telegram Bot API (send message)
```

---

### F4: Visualization & Reporting

```
COMPONENTS INVOLVED:
├── Templates:    daily_briefing.jinja2, weekly_report.jinja2
├── DB Tables:    tasks (aggregation queries)
├── Services:     report_service.py
└── Output:       Telegram (Markdown formatted text)
```

---

## 3. DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PAEA DATA FLOW                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   TELEGRAM                         FASTAPI                              │
│  ┌─────────┐                      ┌─────────┐                           │
│  │  User   │ ───── Webhook ─────▶ │  /api   │                           │
│  │ Message │                      │ /webhook│                           │
│  └─────────┘                      └────┬────┘                           │
│       ▲                                │                                │
│       │                                ▼                                │
│       │                         ┌─────────────┐                         │
│       │                         │  LANGGRAPH  │                         │
│       │                         │   ENGINE    │                         │
│       │                         └──────┬──────┘                         │
│       │                                │                                │
│       │         ┌──────────────────────┼──────────────────────┐        │
│       │         ▼                      ▼                      ▼        │
│       │   ┌───────────┐         ┌───────────┐         ┌───────────┐   │
│       │   │ PostgreSQL│         │   Qdrant  │         │Elasticsearch│   │
│       │   │           │         │           │         │           │   │
│       │   │ • tasks   │         │ • vectors │         │ • logs    │   │
│       │   │ • state   │         │ • metadata│         │ • search  │   │
│       │   │ • logs    │         │           │         │           │   │
│       │   └───────────┘         └───────────┘         └───────────┘   │
│       │                                                                │
│       │                         ┌───────────┐                          │
│       └──────── Response ────── │  OpenAI   │                          │
│                                 │    API    │                          │
│                                 └───────────┘                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. DATABASE ENTITY RELATIONSHIPS

> **Note:** All IDs are BIGINT starting from 1,000,000 for easy counting.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ENTITY RELATIONSHIPS                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌───────────┐                                                         │
│   │ projects  │                                                         │
│   │───────────│                                                         │
│   │ id (PK)   │◄─────────────┐   BIGINT, starts at 1000000             │
│   │ name      │              │                                         │
│   │ status    │              │                                         │
│   └───────────┘              │                                         │
│                              │                                         │
│   ┌───────────┐         ┌────┴────┐         ┌───────────┐              │
│   │ reminders │         │  tasks  │         │ chat_logs │              │
│   │───────────│         │─────────│         │───────────│              │
│   │ id (PK)   │         │ id (PK) │         │ id (PK)   │              │
│   │ task_id   │────────▶│ content │         │session_id │              │
│   │ remind_at │   (FK)  │ status  │         │ role      │              │
│   │ is_sent   │         │priority │         │ content   │              │
│   └───────────┘         │deadline │         │ intent    │              │
│                         │ tags[]  │         │ sentiment │              │
│                         │project_id│        │ timestamp │              │
│                         │parent_id│─┐       └───────────┘              │
│                         └─────────┘ │                                  │
│                              ▲      │                                  │
│                              └──────┘ (self-reference for subtasks)    │
│                                                                         │
│   ┌────────────┐        ┌───────────┐       ┌───────────────────┐      │
│   │ user_state │        │ documents │       │langgraph_checkpoints│     │
│   │────────────│        │───────────│       │───────────────────│      │
│   │ key (PK)   │        │ id (PK)   │       │ thread_id (PK)    │      │
│   │ value      │        │ content   │       │ checkpoint (BYTEA)│      │
│   │ confidence │        │embedding_id│       │ metadata (JSONB)  │      │
│   └────────────┘        └───────────┘       └───────────────────┘      │
│                                                                         │
│   ┌─────────────────┐                                                   │
│   │ calendar_events │                                                   │
│   │─────────────────│                                                   │
│   │ id (PK)         │                                                   │
│   │ title           │                                                   │
│   │ start_time      │                                                   │
│   │ source          │                                                   │
│   └─────────────────┘                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. AGENT STATE MACHINE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       LANGGRAPH STATE MACHINE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                        ┌─────────────┐                                  │
│                        │   START     │                                  │
│                        └──────┬──────┘                                  │
│                               │                                         │
│                               ▼                                         │
│                        ┌─────────────┐                                  │
│                        │  RECEIVER   │ ◀── Telegram webhook             │
│                        └──────┬──────┘                                  │
│                               │                                         │
│                               ▼                                         │
│                        ┌─────────────┐                                  │
│                        │  RETRIEVER  │ ◀── RAG (Qdrant + ES)            │
│                        └──────┬──────┘                                  │
│                               │                                         │
│                               ▼                                         │
│                        ┌─────────────┐                                  │
│                        │  ANALYZER   │ ◀── Intent classification        │
│                        └──────┬──────┘                                  │
│                               │                                         │
│              ┌────────────────┼────────────────┐                        │
│              ▼                ▼                ▼                        │
│       ┌───────────┐   ┌───────────┐    ┌───────────┐                   │
│       │create_task│   │query_memory│    │   chat    │                   │
│       └─────┬─────┘   └─────┬─────┘    └─────┬─────┘                   │
│             │               │                │                          │
│             ▼               │                │                          │
│       ┌───────────┐         │                │                          │
│       │  REFINER  │◀────────┼────────────────┘                          │
│       └─────┬─────┘         │                                           │
│             │               │                                           │
│    ┌────────┴────────┐      │                                           │
│    ▼                 ▼      ▼                                           │
│ [incomplete]     [complete]                                             │
│    │                 │                                                  │
│    ▼                 ▼                                                  │
│ ┌──────┐       ┌───────────┐                                            │
│ │ LOOP │       │ EXECUTOR  │ ──▶ Write to DB                            │
│ │ BACK │       └─────┬─────┘                                            │
│ └──┬───┘             │                                                  │
│    │                 ▼                                                  │
│    │           ┌───────────┐                                            │
│    │           │ RESPONDER │ ──▶ Send Telegram message                  │
│    │           └─────┬─────┘                                            │
│    │                 │                                                  │
│    │                 ▼                                                  │
│    │           ┌───────────┐                                            │
│    └──────────▶│    END    │                                            │
│                └───────────┘                                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

STATE DEFINITION (TypedDict):
├── messages: list[BaseMessage]     # Conversation history
├── user_input: str                 # Current user message
├── intent: str                     # Classified intent
├── entities: dict                  # Extracted entities
├── retrieved_context: list[dict]   # RAG results
├── task_draft: dict | None         # Current task being refined
├── clarification_count: int        # Loop counter (max 3)
├── final_response: str             # Message to send to user
└── should_end: bool                # Terminal flag
```

---

## 6. FILE STRUCTURE REFERENCE

```
paea/
├── docs/                           # ◀── YOU ARE HERE
│   ├── PROJECT_SPECS.md            # Business requirements
│   ├── TECHNICAL_ARCHITECTURE.md   # Technical design
│   ├── CODING_CONVENTION.md        # Standards
│   ├── USER_PROFILE.md             # Persona & style guide
│   ├── USER_CASES_AND_FEATURES.md  # Use cases
│   ├── SYSTEM_PROMPTS_BLUEPRINT.md # Agent prompts
│   └── PROJECT_CONTEXT_MAP.md      # This file
│
├── app/
│   ├── api/routes/
│   │   ├── telegram.py             # F1, F2, F3, F4
│   │   └── tasks.py                # F1
│   │
│   ├── agents/
│   │   ├── graph.py                # All features
│   │   ├── state.py                # All features
│   │   └── nodes/
│   │       ├── receiver.py         # F1, F2
│   │       ├── retriever.py        # F2
│   │       ├── analyzer.py         # F1, F2
│   │       ├── refiner.py          # F1
│   │       └── executor.py         # F1
│   │
│   ├── services/
│   │   ├── llm_service.py          # All features
│   │   ├── retrieval_service.py    # F2
│   │   ├── task_service.py         # F1
│   │   └── prompt_manager.py       # All features
│   │
│   ├── workers/
│   │   ├── reflection.py           # F3
│   │   └── scheduler.py            # F3, F4
│   │
│   ├── prompts/
│   │   ├── system/                 # Agent personalities
│   │   └── templates/              # Jinja2 templates
│   │
│   └── models/                     # SQLAlchemy ORM
│
├── docker-compose.yml
└── pyproject.toml
```

---

## 7. QUICK REFERENCE: KEY DECISIONS

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent Framework | LangGraph | Stateful, supports cycles (clarification loop) |
| LLM Provider | OpenAI GPT-4o | Best Vietnamese support, reliable |
| Embedding Model | text-embedding-3-small | Cost-effective, 1536 dims |
| Vector DB | Qdrant | Open-source, fast, good filtering |
| Keyword Search | Elasticsearch | Familiar, powerful aggregations |
| Task Scheduler | APScheduler | Lighter than Celery for single-node |
| Webhook Security | Secret Token Header | Telegram best practice |
| Prompt Storage | YAML + Jinja2 | Separation of concerns |
| DB | PostgreSQL | ACID, JSONB support, arrays |

---

## 8. GLOSSARY

| Term | Definition |
|------|------------|
| **VietTech** | Communication style mixing Vietnamese with English technical terms |
| **SMART** | Specific, Measurable, Achievable, Relevant, Time-bound (task criteria) |
| **Refiner Loop** | Clarification cycle that asks user for missing task details |
| **Scanner** | RAG agent that searches long-term memory |
| **Manager** | Background worker for reflection and daily briefing |
| **User State** | Key-value store tracking user's current focus, mood, patterns |
| **Hybrid Search** | Combining vector (semantic) + keyword search |
| **Checkpoint** | Serialized LangGraph state for conversation persistence |

---

## 9. OPEN QUESTIONS / FUTURE WORK

1. **Google Calendar Sync** — Not yet specified how to integrate
2. **Multi-user Support** — Current design is single-user; DB schema may need `user_id`
3. **Offline Mode** — What happens when LLM API is unreachable?
4. **Data Export** — User should be able to export their data (GDPR-style)
5. **Notification Throttling** — Avoid spamming user with too many Telegram messages
