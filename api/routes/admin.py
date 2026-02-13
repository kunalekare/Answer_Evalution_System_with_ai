"""
Admin Routes - AssessIQ
========================
API endpoints for admin management.

Endpoints:
- GET /admin/dashboard - Admin dashboard stats
- GET /admin/teachers - List all teachers
- POST /admin/teachers - Create a teacher
- GET /admin/teachers/{id} - Get teacher details
- PUT /admin/teachers/{id} - Update teacher
- DELETE /admin/teachers/{id} - Delete teacher
- GET /admin/activity-logs - View activity logs
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database.models import (
    get_db, Admin, Teacher, Student, Class, Subject, 
    Evaluation, ManualEvaluation, ActivityLog,
    UserStatus, UserRole
)
from api.services.auth_service import (
    auth_service, get_current_admin, TokenData, hash_password
)

logger = logging.getLogger("AssessIQ.Admin")

router = APIRouter()


# ========== Request/Response Models ==========
class CreateTeacherRequest(BaseModel):
    """Create teacher request."""
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "teacher@example.com",
                "password": "teacher123",
                "name": "John Smith",
                "phone": "9876543210",
                "employee_id": "EMP001",
                "department": "Computer Science",
                "designation": "Assistant Professor"
            }
        }


class UpdateTeacherRequest(BaseModel):
    """Update teacher request."""
    name: Optional[str] = None
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    status: Optional[str] = None  # "active", "inactive", "suspended"


class ResetPasswordRequest(BaseModel):
    """Reset password request."""
    new_password: str


# ========== Dashboard ==========
@router.get("/dashboard")
async def admin_dashboard(
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get admin dashboard statistics.
    """
    # Get counts
    total_teachers = db.query(func.count(Teacher.id)).filter(
        Teacher.status == UserStatus.ACTIVE
    ).scalar() or 0
    
    total_students = db.query(func.count(Student.id)).filter(
        Student.status == UserStatus.ACTIVE
    ).scalar() or 0
    
    total_classes = db.query(func.count(Class.id)).filter(
        Class.is_active == True
    ).scalar() or 0
    
    total_subjects = db.query(func.count(Subject.id)).filter(
        Subject.is_active == True
    ).scalar() or 0
    
    total_evaluations = db.query(func.count(Evaluation.id)).scalar() or 0
    
    total_manual_evals = db.query(func.count(ManualEvaluation.id)).scalar() or 0
    
    avg_score = db.query(func.avg(Evaluation.final_score)).scalar() or 0
    
    # Recent activities
    recent_activities = db.query(ActivityLog).order_by(
        desc(ActivityLog.created_at)
    ).limit(10).all()
    
    # Recent teachers
    recent_teachers = db.query(Teacher).order_by(
        desc(Teacher.created_at)
    ).limit(5).all()
    
    return {
        "success": True,
        "data": {
            "statistics": {
                "total_teachers": total_teachers,
                "total_students": total_students,
                "total_classes": total_classes,
                "total_subjects": total_subjects,
                "total_evaluations": total_evaluations,
                "total_manual_evaluations": total_manual_evals,
                "average_score": round(avg_score, 2) if avg_score else 0
            },
            "recent_activities": [a.to_dict() for a in recent_activities],
            "recent_teachers": [t.to_dict() for t in recent_teachers]
        }
    }


