# Dashboard Integration Examples for Existing Routes

This document shows how to integrate dashboard metric updates into your existing API route handlers.

---

## Pattern 1: After Creating an Evaluation

### Current Code (Before)
```python
@router.post("/create-evaluation", tags=["Evaluation"])
async def create_evaluation(
    data: EvaluationCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Create evaluation
    evaluation = Evaluation(
        student_id=data.student_id,
        content=data.content,
        score=data.score,
        teacher_id=current_user["user_id"]
    )
    db.add(evaluation)
    db.commit()
    
    return {"message": "Evaluation created", "id": evaluation.id}
```

### Updated Code (With Dashboard)
```python
from api.services.dashboard_service import DashboardService
from database.models import UserRole

@router.post("/create-evaluation", tags=["Evaluation"])
async def create_evaluation(
    data: EvaluationCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Create evaluation
    evaluation = Evaluation(
        student_id=data.student_id,
        content=data.content,
        score=data.score,
        teacher_id=current_user["user_id"]
    )
    db.add(evaluation)
    db.commit()
    
    # ✨ NEW: Update dashboard
    teacher_id = current_user["user_id"]
    teacher_role = UserRole(current_user["user_role"])
    
    dashboard = DashboardService.get_dashboard_by_user(db, teacher_id, teacher_role)
    if dashboard:
        # Increment activity counter
        DashboardService.increment_total_activities(db, dashboard)
        
        # Recalculate teacher metrics (evaluations_created, average_score, etc.)
        DashboardService.update_teacher_metrics(db, teacher_id)
        
        # Record this metric for historical tracking
        DashboardService.record_metric(
            db,
            dashboard,
            "evaluations_created",
            dashboard.evaluations_created,
            period_type="daily",
            context={"evaluation_id": evaluation.id, "student_id": data.student_id}
        )
    
    return {"message": "Evaluation created", "id": evaluation.id}
```

---

## Pattern 2: After Creating a Class

### Before
```python
@router.post("/classes/create", tags=["Classes"])
async def create_class(
    data: ClassCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    class_obj = Class(
        name=data.name,
        teacher_id=current_user["user_id"]
    )
    db.add(class_obj)
    db.commit()
    
    return {"message": "Class created"}
```

### After
```python
@router.post("/classes/create", tags=["Classes"])
async def create_class(
    data: ClassCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    class_obj = Class(
        name=data.name,
        teacher_id=current_user["user_id"]
    )
    db.add(class_obj)
    db.commit()
    
    # ✨ NEW: Update dashboard
    teacher_id = current_user["user_id"]
    dashboard = DashboardService.get_dashboard_by_user(db, teacher_id, UserRole.TEACHER)
    if dashboard:
        DashboardService.increment_total_activities(db, dashboard)
        DashboardService.update_teacher_metrics(db, teacher_id)  # Updates classes_managed
    
    return {"message": "Class created"}
```

---

## Pattern 3: After File Upload

### Before
```python
@router.post("/upload-file", tags=["Upload"])
async def upload_file(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Save file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Record in database
    uploaded_file = UploadedFile(
        filename=file.filename,
        path=file_path,
        user_id=current_user["user_id"]
    )
    db.add(uploaded_file)
    db.commit()
    
    return {"message": "File uploaded"}
```

### After
```python
@router.post("/upload-file", tags=["Upload"])
async def upload_file(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Save file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Record in database
    uploaded_file = UploadedFile(
        filename=file.filename,
        path=file_path,
        user_id=current_user["user_id"]
    )
    db.add(uploaded_file)
    db.commit()
    
    # ✨ NEW: Update dashboard
    user_id = current_user["user_id"]
    user_role = UserRole(current_user["user_role"])
    
    dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
    if dashboard:
        DashboardService.increment_documents_uploaded(db, dashboard)
        DashboardService.increment_total_activities(db, dashboard)
    
    return {"message": "File uploaded"}
```

---

## Pattern 4: After Filing a Grievance

