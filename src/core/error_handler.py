"""
Global error handling system for Windows Scheduler GUI.

This module provides a unified error handling mechanism with user-friendly error messages,
error reporting, diagnostic functionality, and system recovery features.
"""

import sys
import traceback
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from functools import wraps
import tkinter as tk
from tkinter import messagebox

from src.models.enums import LogLevel
from src.core.log_manager import get_log_manager


class SchedulerError(Exception):
    """Base exception class for all scheduler-related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = datetime.now()


class TaskExecutionError(SchedulerError):
    """Exception raised when task execution fails."""
    pass


class WindowsControlError(SchedulerError):
    """Exception raised when Windows control operations fail."""
    pass


class ConfigurationError(SchedulerError):
    """Exception raised when configuration is invalid or missing."""
    pass


class StorageError(SchedulerError):
    """Exception raised when storage operations fail."""
    pass


class ValidationError(SchedulerError):
    """Exception raised when data validation fails."""
    pass


class NetworkError(SchedulerError):
    """Exception raised when network operations fail."""
    pass


class PermissionError(SchedulerError):
    """Exception raised when permission checks fail."""
    pass


class ErrorSeverity:
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GlobalErrorHandler:
    """Global error handler for the application."""
    
    def __init__(self):
        self.log_manager = get_log_manager()
        self.error_callbacks: List[Callable[[Exception], None]] = []
        self.recovery_callbacks: Dict[str, Callable[[], bool]] = {}
        self.error_count = 0
        self.critical_error_count = 0
        self.last_error_time: Optional[datetime] = None
        
        # Setup global exception handler
        self._setup_global_handler()
    
    def _setup_global_handler(self):
        """Setup global exception handler for unhandled exceptions."""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # Allow keyboard interrupt to work normally
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # Handle all other exceptions
            error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            self.handle_critical_error(
                exc_value if isinstance(exc_value, SchedulerError) else 
                SchedulerError(f"Unhandled exception: {str(exc_value)}", 
                             details={"traceback": error_msg})
            )
        
        sys.excepthook = handle_exception
    
    def register_error_callback(self, callback: Callable[[Exception], None]):
        """Register a callback to be called when errors occur."""
        self.error_callbacks.append(callback)
    
    def register_recovery_callback(self, error_type: str, callback: Callable[[], bool]):
        """Register a recovery callback for specific error types."""
        self.recovery_callbacks[error_type] = callback
    
    def handle_error(self, error: Exception, severity: str = ErrorSeverity.MEDIUM,
                    show_user_message: bool = True, attempt_recovery: bool = True) -> bool:
        """
        Handle an error with appropriate logging, user notification, and recovery.
        
        Args:
            error: The exception to handle
            severity: Error severity level
            show_user_message: Whether to show user-friendly message
            attempt_recovery: Whether to attempt automatic recovery
            
        Returns:
            True if error was handled successfully, False otherwise
        """
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        if severity == ErrorSeverity.CRITICAL:
            self.critical_error_count += 1
        
        # Log the error
        self._log_error(error, severity)
        
        # Notify error callbacks
        for callback in self.error_callbacks:
            try:
                callback(error)
            except Exception as cb_error:
                self.log_manager.log(
                    LogLevel.ERROR,
                    f"Error in error callback: {str(cb_error)}"
                )
        
        # Show user message if requested
        if show_user_message:
            self._show_user_error_message(error, severity)
        
        # Attempt recovery if requested
        recovery_success = False
        if attempt_recovery:
            recovery_success = self._attempt_recovery(error)
        
        # Handle critical errors
        if severity == ErrorSeverity.CRITICAL:
            return self._handle_critical_error(error)
        
        return recovery_success
    
    def handle_critical_error(self, error: Exception) -> bool:
        """Handle critical errors that may require application shutdown."""
        return self.handle_error(error, ErrorSeverity.CRITICAL, True, True)
    
    def _log_error(self, error: Exception, severity: str):
        """Log error details."""
        log_level = LogLevel.ERROR
        if severity == ErrorSeverity.CRITICAL:
            log_level = LogLevel.CRITICAL
        elif severity == ErrorSeverity.LOW:
            log_level = LogLevel.WARNING
        
        error_details = {
            "error_type": type(error).__name__,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "error_count": self.error_count
        }
        
        if isinstance(error, SchedulerError):
            error_details.update({
                "error_code": error.error_code,
                "details": error.details
            })
        
        self.log_manager.log(
            log_level,
            f"Error handled: {str(error)}",
            details=error_details
        )
    
    def _show_user_error_message(self, error: Exception, severity: str):
        """Show user-friendly error message."""
        try:
            title, message = self._get_user_friendly_message(error, severity)
            
            if severity == ErrorSeverity.CRITICAL:
                messagebox.showerror(title, message)
            elif severity == ErrorSeverity.HIGH:
                messagebox.showerror(title, message)
            elif severity == ErrorSeverity.MEDIUM:
                messagebox.showwarning(title, message)
            else:
                messagebox.showinfo(title, message)
        except Exception as msg_error:
            # Fallback if message display fails
            self.log_manager.log(
                LogLevel.ERROR,
                f"Failed to show error message: {str(msg_error)}"
            )
    
    def _get_user_friendly_message(self, error: Exception, severity: str) -> tuple[str, str]:
        """Get user-friendly error title and message."""
        if isinstance(error, TaskExecutionError):
            return "任務執行錯誤", f"任務執行失敗：\n{error.message}\n\n請檢查任務配置並重試。"
        
        elif isinstance(error, WindowsControlError):
            return "Windows控制錯誤", f"Windows操作失敗：\n{error.message}\n\n請確認目標應用程式正在運行且有適當權限。"
        
        elif isinstance(error, ConfigurationError):
            return "配置錯誤", f"配置文件錯誤：\n{error.message}\n\n請檢查配置設定或重置為預設值。"
        
        elif isinstance(error, StorageError):
            return "存儲錯誤", f"資料存取失敗：\n{error.message}\n\n請檢查檔案權限和磁碟空間。"
        
        elif isinstance(error, ValidationError):
            return "驗證錯誤", f"資料驗證失敗：\n{error.message}\n\n請檢查輸入資料的格式和內容。"
        
        elif isinstance(error, NetworkError):
            return "網路錯誤", f"網路連接失敗：\n{error.message}\n\n請檢查網路連接。"
        
        elif isinstance(error, PermissionError):
            return "權限錯誤", f"權限不足：\n{error.message}\n\n請以管理員身份運行或檢查權限設定。"
        
        else:
            severity_text = {
                ErrorSeverity.CRITICAL: "嚴重錯誤",
                ErrorSeverity.HIGH: "重要錯誤", 
                ErrorSeverity.MEDIUM: "錯誤",
                ErrorSeverity.LOW: "警告"
            }.get(severity, "錯誤")
            
            return severity_text, f"發生未預期的錯誤：\n{str(error)}\n\n請聯繫技術支援。"
    
    def _attempt_recovery(self, error: Exception) -> bool:
        """Attempt automatic recovery from error."""
        error_type = type(error).__name__
        
        if error_type in self.recovery_callbacks:
            try:
                recovery_callback = self.recovery_callbacks[error_type]
                success = recovery_callback()
                
                if success:
                    self.log_manager.log(
                        LogLevel.INFO,
                        f"Successfully recovered from {error_type}"
                    )
                else:
                    self.log_manager.log(
                        LogLevel.WARNING,
                        f"Recovery attempt failed for {error_type}"
                    )
                
                return success
            except Exception as recovery_error:
                self.log_manager.log(
                    LogLevel.ERROR,
                    f"Recovery callback failed: {str(recovery_error)}"
                )
        
        return False
    
    def _handle_critical_error(self, error: Exception) -> bool:
        """Handle critical errors that may require special action."""
        self.log_manager.log(
            LogLevel.CRITICAL,
            f"Critical error occurred: {str(error)}",
            details={"critical_error_count": self.critical_error_count}
        )
        
        # If too many critical errors, suggest safe mode
        if self.critical_error_count >= 3:
            response = messagebox.askyesno(
                "嚴重錯誤",
                "應用程式發生多次嚴重錯誤。\n\n是否要進入安全模式？\n\n"
                "安全模式將停用所有自動化功能，僅允許基本操作。"
            )
            
            if response:
                return self._enter_safe_mode()
        
        return False
    
    def _enter_safe_mode(self) -> bool:
        """Enter safe mode with limited functionality."""
        try:
            self.log_manager.log(
                LogLevel.INFO,
                "Entering safe mode due to critical errors"
            )
            
            # Notify all components to enter safe mode
            for callback in self.error_callbacks:
                try:
                    # Use a special safe mode error to signal components
                    safe_mode_error = SchedulerError(
                        "Entering safe mode",
                        error_code="SAFE_MODE",
                        details={"action": "enter_safe_mode"}
                    )
                    callback(safe_mode_error)
                except Exception:
                    pass  # Ignore callback errors in safe mode
            
            messagebox.showinfo(
                "安全模式",
                "已進入安全模式。\n\n"
                "自動化功能已停用，僅可進行基本操作。\n"
                "請重新啟動應用程式以恢復正常功能。"
            )
            
            return True
        except Exception as safe_mode_error:
            self.log_manager.log(
                LogLevel.CRITICAL,
                f"Failed to enter safe mode: {str(safe_mode_error)}"
            )
            return False
    
    def get_error_report(self) -> Dict[str, Any]:
        """Generate error report for diagnostics."""
        return {
            "total_errors": self.error_count,
            "critical_errors": self.critical_error_count,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "registered_callbacks": len(self.error_callbacks),
            "recovery_handlers": list(self.recovery_callbacks.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_error_counters(self):
        """Reset error counters (useful for testing or after recovery)."""
        self.error_count = 0
        self.critical_error_count = 0
        self.last_error_time = None
        
        self.log_manager.log(
            LogLevel.INFO,
            "Error counters reset"
        )


# Global error handler instance
_global_error_handler: Optional[GlobalErrorHandler] = None


def get_global_error_handler() -> GlobalErrorHandler:
    """Get the global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = GlobalErrorHandler()
    return _global_error_handler


def handle_errors(severity: str = ErrorSeverity.MEDIUM, 
                 show_user_message: bool = True,
                 attempt_recovery: bool = True):
    """
    Decorator for automatic error handling.
    
    Args:
        severity: Error severity level
        show_user_message: Whether to show user-friendly message
        attempt_recovery: Whether to attempt automatic recovery
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = get_global_error_handler()
                error_handler.handle_error(e, severity, show_user_message, attempt_recovery)
                return None
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, default_return=None, 
                error_message: str = "Operation failed", **kwargs):
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        default_return: Value to return if function fails
        error_message: Custom error message
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or default_return if error occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler = get_global_error_handler()
        scheduler_error = SchedulerError(
            f"{error_message}: {str(e)}",
            details={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)}
        )
        error_handler.handle_error(scheduler_error)
        return default_return