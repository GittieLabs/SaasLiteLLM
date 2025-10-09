#!/bin/bash

# Setup script for local development
echo "Setting up LiteLLM Railway App locally..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

cd "$PROJECT_DIR"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Try to source uv from common locations
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    elif [ -f "$HOME/.local/bin/uv" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    # Check again if uv is available
    if ! command -v uv &> /dev/null; then
        echo "Failed to install uv. Please install it manually from https://github.com/astral-sh/uv"
        exit 1
    fi
fi

echo "uv version: $(uv --version)"

# Create virtual environment and install dependencies
echo "Creating virtual environment and installing dependencies..."
uv venv

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "Virtual environment activated"
else
    echo "Failed to create virtual environment"
    exit 1
fi

# Install dependencies directly instead of editable install
echo "Installing project dependencies..."
uv pip install litellm[proxy]>=1.44.0 fastapi>=0.104.0 uvicorn[standard]>=0.24.0 psycopg2-binary>=2.9.7 sqlalchemy>=2.0.0 alembic>=1.12.0 pydantic>=2.5.0 pydantic-settings>=2.1.0 python-dotenv>=1.0.0 httpx>=0.25.0 redis>=5.0.0

echo "Installing development dependencies..."
uv pip install pytest>=7.4.0 pytest-asyncio>=0.21.0 black>=23.0.0 ruff>=0.1.0 mypy>=1.7.0

# Copy environment files
if [ ! -f .env ]; then
    echo "Copying .env.local to .env for local development..."
    cp .env.local .env
    echo "✅ Local environment file created"
else
    echo ".env file already exists"
fi

echo ""
echo "Setup complete! 🎉"
echo ""
echo "Next steps for local development:"
echo "1. Start Docker services: ./scripts/docker_setup.sh"
echo "2. Add your API keys to .env file"
echo "3. Start the server: source .venv/bin/activate && python scripts/start_local.py"
echo ""
echo "Or run everything at once:"
echo "  ./scripts/docker_setup.sh && source .venv/bin/activate && python scripts/start_local.py"