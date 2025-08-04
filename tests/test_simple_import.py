#!/usr/bin/env python3
"""
Simple import test.
"""

import sys
import os

# Add src to path - adjust path since we're now in tests directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    print("Testing basic imports...")
    
    # Test individual imports
    print("1. Testing tkinter...")
    import tkinter as tk
    from tkinter import ttk
    print("✅ tkinter imported")
    
    print("2. Testing datetime...")
    from datetime import datetime, timedelta
    print("✅ datetime imported")
    
    print("3. Testing typing...")
    from typing import List, Dict, Any, Optional, Callable
    print("✅ typing imported")
    
    print("4. Testing BasePage...")
    from gui.page_manager import BasePage
    print("✅ BasePage imported")
    
    print("5. Testing ExecutionLog...")
    from models.execution import ExecutionLog
    print("✅ ExecutionLog imported")
    
    print("6. Testing log storage...")
    from storage.log_storage import get_log_storage
    print("✅ log_storage imported")
    
    print("7. Testing logs page...")
    from gui.pages.logs_page import ScheduleLogsPage
    print("✅ ScheduleLogsPage imported")
    
    print("\n🎉 All imports successful!")
    
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