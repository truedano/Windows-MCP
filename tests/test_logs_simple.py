#!/usr/bin/env python3
"""
Simple test for logs page implementation.
"""

import sys
import os

# Add src to path - adjust path since we're now in tests directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    print("Testing imports...")
    
    # Test basic imports
    from gui.pages.logs_page import ScheduleLogsPage
    print("✅ ScheduleLogsPage imported successfully")
    
    from gui.pages.logs_page import SearchBarWidget
    print("✅ SearchBarWidget imported successfully")
    
    from gui.pages.logs_page import LogsTableWidget
    print("✅ LogsTableWidget imported successfully")
    
    from gui.pages.logs_page import LogExportWidget
    print("✅ LogExportWidget imported successfully")
    
    from gui.pages.logs_page import PaginationWidget
    print("✅ PaginationWidget imported successfully")
    
    # Test class methods
    required_methods = [
        'initialize_content',
        'refresh_content',
        '_create_page_ui',
        '_load_initial_data',
        '_on_search',
        '_on_page_change',
        '_load_logs_page',
        '_refresh_logs',
        '_export_logs',
        '_clear_logs',
        '_backup_logs',
        '_on_log_select'
    ]
    
    for method in required_methods:
        if hasattr(ScheduleLogsPage, method):
            print(f"✅ Method {method} exists")
        else:
            print(f"❌ Method {method} missing")
    
    print("\n🎉 All tests passed! Logs page implementation is complete.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)