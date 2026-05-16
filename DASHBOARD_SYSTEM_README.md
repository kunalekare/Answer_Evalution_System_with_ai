# Dashboard Database & API Documentation

## Overview

The dashboard system provides real-time tracking of user activities and metrics. When a user first visits the website, their dashboard initializes with **all zero values**. As the user performs actions (creates evaluations, uploads files, receives feedback, etc.), the dashboard metrics update automatically to reflect their activity.

---

## Database Structure

### 1. **Dashboard Table**

The main table that stores user dashboard data with all metrics initialized to zero.

```sql
CREATE TABLE dashboards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dashboard_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- User Reference (one of these will be set based on user role)
    admin_id INTEGER UNIQUE FOREIGN KEY,
    teacher_id INTEGER UNIQUE FOREIGN KEY,
    student_id INTEGER UNIQUE FOREIGN KEY,
    user_role ENUM('admin', 'teacher', 'student') NOT NULL,
    
    -- Initialization
    initialized_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_first_visit BOOLEAN DEFAULT TRUE,
    
    -- Common Metrics (All Users)
    total_activities INTEGER DEFAULT 0,
    total_logins INTEGER DEFAULT 0,
    last_activity_at DATETIME,
    
    -- Admin Metrics
    teachers_created INTEGER DEFAULT 0,
    teachers_active INTEGER DEFAULT 0,
    students_managed INTEGER DEFAULT 0,
    evaluations_overseen INTEGER DEFAULT 0,
    
    -- Teacher Metrics
    students_taught INTEGER DEFAULT 0,
    classes_managed INTEGER DEFAULT 0,
    evaluations_created INTEGER DEFAULT 0,
    manual_evaluations_done INTEGER DEFAULT 0,
    model_answers_uploaded INTEGER DEFAULT 0,
    total_evaluations INTEGER DEFAULT 0,
    average_evaluation_score FLOAT DEFAULT 0.0,
    
    -- Student Metrics
    assignments_received INTEGER DEFAULT 0,
    assignments_completed INTEGER DEFAULT 0,
    evaluations_received INTEGER DEFAULT 0,
    average_score FLOAT DEFAULT 0.0,
    highest_score FLOAT DEFAULT 0.0,
    lowest_score FLOAT DEFAULT 0.0,
    total_feedback_received INTEGER DEFAULT 0,
    
    -- Engagement Metrics
    documents_uploaded INTEGER DEFAULT 0,
    documents_downloaded INTEGER DEFAULT 0,
    grievances_filed INTEGER DEFAULT 0,
    grievances_resolved INTEGER DEFAULT 0,
    community_messages_sent INTEGER DEFAULT 0,
    
    -- Custom Data
    data JSON,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### 2. **DashboardMetric Table**

Stores historical snapshots of metrics for charting and trend analysis.

```sql
CREATE TABLE dashboard_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_id VARCHAR(50) UNIQUE NOT NULL,
    dashboard_id INTEGER FOREIGN KEY NOT NULL,
    
    -- Metric Details
    metric_name VARCHAR(100) NOT NULL,  -- e.g., "evaluations_created"
    metric_value FLOAT NOT NULL,         -- the value at that time
    
    -- Time Tracking
    period_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    period_type VARCHAR(20) DEFAULT 'daily',  -- 'daily', 'weekly', 'monthly'
    
    -- Additional Context
    context JSON,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

---

## API Endpoints

### Base URL
```
/api/v1/dashboard
```

All endpoints require authentication via JWT token in `Authorization` header.

---

### 1. **GET /** - Get User Dashboard
Retrieve user's dashboard with current metrics.

**Request:**
```bash
GET /api/v1/dashboard/
Authorization: Bearer <JWT_TOKEN>
```

