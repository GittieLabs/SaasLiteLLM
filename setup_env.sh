#!/bin/bash

echo "Creating LiteLLM Railway project structure..."

# Create directory structure
mkdir -p src/config src/models src/utils scripts tests docker

# Create __init__.py files
cat > src/__init__.py << 'EOF'
# Main package
EOF

cat > src/config/__init__.py << 'EOF'
# Configuration module
EOF

cat > src/models/__init__.py << 'EOF'
# Models module
EOF

cat > src/utils/__init__.py << 'EOF'
# Utils module
EOF

cat > tests/__init__.py << 'EOF'
# Tests module
EOF

# Create pyproject.toml
cat > pyproject.toml << 'EOF'
[project]
name = "litellm-railway-app"
version = "0.1.0"
description = "LiteLLM proxy deployment for Railway with PostgreSQL"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "litellm[proxy]>=1.44.0",
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "psycopg2-binary>=2.9.7",
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.25.0",
    "redis>=5.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
target-version = "py311"
EOF

# Create docker-compose.yml for local development
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: litellm-postgres
    environment:
      POSTGRES_DB: litellm
      POSTGRES_USER: litellm_user
      POSTGRES_PASSWORD: litellm_password
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U litellm_user -d litellm"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - litellm-network

  redis:
    image: redis:7-alpine
    container_name: litellm-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - litellm-network

  # Optional: pgAdmin for database management
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: litellm-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@litellm.local
      PGADMIN_DEFAULT_PASSWORD: admin
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - "5050:80"
    depends_on:
      - postgres
    networks:
      - litellm-network
    profiles:
      - pgadmin

volumes:
  postgres_data:
  redis_data:

networks:
  litellm-network:
    driver: bridge
EOF

# Create docker/postgres/init.sql
cat > docker/postgres/init.sql << 'EOF'
-- Initialize the LiteLLM database
CREATE DATABASE litellm;

-- Create user if not exists
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'litellm_user') THEN
      CREATE USER litellm_user WITH PASSWORD 'litellm_password';
   END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE litellm TO litellm_user;

-- Connect to litellm database
\c litellm;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO litellm_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO litellm_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO litellm_user;

-- Create extension for UUID generation if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Basic setup complete
SELECT 'LiteLLM PostgreSQL database initialized successfully!' as message;
EOF

# Create .env.local for local development
cat > .env.local << 'EOF'
# Local Development Environment
DATABASE_URL=postgresql://litellm_user:litellm_password@localhost:5432/litellm

# LiteLLM Master Key (change this for production)
LITELLM_MASTER_KEY=sk-local-dev-master-key-change-me

# API Keys for LLM Providers
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Redis Configuration (local Docker)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Server Settings
HOST=0.0.0.0
PORT=8000
WORKERS=1
ENVIRONMENT=development
DEBUG=true
EOF

# Create src/config/litellm_config.yaml
cat > src/config/litellm_config.yaml << 'EOF'
model_list:
  # OpenAI Models
  - model_name: gpt-4-turbo
    litellm_params:
      model: gpt-4-turbo-preview
      api_key: os.environ/OPENAI_API_KEY
    model_info:
      mode: chat
      
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: gpt-3.5-turbo
      api_key: os.environ/OPENAI_API_KEY
    model_info:
      mode: chat

  # Anthropic Models
  - model_name: claude-3-opus
    litellm_params:
      model: claude-3-opus-20240229
      api_key: os.environ/ANTHROPIC_API_KEY
    model_info:
      mode: chat

  - model_name: claude-3-sonnet
    litellm_params:
      model: claude-3-sonnet-20240229
      api_key: os.environ/ANTHROPIC_API_KEY
    model_info:
      mode: chat

# General settings
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
  
# Router settings
router_settings:
  redis_host: os.environ/REDIS_HOST
  redis_port: os.environ/REDIS_PORT
  redis_password: os.environ/REDIS_PASSWORD
  enable_pre_call_checks: true
  
# Teams configuration
teams:
  - team_id: team_1
    team_alias: "development-team"
    members_with_roles:
      - role: "admin"
        user_id: "dev-admin"
    metadata:
      department: "engineering"
      budget_limit: 1000
    models:
      - "gpt-3.5-turbo"
      - "claude-3-sonnet"
      
  - team_id: team_2
    team_alias: "production-team"
    members_with_roles:
      - role: "admin"
        user_id: "prod-admin"
    metadata:
      department: "production"
      budget_limit: 5000
    models:
      - "gpt-4-turbo"
      - "claude-3-opus"
      - "claude-3-sonnet"
EOF

# Create src/config/settings.py
cat > src/config/settings.py << 'EOF'
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # LiteLLM
    litellm_master_key: str
    litellm_config_path: str = "src/config/litellm_config.yaml"
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Redis (optional for caching)
    redis_host: Optional[str] = None
    redis_port: Optional[int] = 6379
    redis_password: Optional[str] = None
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
EOF

