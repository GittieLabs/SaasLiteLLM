-- Model Groups Tables Migration
-- Creates tables for managing model groups (ResumeAgent, ParsingAgent, etc.)
-- with primary and fallback model assignments

-- Model Groups table
CREATE TABLE IF NOT EXISTS model_groups (
    model_group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200),
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_model_group_name ON model_groups(group_name);
CREATE INDEX idx_model_group_status ON model_groups(status);

-- Model Group Models table (primary + fallbacks)
CREATE TABLE IF NOT EXISTS model_group_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_group_id UUID NOT NULL REFERENCES model_groups(model_group_id) ON DELETE CASCADE,
    model_name VARCHAR(200) NOT NULL,
    priority INTEGER DEFAULT 0,  -- 0 = primary, 1 = first fallback, 2 = second fallback, etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_model_group_models_lookup
    ON model_group_models(model_group_id, priority, is_active);
CREATE INDEX idx_model_group_models_group ON model_group_models(model_group_id);

-- Add trigger to update updated_at on model_groups
CREATE TRIGGER update_model_groups_updated_at
    BEFORE UPDATE ON model_groups
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verify tables created
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('model_groups', 'model_group_models')
ORDER BY tablename;
