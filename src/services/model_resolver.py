"""
Model Group Resolution Service
Resolves model group names (e.g., "ResumeAgent") to actual model names with fallbacks
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.model_groups import ModelGroup, ModelGroupModel, TeamModelGroup


class ModelResolutionError(Exception):
    """Raised when model group resolution fails"""
    pass


class ModelResolver:
    """
    Service for resolving model group names to actual models
    """

    def __init__(self, db: Session):
        self.db = db

    def verify_team_access(self, team_id: str, model_group_name: str) -> bool:
        """
        Verify that a team has access to a specific model group
        """
        # Get model group
        model_group = self.db.query(ModelGroup).filter(
            ModelGroup.group_name == model_group_name
        ).first()

        if not model_group:
            return False

        # Check if team has this group assigned
        assignment = self.db.query(TeamModelGroup).filter(
            and_(
                TeamModelGroup.team_id == team_id,
                TeamModelGroup.model_group_id == model_group.model_group_id
            )
        ).first()

        return assignment is not None

    def resolve_model_group(
        self,
        team_id: str,
        model_group_name: str,
        include_fallbacks: bool = True
    ) -> Tuple[str, List[str]]:
        """
        Resolve a model group name to the actual model name(s)

        Args:
            team_id: Team requesting the model
            model_group_name: Name of model group (e.g., "ResumeAgent")
            include_fallbacks: Whether to include fallback models

        Returns:
            Tuple of (primary_model, [fallback_models])

        Raises:
            ModelResolutionError: If resolution fails
        """
        # Verify team has access to this model group
        if not self.verify_team_access(team_id, model_group_name):
            raise ModelResolutionError(
                f"Team '{team_id}' does not have access to model group '{model_group_name}'"
            )

        # Get model group
        model_group = self.db.query(ModelGroup).filter(
            and_(
                ModelGroup.group_name == model_group_name,
                ModelGroup.status == "active"
            )
        ).first()

        if not model_group:
            raise ModelResolutionError(f"Model group '{model_group_name}' not found or inactive")

        # Get models sorted by priority
        models = self.db.query(ModelGroupModel).filter(
            and_(
                ModelGroupModel.model_group_id == model_group.model_group_id,
                ModelGroupModel.is_active == True
            )
        ).order_by(ModelGroupModel.priority).all()

        if not models:
            raise ModelResolutionError(f"No active models configured for group '{model_group_name}'")

        # Primary model is priority 0
        primary_model = models[0].model_name

        # Fallback models are priority 1+
        fallback_models = [m.model_name for m in models[1:]] if include_fallbacks else []

        return primary_model, fallback_models

    def get_model_group_by_name(self, model_group_name: str) -> Optional[ModelGroup]:
        """
        Get a model group by its name
        """
        return self.db.query(ModelGroup).filter(
            ModelGroup.group_name == model_group_name
        ).first()

    def get_team_model_groups(self, team_id: str) -> List[ModelGroup]:
        """
        Get all model groups assigned to a team
        """
        assignments = self.db.query(TeamModelGroup).filter(
            TeamModelGroup.team_id == team_id
        ).all()

        model_group_ids = [a.model_group_id for a in assignments]

        return self.db.query(ModelGroup).filter(
            ModelGroup.model_group_id.in_(model_group_ids)
        ).all()


def get_model_resolver(db: Session) -> ModelResolver:
    """
    Factory function to get a ModelResolver instance
    """
    return ModelResolver(db)
