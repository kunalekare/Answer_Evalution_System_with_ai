"""
OAuth Routes - Google & GitHub Authentication Endpoints
=======================================================
API endpoints for OAuth login/signup flow.

Endpoints:
- GET /oauth/google/authorize - Redirect to Google OAuth
- GET /oauth/google/callback - Google OAuth callback
- GET /oauth/github/authorize - Redirect to GitHub OAuth
- GET /oauth/github/callback - GitHub OAuth callback
"""

import logging
from typing import Optional
from urllib.parse import urlencode
import base64
import json

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database.models import get_db
from api.services.oauth_service import oauth_service
from config.settings import settings

logger = logging.getLogger("AssessIQ.OAuth")

router = APIRouter(prefix="/oauth", tags=["OAuth Authentication"])


# ========== Helper Functions ==========
def encode_state(role: str) -> str:
    """Encode role into OAuth state parameter."""
    return base64.urlsafe_b64encode(json.dumps({"role": role}).encode()).decode()


def decode_state(state: str) -> dict:
    """Decode role from OAuth state parameter."""
    try:
        return json.loads(base64.urlsafe_b64decode(state.encode()).decode())
    except Exception:
        return {"role": "student"}


# ========== Google OAuth Routes ==========
@router.get("/google/authorize", response_description="Redirect to Google OAuth")
async def google_authorize(role: str = "student"):
    """
    Initiate Google OAuth flow.
    
    Query Parameters:
    - role: 'student', 'teacher', or 'admin' (default: student)
    
    Returns:
        Redirect to Google OAuth consent screen
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    if role not in ["student", "teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'student', 'teacher', or 'admin'"
        )
    
    # Encode role into state for recovery in callback
    state = encode_state(role)
    
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",  # Don't request refresh token
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get("/google/callback", response_description="Google OAuth callback")
async def google_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    
    Query Parameters:
    - code: Authorization code from Google
    - state: State parameter with encoded role
    - error: Error message if auth failed
    
    Returns:
        Redirect to frontend with token or error
    """
    if error:
        logger.warning(f"Google OAuth error: {error}")
        return RedirectResponse(
            url=f"{settings.OAUTH_ERROR_REDIRECT}?error={error}",
            status_code=status.HTTP_302_FOUND
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code"
        )
    
    try:
        # Decode role from state
        state_data = decode_state(state)
        role = state_data.get("role", "student")
        
        # Process OAuth
        result = await oauth_service.handle_google_oauth(code, db, role)
        
        # Create redirect URL with tokens
        redirect_params = {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
            "role": role,
            "user": json.dumps(result["user"]),
        }
        
        redirect_url = f"{settings.OAUTH_SUCCESS_REDIRECT}?{urlencode(redirect_params)}"
        
        logger.info(f"Successful Google OAuth login for: {result['user']['email']}")
        
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
        
    except HTTPException as e:
        logger.error(f"Google OAuth HTTP error: {e.detail}")
        return RedirectResponse(
            url=f"{settings.OAUTH_ERROR_REDIRECT}?error={e.detail}",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        logger.error(f"Google callback error: {str(e)}")
        return RedirectResponse(
            url=f"{settings.OAUTH_ERROR_REDIRECT}?error=authentication_failed",
            status_code=status.HTTP_302_FOUND
        )


# ========== GitHub OAuth Routes ==========
@router.get("/github/authorize", response_description="Redirect to GitHub OAuth")
async def github_authorize(role: str = "student"):
    """
    Initiate GitHub OAuth flow.
    
    Query Parameters:
    - role: 'student', 'teacher', or 'admin' (default: student)
    
    Returns:
        Redirect to GitHub OAuth authorization
    """
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth not configured"
        )
    
    if role not in ["student", "teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'student', 'teacher', or 'admin'"
        )
    
    # Encode role into state
    state = encode_state(role)
    
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "user:email read:user",
        "state": state,
        "allow_signup": "true",
    }
    
    auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    
    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get("/github/callback", response_description="GitHub OAuth callback")
async def github_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """
    Handle GitHub OAuth callback.
    
    Query Parameters:
    - code: Authorization code from GitHub
    - state: State parameter with encoded role
    - error: Error message if auth failed
    
    Returns:
        Redirect to frontend with token or error
    """
    if error:
        logger.warning(f"GitHub OAuth error: {error}")
        return RedirectResponse(
            url=f"{settings.OAUTH_ERROR_REDIRECT}?error={error}",
            status_code=status.HTTP_302_FOUND
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code"
        )
    
    try:
        # Decode role from state
        state_data = decode_state(state)
        role = state_data.get("role", "student")
        
        # Process OAuth
        result = await oauth_service.handle_github_oauth(code, db, role)
        
        # Create redirect URL with tokens
        redirect_params = {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
            "role": role,
            "user": json.dumps(result["user"]),
        }
        
        redirect_url = f"{settings.OAUTH_SUCCESS_REDIRECT}?{urlencode(redirect_params)}"
        
        logger.info(f"Successful GitHub OAuth login for: {result['user']['email']}")
        
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
        
    except HTTPException as e:
        logger.error(f"GitHub OAuth HTTP error: {e.detail}")
        return RedirectResponse(
            url=f"{settings.OAUTH_ERROR_REDIRECT}?error={e.detail}",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        logger.error(f"GitHub callback error: {str(e)}")
        return RedirectResponse(
            url=f"{settings.OAUTH_ERROR_REDIRECT}?error=authentication_failed",
            status_code=status.HTTP_302_FOUND
        )


# ========== OAuth Info Endpoints ==========
@router.get("/config", response_description="OAuth configuration for frontend")
async def get_oauth_config():
    """
    Get OAuth configuration for frontend.
    
    Returns:
        OAuth client IDs and URLs for frontend
    """
    return {
        "google": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "authorize_url": f"/api/v1/auth/oauth/google/authorize",
            "configured": bool(settings.GOOGLE_CLIENT_ID),
        },
        "github": {
            "client_id": settings.GITHUB_CLIENT_ID,
            "authorize_url": f"/api/v1/auth/oauth/github/authorize",
            "configured": bool(settings.GITHUB_CLIENT_ID),
        }
    }
