#!/bin/bash

echo "🐳 Setting up Docker environment for LiteLLM..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop from https://docker.com"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please update Docker Desktop."
    exit 1
fi

echo "✅ Docker is available"

# Start the services
echo "🚀 Starting PostgreSQL and Redis containers..."
docker compose up -d postgres redis

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker compose ps postgres | grep -q "Up"; then
    echo "✅ PostgreSQL is running on localhost:5432"
else
    echo "❌ Failed to start PostgreSQL"
    exit 1
fi

if docker compose ps redis | grep -q "Up"; then
    echo "✅ Redis is running on localhost:6379"
else
    echo "❌ Failed to start Redis"
    exit 1
fi

# Test database connection
echo "🔌 Testing database connection..."
sleep 5

if docker exec litellm-postgres pg_isready -U litellm_user -d litellm; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    exit 1
fi

echo ""
echo "🎉 Docker environment is ready!"
echo ""
echo "Services running:"
echo "  📊 PostgreSQL: localhost:5432 (litellm/litellm_user)"
echo "  🔴 Redis: localhost:6379"
echo ""
echo "Optional:"
echo "  🔧 pgAdmin: docker compose --profile pgadmin up -d pgadmin"
echo "  📱 Access pgAdmin at: http://localhost:5050 (admin@litellm.local/admin)"
echo ""
echo "Next steps:"
echo "  1. Copy local env: cp .env.local .env"
echo "  2. Add your API keys to .env"
echo "  3. Run: python scripts/start_local.py"