**Response (First Visit - All Zeros):**
```json
{
  "status": "success",
  "message": "Dashboard retrieved successfully",
  "is_first_visit": true,
  "data": {
    "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_role": "teacher",
    "initialized_at": "2024-01-15T10:30:00Z",
    "is_first_visit": true,
    "last_updated_at": "2024-01-15T10:30:00Z",
    "common_metrics": {
      "total_activities": 0,
      "total_logins": 1,
      "last_activity_at": "2024-01-15T10:30:00Z"
    },
    "teacher_metrics": {
      "students_taught": 0,
      "classes_managed": 0,
      "evaluations_created": 0,
      "manual_evaluations_done": 0,
      "model_answers_uploaded": 0,
      "total_evaluations": 0,
      "average_evaluation_score": 0.0
    },
    "engagement_metrics": {
      "documents_uploaded": 0,
      "documents_downloaded": 0,
      "grievances_filed": 0,
      "grievances_resolved": 0,
      "community_messages_sent": 0
    }
  }
}
```

**Response (After Activities - Updated Values):**
```json
{
  "status": "success",
  "message": "Dashboard retrieved successfully",
  "is_first_visit": false,
  "data": {
    "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_role": "teacher",
    "initialized_at": "2024-01-15T10:30:00Z",
    "teacher_metrics": {
      "students_taught": 45,
      "classes_managed": 3,
      "evaluations_created": 125,
      "manual_evaluations_done": 78,
      "model_answers_uploaded": 15,
      "total_evaluations": 203,
      "average_evaluation_score": 78.5
    }
  }
}
```

---

### 2. **POST /increment/activity** - Increment Activity Counter

Call this after user performs any action.

**Request:**
```bash
POST /api/v1/dashboard/increment/activity
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "status": "success",
  "total_activities": 1
}
```

---

### 3. **POST /increment/grievances** - Log Grievance Filed

Call when user files a new grievance.

**Request:**
```bash
POST /api/v1/dashboard/increment/grievances
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "status": "success",
  "grievances_filed": 1
}
```

---

### 4. **POST /increment/messages** - Log Community Message

Call when user sends a message in community.

**Request:**
```bash
POST /api/v1/dashboard/increment/messages
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "status": "success",
  "community_messages_sent": 1
}
```

---

### 5. **GET /metrics/{metric_name}** - Get Metric History

Retrieve historical data for charting.

**Request:**
```bash
GET /api/v1/dashboard/metrics/evaluations_created?days=30
Authorization: Bearer <JWT_TOKEN>
```

**Query Parameters:**
- `days` (integer, 1-365): Number of days of history to retrieve. Default: 30

**Response:**
```json
{
  "status": "success",
  "metric_name": "evaluations_created",
  "data": [
    {
      "metric_id": "abc123",
      "metric_name": "evaluations_created",
      "metric_value": 5,
      "period_date": "2024-01-01T00:00:00Z",
      "period_type": "daily",
      "created_at": "2024-01-01T10:30:00Z"
    },
    {
      "metric_id": "abc124",
      "metric_name": "evaluations_created",
      "metric_value": 8,
      "period_date": "2024-01-02T00:00:00Z",
      "period_type": "daily",
      "created_at": "2024-01-02T10:30:00Z"
    }
  ]
}
```

---

### 6. **GET /summary** - Get Daily Summary

Get today's activity overview.

**Request:**
```bash
GET /api/v1/dashboard/summary
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "date": "2024-01-15",
    "total_activities": 45,
    "today_activities": 12,
    "total_logins": 5,
    "last_activity": "2024-01-15T15:45:30Z"
  }
}
```

---

### 7. **POST /reset** - Reset Dashboard to Zero

Reset all metrics to zero (for new semester/period).

**Request:**
```bash
POST /api/v1/dashboard/reset
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "status": "success",
  "message": "Dashboard reset to zero successfully",
  "data": {
    "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_role": "teacher",
    "teacher_metrics": {
      "students_taught": 0,
      "classes_managed": 0,
      "evaluations_created": 0,
      "manual_evaluations_done": 0,
      "model_answers_uploaded": 0,
      "total_evaluations": 0,
      "average_evaluation_score": 0.0
    }
  }
}
```

