"""
Tests for action type and parameter validation.
"""

import unittest
from src.models.action import (
    ActionType, validate_action_params,
    LaunchAppParams, CloseAppParams, ResizeWindowParams,
    MoveWindowParams, WindowControlParams, ClickAbsParams,
    TypeTextParams, SendKeysParams, CustomCommandParams
)


class TestActionValidation(unittest.TestCase):
    """Test cases for action parameter validation."""
    
    def test_launch_app_validation(self):
        """Test launch app parameter validation."""
        # Valid parameters
        valid_params = {"app_name": "notepad"}
        self.assertTrue(validate_action_params(ActionType.LAUNCH_APP, valid_params))
        
        # Invalid parameters
        invalid_params = [
            {},  # Missing app_name
            {"app_name": ""},  # Empty app_name
            {"app_name": "   "},  # Whitespace only app_name
            {"app_name": 123},  # Non-string app_name
            {"wrong_key": "notepad"},  # Wrong parameter key
        ]
        
        for params in invalid_params:
            with self.subTest(params=params):
                self.assertFalse(validate_action_params(ActionType.LAUNCH_APP, params))
    
    def test_close_app_validation(self):
        """Test close app parameter validation."""
        # Valid parameters
        valid_params = {"app_name": "notepad"}
        self.assertTrue(validate_action_params(ActionType.CLOSE_APP, valid_params))
        
        # Invalid parameters
        invalid_params = [
            {},  # Missing app_name
            {"app_name": ""},  # Empty app_name
            {"app_name": None},  # None app_name
        ]
        
        for params in invalid_params:
            with self.subTest(params=params):
                self.assertFalse(validate_action_params(ActionType.CLOSE_APP, params))
    
    def test_resize_window_validation(self):
        """Test resize window parameter validation."""
        # Valid parameters
        valid_params = {"app_name": "notepad", "width": 800, "height": 600}
        self.assertTrue(validate_action_params(ActionType.RESIZE_WINDOW, valid_params))
        
        # Invalid parameters
        invalid_params = [
            {},  # Missing all parameters
            {"app_name": "notepad"},  # Missing width and height
            {"app_name": "notepad", "width": 800},  # Missing height
            {"app_name": "notepad", "width": 0, "height": 600},  # Zero width
            {"app_name": "notepad", "width": 800, "height": -1},  # Negative height
            {"app_name": "notepad", "width": "800", "height": 600},  # String width
            {"app_name": "", "width": 800, "height": 600},  # Empty app_name
        ]
        
        for params in invalid_params:
            with self.subTest(params=params):
                self.assertFalse(validate_action_params(ActionType.RESIZE_WINDOW, params))
    
    def test_move_window_validation(self):
        """Test move window parameter validation."""
        # Valid parameters
        valid_params = {"app_name": "notepad", "x": 100, "y": 200}
        self.assertTrue(validate_action_params(ActionType.MOVE_WINDOW, valid_params))
        
        # Edge case: zero coordinates should be valid
        edge_params = {"app_name": "notepad", "x": 0, "y": 0}
        self.assertTrue(validate_action_params(ActionType.MOVE_WINDOW, edge_params))
        
        # Invalid parameters
        invalid_params = [
            {},  # Missing all parameters
            {"app_name": "notepad"},  # Missing coordinates
            {"app_name": "notepad", "x": -1, "y": 200},  # Negative x
            {"app_name": "notepad", "x": 100, "y": -1},  # Negative y
            {"app_name": "notepad", "x": 100.5, "y": 200},  # Float x
            {"app_name": "", "x": 100, "y": 200},  # Empty app_name
        ]
        
        for params in invalid_params:
            with self.subTest(params=params):
                self.assertFalse(validate_action_params(ActionType.MOVE_WINDOW, params))
    
    def test_window_control_validation(self):
        """Test window control operations validation."""
        window_control_actions = [
            ActionType.MINIMIZE_WINDOW,
            ActionType.MAXIMIZE_WINDOW,
            ActionType.RESTORE_WINDOW,
            ActionType.FOCUS_WINDOW
        ]
        
        # Valid parameters
        valid_params = {"app_name": "notepad"}
        
        for action_type in window_control_actions:
            with self.subTest(action_type=action_type):
                self.assertTrue(validate_action_params(action_type, valid_params))
        
        # Invalid parameters
        invalid_params = [
            {},  # Missing app_name
            {"app_name": ""},  # Empty app_name
            {"wrong_key": "notepad"},  # Wrong parameter key
        ]
        
        for action_type in window_control_actions:
            for params in invalid_params:
                with self.subTest(action_type=action_type, params=params):
                    self.assertFalse(validate_action_params(action_type, params))
    
    def test_click_abs_validation(self):
        """Test click element parameter validation."""
        # Valid parameters
        valid_params = {"app_name": "notepad", "x": 100, "y": 200}
        self.assertTrue(validate_action_params(ActionType.CLICK_ABS, {"x": 100, "y": 200}))
        
        # Invalid parameters
        invalid_params = [
            {},  # Missing all parameters
            {"app_name": "notepad"},  # Missing coordinates
            {"app_name": "notepad", "x": -1, "y": 200},  # Negative x
            {"app_name": "notepad", "x": 100, "y": -1},  # Negative y
            {"app_name": "", "x": 100, "y": 200},  # Empty app_name
        ]
        
        for params in invalid_params:
            with self.subTest(params=params):
                self.assertFalse(validate_action_params(ActionType.CLICK_ABS, {"x": params.get("x", -1), "y": params.get("y", -1)}))
    
    def test_type_text_validation(self):
        """Test type text parameter validation."""
        # Valid parameters
        valid_params = {"app_name": "notepad", "text": "Hello World", "x": 100, "y": 200}
        self.assertTrue(validate_action_params(ActionType.TYPE_TEXT, valid_params))
        
        # Edge case: empty text should be valid (might be used to clear fields)
        edge_params = {"app_name": "notepad", "text": "", "x": 100, "y": 200}
        self.assertTrue(validate_action_params(ActionType.TYPE_TEXT, edge_params))
        
        # Invalid parameters
        invalid_params = [
            {},  # Missing all parameters
            {"app_name": "notepad", "text": "Hello"},  # Missing coordinates
            {"app_name": "notepad", "text": "Hello", "x": -1, "y": 200},  # Negative x
            {"app_name": "notepad", "text": "Hello", "x": 100, "y": -1},  # Negative y
            {"app_name": "", "text": "Hello", "x": 100, "y": 200},  # Empty app_name
            {"app_name": "notepad", "text": 123, "x": 100, "y": 200},  # Non-string text
        ]
        
        for params in invalid_params:
            with self.subTest(params=params):
                self.assertFalse(validate_action_params(ActionType.TYPE_TEXT, params))
    
    def test_send_keys_validation(self):
        """Test send keys parameter validation."""
        # Valid parameters
        valid_params = {"keys": ["ctrl", "c"]}
        self.assertTrue(validate_action_params(ActionType.SEND_KEYS, valid_params))
        
        # More valid key combinations
        valid_key_combinations = [
            {"keys": ["alt", "f4"]},
            {"keys": ["ctrl", "shift", "n"]},
            {"keys": ["win", "r"]},
            {"keys": ["f1"]},
        ]
        
        for params in valid_key_combinations:
            with self.subTest(params=params):
                self.assertTrue(validate_action_params(ActionType.SEND_KEYS, params))
        
        # Invalid parameters
        invalid_params = [
            {},  # Missing keys
            {"keys": []},  # Empty keys list
            {"keys": [""]},  # Empty string in keys
            {"keys": ["   "]},  # Whitespace only in keys
            {"keys": [123]},  # Non-string in keys
            {"keys": "ctrl+c"},  # String instead of list
            {"wrong_key": ["ctrl", "c"]},  # Wrong parameter key
        ]
        
        for params in invalid_params:
            with self.subTest(params=params):
                self.assertFalse(validate_action_params(ActionType.SEND_KEYS, params))
    
    def test_custom_command_validation(self):
        """Test custom command parameter validation."""
        # Valid parameters
        valid_params = {"command": "Get-Process"}
        self.assertTrue(validate_action_params(ActionType.CUSTOM_COMMAND, valid_params))
        
        # More valid commands
        valid_commands = [
            {"command": "notepad.exe"},
            {"command": "powershell -Command 'Get-Date'"},
            {"command": "dir C:\\"},
        ]
        
        for params in valid_commands:
            with self.subTest(params=params):
                self.assertTrue(validate_action_params(ActionType.CUSTOM_COMMAND, params))
        
        # Invalid parameters
        invalid_params = [
            {},  # Missing command
            {"command": ""},  # Empty command
            {"command": "   "},  # Whitespace only command
            {"command": 123},  # Non-string command
            {"wrong_key": "Get-Process"},  # Wrong parameter key
        ]
        
        for params in invalid_params:
            with self.subTest(params=params):
                self.assertFalse(validate_action_params(ActionType.CUSTOM_COMMAND, params))
    
    def test_invalid_action_type(self):
        """Test validation with invalid action type."""
        # This should handle gracefully and return False
        params = {"app_name": "notepad"}
        
        # Test with None
        self.assertFalse(validate_action_params(None, params))
        
        # Test with invalid string (this would raise an exception in real usage)
        # but our validation should handle it gracefully
        try:
            result = validate_action_params("invalid_action", params)
            self.assertFalse(result)
        except (AttributeError, TypeError):
            # This is expected behavior for invalid action types
            pass
    
    def test_parameter_dataclasses(self):
        """Test parameter dataclasses creation."""
        # Test LaunchAppParams
        launch_params = LaunchAppParams(app_name="notepad")
        self.assertEqual(launch_params.app_name, "notepad")
        
        # Test ResizeWindowParams
        resize_params = ResizeWindowParams(app_name="notepad", width=800, height=600)
        self.assertEqual(resize_params.width, 800)
        self.assertEqual(resize_params.height, 600)
        
        # Test TypeTextParams
        type_params = TypeTextParams(app_name="notepad", text="Hello", x=100, y=200)
        self.assertEqual(type_params.text, "Hello")
        self.assertEqual(type_params.x, 100)
        
        # Test SendKeysParams
        keys_params = SendKeysParams(keys=["ctrl", "c"])
        self.assertEqual(keys_params.keys, ["ctrl", "c"])
        
        # Test CustomCommandParams
        command_params = CustomCommandParams(command="Get-Process")
        self.assertEqual(command_params.command, "Get-Process")


if __name__ == '__main__':
    unittest.main()