# Create src/models/database.py
cat > src/models/database.py << 'EOF'
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

def get_database_engine():
    """Create database engine"""
    return create_engine(settings.database_url, echo=settings.debug)

def test_database_connection():
    """Test database connectivity"""
    try:
        engine = get_database_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def setup_database():
    """Setup database tables for LiteLLM"""
    try:
        # LiteLLM will handle table creation automatically
        # when the proxy starts with a valid database URL
        logger.info("Database setup initiated - LiteLLM will create tables automatically")
        return True
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False
EOF

# Create src/main.py
cat > src/main.py << 'EOF'
import os
import sys
import uvicorn
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings

def start_litellm_proxy():
    """Start LiteLLM proxy server"""
    # Set environment variables for LiteLLM
    os.environ["DATABASE_URL"] = settings.database_url
    os.environ["LITELLM_MASTER_KEY"] = settings.litellm_master_key
    
    # Set API keys if provided
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
        
    # Set Redis config if provided
    if settings.redis_host:
        os.environ["REDIS_HOST"] = settings.redis_host
        os.environ["REDIS_PORT"] = str(settings.redis_port)
        if settings.redis_password:
            os.environ["REDIS_PASSWORD"] = settings.redis_password
    
    # Import and start LiteLLM proxy
    from litellm.proxy.server import app, initialize
    
    # Initialize the proxy with config
    config_path = Path(__file__).parent / settings.litellm_config_path
    initialize(config_path=str(config_path))
    
    return app

# Create the FastAPI app
app = start_litellm_proxy()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug
    )
EOF

# Create scripts/docker_setup.sh
cat > scripts/docker_setup.sh << 'EOF'
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
EOF

# Create scripts/setup_local.sh
cat > scripts/setup_local.sh << 'EOF'
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

# Install dependencies
echo "Installing project dependencies..."
uv pip install -e .

echo "Installing development dependencies..."
uv pip install -e ".[dev]"

# Copy environment files
if [ ! -f .env ]; then
    echo "Copying .env.local to .env for local development..."
    cp .env.local .env
    echo "✅ Local environment file created"
else
    echo ".env file already exists"
fi

if [ ! -f .env.example ]; then
    echo "Creating .env.example for Railway deployment..."
    cp .env.example.template .env.example 2>/dev/null || echo "# See .env.local for local development template" > .env.example
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
EOF

# Create scripts/start_local.py
cat > scripts/start_local.py << 'EOF'
#!/usr/bin/env python3
"""
Local development server startup script
"""
import sys
import subprocess
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from config.settings import settings
    from models.database import test_database_connection
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    print("Make sure you've installed dependencies with: uv pip install -e .")
    sys.exit(1)

def check_docker_services():
    """Check if Docker services are running"""
    try:
        result = subprocess.run(["docker", "compose", "ps", "--services", "--filter", "status=running"], 
                              capture_output=True, text=True, check=True)
        running_services = result.stdout.strip().split('\n')
        
        postgres_running = 'postgres' in running_services
        redis_running = 'redis' in running_services
        
        if not postgres_running:
            print("❌ PostgreSQL container is not running")
            print("   Run: ./scripts/docker_setup.sh")
            return False
            
        if not redis_running:
            print("⚠️  Redis container is not running (optional)")
            
        return True
    except subprocess.CalledProcessError:
        print("❌ Docker services check failed")
        print("   Make sure Docker is running and services are started with: ./scripts/docker_setup.sh")
        return False

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check Docker services first
    if not check_docker_services():
        return False
    
    # Check environment variables
    try:
        database_url = settings.database_url
        master_key = settings.litellm_master_key
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        return False
    
    print(f"📊 Database: {database_url}")
    print(f"🔑 Master key: {master_key[:20]}...")
    
    # Test database connection
    if not test_database_connection():
        print("❌ Database connection failed")
        print("   Make sure PostgreSQL container is running: ./scripts/docker_setup.sh")
        return False
    
    print("✅ Prerequisites check passed!")
    return True

def start_server():
    """Start the development server"""
    if not check_prerequisites():
        sys.exit(1)
    
    print("")
    print("🚀 Starting LiteLLM proxy server...")
    print(f"🌐 Server will be available at: http://{settings.host}:{settings.port}")
    print(f"🎛️  Admin UI will be available at: http://{settings.host}:{settings.port}/ui")
    print(f"📖 API docs: http://{settings.host}:{settings.port}/docs")
    print("")
    print("Press Ctrl+C to stop the server")
    print("")
    
    # Start the server
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.main:app",
            "--host", settings.host,
            "--port", str(settings.port),
            "--reload" if settings.debug else "--no-reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()
EOF

