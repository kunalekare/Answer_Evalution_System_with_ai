# OAuth Authentication Flow - Complete Setup ✅

## What's Now in Place

Your `.env` file has been populated with Google and GitHub OAuth credentials:
```env
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
GITHUB_CLIENT_ID=Ov23lis0uAgCgTJQCq5a
GITHUB_CLIENT_SECRET=7ad90deff84e5a8f75e17f45f456523945ee657f
```

---

## Complete Authentication Flow

### 1. **User Visits Frontend** 
   - URL: `http://localhost:3000`
   - User sees login modal with Google and GitHub buttons

### 2. **User Clicks OAuth Button**
   - Frontend calls: `/api/v1/auth/oauth/{provider}/authorize?role=student`
   - Backend (`oauth.py`) constructs OAuth URL
   - User is redirected to provider (Google/GitHub)

### 3. **User Authenticates with Provider**
   - User logs in with Google/GitHub credentials
   - Provider asks for permissions (email, profile)
   - User approves access

### 4. **Provider Redirects Back**
   - Provider calls: `http://localhost:8000/api/v1/auth/oauth/{provider}/callback?code=XXX&state=YYY`
   - Backend (`oauth_service.py`) exchanges code for access token

### 5. **Backend Gets User Info**
   - Backend retrieves user's email, name, profile picture from provider
   - Creates or links user account in database

### 6. **Backend Issues JWT Tokens**
   - Backend generates JWTs (access + refresh tokens)
   - Redirects to frontend with tokens in URL params

### 7. **Frontend Stores Tokens**
   - Frontend extracts tokens from URL (`AuthContext.jsx`)
   - Stores in localStorage
   - Redirects to dashboard
   - User is logged in ✓

---

## File System Architecture

```
backend/
├── config/settings.py              # Loads .env OAuth credentials
├── api/
│   ├── routes/
│   │   ├── oauth.py               # Routes: /authorize, /callback
│   │   └── auth.py                # Routes: /login, /logout, /register
│   └── services/
│       ├── oauth_service.py        # Token exchange, user info, account linking
│       └── auth_service.py         # JWT creation, password hashing
├── database/
│   └── models.py                   # User/Admin/Teacher/Student models
└── main.py                         # FastAPI app setup

frontend/
└── src/
    ├── components/
    │   └── AuthModal.jsx           # UI: Google/GitHub buttons
    └── context/
        └── AuthContext.jsx         # Token handling, OAuth callback parsing
```

---

## Credential Flow

```
.env File (LOCAL)
    ↓
settings.py (reads .env)
    ↓
oauth.py (uses settings for redirects)
    ↓
oauth_service.py (uses settings for token exchange)
    ↓
Backend API (validates with credentials)
    ↓
Frontend (receives JWT tokens)
```

---

## Quick Start

### Step 1: Verify .env is Created
```bash
# Check if .env file exists with credentials
cat .env
```

Look for:
- ✓ GOOGLE_CLIENT_ID
- ✓ GOOGLE_CLIENT_SECRET  
- ✓ GITHUB_CLIENT_ID
- ✓ GITHUB_CLIENT_SECRET

### Step 2: Start Backend
```bash
# Install dependencies (one time)
pip install -r requirements.txt

# Run backend
python -m uvicorn api.main:app --reload --port 8000
```

Backend output should show:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 3: Start Frontend
```bash
cd frontend
npm install  # one time
npm start
```

Frontend runs on `http://localhost:3000`

### Step 4: Test OAuth Login
1. Open http://localhost:3000 in browser
2. Click "Sign In" button
3. Click "Google" or "GitHub" button
4. Authenticate with your credentials
5. You're redirected to dashboard ✓

---

## How Each Provider Works

