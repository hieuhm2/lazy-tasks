# PRODUCT SPECIFICATIONS: FEATURES & USE CASES
**Project:** Personal AI Executive Assistant (Lazy Tasks)
**Type:** Local-first, Agentic System
**Role:** An intelligent, proactive partner that helps manage tasks, clarify goals, and recall context.

---

## 1. CORE FEATURES

### F1. Intelligent Task Capture (The "Refiner" Agent)
Instead of passively saving input, the Agent analyzes it against **SMART criteria** (Specific, Measurable, Achievable, Relevant, Time-bound).
- **Auto-Clarification:** If the user input is vague, the Agent triggers a clarification loop to ask for missing details (deadline, specific output, context).
- **Structured Saving:** Once clarified, data is saved into PostgreSQL with metadata (priority, complexity, tags).

### F2. Contextual "Scan" & Memory (RAG)
The ability to "scan" past data to provide personalized responses.
- **Ingestion:** Automatically captures chat logs, notes, and documents. Uses Gemini to summarize and generate embeddings.
- **Hybrid Retrieval:**
  - **Vector Search (Qdrant):** For semantic queries (e.g., "What was I worried about last week?").
  - **Keyword Search (Elasticsearch):** For precise lookup (e.g., "Find the file named 'budget_v2'").
- **Proactive Recall:** Before answering, the Agent checks long-term memory to see if the topic relates to previous goals or projects.

### F3. Proactive Planning & Reflection (The "Manager" Worker)
Background processes that act as an Executive Manager.
- **Startup Briefing:** Triggered when the system starts (laptop opens). Sends a summary of the day's priorities and schedule via Telegram.
- **Periodic Reflection:** A background worker analyzes chat logs and task completion rates to:
  - Detect burnout or overload.
  - Update the `User State` (e.g., "User is currently focused on Project A").
  - Suggest rescheduling if tasks are overdue.

### F4. Visualization & Reporting
- **Text-based Timeline:** Generates a clean, emoji-coded timeline of the day/week in Telegram chat (replacing the need for a Calendar UI).
- **Daily/Weekly Reports:** Summaries of what has been achieved vs. planned.

---

## 2. DETAILED USE CASES (SCENARIOS)

### UC1: The Vague Task Flow (Clarification Loop)
**Trigger:** User sends a vague message.
**Scenario:**
1. **User:** "Nhắc anh làm cái báo cáo nhé."
2. **Agent (Analyzer):** Detects `create_task`. Missing `topic`, `deadline`.
3. **Agent (Refiner):** Replies: "Báo cáo cho dự án nào đấy anh? Deadline khi nào cần?"
4. **User:** "Báo cáo tài chính Q1, chiều thứ 6 nộp."
5. **Agent (Executor):** Creates task: `{"content": "Làm báo cáo tài chính Q1", "deadline": "Friday 17:00", "status": "TODO"}`.
6. **Agent:** "Đã save. Tôi set reminder trước 2 tiếng nhé."

### UC2: Contextual Retrieval ("Scan Data")
**Trigger:** User asks about past info.
**Scenario:**
1. **User:** "Tháng trước anh có note gì về cái project Marketing không nhỉ?"
2. **Agent:** Hybrid searches (Qdrant + ES).
3. **Agent:** "Tôi scan thấy log ngày 15/12 anh có discuss về 'Social Media Campaign'. Key note là:
   - Tập trung vào short video.
   - Budget: 5k$.
   Anh có muốn convert mấy ý này thành task không?"

### UC3: The "Startup" Routine
**Trigger:** Laptop opens (System Start).
**Scenario:**
1. **System:** Detects startup.
2. **Agent:** Sends Telegram msg:
   > "👋 **Chào buổi sáng!**
   >
   > **Tiêu điểm hôm nay:**
   > 1. [P1] Fix lỗi API login (Deadline: 2 PM) 🔴
   > 2. [P2] Review code cho team (Deadline: 5 PM)
   >
   > *Note: Anh có lịch họp lúc 10h sáng nay nhé.*"

### UC4: The Reflection Worker (Background)
**Trigger:** End of day (or periodic cron).
**Scenario:**
1. **Worker:** Scans completed tasks vs. planned tasks.
2. **Analysis:** Notices user only completed 1 out of 5 tasks and expressed frustration in chat logs (Sentiment Analysis).
3. **Action:** Updates `User State`: `status="overwhelmed"`.
4. **Agent:** Next morning, adjusts tone: "You had a tough day yesterday. Let's keep the plan light today. Only 2 priority tasks."

---

## 3. SYSTEM BEHAVIORS & RULES

1.  **Zero Ambiguity Rule:** The system must never guess critical task details (deadline, output). It must ask.
2.  **Privacy First:** All data stays local (Postgres/ES/Qdrant). Only anonymized/necessary context is sent to LLM API.
3.  **Chat-First UX:** All outputs must be formatted for readability on Telegram (Markdown, Emojis, concise text).