# Create scripts/setup_teams.py
cat > scripts/setup_teams.py << 'EOF'
#!/usr/bin/env python3
"""
Script to setup teams and generate API keys
"""
import asyncio
import httpx
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.settings import settings

async def create_team_and_keys():
    """Create teams and generate virtual API keys"""
    base_url = f"http://{settings.host}:{settings.port}"
    headers = {
        "Authorization": f"Bearer {settings.litellm_master_key}",
        "Content-Type": "application/json"
    }
    
    teams_config = [
        {
            "team_id": "team_dev",
            "team_alias": "development-team",
            "models": ["gpt-3.5-turbo", "claude-3-sonnet"],
            "budget_limit": 100.0
        },
        {
            "team_id": "team_prod", 
            "team_alias": "production-team",
            "models": ["gpt-4-turbo", "claude-3-opus"],
            "budget_limit": 1000.0
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for team_config in teams_config:
            try:
                # Create team
                team_response = await client.post(
                    f"{base_url}/team/new",
                    headers=headers,
                    json=team_config
                )
                
                if team_response.status_code == 200:
                    print(f"✅ Created team: {team_config['team_alias']}")
                    
                    # Generate API key for team
                    key_data = {
                        "team_id": team_config["team_id"],
                        "models": team_config["models"],
                        "max_budget": team_config["budget_limit"]
                    }
                    
                    key_response = await client.post(
                        f"{base_url}/key/generate",
                        headers=headers,
                        json=key_data
                    )
                    
                    if key_response.status_code == 200:
                        key_info = key_response.json()
                        print(f"🔑 Generated API key for {team_config['team_alias']}: {key_info.get('key', 'N/A')}")
                    else:
                        print(f"❌ Failed to generate key for {team_config['team_alias']}: {key_response.text}")
                        
                else:
                    print(f"❌ Failed to create team {team_config['team_alias']}: {team_response.text}")
                    
            except Exception as e:
                print(f"❌ Error setting up team {team_config['team_alias']}: {e}")

if __name__ == "__main__":
    print("🔧 Setting up teams and API keys...")
    print("Make sure the LiteLLM server is running first!")
    print("")
    asyncio.run(create_team_and_keys())
EOF

# Create scripts/stop_docker.sh
cat > scripts/stop_docker.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping Docker services..."

# Stop all services
docker compose down

echo "✅ Docker services stopped"
echo ""
echo "To start again: ./scripts/docker_setup.sh"
EOF

# Create .env.example for Railway deployment
cat > .env.example << 'EOF'
# Database Configuration (Railway PostgreSQL)
DATABASE_URL=postgresql://username:password@host:port/database

# LiteLLM Master Key (generate a secure random string)
LITELLM_MASTER_KEY=your-super-secure-master-key-here

# API Keys for LLM Providers
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Redis Configuration (optional, for caching)
REDIS_HOST=
REDIS_PORT=6379
REDIS_PASSWORD=

# Server Settings
HOST=0.0.0.0
PORT=8000
WORKERS=1
ENVIRONMENT=production
DEBUG=false
EOF

# Create railway.toml
cat > railway.toml << 'EOF'
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python src/main.py"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
EOF

# Create Procfile
cat > Procfile << 'EOF'
web: python src/main.py
EOF

# Create runtime.txt
cat > runtime.txt << 'EOF'
python-3.11.6
EOF

# Create tests/test_main.py
cat > tests/test_main.py << 'EOF'
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_import_main():
    """Test that main module can be imported"""
    try:
        from main import app
        assert app is not None
    except ImportError:
        pytest.skip("Dependencies not installed")

def test_settings_load():
    """Test that settings can be loaded"""
    try:
        from config.settings import Settings
        settings = Settings()
        assert settings is not None
    except ImportError:
        pytest.skip("Dependencies not installed")
EOF

# Create .dockerignore
cat > .dockerignore << 'EOF'
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.git/
.gitignore
README.md
.env
.env.local
docker-compose.yml
.pytest_cache/
.coverage
tests/
scripts/
EOF

# Create README.md
cat > README.md << 'EOF'
# LiteLLM Railway Deployment

A production-ready LiteLLM proxy deployment for Railway with PostgreSQL support, team management, and virtual API keys.

## Features

- 🚀 Deploy to Railway with one click
- 🐘 PostgreSQL database integration
- 👥 Team management with role-based access
- 🔑 Virtual API key generation
- 🔄 Multiple LLM provider support (OpenAI, Anthropic, etc.)
- 📊 Built-in admin UI and monitoring
- 🐳 Docker Compose for local development

## Quick Start

### Local Development with Docker

1. **Setup the project:**
   ```bash
   chmod +x setup_env.sh
   ./setup_env.sh
   ```

2. **Start Docker services:**
   ```bash
   ./scripts/docker_setup.sh
   ```

3. **Configure API keys:**
   ```bash
   # Edit .env file and add your API keys
   nano .env
   ```

4. **Start the LiteLLM server:**
   ```bash
   source .venv/bin/activate
   python scripts/start_local.py
   ```

5. **Setup teams (after server is running):**
   ```bash
   python scripts/setup_teams.py
   ```

### One-Command Local Setup

```bash
./scripts/docker_setup.sh && source .venv/bin/activate && python scripts/start_local.py
```

### Railway Deployment

1. **Connect to Railway:**
   - Create a new Railway project
   - Add a PostgreSQL service
   - Connect your GitHub repository

2. **Configure environment variables in Railway:**
   ```
   DATABASE_URL=<from-railway-postgres>
   LITELLM_MASTER_KEY=<generate-secure-key>
   OPENAI_API_KEY=<your-openai-key>
   ANTHROPIC_API_KEY=<your-anthropic-key>
   ```

3. **Deploy:**
   - Railway will automatically deploy on push to main branch

## Local Development

### Docker Services

The project includes Docker Compose configuration for:

- **PostgreSQL 15**: Database server (localhost:5432)
- **Redis 7**: Caching server (localhost:6379) 
- **pgAdmin** (optional): Database management UI (localhost:5050)

### Commands

```bash
# Start Docker services
./scripts/docker_setup.sh

# Stop Docker services  
./scripts/stop_docker.sh

# Start with pgAdmin
docker compose --profile pgadmin up -d

# View logs
docker compose logs -f postgres
docker compose logs -f redis

# Reset database
docker compose down -v
./scripts/docker_setup.sh
```

### Local URLs

- **LiteLLM Server**: http://localhost:8000
- **Admin UI**: http://localhost:8000/ui
- **API Docs**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:5050 (admin@litellm.local/admin)

## API Usage

### Access the Admin UI
```
http://localhost:8000/ui
```

### Generate API Keys
```bash
curl -X POST http://localhost:8000/key/generate \
  -H "Authorization: Bearer sk-local-dev-master-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "team_dev",
    "models": ["gpt-3.5-turbo"],
    "max_budget": 100
  }'
```

### Use Virtual API Keys
```bash
curl -X POST http://localhost:8000/chat/completions \
  -H "Authorization: Bearer YOUR_VIRTUAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Configuration

### Adding New Models
Edit `src/config/litellm_config.yaml`:

```yaml
model_list:
  - model_name: new-model
    litellm_params:
      model: provider/model-name
      api_key: os.environ/PROVIDER_API_KEY
```

### Environment Files

- `.env.local`: Local development with Docker
- `.env.example`: Template for Railway deployment
- `.env`: Your actual environment (not in git)

## Development

### Running Tests
```bash
source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

### Code Formatting
```bash
black src/
ruff check src/
```

## Monitoring

- Health check: `/health`
- Metrics: `/metrics` 
- Admin dashboard: `/ui`
- API documentation: `/docs`

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Test connection manually
docker exec -it litellm-postgres psql -U litellm_user -d litellm
```

### Reset Everything
```bash
# Stop services and remove volumes
docker compose down -v

# Restart fresh
./scripts/docker_setup.sh
```

## Support

For issues and questions, please check the LiteLLM documentation or create an issue in this repository.
EOF

# Make scripts executable
chmod +x scripts/setup_local.sh
chmod +x scripts/start_local.py
chmod +x scripts/setup_teams.py
chmod +x scripts/docker_setup.sh
chmod +x scripts/stop_docker.sh

echo "🎉 Project structure created successfully!"
echo ""
echo "📁 Files created:"
echo "├── src/                     # LiteLLM application code"
echo "├── scripts/                 # Setup and utility scripts"
echo "├── docker/                  # Docker configuration"
echo "├── tests/                   # Test files"
echo "├── docker-compose.yml       # Local development services"
echo "├── .env.local               # Local environment settings"
echo "├── .env.example             # Railway deployment template"
echo "├── pyproject.toml           # Python dependencies"
echo "├── railway.toml             # Railway deployment config"
echo "└── README.md                # Documentation"
echo ""
echo "🐳 Docker services configured:"
echo "   📊 PostgreSQL (localhost:5432)"
echo "   🔴 Redis (localhost:6379)"
echo "   🔧 pgAdmin (localhost:5050) - optional"
echo ""
echo "🚀 Next steps:"
echo "1. Install dependencies: ./scripts/setup_local.sh"
echo "2. Start Docker services: ./scripts/docker_setup.sh"
echo "3. Add API keys to .env file"
echo "4. Start LiteLLM: source .venv/bin/activate && python scripts/start_local.py"
echo ""
echo "📖 Quick start command:"
echo "   ./scripts/setup_local.sh && ./scripts/docker_setup.sh"