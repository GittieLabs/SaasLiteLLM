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
