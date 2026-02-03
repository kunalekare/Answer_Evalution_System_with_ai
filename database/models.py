"""
Database Models
================
SQLAlchemy models for the AssessIQ database.

Tables:
- Evaluations: Stores evaluation metadata and results
- ModelAnswers: Stores model answer keys for reuse
- Students: Stores student information (optional)
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
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID

from config.settings import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


# ========== Enums ==========
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


# ========== Models ==========
class Student(Base):
    """
    Student Model (Optional)
    -------------------------
    Stores student information for tracking purposes.
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(50), unique=True, index=True)  # Roll number
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=True)
    class_name = Column(String(50), nullable=True)  # e.g., "6th Semester CSE"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    evaluations = relationship("Evaluation", back_populates="student")
    
    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.name}')>"


class ModelAnswer(Base):
    """
    Model Answer Storage
    ---------------------
    Stores model answer keys for reuse across multiple evaluations.
    """
    __tablename__ = "model_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    answer_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    subject = Column(String(100), nullable=True, index=True)
    question_number = Column(String(50), nullable=True)
    question_text = Column(Text, nullable=True)
    answer_text = Column(Text, nullable=True)  # OCR extracted text
    file_path = Column(String(500), nullable=True)  # Original file path
    question_type = Column(Enum(QuestionType), default=QuestionType.DESCRIPTIVE)
    max_marks = Column(Integer, default=10)
    keywords = Column(JSON, nullable=True)  # List of keywords
    created_by = Column(String(100), nullable=True)  # Teacher ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    evaluations = relationship("Evaluation", back_populates="model_answer")
    
    def __repr__(self):
        return f"<ModelAnswer(id={self.id}, subject='{self.subject}')>"


class Evaluation(Base):
    """
    Evaluation Results
    -------------------
    Stores complete evaluation results including scores and feedback.
    """
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evaluation_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # References
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    model_answer_id = Column(Integer, ForeignKey("model_answers.id"), nullable=True)
    
    # Input data
    student_answer_text = Column(Text, nullable=True)
    student_answer_file = Column(String(500), nullable=True)
    question_type = Column(Enum(QuestionType), default=QuestionType.DESCRIPTIVE)
    subject = Column(String(100), nullable=True)
    
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
    matched_keywords = Column(JSON, nullable=True)  # List of matched keywords
    missing_keywords = Column(JSON, nullable=True)  # List of missing keywords
    concept_coverage = Column(Float, nullable=True)  # Percentage
    
    # Feedback
    explanation = Column(Text, nullable=True)
    suggestions = Column(JSON, nullable=True)  # List of suggestions
    
    # Metadata
    processing_time = Column(Float, nullable=True)  # Seconds
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="evaluations")
    model_answer = relationship("ModelAnswer", back_populates="evaluations")
    
    def __repr__(self):
        return f"<Evaluation(id={self.evaluation_id}, score={self.final_score})>"
    
    def to_dict(self):
        """Convert evaluation to dictionary."""
        return {
            "evaluation_id": self.evaluation_id,
            "student_id": self.student.student_id if self.student else None,
            "subject": self.subject,
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
            "processing_time": self.processing_time,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }


class EvaluationLog(Base):
    """
    Evaluation Activity Log
    ------------------------
    Logs all evaluation activities for auditing.
    """
    __tablename__ = "evaluation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evaluation_id = Column(String(36), index=True)
    action = Column(String(50), nullable=False)  # e.g., "created", "viewed", "deleted"
    details = Column(JSON, nullable=True)
    user_id = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<EvaluationLog(action='{self.action}', evaluation='{self.evaluation_id}')>"


# ========== Database Operations ==========
class DatabaseManager:
    """
    Database Manager
    -----------------
    Helper class for database operations.
    """
    
    def __init__(self):
        """Initialize database manager."""
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
    
    # ===== Evaluation Operations =====
    def save_evaluation(self, evaluation_data: dict) -> Evaluation:
        """Save a new evaluation result."""
        session = self.get_session()
        try:
            evaluation = Evaluation(
                evaluation_id=evaluation_data.get("evaluation_id", str(uuid.uuid4())),
                student_answer_text=evaluation_data.get("student_answer_text"),
                student_answer_file=evaluation_data.get("student_answer_file"),
                question_type=QuestionType(evaluation_data.get("question_type", "descriptive")),
                subject=evaluation_data.get("subject"),
                max_marks=evaluation_data.get("max_marks", 10),
                obtained_marks=evaluation_data.get("obtained_marks"),
                final_score=evaluation_data.get("final_score"),
                grade=GradeLevel(evaluation_data.get("grade", "average")),
                semantic_score=evaluation_data.get("semantic_score"),
                keyword_score=evaluation_data.get("keyword_score"),
                diagram_score=evaluation_data.get("diagram_score"),
                length_penalty=evaluation_data.get("length_penalty", 0),
                matched_keywords=evaluation_data.get("matched_keywords"),
                missing_keywords=evaluation_data.get("missing_keywords"),
                concept_coverage=evaluation_data.get("concept_coverage"),
                explanation=evaluation_data.get("explanation"),
                suggestions=evaluation_data.get("suggestions"),
                processing_time=evaluation_data.get("processing_time"),
            )
            session.add(evaluation)
            session.commit()
            session.refresh(evaluation)
            return evaluation
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_evaluation(self, evaluation_id: str) -> Optional[Evaluation]:
        """Get evaluation by ID."""
        session = self.get_session()
        try:
            return session.query(Evaluation).filter(
                Evaluation.evaluation_id == evaluation_id
            ).first()
        finally:
            session.close()
    
    def get_all_evaluations(
        self, 
        limit: int = 50, 
        offset: int = 0,
        grade_filter: str = None
    ) -> List[Evaluation]:
        """Get all evaluations with optional filtering."""
        session = self.get_session()
        try:
            query = session.query(Evaluation)
            
            if grade_filter:
                query = query.filter(Evaluation.grade == GradeLevel(grade_filter))
            
            query = query.order_by(Evaluation.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            return query.all()
        finally:
            session.close()
    
    def delete_evaluation(self, evaluation_id: str) -> bool:
        """Delete an evaluation."""
        session = self.get_session()
        try:
            evaluation = session.query(Evaluation).filter(
                Evaluation.evaluation_id == evaluation_id
            ).first()
            
            if evaluation:
                session.delete(evaluation)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_statistics(self) -> dict:
        """Get evaluation statistics."""
        session = self.get_session()
        try:
            from sqlalchemy import func
            
            total = session.query(func.count(Evaluation.id)).scalar()
            
            if total == 0:
                return {
                    "total_evaluations": 0,
                    "average_score": 0,
                    "grade_distribution": {},
                }
            
            avg_score = session.query(func.avg(Evaluation.final_score)).scalar() or 0
            
            # Grade distribution
            grade_counts = session.query(
                Evaluation.grade, 
                func.count(Evaluation.id)
            ).group_by(Evaluation.grade).all()
            
            grade_distribution = {
                g.value if g else "unknown": count 
                for g, count in grade_counts
            }
            
            return {
                "total_evaluations": total,
                "average_score": round(avg_score, 2),
                "grade_distribution": grade_distribution,
            }
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


# Initialize on module load if in development
if settings.DEBUG:
    init_db()
