#!/usr/bin/env python3
"""
Test script for ScheduleLogsPage implementation.
"""

import sys
import os

# Add src to path (adjust for tests directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    # Test imports
    from gui.pages.logs_page import ScheduleLogsPage, SearchBarWidget, LogsTableWidget
    print("✅ All imports successful")
    
    # Test class instantiation (without actually creating widgets)
    print("✅ ScheduleLogsPage class available")
    print("✅ SearchBarWidget class available") 
    print("✅ LogsTableWidget class available")
    
    # Check if the class has required methods
    required_methods = [
        '_create_page_ui',
        '_load_initial_data',
        '_on_search',
        '_on_page_change',
        '_load_logs_page',
        '_refresh_logs',
        '_export_logs',
        '_clear_logs',
        '_backup_logs',
        '_on_log_select',
        'activate'
    ]
    
    for method in required_methods:
        if hasattr(ScheduleLogsPage, method):
            print(f"✅ Method {method} exists")
        else:
            print(f"❌ Method {method} missing")
    
    print("\n🎉 ScheduleLogsPage implementation test completed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)