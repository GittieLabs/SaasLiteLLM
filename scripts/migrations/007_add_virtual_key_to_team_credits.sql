-- Migration: Add virtual_key column to team_credits table
-- Purpose: Store LiteLLM virtual API keys for teams

-- Add virtual_key column
ALTER TABLE team_credits
    ADD COLUMN IF NOT EXISTS virtual_key VARCHAR(500);

-- Add index for faster key lookups
CREATE INDEX IF NOT EXISTS idx_team_credits_virtual_key
    ON team_credits(virtual_key);

-- Verify column was added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'team_credits'
AND column_name = 'virtual_key';
