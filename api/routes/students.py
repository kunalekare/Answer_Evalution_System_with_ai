"""
Student Routes - AssessIQ
==========================
API endpoints for student operations.

Endpoints:
- GET /student/dashboard - Student dashboard
- GET /student/evaluations - View own evaluations
- GET /student/profile - View/update profile
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database.models import (
    get_db, Student, Evaluation, ManualEvaluation, Class, Subject,
    UserStatus
)
from api.services.auth_service import (
    get_current_user, get_current_student, TokenData, hash_password
)

logger = logging.getLogger("AssessIQ.Student")

router = APIRouter()


# ========== Request/Response Models ==========
class UpdateProfileRequest(BaseModel):
    """Update profile request."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str


# ========== Dashboard ==========
@router.get("/dashboard")
async def student_dashboard(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get student dashboard with stats and recent evaluations.
    """
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")
    
    student = db.query(Student).filter(Student.id == current_user.user_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get evaluation stats
    total_evaluations = db.query(func.count(Evaluation.id)).filter(
        Evaluation.student_id == student.id
    ).scalar() or 0
    
    avg_score = db.query(func.avg(Evaluation.final_score)).filter(
        Evaluation.student_id == student.id
    ).scalar() or 0
    
    highest_score = db.query(func.max(Evaluation.final_score)).filter(
        Evaluation.student_id == student.id
    ).scalar() or 0
    
    lowest_score = db.query(func.min(Evaluation.final_score)).filter(
        Evaluation.student_id == student.id
    ).scalar() or 0
    
    # Grade distribution
    from database.models import GradeLevel
    grade_dist = {}
    for grade in GradeLevel:
        count = db.query(func.count(Evaluation.id)).filter(
            Evaluation.student_id == student.id,
            Evaluation.grade == grade
        ).scalar() or 0
        grade_dist[grade.value] = count
    
    # Recent evaluations
    recent_evals = db.query(Evaluation).filter(
        Evaluation.student_id == student.id
    ).order_by(desc(Evaluation.created_at)).limit(10).all()
    
    # Class info
    class_info = None
    if student.class_info:
        class_info = student.class_info.to_dict()
    
    return {
        "success": True,
        "data": {
            "student": student.to_dict(),
            "class": class_info,
            "statistics": {
                "total_evaluations": total_evaluations,
                "average_score": round(avg_score, 2) if avg_score else 0,
                "highest_score": round(highest_score, 2) if highest_score else 0,
                "lowest_score": round(lowest_score, 2) if lowest_score else 0,
                "grade_distribution": grade_dist
            },
            "recent_evaluations": [e.to_dict() for e in recent_evals]
        }
    }


# ========== Evaluations ==========
@router.get("/evaluations")
async def list_student_evaluations(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    subject_id: Optional[str] = None
):
    """
    Get all evaluations for this student.
    """
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")
    
    student = db.query(Student).filter(Student.id == current_user.user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    query = db.query(Evaluation).filter(Evaluation.student_id == student.id)
    
    if subject_id:
        subject = db.query(Subject).filter(Subject.subject_id == subject_id).first()
        if subject:
            query = query.filter(Evaluation.subject_id == subject.id)
    
    total = query.count()
    offset = (page - 1) * limit
    evaluations = query.order_by(desc(Evaluation.created_at)).offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "data": {
            "evaluations": [e.to_dict() for e in evaluations],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    }


@router.get("/evaluations/{evaluation_id}")
async def get_evaluation_details(
    evaluation_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed evaluation result.
    """
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")
    
    student = db.query(Student).filter(Student.id == current_user.user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    evaluation = db.query(Evaluation).filter(
        Evaluation.evaluation_id == evaluation_id,
        Evaluation.student_id == student.id
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    return {
        "success": True,
        "data": evaluation.to_dict()
    }


# ========== Manual Evaluations ==========
@router.get("/manual-evaluations")
async def list_manual_evaluations(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get all manual evaluations for this student.
    """
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")
    
    student = db.query(Student).filter(Student.id == current_user.user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    query = db.query(ManualEvaluation).filter(ManualEvaluation.student_id == student.id)
    
    total = query.count()
    offset = (page - 1) * limit
    evaluations = query.order_by(desc(ManualEvaluation.created_at)).offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "data": {
            "evaluations": [e.to_dict() for e in evaluations],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    }


# ========== Profile ==========
@router.get("/profile")
async def get_profile(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get student profile.
    """
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")
    
    student = db.query(Student).filter(Student.id == current_user.user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    profile = student.to_dict()
    
    # Add class info
    if student.class_info:
        profile["class_details"] = student.class_info.to_dict()
    
    # Add teacher info
    if student.teacher:
        profile["teacher_details"] = {
            "name": student.teacher.name,
            "email": student.teacher.email,
            "department": student.teacher.department
        }
    
    return {
        "success": True,
        "data": profile
    }


@router.put("/profile")
async def update_profile(
    update_data: UpdateProfileRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update student profile (limited fields).
    """
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")
    
    student = db.query(Student).filter(Student.id == current_user.user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if update_data.name is not None:
        student.name = update_data.name
    if update_data.email is not None:
        # Check email uniqueness
        existing = db.query(Student).filter(
            Student.email == update_data.email,
            Student.id != student.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        student.email = update_data.email
    if update_data.phone is not None:
        student.phone = update_data.phone
    if update_data.address is not None:
        student.address = update_data.address
    if update_data.gender is not None:
        student.gender = update_data.gender
    if update_data.date_of_birth is not None:
        try:
            student.date_of_birth = datetime.fromisoformat(update_data.date_of_birth)
        except:
            pass
    
    student.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(student)
    
    return {
        "success": True,
        "message": "Profile updated successfully",
        "data": student.to_dict()
    }


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change student password.
    """
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")
    
    student = db.query(Student).filter(Student.id == current_user.user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify current password
    from api.services.auth_service import verify_password
    if not student.password_hash or not verify_password(password_data.current_password, student.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    student.password_hash = hash_password(password_data.new_password)
    student.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }


# ========== Performance Analytics ==========
@router.get("/analytics")
async def get_performance_analytics(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get performance analytics for the student.
    """
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")
    
    student = db.query(Student).filter(Student.id == current_user.user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get all evaluations
    evaluations = db.query(Evaluation).filter(
        Evaluation.student_id == student.id
    ).order_by(Evaluation.created_at).all()
    
    if not evaluations:
        return {
            "success": True,
            "data": {
                "message": "No evaluations found",
                "trends": [],
                "subject_performance": [],
                "improvement_areas": []
            }
        }
    
    # Score trend over time
    trends = [
        {
            "date": e.created_at.isoformat() if e.created_at else None,
            "score": e.final_score,
            "subject": e.subject_ref.name if e.subject_ref else None
        }
        for e in evaluations
    ]
    
    # Performance by subject
    subject_scores = {}
    for e in evaluations:
        subject_name = e.subject_ref.name if e.subject_ref else "Unknown"
        if subject_name not in subject_scores:
            subject_scores[subject_name] = []
        subject_scores[subject_name].append(e.final_score or 0)
    
    subject_performance = [
        {
            "subject": subject,
            "average_score": round(sum(scores) / len(scores), 2),
            "total_evaluations": len(scores)
        }
        for subject, scores in subject_scores.items()
    ]
    
    # Identify improvement areas (subjects with lower scores)
    improvement_areas = sorted(subject_performance, key=lambda x: x["average_score"])[:3]
    
    return {
        "success": True,
        "data": {
            "trends": trends,
            "subject_performance": sorted(subject_performance, key=lambda x: -x["average_score"]),
            "improvement_areas": improvement_areas,
            "total_evaluations": len(evaluations),
            "overall_average": round(sum(e.final_score or 0 for e in evaluations) / len(evaluations), 2)
        }
    }
