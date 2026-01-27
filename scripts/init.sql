-- PAEA Database Initialization Script
-- All tables use incremental BIGINT IDs starting from 1,000,000

-- Create sequences starting from 1000000
CREATE SEQUENCE IF NOT EXISTS tasks_id_seq START WITH 1000000;
CREATE SEQUENCE IF NOT EXISTS projects_id_seq START WITH 1000000;
CREATE SEQUENCE IF NOT EXISTS reminders_id_seq START WITH 1000000;
CREATE SEQUENCE IF NOT EXISTS calendar_events_id_seq START WITH 1000000;
CREATE SEQUENCE IF NOT EXISTS chat_logs_id_seq START WITH 1000000;
CREATE SEQUENCE IF NOT EXISTS documents_id_seq START WITH 1000000;

-- Projects for grouping tasks (must be created first due to FK)
CREATE TABLE IF NOT EXISTS projects (
    id BIGINT PRIMARY KEY DEFAULT nextval('projects_id_seq'),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',  -- active, paused, archived
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks with full metadata
CREATE TABLE IF NOT EXISTS tasks (
    id BIGINT PRIMARY KEY DEFAULT nextval('tasks_id_seq'),
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'todo',     -- todo, in_progress, done, cancelled
    priority INTEGER DEFAULT 3,            -- 1 (P1) to 5 (P5)
    complexity VARCHAR(10),                -- low, medium, high
    deadline TIMESTAMPTZ,
    tags TEXT[],                           -- Array of tags
    project_id BIGINT REFERENCES projects(id),
    parent_task_id BIGINT REFERENCES tasks(id),  -- For subtasks
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reminders linked to tasks
CREATE TABLE IF NOT EXISTS reminders (
    id BIGINT PRIMARY KEY DEFAULT nextval('reminders_id_seq'),
    task_id BIGINT REFERENCES tasks(id) ON DELETE CASCADE,
    remind_at TIMESTAMPTZ NOT NULL,
    message TEXT,
    is_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Calendar events (synced or manual)
CREATE TABLE IF NOT EXISTS calendar_events (
    id BIGINT PRIMARY KEY DEFAULT nextval('calendar_events_id_seq'),
    title VARCHAR(255) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    location TEXT,
    source VARCHAR(50) DEFAULT 'manual',   -- manual, google_calendar, etc.
    external_id VARCHAR(255),              -- For sync reference
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat logs for RAG and analysis
CREATE TABLE IF NOT EXISTS chat_logs (
    id BIGINT PRIMARY KEY DEFAULT nextval('chat_logs_id_seq'),
    session_id VARCHAR(100) NOT NULL,
    telegram_chat_id BIGINT,               -- Telegram chat ID for reference
    role VARCHAR(20) NOT NULL,             -- user, assistant, system
    content TEXT NOT NULL,
    intent VARCHAR(50),                    -- Detected intent (create_task, query, chat, review)
    sentiment FLOAT,                       -- -1.0 to 1.0 (for reflection worker)
    metadata JSONB,                        -- Additional metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User state (key-value store)
CREATE TABLE IF NOT EXISTS user_state (
    key VARCHAR(100) PRIMARY KEY,          -- current_focus, status, energy_level, etc.
    value JSONB NOT NULL,                  -- Flexible value storage
    confidence FLOAT DEFAULT 1.0,          -- Confidence of inferred state
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents for RAG ingestion
CREATE TABLE IF NOT EXISTS documents (
    id BIGINT PRIMARY KEY DEFAULT nextval('documents_id_seq'),
    title VARCHAR(255),
    content TEXT NOT NULL,
    source VARCHAR(100),                   -- telegram, file_upload, note
    file_path VARCHAR(500),
    embedding_id VARCHAR(100),             -- Reference to Qdrant point ID
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- LangGraph checkpoints for conversation state
CREATE TABLE IF NOT EXISTS langgraph_checkpoints (
    thread_id VARCHAR(100) PRIMARY KEY,
    checkpoint BYTEA NOT NULL,             -- Serialized graph state
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_chat_logs_session ON chat_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_logs_timestamp ON chat_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_logs_telegram_chat ON chat_logs(telegram_chat_id);
CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at) WHERE is_sent = FALSE;
CREATE INDEX IF NOT EXISTS idx_calendar_events_time ON calendar_events(start_time);

-- Insert default user state
INSERT INTO user_state (key, value) VALUES
    ('status', '"active"'),
    ('energy_level', '"normal"'),
    ('current_focus', 'null')
ON CONFLICT (key) DO NOTHING;

COMMENT ON TABLE tasks IS 'Tasks with SMART criteria tracking';
COMMENT ON TABLE chat_logs IS 'All chat messages for RAG and reflection analysis';
COMMENT ON TABLE user_state IS 'Key-value store for inferred user state';
