"""
Model Alias and Access Group models for LiteLLM integration
"""
from sqlalchemy import Column, String, Numeric, DateTime, Text, ForeignKey, UUID, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .job_tracking import Base


class ModelAlias(Base):
    """
    Model Alias - User-facing name that maps to actual LLM model
    Example: "chat-fast" → "gpt-3.5-turbo"
    """
    __tablename__ = "model_aliases"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_alias = Column(String(200), unique=True, nullable=False)  # e.g., "chat-fast"
    display_name = Column(String(200))                              # e.g., "Fast Chat Model"
    provider = Column(String(100), nullable=False)                  # e.g., "openai", "anthropic"
    actual_model = Column(String(200), nullable=False)              # e.g., "gpt-3.5-turbo"
    litellm_model_id = Column(String(200))                          # LiteLLM's DB model ID
    description = Column(Text)
    pricing_input = Column(Numeric(10, 6))                          # Cost per 1M input tokens
    pricing_output = Column(Numeric(10, 6))                         # Cost per 1M output tokens
    status = Column(String(50), default="active")                   # active, inactive, deprecated
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    access_group_assignments = relationship(
        "ModelAliasAccessGroup",
        back_populates="model_alias",
        cascade="all, delete-orphan"
    )

    def to_dict(self, include_access_groups=False):
        result = {
            "id": str(self.id),
            "model_alias": self.model_alias,
            "display_name": self.display_name,
            "provider": self.provider,
            "actual_model": self.actual_model,
            "litellm_model_id": self.litellm_model_id,
            "description": self.description,
            "pricing_input": float(self.pricing_input) if self.pricing_input else None,
            "pricing_output": float(self.pricing_output) if self.pricing_output else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        if include_access_groups:
            result["access_groups"] = [
                assignment.access_group.group_name
                for assignment in self.access_group_assignments
                if assignment.access_group
            ]

        return result


class ModelAccessGroup(Base):
    """
    Model Access Group - Collection of model aliases for access control
    Example: "basic-chat" contains ["chat-fast", "chat-smart"]
    """
    __tablename__ = "model_access_groups"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_name = Column(String(200), unique=True, nullable=False)   # e.g., "basic-chat"
    display_name = Column(String(200))                              # e.g., "Basic Chat Models"
    description = Column(Text)
    status = Column(String(50), default="active")                   # active, inactive
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    model_alias_assignments = relationship(
        "ModelAliasAccessGroup",
        back_populates="access_group",
        cascade="all, delete-orphan"
    )
    team_assignments = relationship(
        "TeamAccessGroup",
        back_populates="access_group",
        cascade="all, delete-orphan"
    )

    def to_dict(self, include_models=False, include_teams=False):
        result = {
            "id": str(self.id),
            "group_name": self.group_name,
            "display_name": self.display_name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        if include_models:
            result["model_aliases"] = [
                assignment.model_alias.to_dict()
                for assignment in self.model_alias_assignments
                if assignment.model_alias
            ]

        if include_teams:
            result["teams"] = [
                assignment.team_id
                for assignment in self.team_assignments
            ]

        return result


class ModelAliasAccessGroup(Base):
    """
    Assignment table mapping model aliases to access groups (many-to-many)
    """
    __tablename__ = "model_alias_access_groups"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_alias_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('model_aliases.id', ondelete='CASCADE'),
        nullable=False
    )
    access_group_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('model_access_groups.id', ondelete='CASCADE'),
        nullable=False
    )
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    model_alias = relationship("ModelAlias", back_populates="access_group_assignments")
    access_group = relationship("ModelAccessGroup", back_populates="model_alias_assignments")

    __table_args__ = (
        Index('idx_model_alias_access_groups_alias', 'model_alias_id'),
        Index('idx_model_alias_access_groups_group', 'access_group_id'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "model_alias_id": str(self.model_alias_id),
            "access_group_id": str(self.access_group_id),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None
        }


class TeamAccessGroup(Base):
    """
    Assignment table mapping teams to their allowed access groups
    Replaces the old team_model_groups table
    """
    __tablename__ = "team_access_groups"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(String(255), nullable=False)
    access_group_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('model_access_groups.id', ondelete='CASCADE'),
        nullable=False
    )
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    access_group = relationship("ModelAccessGroup", back_populates="team_assignments")

    __table_args__ = (
        Index('idx_team_access_groups_team', 'team_id'),
        Index('idx_team_access_groups_group', 'access_group_id'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "team_id": self.team_id,
            "access_group_id": str(self.access_group_id),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None
        }
