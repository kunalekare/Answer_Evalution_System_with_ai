"""
Authentication Service - AssessIQ
==================================
JWT-based authentication for Admin, Teacher, and Student roles.

Features:
- Password hashing with bcrypt
- JWT token generation and validation
- Role-based access control
- Refresh token management
"""

import os
import logging
import bcrypt as bcrypt_lib
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from database.models import (
    Admin, Teacher, Student, RefreshToken, ActivityLog,
    UserRole, UserStatus, ActivityType,
    get_db, SessionLocal
)
from config.settings import settings

logger = logging.getLogger("AssessIQ.Auth")

# ========== Security Configuration ==========
# Secret key for JWT - should be in environment variable in production
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "assessiq-secret-key-2026")[:64]  # Limit key length
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 7

# HTTP Bearer security scheme
security = HTTPBearer()


# ========== Pydantic Models ==========
class TokenData(BaseModel):
    """Token payload data."""
    user_id: int
    user_unique_id: str  # admin_id, teacher_id, or student_id
    email: str
    name: str
    role: str
    exp: Optional[datetime] = None


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str
    role: str  # "admin", "teacher", "student"


class RegisterRequest(BaseModel):
    """Registration request model."""
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Change password request model."""
    old_password: str
    new_password: str


# ========== Password Utilities ==========
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt_lib.gensalt(rounds=12)
    hashed = bcrypt_lib.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt_lib.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# ========== JWT Utilities ==========
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None


# ========== Authentication Service ==========
class AuthService:
    """
    Authentication Service
    -----------------------
    Handles user authentication, token management, and session tracking.
    """
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    def get_db_session(self) -> Session:
        """Get a new database session."""
        return SessionLocal()
    
    # ===== User Authentication =====
    def authenticate_user(
        self, 
        email: str, 
        password: str, 
        role: str,
        ip_address: Optional[str] = None
    ) -> Tuple[Optional[Any], Optional[str]]:
        """
        Authenticate a user by email and password.
        
        Returns:
            Tuple of (user_object, error_message)
        """
        db = self.get_db_session()
        try:
            user = None
            
            if role == "admin":
                user = db.query(Admin).filter(Admin.email == email).first()
            elif role == "teacher":
                user = db.query(Teacher).filter(Teacher.email == email).first()
            elif role == "student":
                user = db.query(Student).filter(Student.email == email).first()
            else:
                return None, "Invalid role specified"
            
            if not user:
                return None, "User not found"
            
            # Check if user has password (students might not have login enabled)
            if not user.password_hash:
                return None, "Login not enabled for this account"
            
            # Verify password
            if not verify_password(password, user.password_hash):
                return None, "Invalid password"
            
            # Check user status
            if hasattr(user, 'status') and user.status != UserStatus.ACTIVE:
                return None, f"Account is {user.status.value}"
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            
            # Log activity
            self._log_activity(
                db=db,
                user_id=user.id,
                user_role=UserRole(role),
                activity_type=ActivityType.LOGIN,
                action="user_login",
                resource_type=role,
                resource_id=getattr(user, f"{role}_id", str(user.id)),
                ip_address=ip_address
            )
            
            return user, None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            db.rollback()
            return None, str(e)
        finally:
            db.close()
    
    def login(
        self, 
        email: str, 
        password: str, 
        role: str,
        ip_address: Optional[str] = None
    ) -> Tuple[Optional[Token], Optional[str]]:
        """
        Login a user and generate tokens.
        
        Returns:
            Tuple of (Token object, error_message)
        """
        user, error = self.authenticate_user(email, password, role, ip_address)
        
        if error:
            return None, error
        
        # Create token payload
        user_unique_id = getattr(user, f"{role}_id", str(user.id))
        token_data = {
            "sub": str(user.id),
            "user_id": user.id,
            "user_unique_id": user_unique_id,
            "email": user.email,
            "name": user.name,
            "role": role
        }
        
        # Generate tokens
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Store refresh token in database
        db = self.get_db_session()
        try:
            token_record = RefreshToken(
                token=refresh_token,
                user_id=user.id,
                user_role=UserRole(role),
                expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            )
            db.add(token_record)
            db.commit()
        except Exception as e:
            logger.error(f"Error storing refresh token: {e}")
            db.rollback()
        finally:
            db.close()
        
        # Prepare user data for response
        user_data = user.to_dict() if hasattr(user, 'to_dict') else {
            "id": user_unique_id,
            "email": user.email,
            "name": user.name,
            "role": role
        }
        user_data["role"] = role
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_data
        ), None
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Refresh an access token using a refresh token.
        
        Returns:
            Tuple of (new_access_token, error_message)
        """
        # Decode refresh token
        payload = decode_token(refresh_token)
        if not payload:
            return None, "Invalid refresh token"
        
        if payload.get("type") != "refresh":
            return None, "Invalid token type"
        
        # Check if refresh token is revoked
        db = self.get_db_session()
        try:
            token_record = db.query(RefreshToken).filter(
                RefreshToken.token == refresh_token,
                RefreshToken.is_revoked == False
            ).first()
            
            if not token_record:
                return None, "Refresh token not found or revoked"
            
            if token_record.expires_at < datetime.utcnow():
                return None, "Refresh token expired"
            
            # Create new access token
            token_data = {
                "sub": payload.get("sub"),
                "user_id": payload.get("user_id"),
                "user_unique_id": payload.get("user_unique_id"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "role": payload.get("role")
            }
            
            new_access_token = create_access_token(token_data)
            return new_access_token, None
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None, str(e)
        finally:
            db.close()
    
    def logout(self, refresh_token: str) -> bool:
        """Revoke a refresh token (logout)."""
        db = self.get_db_session()
        try:
            token_record = db.query(RefreshToken).filter(
                RefreshToken.token == refresh_token
            ).first()
            
            if token_record:
                token_record.is_revoked = True
                token_record.revoked_at = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def logout_all(self, user_id: int, user_role: str) -> int:
        """Revoke all refresh tokens for a user."""
        db = self.get_db_session()
        try:
            count = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.user_role == UserRole(user_role),
                RefreshToken.is_revoked == False
            ).update({
                "is_revoked": True,
                "revoked_at": datetime.utcnow()
            })
            db.commit()
            return count
        except Exception as e:
            logger.error(f"Error revoking all tokens: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    # ===== User Registration =====
    def register_admin(self, data: RegisterRequest, created_by: Optional[int] = None) -> Tuple[Optional[Admin], Optional[str]]:
        """Register a new admin (super admin only)."""
        db = self.get_db_session()
        try:
            # Check if email exists
            existing = db.query(Admin).filter(Admin.email == data.email).first()
            if existing:
                return None, "Email already registered"
            
            admin = Admin(
                email=data.email,
                password_hash=hash_password(data.password),
                name=data.name,
                phone=data.phone,
                is_super_admin=False
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            
            return admin, None
        except Exception as e:
            logger.error(f"Error registering admin: {e}")
            db.rollback()
            return None, str(e)
        finally:
            db.close()
    
    def register_teacher(
        self, 
        data: dict, 
        created_by: int
    ) -> Tuple[Optional[Teacher], Optional[str]]:
        """Register a new teacher (admin only)."""
        db = self.get_db_session()
        try:
            # Check if email exists
            existing = db.query(Teacher).filter(Teacher.email == data.get("email")).first()
            if existing:
                return None, "Email already registered"
            
            teacher = Teacher(
                email=data.get("email"),
                password_hash=hash_password(data.get("password")),
                name=data.get("name"),
                phone=data.get("phone"),
                employee_id=data.get("employee_id"),
                department=data.get("department"),
                designation=data.get("designation"),
                created_by=created_by
            )
            db.add(teacher)
            db.commit()
            db.refresh(teacher)
            
            # Log activity
            self._log_activity(
                db=db,
                admin_id=created_by,
                user_role=UserRole.ADMIN,
                activity_type=ActivityType.CREATE,
                action="created_teacher",
                resource_type="teacher",
                resource_id=teacher.teacher_id
            )
            
            return teacher, None
        except Exception as e:
            logger.error(f"Error registering teacher: {e}")
            db.rollback()
            return None, str(e)
        finally:
            db.close()
    
    def register_student(
        self, 
        data: dict, 
        teacher_id: int
    ) -> Tuple[Optional[Student], Optional[str]]:
        """Register a new student (teacher only)."""
        db = self.get_db_session()
        try:
            # Check if email exists (if provided)
            if data.get("email"):
                existing = db.query(Student).filter(Student.email == data.get("email")).first()
                if existing:
                    return None, "Email already registered"
            
            student = Student(
                roll_no=data.get("roll_no"),
                enrollment_no=data.get("enrollment_no"),
                email=data.get("email"),
                password_hash=hash_password(data.get("password")) if data.get("password") else None,
                name=data.get("name"),
                phone=data.get("phone"),
                gender=data.get("gender"),
                date_of_birth=data.get("date_of_birth"),
                address=data.get("address"),
                class_id=data.get("class_id"),
                teacher_id=teacher_id,
                academic_year=data.get("academic_year")
            )
            db.add(student)
            db.commit()
            db.refresh(student)
            
            # Log activity
            self._log_activity(
                db=db,
                teacher_id=teacher_id,
                user_role=UserRole.TEACHER,
                activity_type=ActivityType.CREATE,
                action="created_student",
                resource_type="student",
                resource_id=student.student_id
            )
            
            return student, None
        except Exception as e:
            logger.error(f"Error registering student: {e}")
            db.rollback()
            return None, str(e)
        finally:
            db.close()
    
    # ===== Password Management =====
    def change_password(
        self, 
        user_id: int, 
        role: str, 
        old_password: str, 
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """Change user password."""
        db = self.get_db_session()
        try:
            user = None
            
            if role == "admin":
                user = db.query(Admin).filter(Admin.id == user_id).first()
            elif role == "teacher":
                user = db.query(Teacher).filter(Teacher.id == user_id).first()
            elif role == "student":
                user = db.query(Student).filter(Student.id == user_id).first()
            
            if not user:
                return False, "User not found"
            
            if not verify_password(old_password, user.password_hash):
                return False, "Current password is incorrect"
            
            user.password_hash = hash_password(new_password)
            db.commit()
            
            # Revoke all refresh tokens (force re-login)
            self.logout_all(user_id, role)
            
            return True, None
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            db.rollback()
            return False, str(e)
        finally:
            db.close()
    
    def reset_password(
        self, 
        user_id: int, 
        role: str, 
        new_password: str,
        admin_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """Reset user password (admin only)."""
        db = self.get_db_session()
        try:
            user = None
            
            if role == "admin":
                user = db.query(Admin).filter(Admin.id == user_id).first()
            elif role == "teacher":
                user = db.query(Teacher).filter(Teacher.id == user_id).first()
            elif role == "student":
                user = db.query(Student).filter(Student.id == user_id).first()
            
            if not user:
                return False, "User not found"
            
            user.password_hash = hash_password(new_password)
            db.commit()
            
            # Revoke all refresh tokens
            self.logout_all(user_id, role)
            
            return True, None
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            db.rollback()
            return False, str(e)
        finally:
            db.close()
    
    # ===== Activity Logging =====
    def _log_activity(
        self,
        db: Session,
        activity_type: ActivityType,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        admin_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        student_id: Optional[int] = None,
        user_id: Optional[int] = None,
        user_role: Optional[UserRole] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None
    ):
        """Log an activity."""
        try:
            # Determine user IDs based on role
            if user_role == UserRole.ADMIN and user_id:
                admin_id = user_id
            elif user_role == UserRole.TEACHER and user_id:
                teacher_id = user_id
            elif user_role == UserRole.STUDENT and user_id:
                student_id = user_id
            
            log = ActivityLog(
                admin_id=admin_id,
                teacher_id=teacher_id,
                student_id=student_id,
                user_role=user_role,
                activity_type=activity_type,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging activity: {e}")


# ========== FastAPI Dependencies ==========
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> TokenData:
    """
    Dependency to get the current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise credentials_exception
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    return TokenData(
        user_id=payload.get("user_id"),
        user_unique_id=payload.get("user_unique_id"),
        email=payload.get("email"),
        name=payload.get("name"),
        role=payload.get("role"),
        exp=datetime.fromtimestamp(payload.get("exp")) if payload.get("exp") else None
    )


async def get_current_admin(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Dependency to ensure user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_teacher(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Dependency to ensure user is a teacher."""
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )
    return current_user


async def get_current_teacher_only(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Dependency to ensure user is strictly a teacher."""
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )
    return current_user


async def get_current_student(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Dependency to ensure user is a student."""
    if current_user.role not in ["admin", "teacher", "student"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required"
        )
    return current_user


# ========== Utility Functions ==========
def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# ========== Create Default Admin ==========
def create_default_admin():
    """Create a default super admin if none exists."""
    db = SessionLocal()
    try:
        existing = db.query(Admin).filter(Admin.is_super_admin == True).first()
        if not existing:
            admin = Admin(
                email="admin@assessiq.com",
                password_hash=hash_password("admin123"),
                name="Super Admin",
                is_super_admin=True,
                status=UserStatus.ACTIVE
            )
            db.add(admin)
            db.commit()
            logger.info("Created default super admin: admin@assessiq.com / admin123")
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")
        db.rollback()
    finally:
        db.close()


# Create singleton auth service
auth_service = AuthService()
