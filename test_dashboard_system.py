"""
Dashboard System Test Script
=============================
Tests that dashboard initializes with zeros and updates correctly.

Run from workspace root:
    python test_dashboard.py
"""

import sys
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from datetime import datetime
from database.models import (
    SessionLocal, Admin, Teacher, Student, Dashboard, 
    UserRole, ActivityLog, ActivityType, init_db
)
from api.services.dashboard_service import DashboardService


def test_dashboard_initialization():
    """Test that dashboard initializes with all zeros"""
    print("\n" + "=" * 70)
    print("TEST 1: Dashboard Initialization with Zero Values")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Get or create a test teacher
        teacher = db.query(Teacher).first()
        if not teacher:
            print("❌ No teacher found in database. Please create a teacher first.")
            return False
        
        print(f"✓ Found teacher: {teacher.name} (ID: {teacher.id})")
        
        # Get or create dashboard
        dashboard = DashboardService.get_or_create_dashboard(
            db, teacher.id, UserRole.TEACHER
        )
        
        print(f"✓ Dashboard created: {dashboard.dashboard_id}")
        print(f"✓ Initialized at: {dashboard.initialized_at}")
        print(f"✓ Is first visit: {dashboard.is_first_visit}")
        
        # Verify all metrics are zero initially
        assert dashboard.students_taught == 0, "students_taught should be 0"
        assert dashboard.classes_managed == 0, "classes_managed should be 0"
        assert dashboard.evaluations_created == 0, "evaluations_created should be 0"
        assert dashboard.total_activities == 0, "total_activities should be 0"
        assert dashboard.documents_uploaded == 0, "documents_uploaded should be 0"
        assert dashboard.grievances_filed == 0, "grievances_filed should be 0"
        
        print("\n✓ All metrics initialized to ZERO")
        print(f"  - students_taught: {dashboard.students_taught}")
        print(f"  - classes_managed: {dashboard.classes_managed}")
        print(f"  - evaluations_created: {dashboard.evaluations_created}")
        print(f"  - total_activities: {dashboard.total_activities}")
        print(f"  - documents_uploaded: {dashboard.documents_uploaded}")
        print(f"  - grievances_filed: {dashboard.grievances_filed}")
        
        return True
    
    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()


def test_increment_activities():
    """Test that activity counter increments correctly"""
    print("\n" + "=" * 70)
    print("TEST 2: Increment Activity Counter")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        teacher = db.query(Teacher).first()
        if not teacher:
            print("❌ No teacher found")
            return False
        
        dashboard = DashboardService.get_dashboard_by_user(db, teacher.id, UserRole.TEACHER)
        if not dashboard:
            dashboard = DashboardService.get_or_create_dashboard(db, teacher.id, UserRole.TEACHER)
        
        initial_count = dashboard.total_activities
        print(f"✓ Initial activity count: {initial_count}")
        
        # Increment 3 times
        for i in range(3):
            DashboardService.increment_total_activities(db, dashboard)
            db.refresh(dashboard)
            print(f"  Increment {i+1}: {dashboard.total_activities}")
        
        assert dashboard.total_activities == initial_count + 3, "Activities should increment"
        print(f"\n✓ Activity counter incremented correctly")
        print(f"  Started at: {initial_count}")
        print(f"  Ended at: {dashboard.total_activities}")
        print(f"  Increments: 3")
        
        return True
    
    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()


def test_engagement_metrics():
    """Test engagement metrics increment"""
    print("\n" + "=" * 70)
    print("TEST 3: Engagement Metrics")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        teacher = db.query(Teacher).first()
        if not teacher:
            print("❌ No teacher found")
            return False
        
        dashboard = DashboardService.get_dashboard_by_user(db, teacher.id, UserRole.TEACHER)
        if not dashboard:
            dashboard = DashboardService.get_or_create_dashboard(db, teacher.id, UserRole.TEACHER)
        
        print(f"✓ Testing engagement metrics for teacher: {teacher.name}")
        
        # Test each engagement metric
        DashboardService.increment_documents_uploaded(db, dashboard)
        assert dashboard.documents_uploaded == 1, "documents_uploaded should be 1"
        print(f"✓ Documents uploaded incremented: {dashboard.documents_uploaded}")
        
        DashboardService.increment_grievances_filed(db, dashboard)
        assert dashboard.grievances_filed == 1, "grievances_filed should be 1"
        print(f"✓ Grievances filed incremented: {dashboard.grievances_filed}")
        
        DashboardService.increment_community_messages(db, dashboard)
        assert dashboard.community_messages_sent == 1, "community_messages should be 1"
        print(f"✓ Community messages incremented: {dashboard.community_messages_sent}")
        
        DashboardService.increment_documents_downloaded(db, dashboard)
        assert dashboard.documents_downloaded == 1, "documents_downloaded should be 1"
        print(f"✓ Documents downloaded incremented: {dashboard.documents_downloaded}")
        
        print(f"\n✓ All engagement metrics working correctly!")
        
        return True
    
    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()


