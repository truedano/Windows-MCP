"""
Tests for the global error handling system.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, "src")

from src.core.error_handler import (
    GlobalErrorHandler,
    SchedulerError,
    TaskExecutionError,
    WindowsControlError,
    ConfigurationError,
    StorageError,
    ValidationError,
    NetworkError,
    PermissionError,
    ErrorSeverity,
    get_global_error_handler,
    handle_errors,
    safe_execute
)


class TestSchedulerErrors:
    """Test custom exception classes."""
    
    def test_scheduler_error_creation(self):
        """Test SchedulerError creation with details."""
        error = SchedulerError(
            "Test error",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
        assert isinstance(error.timestamp, datetime)
    
    def test_scheduler_error_defaults(self):
        """Test SchedulerError with default values."""
        error = SchedulerError("Test error")
        
        assert error.message == "Test error"
        assert error.error_code == "SchedulerError"
        assert error.details == {}
    
    def test_specific_error_types(self):
        """Test specific error type creation."""
        task_error = TaskExecutionError("Task failed")
        assert isinstance(task_error, SchedulerError)
        assert task_error.error_code == "TaskExecutionError"
        
        windows_error = WindowsControlError("Windows operation failed")
        assert isinstance(windows_error, SchedulerError)
        assert windows_error.error_code == "WindowsControlError"
        
        config_error = ConfigurationError("Config invalid")
        assert isinstance(config_error, SchedulerError)
        assert config_error.error_code == "ConfigurationError"


class TestGlobalErrorHandler:
    """Test GlobalErrorHandler functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.handler = GlobalErrorHandler()
        self.mock_log_manager = Mock()
        self.handler.log_manager = self.mock_log_manager
    
    def test_error_handler_initialization(self):
        """Test error handler initialization."""
        assert self.handler.error_count == 0
        assert self.handler.critical_error_count == 0
        assert self.handler.last_error_time is None
        assert len(self.handler.error_callbacks) == 0
        assert len(self.handler.recovery_callbacks) == 0
    
    def test_register_error_callback(self):
        """Test registering error callbacks."""
        callback = Mock()
        self.handler.register_error_callback(callback)
        
        assert len(self.handler.error_callbacks) == 1
        assert callback in self.handler.error_callbacks
    
    def test_register_recovery_callback(self):
        """Test registering recovery callbacks."""
        callback = Mock(return_value=True)
        self.handler.register_recovery_callback("TestError", callback)
        
        assert "TestError" in self.handler.recovery_callbacks
        assert self.handler.recovery_callbacks["TestError"] == callback
    
    @patch('tkinter.messagebox.showerror')
    def test_handle_error_basic(self, mock_messagebox):
        """Test basic error handling."""
        error = SchedulerError("Test error")
        
        result = self.handler.handle_error(
            error, 
            severity=ErrorSeverity.MEDIUM,
            show_user_message=True,
            attempt_recovery=False
        )
        
        assert self.handler.error_count == 1
        assert self.handler.last_error_time is not None
        self.mock_log_manager.log.assert_called()
        mock_messagebox.assert_called_once()
    
    @patch('tkinter.messagebox.showerror')
    def test_handle_critical_error(self, mock_messagebox):
        """Test critical error handling."""
        error = SchedulerError("Critical error")
        
        result = self.handler.handle_error(
            error,
            severity=ErrorSeverity.CRITICAL
        )
        
        assert self.handler.critical_error_count == 1
        self.mock_log_manager.log.assert_called()
    
    def test_error_callback_execution(self):
        """Test error callback execution."""
        callback = Mock()
        self.handler.register_error_callback(callback)
        
        error = SchedulerError("Test error")
        self.handler.handle_error(error, show_user_message=False)
        
        callback.assert_called_once_with(error)
    
    def test_recovery_callback_execution(self):
        """Test recovery callback execution."""
        recovery_callback = Mock(return_value=True)
        self.handler.register_recovery_callback("SchedulerError", recovery_callback)
        
        error = SchedulerError("Test error")
        result = self.handler.handle_error(error, attempt_recovery=True, show_user_message=False)
        
        recovery_callback.assert_called_once()
        assert result is True
    
    def test_recovery_callback_failure(self):
        """Test recovery callback failure handling."""
        recovery_callback = Mock(return_value=False)
        self.handler.register_recovery_callback("SchedulerError", recovery_callback)
        
        error = SchedulerError("Test error")
        result = self.handler.handle_error(error, attempt_recovery=True, show_user_message=False)
        
        recovery_callback.assert_called_once()
        assert result is False
    
    def test_get_error_report(self):
        """Test error report generation."""
        # Generate some errors
        error1 = SchedulerError("Error 1")
        error2 = SchedulerError("Error 2")
        
        self.handler.handle_error(error1, show_user_message=False)
        self.handler.handle_error(error2, severity=ErrorSeverity.CRITICAL, show_user_message=False)
        
        report = self.handler.get_error_report()
        
        assert report["total_errors"] == 2
        assert report["critical_errors"] == 1
        assert report["last_error_time"] is not None
        assert "timestamp" in report
    
    def test_reset_error_counters(self):
        """Test resetting error counters."""
        error = SchedulerError("Test error")
        self.handler.handle_error(error, show_user_message=False)
        
        assert self.handler.error_count == 1
        
        self.handler.reset_error_counters()
        
        assert self.handler.error_count == 0
        assert self.handler.critical_error_count == 0
        assert self.handler.last_error_time is None
    
    @patch('tkinter.messagebox.askyesno', return_value=True)
    @patch('tkinter.messagebox.showinfo')
    def test_safe_mode_entry(self, mock_showinfo, mock_askyesno):
        """Test entering safe mode after multiple critical errors."""
        # Generate multiple critical errors
        for i in range(3):
            error = SchedulerError(f"Critical error {i}")
            self.handler.handle_error(error, severity=ErrorSeverity.CRITICAL, show_user_message=False)
        
        # The third critical error should trigger safe mode dialog
        mock_askyesno.assert_called_once()
        mock_showinfo.assert_called_once()


