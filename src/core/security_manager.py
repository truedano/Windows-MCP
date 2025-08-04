"""
Security validation and permission management system for Windows Scheduler GUI.

This module provides dangerous operation confirmation, permission checks, 
operation auditing, and security validation functionality.
"""

import os
import sys
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
import tkinter as tk
from tkinter import messagebox
import re

from src.models.enums import ActionType, LogLevel
from src.core.log_manager import get_log_manager
from src.core.error_handler import get_global_error_handler, PermissionError, ValidationError


class SecurityLevel(Enum):
    """Security levels for operations."""
    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    DANGEROUS = "dangerous"


class OperationType(Enum):
    """Types of operations for auditing."""
    TASK_CREATE = "task_create"
    TASK_EDIT = "task_edit"
    TASK_DELETE = "task_delete"
    TASK_EXECUTE = "task_execute"
    APP_LAUNCH = "app_launch"
    APP_CLOSE = "app_close"
    WINDOW_CONTROL = "window_control"
    CUSTOM_COMMAND = "custom_command"
    CONFIG_CHANGE = "config_change"
    SYSTEM_ACCESS = "system_access"


class AuditRecord:
    """Audit record for security operations."""
    
    def __init__(self, operation_type: OperationType, user_action: str,
                 target: str, parameters: Dict[str, Any], 
                 security_level: SecurityLevel, result: str):
        self.timestamp = datetime.now()
        self.operation_type = operation_type
        self.user_action = user_action
        self.target = target
        self.parameters = parameters
        self.security_level = security_level
        self.result = result
        self.session_id = self._generate_session_id()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        data = f"{self.timestamp}{os.getpid()}{id(self)}"
        return hashlib.md5(data.encode()).hexdigest()[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit record to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "operation_type": self.operation_type.value,
            "user_action": self.user_action,
            "target": self.target,
            "parameters": self.parameters,
            "security_level": self.security_level.value,
            "result": self.result,
            "session_id": self.session_id
        }


