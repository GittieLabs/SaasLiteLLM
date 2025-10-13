"""
Authentication dependencies for FastAPI endpoints
"""
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from ..models.credits import TeamCredits
from ..models.job_tracking import get_db


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

    return team_creds.team_id
