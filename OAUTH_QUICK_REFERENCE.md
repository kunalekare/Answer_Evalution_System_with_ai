# OAuth Credentials Quick Reference
===================================

## What You Need to Get

### Google OAuth Credentials

**Where to get them:**
- https://console.cloud.google.com

**What you need:**
1. `GOOGLE_CLIENT_ID` - Looks like: `123456789-abcdefghijk.apps.googleusercontent.com`
2. `GOOGLE_CLIENT_SECRET` - Looks like: `GOCSPX-xxxxxxxxxxxxxxxxxxxx`

**Setup takes:** ~10 minutes

---

### GitHub OAuth Credentials

**Where to get them:**
- https://github.com/settings/oauth-apps

**What you need:**
1. `GITHUB_CLIENT_ID` - Looks like: `abc123def456gh`
2. `GITHUB_CLIENT_SECRET` - Looks like: `ghp_xxxxxxxxxxxxxxxxxxxx` ⚠️ **SAVE THIS IMMEDIATELY - Only shown once!**

**Setup takes:** ~5 minutes

---

## Your .env Template

Copy this and fill in your credentials:

```env
# ===== Google OAuth =====
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/google/callback

# ===== GitHub OAuth =====
GITHUB_CLIENT_ID=Ov23lis0uAgCgTJQCq5a
GITHUB_CLIENT_SECRET=7ad90deff84e5a8f75e17f45f456523945ee657f
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/github/callback

# ===== Frontend URLs =====
FRONTEND_URL=http://localhost:3000
OAUTH_SUCCESS_REDIRECT=http://localhost:3000/dashboard
OAUTH_ERROR_REDIRECT=http://localhost:3000/?error=oauth_failed

# ===== Other Settings =====
DEBUG=True
DATABASE_URL=sqlite:///./assessiq.db
JWT_SECRET_KEY=your-super-secret-key-change-in-production
```

---

## Redirect URI Reference

**Use these exact URLs in your OAuth provider settings:**

Google:
```
http://localhost:8000/api/v1/auth/oauth/google/callback
```

GitHub:
```
http://localhost:8000/api/v1/auth/oauth/github/callback
```

⚠️ **Must match exactly!** (Including http/https, domain, path)

---

## Complete Step-by-Step

### Step 1: Get Google Credentials (10 min)
1. Go to https://console.cloud.google.com
2. Create project → Enable OAuth API → Create OAuth credentials
3. Copy `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`

### Step 2: Get GitHub Credentials (5 min)
1. Go to https://github.com/settings/oauth-apps
2. Click "New OAuth App"
3. Copy `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`

### Step 3: Create .env File
1. Open terminal in project root
2. Create `.env` file with credentials from above
3. Save file

### Step 4: Install Dependencies
```bash
pip install authlib==1.3.0 httpx==0.25.1
```

### Step 5: Run Backend
```bash
python -m uvicorn api.main:app --reload --port 8000
```

### Step 6: Run Frontend
```bash
cd frontend && npm start
```

### Step 7: Test
- Open http://localhost:3000
- Click "Sign In"
- Click "Google" or "GitHub" button
- Authenticate
- You're logged in! ✓

---

## What Happens After Setup

1. **User sees Google & GitHub buttons** in login modal
2. **User clicks button** → Redirected to OAuth provider
3. **User authenticates** with their Google/GitHub account
4. **User is redirected back** to your app
5. **Account is created/linked** automatically
6. **User is logged in** to dashboard
7. **All features available**

---

## Still Need Help?

Read the detailed guide:
- `OAUTH_SETUP_GUIDE.md` - Complete setup instructions
- `OAUTH_IMPLEMENTATION_SUMMARY.md` - What was implemented

Or reach out with questions!

🎉 Your app now supports OAuth! Enjoy!
