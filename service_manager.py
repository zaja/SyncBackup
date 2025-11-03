#!/usr/bin/env python3
"""
Service Manager - Helper script for managing SyncBackup Windows Service
Run this script as Administrator to install/uninstall/manage the service

Usage:
    python service_manager.py install   - Install the service
    python service_manager.py uninstall - Uninstall the service
    python service_manager.py start     - Start the service
    python service_manager.py stop      - Stop the service
    python service_manager.py restart   - Restart the service
    python service_manager.py status    - Check service status
    python service_manager.py debug     - Run service in debug mode (console)
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point"""
    try:
        from app.windows_service import (
            install_service, uninstall_service, start_service, 
            stop_service, get_service_status, PYWIN32_AVAILABLE
        )
    except ImportError as e:
        print(f"Error importing service module: {e}")
        print("\nMake sure pywin32 is installed:")
        print("  pip install pywin32")
        return 1
    
    if not PYWIN32_AVAILABLE:
        print("Error: pywin32 is not available")
        print("\nPlease install it with:")
        print("  pip install pywin32")
        return 1
    
    # Check for admin privileges
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("=" * 70)
        print("ERROR: Administrator privileges required!")
        print("=" * 70)
        print("\nPlease run this script as Administrator:")
        print("  1. Right-click on Command Prompt or PowerShell")
        print("  2. Select 'Run as Administrator'")
        print("  3. Run the command again")
        print("=" * 70)
        return 1
    
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    
    command = sys.argv[1].lower()
    
    print("=" * 70)
    print("SyncBackup Service Manager")
    print("=" * 70)
    print()
    
    if command == "install":
        print("Installing SyncBackup Windows Service...")
        print()
        if install_service():
            print()
            print("=" * 70)
            print("SUCCESS: Service installed!")
            print("=" * 70)
            print("\nNext steps:")
            print("  1. Start the service: python service_manager.py start")
            print("  2. Or use Windows Services Manager (services.msc)")
            return 0
        else:
            print()
            print("=" * 70)
            print("FAILED: Service installation failed")
            print("=" * 70)
            return 1
    
    elif command == "uninstall":
        print("Uninstalling SyncBackup Windows Service...")
        print()
        if uninstall_service():
            print()
            print("=" * 70)
            print("SUCCESS: Service uninstalled!")
            print("=" * 70)
            return 0
        else:
            print()
            print("=" * 70)
            print("FAILED: Service uninstallation failed")
            print("=" * 70)
            return 1
    
    elif command == "start":
        print("Starting SyncBackup Windows Service...")
        print()
        if start_service():
            print()
            print("=" * 70)
            print("SUCCESS: Service started!")
            print("=" * 70)
            print("\nCheck status: python service_manager.py status")
            return 0
        else:
            print()
            print("=" * 70)
            print("FAILED: Service start failed")
            print("=" * 70)
            return 1
    
    elif command == "stop":
        print("Stopping SyncBackup Windows Service...")
        print()
        if stop_service():
            print()
            print("=" * 70)
            print("SUCCESS: Service stopped!")
            print("=" * 70)
            return 0
        else:
            print()
            print("=" * 70)
            print("FAILED: Service stop failed")
            print("=" * 70)
            return 1
    
    elif command == "restart":
        print("Restarting SyncBackup Windows Service...")
        print()
        print("Stopping service...")
        stop_service()
        import time
        time.sleep(2)
        print("Starting service...")
        if start_service():
            print()
            print("=" * 70)
            print("SUCCESS: Service restarted!")
            print("=" * 70)
            return 0
        else:
            print()
            print("=" * 70)
            print("FAILED: Service restart failed")
            print("=" * 70)
            return 1
    
    elif command == "status":
        print("Checking SyncBackup Windows Service status...")
        print()
        status = get_service_status()
        print(f"Service Status: {status}")
        print()
        print("=" * 70)
        return 0
    
    elif command == "debug":
        print("Running service in DEBUG mode (console)...")
        print("Press Ctrl+C to stop.")
        print()
        print("=" * 70)
        print()
        
        # Import and run service directly
        from app.windows_service import ServiceClass
        service = ServiceClass(None)
        try:
            service.main()
        except KeyboardInterrupt:
            print("\n\nService stopped by user")
            return 0
    
    else:
        print(f"Unknown command: {command}")
        print()
        print(__doc__)
        return 1

if __name__ == "__main__":
    sys.exit(main())
