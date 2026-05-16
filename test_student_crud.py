#!/usr/bin/env python3
"""
Test student CRUD operations
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
DEMO_TOKEN = "demo_token"

headers = {
    "Authorization": f"Bearer {DEMO_TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 60)
print("TESTING STUDENT CRUD OPERATIONS")
print("=" * 60)

# Test 1: Fetch students BEFORE adding
print("\n1️⃣ FETCHING STUDENTS (BEFORE ADD)...")
try:
    response = requests.get(f"{BASE_URL}/teacher/students", headers=headers)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    if data.get('success') and data.get('data'):
        students_before = data['data'].get('students', [])
        print(f"Students count before: {len(students_before)}")
    else:
        print("❌ Failed to fetch students")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Add a new student
print("\n2️⃣ ADDING NEW STUDENT...")
new_student = {
    "roll_no": "999",
    "name": "Test Student New",
    "email": "test999@example.com"
}
try:
    response = requests.post(f"{BASE_URL}/teacher/students", json=new_student, headers=headers)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    print(f"✅ Student added: {data.get('data', {}).get('name')}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Fetch students AFTER adding
print("\n3️⃣ FETCHING STUDENTS (AFTER ADD)...")
try:
    response = requests.get(f"{BASE_URL}/teacher/students", headers=headers)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    if data.get('success') and data.get('data'):
        students_after = data['data'].get('students', [])
        print(f"Students count after: {len(students_after)}")
        print("\nStudent List:")
        for s in students_after:
            print(f"  - {s.get('name')} (Roll: {s.get('roll_no')})")
    else:
        print("❌ Failed to fetch students")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
