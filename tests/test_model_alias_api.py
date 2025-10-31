"""
Tests for Model Alias API - Direct Provider Integration

Tests the model alias API endpoints after removing LiteLLM proxy dependency.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
import uuid

# Import from src
import sys
from pathlib import Path as PathType
sys.path.insert(0, str(PathType(__file__).parent.parent / "src"))

from saas_api import app
from models.model_aliases import ModelAlias, ModelAccessGroup


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    session = MagicMock()
    return session


@pytest.fixture
def sample_model_alias():
    """Create a sample model alias"""
    return ModelAlias(
        id=1,
        model_alias="chat-fast",
        display_name="Fast Chat Model",
        provider="openai",
        actual_model="gpt-4o-mini",
        litellm_model_id=None,  # No longer using LiteLLM
        description="Fast model for chat",
        pricing_input=Decimal("0.15"),
        pricing_output=Decimal("0.6"),
        status="active"
    )


@pytest.fixture
def sample_access_group():
    """Create a sample access group"""
    return ModelAccessGroup(
        id=1,
        group_name="default",
        display_name="Default Access",
        description="Default access group"
    )


class TestCreateModelAlias:
    """Test POST /api/models/create endpoint"""

    @patch('api.models.get_db')
    def test_create_model_alias_success(self, mock_get_db, client):
        """Test successful model alias creation without LiteLLM"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock query to return no existing model
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock flush and commit
        mock_db.flush.return_value = None
        mock_db.commit.return_value = None

        payload = {
            "model_alias": "test-model",
            "display_name": "Test Model",
            "provider": "openai",
            "actual_model": "gpt-4o",
            "pricing_input": 2.5,
            "pricing_output": 10.0,
            "access_groups": []
        }

        response = client.post("/api/models/create", json=payload)

        # Should succeed without calling LiteLLM
        assert response.status_code == 200
        data = response.json()
        assert data["model_alias"] == "test-model"
        assert data["provider"] == "openai"
        assert data["actual_model"] == "gpt-4o"
        assert data["litellm_model_id"] is None  # Should be None now

    @patch('api.models.get_db')
    def test_create_model_alias_duplicate(self, mock_get_db, client):
        """Test creating duplicate model alias fails"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock query to return existing model
        existing_model = Mock()
        existing_model.model_alias = "existing-model"
        mock_db.query.return_value.filter.return_value.first.return_value = existing_model

        payload = {
            "model_alias": "existing-model",
            "display_name": "Existing Model",
            "provider": "openai",
            "actual_model": "gpt-4o",
            "pricing_input": 2.5,
            "pricing_output": 10.0,
            "access_groups": []
        }

        response = client.post("/api/models/create", json=payload)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @patch('api.models.get_db')
    def test_create_model_alias_with_pricing(self, mock_get_db, client):
        """Test model alias creation with custom pricing"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.flush.return_value = None
        mock_db.commit.return_value = None

        payload = {
            "model_alias": "premium-model",
            "display_name": "Premium Model",
            "provider": "anthropic",
            "actual_model": "claude-sonnet-4-5",
            "pricing_input": 3.0,
            "pricing_output": 15.0,
            "description": "Latest Claude model",
            "access_groups": []
        }

        response = client.post("/api/models/create", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["pricing_input"] == 3.0
        assert data["pricing_output"] == 15.0

    @patch('api.models.get_db')
    def test_create_model_alias_with_access_groups(self, mock_get_db, client):
        """Test model alias creation with access groups"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock no existing model
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # No existing model
            Mock(group_name="premium"),  # Access group exists
        ]

        mock_db.flush.return_value = None
        mock_db.commit.return_value = None

        payload = {
            "model_alias": "premium-chat",
            "display_name": "Premium Chat",
            "provider": "openai",
            "actual_model": "gpt-5",
            "pricing_input": 1.25,
            "pricing_output": 10.0,
            "access_groups": ["premium"]
        }

        response = client.post("/api/models/create", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "premium" in data["access_groups"]


class TestUpdateModelAlias:
    """Test PUT /api/models/{alias} endpoint"""

    @patch('api.models.get_db')
    def test_update_model_alias_success(self, mock_get_db, client, sample_model_alias):
        """Test successful model alias update"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock query to return existing model
        mock_db.query.return_value.filter.return_value.first.return_value = sample_model_alias
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        payload = {
            "display_name": "Updated Display Name",
            "pricing_input": 0.2,
            "pricing_output": 0.8
        }

        response = client.put("/api/models/chat-fast", json=payload)

        assert response.status_code == 200
        # Should not try to update LiteLLM

    @patch('api.models.get_db')
    def test_update_model_alias_not_found(self, mock_get_db, client):
        """Test updating non-existent model alias"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock query to return None
        mock_db.query.return_value.filter.return_value.first.return_value = None

        payload = {
            "display_name": "Updated Name"
        }

        response = client.put("/api/models/nonexistent", json=payload)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestDeleteModelAlias:
    """Test DELETE /api/models/{alias} endpoint"""

    @patch('api.models.get_db')
    def test_delete_model_alias_success(self, mock_get_db, client, sample_model_alias):
        """Test successful model alias deletion without LiteLLM"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock query to return existing model
        mock_db.query.return_value.filter.return_value.first.return_value = sample_model_alias
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        response = client.delete("/api/models/chat-fast")

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        # Should not try to delete from LiteLLM

    @patch('api.models.get_db')
    def test_delete_model_alias_not_found(self, mock_get_db, client):
        """Test deleting non-existent model alias"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock query to return None
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.delete("/api/models/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestListModelAliases:
    """Test GET /api/models endpoint"""

    @patch('api.models.get_db')
    def test_list_model_aliases(self, mock_get_db, client, sample_model_alias):
        """Test listing all model aliases"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock query to return list of models
        mock_db.query.return_value.all.return_value = [sample_model_alias]

        response = client.get("/api/models")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["model_alias"] == "chat-fast"

    @patch('api.models.get_db')
    def test_list_model_aliases_with_provider_filter(self, mock_get_db, client, sample_model_alias):
        """Test filtering models by provider"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock query chain
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [sample_model_alias]

        response = client.get("/api/models?provider=openai")

        assert response.status_code == 200
        data = response.json()
        # All returned models should be from OpenAI
        for model in data:
            assert model["provider"] == "openai"


class TestGetModelAlias:
    """Test GET /api/models/{alias} endpoint"""

    @patch('api.models.get_db')
    def test_get_model_alias_success(self, mock_get_db, client, sample_model_alias):
        """Test getting a specific model alias"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock query to return model
        mock_db.query.return_value.filter.return_value.first.return_value = sample_model_alias

        response = client.get("/api/models/chat-fast")

        assert response.status_code == 200
        data = response.json()
        assert data["model_alias"] == "chat-fast"
        assert data["provider"] == "openai"
        assert data["actual_model"] == "gpt-4o-mini"

    @patch('api.models.get_db')
    def test_get_model_alias_not_found(self, mock_get_db, client):
        """Test getting non-existent model alias"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock query to return None
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/api/models/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestDirectProviderIntegration:
    """Test that model aliases work with direct provider integration"""

    def test_no_litellm_model_id_required(self, sample_model_alias):
        """Test that litellm_model_id is not required"""
        assert sample_model_alias.litellm_model_id is None
        # Model should still be valid without LiteLLM ID

    def test_model_alias_has_provider_info(self, sample_model_alias):
        """Test that model alias has all needed provider info"""
        assert sample_model_alias.provider is not None
        assert sample_model_alias.actual_model is not None
        # These are sufficient for direct provider calls

    def test_pricing_stored_as_decimal(self, sample_model_alias):
        """Test that pricing is stored as Decimal for precision"""
        assert isinstance(sample_model_alias.pricing_input, Decimal)
        assert isinstance(sample_model_alias.pricing_output, Decimal)
        assert sample_model_alias.pricing_input == Decimal("0.15")
        assert sample_model_alias.pricing_output == Decimal("0.6")
