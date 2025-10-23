"""
Comprehensive tests for pricing_scraper service

Tests web scraping, pricing validation, and update cycle management.
"""
import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from bs4 import BeautifulSoup
import httpx

# Import from src
import sys
from pathlib import Path as PathType
sys.path.insert(0, str(PathType(__file__).parent.parent / "src"))

from services.pricing_scraper import PricingScraper, get_pricing_scraper


@pytest.fixture
def scraper():
    """Create PricingScraper instance"""
    return PricingScraper()


@pytest.fixture
def mock_html():
    """Mock HTML response"""
    return """
    <html>
        <body>
            <h1>Pricing</h1>
            <p>Model pricing information</p>
        </body>
    </html>
    """


@pytest.fixture
def mock_scrape_results():
    """Mock scrape results"""
    return {
        "timestamp": "2025-01-01T00:00:00+00:00",
        "providers": {
            "openai": {
                "status": "success",
                "models_found": 2,
                "data": [
                    {"model_name": "gpt-4o", "input_price": 5.00, "output_price": 15.00},
                    {"model_name": "gpt-4-turbo", "input_price": 10.00, "output_price": 30.00}
                ]
            }
        },
        "summary": {
            "total_scraped": 2,
            "successful": 1,
            "failed": 0,
            "updates": []
        }
    }


class TestPricingScraperInit:
    """Test PricingScraper initialization"""

    def test_init_creates_updater(self, scraper):
        """Test that initialization creates pricing updater instance"""
        assert scraper.updater is not None

    def test_init_sets_timeout(self, scraper):
        """Test that timeout is set"""
        assert scraper.timeout == 30.0

    def test_init_has_pricing_urls(self, scraper):
        """Test that pricing URLs are configured"""
        assert "openai" in scraper.pricing_urls
        assert "anthropic" in scraper.pricing_urls
        assert "gemini" in scraper.pricing_urls
        assert "fireworks" in scraper.pricing_urls

    def test_pricing_urls_are_valid(self, scraper):
        """Test that all pricing URLs start with https"""
        for provider, url in scraper.pricing_urls.items():
            assert url.startswith("https://"), f"{provider} URL should use HTTPS"


