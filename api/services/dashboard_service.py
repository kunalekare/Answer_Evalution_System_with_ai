"""
Dashboard Service
=================
Handles dashboard initialization and metric updates.
- Initializes dashboard with zero values on first user access
- Updates metrics when user performs actions
- Tracks trends and historical data
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database.models import (
    Dashboard, DashboardMetric, UserRole,
    Teacher, Student,
    Evaluation, ManualEvaluation,
    ActivityLog, Grievance,
    UploadedFile, ModelAnswer,
    Class
)


class DashboardService:
    """Service for managing dashboard operations."""
    
    @staticmethod
    def get_dashboard_by_user(
        db: Session,
        user_id: int,
        user_role: UserRole
    ) -> Optional[Dashboard]:
        """Get dashboard for a specific user by role."""
        if user_role == UserRole.ADMIN:
            return db.query(Dashboard).filter_by(admin_id=user_id).first()
        elif user_role == UserRole.TEACHER:
            return db.query(Dashboard).filter_by(teacher_id=user_id).first()
        elif user_role == UserRole.STUDENT:
            return db.query(Dashboard).filter_by(student_id=user_id).first()
        return None
    
    @staticmethod
    def get_or_create_dashboard(
        db: Session,
        user_id: int,
        user_role: UserRole
    ) -> Dashboard:
        """
        Get existing dashboard or create new one with zero values.
        Called on user's first visit to dashboard.
        
        Args:
            db: Database session
            user_id: User's database ID
            user_role: User's role (admin/teacher/student)
        
        Returns:
            Dashboard instance
        """
        # Query for existing dashboard
        dashboard = None
        
        if user_role == UserRole.ADMIN:
            dashboard = db.query(Dashboard).filter_by(admin_id=user_id).first()
        elif user_role == UserRole.TEACHER:
            dashboard = db.query(Dashboard).filter_by(teacher_id=user_id).first()
        elif user_role == UserRole.STUDENT:
            dashboard = db.query(Dashboard).filter_by(student_id=user_id).first()
        
        # If dashboard exists, just update last accessed time
        if dashboard:
            dashboard.is_first_visit = False
            dashboard.updated_at = datetime.utcnow()
            db.commit()
            return dashboard
        
        # Create new dashboard with all zeros
        dashboard = Dashboard(
            user_role=user_role,
            # All numeric fields default to 0/0.0 as set in model
        )
        
        # Assign user based on role
        if user_role == UserRole.ADMIN:
            dashboard.admin_id = user_id
        elif user_role == UserRole.TEACHER:
            dashboard.teacher_id = user_id
        elif user_role == UserRole.STUDENT:
            dashboard.student_id = user_id
        
        db.add(dashboard)
        db.commit()
        db.refresh(dashboard)
        
        return dashboard
    
    @staticmethod
    def update_login_count(db: Session, dashboard: Dashboard) -> Dashboard:
        """Increment total logins."""
        dashboard.total_logins += 1
        dashboard.last_activity_at = datetime.utcnow()
        db.commit()
        return dashboard
    
    @staticmethod
    def increment_total_activities(db: Session, dashboard: Dashboard) -> Dashboard:
        """Increment total activities counter."""
        dashboard.total_activities += 1
        dashboard.last_activity_at = datetime.utcnow()
        db.commit()
        return dashboard
    
    # ===== ADMIN DASHBOARD UPDATES =====
    
    @staticmethod
    def update_admin_metrics(db: Session, admin_id: int) -> Dashboard:
        """
        Recalculate admin dashboard metrics from database.
        Called after admin creates teacher or takes actions.
        """
        dashboard = db.query(Dashboard).filter_by(admin_id=admin_id).first()
        if not dashboard:
            return None
        
        # Count teachers created by this admin
        dashboard.teachers_created = db.query(Teacher).filter_by(created_by=admin_id).count()
        
        # Count active teachers
        dashboard.teachers_active = db.query(Teacher).filter(
            and_(Teacher.created_by == admin_id, Teacher.status.value == 'active')
        ).count()
        
        # Count students managed (across all teachers)
        dashboard.students_managed = db.query(Student).join(Teacher).filter(
            Teacher.created_by == admin_id
        ).count()
        
        # Count evaluations overseen
        dashboard.evaluations_overseen = db.query(Evaluation).join(Teacher).filter(
            Teacher.created_by == admin_id
        ).count()
        
        dashboard.last_activity_at = datetime.utcnow()
        db.commit()
        return dashboard
    
    # ===== TEACHER DASHBOARD UPDATES =====
    
    @staticmethod
    def update_teacher_metrics(db: Session, teacher_id: int) -> Dashboard:
        """
        Recalculate teacher dashboard metrics from database.
        Called after teacher creates class, does evaluation, etc.
        """
        dashboard = db.query(Dashboard).filter_by(teacher_id=teacher_id).first()
        if not dashboard:
            return None
        
        # Count students taught
        dashboard.students_taught = db.query(Student).filter_by(teacher_id=teacher_id).count()
        
        # Count classes managed
        dashboard.classes_managed = db.query(Class).filter_by(teacher_id=teacher_id).count()
        
        # Count AI evaluations created
        dashboard.evaluations_created = db.query(Evaluation).filter_by(teacher_id=teacher_id).count()
        
        # Count manual evaluations
        dashboard.manual_evaluations_done = db.query(ManualEvaluation).filter_by(teacher_id=teacher_id).count()
        
        # Count model answers uploaded
        dashboard.model_answers_uploaded = db.query(ModelAnswer).filter_by(teacher_id=teacher_id).count()
        
        # Total evaluations
        dashboard.total_evaluations = dashboard.evaluations_created + dashboard.manual_evaluations_done
        
        # Calculate average evaluation score
        avg_score = db.query(Evaluation.final_score).filter(
            Evaluation.teacher_id == teacher_id
        ).values(Evaluation.final_score)
        
        scores = [score[0] for score in avg_score if score[0] is not None]
        dashboard.average_evaluation_score = sum(scores) / len(scores) if scores else 0.0
        
        # Count documents uploaded
        dashboard.documents_uploaded = db.query(UploadedFile).filter_by(teacher_id=teacher_id).count()
        
        dashboard.last_activity_at = datetime.utcnow()
        db.commit()
        return dashboard
    
    # ===== STUDENT DASHBOARD UPDATES =====
    
    @staticmethod
    def update_student_metrics(db: Session, student_id: int) -> Dashboard:
        """
        Recalculate student dashboard metrics from database.
        Called after student receives evaluation, submits answers, etc.
        """
        dashboard = db.query(Dashboard).filter_by(student_id=student_id).first()
        if not dashboard:
            return None
        
        # Count evaluations received
        evaluations = db.query(Evaluation).filter_by(student_id=student_id).all()
        dashboard.evaluations_received = len(evaluations)
        
        # Calculate scores
        scores = [e.final_score for e in evaluations if e.final_score is not None]
        
        if scores:
            dashboard.average_score = sum(scores) / len(scores)
            dashboard.highest_score = max(scores)
            dashboard.lowest_score = min(scores)
        else:
            dashboard.average_score = 0.0
            dashboard.highest_score = 0.0
            dashboard.lowest_score = 0.0
        
        # Get feedback count
        dashboard.total_feedback_received = sum(
            1 for e in evaluations if e.feedback and len(e.feedback) > 0
        )
        
        # Count assignments received (model answers assigned to student's class)
        student = db.query(Student).filter_by(id=student_id).first()
        if student:
            dashboard.assignments_received = db.query(ModelAnswer).filter_by(
                class_id=student.class_id
            ).count()
        
        dashboard.last_activity_at = datetime.utcnow()
        db.commit()
        return dashboard
    
    # ===== ENGAGEMENT METRICS =====
    
    @staticmethod
    def increment_grievances_filed(db: Session, dashboard: Dashboard) -> Dashboard:
        """Increment grievances filed count."""
        dashboard.grievances_filed += 1
        db.commit()
        return dashboard
    
    @staticmethod
    def increment_community_messages(db: Session, dashboard: Dashboard) -> Dashboard:
        """Increment community messages sent count."""
        dashboard.community_messages_sent += 1
        db.commit()
        return dashboard
    
    @staticmethod
    def increment_documents_uploaded(db: Session, dashboard: Dashboard) -> Dashboard:
        """Increment documents uploaded count."""
        dashboard.documents_uploaded += 1
        db.commit()
        return dashboard
    
    @staticmethod
    def increment_documents_downloaded(db: Session, dashboard: Dashboard) -> Dashboard:
        """Increment documents downloaded count."""
        dashboard.documents_downloaded += 1
        db.commit()
        return dashboard
    
    # ===== HISTORICAL METRICS =====
    
    @staticmethod
    def record_metric(
        db: Session,
        dashboard: Dashboard,
        metric_name: str,
        metric_value: float,
        period_type: str = "daily",
        context: Optional[Dict[str, Any]] = None
    ) -> DashboardMetric:
        """
        Record a metric snapshot for historical tracking.
        Useful for charting trends over time.
        
        Args:
            db: Database session
            dashboard: Dashboard instance
            metric_name: Name of the metric (e.g., 'evaluations_created')
            metric_value: Value to record
            period_type: 'daily', 'weekly', 'monthly'
            context: Additional context JSON
        
        Returns:
            DashboardMetric instance
        """
        metric = DashboardMetric(
            dashboard_id=dashboard.id,
            metric_name=metric_name,
            metric_value=metric_value,
            period_type=period_type,
            context=context or {}
        )
        
        db.add(metric)
        db.commit()
        db.refresh(metric)
        
        return metric
    
    @staticmethod
    def get_metric_history(
        db: Session,
        dashboard: Dashboard,
        metric_name: str,
        days: int = 30
    ) -> list:
        """
        Get historical data for a metric over N days for charting.
        
        Args:
            db: Database session
            dashboard: Dashboard instance
            metric_name: Name of the metric
            days: Number of days to retrieve
        
        Returns:
            List of DashboardMetric records
        """
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        metrics = db.query(DashboardMetric).filter(
            and_(
                DashboardMetric.dashboard_id == dashboard.id,
                DashboardMetric.metric_name == metric_name,
                DashboardMetric.created_at >= start_date
            )
        ).order_by(DashboardMetric.created_at.asc()).all()
        
        return metrics
    
    @staticmethod
    def get_daily_summary(db: Session, dashboard: Dashboard) -> Dict[str, Any]:
        """
        Get a summary of today's activities.
        
        Args:
            db: Database session
            dashboard: Dashboard instance
        
        Returns:
            Dictionary with today's summary
        """
        from datetime import timedelta
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Count today's activities
        today_activities = db.query(ActivityLog).filter(
            and_(
                ActivityLog.created_at >= today_start,
                ActivityLog.created_at < today_end
            )
        ).count()
        
        return {
            "date": today_start.date().isoformat(),
            "total_activities": dashboard.total_activities,
            "today_activities": today_activities,
            "total_logins": dashboard.total_logins,
            "last_activity": dashboard.last_activity_at.isoformat() if dashboard.last_activity_at else None,
        }
    
    @staticmethod
    def reset_dashboard(db: Session, dashboard: Dashboard) -> Dashboard:
        """
        Reset all dashboard metrics to zero (for new period/semester).
        """
        dashboard.reset_to_zero()
        db.commit()
        return dashboard


# Helper function for route dependency
def get_dashboard_service():
    """Dependency injection for DashboardService."""
    return DashboardService()