class SecurityManager:
    """Main security manager for the application."""
    
    def __init__(self):
        self.log_manager = get_log_manager()
        self.error_handler = get_global_error_handler()
        self.audit_records: List[AuditRecord] = []
        self.blocked_applications: Set[str] = set()
        self.dangerous_commands: Set[str] = set()
        self.permission_cache: Dict[str, Tuple[bool, datetime]] = {}
        self.security_settings = self._load_security_settings()
        
        # Initialize security rules
        self._initialize_security_rules()
    
    def _load_security_settings(self) -> Dict[str, Any]:
        """Load security settings from configuration."""
        default_settings = {
            "require_confirmation_for_dangerous_ops": True,
            "enable_operation_auditing": True,
            "audit_retention_days": 30,
            "max_audit_records": 10000,
            "enable_permission_caching": True,
            "permission_cache_duration_minutes": 5,
            "block_system_critical_apps": True,
            "allow_custom_commands": False,
            "max_batch_operations": 10
        }
        
        try:
            # Try to load from config file if it exists
            config_path = Path("config/security_settings.json")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
        except Exception as e:
            self.log_manager.log(
                LogLevel.WARNING,
                f"Failed to load security settings, using defaults: {str(e)}"
            )
        
        return default_settings
    
    def _initialize_security_rules(self):
        """Initialize security rules and blocked items."""
        # System critical applications that should be protected
        self.blocked_applications.update([
            "explorer.exe",
            "winlogon.exe", 
            "csrss.exe",
            "smss.exe",
            "wininit.exe",
            "services.exe",
            "lsass.exe",
            "svchost.exe",
            "dwm.exe",
            "taskhost.exe",
            "taskhostw.exe"
        ])
        
        # Dangerous command patterns
        self.dangerous_commands.update([
            r".*shutdown.*",
            r".*restart.*",
            r".*format.*",
            r".*del\s+.*",
            r".*rmdir.*",
            r".*rd\s+.*",
            r".*reg\s+delete.*",
            r".*net\s+user.*",
            r".*net\s+localgroup.*",
            r".*sc\s+delete.*",
            r".*taskkill.*\/f.*",
            r".*powershell.*-ExecutionPolicy.*Bypass.*",
            r".*cmd.*\/c.*del.*",
            r".*wmic.*"
        ])
    
    def validate_operation_security(self, operation_type: OperationType,
                                  target: str, parameters: Dict[str, Any]) -> Tuple[bool, SecurityLevel, str]:
        """
        Validate the security of an operation.
        
        Args:
            operation_type: Type of operation
            target: Target of the operation (app name, command, etc.)
            parameters: Operation parameters
            
        Returns:
            Tuple of (is_allowed, security_level, reason)
        """
        try:
            # Determine security level
            security_level = self._assess_security_level(operation_type, target, parameters)
            
            # Check if operation is blocked
            is_blocked, block_reason = self._check_operation_blocked(operation_type, target, parameters)
            if is_blocked:
                return False, security_level, block_reason
            
            # Check specific validation rules
            is_valid, validation_reason = self._validate_operation_rules(operation_type, target, parameters)
            if not is_valid:
                return False, security_level, validation_reason
            
            # Check permission requirements
            has_permission, permission_reason = self._check_operation_permissions(operation_type, target, parameters)
            if not has_permission:
                return False, security_level, permission_reason
            
            return True, security_level, "Operation validated successfully"
            
        except Exception as e:
            self.error_handler.handle_error(
                ValidationError(f"Security validation failed: {str(e)}")
            )
            return False, SecurityLevel.DANGEROUS, f"Validation error: {str(e)}"
    
    def _assess_security_level(self, operation_type: OperationType,
                             target: str, parameters: Dict[str, Any]) -> SecurityLevel:
        """Assess the security level of an operation."""
        # System critical operations
        if operation_type == OperationType.CUSTOM_COMMAND:
            if self._is_dangerous_command(parameters.get("command", "")):
                return SecurityLevel.DANGEROUS
            return SecurityLevel.HIGH_RISK
        
        # Application control operations
        if operation_type in [OperationType.APP_CLOSE, OperationType.APP_LAUNCH]:
            if self._is_system_critical_app(target):
                return SecurityLevel.DANGEROUS
            return SecurityLevel.MEDIUM_RISK
        
        # Task operations
        if operation_type in [OperationType.TASK_DELETE]:
            return SecurityLevel.MEDIUM_RISK
        
        # Configuration changes
        if operation_type == OperationType.CONFIG_CHANGE:
            return SecurityLevel.LOW_RISK
        
        # Window control operations
        if operation_type == OperationType.WINDOW_CONTROL:
            return SecurityLevel.SAFE
        
        # Default to medium risk
        return SecurityLevel.MEDIUM_RISK
    
    def _check_operation_blocked(self, operation_type: OperationType,
                               target: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if operation is explicitly blocked."""
        # Block system critical applications if setting is enabled
        if (self.security_settings.get("block_system_critical_apps", True) and
            self._is_system_critical_app(target)):
            return True, f"操作被阻止：{target} 是系統關鍵應用程式"
        
        # Block custom commands if setting is disabled
        if (operation_type == OperationType.CUSTOM_COMMAND and
            not self.security_settings.get("allow_custom_commands", False)):
            return True, "自訂命令功能已被停用"
        
        # Check for dangerous command patterns
        if operation_type == OperationType.CUSTOM_COMMAND:
            command = parameters.get("command", "")
            if self._is_dangerous_command(command):
                return True, f"危險命令被阻止：{command}"
        
        return False, ""
    
    def _validate_operation_rules(self, operation_type: OperationType,
                                target: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate operation against security rules."""
        # Validate batch operation limits
        if "batch_count" in parameters:
            max_batch = self.security_settings.get("max_batch_operations", 10)
            if parameters["batch_count"] > max_batch:
                return False, f"批次操作數量超過限制（最大：{max_batch}）"
        
        # Validate file paths for safety
        if "file_path" in parameters:
            file_path = parameters["file_path"]
            if not self._is_safe_file_path(file_path):
                return False, f"不安全的檔案路徑：{file_path}"
        
        # Validate command parameters
        if operation_type == OperationType.CUSTOM_COMMAND:
            command = parameters.get("command", "")
            if not self._validate_command_safety(command):
                return False, f"命令包含不安全的參數：{command}"
        
        return True, ""
    
    def _check_operation_permissions(self, operation_type: OperationType,
                                   target: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if user has permission for the operation."""
        # Check cached permissions
        cache_key = f"{operation_type.value}:{target}"
        if self.security_settings.get("enable_permission_caching", True):
            if cache_key in self.permission_cache:
                cached_result, cache_time = self.permission_cache[cache_key]
                cache_duration = timedelta(
                    minutes=self.security_settings.get("permission_cache_duration_minutes", 5)
                )
                if datetime.now() - cache_time < cache_duration:
                    return cached_result, "使用快取的權限檢查結果"
        
        # Perform permission check
        has_permission = self._perform_permission_check(operation_type, target, parameters)
        
        # Cache the result
        if self.security_settings.get("enable_permission_caching", True):
            self.permission_cache[cache_key] = (has_permission, datetime.now())
        
        if not has_permission:
            return False, "權限不足，無法執行此操作"
        
        return True, "權限檢查通過"
    
    def _perform_permission_check(self, operation_type: OperationType,
                                target: str, parameters: Dict[str, Any]) -> bool:
        """Perform actual permission check."""
        # For now, assume basic permission checks
        # In a real implementation, this would check Windows permissions,
        # user groups, etc.
        
        # Check if running as administrator for dangerous operations
        if operation_type in [OperationType.CUSTOM_COMMAND, OperationType.SYSTEM_ACCESS]:
            return self._is_running_as_admin()
        
        return True
    
    def _is_running_as_admin(self) -> bool:
        """Check if the application is running with administrator privileges."""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    
    def _is_system_critical_app(self, app_name: str) -> bool:
        """Check if application is system critical."""
        if not app_name:
            return False
        
        app_name_lower = app_name.lower()
        return any(blocked_app.lower() in app_name_lower for blocked_app in self.blocked_applications)
    
    def _is_dangerous_command(self, command: str) -> bool:
        """Check if command matches dangerous patterns."""
        if not command:
            return False
        
        command_lower = command.lower()
        return any(re.match(pattern, command_lower) for pattern in self.dangerous_commands)
    
    def _is_safe_file_path(self, file_path: str) -> bool:
        """Check if file path is safe."""
        if not file_path:
            return False
        
        # Block access to system directories
        dangerous_paths = [
            "c:\\windows\\system32",
            "c:\\windows\\syswow64", 
            "c:\\program files\\windows",
            "c:\\users\\all users",
            "c:\\programdata\\microsoft\\windows"
        ]
        
        file_path_lower = file_path.lower()
        return not any(dangerous_path in file_path_lower for dangerous_path in dangerous_paths)
    
    def _validate_command_safety(self, command: str) -> bool:
        """Validate command for safety."""
        if not command:
            return True
        
        # Check for command injection patterns
        dangerous_patterns = [
            r".*&&.*",
            r".*\|\|.*",
            r".*\|.*",
            r".*>.*",
            r".*<.*",
            r".*`.*",
            r".*\$\(.*\).*",
            r".*%.*%.*"
        ]
        
        command_lower = command.lower()
        return not any(re.match(pattern, command_lower) for pattern in dangerous_patterns)
    
    def request_dangerous_operation_confirmation(self, operation_type: OperationType,
                                               target: str, parameters: Dict[str, Any],
                                               security_level: SecurityLevel) -> bool:
        """
        Request user confirmation for dangerous operations.
        
        Args:
            operation_type: Type of operation
            target: Target of the operation
            parameters: Operation parameters
            security_level: Security level of the operation
            
        Returns:
            True if user confirms, False otherwise
        """
        if not self.security_settings.get("require_confirmation_for_dangerous_ops", True):
            return True
        
        if security_level in [SecurityLevel.SAFE, SecurityLevel.LOW_RISK]:
            return True
        
        # Create confirmation dialog
        title = "安全確認"
        message = self._generate_confirmation_message(operation_type, target, parameters, security_level)
        
        try:
            # Show confirmation dialog
            if security_level == SecurityLevel.DANGEROUS:
                # For dangerous operations, require explicit confirmation
                response = messagebox.askyesno(
                    title,
                    f"{message}\n\n⚠️ 這是一個危險操作，可能會影響系統穩定性。\n\n您確定要繼續嗎？",
                    icon="warning"
                )
            elif security_level == SecurityLevel.HIGH_RISK:
                response = messagebox.askyesno(
                    title,
                    f"{message}\n\n⚠️ 這是一個高風險操作。\n\n您確定要繼續嗎？",
                    icon="warning"
                )
            else:  # MEDIUM_RISK
                response = messagebox.askyesno(
                    title,
                    f"{message}\n\n您確定要執行此操作嗎？",
                    icon="question"
                )
            
            # Log the confirmation result
            self.log_manager.log(
                LogLevel.INFO,
                f"User confirmation for {operation_type.value}: {'Approved' if response else 'Denied'}",
                details={
                    "target": target,
                    "security_level": security_level.value,
                    "user_response": response
                }
            )
            
            return response
            
        except Exception as e:
            self.error_handler.handle_error(
                ValidationError(f"Failed to show confirmation dialog: {str(e)}")
            )
            # Default to deny for safety
            return False
    
    def _generate_confirmation_message(self, operation_type: OperationType,
                                     target: str, parameters: Dict[str, Any],
                                     security_level: SecurityLevel) -> str:
        """Generate confirmation message for the operation."""
        operation_descriptions = {
            OperationType.TASK_CREATE: f"建立新任務：{target}",
            OperationType.TASK_EDIT: f"編輯任務：{target}",
            OperationType.TASK_DELETE: f"刪除任務：{target}",
            OperationType.TASK_EXECUTE: f"執行任務：{target}",
            OperationType.APP_LAUNCH: f"啟動應用程式：{target}",
            OperationType.APP_CLOSE: f"關閉應用程式：{target}",
            OperationType.WINDOW_CONTROL: f"控制視窗：{target}",
            OperationType.CUSTOM_COMMAND: f"執行自訂命令：{parameters.get('command', target)}",
            OperationType.CONFIG_CHANGE: f"修改配置：{target}",
            OperationType.SYSTEM_ACCESS: f"系統存取：{target}"
        }
        
        base_message = operation_descriptions.get(operation_type, f"執行操作：{target}")
        
        # Add parameter details if relevant
        if parameters:
            param_details = []
            for key, value in parameters.items():
                if key not in ["command"] and value:  # command already shown in base message
                    param_details.append(f"{key}: {value}")
            
            if param_details:
                base_message += f"\n參數：{', '.join(param_details)}"
        
        return base_message
    
    def audit_operation(self, operation_type: OperationType, user_action: str,
                       target: str, parameters: Dict[str, Any],
                       security_level: SecurityLevel, result: str):
        """
        Audit an operation for security tracking.
        
        Args:
            operation_type: Type of operation
            user_action: Description of user action
            target: Target of the operation
            parameters: Operation parameters
            security_level: Security level of the operation
            result: Result of the operation
        """
        if not self.security_settings.get("enable_operation_auditing", True):
            return
        
        try:
            # Create audit record
            audit_record = AuditRecord(
                operation_type=operation_type,
                user_action=user_action,
                target=target,
                parameters=parameters,
                security_level=security_level,
                result=result
            )
            
            # Add to audit records
            self.audit_records.append(audit_record)
            
            # Log the audit record
            self.log_manager.log(
                LogLevel.INFO,
                f"Operation audited: {user_action}",
                details=audit_record.to_dict()
            )
            
            # Cleanup old records if necessary
            self._cleanup_audit_records()
            
        except Exception as e:
            self.error_handler.handle_error(
                ValidationError(f"Failed to audit operation: {str(e)}")
            )
    
    def _cleanup_audit_records(self):
        """Clean up old audit records based on retention settings."""
        max_records = self.security_settings.get("max_audit_records", 10000)
        retention_days = self.security_settings.get("audit_retention_days", 30)
        
        # Remove records older than retention period
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        self.audit_records = [
            record for record in self.audit_records
            if record.timestamp > cutoff_date
        ]
        
        # Remove excess records if still over limit
        if len(self.audit_records) > max_records:
            # Keep the most recent records
            self.audit_records = self.audit_records[-max_records:]
    
    def get_audit_report(self, start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        operation_type: Optional[OperationType] = None) -> List[Dict[str, Any]]:
        """
        Get audit report for specified criteria.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            operation_type: Filter by operation type
            
        Returns:
            List of audit records as dictionaries
        """
        filtered_records = self.audit_records
        
        # Filter by date range
        if start_date:
            filtered_records = [r for r in filtered_records if r.timestamp >= start_date]
        if end_date:
            filtered_records = [r for r in filtered_records if r.timestamp <= end_date]
        
        # Filter by operation type
        if operation_type:
            filtered_records = [r for r in filtered_records if r.operation_type == operation_type]
        
        return [record.to_dict() for record in filtered_records]
    
    def export_audit_log(self, file_path: str, start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> bool:
        """
        Export audit log to file.
        
        Args:
            file_path: Path to export file
            start_date: Start date for export
            end_date: End date for export
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            audit_data = self.get_audit_report(start_date, end_date)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "export_timestamp": datetime.now().isoformat(),
                    "total_records": len(audit_data),
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "audit_records": audit_data
                }, f, indent=2, ensure_ascii=False)
            
            self.log_manager.log(
                LogLevel.INFO,
                f"Audit log exported to {file_path}",
                details={"record_count": len(audit_data)}
            )
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(
                ValidationError(f"Failed to export audit log: {str(e)}")
            )
            return False
    
    def clear_permission_cache(self):
        """Clear the permission cache."""
        self.permission_cache.clear()
        self.log_manager.log(LogLevel.INFO, "Permission cache cleared")
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status and statistics."""
        return {
            "audit_records_count": len(self.audit_records),
            "blocked_applications_count": len(self.blocked_applications),
            "dangerous_commands_count": len(self.dangerous_commands),
            "permission_cache_size": len(self.permission_cache),
            "security_settings": self.security_settings.copy(),
            "is_running_as_admin": self._is_running_as_admin(),
            "last_audit_timestamp": self.audit_records[-1].timestamp.isoformat() if self.audit_records else None
        }


# Global security manager instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get the global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def require_security_validation(operation_type: OperationType, 
                               require_confirmation: bool = True):
    """
    Decorator for operations that require security validation.
    
    Args:
        operation_type: Type of operation being performed
        require_confirmation: Whether to require user confirmation
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            security_manager = get_security_manager()
            
            # Extract target and parameters from function arguments
            target = kwargs.get('target', args[0] if args else 'unknown')
            parameters = kwargs.copy()
            
            # Validate operation security
            is_allowed, security_level, reason = security_manager.validate_operation_security(
                operation_type, str(target), parameters
            )
            
            if not is_allowed:
                raise PermissionError(f"Operation denied: {reason}")
            
            # Request confirmation if required
            if require_confirmation and security_level in [SecurityLevel.HIGH_RISK, SecurityLevel.DANGEROUS]:
                confirmed = security_manager.request_dangerous_operation_confirmation(
                    operation_type, str(target), parameters, security_level
                )
                if not confirmed:
                    raise PermissionError("Operation cancelled by user")
            
            # Execute the operation
            try:
                result = func(*args, **kwargs)
                
                # Audit successful operation
                security_manager.audit_operation(
                    operation_type=operation_type,
                    user_action=f"Executed {func.__name__}",
                    target=str(target),
                    parameters=parameters,
                    security_level=security_level,
                    result="SUCCESS"
                )
                
                return result
                
            except Exception as e:
                # Audit failed operation
                security_manager.audit_operation(
                    operation_type=operation_type,
                    user_action=f"Failed {func.__name__}",
                    target=str(target),
                    parameters=parameters,
                    security_level=security_level,
                    result=f"FAILED: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator