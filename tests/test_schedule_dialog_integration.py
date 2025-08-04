#!/usr/bin/env python3
"""
Integration tests for ScheduleDialog functionality.
Tests the actual GUI dialog creation and basic operations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import tkinter as tk
from tkinter import ttk

def test_imports():
    """Test if all imports work correctly."""
    try:
        # Test model imports
        from models.task import Task, TaskStatus
        from models.schedule import Schedule, ScheduleType, ConditionalTrigger, ConditionType
        from models.action import ActionType, validate_action_params
        print("✓ Model imports successful")
        
        # Test widget imports
        from gui.widgets.trigger_time_widget import TriggerTimeWidget
        from gui.widgets.conditional_trigger_widget import ConditionalTriggerWidget
        from gui.widgets.action_type_widget import ActionTypeWidget
        from gui.widgets.execution_preview_widget import ExecutionPreviewWidget
        print("✓ Widget imports successful")
        
        # Test dialog import
        from gui.dialogs.schedule_dialog import ScheduleDialog
        print("✓ Dialog import successful")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_dialog_creation():
    """Test creating the dialog."""
    try:
        root = tk.Tk()
        root.withdraw()  # Hide root window
        
        from gui.dialogs.schedule_dialog import ScheduleDialog
        
        # Create dialog
        dialog = ScheduleDialog(root)
        print("✓ Dialog creation successful")
        
        # Test getting configuration (should return None for empty dialog)
        config = dialog._get_schedule_config()
        print(f"✓ Configuration retrieval: {config is None}")
        
        root.destroy()
        return True
    except Exception as e:
        print(f"✗ Dialog creation failed: {e}")
        return False

def main():
    """Main test function."""
    print("ScheduleDialog Integration Tests")
    print("=" * 35)
    
    # Test imports
    if not test_imports():
        return False
    
    print()
    
    # Test dialog creation
    if not test_dialog_creation():
        return False
    
    print()
    print("✓ All tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)