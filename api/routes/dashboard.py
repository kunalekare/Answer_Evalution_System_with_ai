"""
Dashboard Routes
================
API endpoints for dashboard data.
- GET dashboard: Retrieve user's dashboard (initializes if first visit)
- GET metrics: Retrieve specific metrics
- POST reset: Reset dashboard (admin only)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from datetime import datetime
from typing import Optional

from database.models import get_db, UserRole, Dashboard, Evaluation, Teacher, Student
from api.services.dashboard_service import DashboardService
from api.services.auth_service import get_current_user

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/", summary="Get User Dashboard")
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's dashboard with all metrics.
    - Initializes with zero values on first access
    - Updates metrics from database
    - Returns role-specific metrics
    
    **Response includes:**
    - Dashboard ID and initialization date
    - Role-specific metrics (admin/teacher/student)
    - Engagement metrics
    - Custom data
    
    **Initial state (first visit):** All numeric values are 0
    **Updates happen:** When user performs actions (created via events/hooks)
    """
    try:
        user_id = current_user.get("user_id")
        user_role = UserRole(current_user.get("user_role"))
        
        # Get or create dashboard
        dashboard = DashboardService.get_or_create_dashboard(db, user_id, user_role)
        
        # Increment login count
        DashboardService.update_login_count(db, dashboard)
        
        # Update metrics based on user role
        if user_role == UserRole.ADMIN:
            DashboardService.update_admin_metrics(db, user_id)
        elif user_role == UserRole.TEACHER:
            DashboardService.update_teacher_metrics(db, user_id)
        elif user_role == UserRole.STUDENT:
            DashboardService.update_student_metrics(db, user_id)
        
        # Refresh to get latest data
        db.refresh(dashboard)
        
        return {
            "status": "success",
            "message": "Dashboard retrieved successfully",
            "data": dashboard.to_dict(),
            "is_first_visit": dashboard.is_first_visit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard: {str(e)}")


@router.post("/increment/activity", summary="Increment Activity Counter")
async def increment_activity(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Increment user's total activities counter.
    Call this after user performs an action (create, update, evaluate, etc.)
    """
    try:
        user_id = current_user.get("user_id")
        user_role = UserRole(current_user.get("user_role"))
        
        dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
        
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        DashboardService.increment_total_activities(db, dashboard)
        db.refresh(dashboard)
        
        return {
            "status": "success",
            "total_activities": dashboard.total_activities
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/increment/grievances", summary="Increment Grievances Filed")
async def increment_grievances(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Increment grievances filed counter when user files a grievance."""
    try:
        user_id = current_user.get("user_id")
        user_role = UserRole(current_user.get("user_role"))
        
        dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
        
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        DashboardService.increment_grievances_filed(db, dashboard)
        db.refresh(dashboard)
        
        return {
            "status": "success",
            "grievances_filed": dashboard.grievances_filed
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/increment/messages", summary="Increment Community Messages")
async def increment_messages(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Increment community messages sent counter."""
    try:
        user_id = current_user.get("user_id")
        user_role = UserRole(current_user.get("user_role"))
        
        dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
        
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        DashboardService.increment_community_messages(db, dashboard)
        db.refresh(dashboard)
        
        return {
            "status": "success",
            "community_messages_sent": dashboard.community_messages_sent
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{metric_name}", summary="Get Metric History")
async def get_metric_history(
    metric_name: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get historical data for a specific metric.
    Useful for charting trends over time.
    
    **Parameters:**
    - metric_name: Name of metric (e.g., 'evaluations_created', 'average_score')
    - days: Number of days to retrieve (1-365, default 30)
    
    **Returns:** List of metric records with dates and values
    """
    try:
        user_id = current_user.get("user_id")
        user_role = UserRole(current_user.get("user_role"))
        
        dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
        
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        metrics = DashboardService.get_metric_history(db, dashboard, metric_name, days)
        
        return {
            "status": "success",
            "metric_name": metric_name,
            "data": [m.to_dict() for m in metrics]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", summary="Get Daily Summary")
async def get_daily_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get today's activity summary.
    Shows today's activities vs. total.
    """
    try:
        user_id = current_user.get("user_id")
        user_role = UserRole(current_user.get("user_role"))
        
        dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
        
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        summary = DashboardService.get_daily_summary(db, dashboard)
        
        return {
            "status": "success",
            "data": summary
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", summary="Reset Dashboard")
async def reset_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Reset all dashboard metrics to zero.
    Only admin can reset other users' dashboards.
    Users can only reset their own.
    
    **Use cases:**
    - Start of new semester
    - Start of new evaluation period
    - Manual reset requested by admin
    """
    try:
        user_id = current_user.get("user_id")
        user_role = UserRole(current_user.get("user_role"))
        
        dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
        
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        dashboard = DashboardService.reset_dashboard(db, dashboard)
        
        return {
            "status": "success",
            "message": "Dashboard reset to zero successfully",
            "data": dashboard.to_dict()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-evaluations", summary="Get Recent Evaluations")
async def get_recent_evaluations(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent evaluations for the current user (teacher or student).
    
    **For Teachers:** Returns all evaluations they created/reviewed
    **For Students:** Returns their own evaluations
    
    Returns up to `limit` most recent evaluations with student details.
    """
    try:
        user_id = current_user.get("user_id")
        user_role = current_user.get("user_role")
        
        query = db.query(Evaluation).order_by(desc(Evaluation.created_at))
        
        # Filter by user role
        if user_role == "student":
            # Students see only their own evaluations
            query = query.filter(Evaluation.student_id == user_id)
        elif user_role == "teacher":
            # Teachers see evaluations they created
            query = query.filter(Evaluation.teacher_id == user_id)
        else:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        evaluations = query.limit(limit).all()
        
        # Format response with student details
        result_data = []
        for eval_obj in evaluations:
            student_name = "Unknown"
            subject = "General"
            
            # Get student name if available
            if eval_obj.student:
                student_name = eval_obj.student.name
            
            # Get subject if available  
            if eval_obj.subject_ref:
                subject = eval_obj.subject_ref.name
            
            # Calculate time ago
            if eval_obj.created_at:
                time_diff = datetime.utcnow() - eval_obj.created_at
                if time_diff.days > 0:
                    time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
                elif time_diff.seconds >= 3600:
                    hours = time_diff.seconds // 3600
                    time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
                elif time_diff.seconds >= 60:
                    minutes = time_diff.seconds // 60
                    time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                else:
                    time_ago = "Just now"
            else:
                time_ago = "Unknown"
            
            result_data.append({
                "evaluation_id": eval_obj.evaluation_id,
                "student_name": student_name,
                "subject": subject,
                "score": float(eval_obj.final_score) if eval_obj.final_score else 0,
                "grade": eval_obj.grade.value if eval_obj.grade else "Unknown",
                "marks": f"{float(eval_obj.obtained_marks) if eval_obj.obtained_marks else 0}/{eval_obj.max_marks}",
                "time_ago": time_ago,
                "created_at": eval_obj.created_at.isoformat() if eval_obj.created_at else None,
            })
        
        return {
            "status": "success",
            "message": "Recent evaluations retrieved successfully",
            "data": result_data,
            "total": len(result_data)
        }
    
    except Exception as e:
        import logging
        logging.error(f"Error fetching recent evaluations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving recent evaluations: {str(e)}")


@router.get("/evaluations", summary="Get All Evaluations with Pagination")
async def get_evaluations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|final_score|grade)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    grade_filter: Optional[str] = Query(None, regex="^(excellent|good|average|poor)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated evaluations for the current user with optional filters.
    
    **Query Parameters:**
    - skip: Number of records to skip (for pagination)
    - limit: Number of records to return (max 100)
    - sort_by: Sort by field (created_at, final_score, grade)
    - sort_order: Sort order (asc or desc)
    - grade_filter: Filter by grade (excellent, good, average, poor)
    
    **For Teachers:** Returns all evaluations they created
    **For Students:** Returns their own evaluations
    """
    try:
        user_id = current_user.get("user_id")
        user_role = current_user.get("user_role")
        
        query = db.query(Evaluation)
        
        # Filter by user role
        if user_role == "student":
            query = query.filter(Evaluation.student_id == user_id)
        elif user_role == "teacher":
            query = query.filter(Evaluation.teacher_id == user_id)
        else:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Apply grade filter if provided
        if grade_filter:
            from database.models import GradeLevel
            grade_enum = GradeLevel[grade_filter.upper()]
            query = query.filter(Evaluation.grade == grade_enum)
        
        # Apply sorting
        if sort_order == "desc":
            query = query.order_by(desc(getattr(Evaluation, sort_by)))
        else:
            query = query.order_by(getattr(Evaluation, sort_by))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        evaluations = query.offset(skip).limit(limit).all()
        
        # Format response
        result_data = []
        for eval_obj in evaluations:
            student_name = "Unknown"
            subject = "General"
            
            if eval_obj.student:
                student_name = eval_obj.student.name
            
            if eval_obj.subject_ref:
                subject = eval_obj.subject_ref.name
            
            if eval_obj.created_at:
                time_diff = datetime.utcnow() - eval_obj.created_at
                if time_diff.days > 0:
                    time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
                elif time_diff.seconds >= 3600:
                    hours = time_diff.seconds // 3600
                    time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
                elif time_diff.seconds >= 60:
                    minutes = time_diff.seconds // 60
                    time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                else:
                    time_ago = "Just now"
            else:
                time_ago = "Unknown"
            
            result_data.append({
                "evaluation_id": eval_obj.evaluation_id,
                "student_name": student_name,
                "subject": subject,
                "final_score": float(eval_obj.final_score) if eval_obj.final_score else 0,
                "grade": eval_obj.grade.value if eval_obj.grade else "Unknown",
                "obtained_marks": float(eval_obj.obtained_marks) if eval_obj.obtained_marks else 0,
                "max_marks": eval_obj.max_marks,
                "time_ago": time_ago,
                "created_at": eval_obj.created_at.isoformat() if eval_obj.created_at else None,
                "is_reviewed": eval_obj.is_reviewed,
            })
        
        return {
            "status": "success",
            "message": "Evaluations retrieved successfully",
            "data": result_data,
            "total": total,
            "skip": skip,
            "limit": limit,
            "page": skip // limit + 1,
            "total_pages": (total + limit - 1) // limit
        }
    
    except Exception as e:
        import logging
        logging.error(f"Error fetching evaluations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving evaluations: {str(e)}")



async def get_all_dashboards(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all user dashboards (admin only).
    Shows overview of all users' dashboard states.
    """
    try:
        # Check if user is admin
        if UserRole(current_user.get("user_role")) != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can view all dashboards")
        
        dashboards = db.query(Dashboard).offset(skip).limit(limit).all()
        total = db.query(Dashboard).count()
        
        return {
            "status": "success",
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": [d.to_dict() for d in dashboards]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
