-- Migration 010: Add comprehensive cost tracking and markup capability
-- Adds separate cost fields to track provider costs vs client costs
-- Adds markup percentage to team_credits for profit margins

-- Add detailed cost tracking to llm_calls table
ALTER TABLE llm_calls
ADD COLUMN IF NOT EXISTS input_cost_usd DECIMAL(10,8),
ADD COLUMN IF NOT EXISTS output_cost_usd DECIMAL(10,8),
ADD COLUMN IF NOT EXISTS provider_cost_usd DECIMAL(10,8),
ADD COLUMN IF NOT EXISTS client_cost_usd DECIMAL(10,8);

-- Add markup percentage to team_credits
ALTER TABLE team_credits
ADD COLUMN IF NOT EXISTS cost_markup_percentage DECIMAL(5,2) DEFAULT 0.00;

-- Update existing cost_usd to provider_cost_usd for any existing records
UPDATE llm_calls
SET provider_cost_usd = cost_usd
WHERE provider_cost_usd IS NULL AND cost_usd IS NOT NULL;

-- Add comments for clarity
COMMENT ON COLUMN llm_calls.input_cost_usd IS 'Cost for input/prompt tokens from provider';
COMMENT ON COLUMN llm_calls.output_cost_usd IS 'Cost for output/completion tokens from provider';
COMMENT ON COLUMN llm_calls.provider_cost_usd IS 'Total cost charged by LLM provider (LiteLLM)';
COMMENT ON COLUMN llm_calls.client_cost_usd IS 'Total cost charged to client (provider cost + markup)';
COMMENT ON COLUMN llm_calls.cost_usd IS 'Legacy cost field - use provider_cost_usd instead';

COMMENT ON COLUMN team_credits.cost_markup_percentage IS 'Markup percentage applied to provider costs (e.g., 50.00 = 50% markup, 100.00 = 2x cost)';

-- Example: If provider cost is $0.01 and markup is 50%, client pays $0.015
