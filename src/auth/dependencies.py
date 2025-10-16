"""
Authentication dependencies for FastAPI endpoints
"""
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, Union
from datetime import datetime
from ..models.credits import TeamCredits
from ..models.admin_users import AdminUser, AdminSession
from ..models.job_tracking import get_db
from ..config.settings import settings
from ..auth.utils import decode_access_token, extract_bearer_token, create_token_hash


async def verify_admin_key(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")
) -> None:
    """
    Verify admin API key for management endpoints (Legacy).

    Expects X-Admin-Key header with the MASTER_KEY from settings.

    This protects administrative endpoints like:
    - Organization creation/management
    - Team creation/management
    - Model group configuration
    - Credit allocation

    Raises:
        HTTPException: 401 if key is missing or invalid
    """
    if not x_admin_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Admin-Key header. Admin authentication required."
        )

    if x_admin_key != settings.master_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin API key"
        )


async def verify_admin_auth(
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    db: Session = Depends(get_db)
) -> Union[AdminUser, None]:
    """
    Verify admin authentication via JWT token or legacy X-Admin-Key.

    Supports two authentication methods:
    1. JWT Bearer token (preferred): Authorization: Bearer <token>
    2. Legacy X-Admin-Key header (backward compatibility): X-Admin-Key: <master_key>

    Returns:
        AdminUser if JWT authentication is used, None if X-Admin-Key is used

    Raises:
        HTTPException: 401 if authentication fails
    """
    # Try JWT authentication first (preferred method)
    if authorization:
        token = extract_bearer_token(authorization)
        if token:
            # Decode token
            payload = decode_access_token(token)
            if payload:
                user_id = payload.get("user_id")
                if user_id:
                    # Check if session is valid
                    token_hash = create_token_hash(token)
                    session = db.query(AdminSession).filter(
                        AdminSession.token_hash == token_hash,
                        AdminSession.is_revoked == False,
                        AdminSession.expires_at > datetime.utcnow()
                    ).first()

                    if session:
                        # Get user
                        user = db.query(AdminUser).filter(
                            AdminUser.user_id == user_id,
                            AdminUser.is_active == True
                        ).first()

                        if user:
                            return user

    # Fall back to X-Admin-Key authentication (legacy)
    if x_admin_key and x_admin_key == settings.master_key:
        return None  # Valid legacy auth, but no user object

    # Neither authentication method succeeded
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide either 'Authorization: Bearer <token>' or 'X-Admin-Key: <master_key>'"
    )


async def verify_virtual_key(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> str:
    """
    Verify virtual API key and return authenticated team_id.

    Expects Authorization header: "Bearer sk-xxx..."

    Returns:
        team_id: The authenticated team's ID

    Raises:
        HTTPException: 401 if key is missing or invalid
    """
    # Check if Authorization header is present
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Expected: 'Authorization: Bearer sk-xxx...'"
        )

    # Parse Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: 'Authorization: Bearer sk-xxx...'"
        )

    virtual_key = parts[1]

    # Validate virtual key exists and get team_id
    team_creds = db.query(TeamCredits).filter(
        TeamCredits.virtual_key == virtual_key
    ).first()

    if not team_creds:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    # Check team status
    if team_creds.status != "active":
        raise HTTPException(
            status_code=403,
            detail=f"Team access is {team_creds.status}. Please contact support."
        )

    return team_creds.team_id
