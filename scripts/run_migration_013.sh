#!/bin/bash
# Run migration 013 to restore virtual_key column via Railway shell

set -e

echo "Running migration 013 to restore virtual_key column..."

# Use Railway's shell command to execute SQL directly
railway run --service=saas-api bash -c "python3 << 'PYTHON_EOF'
import os
from sqlalchemy import create_engine, text

# Get database URL from environment
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print('ERROR: DATABASE_URL not found in environment')
    exit(1)

print('Connecting to database...')
engine = create_engine(database_url)

migration_sql = '''
ALTER TABLE team_credits ADD COLUMN IF NOT EXISTS virtual_key VARCHAR(500);
CREATE INDEX IF NOT EXISTS idx_team_credits_virtual_key ON team_credits(virtual_key);
'''

print('Executing migration...')
with engine.connect() as conn:
    with conn.begin():
        conn.execute(text('ALTER TABLE team_credits ADD COLUMN IF NOT EXISTS virtual_key VARCHAR(500)'))
        print('✓ Added virtual_key column')
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_team_credits_virtual_key ON team_credits(virtual_key)'))
        print('✓ Created index')

print('Migration 013 completed successfully!')
PYTHON_EOF
"

echo "Done!"
