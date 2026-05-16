# OAuth Authentication Setup - Quick Commands

## 🚀 Quick Start

### Verify .env Configuration
```bash
# Check if credentials are loaded
cat .env | grep -E "GOOGLE_CLIENT_ID|GITHUB_CLIENT_ID"

# Should output:
# GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
# GITHUB_CLIENT_ID=YOUR_GITHUB_CLIENT_ID
```

### Start Backend Server
```bash
# Run on port 8000
python -m uvicorn api.main:app --reload --port 8000

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Start Frontend App (in another terminal)
```bash
cd frontend
npm start

# Expected output:
# Compiled successfully!
# On Your Network: http://localhost:3000
```

---

## 🔐 Authentication Flow (Step-by-Step)

```
BROWSER                          BACKEND                        PROVIDER
  │                                │                              │
  ├─── Click "Sign In" ────────────>│                              │
  │                                │                              │
  ├─── Click "Google" ────────────>│                              │
  │                                │                              │
  │    <─── Redirect to ────────────┤─── Send OAuth URL ────────>│
  │        Google Login              │                             │
  │                                │                              │
  │    User Authenticates ────────────────── Verify ────────────>│
  │                                │                          │
  │    <─── Callback ───────────────────────────────────────────┤
  │        (with code)              │                             │
  │                                │                              │
  │    ┌─────────────────────────────────────────────────────┐  │
  │    │ Code → Token Exchange with Google                   │  │
  │    │ GET: oauth2.googleapis.com/token                    │  │
  │    │ Send: code + client_id + client_secret               │  │
  │    │ Get: access_token                                   │  │
  │    └─────────────────────────────────────────────────────┘  │
  │                                │                              │
  │    ┌─────────────────────────────────────────────────────┐  │
  │    │ Token → User Info from Google                       │  │
  │    │ GET: www.googleapis.com/oauth2/v2/userinfo          │  │
  │    │ Get: email, name, picture                           │  │
  │    └─────────────────────────────────────────────────────┘  │
  │                                │                              │
  │    ┌─────────────────────────────────────────────────────┐  │
  │    │ Create/Link Account in Database                      │  │
  │    │ INSERT INTO students (email, name, picture...)       │  │
  │    └─────────────────────────────────────────────────────┘  │
  │                                │                              │
  │    ┌─────────────────────────────────────────────────────┐  │
  │    │ Generate JWT Tokens                                 │  │
  │    │ access_token (15 min)                               │  │
  │    │ refresh_token (7 days)                              │  │
  │    └─────────────────────────────────────────────────────┘  │
  │                                │                              │
  │ <─── Dashboard URL ───────────┤                              │
  │      with tokens               │                              │
  │      (in URL params)            │                              │
  │                                │                              │
  ├─── Parse & Store ────────────>│                              │
  │    Tokens                                                    │
  │    (in localStorage)            │                              │
  │                                │                              │
  ├─── GET /api/v1/dashboard ────>│                              │
  │    (with Authorization token)   │                              │
  │                                │                              │
  │ <─── Dashboard HTML ───────────┤                              │
  │                                │                              │
  ✅ Logged In!                     │                              │
