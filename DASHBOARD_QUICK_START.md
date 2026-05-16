# Dashboard Quick Setup & Testing Guide

## Quick Start

### 1. Initialize Database Tables

The dashboard tables are automatically created when the app starts thanks to SQLAlchemy's `Base.metadata.create_all()`.

To manually initialize:
```python
from database.models import init_db
init_db()
print("Dashboard tables created!")
```

### 2. Test with cURL

#### Get Dashboard (First Visit - All Zeros)
```bash
curl -X GET http://localhost:8000/api/v1/dashboard/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Expected: All metrics should be 0 on first visit

#### Increment Activity
```bash
curl -X POST http://localhost:8000/api/v1/dashboard/increment/activity \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Get Updated Dashboard
```bash
curl -X GET http://localhost:8000/api/v1/dashboard/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Expected: `total_activities` should now be 1+

#### Reset Dashboard
```bash
curl -X POST http://localhost:8000/api/v1/dashboard/reset \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Test with Python

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
TEACHER_TOKEN = "your_jwt_token_here"

headers = {"Authorization": f"Bearer {TEACHER_TOKEN}"}

# Get dashboard
response = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
print("Initial Dashboard:")
print(json.dumps(response.json(), indent=2))

# Increment activity 5 times
for i in range(5):
    requests.post(f"{BASE_URL}/dashboard/increment/activity", headers=headers)
    print(f"Activity {i+1} recorded")

# Get updated dashboard
response = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
dashboard = response.json()["data"]
print(f"\nTotal Activities: {dashboard['common_metrics']['total_activities']}")

# Get daily summary
response = requests.get(f"{BASE_URL}/dashboard/summary", headers=headers)
print(f"\nDaily Summary:")
print(json.dumps(response.json(), indent=2))

# Reset dashboard
response = requests.post(f"{BASE_URL}/dashboard/reset", headers=headers)
print(f"\nDashboard Reset:")
print(json.dumps(response.json()["data"]["common_metrics"], indent=2))
```

### 4. Test Endpoints

#### Test File: `test_dashboard.py`
```python
"""
Test dashboard API endpoints
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

# Get tokens from login
def get_teacher_token():
    """Get JWT token for teacher (use demo teacher credentials)"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "teacher@demo.com",
            "password": "teacher123"
        }
    )
    return response.json()["data"]["access_token"]

def test_dashboard_flow():
    """Test complete dashboard flow"""
    token = get_teacher_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=" * 60)
    print("DASHBOARD TEST FLOW")
    print("=" * 60)
    
    # 1. First visit - all zeros
    print("\n1. Getting dashboard (first visit)...")
    response = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
    dashboard = response.json()["data"]
    print(f"   Is first visit: {response.json()['is_first_visit']}")
    print(f"   Total activities: {dashboard['common_metrics']['total_activities']}")
    print(f"   Total logins: {dashboard['common_metrics']['total_logins']}")
    
    # 2. Simulate some activities
    print("\n2. Incrementing activity counter...")
    for i in range(3):
        requests.post(f"{BASE_URL}/dashboard/increment/activity", headers=headers)
        print(f"   Activity {i+1} recorded")
    
    # 3. Get updated dashboard
    print("\n3. Getting updated dashboard...")
    response = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
    dashboard = response.json()["data"]
    print(f"   Total activities: {dashboard['common_metrics']['total_activities']}")
    print(f"   Expected: 3 (previous activities already on server)")
    
    # 4. Simulate filing grievance
    print("\n4. Filing grievance...")
    requests.post(f"{BASE_URL}/dashboard/increment/grievances", headers=headers)
    response = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
    print(f"   Grievances filed: {response.json()['data']['engagement_metrics']['grievances_filed']}")
    
    # 5. Simulate community message
    print("\n5. Sending community message...")
    requests.post(f"{BASE_URL}/dashboard/increment/messages", headers=headers)
    response = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
    print(f"   Community messages: {response.json()['data']['engagement_metrics']['community_messages_sent']}")
    
    # 6. Get daily summary
    print("\n6. Getting daily summary...")
    response = requests.get(f"{BASE_URL}/dashboard/summary", headers=headers)
    summary = response.json()["data"]
    print(f"   Date: {summary['date']}")
    print(f"   Today's activities: {summary['today_activities']}")
    print(f"   Total activities: {summary['total_activities']}")
    
    # 7. Get metric history
    print("\n7. Getting metric history (last 30 days)...")
    response = requests.get(f"{BASE_URL}/dashboard/metrics/total_activities?days=30", headers=headers)
    metrics = response.json()["data"]
    print(f"   Historical records: {len(metrics)}")
    if metrics:
        print(f"   Latest value: {metrics[-1]['metric_value']}")
    
    # 8. Reset dashboard
    print("\n8. Resetting dashboard...")
    response = requests.post(f"{BASE_URL}/dashboard/reset", headers=headers)
    dashboard = response.json()["data"]
    print(f"   Activities after reset: {dashboard['common_metrics']['total_activities']}")
    print(f"   Grievances after reset: {dashboard['engagement_metrics']['grievances_filed']}")
    
    print("\n" + "=" * 60)
    print("TEST FLOW COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    test_dashboard_flow()
```

Run it:
```bash
python test_dashboard.py
```

---

## Integration Checklist

- [ ] Dashboard tables created in database
- [ ] Dashboard routes registered in `main.py`
- [ ] Dashboard service imported in relevant route handlers
- [ ] After create/update/delete operations, call appropriate increment method
- [ ] Frontend displays dashboard data on user dashboard page
- [ ] Frontend calls `/increment/activity` after user actions
- [ ] API documentation updated in Swagger/OpenAPI
- [ ] Test all endpoints with cURL/Postman
- [ ] Verify metrics update correctly

---

## Common Issues

### Issue: Dashboard not found (404)
**Solution**: Make sure user is authenticated and dashboard was initialized on login

### Issue: All metrics still 0 after actions
**Solution**: Verify you're calling the increment functions in your route handlers

### Issue: Query errors in dashboard_service.py
**Solution**: Make sure all model imports in `dashboard_service.py` are correctly imported from `database.models`

---

## Next Steps

1. **Frontend Dashboard Page**: Create a page showing all metrics with charts
2. **Metric Recording**: Set up daily batch job to record historical metrics
3. **Notifications**: Alert users of milestones (e.g., "Congratulations! 100 evaluations!")
4. **Analytics**: Build admin analytics showing user engagement trends
5. **Export**: Allow users to export their dashboard data

---

## Key Points to Remember

✅ Dashboard initializes with **ALL ZEROS** on first visit
✅ Metrics update **AUTOMATICALLY** based on user actions
✅ Historical data is **TRACKED** for trending
✅ Dashboard can be **RESET** for new periods
✅ Admin can **VIEW ALL** user dashboards
