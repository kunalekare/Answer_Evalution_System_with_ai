"""
Database Models - AssessIQ
===========================
Complete SQLAlchemy models for the AssessIQ database.

Tables:
- Admin: System administrators
- Teacher: Teachers (managed by admins)
- Student: Students (managed by teachers)
- Class: Class/section management
- Subject: Subject master list
- ModelAnswer: Model answer keys
- Evaluation: AI evaluation results
- ManualEvaluation: Manual checking by teachers
- UploadedFile: Central file storage
- ActivityLog: Audit trail
"""

import uuid
from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    Boolean,
    Enum,
    ForeignKey,
    JSON,
    LargeBinary,
    Index,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func

from config.settings import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


# ========== Enums ==========
class UserRole(PyEnum):
    """User role enumeration."""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class UserStatus(PyEnum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class QuestionType(PyEnum):
    """Question type enumeration."""
    FACTUAL = "factual"
    DESCRIPTIVE = "descriptive"
    DIAGRAM = "diagram"
    MIXED = "mixed"


class GradeLevel(PyEnum):
    """Grade level enumeration."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"


class FileType(PyEnum):
    """File type enumeration."""
    MODEL_ANSWER = "model_answer"
    STUDENT_ANSWER = "student_answer"
    EVALUATION_RESULT = "evaluation_result"
    MANUAL_CHECK = "manual_check"
    OTHER = "other"


class ActivityType(PyEnum):
    """Activity type enumeration."""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EVALUATE = "evaluate"
    UPLOAD = "upload"
    DOWNLOAD = "download"


class GrievanceStatus(PyEnum):
    """Grievance status enumeration."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class GrievancePriority(PyEnum):
    """Grievance priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CommunityType(PyEnum):
    """Community type enumeration."""
    ADMIN_TEACHER = "admin_teacher"  # Admin manages teachers
    TEACHER_STUDENT = "teacher_student"  # Teacher manages students


class MemberRole(PyEnum):
    """Member role within a community."""
    OWNER = "owner"  # Admin or Teacher who owns the community
    MEMBER = "member"  # Regular member


class MessageType(PyEnum):
    """Message type enumeration."""
    TEXT = "text"
    ANNOUNCEMENT = "announcement"
    FILE = "file"
    SYSTEM = "system"


# ========== User Models ==========
class Admin(Base):
    """
    Admin Model
    ------------
    System administrators who manage teachers.
    """
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(String(50), unique=True, index=True, default=lambda: f"ADM{uuid.uuid4().hex[:8].upper()}")
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    profile_image = Column(String(500), nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    is_super_admin = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teachers_created = relationship("Teacher", back_populates="created_by_admin", foreign_keys="Teacher.created_by")
    activity_logs = relationship("ActivityLog", back_populates="admin", foreign_keys="ActivityLog.admin_id")

    def __repr__(self):
        return f"<Admin(id={self.admin_id}, name='{self.name}')>"

    def to_dict(self):
        return {
            "admin_id": self.admin_id,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "profile_image": self.profile_image,
            "status": self.status.value if self.status else None,
            "is_super_admin": self.is_super_admin,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Teacher(Base):
    """
    Teacher Model
    --------------
    Teachers who manage students and create evaluations.
    """
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(String(50), unique=True, index=True, default=lambda: f"TCH{uuid.uuid4().hex[:8].upper()}")
    employee_id = Column(String(50), unique=True, nullable=True)  # Official employee ID
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    designation = Column(String(100), nullable=True)
    profile_image = Column(String(500), nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    created_by = Column(Integer, ForeignKey("admins.id"), nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by_admin = relationship("Admin", back_populates="teachers_created", foreign_keys=[created_by])
    classes = relationship("Class", back_populates="teacher")
    students = relationship("Student", back_populates="teacher")
    model_answers = relationship("ModelAnswer", back_populates="teacher")
    evaluations = relationship("Evaluation", back_populates="teacher", foreign_keys="Evaluation.teacher_id")
    manual_evaluations = relationship("ManualEvaluation", back_populates="teacher", foreign_keys="ManualEvaluation.teacher_id")
    activity_logs = relationship("ActivityLog", back_populates="teacher", foreign_keys="ActivityLog.teacher_id")
    subjects_taught = relationship("TeacherSubject", back_populates="teacher")

    def __repr__(self):
        return f"<Teacher(id={self.teacher_id}, name='{self.name}')>"

    def to_dict(self):
        return {
            "teacher_id": self.teacher_id,
            "employee_id": self.employee_id,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "department": self.department,
            "designation": self.designation,
            "profile_image": self.profile_image,
            "status": self.status.value if self.status else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Student(Base):
    """
    Student Model
    --------------
    Students with roll numbers, managed by teachers.
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(50), unique=True, index=True, default=lambda: f"STU{uuid.uuid4().hex[:8].upper()}")
    roll_no = Column(String(50), nullable=False, index=True)
    enrollment_no = Column(String(50), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)  # Optional - for student login
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    profile_image = Column(String(500), nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    academic_year = Column(String(20), nullable=True)  # e.g., "2025-2026"
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint for roll_no within a class
    __table_args__ = (
        UniqueConstraint('roll_no', 'class_id', name='unique_roll_in_class'),
    )

    # Relationships
    class_info = relationship("Class", back_populates="students")
    teacher = relationship("Teacher", back_populates="students")
    evaluations = relationship("Evaluation", back_populates="student")
    manual_evaluations = relationship("ManualEvaluation", back_populates="student")
    uploaded_files = relationship("UploadedFile", back_populates="student")

    def __repr__(self):
        return f"<Student(roll_no={self.roll_no}, name='{self.name}')>"

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "roll_no": self.roll_no,
            "enrollment_no": self.enrollment_no,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "class_name": self.class_info.name if self.class_info else None,
            "class_id": self.class_id,
            "teacher_name": self.teacher.name if self.teacher else None,
            "status": self.status.value if self.status else None,
            "academic_year": self.academic_year,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ========== Class & Subject Models ==========
class Class(Base):
    """
    Class Model
    ------------
    Class/Section management.
    """
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(String(50), unique=True, index=True, default=lambda: f"CLS{uuid.uuid4().hex[:8].upper()}")
    name = Column(String(100), nullable=False)  # e.g., "6th Semester CSE-A"
    section = Column(String(20), nullable=True)  # e.g., "A", "B"
    semester = Column(Integer, nullable=True)
    department = Column(String(100), nullable=True)
    academic_year = Column(String(20), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)  # Class teacher
    max_students = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teacher = relationship("Teacher", back_populates="classes")
    students = relationship("Student", back_populates="class_info")
    subjects = relationship("ClassSubject", back_populates="class_info")

    def __repr__(self):
        return f"<Class(name='{self.name}', section='{self.section}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "class_id": self.class_id,
            "name": self.name,
            "section": self.section,
            "semester": self.semester,
            "department": self.department,
            "academic_year": self.academic_year,
            "teacher_name": self.teacher.name if self.teacher else None,
            "student_count": len(self.students) if self.students else 0,
            "max_students": self.max_students,
            "is_active": self.is_active,
        }


