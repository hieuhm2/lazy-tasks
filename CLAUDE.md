# Lazy Tasks - Personal AI Executive Assistant

> **Quick Summary:** Local-first AI assistant for task management via Telegram. Built with LangGraph + FastAPI + PostgreSQL + Qdrant.
>
> **Project Type:** Personal side project (no tests required, keep it simple)

---

## DOCUMENTATION INDEX

Read the appropriate file based on your current task:

| If you need to... | Read this file |
|-------------------|----------------|
| Understand the **business logic** and core features | `docs/PROJECT_SPECS.md` |
| Know the **tech stack**, DB schema, or infrastructure | `docs/TECHNICAL_ARCHITECTURE.md` |
| Write code following **standards** (typing, prompts, DI) | `docs/CODING_CONVENTION.md` |
| Match the **communication style** (VietTech tone) | `docs/USER_PROFILE.md` |
| Understand **use cases** and user scenarios | `docs/USER_CASES_AND_FEATURES.md` |
| Work on **agent prompts** or LLM behavior | `docs/SYSTEM_PROMPTS_BLUEPRINT.md` |
| Get a **high-level overview** or find component relationships | `docs/PROJECT_CONTEXT_MAP.md` |

---

## TASK-BASED READING GUIDE

### Starting a New Feature
1. `docs/PROJECT_CONTEXT_MAP.md` — Find which components are involved
2. `docs/TECHNICAL_ARCHITECTURE.md` — Check DB schema and services
3. `docs/CODING_CONVENTION.md` — Follow the standards

### Working on LLM/Agent Logic
1. `docs/SYSTEM_PROMPTS_BLUEPRINT.md` — Agent personas and prompt templates
2. `docs/USER_PROFILE.md` — VietTech style and few-shot examples
3. `docs/PROJECT_SPECS.md` — Core agent loop definition

### Writing User-Facing Messages
1. `docs/USER_PROFILE.md` — **MUST READ** for tone and style
2. `docs/SYSTEM_PROMPTS_BLUEPRINT.md` — Jinja2 templates

### Debugging or Understanding Flow
1. `docs/PROJECT_CONTEXT_MAP.md` — Data flow diagrams, state machine
2. `docs/USER_CASES_AND_FEATURES.md` — Step-by-step scenarios

### Adding a Database Table/Column
1. `docs/TECHNICAL_ARCHITECTURE.md` — Section 3 (DB Schema)
2. `docs/PROJECT_CONTEXT_MAP.md` — Section 4 (Entity Relationships)

> **ID Convention:** All tables use BIGINT IDs starting from 1,000,000 (not UUID) for easy counting.

---

## KEY CONVENTIONS (Quick Reference)

### Language Rules
- **Code** (variables, comments): English
- **User-facing strings**: Vietnamese (VietTech style)
- **Technical terms**: Keep in English (task, deadline, deploy, bug, API, sync, log)

### Prompt Management
- **NEVER** hardcode prompts in `.py` files
- Store prompts in `app/prompts/` (YAML for system prompts, Jinja2 for templates)
- Use `PromptManager` service to load prompts

### Code Style
- Python 3.11+
- Strict type hints on all functions
- Google-style docstrings
- Dependency Injection for DB/LLM services (easy swapping)
- Business logic in `app/services/`, not in API routes

### Agent Behavior
- **Zero Ambiguity Rule:** Never save a task without confirming critical details (deadline, output)
- **Clarification Loop:** Ask at most 3 questions, provide options when possible
- **Privacy First:** All data stays local; only necessary context goes to LLM API

---

## PROJECT STRUCTURE

```
lazy-tasks/
├── CLAUDE.md                    # ◀── You are here
├── docs/                        # Documentation
│   ├── PROJECT_SPECS.md         # Business logic
│   ├── TECHNICAL_ARCHITECTURE.md# Tech design
│   ├── CODING_CONVENTION.md     # Standards
│   ├── USER_PROFILE.md          # VietTech style
│   ├── USER_CASES_AND_FEATURES.md # Scenarios
│   ├── SYSTEM_PROMPTS_BLUEPRINT.md # Agent prompts
│   └── PROJECT_CONTEXT_MAP.md   # Knowledge graph
├── app/
│   ├── api/routes/              # FastAPI endpoints
│   ├── agents/                  # LangGraph nodes & graph
│   ├── services/                # Business logic
│   ├── workers/                 # Background jobs
│   ├── prompts/                 # YAML + Jinja2 templates
│   ├── models/                  # SQLAlchemy ORM
│   └── main.py                  # Entry point
├── docker-compose.yml
└── pyproject.toml
```

---

## TECH STACK SUMMARY

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Web Framework | FastAPI |
| Agent Framework | LangGraph |
| LLM | OpenAI GPT-4o |
| Embeddings | OpenAI text-embedding-3-small (1536 dims) |
| Database | PostgreSQL 15 |
| Vector DB | Qdrant |
| Search | Elasticsearch 8 |
| Interface | Telegram Bot (Webhook) |
| Scheduler | APScheduler |

---

## COMMON COMMANDS

```bash
# Start all services
docker-compose up -d

# Run the app locally
uvicorn app.main:app --reload --port 8000

# Check types
mypy app/

# Format code
ruff format app/
ruff check app/ --fix
```

---

## ENVIRONMENT VARIABLES

Required in `.env`:
```
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_WEBHOOK_SECRET=random-32-char-string
POSTGRES_URL=postgresql://user:pass@localhost:5432/lazy_tasks
QDRANT_URL=http://localhost:6333
ELASTICSEARCH_URL=http://localhost:9200
```

---

## AGENTS OVERVIEW

| Agent | Role | Prompt File |
|-------|------|-------------|
| **Analyzer** | Classify user intent | `app/prompts/system/analyzer.yaml` |
| **Refiner** | Validate SMART criteria, ask clarifications | `app/prompts/system/refiner.yaml` |
| **Scanner** | RAG search (Qdrant + ES) | `app/prompts/system/scanner.yaml` |
| **Manager** | Daily briefing, reflection, burnout detection | `app/prompts/system/manager.yaml` |
| **Personality** | Base VietTech style (injected into all) | `app/prompts/system/personality.yaml` |

---

## IMPORTANT REMINDERS

1. **Read `USER_PROFILE.md`** before writing any user-facing text
2. **Check `TECHNICAL_ARCHITECTURE.md` Section 3** before modifying database
3. **Follow prompt structure** in `SYSTEM_PROMPTS_BLUEPRINT.md` — don't invent new formats
4. **Test VietTech output** — ensure technical terms stay in English
5. **Never commit `.env`** — it's in `.gitignore`
