-- Migration 008: Migrate from Model Groups to Model Aliases & Access Groups
-- This migration replaces the model_groups system with LiteLLM's native model alias system

-- Drop old tables (no migration needed since this is new code)
DROP TABLE IF EXISTS team_model_groups CASCADE;
DROP TABLE IF EXISTS model_group_models CASCADE;
DROP TABLE IF EXISTS model_groups CASCADE;

-- Create model_aliases table
-- Stores user-facing model aliases that map to actual models in LiteLLM
CREATE TABLE IF NOT EXISTS model_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_alias VARCHAR(200) UNIQUE NOT NULL,          -- User-facing alias (e.g., "chat-fast")
    display_name VARCHAR(200),                         -- Display name (e.g., "Fast Chat Model")
    provider VARCHAR(100) NOT NULL,                    -- Provider (e.g., "openai", "anthropic")
    actual_model VARCHAR(200) NOT NULL,                -- Real model name (e.g., "gpt-3.5-turbo")
    litellm_model_id VARCHAR(200),                     -- LiteLLM's database model ID
    description TEXT,                                   -- Optional description
    pricing_input DECIMAL(10,6),                       -- Cost per 1M input tokens
    pricing_output DECIMAL(10,6),                      -- Cost per 1M output tokens
    status VARCHAR(50) DEFAULT 'active',               -- active, inactive, deprecated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on model_alias for fast lookups
CREATE INDEX idx_model_aliases_alias ON model_aliases(model_alias);
CREATE INDEX idx_model_aliases_status ON model_aliases(status);

-- Create model_access_groups table
-- Groups of model aliases for access control
CREATE TABLE IF NOT EXISTS model_access_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_name VARCHAR(200) UNIQUE NOT NULL,           -- Group identifier (e.g., "basic-chat")
    display_name VARCHAR(200),                         -- Display name (e.g., "Basic Chat Models")
    description TEXT,                                   -- Optional description
    status VARCHAR(50) DEFAULT 'active',               -- active, inactive
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on group_name for fast lookups
CREATE INDEX idx_model_access_groups_name ON model_access_groups(group_name);
CREATE INDEX idx_model_access_groups_status ON model_access_groups(status);

-- Create model_alias_access_groups table
-- Maps model aliases to access groups (many-to-many)
CREATE TABLE IF NOT EXISTS model_alias_access_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_alias_id UUID NOT NULL REFERENCES model_aliases(id) ON DELETE CASCADE,
    access_group_id UUID NOT NULL REFERENCES model_access_groups(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_alias_id, access_group_id)
);

-- Create indexes for efficient queries
CREATE INDEX idx_model_alias_access_groups_alias ON model_alias_access_groups(model_alias_id);
CREATE INDEX idx_model_alias_access_groups_group ON model_alias_access_groups(access_group_id);

-- Create team_access_groups table
-- Maps teams to access groups (replaces team_model_groups)
CREATE TABLE IF NOT EXISTS team_access_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id VARCHAR(255) NOT NULL,
    access_group_id UUID NOT NULL REFERENCES model_access_groups(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, access_group_id)
);

-- Create indexes for efficient team queries
CREATE INDEX idx_team_access_groups_team ON team_access_groups(team_id);
CREATE INDEX idx_team_access_groups_group ON team_access_groups(access_group_id);

-- Add comments for documentation
COMMENT ON TABLE model_aliases IS 'User-facing model aliases that map to actual LLM models';
COMMENT ON TABLE model_access_groups IS 'Collections of model aliases for access control';
COMMENT ON TABLE model_alias_access_groups IS 'Many-to-many relationship between aliases and access groups';
COMMENT ON TABLE team_access_groups IS 'Maps teams to their allowed model access groups';

COMMENT ON COLUMN model_aliases.model_alias IS 'The alias name used in application code (e.g., "chat-fast")';
COMMENT ON COLUMN model_aliases.actual_model IS 'The real model name in LiteLLM (e.g., "gpt-3.5-turbo")';
COMMENT ON COLUMN model_aliases.litellm_model_id IS 'Reference to LiteLLM_ModelTable.id in LiteLLM database';