class Subject(Base):
    """
    Subject Model
    --------------
    Subject master list.
    """
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(String(50), unique=True, index=True, default=lambda: f"SUB{uuid.uuid4().hex[:8].upper()}")
    code = Column(String(20), unique=True, nullable=False)  # e.g., "CS601"
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    credits = Column(Integer, default=3)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    class_subjects = relationship("ClassSubject", back_populates="subject")
    teacher_subjects = relationship("TeacherSubject", back_populates="subject")
    model_answers = relationship("ModelAnswer", back_populates="subject_ref")
    evaluations = relationship("Evaluation", back_populates="subject_ref")

    def __repr__(self):
        return f"<Subject(code='{self.code}', name='{self.name}')>"

    def to_dict(self):
        return {
            "subject_id": self.subject_id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "credits": self.credits,
            "department": self.department,
            "is_active": self.is_active,
        }


class ClassSubject(Base):
    """
    Class-Subject Association
    --------------------------
    Maps subjects to classes.
    """
    __tablename__ = "class_subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)  # Subject teacher for this class
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('class_id', 'subject_id', name='unique_class_subject'),
    )

    # Relationships
    class_info = relationship("Class", back_populates="subjects")
    subject = relationship("Subject", back_populates="class_subjects")


class TeacherSubject(Base):
    """
    Teacher-Subject Association
    ----------------------------
    Maps subjects taught by teachers.
    """
    __tablename__ = "teacher_subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('teacher_id', 'subject_id', name='unique_teacher_subject'),
    )

    # Relationships
    teacher = relationship("Teacher", back_populates="subjects_taught")
    subject = relationship("Subject", back_populates="teacher_subjects")


