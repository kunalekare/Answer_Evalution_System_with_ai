# 🚀 Quick Start Reference - AssessIQ

## 5-Minute Setup

### Start Backend
```bash
cd Answer_Evaluation
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend (in new terminal)
```bash
cd Answer_Evaluation/frontend
npm install  # First time only
npm start
```

### Stop Servers
- Backend: Press `Ctrl+C` in terminal
- Frontend: Press `Ctrl+C` in terminal

---

## Login Credentials

```
Teacher Account:
  Email: teacher@assessiq.com
  Password: teacher123
  
Admin Account:
  Email: admin@assessiq.com
  Password: admin123
  
Student Account:
  Email: student@assessiq.com
  Password: student123
```

---

## Key URLs

| Function              | URL                                              |
|----------------------|--------------------------------------------------|
| Frontend              | http://localhost:3000                            |
| Backend API          | http://localhost:8000                            |
| API Docs (Swagger)   | http://localhost:8000/docs                       |
| Health Check         | http://localhost:8000/health                     |
| Authentication       | http://localhost:8000/api/v1/auth/login          |
| Teacher Classes      | http://localhost:8000/api/v1/teacher/classes     |
| Teacher Students     | http://localhost:8000/api/v1/teacher/students    |

---

## Common Commands

### Run Tests
```bash
# All authentication tests
python test_teacher_login.py

# Quick evaluation tests
python test_quick_eval.py

# Full Sarvam AI tests
python test_sarvam_full_flow.py
```

### View Logs
```bash
# Follow backend logs
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Check frontend console
# Open browser > Right-click > Inspect > Console tab
```

### Database
```bash
# Database file location
Answer_Evaluation/assessiq.db

# To reset database
# Simply delete assessiq.db and restart backend
```

---

## Solving Common Issues

### Issue: "Module not found" error
**Solution**: Ensure you're in the right directory and using Python from the project
```bash
cd Answer_Evaluation
python -m uvicorn api.main:app --reload
```

### Issue: Port 8000 already in use
**Solution**: Kill previous process or use different port
```bash
# Use different port
python -m uvicorn api.main:app --port 8001
```

### Issue: Frontend can't connect to backend
**Solution**: Check if backend is running at port 8000
```bash
# Verify backend is running
curl http://localhost:8000/health
```

### Issue: Login fails
**Solution**: Check you're using correct credentials
- Email: `teacher@assessiq.com` (not `papereval.com`)
- Password: `teacher123`

### Issue: Tests fail with connection error
**Solution**: Ensure backend is running before running tests
```bash
# Terminal 1: Start backend
python -m uvicorn api.main:app --reload

# Terminal 2: Run tests
python test_teacher_login.py
```

---

## File Structure

```
Answer_Evaluation/
├── api/                          # Backend code
│   ├── main.py                   # FastAPI app entry
│   ├── routes/                   # API endpoints
│   ├── services/                 # Business logic
│   └── __init__.py
├── frontend/                      # React frontend
│   ├── src/
│   │   ├── pages/               # Page components
│   │   ├── components/          # Reusable components
│   │   ├── context/             # React context (Auth)
│   │   ├── services/            # API calls
│   │   └── App.jsx              # Main app
│   └── package.json
├── database/                      # Database models
│   ├── models.py                # SQLAlchemy models
│   └── __init__.py
├── config/                        # Configuration
│   ├── settings.py              # App settings
│   └── __init__.py
├── assessiq.db                   # SQLite database (auto-created)
└── README.md                     # Project documentation
```

---

## API Quick Reference

### Authentication
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teacher@assessiq.com",
    "password": "teacher123",
    "role": "teacher"
  }'

# Response: {access_token, refresh_token, user}
```

### Teacher Endpoints
```bash
# Get classes (requires Authorization header)
curl -X GET http://localhost:8000/api/v1/teacher/classes \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get students
curl -X GET http://localhost:8000/api/v1/teacher/students \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create student
curl -X POST http://localhost:8000/api/v1/teacher/students \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "roll_no": "101",
    "email": "john@example.com"
  }'
```

