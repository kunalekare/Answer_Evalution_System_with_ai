"""
Grievance Routes - AssessIQ
============================
API endpoints for grievance/complaint handling system.

Features:
- Students raise grievances to teachers
- Teachers can resolve, reject, or escalate to admin
- Admin handles escalated grievances
- Status tracking and response system

Workflow:
1. Student submits complaint
2. Teacher reviews complaint
3. Teacher: Resolve ✅ | Reject ❌ | Escalate ⬆ to Admin
4. Admin handles escalated complaint

Status: Pending → In Review → Resolved/Rejected/Escalated

Endpoints:
- GET /grievance - List grievances
- POST /grievance - Create grievance
- GET /grievance/{id} - Get grievance details
- PUT /grievance/{id}/status - Update status
- POST /grievance/{id}/response - Add response
- GET /grievance/stats - Get statistics
"""

import os
import logging
import uuid
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, and_

from database.models import (
    get_db, Admin, Teacher, Student, Community,
    Grievance, GrievanceResponse,
    GrievanceStatus, GrievancePriority, UserStatus
)
from api.services.auth_service import (
    auth_service, get_current_user, TokenData
)
from config.settings import settings

logger = logging.getLogger("AssessIQ.Grievance")

router = APIRouter()


# ========== Request/Response Models ==========
class CreateGrievanceRequest(BaseModel):
    """Create grievance request."""
    subject: str
    description: str
    category: Optional[str] = None  # "Academic", "Behavioral", "Technical", "Other"
    priority: Optional[str] = "medium"  # "low", "medium", "high", "urgent"
    community_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Evaluation Score Issue",
                "description": "My answer evaluation shows incorrect score. I believe the AI misread my handwriting.",
                "category": "Academic",
                "priority": "medium"
            }
        }


class UpdateGrievanceStatusRequest(BaseModel):
    """Update grievance status."""
    status: str  # "in_review", "resolved", "rejected", "escalated"
    resolution: Optional[str] = None
    escalation_reason: Optional[str] = None


class AddGrievanceResponseRequest(BaseModel):
    """Add response to grievance."""
    content: str
    action_taken: Optional[str] = None  # "status_changed", "escalated", "resolved"


# ========== Helper Functions ==========
def can_view_grievance(grievance: Grievance, user_id: int, role: str) -> bool:
    """Check if user can view the grievance."""
    if role == "admin":
        return True  # Admin can view all
    
    if role == "teacher":
        # Teacher can view if assigned or if they created it
        if grievance.assigned_teacher_id == user_id:
            return True
        if grievance.complainant_teacher_id == user_id:
            return True
    
    if role == "student":
        # Student can only view their own grievances
        if grievance.complainant_student_id == user_id:
            return True
    
    return False


def can_update_grievance(grievance: Grievance, user_id: int, role: str) -> bool:
    """Check if user can update the grievance status."""
    if role == "admin":
        return True  # Admin can update any
    
    if role == "teacher":
        # Teacher can update if assigned to them
        if grievance.assigned_teacher_id == user_id:
            return True
    
    return False


