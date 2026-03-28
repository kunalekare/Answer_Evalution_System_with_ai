# Authentication & Student Management - 401 Error Fix

## Problem Identified
When accessing teacher endpoints (like `/api/v1/teacher/classes`), users were receiving **401 Unauthorized** errors. This was because:

1. No token was being sent in the Authorization header
2. Users were not logged in with proper JWT tokens
3. No demo teacher accounts existed for testing

## Solution Implemented

### ✅ Backend Changes

#### 1. Demo Accounts Created Automatically
- **Admin**: `admin@assessiq.com` / `admin123`
- **Teacher**: `teacher@assessiq.com` / `teacher123`
- **Student**: `student@assessiq.com` / `student123`

These are created automatically on application startup.

#### 2. New Endpoint: Get Demo Credentials
```
GET /api/v1/auth/demo-credentials

Response:
{
  "success": true,
  "data": {
    "accounts": [
      {
        "role": "admin",
        "email": "admin@assessiq.com",
        "password": "admin123",
        "description": "System administrator - Full access"
      },
      {
        "role": "teacher",
        "email": "teacher@assessiq.com",
        "password": "teacher123",
        "description": "Teacher - Can manage students and classes"
      },
      {
        "role": "student",
        "email": "student@assessiq.com",
        "password": "student123",
        "description": "Student - Can submit answers and view results"
      }
    ]
  }
}
```

#### 3. Files Modified

**`api/services/auth_service.py`**
- ✅ Added `create_demo_teacher()` function
- ✅ Added `create_demo_student()` function
- ✅ Both functions create accounts only if they don't exist

**`api/main.py`**
- ✅ Updated startup event to create demo accounts
- ✅ Logs demo credentials on startup

**`api/routes/auth.py`**
- ✅ Added `/auth/demo-credentials` endpoint
- ✅ Returns list of demo accounts
- ✅ Useful for frontend to display test credentials

### ✅ Frontend Changes

**`frontend/src/services/api.js`**
- ✅ Added `getDemoCredentials()` function
- ✅ Provides fallback demo credentials if backend unreachable
- ✅ Better error handling for 401/422 responses

**`frontend/src/pages/Evaluate.jsx`**
- ✅ Added input validation for text evaluation
- ✅ Better error messages for validation failures
- ✅ Shows character count requirements

---

## How to Use for Student Management

### Step 1: Login as Teacher

```javascript
// In any React component or browser console:
const loginData = {
  email: "teacher@assessiq.com",
  password: "teacher123",
  role: "teacher"
};

// POST to /api/v1/auth/login
```

**Using GUI:**
1. Go to login page
2. Enter email: `teacher@assessiq.com`
3. Enter password: `teacher123`
4. Select Role: "Teacher"
5. Click Login

### Step 2: After Login

You will receive:
- `access_token`: For authenticated API calls
- `refresh_token`: For refreshing expired tokens
- `user`: User information

These are **automatically stored** in localStorage:
```javascript
localStorage.getItem('token')  // Access token
localStorage.getItem('refreshToken')  // Refresh token
localStorage.getItem('assessiq_user')  // User info
```

### Step 3: Access Teacher Endpoints

Once logged in, you can access:

```javascript
// ✅ NOW WORKS - Get all classes
GET /api/v1/teacher/classes

// ✅ NOW WORKS - Get all students
GET /api/v1/teacher/students

// ✅ NOW WORKS - Create student
POST /api/v1/teacher/students
{
  "name": "John Doe",
  "email": "john@example.com",
  "roll_number": "STU001"
}

// ✅ NOW WORKS - Get student evaluations
GET /api/v1/teacher/students/{student_id}/evaluations
```

The Authorization header is **automatically added** by the API interceptor:
```
Authorization: Bearer {access_token}
```

---

## API Flow Diagram

