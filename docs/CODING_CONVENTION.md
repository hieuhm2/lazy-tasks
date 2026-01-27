# CODING CONVENTIONS & STANDARDS

## 1. Prompt Management (Centralized)
**Rule:** NEVER hardcode prompts inside Python logic files (`.py`).
**Implementation:**
- All prompts must be stored in `app/prompts/` directory.
- Use **YAML** or **Jinja2** templates for prompts to separate logic from text.
- Create a `PromptManager` service to load prompts by name.

**Directory Structure:**
This is just an example, can change for convinient purpose.
```text
app/prompts/
├── system/
│   ├── refiner.yaml       # System prompt for Refiner Agent
│   ├── scanner.yaml       # System prompt for Scanner
│   └── personality.yaml   # Base personality injection
├── templates/
│   ├── task_clarification.jinja2
│   └── daily_briefing.jinja2
└── manifest.yaml          # Registry of all prompts

```

## 2. Code Style & Typing

* **Language:** Python 3.11+.
* **Type Hinting:** Strictly enforce Type Hints for all function arguments and return values.
* **Docstrings:** Use Google-style docstrings.

## 3. Architecture Pattern

* **Dependency Injection:** Use DI for Database and LLM services to allow easy swapping of implementations.
* **Service Layer:** Business logic must sit in `app/services`, not in API routers.

## 4. Language Handling in Code

* **Variable Names/Comments:** MUST be in **English** (e.g., `user_input`, `process_task`).
* **String Literals (Output to User):** MUST be in **Vietnamese** (or loaded from localization files if possible, but for MVP, hardcoded Vietnamese strings in specific response templates are acceptable).

