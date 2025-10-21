-- Migration 010: Add provider_credentials table
-- Stores API keys for AI providers (OpenAI, Anthropic, Gemini, Fireworks)

CREATE TYPE provider_type AS ENUM ('openai', 'anthropic', 'gemini', 'fireworks');

CREATE TABLE IF NOT EXISTS provider_credentials (
    credential_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id VARCHAR NOT NULL,
    provider provider_type NOT NULL,

    -- Encrypted API key
    api_key TEXT NOT NULL,

    -- Optional custom API base URL
    api_base VARCHAR,

    -- Credential label for identification
    credential_name VARCHAR NOT NULL,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Audit trail
    created_by VARCHAR,
    updated_by VARCHAR,

    -- Indexes
    CONSTRAINT fk_organization FOREIGN KEY (organization_id)
        REFERENCES organizations(organization_id) ON DELETE CASCADE
);

CREATE INDEX idx_provider_credentials_org ON provider_credentials(organization_id);
CREATE INDEX idx_provider_credentials_provider ON provider_credentials(provider);
CREATE INDEX idx_provider_credentials_active ON provider_credentials(is_active);

-- Add unique constraint: one active credential per provider per organization
CREATE UNIQUE INDEX idx_provider_credentials_unique_active
    ON provider_credentials(organization_id, provider)
    WHERE is_active = true;

COMMENT ON TABLE provider_credentials IS 'API credentials for AI model providers';
COMMENT ON COLUMN provider_credentials.api_key IS 'Encrypted API key - encrypt at application layer';
COMMENT ON COLUMN provider_credentials.api_base IS 'Optional custom API endpoint URL';
