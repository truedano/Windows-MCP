"""
Tests for the security validation system.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, "src")

from src.core.security_manager import (
    SecurityManager,
    SecurityLevel,
    OperationType,
    AuditRecord,
    get_security_manager,
    require_security_validation
)
from src.core.error_handler import PermissionError, ValidationError


class TestSecurityManager:
    """Test SecurityManager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.security_manager = SecurityManager()
        self.mock_log_manager = Mock()
        self.security_manager.log_manager = self.mock_log_manager
    
    def test_security_manager_initialization(self):
        """Test security manager initialization."""
        assert len(self.security_manager.blocked_applications) > 0
        assert len(self.security_manager.dangerous_commands) > 0
        assert len(self.security_manager.audit_records) == 0
        assert isinstance(self.security_manager.security_settings, dict)
    
    def test_validate_safe_operation(self):
        """Test validation of safe operations."""
        is_allowed, security_level, reason = self.security_manager.validate_operation_security(
            OperationType.WINDOW_CONTROL,
            "notepad.exe",
            {"action": "resize", "width": 800, "height": 600}
        )
        
        assert is_allowed is True
        assert security_level == SecurityLevel.SAFE
        assert "successfully" in reason.lower()
    
    def test_validate_dangerous_operation(self):
        """Test validation of dangerous operations."""
        is_allowed, security_level, reason = self.security_manager.validate_operation_security(
            OperationType.CUSTOM_COMMAND,
            "cmd.exe",
            {"command": "shutdown /s /t 0"}
        )
        
        assert is_allowed is False
        assert security_level == SecurityLevel.DANGEROUS
        assert "危險命令被阻止" in reason
    
    def test_validate_system_critical_app(self):
        """Test validation of system critical applications."""
        is_allowed, security_level, reason = self.security_manager.validate_operation_security(
            OperationType.APP_CLOSE,
            "explorer.exe",
            {}
        )
        
        assert is_allowed is False
        assert security_level == SecurityLevel.DANGEROUS
        assert "系統關鍵應用程式" in reason
    
    def test_validate_batch_operation_limit(self):
        """Test validation of batch operation limits."""
        is_allowed, security_level, reason = self.security_manager.validate_operation_security(
            OperationType.TASK_EXECUTE,
            "batch_task",
            {"batch_count": 15}  # Exceeds default limit of 10
        )
        
        assert is_allowed is False
        assert "批次操作數量超過限制" in reason
    
    def test_validate_unsafe_file_path(self):
        """Test validation of unsafe file paths."""
        is_allowed, security_level, reason = self.security_manager.validate_operation_security(
            OperationType.SYSTEM_ACCESS,
            "file_operation",
            {"file_path": "C:\\Windows\\System32\\important.dll"}
        )
        
        assert is_allowed is False
        assert "不安全的檔案路徑" in reason
    
    @patch('tkinter.messagebox.askyesno', return_value=True)
    def test_dangerous_operation_confirmation_approved(self, mock_messagebox):
        """Test dangerous operation confirmation when user approves."""
        result = self.security_manager.request_dangerous_operation_confirmation(
            OperationType.CUSTOM_COMMAND,
            "cmd.exe",
            {"command": "test command"},
            SecurityLevel.DANGEROUS
        )
        
        assert result is True
        mock_messagebox.assert_called_once()
    
    @patch('tkinter.messagebox.askyesno', return_value=False)
    def test_dangerous_operation_confirmation_denied(self, mock_messagebox):
        """Test dangerous operation confirmation when user denies."""
        result = self.security_manager.request_dangerous_operation_confirmation(
            OperationType.CUSTOM_COMMAND,
            "cmd.exe", 
            {"command": "test command"},
            SecurityLevel.DANGEROUS
        )
        
        assert result is False
        mock_messagebox.assert_called_once()
    
    def test_audit_operation(self):
        """Test operation auditing."""
        self.security_manager.audit_operation(
            OperationType.TASK_CREATE,
            "User created new task",
            "test_task",
            {"param1": "value1"},
            SecurityLevel.MEDIUM_RISK,
            "SUCCESS"
        )
        
        assert len(self.security_manager.audit_records) == 1
        
        record = self.security_manager.audit_records[0]
        assert record.operation_type == OperationType.TASK_CREATE
        assert record.user_action == "User created new task"
        assert record.target == "test_task"
        assert record.result == "SUCCESS"
    
    def test_audit_record_cleanup(self):
        """Test audit record cleanup."""
        # Set low limits for testing
        self.security_manager.security_settings["max_audit_records"] = 3
        self.security_manager.security_settings["audit_retention_days"] = 1
        
        # Add records
        for i in range(5):
            self.security_manager.audit_operation(
                OperationType.TASK_EXECUTE,
                f"Test operation {i}",
                f"target_{i}",
                {},
                SecurityLevel.SAFE,
                "SUCCESS"
            )
        
        # Should only keep the last 3 records
        assert len(self.security_manager.audit_records) == 3
    
    def test_get_audit_report(self):
        """Test audit report generation."""
        # Add some test records
        start_time = datetime.now()
        
        self.security_manager.audit_operation(
            OperationType.TASK_CREATE,
            "Create task 1",
            "task1",
            {},
            SecurityLevel.SAFE,
            "SUCCESS"
        )
        
        self.security_manager.audit_operation(
            OperationType.TASK_DELETE,
            "Delete task 2", 
            "task2",
            {},
            SecurityLevel.MEDIUM_RISK,
            "SUCCESS"
        )
        
        # Get all records
        all_records = self.security_manager.get_audit_report()
        assert len(all_records) == 2
        
        # Filter by operation type
        create_records = self.security_manager.get_audit_report(
            operation_type=OperationType.TASK_CREATE
        )
        assert len(create_records) == 1
        assert create_records[0]["operation_type"] == OperationType.TASK_CREATE.value
    
    def test_export_audit_log(self):
        """Test audit log export."""
        # Add test record
        self.security_manager.audit_operation(
            OperationType.TASK_EXECUTE,
            "Test export",
            "test_target",
            {"test": "data"},
            SecurityLevel.SAFE,
            "SUCCESS"
        )
        
        # Test export (mock file operations)
        with patch('builtins.open', create=True) as mock_open:
            with patch('json.dump') as mock_json_dump:
                result = self.security_manager.export_audit_log("test_export.json")
                
                assert result is True
                mock_open.assert_called_once()
                mock_json_dump.assert_called_once()
    
    def test_permission_cache(self):
        """Test permission caching."""
        # Enable caching
        self.security_manager.security_settings["enable_permission_caching"] = True
        
        # First check should perform actual validation
        with patch.object(self.security_manager, '_perform_permission_check', return_value=True) as mock_check:
            has_permission, reason = self.security_manager._check_operation_permissions(
                OperationType.TASK_EXECUTE,
                "test_target",
                {}
            )
            
            assert has_permission is True
            mock_check.assert_called_once()
        
        # Second check should use cache
        with patch.object(self.security_manager, '_perform_permission_check', return_value=True) as mock_check:
            has_permission, reason = self.security_manager._check_operation_permissions(
                OperationType.TASK_EXECUTE,
                "test_target", 
                {}
            )
            
            assert has_permission is True
            assert "快取" in reason
            mock_check.assert_not_called()
    
    def test_clear_permission_cache(self):
        """Test clearing permission cache."""
        # Add something to cache
        self.security_manager.permission_cache["test"] = (True, datetime.now())
        assert len(self.security_manager.permission_cache) == 1
        
        # Clear cache
        self.security_manager.clear_permission_cache()
        assert len(self.security_manager.permission_cache) == 0
    
    def test_get_security_status(self):
        """Test security status report."""
        status = self.security_manager.get_security_status()
        
        assert "audit_records_count" in status
        assert "blocked_applications_count" in status
        assert "dangerous_commands_count" in status
        assert "security_settings" in status
        assert "is_running_as_admin" in status
        
        assert isinstance(status["audit_records_count"], int)
        assert isinstance(status["blocked_applications_count"], int)
        assert isinstance(status["security_settings"], dict)


