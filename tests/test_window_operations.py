"""
Tests for window operations functionality in WindowsController.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.core.windows_controller import WindowsController
from src.models.execution import ExecutionResult
from src.models.data_models import App
from src.models.action import ActionType


class TestWindowOperations(unittest.TestCase):
    """Test cases for window operations in WindowsController."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = WindowsController()
    
    # Test window launch operations
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_launch_app_success(self, mock_execute_ps):
        """Test successful application launch."""
        mock_execute_ps.return_value = "SUCCESS: Launched Notepad"
        
        result = self.controller.launch_app("notepad")
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "launch_app")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Successfully launched", result.message)
        mock_execute_ps.assert_called_once()
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_launch_app_failure(self, mock_execute_ps):
        """Test failed application launch."""
        mock_execute_ps.return_value = "ERROR: Could not find application"
        
        result = self.controller.launch_app("nonexistent")
        
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "launch_app")
        self.assertEqual(result.target, "nonexistent")
        self.assertIn("Failed to launch", result.message)
    
    # Test window close operations
    @patch('src.core.windows_controller.psutil.process_iter')
    def test_close_app_success(self, mock_process_iter):
        """Test successful application close."""
        mock_proc = Mock()
        mock_proc.info = {'pid': 1234, 'name': 'notepad.exe'}
        mock_proc.terminate = Mock()
        mock_process_iter.return_value = [mock_proc]
        
        result = self.controller.close_app("notepad")
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "close_app")
        self.assertEqual(result.target, "notepad")
        mock_proc.terminate.assert_called_once()
    
    @patch('src.core.windows_controller.psutil.process_iter')
    def test_close_app_not_found(self, mock_process_iter):
        """Test closing app that is not running."""
        mock_process_iter.return_value = []
        
        result = self.controller.close_app("nonexistent")
        
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "close_app")
        self.assertEqual(result.target, "nonexistent")
        self.assertIn("No running processes found", result.message)
    
    # Test window resize operations
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_resize_window_success(self, mock_execute_ps):
        """Test successful window resize."""
        mock_execute_ps.return_value = "SUCCESS: Resized window to 800x600"
        
        result = self.controller.resize_window("notepad", 800, 600)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "resize_window")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Successfully resized", result.message)
        self.assertIn("800x600", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_resize_window_invalid_dimensions(self, mock_execute_ps):
        """Test window resize with invalid dimensions."""
        mock_execute_ps.return_value = "ERROR: Invalid dimensions"
        
        result = self.controller.resize_window("notepad", -100, 600)
        
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "resize_window")
        self.assertIn("Failed to resize", result.message)
    
    # Test window move operations
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_move_window_success(self, mock_execute_ps):
        """Test successful window move."""
        mock_execute_ps.return_value = "SUCCESS: Moved window to (100, 200)"
        
        result = self.controller.move_window("notepad", 100, 200)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "move_window")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Successfully moved", result.message)
        self.assertIn("(100, 200)", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_move_window_to_edge(self, mock_execute_ps):
        """Test moving window to screen edge."""
        mock_execute_ps.return_value = "SUCCESS: Moved window to (0, 0)"
        
        result = self.controller.move_window("notepad", 0, 0)
        
        self.assertTrue(result.success)
        self.assertIn("(0, 0)", result.message)
    
    # Test window state control operations
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_minimize_window_success(self, mock_execute_ps):
        """Test successful window minimize."""
        mock_execute_ps.return_value = "SUCCESS: Minimized window"
        
        result = self.controller.minimize_window("notepad")
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "minimize_window")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Successfully minimized", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_maximize_window_success(self, mock_execute_ps):
        """Test successful window maximize."""
        mock_execute_ps.return_value = "SUCCESS: Maximized window"
        
        result = self.controller.maximize_window("notepad")
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "maximize_window")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Successfully maximized", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_focus_window_success(self, mock_execute_ps):
        """Test successful window focus."""
        mock_execute_ps.return_value = "SUCCESS: Focused window"
        
        result = self.controller.focus_window("notepad")
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "focus_window")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Successfully focused", result.message)
    
    # Test window state query operations
    def test_get_app_state_found(self):
        """Test getting app state when app is found."""
        # Mock running apps
        mock_app = App(
            name="notepad.exe",
            title="Untitled - Notepad",
            process_id=1234,
            window_handle=12345,
            is_visible=True,
            x=100, y=100, width=800, height=600
        )
        
        with patch.object(self.controller, 'get_running_apps', return_value=[mock_app]):
            state = self.controller.get_app_state("notepad")
            
            self.assertIsNotNone(state)
            self.assertEqual(state['name'], "notepad.exe")
            self.assertEqual(state['title'], "Untitled - Notepad")
            self.assertEqual(state['process_id'], 1234)
            self.assertEqual(state['position']['x'], 100)
            self.assertEqual(state['position']['y'], 100)
            self.assertEqual(state['size']['width'], 800)
            self.assertEqual(state['size']['height'], 600)
            self.assertEqual(state['status'], "running")
    
    def test_get_app_state_not_found(self):
        """Test getting app state when app is not found."""
        with patch.object(self.controller, 'get_running_apps', return_value=[]):
            state = self.controller.get_app_state("nonexistent")
            
            self.assertIsNone(state)
    
    # Test complex window operations
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_window_operations_sequence(self, mock_execute_ps):
        """Test sequence of window operations."""
        # Mock successful responses for each operation
        mock_execute_ps.side_effect = [
            "SUCCESS: Launched Calculator",
            "SUCCESS: Resized window to 400x300",
            "SUCCESS: Moved window to (200, 150)",
            "SUCCESS: Focused window"
        ]
        
        # Execute sequence of operations
        launch_result = self.controller.launch_app("calculator")
        resize_result = self.controller.resize_window("calculator", 400, 300)
        move_result = self.controller.move_window("calculator", 200, 150)
        focus_result = self.controller.focus_window("calculator")
        
        # Verify all operations succeeded
        self.assertTrue(launch_result.success)
        self.assertTrue(resize_result.success)
        self.assertTrue(move_result.success)
        self.assertTrue(focus_result.success)
        
        # Verify correct number of PowerShell calls
        self.assertEqual(mock_execute_ps.call_count, 4)
    
    # Test error handling in window operations
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_window_operation_exception_handling(self, mock_execute_ps):
        """Test exception handling in window operations."""
        mock_execute_ps.side_effect = Exception("PowerShell error")
        
        result = self.controller.resize_window("notepad", 800, 600)
        
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "resize_window")
        self.assertIn("Exception occurred", result.message)
        self.assertIn("PowerShell error", result.message)
    
    # Test window operations with different applications
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_multiple_app_operations(self, mock_execute_ps):
        """Test operations on multiple applications."""
        mock_execute_ps.side_effect = [
            "SUCCESS: Launched Notepad",
            "SUCCESS: Launched Calculator",
            "SUCCESS: Resized window to 800x600",
            "SUCCESS: Resized window to 400x300"
        ]
        
        # Launch multiple apps
        notepad_result = self.controller.launch_app("notepad")
        calc_result = self.controller.launch_app("calculator")
        
        # Resize both apps
        notepad_resize = self.controller.resize_window("notepad", 800, 600)
        calc_resize = self.controller.resize_window("calculator", 400, 300)
        
        # Verify all operations
        self.assertTrue(notepad_result.success)
        self.assertTrue(calc_result.success)
        self.assertTrue(notepad_resize.success)
        self.assertTrue(calc_resize.success)
    
    # Test window operations with edge cases
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_window_operations_edge_cases(self, mock_execute_ps):
        """Test window operations with edge cases."""
        # Test with empty app name
        mock_execute_ps.return_value = "ERROR: No app name provided"
        
        result = self.controller.resize_window("", 800, 600)
        
        self.assertFalse(result.success)
        self.assertIn("Failed to resize", result.message)
    
    # Test window state consistency
    @patch('src.core.windows_controller.psutil.process_iter')
    @patch('src.core.windows_controller.WindowsController._get_window_info')
    def test_window_state_consistency(self, mock_get_window_info, mock_process_iter):
        """Test consistency of window state information."""
        # Mock process and window info
        mock_proc = Mock()
        mock_proc.info = {'pid': 1234, 'name': 'notepad.exe', 'exe': 'C:\\Windows\\notepad.exe'}
        mock_process_iter.return_value = [mock_proc]
        
        mock_get_window_info.return_value = {
            'title': 'Untitled - Notepad',
            'handle': 12345,
            'visible': True,
            'x': 100,
            'y': 100,
            'width': 800,
            'height': 600
        }
        
        # Get running apps and verify state
        apps = self.controller.get_running_apps()
        
        self.assertEqual(len(apps), 1)
        app = apps[0]
        self.assertEqual(app.name, 'notepad.exe')
        self.assertEqual(app.title, 'Untitled - Notepad')
        self.assertEqual(app.process_id, 1234)
        self.assertTrue(app.is_visible)
        self.assertEqual(app.x, 100)
        self.assertEqual(app.y, 100)
        self.assertEqual(app.width, 800)
        self.assertEqual(app.height, 600)


if __name__ == '__main__':
    unittest.main()