### Text Evaluation
```bash
# Evaluate text
curl -X POST http://localhost:8000/api/v1/evaluate/text \
  -H "Content-Type: application/json" \
  -d '{
    "student_answer": "The capital of France is Paris",
    "model_answer": "Paris is the capital of France",
    "question": "What is the capital of France?"
  }'
```

### OCR
```bash
# Extract text from image
curl -X POST http://localhost:8000/api/v1/upload/extract-text \
  -H "Content-Type: multipart/form-data" \
  -F "file=@image.jpg" \
  -F "ocr_engine=sarvam"
```

---

## Performance Tips

### For Development
- Use `--reload` flag for auto-restart on code changes
- Open DevTools console in browser for debugging
- Check browser console and terminal logs simultaneously

### For Production
- Use production-grade server (Gunicorn, etc.)
- Set `DEBUG = False` in settings
- Use environment variables for sensitive data
- Enable CORS only for your frontend domain
- Use PostgreSQL instead of SQLite

---

## Documentation Files

| File                                 | Purpose                              |
|--------------------------------------|--------------------------------------|
| README.md                            | Project overview                     |
| SESSION_SUMMARY.md                   | This session's work                  |
| AUTHENTICATION_FIX_COMPLETE.md       | Auth system details                  |
| FINAL_VERIFICATION.md                | System status report                 |
| TESTING_GUIDE.md                     | How to run tests                     |
| SARVAM_QUICK_REFERENCE.md            | OCR setup guide                      |
| QUICK_COMMANDS.md                    | Common commands                      |

---

## Environment Variables

Create `.env` file in project root (optional):

```
# Database
DATABASE_URL=sqlite:///./assessiq.db

# JWT
JWT_SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# OCR
SARVAM_API_KEY=your-sarvam-key
GOOGLE_VISION_API_KEY=your-google-key

# Development
DEBUG=True
LOG_LEVEL=INFO
```

---

## Git Commands

```bash
# View commit history
git log --oneline

# View changes
git status

# Add files
git add .

# Commit changes
git commit -m "Your message"

# Push to server
git push

# Pull latest changes
git pull
```

---

## System Requirements

- **OS**: Windows, Mac, or Linux
- **Python**: 3.8+
- **Node.js**: 14+
- **Database**: SQLite (auto-created) or PostgreSQL
- **RAM**: 2GB minimum
- **Disk**: 1GB available

---

## Support Resources

1. **Backend Docs**: http://localhost:8000/docs (Swagger UI)
2. **Frontend Console**: DevTools > Console tab
3. **Backend Logs**: Terminal where you started the server
4. **Database**: View with `sqlite3 assessiq.db`
5. **Code**: Check source files for documentation

---

## Useful Keyboard Shortcuts

| Shortcut           | Function                          |
|-------------------|-----------------------------------|
| `Ctrl+C`          | Stop server in terminal           |
| `F12`             | Open browser DevTools             |
| `Ctrl+Shift+C`    | Inspect element in browser        |
| `Ctrl+Shift+K`    | Clear console                     |
| `Ctrl+Shift+J`    | Focus on console                  |
| `Ctrl+R`          | Reload page                       |
| `Ctrl+Shift+R`    | Hard reload (clear cache)         |

---

## Emergency Procedures

### Reset Everything
```bash
# Stop both servers (Ctrl+C)
# Delete database
rm assessiq.db
# Restart backend - it will recreate database with fresh demo data
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Clear Browser Cache
```bash
# Chrome: Ctrl+Shift+Delete
# Firefox: Ctrl+Shift+Delete
# Safari: History > Clear History
```

### Check Database Integrity
```bash
# Install sqlite3 if needed: pip install sqlite3
sqlite3 assessiq.db ".tables"
sqlite3 assessiq.db "SELECT count(*) FROM teachers;"
```

---

**Last Updated**: 2026-03-28  
**For Questions**: Check the documentation files or review the test scripts  
**Status**: ✅ System Ready!