---

### 8. **GET /admin/all** - Get All Dashboards (Admin Only)

Retrieve all user dashboards.

**Request:**
```bash
GET /api/v1/dashboard/admin/all?skip=0&limit=10
Authorization: Bearer <JWT_TOKEN>
```

**Query Parameters:**
- `skip` (integer): Number of records to skip. Default: 0
- `limit` (integer, 1-100): Max records to return. Default: 10

**Response:**
```json
{
  "status": "success",
  "total": 156,
  "skip": 0,
  "limit": 10,
  "data": [
    {
      "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_role": "teacher",
      "initialized_at": "2024-01-15T10:30:00Z",
      "teacher_metrics": {...}
    }
  ]
}
```

---

## Integration Guide

### How Dashboard Initialization Works

1. **First Login**: User logs in for the first time
2. **Dashboard Check**: System queries database for user's dashboard
3. **Not Found**: Dashboard doesn't exist
4. **Auto-Create**: New dashboard created with all metrics = 0
5. **Return**: Dashboard data sent to frontend

### Integration Points in Existing Code

#### 1. **After Teacher Creates Class**
```python
from api.services.dashboard_service import DashboardService
from database.models import UserRole

# After successfully creating class
dashboard = DashboardService.get_dashboard_by_user(db, teacher_id, UserRole.TEACHER)
if dashboard:
    DashboardService.update_teacher_metrics(db, teacher_id)
```

#### 2. **After Evaluation is Created**
```python
# In evaluation route handler
from api.services.dashboard_service import DashboardService

# After successfully creating evaluation
dashboard = DashboardService.get_dashboard_by_user(db, teacher_id, UserRole.TEACHER)
if dashboard:
    DashboardService.increment_total_activities(db, dashboard)
    DashboardService.update_teacher_metrics(db, teacher_id)
    
    # Optionally record historical metric
    DashboardService.record_metric(
        db,
        dashboard,
        "evaluations_created",
        dashboard.evaluations_created,
        period_type="daily"
    )
```

#### 3. **After File Upload**
```python
# In file upload handler
dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
if dashboard:
    DashboardService.increment_documents_uploaded(db, dashboard)
    DashboardService.increment_total_activities(db, dashboard)
```

#### 4. **After Grievance Filed**
```python
# In grievance creation handler
dashboard = DashboardService.get_dashboard_by_user(db, user_id, user_role)
if dashboard:
    DashboardService.increment_grievances_filed(db, dashboard)
```

---

## Frontend Integration

### Example: Display Dashboard on Load

```javascript
// Get dashboard when page loads
async function loadDashboard() {
  const response = await fetch('/api/v1/dashboard/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  if (data.is_first_visit) {
    console.log("First visit - showing welcome with all zero values");
  }
  
  // Display metrics based on user role
  displayMetrics(data.data);
}

// Increment activity when user performs action
async function recordActivity() {
  await fetch('/api/v1/dashboard/increment/activity', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
}

// Display metrics from dashboard
function displayMetrics(dashboard) {
  if (dashboard.user_role === 'teacher') {
    document.getElementById('students-count').textContent = 
      dashboard.teacher_metrics.students_taught;
    document.getElementById('evaluations-count').textContent = 
      dashboard.teacher_metrics.evaluations_created;
  }
}

// Get metric history for chart
async function getMetricHistory(metricName, days = 30) {
  const response = await fetch(
    `/api/v1/dashboard/metrics/${metricName}?days=${days}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  const data = await response.json();
  return data.data;  // Returns array of metrics
}

// Chart example with Chart.js
async function drawEvaluationChart() {
  const metrics = await getMetricHistory('evaluations_created', 30);
  
  const ctx = document.getElementById('evaluationChart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: metrics.map(m => m.period_date),
      datasets: [{
        label: 'Evaluations Created',
        data: metrics.map(m => m.metric_value)
      }]
    }
  });
}
```

---

## Database Queries

### Check Dashboard Exists
```python
from database.models import Dashboard, UserRole

