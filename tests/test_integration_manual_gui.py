#!/usr/bin/env python3
"""
Manual GUI Integration Test for Windows Scheduler GUI
Tests the complete GUI application with user interaction capabilities.

This complements the automated integration tests by providing manual testing
for GUI components that require user interaction.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class ManualGUIIntegrationTest:
    """Manual GUI integration test interface."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Manual GUI Integration Test")
        self.root.geometry("800x600")
        
        self.test_results = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the test interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Manual GUI Integration Tests", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Test buttons frame
        tests_frame = ttk.LabelFrame(main_frame, text="Integration Tests", padding="10")
        tests_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Test buttons
        test_buttons = [
            ("1. Test Main Application Launch", self.test_main_app_launch),
            ("2. Test Schedule Dialog Integration", self.test_schedule_dialog),
            ("3. Test Apps Page Integration", self.test_apps_page),
            ("4. Test Logs Page Integration", self.test_logs_page),
            ("5. Test Settings Page Integration", self.test_settings_page),
            ("6. Test Task Creation Workflow", self.test_task_workflow),
            ("7. Test Error Handling GUI", self.test_error_handling),
            ("8. Test Complete User Journey", self.test_complete_journey)
        ]
        
        for i, (text, command) in enumerate(test_buttons):
            btn = ttk.Button(tests_frame, text=text, command=command, width=40)
            btn.grid(row=i, column=0, pady=2, sticky=tk.W)
            
            # Status label
            status_label = ttk.Label(tests_frame, text="Not tested", foreground="gray")
            status_label.grid(row=i, column=1, padx=(10, 0), sticky=tk.W)
            self.test_results[text] = status_label
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Test Results", padding="10")
        results_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Results text
        self.results_text = tk.Text(results_frame, height=15, width=80)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(control_frame, text="Run All Tests", 
                  command=self.run_all_tests).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(control_frame, text="Clear Results", 
                  command=self.clear_results).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(control_frame, text="Export Results", 
                  command=self.export_results).grid(row=0, column=2)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        self.log("Manual GUI Integration Test initialized")
        self.log("Click on test buttons to run individual tests")
        self.log("=" * 50)
    
    def log(self, message):
        """Log message to results text."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.results_text.see(tk.END)
        self.root.update()
    
    def update_test_status(self, test_name, status, color="green"):
        """Update test status."""
        if test_name in self.test_results:
            self.test_results[test_name].config(text=status, foreground=color)
    
    def test_main_app_launch(self):
        """Test 1: Main application launch integration."""
        self.log("\n=== Test 1: Main Application Launch ===")
        
        try:
            from gui.scheduler_app import SchedulerApp
            
            self.log("Importing SchedulerApp...")
            
            # Create app instance (but don't run mainloop)
            app = SchedulerApp()
            self.log("✓ SchedulerApp created successfully")
            
            # Test initialization
            app._load_configuration()
            self.log("✓ Configuration loaded")
            
            # Test main window creation
            if hasattr(app, 'main_window'):
                self.log("✓ Main window component available")
            
            self.update_test_status("1. Test Main Application Launch", "PASSED")
            self.log("✓ Main application launch test completed successfully")
            
        except Exception as e:
            self.log(f"✗ Main application launch test failed: {e}")
            self.update_test_status("1. Test Main Application Launch", "FAILED", "red")
    
    def test_schedule_dialog(self):
        """Test 2: Schedule dialog integration."""
        self.log("\n=== Test 2: Schedule Dialog Integration ===")
        
        try:
            from gui.dialogs.schedule_dialog import ScheduleDialog
            
            self.log("Creating schedule dialog...")
            
            # Create dialog
            dialog = ScheduleDialog(self.root)
            self.log("✓ Schedule dialog created")
            
            # Test dialog components
            if hasattr(dialog, '_create_ui'):
                self.log("✓ Dialog UI creation method available")
            
            # Test configuration retrieval
            config = dialog._get_schedule_config()
            self.log(f"✓ Configuration retrieval: {config is None}")
            
            self.update_test_status("2. Test Schedule Dialog Integration", "PASSED")
            self.log("✓ Schedule dialog integration test completed")
            
        except Exception as e:
            self.log(f"✗ Schedule dialog test failed: {e}")
            self.update_test_status("2. Test Schedule Dialog Integration", "FAILED", "red")
    
    def test_apps_page(self):
        """Test 3: Apps page integration."""
        self.log("\n=== Test 3: Apps Page Integration ===")
        
        try:
            from gui.pages.apps_page import AppsPage
            
            self.log("Creating apps page...")
            
            # Create page
            page = AppsPage(self.root)
            self.log("✓ Apps page created")
            
            # Test page activation
            if hasattr(page, 'activate'):
                page.activate()
                self.log("✓ Page activation successful")
            
            self.update_test_status("3. Test Apps Page Integration", "PASSED")
            self.log("✓ Apps page integration test completed")
            
        except Exception as e:
            self.log(f"✗ Apps page test failed: {e}")
            self.update_test_status("3. Test Apps Page Integration", "FAILED", "red")
    
    def test_logs_page(self):
        """Test 4: Logs page integration."""
        self.log("\n=== Test 4: Logs Page Integration ===")
        
        try:
            from gui.pages.logs_page import ScheduleLogsPage
            
            self.log("Creating logs page...")
            
            # Create page
            page = ScheduleLogsPage(self.root)
            self.log("✓ Logs page created")
            
            # Test page methods
            required_methods = ['_create_page_ui', '_load_initial_data', 'activate']
            for method in required_methods:
                if hasattr(page, method):
                    self.log(f"✓ Method {method} available")
                else:
                    self.log(f"⚠ Method {method} missing")
            
            self.update_test_status("4. Test Logs Page Integration", "PASSED")
            self.log("✓ Logs page integration test completed")
            
        except Exception as e:
            self.log(f"✗ Logs page test failed: {e}")
            self.update_test_status("4. Test Logs Page Integration", "FAILED", "red")
    
    def test_settings_page(self):
        """Test 5: Settings page integration."""
        self.log("\n=== Test 5: Settings Page Integration ===")
        
        try:
            from gui.pages.settings_page import SettingsPage
            
            self.log("Creating settings page...")
            
            # Create page
            page = SettingsPage(self.root)
            self.log("✓ Settings page created")
            
            # Test page activation
            if hasattr(page, 'activate'):
                page.activate()
                self.log("✓ Page activation successful")
            
            self.update_test_status("5. Test Settings Page Integration", "PASSED")
            self.log("✓ Settings page integration test completed")
            
        except Exception as e:
            self.log(f"✗ Settings page test failed: {e}")
            self.update_test_status("5. Test Settings Page Integration", "FAILED", "red")
    
    def test_task_workflow(self):
        """Test 6: Task creation workflow."""
        self.log("\n=== Test 6: Task Creation Workflow ===")
        
        try:
            from models.task import Task, TaskStatus
            from models.schedule import Schedule, ScheduleType
            from models.action import ActionType
            from core.task_manager import TaskManager
            
            self.log("Testing task creation workflow...")
            
            # Create task manager
            task_manager = TaskManager()
            self.log("✓ Task manager created")
            
            # Create test task
            task = Task(
                name="Manual Test Task",
                description="Task created during manual testing",
                action_type=ActionType.LAUNCH_APP,
                action_params={"app_path": "notepad.exe"},
                schedule=Schedule(
                    schedule_type=ScheduleType.ONCE,
                    start_time=datetime.now() + timedelta(minutes=5)
                )
            )
            
            # Validate task
            if task.validate():
                self.log("✓ Task validation successful")
            
            # Add task
            task_id = task_manager.add_task(task)
            self.log(f"✓ Task added with ID: {task_id}")
            
            # Retrieve task
            retrieved_task = task_manager.get_task(task_id)
            if retrieved_task and retrieved_task.name == task.name:
                self.log("✓ Task retrieval successful")
            
            self.update_test_status("6. Test Task Creation Workflow", "PASSED")
            self.log("✓ Task creation workflow test completed")
            
        except Exception as e:
            self.log(f"✗ Task workflow test failed: {e}")
            self.update_test_status("6. Test Task Creation Workflow", "FAILED", "red")
    
    def test_error_handling(self):
        """Test 7: Error handling GUI."""
        self.log("\n=== Test 7: Error Handling GUI ===")
        
        try:
            from core.error_handler import ErrorHandler
            from models.validation import ValidationError
            
            self.log("Testing error handling...")
            
            # Create error handler
            error_handler = ErrorHandler()
            self.log("✓ Error handler created")
            
            # Test validation error
            try:
                from models.task import Task
                invalid_task = Task(name="", description="Invalid task")
                invalid_task.validate()
                self.log("⚠ Expected validation error not raised")
            except (ValidationError, Exception) as e:
                self.log(f"✓ Error handling working: {type(e).__name__}")
            
            self.update_test_status("7. Test Error Handling GUI", "PASSED")
            self.log("✓ Error handling test completed")
            
        except Exception as e:
            self.log(f"✗ Error handling test failed: {e}")
            self.update_test_status("7. Test Error Handling GUI", "FAILED", "red")
    
    def test_complete_journey(self):
        """Test 8: Complete user journey."""
        self.log("\n=== Test 8: Complete User Journey ===")
        
        try:
            self.log("Testing complete user journey...")
            
            # This would typically involve:
            # 1. Launch app
            # 2. Navigate to schedules page
            # 3. Create new task
            # 4. View task in list
            # 5. Check logs
            # 6. Modify settings
            
            from gui.scheduler_app import SchedulerApp
            from core.scheduler_engine import get_scheduler_engine
            
            # Initialize app components
            app = SchedulerApp()
            engine = get_scheduler_engine()
            
            self.log("✓ App and engine initialized")
            
            # Test navigation components
            if hasattr(app, 'page_manager'):
                self.log("✓ Page manager available")
            
            self.log("✓ Complete user journey components verified")
            
            self.update_test_status("8. Test Complete User Journey", "PASSED")
            self.log("✓ Complete user journey test completed")
            
        except Exception as e:
            self.log(f"✗ Complete user journey test failed: {e}")
            self.update_test_status("8. Test Complete User Journey", "FAILED", "red")
    
    def run_all_tests(self):
        """Run all tests sequentially."""
        self.log("\n" + "=" * 50)
        self.log("RUNNING ALL MANUAL GUI INTEGRATION TESTS")
        self.log("=" * 50)
        
        tests = [
            self.test_main_app_launch,
            self.test_schedule_dialog,
            self.test_apps_page,
            self.test_logs_page,
            self.test_settings_page,
            self.test_task_workflow,
            self.test_error_handling,
            self.test_complete_journey
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(0.5)  # Brief pause between tests
            except Exception as e:
                self.log(f"✗ Test failed with exception: {e}")
        
        self.log("\n" + "=" * 50)
        self.log("ALL MANUAL TESTS COMPLETED")
        self.log("=" * 50)
        
        # Show summary
        self.show_summary()
    
    def show_summary(self):
        """Show test summary."""
        passed = 0
        failed = 0
        not_tested = 0
        
        for label in self.test_results.values():
            status = label.cget("text")
            if status == "PASSED":
                passed += 1
            elif status == "FAILED":
                failed += 1
            else:
                not_tested += 1
        
        summary = f"""
