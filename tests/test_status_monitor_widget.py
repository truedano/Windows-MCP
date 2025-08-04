"""
Test for StatusMonitorWidget functionality.
"""

import tkinter as tk
from tkinter import ttk
import unittest
from datetime import datetime, timedelta

from src.gui.widgets.status_monitor_widget import StatusMonitorWidget
from src.models.statistics import SystemStatistics, SystemStatus, ActivityItem


class TestStatusMonitorWidget(unittest.TestCase):
    """Test cases for StatusMonitorWidget."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        self.widget = StatusMonitorWidget(self.root)
        
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'widget'):
            self.widget.destroy()
        self.root.destroy()
    
    def test_widget_creation(self):
        """Test that widget is created successfully."""
        self.assertIsInstance(self.widget, StatusMonitorWidget)
        self.assertIsInstance(self.widget, ttk.Frame)
    
    def test_statistics_display(self):
        """Test statistics display functionality."""
        # Create test statistics
        test_stats = SystemStatistics(
            active_tasks=10,
            total_executions=500,
            successful_executions=475,
            failed_executions=25,
            success_rate=95.0,
            recent_activities=[],
            system_status=SystemStatus(
                scheduler_running=True,
                windows_mcp_connected=True,
                logging_enabled=True,
                next_task_name="Test Task",
                next_task_time=datetime.now() + timedelta(hours=1),
                active_tasks_count=10
            ),
            uptime=timedelta(hours=5),
            last_updated=datetime.now()
        )
        
        # Set statistics
        self.widget.statistics = test_stats
        self.widget._update_statistics_display()
        
        # Check if values are displayed correctly
        self.assertEqual(self.widget.active_tasks_value.cget("text"), "10")
        self.assertEqual(self.widget.total_executions_value.cget("text"), "500")
        self.assertEqual(self.widget.success_rate_value.cget("text"), "95.0%")
    
    def test_system_status_display(self):
        """Test system status display functionality."""
        # Create test status
        test_status = SystemStatus(
            scheduler_running=True,
            windows_mcp_connected=False,
            logging_enabled=True,
            next_task_name="Test Task",
            next_task_time=datetime.now() + timedelta(minutes=30),
            active_tasks_count=5
        )
        
        test_stats = SystemStatistics(
            active_tasks=5,
            total_executions=100,
            successful_executions=95,
            failed_executions=5,
            success_rate=95.0,
            recent_activities=[],
            system_status=test_status,
            uptime=timedelta(hours=2),
            last_updated=datetime.now()
        )
        
        # Set statistics and update display
        self.widget.statistics = test_stats
        self.widget._update_system_status_display()
        
        # Check status indicators
        self.assertIn("運行中", self.widget.scheduler_status_label.cget("text"))
        self.assertIn("未連接", self.widget.mcp_status_label.cget("text"))
        self.assertIn("已啟用", self.widget.logging_status_label.cget("text"))
    
    def test_recent_activity_display(self):
        """Test recent activity display functionality."""
        # Create test activities
        activities = [
            ActivityItem(
                timestamp=datetime.now() - timedelta(minutes=5),
                description="測試任務1",
                status="success",
                details="成功完成"
            ),
            ActivityItem(
                timestamp=datetime.now() - timedelta(minutes=10),
                description="測試任務2",
                status="failure",
                details="執行失敗"
            ),
            ActivityItem(
                timestamp=datetime.now() - timedelta(minutes=15),
                description="測試任務3",
                status="warning",
                details="有警告"
            )
        ]
        
        test_stats = SystemStatistics(
            active_tasks=3,
            total_executions=50,
            successful_executions=45,
            failed_executions=5,
            success_rate=90.0,
            recent_activities=activities,
            system_status=SystemStatus(
                scheduler_running=True,
                windows_mcp_connected=True,
                logging_enabled=True
            ),
            uptime=timedelta(hours=1),
            last_updated=datetime.now()
        )
        
        # Set statistics and update display
        self.widget.statistics = test_stats
        self.widget._update_recent_activity_display()
        
        # Check if activities are displayed
        self.assertEqual(self.widget.activity_listbox.size(), 3)
        
        # Check if first activity contains expected text
        first_item = self.widget.activity_listbox.get(0)
        self.assertIn("測試任務1", first_item)
        self.assertIn("✓", first_item)
    
    def test_status_icon_mapping(self):
        """Test status icon mapping functionality."""
        self.assertEqual(self.widget._get_status_icon("success"), "✓")
        self.assertEqual(self.widget._get_status_icon("failure"), "✗")
        self.assertEqual(self.widget._get_status_icon("warning"), "⚠")
        self.assertEqual(self.widget._get_status_icon("info"), "ℹ")
        self.assertEqual(self.widget._get_status_icon("unknown"), "•")
    
    def test_update_interval_setting(self):
        """Test update interval setting functionality."""
        original_interval = self.widget.update_interval
        new_interval = 10000  # 10 seconds
        
        self.widget.set_update_interval(new_interval)
        self.assertEqual(self.widget.update_interval, new_interval)
    
    def test_refresh_callback(self):
        """Test refresh callback functionality."""
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        self.widget.set_refresh_callback(test_callback)
        self.widget._manual_refresh()
        
        self.assertTrue(callback_called)
    
    def test_error_handling(self):
        """Test error handling in status updates."""
        # Simulate error by setting invalid statistics
        self.widget.statistics = None
        
        # This should not raise an exception
        try:
            self.widget._update_statistics_display()
            self.widget._update_system_status_display()
            self.widget._update_recent_activity_display()
        except Exception as e:
            self.fail(f"Error handling failed: {e}")
    
    def test_formatted_uptime(self):
        """Test uptime formatting."""
        # Test different uptime formats
        test_cases = [
            (timedelta(minutes=30), "30分鐘"),
            (timedelta(hours=2, minutes=15), "2小時15分鐘"),
            (timedelta(days=1, hours=3, minutes=45), "1天3小時45分鐘")
        ]
        
        for uptime, expected in test_cases:
            test_stats = SystemStatistics.create_empty()
            test_stats.uptime = uptime
            
            formatted = test_stats.get_formatted_uptime()
            self.assertEqual(formatted, expected)


def run_manual_test():
    """Run manual test to visually inspect the widget."""
    root = tk.Tk()
    root.title("Status Monitor Widget Test")
    root.geometry("800x600")
    
    # Create the widget
    widget = StatusMonitorWidget(root)
    widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Add some test data
    def add_test_activity():
        if hasattr(widget, 'statistics') and widget.statistics:
            widget.statistics.add_activity(
                f"測試活動 {datetime.now().strftime('%H:%M:%S')}",
                "success",
                "手動測試活動"
            )
            widget._update_recent_activity_display()
    
    # Add test button
    button_frame = ttk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=5)
    
    test_button = ttk.Button(
        button_frame,
        text="添加測試活動",
        command=add_test_activity
    )
    test_button.pack(side=tk.LEFT)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        run_manual_test()
    else:
        unittest.main()