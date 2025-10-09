-- Job Tracking Database Schema Migration
-- Creates all tables needed for job-based cost tracking

-- Create enum type for job status
DO $$ BEGIN
    CREATE TYPE job_status AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Drop existing jobs table if it exists (from test)
DROP TABLE IF EXISTS jobs CASCADE;

-- Jobs table
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    job_type VARCHAR(100) NOT NULL,
    status job_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    job_metadata JSONB DEFAULT '{}',
    error_message VARCHAR(1000)
);

CREATE INDEX idx_team_created ON jobs(team_id, created_at);
CREATE INDEX idx_team_status ON jobs(team_id, status);
CREATE INDEX idx_job_type_created ON jobs(job_type, created_at);
CREATE INDEX idx_status ON jobs(status);

-- LLM Calls table
CREATE TABLE llm_calls (
    call_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    litellm_request_id VARCHAR(255) UNIQUE,
    model_used VARCHAR(100),
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost_usd NUMERIC(10, 6) DEFAULT 0.0,
    latency_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    purpose VARCHAR(200),
    request_data JSONB,
    response_data JSONB,
    error VARCHAR(1000)
);

CREATE INDEX idx_job_id_created ON llm_calls(job_id, created_at);
CREATE INDEX idx_created_at ON llm_calls(created_at);

-- Job Cost Summaries table
CREATE TABLE job_cost_summaries (
    job_id UUID PRIMARY KEY REFERENCES jobs(job_id) ON DELETE CASCADE,
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,
    total_prompt_tokens INTEGER DEFAULT 0,
    total_completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd NUMERIC(12, 6) DEFAULT 0.0,
    avg_latency_ms INTEGER,
    total_duration_seconds INTEGER,
    calculated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Team Usage Summaries table
CREATE TABLE team_usage_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id VARCHAR(255) NOT NULL,
    period VARCHAR(50) NOT NULL,
    period_type VARCHAR(20) DEFAULT 'monthly',
    total_jobs INTEGER DEFAULT 0,
    successful_jobs INTEGER DEFAULT 0,
    failed_jobs INTEGER DEFAULT 0,
    cancelled_jobs INTEGER DEFAULT 0,
    total_cost_usd NUMERIC(12, 2) DEFAULT 0.0,
    total_tokens INTEGER DEFAULT 0,
    job_type_breakdown JSONB DEFAULT '{}',
    calculated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_team_period ON team_usage_summaries(team_id, period);

-- Webhook Registrations table
CREATE TABLE webhook_registrations (
    webhook_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id VARCHAR(255) NOT NULL,
    webhook_url VARCHAR(500) NOT NULL,
    events JSONB DEFAULT '[]',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_triggered_at TIMESTAMP,
    auth_header VARCHAR(500)
);

CREATE INDEX idx_webhook_team_id ON webhook_registrations(team_id);
CREATE INDEX idx_webhook_active ON webhook_registrations(is_active);

-- Verify tables created
SELECT
    schemaname,
    tablename
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('jobs', 'llm_calls', 'job_cost_summaries', 'team_usage_summaries', 'webhook_registrations')
ORDER BY tablename;
