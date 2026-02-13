"""
Community Routes - AssessIQ
============================
API endpoints for WhatsApp-like community management.

Features:
- Admin creates communities for teachers
- Teachers create communities for students
- Group chat functionality
- Announcements
- File sharing

Endpoints:
- GET /community - List user's communities
- POST /community - Create a community
- GET /community/{id} - Get community details
- PUT /community/{id} - Update community
- DELETE /community/{id} - Delete community
- POST /community/{id}/members - Add members
- DELETE /community/{id}/members/{member_id} - Remove member
- GET /community/{id}/messages - Get messages
- POST /community/{id}/messages - Send message
- POST /community/{id}/announcements - Send announcement
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
    get_db, Admin, Teacher, Student,
    Community, CommunityMember, CommunityMessage,
    CommunityType, MemberRole, MessageType, UserStatus
)
from api.services.auth_service import (
    auth_service, get_current_user, TokenData
)
from config.settings import settings

logger = logging.getLogger("AssessIQ.Community")

router = APIRouter()


# ========== Request/Response Models ==========
class CreateCommunityRequest(BaseModel):
    """Create community request."""
    name: str
    description: Optional[str] = None
    community_type: str  # "admin_teacher" or "teacher_student"
    allow_member_posts: bool = True
    allow_file_sharing: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "name": "CSE 6th Semester",
                "description": "Community for CSE 6th semester students",
                "community_type": "teacher_student",
                "allow_member_posts": True,
                "allow_file_sharing": True
            }
        }


class UpdateCommunityRequest(BaseModel):
    """Update community request."""
    name: Optional[str] = None
    description: Optional[str] = None
    allow_member_posts: Optional[bool] = None
    allow_file_sharing: Optional[bool] = None


class AddMembersRequest(BaseModel):
    """Add members to community."""
    member_ids: List[str]  # List of teacher_id or student_id


class SendMessageRequest(BaseModel):
    """Send message request."""
    content: str
    message_type: str = "text"  # "text", "announcement"
    reply_to_id: Optional[str] = None


# ========== Helper Functions ==========
def get_user_from_token(token_data: TokenData, db: Session):
    """Get user object from token data."""
    if token_data.role == "admin":
        return db.query(Admin).filter(Admin.id == token_data.user_id).first()
    elif token_data.role == "teacher":
        return db.query(Teacher).filter(Teacher.id == token_data.user_id).first()
    elif token_data.role == "student":
        return db.query(Student).filter(Student.id == token_data.user_id).first()
    return None


def is_community_owner(community: Community, user_id: int, role: str) -> bool:
    """Check if user is the owner of the community."""
    if role == "admin" and community.owner_admin_id == user_id:
        return True
    if role == "teacher" and community.owner_teacher_id == user_id:
        return True
    return False


def is_community_member(community_id: int, user_id: int, role: str, db: Session) -> bool:
    """Check if user is a member of the community."""
    query = db.query(CommunityMember).filter(
        CommunityMember.community_id == community_id,
        CommunityMember.is_active == True
    )
    
    if role == "admin":
        query = query.filter(CommunityMember.admin_id == user_id)
    elif role == "teacher":
        query = query.filter(CommunityMember.teacher_id == user_id)
    elif role == "student":
        query = query.filter(CommunityMember.student_id == user_id)
    
    return query.first() is not None


# ========== Community Management ==========
@router.get("")
async def list_communities(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    List all communities the user belongs to.
    """
    try:
        offset = (page - 1) * limit
        
        # Build query based on user role
        if current_user.role == "admin":
            # Admin sees communities they own + communities they're members of
            communities = db.query(Community).outerjoin(
                CommunityMember,
                and_(
                    CommunityMember.community_id == Community.id,
                    CommunityMember.admin_id == current_user.user_id
                )
            ).filter(
                or_(
                    Community.owner_admin_id == current_user.user_id,
                    CommunityMember.admin_id == current_user.user_id
                ),
                Community.is_active == True
            ).distinct().offset(offset).limit(limit).all()
            
        elif current_user.role == "teacher":
            # Teacher sees communities they own + communities they're members of
            communities = db.query(Community).outerjoin(
                CommunityMember,
                and_(
                    CommunityMember.community_id == Community.id,
                    CommunityMember.teacher_id == current_user.user_id
                )
            ).filter(
                or_(
                    Community.owner_teacher_id == current_user.user_id,
                    CommunityMember.teacher_id == current_user.user_id
                ),
                Community.is_active == True
            ).distinct().offset(offset).limit(limit).all()
            
        else:  # Student
            # Student sees only communities they're members of
            communities = db.query(Community).join(
                CommunityMember,
                CommunityMember.community_id == Community.id
            ).filter(
                CommunityMember.student_id == current_user.user_id,
                CommunityMember.is_active == True,
                Community.is_active == True
            ).offset(offset).limit(limit).all()
        
        # Get latest message for each community
        community_list = []
        for comm in communities:
            comm_data = comm.to_dict()
            
            # Get latest message
            latest_msg = db.query(CommunityMessage).filter(
                CommunityMessage.community_id == comm.id,
                CommunityMessage.is_deleted == False
            ).order_by(desc(CommunityMessage.created_at)).first()
            
            if latest_msg:
                comm_data["latest_message"] = {
                    "content": latest_msg.content[:50] + "..." if len(latest_msg.content or "") > 50 else latest_msg.content,
                    "sender": latest_msg.sender_admin.name if latest_msg.sender_admin else (
                        latest_msg.sender_teacher.name if latest_msg.sender_teacher else (
                            latest_msg.sender_student.name if latest_msg.sender_student else "Unknown"
                        )
                    ),
                    "time": latest_msg.created_at.isoformat() if latest_msg.created_at else None
                }
            else:
                comm_data["latest_message"] = None
            
            # Get unread count (simplified - just count messages after last seen)
            comm_data["unread_count"] = 0
            
            # Check if owner
            comm_data["is_owner"] = is_community_owner(comm, current_user.user_id, current_user.role)
            
            community_list.append(comm_data)
        
        return {
            "success": True,
            "data": community_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(community_list)
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing communities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_community(
    request: CreateCommunityRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new community.
    - Admin can create admin_teacher communities
    - Teacher can create teacher_student communities
    """
    try:
        # Validate permissions
        if request.community_type == "admin_teacher" and current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only admins can create admin-teacher communities"
            )
        
        if request.community_type == "teacher_student" and current_user.role not in ["admin", "teacher"]:
            raise HTTPException(
                status_code=403,
                detail="Only teachers can create teacher-student communities"
            )
        
        # Create community
        community = Community(
            name=request.name,
            description=request.description,
            community_type=CommunityType(request.community_type),
            allow_member_posts=request.allow_member_posts,
            allow_file_sharing=request.allow_file_sharing,
            member_count=1
        )
        
        # Set owner
        if current_user.role == "admin":
            community.owner_admin_id = current_user.user_id
        else:
            community.owner_teacher_id = current_user.user_id
        
        db.add(community)
        db.flush()
        
        # Add creator as owner member
        member = CommunityMember(
            community_id=community.id,
            member_role=MemberRole.OWNER
        )
        
        if current_user.role == "admin":
            member.admin_id = current_user.user_id
        else:
            member.teacher_id = current_user.user_id
        
        db.add(member)
        db.commit()
        
        # Send system message
        system_msg = CommunityMessage(
            community_id=community.id,
            message_type=MessageType.SYSTEM,
            content=f"Community '{request.name}' was created"
        )
        if current_user.role == "admin":
            system_msg.sender_admin_id = current_user.user_id
        else:
            system_msg.sender_teacher_id = current_user.user_id
        db.add(system_msg)
        db.commit()
        
        logger.info(f"Community created: {community.community_id} by {current_user.email}")
        
        return {
            "success": True,
            "message": "Community created successfully",
            "data": community.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating community: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{community_id}")
async def get_community(
    community_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get community details with members list.
    """
    try:
        community = db.query(Community).filter(
            Community.community_id == community_id,
            Community.is_active == True
        ).first()
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is a member or owner
        is_owner = is_community_owner(community, current_user.user_id, current_user.role)
        is_member = is_community_member(community.id, current_user.user_id, current_user.role, db)
        
        if not is_owner and not is_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community")
        
        # Get community data
        comm_data = community.to_dict()
        comm_data["is_owner"] = is_owner
        
        # Get members
        members = db.query(CommunityMember).filter(
            CommunityMember.community_id == community.id,
            CommunityMember.is_active == True
        ).all()
        
        comm_data["members"] = [m.to_dict() for m in members]
        
        return {
            "success": True,
            "data": comm_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting community: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{community_id}")
async def update_community(
    community_id: str,
    request: UpdateCommunityRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update community settings. Only owner can update.
    """
    try:
        community = db.query(Community).filter(
            Community.community_id == community_id,
            Community.is_active == True
        ).first()
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check ownership
        if not is_community_owner(community, current_user.user_id, current_user.role):
            raise HTTPException(status_code=403, detail="Only owner can update community")
        
        # Update fields
        if request.name is not None:
            community.name = request.name
        if request.description is not None:
            community.description = request.description
        if request.allow_member_posts is not None:
            community.allow_member_posts = request.allow_member_posts
        if request.allow_file_sharing is not None:
            community.allow_file_sharing = request.allow_file_sharing
        
        db.commit()
        
        return {
            "success": True,
            "message": "Community updated successfully",
            "data": community.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating community: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{community_id}")
async def delete_community(
    community_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete (deactivate) a community. Only owner can delete.
    """
    try:
        community = db.query(Community).filter(
            Community.community_id == community_id,
            Community.is_active == True
        ).first()
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check ownership
        if not is_community_owner(community, current_user.user_id, current_user.role):
            raise HTTPException(status_code=403, detail="Only owner can delete community")
        
        # Soft delete
        community.is_active = False
        db.commit()
        
        logger.info(f"Community deleted: {community_id} by {current_user.email}")
        
        return {
            "success": True,
            "message": "Community deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting community: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Member Management ==========
@router.post("/{community_id}/members")
async def add_members(
    community_id: str,
    request: AddMembersRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add members to a community. Only owner can add members.
    """
    try:
        community = db.query(Community).filter(
            Community.community_id == community_id,
            Community.is_active == True
        ).first()
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check ownership
        if not is_community_owner(community, current_user.user_id, current_user.role):
            raise HTTPException(status_code=403, detail="Only owner can add members")
        
        added = []
        already_members = []
        not_found = []
        
        for member_id in request.member_ids:
            user = None
            member = CommunityMember(community_id=community.id)
            
            # Determine member type based on community type
            if community.community_type == CommunityType.ADMIN_TEACHER:
                # Add teachers to admin-teacher community
                user = db.query(Teacher).filter(
                    Teacher.teacher_id == member_id,
                    Teacher.status == UserStatus.ACTIVE
                ).first()
                if user:
                    member.teacher_id = user.id
                    
                    # Check if already member
                    existing = db.query(CommunityMember).filter(
                        CommunityMember.community_id == community.id,
                        CommunityMember.teacher_id == user.id
                    ).first()
                    
                    if existing:
                        if existing.is_active:
                            already_members.append(member_id)
                            continue
                        else:
                            existing.is_active = True
                            added.append({"id": member_id, "name": user.name})
                            continue
            else:
                # Add students to teacher-student community
                user = db.query(Student).filter(
                    Student.student_id == member_id,
                    Student.status == UserStatus.ACTIVE
                ).first()
                if user:
                    member.student_id = user.id
                    
                    # Check if already member
                    existing = db.query(CommunityMember).filter(
                        CommunityMember.community_id == community.id,
                        CommunityMember.student_id == user.id
                    ).first()
                    
                    if existing:
                        if existing.is_active:
                            already_members.append(member_id)
                            continue
                        else:
                            existing.is_active = True
                            added.append({"id": member_id, "name": user.name})
                            continue
            
            if not user:
                not_found.append(member_id)
                continue
            
            db.add(member)
            added.append({"id": member_id, "name": user.name})
        
        # Update member count
        community.member_count = db.query(CommunityMember).filter(
            CommunityMember.community_id == community.id,
            CommunityMember.is_active == True
        ).count()
        
        db.commit()
        
        # Send system message for added members
        if added:
            names = ", ".join([m["name"] for m in added])
            system_msg = CommunityMessage(
                community_id=community.id,
                message_type=MessageType.SYSTEM,
                content=f"{names} joined the community"
            )
            if current_user.role == "admin":
                system_msg.sender_admin_id = current_user.user_id
            else:
                system_msg.sender_teacher_id = current_user.user_id
            db.add(system_msg)
            db.commit()
        
        return {
            "success": True,
            "message": f"Added {len(added)} members",
            "data": {
                "added": added,
                "already_members": already_members,
                "not_found": not_found
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding members: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{community_id}/members/{member_id}")
async def remove_member(
    community_id: str,
    member_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a member from community. Only owner can remove members.
    """
    try:
        community = db.query(Community).filter(
            Community.community_id == community_id,
            Community.is_active == True
        ).first()
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check ownership
        if not is_community_owner(community, current_user.user_id, current_user.role):
            raise HTTPException(status_code=403, detail="Only owner can remove members")
        
        # Find member
        member = None
        user_name = None
        
        if community.community_type == CommunityType.ADMIN_TEACHER:
            teacher = db.query(Teacher).filter(Teacher.teacher_id == member_id).first()
            if teacher:
                member = db.query(CommunityMember).filter(
                    CommunityMember.community_id == community.id,
                    CommunityMember.teacher_id == teacher.id,
                    CommunityMember.is_active == True
                ).first()
                user_name = teacher.name
        else:
            student = db.query(Student).filter(Student.student_id == member_id).first()
            if student:
                member = db.query(CommunityMember).filter(
                    CommunityMember.community_id == community.id,
                    CommunityMember.student_id == student.id,
                    CommunityMember.is_active == True
                ).first()
                user_name = student.name
        
        if not member:
            raise HTTPException(status_code=404, detail="Member not found in community")
        
        # Cannot remove owner
        if member.member_role == MemberRole.OWNER:
            raise HTTPException(status_code=400, detail="Cannot remove community owner")
        
        # Soft delete member
        member.is_active = False
        
        # Update member count
        community.member_count = db.query(CommunityMember).filter(
            CommunityMember.community_id == community.id,
            CommunityMember.is_active == True
        ).count()
        
        db.commit()
        
        # Send system message
        system_msg = CommunityMessage(
            community_id=community.id,
            message_type=MessageType.SYSTEM,
            content=f"{user_name} was removed from the community"
        )
        if current_user.role == "admin":
            system_msg.sender_admin_id = current_user.user_id
        else:
            system_msg.sender_teacher_id = current_user.user_id
        db.add(system_msg)
        db.commit()
        
        return {
            "success": True,
            "message": f"{user_name} removed from community"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing member: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Messages ==========
@router.get("/{community_id}/messages")
async def get_messages(
    community_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    before_id: Optional[str] = None
):
    """
    Get messages from a community.
    """
    try:
        community = db.query(Community).filter(
            Community.community_id == community_id,
            Community.is_active == True
        ).first()
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check membership
        is_owner = is_community_owner(community, current_user.user_id, current_user.role)
        is_member = is_community_member(community.id, current_user.user_id, current_user.role, db)
        
        if not is_owner and not is_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community")
        
        # Build query
        query = db.query(CommunityMessage).filter(
            CommunityMessage.community_id == community.id,
            CommunityMessage.is_deleted == False
        )
        
        # Pagination with cursor
        if before_id:
            before_msg = db.query(CommunityMessage).filter(
                CommunityMessage.message_id == before_id
            ).first()
            if before_msg:
                query = query.filter(CommunityMessage.id < before_msg.id)
        
        messages = query.order_by(desc(CommunityMessage.created_at)).limit(limit).all()
        
        # Reverse to get chronological order
        messages = list(reversed(messages))
        
        return {
            "success": True,
            "data": [m.to_dict() for m in messages],
            "pagination": {
                "page": page,
                "limit": limit,
                "has_more": len(messages) == limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{community_id}/messages")
async def send_message(
    community_id: str,
    request: SendMessageRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message to a community.
    """
    try:
        community = db.query(Community).filter(
            Community.community_id == community_id,
            Community.is_active == True
        ).first()
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check membership
        is_owner = is_community_owner(community, current_user.user_id, current_user.role)
        is_member = is_community_member(community.id, current_user.user_id, current_user.role, db)
        
        if not is_owner and not is_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community")
        
        # Check if member can post
        if not is_owner and not community.allow_member_posts:
            raise HTTPException(status_code=403, detail="Members cannot post in this community")
        
        # Announcements only by owners
        if request.message_type == "announcement" and not is_owner:
            raise HTTPException(status_code=403, detail="Only owners can send announcements")
        
        # Create message
        message = CommunityMessage(
            community_id=community.id,
            message_type=MessageType(request.message_type),
            content=request.content
        )
        
        # Set sender
        if current_user.role == "admin":
            message.sender_admin_id = current_user.user_id
        elif current_user.role == "teacher":
            message.sender_teacher_id = current_user.user_id
        else:
            message.sender_student_id = current_user.user_id
        
        # Handle reply
        if request.reply_to_id:
            reply_to = db.query(CommunityMessage).filter(
                CommunityMessage.message_id == request.reply_to_id
            ).first()
            if reply_to:
                message.reply_to_id = reply_to.id
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        return {
            "success": True,
            "message": "Message sent",
            "data": message.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{community_id}/messages/file")
async def send_file_message(
    community_id: str,
    file: UploadFile = File(...),
    content: str = Form(""),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a file message to a community.
    """
    try:
        community = db.query(Community).filter(
            Community.community_id == community_id,
            Community.is_active == True
        ).first()
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check membership
        is_owner = is_community_owner(community, current_user.user_id, current_user.role)
        is_member = is_community_member(community.id, current_user.user_id, current_user.role, db)
        
        if not is_owner and not is_member:
            raise HTTPException(status_code=403, detail="You are not a member of this community")
        
        # Check file sharing permission
        if not community.allow_file_sharing:
            raise HTTPException(status_code=403, detail="File sharing is disabled in this community")
        
        # Save file
        file_ext = os.path.splitext(file.filename)[1]
        file_id = str(uuid.uuid4())
        file_path = os.path.join(settings.UPLOAD_DIR, "community", file_id + file_ext)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Create message
        message = CommunityMessage(
            community_id=community.id,
            message_type=MessageType.FILE,
            content=content or f"Shared file: {file.filename}",
            file_path=file_path,
            file_name=file.filename
        )
        
        # Set sender
        if current_user.role == "admin":
            message.sender_admin_id = current_user.user_id
        elif current_user.role == "teacher":
            message.sender_teacher_id = current_user.user_id
        else:
            message.sender_student_id = current_user.user_id
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        return {
            "success": True,
            "message": "File sent",
            "data": message.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending file message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{community_id}/messages/{message_id}")
async def delete_message(
    community_id: str,
    message_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a message. Users can delete their own messages, owners can delete any.
    """
    try:
        community = db.query(Community).filter(
            Community.community_id == community_id,
            Community.is_active == True
        ).first()
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        message = db.query(CommunityMessage).filter(
            CommunityMessage.message_id == message_id,
            CommunityMessage.community_id == community.id,
            CommunityMessage.is_deleted == False
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Check permission
        is_owner = is_community_owner(community, current_user.user_id, current_user.role)
        is_sender = False
        
        if current_user.role == "admin" and message.sender_admin_id == current_user.user_id:
            is_sender = True
        elif current_user.role == "teacher" and message.sender_teacher_id == current_user.user_id:
            is_sender = True
        elif current_user.role == "student" and message.sender_student_id == current_user.user_id:
            is_sender = True
        
        if not is_owner and not is_sender:
            raise HTTPException(status_code=403, detail="You cannot delete this message")
        
        # Soft delete
        message.is_deleted = True
        message.content = "This message was deleted"
        db.commit()
        
        return {
            "success": True,
            "message": "Message deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{community_id}/messages/{message_id}/pin")
async def pin_message(
    community_id: str,
    message_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pin/unpin a message. Only owners can pin messages.
    """
    try:
        community = db.query(Community).filter(
            Community.community_id == community_id,
            Community.is_active == True
        ).first()
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check ownership
        if not is_community_owner(community, current_user.user_id, current_user.role):
            raise HTTPException(status_code=403, detail="Only owner can pin messages")
        
        message = db.query(CommunityMessage).filter(
            CommunityMessage.message_id == message_id,
            CommunityMessage.community_id == community.id,
            CommunityMessage.is_deleted == False
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Toggle pin
        message.is_pinned = not message.is_pinned
        db.commit()
        
        return {
            "success": True,
            "message": "Message pinned" if message.is_pinned else "Message unpinned",
            "data": {"is_pinned": message.is_pinned}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error pinning message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Available Members ==========
@router.get("/{community_id}/available-members")
async def get_available_members(
    community_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    search: str = Query("", description="Search by name or ID")
):
    """
    Get list of users that can be added to the community.
    """
    try:
        community = db.query(Community).filter(
            Community.community_id == community_id,
            Community.is_active == True
        ).first()
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check ownership
        if not is_community_owner(community, current_user.user_id, current_user.role):
            raise HTTPException(status_code=403, detail="Only owner can view available members")
        
        available = []
        
        if community.community_type == CommunityType.ADMIN_TEACHER:
            # Get teachers not in community
            existing_ids = db.query(CommunityMember.teacher_id).filter(
                CommunityMember.community_id == community.id,
                CommunityMember.is_active == True,
                CommunityMember.teacher_id.isnot(None)
            ).all()
            existing_ids = [e[0] for e in existing_ids]
            
            query = db.query(Teacher).filter(
                Teacher.status == UserStatus.ACTIVE,
                Teacher.id.notin_(existing_ids) if existing_ids else True
            )
            
            if search:
                query = query.filter(
                    or_(
                        Teacher.name.ilike(f"%{search}%"),
                        Teacher.teacher_id.ilike(f"%{search}%"),
                        Teacher.email.ilike(f"%{search}%")
                    )
                )
            
            teachers = query.limit(50).all()
            available = [
                {
                    "id": t.teacher_id,
                    "name": t.name,
                    "email": t.email,
                    "department": t.department
                }
                for t in teachers
            ]
        else:
            # Get students not in community
            existing_ids = db.query(CommunityMember.student_id).filter(
                CommunityMember.community_id == community.id,
                CommunityMember.is_active == True,
                CommunityMember.student_id.isnot(None)
            ).all()
            existing_ids = [e[0] for e in existing_ids]
            
            query = db.query(Student).filter(
                Student.status == UserStatus.ACTIVE,
                Student.id.notin_(existing_ids) if existing_ids else True
            )
            
            # If teacher, only show their students
            if current_user.role == "teacher":
                query = query.filter(Student.teacher_id == current_user.user_id)
            
            if search:
                query = query.filter(
                    or_(
                        Student.name.ilike(f"%{search}%"),
                        Student.student_id.ilike(f"%{search}%"),
                        Student.roll_no.ilike(f"%{search}%")
                    )
                )
            
            students = query.limit(50).all()
            available = [
                {
                    "id": s.student_id,
                    "name": s.name,
                    "roll_no": s.roll_no,
                    "class": s.class_info.name if s.class_info else None
                }
                for s in students
            ]
        
        return {
            "success": True,
            "data": available
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available members: {e}")
        raise HTTPException(status_code=500, detail=str(e))
