-- Credits Tables Migration
-- Creates tables for credit-based billing and transaction tracking

-- Team Credits table
CREATE TABLE IF NOT EXISTS team_credits (
    team_id VARCHAR(255) PRIMARY KEY,
    organization_id VARCHAR(255) REFERENCES organizations(organization_id),
    credits_allocated INTEGER DEFAULT 0,
    credits_used INTEGER DEFAULT 0,
    credits_remaining INTEGER GENERATED ALWAYS AS (credits_allocated - credits_used) STORED,
    credit_limit INTEGER,
    auto_refill BOOLEAN DEFAULT FALSE,
    refill_amount INTEGER,
    refill_period VARCHAR(50),  -- 'monthly', 'weekly', 'daily'
    last_refill_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_team_credits_org ON team_credits(organization_id);
CREATE INDEX idx_team_credits_remaining ON team_credits(credits_remaining);

-- Credit Transactions table (audit log)
CREATE TABLE IF NOT EXISTS credit_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id VARCHAR(255) NOT NULL,
    organization_id VARCHAR(255),
    job_id UUID REFERENCES jobs(job_id),
    transaction_type VARCHAR(50) NOT NULL,  -- 'deduction', 'allocation', 'refund', 'adjustment'
    credits_amount INTEGER NOT NULL,
    credits_before INTEGER NOT NULL,
    credits_after INTEGER NOT NULL,
    reason VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_credit_transactions_team ON credit_transactions(team_id, created_at);
CREATE INDEX idx_credit_transactions_job ON credit_transactions(job_id);
CREATE INDEX idx_credit_transactions_org ON credit_transactions(organization_id, created_at);
CREATE INDEX idx_credit_transactions_type ON credit_transactions(transaction_type);

-- Add trigger to update updated_at on team_credits
CREATE TRIGGER update_team_credits_updated_at
    BEFORE UPDATE ON team_credits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verify tables created
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('team_credits', 'credit_transactions')
ORDER BY tablename;
