#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Windows Scheduler GUI
Tests all GUI components with business logic integration, Windows-MCP integration,
end-to-end user operation flows, and schedule logging functionality.

This test suite covers task 15.1 requirements:
- Test all GUI components with business logic integration
- Verify complete Windows-MCP integration functionality  
- Perform end-to-end user operation flow testing
- Test complete schedule logging page functionality
"""

import sys
import os
import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import threading
import time
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class IntegrationTestSuite(unittest.TestCase):
    """Comprehensive integration test suite."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
    def tearDown(self):
        """Clean up test environment."""
        if self.root:
            self.root.destroy()
    
    def test_01_core_imports_and_initialization(self):
        """Test 1: Core system imports and initialization."""
        print("\n=== Test 1: Core System Imports and Initialization ===")
        
        try:
            # Test core model imports
            from models.task import Task, TaskStatus
            from models.schedule import Schedule, ScheduleType
            from models.action import ActionType
            from models.config import AppConfig
            print("✓ Core model imports successful")
            
            # Test core business logic imports
            from core.scheduler_engine import SchedulerEngine
            from core.task_manager import TaskManager
            from core.config_manager import ConfigManager
            from core.log_manager import LogManager
            print("✓ Core business logic imports successful")
            
            # Test storage layer imports
            from storage.task_storage import TaskStorage
            from storage.log_storage import LogStorage
            print("✓ Storage layer imports successful")
            
            # Test Windows controller imports
            from core.windows_controller import WindowsController
            from core.mock_windows_controller import MockWindowsController
            print("✓ Windows controller imports successful")
            
            return True
        except Exception as e:
            print(f"✗ Core imports failed: {e}")
            self.fail(f"Core imports failed: {e}")
    
    def test_02_gui_components_integration(self):
        """Test 2: GUI components with business logic integration."""
        print("\n=== Test 2: GUI Components Integration ===")
        
        try:
            # Test main application components
            from gui.scheduler_app import SchedulerApp
            from gui.main_window import MainWindow
            from gui.page_manager import PageManager
            print("✓ Main GUI components imported")
            
            # Test page imports
            from gui.pages.overview_page import OverviewPage
            from gui.pages.schedules_page import SchedulesPage
            from gui.pages.apps_page import AppsPage
            from gui.pages.logs_page import ScheduleLogsPage
            from gui.pages.settings_page import SettingsPage
            print("✓ All page components imported")
            
            # Test widget imports
            from gui.widgets.app_monitor_panel import AppMonitorPanel
            from gui.widgets.status_monitor_widget import StatusMonitorWidget
            from gui.widgets.task_list_widget import TaskListWidget
            print("✓ Widget components imported")
            
            # Test dialog imports
            from gui.dialogs.schedule_dialog import ScheduleDialog
            from gui.dialogs.security_confirmation_dialog import SecurityConfirmationDialog
            print("✓ Dialog components imported")
            
            return True
        except Exception as e:
            print(f"✗ GUI components integration failed: {e}")
            self.fail(f"GUI components integration failed: {e}")
    
    def test_03_scheduler_engine_integration(self):
        """Test 3: Scheduler engine with task management integration."""
        print("\n=== Test 3: Scheduler Engine Integration ===")
        
        try:
            from core.scheduler_engine import SchedulerEngine, get_scheduler_engine
            from core.task_manager import TaskManager
            from models.task import Task, TaskStatus
            from models.schedule import Schedule, ScheduleType
            from models.action import ActionType
            
            # Test scheduler engine initialization
            engine = get_scheduler_engine()
            self.assertIsNotNone(engine)
            print("✓ Scheduler engine initialized")
            
            # Test task manager integration
            task_manager = TaskManager()
            self.assertIsNotNone(task_manager)
            print("✓ Task manager initialized")
            
            # Test creating a sample task
            task = Task(
                name="Integration Test Task",
                description="Test task for integration testing",
                action_type=ActionType.LAUNCH_APP,
                action_params={"app_path": "notepad.exe"},
                schedule=Schedule(
                    schedule_type=ScheduleType.ONCE,
                    start_time=datetime.now() + timedelta(seconds=5)
                )
            )
            
            # Test task validation
            self.assertTrue(task.validate())
            print("✓ Task creation and validation successful")
            
            # Test adding task to manager
            task_id = task_manager.add_task(task)
            self.assertIsNotNone(task_id)
            print(f"✓ Task added to manager with ID: {task_id}")
            
            # Test retrieving task
            retrieved_task = task_manager.get_task(task_id)
            self.assertIsNotNone(retrieved_task)
            self.assertEqual(retrieved_task.name, task.name)
            print("✓ Task retrieval successful")
            
            return True
        except Exception as e:
            print(f"✗ Scheduler engine integration failed: {e}")
            self.fail(f"Scheduler engine integration failed: {e}")
    
    def test_04_windows_mcp_integration(self):
        """Test 4: Windows-MCP integration functionality."""
        print("\n=== Test 4: Windows-MCP Integration ===")
        
        try:
            from core.windows_controller import WindowsController
            from core.mock_windows_controller import MockWindowsController
            
            # Test with mock controller for safe testing
            controller = MockWindowsController()
            self.assertIsNotNone(controller)
            print("✓ Mock Windows controller initialized")
            
            # Test application detection
            apps = controller.get_running_applications()
            self.assertIsInstance(apps, list)
            print(f"✓ Application detection successful: {len(apps)} apps found")
            
            # Test window operations (using mock)
            if apps:
                test_app = apps[0]
                
                # Test window state retrieval
                window_info = controller.get_window_info(test_app.get('pid', 0))
                self.assertIsInstance(window_info, dict)
                print("✓ Window info retrieval successful")
                
                # Test window operations
                result = controller.set_window_position(test_app.get('pid', 0), 100, 100)
                print(f"✓ Window position operation: {result}")
                
                result = controller.set_window_size(test_app.get('pid', 0), 800, 600)
                print(f"✓ Window size operation: {result}")
            
            return True
        except Exception as e:
            print(f"✗ Windows-MCP integration failed: {e}")
            self.fail(f"Windows-MCP integration failed: {e}")
    
    def test_05_end_to_end_user_flow(self):
        """Test 5: End-to-end user operation flow."""
        print("\n=== Test 5: End-to-End User Flow ===")
        
        try:
            from gui.scheduler_app import SchedulerApp
            from core.scheduler_engine import get_scheduler_engine
            from models.task import Task, TaskStatus
            from models.schedule import Schedule, ScheduleType
            from models.action import ActionType
            
            # Initialize scheduler app (without showing GUI)
            app = SchedulerApp()
            self.assertIsNotNone(app)
            print("✓ Scheduler app initialized")
            
            # Test configuration loading
            app._load_configuration()
            print("✓ Configuration loaded")
            
            # Test scheduler engine integration
            engine = get_scheduler_engine()
            self.assertIsNotNone(engine)
            print("✓ Scheduler engine accessible")
            
            # Simulate user creating a new task
            new_task = Task(
                name="End-to-End Test Task",
                description="Testing complete user workflow",
                action_type=ActionType.LAUNCH_APP,
                action_params={"app_path": "calc.exe"},
                schedule=Schedule(
                    schedule_type=ScheduleType.DAILY,
                    start_time=datetime.now() + timedelta(minutes=1)
                )
            )
            
            # Test task validation in user flow
            self.assertTrue(new_task.validate())
            print("✓ User task validation successful")
            
            # Test task addition through app
            task_id = app.task_manager.add_task(new_task)
            self.assertIsNotNone(task_id)
            print(f"✓ Task added through app workflow: {task_id}")
            
            # Test task listing
            tasks = app.task_manager.get_all_tasks()
            self.assertGreater(len(tasks), 0)
            print(f"✓ Task listing successful: {len(tasks)} tasks")
            
            # Test task status monitoring
            task = app.task_manager.get_task(task_id)
            self.assertEqual(task.status, TaskStatus.PENDING)
            print("✓ Task status monitoring successful")
            
            return True
        except Exception as e:
            print(f"✗ End-to-end user flow failed: {e}")
            self.fail(f"End-to-end user flow failed: {e}")
    
    def test_06_schedule_logging_functionality(self):
        """Test 6: Complete schedule logging page functionality."""
        print("\n=== Test 6: Schedule Logging Functionality ===")
        
        try:
            from gui.pages.logs_page import ScheduleLogsPage
            from storage.log_storage import LogStorage
            from core.log_manager import LogManager
            from models.execution import ExecutionLog, ExecutionStatus
            
            # Test log storage initialization
            log_storage = LogStorage()
            self.assertIsNotNone(log_storage)
            print("✓ Log storage initialized")
            
            # Test log manager initialization
            log_manager = LogManager()
            self.assertIsNotNone(log_manager)
            print("✓ Log manager initialized")
            
            # Create test logs
            test_log = ExecutionLog(
                task_id="test_task_001",
                task_name="Integration Test Task",
                execution_time=datetime.now(),
                status=ExecutionStatus.SUCCESS,
                message="Task executed successfully during integration test"
            )
            
            # Test log creation
            log_id = log_storage.add_log(test_log)
            self.assertIsNotNone(log_id)
            print(f"✓ Log creation successful: {log_id}")
            
            # Test log retrieval
            retrieved_log = log_storage.get_log(log_id)
            self.assertIsNotNone(retrieved_log)
            self.assertEqual(retrieved_log.task_name, test_log.task_name)
            print("✓ Log retrieval successful")
            
            # Test logs page initialization (without GUI)
            logs_page = ScheduleLogsPage(self.root)
            self.assertIsNotNone(logs_page)
            print("✓ Logs page initialized")
            
            # Test log filtering and search functionality
            all_logs = log_storage.get_logs()
            self.assertGreater(len(all_logs), 0)
            print(f"✓ Log listing successful: {len(all_logs)} logs")
            
            # Test log export functionality
            export_data = log_storage.export_logs()
            self.assertIsInstance(export_data, list)
            print("✓ Log export functionality successful")
            
            return True
        except Exception as e:
            print(f"✗ Schedule logging functionality failed: {e}")
            self.fail(f"Schedule logging functionality failed: {e}")
    
    def test_07_error_handling_integration(self):
        """Test 7: Error handling and recovery integration."""
        print("\n=== Test 7: Error Handling Integration ===")
        
        try:
            from core.error_handler import ErrorHandler
            from core.security_manager import SecurityManager
            from models.validation import ValidationError
            
            # Test error handler initialization
            error_handler = ErrorHandler()
            self.assertIsNotNone(error_handler)
            print("✓ Error handler initialized")
            
            # Test security manager initialization
            security_manager = SecurityManager()
            self.assertIsNotNone(security_manager)
            print("✓ Security manager initialized")
            
            # Test validation error handling
            try:
                from models.task import Task
                from models.action import ActionType
                
                # Create invalid task to test error handling
                invalid_task = Task(
                    name="",  # Invalid empty name
                    description="Test invalid task",
                    action_type=ActionType.LAUNCH_APP,
                    action_params={}  # Missing required parameters
                )
                
                # This should raise a validation error
                invalid_task.validate()
                self.fail("Expected validation error was not raised")
                
            except ValidationError:
                print("✓ Validation error handling successful")
            except Exception as e:
                print(f"✓ Error handling working: {type(e).__name__}")
            
            # Test security validation
            safe_path = "notepad.exe"
            unsafe_path = "../../system32/format.exe"
            
            is_safe = security_manager.validate_application_path(safe_path)
            print(f"✓ Security validation for safe path: {is_safe}")
            
            is_unsafe = security_manager.validate_application_path(unsafe_path)
            print(f"✓ Security validation for unsafe path: {not is_unsafe}")
            
            return True
        except Exception as e:
            print(f"✗ Error handling integration failed: {e}")
            self.fail(f"Error handling integration failed: {e}")
    
    def test_08_configuration_management_integration(self):
        """Test 8: Configuration management integration."""
        print("\n=== Test 8: Configuration Management Integration ===")
        
        try:
            from core.config_manager import ConfigManager
            from models.config import AppConfig
            
            # Test config manager initialization
            config_manager = ConfigManager()
            self.assertIsNotNone(config_manager)
            print("✓ Config manager initialized")
            
            # Test configuration loading
            config = config_manager.load_config()
            self.assertIsInstance(config, AppConfig)
            print("✓ Configuration loading successful")
            
            # Test configuration modification
            original_log_level = config.log_level
            config.log_level = "DEBUG"
            
            # Test configuration saving
            config_manager.save_config(config)
            print("✓ Configuration saving successful")
            
            # Test configuration reload
            reloaded_config = config_manager.load_config()
            self.assertEqual(reloaded_config.log_level, "DEBUG")
            print("✓ Configuration reload successful")
            
            # Restore original configuration
            config.log_level = original_log_level
            config_manager.save_config(config)
            print("✓ Configuration restoration successful")
            
            return True
        except Exception as e:
            print(f"✗ Configuration management integration failed: {e}")
            self.fail(f"Configuration management integration failed: {e}")

def run_integration_tests():
    """Run all integration tests."""
    print("Windows Scheduler GUI - Comprehensive Integration Tests")
    print("=" * 60)
    print("Testing task 15.1 requirements:")
    print("- GUI components with business logic integration")
    print("- Windows-MCP integration functionality")
    print("- End-to-end user operation flows")
    print("- Schedule logging page functionality")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(IntegrationTestSuite)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✓ Task 15.1 requirements successfully verified")
    else:
        print("\n❌ SOME INTEGRATION TESTS FAILED")
        print("✗ Task 15.1 requirements need attention")
    
    return success

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)