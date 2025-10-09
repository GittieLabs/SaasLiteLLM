#!/bin/bash

echo "🛑 Stopping Docker services..."

# Stop all services
docker compose down

echo "✅ Docker services stopped"
echo ""
echo "To start again: ./scripts/docker_setup.sh"
