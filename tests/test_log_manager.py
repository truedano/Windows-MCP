"""
Tests for log manager functionality.
"""

import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from pathlib import Path

from src.core.log_manager import LogManager
from src.storage.log_storage import LogStorage
from src.models.execution import ExecutionLog, ExecutionResult, ExecutionStatistics
from src.models.task import Task, TaskStatus
from src.models.action import ActionType
from src.models.schedule import Schedule, ScheduleType


class TestLogManager(unittest.TestCase):
    """Test cases for LogManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = LogStorage(
            logs_dir=str(Path(self.temp_dir) / "logs"),
            logs_file="test_logs.json"
        )
        self.log_manager = LogManager(storage=self.storage)
        
        # Create test task
        self.test_task = Task(
            id="test_task_001",
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params={},
            schedule=Schedule(
                schedule_type=ScheduleType.ONCE,
                start_time=datetime.now()
            ),
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        # Create test execution results
        self.success_result = ExecutionResult.success_result(
            "launch_app",
            "notepad",
            "App launched successfully"
        )
        
        self.failure_result = ExecutionResult.failure_result(
            "launch_app",
            "notepad",
            "Failed to launch app"
        )
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_log_execution_success(self):
        """Test logging successful task execution."""
        duration = timedelta(seconds=2)
        
        success = self.log_manager.log_execution(
            self.test_task,
            self.success_result,
            duration
        )
        
        self.assertTrue(success)
        
        # Verify log was added to cache
        logs = self.log_manager.get_logs(0, 10)
        self.assertEqual(len(logs), 1)
        
        log = logs[0]
        self.assertEqual(log.schedule_name, self.test_task.name)
        self.assertTrue(log.result.success)
        self.assertEqual(log.duration, duration)
    
    def test_log_execution_failure(self):
        """Test logging failed task execution."""
        duration = timedelta(seconds=1)
        
        success = self.log_manager.log_execution(
            self.test_task,
            self.failure_result,
            duration
        )
        
        self.assertTrue(success)
        
        # Verify log was added
        logs = self.log_manager.get_logs(0, 10)
        self.assertEqual(len(logs), 1)
        
        log = logs[0]
        self.assertEqual(log.schedule_name, self.test_task.name)
        self.assertFalse(log.result.success)
        self.assertEqual(log.duration, duration)
    
    def test_log_execution_without_duration(self):
        """Test logging execution without providing duration."""
        success = self.log_manager.log_execution(
            self.test_task,
            self.success_result
        )
        
        self.assertTrue(success)
        
        # Verify log was added with calculated duration
        logs = self.log_manager.get_logs(0, 10)
        self.assertEqual(len(logs), 1)
        
        log = logs[0]
        self.assertIsInstance(log.duration, timedelta)
        self.assertGreaterEqual(log.duration.total_seconds(), 0)
    
    def test_get_logs_pagination(self):
        """Test log retrieval with pagination."""
        # Add multiple logs
        for i in range(10):
            task = Task(
                id=f"task_{i}",
                name=f"Task {i}",
                target_app="notepad",
                action_type=ActionType.LAUNCH_APP,
                action_params={},
                schedule=Schedule(
                    schedule_type=ScheduleType.ONCE,
                    start_time=datetime.now()
                ),
                status=TaskStatus.PENDING,
                created_at=datetime.now()
            )
            
            self.log_manager.log_execution(task, self.success_result)
        
        # Test pagination
        page1 = self.log_manager.get_logs(0, 5)
        page2 = self.log_manager.get_logs(1, 5)
        
        self.assertEqual(len(page1), 5)
        self.assertEqual(len(page2), 5)
        
        # Verify no overlap
        page1_ids = {log.id for log in page1}
        page2_ids = {log.id for log in page2}
        self.assertEqual(len(page1_ids & page2_ids), 0)
    
    def test_get_logs_with_filters(self):
        """Test log retrieval with filters."""
        # Add logs with different properties
        task1 = self.test_task
        task1.name = "Success Task"
        
        task2 = Task(
            id="task_002",
            name="Failure Task",
            target_app="calculator",
            action_type=ActionType.CLOSE_APP,
            action_params={},
            schedule=Schedule(
                schedule_type=ScheduleType.ONCE,
                start_time=datetime.now()
            ),
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.log_manager.log_execution(task1, self.success_result)
        self.log_manager.log_execution(task2, self.failure_result)
        
        # Test filter by success
        success_logs = self.log_manager.get_logs(0, 10, {'success': True})
        self.assertEqual(len(success_logs), 1)
        self.assertTrue(success_logs[0].result.success)
        
        # Test filter by schedule name
        task1_logs = self.log_manager.get_logs(0, 10, {'schedule_name': 'Success Task'})
        self.assertEqual(len(task1_logs), 1)
        self.assertEqual(task1_logs[0].schedule_name, 'Success Task')
    
    def test_search_logs(self):
        """Test log searching functionality."""
        # Add searchable logs
        self.log_manager.log_execution(self.test_task, self.success_result)
        
        # Search for logs
        results = self.log_manager.search_logs("notepad")
        self.assertGreater(len(results), 0)
        
        # Verify search results
        found_log = results[0]
        self.assertIn("notepad", found_log.result.target.lower())
    
    def test_get_execution_statistics(self):
        """Test execution statistics calculation."""
        # Add mixed success/failure logs
        for i in range(5):
            result = self.success_result if i % 2 == 0 else self.failure_result
            self.log_manager.log_execution(self.test_task, result)
        
        stats = self.log_manager.get_execution_statistics()
        
        self.assertIsInstance(stats, ExecutionStatistics)
        self.assertEqual(stats.total_executions, 5)
        self.assertEqual(stats.successful_executions, 3)  # 0, 2, 4
        self.assertEqual(stats.failed_executions, 2)     # 1, 3
        self.assertAlmostEqual(stats.success_rate, 60.0, places=1)
    
    def test_get_execution_statistics_empty(self):
        """Test statistics with no logs."""
        stats = self.log_manager.get_execution_statistics()
        
        self.assertEqual(stats.total_executions, 0)
        self.assertEqual(stats.successful_executions, 0)
        self.assertEqual(stats.failed_executions, 0)
        self.assertEqual(stats.success_rate, 0.0)
    
    def test_statistics_caching(self):
        """Test statistics caching mechanism."""
        # Add a log
        self.log_manager.log_execution(self.test_task, self.success_result)
        
        # Get statistics twice
        stats1 = self.log_manager.get_execution_statistics()
        stats2 = self.log_manager.get_execution_statistics()
        
        # Should be the same object (cached)
        self.assertIs(stats1, stats2)
        
        # Force refresh
        stats3 = self.log_manager.get_execution_statistics(force_refresh=True)
        
        # Should be different object but same values
        self.assertIsNot(stats1, stats3)
        self.assertEqual(stats1.total_executions, stats3.total_executions)
    
    def test_clear_old_logs(self):
        """Test clearing old logs."""
        # Add old and new logs
        old_time = datetime.now() - timedelta(days=10)
        new_time = datetime.now()
        
        # Mock execution times
        old_result = ExecutionResult.success_result("test", "app", "message")
        old_result.timestamp = old_time
        
        new_result = ExecutionResult.success_result("test", "app", "message")
        new_result.timestamp = new_time
        
        self.log_manager.log_execution(self.test_task, old_result)
        self.log_manager.log_execution(self.test_task, new_result)
        
        # Verify both logs exist
        all_logs = self.log_manager.get_logs(0, 10)
        self.assertEqual(len(all_logs), 2)
        
        # Clear old logs
        cutoff_date = datetime.now() - timedelta(days=5)
        success = self.log_manager.clear_old_logs(cutoff_date)
        self.assertTrue(success)
        
        # Verify only new log remains
        remaining_logs = self.log_manager.get_logs(0, 10)
        self.assertEqual(len(remaining_logs), 1)
    
    def test_get_logs_by_schedule(self):
        """Test getting logs by schedule name."""
        # Add logs for different schedules
        task1 = self.test_task
        task1.name = "Schedule A"
        
        task2 = Task(
            id="task_002",
            name="Schedule B",
            target_app="calculator",
            action_type=ActionType.LAUNCH_APP,
            action_params={},
            schedule=Schedule(
                schedule_type=ScheduleType.ONCE,
                start_time=datetime.now()
            ),
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.log_manager.log_execution(task1, self.success_result)
        self.log_manager.log_execution(task2, self.success_result)
        self.log_manager.log_execution(task1, self.failure_result)
        
        # Get logs for Schedule A
        schedule_a_logs = self.log_manager.get_logs_by_schedule("Schedule A")
        self.assertEqual(len(schedule_a_logs), 2)
        
        for log in schedule_a_logs:
            self.assertEqual(log.schedule_name, "Schedule A")
    
    def test_get_logs_by_date_range(self):
        """Test getting logs by date range."""
        # Add logs with different dates
        old_date = datetime.now() - timedelta(days=5)
        new_date = datetime.now()
        
        # Mock execution times
        old_result = ExecutionResult.success_result("test", "app", "old")
        old_result.timestamp = old_date
        
        new_result = ExecutionResult.success_result("test", "app", "new")
        new_result.timestamp = new_date
        
        self.log_manager.log_execution(self.test_task, old_result)
        self.log_manager.log_execution(self.test_task, new_result)
        
        # Get logs for recent date range
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)
        
        recent_logs = self.log_manager.get_logs_by_date_range(start_date, end_date)
        self.assertEqual(len(recent_logs), 1)
        self.assertIn("new", recent_logs[0].result.message)
    
    def test_get_failed_logs(self):
        """Test getting only failed logs."""
        # Add mixed logs
        self.log_manager.log_execution(self.test_task, self.success_result)
        self.log_manager.log_execution(self.test_task, self.failure_result)
        self.log_manager.log_execution(self.test_task, self.success_result)
        
        # Get failed logs
        failed_logs = self.log_manager.get_failed_logs()
        self.assertEqual(len(failed_logs), 1)
        self.assertFalse(failed_logs[0].result.success)
    
    def test_get_recent_activity(self):
        """Test getting recent activity."""
        # Add logs
        self.log_manager.log_execution(self.test_task, self.success_result)
        
        # Get recent activity
        recent_logs = self.log_manager.get_recent_activity(hours=1)
        self.assertEqual(len(recent_logs), 1)
    
    def test_get_schedule_statistics(self):
        """Test getting statistics for a specific schedule."""
        # Add logs for a schedule
        task = self.test_task
        task.name = "Test Schedule"
        
        self.log_manager.log_execution(task, self.success_result)
        self.log_manager.log_execution(task, self.failure_result)
        self.log_manager.log_execution(task, self.success_result)
        
        # Get schedule statistics
        stats = self.log_manager.get_schedule_statistics("Test Schedule")
        
        self.assertEqual(stats['total_executions'], 3)
        self.assertEqual(stats['successful_executions'], 2)
        self.assertEqual(stats['failed_executions'], 1)
        self.assertAlmostEqual(stats['success_rate'], 66.67, places=1)
        self.assertIsNotNone(stats['last_execution'])
    
    def test_get_schedule_statistics_empty(self):
        """Test getting statistics for non-existent schedule."""
        stats = self.log_manager.get_schedule_statistics("Non-existent")
        
        self.assertEqual(stats['total_executions'], 0)
        self.assertEqual(stats['successful_executions'], 0)
        self.assertEqual(stats['failed_executions'], 0)
        self.assertEqual(stats['success_rate'], 0.0)
    
    def test_get_daily_statistics(self):
        """Test getting daily statistics."""
        # Add logs
        self.log_manager.log_execution(self.test_task, self.success_result)
        self.log_manager.log_execution(self.test_task, self.failure_result)
        
        # Get daily statistics
        daily_stats = self.log_manager.get_daily_statistics(days=3)
        
        self.assertEqual(len(daily_stats), 3)
        
        # Today should have logs
        today_stats = daily_stats[0]
        self.assertEqual(today_stats['total_executions'], 2)
        self.assertEqual(today_stats['successful_executions'], 1)
        self.assertEqual(today_stats['failed_executions'], 1)
    
    def test_get_error_summary(self):
        """Test getting error summary."""
        # Add failed logs with different errors
        error1 = ExecutionResult.failure_result("test", "app", "Error type 1")
        error2 = ExecutionResult.failure_result("test", "app", "Error type 2")
        error3 = ExecutionResult.failure_result("test", "app", "Error type 1")  # Duplicate
        
        self.log_manager.log_execution(self.test_task, error1)
        self.log_manager.log_execution(self.test_task, error2)
        self.log_manager.log_execution(self.test_task, error3)
        
        # Get error summary
        error_summary = self.log_manager.get_error_summary()
        
        self.assertEqual(len(error_summary), 2)
        
        # Most common error should be first
        most_common = error_summary[0]
        self.assertEqual(most_common['error_message'], "Error type 1")
        self.assertEqual(most_common['count'], 2)
        self.assertAlmostEqual(most_common['percentage'], 66.67, places=1)
    
    def test_generate_execution_report(self):
        """Test generating comprehensive execution report."""
        # Add various logs
        task1 = self.test_task
        task1.name = "Task A"
        
        task2 = Task(
            id="task_002",
            name="Task B",
            target_app="calculator",
            action_type=ActionType.LAUNCH_APP,
            action_params={},
            schedule=Schedule(
                schedule_type=ScheduleType.ONCE,
                start_time=datetime.now()
            ),
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.log_manager.log_execution(task1, self.success_result)
        self.log_manager.log_execution(task2, self.failure_result)
        self.log_manager.log_execution(task1, self.success_result)
        
        # Generate report
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)
        
        report = self.log_manager.generate_execution_report(start_date, end_date)
        
        # Verify report structure
        self.assertIn('period', report)
        self.assertIn('summary', report)
        self.assertIn('schedule_breakdown', report)
        self.assertIn('daily_breakdown', report)
        self.assertIn('error_analysis', report)
        self.assertIn('performance_metrics', report)
        
        # Verify summary
        summary = report['summary']
        self.assertEqual(summary['total_executions'], 3)
        self.assertEqual(summary['successful_executions'], 2)
        self.assertEqual(summary['failed_executions'], 1)
        self.assertEqual(summary['unique_schedules'], 2)
    
    def test_export_logs(self):
        """Test exporting logs."""
        # Add logs
        self.log_manager.log_execution(self.test_task, self.success_result)
        self.log_manager.log_execution(self.test_task, self.failure_result)
        
        # Get logs to export
        logs = self.log_manager.get_logs(0, 10)
        
        # Export to JSON
        export_path = str(Path(self.temp_dir) / "export.json")
        success = self.log_manager.export_logs(logs, "json", export_path)
        
        self.assertTrue(success)
        self.assertTrue(Path(export_path).exists())
    
    def test_log_added_callbacks(self):
        """Test log added callback functionality."""
        callback_called = False
        callback_log = None
        
        def test_callback(log):
            nonlocal callback_called, callback_log
            callback_called = True
            callback_log = log
        
        # Add callback
        self.log_manager.add_log_added_callback(test_callback)
        
        # Log execution
        self.log_manager.log_execution(self.test_task, self.success_result)
        
        # Verify callback was called
        self.assertTrue(callback_called)
        self.assertIsNotNone(callback_log)
        self.assertEqual(callback_log.schedule_name, self.test_task.name)
        
        # Remove callback
        self.log_manager.remove_log_added_callback(test_callback)
    
    def test_cleanup_logs(self):
        """Test automatic log cleanup."""
        # Mock config manager
        mock_config = Mock()
        mock_config.log_retention_days = 7
        
        with patch.object(self.log_manager, 'config_manager') as mock_config_manager:
            mock_config_manager.get_config.return_value = mock_config
            
            # Add old logs
            old_result = ExecutionResult.success_result("test", "app", "old")
            old_result.timestamp = datetime.now() - timedelta(days=10)
            
            self.log_manager.log_execution(self.test_task, old_result)
            self.log_manager.log_execution(self.test_task, self.success_result)
            
            # Perform cleanup
            result = self.log_manager.cleanup_logs()
            
            self.assertTrue(result['success'])
            self.assertEqual(result['retention_days'], 7)
            self.assertGreater(result['logs_removed'], 0)
    
    def test_cache_management(self):
        """Test log cache management."""
        # Set small cache size for testing
        original_max_logs = self.log_manager._max_logs
        self.log_manager._max_logs = 3
        
        try:
            # Add more logs than cache can hold
            for i in range(5):
                task = Task(
                    id=f"task_{i}",
                    name=f"Task {i}",
                    target_app="notepad",
                    action_type=ActionType.LAUNCH_APP,
                    action_params={},
                    schedule=Schedule(
                        schedule_type=ScheduleType.ONCE,
                        start_time=datetime.now()
                    ),
                    status=TaskStatus.PENDING,
                    created_at=datetime.now()
                )
                
                self.log_manager.log_execution(task, self.success_result)
            
            # Verify cache size is limited
            with self.log_manager._cache_lock:
                cache_size = len(self.log_manager._log_cache)
            
            self.assertLessEqual(cache_size, 3)
            
        finally:
            # Restore original cache size
            self.log_manager._max_logs = original_max_logs
    
    def test_get_storage_statistics(self):
        """Test getting storage statistics."""
        # Add some logs
        self.log_manager.log_execution(self.test_task, self.success_result)
        
        # Get storage statistics
        stats = self.log_manager.get_storage_statistics()
        
        self.assertIsInstance(stats, dict)
        # The exact keys depend on storage implementation


if __name__ == "__main__":
    unittest.main()