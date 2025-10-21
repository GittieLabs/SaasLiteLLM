-- Migration 011: Add tokens_per_credit column to team_credits table
-- This allows per-team configuration of token-to-credit conversion rates
-- Default is 10000 tokens per credit (matching DEFAULT_TOKENS_PER_CREDIT constant)

-- Add tokens_per_credit column with default value
ALTER TABLE team_credits
ADD COLUMN IF NOT EXISTS tokens_per_credit INTEGER DEFAULT 10000;

-- Add comment explaining the column
COMMENT ON COLUMN team_credits.tokens_per_credit IS 'Number of tokens equivalent to 1 credit in consumption_tokens budget mode. Default: 10000 tokens = 1 credit';

-- Update existing rows to have the default value explicitly set
UPDATE team_credits
SET tokens_per_credit = 10000
WHERE tokens_per_credit IS NULL;