# ========== File Storage ==========
class UploadedFile(Base):
    """
    Uploaded File Model
    --------------------
    Central file storage with metadata.
    """
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)  # UUID-based filename
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=True)  # in bytes
    mime_type = Column(String(100), nullable=True)
    file_type = Column(Enum(FileType), default=FileType.OTHER)
    
    # Associations
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=True)
    model_answer_id = Column(Integer, ForeignKey("model_answers.id"), nullable=True)
    
    # Extracted content
    extracted_text = Column(Text, nullable=True)  # OCR extracted text
    
    # Metadata
    checksum = Column(String(64), nullable=True)  # SHA-256 hash
    is_processed = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="uploaded_files")

    def __repr__(self):
        return f"<UploadedFile(id={self.file_id}, name='{self.original_filename}')>"

    def to_dict(self):
        return {
            "file_id": self.file_id,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "file_type": self.file_type.value if self.file_type else None,
            "is_processed": self.is_processed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ========== Model Answer ==========
class ModelAnswer(Base):
    """
    Model Answer Model
    -------------------
    Stores model answer keys for reuse.
    """
    __tablename__ = "model_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    answer_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Question details
    question_number = Column(String(50), nullable=True)
    question_text = Column(Text, nullable=True)
    answer_text = Column(Text, nullable=True)  # OCR extracted or typed text
    
    # File reference
    file_path = Column(String(500), nullable=True)
    
    # Subject & Teacher
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    
    # Evaluation criteria
    question_type = Column(Enum(QuestionType), default=QuestionType.DESCRIPTIVE)
    max_marks = Column(Integer, default=10)
    keywords = Column(JSON, nullable=True)  # List of important keywords
    key_concepts = Column(JSON, nullable=True)  # List of key concepts
    rubric = Column(JSON, nullable=True)  # Marking rubric
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subject_ref = relationship("Subject", back_populates="model_answers")
    teacher = relationship("Teacher", back_populates="model_answers")
    evaluations = relationship("Evaluation", back_populates="model_answer")

    def __repr__(self):
        return f"<ModelAnswer(id={self.answer_id}, question='{self.question_number}')>"

    def to_dict(self):
        return {
            "answer_id": self.answer_id,
            "question_number": self.question_number,
            "question_text": self.question_text,
            "question_type": self.question_type.value if self.question_type else None,
            "max_marks": self.max_marks,
            "keywords": self.keywords,
            "subject": self.subject_ref.name if self.subject_ref else None,
            "teacher": self.teacher.name if self.teacher else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ========== Evaluation Models ==========
class Evaluation(Base):
    """
    Evaluation Model
    -----------------
    Stores AI evaluation results.
    """
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evaluation_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # References
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    model_answer_id = Column(Integer, ForeignKey("model_answers.id"), nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    
    # Input data
    student_answer_text = Column(Text, nullable=True)
    student_answer_file = Column(String(500), nullable=True)
    question_type = Column(Enum(QuestionType), default=QuestionType.DESCRIPTIVE)
    
    # Scoring
    max_marks = Column(Integer, default=10)
    obtained_marks = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)  # Percentage
    grade = Column(Enum(GradeLevel), nullable=True)
    
    # Score breakdown
    semantic_score = Column(Float, nullable=True)
    keyword_score = Column(Float, nullable=True)
    diagram_score = Column(Float, nullable=True)
    length_penalty = Column(Float, default=0.0)
    
    # Concepts
    matched_keywords = Column(JSON, nullable=True)
    missing_keywords = Column(JSON, nullable=True)
    concept_coverage = Column(Float, nullable=True)
    
    # Feedback
    explanation = Column(Text, nullable=True)
    suggestions = Column(JSON, nullable=True)
    
    # Status
    is_reviewed = Column(Boolean, default=False)  # Teacher reviewed
    reviewed_by = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Metadata
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="evaluations")
    teacher = relationship("Teacher", back_populates="evaluations", foreign_keys=[teacher_id])
    model_answer = relationship("ModelAnswer", back_populates="evaluations")
    subject_ref = relationship("Subject", back_populates="evaluations")

    def __repr__(self):
        return f"<Evaluation(id={self.evaluation_id}, score={self.final_score})>"

    def to_dict(self):
        return {
            "evaluation_id": self.evaluation_id,
            "student": self.student.to_dict() if self.student else None,
            "subject": self.subject_ref.name if self.subject_ref else None,
            "question_type": self.question_type.value if self.question_type else None,
            "max_marks": self.max_marks,
            "obtained_marks": self.obtained_marks,
            "final_score": self.final_score,
            "grade": self.grade.value if self.grade else None,
            "score_breakdown": {
                "semantic_score": self.semantic_score,
                "keyword_score": self.keyword_score,
                "diagram_score": self.diagram_score,
                "length_penalty": self.length_penalty,
            },
            "concepts": {
                "matched": self.matched_keywords,
                "missing": self.missing_keywords,
                "coverage_percentage": self.concept_coverage,
            },
            "explanation": self.explanation,
            "suggestions": self.suggestions,
            "is_reviewed": self.is_reviewed,
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ManualEvaluation(Base):
    """
    Manual Evaluation Model
    ------------------------
    Teacher's manual checking and grading.
    """
    __tablename__ = "manual_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    manual_eval_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # References
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    ai_evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=True)  # Link to AI eval if exists
    
    # Answer files
    student_answer_file = Column(String(500), nullable=True)
    model_answer_file = Column(String(500), nullable=True)
    
    # Question details
    question_number = Column(String(50), nullable=True)
    question_text = Column(Text, nullable=True)
    
    # Manual grading
    max_marks = Column(Integer, default=10)
    obtained_marks = Column(Float, nullable=True)
    grade = Column(Enum(GradeLevel), nullable=True)
    
    # Annotations (for marking on answer sheet)
    annotations = Column(JSON, nullable=True)  # {x, y, text, color}
    
    # Feedback
    teacher_remarks = Column(Text, nullable=True)
    improvement_suggestions = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, in_progress, completed
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="manual_evaluations")
    teacher = relationship("Teacher", back_populates="manual_evaluations", foreign_keys=[teacher_id])

    def __repr__(self):
        return f"<ManualEvaluation(id={self.manual_eval_id}, marks={self.obtained_marks})>"

    def to_dict(self):
        return {
            "manual_eval_id": self.manual_eval_id,
            "student": self.student.to_dict() if self.student else None,
            "teacher": self.teacher.name if self.teacher else None,
            "question_number": self.question_number,
            "max_marks": self.max_marks,
            "obtained_marks": self.obtained_marks,
            "grade": self.grade.value if self.grade else None,
            "teacher_remarks": self.teacher_remarks,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ========== Activity Log ==========
class ActivityLog(Base):
    """
    Activity Log Model
    -------------------
    Audit trail for all actions.
    """
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Actor
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    user_role = Column(Enum(UserRole), nullable=True)
    
    # Action
    activity_type = Column(Enum(ActivityType), nullable=False)
    action = Column(String(100), nullable=False)  # e.g., "created_student", "uploaded_answer"
    resource_type = Column(String(50), nullable=True)  # e.g., "student", "evaluation"
    resource_id = Column(String(50), nullable=True)
    
    # Details
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    admin = relationship("Admin", back_populates="activity_logs", foreign_keys=[admin_id])
    teacher = relationship("Teacher", back_populates="activity_logs", foreign_keys=[teacher_id])

    def __repr__(self):
        return f"<ActivityLog(action='{self.action}', resource='{self.resource_type}')>"

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "user_role": self.user_role.value if self.user_role else None,
            "activity_type": self.activity_type.value if self.activity_type else None,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ========== Session/Token Management ==========
class RefreshToken(Base):
    """
    Refresh Token Model
    --------------------
    Stores refresh tokens for JWT authentication.
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    user_role = Column(Enum(UserRole), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<RefreshToken(user_id={self.user_id}, role={self.user_role})>"


# ========== Community Models ==========
class Community(Base):
    """
    Community Model
    ----------------
    WhatsApp-like community for communication.
    Admin creates communities for teachers.
    Teachers create communities for students.
    """
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    community_id = Column(String(50), unique=True, index=True, default=lambda: f"COM{uuid.uuid4().hex[:8].upper()}")
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    community_type = Column(Enum(CommunityType), nullable=False)
    profile_image = Column(String(500), nullable=True)
    
    # Owner (admin or teacher who created this)
    owner_admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    owner_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True)
    allow_member_posts = Column(Boolean, default=True)
    allow_file_sharing = Column(Boolean, default=True)
    
    # Stats
    member_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner_admin = relationship("Admin", foreign_keys=[owner_admin_id])
    owner_teacher = relationship("Teacher", foreign_keys=[owner_teacher_id])
    members = relationship("CommunityMember", back_populates="community", cascade="all, delete-orphan")
    messages = relationship("CommunityMessage", back_populates="community", cascade="all, delete-orphan")
    grievances = relationship("Grievance", back_populates="community", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Community(id={self.community_id}, name='{self.name}')>"

    def to_dict(self):
        return {
            "community_id": self.community_id,
            "name": self.name,
            "description": self.description,
            "community_type": self.community_type.value if self.community_type else None,
            "profile_image": self.profile_image,
            "owner": self.owner_admin.name if self.owner_admin else (self.owner_teacher.name if self.owner_teacher else None),
            "is_active": self.is_active,
            "allow_member_posts": self.allow_member_posts,
            "allow_file_sharing": self.allow_file_sharing,
            "member_count": self.member_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CommunityMember(Base):
    """
    Community Member Model
    -----------------------
    Tracks members of each community.
    """
    __tablename__ = "community_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    community_id = Column(Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False)
    
    # Member (can be admin, teacher, or student)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    
    # Role in community
    member_role = Column(Enum(MemberRole), default=MemberRole.MEMBER)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_muted = Column(Boolean, default=False)
    
    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('community_id', 'admin_id', name='unique_community_admin'),
        UniqueConstraint('community_id', 'teacher_id', name='unique_community_teacher'),
        UniqueConstraint('community_id', 'student_id', name='unique_community_student'),
    )

    # Relationships
    community = relationship("Community", back_populates="members")
    admin = relationship("Admin", foreign_keys=[admin_id])
    teacher = relationship("Teacher", foreign_keys=[teacher_id])
    student = relationship("Student", foreign_keys=[student_id])

    def __repr__(self):
        return f"<CommunityMember(community={self.community_id}, role={self.member_role})>"

    def to_dict(self):
        member_name = None
        member_id = None
        member_type = None
        
        if self.admin:
            member_name = self.admin.name
            member_id = self.admin.admin_id
            member_type = "admin"
        elif self.teacher:
            member_name = self.teacher.name
            member_id = self.teacher.teacher_id
            member_type = "teacher"
        elif self.student:
            member_name = self.student.name
            member_id = self.student.student_id
            member_type = "student"
            
        return {
            "community_id": self.community.community_id if self.community else None,
            "member_id": member_id,
            "member_name": member_name,
            "member_type": member_type,
            "member_role": self.member_role.value if self.member_role else None,
            "is_active": self.is_active,
            "is_muted": self.is_muted,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class CommunityMessage(Base):
    """
    Community Message Model
    ------------------------
    Messages within a community (like WhatsApp).
    """
    __tablename__ = "community_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    community_id = Column(Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False)
    
    # Sender (can be admin, teacher, or student)
    sender_admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    sender_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    sender_student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    
    # Message content
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    content = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    
    # Reply to (for threaded messages)
    reply_to_id = Column(Integer, ForeignKey("community_messages.id"), nullable=True)
    
    # Status
    is_pinned = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    community = relationship("Community", back_populates="messages")
    sender_admin = relationship("Admin", foreign_keys=[sender_admin_id])
    sender_teacher = relationship("Teacher", foreign_keys=[sender_teacher_id])
    sender_student = relationship("Student", foreign_keys=[sender_student_id])
    reply_to = relationship("CommunityMessage", remote_side=[id])

    def __repr__(self):
        return f"<CommunityMessage(id={self.message_id}, type={self.message_type})>"

    def to_dict(self):
        sender_name = None
        sender_id = None
        sender_type = None
        
        if self.sender_admin:
            sender_name = self.sender_admin.name
            sender_id = self.sender_admin.admin_id
            sender_type = "admin"
        elif self.sender_teacher:
            sender_name = self.sender_teacher.name
            sender_id = self.sender_teacher.teacher_id
            sender_type = "teacher"
        elif self.sender_student:
            sender_name = self.sender_student.name
            sender_id = self.sender_student.student_id
            sender_type = "student"
            
        return {
            "message_id": self.message_id,
            "community_id": self.community.community_id if self.community else None,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "sender_type": sender_type,
            "message_type": self.message_type.value if self.message_type else None,
            "content": self.content,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "is_pinned": self.is_pinned,
            "is_deleted": self.is_deleted,
            "reply_to_id": self.reply_to.message_id if self.reply_to else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Grievance(Base):
    """
    Grievance Model
    ----------------
    Complaint/grievance handling system.
    Students can raise grievances to teachers.
    Teachers can escalate to admin.
    """
    __tablename__ = "grievances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    grievance_id = Column(String(50), unique=True, index=True, default=lambda: f"GRV{uuid.uuid4().hex[:8].upper()}")
    
    # Community (optional - can be general grievance)
    community_id = Column(Integer, ForeignKey("communities.id", ondelete="SET NULL"), nullable=True)
    
    # Complainant
    complainant_student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    complainant_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    
    # Assigned to
    assigned_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    assigned_admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    
    # Grievance details
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)  # e.g., "Academic", "Behavioral", "Technical"
    priority = Column(Enum(GrievancePriority), default=GrievancePriority.MEDIUM)
    
    # Attachments
    attachments = Column(JSON, nullable=True)  # List of file paths
    
    # Status
    status = Column(Enum(GrievanceStatus), default=GrievanceStatus.PENDING)
    
    # Resolution
    resolution = Column(Text, nullable=True)
    resolved_by_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    resolved_by_admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Escalation
    escalated_at = Column(DateTime, nullable=True)
    escalation_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    community = relationship("Community", back_populates="grievances")
    complainant_student = relationship("Student", foreign_keys=[complainant_student_id])
    complainant_teacher = relationship("Teacher", foreign_keys=[complainant_teacher_id])
    assigned_teacher = relationship("Teacher", foreign_keys=[assigned_teacher_id])
    assigned_admin = relationship("Admin", foreign_keys=[assigned_admin_id])
    resolved_by_teacher = relationship("Teacher", foreign_keys=[resolved_by_teacher_id])
    resolved_by_admin = relationship("Admin", foreign_keys=[resolved_by_admin_id])
    responses = relationship("GrievanceResponse", back_populates="grievance", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Grievance(id={self.grievance_id}, status={self.status})>"

    def to_dict(self):
        complainant_name = None
        complainant_type = None
        
        if self.complainant_student:
            complainant_name = self.complainant_student.name
            complainant_type = "student"
        elif self.complainant_teacher:
            complainant_name = self.complainant_teacher.name
            complainant_type = "teacher"
            
        return {
            "grievance_id": self.grievance_id,
            "community_id": self.community.community_id if self.community else None,
            "complainant_name": complainant_name,
            "complainant_type": complainant_type,
            "assigned_to": self.assigned_admin.name if self.assigned_admin else (self.assigned_teacher.name if self.assigned_teacher else None),
            "subject": self.subject,
            "description": self.description,
            "category": self.category,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "resolution": self.resolution,
            "resolved_by": self.resolved_by_admin.name if self.resolved_by_admin else (self.resolved_by_teacher.name if self.resolved_by_teacher else None),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "escalated_at": self.escalated_at.isoformat() if self.escalated_at else None,
            "escalation_reason": self.escalation_reason,
            "attachments": self.attachments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class GrievanceResponse(Base):
    """
    Grievance Response Model
    -------------------------
    Responses/comments on grievances.
    """
    __tablename__ = "grievance_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    response_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    grievance_id = Column(Integer, ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False)
    
    # Responder
    responder_admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    responder_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    responder_student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    
    # Response content
    content = Column(Text, nullable=False)
    attachments = Column(JSON, nullable=True)
    
    # Action taken (if any)
    action_taken = Column(String(100), nullable=True)  # e.g., "status_changed", "escalated", "resolved"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    grievance = relationship("Grievance", back_populates="responses")
    responder_admin = relationship("Admin", foreign_keys=[responder_admin_id])
    responder_teacher = relationship("Teacher", foreign_keys=[responder_teacher_id])
    responder_student = relationship("Student", foreign_keys=[responder_student_id])

    def __repr__(self):
        return f"<GrievanceResponse(id={self.response_id})>"

    def to_dict(self):
        responder_name = None
        responder_type = None
        
        if self.responder_admin:
            responder_name = self.responder_admin.name
            responder_type = "admin"
        elif self.responder_teacher:
            responder_name = self.responder_teacher.name
            responder_type = "teacher"
        elif self.responder_student:
            responder_name = self.responder_student.name
            responder_type = "student"
            
        return {
            "response_id": self.response_id,
            "grievance_id": self.grievance.grievance_id if self.grievance else None,
            "responder_name": responder_name,
            "responder_type": responder_type,
            "content": self.content,
            "attachments": self.attachments,
            "action_taken": self.action_taken,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ========== Database Operations ==========
class DatabaseManager:
    """
    Database Manager
    -----------------
    Helper class for database operations.
    """
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    # ===== Statistics =====
    def get_statistics(self) -> dict:
        """Get overall statistics."""
        session = self.get_session()
        try:
            stats = {
                "total_admins": session.query(func.count(Admin.id)).scalar() or 0,
                "total_teachers": session.query(func.count(Teacher.id)).filter(Teacher.status == UserStatus.ACTIVE).scalar() or 0,
                "total_students": session.query(func.count(Student.id)).filter(Student.status == UserStatus.ACTIVE).scalar() or 0,
                "total_classes": session.query(func.count(Class.id)).filter(Class.is_active == True).scalar() or 0,
                "total_subjects": session.query(func.count(Subject.id)).filter(Subject.is_active == True).scalar() or 0,
                "total_evaluations": session.query(func.count(Evaluation.id)).scalar() or 0,
                "total_manual_evaluations": session.query(func.count(ManualEvaluation.id)).scalar() or 0,
                "average_score": session.query(func.avg(Evaluation.final_score)).scalar() or 0,
            }
            return stats
        finally:
            session.close()


# ========== Dependency Injection ==========
def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== Initialize Database ==========
def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


# Create singleton database manager
db_manager = DatabaseManager()

# Initialize on module load
init_db()
