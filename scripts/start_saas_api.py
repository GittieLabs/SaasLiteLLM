#!/usr/bin/env python3
"""
Start the SaaS API wrapper service on port 8003 (local dev).
This runs alongside LiteLLM (port 8002 local, 8000 production).
"""
import sys
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.settings import settings

def start_saas_api():
    """Start the SaaS API service"""
    print("🚀 Starting SaaS API wrapper service...")
    print(f"🌐 SaaS API will be available at: http://0.0.0.0:8003")
    print(f"📖 API docs: http://0.0.0.0:8003/docs")
    print(f"🔗 LiteLLM backend: http://localhost:{settings.port}")
    print("")
    print(f"Make sure LiteLLM is running on port {settings.port} first!")
    print("Press Ctrl+C to stop")
    print("")

    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.saas_api:app",
            "--host", "0.0.0.0",
            "--port", "8003",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 SaaS API stopped")
    except Exception as e:
        print(f"❌ Failed to start SaaS API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_saas_api()
