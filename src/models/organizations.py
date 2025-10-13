"""
Organization models for multi-tenant hierarchy
"""
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .job_tracking import Base


class Organization(Base):
    """
    Organization model for top-level multi-tenant structure.
    Organizations contain multiple teams.
    """
    __tablename__ = "organizations"

    organization_id = Column(String(255), primary_key=True)
    name = Column(String(500), nullable=False)
    status = Column(String(50), default="active")
    org_metadata = Column("metadata", JSON, default=dict)  # Use 'metadata' as DB column name
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "organization_id": self.organization_id,
            "name": self.name,
            "status": self.status,
            "metadata": self.org_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
