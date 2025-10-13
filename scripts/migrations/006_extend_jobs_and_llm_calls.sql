-- Extend Jobs and LLM Calls Tables Migration
-- Adds new fields for organization tracking, external task IDs, credit tracking, and model groups

-- Extend jobs table
ALTER TABLE jobs
    ADD COLUMN IF NOT EXISTS organization_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS external_task_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS credit_applied BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS model_groups_used TEXT[] DEFAULT '{}';

-- Add foreign key constraint for organization
ALTER TABLE jobs
    ADD CONSTRAINT fk_jobs_organization
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id);

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_jobs_organization ON jobs(organization_id, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_external_task ON jobs(external_task_id);
CREATE INDEX IF NOT EXISTS idx_jobs_credit_applied ON jobs(credit_applied);

-- Extend llm_calls table
ALTER TABLE llm_calls
    ADD COLUMN IF NOT EXISTS model_group_used VARCHAR(100),
    ADD COLUMN IF NOT EXISTS resolved_model VARCHAR(200);

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_llm_calls_model_group ON llm_calls(model_group_used);
CREATE INDEX IF NOT EXISTS idx_llm_calls_resolved_model ON llm_calls(resolved_model);

-- Verify columns added
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name IN ('jobs', 'llm_calls')
AND column_name IN ('organization_id', 'external_task_id', 'credit_applied', 'model_groups_used', 'model_group_used', 'resolved_model')
ORDER BY table_name, column_name;