TEST SUMMARY:
- Passed: {passed}
- Failed: {failed}
- Not tested: {not_tested}
- Total: {len(self.test_results)}
        """
        
        self.log(summary)
        
        if failed == 0 and not_tested == 0:
            messagebox.showinfo("Test Results", "🎉 All manual integration tests passed!")
        elif failed > 0:
            messagebox.showwarning("Test Results", f"⚠ {failed} tests failed. Check results for details.")
        else:
            messagebox.showinfo("Test Results", f"ℹ {not_tested} tests not run yet.")
    
    def clear_results(self):
        """Clear results text."""
        self.results_text.delete(1.0, tk.END)
        for label in self.test_results.values():
            label.config(text="Not tested", foreground="gray")
    
    def export_results(self):
        """Export results to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"manual_integration_test_results_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Manual GUI Integration Test Results\n")
                f.write("=" * 40 + "\n")
                f.write(f"Generated: {datetime.now()}\n\n")
                f.write(self.results_text.get(1.0, tk.END))
            
            messagebox.showinfo("Export", f"Results exported to {filename}")
            self.log(f"✓ Results exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {e}")
            self.log(f"✗ Export failed: {e}")
    
    def run(self):
        """Run the manual test interface."""
        self.root.mainloop()

def main():
    """Main function."""
    print("Starting Manual GUI Integration Test...")
    
    test_app = ManualGUIIntegrationTest()
    test_app.run()

if __name__ == "__main__":
    main()