# OAuth Setup Guide - Google & GitHub Authentication
========================================================

This guide explains how to set up Google and GitHub OAuth for the AssessIQ platform.

## Overview

The system now supports OAuth login/signup with:
- **Google OAuth 2.0** - Most popular, recommended for students
- **GitHub OAuth 2.0** - Developer-friendly, good for tech-savvy users

Users can now login with one click from Google or GitHub accounts, or use traditional email/password.

## Features

✅ One-click login/signup with Google  
✅ One-click login/signup with GitHub  
✅ Automatic account creation for new users  
✅ Profile image from OAuth provider  
✅ Role selection (Student, Teacher, Admin)  
✅ Link OAuth to existing email accounts  
✅ Seamless token handling  

---

## PART 1: GOOGLE OAUTH SETUP

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click on the project dropdown at the top
3. Click **"NEW PROJECT"**
4. Enter project name: "AssessIQ" (or your preferred name)
5. Click **CREATE**
6. Wait for the project to be created

### Step 2: Enable Google OAuth API

1. In the Google Cloud Console, search for **"OAuth 2.0"** in the search bar
2. Click on **"OAuth consent screen"** from the left sidebar
3. Select **External** as the User Type
4. Click **CREATE**
5. Fill in the OAuth consent screen form:
   - **App name**: AssessIQ
   - **User support email**: your-email@example.com
   - **Developer contact**: your-email@example.com
6. Click **SAVE AND CONTINUE**
7. On the next page, click **ADD OR REMOVE SCOPES**
8. Search and select these scopes:
   - `openid`
   - `email`
   - `profile`
9. Click **UPDATE**
10. Click **SAVE AND CONTINUE** → **SAVE AND CONTINUE** (skip optional fields)

### Step 3: Create OAuth 2.0 Credentials

1. Click **Credentials** in the left sidebar
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Select **Web application**
4. Enter name: "AssessIQ Web"
5. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:8000/api/v1/auth/oauth/google/callback
   http://localhost:3000/dashboard
   https://your-production-domain.com/api/v1/auth/oauth/google/callback
   https://your-production-frontend.com/dashboard
   ```
6. Click **CREATE**
7. A popup will show your credentials. Copy them:
   - **Client ID**: `XXXXXXXXX-XXXXXXXXXXXXXXXXXXXX.apps.googleusercontent.com`
   - **Client Secret**: `GOCSPX-XXXXXXXXXXXXXXXXXXXXXXXX`

### Step 4: Add Google Credentials to .env

Create or update `.env` file in project root:

```
# Google OAuth
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/google/callback

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

---

## PART 2: GITHUB OAUTH SETUP

### Step 1: Go to GitHub Developer Settings