# ========== Teacher Management ==========
@router.get("/teachers")
async def list_teachers(
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None
):
    """
    List all teachers with pagination and filters.
    """
    query = db.query(Teacher)
    
    # Apply filters
    if status:
        query = query.filter(Teacher.status == UserStatus(status))
    
    if department:
        query = query.filter(Teacher.department.ilike(f"%{department}%"))
    
    if search:
        query = query.filter(
            (Teacher.name.ilike(f"%{search}%")) |
            (Teacher.email.ilike(f"%{search}%")) |
            (Teacher.employee_id.ilike(f"%{search}%"))
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    teachers = query.order_by(desc(Teacher.created_at)).offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "data": {
            "teachers": [t.to_dict() for t in teachers],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    }


@router.post("/teachers", status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_data: CreateTeacherRequest,
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new teacher.
    """
    # Check if email exists
    existing = db.query(Teacher).filter(Teacher.email == teacher_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if employee_id exists
    if teacher_data.employee_id:
        existing = db.query(Teacher).filter(
            Teacher.employee_id == teacher_data.employee_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )
    
    # Create teacher
    teacher = Teacher(
        email=teacher_data.email,
        password_hash=hash_password(teacher_data.password),
        name=teacher_data.name,
        phone=teacher_data.phone,
        employee_id=teacher_data.employee_id,
        department=teacher_data.department,
        designation=teacher_data.designation,
        created_by=current_user.user_id
    )
    
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    
    logger.info(f"Teacher created: {teacher.teacher_id} by admin {current_user.user_id}")
    
    return {
        "success": True,
        "message": "Teacher created successfully",
        "data": teacher.to_dict()
    }


@router.get("/teachers/{teacher_id}")
async def get_teacher(
    teacher_id: str,
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get teacher details by ID.
    """
    teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Get additional stats
    student_count = db.query(func.count(Student.id)).filter(
        Student.teacher_id == teacher.id
    ).scalar() or 0
    
    class_count = db.query(func.count(Class.id)).filter(
        Class.teacher_id == teacher.id
    ).scalar() or 0
    
    evaluation_count = db.query(func.count(Evaluation.id)).filter(
        Evaluation.teacher_id == teacher.id
    ).scalar() or 0
    
    teacher_data = teacher.to_dict()
    teacher_data["stats"] = {
        "student_count": student_count,
        "class_count": class_count,
        "evaluation_count": evaluation_count
    }
    
    return {
        "success": True,
        "data": teacher_data
    }


@router.put("/teachers/{teacher_id}")
async def update_teacher(
    teacher_id: str,
    update_data: UpdateTeacherRequest,
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update teacher details.
    """
    teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Update fields
    if update_data.name is not None:
        teacher.name = update_data.name
    if update_data.phone is not None:
        teacher.phone = update_data.phone
    if update_data.employee_id is not None:
        # Check uniqueness
        existing = db.query(Teacher).filter(
            Teacher.employee_id == update_data.employee_id,
            Teacher.id != teacher.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )
        teacher.employee_id = update_data.employee_id
    if update_data.department is not None:
        teacher.department = update_data.department
    if update_data.designation is not None:
        teacher.designation = update_data.designation
    if update_data.status is not None:
        teacher.status = UserStatus(update_data.status)
    
    teacher.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(teacher)
    
    logger.info(f"Teacher updated: {teacher_id} by admin {current_user.user_id}")
    
    return {
        "success": True,
        "message": "Teacher updated successfully",
        "data": teacher.to_dict()
    }


@router.delete("/teachers/{teacher_id}")
async def delete_teacher(
    teacher_id: str,
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a teacher (soft delete - set status to inactive).
    """
    teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Soft delete
    teacher.status = UserStatus.INACTIVE
    teacher.updated_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Teacher deleted: {teacher_id} by admin {current_user.user_id}")
    
    return {
        "success": True,
        "message": "Teacher deleted successfully"
    }


@router.post("/teachers/{teacher_id}/reset-password")
async def reset_teacher_password(
    teacher_id: str,
    password_data: ResetPasswordRequest,
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Reset teacher's password.
    """
    teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    success, error = auth_service.reset_password(
        user_id=teacher.id,
        role="teacher",
        new_password=password_data.new_password,
        admin_id=current_user.user_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {
        "success": True,
        "message": "Password reset successfully"
    }


# ========== Activity Logs ==========
@router.get("/activity-logs")
async def get_activity_logs(
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user_role: Optional[str] = None,
    activity_type: Optional[str] = None
):
    """
    Get activity logs with pagination.
    """
    query = db.query(ActivityLog)
    
    if user_role:
        query = query.filter(ActivityLog.user_role == UserRole(user_role))
    
    if activity_type:
        from database.models import ActivityType
        query = query.filter(ActivityLog.activity_type == ActivityType(activity_type))
    
    total = query.count()
    offset = (page - 1) * limit
    logs = query.order_by(desc(ActivityLog.created_at)).offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "data": {
            "logs": [log.to_dict() for log in logs],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    }