class TestSecurityDecorator:
    """Test security validation decorator."""
    
    def setup_method(self):
        """Setup test environment."""
        self.security_manager = get_security_manager()
        self.security_manager.audit_records.clear()
    
    @patch('tkinter.messagebox.askyesno', return_value=True)
    def test_security_decorator_success(self, mock_messagebox):
        """Test security decorator with successful operation."""
        @require_security_validation(OperationType.TASK_CREATE, require_confirmation=False)
        def test_function(target, param1="value1"):
            return f"Success: {target}"
        
        result = test_function("test_target", param1="test_value")
        assert result == "Success: test_target"
        
        # Check that operation was audited
        assert len(self.security_manager.audit_records) == 1
        record = self.security_manager.audit_records[0]
        assert record.operation_type == OperationType.TASK_CREATE
        assert record.result == "SUCCESS"
    
    @patch('tkinter.messagebox.askyesno', return_value=False)
    def test_security_decorator_user_cancellation(self, mock_messagebox):
        """Test security decorator when user cancels dangerous operation."""
        @require_security_validation(OperationType.CUSTOM_COMMAND, require_confirmation=True)
        def dangerous_function(target, command="dangerous_command"):
            return "This should not execute"
        
        with pytest.raises(PermissionError) as exc_info:
            dangerous_function("cmd.exe", command="shutdown /s /t 0")
        
        assert "cancelled by user" in str(exc_info.value)
    
    def test_security_decorator_blocked_operation(self):
        """Test security decorator with blocked operation."""
        @require_security_validation(OperationType.APP_CLOSE, require_confirmation=False)
        def close_app_function(target):
            return f"Closing {target}"
        
        with pytest.raises(PermissionError) as exc_info:
            close_app_function("explorer.exe")  # System critical app
        
        assert "Operation denied" in str(exc_info.value)
    
    def test_security_decorator_function_exception(self):
        """Test security decorator when decorated function raises exception."""
        @require_security_validation(OperationType.TASK_EXECUTE, require_confirmation=False)
        def failing_function(target):
            raise ValueError("Function failed")
        
        with pytest.raises(ValueError):
            failing_function("test_target")
        
        # Check that failure was audited
        assert len(self.security_manager.audit_records) == 1
        record = self.security_manager.audit_records[0]
        assert record.result.startswith("FAILED:")


