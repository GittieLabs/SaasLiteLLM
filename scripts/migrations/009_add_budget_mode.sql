--
-- Migration: Add budget mode support for flexible credit deduction
-- Date: 2025-10-14
--

-- Add budget_mode column to team_credits table
-- Supports: "job_based" (1 credit per job), "consumption_usd" (credits based on $ spent), "consumption_tokens" (credits based on tokens used)
ALTER TABLE team_credits
ADD COLUMN IF NOT EXISTS budget_mode VARCHAR(50) DEFAULT 'job_based';

-- Add credit conversion rate (how many credits = $1 USD)
-- Default: 10 credits = $1 (1 credit = $0.10)
ALTER TABLE team_credits
ADD COLUMN IF NOT EXISTS credits_per_dollar DECIMAL(10, 2) DEFAULT 10.0;

-- Add index for budget_mode queries
CREATE INDEX IF NOT EXISTS idx_team_credits_budget_mode ON team_credits(budget_mode);

-- Update existing rows to use job_based mode
UPDATE team_credits
SET budget_mode = 'job_based'
WHERE budget_mode IS NULL;

COMMENT ON COLUMN team_credits.budget_mode IS 'Budget mode: job_based (1 credit/job), consumption_usd (credits = $ * rate), consumption_tokens (credits = tokens / 10000)';
COMMENT ON COLUMN team_credits.credits_per_dollar IS 'Conversion rate for consumption_usd mode. Default: 10 credits = $1';