### Before
```python
@router.post("/grievance/file", tags=["Grievance"])
async def file_grievance(
    data: GrievanceRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    grievance = Grievance(
        title=data.title,
        description=data.description,
        filed_by_id=current_user["user_id"]
    )
    db.add(grievance)
    db.commit()
    
    return {"message": "Grievance filed"}
```

### After
```python
@router.post("/grievance/file", tags=["Grievance"])
async def file_grievance(
    data: GrievanceRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    grievance = Grievance(
        title=data.title,
        description=data.description,
        filed_by_id=current_user["user_id"]
    )
    db.add(grievance)
    db.commit()
    
    # ✨ NEW: Update dashboard
    user_id = current_user["user_id"]
    user_role = UserRole(current_user["user_role"])
    
    dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
    if dashboard:
        DashboardService.increment_grievances_filed(db, dashboard)
        DashboardService.increment_total_activities(db, dashboard)
    
    return {"message": "Grievance filed"}
```

---

## Pattern 5: After Downloading File

### Before
```python
@router.get("/download/{file_id}", tags=["Download"])
async def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    file = db.query(UploadedFile).filter_by(id=file_id).first()
    if not file:
        raise HTTPException(status_code=404)
    
    return FileResponse(file.path)
```

### After
```python
@router.get("/download/{file_id}", tags=["Download"])
async def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    file = db.query(UploadedFile).filter_by(id=file_id).first()
    if not file:
        raise HTTPException(status_code=404)
    
    # ✨ NEW: Update dashboard
    user_id = current_user["user_id"]
    user_role = UserRole(current_user["user_role"])
    
    dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
    if dashboard:
        DashboardService.increment_documents_downloaded(db, dashboard)
    
    return FileResponse(file.path)
```

---

## Pattern 6: After Sending Community Message

### Before
```python
@router.post("/community/message", tags=["Community"])
async def send_message(
    data: MessageRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    message = Message(
        content=data.content,
        community_id=data.community_id,
        sender_id=current_user["user_id"]
    )
    db.add(message)
    db.commit()
    
    return {"message": "Message sent"}
```

### After
```python
@router.post("/community/message", tags=["Community"])
async def send_message(
    data: MessageRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    message = Message(
        content=data.content,
        community_id=data.community_id,
        sender_id=current_user["user_id"]
    )
    db.add(message)
    db.commit()
    
    # ✨ NEW: Update dashboard
    user_id = current_user["user_id"]
    user_role = UserRole(current_user["user_role"])
    
    dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
    if dashboard:
        DashboardService.increment_community_messages(db, dashboard)
        DashboardService.increment_total_activities(db, dashboard)
    
    return {"message": "Message sent"}
```

---

## Pattern 7: After Resolving Grievance (Admin)

### Before
```python
@router.post("/admin/grievance/{grievance_id}/resolve", tags=["Admin"])
async def resolve_grievance(
    grievance_id: int,
    data: ResolutionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    grievance = db.query(Grievance).filter_by(id=grievance_id).first()
    if not grievance:
        raise HTTPException(status_code=404)
    
    grievance.status = GrievanceStatus.RESOLVED
    grievance.resolution = data.resolution
    db.commit()
    
    return {"message": "Grievance resolved"}
```

### After
```python
@router.post("/admin/grievance/{grievance_id}/resolve", tags=["Admin"])
async def resolve_grievance(
    grievance_id: int,
    data: ResolutionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    grievance = db.query(Grievance).filter_by(id=grievance_id).first()
    if not grievance:
        raise HTTPException(status_code=404)
    
    grievance.status = GrievanceStatus.RESOLVED
    grievance.resolution = data.resolution
    db.commit()
    
    # ✨ NEW: Update admin dashboard
    admin_id = current_user["user_id"]
    dashboard = DashboardService.get_dashboard_by_user(db, admin_id, UserRole.ADMIN)
    if dashboard:
        DashboardService.increment_total_activities(db, dashboard)
        DashboardService.update_admin_metrics(db, admin_id)
    
    return {"message": "Grievance resolved"}
```

---

## Pattern 8: Bulk Update for Admin Adding Teacher

