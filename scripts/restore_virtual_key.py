"""
Script to restore virtual_key column to team_credits table
This rolls back migration 012 which removed the column prematurely
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, text
from config.settings import settings

def main():
    """Run migration 013 to restore virtual_key column"""
    print("Connecting to database...")
    engine = create_engine(settings.database_url)

    migration_sql = """
-- Migration 013: Restore virtual_key column
-- Purpose: Rollback migration 012 - authentication system still depends on virtual_key

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

SELECT 'Migration 013 completed successfully - virtual_key column restored' as status;
    """

    print("Executing migration 013...")
    with engine.connect() as conn:
        # Execute as a transaction
        with conn.begin():
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
            for stmt in statements:
                if stmt:
                    print(f"Executing: {stmt[:50]}...")
                    result = conn.execute(text(stmt))
                    # Try to fetch results if any
                    try:
                        rows = result.fetchall()
                        for row in rows:
                            print(f"  Result: {row}")
                    except:
                        pass

    print("\nMigration 013 completed successfully!")
    print("The virtual_key column has been restored to team_credits table.")

if __name__ == "__main__":
    main()
