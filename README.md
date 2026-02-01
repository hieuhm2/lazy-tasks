# Lazy Tasks - Personal AI Executive Assistant

Local-first AI assistant for task management via Telegram. Built with LangGraph + FastAPI + PostgreSQL + Qdrant.

## Quick Start

### 1. Setup Environment

**Option A: Using Conda (Recommended)**
```bash
# Create conda environment
conda env create -f environment.yml
conda activate lazy-tasks
```

**Option B: Using pip**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example config
cp .env.example .env

# Edit .env with your values:
# - OPENAI_API_KEY
# - TELEGRAM_BOT_TOKEN
# - TELEGRAM_WEBHOOK_SECRET (generate random 32-char string)
```

### 3. Start Services

```bash
# Start all services (PostgreSQL, Qdrant, Elasticsearch)
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Run the Application

**Option A: With Docker**
```bash
docker-compose up -d --build
```

**Option B: Locally (for development)**
```bash
# Make sure Docker services are running
docker-compose up -d postgres qdrant elasticsearch

# Run FastAPI app
make run
# or: uvicorn app.main:app --reload --port 8000
```

### 5. Setup Telegram Webhook

```bash
# Set webhook (replace with your public URL)
make webhook-set URL=https://your-domain.com TELEGRAM_BOT_TOKEN=your-token TELEGRAM_WEBHOOK_SECRET=your-secret

# Verify webhook
make webhook-info TELEGRAM_BOT_TOKEN=your-token
```

For local development, use [ngrok](https://ngrok.com/) to expose localhost:
```bash
ngrok http 8000
# Then use the ngrok URL for webhook
```

## Project Structure

```
lazy-tasks/
├── app/
│   ├── api/routes/         # FastAPI endpoints
│   ├── core/               # Config, database
│   ├── models/             # SQLAlchemy ORM models
│   ├── services/           # Business logic
│   ├── prompts/            # YAML + Jinja2 templates
│   └── main.py             # Entry point
├── scripts/
│   └── init.sql            # Database initialization
├── docs/                   # Documentation
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

## Available Commands

```bash
make help           # Show all commands
make up             # Start Docker services
make down           # Stop Docker services
make logs           # View logs
make run            # Run app locally
make lint           # Run linter
make format         # Format code
make db-shell       # Open PostgreSQL shell
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Web Framework | FastAPI |
| Agent Framework | LangGraph |
| LLM | OpenAI GPT-4o |
| Database | PostgreSQL 15 |
| Vector DB | Qdrant |
| Search | Elasticsearch 8 |
| Interface | Telegram Bot |

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /webhook/telegram` - Telegram webhook receiver

## Development

```bash
# Install dev dependencies
make dev

# Run linter
make lint

# Format code
make format

# Type check
make typecheck
```

## Documentation

See the `docs/` folder for detailed documentation:

- [Project Specs](docs/PROJECT_SPECS.md) - Business logic
- [Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md) - Tech design
- [Coding Convention](docs/CODING_CONVENTION.md) - Standards
- [User Profile](docs/USER_PROFILE.md) - VietTech style guide
