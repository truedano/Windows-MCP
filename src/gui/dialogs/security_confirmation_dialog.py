"""
Security confirmation dialog for dangerous operations.

This dialog provides detailed information about operations that require user confirmation
and allows users to make informed decisions about security-sensitive actions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
from datetime import datetime

from src.core.security_manager import SecurityLevel, OperationType


class SecurityConfirmationDialog:
    """Dialog for confirming dangerous operations."""
    
    def __init__(self, parent: tk.Widget, operation_type: OperationType,
                 target: str, parameters: Dict[str, Any], 
                 security_level: SecurityLevel):
        self.parent = parent
        self.operation_type = operation_type
        self.target = target
        self.parameters = parameters
        self.security_level = security_level
        self.result = False
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("安全確認")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()  # Make dialog modal
        
        # Center dialog on parent
        self._center_dialog()
        
        # Create dialog content
        self._create_widgets()
        
        # Set focus and wait for result
        self.dialog.focus_set()
        self.dialog.wait_window()
    
    def _center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate dialog position
        dialog_width = 500
        dialog_height = 400
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Security level indicator
        self._create_security_indicator(main_frame)
        
        # Operation details
        self._create_operation_details(main_frame)
        
        # Risk information
        self._create_risk_information(main_frame)
        
        # Buttons
        self._create_buttons(main_frame)
    
    def _create_security_indicator(self, parent: ttk.Frame):
        """Create security level indicator."""
        indicator_frame = ttk.Frame(parent)
        indicator_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Security level colors and icons
        level_config = {
            SecurityLevel.DANGEROUS: {
                "color": "#dc3545",
                "icon": "⚠️",
                "text": "危險操作",
                "description": "此操作可能會影響系統穩定性或安全性"
            },
            SecurityLevel.HIGH_RISK: {
                "color": "#fd7e14", 
                "icon": "⚠️",
                "text": "高風險操作",
                "description": "此操作具有較高的風險，請謹慎考慮"
            },
            SecurityLevel.MEDIUM_RISK: {
                "color": "#ffc107",
                "icon": "⚡",
                "text": "中等風險操作", 
                "description": "此操作可能會產生意外的結果"
            }
        }
        
        config = level_config.get(self.security_level, level_config[SecurityLevel.MEDIUM_RISK])
        
        # Icon and title
        title_frame = ttk.Frame(indicator_frame)
        title_frame.pack(fill=tk.X)
        
        icon_label = ttk.Label(title_frame, text=config["icon"], font=("Arial", 16))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        title_label = ttk.Label(title_frame, text=config["text"], 
                               font=("Arial", 14, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Description
        desc_label = ttk.Label(indicator_frame, text=config["description"],
                              font=("Arial", 10), foreground="gray")
        desc_label.pack(fill=tk.X, pady=(5, 0))
    
    def _create_operation_details(self, parent: ttk.Frame):
        """Create operation details section."""
        details_frame = ttk.LabelFrame(parent, text="操作詳情", padding="10")
        details_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Operation type
        type_frame = ttk.Frame(details_frame)
        type_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(type_frame, text="操作類型:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(type_frame, text=self._get_operation_display_name()).pack(side=tk.LEFT, padx=(10, 0))
        
        # Target
        target_frame = ttk.Frame(details_frame)
        target_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(target_frame, text="目標:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(target_frame, text=self.target).pack(side=tk.LEFT, padx=(10, 0))
        
        # Parameters (if any)
        if self.parameters:
            params_frame = ttk.Frame(details_frame)
            params_frame.pack(fill=tk.X, pady=(5, 0))
            
            ttk.Label(params_frame, text="參數:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
            
            # Create scrollable text widget for parameters
            params_text = tk.Text(params_frame, height=4, width=50, wrap=tk.WORD)
            params_scrollbar = ttk.Scrollbar(params_frame, orient=tk.VERTICAL, command=params_text.yview)
            params_text.configure(yscrollcommand=params_scrollbar.set)
            
            params_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(5, 0))
            params_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(5, 0))
            
            # Insert parameters
            for key, value in self.parameters.items():
                params_text.insert(tk.END, f"{key}: {value}\n")
            
            params_text.config(state=tk.DISABLED)
    
    def _create_risk_information(self, parent: ttk.Frame):
        """Create risk information section."""
        risk_frame = ttk.LabelFrame(parent, text="風險資訊", padding="10")
        risk_frame.pack(fill=tk.X, pady=(0, 15))
        
        risk_messages = {
            SecurityLevel.DANGEROUS: [
                "• 此操作可能會導致系統不穩定",
                "• 可能會影響其他正在運行的應用程式",
                "• 建議在執行前備份重要資料",
                "• 請確保您了解此操作的後果"
            ],
            SecurityLevel.HIGH_RISK: [
                "• 此操作可能會產生意外的結果",
                "• 建議在非工作時間執行",
                "• 請確保目標應用程式處於適當狀態",
                "• 執行前請檢查相關設定"
            ],
            SecurityLevel.MEDIUM_RISK: [
                "• 此操作通常是安全的",
                "• 但仍可能產生意外的結果",
                "• 建議先在測試環境中驗證",
                "• 請確認操作參數正確"
            ]
        }
        
        messages = risk_messages.get(self.security_level, risk_messages[SecurityLevel.MEDIUM_RISK])
        
        for message in messages:
            label = ttk.Label(risk_frame, text=message, font=("Arial", 9))
            label.pack(anchor=tk.W, pady=1)
    
    def _create_buttons(self, parent: ttk.Frame):
        """Create dialog buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Cancel button
        cancel_btn = ttk.Button(button_frame, text="取消", command=self._cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Confirm button
        confirm_text = "確認執行" if self.security_level != SecurityLevel.DANGEROUS else "我了解風險並確認執行"
        confirm_btn = ttk.Button(button_frame, text=confirm_text, command=self._confirm)
        confirm_btn.pack(side=tk.RIGHT)
        
        # Set default button based on security level
        if self.security_level == SecurityLevel.DANGEROUS:
            cancel_btn.focus_set()  # Default to cancel for dangerous operations
        else:
            confirm_btn.focus_set()
        
        # Bind Enter and Escape keys
        self.dialog.bind('<Return>', lambda e: self._confirm())
        self.dialog.bind('<Escape>', lambda e: self._cancel())
    
    def _get_operation_display_name(self) -> str:
        """Get display name for operation type."""
        display_names = {
            OperationType.TASK_CREATE: "建立任務",
            OperationType.TASK_EDIT: "編輯任務",
            OperationType.TASK_DELETE: "刪除任務",
            OperationType.TASK_EXECUTE: "執行任務",
            OperationType.APP_LAUNCH: "啟動應用程式",
            OperationType.APP_CLOSE: "關閉應用程式",
            OperationType.WINDOW_CONTROL: "視窗控制",
            OperationType.CUSTOM_COMMAND: "自訂命令",
            OperationType.CONFIG_CHANGE: "配置變更",
            OperationType.SYSTEM_ACCESS: "系統存取"
        }
        return display_names.get(self.operation_type, self.operation_type.value)
    
    def _confirm(self):
        """Handle confirm button click."""
        self.result = True
        self.dialog.destroy()
    
    def _cancel(self):
        """Handle cancel button click."""
        self.result = False
        self.dialog.destroy()
    
    def get_result(self) -> bool:
        """Get the dialog result."""
        return self.result


def show_security_confirmation(parent: tk.Widget, operation_type: OperationType,
                              target: str, parameters: Dict[str, Any],
                              security_level: SecurityLevel) -> bool:
    """
    Show security confirmation dialog.
    
    Args:
        parent: Parent widget
        operation_type: Type of operation
        target: Target of the operation
        parameters: Operation parameters
        security_level: Security level of the operation
        
    Returns:
        True if user confirms, False otherwise
    """
    try:
        dialog = SecurityConfirmationDialog(parent, operation_type, target, parameters, security_level)
        return dialog.get_result()
    except Exception:
        # Fallback to simple message box if dialog fails
        return messagebox.askyesno(
            "安全確認",
            f"您確定要執行此操作嗎？\n\n操作: {operation_type.value}\n目標: {target}",
            icon="warning"
        )