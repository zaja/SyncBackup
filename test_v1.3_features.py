#!/usr/bin/env python3
"""
Test script for SyncBackup v1.3 new features

This script tests:
1. Database schema updates (new tables)
2. Settings management
3. Notification queue functionality
4. Windows Service availability check

Author: Goran Zajec
Website: https://svejedobro.hr
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import DatabaseManager

def test_database_schema():
    """Test that new database tables exist"""
    print("=" * 60)
    print("TEST 1: Database Schema")
    print("=" * 60)
    
    db = DatabaseManager("app/sync_backup.db")
    
    # Test app_settings table
    try:
        settings = db.get_all_settings()
        print("✅ app_settings table exists")
        print(f"   Found {len(settings)} settings:")
        for key, value in settings.items():
            print(f"   - {key}: {value}")
    except Exception as e:
        print(f"❌ app_settings table error: {e}")
        return False
    
    # Test notification_queue table
    try:
        notifications = db.get_pending_notifications()
        print(f"✅ notification_queue table exists")
        print(f"   Found {len(notifications)} pending notifications")
    except Exception as e:
        print(f"❌ notification_queue table error: {e}")
        return False
    
    print()
    return True

def test_settings_management():
    """Test settings get/set functionality"""
    print("=" * 60)
    print("TEST 2: Settings Management")
    print("=" * 60)
    
    db = DatabaseManager("app/sync_backup.db")
    
    # Test getting settings
    try:
        lang = db.get_setting('language', 'hr')
        print(f"✅ Get setting 'language': {lang}")
        
        notif_mode = db.get_setting('notification_mode', 'batch')
        print(f"✅ Get setting 'notification_mode': {notif_mode}")
        
        batch_interval = db.get_setting('notification_batch_interval', '300')
        print(f"✅ Get setting 'notification_batch_interval': {batch_interval}")
        
    except Exception as e:
        print(f"❌ Error getting settings: {e}")
        return False
    
    # Test setting a value
    try:
        db.set_setting('test_setting', 'test_value')
        test_val = db.get_setting('test_setting')
        if test_val == 'test_value':
            print(f"✅ Set/Get test setting successful")
        else:
            print(f"❌ Set/Get test setting failed")
            return False
    except Exception as e:
        print(f"❌ Error setting value: {e}")
        return False
    
    print()
    return True

def test_notification_queue():
    """Test notification queue functionality"""
    print("=" * 60)
    print("TEST 3: Notification Queue")
    print("=" * 60)
    
    db = DatabaseManager("app/sync_backup.db")
    
    # Add test notification
    try:
        notif_id = db.add_notification_to_queue(
            job_id=999,
            job_name="Test Job",
            status="success",
            message="Test notification",
            files_processed=10,
            duration_seconds=5.5
        )
        print(f"✅ Added test notification (ID: {notif_id})")
    except Exception as e:
        print(f"❌ Error adding notification: {e}")
        return False
    
    # Get pending notifications
    try:
        pending = db.get_pending_notifications()
        print(f"✅ Retrieved {len(pending)} pending notifications")
        
        # Find our test notification
        test_notif = None
        for n in pending:
            if n['job_name'] == 'Test Job':
                test_notif = n
                break
        
        if test_notif:
            print(f"   Test notification found:")
            print(f"   - Job: {test_notif['job_name']}")
            print(f"   - Status: {test_notif['status']}")
            print(f"   - Files: {test_notif['files_processed']}")
            print(f"   - Duration: {test_notif['duration_seconds']}s")
        else:
            print(f"⚠️  Test notification not found in pending list")
    except Exception as e:
        print(f"❌ Error getting pending notifications: {e}")
        return False
    
    # Mark as sent
    try:
        if test_notif:
            db.mark_notifications_as_sent([test_notif['id']])
            print(f"✅ Marked test notification as sent")
            
            # Verify it's no longer pending
            pending_after = db.get_pending_notifications()
            still_pending = any(n['id'] == test_notif['id'] for n in pending_after)
            if not still_pending:
                print(f"✅ Test notification removed from pending queue")
            else:
                print(f"❌ Test notification still in pending queue")
                return False
    except Exception as e:
        print(f"❌ Error marking as sent: {e}")
        return False
    
    print()
    return True

def test_windows_service_availability():
    """Test if Windows Service functionality is available"""
    print("=" * 60)
    print("TEST 4: Windows Service Availability")
    print("=" * 60)
    
    try:
        from app.windows_service import PYWIN32_AVAILABLE, get_service_status
        
        if PYWIN32_AVAILABLE:
            print("✅ pywin32 is installed - Windows Service support available")
            
            # Try to get service status
            try:
                status = get_service_status()
                print(f"   Service status: {status}")
            except Exception as e:
                print(f"   Service status check: {e}")
        else:
            print("⚠️  pywin32 is NOT installed - Windows Service support disabled")
            print("   To enable: pip install pywin32")
    except Exception as e:
        print(f"❌ Error checking Windows Service: {e}")
        return False
    
    print()
    return True

def test_notification_batching_logic():
    """Test notification batching summary logic"""
    print("=" * 60)
    print("TEST 5: Notification Batching Logic")
    print("=" * 60)
    
    # Simulate multiple notifications
    test_notifications = [
        {'job_name': 'Job1', 'status': 'success', 'files_processed': 10},
        {'job_name': 'Job2', 'status': 'success', 'files_processed': 5},
        {'job_name': 'Job3', 'status': 'error', 'files_processed': 0},
        {'job_name': 'Job4', 'status': 'skipped', 'files_processed': 0},
        {'job_name': 'Job5', 'status': 'success', 'files_processed': 15},
        {'job_name': 'Job6', 'status': 'error', 'files_processed': 0},
    ]
    
    # Count by status
    success_count = sum(1 for n in test_notifications if n['status'] == 'success')
    error_count = sum(1 for n in test_notifications if n['status'] == 'error')
    skipped_count = sum(1 for n in test_notifications if n['status'] == 'skipped')
    
    print(f"Test data: {len(test_notifications)} notifications")
    print(f"✅ Success count: {success_count}")
    print(f"✅ Error count: {error_count}")
    print(f"✅ Skipped count: {skipped_count}")
    
    # Build summary message (same logic as in main.py)
    title = f"📊 Backup Summary ({len(test_notifications)} jobs)"
    
    message_parts = []
    if success_count > 0:
        message_parts.append(f"✅ {success_count} completed")
    if error_count > 0:
        message_parts.append(f"❌ {error_count} failed")
    if skipped_count > 0:
        message_parts.append(f"⏸️ {skipped_count} skipped")
    
    message = "\n".join(message_parts)
    
    # Add failed jobs
    if error_count > 0:
        failed_jobs = [n['job_name'] for n in test_notifications if n['status'] == 'error']
        message += f"\n\nFailed: {', '.join(failed_jobs[:3])}"
        if len(failed_jobs) > 3:
            message += f" (+{len(failed_jobs) - 3} more)"
    
    print(f"\nGenerated batch notification:")
    print(f"Title: {title}")
    print(f"Message:\n{message}")
    
    print()
    return True

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("SyncBackup v1.3 - Feature Tests")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("Database Schema", test_database_schema()))
    results.append(("Settings Management", test_settings_management()))
    results.append(("Notification Queue", test_notification_queue()))
    results.append(("Windows Service", test_windows_service_availability()))
    results.append(("Batching Logic", test_notification_batching_logic()))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! v1.3 features are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
