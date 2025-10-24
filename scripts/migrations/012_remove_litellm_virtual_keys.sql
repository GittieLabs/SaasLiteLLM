-- Migration 012: Remove LiteLLM virtual key dependencies
-- Purpose: Clean up after migrating to direct provider calls
-- Date: 2025-10-23
-- WARNING: Run this ONLY after all teams have been migrated to use provider_credentials

-- Step 1: Verify migration readiness
-- Check if any teams are still using virtual keys
DO $$
DECLARE
    virtual_key_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO virtual_key_count
    FROM team_credits
    WHERE virtual_key IS NOT NULL AND virtual_key != '';

    IF virtual_key_count > 0 THEN
        RAISE NOTICE 'WARNING: Found % teams still using virtual_key. Consider migrating them first.', virtual_key_count;
    ELSE
        RAISE NOTICE 'OK: No teams using virtual_key. Safe to proceed.';
    END IF;
END $$;

-- Step 2: Remove virtual_key column from team_credits
ALTER TABLE team_credits
    DROP COLUMN IF EXISTS virtual_key CASCADE;

-- Step 3: Drop the associated index
DROP INDEX IF EXISTS idx_team_credits_virtual_key;

-- Step 4: Verify column was removed
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
        RAISE EXCEPTION 'ERROR: virtual_key column still exists!';
    ELSE
        RAISE NOTICE 'SUCCESS: virtual_key column removed from team_credits';
    END IF;
END $$;

-- Migration complete
SELECT 'Migration 012 completed successfully' as status;
