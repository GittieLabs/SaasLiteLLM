"""
Admin User Management Models

Models for admin dashboard user authentication, sessions, and audit logging.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .job_tracking import Base


class AdminUser(Base):
    """
    Admin dashboard users with role-based access control.

    Roles:
    - owner: Full access, can manage admins
    - admin: Manage users and resources, cannot change admin roles
    - user: Read-only access
    """
    __tablename__ = "admin_users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, index=True)  # 'owner', 'admin', 'user'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('admin_users.user_id'), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    user_metadata = Column(JSON, default={}, nullable=False)

    def to_dict(self):
        """Convert to dictionary (excluding password_hash)"""
        return {
            "user_id": str(self.user_id),
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": str(self.created_by) if self.created_by else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "metadata": self.user_metadata or {}
        }


class AdminSession(Base):
    """
    Admin user sessions for JWT token management.

    Tracks active sessions and allows token revocation.
    """
    __tablename__ = "admin_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('admin_users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "session_id": str(self.session_id),
            "user_id": str(self.user_id),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ip_address": self.ip_address,
            "is_revoked": self.is_revoked
        }


class AdminAuditLog(Base):
    """
    Audit log for all admin actions.

    Tracks who did what, when, and from where for compliance and security.
    """
    __tablename__ = "admin_audit_log"

    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('admin_users.user_id'), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # e.g., 'created_team', 'deleted_user'
    resource_type = Column(String(50), nullable=True, index=True)  # e.g., 'team', 'organization', 'user'
    resource_id = Column(String(255), nullable=True, index=True)
    details = Column(JSON, nullable=True)  # Additional context about the action
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "audit_id": str(self.audit_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details or {},
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