```

---

## 📁 File Structure

```
AssessIQ/
├── .env  ← OAuth Credentials (CREATED)
│   ├── GOOGLE_CLIENT_ID
│   ├── GOOGLE_CLIENT_SECRET
│   ├── GITHUB_CLIENT_ID
│   ├── GITHUB_CLIENT_SECRET
│   └── FRONTEND_URL, JWT_SECRET_KEY, etc.
│
├── api/
│   ├── main.py (FastAPI setup)
│   │   └── registers oauth.router
│   │
│   ├── routes/
│   │   ├── oauth.py (ENDPOINTS)
│   │   │   ├── GET /oauth/google/authorize
│   │   │   ├── GET /oauth/google/callback
│   │   │   ├── GET /oauth/github/authorize
│   │   │   └── GET /oauth/github/callback
│   │   │
│   │   └── auth.py (Traditional login/register)
│   │
│   └── services/
│       └── oauth_service.py (BUSINESS LOGIC)
│           ├── exchange_google_code()
│           ├── get_google_user_info()
│           ├── handle_google_oauth()
│           ├── exchange_github_code()
│           ├── get_github_user_info()
│           └── handle_github_oauth()
│
├── config/
│   └── settings.py (CONFIGURATION)
│       ├── GOOGLE_CLIENT_ID ← from .env
│       ├── GOOGLE_CLIENT_SECRET ← from .env
│       ├── GITHUB_CLIENT_ID ← from .env
│       ├── GITHUB_CLIENT_SECRET ← from .env
│       ├── OAUTH_SUCCESS_REDIRECT
│       └── OAUTH_ERROR_REDIRECT
│
├── database/
│   └── models.py (DATABASE)
│       ├── Student (email, oauth_provider, oauth_id)
│       ├── Teacher
│       └── Admin
│
└── frontend/
    └── src/
        ├── components/
        │   └── AuthModal.jsx (UI)
        │       ├── Google OAuth Button
        │       │   └── onClick → /api/v1/auth/oauth/google/authorize
        │       │
        │       └── GitHub OAuth Button
        │           └── onClick → /api/v1/auth/oauth/github/authorize
        │
        └── context/
            └── AuthContext.jsx (STATE)
                ├── parseOAuthTokensFromURL()
                │   └── Extracts tokens from URL after callback
                │
                └── stores: accessToken, refreshToken, user
```

---

## 🔗 Complete Authentication URLs

### 1. Frontend Login Page
```
http://localhost:3000/
```

### 2. Google Authorization (User clicks "Google")
```
http://localhost:8000/api/v1/auth/oauth/google/authorize?role=student

↓ Redirects to ↓

https://accounts.google.com/o/oauth2/v2/auth?
  client_id=YOUR_GOOGLE_CLIENT_ID&
  redirect_uri=http://localhost:8000/api/v1/auth/oauth/google/callback&
  response_type=code&
  scope=openid email profile
```

### 3. Google Callback (After User Approves)
```
http://localhost:8000/api/v1/auth/oauth/google/callback?
  code=4/0AX4XfWj...&
  state=eyJyb2xlIjoic3R1ZGVudCJ9

↓ Backend Exchanges Code ↓

POST https://oauth2.googleapis.com/token
{
  "grant_type": "authorization_code",
  "code": "4/0AX4XfWj...",
  "client_id": "YOUR_GOOGLE_CLIENT_ID",
  "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
  "redirect_uri": "http://localhost:8000/api/v1/auth/oauth/google/callback"
}

↓ Response ↓

{
  "access_token": "ya29.a0AfH6SMB...",
  "token_type": "Bearer",
  "expires_in": 3599
}

↓ Get User Info ↓

GET https://www.googleapis.com/oauth2/v2/userinfo
Header: Authorization: Bearer ya29.a0AfH6SMB...

↓ Response ↓

{
  "id": "123456789",
  "email": "user@gmail.com",
  "verified_email": true,
  "name": "User Name",
  "picture": "https://..."
}

↓ Create Account & Issue JWT ↓

http://localhost:3000/dashboard?
  access_token=eyJhbGc...&
  refresh_token=eyJhbGc...&
  user={"email":"user@gmail.com",...}
```

### 4. GitHub Authorization (User clicks "GitHub")
```
http://localhost:8000/api/v1/auth/oauth/github/authorize?role=student

↓ Redirects to ↓

https://github.com/login/oauth/authorize?
  client_id=Ov23lis0uAgCgTJQCq5a&
  redirect_uri=http://localhost:8000/api/v1/auth/oauth/github/callback&
  scope=user:email
```

---

## 🧪 Testing

### Test OAuth Endpoint (Manual)
```bash
# Test Google authorize endpoint
curl -X GET "http://localhost:8000/api/v1/auth/oauth/google/authorize?role=student" \
  -H "Accept: application/json" | jq .

# Test GitHub authorize endpoint
curl -X GET "http://localhost:8000/api/v1/auth/oauth/github/authorize?role=student" \
  -H "Accept: application/json" | jq .
