#!/usr/bin/env python3
"""
Local development server startup script
"""
import sys
import subprocess
import os
from pathlib import Path

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
    
    # Check if .env file exists
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Copy the local environment: cp .env.local .env")
        return False
    
    print("✅ Prerequisites check passed!")
    return True

def start_server():
    """Start the development server using LiteLLM CLI"""
    if not check_prerequisites():
        sys.exit(1)
    
    # Get paths
    project_root = Path(__file__).parent.parent
    config_path = project_root / "src" / "config" / "litellm_config.yaml"
    
    print("")
    print("🚀 Starting LiteLLM proxy server...")
    print(f"🌐 Server will be available at: http://localhost:8000")
    print(f"🎛️  Admin UI will be available at: http://localhost:8000/ui")
    print(f"📖 API docs: http://localhost:8000/docs")
    print("")
    print("Press Ctrl+C to stop the server")
    print("")
    
    # Start the server using litellm CLI
    try:
        subprocess.run([
            "litellm",
            "--config", str(config_path),
            "--port", "8000",
            "--host", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()