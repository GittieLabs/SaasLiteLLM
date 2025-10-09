#!/usr/bin/env python3
"""
Local development server startup script
"""
import sys
import subprocess
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from config.settings import settings
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
    print("   (Database connection will be tested by LiteLLM)")

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

    # Set environment variables for LiteLLM
    env = os.environ.copy()
    env["DATABASE_URL"] = settings.database_url
    env["LITELLM_MASTER_KEY"] = settings.litellm_master_key
    if settings.openai_api_key:
        env["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.anthropic_api_key:
        env["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
    if settings.redis_host:
        env["REDIS_HOST"] = settings.redis_host
        env["REDIS_PORT"] = str(settings.redis_port)

    # Config file path
    config_file = project_root / "src" / "config" / "litellm_config.yaml"

    # Start the LiteLLM proxy using CLI
    try:
        subprocess.run([
            "litellm",
            "--config", str(config_file),
            "--port", str(settings.port),
            "--host", settings.host,
            "--detailed_debug" if settings.debug else "--debug"
        ], env=env)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()
