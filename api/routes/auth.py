"""
Authentication Routes - AssessIQ
=================================
API endpoints for user authentication.

Endpoints:
- POST /auth/login - Login for admin/teacher/student
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Logout (revoke refresh token)
- GET /auth/me - Get current user info
- PUT /auth/password - Change password
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database.models import get_db, Admin, Teacher, Student
from api.services.auth_service import (
    auth_service,
    get_current_user,
    get_client_ip,
    TokenData,
    Token,
    create_default_admin
)

logger = logging.getLogger("AssessIQ.Auth")

router = APIRouter()


# ========== Request/Response Models ==========
class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str
    role: str  # "admin", "teacher", "student"

    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@assessiq.com",
                "password": "admin123",
                "role": "admin"
            }
        }


class RefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    old_password: str
    new_password: str


class MessageResponse(BaseModel):
    """Simple message response."""
    success: bool
    message: str


# ========== Routes ==========
@router.post("/login", response_model=Token)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login a user and get access/refresh tokens.
    
    Roles:
    - admin: System administrator
    - teacher: Teacher/Faculty
    - student: Student
    """
    # Validate role
    if login_data.role not in ["admin", "teacher", "student"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'admin', 'teacher', or 'student'"
        )
    
    # Get client IP
    ip_address = get_client_ip(request)
    
    # Authenticate
    token, error = auth_service.login(
        email=login_data.email,
        password=login_data.password,
        role=login_data.role,
        ip_address=ip_address
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )
    
    return token


@router.post("/refresh")
async def refresh_token(refresh_data: RefreshRequest):
    """
    Refresh an access token using a refresh token.
    """
    new_token, error = auth_service.refresh_access_token(refresh_data.refresh_token)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )
    
    return {
        "success": True,
        "access_token": new_token,
        "token_type": "bearer"
    }


@router.post("/logout", response_model=MessageResponse)
async def logout(logout_data: LogoutRequest):
    """
    Logout by revoking the refresh token.
    """
    success = auth_service.logout(logout_data.refresh_token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already revoked token"
        )
    
    return MessageResponse(success=True, message="Logged out successfully")


@router.get("/me")
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's information.
    """
    user_data = None
    
    if current_user.role == "admin":
        user = db.query(Admin).filter(Admin.id == current_user.user_id).first()
        if user:
            user_data = user.to_dict()
    elif current_user.role == "teacher":
        user = db.query(Teacher).filter(Teacher.id == current_user.user_id).first()
        if user:
            user_data = user.to_dict()
    elif current_user.role == "student":
        user = db.query(Student).filter(Student.id == current_user.user_id).first()
        if user:
            user_data = user.to_dict()
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_data["role"] = current_user.role
    
    return {
        "success": True,
        "data": user_data
    }


@router.put("/password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Change the current user's password.
    """
    success, error = auth_service.change_password(
        user_id=current_user.user_id,
        role=current_user.role,
        old_password=password_data.old_password,
        new_password=password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return MessageResponse(
        success=True, 
        message="Password changed successfully. Please login again."
    )


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all_sessions(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Logout from all sessions by revoking all refresh tokens.
    """
    count = auth_service.logout_all(current_user.user_id, current_user.role)
    
    return MessageResponse(
        success=True,
        message=f"Logged out from {count} session(s)"
    )


# ========== Initialize Default Admin ==========
@router.on_event("startup")
async def startup_event():
    """Create default admin on startup."""
    create_default_admin()
