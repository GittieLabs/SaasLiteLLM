-- =====================================================
-- DROP ALL LITELLM PROXY TABLES
-- =====================================================
-- Purpose: Remove all LiteLLM proxy database tables
-- Date: 2025-10-23
--
-- WARNING: THIS IS IRREVERSIBLE!
--
-- Run only after:
--   1. All teams migrated to direct provider credentials
--   2. LiteLLM proxy service is shut down
--   3. virtual_key column removed from team_credits (migration 012)
--   4. Database backup created
--
-- Backup command before running:
-- pg_dump -h HOST -p PORT -U postgres -d railway > backup_before_litellm_drop_$(date +%Y%m%d_%H%M%S).sql
-- =====================================================

-- Pre-check: Verify virtual_key column is gone
DO $$
DECLARE
    virtual_key_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'team_credits'
        AND column_name = 'virtual_key'
    ) INTO virtual_key_exists;

    IF virtual_key_exists THEN
        RAISE EXCEPTION 'ABORTED: virtual_key column still exists in team_credits. Run migration 012 first!';
    END IF;
END $$;

-- Show what we're about to drop
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size('public."' || tablename || '"')) as size
FROM pg_tables
WHERE tablename LIKE 'LiteLLM_%'
ORDER BY tablename;

-- Confirmation message
DO $$
BEGIN
    RAISE NOTICE '================================================================';
    RAISE NOTICE 'About to drop 17 LiteLLM tables. This cannot be undone!';
    RAISE NOTICE 'Press Ctrl+C within 5 seconds to cancel...';
    RAISE NOTICE '================================================================';
    PERFORM pg_sleep(5);
END $$;

-- Drop in order (respecting foreign key dependencies)
-- Start with dependent/child tables, end with parent tables

-- Drop dependent tables first
DROP TABLE IF EXISTS "LiteLLM_ObjectPermissionTable" CASCADE;
DROP TABLE IF EXISTS "LiteLLM_TagTable" CASCADE;
DROP TABLE IF EXISTS "LiteLLM_EndUserTable" CASCADE;
DROP TABLE IF EXISTS "LiteLLM_HealthCheckTable" CASCADE;

-- Drop managed resources
DROP TABLE IF EXISTS "LiteLLM_ManagedFileTable" CASCADE;
DROP TABLE IF EXISTS "LiteLLM_ManagedObjectTable" CASCADE;
DROP TABLE IF EXISTS "LiteLLM_ManagedVectorStoresTable" CASCADE;
DROP TABLE IF EXISTS "LiteLLM_MCPServerTable" CASCADE;

-- Drop feature tables
DROP TABLE IF EXISTS "LiteLLM_GuardrailsTable" CASCADE;
DROP TABLE IF EXISTS "LiteLLM_PromptTable" CASCADE;

-- Drop model and credential tables
DROP TABLE IF EXISTS "LiteLLM_ModelTable" CASCADE;
DROP TABLE IF EXISTS "LiteLLM_ProxyModelTable" CASCADE;
DROP TABLE IF EXISTS "LiteLLM_CredentialsTable" CASCADE;

-- Drop budget and core tables
DROP TABLE IF EXISTS "LiteLLM_BudgetTable" CASCADE;
DROP TABLE IF EXISTS "LiteLLM_UserTable" CASCADE;
DROP TABLE IF EXISTS "LiteLLM_TeamTable" CASCADE;
DROP TABLE IF EXISTS "LiteLLM_OrganizationTable" CASCADE;

-- Verify all LiteLLM tables are dropped
DO $$
DECLARE
    remaining_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO remaining_count
    FROM pg_tables
    WHERE tablename LIKE 'LiteLLM_%';

    IF remaining_count > 0 THEN
        RAISE EXCEPTION 'ERROR: % LiteLLM tables still exist!', remaining_count;
    ELSE
        RAISE NOTICE '================================================================';
        RAISE NOTICE 'SUCCESS: All 17 LiteLLM tables have been dropped';
        RAISE NOTICE '================================================================';
    END IF;
END $$;

-- Show remaining tables (should only be your application tables)
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size('public.' || tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
AND tablename NOT LIKE 'pg_%'
AND tablename NOT LIKE 'sql_%'
ORDER BY tablename;

-- Final summary
SELECT
    COUNT(*) as total_tables,
    pg_size_pretty(SUM(pg_total_relation_size('public.' || tablename))) as total_size
FROM pg_tables
WHERE schemaname = 'public'
AND tablename NOT LIKE 'pg_%'
AND tablename NOT LIKE 'sql_%';

-- Migration complete
SELECT 'LiteLLM proxy tables dropped successfully' as status;