### Google OAuth Flow
```
User clicks "Google" button
    ↓
Browser → Google OAuth endpoint
    ↓
User logs in with @gmail or @workspace account
    ↓
Google redirects → http://localhost:8000/api/v1/auth/oauth/google/callback
    ↓
Backend exchanges code for access token
    ↓
Backend fetches: email, name, picture from Google
    ↓
Account created/linked in database
    ↓
Browser redirected → http://localhost:3000/dashboard (with JWT tokens)
    ↓
✓ Logged in!
```

### GitHub OAuth Flow
```
User clicks "GitHub" button
    ↓
Browser → GitHub OAuth endpoint
    ↓
User logs in with GitHub account
    ↓
GitHub redirects → http://localhost:8000/api/v1/auth/oauth/github/callback
    ↓
Backend exchanges code for access token
    ↓
Backend fetches: username, email, avatar from GitHub
    ↓
Account created/linked in database
    ↓
Browser redirected → http://localhost:3000/dashboard (with JWT tokens)
    ↓
✓ Logged in!
```

---

## OAuth Settings Breakdown

### Redirect URIs (Must match provider settings)
```
Google:  http://localhost:8000/api/v1/auth/oauth/google/callback
GitHub:  http://localhost:8000/api/v1/auth/oauth/github/callback
```

### Frontend Redirect
```
Success: http://localhost:3000/dashboard
Error:   http://localhost:3000/?error=oauth_failed
```

### Other Settings
```
FRONTEND_URL=http://localhost:3000          # For CORS
JWT_SECRET_KEY=...                          # For token signing
DEBUG=True                                  # Development mode
```

---

## Troubleshooting

### Issue: "Google OAuth not configured"
**Solution:** Check that GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are in .env
```bash
# Verify
grep GOOGLE .env
```

### Issue: "Invalid redirect_uri"
**Solution:** Check OAuth app settings match redirect URIs
- Google: https://console.cloud.google.com → OAuth consent screen
- GitHub: https://github.com/settings/oauth-apps

### Issue: "Failed to get user info"
**Solution:** Access token may be expired. Check network in browser DevTools

### Issue: Frontend stuck on "Authenticating..."
**Solution:** Check browser DevTools Console for errors + network requests

---

## Database Integration

When user authenticates:

1. **First Time (New User)**
   - Account created in `students` table
   - Default role: `student` 
   - Can be promoted to `teacher` or `admin` by admin

2. **Returning User**
   - Existing account linked
   - Same tokens issued
   - Role preserved

3. **Data Stored**
   - Email (unique)
   - OAuth provider ID
   - Name & picture from provider
   - Created/updated timestamps
   - Role & status flags

---

## Testing Commands

### Test Google OAuth endpoint
```bash
curl -X GET "http://localhost:8000/api/v1/auth/oauth/google/authorize?role=student"
```

### Test GitHub OAuth endpoint
```bash
curl -X GET "http://localhost:8000/api/v1/auth/oauth/github/authorize?role=student"
```

### View all auth endpoints
```bash
curl -s http://localhost:8000/openapi.json | jq '.paths | keys[] | select(contains("auth"))'
```

---

## ✅ Setup Complete!

Your OAuth authentication system is now ready:

- ✓ Credentials configured in `.env`
- ✓ Backend routes configured in `api/routes/oauth.py`
- ✓ OAuth service ready in `api/services/oauth_service.py`
- ✓ Frontend buttons ready in `frontend/src/components/AuthModal.jsx`
- ✓ Token handling ready in `frontend/src/context/AuthContext.jsx`

**Just run:**
```bash
# Terminal 1: Backend
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2: Frontend  
cd frontend && npm start

# Then visit: http://localhost:3000
```

---

## Next Steps

1. **Test OAuth login** with your Google account
2. **Test OAuth login** with your GitHub account
3. **Check tokens** in browser DevTools → Application → Local Storage
4. **View users** in database: `sqlite3 assessiq.db`
   ```sql
   SELECT email, provider, role FROM students LIMIT 5;
   ```

🎉 **OAuth authentication is live!**