### Before
```python
@router.post("/admin/teacher/add", tags=["Admin"])
async def add_teacher(
    data: TeacherCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    teacher = Teacher(
        name=data.name,
        email=data.email,
        created_by=current_user["user_id"]
    )
    db.add(teacher)
    db.commit()
    
    return {"message": "Teacher added"}
```

### After
```python
@router.post("/admin/teacher/add", tags=["Admin"])
async def add_teacher(
    data: TeacherCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    teacher = Teacher(
        name=data.name,
        email=data.email,
        created_by=current_user["user_id"]
    )
    db.add(teacher)
    db.commit()
    
    # ✨ NEW: Update admin dashboard
    admin_id = current_user["user_id"]
    dashboard = DashboardService.get_dashboard_by_user(db, admin_id, UserRole.ADMIN)
    if dashboard:
        DashboardService.increment_total_activities(db, dashboard)
        DashboardService.update_admin_metrics(db, admin_id)  # Updates teachers_created, teachers_active
    
    # Also initialize dashboard for the new teacher
    DashboardService.get_or_create_dashboard(db, teacher.id, UserRole.TEACHER)
    
    return {"message": "Teacher added"}
```

---

## General Integration Template

Use this template for any route that creates/updates data:

```python
@router.post("/path/to/resource", tags=["Category"])
async def your_action(
    data: YourRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 1. Perform your action
    resource = YourModel(
        # your fields
    )
    db.add(resource)
    db.commit()
    
    # 2. ✨ Update dashboard (ADD THESE LINES)
    user_id = current_user["user_id"]
    user_role = UserRole(current_user["user_role"])
    
    dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
    if dashboard:
        # Common: Always increment activity
        DashboardService.increment_total_activities(db, dashboard)
        
        # Specific: Update based on action type
        if current_user["user_role"] == "teacher":
            DashboardService.update_teacher_metrics(db, user_id)
        elif current_user["user_role"] == "admin":
            DashboardService.update_admin_metrics(db, user_id)
        elif current_user["user_role"] == "student":
            DashboardService.update_student_metrics(db, user_id)
    
    # 3. Return response
    return {"message": "Action completed"}
```

---

## Important: Import Statements

Add to the top of each route file that uses dashboard:

```python
from api.services.dashboard_service import DashboardService
from database.models import UserRole
```

---

## Checklist for Integration

For each route, verify:

- [ ] Import `DashboardService` and `UserRole`
- [ ] Get `user_id` and `user_role` from `current_user`
- [ ] Call `DashboardService.get_dashboard_by_user()` to get dashboard
- [ ] Check if dashboard exists with `if dashboard:`
- [ ] Call appropriate increment/update methods
- [ ] Database is committed after action

---

## Performance Notes

- Dashboard updates are fast (< 50ms)
- Use batch updates for bulk operations
- Don't call update methods on every minor change
- Cache dashboard data on frontend

---

## Example: Complete Route with Dashboard

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.services.dashboard_service import DashboardService
from database.models import UserRole, get_db
from api.services.auth_service import get_current_user

router = APIRouter()

@router.post("/evaluations/create", tags=["Evaluation"])
async def create_evaluation(
    eval_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create evaluation and update dashboard metrics."""
    
    try:
        # 1. Create evaluation
        from database.models import Evaluation
        
        evaluation = Evaluation(
            student_id=eval_data["student_id"],
            final_score=eval_data["score"],
            teacher_id=current_user["user_id"]
        )
        db.add(evaluation)
        db.commit()
        
        # 2. Update dashboard
        user_id = current_user["user_id"]
        user_role = UserRole(current_user["user_role"])
        
        dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
        if dashboard:
            # Always increment activity
            DashboardService.increment_total_activities(db, dashboard)
            
            # Update teacher metrics
            if user_role == UserRole.TEACHER:
                DashboardService.update_teacher_metrics(db, user_id)
                
                # Record for history
                DashboardService.record_metric(
                    db,
                    dashboard,
                    "evaluations_created",
                    dashboard.evaluations_created,
                    period_type="daily"
                )
        
        return {
            "status": "success",
            "message": "Evaluation created",
            "evaluation_id": evaluation.id
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

---

This shows all the patterns you need to integrate dashboard updates throughout your application!
