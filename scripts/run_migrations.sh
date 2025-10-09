#!/bin/bash
# Run database migrations for job tracking tables

echo "🔄 Running database migrations..."

# Check if PostgreSQL container is running
if ! docker compose ps postgres | grep -q "Up"; then
    echo "❌ PostgreSQL container is not running"
    echo "   Run: docker compose up -d postgres"
    exit 1
fi

MIGRATION_DIR="$(dirname "$0")/migrations"

if [ ! -d "$MIGRATION_DIR" ]; then
    echo "❌ Migrations directory not found: $MIGRATION_DIR"
    exit 1
fi

# Run each migration file in order
for migration in "$MIGRATION_DIR"/*.sql; do
    if [ -f "$migration" ]; then
        echo "📄 Running migration: $(basename "$migration")"
        docker exec -i litellm-postgres sh -c 'PGPASSWORD=litellm_password psql -U litellm_user -d litellm' < "$migration"

        if [ $? -eq 0 ]; then
            echo "✅ Migration completed: $(basename "$migration")"
        else
            echo "❌ Migration failed: $(basename "$migration")"
            exit 1
        fi
    fi
done

echo ""
echo "🎉 All migrations completed successfully!"
echo ""
echo "📊 Current tables:"
docker exec litellm-postgres sh -c 'PGPASSWORD=litellm_password psql -U litellm_user -d litellm -c "\dt"'