class TestScrapeAllProviders:
    """Test scrape_all_providers method"""

    @pytest.mark.asyncio
    async def test_scrape_all_providers_success(self, scraper):
        """Test scraping all providers successfully"""
        with patch.object(scraper, 'scrape_provider', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = [
                {"model_name": "test-model", "input_price": 1.00, "output_price": 2.00}
            ]

            results = await scraper.scrape_all_providers()

            assert results["summary"]["total_scraped"] == 4  # 4 providers × 1 model each
            assert results["summary"]["successful"] == 4
            assert results["summary"]["failed"] == 0
            assert "timestamp" in results

    @pytest.mark.asyncio
    async def test_scrape_all_providers_with_failures(self, scraper):
        """Test handling provider scraping failures"""
        async def mock_scrape_side_effect(provider):
            if provider == "openai":
                raise Exception("HTTP 403 Forbidden")
            return []

        with patch.object(scraper, 'scrape_provider', new_callable=AsyncMock, side_effect=mock_scrape_side_effect):
            results = await scraper.scrape_all_providers()

            assert results["summary"]["failed"] == 1
            assert results["summary"]["successful"] == 3
            assert results["providers"]["openai"]["status"] == "error"
            assert "403" in results["providers"]["openai"]["error"]

    @pytest.mark.asyncio
    async def test_scrape_all_providers_structure(self, scraper):
        """Test result structure"""
        with patch.object(scraper, 'scrape_provider', new_callable=AsyncMock, return_value=[]):
            results = await scraper.scrape_all_providers()

            assert "timestamp" in results
            assert "providers" in results
            assert "summary" in results
            assert "total_scraped" in results["summary"]
            assert "successful" in results["summary"]
            assert "failed" in results["summary"]


class TestScrapeProvider:
    """Test scrape_provider method"""

    @pytest.mark.asyncio
    async def test_scrape_provider_unknown(self, scraper):
        """Test scraping unknown provider raises error"""
        with pytest.raises(ValueError, match="Unknown provider"):
            await scraper.scrape_provider("unknown_provider")

    @pytest.mark.asyncio
    async def test_scrape_provider_openai(self, scraper, mock_html):
        """Test scraping OpenAI provider"""
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await scraper.scrape_provider("openai")

            assert isinstance(result, list)
            # OpenAI parser returns empty list (not implemented)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_scrape_provider_http_error(self, scraper):
        """Test handling HTTP errors"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock(side_effect=httpx.HTTPStatusError(
            "403 Forbidden",
            request=Mock(),
            response=Mock()
        ))

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            with pytest.raises(httpx.HTTPStatusError):
                await scraper.scrape_provider("openai")

    @pytest.mark.asyncio
    async def test_scrape_provider_timeout(self, scraper):
        """Test handling timeout errors"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )

            with pytest.raises(httpx.TimeoutException):
                await scraper.scrape_provider("anthropic")

    @pytest.mark.asyncio
    async def test_scrape_provider_all_providers(self, scraper, mock_html):
        """Test scraping each provider type"""
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            for provider in ["openai", "anthropic", "gemini", "fireworks"]:
                result = await scraper.scrape_provider(provider)
                assert isinstance(result, list)


class TestParserMethods:
    """Test HTML parser methods"""

    def test_parse_openai_pricing(self, scraper):
        """Test OpenAI pricing parser"""
        soup = BeautifulSoup("<html><body>Test</body></html>", 'html.parser')
        result = scraper._parse_openai_pricing(soup)

        assert isinstance(result, list)
        # Not implemented yet, returns empty list
        assert len(result) == 0

    def test_parse_anthropic_pricing(self, scraper):
        """Test Anthropic pricing parser"""
        soup = BeautifulSoup("<html><body>Test</body></html>", 'html.parser')
        result = scraper._parse_anthropic_pricing(soup)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_gemini_pricing(self, scraper):
        """Test Gemini pricing parser"""
        soup = BeautifulSoup("<html><body>Test</body></html>", 'html.parser')
        result = scraper._parse_gemini_pricing(soup)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_fireworks_pricing(self, scraper):
        """Test Fireworks pricing parser"""
        soup = BeautifulSoup("<html><body>Test</body></html>", 'html.parser')
        result = scraper._parse_fireworks_pricing(soup)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_parser_methods_log_warnings(self, scraper, caplog):
        """Test that parser methods log warnings when not implemented"""
        soup = BeautifulSoup("<html><body>Test</body></html>", 'html.parser')

        scraper._parse_openai_pricing(soup)
        assert "not fully implemented" in caplog.text

        scraper._parse_anthropic_pricing(soup)
        assert "not fully implemented" in caplog.text


class TestUpdatePricingFromScrape:
    """Test update_pricing_from_scrape method"""

    @pytest.mark.asyncio
    async def test_update_pricing_from_scrape_success(self, scraper, mock_scrape_results):
        """Test updating pricing from scrape results"""
        with patch.object(scraper.updater, 'update_model_pricing') as mock_update:
            mock_update.return_value = {"status": "updated", "model": "gpt-4o"}

            result = await scraper.update_pricing_from_scrape(mock_scrape_results)

            assert result["total_updates"] == 2
            assert len(result["updated"]) == 2
            assert len(result["unchanged"]) == 0
            assert mock_update.call_count == 2

    @pytest.mark.asyncio
    async def test_update_pricing_from_scrape_unchanged(self, scraper, mock_scrape_results):
        """Test updating with unchanged pricing"""
        with patch.object(scraper.updater, 'update_model_pricing') as mock_update:
            mock_update.return_value = {"status": "unchanged", "model": "gpt-4o"}

            result = await scraper.update_pricing_from_scrape(mock_scrape_results)

            assert len(result["updated"]) == 0
            assert len(result["unchanged"]) == 2

    @pytest.mark.asyncio
    async def test_update_pricing_from_scrape_with_failures(self, scraper, mock_scrape_results):
        """Test handling update failures"""
        with patch.object(scraper.updater, 'update_model_pricing') as mock_update:
            mock_update.side_effect = [
                {"status": "updated", "model": "gpt-4o"},
                Exception("Database error")
            ]

            result = await scraper.update_pricing_from_scrape(mock_scrape_results)

            # Should continue despite error
            assert result["total_updates"] == 1

    @pytest.mark.asyncio
    async def test_update_pricing_from_scrape_skips_failed_providers(self, scraper):
        """Test that failed provider scrapes are skipped"""
        failed_results = {
            "timestamp": "2025-01-01T00:00:00+00:00",
            "providers": {
                "openai": {
                    "status": "error",
                    "error": "HTTP 403"
                }
            },
            "summary": {}
        }

        with patch.object(scraper.updater, 'update_model_pricing') as mock_update:
            result = await scraper.update_pricing_from_scrape(failed_results)

            assert result["total_updates"] == 0
            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_pricing_adds_notes(self, scraper, mock_scrape_results):
        """Test that updates include source notes"""
        with patch.object(scraper.updater, 'update_model_pricing') as mock_update:
            mock_update.return_value = {"status": "updated"}

            await scraper.update_pricing_from_scrape(mock_scrape_results)

            # Check that notes parameter was passed
            call_args = mock_update.call_args_list[0]
            assert "notes" in call_args.kwargs
            assert "Scraped from" in call_args.kwargs["notes"]


class TestValidateCurrentPricing:
    """Test validate_current_pricing method"""

    @pytest.mark.asyncio
    @patch('services.pricing_scraper.MODEL_PRICING', {
        "gpt-4o": {"input": 5.00, "output": 15.00},
        "default": {"input": 0.50, "output": 1.50}
    })
    async def test_validate_current_pricing_no_warnings(self, scraper):
        """Test validation with normal pricing"""
        result = await scraper.validate_current_pricing()

        assert result["models_validated"] == 1  # Excludes "default"
        assert len(result["warnings"]) == 0
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    @patch('services.pricing_scraper.MODEL_PRICING', {
        "cheap-model": {"input": 0.005, "output": 0.01},
        "default": {}
    })
    async def test_validate_current_pricing_low_input(self, scraper):
        """Test validation detects suspiciously low input price"""
        result = await scraper.validate_current_pricing()

        assert len(result["warnings"]) == 1
        assert result["warnings"][0]["issue"] == "suspiciously_low_input_price"
        assert result["warnings"][0]["model"] == "cheap-model"

    @pytest.mark.asyncio
    @patch('services.pricing_scraper.MODEL_PRICING', {
        "expensive-model": {"input": 50.00, "output": 1500.00},
        "default": {}
    })
    async def test_validate_current_pricing_high_output(self, scraper):
        """Test validation detects suspiciously high output price"""
        result = await scraper.validate_current_pricing()

        assert len(result["warnings"]) >= 1
        warning_issues = [w["issue"] for w in result["warnings"]]
        assert "suspiciously_high_output_price" in warning_issues

    @pytest.mark.asyncio
    @patch('services.pricing_scraper.MODEL_PRICING', {
        "weird-model": {"input": 10.00, "output": 2.00},
        "default": {}
    })
    async def test_validate_current_pricing_output_much_lower(self, scraper):
        """Test validation detects output price much lower than input"""
        result = await scraper.validate_current_pricing()

        assert len(result["warnings"]) >= 1
        warning_issues = [w["issue"] for w in result["warnings"]]
        assert "output_price_much_lower_than_input" in warning_issues

    @pytest.mark.asyncio
    @patch('services.pricing_scraper.MODEL_PRICING', {
        "model1": {"input": 0.005, "output": 1500.00},
        "model2": {"input": 10.00, "output": 2.00},
        "default": {}
    })
    async def test_validate_current_pricing_multiple_warnings(self, scraper):
        """Test validation with multiple warnings"""
        result = await scraper.validate_current_pricing()

        assert len(result["warnings"]) >= 2
        assert result["models_validated"] == 2


class TestRunPricingUpdateCycle:
    """Test run_pricing_update_cycle method"""

    @pytest.mark.asyncio
    async def test_run_pricing_update_cycle_success(self, scraper, mock_scrape_results):
        """Test successful pricing update cycle"""
        with patch.object(scraper, 'scrape_all_providers', new_callable=AsyncMock) as mock_scrape, \
             patch.object(scraper, 'validate_current_pricing', new_callable=AsyncMock) as mock_validate, \
             patch.object(scraper, 'update_pricing_from_scrape', new_callable=AsyncMock) as mock_update:

            mock_scrape.return_value = mock_scrape_results
            mock_validate.return_value = {"models_validated": 10, "warnings": [], "errors": []}
            mock_update.return_value = {"total_updates": 2}

            results = await scraper.run_pricing_update_cycle()

            assert results["status"] == "completed"
            assert results["scrape_results"] is not None
            assert results["validation"] is not None
            assert results["updates"] is not None
            assert "duration_seconds" in results

    @pytest.mark.asyncio
    async def test_run_pricing_update_cycle_no_data(self, scraper):
        """Test cycle when no data is scraped"""
        with patch.object(scraper, 'scrape_all_providers', new_callable=AsyncMock) as mock_scrape, \
             patch.object(scraper, 'validate_current_pricing', new_callable=AsyncMock) as mock_validate, \
             patch.object(scraper, 'update_pricing_from_scrape', new_callable=AsyncMock) as mock_update:

            mock_scrape.return_value = {
                "summary": {"total_scraped": 0},
                "providers": {}
            }
            mock_validate.return_value = {"models_validated": 10}

            results = await scraper.run_pricing_update_cycle()

            assert results["status"] == "completed"
            assert results["updates"]["skipped"] is True
            assert results["updates"]["reason"] == "no_data_scraped"
            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_pricing_update_cycle_failure(self, scraper):
        """Test cycle handling failures"""
        with patch.object(scraper, 'scrape_all_providers', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = Exception("Network error")

            results = await scraper.run_pricing_update_cycle()

            assert results["status"] == "failed"
            assert "error" in results
            assert "Network error" in results["error"]

    @pytest.mark.asyncio
    async def test_run_pricing_update_cycle_calculates_duration(self, scraper):
        """Test that cycle duration is calculated"""
        with patch.object(scraper, 'scrape_all_providers', new_callable=AsyncMock) as mock_scrape, \
             patch.object(scraper, 'validate_current_pricing', new_callable=AsyncMock) as mock_validate:

            mock_scrape.return_value = {"summary": {"total_scraped": 0}, "providers": {}}
            mock_validate.return_value = {"models_validated": 0}

            results = await scraper.run_pricing_update_cycle()

            assert "duration_seconds" in results
            assert isinstance(results["duration_seconds"], float)
            assert results["duration_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_run_pricing_update_cycle_has_timestamps(self, scraper):
        """Test that cycle includes start and end timestamps"""
        with patch.object(scraper, 'scrape_all_providers', new_callable=AsyncMock) as mock_scrape, \
             patch.object(scraper, 'validate_current_pricing', new_callable=AsyncMock) as mock_validate:

            mock_scrape.return_value = {"summary": {"total_scraped": 0}, "providers": {}}
            mock_validate.return_value = {"models_validated": 0}

            results = await scraper.run_pricing_update_cycle()

            assert "cycle_start" in results
            assert "cycle_end" in results
            # Verify ISO format
            datetime.fromisoformat(results["cycle_start"])
            datetime.fromisoformat(results["cycle_end"])


class TestGetPricingScraperSingleton:
    """Test get_pricing_scraper singleton function"""

    def test_get_singleton_instance(self):
        """Test that singleton returns same instance"""
        instance1 = get_pricing_scraper()
        instance2 = get_pricing_scraper()

        assert instance1 is instance2

    def test_singleton_instance_is_pricing_scraper(self):
        """Test that singleton returns PricingScraper instance"""
        instance = get_pricing_scraper()

        assert isinstance(instance, PricingScraper)


class TestIntegration:
    """Integration tests for complete workflows"""

    @pytest.mark.asyncio
    async def test_complete_scrape_and_update_workflow(self, scraper, mock_scrape_results):
        """Test complete workflow from scrape to update"""
        with patch.object(scraper, 'scrape_all_providers', new_callable=AsyncMock) as mock_scrape, \
             patch.object(scraper.updater, 'update_model_pricing') as mock_update:

            mock_scrape.return_value = mock_scrape_results
            mock_update.return_value = {"status": "updated", "model": "gpt-4o"}

            # Run complete cycle
            results = await scraper.run_pricing_update_cycle()

            # Verify all steps executed
            assert results["status"] == "completed"
            assert results["scrape_results"]["summary"]["total_scraped"] == 2
            assert results["updates"]["total_updates"] == 2

    @pytest.mark.asyncio
    async def test_error_recovery_in_cycle(self, scraper):
        """Test that cycle completes even with partial failures"""
        with patch.object(scraper, 'scrape_all_providers', new_callable=AsyncMock) as mock_scrape, \
             patch.object(scraper, 'validate_current_pricing', new_callable=AsyncMock) as mock_validate, \
             patch.object(scraper, 'update_pricing_from_scrape', new_callable=AsyncMock) as mock_update:

            # Scraping succeeds
            mock_scrape.return_value = {"summary": {"total_scraped": 1}, "providers": {}}
            # Validation fails
            mock_validate.side_effect = Exception("Validation error")

            results = await scraper.run_pricing_update_cycle()

            # Should still mark as failed but include duration
            assert results["status"] == "failed"
            assert "duration_seconds" in results
            assert results["cycle_end"] is not None
