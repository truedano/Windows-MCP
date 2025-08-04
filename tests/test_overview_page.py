"""
Test system overview page implementation.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
from datetime import datetime, timedelta

from src.gui.pages.overview_page import OverviewPage
from src.models.statistics import SystemStatistics, ActivityItem, SystemStatus


class TestOverviewPage(unittest.TestCase):
    """Test overview page functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
        # Mock managers
        self.mock_task_manager = Mock()
        self.mock_scheduler_engine = Mock()
        self.mock_log_manager = Mock()
        
        # Create overview page with mocked managers
        with patch('src.gui.pages.overview_page.get_task_manager', return_value=self.mock_task_manager):
            with patch('src.gui.pages.overview_page.get_scheduler_engine', return_value=self.mock_scheduler_engine):
                with patch('src.gui.pages.overview_page.get_log_manager', return_value=self.mock_log_manager):
                    self.overview_page = OverviewPage(self.root)
    
    def tearDown(self):
        """Clean up test environment."""
        self.overview_page.destroy()
        self.root.destroy()
    
    def test_overview_page_initialization(self):
        """Test overview page initialization."""
        self.assertIsNotNone(self.overview_page)
        self.assertEqual(self.overview_page.page_name, "Overview")
        self.assertEqual(self.overview_page.display_name, "系統概覽")
    
    def test_get_current_statistics(self):
        """Test getting current statistics."""
        # Mock task manager
        mock_tasks = [Mock(status=Mock(value="active")), Mock(status=Mock(value="scheduled"))]
        self.mock_task_manager.get_all_tasks.return_value = mock_tasks
        
        # Mock log manager
        mock_stats = Mock()
        mock_stats.total_executions = 100
        mock_stats.successful_executions = 95
        mock_stats.failed_executions = 5
        mock_stats.success_rate = 95.0
        self.mock_log_manager.get_execution_statistics.return_value = mock_stats
        self.mock_log_manager.get_logs.return_value = []
        
        # Mock scheduler engine
        self.mock_scheduler_engine.is_running = True
        
        # Get statistics
        statistics = self.overview_page._get_current_statistics()
        
        # Verify statistics
        self.assertIsInstance(statistics, SystemStatistics)
        self.assertEqual(statistics.active_tasks, 2)
        self.assertEqual(statistics.total_executions, 100)
        self.assertEqual(statistics.successful_executions, 95)
        self.assertEqual(statistics.failed_executions, 5)
        self.assertEqual(statistics.success_rate, 95.0)
    
    def test_add_activity(self):
        """Test adding activity."""
        # Mock recent activity widget
        mock_widget = Mock()
        self.overview_page.recent_activity_widget = mock_widget
        
        # Add activity
        self.overview_page.add_activity("Test Task", "success", "Test details")
        
        # Verify activity was added
        mock_widget.add_activity.assert_called_once()
        call_args = mock_widget.add_activity.call_args[0][0]
        self.assertIsInstance(call_args, ActivityItem)
        self.assertEqual(call_args.description, "Test Task")
        self.assertEqual(call_args.status, "success")
        self.assertEqual(call_args.details, "Test details")
    
    def test_refresh_content(self):
        """Test content refresh."""
        # Mock widgets
        self.overview_page.statistics_panel = Mock()
        self.overview_page.recent_activity_widget = Mock()
        self.overview_page.system_status_widget = Mock()
        
        # Mock managers
        self.mock_task_manager.get_all_tasks.return_value = []
        self.mock_log_manager.get_execution_statistics.return_value = Mock(
            total_executions=0, successful_executions=0, failed_executions=0, success_rate=0.0
        )
        self.mock_log_manager.get_logs.return_value = []
        
        # Set page as initialized
        self.overview_page.is_initialized = True
        
        # Refresh content
        self.overview_page.refresh_content()
        
        # Verify widgets were updated
        self.overview_page.statistics_panel.update_statistics.assert_called_once()
        self.overview_page.recent_activity_widget.update_from_statistics.assert_called_once()
        self.overview_page.system_status_widget.update_from_statistics.assert_called_once()
    
    def test_auto_refresh_timer(self):
        """Test auto-refresh timer functionality."""
        # Mock the after method
        self.overview_page.frame.after = Mock(return_value="timer_id")
        
        # Start auto-refresh
        self.overview_page._start_auto_refresh()
        
        # Verify timer was started
        self.overview_page.frame.after.assert_called_once_with(
            self.overview_page._refresh_interval, 
            self.overview_page._auto_refresh
        )
        self.assertEqual(self.overview_page._refresh_timer, "timer_id")


