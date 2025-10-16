-- Migration: Add status field to team_credits for pause/suspend functionality
-- Date: 2025-10-14
-- Description: Allows admins to suspend or pause teams manually

-- Add status column to team_credits
ALTER TABLE team_credits
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active' NOT NULL;

-- Add index for faster status lookups
CREATE INDEX IF NOT EXISTS idx_team_credits_status ON team_credits(status);

-- Add comment explaining status values
COMMENT ON COLUMN team_credits.status IS 'Team status: active, suspended, paused. Suspended/paused teams cannot make API calls.';

-- Update existing teams to 'active' status
UPDATE team_credits SET status = 'active' WHERE status IS NULL;
