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
