from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.settings import settings
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
