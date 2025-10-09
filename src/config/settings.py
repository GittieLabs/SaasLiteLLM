from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

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
        # Look for .env file in project root (parent of src/)
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = False

settings = Settings()
