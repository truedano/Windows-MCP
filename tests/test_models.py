"""
Tests for data models.
"""

import unittest
from datetime import datetime, timedelta
from src.models import (
    Task, TaskStatus, Schedule, ScheduleType, ConditionalTrigger, ConditionType,
    ActionType, ExecutionResult, ExecutionLog, ExecutionStatistics,
    AppConfig, HelpContent, FAQItem, ContactInfo, SystemStatistics,
    validation
)


class TestDataModels(unittest.TestCase):
    """Test cases for data models."""
    
    def test_action_type_enum(self):
        """Test ActionType enumeration."""
        self.assertEqual(ActionType.LAUNCH_APP.value, "launch_app")
        self.assertEqual(ActionType.CLOSE_APP.value, "close_app")
        self.assertEqual(ActionType.RESIZE_WINDOW.value, "resize_window")
    
    def test_execution_result_creation(self):
        """Test ExecutionResult creation and serialization."""
        result = ExecutionResult.success_result("launch_app", "notepad", "App launched successfully")
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "launch_app")
        self.assertEqual(result.target, "notepad")
        self.assertEqual(result.message, "App launched successfully")
        
        # Test serialization
        result_dict = result.to_dict()
        self.assertIn('success', result_dict)
        self.assertIn('timestamp', result_dict)
        
        # Test deserialization
        restored_result = ExecutionResult.from_dict(result_dict)
        self.assertEqual(restored_result.success, result.success)
        self.assertEqual(restored_result.operation, result.operation)
    
    def test_schedule_next_execution(self):
        """Test schedule next execution calculation."""
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        schedule = Schedule(
            schedule_type=ScheduleType.DAILY,
            start_time=start_time,
            repeat_enabled=True
        )
        
        # Test next execution from before start time
        from_time = datetime(2024, 1, 1, 9, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        self.assertEqual(next_exec, start_time)
        
        # Test next execution from after start time
        from_time = datetime(2024, 1, 1, 11, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        expected = datetime(2024, 1, 2, 10, 0, 0)
        self.assertEqual(next_exec, expected)
    
    def test_conditional_trigger_evaluation(self):
        """Test conditional trigger evaluation."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_TITLE_CONTAINS,
            condition_value="notepad",
            enabled=True
        )
        
        # Test positive case
        context = {'window_titles': ['Notepad - Untitled', 'Chrome Browser']}
        self.assertTrue(trigger.evaluate(context))
        
        # Test negative case
        context = {'window_titles': ['Chrome Browser', 'Calculator']}
        self.assertFalse(trigger.evaluate(context))
        
        # Test disabled trigger
        trigger.enabled = False
        self.assertTrue(trigger.evaluate(context))  # Should return True when disabled
    
    def test_task_validation(self):
        """Test task validation."""
        schedule = Schedule(
            schedule_type=ScheduleType.ONCE,
            start_time=datetime.now() + timedelta(hours=1)
        )
        
        task = Task(
            id="test_001",
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params={"app_name": "notepad"},
            schedule=schedule,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.assertTrue(task.validate())
        
        # Test invalid task (missing name)
        task.name = ""
        self.assertFalse(task.validate())
    
    def test_app_config_validation(self):
        """Test application configuration validation."""
        config = AppConfig()
        self.assertTrue(config.validate())
        
        # Test invalid schedule frequency
        config.schedule_check_frequency = 0
        self.assertFalse(config.validate())
        
        # Test invalid window dimensions
        config.schedule_check_frequency = 1  # Reset to valid
        config.window_width = 500  # Too small
        self.assertFalse(config.validate())
    
    def test_help_content_search(self):
        """Test help content search functionality."""
        help_content = HelpContent.get_default_content()
        
        # Search for existing content
        results = help_content.search_content("排程")
        self.assertGreater(len(results), 0)
        
        # Search for non-existing content
        results = help_content.search_content("xyz123nonexistent")
        self.assertEqual(len(results), 0)
    
    def test_execution_statistics(self):
        """Test execution statistics calculations."""
        stats = ExecutionStatistics.empty_stats()
        self.assertEqual(stats.success_rate, 0.0)
        self.assertEqual(stats.total_executions, 0)
        
        # Test with some data
        stats.total_executions = 10
        stats.successful_executions = 8
        stats.failed_executions = 2
        
        self.assertEqual(stats.success_rate, 80.0)
        self.assertEqual(stats.failure_rate, 20.0)
    
    def test_validation_functions(self):
        """Test validation utility functions."""
        # Test task name validation
        self.assertTrue(validation.validate_task_name("Valid Task Name"))
        self.assertFalse(validation.validate_task_name("Invalid<Name"))
        self.assertFalse(validation.validate_task_name(""))
        
        # Test email validation
        self.assertTrue(validation.validate_email("test@example.com"))
        self.assertFalse(validation.validate_email("invalid-email"))
        
        # Test coordinates validation
        self.assertTrue(validation.validate_coordinates(100, 200))
        self.assertFalse(validation.validate_coordinates(-1, 100))
        self.assertFalse(validation.validate_coordinates("100", 200))
        
        # Test keyboard keys validation
        self.assertTrue(validation.validate_keyboard_keys(["ctrl", "c"]))
        self.assertTrue(validation.validate_keyboard_keys(["alt", "f4"]))
        self.assertFalse(validation.validate_keyboard_keys(["invalid_key"]))
        self.assertFalse(validation.validate_keyboard_keys([]))


if __name__ == '__main__':
    unittest.main()