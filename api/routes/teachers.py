"""
Teacher Routes - AssessIQ
==========================
API endpoints for teacher operations.

Endpoints:
- GET /teacher/dashboard - Teacher dashboard
- CRUD /teacher/students - Student management
- CRUD /teacher/classes - Class management
- CRUD /teacher/subjects - Subject management
- GET /teacher/evaluations - View evaluations
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database.models import (
    get_db, Teacher, Student, Class, Subject, ClassSubject, TeacherSubject,
    Evaluation, ManualEvaluation, ModelAnswer,
    UserStatus, UserRole
)
from api.services.auth_service import (
    auth_service, get_current_teacher, get_current_teacher_only, 
    TokenData, hash_password
)

logger = logging.getLogger("AssessIQ.Teacher")

router = APIRouter()


# ========== Request/Response Models ==========
class CreateStudentRequest(BaseModel):
    """Create student request."""
    roll_no: str
    name: str
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    enrollment_no: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    class_id: Optional[int] = None
    academic_year: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "roll_no": "2024001",
                "name": "Alice Johnson",
                "email": "alice@student.com",
                "password": "student123",
                "phone": "9876543210",
                "enrollment_no": "ENR2024001",
                "gender": "Female",
                "academic_year": "2025-2026"
            }
        }


class UpdateStudentRequest(BaseModel):
    """Update student request."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    roll_no: Optional[str] = None
    enrollment_no: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    class_id: Optional[int] = None
    status: Optional[str] = None


class CreateClassRequest(BaseModel):
    """Create class request."""
    name: str
    section: Optional[str] = None
    semester: Optional[int] = None
    department: Optional[str] = None
    academic_year: Optional[str] = None
    max_students: Optional[int] = 60


class UpdateClassRequest(BaseModel):
    """Update class request."""
    name: Optional[str] = None
    section: Optional[str] = None
    semester: Optional[int] = None
    department: Optional[str] = None
    academic_year: Optional[str] = None
    max_students: Optional[int] = None
    is_active: Optional[bool] = None


class CreateSubjectRequest(BaseModel):
    """Create subject request."""
    code: str
    name: str
    description: Optional[str] = None
    credits: Optional[int] = 3
    department: Optional[str] = None


class BulkCreateStudentsRequest(BaseModel):
    """Bulk create students request."""
    students: List[CreateStudentRequest]
    class_id: Optional[int] = None