def test_dashboard_reset():
    """Test dashboard reset to zero"""
    print("\n" + "=" * 70)
    print("TEST 4: Dashboard Reset to Zero")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        teacher = db.query(Teacher).first()
        if not teacher:
            print("❌ No teacher found")
            return False
        
        dashboard = DashboardService.get_dashboard_by_user(db, teacher.id, UserRole.TEACHER)
        if not dashboard:
            dashboard = DashboardService.get_or_create_dashboard(db, teacher.id, UserRole.TEACHER)
        
        # Add some data
        for _ in range(5):
            DashboardService.increment_total_activities(db, dashboard)
        DashboardService.increment_grievances_filed(db, dashboard)
        DashboardService.increment_community_messages(db, dashboard)
        
        db.refresh(dashboard)
        print(f"✓ Before reset:")
        print(f"  - total_activities: {dashboard.total_activities}")
        print(f"  - grievances_filed: {dashboard.grievances_filed}")
        print(f"  - community_messages_sent: {dashboard.community_messages_sent}")
        
        # Reset
        dashboard = DashboardService.reset_dashboard(db, dashboard)
        
        assert dashboard.total_activities == 0, "total_activities should be 0 after reset"
        assert dashboard.grievances_filed == 0, "grievances_filed should be 0 after reset"
        assert dashboard.community_messages_sent == 0, "community_messages should be 0 after reset"
        
        print(f"\n✓ After reset:")
        print(f"  - total_activities: {dashboard.total_activities}")
        print(f"  - grievances_filed: {dashboard.grievances_filed}")
        print(f"  - community_messages_sent: {dashboard.community_messages_sent}")
        
        print(f"\n✓ Dashboard reset to ZERO successfully!")
        
        return True
    
    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()


def test_metric_recording():
    """Test historical metric recording"""
    print("\n" + "=" * 70)
    print("TEST 5: Historical Metric Recording")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        teacher = db.query(Teacher).first()
        if not teacher:
            print("❌ No teacher found")
            return False
        
        dashboard = DashboardService.get_dashboard_by_user(db, teacher.id, UserRole.TEACHER)
        if not dashboard:
            dashboard = DashboardService.get_or_create_dashboard(db, teacher.id, UserRole.TEACHER)
        
        print(f"✓ Recording metrics for dashboard: {dashboard.dashboard_id}")
        
        # Record a metric
        metric = DashboardService.record_metric(
            db,
            dashboard,
            "evaluations_created",
            42.5,
            period_type="daily",
            context={"test": True}
        )
        
        assert metric.metric_value == 42.5, "Metric value should match"
        assert metric.metric_name == "evaluations_created", "Metric name should match"
        assert metric.period_type == "daily", "Period type should be daily"
        
        print(f"✓ Metric recorded successfully:")
        print(f"  - metric_id: {metric.metric_id}")
        print(f"  - metric_name: {metric.metric_name}")
        print(f"  - metric_value: {metric.metric_value}")
        print(f"  - period_type: {metric.period_type}")
        print(f"  - context: {metric.context}")
        
        # Get metric history
        history = DashboardService.get_metric_history(
            db,
            dashboard,
            "evaluations_created",
            days=30
        )
        
        assert len(history) >= 1, "History should have at least one record"
        print(f"\n✓ Retrieved metric history: {len(history)} records")
        
        return True
    
    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()


def test_dashboard_to_dict():
    """Test dashboard dictionary conversion for API response"""
    print("\n" + "=" * 70)
    print("TEST 6: Dashboard to Dictionary (API Response Format)")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        teacher = db.query(Teacher).first()
        if not teacher:
            print("❌ No teacher found")
            return False
        
        dashboard = DashboardService.get_dashboard_by_user(db, teacher.id, UserRole.TEACHER)
        if not dashboard:
            dashboard = DashboardService.get_or_create_dashboard(db, teacher.id, UserRole.TEACHER)
        
        # Convert to dictionary (what API returns)
        data = dashboard.to_dict()
        
        print(f"✓ Dashboard converted to dictionary for API response")
        print(f"\n  Keys in response: {list(data.keys())}")
        
        # Verify structure
        assert "dashboard_id" in data, "Should have dashboard_id"
        assert "user_role" in data, "Should have user_role"
        assert "common_metrics" in data, "Should have common_metrics"
        assert data["user_role"] == "teacher", "Should be teacher role"
        
        assert "teacher_metrics" in data, "Should have teacher_metrics"
        assert data["teacher_metrics"]["students_taught"] == 0, "Should start at 0"
        
        assert "engagement_metrics" in data, "Should have engagement_metrics"
        
        print(f"\n✓ API response structure verified!")
        print(f"  - dashboard_id: {data['dashboard_id']}")
        print(f"  - user_role: {data['user_role']}")
        print(f"  - teacher_metrics.students_taught: {data['teacher_metrics']['students_taught']}")
        
        return True
    
    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("DASHBOARD SYSTEM TEST SUITE")
    print("=" * 70)
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Initialize database
    print("\nInitializing database...")
    init_db()
    print("✓ Database initialized\n")
    
    # Run tests
    tests = [
        ("Initialization", test_dashboard_initialization),
        ("Increment Activities", test_increment_activities),
        ("Engagement Metrics", test_engagement_metrics),
        ("Dashboard Reset", test_dashboard_reset),
        ("Metric Recording", test_metric_recording),
        ("Dictionary Conversion", test_dashboard_to_dict),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 All dashboard tests passed! Dashboard system is working correctly.\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review above.\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