class TestOverviewPageWidgets(unittest.TestCase):
    """Test overview page widget components."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()
    
    def tearDown(self):
        """Clean up test environment."""
        self.root.destroy()
    
    def test_statistics_panel_widget(self):
        """Test statistics panel widget."""
        from src.gui.widgets.statistics_panel_widget import StatisticsPanelWidget, StatisticsCard
        
        # Create widget
        widget = StatisticsPanelWidget(self.root)
        
        # Test statistics card
        card = StatisticsCard(self.root, "Test Title", "100", "#4CAF50")
        card.update_value("200", "Test subtitle")
        
        # Verify card was created
        self.assertIsNotNone(widget)
        self.assertIsNotNone(card)
    
    def test_recent_activity_widget(self):
        """Test recent activity widget."""
        from src.gui.widgets.recent_activity_widget import RecentActivityWidget
        
        # Create widget
        widget = RecentActivityWidget(self.root, max_items=5)
        
        # Create test activity
        activity = ActivityItem(
            timestamp=datetime.now(),
            description="Test Activity",
            status="success",
            details="Test details"
        )
        
        # Add activity
        widget.add_activity(activity)
        
        # Verify activity was added
        self.assertEqual(len(widget.activity_items), 1)
        self.assertEqual(widget.activity_items[0].description, "Test Activity")
    
    def test_system_status_widget(self):
        """Test system status widget."""
        from src.gui.widgets.system_status_widget import SystemStatusWidget, StatusIndicator
        
        # Create widget
        widget = SystemStatusWidget(self.root)
        
        # Test status indicator
        indicator = StatusIndicator(self.root, "Test Status")
        indicator.update_status(True, "Custom Text")
        
        # Verify widgets were created
        self.assertIsNotNone(widget)
        self.assertIsNotNone(indicator)
        self.assertTrue(indicator.status)


class TestSystemStatisticsIntegration(unittest.TestCase):
    """Test system statistics integration."""
    
    def test_system_statistics_creation(self):
        """Test system statistics creation."""
        # Create test data
        activities = [
            ActivityItem(datetime.now(), "Task 1", "success"),
            ActivityItem(datetime.now(), "Task 2", "failure")
        ]
        
        status = SystemStatus(
            scheduler_running=True,
            windows_mcp_connected=True,
            logging_enabled=True,
            next_task_name="Next Task",
            next_task_time=datetime.now() + timedelta(hours=1)
        )
        
        statistics = SystemStatistics(
            active_tasks=5,
            total_executions=100,
            successful_executions=95,
            failed_executions=5,
            success_rate=95.0,
            recent_activities=activities,
            system_status=status,
            uptime=timedelta(hours=24),
            last_updated=datetime.now()
        )
        
        # Verify statistics
        self.assertEqual(statistics.active_tasks, 5)
        self.assertEqual(statistics.total_executions, 100)
        self.assertEqual(statistics.success_rate, 95.0)
        self.assertEqual(len(statistics.recent_activities), 2)
        self.assertTrue(statistics.system_status.scheduler_running)
    
    def test_activity_item_serialization(self):
        """Test activity item serialization."""
        activity = ActivityItem(
            timestamp=datetime.now(),
            description="Test Activity",
            status="success",
            details="Test details"
        )
        
        # Test to_dict
        activity_dict = activity.to_dict()
        self.assertIn("timestamp", activity_dict)
        self.assertIn("description", activity_dict)
        self.assertIn("status", activity_dict)
        self.assertIn("details", activity_dict)
        
        # Test from_dict
        restored_activity = ActivityItem.from_dict(activity_dict)
        self.assertEqual(restored_activity.description, activity.description)
        self.assertEqual(restored_activity.status, activity.status)
        self.assertEqual(restored_activity.details, activity.details)


if __name__ == '__main__':
    unittest.main()