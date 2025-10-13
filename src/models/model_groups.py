"""
Model Group models for dynamic model routing and management
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, UUID, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .job_tracking import Base


class ModelGroup(Base):
    """
    Model Group (e.g., ResumeAgent, ParsingAgent, RAGAgent)
    Represents a named group of models with primary and fallback configurations
    """
    __tablename__ = "model_groups"

    model_group_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    models = relationship("ModelGroupModel", back_populates="model_group", cascade="all, delete-orphan")
    team_assignments = relationship("TeamModelGroup", back_populates="model_group", cascade="all, delete-orphan")

    def to_dict(self, include_models=False):
        result = {
            "model_group_id": str(self.model_group_id),
            "group_name": self.group_name,
            "display_name": self.display_name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        if include_models:
            result["models"] = [m.to_dict() for m in sorted(self.models, key=lambda x: x.priority)]

        return result


class ModelGroupModel(Base):
    """
    Models assigned to a model group with priority (0 = primary, 1+ = fallbacks)
    """
    __tablename__ = "model_group_models"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_group_id = Column(PG_UUID(as_uuid=True), ForeignKey('model_groups.model_group_id', ondelete='CASCADE'), nullable=False)
    model_name = Column(String(200), nullable=False)
    priority = Column(Integer, default=0)  # 0 = primary, 1 = first fallback, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    model_group = relationship("ModelGroup", back_populates="models")

    __table_args__ = (
        Index('idx_model_group_models_lookup', 'model_group_id', 'priority', 'is_active'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "model_group_id": str(self.model_group_id),
            "model_name": self.model_name,
            "priority": self.priority,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class TeamModelGroup(Base):
    """
    Assignment table mapping teams to their assigned model groups
    """
    __tablename__ = "team_model_groups"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(String(255), nullable=False)
    model_group_id = Column(PG_UUID(as_uuid=True), ForeignKey('model_groups.model_group_id', ondelete='CASCADE'), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    model_group = relationship("ModelGroup", back_populates="team_assignments")

    __table_args__ = (
        Index('idx_team_model_groups_team', 'team_id'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "team_id": self.team_id,
            "model_group_id": str(self.model_group_id),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None
        }
