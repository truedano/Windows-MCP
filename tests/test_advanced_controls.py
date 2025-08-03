"""
Tests for advanced control functionality in WindowsController.
"""

import unittest
import subprocess
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.core.windows_controller import WindowsController
from src.models.execution import ExecutionResult
from src.models.action import ActionType


class TestAdvancedControls(unittest.TestCase):
    """Test cases for advanced control features in WindowsController."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = WindowsController()
    
    # Test element clicking functionality
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_click_element_success(self, mock_execute_ps):
        """Test successful element clicking."""
        mock_execute_ps.return_value = "SUCCESS: Clicked at (100, 200) in calculator"
        
        result = self.controller.click_element("calculator", 100, 200)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "click_element")
        self.assertEqual(result.target, "calculator")
        self.assertIn("Successfully clicked at (100, 200)", result.message)
        mock_execute_ps.assert_called_once()
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_click_element_app_not_found(self, mock_execute_ps):
        """Test clicking when application is not found."""
        mock_execute_ps.return_value = "ERROR: Process nonexistent not found or has no window"
        
        result = self.controller.click_element("nonexistent", 100, 200)
        
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "click_element")
        self.assertEqual(result.target, "nonexistent")
        self.assertIn("Failed to click", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_click_element_coordinates_validation(self, mock_execute_ps):
        """Test clicking with various coordinate values."""
        mock_execute_ps.return_value = "SUCCESS: Clicked at (0, 0) in notepad"
        
        # Test edge coordinates
        result = self.controller.click_element("notepad", 0, 0)
        self.assertTrue(result.success)
        
        # Test large coordinates
        mock_execute_ps.return_value = "SUCCESS: Clicked at (1920, 1080) in notepad"
        result = self.controller.click_element("notepad", 1920, 1080)
        self.assertTrue(result.success)
    
    # Test text typing functionality
    @patch('src.core.windows_controller.WindowsController.click_element')
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_type_text_success(self, mock_execute_ps, mock_click):
        """Test successful text typing."""
        # Mock successful click
        mock_click.return_value = ExecutionResult.success_result(
            "click_element", "notepad", "Clicked successfully"
        )
        
        # Mock successful text typing
        mock_execute_ps.return_value = "SUCCESS: Typed text at (50, 100) in notepad"
        
        result = self.controller.type_text("notepad", "Hello World", 50, 100)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "type_text")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Successfully typed text", result.message)
        
        # Verify click was called first
        mock_click.assert_called_once_with("notepad", 50, 100)
    
    @patch('src.core.windows_controller.WindowsController.click_element')
    def test_type_text_click_failure(self, mock_click):
        """Test text typing when initial click fails."""
        # Mock failed click
        mock_click.return_value = ExecutionResult.failure_result(
            "click_element", "notepad", "Click failed"
        )
        
        result = self.controller.type_text("notepad", "Hello World", 50, 100)
        
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "type_text")
        self.assertEqual(result.target, "notepad")
        self.assertIn("Failed to click before typing", result.message)
    
    @patch('src.core.windows_controller.WindowsController.click_element')
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_type_text_special_characters(self, mock_execute_ps, mock_click):
        """Test typing text with special characters."""
        mock_click.return_value = ExecutionResult.success_result(
            "click_element", "notepad", "Clicked successfully"
        )
        mock_execute_ps.return_value = "SUCCESS: Typed text at (50, 100) in notepad"
        
        # Test with quotes and special characters
        special_text = "Hello 'World' with \"quotes\" and symbols: @#$%"
        result = self.controller.type_text("notepad", special_text, 50, 100)
        
        self.assertTrue(result.success)
        self.assertIn("Successfully typed text", result.message)
    
    # Test keyboard shortcuts functionality
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_send_keys_simple_shortcut(self, mock_execute_ps):
        """Test sending simple keyboard shortcuts."""
        mock_execute_ps.return_value = "SUCCESS: Sent keys ctrl + c"
        
        result = self.controller.send_keys(["ctrl", "c"])
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "send_keys")
        self.assertEqual(result.target, "system")
        self.assertIn("Successfully sent keys", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_send_keys_complex_shortcut(self, mock_execute_ps):
        """Test sending complex keyboard shortcuts."""
        mock_execute_ps.return_value = "SUCCESS: Sent keys ctrl + shift + s"
        
        result = self.controller.send_keys(["ctrl", "shift", "s"])
        
        self.assertTrue(result.success)
        self.assertIn("ctrl + shift + s", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_send_keys_function_keys(self, mock_execute_ps):
        """Test sending function keys."""
        mock_execute_ps.return_value = "SUCCESS: Sent keys f5"
        
        result = self.controller.send_keys(["f5"])
        
        self.assertTrue(result.success)
        self.assertIn("f5", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_send_keys_navigation_keys(self, mock_execute_ps):
        """Test sending navigation keys."""
        mock_execute_ps.return_value = "SUCCESS: Sent keys alt + tab"
        
        result = self.controller.send_keys(["alt", "tab"])
        
        self.assertTrue(result.success)
        self.assertIn("alt + tab", result.message)
    
    def test_convert_to_sendkeys_format_basic(self):
        """Test SendKeys format conversion for basic keys."""
        # Test Ctrl+C
        result = self.controller._convert_to_sendkeys_format(["ctrl", "c"])
        self.assertEqual(result, "^c")
        
        # Test Alt+Tab
        result = self.controller._convert_to_sendkeys_format(["alt", "tab"])
        self.assertEqual(result, "%{TAB}")
        
        # Test Shift+F5
        result = self.controller._convert_to_sendkeys_format(["shift", "f5"])
        self.assertEqual(result, "+{F5}")
    
    def test_convert_to_sendkeys_format_complex(self):
        """Test SendKeys format conversion for complex combinations."""
        # Test Ctrl+Shift+S
        result = self.controller._convert_to_sendkeys_format(["ctrl", "shift", "s"])
        self.assertEqual(result, "^+s")
        
        # Test single character
        result = self.controller._convert_to_sendkeys_format(["a"])
        self.assertEqual(result, "a")
        
        # Test special keys
        result = self.controller._convert_to_sendkeys_format(["enter"])
        self.assertEqual(result, "{ENTER}")
        
        result = self.controller._convert_to_sendkeys_format(["escape"])
        self.assertEqual(result, "{ESC}")
    
    # Test PowerShell command execution
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_execute_powershell_command_success(self, mock_execute_ps):
        """Test successful PowerShell command execution."""
        mock_execute_ps.return_value = "Process list retrieved successfully"
        
        result = self.controller.execute_powershell_command("Get-Process")
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "custom_command")
        self.assertEqual(result.target, "powershell")
        self.assertIn("PowerShell command executed successfully", result.message)
        mock_execute_ps.assert_called_once_with("Get-Process")
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_execute_powershell_command_failure(self, mock_execute_ps):
        """Test failed PowerShell command execution."""
        mock_execute_ps.return_value = None
        
        result = self.controller.execute_powershell_command("Invalid-Command")
        
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "custom_command")
        self.assertEqual(result.target, "powershell")
        self.assertIn("PowerShell command execution failed", result.message)
    
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_execute_powershell_command_exception(self, mock_execute_ps):
        """Test PowerShell command execution with exception."""
        mock_execute_ps.side_effect = Exception("PowerShell error")
        
        result = self.controller.execute_powershell_command("Get-Process")
        
        self.assertFalse(result.success)
        self.assertIn("Exception occurred", result.message)
        self.assertIn("PowerShell error", result.message)
    
    # Test PowerShell execution internals
    @patch('src.core.windows_controller.subprocess.run')
    def test_execute_powershell_internal_success(self, mock_run):
        """Test internal PowerShell execution success."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Command executed successfully\n"
        mock_run.return_value = mock_result
        
        result = self.controller._execute_powershell("Get-Process")
        
        self.assertEqual(result, "Command executed successfully")
        mock_run.assert_called_once()
        
        # Verify PowerShell command structure
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], "powershell")
        self.assertEqual(call_args[1], "-Command")
        self.assertEqual(call_args[2], "Get-Process")
    
    @patch('src.core.windows_controller.subprocess.run')
    def test_execute_powershell_internal_error(self, mock_run):
        """Test internal PowerShell execution with error."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Command not found\n"
        mock_run.return_value = mock_result
        
        result = self.controller._execute_powershell("Invalid-Command")
        
        self.assertEqual(result, "ERROR: Command not found")
    
    @patch('src.core.windows_controller.subprocess.run')
    def test_execute_powershell_internal_timeout(self, mock_run):
        """Test internal PowerShell execution timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("powershell", 30)
        
        result = self.controller._execute_powershell("Start-Sleep -Seconds 60")
        
        self.assertEqual(result, "ERROR: PowerShell command timed out")
    
    @patch('src.core.windows_controller.subprocess.run')
    def test_execute_powershell_internal_exception(self, mock_run):
        """Test internal PowerShell execution with exception."""
        mock_run.side_effect = Exception("System error")
        
        result = self.controller._execute_powershell("Get-Process")
        
        self.assertEqual(result, "ERROR: System error")
    
    # Test advanced control integration with action execution
    def test_execute_action_click_element(self):
        """Test execute_action with CLICK_ELEMENT."""
        with patch.object(self.controller, 'click_element') as mock_click:
            mock_click.return_value = ExecutionResult.success_result(
                "click_element", "calculator", "Clicked successfully"
            )
            
            result = self.controller.execute_action(
                ActionType.CLICK_ELEMENT,
                {'app_name': 'calculator', 'x': 100, 'y': 200}
            )
            
            mock_click.assert_called_once_with('calculator', 100, 200)
            self.assertTrue(result.success)
    
    def test_execute_action_type_text(self):
        """Test execute_action with TYPE_TEXT."""
        with patch.object(self.controller, 'type_text') as mock_type:
            mock_type.return_value = ExecutionResult.success_result(
                "type_text", "notepad", "Text typed successfully"
            )
            
            result = self.controller.execute_action(
                ActionType.TYPE_TEXT,
                {'app_name': 'notepad', 'text': 'Hello', 'x': 50, 'y': 100}
            )
            
            mock_type.assert_called_once_with('notepad', 'Hello', 50, 100)
            self.assertTrue(result.success)
    
    def test_execute_action_send_keys(self):
        """Test execute_action with SEND_KEYS."""
        with patch.object(self.controller, 'send_keys') as mock_keys:
            mock_keys.return_value = ExecutionResult.success_result(
                "send_keys", "system", "Keys sent successfully"
            )
            
            result = self.controller.execute_action(
                ActionType.SEND_KEYS,
                {'keys': ['ctrl', 'c']}
            )
            
            mock_keys.assert_called_once_with(['ctrl', 'c'])
            self.assertTrue(result.success)
    
    def test_execute_action_custom_command(self):
        """Test execute_action with CUSTOM_COMMAND."""
        with patch.object(self.controller, 'execute_powershell_command') as mock_ps:
            mock_ps.return_value = ExecutionResult.success_result(
                "custom_command", "powershell", "Command executed successfully"
            )
            
            result = self.controller.execute_action(
                ActionType.CUSTOM_COMMAND,
                {'command': 'Get-Process'}
            )
            
            mock_ps.assert_called_once_with('Get-Process')
            self.assertTrue(result.success)
    
    # Test complex advanced control scenarios
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_advanced_control_workflow(self, mock_execute_ps):
        """Test complex workflow using advanced controls."""
        # Mock successful responses for each operation
        mock_execute_ps.side_effect = [
            "SUCCESS: Clicked at (100, 200) in notepad",
            "SUCCESS: Typed text at (100, 200) in notepad",
            "SUCCESS: Sent keys ctrl + s",
            "File saved successfully"
        ]
        
        # Execute workflow: click, type, save, verify
        click_result = self.controller.click_element("notepad", 100, 200)
        type_result = self.controller.type_text("notepad", "Hello World", 100, 200)
        save_result = self.controller.send_keys(["ctrl", "s"])
        verify_result = self.controller.execute_powershell_command("Test-Path 'file.txt'")
        
        # Verify all operations succeeded
        self.assertTrue(click_result.success)
        self.assertTrue(type_result.success)
        self.assertTrue(save_result.success)
        self.assertTrue(verify_result.success)
        
        # Verify correct number of PowerShell calls
        self.assertEqual(mock_execute_ps.call_count, 4)
    
    # Test error handling in advanced controls
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_advanced_control_error_handling(self, mock_execute_ps):
        """Test error handling in advanced control operations."""
        mock_execute_ps.side_effect = Exception("System error")
        
        # Test each advanced control method handles exceptions
        click_result = self.controller.click_element("notepad", 100, 200)
        type_result = self.controller.type_text("notepad", "Hello", 100, 200)
        keys_result = self.controller.send_keys(["ctrl", "c"])
        ps_result = self.controller.execute_powershell_command("Get-Process")
        
        # All should fail gracefully
        self.assertFalse(click_result.success)
        self.assertFalse(type_result.success)
        self.assertFalse(keys_result.success)
        self.assertFalse(ps_result.success)
        
        # All should contain exception information
        self.assertIn("Exception occurred", click_result.message)
        self.assertIn("Exception occurred", type_result.message)
        self.assertIn("Exception occurred", keys_result.message)
        self.assertIn("Exception occurred", ps_result.message)
    
    # Test advanced controls with edge cases
    @patch('src.core.windows_controller.WindowsController._execute_powershell')
    def test_advanced_controls_edge_cases(self, mock_execute_ps):
        """Test advanced controls with edge cases."""
        # Test empty text typing
        mock_execute_ps.return_value = "SUCCESS: Typed text"
        with patch.object(self.controller, 'click_element') as mock_click:
            mock_click.return_value = ExecutionResult.success_result(
                "click_element", "notepad", "Clicked"
            )
            result = self.controller.type_text("notepad", "", 100, 200)
            self.assertTrue(result.success)
        
        # Test empty key sequence
        result = self.controller.send_keys([])
        # This should be handled by validation in action.py
        
        # Test empty PowerShell command
        result = self.controller.execute_powershell_command("")
        self.assertFalse(result.success)


if __name__ == '__main__':
    unittest.main()