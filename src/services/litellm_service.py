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
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a team in LiteLLM

        Args:
            team_id: Unique team identifier
            team_alias: Human-readable team name
            organization_id: Organization this team belongs to
            max_budget: Maximum budget in USD (optional)
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


def get_litellm_service() -> LiteLLMService:
    """Dependency injection for LiteLLM service"""
    return LiteLLMService()
