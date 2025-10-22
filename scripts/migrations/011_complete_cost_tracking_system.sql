-- Migration 011: Complete cost tracking system
-- Store the ACTUAL model used (resolved from alias), its pricing, and calculated costs with markup

-- Add model pricing and detailed cost tracking to llm_calls
ALTER TABLE llm_calls
ADD COLUMN IF NOT EXISTS model_pricing_input DECIMAL(10,6),  -- Input price per 1M tokens (what provider charges)
ADD COLUMN IF NOT EXISTS model_pricing_output DECIMAL(10,6);  -- Output price per 1M tokens (what provider charges)

-- Update comments to clarify the complete flow
COMMENT ON COLUMN llm_calls.model_used IS 'Model alias requested (e.g., gpa-rag-chat)';
COMMENT ON COLUMN llm_calls.resolved_model IS 'Actual model used by provider (e.g., gpt-4-0613) - THIS is what determines cost';
COMMENT ON COLUMN llm_calls.model_pricing_input IS 'Input token price per 1M tokens for the RESOLVED model at time of call';
COMMENT ON COLUMN llm_calls.model_pricing_output IS 'Output token price per 1M tokens for the RESOLVED model at time of call';
COMMENT ON COLUMN llm_calls.input_cost_usd IS 'Calculated: prompt_tokens * model_pricing_input / 1,000,000';
COMMENT ON COLUMN llm_calls.output_cost_usd IS 'Calculated: completion_tokens * model_pricing_output / 1,000,000';
COMMENT ON COLUMN llm_calls.provider_cost_usd IS 'Total cost from provider: input_cost_usd + output_cost_usd';
COMMENT ON COLUMN llm_calls.client_cost_usd IS 'Cost charged to client: provider_cost_usd * (1 + markup_percentage / 100)';

-- Example flow:
-- 1. Request uses alias "gpa-rag-chat"
-- 2. Resolves to actual model "gpt-4-0613"
-- 3. Look up pricing for "gpt-4-0613": $30/1M input, $60/1M output
-- 4. Calculate provider cost: (1000 * $30 / 1M) + (500 * $60 / 1M) = $0.06
-- 5. Apply 50% markup: $0.06 * 1.5 = $0.09 client cost
-- 6. Convert to credits: $0.09 * credits_per_dollar = credits to deduct
