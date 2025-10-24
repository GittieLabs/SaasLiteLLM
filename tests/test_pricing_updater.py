"""
Comprehensive tests for pricing_updater service

Tests pricing update management, versioning, and history tracking.
"""
import pytest
import json
import tempfile
from datetime import datetime, UTC, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import from src
import sys
from pathlib import Path as PathType
sys.path.insert(0, str(PathType(__file__).parent.parent / "src"))

from services.pricing_updater import PricingUpdater, get_pricing_updater


@pytest.fixture
def temp_pricing_history():
    """Create a temporary pricing history file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
        # Initialize with empty history
        json.dump({
            "version": "1.0",
            "last_updated": datetime.now(UTC).isoformat(),
            "models": {}
        }, f)

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def updater(temp_pricing_history):
    """Create PricingUpdater instance with temporary file"""
    return PricingUpdater(pricing_history_path=temp_pricing_history)


@pytest.fixture
def mock_model_pricing():
    """Mock MODEL_PRICING data"""
    return {
        "gpt-4o": {"input": 5.00, "output": 15.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "default": {"input": 0.50, "output": 1.50}
    }


class TestPricingUpdaterInit:
    """Test PricingUpdater initialization"""

    def test_init_with_custom_path(self, temp_pricing_history):
        """Test initialization with custom pricing history path"""
        updater = PricingUpdater(pricing_history_path=temp_pricing_history)

        assert updater.pricing_history_path == Path(temp_pricing_history)
        assert updater.pricing_history is not None
        assert "version" in updater.pricing_history
        assert "models" in updater.pricing_history

    def test_init_creates_directory(self):
        """Test that initialization creates parent directory if needed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "subdir" / "pricing.json"
            updater = PricingUpdater(pricing_history_path=str(test_path))

            assert test_path.parent.exists()

    def test_init_loads_existing_history(self):
        """Test that initialization loads existing history file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            existing_data = {
                "version": "1.0",
                "last_updated": "2025-01-01T00:00:00+00:00",
                "models": {
                    "gpt-4o": {
                        "provider": "openai",
                        "updates": [{
                            "timestamp": "2025-01-01T00:00:00+00:00",
                            "input_price": 5.00,
                            "output_price": 15.00
                        }]
                    }
                }
            }
            json.dump(existing_data, f)
            temp_path = f.name

        try:
            updater = PricingUpdater(pricing_history_path=temp_path)
            assert "gpt-4o" in updater.pricing_history["models"]
            assert len(updater.pricing_history["models"]["gpt-4o"]["updates"]) == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_init_handles_corrupted_file(self):
        """Test that initialization handles corrupted JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content{{{")
            temp_path = f.name

        try:
            updater = PricingUpdater(pricing_history_path=temp_path)
            # Should create new empty history
            assert updater.pricing_history["models"] == {}
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestUpdateModelPricing:
    """Test update_model_pricing method"""

    @patch('services.pricing_updater.MODEL_PRICING', {"gpt-4o": {"input": 5.00, "output": 15.00}})
    def test_update_model_pricing_basic(self, updater):
        """Test basic model pricing update"""
        result = updater.update_model_pricing(
            model_name="gpt-4o",
            input_price=6.00,
            output_price=18.00,
            source="manual"
        )

        assert result["status"] == "updated"
        assert result["model"] == "gpt-4o"
        assert result["new_pricing"]["input"] == 6.00
        assert result["new_pricing"]["output"] == 18.00
        assert "timestamp" in result

    @patch('services.pricing_updater.MODEL_PRICING', {})
    def test_update_new_model(self, updater):
        """Test updating pricing for a new model"""
        result = updater.update_model_pricing(
            model_name="new-model",
            input_price=2.00,
            output_price=6.00
        )

        assert result["status"] == "updated"
        assert result["change_info"]["type"] == "new_model"

    def test_update_normalizes_model_name(self, updater):
        """Test that model name is normalized (lowercase, trimmed)"""
        with patch('services.pricing_updater.MODEL_PRICING', {}):
            updater.update_model_pricing(
                model_name="  GPT-4O  ",
                input_price=5.00,
                output_price=15.00
            )

            assert "gpt-4o" in updater.pricing_history["models"]

    def test_update_rejects_negative_pricing(self, updater):
        """Test that negative pricing is rejected"""
        with pytest.raises(ValueError, match="Pricing must be non-negative"):
            updater.update_model_pricing(
                model_name="gpt-4o",
                input_price=-1.00,
                output_price=15.00
            )

    def test_update_warns_on_high_pricing(self, updater, caplog):
        """Test warning for unusually high pricing"""
        with patch('services.pricing_updater.MODEL_PRICING', {}):
            updater.update_model_pricing(
                model_name="expensive-model",
                input_price=1500.00,
                output_price=2000.00
            )

            assert "Unusually high pricing" in caplog.text

    @patch('services.pricing_updater.MODEL_PRICING', {"gpt-4o": {"input": 5.00, "output": 15.00}})
    def test_update_unchanged_pricing(self, updater):
        """Test updating with unchanged pricing"""
        result = updater.update_model_pricing(
            model_name="gpt-4o",
            input_price=5.00,
            output_price=15.00
        )

        assert result["status"] == "unchanged"
        assert result["message"] == "Pricing is already up to date"

    @patch('services.pricing_updater.MODEL_PRICING', {"gpt-4o": {"input": 5.00, "output": 15.00}})
    def test_update_with_notes(self, updater):
        """Test update with notes field"""
        result = updater.update_model_pricing(
            model_name="gpt-4o",
            input_price=6.00,
            output_price=18.00,
            notes="Price increase from provider announcement"
        )

        assert result["status"] == "updated"
        # Verify notes saved in history
        history = updater.pricing_history["models"]["gpt-4o"]["updates"][-1]
        assert history["notes"] == "Price increase from provider announcement"

    @patch('services.pricing_updater.MODEL_PRICING', {"gpt-4o": {"input": 5.00, "output": 15.00}})
    @patch('services.pricing_updater.get_provider_from_model', return_value="openai")
    def test_update_records_provider(self, mock_provider, updater):
        """Test that provider is recorded in history"""
        updater.update_model_pricing(
            model_name="gpt-4o",
            input_price=6.00,
            output_price=18.00
        )

        assert updater.pricing_history["models"]["gpt-4o"]["provider"] == "openai"


class TestCalculatePriceChange:
    """Test _calculate_price_change method"""

    def test_calculate_price_increase(self, updater):
        """Test calculating price increase percentage"""
        current = {"input": 5.00, "output": 15.00}
        change = updater._calculate_price_change(current, 6.00, 18.00)

        assert change["input_change_percent"] == 20.0
        assert change["output_change_percent"] == 20.0
        assert change["input_direction"] == "increase"
        assert change["output_direction"] == "increase"

    def test_calculate_price_decrease(self, updater):
        """Test calculating price decrease percentage"""
        current = {"input": 5.00, "output": 15.00}
        change = updater._calculate_price_change(current, 4.00, 12.00)

        assert change["input_change_percent"] == -20.0
        assert change["output_change_percent"] == -20.0
        assert change["input_direction"] == "decrease"
        assert change["output_direction"] == "decrease"

    def test_calculate_new_model(self, updater):
        """Test calculating change for new model"""
        change = updater._calculate_price_change(None, 5.00, 15.00)

        assert change["type"] == "new_model"
        assert "New model added" in change["message"]

    def test_calculate_mixed_changes(self, updater):
        """Test calculating mixed price changes"""
        current = {"input": 5.00, "output": 15.00}
        change = updater._calculate_price_change(current, 6.00, 12.00)

        assert change["input_direction"] == "increase"
        assert change["output_direction"] == "decrease"


class TestBulkUpdatePricing:
    """Test bulk_update_pricing method"""

    @patch('services.pricing_updater.MODEL_PRICING', {"gpt-4o": {"input": 5.00, "output": 15.00}})
    def test_bulk_update_success(self, updater):
        """Test successful bulk update"""
        updates = [
            {"model_name": "gpt-4o", "input_price": 6.00, "output_price": 18.00},
            {"model_name": "new-model", "input_price": 2.00, "output_price": 6.00}
        ]

        result = updater.bulk_update_pricing(updates)

        assert len(result["updated"]) == 2
        assert len(result["unchanged"]) == 0
        assert len(result["failed"]) == 0

    @patch('services.pricing_updater.MODEL_PRICING', {"gpt-4o": {"input": 5.00, "output": 15.00}})
    def test_bulk_update_with_unchanged(self, updater):
        """Test bulk update with unchanged models"""
        updates = [
            {"model_name": "gpt-4o", "input_price": 5.00, "output_price": 15.00},
        ]

        result = updater.bulk_update_pricing(updates)

        assert len(result["unchanged"]) == 1
        assert len(result["updated"]) == 0

    def test_bulk_update_with_failures(self, updater):
        """Test bulk update with failures"""
        updates = [
            {"model_name": "model1", "input_price": -1.00, "output_price": 15.00},  # Invalid
            {"model_name": "model2", "input_price": 2.00, "output_price": 6.00}
        ]

        with patch('services.pricing_updater.MODEL_PRICING', {}):
            result = updater.bulk_update_pricing(updates)

        assert len(result["failed"]) == 1
        assert len(result["updated"]) == 1

    @patch('services.pricing_updater.MODEL_PRICING', {})
    def test_bulk_update_with_notes(self, updater):
        """Test bulk update with notes"""
        updates = [
            {
                "model_name": "gpt-4o",
                "input_price": 6.00,
                "output_price": 18.00,
                "notes": "Q1 2025 price update"
            }
        ]

        result = updater.bulk_update_pricing(updates)

        assert len(result["updated"]) == 1
        history = updater.pricing_history["models"]["gpt-4o"]["updates"][-1]
        assert history["notes"] == "Q1 2025 price update"


class TestGetPricingHistory:
    """Test get_pricing_history method"""

    def test_get_all_history(self, updater):
        """Test getting all pricing history"""
        # Setup history
        updater.pricing_history["models"] = {
            "gpt-4o": {
                "provider": "openai",
                "updates": [{
                    "timestamp": "2025-01-01T00:00:00+00:00",
                    "input_price": 5.00,
                    "output_price": 15.00
                }]
            }
        }

        history = updater.get_pricing_history()

        assert len(history) == 1
        assert history[0]["model"] == "gpt-4o"
        assert history[0]["provider"] == "openai"

    def test_get_history_by_model(self, updater):
        """Test filtering history by model name"""
        updater.pricing_history["models"] = {
            "gpt-4o": {
                "provider": "openai",
                "updates": [{"timestamp": "2025-01-01T00:00:00+00:00", "input_price": 5.00, "output_price": 15.00}]
            },
            "claude-3-5-sonnet-20241022": {
                "provider": "anthropic",
                "updates": [{"timestamp": "2025-01-02T00:00:00+00:00", "input_price": 3.00, "output_price": 15.00}]
            }
        }

        history = updater.get_pricing_history(model_name="gpt-4o")

        assert len(history) == 1
        assert history[0]["model"] == "gpt-4o"

    def test_get_history_by_provider(self, updater):
        """Test filtering history by provider"""
        updater.pricing_history["models"] = {
            "gpt-4o": {
                "provider": "openai",
                "updates": [{"timestamp": "2025-01-01T00:00:00+00:00", "input_price": 5.00, "output_price": 15.00}]
            },
            "claude-3-5-sonnet-20241022": {
                "provider": "anthropic",
                "updates": [{"timestamp": "2025-01-02T00:00:00+00:00", "input_price": 3.00, "output_price": 15.00}]
            }
        }

        history = updater.get_pricing_history(provider="openai")

        assert len(history) == 1
        assert history[0]["provider"] == "openai"

    def test_get_history_with_limit(self, updater):
        """Test limiting number of results"""
        updater.pricing_history["models"] = {
            "gpt-4o": {
                "provider": "openai",
                "updates": [
                    {"timestamp": "2025-01-01T00:00:00+00:00", "input_price": 5.00, "output_price": 15.00},
                    {"timestamp": "2025-01-02T00:00:00+00:00", "input_price": 6.00, "output_price": 18.00},
                    {"timestamp": "2025-01-03T00:00:00+00:00", "input_price": 7.00, "output_price": 21.00}
                ]
            }
        }

        history = updater.get_pricing_history(limit=2)

        assert len(history) == 2
        # Should get most recent updates
        assert history[0]["input_price"] == 7.00

    def test_get_history_sorted_by_timestamp(self, updater):
        """Test that history is sorted by timestamp (newest first)"""
        updater.pricing_history["models"] = {
            "gpt-4o": {
                "provider": "openai",
                "updates": [
                    {"timestamp": "2025-01-01T00:00:00+00:00", "input_price": 5.00, "output_price": 15.00},
                    {"timestamp": "2025-01-03T00:00:00+00:00", "input_price": 7.00, "output_price": 21.00},
                    {"timestamp": "2025-01-02T00:00:00+00:00", "input_price": 6.00, "output_price": 18.00}
                ]
            }
        }

        history = updater.get_pricing_history()

        assert history[0]["input_price"] == 7.00
        assert history[1]["input_price"] == 6.00
        assert history[2]["input_price"] == 5.00


class TestGetModelsNeedingUpdate:
    """Test get_models_needing_update method"""

    @patch('services.pricing_updater.MODEL_PRICING', {"gpt-4o": {"input": 5.00, "output": 15.00}, "default": {}})
    def test_get_never_validated_models(self, updater):
        """Test finding models that have never been validated"""
        result = updater.get_models_needing_update()

        assert len(result) == 1
        assert result[0]["model"] == "gpt-4o"
        assert result[0]["status"] == "never_validated"
        assert result[0]["last_updated"] == "never"

    @patch('services.pricing_updater.MODEL_PRICING', {"gpt-4o": {"input": 5.00, "output": 15.00}, "default": {}})
    def test_get_stale_models(self, updater):
        """Test finding models with stale pricing"""
        # Add old update
        old_date = (datetime.now(UTC) - timedelta(days=45)).isoformat()
        updater.pricing_history["models"]["gpt-4o"] = {
            "provider": "openai",
            "updates": [{
                "timestamp": old_date,
                "input_price": 5.00,
                "output_price": 15.00
            }]
        }

        result = updater.get_models_needing_update(days_threshold=30)

        assert len(result) == 1
        assert result[0]["status"] == "stale"
        assert result[0]["days_since_update"] > 30

    @patch('services.pricing_updater.MODEL_PRICING', {"gpt-4o": {"input": 5.00, "output": 15.00}, "default": {}})
    def test_get_fresh_models_excluded(self, updater):
        """Test that recently updated models are excluded"""
        # Add recent update
        recent_date = (datetime.now(UTC) - timedelta(days=5)).isoformat()
        updater.pricing_history["models"]["gpt-4o"] = {
            "provider": "openai",
            "updates": [{
                "timestamp": recent_date,
                "input_price": 5.00,
                "output_price": 15.00
            }]
        }

        result = updater.get_models_needing_update(days_threshold=30)

        assert len(result) == 0


class TestGeneratePricingChangeReport:
    """Test generate_pricing_change_report method"""

    def test_generate_report_all_changes(self, updater):
        """Test generating report for all changes"""
        updater.pricing_history["models"] = {
            "gpt-4o": {
                "provider": "openai",
                "updates": [
                    {
                        "timestamp": "2025-01-01T00:00:00+00:00",
                        "input_price": 5.00,
                        "output_price": 15.00,
                        "previous_input_price": None,
                        "previous_output_price": None
                    },
                    {
                        "timestamp": "2025-01-02T00:00:00+00:00",
                        "input_price": 6.00,
                        "output_price": 18.00,
                        "previous_input_price": 5.00,
                        "previous_output_price": 15.00
                    }
                ]
            }
        }

        report = updater.generate_pricing_change_report()

        assert report["summary"]["total_changes"] == 2
        assert report["summary"]["new_models"] == 1
        assert report["summary"]["increases"] == 1

    def test_generate_report_with_date_range(self, updater):
        """Test generating report with date range filter"""
        updater.pricing_history["models"] = {
            "gpt-4o": {
                "provider": "openai",
                "updates": [
                    {
                        "timestamp": "2025-01-01T00:00:00+00:00",
                        "input_price": 5.00,
                        "output_price": 15.00,
                        "previous_input_price": None,
                        "previous_output_price": None
                    },
                    {
                        "timestamp": "2025-02-01T00:00:00+00:00",
                        "input_price": 6.00,
                        "output_price": 18.00,
                        "previous_input_price": 5.00,
                        "previous_output_price": 15.00
                    }
                ]
            }
        }

        start = datetime(2025, 1, 15, tzinfo=UTC)
        report = updater.generate_pricing_change_report(start_date=start)

        assert report["summary"]["total_changes"] == 1

    def test_generate_report_categorizes_changes(self, updater):
        """Test that report categorizes price increases and decreases"""
        updater.pricing_history["models"] = {
            "model1": {
                "provider": "provider1",
                "updates": [{
                    "timestamp": "2025-01-01T00:00:00+00:00",
                    "input_price": 6.00,
                    "output_price": 18.00,
                    "previous_input_price": 5.00,
                    "previous_output_price": 15.00
                }]
            },
            "model2": {
                "provider": "provider2",
                "updates": [{
                    "timestamp": "2025-01-02T00:00:00+00:00",
                    "input_price": 4.00,
                    "output_price": 12.00,
                    "previous_input_price": 5.00,
                    "previous_output_price": 15.00
                }]
            }
        }

        report = updater.generate_pricing_change_report()

        assert len(report["price_increases"]) == 1
        assert len(report["price_decreases"]) == 1


class TestExportCurrentPricing:
    """Test export_current_pricing method"""

    @patch('services.pricing_updater.MODEL_PRICING', {
        "gpt-4o": {"input": 5.00, "output": 15.00},
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "default": {"input": 0.50, "output": 1.50}
    })
    @patch('services.pricing_updater.get_provider_from_model')
    def test_export_current_pricing(self, mock_provider, updater):
        """Test exporting current pricing data"""
        mock_provider.side_effect = lambda m: "openai" if "gpt" in m else "anthropic"

        export = updater.export_current_pricing()

        assert "gpt-4o" in export
        assert "claude-3-5-sonnet-20241022" in export
        assert "default" not in export  # Should exclude default

        assert export["gpt-4o"]["input_per_1m"] == 5.00
        assert export["gpt-4o"]["output_per_1m"] == 15.00

    @patch('services.pricing_updater.MODEL_PRICING', {"gpt-4o": {"input": 5.00, "output": 15.00}})
    @patch('services.pricing_updater.get_provider_from_model', return_value="openai")
    def test_export_includes_verification_time(self, mock_provider, updater):
        """Test that export includes last verification timestamp"""
        # Add update to history
        updater.pricing_history["models"]["gpt-4o"] = {
            "provider": "openai",
            "updates": [{
                "timestamp": "2025-01-01T00:00:00+00:00",
                "input_price": 5.00,
                "output_price": 15.00
            }]
        }

        export = updater.export_current_pricing()

        assert export["gpt-4o"]["last_verified"] == "2025-01-01T00:00:00+00:00"


class TestGetPricingUpdaterSingleton:
    """Test get_pricing_updater singleton function"""

    def test_get_singleton_instance(self):
        """Test that singleton returns same instance"""
        instance1 = get_pricing_updater()
        instance2 = get_pricing_updater()

        assert instance1 is instance2

    def test_singleton_instance_is_pricing_updater(self):
        """Test that singleton returns PricingUpdater instance"""
        instance = get_pricing_updater()

        assert isinstance(instance, PricingUpdater)


class TestFilePersistence:
    """Test file I/O and persistence"""

    def test_save_pricing_history(self, updater):
        """Test saving pricing history to file"""
        with patch('services.pricing_updater.MODEL_PRICING', {}):
            updater.update_model_pricing("test-model", 1.00, 2.00)

        # Reload from file
        with open(updater.pricing_history_path, 'r') as f:
            saved_data = json.load(f)

        assert "test-model" in saved_data["models"]

    def test_save_updates_last_updated_timestamp(self, updater):
        """Test that save updates last_updated field"""
        old_timestamp = updater.pricing_history["last_updated"]

        with patch('services.pricing_updater.MODEL_PRICING', {}):
            updater.update_model_pricing("test-model", 1.00, 2.00)

        # Reload
        with open(updater.pricing_history_path, 'r') as f:
            saved_data = json.load(f)

        assert saved_data["last_updated"] != old_timestamp

    def test_save_error_handling(self, updater):
        """Test error handling when save fails"""
        # Mock the open function to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                updater._save_pricing_history()
