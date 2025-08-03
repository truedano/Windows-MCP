"""
Tests for WindowStateManager functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import time

from src.core.window_state_manager import WindowStateManager
from src.core.windows_controller import WindowsController
from src.models.execution import ExecutionResult
from src.models.data_models import App


class TestWindowStateManager(unittest.TestCase):
    """Test cases for WindowStateManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_controller = Mock(spec=WindowsController)
        self.state_manager = WindowStateManager(self.mock_controller)
    
    def test_initialization(self):
        """Test WindowStateManager initialization."""
        self.assertIsNotNone(self.state_manager)
        self.assertEqual(self.state_manager.controller, self.mock_controller)
        self.assertFalse(self.state_manager._monitoring)
        self.assertEqual(self.state_manager._monitor_interval, 5.0)
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        # Test start monitoring
        result = self.state_manager.start_monitoring(interval=2.0)
        self.assertTrue(result)
        self.assertTrue(self.state_manager._monitoring)
        self.assertEqual(self.state_manager._monitor_interval, 2.0)
        
        # Test start monitoring when already running
        result = self.state_manager.start_monitoring()
        self.assertFalse(result)
        
        # Test stop monitoring
        result = self.state_manager.stop_monitoring()
        self.assertTrue(result)
        self.assertFalse(self.state_manager._monitoring)
        
        # Test stop monitoring when not running
        result = self.state_manager.stop_monitoring()
        self.assertFalse(result)
    
    def test_get_window_state_history_empty(self):
        """Test getting window state history when empty."""
        history = self.state_manager.get_window_state_history("notepad")
        self.assertEqual(history, [])
    
    def test_get_current_window_states_empty(self):
        """Test getting current window states when empty."""
        states = self.state_manager.get_current_window_states()
        self.assertEqual(states, {})
    
    def test_restore_window_state_app_not_found(self):
        """Test restoring window state when app is not found."""
        self.mock_controller.get_app_state.return_value = None
        
        target_state = {
            'position': {'x': 100, 'y': 200},
            'size': {'width': 800, 'height': 600}
        }
        
        result = self.state_manager.restore_window_state("notepad", target_state)
        
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "restore_window_state")
        self.assertEqual(result.target, "notepad")
        self.assertIn("not found", result.message)
    
    def test_restore_window_state_success(self):
        """Test successful window state restoration."""
        # Mock current app state
        current_state = {
            'name': 'notepad.exe',
            'position': {'x': 0, 'y': 0},
            'size': {'width': 400, 'height': 300},
            'is_visible': True
        }
        self.mock_controller.get_app_state.return_value = current_state
        
        # Mock successful operations
        self.mock_controller.move_window.return_value = ExecutionResult.success_result(
            "move_window", "notepad", "Moved successfully"
        )
        self.mock_controller.resize_window.return_value = ExecutionResult.success_result(
            "resize_window", "notepad", "Resized successfully"
        )
        
        target_state = {
            'position': {'x': 100, 'y': 200},
            'size': {'width': 800, 'height': 600}
        }
        
        result = self.state_manager.restore_window_state("notepad", target_state)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "restore_window_state")
        self.assertEqual(result.target, "notepad")
        
        # Verify operations were called
        self.mock_controller.move_window.assert_called_once_with("notepad", 100, 200)
        self.mock_controller.resize_window.assert_called_once_with("notepad", 800, 600)
    
    def test_restore_window_state_with_visibility(self):
        """Test window state restoration with visibility changes."""
        current_state = {
            'name': 'notepad.exe',
            'is_visible': False
        }
        self.mock_controller.get_app_state.return_value = current_state
        self.mock_controller.focus_window.return_value = ExecutionResult.success_result(
            "focus_window", "notepad", "Focused successfully"
        )
        
        target_state = {'is_visible': True}
        
        result = self.state_manager.restore_window_state("notepad", target_state)
        
        self.assertTrue(result.success)
        self.mock_controller.focus_window.assert_called_once_with("notepad")
    
    def test_batch_window_operations_success(self):
        """Test successful batch window operations."""
        operations = [
            {'action': 'launch', 'app_name': 'notepad'},
            {'action': 'resize', 'app_name': 'notepad', 'params': {'width': 800, 'height': 600}},
            {'action': 'move', 'app_name': 'notepad', 'params': {'x': 100, 'y': 200}}
        ]
        
        # Mock successful operations
        self.mock_controller.launch_app.return_value = ExecutionResult.success_result(
            "launch_app", "notepad", "Launched successfully"
        )
        self.mock_controller.resize_window.return_value = ExecutionResult.success_result(
            "resize_window", "notepad", "Resized successfully"
        )
        self.mock_controller.move_window.return_value = ExecutionResult.success_result(
            "move_window", "notepad", "Moved successfully"
        )
        
        results = self.state_manager.batch_window_operations(operations)
        
        self.assertEqual(len(results), 3)
        self.assertTrue(all(result.success for result in results))
        
        # Verify operations were called
        self.mock_controller.launch_app.assert_called_once_with('notepad')
        self.mock_controller.resize_window.assert_called_once_with('notepad', 800, 600)
        self.mock_controller.move_window.assert_called_once_with('notepad', 100, 200)
    
    def test_batch_window_operations_unknown_action(self):
        """Test batch operations with unknown action."""
        operations = [
            {'action': 'unknown_action', 'app_name': 'notepad'}
        ]
        
        results = self.state_manager.batch_window_operations(operations)
        
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)
        self.assertIn("Unknown action", results[0].message)
    
    def test_arrange_windows_grid_too_many_windows(self):
        """Test grid arrangement with too many windows."""
        app_names = ['app1', 'app2', 'app3', 'app4', 'app5']
        
        results = self.state_manager.arrange_windows_grid(app_names, 2, 2)
        
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)
        self.assertIn("Too many windows", results[0].message)
    
    def test_arrange_windows_grid_success(self):
        """Test successful grid arrangement."""
        app_names = ['notepad', 'calculator']
        
        # Mock successful operations
        self.mock_controller.resize_window.return_value = ExecutionResult.success_result(
            "resize_window", "app", "Resized successfully"
        )
        self.mock_controller.move_window.return_value = ExecutionResult.success_result(
            "move_window", "app", "Moved successfully"
        )
        
        results = self.state_manager.arrange_windows_grid(app_names, 2, 2)
        
        # Should have 4 results (2 resize + 2 move operations)
        self.assertEqual(len(results), 4)
        self.assertTrue(all(result.success for result in results))
        
        # Verify resize calls
        self.assertEqual(self.mock_controller.resize_window.call_count, 2)
        self.assertEqual(self.mock_controller.move_window.call_count, 2)
    
    def test_validate_window_state_app_not_found(self):
        """Test window state validation when app is not found."""
        self.mock_controller.get_app_state.return_value = None
        
        expected_state = {'position': {'x': 100, 'y': 200}}
        
        result = self.state_manager.validate_window_state("notepad", expected_state)
        
        self.assertFalse(result)
    
    def test_validate_window_state_position_match(self):
        """Test window state validation with matching position."""
        current_state = {
            'position': {'x': 100, 'y': 200},
            'size': {'width': 800, 'height': 600},
            'is_visible': True
        }
        self.mock_controller.get_app_state.return_value = current_state
        
        expected_state = {'position': {'x': 105, 'y': 195}}  # Within tolerance
        
        result = self.state_manager.validate_window_state("notepad", expected_state)
        
        self.assertTrue(result)
    
    def test_validate_window_state_position_mismatch(self):
        """Test window state validation with mismatched position."""
        current_state = {
            'position': {'x': 100, 'y': 200},
            'size': {'width': 800, 'height': 600},
            'is_visible': True
        }
        self.mock_controller.get_app_state.return_value = current_state
        
        expected_state = {'position': {'x': 150, 'y': 250}}  # Outside tolerance
        
        result = self.state_manager.validate_window_state("notepad", expected_state)
        
        self.assertFalse(result)
    
    def test_validate_window_state_size_match(self):
        """Test window state validation with matching size."""
        current_state = {
            'position': {'x': 100, 'y': 200},
            'size': {'width': 800, 'height': 600},
            'is_visible': True
        }
        self.mock_controller.get_app_state.return_value = current_state
        
        expected_state = {'size': {'width': 805, 'height': 595}}  # Within tolerance
        
        result = self.state_manager.validate_window_state("notepad", expected_state)
        
        self.assertTrue(result)
    
    def test_validate_window_state_visibility_match(self):
        """Test window state validation with matching visibility."""
        current_state = {
            'position': {'x': 100, 'y': 200},
            'size': {'width': 800, 'height': 600},
            'is_visible': True
        }
        self.mock_controller.get_app_state.return_value = current_state
        
        expected_state = {'is_visible': True}
        
        result = self.state_manager.validate_window_state("notepad", expected_state)
        
        self.assertTrue(result)
    
    def test_validate_window_state_visibility_mismatch(self):
        """Test window state validation with mismatched visibility."""
        current_state = {
            'position': {'x': 100, 'y': 200},
            'size': {'width': 800, 'height': 600},
            'is_visible': True
        }
        self.mock_controller.get_app_state.return_value = current_state
        
        expected_state = {'is_visible': False}
        
        result = self.state_manager.validate_window_state("notepad", expected_state)
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()