class TestErrorDecorator:
    """Test error handling decorator."""
    
    def setup_method(self):
        """Setup test environment."""
        self.handler = get_global_error_handler()
        self.handler.reset_error_counters()
    
    def test_handle_errors_decorator_success(self):
        """Test decorator with successful function execution."""
        @handle_errors()
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
        assert self.handler.error_count == 0
    
    @patch('tkinter.messagebox.showwarning')
    def test_handle_errors_decorator_failure(self, mock_messagebox):
        """Test decorator with function that raises exception."""
        @handle_errors(severity=ErrorSeverity.MEDIUM)
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        assert result is None
        assert self.handler.error_count == 1
        mock_messagebox.assert_called_once()


class TestSafeExecute:
    """Test safe_execute function."""
    
    def setup_method(self):
        """Setup test environment."""
        self.handler = get_global_error_handler()
        self.handler.reset_error_counters()
    
    def test_safe_execute_success(self):
        """Test safe_execute with successful function."""
        def test_function(x, y):
            return x + y
        
        result = safe_execute(test_function, 2, 3)
        assert result == 5
        assert self.handler.error_count == 0
    
    @patch('tkinter.messagebox.showerror')
    def test_safe_execute_failure(self, mock_messagebox):
        """Test safe_execute with failing function."""
        def test_function():
            raise ValueError("Test error")
        
        result = safe_execute(test_function, default_return="default")
        assert result == "default"
        assert self.handler.error_count == 1
        mock_messagebox.assert_called_once()
    
    @patch('tkinter.messagebox.showerror')
    def test_safe_execute_with_custom_message(self, mock_messagebox):
        """Test safe_execute with custom error message."""
        def test_function():
            raise ValueError("Original error")
        
        result = safe_execute(
            test_function, 
            error_message="Custom operation failed",
            default_return=None
        )
        
        assert result is None
        assert self.handler.error_count == 1


class TestUserFriendlyMessages:
    """Test user-friendly error message generation."""
    
    def setup_method(self):
        """Setup test environment."""
        self.handler = GlobalErrorHandler()
    
    def test_task_execution_error_message(self):
        """Test TaskExecutionError message formatting."""
        error = TaskExecutionError("Task failed to execute")
        title, message = self.handler._get_user_friendly_message(error, ErrorSeverity.MEDIUM)
        
        assert title == "任務執行錯誤"
        assert "任務執行失敗" in message
        assert "請檢查任務配置並重試" in message
    
    def test_windows_control_error_message(self):
        """Test WindowsControlError message formatting."""
        error = WindowsControlError("Window not found")
        title, message = self.handler._get_user_friendly_message(error, ErrorSeverity.MEDIUM)
        
        assert title == "Windows控制錯誤"
        assert "Windows操作失敗" in message
        assert "請確認目標應用程式正在運行" in message
    
    def test_configuration_error_message(self):
        """Test ConfigurationError message formatting."""
        error = ConfigurationError("Invalid config format")
        title, message = self.handler._get_user_friendly_message(error, ErrorSeverity.MEDIUM)
        
        assert title == "配置錯誤"
        assert "配置文件錯誤" in message
        assert "請檢查配置設定" in message
    
    def test_generic_error_message(self):
        """Test generic error message formatting."""
        error = Exception("Unknown error")
        title, message = self.handler._get_user_friendly_message(error, ErrorSeverity.HIGH)
        
        assert title == "重要錯誤"
        assert "發生未預期的錯誤" in message
        assert "請聯繫技術支援" in message


if __name__ == "__main__":
    pytest.main([__file__])