class TestAuditRecord:
    """Test AuditRecord functionality."""
    
    def test_audit_record_creation(self):
        """Test audit record creation."""
        record = AuditRecord(
            operation_type=OperationType.TASK_CREATE,
            user_action="Create new task",
            target="test_task",
            parameters={"param1": "value1"},
            security_level=SecurityLevel.SAFE,
            result="SUCCESS"
        )
        
        assert record.operation_type == OperationType.TASK_CREATE
        assert record.user_action == "Create new task"
        assert record.target == "test_task"
        assert record.parameters == {"param1": "value1"}
        assert record.security_level == SecurityLevel.SAFE
        assert record.result == "SUCCESS"
        assert isinstance(record.timestamp, datetime)
        assert isinstance(record.session_id, str)
        assert len(record.session_id) == 8
    
    def test_audit_record_to_dict(self):
        """Test audit record dictionary conversion."""
        record = AuditRecord(
            operation_type=OperationType.TASK_DELETE,
            user_action="Delete task",
            target="old_task",
            parameters={},
            security_level=SecurityLevel.MEDIUM_RISK,
            result="SUCCESS"
        )
        
        record_dict = record.to_dict()
        
        assert record_dict["operation_type"] == "task_delete"
        assert record_dict["user_action"] == "Delete task"
        assert record_dict["target"] == "old_task"
        assert record_dict["security_level"] == "medium_risk"
        assert record_dict["result"] == "SUCCESS"
        assert "timestamp" in record_dict
        assert "session_id" in record_dict


class TestSecurityLevels:
    """Test security level assessment."""
    
    def setup_method(self):
        """Setup test environment."""
        self.security_manager = SecurityManager()
    
    def test_safe_operation_level(self):
        """Test safe operation security level."""
        level = self.security_manager._assess_security_level(
            OperationType.WINDOW_CONTROL,
            "notepad.exe",
            {"action": "resize"}
        )
        assert level == SecurityLevel.SAFE
    
    def test_medium_risk_operation_level(self):
        """Test medium risk operation security level."""
        level = self.security_manager._assess_security_level(
            OperationType.APP_LAUNCH,
            "calculator.exe",
            {}
        )
        assert level == SecurityLevel.MEDIUM_RISK
    
    def test_high_risk_operation_level(self):
        """Test high risk operation security level."""
        level = self.security_manager._assess_security_level(
            OperationType.CUSTOM_COMMAND,
            "cmd.exe",
            {"command": "dir"}
        )
        assert level == SecurityLevel.HIGH_RISK
    
    def test_dangerous_operation_level(self):
        """Test dangerous operation security level."""
        level = self.security_manager._assess_security_level(
            OperationType.APP_CLOSE,
            "explorer.exe",
            {}
        )
        assert level == SecurityLevel.DANGEROUS


if __name__ == "__main__":
    pytest.main([__file__])