```

### Test with Browser
1. Open http://localhost:3000
2. Click "Sign In"
3. Click "Google" button
4. You'll be redirected to Google login
5. After authenticating, you'll return to dashboard
6. Check localStorage for tokens:
   ```javascript
   // In DevTools Console:
   localStorage.getItem('accessToken')
   localStorage.getItem('user')
   ```

---

## 🐛 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "Google OAuth not configured" | Missing credentials in .env | Check .env has GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET |
| "Invalid redirect_uri" | Redirect URI doesn't match OAuth app settings | Update in Google Console / GitHub Settings |
| "Redirect loop" | JWT secret key is wrong | Ensure JWT_SECRET_KEY in .env |
| "CORS error" | Frontend domain not in CORS_ORIGINS | Add to config/settings.py CORS_ORIGINS |
| OAuth button not appearing | Frontend component issue | Check browser DevTools Console for errors |
| Stuck on "Authenticating" | Backend not responding | Check backend is running on port 8000 |

---

## 📊 Data Flow Summary

```
User Input → Browser → Frontend → Backend → OAuth Provider → Backend → Database → Frontend → Dashboard

Step 1: Button Click
  User clicks "Google" or "GitHub" button in AuthModal.jsx

Step 2: Frontend Redirects
  window.location = "/api/v1/auth/oauth/{provider}/authorize?role=student"

Step 3: Backend Constructs URL
  oauth.py generates OAuth provider URL with client_id, redirect_uri, scope

Step 4: Browser Redirects to Provider
  Browser → Google/GitHub login page

Step 5: User Authenticates
  User enters credentials, approves app permissions

Step 6: Provider Calls Callback
  Google/GitHub → Backend callback endpoint with authorization code

Step 7: Backend Exchanges Code
  oauth_service.py exchanges code for access token via provider API

Step 8: Backend Fetches User Info
  oauth_service.py gets user email, name, picture from provider

Step 9: Backend Creates/Links Account
  Database models create new user or link existing user

Step 10: Backend Issues JWT Tokens
  auth_service.py generates access_token & refresh_token

Step 11: Backend Redirects to Frontend
  Browser → Frontend dashboard URL with tokens in params

Step 12: Frontend Parses Tokens
  AuthContext.jsx extracts tokens from URL, stores in localStorage

Step 13: Frontend Redirects to Dashboard
  Browser → http://localhost:3000/dashboard

Step 14: User Logged In ✅
  Dashboard loads with user data and full app access
```

---

## ✅ Setup Verification

Run this to verify everything is in place:

```bash
# 1. Check .env exists and has credentials
[ -f .env ] && echo "✓ .env file exists" || echo "✗ .env missing"
grep "GOOGLE_CLIENT_ID" .env && echo "✓ Google credentials loaded" || echo "✗ Google credentials missing"
grep "GITHUB_CLIENT_ID" .env && echo "✓ GitHub credentials loaded" || echo "✗ GitHub credentials missing"

# 2. Check OAuth routes exist
grep -r "oauth/google/authorize" api/ && echo "✓ Google routes exist" || echo "✗ Google routes missing"
grep -r "oauth/github/authorize" api/ && echo "✓ GitHub routes exist" || echo "✗ GitHub routes missing"

# 3. Check settings loads .env
grep "env_file = " config/settings.py && echo "✓ Settings loads .env" || echo "✗ Settings not loading .env"

# 4. Check frontend OAuth buttons
grep -r "oauth/google/authorize" frontend/ && echo "✓ Frontend Google button exists" || echo "✗ Frontend Google button missing"
grep -r "oauth/github/authorize" frontend/ && echo "✓ Frontend GitHub button exists" || echo "✗ Frontend GitHub button missing"
```

---

## 🎉 You're Ready!

Your OAuth authentication is fully configured and ready to test:

```bash
# Terminal 1
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2
cd frontend && npm start

# Browser
http://localhost:3000 → Click "Sign In" → Click "Google" or "GitHub" → Authenticate → Dashboard ✅
```
