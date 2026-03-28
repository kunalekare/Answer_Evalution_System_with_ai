#!/usr/bin/env python3
"""
Test teacher login flow and student management endpoints.
This script verifies that the authentication fix is working properly.
"""

import requests
import json
import time
from typing import Dict, Optional, Any

BASE_URL = "http://localhost:8000/api/v1"

class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    """Print success message."""
    print(f"{Color.GREEN}✓ {msg}{Color.END}")

def print_error(msg: str):
    """Print error message."""
    print(f"{Color.RED}✗ {msg}{Color.END}")

def print_info(msg: str):
    """Print info message."""
    print(f"{Color.BLUE}ℹ {msg}{Color.END}")

def print_warning(msg: str):
    """Print warning message."""
    print(f"{Color.YELLOW}⚠ {msg}{Color.END}")

def test_teacher_login() -> Optional[Dict[str, Any]]:
    """Test teacher login endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Teacher Login")
    print("="*60)
    
    login_data = {
        "email": "teacher@assessiq.com",
        "password": "teacher123",
        "role": "teacher"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        print_info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Login successful!")
            print(f"  - Email: {data.get('user', {}).get('email')}")
            print(f"  - Role: {data.get('user', {}).get('role')}")
            print(f"  - Token: {data.get('access_token', '')[:30]}...")
            return data
        else:
            print_error(f"Login failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Login request failed: {e}")
        return None

def test_get_classes(token: str) -> bool:
    """Test getting teacher's classes."""
    print("\n" + "="*60)
    print("TEST 2: Get Teacher's Classes")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/teacher/classes", headers=headers, timeout=10)
        print_info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Classes retrieved successfully!")
            classes = data.get('data', [])
            if isinstance(classes, list):
                print(f"  - Found {len(classes)} classes")
                for cls in classes[:3]:  # Show first 3
                    print(f"    • {cls.get('name', 'N/A')}")
            return True
        elif response.status_code == 401:
            print_error("Unauthorized (401) - Token may be invalid")
            print(f"  Response: {response.text}")
            return False
        else:
            print_error(f"Failed to get classes: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def test_get_students(token: str) -> bool:
    """Test getting teacher's students."""
    print("\n" + "="*60)
    print("TEST 3: Get Teacher's Students")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/teacher/students", headers=headers, timeout=10)
        print_info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Students retrieved successfully!")
            students = data.get('data', [])
            if isinstance(students, list):
                print(f"  - Found {len(students)} students")
                for student in students[:3]:  # Show first 3
                    print(f"    • {student.get('name', 'N/A')} ({student.get('roll_no', 'N/A')})")
            return True
        elif response.status_code == 401:
            print_error("Unauthorized (401) - Token may be invalid")
            print(f"  Response: {response.text}")
            return False
        else:
            print_error(f"Failed to get students: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def test_without_token() -> bool:
    """Test that requests without token are rejected."""
    print("\n" + "="*60)
    print("TEST 4: Request Without Token (should fail)")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/teacher/classes", headers=headers, timeout=10)
        print_info(f"Response Status: {response.status_code}")
        
        if response.status_code in [401, 403]:
            print_success("Correctly rejected request without token")
            return True
        else:
            print_warning(f"Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("TEACHER LOGIN & AUTHENTICATION TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Login
    login_response = test_teacher_login()
    if not login_response:
        print_error("\nCannot continue - login failed!")
        return False
    
    token = login_response.get('access_token')
    
    # Test 2: Get classes
    classes_ok = test_get_classes(token)
    
    # Test 3: Get students  
    students_ok = test_get_students(token)
    
    # Test 4: Request without token
    test_without_token()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Login:              {'✓ PASS' if login_response else '✗ FAIL'}")
    print(f"Get Classes:        {'✓ PASS' if classes_ok else '✗ FAIL'}")
    print(f"Get Students:       {'✓ PASS' if students_ok else '✗ FAIL'}")
    print("="*60)
    
    all_pass = login_response and classes_ok and students_ok
    if all_pass:
        print_success("\nAll tests passed! ✓")
    else:
        print_error("\nSome tests failed! ✗")
    
    return all_pass

if __name__ == "__main__":
    main()
