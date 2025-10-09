#!/usr/bin/env python3
"""
Simple script to manually create LiteLLM database tables
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_basic_tables():
    # Database connection parameters
    db_params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'litellm',
        'user': 'litellm_user',
        'password': 'litellm_password'
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("Creating basic LiteLLM tables...")
        
        # Create essential tables for LiteLLM to function
        tables = [
            """
            CREATE TABLE IF NOT EXISTS "LiteLLM_VerificationToken" (
                token TEXT PRIMARY KEY,
                spend FLOAT DEFAULT 0,
                expires TEXT,
                models TEXT[],
                aliases JSON,
                config JSON,
                user_id TEXT,
                team_id TEXT,
                max_parallel_requests INTEGER,
                metadata JSON,
                tpm_limit BIGINT,
                rpm_limit BIGINT,
                max_budget FLOAT,
                budget_duration TEXT,
                budget_reset_at TIMESTAMP,
                allowed_cache_controls TEXT[],
                soft_budget FLOAT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "LiteLLM_SpendLogs" (
                request_id TEXT PRIMARY KEY,
                call_type TEXT,
                api_key TEXT,
                spend FLOAT,
                total_tokens INTEGER,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                startTime TIMESTAMP,
                endTime TIMESTAMP,
                model TEXT,
                user TEXT,
                metadata JSON,
                cache_hit TEXT,
                cache_key TEXT,
                request_tags TEXT[],
                team_id TEXT,
                end_user TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "LiteLLM_TeamTable" (
                team_id TEXT PRIMARY KEY,
                team_alias TEXT,
                organization_id TEXT,
                metadata JSON,
                max_budget FLOAT,
                spend FLOAT DEFAULT 0,
                models TEXT[],
                blocked BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "LiteLLM_UserTable" (
                user_id TEXT PRIMARY KEY,
                user_email TEXT,
                user_role TEXT,
                teams TEXT[],
                organization_id TEXT,
                max_budget FLOAT,
                spend FLOAT DEFAULT 0,
                models TEXT[],
                blocked BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """
        ]
        
        for table_sql in tables:
            cur.execute(table_sql)
            print("✓ Created table")
        
        print("✓ All basic tables created successfully!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_basic_tables()
    if success:
        print("Database setup completed successfully!")
    else:
        print("Database setup failed!")