dashboard = db.query(Dashboard).filter_by(teacher_id=teacher_id).first()
```

### Get All Dashboards for Admin
```python
dashboards = db.query(Dashboard).filter_by(
    admin_id=admin_id
).all()
```

### Get Top Performing Teachers (by average score)
```python
top_teachers = db.query(
    Dashboard.teacher_id,
    Dashboard.average_evaluation_score
).filter(
    Dashboard.user_role == UserRole.TEACHER
).order_by(
    Dashboard.average_evaluation_score.desc()
).limit(10).all()
```

### Get All Students in Dashboard
```python
students = db.query(
    Dashboard.student_id,
    Dashboard.average_score,
    Dashboard.assignments_completed
).filter(
    Dashboard.user_role == UserRole.STUDENT
).all()
```

---

## Best Practices

### ✅ DO

- **Call `/` endpoint on every page load** to ensure fresh dashboard data
- **Increment activity after user actions** (create, update, delete, upload)
- **Record historical metrics daily** for trending
- **Reset dashboard at semester start** using `/reset`
- **Use metric history for analytics** to show user progress

### ❌ DON'T

- **Manually update dashboard fields** outside of DashboardService methods
- **Query dashboard directly in routes** - always use DashboardService
- **Forget to call increment functions** after user actions
- **Store sensitive user data in custom JSON field**

---

## Performance Considerations

1. **Dashboard Queries are Indexed**: `student_id`, `teacher_id`, `admin_id` are indexed for fast lookups
2. **Metric Historical Data**: Consider archiving old metrics after 1 year
3. **Caching**: Consider caching dashboard data on frontend for 5-10 minutes
4. **Bulk Updates**: For large updates (e.g., semester end), use batch operations

---

## Troubleshooting

### Dashboard Shows Zeros But Should Have Values
- Check if metrics are being calculated correctly
- Verify `update_teacher_metrics/update_admin_metrics/update_student_metrics` is being called
- Run manual update: Call `/` endpoint with `?force_recalc=true` (if implemented)

### Dashboard Doesn't Initialize
- Check user has role assigned (admin/teacher/student)
- Verify authentication token is valid
- Check database connection

### Historical Metrics Not Recording
- Ensure `DashboardService.record_metric()` is called after updates
- Check that `dashboard_metrics` table has space (not full)

---

## Migration from Old System (if applicable)

```python
# Script to initialize dashboards for existing users
from database.models import Dashboard, Admin, Teacher, Student, UserRole, SessionLocal
from api.services.dashboard_service import DashboardService

db = SessionLocal()

# Initialize admin dashboards
for admin in db.query(Admin).all():
    DashboardService.get_or_create_dashboard(db, admin.id, UserRole.ADMIN)
    DashboardService.update_admin_metrics(db, admin.id)

# Initialize teacher dashboards
for teacher in db.query(Teacher).all():
    DashboardService.get_or_create_dashboard(db, teacher.id, UserRole.TEACHER)
    DashboardService.update_teacher_metrics(db, teacher.id)

# Initialize student dashboards
for student in db.query(Student).all():
    DashboardService.get_or_create_dashboard(db, student.id, UserRole.STUDENT)
    DashboardService.update_student_metrics(db, student.id)

db.close()
print("Dashboard initialization complete!")
```

---

## Summary

The dashboard system provides:

| Feature | Behavior |
|---------|----------|
| **First Visit** | All metrics show 0 |
| **After Actions** | Metrics update automatically |
| **History** | Track trends over 30+ days |
| **Reset** | Clear all metrics for new period |
| **Admin View** | See all users' dashboards |
| **Fast** | Indexed queries return in <100ms |

Users get **real-time feedback** on their platform usage through an intuitive dashboard that starts at zero and grows with their engagement!
