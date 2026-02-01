# PROJECT SPECIFICATIONS: Personal AI Executive Assistant (Lazy Tasks)

## 1. Overview
Lazy Tasks is a local-first, agentic AI assistant designed to manage personal tasks, goals, and schedules via a Telegram interface. It moves beyond simple command-response by proactively clarifying vague tasks, scanning past data for context, and reflecting on user progress.

## 2. Core Behavior (The Agent Loop)
The system is built on **LangGraph** with the following cyclic workflow:
1.  **Receiver Node:** Captures user input from Telegram.
2.  **Retriever Node (RAG):**
    - Semantic Search via **Qdrant** (for vague context).
    - Keyword Search via **Elasticsearch** (for specific logs/docs).
3.  **Analyzer Node (LLM):** Determines user intent (Create Task, Query, Chat, or Review).
4.  **Refiner Node (The Loop):**
    - Checks if the task is SMART (Specific, Measurable, Achievable, Relevant, Time-bound).
    - If info is missing -> Updates state & asks user for clarification (returns to user).
    - If info is complete -> Proceed to execution.
5.  **Executor Node:** Writes to Postgres DB / Triggers External APIs.
6.  **Reflection Worker (Background):** Periodically scans logs to update user state and detect burnout/progress.

## 3. Key Features
- **Smart Clarification:** Never blindly save a task. Always ask for details if vague.
- **Contextual Memory:** Uses Hybrid Search (Vector + Keyword) to recall past goals.
- **Daily Briefing:** Triggers a summary report when the system starts.
- **Headless Architecture:** Core logic is exposed via FastAPI, decoupled from the Telegram bot.

