"""
OAuth Service - Google & GitHub Authentication
================================================
Handle OAuth flows for Google and GitHub login/signup.

Features:
- Google OAuth 2.0
- GitHub OAuth 2.0
- Automatic user creation/linking
- Role-based access (defaults to student, can be promoted)
"""

import logging
import httpx
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from database.models import Admin, Teacher, Student, UserStatus
from api.services.auth_service import create_tokens, hash_password
from config.settings import settings

logger = logging.getLogger("AssessIQ.OAuth")


class OAuthService:
    """Service for handling OAuth authentication flows."""
    
    # ========== Google OAuth ==========
    @staticmethod
    async def get_google_user_info(access_token: str) -> Dict[str, Any]:
        """
        Get user info from Google using access token.
        
        Args:
            access_token: Google OAuth access token
            
        Returns:
            Dict with user info (id, email, name, picture)
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.error(f"Google userinfo error: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to get Google user info"
                )
            
            return response.json()

    @staticmethod
    async def exchange_google_code(code: str) -> str:
        """
        Exchange Google authorization code for access token.
        
        Args:
            code: Google authorization code
            
        Returns:
            Access token
        """
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            logger.error("Google OAuth credentials not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured"
            )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.error(f"Google token exchange error: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to exchange Google code for token"
                )
            
            data = response.json()
            return data.get("access_token")

    # ========== GitHub OAuth ==========
    @staticmethod
    async def get_github_user_info(access_token: str) -> Dict[str, Any]:
        """
        Get user info from GitHub using access token.
        
        Args:
            access_token: GitHub OAuth access token
            
        Returns:
            Dict with user info (id, login, name, avatar_url, email)
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.error(f"GitHub userinfo error: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to get GitHub user info"
                )
            
            user_info = response.json()
            
            # Get email if not in main response
            if not user_info.get("email"):
                email_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"token {access_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    timeout=10.0
                )
                
                if email_response.status_code == 200:
                    emails = email_response.json()
                    # Get primary email or first verified email
                    for email_obj in emails:
                        if email_obj.get("primary"):
                            user_info["email"] = email_obj["email"]
                            break
                    if not user_info.get("email") and emails:
                        user_info["email"] = emails[0].get("email")
            
            return user_info

    @staticmethod
    async def exchange_github_code(code: str) -> str:
        """
        Exchange GitHub authorization code for access token.
        
        Args:
            code: GitHub authorization code
            
        Returns:
            Access token
        """
        if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
            logger.error("GitHub OAuth credentials not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GitHub OAuth not configured"
            )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI,
                },
                headers={"Accept": "application/json"},
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.error(f"GitHub token exchange error: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to exchange GitHub code for token"
                )
            
            data = response.json()
            
            if "error" in data:
                logger.error(f"GitHub error: {data['error']}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=data.get("error_description", "GitHub authentication failed")
                )
            
            return data.get("access_token")

    # ========== User Management ==========
    @staticmethod
    def find_or_create_student(
        db: Session,
        email: str,
        oauth_provider: str,
        oauth_id: str,
        name: str,
        profile_image: Optional[str] = None,
    ) -> Tuple[Student, bool]:
        """
        Find existing student by OAuth ID or email, or create new one.
        
        Args:
            db: Database session
            email: User email
            oauth_provider: 'google' or 'github'
            oauth_id: Provider's user ID
            name: User's full name
            profile_image: User's profile picture URL
            
        Returns:
            Tuple of (User, is_new_user)
        """
        # First, check if user exists by OAuth ID
        student = db.query(Student).filter(
            Student.oauth_id == oauth_id,
            Student.oauth_provider == oauth_provider
        ).first()
        
        if student:
            # Update last login
            student.last_login = datetime.utcnow()
            if profile_image and not student.profile_image:
                student.profile_image = profile_image
            db.commit()
            return student, False
        
        # Check if user exists by email and link OAuth
        student = db.query(Student).filter(Student.email == email).first()
        
        if student:
            # Link OAuth to existing user
            student.oauth_provider = oauth_provider
            student.oauth_id = oauth_id
            student.last_login = datetime.utcnow()
            if profile_image and not student.profile_image:
                student.profile_image = profile_image
            db.commit()
            logger.info(f"Linked {oauth_provider} OAuth to existing student: {email}")
            return student, False
        
        # Create new student user
        new_student = Student(
            email=email,
            name=name,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
            profile_image=profile_image,
            status=UserStatus.ACTIVE,
            last_login=datetime.utcnow(),
            # Set a default roll number from email
            roll_no=email.split("@")[0].upper()[:20],
        )
        
        db.add(new_student)
        db.commit()
        db.refresh(new_student)
        
        logger.info(f"Created new student via {oauth_provider} OAuth: {email}")
        return new_student, True

    @staticmethod
    def find_or_create_teacher(
        db: Session,
        email: str,
        oauth_provider: str,
        oauth_id: str,
        name: str,
        profile_image: Optional[str] = None,
    ) -> Tuple[Teacher, bool]:
        """
        Find existing teacher by OAuth ID or email, or create new one.
        
        Args:
            db: Database session
            email: User email
            oauth_provider: 'google' or 'github'
            oauth_id: Provider's user ID
            name: User's full name
            profile_image: User's profile picture URL
            
        Returns:
            Tuple of (User, is_new_user)
        """
        # Check if user exists by OAuth ID
        teacher = db.query(Teacher).filter(
            Teacher.oauth_id == oauth_id,
            Teacher.oauth_provider == oauth_provider
        ).first()
        
        if teacher:
            teacher.last_login = datetime.utcnow()
            if profile_image and not teacher.profile_image:
                teacher.profile_image = profile_image
            db.commit()
            return teacher, False
        
        # Check if user exists by email and link OAuth
        teacher = db.query(Teacher).filter(Teacher.email == email).first()
        
        if teacher:
            teacher.oauth_provider = oauth_provider
            teacher.oauth_id = oauth_id
            teacher.last_login = datetime.utcnow()
            if profile_image and not teacher.profile_image:
                teacher.profile_image = profile_image
            db.commit()
            logger.info(f"Linked {oauth_provider} OAuth to existing teacher: {email}")
            return teacher, False
        
        # Create new teacher user
        new_teacher = Teacher(
            email=email,
            name=name,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
            profile_image=profile_image,
            status=UserStatus.ACTIVE,
            last_login=datetime.utcnow(),
        )
        
        db.add(new_teacher)
        db.commit()
        db.refresh(new_teacher)
        
        logger.info(f"Created new teacher via {oauth_provider} OAuth: {email}")
        return new_teacher, True

    @staticmethod
    def find_or_create_admin(
        db: Session,
        email: str,
        oauth_provider: str,
        oauth_id: str,
        name: str,
        profile_image: Optional[str] = None,
    ) -> Tuple[Admin, bool]:
        """
        Find existing admin by OAuth ID or email, or create new one.
        Note: Admin creation via OAuth is restricted and requires existing account.
        
        Args:
            db: Database session
            email: User email
            oauth_provider: 'google' or 'github'
            oauth_id: Provider's user ID
            name: User's full name
            profile_image: User's profile picture URL
            
        Returns:
            Tuple of (User, is_new_user) or raises 403
        """
        # Check if user exists by OAuth ID
        admin = db.query(Admin).filter(
            Admin.oauth_id == oauth_id,
            Admin.oauth_provider == oauth_provider
        ).first()
        
        if admin:
            admin.last_login = datetime.utcnow()
            if profile_image and not admin.profile_image:
                admin.profile_image = profile_image
            db.commit()
            return admin, False
        
        # Check if user exists by email and link OAuth
        admin = db.query(Admin).filter(Admin.email == email).first()
        
        if admin:
            admin.oauth_provider = oauth_provider
            admin.oauth_id = oauth_id
            admin.last_login = datetime.utcnow()
            if profile_image and not admin.profile_image:
                admin.profile_image = profile_image
            db.commit()
            logger.info(f"Linked {oauth_provider} OAuth to existing admin: {email}")
            return admin, False
        
        # Don't auto-create admin users via OAuth
        logger.warning(f"Attempted to create admin via OAuth: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts cannot be created via OAuth"
        )

    # ========== Google Authentication Flow ==========
    @staticmethod
    async def handle_google_oauth(
        code: str,
        db: Session,
        role: str = "student",
    ) -> Dict[str, Any]:
        """
        Handle Google OAuth callback.
        
        Args:
            code: Google authorization code
            db: Database session
            role: Target role (student, teacher, admin)
            
        Returns:
            Dict with tokens and user info
        """
        try:
            # Exchange code for access token
            access_token = await OAuthService.exchange_google_code(code)
            
            # Get user info
            google_user = await OAuthService.get_google_user_info(access_token)
            
            email = google_user.get("email")
            name = google_user.get("name", email.split("@")[0])
            oauth_id = str(google_user.get("id"))
            picture = google_user.get("picture")
            
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not get email from Google"
                )
            
            # Create or find user based on role
            if role == "admin":
                user, _ = OAuthService.find_or_create_admin(
                    db, email, "google", oauth_id, name, picture
                )
                user_id = user.id
                user_unique_id = user.admin_id
            elif role == "teacher":
                user, _ = OAuthService.find_or_create_teacher(
                    db, email, "google", oauth_id, name, picture
                )
                user_id = user.id
                user_unique_id = user.teacher_id
            else:  # student
                user, _ = OAuthService.find_or_create_student(
                    db, email, "google", oauth_id, name, picture
                )
                user_id = user.id
                user_unique_id = user.student_id
            
            # Create JWT tokens
            tokens = create_tokens(
                user_id=user_id,
                user_unique_id=user_unique_id,
                email=email,
                name=name,
                role=role,
            )
            
            return {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": user_id,
                    "unique_id": user_unique_id,
                    "email": email,
                    "name": name,
                    "role": role,
                    "profile_image": picture,
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Google OAuth error: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)  # Return actual error message for logging
            )

    # ========== GitHub Authentication Flow ==========
    @staticmethod
    async def handle_github_oauth(
        code: str,
        db: Session,
        role: str = "student",
    ) -> Dict[str, Any]:
        """
        Handle GitHub OAuth callback.
        
        Args:
            code: GitHub authorization code
            db: Database session
            role: Target role (student, teacher, admin)
            
        Returns:
            Dict with tokens and user info
        """
        try:
            # Exchange code for access token
            access_token = await OAuthService.exchange_github_code(code)
            
            # Get user info
            github_user = await OAuthService.get_github_user_info(access_token)
            
            email = github_user.get("email")
            name = github_user.get("name") or github_user.get("login")
            oauth_id = str(github_user.get("id"))
            avatar = github_user.get("avatar_url")
            
            if not email or not name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not get email/name from GitHub"
                )
            
            # Create or find user based on role
            if role == "admin":
                user, _ = OAuthService.find_or_create_admin(
                    db, email, "github", oauth_id, name, avatar
                )
                user_id = user.id
                user_unique_id = user.admin_id
            elif role == "teacher":
                user, _ = OAuthService.find_or_create_teacher(
                    db, email, "github", oauth_id, name, avatar
                )
                user_id = user.id
                user_unique_id = user.teacher_id
            else:  # student
                user, _ = OAuthService.find_or_create_student(
                    db, email, "github", oauth_id, name, avatar
                )
                user_id = user.id
                user_unique_id = user.student_id
            
            # Create JWT tokens
            tokens = create_tokens(
                user_id=user_id,
                user_unique_id=user_unique_id,
                email=email,
                name=name,
                role=role,
            )
            
            return {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": user_id,
                    "unique_id": user_unique_id,
                    "email": email,
                    "name": name,
                    "role": role,
                    "profile_image": avatar,
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"GitHub OAuth error: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)  # Return actual error message for logging
            )


# Global instance
oauth_service = OAuthService()
