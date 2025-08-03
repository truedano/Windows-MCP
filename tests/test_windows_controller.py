"""
Tests for Windows Controller functionality.
"""

import unittest
import subprocess
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.core.windows_controller import WindowsController
from src.models.execution import ExecutionResult
from src.models.data_models import App
from src.models.action import ActionType


class TestWindowsController(unittest.TestCase):
    """Test cases for WindowsController class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = WindowsController()
    
    def test_initialization(self):
        """Test WindowsController initialization."""
        self.assertIsNotNone(self.controller)
        self.assertIsNone(self.controller._last_scan_time)
        self.assertEqual(self.controller._cached_apps, [])
        self.assertEqual(self.controller._cache_duration, 5)
    
    @patch('src.core.windows_controller.psutil.process_iter')
    def test_get_running_apps_empty(self, mock_process_iter):
        """Test getting running apps when no apps are found."""
        mock_process_iter.return_value = []
        
        apps = self.controller.get_running_apps()
        
        self.assertEqual(apps, [])
    
    @patch('src.core.windows_controller.psutil.process_iter')
    def test_get_running_apps_with_cache(self, mock_process_iter):
        """Test getting running apps with cache."""
        # Set up cache
        cached_app = App(
            name="notepad.exe",
            title="Untitled - Notepad",
            process_id=1234,
            window_handle=12345,
            is_visible=True,
            x=100, y=100, width=800, height=600
        )
        self.controller._cached_apps = [cached_app]
        self.controller._last_scan_time = datetime.now().timestamp()
        
        apps = self.controller.get_running_apps()
        
        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0].name, "notepad.exe")
        # Should not call process_iter due to cache
        mock_process_iter.assert_not_called()
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_launch_app_success(self, mock_execute_ps):
        """Test successful app launch."""
        mock_execute_ps.return_value = "SUCCESS: Launched Notepad"
        
        result = self.controller.launch_app("notepad")
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "launch_app")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Successfully launched", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_launch_app_failure(self, mock_execute_ps):
        """Test failed app launch."""
        mock_execute_ps.return_value = "ERROR: Could not find or launch nonexistent"
        
        result = self.controller.launch_app("nonexistent")
        
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "launch_app")
        self.assertEqual(result.target, "nonexistent")
        self.assertIn("Failed to launch", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_launch_app_exception(self, mock_execute_ps):
        """Test app launch with exception."""
        mock_execute_ps.side_effect = Exception("PowerShell error")
        
        result = self.controller.launch_app("notepad")
        
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "launch_app")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Exception occurred", result.message)
    
    @patch('src.core.windows_controller.psutil.process_iter')
    def test_close_app_success(self, mock_process_iter):
        """Test successful app close."""
        # Mock process
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
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_resize_window_success(self, mock_execute_ps):
        """Test successful window resize."""
        mock_execute_ps.return_value = "SUCCESS: Resized window to 800x600"
        
        result = self.controller.resize_window("notepad", 800, 600)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "resize_window")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Successfully resized", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_resize_window_failure(self, mock_execute_ps):
        """Test failed window resize."""
        mock_execute_ps.return_value = "ERROR: Process notepad not found"
        
        result = self.controller.resize_window("notepad", 800, 600)
        
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "resize_window")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Failed to resize", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_move_window_success(self, mock_execute_ps):
        """Test successful window move."""
        mock_execute_ps.return_value = "SUCCESS: Moved window to (100, 200)"
        
        result = self.controller.move_window("notepad", 100, 200)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "move_window")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Successfully moved", result.message)
    
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
    
    def test_execute_action_launch_app(self):
        """Test execute_action with LAUNCH_APP."""
        with patch.object(self.controller, 'launch_app') as mock_launch:
            mock_launch.return_value = ExecutionResult.success_result("launch_app", "notepad")
            
            result = self.controller.execute_action(
                ActionType.LAUNCH_APP,
                {'app_name': 'notepad'}
            )
            
            mock_launch.assert_called_once_with('notepad')
            self.assertTrue(result.success)
    
    def test_execute_action_close_app(self):
        """Test execute_action with CLOSE_APP."""
        with patch.object(self.controller, 'close_app') as mock_close:
            mock_close.return_value = ExecutionResult.success_result("close_app", "notepad")
            
            result = self.controller.execute_action(
                ActionType.CLOSE_APP,
                {'app_name': 'notepad'}
            )
            
            mock_close.assert_called_once_with('notepad')
            self.assertTrue(result.success)
    
    def test_execute_action_resize_window(self):
        """Test execute_action with RESIZE_WINDOW."""
        with patch.object(self.controller, 'resize_window') as mock_resize:
            mock_resize.return_value = ExecutionResult.success_result("resize_window", "notepad")
            
            result = self.controller.execute_action(
                ActionType.RESIZE_WINDOW,
                {'app_name': 'notepad', 'width': 800, 'height': 600}
            )
            
            mock_resize.assert_called_once_with('notepad', 800, 600)
            self.assertTrue(result.success)
    
    def test_execute_action_move_window(self):
        """Test execute_action with MOVE_WINDOW."""
        with patch.object(self.controller, 'move_window') as mock_move:
            mock_move.return_value = ExecutionResult.success_result("move_window", "notepad")
            
            result = self.controller.execute_action(
                ActionType.MOVE_WINDOW,
                {'app_name': 'notepad', 'x': 100, 'y': 200}
            )
            
            mock_move.assert_called_once_with('notepad', 100, 200)
            self.assertTrue(result.success)
    
    def test_execute_action_unsupported(self):
        """Test execute_action with unsupported action type."""
        # Use a mock action type that doesn't exist
        with patch('src.core.windows_controller.ActionType') as mock_action_type:
            mock_action_type.UNSUPPORTED = "unsupported"
            mock_action_type.UNSUPPORTED.value = "unsupported"
            
            result = self.controller.execute_action(
                mock_action_type.UNSUPPORTED,
                {}
            )
            
            self.assertFalse(result.success)
            self.assertIn("Unsupported action type", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_execute_powershell_command_success(self, mock_execute_ps):
        """Test successful PowerShell command execution."""
        mock_execute_ps.return_value = "Command output"
        
        result = self.controller.execute_powershell_command("Get-Process")
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "custom_command")
        self.assertEqual(result.target, "powershell")
        mock_execute_ps.assert_called_once_with("Get-Process")
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_execute_powershell_command_failure(self, mock_execute_ps):
        """Test failed PowerShell command execution."""
        mock_execute_ps.return_value = None
        
        result = self.controller.execute_powershell_command("Invalid-Command")
        
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "custom_command")
        self.assertEqual(result.target, "powershell")
    
    @patch('src.core.windows_controller.subprocess.run')
    def test_execute_powershell_success(self, mock_run):
        """Test _execute_powershell method success."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Command output\n"
        mock_run.return_value = mock_result
        
        result = self.controller._execute_powershell("Get-Process")
        
        self.assertEqual(result, "Command output")
        mock_run.assert_called_once()
    
    @patch('src.core.windows_controller.subprocess.run')
    def test_execute_powershell_error(self, mock_run):
        """Test _execute_powershell method with error."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Command error\n"
        mock_run.return_value = mock_result
        
        result = self.controller._execute_powershell("Invalid-Command")
        
        self.assertEqual(result, "ERROR: Command error")
    
    @patch('src.core.windows_controller.subprocess.run')
    def test_execute_powershell_timeout(self, mock_run):
        """Test _execute_powershell method with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("powershell", 30)
        
        result = self.controller._execute_powershell("Long-Running-Command")
        
        self.assertEqual(result, "ERROR: PowerShell command timed out")
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_get_window_info_success(self, mock_execute_ps):
        """Test _get_window_info method success."""
        mock_execute_ps.return_value = '{"title": "Notepad", "handle": 12345, "visible": true, "x": 100, "y": 200, "width": 800, "height": 600}'
        
        result = self.controller._get_window_info(1234)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], "Notepad")
        self.assertEqual(result['handle'], 12345)
        self.assertTrue(result['visible'])
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_get_window_info_failure(self, mock_execute_ps):
        """Test _get_window_info method failure."""
        mock_execute_ps.return_value = "No window found"
        
        result = self.controller._get_window_info(1234)
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()