# ========== Grievance Management ==========
@router.get("")
async def list_grievances(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    category_filter: Optional[str] = None
):
    """
    List grievances based on user role.
    - Admin: All grievances (with escalated ones highlighted)
    - Teacher: Assigned grievances + own grievances
    - Student: Own grievances only
    """
    try:
        offset = (page - 1) * limit
        
        # Build query based on role
        query = db.query(Grievance)
        
        if current_user.role == "admin":
            # Admin sees all, prioritize escalated
            pass
        elif current_user.role == "teacher":
            # Teacher sees assigned + own grievances
            query = query.filter(
                or_(
                    Grievance.assigned_teacher_id == current_user.user_id,
                    Grievance.complainant_teacher_id == current_user.user_id
                )
            )
        else:  # Student
            # Student sees only own grievances
            query = query.filter(
                Grievance.complainant_student_id == current_user.user_id
            )
        
        # Apply filters
        if status_filter:
            try:
                status_enum = GrievanceStatus(status_filter)
                query = query.filter(Grievance.status == status_enum)
            except ValueError:
                pass
        
        if priority_filter:
            try:
                priority_enum = GrievancePriority(priority_filter)
                query = query.filter(Grievance.priority == priority_enum)
            except ValueError:
                pass
        
        if category_filter:
            query = query.filter(Grievance.category == category_filter)
        
        # Get total count
        total = query.count()
        
        # Order by priority and date
        grievances = query.order_by(
            desc(Grievance.status == GrievanceStatus.ESCALATED),
            desc(Grievance.priority == GrievancePriority.URGENT),
            desc(Grievance.priority == GrievancePriority.HIGH),
            desc(Grievance.created_at)
        ).offset(offset).limit(limit).all()
        
        # Get response counts
        grievance_list = []
        for g in grievances:
            g_data = g.to_dict()
            g_data["response_count"] = db.query(GrievanceResponse).filter(
                GrievanceResponse.grievance_id == g.id
            ).count()
            grievance_list.append(g_data)
        
        return {
            "success": True,
            "data": grievance_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing grievances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_grievance(
    request: CreateGrievanceRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new grievance.
    - Students create grievances addressed to their teacher
    - Teachers can create grievances addressed to admin
    """
    try:
        grievance = Grievance(
            subject=request.subject,
            description=request.description,
            category=request.category,
            priority=GrievancePriority(request.priority) if request.priority else GrievancePriority.MEDIUM,
            status=GrievanceStatus.PENDING
        )
        
        # Set complainant
        if current_user.role == "student":
            grievance.complainant_student_id = current_user.user_id
            
            # Get student's teacher
            student = db.query(Student).filter(Student.id == current_user.user_id).first()
            if student and student.teacher_id:
                grievance.assigned_teacher_id = student.teacher_id
            else:
                # Assign to any active teacher
                teacher = db.query(Teacher).filter(Teacher.status == UserStatus.ACTIVE).first()
                if teacher:
                    grievance.assigned_teacher_id = teacher.id
                    
        elif current_user.role == "teacher":
            grievance.complainant_teacher_id = current_user.user_id
            
            # Get any admin
            admin = db.query(Admin).first()
            if admin:
                grievance.assigned_admin_id = admin.id
        
        # Link to community if provided
        if request.community_id:
            community = db.query(Community).filter(
                Community.community_id == request.community_id
            ).first()
            if community:
                grievance.community_id = community.id
        
        db.add(grievance)
        db.commit()
        db.refresh(grievance)
        
        logger.info(f"Grievance created: {grievance.grievance_id} by {current_user.email}")
        
        return {
            "success": True,
            "message": "Grievance submitted successfully",
            "data": grievance.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating grievance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/with-attachments")
async def create_grievance_with_attachments(
    subject: str = Form(...),
    description: str = Form(...),
    category: Optional[str] = Form(None),
    priority: Optional[str] = Form("medium"),
    community_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a grievance with file attachments.
    """
    try:
        grievance = Grievance(
            subject=subject,
            description=description,
            category=category,
            priority=GrievancePriority(priority) if priority else GrievancePriority.MEDIUM,
            status=GrievanceStatus.PENDING
        )
        
        # Set complainant
        if current_user.role == "student":
            grievance.complainant_student_id = current_user.user_id
            student = db.query(Student).filter(Student.id == current_user.user_id).first()
            if student and student.teacher_id:
                grievance.assigned_teacher_id = student.teacher_id
        elif current_user.role == "teacher":
            grievance.complainant_teacher_id = current_user.user_id
            admin = db.query(Admin).first()
            if admin:
                grievance.assigned_admin_id = admin.id
        
        if community_id:
            community = db.query(Community).filter(
                Community.community_id == community_id
            ).first()
            if community:
                grievance.community_id = community.id
        
        # Save attachments
        attachments = []
        if files:
            grievance_dir = os.path.join(settings.UPLOAD_DIR, "grievances", str(uuid.uuid4()))
            os.makedirs(grievance_dir, exist_ok=True)
            
            for file in files:
                if file.filename:
                    file_path = os.path.join(grievance_dir, file.filename)
                    with open(file_path, "wb") as f:
                        f.write(await file.read())
                    attachments.append(file_path)
        
        grievance.attachments = attachments if attachments else None
        
        db.add(grievance)
        db.commit()
        db.refresh(grievance)
        
        return {
            "success": True,
            "message": "Grievance submitted successfully",
            "data": grievance.to_dict()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating grievance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_grievance_stats(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get grievance statistics based on user role.
    """
    try:
        # Build base query based on role
        if current_user.role == "admin":
            base_query = db.query(Grievance)
        elif current_user.role == "teacher":
            base_query = db.query(Grievance).filter(
                or_(
                    Grievance.assigned_teacher_id == current_user.user_id,
                    Grievance.complainant_teacher_id == current_user.user_id
                )
            )
        else:
            base_query = db.query(Grievance).filter(
                Grievance.complainant_student_id == current_user.user_id
            )
        
        # Count by status
        stats = {
            "total": base_query.count(),
            "pending": base_query.filter(Grievance.status == GrievanceStatus.PENDING).count(),
            "in_review": base_query.filter(Grievance.status == GrievanceStatus.IN_REVIEW).count(),
            "resolved": base_query.filter(Grievance.status == GrievanceStatus.RESOLVED).count(),
            "rejected": base_query.filter(Grievance.status == GrievanceStatus.REJECTED).count(),
            "escalated": base_query.filter(Grievance.status == GrievanceStatus.ESCALATED).count(),
        }
        
        # Count by priority
        stats["by_priority"] = {
            "urgent": base_query.filter(Grievance.priority == GrievancePriority.URGENT).count(),
            "high": base_query.filter(Grievance.priority == GrievancePriority.HIGH).count(),
            "medium": base_query.filter(Grievance.priority == GrievancePriority.MEDIUM).count(),
            "low": base_query.filter(Grievance.priority == GrievancePriority.LOW).count(),
        }
        
        # Count by category
        categories = db.query(
            Grievance.category,
            func.count(Grievance.id)
        ).filter(
            Grievance.category.isnot(None)
        ).group_by(Grievance.category).all()
        
        stats["by_category"] = {cat: count for cat, count in categories if cat}
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting grievance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{grievance_id}")
async def get_grievance(
    grievance_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get grievance details with responses.
    """
    try:
        grievance = db.query(Grievance).filter(
            Grievance.grievance_id == grievance_id
        ).first()
        
        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")
        
        # Check permission
        if not can_view_grievance(grievance, current_user.user_id, current_user.role):
            raise HTTPException(status_code=403, detail="You cannot view this grievance")
        
        # Get grievance data with responses
        g_data = grievance.to_dict()
        
        # Get responses
        responses = db.query(GrievanceResponse).filter(
            GrievanceResponse.grievance_id == grievance.id
        ).order_by(GrievanceResponse.created_at).all()
        
        g_data["responses"] = [r.to_dict() for r in responses]
        
        return {
            "success": True,
            "data": g_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting grievance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{grievance_id}/status")
async def update_grievance_status(
    grievance_id: str,
    request: UpdateGrievanceStatusRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update grievance status.
    - Teacher can: in_review, resolved, rejected, escalated
    - Admin can: all status changes
    """
    try:
        grievance = db.query(Grievance).filter(
            Grievance.grievance_id == grievance_id
        ).first()
        
        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")
        
        # Check permission
        if not can_update_grievance(grievance, current_user.user_id, current_user.role):
            raise HTTPException(status_code=403, detail="You cannot update this grievance")
        
        # Validate status transition
        old_status = grievance.status
        try:
            new_status = GrievanceStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")
        
        # Update status
        grievance.status = new_status
        
        # Handle specific status changes
        if new_status == GrievanceStatus.RESOLVED:
            grievance.resolution = request.resolution
            grievance.resolved_at = datetime.utcnow()
            if current_user.role == "admin":
                grievance.resolved_by_admin_id = current_user.user_id
            else:
                grievance.resolved_by_teacher_id = current_user.user_id
                
        elif new_status == GrievanceStatus.ESCALATED:
            grievance.escalated_at = datetime.utcnow()
            grievance.escalation_reason = request.escalation_reason
            
            # Assign to admin
            admin = db.query(Admin).first()
            if admin:
                grievance.assigned_admin_id = admin.id
        
        db.commit()
        
        # Add system response for status change
        response = GrievanceResponse(
            grievance_id=grievance.id,
            content=f"Status changed from '{old_status.value}' to '{new_status.value}'",
            action_taken="status_changed"
        )
        
        if current_user.role == "admin":
            response.responder_admin_id = current_user.user_id
        elif current_user.role == "teacher":
            response.responder_teacher_id = current_user.user_id
        else:
            response.responder_student_id = current_user.user_id
        
        db.add(response)
        db.commit()
        
        logger.info(f"Grievance {grievance_id} status updated to {new_status.value}")
        
        return {
            "success": True,
            "message": f"Grievance status updated to {new_status.value}",
            "data": grievance.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating grievance status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{grievance_id}/response")
async def add_grievance_response(
    grievance_id: str,
    request: AddGrievanceResponseRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a response/comment to a grievance.
    """
    try:
        grievance = db.query(Grievance).filter(
            Grievance.grievance_id == grievance_id
        ).first()
        
        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")
        
        # Check permission (anyone who can view can respond)
        if not can_view_grievance(grievance, current_user.user_id, current_user.role):
            raise HTTPException(status_code=403, detail="You cannot respond to this grievance")
        
        # Create response
        response = GrievanceResponse(
            grievance_id=grievance.id,
            content=request.content,
            action_taken=request.action_taken
        )
        
        if current_user.role == "admin":
            response.responder_admin_id = current_user.user_id
        elif current_user.role == "teacher":
            response.responder_teacher_id = current_user.user_id
        else:
            response.responder_student_id = current_user.user_id
        
        # Update grievance to "in review" if pending
        if grievance.status == GrievanceStatus.PENDING and current_user.role in ["admin", "teacher"]:
            grievance.status = GrievanceStatus.IN_REVIEW
        
        db.add(response)
        db.commit()
        db.refresh(response)
        
        return {
            "success": True,
            "message": "Response added successfully",
            "data": response.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding grievance response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{grievance_id}/response/with-attachments")
async def add_grievance_response_with_attachments(
    grievance_id: str,
    content: str = Form(...),
    action_taken: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a response with file attachments.
    """
    try:
        grievance = db.query(Grievance).filter(
            Grievance.grievance_id == grievance_id
        ).first()
        
        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")
        
        if not can_view_grievance(grievance, current_user.user_id, current_user.role):
            raise HTTPException(status_code=403, detail="You cannot respond to this grievance")
        
        # Save attachments
        attachments = []
        if files:
            response_dir = os.path.join(settings.UPLOAD_DIR, "grievances", grievance_id, "responses", str(uuid.uuid4()))
            os.makedirs(response_dir, exist_ok=True)
            
            for file in files:
                if file.filename:
                    file_path = os.path.join(response_dir, file.filename)
                    with open(file_path, "wb") as f:
                        f.write(await file.read())
                    attachments.append(file_path)
        
        # Create response
        response = GrievanceResponse(
            grievance_id=grievance.id,
            content=content,
            action_taken=action_taken,
            attachments=attachments if attachments else None
        )
        
        if current_user.role == "admin":
            response.responder_admin_id = current_user.user_id
        elif current_user.role == "teacher":
            response.responder_teacher_id = current_user.user_id
        else:
            response.responder_student_id = current_user.user_id
        
        if grievance.status == GrievanceStatus.PENDING and current_user.role in ["admin", "teacher"]:
            grievance.status = GrievanceStatus.IN_REVIEW
        
        db.add(response)
        db.commit()
        db.refresh(response)
        
        return {
            "success": True,
            "message": "Response added successfully",
            "data": response.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding grievance response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Categories ==========
@router.get("/categories/list")
async def get_grievance_categories(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get list of grievance categories.
    """
    categories = [
        {"id": "academic", "name": "Academic", "description": "Issues related to academics, evaluations, grades"},
        {"id": "behavioral", "name": "Behavioral", "description": "Issues related to conduct or behavior"},
        {"id": "technical", "name": "Technical", "description": "Technical issues with the system"},
        {"id": "administrative", "name": "Administrative", "description": "Administrative concerns"},
        {"id": "other", "name": "Other", "description": "Other issues not covered above"}
    ]
    
    return {
        "success": True,
        "data": categories
    }
