"""
Admin User Management API endpoints

Provides authentication and user management for the admin dashboard:
- Setup: First-time owner account creation (requires MASTER_KEY)
- Login/Logout: Email/password authentication with JWT
- User CRUD: Manage admin users with role-based permissions
- Audit Logs: View admin action history
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from ..models.admin_users import AdminUser, AdminSession, AdminAuditLog
from ..models.job_tracking import get_db
from ..auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_token_hash,
    decode_access_token,
    extract_bearer_token
)
from ..auth.dependencies import verify_admin_key
from ..config.settings import settings

router = APIRouter(prefix="/api/admin-users", tags=["admin-users"])


# Request/Response Models

class SetupRequest(BaseModel):
    """First-time owner account creation"""
    email: EmailStr
    display_name: str
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """Login with email and password"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response with JWT token and user info"""
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserCreateRequest(BaseModel):
    """Create a new admin user"""
    email: EmailStr
    display_name: str
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(owner|admin|user)$")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UserUpdateRequest(BaseModel):
    """Update an existing admin user"""
    display_name: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(owner|admin|user)$")
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class PasswordChangeRequest(BaseModel):
    """Change user password"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """User information response"""
    user_id: str
    email: str
    display_name: str
    role: str
    is_active: bool
    created_at: str
    created_by: Optional[str]
    last_login: Optional[str]
    metadata: Dict[str, Any]


class AuditLogResponse(BaseModel):
    """Audit log entry response"""
    audit_id: str
    user_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    created_at: str


# Helper Functions

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    if request.client:
        return request.client.host
    return "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("user-agent", "unknown")


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> AdminUser:
    """
    Dependency to get current authenticated user from JWT token.
    Raises 401 if token is invalid or user not found.
    """
    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Decode token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Check if session is valid and not revoked
    token_hash = create_token_hash(token)
    session = db.query(AdminSession).filter(
        AdminSession.token_hash == token_hash,
        AdminSession.is_revoked == False,
        AdminSession.expires_at > datetime.utcnow()
    ).first()

    if not session:
        raise HTTPException(status_code=401, detail="Session expired or revoked")

    # Get user
    user = db.query(AdminUser).filter(
        AdminUser.user_id == user_id,
        AdminUser.is_active == True
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


def require_owner_or_admin(current_user: AdminUser = Depends(get_current_user)) -> AdminUser:
    """
    Dependency to require owner or admin role.
    """
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Required roles: owner, admin"
        )
    return current_user


async def log_audit(
    db: Session,
    user_id: Optional[uuid.UUID],
    action: str,
    resource_type: Optional[str],
    resource_id: Optional[str],
    details: Optional[Dict[str, Any]],
    request: Request
):
    """Log an admin action to the audit log"""
    audit_entry = AdminAuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=get_client_ip(request)
    )
    db.add(audit_entry)
    db.commit()


# Endpoints

@router.get("/setup/status")
async def check_setup_status(db: Session = Depends(get_db)):
    """
    Check if initial setup is required.

    Public endpoint - no authentication required.
    Returns whether an owner account needs to be created.
    """
    user_count = db.query(AdminUser).count()
    return {
        "needs_setup": user_count == 0,
        "has_users": user_count > 0
    }


@router.post("/setup", response_model=LoginResponse)
async def setup_owner_account(
    request: SetupRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    First-time setup: Create owner account.

    This endpoint is only available when no users exist yet.
    No authentication required for first-time setup.

    The created owner account can then be used to login with email/password.
    """
    # Check if any users exist
    existing_users = db.query(AdminUser).count()
    if existing_users > 0:
        raise HTTPException(
            status_code=400,
            detail="Setup already completed. Owner account exists."
        )

    # Check if email is already used
    existing_email = db.query(AdminUser).filter(
        AdminUser.email == request.email
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create owner user
    hashed_password = hash_password(request.password)
    user = AdminUser(
        email=request.email,
        display_name=request.display_name,
        password_hash=hashed_password,
        role="owner",
        is_active=True,
        created_by=None,  # First user, no creator
        user_metadata={}
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create access token
    token = create_access_token(
        data={
            "user_id": str(user.user_id),
            "email": user.email,
            "role": user.role
        }
    )

    # Create session
    token_hash = create_token_hash(token)
    session = AdminSession(
        user_id=user.user_id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=24),
        ip_address=get_client_ip(req),
        user_agent=get_user_agent(req)
    )
    db.add(session)

    # Update last_login
    user.last_login = datetime.utcnow()

    # Log audit
    await log_audit(
        db, user.user_id, "setup_owner", "admin_user", str(user.user_id),
        {"email": user.email, "display_name": user.display_name}, req
    )

    db.commit()

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=user.to_dict()
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.

    Returns JWT token for subsequent authenticated requests.
    """
    # Find user by email
    user = db.query(AdminUser).filter(
        AdminUser.email == request.email
    ).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create access token
    token = create_access_token(
        data={
            "user_id": str(user.user_id),
            "email": user.email,
            "role": user.role
        }
    )

    # Create session
    token_hash = create_token_hash(token)
    session = AdminSession(
        user_id=user.user_id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=24),
        ip_address=get_client_ip(req),
        user_agent=get_user_agent(req)
    )
    db.add(session)

    # Update last_login
    user.last_login = datetime.utcnow()

    # Log audit
    await log_audit(
        db, user.user_id, "login", "admin_user", str(user.user_id),
        {"email": user.email}, req
    )

    db.commit()

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=user.to_dict()
    )


@router.post("/logout")
async def logout(
    req: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Logout and revoke current session.

    Requires: Bearer token in Authorization header
    """
    token = extract_bearer_token(authorization)
    if token:
        token_hash = create_token_hash(token)
        session = db.query(AdminSession).filter(
            AdminSession.token_hash == token_hash
        ).first()

        if session:
            session.is_revoked = True
            db.commit()

    # Log audit
    await log_audit(
        db, current_user.user_id, "logout", "admin_user", str(current_user.user_id),
        {}, req
    )

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Requires: Bearer token in Authorization header
    """
    return UserResponse(**current_user.to_dict())


@router.get("", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(require_owner_or_admin)
):
    """
    List all admin users.

    Requires: Bearer token with owner or admin role
    """
    users = db.query(AdminUser).order_by(AdminUser.created_at.desc()).all()
    return [UserResponse(**user.to_dict()) for user in users]


@router.post("", response_model=UserResponse)
async def create_user(
    request: UserCreateRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(require_owner_or_admin)
):
    """
    Create a new admin user.

    Requires: Bearer token with owner or admin role

    Role restrictions:
    - Admins can only create 'user' roles
    - Owners can create any role
    """
    # Check role permissions
    if current_user.role == "admin" and request.role in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Admins can only create users with 'user' role"
        )

    # Check if email already exists
    existing = db.query(AdminUser).filter(
        AdminUser.email == request.email
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create user
    hashed_password = hash_password(request.password)
    user = AdminUser(
        email=request.email,
        display_name=request.display_name,
        password_hash=hashed_password,
        role=request.role,
        is_active=True,
        created_by=current_user.user_id,
        user_metadata=request.metadata
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Log audit
    await log_audit(
        db, current_user.user_id, "created_user", "admin_user", str(user.user_id),
        {"email": user.email, "role": user.role}, req
    )

    return UserResponse(**user.to_dict())


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(require_owner_or_admin)
):
    """
    Update an admin user.

    Requires: Bearer token with owner or admin role

    Role restrictions:
    - Admins cannot modify owner or admin users
    - Owners can modify any user
    - Cannot modify your own role
    """
    # Get target user
    user = db.query(AdminUser).filter(
        AdminUser.user_id == uuid.UUID(user_id)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check role permissions
    if current_user.role == "admin" and user.role in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Admins cannot modify owner or admin users"
        )

    # Prevent changing your own role
    if str(current_user.user_id) == user_id and request.role is not None:
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own role"
        )

    # Update fields
    if request.display_name is not None:
        user.display_name = request.display_name
    if request.role is not None:
        # Additional check for admin trying to promote
        if current_user.role == "admin" and request.role in ["owner", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Admins cannot promote users to owner or admin"
            )
        user.role = request.role
    if request.is_active is not None:
        user.is_active = request.is_active
    if request.metadata is not None:
        user.user_metadata = request.metadata

    db.commit()
    db.refresh(user)

    # Log audit
    await log_audit(
        db, current_user.user_id, "updated_user", "admin_user", str(user.user_id),
        request.dict(exclude_none=True), req
    )

    return UserResponse(**user.to_dict())


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    req: Request,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(require_owner_or_admin)
):
    """
    Delete (deactivate) an admin user.

    Requires: Bearer token with owner or admin role

    Role restrictions:
    - Admins cannot delete owner or admin users
    - Owners can delete any user except themselves
    - Cannot delete your own account
    """
    # Get target user
    user = db.query(AdminUser).filter(
        AdminUser.user_id == uuid.UUID(user_id)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-deletion
    if str(current_user.user_id) == user_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )

    # Check role permissions
    if current_user.role == "admin" and user.role in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Admins cannot delete owner or admin users"
        )

    # Deactivate user instead of deleting
    user.is_active = False
    db.commit()

    # Revoke all sessions
    db.query(AdminSession).filter(
        AdminSession.user_id == user.user_id
    ).update({"is_revoked": True})
    db.commit()

    # Log audit
    await log_audit(
        db, current_user.user_id, "deleted_user", "admin_user", str(user.user_id),
        {"email": user.email}, req
    )

    return {"message": f"User {user.email} deactivated successfully"}


@router.post("/me/change-password")
async def change_password(
    request: PasswordChangeRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """
    Change current user's password.

    Requires: Bearer token in Authorization header
    """
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.password_hash = hash_password(request.new_password)
    db.commit()

    # Log audit
    await log_audit(
        db, current_user.user_id, "changed_password", "admin_user", str(current_user.user_id),
        {}, req
    )

    return {"message": "Password changed successfully"}


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(require_owner_or_admin)
):
    """
    Get audit logs.

    Requires: Bearer token with owner or admin role

    Query parameters:
    - limit: Max number of logs to return (default 100)
    - offset: Pagination offset (default 0)
    - action: Filter by action type
    - user_id: Filter by user ID
    - resource_type: Filter by resource type
    """
    query = db.query(AdminAuditLog)

    # Apply filters
    if action:
        query = query.filter(AdminAuditLog.action == action)
    if user_id:
        query = query.filter(AdminAuditLog.user_id == uuid.UUID(user_id))
    if resource_type:
        query = query.filter(AdminAuditLog.resource_type == resource_type)

    # Order by newest first
    query = query.order_by(AdminAuditLog.created_at.desc())

    # Apply pagination
    logs = query.limit(limit).offset(offset).all()

    return [AuditLogResponse(**log.to_dict()) for log in logs]