# ========== Dashboard ==========
@router.get("/dashboard")
async def teacher_dashboard(
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    Get teacher dashboard statistics.
    """
    teacher = db.query(Teacher).filter(Teacher.id == current_user.user_id).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Get counts
    total_students = db.query(func.count(Student.id)).filter(
        Student.teacher_id == teacher.id,
        Student.status == UserStatus.ACTIVE
    ).scalar() or 0
    
    total_classes = db.query(func.count(Class.id)).filter(
        Class.teacher_id == teacher.id,
        Class.is_active == True
    ).scalar() or 0
    
    total_evaluations = db.query(func.count(Evaluation.id)).filter(
        Evaluation.teacher_id == teacher.id
    ).scalar() or 0
    
    total_manual_evals = db.query(func.count(ManualEvaluation.id)).filter(
        ManualEvaluation.teacher_id == teacher.id
    ).scalar() or 0
    
    pending_reviews = db.query(func.count(Evaluation.id)).filter(
        Evaluation.teacher_id == teacher.id,
        Evaluation.is_reviewed == False
    ).scalar() or 0
    
    avg_score = db.query(func.avg(Evaluation.final_score)).filter(
        Evaluation.teacher_id == teacher.id
    ).scalar() or 0
    
    # Recent evaluations
    recent_evals = db.query(Evaluation).filter(
        Evaluation.teacher_id == teacher.id
    ).order_by(desc(Evaluation.created_at)).limit(10).all()
    
    # Recent students
    recent_students = db.query(Student).filter(
        Student.teacher_id == teacher.id
    ).order_by(desc(Student.created_at)).limit(5).all()
    
    return {
        "success": True,
        "data": {
            "teacher": teacher.to_dict(),
            "statistics": {
                "total_students": total_students,
                "total_classes": total_classes,
                "total_evaluations": total_evaluations,
                "total_manual_evaluations": total_manual_evals,
                "pending_reviews": pending_reviews,
                "average_score": round(avg_score, 2) if avg_score else 0
            },
            "recent_evaluations": [e.to_dict() for e in recent_evals],
            "recent_students": [s.to_dict() for s in recent_students]
        }
    }


# ========== Student Management ==========
@router.get("/students")
async def list_students(
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    class_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """
    List all students managed by this teacher.
    """
    query = db.query(Student).filter(Student.teacher_id == current_user.user_id)
    
    if class_id:
        query = query.filter(Student.class_id == class_id)
    
    if status:
        query = query.filter(Student.status == UserStatus(status))
    
    if search:
        query = query.filter(
            (Student.name.ilike(f"%{search}%")) |
            (Student.roll_no.ilike(f"%{search}%")) |
            (Student.email.ilike(f"%{search}%"))
        )
    
    total = query.count()
    offset = (page - 1) * limit
    students = query.order_by(Student.roll_no).offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "data": {
            "students": [s.to_dict() for s in students],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    }


@router.post("/students", status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: CreateStudentRequest,
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    Create a new student.
    """
    # Check if email exists (if provided)
    if student_data.email:
        existing = db.query(Student).filter(Student.email == student_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if enrollment_no exists (if provided)
    if student_data.enrollment_no:
        existing = db.query(Student).filter(
            Student.enrollment_no == student_data.enrollment_no
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enrollment number already exists"
            )
    
    # Check roll_no uniqueness within class
    if student_data.class_id:
        existing = db.query(Student).filter(
            Student.roll_no == student_data.roll_no,
            Student.class_id == student_data.class_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Roll number already exists in this class"
            )
    
    # Parse date of birth if provided
    dob = None
    if student_data.date_of_birth:
        try:
            dob = datetime.fromisoformat(student_data.date_of_birth)
        except:
            pass
    
    # Create student
    student = Student(
        roll_no=student_data.roll_no,
        name=student_data.name,
        email=student_data.email,
        password_hash=hash_password(student_data.password) if student_data.password else None,
        phone=student_data.phone,
        enrollment_no=student_data.enrollment_no,
        gender=student_data.gender,
        date_of_birth=dob,
        address=student_data.address,
        class_id=student_data.class_id,
        teacher_id=current_user.user_id,
        academic_year=student_data.academic_year
    )
    
    db.add(student)
    db.commit()
    db.refresh(student)
    
    logger.info(f"Student created: {student.student_id} by teacher {current_user.user_id}")
    
    return {
        "success": True,
        "message": "Student created successfully",
        "data": student.to_dict()
    }


@router.post("/students/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_students(
    bulk_data: BulkCreateStudentsRequest,
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    Create multiple students at once.
    """
    created = []
    errors = []
    
    for idx, student_data in enumerate(bulk_data.students):
        try:
            # Check email uniqueness
            if student_data.email:
                existing = db.query(Student).filter(Student.email == student_data.email).first()
                if existing:
                    errors.append({"index": idx, "roll_no": student_data.roll_no, "error": "Email already exists"})
                    continue
            
            class_id = student_data.class_id or bulk_data.class_id
            
            # Check roll_no uniqueness
            if class_id:
                existing = db.query(Student).filter(
                    Student.roll_no == student_data.roll_no,
                    Student.class_id == class_id
                ).first()
                if existing:
                    errors.append({"index": idx, "roll_no": student_data.roll_no, "error": "Roll number already exists in class"})
                    continue
            
            dob = None
            if student_data.date_of_birth:
                try:
                    dob = datetime.fromisoformat(student_data.date_of_birth)
                except:
                    pass
            
            student = Student(
                roll_no=student_data.roll_no,
                name=student_data.name,
                email=student_data.email,
                password_hash=hash_password(student_data.password) if student_data.password else None,
                phone=student_data.phone,
                enrollment_no=student_data.enrollment_no,
                gender=student_data.gender,
                date_of_birth=dob,
                address=student_data.address,
                class_id=class_id,
                teacher_id=current_user.user_id,
                academic_year=student_data.academic_year
            )
            db.add(student)
            created.append(student_data.roll_no)
        except Exception as e:
            errors.append({"index": idx, "roll_no": student_data.roll_no, "error": str(e)})
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Created {len(created)} students",
        "data": {
            "created": created,
            "errors": errors
        }
    }


@router.get("/students/{student_id}")
async def get_student(
    student_id: str,
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    Get student details.
    """
    student = db.query(Student).filter(
        Student.student_id == student_id,
        Student.teacher_id == current_user.user_id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get evaluation stats
    eval_count = db.query(func.count(Evaluation.id)).filter(
        Evaluation.student_id == student.id
    ).scalar() or 0
    
    avg_score = db.query(func.avg(Evaluation.final_score)).filter(
        Evaluation.student_id == student.id
    ).scalar() or 0
    
    student_data = student.to_dict()
    student_data["stats"] = {
        "evaluation_count": eval_count,
        "average_score": round(avg_score, 2) if avg_score else 0
    }
    
    return {
        "success": True,
        "data": student_data
    }


@router.put("/students/{student_id}")
async def update_student(
    student_id: str,
    update_data: UpdateStudentRequest,
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    Update student details.
    """
    student = db.query(Student).filter(
        Student.student_id == student_id,
        Student.teacher_id == current_user.user_id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update fields
    if update_data.name is not None:
        student.name = update_data.name
    if update_data.email is not None:
        # Check uniqueness
        existing = db.query(Student).filter(
            Student.email == update_data.email,
            Student.id != student.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        student.email = update_data.email
    if update_data.phone is not None:
        student.phone = update_data.phone
    if update_data.roll_no is not None:
        student.roll_no = update_data.roll_no
    if update_data.enrollment_no is not None:
        student.enrollment_no = update_data.enrollment_no
    if update_data.gender is not None:
        student.gender = update_data.gender
    if update_data.address is not None:
        student.address = update_data.address
    if update_data.class_id is not None:
        student.class_id = update_data.class_id
    if update_data.status is not None:
        student.status = UserStatus(update_data.status)
    
    student.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(student)
    
    return {
        "success": True,
        "message": "Student updated successfully",
        "data": student.to_dict()
    }


@router.delete("/students/{student_id}")
async def delete_student(
    student_id: str,
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    Delete a student (soft delete).
    """
    student = db.query(Student).filter(
        Student.student_id == student_id,
        Student.teacher_id == current_user.user_id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student.status = UserStatus.INACTIVE
    student.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Student deleted successfully"
    }


# ========== Class Management ==========
@router.get("/classes")
async def list_classes(
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db),
    active_only: bool = True
):
    """
    List all classes managed by this teacher.
    """
    query = db.query(Class).filter(Class.teacher_id == current_user.user_id)
    
    if active_only:
        query = query.filter(Class.is_active == True)
    
    classes = query.order_by(Class.name).all()
    
    return {
        "success": True,
        "data": {
            "classes": [c.to_dict() for c in classes]
        }
    }


@router.post("/classes", status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: CreateClassRequest,
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    Create a new class.
    """
    new_class = Class(
        name=class_data.name,
        section=class_data.section,
        semester=class_data.semester,
        department=class_data.department,
        academic_year=class_data.academic_year,
        max_students=class_data.max_students or 60,
        teacher_id=current_user.user_id
    )
    
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    
    return {
        "success": True,
        "message": "Class created successfully",
        "data": new_class.to_dict()
    }


@router.put("/classes/{class_id}")
async def update_class(
    class_id: str,
    update_data: UpdateClassRequest,
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    Update class details.
    """
    cls = db.query(Class).filter(
        Class.class_id == class_id,
        Class.teacher_id == current_user.user_id
    ).first()
    
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    
    if update_data.name is not None:
        cls.name = update_data.name
    if update_data.section is not None:
        cls.section = update_data.section
    if update_data.semester is not None:
        cls.semester = update_data.semester
    if update_data.department is not None:
        cls.department = update_data.department
    if update_data.academic_year is not None:
        cls.academic_year = update_data.academic_year
    if update_data.max_students is not None:
        cls.max_students = update_data.max_students
    if update_data.is_active is not None:
        cls.is_active = update_data.is_active
    
    cls.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cls)
    
    return {
        "success": True,
        "message": "Class updated successfully",
        "data": cls.to_dict()
    }


@router.delete("/classes/{class_id}")
async def delete_class(
    class_id: str,
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    Delete a class (soft delete).
    """
    cls = db.query(Class).filter(
        Class.class_id == class_id,
        Class.teacher_id == current_user.user_id
    ).first()
    
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    
    cls.is_active = False
    cls.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Class deleted successfully"
    }


# ========== Subject Management ==========
@router.get("/subjects")
async def list_subjects(
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    List all subjects (or subjects taught by this teacher).
    """
    # Get subjects taught by this teacher
    teacher_subject_ids = db.query(TeacherSubject.subject_id).filter(
        TeacherSubject.teacher_id == current_user.user_id
    ).all()
    teacher_subject_ids = [s[0] for s in teacher_subject_ids]
    
    # Get all active subjects
    all_subjects = db.query(Subject).filter(Subject.is_active == True).all()
    
    result = []
    for subject in all_subjects:
        subject_data = subject.to_dict()
        subject_data["is_teaching"] = subject.id in teacher_subject_ids
        result.append(subject_data)
    
    return {
        "success": True,
        "data": {
            "subjects": result
        }
    }


@router.post("/subjects", status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: CreateSubjectRequest,
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    Create a new subject.
    """
    # Check if code exists
    existing = db.query(Subject).filter(Subject.code == subject_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subject code already exists")
    
    subject = Subject(
        code=subject_data.code,
        name=subject_data.name,
        description=subject_data.description,
        credits=subject_data.credits,
        department=subject_data.department
    )
    
    db.add(subject)
    db.commit()
    db.refresh(subject)
    
    # Automatically add to teacher's subjects
    teacher_subject = TeacherSubject(
        teacher_id=current_user.user_id,
        subject_id=subject.id
    )
    db.add(teacher_subject)
    db.commit()
    
    return {
        "success": True,
        "message": "Subject created successfully",
        "data": subject.to_dict()
    }


@router.post("/subjects/{subject_id}/assign")
async def assign_subject_to_class(
    subject_id: str,
    class_id: int,
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    Assign a subject to a class.
    """
    subject = db.query(Subject).filter(Subject.subject_id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    cls = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == current_user.user_id
    ).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Check if already assigned
    existing = db.query(ClassSubject).filter(
        ClassSubject.class_id == class_id,
        ClassSubject.subject_id == subject.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Subject already assigned to this class")
    
    class_subject = ClassSubject(
        class_id=class_id,
        subject_id=subject.id,
        teacher_id=current_user.user_id
    )
    db.add(class_subject)
    db.commit()
    
    return {
        "success": True,
        "message": "Subject assigned to class successfully"
    }


# ========== Evaluations ==========
@router.get("/evaluations")
async def list_evaluations(
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    student_id: Optional[str] = None,
    reviewed: Optional[bool] = None
):
    """
    List evaluations for this teacher's students.
    """
    query = db.query(Evaluation).filter(Evaluation.teacher_id == current_user.user_id)
    
    if student_id:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if student:
            query = query.filter(Evaluation.student_id == student.id)
    
    if reviewed is not None:
        query = query.filter(Evaluation.is_reviewed == reviewed)
    
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


@router.put("/evaluations/{evaluation_id}/review")
async def review_evaluation(
    evaluation_id: str,
    current_user: TokenData = Depends(get_current_teacher_only),
    db: Session = Depends(get_db)
):
    """
    Mark an evaluation as reviewed by teacher.
    """
    evaluation = db.query(Evaluation).filter(
        Evaluation.evaluation_id == evaluation_id,
        Evaluation.teacher_id == current_user.user_id
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    evaluation.is_reviewed = True
    evaluation.reviewed_by = current_user.user_id
    evaluation.reviewed_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Evaluation marked as reviewed"
    }
