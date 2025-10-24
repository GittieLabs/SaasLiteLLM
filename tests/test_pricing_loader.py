"""
Comprehensive tests for pricing_loader module

Tests pricing data loading from llm_pricing_current.json including:
- Successful loading and conversion
- Caching behavior
- Fallback pricing when file missing
- Error handling
- Metadata extraction
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Import from src
import sys
from pathlib import Path as PathType
sys.path.insert(0, str(PathType(__file__).parent.parent / "src"))

from utils.pricing_loader import (
    load_pricing_from_json,
    reload_pricing,
    get_pricing_metadata,
    _get_pricing_file_path,
    _convert_json_pricing_to_model_pricing,
    _get_fallback_pricing
)


class TestGetPricingFilePath:
    """Test finding the pricing JSON file"""

    def test_get_pricing_file_path_success(self):
        """Test that pricing file path is found"""
        path = _get_pricing_file_path()

        assert path is not None
        assert isinstance(path, Path)
        assert path.name == "llm_pricing_current.json"

    def test_get_pricing_file_path_exists(self):
        """Test that the pricing file actually exists"""
        path = _get_pricing_file_path()

        if path:  # Only test if path found
            assert path.exists()


class TestConvertJsonPricingToModelPricing:
    """Test JSON to MODEL_PRICING format conversion"""

    def test_convert_basic_pricing(self):
        """Test converting basic pricing data"""
        json_data = {
            "openai": {
                "gpt-4o": {
                    "input_cost_per_token": 2.5e-06,
                    "output_cost_per_token": 1e-05
                }
            }
        }

        result = _convert_json_pricing_to_model_pricing(json_data)

        assert "gpt-4o" in result
        assert result["gpt-4o"]["input"] == 2.50
        assert result["gpt-4o"]["output"] == 10.00

    def test_convert_multiple_providers(self):
        """Test converting multiple providers"""
        json_data = {
            "openai": {
                "gpt-4o": {
                    "input_cost_per_token": 2.5e-06,
                    "output_cost_per_token": 1e-05
                }
            },
            "anthropic": {
                "claude-sonnet-4-5": {
                    "input_cost_per_token": 3e-06,
                    "output_cost_per_token": 1.5e-05
                }
            }
        }

        result = _convert_json_pricing_to_model_pricing(json_data)

        assert "gpt-4o" in result
        assert "claude-sonnet-4-5" in result
        assert result["claude-sonnet-4-5"]["input"] == 3.00
        assert result["claude-sonnet-4-5"]["output"] == 15.00

    def test_convert_skips_metadata(self):
        """Test that metadata section is skipped"""
        json_data = {
            "metadata": {
                "last_updated": "2025-01-01"
            },
            "pricing_notes": {
                "note": "Some info"
            },
            "openai": {
                "gpt-4o": {
                    "input_cost_per_token": 2.5e-06,
                    "output_cost_per_token": 1e-05
                }
            }
        }

        result = _convert_json_pricing_to_model_pricing(json_data)

        assert "metadata" not in result
        assert "pricing_notes" not in result
        assert "gpt-4o" in result

    def test_convert_includes_default_pricing(self):
        """Test that default pricing is always included"""
        json_data = {
            "openai": {
                "gpt-4o": {
                    "input_cost_per_token": 2.5e-06,
                    "output_cost_per_token": 1e-05
                }
            }
        }

        result = _convert_json_pricing_to_model_pricing(json_data)

        assert "default" in result
        assert result["default"]["input"] == 1.00
        assert result["default"]["output"] == 2.00

    def test_convert_handles_missing_costs(self):
        """Test handling of models with missing cost fields"""
        json_data = {
            "openai": {
                "gpt-4o": {
                    "max_tokens": 128000
                    # Missing input_cost_per_token and output_cost_per_token
                }
            }
        }

        result = _convert_json_pricing_to_model_pricing(json_data)

        # Should still create entry with 0 costs
        assert "gpt-4o" in result
        assert result["gpt-4o"]["input"] == 0.00
        assert result["gpt-4o"]["output"] == 0.00


class TestGetFallbackPricing:
    """Test fallback pricing"""

    def test_fallback_pricing_has_major_models(self):
        """Test that fallback includes major models"""
        pricing = _get_fallback_pricing()

        assert "gpt-4o" in pricing
        assert "claude-sonnet-4-5" in pricing
        assert "gemini-2.5-pro" in pricing
        assert "default" in pricing

    def test_fallback_pricing_format(self):
        """Test fallback pricing has correct format"""
        pricing = _get_fallback_pricing()

        for model, prices in pricing.items():
            assert "input" in prices
            assert "output" in prices
            assert isinstance(prices["input"], (int, float))
            assert isinstance(prices["output"], (int, float))


class TestLoadPricingFromJson:
    """Test main pricing loading function"""

    def test_load_pricing_success(self):
        """Test successful loading of pricing data"""
        # Reset cache
        import utils.pricing_loader
        utils.pricing_loader._PRICING_CACHE = None

        pricing = load_pricing_from_json()

        assert isinstance(pricing, dict)
        assert len(pricing) > 0
        assert "default" in pricing

    def test_load_pricing_caches_result(self):
        """Test that pricing is cached after first load"""
        import utils.pricing_loader
        utils.pricing_loader._PRICING_CACHE = None

        # First call
        pricing1 = load_pricing_from_json()

        # Second call should return cached version
        pricing2 = load_pricing_from_json()

        assert pricing1 is pricing2  # Same object reference

    @patch('utils.pricing_loader._get_pricing_file_path')
    def test_load_pricing_file_not_found(self, mock_get_path):
        """Test fallback when pricing file not found"""
        import utils.pricing_loader
        utils.pricing_loader._PRICING_CACHE = None

        mock_get_path.return_value = None

        pricing = load_pricing_from_json()

        # Should return fallback pricing
        assert isinstance(pricing, dict)
        assert "gpt-4o" in pricing
        assert "default" in pricing

    @patch('builtins.open', side_effect=IOError("Permission denied"))
    @patch('utils.pricing_loader._get_pricing_file_path')
    def test_load_pricing_read_error(self, mock_get_path, mock_open_func):
        """Test fallback when file cannot be read"""
        import utils.pricing_loader
        utils.pricing_loader._PRICING_CACHE = None

        mock_get_path.return_value = Path("/fake/path.json")

        pricing = load_pricing_from_json()

        # Should return fallback pricing
        assert isinstance(pricing, dict)
        assert "default" in pricing

    @patch('builtins.open', mock_open(read_data='{"invalid json}'))
    @patch('utils.pricing_loader._get_pricing_file_path')
    def test_load_pricing_invalid_json(self, mock_get_path):
        """Test fallback when JSON is invalid"""
        import utils.pricing_loader
        utils.pricing_loader._PRICING_CACHE = None

        mock_get_path.return_value = Path("/fake/path.json")

        pricing = load_pricing_from_json()

        # Should return fallback pricing
        assert isinstance(pricing, dict)
        assert "default" in pricing


class TestReloadPricing:
    """Test pricing reload functionality"""

    def test_reload_clears_cache(self):
        """Test that reload clears the cache"""
        import utils.pricing_loader

        # Set cache
        utils.pricing_loader._PRICING_CACHE = {"test": "data"}

        # Reload
        pricing = reload_pricing()

        # Cache should be refreshed
        assert pricing is not None
        assert "test" not in pricing or pricing["test"] != "data"

    def test_reload_loads_fresh_data(self):
        """Test that reload loads fresh data"""
        import utils.pricing_loader
        utils.pricing_loader._PRICING_CACHE = {"old": "data"}

        new_pricing = reload_pricing()

        assert isinstance(new_pricing, dict)
        assert "default" in new_pricing


class TestGetPricingMetadata:
    """Test metadata extraction"""

    def test_get_metadata_success(self):
        """Test successful metadata extraction"""
        metadata = get_pricing_metadata()

        assert isinstance(metadata, dict)
        # Should have either metadata or error key
        assert "last_updated" in metadata or "error" in metadata

    @patch('utils.pricing_loader._get_pricing_file_path')
    def test_get_metadata_file_not_found(self, mock_get_path):
        """Test metadata when file not found"""
        mock_get_path.return_value = None

        metadata = get_pricing_metadata()

        assert "error" in metadata
        assert metadata["error"] == "Pricing file not found"

    @patch('builtins.open', side_effect=IOError("Read error"))
    @patch('utils.pricing_loader._get_pricing_file_path')
    def test_get_metadata_read_error(self, mock_get_path, mock_open_func):
        """Test metadata when file cannot be read"""
        mock_get_path.return_value = Path("/fake/path.json")

        metadata = get_pricing_metadata()

        assert "error" in metadata


class TestIntegration:
    """Integration tests with actual pricing file"""

    def test_load_real_pricing_file(self):
        """Test loading the actual pricing file"""
        import utils.pricing_loader
        utils.pricing_loader._PRICING_CACHE = None

        pricing = load_pricing_from_json()

        # Basic validation
        assert isinstance(pricing, dict)
        assert len(pricing) > 10  # Should have many models

        # Spot check some models
        if "gpt-4o" in pricing:
            assert "input" in pricing["gpt-4o"]
            assert "output" in pricing["gpt-4o"]
            assert pricing["gpt-4o"]["input"] > 0
            assert pricing["gpt-4o"]["output"] > 0

    def test_pricing_format_consistency(self):
        """Test that all loaded pricing has consistent format"""
        import utils.pricing_loader
        utils.pricing_loader._PRICING_CACHE = None

        pricing = load_pricing_from_json()

        for model_name, prices in pricing.items():
            assert isinstance(prices, dict), f"Model {model_name} prices not a dict"
            assert "input" in prices, f"Model {model_name} missing 'input'"
            assert "output" in prices, f"Model {model_name} missing 'output'"
            assert isinstance(prices["input"], (int, float)), f"Model {model_name} input not numeric"
            assert isinstance(prices["output"], (int, float)), f"Model {model_name} output not numeric"

    def test_conversion_accuracy(self):
        """Test that per-token to per-million conversion is accurate"""
        # Create test data with known values
        json_data = {
            "test_provider": {
                "test-model": {
                    "input_cost_per_token": 1e-06,  # $0.000001 per token
                    "output_cost_per_token": 2e-06   # $0.000002 per token
                }
            }
        }

        result = _convert_json_pricing_to_model_pricing(json_data)

        # $0.000001 per token * 1,000,000 = $1.00 per 1M tokens
        assert result["test-model"]["input"] == 1.00
        # $0.000002 per token * 1,000,000 = $2.00 per 1M tokens
        assert result["test-model"]["output"] == 2.00
