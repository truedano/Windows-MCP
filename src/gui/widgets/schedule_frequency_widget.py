"""
Schedule Frequency Widget for managing schedule check frequency settings.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class ScheduleFrequencyWidget(ttk.LabelFrame):
    """Widget for managing schedule check frequency settings."""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the ScheduleFrequencyWidget.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for LabelFrame
        """
        super().__init__(parent, text="排程檢查頻率", padding=15, **kwargs)
        
        self.frequency_var = tk.IntVar(value=1)
        self.change_callback: Optional[Callable[[int], None]] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Description
        desc_label = ttk.Label(
            self,
            text="設定系統檢查排程任務的頻率間隔",
            font=("TkDefaultFont", 9),
            foreground="gray"
        )
        desc_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Frequency setting frame
        freq_frame = ttk.Frame(self)
        freq_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Frequency label
        ttk.Label(freq_frame, text="檢查間隔:").pack(side=tk.LEFT)
        
        # Frequency spinbox
        self.frequency_spinbox = ttk.Spinbox(
            freq_frame,
            from_=1,
            to=60,
            width=5,
            textvariable=self.frequency_var,
            command=self._on_frequency_changed
        )
        self.frequency_spinbox.pack(side=tk.LEFT, padx=(10, 5))
        
        # Unit label
        ttk.Label(freq_frame, text="秒").pack(side=tk.LEFT)
        
        # Bind change event
        self.frequency_var.trace_add('write', self._on_frequency_var_changed)
        
        # Preset buttons frame
        preset_frame = ttk.Frame(self)
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(preset_frame, text="快速設定:").pack(side=tk.LEFT)
        
        # Preset buttons
        presets = [
            ("即時 (1秒)", 1),
            ("快速 (5秒)", 5),
            ("標準 (10秒)", 10),
            ("省電 (30秒)", 30)
        ]
        
        for text, value in presets:
            btn = ttk.Button(
                preset_frame,
                text=text,
                command=lambda v=value: self.set_frequency(v)
            )
            btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Performance impact info
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X)
        
        self.impact_label = ttk.Label(
            info_frame,
            text="",
            font=("TkDefaultFont", 8),
            foreground="blue"
        )
        self.impact_label.pack(anchor=tk.W)
        
        # Update impact info
        self._update_impact_info()
    
    def _on_frequency_changed(self):
        """Handle frequency spinbox change."""
        self._update_impact_info()
        if self.change_callback:
            self.change_callback(self.frequency_var.get())
    
    def _on_frequency_var_changed(self, *args):
        """Handle frequency variable change."""
        self._update_impact_info()
        if self.change_callback:
            self.change_callback(self.frequency_var.get())
    
    def _update_impact_info(self):
        """Update performance impact information."""
        frequency = self.frequency_var.get()
        
        if frequency <= 1:
            impact = "⚡ 即時響應，較高CPU使用率"
            color = "orange"
        elif frequency <= 5:
            impact = "🚀 快速響應，中等CPU使用率"
            color = "blue"
        elif frequency <= 15:
            impact = "⚖️ 平衡響應，標準CPU使用率"
            color = "green"
        else:
            impact = "🔋 省電模式，較低CPU使用率"
            color = "purple"
        
        self.impact_label.config(text=impact, foreground=color)
    
    def set_frequency(self, frequency: int):
        """
        Set the frequency value.
        
        Args:
            frequency: Frequency in seconds
        """
        if 1 <= frequency <= 60:
            self.frequency_var.set(frequency)
    
    def get_frequency(self) -> int:
        """
        Get the current frequency value.
        
        Returns:
            Current frequency in seconds
        """
        return self.frequency_var.get()
    
    def set_change_callback(self, callback: Callable[[int], None]):
        """
        Set callback for frequency changes.
        
        Args:
            callback: Function to call when frequency changes
        """
        self.change_callback = callback
    
    def validate(self) -> bool:
        """
        Validate the current frequency setting.
        
        Returns:
            True if valid, False otherwise
        """
        frequency = self.frequency_var.get()
        return 1 <= frequency <= 60