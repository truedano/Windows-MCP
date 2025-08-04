"""
Conditional trigger widget for schedule configuration.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from src.models.schedule import ConditionalTrigger, ConditionType


class ConditionalTriggerWidget(ttk.Frame):
    """Widget for configuring conditional triggers."""
    
    def __init__(self, parent: tk.Widget, on_change: Optional[Callable[[], None]] = None):
        """
        Initialize the conditional trigger widget.
        
        Args:
            parent: Parent widget
            on_change: Callback function when configuration changes
        """
        super().__init__(parent)
        self.on_change = on_change
        
        # Variables
        self.enabled_var = tk.BooleanVar()
        self.condition_type_var = tk.StringVar(value=ConditionType.WINDOW_TITLE_CONTAINS.value)
        self.condition_value_var = tk.StringVar()
        
        # Create UI
        self._create_ui()
        
        # Bind events
        self._bind_events()
    
    def _create_ui(self):
        """Create the widget UI."""
        # Enable checkbox
        enable_frame = ttk.Frame(self)
        enable_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.enable_check = ttk.Checkbutton(enable_frame, text="啟用條件觸發", 
                                          variable=self.enabled_var,
                                          command=self._on_enabled_change)
        self.enable_check.pack(anchor=tk.W)
        
        # Configuration frame
        self.config_frame = ttk.Frame(self)
        self.config_frame.pack(fill=tk.X)
        
        # Condition type selection
        type_frame = ttk.Frame(self.config_frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(type_frame, text="條件類型:").pack(side=tk.LEFT)
        
        # Condition type options
        condition_types = [
            (ConditionType.WINDOW_TITLE_CONTAINS.value, "視窗標題包含"),
            (ConditionType.WINDOW_TITLE_EQUALS.value, "視窗標題等於"),
            (ConditionType.WINDOW_EXISTS.value, "視窗存在"),
            (ConditionType.PROCESS_RUNNING.value, "程序運行中"),
            (ConditionType.TIME_RANGE.value, "時間範圍"),
            (ConditionType.SYSTEM_IDLE.value, "系統閒置")
        ]
        
        self.type_combo = ttk.Combobox(type_frame, textvariable=self.condition_type_var,
                                     values=[ct[0] for ct in condition_types],
                                     state="readonly", width=20)
        self.type_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Set display values
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_change)
        
        # Condition value input
        value_frame = ttk.Frame(self.config_frame)
        value_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(value_frame, text="條件值:").pack(side=tk.LEFT)
        
        self.value_entry = ttk.Entry(value_frame, textvariable=self.condition_value_var, width=30)
        self.value_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # Help text frame
        self.help_frame = ttk.Frame(self.config_frame)
        self.help_frame.pack(fill=tk.X)
        
        self.help_label = ttk.Label(self.help_frame, text="", 
                                  font=("", 8), foreground="gray", wraplength=400)
        self.help_label.pack(anchor=tk.W)
        
        # Initially disable configuration
        self._on_enabled_change()
        
        # Update help text
        self._update_help_text()
    
    def _bind_events(self):
        """Bind widget events."""
        self.condition_value_var.trace_add("write", lambda *args: self._on_change_callback())
    
    def _on_enabled_change(self):
        """Handle enabled checkbox change."""
        enabled = self.enabled_var.get()
        
        # Enable/disable configuration widgets
        state = "normal" if enabled else "disabled"
        
        for widget in self.config_frame.winfo_children():
            self._set_widget_state(widget, state)
        
        self._on_change_callback()
    
    def _set_widget_state(self, widget, state):
        """Recursively set widget state."""
        try:
            if hasattr(widget, 'configure'):
                if isinstance(widget, (ttk.Entry, ttk.Combobox)):
                    widget.configure(state=state)
                elif isinstance(widget, ttk.Label):
                    # Don't disable labels, just change appearance
                    if state == "disabled":
                        widget.configure(foreground="gray")
                    else:
                        widget.configure(foreground="black")
        except tk.TclError:
            pass
        
        # Recursively handle child widgets
        for child in widget.winfo_children():
            self._set_widget_state(child, state)
    
    def _on_type_change(self, event=None):
        """Handle condition type change."""
        self._update_help_text()
        self._on_change_callback()
    
    def _update_help_text(self):
        """Update help text based on selected condition type."""
        condition_type = self.condition_type_var.get()
        
        help_texts = {
            ConditionType.WINDOW_TITLE_CONTAINS.value: 
                "輸入要檢查的視窗標題文字。如果任何視窗標題包含此文字，條件為真。",
            ConditionType.WINDOW_TITLE_EQUALS.value: 
                "輸入完整的視窗標題。如果存在完全匹配的視窗標題，條件為真。",
            ConditionType.WINDOW_EXISTS.value: 
                "輸入應用程式名稱。如果該應用程式的視窗存在，條件為真。",
            ConditionType.PROCESS_RUNNING.value: 
                "輸入程序名稱（不含.exe）。如果該程序正在運行，條件為真。",
            ConditionType.TIME_RANGE.value: 
                "輸入時間範圍，格式: HH:MM-HH:MM（例如: 09:00-17:00）。如果當前時間在此範圍內，條件為真。",
            ConditionType.SYSTEM_IDLE.value: 
                "輸入閒置時間（分鐘）。如果系統閒置時間超過此值，條件為真。"
        }
        
        help_text = help_texts.get(condition_type, "")
        self.help_label.configure(text=help_text)
    
    def _on_change_callback(self):
        """Call the change callback if provided."""
        if self.on_change:
            self.on_change()
    
    def get_trigger_config(self) -> Optional[ConditionalTrigger]:
        """
        Get the current conditional trigger configuration.
        
        Returns:
            ConditionalTrigger object or None if disabled/invalid
        """
        if not self.enabled_var.get():
            return None
        
        condition_value = self.condition_value_var.get().strip()
        if not condition_value:
            return None
        
        try:
            condition_type = ConditionType(self.condition_type_var.get())
            
            return ConditionalTrigger(
                condition_type=condition_type,
                condition_value=condition_value,
                enabled=True
            )
        except (ValueError, TypeError):
            return None
    
    def set_trigger(self, trigger: Optional[ConditionalTrigger]):
        """
        Set the widget values from a ConditionalTrigger object.
        
        Args:
            trigger: ConditionalTrigger object to load, or None to disable
        """
        if trigger is None:
            self.enabled_var.set(False)
            self.condition_type_var.set(ConditionType.WINDOW_TITLE_CONTAINS.value)
            self.condition_value_var.set("")
        else:
            self.enabled_var.set(trigger.enabled)
            self.condition_type_var.set(trigger.condition_type.value)
            self.condition_value_var.set(trigger.condition_value)
        
        # Update UI
        self._on_enabled_change()
        self._update_help_text()
    
    def validate(self) -> bool:
        """
        Validate the current configuration.
        
        Returns:
            True if configuration is valid
        """
        if not self.enabled_var.get():
            return True  # Disabled trigger is always valid
        
        condition_value = self.condition_value_var.get().strip()
        if not condition_value:
            return False
        
        condition_type = self.condition_type_var.get()
        
        # Validate specific condition types
        if condition_type == ConditionType.TIME_RANGE.value:
            # Validate time range format: HH:MM-HH:MM
            try:
                if '-' not in condition_value:
                    return False
                
                start_str, end_str = condition_value.split('-', 1)
                
                # Validate time format
                start_parts = start_str.strip().split(':')
                end_parts = end_str.strip().split(':')
                
                if len(start_parts) != 2 or len(end_parts) != 2:
                    return False
                
                start_hour, start_min = map(int, start_parts)
                end_hour, end_min = map(int, end_parts)
                
                # Validate ranges
                if not (0 <= start_hour <= 23 and 0 <= start_min <= 59):
                    return False
                if not (0 <= end_hour <= 23 and 0 <= end_min <= 59):
                    return False
                
                return True
            except (ValueError, IndexError):
                return False
        
        elif condition_type == ConditionType.SYSTEM_IDLE.value:
            # Validate idle time is a positive integer
            try:
                idle_minutes = int(condition_value)
                return idle_minutes > 0
            except ValueError:
                return False
        
        # For other types, any non-empty string is valid
        return True