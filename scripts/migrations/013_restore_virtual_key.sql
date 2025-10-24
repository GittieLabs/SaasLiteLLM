-- Migration 013: Restore virtual_key column
-- Purpose: Rollback migration 012 - authentication system still depends on virtual_key
-- Date: 2025-10-24
-- Context: Migration 012 removed virtual_key prematurely, breaking all authenticated endpoints

-- Step 1: Add virtual_key column back to team_credits
ALTER TABLE team_credits
    ADD COLUMN IF NOT EXISTS virtual_key VARCHAR(500);

-- Step 2: Recreate the index
CREATE INDEX IF NOT EXISTS idx_team_credits_virtual_key ON team_credits(virtual_key);

-- Step 3: Verify column was added
DO $$
DECLARE
    column_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'team_credits'
        AND column_name = 'virtual_key'
    ) INTO column_exists;

    IF column_exists THEN
        RAISE NOTICE 'SUCCESS: virtual_key column restored to team_credits';
    ELSE
        RAISE EXCEPTION 'ERROR: virtual_key column was not added!';
    END IF;
END $$;

-- Migration complete
SELECT 'Migration 013 completed successfully - virtual_key column restored' as status;