```
┌─────────────────────────────────────────┐
│  1. User Opens Login Page               │
│     - Sees "Demo Credentials" option    │
│     - Can view demo accounts            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. Click "Use Demo Teacher Account"    │
│     - Auto-fills: teacher@assessiq.com  │
│     - Auto-fills: teacher123            │
│     - Auto-selects: Teacher role        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. POST /api/v1/auth/login             │
│     - Backend validates credentials     │
│     - Returns JWT tokens                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. Frontend Stores in localStorage:    │
│     - token (access token)              │
│     - refreshToken (for expiry)         │
│     - assessiq_user (user info)         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  5. Access Protected Endpoints          │
│     - GET /teacher/classes              │
│     - GET /teacher/students             │
│     - POST /teacher/students            │
│     (Token auto-added to header)        │
└─────────────────────────────────────────┘
```

---

## Troubleshooting

### Issue: Still Getting 401 Error

**Cause 1: Token Not in localStorage**
```javascript
// Check if token exists:
console.log(localStorage.getItem('token'));

// If empty, you're not logged in
// Solution: Go to login page, use demo credentials
```

**Cause 2: Token Expired**
```javascript
// Check token expiry:
const token = localStorage.getItem('token');
// Token expires after 1 hour by default

// Solution: Refresh token or log in again
```

**Cause 3: Wrong Role**
```javascript
// Check localStorage:
const user = JSON.parse(localStorage.getItem('assessiq_user'));
console.log(user.role); // Should be "teacher"

// Solution: Log in with role: "teacher"
```

### Issue: Error "Could not validate credentials"

**Cause**: Invalid token format or corrupted data

**Solution**:
1. Clear localStorage: `localStorage.clear()`
2. Refresh page
3. Log in again with demo credentials

### Issue: Teacher endpoint returns "Teacher access required"

**Cause**: Logged in but with wrong role

**Solution**:
1. Logout
2. Log in again with role "teacher"
3. Use email: `teacher@assessiq.com`

---

## Testing Student Management

### Test Scenario 1: Create Student

```bash
# 1. Login as teacher
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teacher@assessiq.com",
    "password": "teacher123",
    "role": "teacher"
  }'

# Store the access_token from response

# 2. Create student
curl -X POST http://localhost:8000/api/v1/teacher/students \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Student",
    "email": "student123@example.com",
    "roll_number": "STU123"
  }'
```

### Test Scenario 2: List All Students

```bash
# Using the same access_token
curl -X GET http://localhost:8000/api/v1/teacher/students \
  -H "Authorization: Bearer {access_token}"
```

### Test Scenario 3: Get Student Evaluations

```bash
# Get evaluations for a student
curl -X GET http://localhost:8000/api/v1/teacher/students/{student_id}/evaluations \
  -H "Authorization: Bearer {access_token}"
```

---

## Security Notes

### ⚠️ For Testing Only
These demo credentials should **only be used for testing**:
- Not suitable for production
- Passwords are simple and known
- Should be disabled in production environment
- Use environment variables to control demo account creation

### 🔒 Production Setup
In production:
1. Remove demo account creation from startup
2. Require proper registration for all users
3. Use strong password requirements
4. Enable 2FA/MFA
5. Use HTTPS only
6. Keep JWT_SECRET_KEY secure

---

## Files Modified

### Backend
- ✅ `api/services/auth_service.py` - Added demo account functions
- ✅ `api/main.py` - Added demo account startup
- ✅ `api/routes/auth.py` - Added demo credentials endpoint

### Frontend
- ✅ `frontend/src/services/api.js` - Added getDemoCredentials()
- ✅ `frontend/src/pages/Evaluate.jsx` - Improved validation
- ✅ `frontend/src/pages/Evaluate.jsx` - Better error handling

---

## Summary

The **401 Unauthorized** error should now be resolved:

1. ✅ Demo teacher account automatically created
2. ✅ Demo credentials available via API endpoint
3. ✅ Frontend can display demo credentials
4. ✅ Once logged in as teacher, can manage students
5. ✅ API automatically adds token to requests
6. ✅ Better error messages on validation failures

**To test student management:**
1. Go to login → Demo Credentials
2. Use: `teacher@assessiq.com` / `teacher123` / Teacher role
3. Go to admin/teacher section
4. Add, edit, view students
5. See all student evaluations

All done! 🎉