1. Go to [GitHub Settings → Developer settings](https://github.com/settings/developers)
2. Click on **OAuth Apps** in the left sidebar (or [Direct Link](https://github.com/settings/oauth-apps))
3. Click **New OAuth App**

### Step 2: Register OAuth Application

Fill in the form:

- **Application name**: AssessIQ
- **Homepage URL**: `http://localhost:3000` (or your frontend URL)
- **Application description**: AI-Powered Student Answer Evaluation System
- **Authorization callback URL**: `http://localhost:8000/api/v1/auth/oauth/github/callback`

### Step 3: Get Your Credentials

After creating the app:
1. You'll see **Client ID** 
2. Click **Generate a new client secret**
3. Copy both values:
   - **Client ID**: `Xxxxxxxxxxxxxxxxxx`
   - **Client Secret**: `Xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

⚠️ **SECURITY**: GitHub will only show the secret once. Store it securely!

### Step 4: Add GitHub Credentials to .env

Update your `.env` file:

```
# GitHub OAuth
GITHUB_CLIENT_ID=your-client-id-here
GITHUB_CLIENT_SECRET=your-client-secret-here
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/github/callback
```

---

## PART 3: ENVIRONMENT SETUP

### Required Dependencies

Install the OAuth packages:

```bash
pip install authlib==1.3.0 httpx==0.25.1
```

Or update all dependencies:

```bash
pip install -r requirements.txt
```

### Complete .env File Example

```env
# ========== Application ==========
DEBUG=True
APP_NAME=AssessIQ
APP_VERSION=1.0.0

# ========== Database ==========
DATABASE_URL=sqlite:///./assessiq.db

# ========== Google OAuth ==========
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/google/callback

# ========== GitHub OAuth ==========
GITHUB_CLIENT_ID=abc123def456
GITHUB_CLIENT_SECRET=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/github/callback

# ========== Frontend ==========
FRONTEND_URL=http://localhost:3000
OAUTH_SUCCESS_REDIRECT=http://localhost:3000/dashboard
OAUTH_ERROR_REDIRECT=http://localhost:3000/?error=oauth_failed

# ========== JWT ==========
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# ========== Sarvam AI OCR ==========
SARVAM_API_KEY=sk_xxxxxxxxxxxxxxx
```

---

## PART 4: TESTING OAUTH LOCALLY

### Start the Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Start API server
python -m uvicorn api.main:app --reload --port 8000
```

You should see:
```
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Start the Frontend

```bash
cd frontend
npm install
npm start
```

Frontend will open at `http://localhost:3000`

### Test Google Login

1. Open the app at `http://localhost:3000`
2. Click "Sign In" or "Create Account"
3. Click the **Google** button
4. Select your Google account
5. You'll be redirected back to the dashboard
6. Check that you're logged in! ✅

### Test GitHub Login

1. Click "Sign In" or "Create Account"
2. Click the **GitHub** button
3. Authorize the application
4. You'll be redirected back to the dashboard
5. Check that you're logged in! ✅

---

## PART 5: PRODUCTION DEPLOYMENT

### Update Redirect URIs

Google OAuth:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **Credentials** → Click your OAuth app
3. Add your production URLs under **Authorized redirect URIs**:
   ```
   https://your-prod-domain.com/api/v1/auth/oauth/google/callback
   https://your-prod-frontend.com/dashboard
   ```

GitHub OAuth:
1. Go to [GitHub OAuth Apps](https://github.com/settings/oauth-apps)
2. Click your app
3. Update **Authorization callback URL** to:
   ```
   https://your-prod-domain.com/api/v1/auth/oauth/github/callback
   ```
4. Update **Homepage URL** to your production frontend

### Production Environment Variables

Update `.env` for production:

```env
DEBUG=False
GOOGLE_CLIENT_ID=production-google-id
GOOGLE_CLIENT_SECRET=production-google-secret
GOOGLE_REDIRECT_URI=https://your-prod-domain.com/api/v1/auth/oauth/google/callback

GITHUB_CLIENT_ID=production-github-id
GITHUB_CLIENT_SECRET=production-github-secret
GITHUB_REDIRECT_URI=https://your-prod-domain.com/api/v1/auth/oauth/github/callback

FRONTEND_URL=https://your-prod-frontend.com
OAUTH_SUCCESS_REDIRECT=https://your-prod-frontend.com/dashboard
OAUTH_ERROR_REDIRECT=https://your-prod-frontend.com/?error=oauth_failed

JWT_SECRET_KEY=your-super-secret-production-key-minimum-32-chars
```

### Important Security Notes

⚠️ **NEVER commit .env to version control**  
⚠️ **Use strong JWT_SECRET_KEY in production (32+ characters)**  
⚠️ **Keep OAuth secrets private**  
⚠️ **Use HTTPS in production (required for OAuth)**  
⚠️ **Rotate secrets periodically**

---

## PART 6: API ENDPOINTS

### OAuth Authorization Endpoints

#### Start Google Login
```
GET /api/v1/auth/oauth/google/authorize?role=student
```

Returns:
```json
{
  "redirect_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "message": "Redirect user to this URL for Google authentication"
}
```

#### Handle Google Callback
```
GET /api/v1/auth/oauth/google/callback?code=...&state=...
```

Returns:
```json
{
  "success": true,
  "redirect_url": "http://localhost:3000/dashboard?access_token=...",
  "tokens": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 123,
      "unique_id": "STU...",
      "email": "student@gmail.com",
      "name": "John Doe",
      "role": "student",
      "profile_image": "https://..."
    }
  }
}
```

#### Start GitHub Login
```
GET /api/v1/auth/oauth/github/authorize?role=student
```

#### Handle GitHub Callback
```
GET /api/v1/auth/oauth/github/callback?code=...&state=...
```

#### Get OAuth Configuration
```
GET /api/v1/auth/oauth/config
```

Returns:
```json
{
  "google": {
    "client_id": "12345...",
    "authorize_url": "/api/v1/auth/oauth/google/authorize",
    "configured": true
  },
  "github": {
    "client_id": "abc123...",
    "authorize_url": "/api/v1/auth/oauth/github/authorize",
    "configured": true
  }
}
```

---

## PART 7: HOW OAUTH FLOW WORKS

### Complete Flow Diagram

```
┌─── Frontend ──────┐         ┌─── Backend ──────┐         ┌─ OAuth Provider ─┐
│                   │         │                  │         │                  │
│  1. User clicks   │         │                  │         │                  │
│  "Login with      │──────┐  │                  │         │                  │
│   Google"         │      │  │                  │         │                  │
│                   │      │  │                  │         │                  │
│  2. Redirect to   │      └─→│  /oauth/google/  │────┐    │                  │
│  OAuth authorize  │         │  authorize?role  │    │    │                  │
│                   │         │                  │    └───→│ Google OAuth     │
│                   │         │                  │         │ Consent Screen   │
│                   │         │                  │         │                  │
│  3. User logs in  │         │                  │         │ ← User grants    │
│  with Google      │         │                  │    ┌────│   permission     │
│                   │         │                  │    │    │                  │
│  4. Redirected to │         │  /oauth/google/  │    │    │ Sends auth code  │
│  callback with    │←────────│  callback?code   │←───┘    │                  │
│  tokens in URL    │         │  &state=...      │         │                  │
│                   │         │                  │         │                  │
│  5. Extract token │         │                  │         │                  │
│  and save to      │         │                  │         │                  │
│  localStorage     │         │                  │         │                  │
│                   │         │                  │         │                  │
│  6. Authenticated│         │                  │         │                  │
│  ✓ Dashboard      │         │                  │         │                  │
└───────────────────┘         └──────────────────┘         └──────────────────┘
```

### Step by Step

1. **User clicks OAuth button** (Google/GitHub)
2. **Frontend redirects to backend OAuth endpoint** 
   - URL: `/api/v1/auth/oauth/{google|github}/authorize?role=student`
   - Role parameter tells backend which role user is signing up as
3. **Backend redirects to OAuth provider** (Google/GitHub)
   - Includes client ID, scopes, redirect URI, state (for CSRF protection)
4. **User logs in with OAuth provider**
5. **OAuth provider redirects back to backend callback**
   - Includes authorization code
6. **Backend exchanges code for access token**
   - Uses client secret (secure, server-to-server)
7. **Backend gets user info from OAuth provider**
   - Email, name, profile picture
8. **Backend finds or creates user in database**
   - Check if OAuth ID exists
   - Check if email exists (link OAuth)
   - Create new user if needed
9. **Backend creates JWT tokens**
10. **Backend redirects to frontend with tokens in URL**
11. **Frontend extracts tokens and stores in localStorage**
12. **Frontend redirects to dashboard**
13. **Authenticated! ✓**

---

## PART 8: TROUBLESHOOTING

### Error: "OAuth not configured"
**Solution**: Check that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in `.env` file

### Error: "Invalid redirect_uri"
**Solution**: Make sure redirect URI in Google/GitHub settings exactly matches `GOOGLE_REDIRECT_URI` / `GITHUB_REDIRECT_URI` in `.env`
- Must include protocol (http/https)
- Must include query parameters if any

### Error: "Undefined is not an object (evaluating useAuth)"
**Solution**: Make sure `AuthProvider` wraps your app in `main.jsx` or `index.jsx`

### Error: "CORS error"
**Solution**: Backend CORS is already configured to allow all origins. If you still get CORS errors:
- Check browser console for exact error
- Make sure frontend URL matches `FRONTEND_URL` in `.env`

### Tokens not appearing in localStorage
**Debug**: 
```javascript
// In browser console
console.log(localStorage.getItem('token'));
console.log(localStorage.getItem('assessiq_user'));
```

If empty, OAuth tokens weren't extracted from URL. Check:
- Are URL parameters present? `?access_token=...&user=...`
- Is JSON parsing succeeding? Check console logs

### User created but profile image missing
This is normal. Some OAuth providers don't return profile pictures by default. Users can manually upload a profile picture later.

---

## PART 9: ADVANCED CONFIGURATION

### Custom OAuth Scopes

To request additional scopes from OAuth providers:

Edit `api/routes/oauth.py`, find the scope string:

**Google:**
```python
"scope": "openid email profile",  # Add more scopes here
```

**GitHub:**
```python
"scope": "user:email read:user",  # Add more scopes here
```

Common scopes:
- Google: `openid`, `email`, `profile`
- GitHub: `user:email`, `read:user`, `public_repo`, `gist`

### Linking OAuth to Existing Accounts

When a user logs in with OAuth using an email that already exists:
- The OAuth provider ID is automatically linked
- Next time they use the same email, OAuth login works
- No manual linking needed!

### Admin Accounts via OAuth

By default, admins CANNOT be created via OAuth (security feature).

To create admin via OAuth:
1. Create account with email/password first (as student/teacher)
2. Have super admin promote via admin panel
3. Then use OAuth with same email

---

## PART 10: QUICK START COMMANDS

```bash
# 1. Clone and setup
git clone <your-repo>
cd Answer_Evaluation
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Create .env with your OAuth credentials
cat > .env << EOF
GOOGLE_CLIENT_ID=your-id
GOOGLE_CLIENT_SECRET=your-secret
GITHUB_CLIENT_ID=your-id
GITHUB_CLIENT_SECRET=your-secret
EOF

# 3. Start backend
python -m uvicorn api.main:app --reload --port 8000

# 4. Start frontend (new terminal)
cd frontend
npm install
npm start

# 5. Open browser
# http://localhost:3000
# Click "Sign In" → Click Google/GitHub button → Authenticate!
```

---

## Need Help?

- Check browser console for errors
- Check server logs for API errors
- Verify `.env` file has correct credentials
- Double-check redirect URIs match exactly
- Make sure dependencies are installed

Happy authenticating! 🚀
