"""
Trigger time widget for schedule configuration.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, List

from src.models.schedule import ScheduleType


class TriggerTimeWidget(ttk.Frame):
    """Widget for configuring trigger time settings."""
    
    def __init__(self, parent: tk.Widget, on_change: Optional[Callable[[], None]] = None):
        """
        Initialize the trigger time widget.
        
        Args:
            parent: Parent widget
            on_change: Callback function when configuration changes
        """
        super().__init__(parent)
        self.on_change = on_change
        
        # Variables
        self.schedule_type_var = tk.StringVar(value=ScheduleType.MANUAL.value)
        self.start_date_var = tk.StringVar()
        self.start_time_var = tk.StringVar()
        self.end_date_var = tk.StringVar()
        self.end_time_var = tk.StringVar()
        self.interval_value_var = tk.IntVar(value=1)
        self.interval_unit_var = tk.StringVar(value="hours")
        self.has_end_time_var = tk.BooleanVar()
        
        # Days of week variables (Monday=0 to Sunday=6)
        self.days_vars = [tk.BooleanVar() for _ in range(7)]
        
        # Set default values
        self._set_default_values()
        
        # Create UI
        self._create_ui()
        
        # Bind events
        self._bind_events()
    
    def _set_default_values(self):
        """Set default values for the widget."""
        now = datetime.now()
        
        # Set default start time to next hour
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        self.start_date_var.set(next_hour.strftime("%Y-%m-%d"))
        self.start_time_var.set(next_hour.strftime("%H:%M"))
        
        # Set default end time to one day later
        end_time = next_hour + timedelta(days=1)
        self.end_date_var.set(end_time.strftime("%Y-%m-%d"))
        self.end_time_var.set(end_time.strftime("%H:%M"))
    
    def _create_ui(self):
        """Create the widget UI."""
        # Schedule type selection
        type_frame = ttk.LabelFrame(self, text="排程類型", padding=5)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Radio buttons for schedule types
        types = [
            (ScheduleType.MANUAL.value, "不主動執行"),
            (ScheduleType.ONCE.value, "一次性執行"),
            (ScheduleType.DAILY.value, "每日重複"),
            (ScheduleType.WEEKLY.value, "每週重複"),
            (ScheduleType.CUSTOM.value, "自訂間隔")
        ]
        
        for value, text in types:
            rb = ttk.Radiobutton(type_frame, text=text, 
                               variable=self.schedule_type_var, value=value,
                               command=self._on_schedule_type_change)
            rb.pack(anchor=tk.W, pady=2)
        
        # Start time configuration
        self._create_start_time_frame()
        
        # End time configuration
        self._create_end_time_frame()
        
        # Schedule-specific options
        self._create_options_frame()
        
        # Update UI based on initial selection
        self._on_schedule_type_change()
    
    def _create_start_time_frame(self):
        """Create start time configuration frame."""
        self.start_frame = ttk.LabelFrame(self, text="開始時間", padding=5)
        self.start_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Date and time inputs
        datetime_frame = ttk.Frame(self.start_frame)
        datetime_frame.pack(fill=tk.X)
        
        # Date input
        ttk.Label(datetime_frame, text="日期:").pack(side=tk.LEFT)
        date_entry = ttk.Entry(datetime_frame, textvariable=self.start_date_var, width=12)
        date_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # Time input
        ttk.Label(datetime_frame, text="時間:").pack(side=tk.LEFT)
        time_entry = ttk.Entry(datetime_frame, textvariable=self.start_time_var, width=8)
        time_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Help text
        help_text = ttk.Label(self.start_frame, 
                             text="日期格式: YYYY-MM-DD, 時間格式: HH:MM",
                             font=("", 8), foreground="gray")
        help_text.pack(anchor=tk.W, pady=(5, 0))
    
    def _create_end_time_frame(self):
        """Create end time configuration frame."""
        self.end_frame = ttk.LabelFrame(self, text="結束時間", padding=5)
        self.end_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Enable end time checkbox
        end_check = ttk.Checkbutton(self.end_frame, text="設定結束時間", 
                                  variable=self.has_end_time_var,
                                  command=self._on_end_time_toggle)
        end_check.pack(anchor=tk.W, pady=(0, 5))
        
        # Date and time inputs
        self.end_datetime_frame = ttk.Frame(self.end_frame)
        self.end_datetime_frame.pack(fill=tk.X)
        
        # Date input
        ttk.Label(self.end_datetime_frame, text="日期:").pack(side=tk.LEFT)
        end_date_entry = ttk.Entry(self.end_datetime_frame, textvariable=self.end_date_var, width=12)
        end_date_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # Time input
        ttk.Label(self.end_datetime_frame, text="時間:").pack(side=tk.LEFT)
        end_time_entry = ttk.Entry(self.end_datetime_frame, textvariable=self.end_time_var, width=8)
        end_time_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Initially disable end time inputs
        self._on_end_time_toggle()
    
    def _create_options_frame(self):
        """Create schedule-specific options frame."""
        self.options_frame = ttk.LabelFrame(self, text="排程選項", padding=5)
        self.options_frame.pack(fill=tk.X)
        
        # Weekly options (days of week)
        self._create_weekly_options()
        
        # Custom interval options
        self._create_custom_options()
    
    def _create_weekly_options(self):
        """Create weekly schedule options."""
        self.weekly_frame = ttk.Frame(self.options_frame)
        
        ttk.Label(self.weekly_frame, text="選擇星期:").pack(anchor=tk.W, pady=(0, 5))
        
        days_frame = ttk.Frame(self.weekly_frame)
        days_frame.pack(fill=tk.X)
        
        day_names = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
        
        for i, day_name in enumerate(day_names):
            cb = ttk.Checkbutton(days_frame, text=day_name, 
                               variable=self.days_vars[i],
                               command=self._on_change_callback)
            cb.pack(side=tk.LEFT, padx=(0, 10))
    
    def _create_custom_options(self):
        """Create custom interval options."""
        self.custom_frame = ttk.Frame(self.options_frame)
        
        ttk.Label(self.custom_frame, text="重複間隔:").pack(anchor=tk.W, pady=(0, 5))
        
        interval_frame = ttk.Frame(self.custom_frame)
        interval_frame.pack(fill=tk.X)
        
        # Interval value
        interval_spinbox = ttk.Spinbox(interval_frame, from_=1, to=999, 
                                     textvariable=self.interval_value_var, width=5,
                                     command=self._on_change_callback)
        interval_spinbox.pack(side=tk.LEFT)
        
        # Interval unit
        units = [("minutes", "分鐘"), ("hours", "小時"), ("days", "天")]
        unit_combo = ttk.Combobox(interval_frame, textvariable=self.interval_unit_var,
                                values=[unit[0] for unit in units], width=8, state="readonly")
        unit_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # Set display values for combobox
        unit_combo.bind("<<ComboboxSelected>>", self._on_change_callback)
    
    def _bind_events(self):
        """Bind widget events."""
        # Bind variable changes
        self.start_date_var.trace_add("write", lambda *args: self._on_change_callback())
        self.start_time_var.trace_add("write", lambda *args: self._on_change_callback())
        self.end_date_var.trace_add("write", lambda *args: self._on_change_callback())
        self.end_time_var.trace_add("write", lambda *args: self._on_change_callback())
        self.interval_value_var.trace_add("write", lambda *args: self._on_change_callback())
    
    def _on_schedule_type_change(self):
        """Handle schedule type change."""
        schedule_type = self.schedule_type_var.get()
        
        # Hide all option frames first
        self.weekly_frame.pack_forget()
        self.custom_frame.pack_forget()
        
        # Show relevant options based on schedule type
        if schedule_type == ScheduleType.WEEKLY.value:
            self.weekly_frame.pack(fill=tk.X)
        elif schedule_type == ScheduleType.CUSTOM.value:
            self.custom_frame.pack(fill=tk.X)
        
        # Update end time visibility
        if schedule_type in (ScheduleType.MANUAL.value, ScheduleType.ONCE.value):
            self.end_frame.pack_forget()
        else:
            self.end_frame.pack(fill=tk.X, pady=(0, 10))
            self.end_frame.pack_configure(before=self.options_frame)
        
        self._on_change_callback()
    
    def _on_end_time_toggle(self):
        """Handle end time checkbox toggle."""
        if self.has_end_time_var.get():
            # Enable end time inputs
            for widget in self.end_datetime_frame.winfo_children():
                widget.configure(state="normal")
        else:
            # Disable end time inputs
            for widget in self.end_datetime_frame.winfo_children():
                if isinstance(widget, ttk.Entry):
                    widget.configure(state="disabled")
        
        self._on_change_callback()
    
    def _on_change_callback(self, *args):
        """Call the change callback if provided."""
        if self.on_change:
            self.on_change()
    
    def get_schedule_config(self) -> Optional[Dict[str, Any]]:
        """
        Get the current schedule configuration.
        
        Returns:
            Dictionary with schedule configuration or None if invalid
        """
        try:
            schedule_type = ScheduleType(self.schedule_type_var.get())
            
            # Parse start time
            start_date_str = self.start_date_var.get().strip()
            start_time_str = self.start_time_var.get().strip()
            
            if not start_date_str or not start_time_str:
                return None
            
            start_time = datetime.strptime(f"{start_date_str} {start_time_str}", 
                                         "%Y-%m-%d %H:%M")
            
            # Parse end time if enabled
            end_time = None
            if self.has_end_time_var.get() and schedule_type not in (ScheduleType.MANUAL.value, ScheduleType.ONCE.value):
                end_date_str = self.end_date_var.get().strip()
                end_time_str = self.end_time_var.get().strip()
                
                if end_date_str and end_time_str:
                    end_time = datetime.strptime(f"{end_date_str} {end_time_str}", 
                                               "%Y-%m-%d %H:%M")
            
            # Get schedule-specific options
            interval = None
            days_of_week = None
            
            if schedule_type == ScheduleType.WEEKLY:
                days_of_week = [i for i, var in enumerate(self.days_vars) if var.get()]
                if not days_of_week:
                    return None  # At least one day must be selected
            elif schedule_type == ScheduleType.CUSTOM:
                interval_value = self.interval_value_var.get()
                interval_unit = self.interval_unit_var.get()
                
                if interval_unit == "minutes":
                    interval = timedelta(minutes=interval_value)
                elif interval_unit == "hours":
                    interval = timedelta(hours=interval_value)
                elif interval_unit == "days":
                    interval = timedelta(days=interval_value)
                else:
                    return None
            
            return {
                'schedule_type': schedule_type.value,
                'start_time': start_time,
                'end_time': end_time,
                'interval': interval,
                'days_of_week': days_of_week
            }
        except (ValueError, TypeError):
            return None
    
    def set_schedule(self, schedule):
        """
        Set the widget values from a Schedule object.
        
        Args:
            schedule: Schedule object to load
        """
        if not schedule:
            return
        
        # Set schedule type
        self.schedule_type_var.set(schedule.schedule_type.value)
        
        # Set start time
        self.start_date_var.set(schedule.start_time.strftime("%Y-%m-%d"))
        self.start_time_var.set(schedule.start_time.strftime("%H:%M"))
        
        # Set end time
        if schedule.end_time:
            self.has_end_time_var.set(True)
            self.end_date_var.set(schedule.end_time.strftime("%Y-%m-%d"))
            self.end_time_var.set(schedule.end_time.strftime("%H:%M"))
        else:
            self.has_end_time_var.set(False)
        
        # Set schedule-specific options
        if schedule.schedule_type == ScheduleType.WEEKLY and schedule.days_of_week:
            for i, var in enumerate(self.days_vars):
                var.set(i in schedule.days_of_week)
        elif schedule.schedule_type == ScheduleType.CUSTOM and schedule.interval:
            total_seconds = int(schedule.interval.total_seconds())
            
            if total_seconds % 86400 == 0:  # Days
                self.interval_value_var.set(total_seconds // 86400)
                self.interval_unit_var.set("days")
            elif total_seconds % 3600 == 0:  # Hours
                self.interval_value_var.set(total_seconds // 3600)
                self.interval_unit_var.set("hours")
            else:  # Minutes
                self.interval_value_var.set(total_seconds // 60)
                self.interval_unit_var.set("minutes")
        
        # Update UI
        self._on_schedule_type_change()
        self._on_end_time_toggle()