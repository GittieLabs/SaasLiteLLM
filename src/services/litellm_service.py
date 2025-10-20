"""
LiteLLM Service - Integration with LiteLLM Proxy
Handles team creation and virtual key management
"""
import httpx
from typing import Optional, Dict, Any
from ..config.settings import settings


class LiteLLMServiceError(Exception):
    """Base exception for LiteLLM service errors"""
    pass


class LiteLLMService:
    """Service for managing LiteLLM teams and virtual keys"""

    def __init__(self):
        self.base_url = settings.litellm_proxy_url
        self.master_key = settings.litellm_master_key

    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for LiteLLM API calls"""
        return {
            "Authorization": f"Bearer {self.master_key}",
            "Content-Type": "application/json"
        }

    async def create_team(
        self,
        team_id: str,
        team_alias: str,
        organization_id: Optional[str] = None,
        max_budget: Optional[float] = None,
        models: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a team in LiteLLM

        Args:
            team_id: Unique team identifier
            team_alias: Human-readable team name
            organization_id: Organization this team belongs to
            max_budget: Maximum budget in USD (optional)
            models: List of allowed models for this team
            metadata: Additional team metadata

        Returns:
            Dict with team creation response
        """
        url = f"{self.base_url}/team/new"

        payload = {
            "team_id": team_id,
            "team_alias": team_alias,
        }

        if organization_id:
            payload["organization_id"] = organization_id

        if max_budget is not None:
            payload["max_budget"] = max_budget

        if models:
            payload["models"] = models

        if metadata:
            payload["metadata"] = metadata

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise LiteLLMServiceError(
                f"Failed to create team in LiteLLM: {e.response.text}"
            )
        except Exception as e:
            raise LiteLLMServiceError(f"LiteLLM API error: {str(e)}")

    async def generate_key(
        self,
        team_id: str,
        key_alias: Optional[str] = None,
        max_budget: Optional[float] = None,
        budget_duration: Optional[str] = None,
        models: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a virtual key for a team

        Args:
            team_id: Team identifier
            key_alias: Human-readable key name
            max_budget: Maximum budget for this key in USD
            budget_duration: Budget reset period (e.g., "1d", "1mo")
            models: List of allowed models (None = all models)
            metadata: Additional key metadata

        Returns:
            Dict with key generation response including 'key' field
        """
        url = f"{self.base_url}/key/generate"

        payload = {
            "team_id": team_id,
        }

        if key_alias:
            payload["key_alias"] = key_alias
        else:
            payload["key_alias"] = f"{team_id}_key"

        if max_budget is not None:
            payload["max_budget"] = max_budget

        if budget_duration:
            payload["budget_duration"] = budget_duration

        if models:
            payload["models"] = models

        if metadata:
            payload["metadata"] = metadata

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise LiteLLMServiceError(
                f"Failed to generate key in LiteLLM: {e.response.text}"
            )
        except Exception as e:
            raise LiteLLMServiceError(f"LiteLLM API error: {str(e)}")

    async def get_team(self, team_id: str) -> Dict[str, Any]:
        """
        Get team details from LiteLLM

        Args:
            team_id: Team identifier

        Returns:
            Dict with team details
        """
        url = f"{self.base_url}/team/info"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    params={"team_id": team_id},
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise LiteLLMServiceError(
                f"Failed to get team from LiteLLM: {e.response.text}"
            )
        except Exception as e:
            raise LiteLLMServiceError(f"LiteLLM API error: {str(e)}")

    async def delete_key(self, key: str) -> Dict[str, Any]:
        """
        Delete a virtual key

        Args:
            key: The virtual key to delete

        Returns:
            Dict with deletion response
        """
        url = f"{self.base_url}/key/delete"

        payload = {"keys": [key]}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise LiteLLMServiceError(
                f"Failed to delete key in LiteLLM: {e.response.text}"
            )
        except Exception as e:
            raise LiteLLMServiceError(f"LiteLLM API error: {str(e)}")

    async def update_team_budget(
        self,
        team_id: str,
        max_budget: float
    ) -> Dict[str, Any]:
        """
        Update team's budget limit

        Args:
            team_id: Team identifier
            max_budget: New maximum budget in USD

        Returns:
            Dict with update response
        """
        url = f"{self.base_url}/team/update"

        payload = {
            "team_id": team_id,
            "max_budget": max_budget
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise LiteLLMServiceError(
                f"Failed to update team budget: {e.response.text}"
            )
        except Exception as e:
            raise LiteLLMServiceError(f"LiteLLM API error: {str(e)}")

    # ========== Model Alias Management ==========

    async def create_model_alias(
        self,
        model_alias: str,
        provider: str,
        actual_model: str,
        access_groups: Optional[list] = None,
        credential_name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        pricing: Optional[Dict] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create model alias in LiteLLM

        Args:
            model_alias: User-facing alias name (e.g., "chat-fast")
            provider: Provider name (e.g., "openai", "anthropic")
            actual_model: Real model name (e.g., "gpt-3.5-turbo")
            access_groups: List of model access group names
            credential_name: Name of LiteLLM credential to use
            api_key: API key for the provider
            api_base: Custom API base URL
            pricing: Dict with input/output pricing per 1M tokens
            metadata: Additional model metadata

        Returns:
            Dict with model creation response including model ID
        """
        url = f"{self.base_url}/model/new"

        # Build litellm_params
        litellm_params = {
            "model": f"{provider}/{actual_model}"
        }

        if credential_name:
            litellm_params["litellm_credential_name"] = credential_name
        if api_key:
            litellm_params["api_key"] = api_key
        if api_base:
            litellm_params["api_base"] = api_base

        # Build model_info
        model_info = {}
        if access_groups:
            model_info["access_groups"] = access_groups
        if pricing:
            model_info["pricing"] = pricing
        if metadata:
            model_info.update(metadata)

        payload = {
            "model_name": model_alias,
            "litellm_params": litellm_params
        }

        if model_info:
            payload["model_info"] = model_info

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise LiteLLMServiceError(
                f"Failed to create model alias in LiteLLM: {e.response.text}"
            )
        except Exception as e:
            raise LiteLLMServiceError(f"LiteLLM API error: {str(e)}")

    async def update_model_alias(
        self,
        model_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update model alias in LiteLLM

        Args:
            model_id: LiteLLM model ID
            updates: Dict with fields to update

        Returns:
            Dict with update response
        """
        url = f"{self.base_url}/model/update"

        payload = {
            "id": model_id,
            **updates
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise LiteLLMServiceError(
                f"Failed to update model alias: {e.response.text}"
            )
        except Exception as e:
            raise LiteLLMServiceError(f"LiteLLM API error: {str(e)}")

    async def delete_model_alias(self, model_id: str) -> Dict[str, Any]:
        """
        Delete model alias from LiteLLM

        Args:
            model_id: LiteLLM model ID

        Returns:
            Dict with deletion response
        """
        url = f"{self.base_url}/model/delete"

        payload = {"id": model_id}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise LiteLLMServiceError(
                f"Failed to delete model alias: {e.response.text}"
            )
        except Exception as e:
            raise LiteLLMServiceError(f"LiteLLM API error: {str(e)}")

    async def get_model_aliases(self) -> list[Dict[str, Any]]:
        """
        List all model aliases from LiteLLM

        Returns:
            List of model aliases
        """
        url = f"{self.base_url}/model/info"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                result = response.json()

                # LiteLLM returns {"data": [...]}
                if isinstance(result, dict) and "data" in result:
                    return result["data"]
                return result if isinstance(result, list) else []
        except httpx.HTTPStatusError as e:
            raise LiteLLMServiceError(
                f"Failed to get model aliases: {e.response.text}"
            )
        except Exception as e:
            raise LiteLLMServiceError(f"LiteLLM API error: {str(e)}")

    async def update_team_models(
        self,
        team_id: str,
        model_aliases: list[str]
    ) -> Dict[str, Any]:
        """
        Update team's allowed models

        Args:
            team_id: Team identifier
            model_aliases: List of model alias names

        Returns:
            Dict with update response
        """
        url = f"{self.base_url}/team/update"

        payload = {
            "team_id": team_id,
            "models": model_aliases
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise LiteLLMServiceError(
                f"Failed to update team models: {e.response.text}"
            )
        except Exception as e:
            raise LiteLLMServiceError(f"LiteLLM API error: {str(e)}")


def get_litellm_service() -> LiteLLMService:
    """Dependency injection for LiteLLM service"""
    return LiteLLMService()
