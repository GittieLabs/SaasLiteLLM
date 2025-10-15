from pydantic_settings import BaseSettings
from typing import Optional
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Database
    database_url: str

    # SaaS API Admin Authentication
    # IMPORTANT: Set MASTER_KEY environment variable in production!
    master_key: str = "sk-admin-default-CHANGE-THIS-IN-PRODUCTION"  # Admin API key for SaaS management endpoints

    # LiteLLM
    # IMPORTANT: Set LITELLM_MASTER_KEY environment variable in production!
    litellm_master_key: str = "sk-litellm-default-CHANGE-THIS-IN-PRODUCTION"
    litellm_config_path: str = "src/config/litellm_config.yaml"
    litellm_proxy_url: str = "http://localhost:8002"  # Default for local dev

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

    # Admin Panel URL for CORS (optional, supports Railway service references)
    # In Railway, set to: https://${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}
    admin_panel_url: Optional[str] = None

    # Additional CORS origins (comma-separated, optional)
    additional_cors_origins: Optional[str] = None

    class Config:
        # Look for .env file in project root (parent of src/)
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = False

settings = Settings()

# Security warning for default keys
if settings.master_key == "sk-admin-default-CHANGE-THIS-IN-PRODUCTION":
    if settings.environment == "production":
        logger.error("⚠️  SECURITY WARNING: Using default MASTER_KEY in production! Set MASTER_KEY environment variable immediately!")
    else:
        logger.warning("Using default MASTER_KEY. Set MASTER_KEY environment variable for production.")

if settings.litellm_master_key == "sk-litellm-default-CHANGE-THIS-IN-PRODUCTION":
    if settings.environment == "production":
        logger.error("⚠️  SECURITY WARNING: Using default LITELLM_MASTER_KEY in production! Set LITELLM_MASTER_KEY environment variable immediately!")
    else:
        logger.warning("Using default LITELLM_MASTER_KEY. Set LITELLM_MASTER_KEY environment variable for production.")
