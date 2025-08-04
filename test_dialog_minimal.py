#!/usr/bin/env python3
"""
Minimal test for schedule dialog.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """Test basic imports."""
    print("Testing basic imports...")
    
    try:
        import tkinter as tk
        print("✓ tkinter imported")
    except ImportError as e:
        print(f"✗ tkinter import failed: {e}")
        return False
    
    try:
        from datetime import datetime, timedelta
        print("✓ datetime imported")
    except ImportError as e:
        print(f"✗ datetime import failed: {e}")
        return False
    
    return True

def test_model_imports():
    """Test model imports."""
    print("Testing model imports...")
    
    try:
        from models.schedule import ScheduleType, ConditionType
        print("✓ schedule models imported")
    except ImportError as e:
        print(f"✗ schedule models import failed: {e}")
        return False
    
    try:
        from models.action import ActionType
        print("✓ action models imported")
    except ImportError as e:
        print(f"✗ action models import failed: {e}")
        return False
    
    try:
        from models.task import Task, TaskStatus
        print("✓ task models imported")
    except ImportError as e:
        print(f"✗ task models import failed: {e}")
        return False
    
    return True

def test_widget_imports():
    """Test widget imports."""
    print("Testing widget imports...")
    
    try:
        from gui.widgets.trigger_time_widget import TriggerTimeWidget
        print("✓ TriggerTimeWidget imported")
    except ImportError as e:
        print(f"✗ TriggerTimeWidget import failed: {e}")
        return False
    
    try:
        from gui.widgets.conditional_trigger_widget import ConditionalTriggerWidget
        print("✓ ConditionalTriggerWidget imported")
    except ImportError as e:
        print(f"✗ ConditionalTriggerWidget import failed: {e}")
        return False
    
    try:
        from gui.widgets.action_type_widget import ActionTypeWidget
        print("✓ ActionTypeWidget imported")
    except ImportError as e:
        print(f"✗ ActionTypeWidget import failed: {e}")
        return False
    
    try:
        from gui.widgets.execution_preview_widget import ExecutionPreviewWidget
        print("✓ ExecutionPreviewWidget imported")
    except ImportError as e:
        print(f"✗ ExecutionPreviewWidget import failed: {e}")
        return False
    
    return True

def test_dialog_import():
    """Test dialog import."""
    print("Testing dialog import...")
    
    try:
        from gui.dialogs.schedule_dialog import ScheduleDialog
        print("✓ ScheduleDialog imported")
        return True
    except ImportError as e:
        print(f"✗ ScheduleDialog import failed: {e}")
        return False

def main():
    """Main test function."""
    print("Schedule Dialog Implementation Test")
    print("=" * 40)
    
    tests = [
        test_basic_imports,
        test_model_imports,
        test_widget_imports,
        test_dialog_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Dialog implementation is ready.")
        return True
    else:
        print("✗ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)